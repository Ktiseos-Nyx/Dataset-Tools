# ArcEnCiel Model Lookup — Design & Handoff

**Status:** Design draft — for handoff to ArcEnCiel (FallenIncursio)
**Date:** 2026-10-04
**Related:** `docs/2026-07-03-additive-download-system.md` (ArcEnCiel public API contract, §4.2)

---

## 1. Context & Goal

Dataset-Tools is a **metadata viewer**, not a downloader. It already detects
ArcEnCiel-generated images and tags them `workflow_type: 'ArcEnCiel'`, but — unlike
Civitai — it cannot **resolve** the models those images used into real, clickable
model metadata.

The goal of this doc is to route the one missing piece (an ArcEnCiel *lookup*
contract) so it can match the existing Civitai lookup, and to turn that into a
concrete set of questions to hand to FallenIncursio rather than forcing a half-built
integration now.

**Non-goals:** downloads, SHA-256 verification, destination routing, `lk_...` Link
Keys — all of that is the trainer's download system, not Dataset-Tools.

---

## 2. The target pattern — how Civitai lookup works today

Dataset-Tools resolves Civitai models **authoritatively** from a machine-readable
identifier embedded in the workflow:

- ComfyUI (and compatible frontends) embed resource URNs in model input fields:
  `urn:air:{baseModel}:{type}:civitai:{modelId}@{versionId}`
- `app/api/metadata/route.ts:1200-1217` scans the workflow JSON for this pattern and
  emits `civitai_urn_resources` with `baseModel`, `type`, `modelId`, `versionId`.
- `components/metadata-panel.tsx` renders each as a direct link:
  `https://civitai.com/models/{modelId}?modelVersionId={versionId}`
- Optional enrichment: `app/api/civitai?modelId=X` → `civitai.com/api/v1/models/{id}`,
  routed through the `safeFetch` egress allowlist.

The key property: **the workflow itself carries the model ID**, so resolution is a
direct lookup with no guessing.

---

## 3. How ArcEnCiel works today (detection only)

`app/api/metadata/route.ts:1168-1193` detects ArcEnCiel by two local signals:

1. `SaveImage` node with `filename_prefix` matching `generator/{uuid}` (36-char UUID).
2. A `lora_name` that is UUID-prefixed, e.g. `ab234327-…_LoraName.safetensors`.

When either matches, `workflow_type = 'ArcEnCiel'` is set and that's it — the model
itself is never identified. ArcEnCiel runs standard ComfyUI nodes, so node
classification works fine; it's the **model resource identifier** that's absent.

---

## 4. The gap

- **No machine-readable model identifier.** Civitai gets `urn:air:…civitai:{modelId}@{versionId}`.
  ArcEnCiel embeds only a UUID-prefixed filename/lora name — there is no known
  equivalent URN, and no confirmed model/version ID.
- **UUID semantics unknown.** Is the `{uuid}` prefix a generation job ID, a model ID,
  a version ID, or nothing we can resolve? Unconfirmed — this is the crux.
- **No lookup endpoint is wired.** We have the public API contract on paper (see §7)
  but no code path consumes it for metadata.

---

## 5. Proposed design — matching Civitai

### 5.1 Short term (buildable now, fuzzy)

A search-based fallback that works against the public API without needing a new
identifier from ArcEnCiel:

1. Strip the UUID prefix from `inputs.lora_name` to recover the human-readable name.
2. `GET https://arcenciel.io/api/models/search?search={name}&status=available`.
3. Surface the top match(es) — title, `baseModel`, model type, cover image — in the
   AI tab, flagged as a *best-effort guess* (same honesty we give GitHub-resolved
   nodes with `source: 'github'`).
4. New `app/api/arcenciel` route behind `safeFetch`; add `arcenciel.io` to
   `ALLOWED_FETCH_HOSTS` in `lib/safe-fetch.ts`.

**Limitation:** relies on the lora name string being a close-enough match to Arc's
model title — fuzzy, can misresolve.

### 5.2 Ideal (needs FallenIncursio, authoritative)

The clean path is for ArcEnCiel to embed a machine-readable identifier — ideally the
same `urn:air` convention — so resolution matches Civitai's exact code path:

- If ArcEnCiel starts emitting `urn:air:{baseModel}:{type}:arcenciel:{modelId}@{versionId}`
  in `lora_name`/`model_name`, Dataset-Tools gets a direct, authoritative lookup with
  zero guessing: extract URN → `GET /models/{id}` + `/models/{id}/versions` → link.

This is the single change that makes ArcEnCiel lookups first-class rather than fuzzy.

---

## 6. Open questions for FallenIncursio

Prioritized — 1-3 are the ones that decide between 5.1 and 5.2.

1. **Does ArcEnCiel embed any machine-readable model/version identifier** in workflow
   metadata today (URN:AIR or otherwise)? If so, exact format and where it appears.
2. **What is the `{uuid}` prefix** in `generator/{uuid}` and UUID-prefixed lora names?
   Generation job ID, model ID, version ID, or opaque? Can it be resolved to a model?
3. **Is the public API stable for read-only lookup** (`/models/search`,
   `/models/{id}`, `/models/{id}/versions`)? Any changes planned that would break a
   third-party metadata viewer?
4. **Would ArcEnCiel consider adopting the `urn:air` resource identifier** (or
   documenting an existing one) so external tools can resolve models authoritatively?
5. **Lookup-only expectations:** attribution/User-Agent requirements, and whether the
   1200 req/min public limit applies to read-only metadata use.

---

## 7. Next steps — what happens once we have answers

This is not a write-and-forget doc. The moment FallenIncursio answers the questions
in §6, the lookup graduates from design to a planned implementation. The path forks
on the identifier question:

- **If a machine-readable identifier exists (or ArcEnCiel adopts one)** → §5.2 is the
  plan: extract it in `app/api/metadata/route.ts`, add an `/api/arcenciel` route
  behind `safeFetch` (`arcenciel.io` allowlisted), and render links in the AI tab
  exactly like Civitai's `civitai_urn_resources`.
- **If no identifier exists** → §5.1 is the plan: search-by-lora-name fallback,
  flagged as best-effort (same honesty we give GitHub-resolved nodes), until ArcEnCiel
  adopts a URN.

Either way the build sequence is the same shape and small:

| Phase | Deliverable |
|---|---|
| 0 | Confirm answers from FallenIncursio; pin the lookup key + API response shape |
| 1 | Extend the metadata parser to emit an `arcenciel_*` resource (name or URN) |
| 2 | `app/api/arcenciel` route (search/detail) via `safeFetch`, allowlist `arcenciel.io` |
| 3 | AI-tab display — links + base model/type, best-effort flag where applicable |

Each phase is independently shippable and none of it blocks the current release. When
the answers land, §6 becomes a checklist and the table above becomes the build order.

---

## 8. Technical notes — known public API contract

Carried over from `docs/2026-07-03-additive-download-system.md` §4.2 (the
lookup-relevant subset only):

| Item | Value |
|---|---|
| Base URL | `https://arcenciel.io/api` |
| Search | `GET /models/search?search=&baseModel=&modelType=&status=available` (unauthenticated) |
| Classes | `GET /models/classes` |
| Detail | `GET /models/{id}` |
| Versions | `GET /models/{id}/versions` → `originalName`, `fileName`, `baseModel`, `fileSizeKb`, `sha256`, `status`, `fileScanStatus` |
| Gallery | `GET /models/{id}/gallery` |
| Assets | resolve image paths against `https://arcenciel.io/uploads/{path}` |
| Auth | none required for public published content |
| Rate limit | 1200 req/min (plenty for lookup) |
| Egress allowlist | add `arcenciel.io` (API + uploads share the host) |

The download-only fields (`filePath`, `externalDownloadUrl`, `sha256webui`) and the
`/download` endpoint are **not** needed for lookup and can be ignored.

---

## 9. Out of scope

- Downloads and the trainer's `DownloadSpec` / SHA-256 / redirect machinery.
- `lk_...` Link Keys and the desktop Link worker flow.
- Changing or "fixing" the existing Civitai downloader.
