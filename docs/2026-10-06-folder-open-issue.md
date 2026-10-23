# Folder Opening & File Discovery — Re-review of #220 (post-#221)

**Status:** Analysis only — no code changes
**Date:** 2026-10-06
**Ref:** [issue #220](https://github.com/Ktiseos-Nyx/Dataset-Tools/issues/220), PR #221 (merged)

---

## 1. CodeRabbit's four findings, re-checked against current `main`

| # | CR finding | Re-check result |
|---|---|---|
| 1 | Electron `File.path` removed (Electron 32+); use `webUtils.getPathForFile` | **Fixed.** `electron/preload.ts:11`, `lib/electron-bridge.ts:60`, `components/drop-zone.tsx:83` |
| 2 | `/api/find-file` 8s timeout, no `request.signal`, 2-level depth, name+size match | **Still present** (see §4) |
| 3 | Watcher `ready` treated as a change; no error handling | **Fixed.** `file-tree.tsx:433` filters `type === 'change'`; `watch/route.ts:120` has an `error` handler |
| 4 | Browser `showDirectoryPicker` then extracts `File.path` | **Still present, and deeper than CR framed it** (see §2–3) |

So two of four are already resolved by #221. The remaining two are both on the
**browser** path — which is the environment this issue actually reproduces in.

---

## 2. The core mismatch (the "triple look")

Dataset-Tools' whole read model is **absolute path → `/api/fs?path=&baseFolder=`**,
resolved server-side (`path.resolve`) and read with `fs`. That only works when a real
absolute path reaches the server — i.e. under Electron (native `pickFolder` returns one)
or when the server is running on the same machine as the files it reads (the local
browser build, via a typed path).

Browsers **cannot** produce an absolute path from their folder pickers:

- `showDirectoryPicker()` returns a `FileSystemDirectoryHandle` — a *capability to
  traverse*, deliberately not a path.
- `<input webkitdirectory>` returns files whose `webkitRelativePath` is **relative to the
  picked directory**, not absolute.

So both browser folder-picker paths are architecturally dead: they ask the user to pick
a folder, then can't turn that into a `currentFolder`, and silently fall through to the
manual path editor.

---

## 3. The "Open Folder" button has four divergent paths

`components/file-tree.tsx` `handleOpenFolder` (line 348):

1. **Electron** → `pickFolder()` → real path → `updateSettings`. ✅ Works.
2. **Chrome/Edge** → `showDirectoryPicker()` → iterate entries → `entry.getFile()` →
   `extractFolderFromFile(file)` → reads `(file as File & {path?}).path` → **always null
   in browser** → `openPathEditor()`. ❌ Picker shown, then a text input appears instead.
3. **Firefox/Safari** (no `showDirectoryPicker`) → `folderPickerRef.click()` →
   `<input webkitdirectory>` → `handleFolderPickerChange` → `extractFolderFromFile` →
   `File.path` null → `openPathEditor()`. ❌ Same dead-end.
4. **Manual path editor** → type/paste absolute path → works, **local build only**. ✅

Additional observations:

- **Stale duplicate of the fixed bug.** `file-tree.tsx:339-346` `extractFolderFromFile`
  still reads `File.path` directly and does *not* use `getPathForFile` (it isn't even
  imported there — line 8 imports only `isElectron, pickFolder`). It's unreachable under
  Electron (the `isElectron()` short-circuit) but is the exact same defect CR flagged in
  `drop-zone.tsx` — fixed there, left stale here.
- **The `webkitdirectory` input is near-unreachable.** In Chromium `showDirectoryPicker`
  exists, so branch 2 runs and branch 3's input is never clicked; in Firefox/Safari it's
  reached but still fails. Either way it produces a broken "pick a folder → nothing
  happens" experience.
- The `showDirectoryPicker` loop only inspects the **first** file then `break`s — a
  second flaw independent of the path problem.

Net: the "Open Folder" button is functional **only** under Electron. In the browser build
it reduces to "manually type an absolute path", wrapped in UI that implies a working
native picker.

---

## 4. `/api/find-file` — heuristic limits (finding #2, still present)

`app/api/find-file/route.ts` searches: last-known folder → project dir → common user
folders → all drives **two levels deep**, matching **filename + size only**.

Consequences:

- A file deeper than 2 levels from a drive root is **never found** (unless it happens to
  be in `lastFolder` / project dir / `Pictures` / `Desktop` / `Downloads` / `Documents`).
- **name+size matching can select the wrong folder** on duplicates.
- The route does **not** check `request.signal`, so a client abort (the 8s timeout in
  `app/page.tsx:173`) doesn't actually stop the server scan — it just stops listening.

This is a best-effort *guess* for dropped files in the browser (where no path is
available). It's inherently unreliable and can't be fixed by a longer timeout.

---

## 5. Direction (planning only — no dev)

**Correction (owner):** the browser picker *already opens*. The failure is that the
selected folder's data never loads — the app can't turn the handle into a `currentFolder`
so it silently falls back to the manual editor. The goal is therefore **not** to remove
the picker; it's to make picking a folder actually load the files. That is **Option B —
client-side handle traversal.**

**B. Client-side handle traversal (the direction).** Keep `showDirectoryPicker()`; walk
the returned `FileSystemDirectoryHandle` client-side to build the tree, and load each
image through the handle rather than through `/api/fs`. Concretely:

- **Tree listing** — a client-side recursive walk of the handle (`entries()` →
  `FileSystemDirectoryHandle` / `FileSystemFileHandle`), producing the same `FsItem[]`
  shape the tree already renders. No `/api/fs` for the browser case.
- **Metadata** — for a selected file, `fileHandle.getFile()` → `File`, then `POST` the
  bytes to the existing `/api/metadata-from-file` (already built for exactly this — parses
  an in-memory `File`). Reuse as-is.
- **Preview** — `URL.createObjectURL(await fileHandle.getFile())` for a quick win; the
  "proper" version downscales with `createImageBitmap(..., { resizeWidth/Height })` →
  canvas → blob to avoid decoding full-res images per tile. (Same tiered-thumbnail idea as
  the server `/api/thumbnail`, but client-side since there's no path.)
- **Folder-persistence** — optional later: store the handle in IndexedDB so a re-picked
  folder can re-request permission without re-browsing.

This is a real change (the browser case abandons server-side listing), but it reuses two
existing pieces: the `FsItem[]` tree renderer and `/api/metadata-from-file`.

**A. Manual-path editor (kept as a fallback, not the goal).** The typed/pasted absolute
path works today in the local build and remains useful. It just shouldn't be the *only*
thing the button produces in a browser.

**C. Browser = single-image (unchanged context).** The hosted demo stays single-image;
that's fine. The local browser build is where B matters.

**Recommendation:** B, scoped to the browser branch only. Electron keeps its native
`pickFolder` path (already working). Implement B in small steps: (1) handle → tree
listing, (2) handle → metadata via the existing route, (3) client-side thumbnails, (4,
optional) IndexedDB persistence.

---

## 6. Not done here

No code changed. The reproduction is already clear (picker opens, data doesn't load —
branch 2 in §3). Next step, when ready, is the smallest slice of B: walk the handle and
render the root listing, leaving metadata/preview on the existing paths.
