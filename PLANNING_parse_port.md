# Python Branch — Parsing Port Plan

> Goal: rebuild the `master_pyqt6` branch's metadata parsing to match the
> `main` (NodeJS) branch's signal-driven design, with minimal heuristics and a
> much smaller dependency footprint. Keep the native PyQt6 UI. Keep both
> branches separate; this repo stays the desktop-native edition.

## Reference

- Canonical parser to port: `Dataset-Tools/app/api/metadata/route.ts` (~2100 lines)
- Issue: https://github.com/Ktiseos-Nyx/Dataset-Tools/issues/212
- The NodeJS `main` branch is the "fixed" version of what this branch built.

## Core principle: two kinds of "heuristic"

| Kind | Python (current) | NodeJS (reference) | Fate |
|---|---|---|---|
| **Confidence scoring** — fuzzy "how sure am I this is the prompt" weights | `numpy_scorers/` (magic numbers, keyword lists, `+8`/`+0.15` boosts) | none | **Delete entirely** |
| **Structural/classification** — "what *is* this thing?" yes/no via regex + field-shape | buried in `rule_engine.py` | thin, justified set (see below) | **Keep, ~1 module's worth** |

The nodejs "tiny bit" of heuristics that legitimately remain (and are fine to keep):

- `TEXT_INPUT_KEYS` / `NON_PROMPT_KEY_FRAGMENTS` — field-name hints while tracing
- `looksLikeTextEncoder` — last-resort class-name substring, only after graph trace fails
- `AI_ENHANCER_PATTERNS` — "is this node an LLM prompt-writer" (a real yes/no)
- mojibake / byte-order / UTF-16 detection — decoding correctness, unavoidable
- version-string regexes (`f\d+...` → Forge, `neo` → Forge Neo, `NGMS:` → Yodayo) — signals, not guesses

None of these emit a confidence number. The parser *decides*, it doesn't *estimate*.
That is what makes it feel native.

## Gap analysis (what Python has vs NodeJS)

- **NodeJS is missing (port back later, if ever):** GGUF model parser,
  Mochi Diffusion, Topaz Gigapixel, SD.Next / RuinedFooocus fork *labels*.
- **NodeJS is NOT missing:** every ComfyUI ecosystem extractor (`Kolors`,
  `Lumina`, `AuraFlow`, `Qwen`, `HiDream`, `PixArt`, `Griptape`, `rgthree`,
  `WAS`, `Inspire`, `Impact`, `Flux`, ...). These are ~40 redundant modules
  + heuristic scoring here; NodeJS covers them with one graph-tracer.
- **NodeJS is ahead in:** ArcEnCiel, Forge Neo/ReForge version detection,
  WebP EXIF, byte-order-correct UTF-16 UserComment, LibLibAI, InvokeAI.

Net: porting `route.ts` loses nothing meaningful except GGUF (a model-file
feature, orthogonal to image metadata).

## Performance & RAM — targets & techniques

Real scenario: ~50–500 images, mixed, worst case 30MB JPEG + 50MB ComfyUI PNG.
Two completely separate cost centers — treat them separately.

### 1. Metadata parsing — never decode pixels
The port reads PNG chunks streaming and **skips IDAT** (the pixel data). A
50MB ComfyUI PNG is ~50MB of pixels + a few MB of `tEXt`/`prompt`/`workflow`
chunks; parsing only touches the latter, so it runs in milliseconds with ~no
RAM. This is the single biggest "less RAM" win, and it's why no image library
(Pillow, libvips, or otherwise) belongs in the parsing path at all.

### 2. Thumbnails — decode once, at thumb size, cache to disk
The only pixel decode in the app. Techniques, in priority order:

- JPEG: call `img.draft("RGB", (size, size))` before anything — decodes at
  reduced resolution (the one case where libvips would otherwise be 10x faster).
- Two-step downscale: `img.reduce(n)` (integer factor, cheap) then
  `img.thumbnail((size, size), Image.Resampling.BILINEAR)`.
- Skip `ImageOps.exif_transpose` for PNG (no orientation in practice); only
  apply for JPEG/TIFF. Avoids a forced full load/copy.
- Read dimensions from the header (the port already does this byte-level) —
  never decode just to size the letterbox.
- `Resampling.BILINEAR`/`BOX`, not LANCZOS — visually identical at ≤256px,
  meaningfully faster.
- Keep the existing lazy-load + `.thumbnails/*.webp` disk cache: a 30MB image
  is decoded exactly once, then it's a ~20KB webp.

### 3. RAM guard
A 4K PNG full-decode peaks ~64MB (RGBA). With the current 16-thread pool that
could spike ~1GB if many large files decode at once. Cap concurrent *decode*
workers for large-dimension files (decode is CPU/mem-bound, not IO-bound), or
bound the pool to ~2x cores. Small files stay heavily parallel.

Verdict: Pillow with `draft()` + `reduce()` covers this scale cleanly.
`pyvips`/libvips is only worth it for a future bulk pre-thumbnail batch mode.

## Phases

### Phase 0 — Freeze & inventory
Survive untouched: `ui/`, theming, `model_parsers/` (gguf + safetensors),
`civitai_api.py`, `crypto_secrets.py`, `file_operations.py`, `access_disk.py`,
`background_operations.py`.

### Phase 1 — New parser core (one package, mirrors `route.ts` 1:1)
- `parser/bytes.py` — magic-byte detect (png/jpeg/webp), PNG chunk reader
  (`tEXt`/`iTXt`/`zTXt`/`eXIf`), JPEG TIFF walker + `decodeUserComment`
  (byte-order + mojibake), WebP RIFF reader, XMP-by-regex, dimension sniffing.
- `parser/ai_metadata.py` — `parseAIMetadata` port: A1111-family signals,
  SwarmUI/EasyDiffusion JSON, InvokeAI, LibLibAI, NovelAI, Midjourney,
  Draw Things, Fooocus.
- `parser/comfyui.py` — graph trace (`extractPromptTextWithTrace`),
  field-shape matchers (`isSamplerByFields`, `isCheckpointByFields`,
  `isLatentByFields`), the 5 phases, muted/bypassed handling,
  provenance (`cnr_id`/`aux_id`).
- `parser/node_registry.json` — replaces `comfyui_node_dictionary.json`
  + `comfyui_node_dictionary_manager.py`.

Public API: `parse_image(buffer: bytes) -> dict` returning
`{ fileName, fileSize, fileType, width, height, exif, iptc, xmp, ai }`.

### Phase 2 — Wire in
Replace the `MetadataEngine` call in `metadata_parser.py` /
`background_operations.py` with `parse_image()`. Re-point the UI keys to the
new `ai` dict schema if they drift.

### Phase 3 — Dependency strip
Remove: `numpy`, `opencv-python-headless`, `pyexiv2`, `piexif`, `exif`,
`defusedxml`, `jsonpath-ng`. Reimplement `thumbnail_grid.py` letterbox in
Pillow using the fast path from "Performance & RAM" above (`draft()` for
JPEG, `reduce()` + `thumbnail()`, skip `exif_transpose` for PNG).
(numpy/cv2 are only used in `a1111_numpy_scorer.py` trivially and
`thumbnail_grid.py`; the entire `numpy_scorers/` package uses no numpy at all.)

### Phase 4 — Delete redundant systems
Remove: `metadata_engine/` (~80 JSON defs + ~40 extractors + `rule_engine.py`
+ template/field/context systems), `numpy_scorers/`, `vendored_sdpr/`,
`parser_definitions/`, and root `numpy_scorer.py`, `rule_evaluator.py`,
`metadata_parser.py`.

### Phase 5 — Parity gate
Run both branches over `example_images/`, diff the `ai` dicts. This is the
acceptance test. Keep GGUF parser working independently (Phase 0 preserved it).

### Phase 6 — Heuristic audit
Document the surviving heuristic set (table above) so confidence-scoring
doesn't get re-introduced later.

## Open questions / decisions

- [ ] Persist `ai` dict schema — match NodeJS keys exactly (`workflow_type`,
      `prompt`, `negative_prompt`, `seed`, `steps`, `cfg_scale`, `sampler`,
      `scheduler`, `model`, `loras`, `size`, `civitai_resources`, ...)?
- [ ] Node provenance (builtin/custom via `cnr_id`/`aux_id`) — port now, or
      defer the node-classification panel?
- [x] `thumbnail_grid.py` — rewrite in Pillow with the `draft()`/`reduce()`
      fast path; drop both numpy and cv2.
- [ ] GGUF: keep the existing `gguf_parser.py` as-is (it already works).
