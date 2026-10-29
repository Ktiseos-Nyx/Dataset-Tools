# Project instructions — Dataset-Tools

Companion to the global `~/.config/opencode/AGENTS.md` (personality + universal rules, loaded first).
OpenCode combines both files every session — this file only adds project-specific facts. Never
duplicate or contradict the global file here.

## What this is

Image/dataset metadata tooling: a Next.js app (web) with an Electron shell that packages it as a
desktop app. Status and planning docs live in `BETA_PLANNING.md` and `README.md`.

## Running

- Default dev flow: `npm run dev` (or `npm run electron:dev` with the shell). Don't run
  `npm run build` / `npm start` unless explicitly testing a production build — the build compiles to
  `.next/`, and `next start` then serves stale output instead of the live dev server.
- The standalone server holds a lock on `.next/standalone`. Ask Dusk to stop any running server
  before a rebuild that touches `.next`, instead of killing his process.
- Dependency changes follow the global AGENTS.md rule: propose the exact command, wait for approval.

## Fragile zones — change deliberately, verify explicitly

- `app/api/metadata/route.ts` — one route parses PNG / JPEG / WebP with layered strategies (A1111,
  ComfyUI, NovelAI, CivitAI, EXIF, XMP, IPTC). "Small" edits can silently kill one layer while others
  still pass. After ANY change here, verify PNG Civitai extraction against a known-good image.
- `lib/safe-fetch.ts` — all outbound HTTP flows through this allowlist. A new external host must be
  added here AND to the renderer CSP in `next.config.mjs`, or it gets blocked (by design).
- `app/api/watch/route.ts` — Chokidar-based SSE file watching, server-side. Chokidar must stay
  BUNDLED (not in `serverExternalPackages`) — externalizing it broke its trace files before.
  `sharp` is the only externalized package.
- Electron packaging (`electron-builder.yml`): app code ships inside asar (fused), sharp + the
  standalone server ship via `extraResources` copying from `.next` with
  `filter: ["standalone/**/*"]` — copying `from: .next/standalone` directly silently drops the
  standalone's own `node_modules` (sharp's native binary vanishes).
- `next.config.mjs` → `outputFileTracingExcludes` keeps secrets (`.env*`, `.git`, etc.) out of the
  standalone bundle. Don't loosen it.

## Package.json

- The `overrides` block is Dusk's deliberate security control surface — exact pins are intentional,
  not stale housekeeping. Never touch it without the global-rule approval flow.
- `zod` is transitive-only (pulled by `eslint-plugin-react-hooks` via `eslint-config-next`). We
  removed it plus unused `react-hook-form` / `@hookform/resolvers` in Oct 2026 to clear a zod
  advisory. Don't re-add them unless deliberately adopting them in code.
- `eslint` stays on v9 — v10 exists but `eslint-config-next`'s plugin chain does not support it yet;
  the "deprecated" npm warning is cosmetic.
