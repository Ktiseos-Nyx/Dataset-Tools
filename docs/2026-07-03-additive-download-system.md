# Additive Multi-Source Download System — Design

**Status:** Arc-reviewed implementation draft
**Date:** 2026-07-03
**Scope:** v1 = pluggable source-adapter framework + Arc En Ciel adapter. Civitai left as-is. Arc Link remains later.

---

## 1. Context & Goal

Ktiseos-Nyx-Trainer (KNX) is a LoRA training tool: a FastAPI backend + Next.js
frontend that runs both **locally** (end-user machines) and on **remote rented GPU
boxes** (e.g. VastAI, accessed through a tunnel). Users download base models, LoRAs,
VAEs, and embeddings into either the trainer's own folders (for training) or the
bundled ComfyUI's folders (for generation).

**Today:**
- KNX has its own **Civitai** downloader. It works but is stale/fragile in the
  *search + URL-resolution* layer (Civitai's gated, quirky API). The underlying
  download **engine** is a good base, but Arc v1 must explicitly add/confirm
  SHA-256 verification, safe redirect handling, and optional request headers.
- **LoRA Manager (LM)** — the ComfyUI extension KNX already ships — handles Civitai
  well (batch URLs, rich metadata, confirmation). LM is the intended long-term owner
  of Civitai acquisition.
- **LM does not support Arc En Ciel** (`arcenciel.io`), a smaller community model site.

**Goal:** an *additive* download system — a small framework where new model **sources**
can be added over time behind a common interface. The first new source is **Arc En
Ciel**, precisely because LM won't do it. Over time, Civitai acquisition is handed to
LM and KNX owns the sources LM won't.

**Non-goals:**
- No forking of LoRA Manager (decided: LM stays as-is, unforked).
- No rebuilding what LM already does well.
- v1 does **not** touch the existing Civitai code.

---

## 2. Constraints & Principles

1. **Native / owned.** No dependency on forking a third-party project.
2. **Must work on remote instances.** Downloads run **server-side on the box**, so the
   user's browser can be anywhere (behind a tunnel). This is load-bearing — it's the
   reason the old Civitai link worked on remote boxes, and it must be preserved.
3. **Cross-platform** (Windows/macOS/Linux). Use `os.path`/`pathlib`, inject
   `PYTHONIOENCODING=utf-8`/`PYTHONUTF8=1` for any subprocess, no hardcoded separators.
4. **Contain each source's quirks in its own adapter.** A bug or API change in one
   source cannot destabilize another.
5. **Quality bar = LM.** Batch URLs, real metadata, SHA-256 confirmation, and
   per-item failure isolation.
6. **Use Arc's current public pull contract for v1.** Search/detail/version metadata and
   public downloads work without an Arc API key today. Arc Link Keys (`lk_...`) are for
   the later push/worker integration, not for v1 in-app pull.
7. **Treat credentials and redirects as security boundaries.** Do not put credentials in
   query strings or logs. Follow only HTTPS redirects to explicitly allowed hosts.

---

## 3. Architecture — two independent axes

The system separates **what** you download from (sources) from **how** a download is
triggered (triggers). They are independent layers.

```
┌─ Trigger layer (Axis 2) ────────────────────────────┐
│  v1:   In-app pull   (search in KNX UI → /download)  │  ← works LOCAL + REMOTE
│  later: Desktop Link (arcenciel.io push → worker)    │  ← mostly local; remote via
└──────────────────────┬──────────────────────────────┘     outbound websocket
                       │  both call ↓
┌─ Source adapters (Axis 1) ──────────────────────────┐
│  SourceAdapter interface + registry                  │
│   ├─ CivitaiAdapter    (NOT built in v1; legacy path │
│   │                     stays; future LM handoff)    │
│   ├─ ArcEnCielAdapter  (v1: public search/detail +   │
│   │                     safe server-side pull)       │
│   └─ (future: HuggingFace, direct URL, …)            │
└──────────────────────┬──────────────────────────────┘
                       │  produces a DownloadSpec
┌─ Download engine (already exists) ──────────────────┐
│  services/model_service.py: fallback chain           │
│  (hf_hub → aria2c → wget → requests), resume,        │
│  SHA-256 verify, safe redirects, filename routing    │
└──────────────────────────────────────────────────────┘
```

**v1 scope:** the `SourceAdapter` framework + `ArcEnCielAdapter` + in-app pull UI,
feeding the existing engine. The desktop Link (Axis 2) and Civitai adapter are **out of
scope for v1** but the seams are reserved for them.

---

## 4. Components

### 4.1 `SourceAdapter` interface

A source adapter knows how to *browse, describe, and resolve a download URL* for one
model site. It does **not** perform the download itself — it produces a `DownloadSpec`
the shared engine consumes.

```python
class SourceAdapter(Protocol):
    name: str                      # "arcenciel", "civitai", …
    credential_kind: str            # "none" | "api_key" | "link_key"

    def search(self, query: SearchQuery) -> SearchResult: ...
    def get_model(self, model_id: str) -> ModelDetail: ...
    def get_versions(self, model_id: str) -> list[ModelVersion]: ...
    def resolve_download(self, version: ModelVersion,
                         credential: str | None = None) -> DownloadSpec: ...
    def base_model_classes(self) -> list[str]: ...   # for search filters
```

**Shared data models** (source-agnostic; each adapter maps its site's JSON into these):

- `SearchQuery { term, sort, page, limit, base_model?, model_type? }`
- `ModelSummary { source, model_id, title, type, base_model, cover_url, nsfw }`
- `ModelDetail { …summary…, description, versions[] }`
- `ModelVersion { version_id, name, base_model, model_type, status, files[],
  sha256?, sha256_webui?, file_scan_status?, cover_url }`
- `DownloadSpec { url, filename, sha256?, size?, headers?, allowed_redirect_hosts,
  dest_type }`
  - `dest_type` is a normalized enum (`checkpoint | lora | vae | embedding | other`)
    used for destination routing (§4.4).

A **registry** maps `name → adapter`. Routes and UI iterate the registry so adding a
source is one new class + one registration line.

### 4.2 `ArcEnCielAdapter`

Verified against Arc En Ciel production on 2026-07-03/04. The old community reference
clients remain useful leads, but the v1 implementation should follow the current public
contract below.

- **Base URL:** `https://arcenciel.io/api`
- **Search (confirmed unauthenticated GET):**
  `GET /models/search?search=&sort=&page=&limit=&baseModel=&modelType=&status=available`
  - For grids, use `compact=true&versionLimit=1..50`.
  - Do **not** use compact search results to resolve downloads; compact responses omit
    file metadata (`filePath`, `fileName`, `sha256`, etc.).
- **Classes / base models:** `GET /models/classes` returns `{ classes: [{ id, name }] }`.
- **Detail:** `GET /models/{id}`
- **Versions:** `GET /models/{id}/versions` carries authoritative download metadata:
  `filePath`, `fileName`, `originalName`, `externalDownloadUrl`, `fileSizeKb`, `sha256`,
  `sha256webui`, `baseModel`, `status`, and `fileScanStatus`.
- **Gallery (optional, for UI previews):** `GET /models/{id}/gallery`
- **Download URL resolution:**
  - If `externalDownloadUrl` is present, only download it when the host is allowlisted
    (currently expected: HuggingFace/HF direct URLs).
  - Otherwise use the canonical Arc endpoint:
    `https://arcenciel.io/api/models/{model_id}/versions/{version_id}/download`.
  - Arc currently responds to the canonical endpoint with `302` to
    `https://uploads.arcenciel.io/api/models/{model_id}/versions/{version_id}/download`,
    then `200` with `Content-Length`, `Accept-Ranges`, and `Content-Disposition`.
- **Auth for v1 pull:** no Arc API key is required for public published downloads.
  Do not add an "Arc API key" setting for v1.
- **Assets base:** image paths are uploads-relative; resolve against
  `https://arcenciel.io/uploads/{path}` or the image URL helper already used in KNX UI.
- **Rate limit observed:** public API responses include a `1200` requests/minute policy.
  Add client-side debouncing, pagination, and modest retry/backoff for `429`.
- **Link Keys:** `lk_...` credentials are for Arc Link worker/queue flows only (§6.4).

### 4.3 Download engine (reuse with required hardening)

`services/model_service.py::download_model_or_vae(DownloadConfig)` already:
- takes a URL + optional `api_token`, downloads **server-side** (remote-safe),
- runs a fallback chain (hf_hub → aria2c → wget → requests) with resume,
- preserves filename.

Before Arc ships, confirm/add these engine guarantees:

- `DownloadConfig.headers: dict[str, str] | None` pass-through for HEAD, aria2c, wget,
  and requests. Redact sensitive header values from logs.
- `DownloadConfig.expected_sha256: str | None`; after download, compute SHA-256 and fail
  the item if it does not match Arc's `sha256`.
- `DownloadConfig.allowed_redirect_hosts: set[str]`; for Arc allow
  `arcenciel.io` and `uploads.arcenciel.io`; for external HuggingFace allow
  `huggingface.co`, `hf.co`, and their documented subdomains.
- Reject non-HTTPS final URLs, unsupported schemes, missing/HTML-looking files, and
  filename/path traversal. Always write to a temp file first, verify, then atomically move
  into the final destination.
- Preserve server-side execution and background-job polling. Do not hold one HTTP request
  open for the entire multi-GB transfer.

The adapter's `DownloadSpec` maps directly onto `DownloadConfig`.

### 4.4 Destination routing

Reuse the existing pattern from the Civitai endpoint (`api/routes/civitai.py:262`):
a request carries a `destination` (`training` vs `comfyui`) and, for ComfyUI, a subfolder.
The adapter's normalized `dest_type` maps to a concrete directory. Arc's current model
types are `LORA`, `CHECKPOINT`, `EMBEDDING`, `VAE`, `SEGMENTATION`, and `OTHER`; do not
assume Arc exposes `diffusion_model` or `text_encoder` as first-class model types.

| `dest_type` | training dest | comfyui dest |
|---|---|---|
| `checkpoint` | `pretrained_model/` | `ComfyUI/models/checkpoints/` |
| `lora` | `output/` | `ComfyUI/models/loras/` |
| `vae` | `vae/` | `ComfyUI/models/vae/` |
| `embedding` | `pretrained_model/` | `ComfyUI/models/embeddings/` |
| `other` / `segmentation` | `pretrained_model/` | user-selected folder |

For ComfyUI, keep the folder override visible. If KNX wants advanced defaults later
(e.g. Flux/Anima diffusion models), derive that from `baseModel`/filename heuristics and
still let the user override.

ComfyUI path resolution uses `get_comfyui_models_path()` (recently hardened to prefer the
bundled `{project_root}/ComfyUI/models`).

### 4.5 API routes / process boundary

New endpoints live in FastAPI (which already owns model downloads):
`GET /api/sources`, `GET /api/sources/{name}/search`,
`GET /api/sources/{name}/models/{id}`, `POST /api/sources/{name}/download`.

**No `server.js` whitelist change needed:** the Node server only routes a fixed set of
`/api/*` prefixes to itself and sends everything else to FastAPI:8000. `/api/sources/*`
falls through to FastAPI automatically.

### 4.6 Frontend UI

A source-agnostic **Browse & Download** surface (shadcn/ui only — `Select`, `Input`,
`Button`, `Card`), modeled on the existing Civitai browse tab:

- A **source selector** (`Civitai | Arc En Ciel`) driving the same results grid.
- Search box + filters (base model, type) populated from the adapter.
- Result cards → version picker → **destination choice** (training vs ComfyUI folder).
- **Batch selection** (queue multiple, mirroring LM's batch-URL strength).
- Live download progress from the job manager.
- No Arc API-key setting for v1. If a later Link flow is added, it should ask for an
  Arc Link Key (`lk_...`) and clearly label it as worker/queue auth, not API auth.

---

## 5. Phase 0 — Arc API smoke probe

**Why:** Arc has no public API docs. The v1 public pull contract has been verified once,
but KNX should keep a tiny repeatable smoke probe so future Arc deploy changes are caught
before users hit broken downloads.

**What:** a small unauthenticated probe:
1. `GET /models/search?...&status=available&compact=true&versionLimit=1` — confirm open
   access + response shape.
2. `GET /models/{id}/versions` — confirm file metadata: filename, size, SHA-256 field,
   `externalDownloadUrl` vs `filePath`, model type, base model, and `fileScanStatus`.
3. `HEAD` the canonical Arc download URL and record status + final host:
   - expected for Arc-hosted files: `302` to `uploads.arcenciel.io`, then `200`.
   - expected for external-only files: adapter should use validated `externalDownloadUrl`.
4. Confirm headers: `Content-Length`, `Accept-Ranges`, `Content-Disposition`, and any
   `RateLimit-*` headers.

**Output:** pins `ArcEnCielAdapter.resolve_download`, redirect allowlist, filename logic,
and hash verification fixtures. It should not require a maintainer account or API key.

---

## 6. Open Questions for Arc En Ciel / the Arc dev

Grouped and prioritized. **[BLOCKER]** = needed before v1 ships.
**[LATER]** = informs the future desktop Link, not v1.

### v1 blockers
1. **[BLOCKER]** Implement SHA-256 verification in KNX's download engine using Arc's
   `sha256` field.
2. **[BLOCKER]** Implement HTTPS-only redirect allowlisting:
   `arcenciel.io`, `uploads.arcenciel.io`, and explicit external providers only.
3. **[BLOCKER]** Treat compact search as non-downloadable. Always fetch detail/versions
   before resolving a download.
4. **[BLOCKER]** Respect version availability:
   - only download `status=PUBLISHED` versions,
   - scheduled/upcoming versions may appear in feeds but file fields can be redacted,
   - block or surface a clear error for `fileScanStatus` values that Arc blocks.
5. **[BLOCKER]** Sanitize filenames from `originalName || fileName || version-{id}` and
   write via temp-file → hash verify → atomic move.

### Metadata & taxonomy
6. Current version fields used by KNX:
   `originalName`, `fileName`, `fileSizeKb`, `sha256`, `sha256webui`, `externalDownloadUrl`,
   `filePath`, `baseModel`, `status`, `fileScanStatus`.
7. Current Arc model types:
   `LORA`, `CHECKPOINT`, `EMBEDDING`, `VAE`, `SEGMENTATION`, `OTHER`.
8. `/models/classes` returns Arc base-model/class names such as Anima, Chenkin RF,
   Chroma, Flux.1 D, Illustrious, NoobAI variants, Pony, etc.

### Operational
9. Public API currently advertises a `1200` requests/minute rate-limit policy. Use
   debounced search and backoff on `429`.
10. There is no public source-side batch download endpoint needed for v1. KNX should
    queue multiple adapter-resolved `DownloadSpec`s and process them per item.
11. Use a clear `User-Agent` identifying KNX, and honor Arc model metadata/links in UI.

### Desktop Link — future (later)
12. **[LATER]** Arc Link uses Link Keys (`lk_...`) as the current worker credential.
    Legacy API-key WebSocket auth is deprecated and may be rejected.
13. **[LATER]** Worker connections are outbound to `link.arcenciel.io` over WebSocket,
    which is the right shape for remote boxes if the box has outbound network access.
14. **[LATER]** Existing Link REST endpoints already support queueing:
    `POST /api/link/queue` and `POST /api/link/queue/bulk` with `x-link-key` and scope
    `jobs`. `targetPath` must start with `models/<category>` or `embeddings`.

---

## 7. Testing

- **Adapter unit tests** (mock Arc HTTP responses, GPU-free): search parsing, version
  parsing, compact-search-no-download behavior, `resolve_download` for both
  `externalDownloadUrl` and canonical Arc `/download` cases, blocked scan statuses,
  scheduled/redacted versions, `dest_type` → directory mapping.
- **Engine tests**: SHA-256 match/mismatch, temp-file cleanup, filename sanitization,
  HTTPS-only redirect allowlist, disallowed redirect host, header redaction, resume.
- **Phase 0 smoke probe** can be a manual script, but keep it checked in so maintainers
  can re-run it when Arc changes.

---

## 8. Rollout

| Phase | Deliverable |
|---|---|
| **0** | Arc API smoke probe → pins response shape, redirect allowlist, fixtures |
| **1** | Engine hardening: SHA-256 verify, headers, HTTPS redirect allowlist, filename/temp-file safety |
| **2** | `SourceAdapter` interface + registry + `ArcEnCielAdapter` (search + detail + resolve) + FastAPI routes + wire to engine |
| **3** | Frontend Browse & Download UI (source selector, batch, destination) with no Arc API-key setting |
| **4 (later)** | Civitai acquisition handed to LM; deprecate/remove KNX's Civitai downloader |
| **5 (later)** | Desktop Link bridge (Axis 2) — outbound-WS worker, Link Key |

---

## 9. Out of scope (v1)

- Forking LoRA Manager (permanently off the table).
- Touching or "fixing" the existing Civitai downloader.
- The desktop Link bridge (designed-for, not built).
- Arc API-key UX for v1 pull downloads.
- Any credential-in-query-string flow.
