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
- Multiple UI component registries exist in `components/` (doras-ui, kibo-ui, systaliko-ui) — these are demo/experimental.
