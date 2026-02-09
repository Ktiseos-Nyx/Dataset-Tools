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

<!-- Quick Links -->
[English Readme](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/README.md) •
[Wiki](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki) •
[Discussions](https://github.com/Ktiseos-Nyx/Dataset-Tools/discussions) •
[Notices](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/NOTICE.md) •
[License](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/LICENSE)

</div>

---

**Dataset Tools NextJS Edition** is a **local-first web application** for browsing AI image datasets with comprehensive metadata extraction. Built from the ground up in TypeScript — no Python dependencies, no OpenCV duct tape, no NumPy startup tax. Running on NextJS 16+ and Shadcn directory components!

### Why this exists
The Python edition worked at 65% success rate with heuristic spaghetti. This NextJS engine hits **90% success rate** on complex ComfyUI workflows using **deterministic graph traversal**. And it's *blazing fast* because we parse metadata in pure JavaScript — no waiting for Python to boot, no OpenCV overhead.

> ⚠️ **Development Tool Warning**
> *   **Run locally:** `npm run dev`
> *   **Requirements:** Node.js 18+ and npm
> *   **Status:** No public deployment. No Vercel sync. Drag-and-drop not implemented yet. WebP metadata extraction coming soon.

### Community-Driven Development
This project is inspired by [stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader) and thrives on community contributions. Found a bug? Have a workflow that won't parse? Want to add support for a new tool? **We welcome forks, fixes, and pull requests!** This is a community tool built by the community, for the community.

---

<div align="center">

**Navigation**
[Features](#current-capabilities-no-hype) • [Supported Formats](#supported-formats) • [Installation](#installation-local-dev-only) • [Usage](#usage-local-dev-workflow) • [API Integration](#api-integration) • [Contributing](#contributing-how-to-actually-help)

</div>

---

## Installation (Local Dev Only)

```bash
# Clone repo
git clone https://github.com/Ktiseos-Nyx/Dataset-Tools.git
cd Dataset-Tools
```
### Install dependencies (Node.js 18+ required)
npm install

### Start dev server
npm run dev

## Current Capabilities (No Hype)

| Feature | Status | Details |
| :--- | :---: | :--- |
| **Metadata Parsing** | ✅ | **90% success rate.** Graph-tracing engine outperforms Python's 65% heuristic approach. |
| **Image Viewing** | ✅ | **Full support.** PNG, JPG, JPEG, WebP render instantly. |
| **WebP Metadata** | ⚠️ | **Viewing only.** Metadata extraction is in active development. |
| **File Loading** | ✅ | **Button upload.** Click "Upload Files" → select images/folders. |
| **Drag & Drop** | ❌ | **Not implemented.** Planned for next milestone. |
| **Speed** | ⚡ | **Blazing fast.** Pure JS parsing — no Python startup tax, no OpenCV overhead. |
| **ComfyUI Workflows** | ✅ | **90% graph tracing.** Handles complex node connections, custom nodes, FLUX/SD3/SDXL. |

### Why 90% > 65% Matters
The Python edition relied on fragile heuristics, NumPy for "math", and OpenCV for image ops — essentially running on *toiletpaper and duct tape*. This NextJS engine uses **deterministic graph traversal** with proper node relationship mapping. When it fails, logs show exactly why — no black-box guessing.

---

## Usage (Local Dev Workflow)

1. **Start the app:**
   ```bash
   npm run dev
   # Open http://localhost:3000
   ```
2. **Load images:** Click the **"Upload Files"** button → select images or folders.
3. **Inspect metadata:** Click any image → see parsed prompts, params, and workflow JSON.
4. **Debug live:** Open browser **DevTools** → **Console** shows `[Parser]` decisions in real-time.
5. **Break it intentionally:** Throw edge-case workflows at it → watch logs → fix parsers!

### 📌 When metadata fails to parse
1. Check browser console for `[Parser]` logs.
2. Note the workflow structure (ComfyUI? A1111? Custom node?).
3. **File an issue with:**
   *   Console error snippet.
   *   Workflow type + custom nodes used.
   *   Minimal repro image (if shareable).
   *   
### Dev Environment Status
*   ✅ **Opens at** `http://localhost:3000`
*   ✅ **Hot-reload enabled**
*   ✅ **Full source map debugging**
*   ✅ **Console logs** show parser decisions in real-time

## Non Dev
Once you've hit :
```bash
npm run build && npm start
```
---

## Contributing: How to Actually Help

### 🐞 Found a parsing failure?
If you encounter a workflow that breaks the parser, please open an issue with the details listed above.

### 💻 Want to improve the parser?
1. Fork repo → `npm install` → `npm run dev`.
2. Modify parsers in `/src/lib/parsers/`.
3. Test with real-world broken workflows.
4. **Submit a PR with:**
   *   Before/after success rate evidence.
   *   Console log proof of fix.
   *   Test case (if permissible).

### 🌱 Low-hanging fruit for new contributors
- [ ] WebP metadata chunk parser (`/src/lib/parsers/webp.ts`)
- [ ] Drag-and-drop UI (React Dropzone integration)
- [ ] "Parser Debugger" panel showing traversal steps visually
- [ ] Batch metadata export (CSV/JSON)

---

## Future Vision (No Vaporware)

| Feature | Status | Purpose |
| :--- | :---: | :--- |
| **WebP Metadata** | 🟡 | Critical for modern workflow exports. |
| **Drag & Drop** | 🟡 | UX parity with desktop tools. |
| **Color Theme System** | 💡 | Not Python themes — new NextJS-native theming. |
| **"Ask an AI" Helper** | 🔮 | Contextual help: *"Why did this workflow fail?"* → AI explains node gaps. |
| **Parser Debugger UI** | 💡 | Visualize graph traversal path for failed parses. |

> **🌟 Our Philosophy:**
> "No false promises. If it's in the repo, it's tested. If it's in the roadmap, we're actively building it. We rebuilt metadata parsing to be boringly reliable — join us to make it 95%."

---

## License
GNU GENERAL PUBLIC LICENSE GPL 3.0

## Support Development
[![Join us on Discord](https://img.shields.io/badge/Join%20us%20on-Discord-5865F2?style=for-the-badge&logo=discord)](https://discord.gg/HhBSvM9gBY)
[![Support us on Ko-fi](https://img.shields.io/badge/Support%20us%20on-Ko--Fi-FF5E5B?style=for-the-badge&logo=kofi)](https://ko-fi.com/duskfallcrew)
