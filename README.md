 # Dataset Tools: An AI Metadata Viewer

<div align="center">



[![Dependency review](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/dependency-review.yml) [![CodeQL](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/github-code-scanning/codeql) ![Build Status](https://img.shields.io/badge/build-passing-brightgreen)

<hr>

[English Readme](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/README.md) [Wiki](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki) [Discussions](https://github.com/Ktiseos-Nyx/Dataset-Tools/discussions) [Notices](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/NOTICE.md) [License](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/LICENSE)

<hr>
 Dataset Tools is a desktop application designed to help users browse and manage their image datasets, particularly those used with AI art generation tools (like Stable Diffusion WebUI Forge, A1111, ComfyUI) and model files (like Safetensors). Developed using Python and PyQt6, it provides an intuitive graphical interface for browsing files, viewing embedded generation parameters, and examining associated metadata.

This project is inspired by tools within the AI art community, notably [stable-diffusion-prompt-reader by receyuki](https://github.com/receyuki/stable-diffusion-prompt-reader), and aims to empower users in improving their dataset curation workflow. We welcome contributions; feel free to fork the repository and submit pull requests!

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

* **Lightweight & Fast:** Designed for quick loading and efficient metadata display.
* **Cross-Platform:** Built with Python and PyQt6 (compatible with Windows, macOS, Linux).
* **Comprehensive Metadata Viewing:**
  * Clearly displays prompt information (positive, negative, SDXL-specific).
  * Shows detailed generation parameters from various AI tools.
* **Intuitive File Handling:**
  * **Drag and Drop:** Easily load single image files or entire folders. Dropped files are auto-selected.
  * Folder browsing and file list navigation.
* **Image Preview:** Clear, rescalable preview for selected images.
* **Copy Metadata:** One-click copy of parsed metadata to the clipboard.
* **Themeable UI:** Supports themes via `qt-material` (e.g., dark_pink, light_lightgreen_500).
* **Advanced Metadata Engine:**
  * **Completely Rebuilt Parser System:** New MetadataEngine with priority-based detection, robust Unicode handling, and comprehensive format support.
  * **Enhanced ComfyUI Support:** Advanced workflow traversal, node connection analysis, and support for modern custom nodes (smZ CLIPTextEncode, etc.).
  * **CivitAI Integration:** Full support for CivitAI's dual metadata formats with URN resource extraction and workflow parsing.
  * **Bulletproof Unicode Handling:** Eliminates mojibake issues with comprehensive fallback chains and robust encoding detection.
  * **A1111 Format Restoration:** Fixed and enhanced A1111 JPEG support with improved detection rules.
  * **Intelligent Fallback System:** When specialized parsers can't handle a file, the system gracefully falls back to vendored parsers ensuring maximum compatibility.
  * **25+ Specialized Parsers:** Dedicated parsers for various AI tools and platforms with ongoing expansion.
  * **Model File Support:** Enhanced metadata viewing capabilities (Safetensors and GGUF support coming soon!).
* **Configurable Logging:** Control application log verbosity via command-line arguments for easier debugging.

## Known Issues

*   **Material Theme Compatibility:** The integrated `qt-material` themes, while visually appealing, are not 100% compatible with all PyQt6/Qt6 elements. While the application remains functional, some minor visual inconsistencies may be present. We are actively exploring alternatives and plan to migrate to Tkinter in the near future to address these and other compatibility challenges.
*   **Advanced Parsers** Advanced parsing is about 75% of the way there. Currently we are struggling to get a lot of the T5 style models to parse in ComfyUI. If you or someone you know use ComfyUI and can pass any information about workflows, or what nodes you're currently using that'd be amazing.
*   **Draw Things** The XMP Extractor MIGHT be working, but with limited data on DrawThings and the original vendored code not working at the moment we're unsure of how this is working.

## Supported Formats

Dataset-Tools aims to read metadata from a wide array of sources. Current capabilities include:

**AI Image Metadata:**

* **A1111 webUI / Forge:** PNG (parameters chunk), JPEG/WEBP (UserComment).
* **ComfyUI:**
  * Standard PNGs (embedded workflow JSON in "prompt" chunk).
  * Civitai-generated JPEGs/PNGs (UserComment JSON with "extraMetadata").
  * **Advanced ComfyUI Workflows:** While many workflows are supported, some complex or custom ComfyUI workflows may not be fully parsed yet. We are continuously working to improve compatibility. Please provide examples of unparsed workflows to help us improve!
* **NovelAI:** PNG (Legacy "Software" tag & "Comment" JSON; Stealth LSB in alpha channel).
* **Midjourney** Popularity rules! This is the old. gold standard of the old discord way (Shh I wrote this at 1 am)
* **InvokeAI:** (Currently undergoing refactoring, may not parse correctly in this version. Fixes planned for next major push.)
* **Easy Diffusion:** PNG, JPEG, WEBP (embedded JSON metadata).
* **Fooocus:** PNG ("Comment" chunk JSON), JPEG (JFIF comment JSON).
* **Midjourney** YAY
* **RuinedFooocus:** JPEG (UserComment JSON).
* **Draw Things:** (Currently undergoing refactoring, may not parse correctly in this version. Fixes planned for next major push.)
* **StableSwarmUI:** PNG, JPEG (EXIF or "sui_image_params" in PNG/UserComment).
* *(Support for other formats may be on the way, please see issues and/or discussions for details)*

### File Types that are COMING SOON AND/or have partial capability

**Model File Metadata (Header Information):**

* `.safetensors`
* `.gguf`

**Other File Types:**

* `.txt`: Displays content.
* `.json`, `.toml`: Displays content (future: structured view).

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

```bash
    python dataset_tools
```

**After installation, run the application from your terminal:**

 ```bash
    dataset-tools
  ```

#### Advanced Command-line Options

  ```bash
   python -m dataset_tools.main [options]
  ```

> [!TIP]
>
> ```bash
>     --log-level LEVEL: Sets the logging verbosity.
> ```
>
> Choices: DEBUG, INFO (default), WARNING, ERROR, CRITICAL.
> Short forms: d, i, w, e, c (case-insensitive).
>
> ```bash
>    Example: python -m dataset_tools.main --log-level DEBUG
> ```

#### GUI Interaction

**Loading Files:**

1. Click the "Open Folder" button or use the File > Change Folder... menu option.
2. Drag and Drop: Drag a single image/model file or an entire folder directly onto the application window.
3. If a single file is dropped, its parent folder will be loaded, and the file will be automatically selected in the list.
4. If a folder is dropped, that folder will be loaded.

**Navigation:**

1. Select files from the list on the left panel to view their details.
   * Image Preview:
         Selected images are displayed in the preview area on the right.
         Non-image files or files that cannot be previewed will show a "No preview available" message.
   * Metadata Display:
         Parsed prompts (Positive, Negative), generation parameters (Steps, Sampler, CFG, Seed, etc.), and other relevant metadata are shown in the text areas below/beside the image preview.
         The Prompt Info and Generation Info section titles will update based on the content found.
   * Copy Metadata:
         Use the "Copy Metadata" button to copy the currently displayed parsed metadata (from the text areas) to your system clipboard.
   * File List Actions:
         Sort Files: Click the "Sort Files" button to sort the items in the file list alphabetically by type (images, then text, then models).
   * Settings & Themes:
         Access application settings (e.g., display theme, window size preferences) via the "Settings..." button at the bottom or the View > Themes menu for quick theme changes.

### Themes

A massive selection of horrifying and eye catching, eye tearing, and meme worthy themes are currently available in the app in QSS form for the PYQT6 branch only.
Future development will include Tkinter themes in a similar format. Please note, that the main developer of this app has 0 clue how QSS entirely works, and just wanted to provide some good and some bad themes.
You can use these for yourself by heading over to [QSS Themes](https://github.com/Ktiseos-Nyx/qss_themes/). You should be able to use your own QSS style sheets in the themes folder. Our insanity is not required, and you do not have to thank us.
Yes, theres is a disclaimer file for theme information and we do not own any of the names, brands or concepts within them. Nor are we intentionally being offensive, trust me on this - nobody will shame you for using the theme "Colors only a Mother Would Love" you know you want to.

We are also using the following imported themes:

* [GTRONICKS](https://github.com/GTRONICK/QSS)
* [UNREAL STYLESHEET](https://github.com/leixingyu/unrealStylesheet)
* [DUNDERLAB QT MATERIAL STYLESHEETS](https://github.com/dunderlab/qt-material)

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

Your contributions are welcome! Whether it's bug reports, feature requests, documentation improvements, or code contributions, please feel free to get involved.

* Issues: Please check the issues tab for existing bugs or ideas. If you don't see your issue, please open a new one with a clear description and steps to reproduce (for bugs).
* Pull Requests:
         Fork the repository.
         Create a new branch for your feature or bugfix (git checkout -b feature/your-feature-name or bugfix/issue-number).
         Make your changes and commit them with clear, descriptive messages.
         Push your branch to your fork (git push origin feature/your-feature-name).
         Submit a pull request to the main branch of the Ktiseos-Nyx/Dataset-Tools repository. Please provide a clear description of your changes in the PR.

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
