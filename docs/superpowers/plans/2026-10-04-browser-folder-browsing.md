# Browser-Native Folder Browsing (Web Build) — Plan

**Status:** Spec — not yet implemented
**Date:** 2026-10-04
**Tracking issue:** [#220](https://github.com/Ktiseos-Nyx/Dataset-Tools/issues/220)

---

## 1. Context & Problem

The web build (Vercel demo + self-hosted `npm start`) is **path-less by design**:
single-file drag-drop → `/api/metadata-from-file` (bytes in, metadata out). Folder
*browsing* is a desktop feature — Electron's native dialog returns a real absolute
path that `/api/fs` can list.

Two concrete symptoms surfaced this:

1. **The "Open folder" button half-works in browsers.** `showDirectoryPicker()`
   opens and the user grants permission, but `handleOpenFolder`
   (`components/file-tree.tsx`) then reaches for `file.path` — an Electron-only
   property that is `undefined` in Chromium — so `extractFolderFromFile` returns
   `null` and the flow dead-ends into the path editor. The browser hands back a
   `FileSystemDirectoryHandle` (full read access), which the code ignores.

2. **Drag-drop auto-detect is slow/flaky.** `/api/find-file` scans every drive two
   levels deep (~10.7s worst case), while the client aborts at 8s
   (`app/page.tsx`). Files in `Pictures`/`Desktop`/`Downloads`/`Documents` resolve
   instantly; elsewhere the scan *may* complete in time or time out, so the folder
   loads inconsistently.

Neither is a security regression — they predate the recent CSP / egress-allowlist
work — but they are the reason folder browsing feels broken in a browser.

---

## 2. Goal

Make folder browsing genuinely work in Chromium browsers by reading folders
**client-side through the `FileSystemDirectoryHandle`** the browser already grants
— no absolute path string anywhere. Electron keeps its current path-based flow
untouched (it works there).

---

## 3. Design

Add a **browser folder source** that runs parallel to the existing path-based source.

- **Pick:** `showDirectoryPicker()` → `FileSystemDirectoryHandle`.
- **List:** `handle.values()` → immediate children (files + subdirectory handles).
- **Navigate:** a subdirectory returns its own handle; keep a stack / tree of handles.
- **Open file:** `entry.getFile()` → `file.arrayBuffer()` → POST `/api/metadata-from-file`
  (route already exists and accepts bytes).
- **Thumbnails:** read bytes → `URL.createObjectURL` (or `blob:`), or add a
  bytes→thumbnail server endpoint if object URLs are too heavy.
- **Drag-drop:** optionally `DataTransferItem.webkitGetAsEntry()` to accept a
  dropped *folder* the same way.

The app's current model is `settings.currentFolder: string` (a path). Browser mode
needs a parallel representation — a root handle + an in-memory tree — rather than
trying to coerce a handle into a path string.

---

## 4. Architecture

Introduce a **folder-source abstraction** so the file tree can be driven by either:

| Source | Root | List | Open |
|---|---|---|---|
| **Path (Electron)** | `currentFolder: string` | `/api/fs?baseFolder=` | `/api/metadata?path=` |
| **Browser (new)** | `FileSystemDirectoryHandle` | `handle.values()` | `/api/metadata-from-file` (bytes) |

The `Directory`/`File` tree components currently navigate by `item.path`. Browser
mode replaces that with handle references. This is the bulk of the work — it's why
this is a feature, not a one-line change.

---

## 5. Scope

### MVP (working, shippable)
- Pick a folder → list top level + drill into subfolders
- Click a file → metadata via `/api/metadata-from-file`
- Basic thumbnails via object URLs
- Clear "browser mode" affordance (and the manual path entry stays for local
  `npm start`)

### Full parity (later)
- Sort, auto-refresh, recursive lazy-loading at scale
- Handle persistence across reloads (IndexedDB + re-requested permission)
- Folder-aware drag-drop (`webkitGetAsEntry`)

---

## 6. Open questions

1. **Handle persistence** — `FileSystemDirectoryHandle` isn't persistable without
   storing it in IndexedDB *and* re-requesting permission each session. Is
   re-picking each session acceptable for MVP? (Recommend: yes.)
2. **Thumbnails** — object URLs vs a new bytes→thumbnail endpoint. Object URLs are
   simplest; large folders may want the server path.
3. **`find-file` in browser mode** — auto-detect-from-drop can't work by path in a
   browser. Does browser mode replace it (handle-based), or do we keep the server
   scan as a local-only nicety?

---

## 7. Out of scope

- Electron changes (works today).
- Downloading / the ArcEnCiel download system.
- The recent security work (CSP, egress allowlist, watch) — unrelated.

---

## 8. Rollout

| Phase | Deliverable |
|---|---|
| 0 | Confirm MVP scope + handle-persistence approach (open questions above) |
| 1 | Folder-source abstraction; browser `FileSystemDirectoryHandle` traversal |
| 2 | Wire file tree + `/api/metadata-from-file` + object-URL thumbnails |
| 3 | Polish: sort, refresh, persistence, folder-aware drag-drop |
