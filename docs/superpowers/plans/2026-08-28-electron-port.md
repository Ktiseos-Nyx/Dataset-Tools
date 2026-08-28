# Electron Port + Pre-Port UI Plan

> **Status:** IN PROGRESS — A1/A3/A6 + B1 scaffold done; packaged build + B2/B3/B4/B5 pending.

## Implementation status (2026-08-28)

- ✅ **A1** — `lib/electron-bridge.ts` (typed `window.electronAPI` seam, `isElectron()`/`pickFolder()`), wired into `file-tree.tsx` `handleOpenFolder` (native dialog first, browser fallbacks unchanged).
- ✅ **A3** — `app/api/settings/route.ts` + `lib/comfyui-github-search.ts` route `settings.json`/`.env.local`/`.cache` through `process.env.ELECTRON_USER_DATA` when set. (Also applied to `app/api/thumbnail/route.ts` `.thumbcache`.)
- ✅ **A6** — "Open a folder" CTA in the empty state (`file-tree.tsx`).
- ✅ **A2** — removed orphaned `app/settings/page.tsx` (unreachable duplicate of the navbar sheet); navbar sheet is the single settings surface.
- 📌 **A4** — already satisfied: `currentFolder` is in `AppSettings` and persisted to `localStorage`, so the folder is remembered across launches. Remaining option is a *recent-folders* list (visual-pass enhancement).
- 📌 **A5/A7** — enhancements, not fixes: A5 is already native titlebar (recommended default); A7 breadcrumbs are an optional upgrade over the text path input. Both are Dusk's visual-pass call.
- ✅ **B1 (scaffold)** — `electron/{main,preload,tsconfig}`, `electron-builder.yml`, `package.json` scripts (`electron:compile/dev/start/build`, `main` field). Compiles + lints clean.
- ⏳ **B1 (packaged verify)** — needs a real `next build` + electron-builder run + icons; sharp native module to confirm under `asar:false`.
- ⏳ **B2/B3/B4/B5** — pending.

### Key decisions made
- **`asar: false`** in `electron-builder.yml` — keeps `node_modules` (sharp native binary) + `.next` as real files so `next start` works without asar-unpack fiddling.
- **`ELECTRON_RUN_AS_NODE`** — packaged app spawns the bundled `next` CLI through Electron's own Node runtime (`process.execPath`), no system node/npx required.
- **Dev workflow** (`electron:dev`) runs `next dev` separately and points Electron at `localhost:3000`; packaged mode spawns `next start` on a free port. Added `electron:start` (`electron . --self-serve`) to test the shell against a one-time `next build` — no Turbopack watcher, near-zero steady-state I/O (avoids `next dev` drive churn).
- **UI inventory** written to `docs/ui-inventory.md` (two competing primitive systems: shadcn/Radix vs `@base-ui/react`).

## Decision log (context)

- **Electron over Tauri** is settled. The entire metadata backend is Node.js (`app/api/metadata/route.ts` ~2000 lines + `sharp` + `exif-parser` + ComfyUI node registry + GitHub search). Electron runs it unchanged; Tauri would require a Rust port of the parser (feasible — ~2-4 weeks for the parsing layer alone — but pointless when Electron ships it for free).
- **Vercel/Web demo** stays path-less (drag-drop per image via `/api/metadata-from-file`). It can never see the local filesystem — that's fine and out of scope for this plan.
- **Python/PyQt6 branch** remains the non-Chromium alternative — fixed later, not part of this plan.

## Distribution matrix

| Platform | Channel | Notes |
|---|---|---|
| **Windows** | Electron GUI `.exe` (NSIS installer) | Primary target — Dusk is on it. |
| **macOS** | CLI via **Homebrew formula** (no `.app`) | No Gatekeeper, no Apple signing/notarization ($99/yr). Mirrors the PyPI edition. |
| **Linux** | AppImage GUI + the same CLI | AppImage via electron-builder; CLI alongside. |

- **macOS is deprioritized** ("out for now"): Apple's signing + Gatekeeper make an unsigned GUI `.app`/`.dmg` not worth it. The CLI-via-Homebrew path dodges all of it — no `.app` bundle, and Node itself is already signed, so Gatekeeper never triggers.
- **CLI prerequisite:** the parser currently *is* the Next.js route (`extractMetadataFromBuffer` + helpers in `app/api/metadata/route.ts`). A CLI means extracting that into a reusable module (`lib/metadata/`) with a thin `bin` entry — one parser shared by web + Electron + CLI. The parser is pure JS (no `sharp` — sharp only lives in the thumbnail route), so a CLI has zero native deps.

---

## Part A — Pre-port UI "rejig" decisions

These are **not required** for Electron to work — they're things worth thinking through *now* because they shape how the port lands. Dusk owns UX calls (per standing split); items A1/A3 are plumbing I own and will just do.

### A1. Folder-picker seam — `window.electronAPI` bridge ✅ (plumbing, do now)

**Current:** `components/file-tree.tsx:347-394` tries three fallbacks inline: `showDirectoryPicker()` → hidden `<input webkitdirectory>` → path editor. In a browser none of the first two yield an absolute path, so it always lands on the editor — this *is* bug #211.

**Rejig:** one clean seam — a `pickFolder()` helper that checks `window.electronAPI` first (native `dialog.showOpenDialog`), else falls back to the current browser behavior. The UI doesn't care which backend answered.

**Why now:** it's the #211 fix and gives the renderer a single capability surface to grow on (folder pick, save dialog, etc.).

### A2. Duplicate settings surfaces — consolidate

**Current:** two settings UIs exist — the navbar `Sheet` (`components/navbar.tsx:70` `SettingsContent`) *and* a full `app/settings/page.tsx`. They overlap (both hit `/api/settings`).

**Options:** (a) keep the sheet, drop the page; (b) keep the page, make the navbar button a link; (c) keep both but split responsibilities.

**Recommendation:** pick one canonical surface before the port so Electron doesn't have to maintain two.

### A3. Settings storage model — 3 stores → 1 story

**Current:** settings live in three places:
- `localStorage` key `app-settings` (client prefs: `currentFolder`, theme, sort, etc.) — works in Electron automatically.
- `.env.local` (secrets: `CIVITAI_API_KEY`, `GITHUB_TOKEN`) — **breaks** in packaged app (read-only install dir).
- `.cache/comfyui-github-search.json` — **breaks** in packaged app.

**Rejig:** route secrets + cache + `settings.json` through `app.getPath('userData')` under Electron (env var hand-off, as in the old plan's Task 9). UI copy change: "Key is saved in .env.local" → "Stored securely in app data" (`navbar.tsx:305,351`).

### A4. Session restore / last-folder memory — UX decision

**Current:** `currentFolder` defaults to `.` (project root); no memory across launches.

**Options:** (a) restore last-opened folder on launch; (b) add a recent-folders list in the open-folder menu; (c) leave as-is (start blank each time).

**Recommendation:** (a) is the expected desktop behavior and is nearly free once storage is in userData.

### A5. Window chrome — native vs frameless titlebar

**Current:** default OS titlebar + an in-app `navbar.tsx` (Browse / Settings). The white title bar strip is annoying because the OS titlebar follows Windows' light theme, not the app's dark theme.

**Not a shadcn/ui concern:** window controls / title bars are Electron-level, not UI-library primitives — shadcn has no titlebar/window-chrome component. So any custom titlebar is either Electron's built-in API or an Electron library (styled with our Tailwind tokens). Nothing in shadcn applies here.

**Options:**
1. **`titleBarStyle: 'hidden'` + `titleBarOverlay`** (built-in) — hides the white strip but keeps the *real native* min/max/close buttons, colored to match theme. Zero deps. Downside: overlay color is set at launch, so a light/dark toggle needs a theme-change IPC to re-color it.
2. **`custom-electron-titlebar`** (~900★, MIT) — VS Code-style custom bar with menu, min/max/close, drag, themeable via JSON. Needs `sandbox: false`. "Option 3, pre-built."
3. **`frame: false`** (fully frameless) — rebuild all controls + drag region ourselves. Most control, most work.

**Recommendation:** start with option 1 (native feel, matches theme, no deps); layer `custom-electron-titlebar` on later only if a menu bar is wanted.

### A6. First-run / empty-state onboarding

**Current:** `Empty` component shows "No images found" when `rootItems` is empty (`file-tree.tsx:479-486`). In Electron first run, the user sees a dead-end with no hint.

**Rejig:** a prominent "Open a folder…" CTA in the empty state (which also exercises A1).

### A7. Path display — breadcrumbs vs text input

**Current:** an editable text input in the tree header (`file-tree.tsx:412-425`). ROADMAP already lists breadcrumbs as a want.

**Options:** (a) keep text input; (b) clickable breadcrumb segments; (c) breadcrumbs + "edit on click".

**Recommendation:** defer — not port-blocking, but note it's the natural companion to A4.

---

## Part B — Backend / Electron work (mine)

### B1. Native folder picker + IPC bridge — fixes #211
- `electron/main.ts`: `ipcMain.handle('pick-folder')` → `dialog.showOpenDialog({ properties: ['openDirectory'] })` → return real absolute path.
- `electron/preload.ts`: `contextBridge.exposeInMainWorld('electronAPI', { pickFolder })`.
- Renderer: `pickFolder()` seam (A1) consumes it, feeds `settings.currentFolder`.

### B2. userData migration
- Main process sets `process.env.ELECTRON_USER_DATA = app.getPath('userData')` before spawning Next.
- `/api/settings` writes secrets + config there when the env var is present.
- `lib/comfyui-github-search.ts` writes its cache there.

### B3. Production build — standalone + random port
- Improve on the old plan (`next start` on fixed 3000): use `output: 'standalone'` in `next.config.mjs`, spawn the standalone server on a free port (or fixed if we control it), no `npx`/`node_modules` resolution at runtime → faster cold start, smaller bundle.

### B4. electron-builder packaging + icons
- Carry over from the old plan (Tasks 5/7): `electron-builder.yml`, NSIS/dmg/AppImage targets, icons.

### B5. Optional — file watching (chokidar)
- Auto-refresh the tree when files change on disk. Nice desktop-only win; not required for v1.

---

## Sequencing

1. **Decide Part A** (A2/A4/A5/A6/A7) — Dusk.
2. **A1 + A3 + B1 + B2** (plumbing) — assistant.
3. **Greenlit A-items** (UI) — Dusk/assistant per split.
4. **B3 + B4** — ship a test installer, then iterate.
5. **B5 + A7** — post-v1 polish.

## Open questions for Dusk
- Which A-items to do now vs defer? (recommend: A1/A3/A6 now; A2/A4/A5/A7 later)
- Icon asset source?
- Code-signing posture (per old plan Task 8 — skip until public release)?
