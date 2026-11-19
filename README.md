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
[About](#about) • [Installation](#installation) • [Usage](#usage) • [Contributing](#contributing) • [Development Mode](#development-mode)

</div>

---

## About 

**Dataset Tools NextJS Edition** is a **local-first web application** for viewing EXIF metadata from AI-generated images and camera photos, including the software used to create AI images and the camera details embedded in photos.

- **Cross-platform:** the CLI/web install runs anywhere Node.js runs — Windows, macOS, and Linux, including headless boxes and cloud containers. Desktop binaries ship for Windows (installer + portable) and Linux (AppImage).
- **Community-driven:** inspired by [stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader) — we welcome forks, fixes, and pull requests.
- **Feature details, supported formats, and tech stack:** maintained in the [Wiki](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki) — see [Key Features](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki/Key-Features), [Supported File Formats & Metadata Details](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki/Supported-File-Formats-&-Metadata-Details), and [Troubleshooting & FAQ](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki/Troubleshooting-&-FAQ).

---

## Installation 

Production mode; dev mode differs — see [Development Mode](#development-mode).

Requires [Node.js](https://nodejs.org) 20.9+ to run the application. Development installs want Node.js 22+ — a dev-only dependency (`concurrently`) requires it, and npm only warns (not fails) on older versions.

```bash
git clone https://github.com/Ktiseos-Nyx/Dataset-Tools.git
cd Dataset-Tools
npm install

npm run build 
npm start
```

Open http://localhost:3000.

Works the same on Windows, macOS, and Linux. **Running on a headless box or cloud container (vast.ai, colab, a server)?** This is your build — skip the desktop binaries and use the web UI. Note the server binds to `127.0.0.1` only: it is *not* reachable from another machine just by opening a container port. For remote access, tunnel to the host's local listener (e.g. `ssh -L 3000:localhost:3000 user@host`) rather than exposing the server publicly.

### Desktop Binaries

Standalone builds live on the [Releases](https://github.com/Ktiseos-Nyx/Dataset-Tools/releases) page — no Node.js, no browser, no npm. They bundle Next.js and run the same metadata engine as the web build, but against any folder on your machine.

| Platform | Artifact | Status & notes |
| :--- | :--- | :--- |
| Windows | NSIS installer + portable EXE | ✅ Supported. Portable keeps its settings and thumbnail cache in a `data` folder next to the EXE (falls back to the default user-data folder if that can't be created); API keys stored there are scrambled, not encrypted — keep it out of shared folders. |
| Linux | AppImage (x64) | ⚠️ **Experimental — not yet verified on a desktop Linux install** (built + smoke-tested only). Portable, no install step: download, `chmod +x`, run. Modern distros may need `libfuse2` (or use `--appimage-extract`). Report what works/breaks in [Discussions](https://github.com/Ktiseos-Nyx/Dataset-Tools/discussions). |
| macOS | — | Not planned as an Electron build; use the CLI/web install above. |

**Windows SmartScreen warning?** Expected for unsigned builds — the [Wiki's Installation page](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki/Installation) covers "More info → Run anyway" and how to verify releases via the VirusTotal scan links we ship.

---

## Usage

1. **Start the app:** `npm start` → open `http://localhost:3000` (or launch the desktop binary)
2. **Browse files:** file tree sidebar, or the folder icon to pick any directory
3. **Drag & drop:** drop an image anywhere — the app finds the folder and loads thumbnails
4. **Inspect metadata:** click any image — prompts, parameters, LoRAs, workflow info; safetensors show architecture, training details, and dataset tags
5. **Edit metadata:** click the edit button on any text field to modify prompts/parameters in PNG files
6. **Customize:** settings panel has theme, accent colors, font size, thumbnail size, and file display options

> **Note on folder browsing:** the desktop app uses a native folder picker; the web build uses browser-local folder access (File System Access API). Subfolder navigation and remembering the folder between visits are still in progress — track **[issue #220](https://github.com/Ktiseos-Nyx/Dataset-Tools/issues/220)**.

### When metadata fails to parse
1. Check the browser console for parser logs.
2. Note the workflow structure (ComfyUI? A1111? Custom nodes?).
3. **[File an issue](https://github.com/Ktiseos-Nyx/Dataset-Tools/issues/new)** with the console error, workflow type + custom nodes used, and a minimal repro image if shareable.

More detail in the [Troubleshooting & FAQ](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki/Troubleshooting-&-FAQ).

---

## Development Mode

<details>
<summary>Click to expand — Development info</summary>

Dev mode is slow and RAM-hungry, if you're interested in doing this we suggest using not only WSL2 for Windows users but a DOCKER CONTAINER. 


```bash
git clone https://github.com/Ktiseos-Nyx/Dataset-Tools.git
cd Dataset-Tools
npm install


npm run dev
```

Open http://localhost:3000.

### Electron Dev

The Electron shell wraps the web app in a desktop window. `electron:dev` runs the Next dev server and launches the Electron shell against it once `localhost:3000` is up. `electron:build` is the release pipeline — production build, Electron compile, then the platform targets via electron-builder (Windows: installer + portable EXE; Linux: AppImage). It builds for the host OS, so Windows artifacts only come out of a Windows host and Linux artifacts out of a Linux host.

**Release prerequisite:** `electron:build` expects a bundled Node runtime in the git-ignored `build/node-node/` directory (no script creates it — place the binary there yourself, matching the build host's OS):

- **Windows builds:** `build/node-node/node.exe` (Node v25)
- **Linux builds (AppImage):** `build/node-node/node-linux` — the plain `node` binary from the official Linux x64 tarball (v25), exec bit intact

Without the matching binary the packaged app silently falls back to Electron's embedded Node, and every API route returns 500. The Linux postbuild check hard-fails an AppImage build that is missing its runtime rather than packaging a broken artifact.

```bash
npm run electron:dev    # next dev + Electron window at localhost:3000
npm run electron:build  # production build → host-OS targets (Windows EXE on Windows)
```

Don't use `electron:build` output for day-to-day testing — it's for cutting releases.


More information in depth will come over time in our [Wiki](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki).

</details>

---

## Contributing

### Community-Driven Development
This project is inspired by [stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader) and thrives on community contributions. Found a bug? Have a workflow that won't parse? Want to add support for a new tool? **We welcome forks, fixes, and pull requests!**

### Found a parsing failure?
Open an issue with the details above. ComfyUI always has edge cases, and while we intend to catch almost everything we can with the lookup on desktop and web, there are always new software tags and nodes.

### Want to improve the parser?
1. Fork repo → `npm install` → `npm run dev`
2. Metadata extraction lives in `app/api/metadata/route.ts`
3. Test with your own images or AI-generated samples
4. Submit a PR with before/after evidence

---

#### Development Disclaimers

<details>
<summary>Click to expand — Development Disclaimers</summary>

This engine has been tested across thousands of images and is in active daily use. While there will always be edge cases with new custom nodes and formats, the core parser is stable and handles the vast majority of real-world workflows. While we are largely no longer in generative AI circles, this application is developed for both sides of the coin. 

We don't want to lie about how the code was created, nor directed. Unlike future projects of ours that are intending to be far more human lead, this took far more human direction than human-based coding. Due to the nature of the original being in python and being a total load of spaghetti code, there was no way we were going to do it again by hand. SD-Prompt Reader was easy to understand, but the edge case detection of most metadata readers falls at simplistic graph traversal. Through absolute insane amounts of research, bashing our heads into walls and throwing ourselves at lawnmowers (Aesthetically not literally) we caught a lot more than the original inspiration as well as our original version. 

We take pride in security, so we do our best to audit with multiple tools, and we're aware of AI-based issues with security, and do our best to monitor dependency issues as well as hallucinatory issues inside the codebase. One singular reason alone Ktiseos Nyx moved to using Next/Node was the idea that it was closer to web development and the nature of typescript was a lot smoother for us to conceptualize than python. This only really covers Duskfallcrew (aka ashbluepollution-95), as they have a graphic design degree not a computer science degree. You try developing a python app when all you understand is how to center a DIV on a web page at 3am. If you run into any issues feel free to use the information on how to contribute, that way we can build better sources together. 

</details>

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
