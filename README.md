# Dataset Tools: An AI Metadata Viewer

<div align="center">

<!-- Social & Support Badges -->
[![Built with NextJS](https://img.shields.io/badge/Built%20with-NextJS-black?style=for-the-badge&logo=next.js)](https://nextjs.org/) [![GitHub](https://img.shields.io/badge/GitHub-View%20on%20GitHub-181717?logo=github&style=for-the-badge)](https://github.com/Ktiseos-Nyx/Dataset-Tools)
[![Demo](https://img.shields.io/badge/Live-Demo-000000?style=for-the-badge&logo=vercel)](https://dataset-tools-three.vercel.app)
[![Twitch](https://img.shields.io/badge/Twitch-Follow%20on%20Twitch-9146FF?logo=twitch&style=for-the-badge)](https://twitch.tv/duskfallcrew)
[![Support us on Ko-fi](https://img.shields.io/badge/Support%20us%20on-Ko--Fi-FF5E5B?style=for-the-badge&logo=kofi)](https://ko-fi.com/duskfallcrew) 
[![Built with v0](https://img.shields.io/badge/Built%20with-v0.app-black?style=for-the-badge)](https://v0.app/chat/itQySJ65urb)

<hr>

[English Readme](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/README.md) •
[Wiki](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki) •
[Discussions](https://github.com/Ktiseos-Nyx/Dataset-Tools/discussions) •
[Notices](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/NOTICE.md) •
[License](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/LICENSE)

<hr>


![Screenshot 2026-02-10 184845 (1)](https://github.com/user-attachments/assets/90f9e2bf-3c3c-4ae0-9131-33fa6b0b745d)


</div>

---

**Dataset Tools NextJS Edition** is a **local-first web application** for browsing AI image datasets with comprehensive metadata extraction. Built from the ground up in TypeScript — no Python dependencies, no OpenCV duct tape, no NumPy startup tax. Running on Next.js 16, React 19, and shadcn/ui components. 

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
```bash
npm install
```

# Start dev server (For Local Testing)
```bash
npm run dev
```

For production:
```bash
npm run build && npm start
```

---

## Usage

1. **Start the app:** `npm run dev` → open `http://localhost:3000`
2. **Browse files:** Use the file tree sidebar, or click the folder icon to pick any directory.
3. **Drag & drop:** Drop an image anywhere in the app — it'll find the folder and load thumbnails.
4. **Inspect metadata:** Click any image → metadata panel shows prompts, parameters, LoRAs, and workflow info. Safetensors files show model architecture, training details, and dataset tags.
5. **Edit metadata:** Click the edit button on any text field to modify prompts and parameters directly in PNG files.
6. **Customize:** Settings panel has theme, accent colors, font size, thumbnail size, and file display options.

### When metadata fails to parse
1. Check browser console for parser logs.
2. Note the workflow structure (ComfyUI? A1111? Custom nodes?).
3. **File an issue with:**
   * Console error snippet
   * Workflow type + custom nodes used
   * Minimal repro image (if shareable)
   * 
---

## Current Capabilities

| Feature | Status | Details |
| :--- | :---: | :--- |
| **Metadata Parsing** | ✅ | **90% success rate.** Graph-tracing engine for ComfyUI, field-based detection for A1111/Forge/NovelAI. |
| **Image Viewing** | ✅ | PNG, JPG, JPEG, WebP. Zoom (25-400%), rotation, fit-to-container. |
| **File Browsing** | ✅ | Recursive lazy-loading file tree. Browse any folder on your system. |
| **Drag & Drop** | ✅ | Drop an image to auto-detect its folder and extract metadata. |
| **Thumbnails** | ✅ | Sharp-powered WebP thumbnails with disk cache (`.thumbcache/`). |
| **Sorting** | ✅ | Sort by name, date modified, or file size in both file tree and thumbnail viewport. |
| **Accent Colors** | ✅ | 7 color themes (zinc, red, orange, green, blue, violet, pink) with dark mode support. |
| **WebP Viewing** | ✅ | Viewing works for static and animated WebP files. Metadata extraction is format-dependent. |
| **ComfyUI Workflows** | ✅ | 3-phase extraction + ComfyUI ≥1.26 provenance (cnr_id/aux_id). Node graph tracing, custom node resolution, service detection. |
| **GitHub Lookup** | ✅ | Fallback search for unknown ComfyUI custom nodes via GitHub code search. |
| **Safetensors Metadata** | ✅ | Full metadata extraction for LoRA and model files — rank, alpha, training params, dataset tags. |
| **Metadata Editing** | ✅ | Edit prompts and parameters in PNG files, write changes back to disk. |

### Supported Formats
- **A1111 / Forge** — PNG tEXt chunks, JPEG EXIF
- **ComfyUI** — JSON workflow with node graph resolution
- **NovelAI** — PNG metadata
- **Civitai** — UTF-16-LE JPEG UserComment
- **Standard EXIF/IPTC/XMP** — All image formats
- **Safetensors** — LoRA rank/alpha, training parameters, dataset tags, base model info
- **PNG as JPEG** - Magic Byte Detection.

---

## Tech Stack

- **Framework:** Next.js 16 (App Router), React 19, TypeScript 5
- **UI:** shadcn/ui + Radix UI + Base UI, Lucide icons, Tailwind CSS v4 (OKLch color space)
- **Thumbnails:** Sharp (libvips) with WebP disk caching
- **Metadata:** Pure JS parsing — PNG chunks, JPEG EXIF (exif-parser), ComfyUI graph traversal with node provenance
- **Node Resolution:** ComfyUI Node Finder port (extension-node-map registry + GitHub code search fallback)

---

### Service Detection

As we had in the python edition our journey is marked with making sure as many of the popular and niche sites with generation services are tagged for easy detection. If your workflow or website has a custom pattern for resource detection, our tool is likely to be able to find it. If it hasn't been hashed and dashed through to the tool yet, just flick an issue up and we'll hook it up ASAP. 

Examples of this are Tensorart, Forge, ArcEncCiel, CivitAI and Yodayo. 

Many tools desktop or remote based have patterns, so the key is either in the metadata handling, or the resource identification. 

### Why 90% > 65% Matters
The Python edition relied on fragile heuristics. This engine uses **deterministic graph traversal** with proper node relationship mapping. It follows wires backwards from sampler nodes to find prompts, identifies nodes by their data (not just class_type), and handles platform-wrapped node names via substring matching. When it fails, logs show exactly why.

### Why this exists
The Python edition worked at 65% success rate with heuristic spaghetti. This NextJS engine hits **90% success rate** on complex ComfyUI workflows using **deterministic graph traversal**. Metadata is parsed in pure JavaScript — no waiting for Python to boot, no OpenCV overhead.

#### Development Stage

This engine has been battle-tested across thousands of images and is in active daily use. While there will always be edge cases with new custom nodes and formats, the core parser is stable and handles the vast majority of real-world workflows. Bug reports with repro images remain the best way to push that success rate higher.

---

## Contributing

### Found a parsing failure?
Open an issue with the details above. Real-world edge cases are how we push past 90%.

### Want to improve the parser?
1. Fork repo → `npm install` → `npm run dev`
2. Metadata extraction lives in `app/api/metadata/route.ts`
3. Test with your own images or AI-generated samples
4. Submit a PR with before/after evidence

### Ideas for contributors
- [ ] WebP metadata chunk parser
- [x] Editable metadata (write back to files)
- [ ] SQLite indexing for faster folder browsing
- [ ] ComfyUI workflow visualization
- [ ] Batch metadata export (CSV/JSON)
- [ ] Parser debugger panel showing traversal steps
- [ ]
---
### Q&A

Q: Are you planning a desktop app?

A: Yes — we're evaluating both Electron and Tauri. No firm decision yet, but the goal is a standalone executable that runs without needing Node.js installed.

Q: Isn't Node.js a security concern?

A: Security is taken seriously in this project. Unlike ML-heavy tools that pull in massive native dependency trees, Dataset Tools has a minimal, auditable surface area. All file access is validated server-side, and API keys are stored in `.env.local`, never exposed to the browser.

Q: Does it only work in Chrome?

A: The app works in any modern browser. Firefox, Edge, and Chromium-based browsers like Vivaldi are all supported.

Q: Is this project actively maintained?

A: Yes. The parser is stable and handles the vast majority of real-world workflows. Maintenance and improvements are ongoing — bug reports and contributions are always welcome.

## AI-Assisted Development

This project was built with significant assistance from large language models — primarily Claude, with additional contributions from Gemini, DeepSeek, and Qwen. The role of the project maintainer has been focused on research, architecture decisions, testing across diverse AI-generated images and workflows, and directing the scope and quality of the codebase.

Transparency note: while LLMs generated a substantial portion of the implementation, every line has been reviewed, tested against real-world datasets, and refined through iterative prompting and validation. The 90%+ metadata parsing success rate is the result of detailed research into AI image generation formats combined with LLM-assisted implementation.

---

## License
GNU General Public License v3.0

## Acknowledgements

* **Core Parsing Logic:** This project incorporates and adapts parsing functionality from [Stable Diffusion Prompt Reader](https://github.com/receyuki/stable-diffusion-prompt-reader) by **[receyuki](https://github.com/receyuki)**. The original MIT license for vendored code is included in `NOTICE.md`.
* **[traugdor](https://github.com/traugdor)** — Project supervision and the [ComfyUI Node Finder](https://github.com/Ktiseos-Nyx/ComfyUI-Node-Finder) (Python), whose extension-node-map registry and node classification logic are now built directly into Dataset Tools.
* Everyone at [Arc En Ciel](https://arcenciel.io/) for continued support.
* **[Anzhc](https://github.com/anzhc)** for ongoing support and motivation.
* The wider AI and open-source communities for feedback, testing, and contributions.


**SPECIAL THANKS**

- Supervised by: [traugdor](https://github.com/traugdor)
- Contributors: open-source community, Whitevamp, Exdysa, and many more.
- Anthropic for Claude API credits supporting development.

## Support Development
[![Support us on Ko-fi](https://img.shields.io/badge/Support%20us%20on-Ko--Fi-FF5E5B?style=for-the-badge&logo=kofi)](https://ko-fi.com/duskfallcrew)
[![Rent GPUs on Vast.ai](https://img.shields.io/badge/Rent%20GPUs%20on-Vast.ai-4B32C3?style=for-the-badge)](https://cloud.vast.ai/?ref_id=70354)
