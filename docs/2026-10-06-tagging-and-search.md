# Tagging & Search — Organization Plan

**Status:** Design draft — not started
**Date:** 2026-10-06

---

## 1. Context & Goal

Dataset-Tools has no search and no way to organize a folder of images. Searching by
*content* (EXIF/IPTC/XMP/AI parameters) is the dream, but it requires indexing all that
metadata into something queryable — i.e. a database — which is a long-term effort.

**Short-term win:** a lightweight, **manual** tag layer on top of the file tree. Tags are
curated by the user, attached to file paths, and filterable — so a big folder becomes
navigable *today*, without waiting on metadata indexing.

This is **not** auto-tagging. Dataset-Tools already *classifies the generating service*
(`workflow_type` — A1111 / Forge / ComfyUI / NovelAI / Civitai / ArcEnCiel / … in
`app/api/metadata/route.ts`); that's read-only metadata, and it's done.

Tags are the user's own **categorical labels**, applied by hand to whatever dimension
matters to them — a country, a subject, a shoot, a client, "favorite", "WIP"… Dataset-Tools
is **not AI-only**: tags are a general-purpose organizer, not an AI feature. It's
organization layered on top of the metadata we already extract, not a second classifier
and not a "suggested tag from the detected service".

### 1.1 Positioning — semi-organizing, not a dex replacement

The inspiration is *faithful, not competitive*: borrow the **idea** of "named, colored,
user-assigned labels you can filter by", nothing else. Dataset-Tools stays a metadata
viewer — we hold back on anything that turns it into a card/look tracker. If a feature
starts to smell like "GenDex replacement", it's out of scope. See §6.

---

## 2. Why tagging first, not content search

- Content search needs an index of parsed metadata → storage + query + reindex-on-change.
- Tagging needs only: a list of tags + a mapping of `filePath → tagIds`. Trivial to store,
  trivially queryable, and it compounds (tags survive metadata changes).

Tagging is the bootstrap for search: once files are tagged, "search" becomes "filter by
tag + match filename" — useful immediately, and content search can slot in later against
the same store.

---

## 3. Proposed design (minimal)

### 3.1 Data model

```ts
// tag definition
{ id: string, name: string, color: string }

// assignments — keyed by absolute path so a moved/renamed file drops its tags honestly
{ "C:/images/foo.png": ["tagId1", "tagId2"], ... }
```

No card, no class, no version, no prompt parts. Two collections only.

### 3.2 Storage — server-side JSON

Tags are keyed by absolute file path and should survive a browser session and the
optional Electron wrapper alike, so store them server-side (not `localStorage`):

- One JSON file, e.g. `.dataset-tools/tags.json` in the project root (or a data folder).
- Read/written by API routes, following the same "one JSON file you can back up" shape
  the rest of the app already leans toward. Atomic write (tmp + rename) on save.
- Server-side on purpose: it must work identically under the web app and the Electron
  build (which we ship as EXEs and keep for its security/functionality posture).

Open question: exact location — see §7.1.

### 3.3 API routes

| Route | Purpose |
|---|---|
| `GET /api/tags` | list tag definitions + all assignments |
| `POST /api/tags` | create/rename/recolor/delete a tag |
| `POST /api/tags/assign` | `{ path, tagIds }` → set a file's tags |
| `DELETE /api/tags/assign` | clear a file's tags |

Merged into fewer routes if that's cleaner; the point is a single owner for tag state.

### 3.4 UI

- **Tag manager** — create/rename/color/delete tags (a small palette of preset colors,
  not a full color wheel). Lives in the existing settings sheet or a small panel.
- **Assign** — on a selected image: a row of tag toggle-chips (pick existing tags, or
  create one inline).
- **Tag chips on rows/cards** — the file tree and thumbnail grid show each file's tags
  as colored chips.
- **Filter / search box** — narrows the tree by tag (AND/OR) and by filename substring.
  This is the "proper search function" for now; content search is §5.

---

## 4. Search — the roadmap

| Stage | What | Needs |
|---|---|---|
| 1 (now) | filename substring + tag filter | none — client-side + the tag store |
| 2 (later) | search by extracted params (prompt, model, seed, CFG, sampler) | indexed metadata |
| 3 (later) | full EXIF/IPTC/XMP text search | a real query store |

Stage 1 ships with tagging. Stages 2–3 are the "database functionality" you flagged as
the hard part — a future doc, not this one.

---

## 5. Build order

| Step | Deliverable | Independent? |
|---|---|---|
| 0 | Decide storage location (§7.1) | — |
| 1 | Tag store + `GET/POST /api/tags` | yes |
| 2 | Tag manager UI (settings sheet) | yes |
| 3 | Assign UI on selected image + chips on rows | yes |
| 4 | Filter/search box (tag + filename) | yes |
| 5 | (later) metadata index for stage-2 search | no — big, separate effort |

Each step is small and shippable; none blocks the metadata/parsing work.

---

## 6. Non-goals (explicitly out of scope)

- **Manual, categorical, no auto-tagger.** Assignments are user-driven. Service
  classification (`workflow_type`) already exists but is separate read-only metadata —
  tags never derive from it automatically.
- **No card/dex system.** No classes, tree-drag organization, prompt versioning, stamps,
  or ribbon aesthetics. Tags here are flat, user-defined labels.
- **No server database for stage 1.** One JSON file only.
- **No cross-machine sync.** Local to the folder/project, like the rest of the app.

---

## 7. Open questions

1. **Storage location** — project-root `.dataset-tools/tags.json` (visible, portable,
   gitignore-able) vs. an OS data folder. Recommend project-root for a viewer that
   browses arbitrary local folders.
2. **Filter semantics** — tag AND vs OR in the filter box; probably OR for discovery.
3. **Scope of tags** — global per project, or per-folder? Recommend global (one flat
   list), since a single image can't be in two folders at once anyway.
4. **Grounding — see §8.** Resolved by reading the code (no changes made); runtime
   topology report still welcome but no longer blocking.

---

## 8. Filesystem grounding — notes from reading the code (no changes)

Read to answer §7.4. Findings:

### 8.1 How paths resolve today

Every filesystem route (`/api/fs`, `/api/image`, `/api/thumbnail`,
`/api/safetensors`, `/api/metadata`, `/api/metadata-write`) takes a client-supplied
`path` + `baseFolder`. The resolution pattern is identical everywhere:

1. `resolvedBase = path.resolve(baseFolder)`
2. `fullPath = isAbsolute(path) ? path : path.join(resolvedBase, path)`
3. `resolvedPath = path.resolve(fullPath)`

`baseFolder` defaults to `.`; in the UI it's `settings.currentFolder`
(`types/settings.ts:30`, default `.`). There is **no fixed server-side root** — the
user picks the browse root. This is by design (`SECURITY_TODO.md` "Context").

### 8.2 Two containment levels, unevenly applied

- **Read routes** (`fs`, `image`, `thumbnail`, `safetensors`) use only a
  `startsWith(resolvedBase)` string-prefix check.
- **`/api/metadata-write`** (the only write route) is hardened: `path.relative`
  containment + `fs.realpath` symlink re-check + project-root containment (`baseFolder`
  inside `process.cwd()`).

`SECURITY_TODO.md:50-54` flags that the read routes should eventually fold onto the
hardened helper. This remains deferred only while the server is loopback-only and
serves a trusted local user. If the server binds to a non-loopback interface or serves
untrusted clients, enforce boundary-aware containment together with server-side
allowed-root and authentication controls.

### 8.3 Where app-level state already lives (the precedent for a tag store)

`DATA_DIR = ELECTRON_USER_DATA || path.resolve('.')` (`app/api/settings/route.ts:8-10`):

- `settings.json` → `DATA_DIR/settings.json`
- `.env.local` → `DATA_DIR/.env.local`
- thumbnail cache → `DATA_DIR/.thumbcache`

`ELECTRON_USER_DATA` is set by the Electron main process to the per-user app-data dir
(read-only install dir in a packaged app); in dev/Vercel it's absent, so it falls back
to `process.cwd()`.

### 8.4 Consequence for the tag store

- **Location: `DATA_DIR/tags.json`** (same dir as `settings.json`), **not** a
  `.dataset-tools` sidecar dropped in the browsed folder. The browsed root is arbitrary
  and user-switchable, so there is no stable "project folder" to write a sidecar into;
  the `DATA_DIR` convention already exists for exactly this kind of app-level state.
- **Tag key: absolute path.** Keying by `baseFolder`-relative path would orphan every
  tag the moment the user switches `currentFolder` (same file, different relative path).
  The absolute key is the `resolvedPath` the routes already compute. A rename/move drops
  tags honestly — the assumption we already accepted.
- **Validation:** any future `/api/tags` that reads/writes should reuse the hardened
  `resolveTarget` / `isInside` helper (`metadata-write`), not the weaker `startsWith`
  pattern the read routes use.

### 8.5 Side observation (unrelated, noticed in passing)

`thumbnail/route.ts:27` keys the cache as `{sanitizedPath}_{size}.webp`, where
`sanitizedPath` replaces every non-`[a-zA-Z0-9._-]` char with `_`. Two *different* files
whose paths sanitize to the same string **and** share a size collide in the cache. Low
severity (wrong thumbnail, never the wrong file) — noting it only because the thumbnail
UX is already under review in the theme doc §7.1.
