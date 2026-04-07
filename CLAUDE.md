# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Image Metadata Viewer & Analyzer built with **Next.js 16** (App Router), **React 19**, and **TypeScript 5**. Parses and displays AI image generation metadata (EXIF, IPTC, XMP) with specialized support for A1111/Forge, ComfyUI, NovelAI, and Civitai formats. Originally generated via v0.app, deployed on Vercel.

## Commands

```bash
npm install        # Install dependencies
npm run dev        # Dev server on localhost:3000
npm run build      # Production build (TS errors ignored via next.config.mjs)
npm run lint       # ESLint
npm start          # Start production server
```

No test framework is configured.

## Architecture

**Client-Server split:** React client components (`"use client"`) communicate with Next.js API routes.

**Data flow:** FileTree → `/api/fs` (list directories) → user selects image → `/api/metadata` (extract metadata) → MetadataPanel displays results. Images served via `/api/image`.

**API Routes** (`app/api/`):
- `fs/` — Directory listing with traversal prevention
- `metadata/` — Core metadata extraction (PNG chunks, JPEG EXIF, AI-specific formats)
- `image/` — File serving with MIME detection
- `rules/` — Conditional metadata rule evaluation
- `civitai/` — Civitai API integration
- `comfyui-nodes/` — ComfyUI node registry lookup (classifies nodes via extension-node-map.json)
- `health/` — Health check

**Key Components** (`components/`):
- `navbar.tsx` — Top nav with view mode toggle
- `file-tree.tsx` — Recursive lazy-loading directory browser
- `metadata-panel.tsx` — Tabbed metadata display (basic/exif/iptc/xmp/ai/rules)
- `image-preview.tsx` — Viewer with zoom (25-400%), rotation, fit controls

**Metadata Parsing** (`app/api/metadata/route.ts`):
- PNG: tEXt/iTXt chunk parsing for A1111, ComfyUI (JSON workflow with node resolution), NovelAI
- JPEG: EXIF via exif-parser, Civitai UTF-16-LE UserComment, A1111 in EXIF
- Security: all file access validated against project root with `path.resolve()`

## Tech Stack

- **UI:** shadcn/ui + Radix UI primitives, Lucide icons, Framer Motion
- **Styling:** Tailwind CSS v4 with OKLch CSS variables, dark mode support. Use `cn()` from `lib/utils.ts` for class merging.
- **Forms:** react-hook-form + zod validation
- **Path alias:** `@/*` maps to project root

## Conventions

- Components: PascalCase. Files: kebab-case. Client components must have `"use client"` directive.
- Types live in `types/` (metadata.ts, fs.ts, rules.ts). Hooks in `hooks/`.
- TypeScript strict mode is on, but build ignores TS errors (`ignoreBuildErrors: true`).
- `doras-ui` clipboard component is used for prompt copy/paste in the metadata panel.

## ComfyUI Node Registry

`lib/comfyui-node-registry.ts` provides node class_type → repo lookup using ComfyUI-Manager's
extension-node-map.json. The metadata extraction route (`app/api/metadata/route.ts`) uses muted
node filtering, forward conditioning trace, AI prompt enhancer detection, and ControlNet detection.

### Phase 2: GitHub search fallback

`lib/comfyui-github-search.ts` adds an opt-in fallback that searches GitHub code for unknown
class_types via `NODE_CLASS_MAPPINGS` references in Python files. Enable per-call with
`{ useGitHubFallback: true }` on `lookupNode`/`classifyNodes`, or via `?github=true` /
`useGitHubFallback: true` on the `/api/comfyui-nodes` route.

- **Token**: requires `GITHUB_TOKEN` in `.env.local` (configurable from the Settings page).
  Only needs `public_repo` scope.
- **Cache**: persistent JSON at `.cache/comfyui-github-search.json` (gitignored). Hits live
  for 7 days, misses for 1 day.
- **Throttle**: ~28 req/min ceiling (GitHub authenticated code search limit is 30/min).
- **Result tagging**: GitHub-resolved nodes carry `source: 'github'` so the UI can flag them
  as best-effort guesses rather than authoritative matches.

### Future phases (not yet implemented)
- **Data-grid / Kibo UI**: A spreadsheet-style data grid was evaluated for tabular metadata viewing.
  Removed in cleanup but could be reinstalled from [Kibo UI](https://kiboui.com) when a table/grid
  view of metadata is needed.
- **ComfyUI local scanner**: Port of `comfyui_scanner.py` + `static_node_analyzer.py` to catch
  niche custom nodes not in the extension-node-map. Depends on settings UI for ComfyUI path config.
- **Node Finder origin**: The ComfyUI node lookup is a Node.js port of
  [Ktiseos-Nyx/ComfyUI-Node-Finder](https://github.com/Ktiseos-Nyx/ComfyUI-Node-Finder) (Python).
