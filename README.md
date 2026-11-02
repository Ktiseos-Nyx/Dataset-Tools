# Dataset Tools: An AI Metadata Viewer

<div align="center">

<!-- Social & Support Badges -->
[![Built with NextJS](https://img.shields.io/badge/Built%20with-NextJS-black?style=for-the-badge&logo=next.js)](https://nextjs.org/) [![GitHub](https://img.shields.io/badge/GitHub-View%20on%20GitHub-181717?logo=github&style=for-the-badge)](https://github.com/Ktiseos-Nyx/Dataset-Tools)
[![Demo](https://img.shields.io/badge/Live-Demo-000000?style=for-the-badge&logo=vercel)](https://dataset-tools-three.vercel.app) [![Support us on Ko-fi](https://img.shields.io/badge/Support%20us%20on-Ko--Fi-FF5E5B?style=for-the-badge&logo=kofi)](https://ko-fi.com/duskfallcrew) 

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



<div align="center">

**Navigation**
[Features](#current-capabilities) • [Supported Formats](#supported-formats) • [Installation](#installation) • [Usage](#usage) • [Contributing](#contributing) • [Development Mode](#development-mode)

</div>

---

## About 

**Dataset Tools NextJS Edition** is a **local-first web application** for viewing EXIF metadata from AI-generated images and camera photos, including the software used to create AI images and the camera details embedded in photos.

---

### Current Capabilities

Current Capabilities for CLI, Destkop Executable and Portable:

| Feature | Status | Details |
| :--- | :---: | :--- |
| **Metadata Parsing** | ✅ | Graph-tracing engine for ComfyUI, field-based detection for A1111/Forge/NovelAI. |
| **Image Viewing** | ✅ | PNG, JPG, JPEG, WebP. Zoom (25-400%), rotation, fit-to-container. |
| **File Browsing** | ✅ | Currently Windows Executable Only: Recursive lazy-loading file tree. Browse any folder on your system. |
| **Drag & Drop** | ✅ | Drop an image to extract metadata. |
| **Thumbnails** | ✅ | Sharp-powered WebP thumbnails with disk cache (`.thumbcache/`). |
| **Sorting** | ✅ | Sort by name, date modified, or file size in both file tree and thumbnail viewport. |
| **Accent Colors** | ✅ | 7 color themes (zinc, red, orange, green, blue, violet, pink) with dark mode support. |
| **WebP Viewing** | ✅ | Viewing works for static and animated WebP files. Metadata extraction is format-dependent. |
| **ComfyUI Workflows** | ✅ | 3-phase extraction + ComfyUI ≥1.26 provenance (cnr_id/aux_id). Node graph tracing, custom node resolution, service detection. |
| **GitHub Lookup** | ✅ | Fallback search for unknown ComfyUI custom nodes via GitHub code search. |
| **Safetensors Metadata** | ✅ | Full metadata extraction for LoRA and model files — rank, alpha, training params, dataset tags. |
| **Metadata Editing** | ✅ | Edit prompts and parameters in PNG files, write changes back to disk. |

---

Current Capabilities for Vercel Demo:

[![Demo](https://img.shields.io/badge/Live-Demo-000000?style=for-the-badge&logo=vercel)](https://dataset-tools-three.vercel.app)

| Feature | Status | Details |
| :--- | :---: | :--- |
| **Metadata Parsing** | ✅ | Graph-tracing engine for ComfyUI, field-based detection for A1111/Forge/NovelAI. |
| **Image Viewing** | ✅ | PNG, JPG, JPEG, WebP. Zoom (25-400%), rotation, fit-to-container. |
| **Drag & Drop** | ✅ | Drop an image to extract metadata. |
| **Accent Colors** | ✅ | 7 color themes (zinc, red, orange, green, blue, violet, pink) with dark mode support. |
| **WebP Viewing** | ✅ | Viewing works for static and animated WebP files. Metadata extraction is format-dependent. |
| **ComfyUI Workflows** | ✅ | 3-phase extraction + ComfyUI ≥1.26 provenance (cnr_id/aux_id). Node graph tracing, custom node resolution, service detection. |

---

### Supported Formats
- **A1111 / Forge** — PNG tEXt chunks, JPEG EXIF
- **ComfyUI** — JSON workflow with node graph resolution
- **NovelAI** — PNG metadata
- **Civitai** — UTF-16-LE JPEG UserComment
- **Standard EXIF/IPTC/XMP** — All image formats
- **Safetensors** — LoRA rank/alpha, training parameters, dataset tags, base model info
- **PNG as JPEG** - Magic Byte Detection.

### Tech Stack

- **Framework:** Next.js 16 (App Router), React 19, TypeScript 5
- **UI:** shadcn/ui + Radix UI + Base UI, Lucide icons, Tailwind CSS v4 (OKLch color space)
- **Thumbnails:** Sharp (libvips) with WebP disk caching
- **Metadata:** Pure JS parsing — PNG chunks, JPEG EXIF (exif-parser), ComfyUI graph traversal with node provenance
- **Node Resolution:** ComfyUI Node Finder port (extension-node-map registry + GitHub code search fallback)



---

## Installation 

These instructions are based on PRODUCTION mode and are similar to DEV mode, please see the [Development Mode](#development-mode) instructions for more information on how that rolls.

Requires [Node.js](https://nodejs.org) 18+.

```bash
git clone https://github.com/Ktiseos-Nyx/Dataset-Tools.git
cd Dataset-Tools
npm install

npm run build 
npm start
Open http://localhost:3000.

```

---

### Desktop App (Windows)

A standalone `.exe` lives on the [Releases](https://github.com/Ktiseos-Nyx/Dataset-Tools/releases) page — no Node.js, no browser, no npm. It bundles Next.js and runs the same metadata engine as the web build, but against any folder on your machine. This comes in TWO flavors: Portable and NSIS based installer. 

Portable works great for travel, or lower end machines that don't want to fuss with the full installation.


---

#### Smart Screen Issues

"Windows protected your PC"?

On first launch Windows will probably throw up a SmartScreen warning. That's not malware — it's because the exe isn't signed with a commercial code-signing certificate, which costs a few hundred dollars a year. Same thing every unsigned open-source desktop app deals with.

To run it:

1. Click **More info**
2. Click **Run anyway**

Two ways to check it yourself before running:

- Every release ships a **VirusTotal scan** link so you can see the file checked against 70+ antivirus engines. You'll occasionally see 1–2 "generic heuristic" flags on a fresh Electron build — that's normal for unsigned apps, not a real detection.
- The whole app is open source — the source and the build configuration are all here, so you can inspect exactly how the exe is produced.

But I hate SmartScreen!

- A portable windows exe with no requirements to install is now available on the most recent releases.
- Future versions for Linux are coming, but not MacOS.
- This portable edition provides no requirements (as far as we're aware) and can be more useful than installing, but be aware it may not cache your settings.

---

## Usage

1. **Start the app:** `npm start` → open `http://localhost:3000`
2. **Browse files:** Use the file tree sidebar, or click the folder icon to pick any directory.
3. **Drag & drop:** Drop an image anywhere in the app — it'll find the folder and load thumbnails.
4. **Inspect metadata:** Click any image → metadata panel shows prompts, parameters, LoRAs, and workflow info. Safetensors files show model architecture, training details, and dataset tags.
5. **Edit metadata:** Click the edit button on any text field to modify prompts and parameters directly in PNG files.
6. **Customize:** Settings panel has theme, accent colors, font size, thumbnail size, and file display options.

> **Note on folder browsing:** "Open folder" (native directory picking) is a **desktop-app (Electron)** feature — browsers don't expose absolute filesystem paths to web pages. Drop-to-detect-folder is a **best-effort server-side search** (`/api/find-file`) that scans the server's filesystem and may find files beyond the common folders or exceed its timeout. The web build is otherwise single-file drag-and-drop. Browser-native folder browsing (via the File System Access API) is in progress — track it in **[issue #220](https://github.com/Ktiseos-Nyx/Dataset-Tools/issues/220)**. This is being actively worked on and has some progress as of the recent updates.

### When metadata fails to parse
1. Check browser console for parser logs.
2. Note the workflow structure (ComfyUI? A1111? Custom nodes?).
3. **File an issue with:**
   * Console error snippet
   * Workflow type + custom nodes used
   * Minimal repro image (if shareable)
   * Your OS if possible.
   * Version of the application.
  
4. If the version is "PYTHON" we don't have any way of supporting that anymore.
---

## Development Mode

Dev mode is highly volatile on some systems, and may cause some unintended effects, if you're interested in doing this we suggest using not only WSL2 for windows users but a DOCKER CONTAINER. 
It's not that it's insecure it's more so that things run differently than production mode, and if anything may have unintended effects on your OS. 

This runs via the turbopack dev mode, and may be slower and considerably janky on lower end systems.

```bash
git clone https://github.com/Ktiseos-Nyx/Dataset-Tools.git
cd Dataset-Tools
npm install

npm run build 
npm run dev
Open http://localhost:3000.

```

More information in depth will come over time in our [Wiki](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki).

---

## Contributing

### Community-Driven Development
This project is inspired by [stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader) and thrives on community contributions. Found a bug? Have a workflow that won't parse? Want to add support for a new tool? **We welcome forks, fixes, and pull requests!**

### Found a parsing failure?
Open an issue with the details above. ComfyUI always has edge cases, and while we intend to catch almost everything we can with the lookup on desktop and CLI, there are always new software tags and nodes.

### Want to improve the parser?
1. Fork repo → `npm install` → `npm run dev`
2. Metadata extraction lives in `app/api/metadata/route.ts`
3. Test with your own images or AI-generated samples
4. Submit a PR with before/after evidence

---

#### Development Info

This engine has been tested across thousands of images and is in active daily use. While there will always be edge cases with new custom nodes and formats, the core parser is stable and handles the vast majority of real-world workflows. While we are largely no longer in generative AI circles, this application is developed for both sides of the coin. 

We don't want to lie about how the code was created, nor directed. Unlike future projects of ours that are intending to be far more human lead, this took far more human direction than human based coding. Due to the nature of the original being in python and being a total load of spaghetti code, there was no way we were going to do it again by hand. SD-Prompt Reader was easy to understand, but the edge case detection of most metadata readers falls at simplistic graph traversal. Through absolute insane amounts of research, bashing our heads into walls and throwing ourselves at lawnmowers (Aesthetically not literally) we caught a lot more than the original inspiration as well as our original version. 

We take pride in security, so we do our best to audit with multiple tools, and we're aware of AI-based issues with security, and do our best to monitor dependency issues as well as hallucinatory issues inside the codebase. One singular reason alone Ktiseos Nyx moved to using Next/Node was the idea that it was closer to web development and the nature of typescript was a lot smoother for us to conceptualize than python. This only really covers Duskfallcrew (aka ashbluepollution-95), as they have a graphic design degree not a computer science degree. You try developing a python app when all you understand is how to center a DIV on a web page at 3am. If you run into any issues feel free to use the information on how to contribute, that way we can build better sources together. 

---

## License
[License](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/LICENSE) GNU General Public License v3.0

---

## Acknowledgements

* **Core Parsing Logic:** This project incorporates and adapts parsing functionality from [Stable Diffusion Prompt Reader](https://github.com/receyuki/stable-diffusion-prompt-reader) by **[receyuki](https://github.com/receyuki)**. The original MIT license for vendored code is included in `NOTICE.md`.
* **App icon:** [Web development icons created by Chanut-is-Industries - Flaticon](https://www.flaticon.com/free-icons/web-development)
* **[Quadmoon](https://github.com/traugdor)** — Project supervision and the [ComfyUI Node Finder](https://github.com/Ktiseos-Nyx/ComfyUI-Node-Finder) (Python), whose extension-node-map registry and node classification logic are now built directly into Dataset Tools.
* Everyone at [Arc En Ciel](https://arcenciel.io/) for continued support.
* **[Anzhc](https://github.com/anzhc)** for ongoing support and motivation.
* The wider AI and open-source communities for feedback, testing, and contributions.


**SPECIAL THANKS**

- Supervised by: [Quadmoon](https://github.com/traugdor)
- Contributors: open-source community, Whitevamp, Exdysa, and many more.
- ComfyUI for consistent changes in how workflows work, both for AI and for non AI workflows.
