# Project instructions — Dataset-Tools

Companion to the global `~/.config/opencode/AGENTS.md` (personality + universal rules, loaded first).
OpenCode combines both files every session — this file only adds project-specific facts. Never
duplicate or contradict the global file here.

## What this is

Image/dataset metadata tooling: a Next.js app (web) with an Electron shell that packages it as a
desktop app. Status and planning docs live in `BETA_PLANNING.md` and `README.md`.

## Teaching mode — OFF for this project

Dataset-Tools is NOT the teaching repository. It is deep in development; walkthroughs,
comprehension checks ("explain it back"), and manual steps for Dusk slow things down here and are
not the default. Default to execution mode: do the work directly, keep explanations short and only
where a decision genuinely needs Dusk's input. Switch to Teaching Mode on the spot if Dusk asks how
something works — but don't force it otherwise.

The designated teaching repository is the Tales of Osea website repo — the global Teaching Mode
rules apply THERE, not here.

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
  standalone bundle. Don't loosen it. NOTE: excludes do NOT stop Next's own unconditional
  `.env`/`.env.production` copy into standalone (build/index.js `writeStandaloneDirectory`) — the
  postbuild scrub in `scripts/copy-standalone-assets.mjs` is the gate for env files; both layers
  must stay.

## Package.json

- The `overrides` block is Dusk's deliberate security control surface — exact pins are intentional,
  not stale housekeeping. Never touch it without the global-rule approval flow.
- `zod` is transitive-only (pulled by `eslint-plugin-react-hooks` via `eslint-config-next`). We
  removed it plus unused `react-hook-form` / `@hookform/resolvers` in Oct 2026 to clear a zod
  advisory. Don't re-add them unless deliberately adopting them in code.
- `eslint` stays on v9 — v10 exists but `eslint-config-next`'s plugin chain does not support it yet;
  the "deprecated" npm warning is cosmetic.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
