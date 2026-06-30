# PLAN — Raw Metadata Edit (PNG) for Dataset-Tools

> **AI handoff note.** This file is a self-contained build plan written in a prior
> session (rooted in a *different* repo, so its memory doesn't carry here). Read it,
> then follow **DT's own `CLAUDE.md`** for conventions. Ask the user before
> deviating from scope below.

## Goal

Add a **dead-simple metadata editor**: show the image's **whole raw metadata string
in one editable textarea**, let the user edit it freely, save it back **in place**.
No per-field UI. No "field for every value." One box, the whole string.

### Why this exists (real use case)
A ComfyUI LoRA-Manager cache bug baked the **wrong LoRA** into the metadata of a
batch of generated images. The user knows the correct LoRA and wants to **fix the
text in place** rather than regenerate ("perfe piccies" — must not be altered).

## Scope — keep it tight

- **PNG only** for now. JPG/EXIF is **deferred** (user has no JPGs to fix yet).
- **Raw string edit**, not parsing. Show the full `parameters` text; user edits it.
- **Do NOT** rebuild DT's parser or fix DT's ComfyUI-detection here — separate job.
- **Do NOT** add per-field editors, batch-apply, or JPG. Resist gold-plating.

## What the data actually is

These are ComfyUI images saved through **LoRA Manager's `Save Image` node**, which
writes the **A1111 / WebUI `parameters` string** into a PNG **`tEXt` chunk keyed
`parameters`** (same format A1111 uses). Example value:

```
masterpiece, best quality, ... cinematic. <lora:CafeBars-KNX:1.0>
Negative prompt: monochrome, worst quality, ...
Steps: 30, Sampler: DPM++ 2M SDE SGM Uniform, CFG scale: 4.0, Seed: 381718260773478,
Size: 832x1216, Model hash: bd43b7cffe, Model: anima-base-v1.0,
Lora hashes: "CafeBars-KNX: 1d9191ae7b"
```

The LoRA appears in **two spots** (inline `<lora:NAME:weight>` and
`Lora hashes: "NAME: hash"`). The user edits both *by hand in the textarea* — the
feature does not need to find or parse them.

## Approach — client-side chunk edit (no pixel recompress)

Read/write the PNG **`tEXt` chunk** with chunk-level libs. **Do NOT use `pngjs`** —
it decodes + re-encodes the whole image, recompressing the user's images and
possibly dropping chunks. Chunk-level edit leaves **pixels byte-for-byte identical.**

```
npm i png-chunks-extract png-chunks-encode png-chunk-text
```
(These ship **no types** — add a one-line `declare module` shim per package, or
`// @ts-ignore` at the imports.)

Suggested util (e.g. `lib/png-metadata.ts`):

```ts
import extractChunks from 'png-chunks-extract';
import encodeChunks from 'png-chunks-encode';
import text from 'png-chunk-text';

// READ → the whole A1111 "parameters" string for the textarea
export async function readPngParameters(file: File): Promise<string | null> {
  const chunks = extractChunks(new Uint8Array(await file.arrayBuffer()));
  for (const c of chunks) {
    if (c.name !== 'tEXt') continue;
    const { keyword, text: value } = text.decode(c.data);
    if (keyword === 'parameters') return value;
  }
  return null;
}

// WRITE → swap the string, leave every pixel byte-for-byte identical
export async function writePngParameters(file: File, edited: string): Promise<Uint8Array> {
  const chunks = extractChunks(new Uint8Array(await file.arrayBuffer()));
  const kept = chunks.filter(c => c.name !== 'tEXt' || text.decode(c.data).keyword !== 'parameters');
  const iend = kept.findIndex(c => c.name === 'IEND');   // tEXt must sit before IEND
  kept.splice(iend, 0, text.encode('parameters', edited));
  return encodeChunks(kept);                             // pixels never decoded → no recompress
}
```

## Save mechanism

DT loads files **server-side by path** (inline path input), so the clean in-place
overwrite is a **small write route**, not a browser download:

- New route, e.g. `app/api/metadata-write/route.ts` → `fs.writeFile(path, bytes)`.
- **Security:** mirror the path validation used by DT's existing read routes
  (`app/api/fs`, `app/api/image`, `app/api/metadata-from-file`) — confine to allowed
  dirs, reject path traversal. Do **not** write arbitrary paths.
- Client builds the new PNG `Uint8Array` (via `writePngParameters`) and POSTs
  `{ path, bytes }` to the route.
- *(Pure-no-backend alt: File System Access API — but it prompts per file and fights
  how DT already loads. Skip unless asked.)*

**Destructive-write guard (these images are precious):** confirm before overwrite,
**or** offer a "save as copy" toggle (write `name.edited.png` alongside). Recommend
at least a confirm step.

## Wiring tasks (checklist)

- [ ] `npm i png-chunks-extract png-chunks-encode png-chunk-text` (+ type shims).
- [ ] Add `lib/png-metadata.ts` (the two functions above).
- [ ] Add `app/api/metadata-write/route.ts` (validated `fs.writeFile`).
- [ ] Find the metadata display component (ROADMAP calls it **`MetadataPanel`**).
- [ ] Add an **"Edit"** button there → shadcn **Dialog** with a **Textarea**
      prefilled from `readPngParameters` → **Save** builds bytes + POSTs to the route
      → toast on success. Confirm-before-overwrite (or save-as-copy).
- [ ] **Use shadcn components** (Dialog, Textarea, Button) — DT has `components.json`;
      shadcn is mandatory, no raw HTML form elements.
- [ ] Graceful empty state if a PNG has no `parameters` chunk.

## Out of scope (explicitly, so it doesn't creep)

JPG/EXIF (`piexifjs`, later) · per-field parsing/editing · fixing DT's
ComfyUI-as-A1111 **detection** (separate job) · batch-apply-to-many (user hand-sorts
a small set).
