# Theme & Appearance System — Consolidation Plan

**Status:** Design draft — not started
**Date:** 2026-10-06

---

## 1. Context & Goal

Dataset-Tools already has dark/light mode (via `next-themes`) and an accent-color
picker (via a `data-accent` attribute read by `app/globals.css`). Both work, but the
theme *state* is split across three places that have drifted apart, and one path is
dead. The goal here is **not** new visual features — it's to consolidate what exists
into one model with one apply path, so the next appearance feature (there are a few
candidates, see §7) lands on solid ground instead of a fourth parallel store.

Non-goals are in §6.

---

## 2. Current state — the problem

### 2.1 Three stores for one concern

| Store | Holds | Writes |
|---|---|---|
| `next-themes` (`theme`) | light / dark / system (`dark` class on `<html>`) | `localStorage` (next-themes) |
| `app-settings` → `useSettings()` | `theme` (duplicate) + `accentColor` | `localStorage['app-settings']` |
| `theme-customizer.tsx` | `data-theme-color` + a stray `theme-color` key | `localStorage['theme-color']` |

`navbar.tsx:104-105` mirrors every theme change into **both** next-themes and
`app-settings`, so `theme` is stored twice. That's the drift risk: two sources can
disagree after any future edit.

### 2.2 The accent color is wired twice, with mismatched attributes

- `layout.tsx:53-60` (pre-hydration script) and `navbar.tsx:87-89,191` write
  `document.documentElement.setAttribute('data-accent', …)`.
- `app/globals.css:122-276` reads **`[data-accent="…"]`** (plus `.dark` variants).
- But `theme-customizer.tsx:34,40` writes **`data-theme-color`** and
  `localStorage['theme-color']` — an attribute no CSS reads.

Result: the `ThemeCustomizer*` color dots (`Pill`, `Bar`, `Sidebar`, `Dock`, `Corner`,
`Toolbar`) are dead. They set an attribute nothing consumes. They're also unused in the
app — only `docs/ui-inventory.md` references them.

### 2.3 Hand-picked contrast, repeated

Each accent has its own `--primary-foreground` (and friends) hardcoded in two variants
(`[data-accent]` + `.dark[data-accent]`): 7 colors × ~2 blocks. That's a maintenance
surface where a bad pick silently fails contrast.

---

## 3. Design principles (generic, not project-specific)

1. **One source of truth.** Appearance state (`theme` + `accentColor`) lives in a
   single store. Everything else derives from it.
2. **Themes as data.** A theme/accent is a palette object; applying it is one function
   that writes CSS variables to `document.documentElement`. No per-color component logic.
3. **Derived contrast.** Foreground-on-accent is computed from measured luminance
   (WCAG relative luminance), not hand-picked per color.
4. **No flash on load.** The persisted palette is replayed before first paint, so the
   first frame is correct in every mode.

---

## 4. Proposed design

### 4.1 Single owner

Keep `next-themes` as the light/dark/system *mechanism* (it's idiomatic for Next.js and
already handles the `dark` class + `suppressHydrationWarning`). Make `app-settings` the
single owner of **`theme` + `accentColor`**, and drop the `navbar.tsx:104-105` duplicate
write. Concretely: one direction of truth.

- `useSettings()` holds `{ theme, accentColor }`.
- Theme changes go through `updateSettings({ theme })`; a small effect syncs that value
  to `next-themes`' `setTheme` (single-direction), or vice versa — **decide in §8.1**.
- Accent changes go through `updateSettings({ accentColor })` only.

### 4.2 One apply function

`lib/theme.ts` — `applyAppearance({ theme, accentColor })`:

- sets the `dark` class (or leaves it to next-themes),
- sets `data-accent`,
- writes the accent's `--primary` / `--ring` / `--accent` etc. to the root.

This replaces the scattered `setAttribute` calls in `navbar.tsx` and `layout.tsx`. It
is the single path the pre-hydration script and the runtime both call.

### 4.3 Derived contrast tokens

Compute `--primary-foreground` (and `--accent-foreground`, `--ring` contrast where
needed) from `--primary`'s luminance at apply time. Collapses the ~14 hardcoded accent
blocks in `app/globals.css:122-276` to:

```css
[data-accent] { --primary: var(--accent-raw); }
/* foreground computed in JS, written as a var */
```

Exact token list TBD — the point is: contrast is math, not memory.

### 4.4 Complete the pre-paint script

`layout.tsx:53-60` already replays `accentColor`. Extend it to replay `theme` too (set
the `dark` class before hydration) so the first frame is correct in every mode — no
more one-frame flash of the wrong accent/mode.

### 4.5 Cleanup

- Delete `components/ui/theme-customizer.tsx` (dead, and its wiring is wrong) or fix it
  to call `applyAppearance` and write `data-accent`. **Decision in §8.2.**
- Remove the stray `localStorage['theme-color']` path.
- Remove `components/ui/theme-toggle.tsx` / `theme-switch.tsx` if they duplicate the
  navbar picker — confirm they're still used first.

---

## 5. Build order

| Step | Deliverable | Independent? |
|---|---|---|
| 0 | Decide §8.1 + §8.2 | — |
| 1 | `lib/theme.ts` apply function + luminance helper | yes |
| 2 | Point `navbar.tsx` + `layout.tsx` at it; drop duplicate writes | yes |
| 3 | Derive `--primary-foreground`; collapse accent CSS blocks | yes |
| 4 | Extend pre-hydration script to theme + accent | yes |
| 5 | Cleanup dead customizer path | last (verifies nothing regressed) |

Each step is a small, reviewable change; none blocks metadata parsing or the Civitai /
ComfyUI work.

---

## 6. Non-goals (explicitly out of scope)

- **No card/dex system.** No classes, tags, stamps, prompt versions, or card grids.
  This is a metadata viewer, not a look tracker.
- **No full-material reskin engine.** No texture patterns, per-surface backgrounds,
  corner-shape languages, or 12 hand-tuned "world" themes. Appearance stays
  light/dark + accent.
- **No draggable color picker** (and therefore no two-lane debounced apply). Discrete
  swatches don't need it.
- **No per-user theming server.** Settings stay client-local as they are today.

---

## 7. Candidate appearance/UX features (TBD)

Placeholder for the other ideas under consideration. To be filled in; each gets its own
doc or a section here once decided. Currently open:

- Help-text toggle for dense settings (explanatory paragraphs, off by default).
- Settings CANCEL / rollback (live apply + snapshot + revert) for the settings sheet.
- Reassignable two-key shortcuts.
- Cross-modal feedback toasts (feedback that renders above an open modal).

*None of these are committed yet.*

> **Related:** organization/search lives in its own doc —
> [`docs/2026-10-06-tagging-and-search.md`](./2026-10-06-tagging-and-search.md).

## 7.1 Duplicate thumbnail locations (research)

The current layout shows the *same* folder's images as thumbnails in **two places**:

- the **bottom thumbnail box** (`ThumbnailViewport`, `app/page.tsx:283`) — the filmstrip
  under the preview, which the owner loves, and
- the **sidebar thumbnail grid** (`file-tree.tsx` `ThumbnailGrid`, only when
  `viewMode === "thumbnail"`).

Both render `/api/thumbnail` for the same directory. Open questions to settle later:

- Is the sidebar grid redundant when the bottom box is present, or do they serve
  different jobs (tree-navigation vs. quick-filmstrip)?
- If redundant, remove the sidebar grid / make it a toggle, or keep both but make the
  sidebar one opt-in.
- Does "thumbnail view" as a mode still earn its keep next to the always-on filmstrip?

*Feeling is unresolved ("the bottom box is amazing… but we don't always want the
sidebar one") — capture the decision here when it lands, don't build either way yet.*

---

## 8. Open questions

1. **Ownership direction** — should `app-settings` drive next-themes, or next-themes
   drive `app-settings`? (Recommend: app-settings is the owner; next-themes is the DOM
   mechanism.)
2. **`theme-customizer.tsx`** — delete (recommended, it's dead + broken) or repair it
   to write `data-accent` and call the apply function?
3. **Token scope** — which shadcn tokens should be derived by luminance vs. left
   hand-authored (`--primary-foreground`, `--accent-foreground`, `--ring`, …)?
