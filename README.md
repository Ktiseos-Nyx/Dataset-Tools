 # Dataset Tools: An AI Metadata Viewer

<div align="center">



[![Dependency review](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/dependency-review.yml) [![CodeQL](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/github-code-scanning/codeql) ![Build Status](https://img.shields.io/badge/build-passing-brightgreen)

<hr>

[English Readme](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/README.md) [Wiki](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki) [Discussions](https://github.com/Ktiseos-Nyx/Dataset-Tools/discussions) [Notices](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/NOTICE.md) [License](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/LICENSE)

<hr>
 Dataset Tools is a desktop application for browsing and managing AI image datasets with comprehensive metadata extraction. Whether you're organizing generations from A1111, ComfyUI, Civitai, or other tools - or just curious what parameters were used to create that cool image - Dataset Tools has you covered.

Built with Python and PyQt6, it provides an intuitive interface for viewing embedded generation parameters, ComfyUI workflows, model metadata, and even camera EXIF data from non-AI images.

**Community-Driven Development:** This project is inspired by [stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader) and thrives on community contributions. Found a bug? Have a workflow that won't parse? Want to add support for a new tool? **We welcome forks, fixes, and pull requests!** This is a community tool built by the community, for the community.

<hr>

## Contact & Support Us

<hr>

[![GitHub](https://img.shields.io/badge/GitHub-View%20on%20GitHub-181717?logo=github&style=for-the-badge)](https://github.com/Ktiseos-Nyx/Dataset-Tools) [![Discord](https://img.shields.io/discord/1024442483750490222?logo=discord&style=for-the-badge&color=5865F2)](https://discord.gg/HhBSvM9gBY) [![Twitch](https://img.shields.io/badge/Twitch-Follow%20on%20Twitch-9146FF?logo=twitch&style=for-the-badge)](https://twitch.tv/duskfallcrew) <a href="https://ko-fi.com/duskfallcrew" target="_blank"><img src="https://img.shields.io/badge/Support%20us%20on-Ko--Fi-FF5E5B?style=for-the-badge&logo=kofi" alt="Support us on Ko-fi"></a>

</div>

---

**Navigation:**
[Features](#features) •
[Issues](#known-issues) •
[Supported Formats](#supported-formats) •
[Example Images](#example_images) •
[Installation](#installation) •
[Usage](#usage) •
[Themes](#themes) •
[Future Ideas (TODO)](#future-ideas-todo) •
[Contributing](#contributing) •
[License](#license) •
[Acknowledgements](#acknowledgements)

---

## Features

* **Lightweight & Fast:** Designed for quick loading and efficient metadata display with intelligent caching.
* **Cross-Platform:** Built with Python and PyQt6 (compatible with Windows, macOS, Linux).
* **Flexible View Modes:**
  * **Thumbnail Grid View:** Browse images visually with thumbnail previews.
  * **File Tree View:** Navigate folders hierarchically with expandable tree structure.
  * **Resizable Windows:** Adjust window size to your preference - all layouts adapt dynamically.
* **Comprehensive Metadata Viewing:**
  * Clearly displays prompt information (positive, negative, SDXL-specific).
  * Shows detailed generation parameters from various AI tools.
  * **Metadata Editing:** Modify and save image metadata directly in the application.
  * **Non-AI Images:** View EXIF/XMP data from cameras and software (privacy note: we don't extract GPS coordinates - no one needs to know about your Bluetooth spam on macOS 😄).
* **Intuitive File Handling:**
  * **Drag and Drop:** Easily load single image files or entire folders. Dropped files are auto-selected.
  * Folder browsing and file list navigation.
* **Image Preview:** Clear, rescalable preview for selected images.
* **Copy Metadata:** One-click copy of parsed metadata to the clipboard.
* **Themeable UI:** Extensive theme browser with 40+ themes ranging from professional to "Colors Only a Mother Would Love".
* **Advanced Metadata Engine:**
  * **Completely Rebuilt Parser System:** New MetadataEngine with priority-based detection, robust Unicode handling, and comprehensive format support.
  * **Enhanced ComfyUI Support:** Advanced workflow traversal, node connection analysis, and support for modern custom nodes.
  * **CivitAI Integration:** Dual metadata format support with URN resource extraction and **Civitai API integration** (requires API key for enhanced resource data).
  * **Bulletproof Unicode Handling:** Eliminates mojibake issues with comprehensive fallback chains and robust encoding detection.
  * **Intelligent Caching:** Smart metadata caching reduces redundant parsing for faster browsing.
  * **Intelligent Fallback System:** When specialized parsers can't handle a file, the system gracefully falls back to vendored parsers ensuring maximum compatibility.
  * **25+ Specialized Parsers:** Dedicated parsers for various AI tools and platforms with ongoing expansion.
  * **Model File Support:** Enhanced metadata viewing capabilities (Safetensors and GGUF support in progress!).
* **Configurable Logging:** Control application log verbosity for debugging (see [Debug Mode](#debug-mode)).

## Known Issues

*   **Material Theme Compatibility:** The integrated `qt-material` themes, while visually appealing, are not 100% compatible with all PyQt6/Qt6 elements. While the application remains functional, some minor visual inconsistencies may be present. We are actively exploring alternatives and plan to migrate to Tkinter in the near future to address these and other compatibility challenges.
*   **Advanced Parsers** Advanced parsing is about 75% of the way there. Currently we are struggling to get a lot of the T5 style models to parse in ComfyUI. If you or someone you know use ComfyUI and can pass any information about workflows, or what nodes you're currently using that'd be amazing.
*   **Draw Things** The XMP Extractor MIGHT be working, but with limited data on DrawThings and the original vendored code not working at the moment we're unsure of how this is working.

## Supported Formats

Dataset-Tools reads metadata from a comprehensive array of AI generation tools and image sources. We're constantly expanding support as new tools and custom nodes emerge!

**AI Image Generation Tools:**

* **Automatic1111 WebUI / Forge:** PNG (parameters chunk), JPEG/WEBP (UserComment EXIF).
* **ComfyUI:** *(Extraction is never 100% - someone always creates a workflow that breaks things! But we're always working to support the latest custom nodes.)*
  * Standard workflows (PNG "prompt"/"workflow" chunks)
  * FLUX workflows (UNETLoader, ModelSamplingFlux, FluxGuidance)
  * SD3, SDXL, SD1.5 workflows
  * Efficiency Nodes (Efficient Loader, KSampler Efficient)
  * DynamicPrompts (batch generation with wildcards)
  * QuadMoon custom nodes
  * HiDream workflows
  * ComfyRoll ecosystem
  * Griptape workflows
  * PixArt/T5-based models
  * AuraFlow, Lumina, Kolors
  * Advanced samplers (SamplerCustomAdvanced, BasicGuider)
  * Text combiners and prompt manipulation nodes
  * And many more custom node ecosystems!
* **CivitAI Images:**
  * FLUX-generated images (A1111 and ComfyUI formats)
  * A1111-style generations
  * ComfyUI workflows exported from Civitai
  * LoRA trainer outputs
  * **Enhanced with Civitai API:** URN extraction and resource lookups (API key required in Settings)
* **InvokeAI:** PNG/JPEG metadata extraction
* **Draw Things:** XMP metadata support (macOS/iOS)
* **SwarmUI / StableSwarmUI:** PNG/JPEG parameter extraction
* **Fooocus / RuinedFooocus:** Comment and UserComment metadata
* **Easy Diffusion:** Embedded JSON metadata
* **Mochi Diffusion:** macOS-specific format support
* **NovelAI:** PNG (legacy "Software" tag, "Comment" JSON, Stealth LSB alpha channel)
* **Midjourney:** Discord-era metadata formats

**Non-AI Images:**

* **Camera/Photo Metadata:** EXIF, IPTC, XMP data from cameras and photo editing software
* **Privacy Note:** We deliberately don't extract GPS coordinates - your location data stays private!

### Model Files & Other Formats

**Model File Metadata:**

* **`.safetensors`** - ✅ LoRA metadata extraction (if authors left metadata intact!)
* **`.gguf`** - 🚧 In progress, basic support working

**Other File Types:**

* **`.png`**, **`.jpg`**, **`.jpeg`**, **`.webp`** - Full support
* **`.txt`** - Content display
* **`.json`**, **`.toml`** - Content display (structured view planned)

> **Note:** Non-image files may not display thumbnails in grid view yet - we're adding SVG icons for better file type visualization!

## Dependencies

<details>
<summary>Click to expand dependency information</summary>

Dataset-Tools relies on several excellent open-source libraries:

**Core Dependencies:**
* **PyQt6** - GUI framework (cross-platform desktop interface)
* **Pillow (PIL)** - Image processing and metadata extraction
* **pyexiv2** - Advanced EXIF/IPTC/XMP metadata reading (enhanced with pypng integration)
* **pypng** - PNG chunk reading for large ComfyUI workflows
* **piexif** - Additional EXIF manipulation
* **pydantic** - Data validation and settings management
* **rich** - Beautiful terminal output and logging
* **toml** - Configuration file parsing
* **requests** - HTTP requests for Civitai API integration

**Optional Enhancements:**
* **qt-material** - Material Design themes
* **QSS stylesheets** - Custom theme support

All dependencies are automatically installed via pip. See [Installation](#installation) for details.

</details>

## Example Images
 If you're interested in seeing the app in action, this table shows what's up! 

| Screenshot 1: Dark QSS Themes | Screenshot 2: ConsoleStyle Gtronicks QSS | Screenshot 3: Font Choices |
| :-----------------------------: | :------------------------------: | :--------------------------: |
| <img src="example_images/Screenshot 2025-07-13 at 22.07.43.jpg" alt="GTRONICK QSS: Manjaromix" width="250"> | <img src="example_images/Screenshot 2025-07-13 at 20.02.22.jpg" alt="ConsoleStyle" width="250"> | <img src="example_images/Screenshot 2025-07-13 at 22.07.01.jpg" alt="Theme (Dark Teal) Choosing" width="250"> |
| Screenshot 4: Paimon Inspired | Screenshot 5: Material Blue | Screenshot 6: Deadpool Inspired |
| <img src="example_images/Screenshot 2025-07-13 at 20.01.54.jpg" alt="Screen Sizes" width="250"> | <img src="example_images/Screenshot 2025-07-13 at 20.01.15.jpg" alt="Civitai Metadata" width="250"> |  <img src="example_images/Screenshot 2025-07-13 at 22.13.02.jpg" alt="Civitai Metadata" width="250">|

## Installation

Installation is easy and is cross platform, there are no executables as those can create issues down the track when the developer isn't sure how that works. At the moment while we're still under heavy development the idea of having executables is months if not nearly a year down the track. However plans to push to package management systems beyond PYPI are entirely on track. Brew requirements will be the next push we work towards, as well as Windows and Linux compatible package managers!

### 🚀 Quick Install (Recommended)

**One command and you're done:**

```bash
pip install kn-dataset-tools
dataset-tools
```

**Requirements:** Python 3.10 or newer

That's it! The tool will launch with a GUI interface for viewing AI metadata.

---

### 📦 Install from Source

If you want the latest development version:

```bash
git clone https://github.com/Ktiseos-Nyx/Dataset-Tools.git
cd Dataset-Tools
pip install .
dataset-tools
```

---

### 🔧 Advanced Installation (Optional)

For developers or users who prefer isolated environments:

<details>
<summary>Click to expand advanced options</summary>

**Using virtual environments:**

```bash
# Create virtual environment
python -m venv dataset-tools-env

# Activate it
# Windows: dataset-tools-env\Scripts\activate
# macOS/Linux: source dataset-tools-env/bin/activate

# Install
pip install kn-dataset-tools
```

**Using uv (fastest):**

```bash
uv pip install kn-dataset-tools
```

**For contributors:**

```bash
git clone https://github.com/Ktiseos-Nyx/Dataset-Tools.git
cd Dataset-Tools
pip install -e .  # Editable install for development
```

</details>

---

### 🆚 vs SD Prompt Reader

Unlike SD Prompt Reader which focuses on basic prompt viewing, Dataset Tools provides:

* Advanced ComfyUI workflow analysis
* LoRA training metadata extraction
* 25+ specialized AI format parsers
* Model file support (SafeTensors, GGUF)
* Comprehensive metadata engine

**Both tools are great!** Use whichever fits your workflow better.

## Usage

### Launching the Application

**After installation, run the application from your terminal:**

```bash
dataset-tools
```

That's it! The GUI will launch and you can start browsing your AI image datasets.

### Debug Mode

Need to troubleshoot extraction issues or report a bug? Enable verbose logging:

```bash
# Full debug output (most verbose)
dataset-tools --log-level DEBUG

# Or use short form
dataset-tools --log-level d

# Other log levels available
dataset-tools --log-level INFO     # Default - normal operation
dataset-tools --log-level WARNING  # Warnings only
dataset-tools --log-level ERROR    # Errors only
```

Debug logs show detailed parser decisions, node detection, and extraction steps - perfect for figuring out why a specific workflow isn't parsing correctly!

#### GUI Interaction

**Loading Files:**

1. Click the "Open Folder" button or use the File > Change Folder... menu option.
2. Drag and Drop: Drag a single image/model file or an entire folder directly onto the application window.
3. If a single file is dropped, its parent folder will be loaded, and the file will be automatically selected in the list.
4. If a folder is dropped, that folder will be loaded.

**Navigation:**

1. **Select files** from the list/tree view to view their details
2. **View Modes:**
   * **Thumbnail Grid:** Visual browsing with image previews
   * **File Tree:** Hierarchical folder navigation
   * Switch between modes via the View menu
3. **Image Preview:**
   * Selected images display in the preview pane
   * Zoom, pan, and resize as needed
   * Non-image files show "No preview available"
4. **Metadata Display:**
   * **Prompt Info:** Positive and negative prompts
   * **Generation Parameters:** Steps, sampler, CFG, seed, model, etc.
   * **Raw Workflow:** Full ComfyUI workflow JSON (when available)
   * **Edit Metadata:** Click Edit button to modify and save metadata
5. **Copy Metadata:** One-click copy to clipboard
6. **Settings & Configuration:**
   * **Themes:** Access via Settings button or View > Themes menu
   * **Civitai API Key:** Enter in Settings for enhanced resource data
   * **Window Size:** All layouts are resizable - stretch to fit your workflow!
   * **Font Preferences:** Customize text display

### Themes

Dataset-Tools comes with **40+ themes** accessible through the built-in theme browser:

* **Professional themes** for serious work
* **Material Design** themes for modern aesthetics
* **Retro/Console themes** for that nostalgic terminal vibe
* **Meme themes** like "Colors Only a Mother Would Love" (yes, really)
* **Custom themes** - Add your own QSS stylesheets to the themes folder!

Access themes via `View > Themes` menu or the Settings button. Our theme collection ranges from beautiful to... questionable. No judgment - use what makes you happy!

**Theme Credits:**
* [GTRONICK](https://github.com/GTRONICK/QSS) - QSS themes
* [Unreal Stylesheet](https://github.com/leixingyu/unrealStylesheet) - Unreal Engine-inspired themes
* [Dunderlab Qt-Material](https://github.com/dunderlab/qt-material) - Material Design themes
* [QSS Themes Repository](https://github.com/Ktiseos-Nyx/qss_themes/) - Our custom collection

See [NOTICE.md](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/NOTICE.md) for full theme licensing and attribution.

### Future Development Roadmap

**Core Features:**

* [ ] **Model File Support:** Complete Safetensors and GGUF metadata display and editing capabilities.
* [ ] **Full Metadata Editing:** Advanced editing and saving capabilities for image metadata.
* [ ] **Plugin Architecture:** Extensible plugin system for easy addition of custom parsers and functionality.
* [ ] **Batch Operations:** Export metadata from folders, rename files based on metadata, bulk processing.
* [ ] **Advanced Search & Filtering:** Dataset search and filtering based on metadata content and parameters.

**User Experience:**

* [ ] **Enhanced UI/UX:** Improved prompt display, better text file viewing with syntax highlighting. (Planned migration to Tkinter for improved cross-platform compatibility and UI consistency.)
* [ ] **Theme System Expansion:** Additional themes and customization options.
* [ ] **Keyboard Shortcuts:** Comprehensive hotkey support for power users.

**Platform & Integration:**

* [ ] **Standalone Executables:** Native builds for Windows, macOS, and Linux.
* [ ] **PyPI Distribution:** Official package distribution for easy `pip install dataset-tools`.
* [ ] **CivitAI API Integration:** Direct model and resource lookup capabilities.
* [ ] **Cross-Platform Compatibility:** Enhanced support across different operating systems.

**Technical Improvements:**

* [ ] **Comprehensive Test Suite:** Automated testing to ensure stability and prevent regressions.
* [ ] **Enhanced Format Support:** Additional AI tool formats and metadata standards.
* [ ] **Performance Optimization:** Faster loading and processing for large datasets.
* [ ] **Error Handling:** Improved error reporting and recovery mechanisms.

**Ecosystem Integration:**

* [ ] **Dataset Management Tools:** Integration with HuggingFace, model downloaders, and conversion utilities.
* [ ] **Workflow Integration:** Support for AI generation workflows and pipeline management.
* [ ] **Community Features:** Parser sharing, format contribution system.

## Contributing

**We welcome forks, fixes, and experiments!** Dataset-Tools is a community project - feel free to:

* **Fork it** and make it your own
* **Break it** and see what happens (then tell us about it!)
* **Fix it** when you find bugs
* **Extend it** with new parsers or features
* **Share it** with others who might find it useful

### How to Contribute

**Found a Bug?**
* Check the [Issues](https://github.com/Ktiseos-Nyx/Dataset-Tools/issues) tab to see if it's already reported
* If not, open a new issue with:
  * Clear description of the problem
  * Steps to reproduce
  * Example images (if it's a parsing issue)
  * Log output with `--log-level DEBUG` enabled

**Want to Add Support for a New Tool/Node?**
* Share example images with metadata in a GitHub issue
* Tell us about the workflow structure
* We're always hunting for new ComfyUI custom nodes to support!

**Code Contributions:**
1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature-name`
3. Make your changes with clear commit messages
4. Push to your fork: `git push origin feature/your-feature-name`
5. Submit a pull request with a description of your changes

**ComfyUI Node Support:**
> **Reality check:** ComfyUI extraction is never 100% finished. Someone always creates a workflow, uses it, sends us the images, and... it breaks. 😂 But we're always working to support the latest nodes! If you have workflows that aren't parsing correctly, please share them so we can add support.

No contribution is too small - typo fixes, documentation improvements, and questions are all valuable!

## License

This project is licensed under the terms of the GNU GENERAL PUBLIC LICENSE [GPL 3.0](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/Themes-Lost-Dreams/LICENSE)
Please see the LICENSE file in the repository root for the full license text.

## Acknowledgements

* Core Parsing Logic & Inspiration: This project incorporates and significantly adapts parsing functionalities from Stable Diffusion Prompt Reader by  **[receyuki](https://github.com/receyuki)** . Our sincere thanks for this foundational work.
      Original Repository: [stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader)
      The original MIT license for this vendored code is included in the NOTICE.md file.
* UI Theming: The beautiful PyQt themes are made possible by [qt-material](https://github.com/dunderlab/qt-material) by [DunderLab](https://github.com/dunderlab) as well as GTRONICK - [GTRONICKS](https://github.com/GTRONICK/QSS) and the UNREAL STYLE SHEET Creator [UNREAL STYLESHEET](https://github.com/leixingyu/unrealStylesheet)
* Essential Libraries: This project relies on great open-source Python libraries including [Pillow,](https://github.com/python-pillow/Pillow), [PyQt6](https://www.riverbankcomputing.com/software/pyqt/), [piexif](https://github.com/hMatoba/Piexif), [pyexiv2](https://github.com/LeoHsiao1/pyexiv2), [toml](https://github.com/uiri/toml), [Pydantic](https://docs.pydantic.dev/latest/), and [Rich](https://github.com/Textualize/rich). Their respective licenses apply.
* **[Anzhc](https://github.com/anzhc)** for continued support and motivation.
* Our peers and the wider AI and open-source communities for their continuous support and inspiration.
* AI Language Models (like those from Google, OpenAI, Anthropic) for assistance with code generation, documentation, and problem-solving during development.
* ...and many more!

<hr>

## Support Us

If you find Dataset Tools useful, please consider supporting the creators!

<a href="https://discord.gg/HhBSvM9gBY" target="_blank"><img src="https://img.shields.io/badge/Join%20us%20on-Discord-5865F2?style=for-the-badge&logo=discord" alt="Join us on Discord"></a>
<a href="https://ko-fi.com/duskfallcrew" target="_blank"><img src="https://img.shields.io/badge/Support%20us%20on-Ko--Fi-FF5E5B?style=for-the-badge&logo=kofi" alt="Support us on Ko-fi"></a>
<a href="https://twitch.tv/duskfallcrew" target="_blank"><img src="https://img.shields.io/badge/Follow%20us%20on-Twitch-9146FF?style=for-the-badge&logo=twitch" alt="Follow us on Twitch"></a>

<hr>
