# Dataset Tools: An AI Metadata Viewer

<div align="center">

<!-- Tech Stack & Status Badges -->
[![Built with NextJS](https://img.shields.io/badge/Built%20with-NextJS-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![Built with v0](https://img.shields.io/badge/Built%20with-v0.app-black?style=for-the-badge)](https://v0.app/chat/itQySJ65urb)

<!-- Social & Support Badges -->
[![GitHub](https://img.shields.io/badge/GitHub-View%20on%20GitHub-181717?logo=github&style=for-the-badge)](https://github.com/Ktiseos-Nyx/Dataset-Tools)
[![Discord](https://img.shields.io/discord/1024442483750490222?logo=discord&style=for-the-badge&color=5865F2)](https://discord.gg/HhBSvM9gBY)
[![Twitch](https://img.shields.io/badge/Twitch-Follow%20on%20Twitch-9146FF?logo=twitch&style=for-the-badge)](https://twitch.tv/duskfallcrew)
[![Support us on Ko-fi](https://img.shields.io/badge/Support%20us%20on-Ko--Fi-FF5E5B?style=for-the-badge&logo=kofi)](https://ko-fi.com/duskfallcrew)

<hr>

[English Readme](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/README.md) •
[Wiki](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki) •
[Discussions](https://github.com/Ktiseos-Nyx/Dataset-Tools/discussions) •
[Notices](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/NOTICE.md) •
[License](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/LICENSE)

</div>

---

**Dataset Tools NextJS Edition** is a **local-first web application** for browsing AI image datasets with comprehensive metadata extraction. Built from the ground up in TypeScript — no Python dependencies, no OpenCV duct tape, no NumPy startup tax. Running on Next.js 16, React 19, and shadcn/ui components.

### Why this exists
The Python edition worked at 65% success rate with heuristic spaghetti. This NextJS engine hits **90% success rate** on complex ComfyUI workflows using **deterministic graph traversal**. Metadata is parsed in pure JavaScript — no waiting for Python to boot, no OpenCV overhead.

> **Development Tool Warning**
> * **Run locally:** `npm run dev`
> * **Requirements:** Node.js 18+ and npm
> * **Status:** No public deployment. Local-only tool.

### Community-Driven Development
This project is inspired by [stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader) and thrives on community contributions. Found a bug? Have a workflow that won't parse? Want to add support for a new tool? **We welcome forks, fixes, and pull requests!**

---

<div align="center">

**Navigation**
[Features](#current-capabilities) • [Supported Formats](#supported-formats) • [Installation](#installation) • [Usage](#usage) • [Contributing](#contributing)

</div>

---

## Installation
**Clone repo**
```bash
git clone https://github.com/Ktiseos-Nyx/Dataset-Tools.git
cd Dataset-Tools
```
# Install dependencies (Node.js 18+ required)
```npm install```

# Start dev server
```npm run dev
```

For production:
```bash
npm run build && npm start
```

---

## Current Capabilities

| Feature | Status | Details |
| :--- | :---: | :--- |
| **Metadata Parsing** | ✅ | **90% success rate.** Graph-tracing engine for ComfyUI, field-based detection for A1111/Forge/NovelAI. |
| **Image Viewing** | ✅ | PNG, JPG, JPEG, WebP. Zoom (25-400%), rotation, fit-to-container. |
| **File Browsing** | ✅ | Recursive lazy-loading file tree. Browse any folder on your system. |
| **Drag & Drop** | ✅ | Drop an image to auto-detect its folder and extract metadata. |
| **Thumbnails** | ✅ | Sharp-powered WebP thumbnails with disk cache (`.thumbcache/`). |
| **Sorting** | ✅ | Sort by name, date modified, or file size. |
| **Accent Colors** | ✅ | 7 color themes (zinc, red, orange, green, blue, violet, pink) with dark mode support. |
| **WebP Metadata** | ⚠️ | Viewing works. Metadata extraction in development. |
| **ComfyUI Workflows** | ✅ | 3-phase extraction: field-based scan → graph trace → type-match fallback. Handles custom nodes, TensorArt wrappers, FLUX/SD3/SDXL. |

### Supported Formats
- **A1111 / Forge** — PNG tEXt chunks, JPEG EXIF
- **ComfyUI** — JSON workflow with node graph resolution
- **NovelAI** — PNG metadata
- **Civitai** — UTF-16-LE JPEG UserComment
- **Standard EXIF/IPTC/XMP** — All image formats

### Why 90% > 65% Matters
The Python edition relied on fragile heuristics. This engine uses **deterministic graph traversal** with proper node relationship mapping. It follows wires backwards from sampler nodes to find prompts, identifies nodes by their data (not just class_type), and handles platform-wrapped node names via substring matching. When it fails, logs show exactly why.

---

## Usage

1. **Start the app:** `npm run dev` → open `http://localhost:3000`
2. **Browse files:** Use the file tree sidebar, or click the folder icon to pick any directory.
3. **Drag & drop:** Drop an image anywhere in the app — it'll find the folder and load thumbnails.
4. **Inspect metadata:** Click any image → metadata panel shows prompts, parameters, LoRAs, and workflow info.
5. **Customize:** Settings panel has theme, accent colors, font size, thumbnail size, and file display options.

### When metadata fails to parse
1. Check browser console for parser logs.
2. Note the workflow structure (ComfyUI? A1111? Custom nodes?).
3. **File an issue with:**
   * Console error snippet
   * Workflow type + custom nodes used
   * Minimal repro image (if shareable)

---

## Contributing

### Found a parsing failure?
Open an issue with the details above. Real-world edge cases are how we push past 90%.

### Want to improve the parser?
1. Fork repo → `npm install` → `npm run dev`
2. Metadata extraction lives in `app/api/metadata/route.ts`
3. Test with images from the `Metadata Samples/` folder
4. Submit a PR with before/after evidence

### Ideas for contributors
- [ ] WebP metadata chunk parser
- [ ] Editable metadata (write back to files)
- [ ] SQLite indexing for faster folder browsing
- [ ] ComfyUI workflow visualization
- [ ] Batch metadata export (CSV/JSON)
- [ ] Parser debugger panel showing traversal steps

---

## Tech Stack

- **Framework:** Next.js 16 (App Router), React 19, TypeScript 5
- **UI:** shadcn/ui + Radix UI, Lucide icons, Tailwind CSS v4 (OKLch color space)
- **Thumbnails:** Sharp (libvips) with WebP disk caching
- **Metadata:** Pure JS parsing — PNG chunks, JPEG EXIF (exif-parser), ComfyUI graph traversal

---

## License
GNU General Public License v3.0

## Support Development
[![Join us on Discord](https://img.shields.io/badge/Join%20us%20on-Discord-5865F2?style=for-the-badge&logo=discord)](https://discord.gg/HhBSvM9gBY)
[![Support us on Ko-fi](https://img.shields.io/badge/Support%20us%20on-Ko--Fi-FF5E5B?style=for-the-badge&logo=kofi)](https://ko-fi.com/duskfallcrew)
