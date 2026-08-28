# UI Component Inventory

> Snapshot of what's under `components/` — which pieces are true shadcn/ui, which are custom. Reference for future UI decisions.

## Current state (after 2026-08-28 cleanup)

The app now runs on a single system: **shadcn/ui on Radix UI**. All third-party component libraries that had been pulled in and never used were deleted.

- **shadcn/ui** = a *collection* of copy-paste components (NOT a primitive); it builds on **Radix UI** (`@radix-ui/react-*`, plus the unified `radix-ui` meta-package).
- **Base UI** (`@base-ui/react`) and **Optics** (`github.com/AgusMayol/optics`, a Base UI-based collection) were removed along with `@base-ui/react`.

Third-party registries remain configured in `components.json` (incl. `@optics`, `@kokonutui`, `@uitripled`, and ~14 others), so any of them can be re-added later with `shadcn add`.

## A. shadcn/ui registry components (Radix + Tailwind)

`accordion`, `alert-dialog`, `aspect-ratio`, `badge`, `breadcrumb`, `button`, `calendar`, `card`, `checkbox`, `collapsible`, `command`, `context-menu`, `dialog`, `drawer`, `dropdown-menu`, `empty`, `hover-card`, `input`, `kbd`, `popover`, `scroll-area`, `select`, `separator`, `sheet`, `skeleton`, `sonner`, `table`, `tabs`, `textarea`, `tooltip`.

## B. Composed / template components (not primitives)

`vercel-tabs`, `vercel-card`, `transition-panel`, `theme-customizer`, `theme-switch`, `theme-toggle`, `responsive-dialog`.

## C. Custom / decorative (project-specific)

`smooth-cursor`, `particles`, `glowing-effect`, `glowingbordercard`, `github-star`, `layout-grid`, `loader`, `markdown`, `code-block`, `status`, `sortable-list`, `color-swatch`, `color-swatch-selector`, `not-found`, `seperatorpro`, `direction`.

## App-level components (`components/*.tsx`)

Hand-rolled feature components: `file-tree`, `drop-zone`, `file-dropzone`, `image-preview`, `image-upload`, `thumbnail-viewport`, `metadata-panel`, `metadata-viewer`, `metadata-edit-dialog`, `safetensors-panel`, `ComfyUIWorkflowViewer`, `navbar`, `infinite-list`, `tags-input`, `hitbox`, `glass-popover`, `glass-notification`, `action-hint`, `theme-provider`.

`components/animate-ui/icons/brush-cleaning` is the only remaining third-party pull — used by `ui/theme-customizer.tsx`.

## Removed (2026-08-28, all unimported)

- `components/optics/` (Base UI button + tooltip)
- `components/kokonutui/` (AI loading spinners)
- `components/doras-ui/` (single `clipboard.tsx`)
- `components/chat/` (`chat-tool.tsx`)
- `components/uitripled/` (shadcn "browse folder"/"gallery grid" blocks)
- `components/ui/{select,separator,navigation-menu,toolbar}/` (Base UI hand-wrappers)
- `@base-ui/react` dependency

## Notes for later

- **Decorative leftovers** (smooth-cursor, particles, glowing-*, layout-grid, github-star) may be unwired — worth a usage grep before assuming they're load-bearing.
- **Registries** in `components.json` are intentionally kept so future components can be pulled with `shadcn add <registry>/<name>`.
