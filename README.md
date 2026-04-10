# Dataset Tools: An AI Metadata Viewer

<div align="center">

<!-- Social & Support Badges -->
[![Built with NextJS](https://img.shields.io/badge/Built%20with-NextJS-black?style=for-the-badge&logo=next.js)](https://nextjs.org/) [![GitHub](https://img.shields.io/badge/GitHub-View%20on%20GitHub-181717?logo=github&style=for-the-badge)](https://github.com/Ktiseos-Nyx/Dataset-Tools)
[![Discord](https://img.shields.io/discord/1024442483750490222?logo=discord&style=for-the-badge&color=5865F2)](https://discord.gg/HhBSvM9gBY)
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
4. **Inspect metadata:** Click any image → metadata panel shows prompts, parameters, LoRAs, and workflow info.
5. **Customize:** Settings panel has theme, accent colors, font size, thumbnail size, and file display options.

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
| **Sorting** | ✅ | Sort by name, date modified, or file size. (Thumbnail Sorting Coming Soon) |
| **Accent Colors** | ✅ | 7 color themes (zinc, red, orange, green, blue, violet, pink) with dark mode support. |
| **WebP Metadata** | ⚠️ | Viewing works. Metadata extraction in development.(Not all webP will have metadata, but some animated ones will)|
| **ComfyUI Workflows** | ✅ | 3-phase extraction: field-based scan → graph trace → type-match fallback. Handles custom nodes, service detection and more. |
| **Github Lookup** | ✅ | If a node isn't found the first time, search, search again. |

### Supported Formats
- **A1111 / Forge** — PNG tEXt chunks, JPEG EXIF
- **ComfyUI** — JSON workflow with node graph resolution
- **NovelAI** — PNG metadata
- **Civitai** — UTF-16-LE JPEG UserComment
- **Standard EXIF/IPTC/XMP** — All image formats
- **Png as Jpeg** - Magic Byte Detection.

---

## Tech Stack

- **Framework:** Next.js 16 (App Router), React 19, TypeScript 5
- **UI:** shadcn/ui + Radix UI, Lucide icons, Tailwind CSS v4 (OKLch color space)
- **Thumbnails:** Sharp (libvips) with WebP disk caching
- **Metadata:** Pure JS parsing — PNG chunks, JPEG EXIF (exif-parser), ComfyUI graph traversal

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

While this is working 99% better than our original python app, please be aware that as we move this into "ALPHA TESTING" that there will be more bugs, we can't provide enough pre-catching for bugs as we tried for the original python. So we're hoping that the amount of work we've put into porting this into a much easier format you can help test. 

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
- [ ] 
---
### Q&A 

Q: Are you working on putting this into an executable format? 

A: Yes, eventually we'll port this to Electron or see what Tauri needs, we're likely for ease of use likely going to use Electron, as for this we're not sure how Tauri would effect the rendering of metadata or otherwise. 

Q: Are you aware that NextJS/Node has more CVE's and is the Number ONE VIBE CODED language this side of the moon?

A: Yes, but just like our python version and anything else we build, we're not like other "VIBE CODED TOOLS" we demand security, peace of mind and a way through the mess. Unlike the trainer which uses major ML stacks to survive, we can promise you A LOT more security with this. As long as you're not installing this on an OpenClaw instance you're fine.

Q: But Chrome Sucks!

A: Duskfallcrew personally reccomends the use of Vivaldi which is a CHROMIUM fork, Electron is only as "BLOATED" as the packages you port with it, along with web trackers and unmitigated cache, image sizes and lazy loading issues. When we port our executable mode, we'll make sure the thing runs on every flipping potato machine out there! 

Q: Why is this not already 100% Done?

A: Because I have 20 projects on the go? Plus i'm currently the solo dork with AI assistance, yes Joel does supervise and add things to the code, his ComfyUI lookup tool is what powers this - Exception: Claude translated it to node because Joel's actually a real life developer, he's not got time to do EVERYTHING. Plus when he's not at work or with his family: He's an A+ Smexy FFXIV player! He beats our Miqo'te's poor fashion choices just by existing! 

---

## License
GNU General Public License v3.0

## Acknowledgements

* Core Parsing Logic & Inspiration: This project incorporates and significantly adapts parsing functionalities from Stable Diffusion Prompt Reader by  **[receyuki](https://github.com/receyuki)** . Our sincere thanks for this foundational work.
      Original Repository: [stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader)
      The original MIT license for this vendored code is included in the NOTICE.md file.
* **[Traugdor](https://github.com/traugdor)** For the supervision, the memes and this: [Python ComfyUI Node Finder](https://github.com/Ktiseos-Nyx/ComfyUI-Node-Finder) 
* Everyone at [Arc En Ciel](arcenciel.io/) for your continued driven support.
* Anthropic - Pls Keep Sending us Free Credits, we're broke!
* **[Anzhc](https://github.com/anzhc)** for continued support and motivation.
* Our peers and the wider AI and open-source communities for their continuous support and inspiration.
* Mempalace for Neurodivergent Memory Support for Local Development [Mempalace @ Github](https://github.com/milla-jovovich/mempalace)
* AI Language Models (like those from Google, OpenAI, Anthropic) for assistance with code generation, documentation, and problem-solving during development.
* ...and many more!


**SPECIAL THANKS**

- Supervised by: traugdor
- Special Thanks to contributors: Open Source Community, Whitevamp, Exdysa, and so many more.
- Special Thanks to Anthropic for the numerous amounts of insanely valuable free credits during marketing ploys. While we're only on the USD 20 a month plan, anything helps so throw more of these our way because development has become sort of a job for us! 

## Support Development
[![Join us on Discord](https://img.shields.io/badge/Join%20us%20on-Discord-5865F2?style=for-the-badge&logo=discord)](https://discord.gg/HhBSvM9gBY)
[![Support us on Ko-fi](https://img.shields.io/badge/Support%20us%20on-Ko--Fi-FF5E5B?style=for-the-badge&logo=kofi)](https://ko-fi.com/duskfallcrew)
