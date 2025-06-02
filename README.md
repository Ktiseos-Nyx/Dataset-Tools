<div align="center">
     <h1>Dataset Tools: An AI Metadata Viewer</h1>
     
[![Dependency review](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/dependency-review.yml) [![CodeQL](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/github-code-scanning/codeql) ![Build Status](https://img.shields.io/badge/build-passing-brightgreen)

<hr>

[English Readme](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/README.md) [Wiki](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki) [Discussions](https://github.com/Ktiseos-Nyx/Dataset-Tools/discussions) [Notices](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/NOTICE.md) [License](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/LICENSE) 

<hr>
 Dataset Tools is a desktop application designed to help users browse and manage their image datasets, particularly those used with AI art generation tools (like Stable Diffusion WebUI Forge, A1111, ComfyUI) and model files (like Safetensors). Developed using Python and PyQt6, it provides an intuitive graphical interface for browsing files, viewing embedded generation parameters, and examining associated metadata.

This project is inspired by tools within the AI art community, notably [stable-diffusion-prompt-reader by receyuki](https://github.com/receyuki/stable-diffusion-prompt-reader), and aims to empower users in improving their dataset curation workflow. We welcome contributions; feel free to fork the repository and submit pull requests!

<hr>

## Contact & Support Us: 

<hr>

[![GitHub](https://img.shields.io/badge/GitHub-View%20on%20GitHub-181717?logo=github&style=for-the-badge)](https://github.com/Ktiseos-Nyx/Dataset-Tools) [![Discord](https://img.shields.io/discord/1024442483750490222?logo=discord&style=for-the-badge&color=5865F2)](https://discord.gg/5t2kYxt7An) [![Twitch](https://img.shields.io/badge/Twitch-Follow%20on%20Twitch-9146FF?logo=twitch&style=for-the-badge)](https://twitch.tv/duskfallcrew) <a href="https://ko-fi.com/duskfallcrew" target="_blank"><img src="https://img.shields.io/badge/Support%20us%20on-Ko--Fi-FF5E5B?style=for-the-badge&logo=kofi" alt="Support us on Ko-fi"></a>

</div>

---

**Navigation:**
[Features](#features) •
[Supported Formats](#supported-formats) •
[Installation](#installation) •
[Usage](#usage) •
[Example Images](#Example_Images)  •
[Future Ideas (TODO)](#future-ideas-todo) •
[Contributing](#contributing) •
[License](#license) •
[Acknowledgements](#acknowledgements)


---

## Features

*   **Lightweight & Fast:** Designed for quick loading and efficient metadata display.
*   **Cross-Platform:** Built with Python and PyQt6 (compatible with Windows, macOS, Linux).
*   **Comprehensive Metadata Viewing:**
    *   Clearly displays prompt information (positive, negative, SDXL-specific).
    *   Shows detailed generation parameters from various AI tools.
*   **Intuitive File Handling:**
    *   **Drag and Drop:** Easily load single image files or entire folders. Dropped files are auto-selected.
    *   Folder browsing and file list navigation.
*   **Image Preview:** Clear, rescalable preview for selected images.
*   **Copy Metadata:** One-click copy of parsed metadata to the clipboard.
*   **Themeable UI:** Supports themes via `qt-material` (e.g., dark_pink, light_lightgreen_500).
*   **Extensible Parser System:**
    *   Utilizes a significantly adapted and enhanced version of `sd-prompt-reader` for robust parsing of many common AI image metadata formats.
    *   **New Custom Parsers:** Includes dedicated parsers for:
        *   `RuinedFooocus` (UserComment JSON).
        *   `Civitai ComfyUI` (UserComment JSON with "extraMetadata").
    *   **Model File Support:** Basic metadata viewing for `.safetensors` and `.gguf` model files.
*   **Configurable Logging:** Control application log verbosity via command-line arguments for easier debugging.

## Supported Formats

Dataset-Tools aims to read metadata from a wide array of sources. Current capabilities include:

**AI Image Metadata:**
*   **A1111 webUI / Forge:** PNG (parameters chunk), JPEG/WEBP (UserComment).
*   **ComfyUI:**
    *   Standard PNGs (embedded workflow JSON in "prompt" chunk).
    *   Civitai-generated JPEGs/PNGs (UserComment JSON with "extraMetadata").
*   **NovelAI:** PNG (Legacy "Software" tag & "Comment" JSON; Stealth LSB in alpha channel).
*   **InvokeAI:** PNG (parsing "invokeai_metadata", "sd-metadata", or "Dream" chunks).
*   **Easy Diffusion:** PNG, JPEG, WEBP (embedded JSON metadata).
*   **Fooocus:** PNG ("Comment" chunk JSON), JPEG (JFIF comment JSON).
*   **RuinedFooocus:** JPEG (UserComment JSON).
*   **Draw Things:** PNG (XMP metadata containing JSON).
*   **StableSwarmUI:** PNG, JPEG (EXIF or "sui_image_params" in PNG/UserComment).
*   *(Support for other formats may be implicitly included via the adapted sd-prompt-reader core.)*

**Model File Metadata (Header Information):**
*   `.safetensors`
*   `.gguf`

**Other File Types:**
*   `.txt`: Displays content.
*   `.json`, `.toml`: Displays content (future: structured view).

## Installation

**Prerequisites:**
*   Python 3.11 (as this was the version used during development and for dependency resolution). Other Python 3.9+ versions might work but are not extensively tested.
*   `pip` (Python package installer).
*   `git` (for cloning the repository).

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Ktiseos-Nyx/Dataset-Tools.git
    cd Dataset-Tools
    ```

2.  **Create and activate a Python virtual environment (recommended):**
    ```bash
    python3.11 -m venv .venv 
    # Or: python -m venv .venv

    # Activate:
    # Windows: .venv\Scripts\activate
    # macOS/Linux (bash/zsh): source .venv/bin/activate
    # macOS/Linux (fish): source .venv/bin/activate.fish
    ```

3.  **Install the package and its dependencies:**
    The project uses `pyproject.toml` and can be installed using pip.
    ```bash
    # For users (standard install):
    pip install .

    # For developers (editable install, recommended for contributing):
    pip install -e .
    ```
    This command will read `pyproject.toml` and install `Dataset-Tools` along with all libraries listed as dependencies (e.g., `PyQt6`, `Pillow`, `qt-material`, `piexif`, `pyexiv2`, `toml`, `rich`, `pydantic`).

## Usage

### Launching the Application

**After installation, run the application from your terminal:**
  
```bash
    python -m dataset_tools.main [options]
```
####  Command-line Options:

> [!TIP]
> 
> ```bash
>     --log-level LEVEL: Sets the logging verbosity.
> ```
> Choices: DEBUG, INFO (default), WARNING, ERROR, CRITICAL.
> Short forms: d, i, w, e, c (case-insensitive).
> ```bash
>    Example: python -m dataset_tools.main --log-level DEBUG
> ```

#### GUI Interaction

**Loading Files:**

1.  Click the "Open Folder" button or use the File > Change Folder... menu option.
2.  Drag and Drop: Drag a single image/model file or an entire folder directly onto the application window.
3.  If a single file is dropped, its parent folder will be loaded, and the file will be automatically selected in the list.
4.  If a folder is dropped, that folder will be loaded.


**Navigation:**
1. Select files from the list on the left panel to view their details.
   *  Image Preview:
         Selected images are displayed in the preview area on the right.
         Non-image files or files that cannot be previewed will show a "No preview available" message.
   *  Metadata Display:
         Parsed prompts (Positive, Negative), generation parameters (Steps, Sampler, CFG, Seed, etc.), and other relevant metadata are shown in the text areas below/beside the image preview.
         The Prompt Info and Generation Info section titles will update based on the content found.
   *  Copy Metadata:
         Use the "Copy Metadata" button to copy the currently displayed parsed metadata (from the text areas) to your system clipboard.
   *  File List Actions:
         Sort Files: Click the "Sort Files" button to sort the items in the file list alphabetically by type (images, then text, then models).
   *  Settings & Themes:
         Access application settings (e.g., display theme, window size preferences) via the "Settings..." button at the bottom or the View > Themes menu for quick theme changes.

## Example Images

| Screenshot 1: Light Green Theme | Screenshot 2: Options Display (Light Green) | Screenshot 3: Theme (Dark Teal) Choosing |
| :-----------------------------: | :------------------------------: | :--------------------------: |
| <img src=".github/Github Screenshots/Screenshot 2025-05-26 at 19.44.11.png" alt="Light Green Theme" width="250"> | <img src=".github/Github Screenshots/Screenshot 2025-05-26 at 19.43.39.png" alt="Options Display (Light Green)" width="250"> | <img src=".github/Github Screenshots/Screenshot 2025-05-26 at 19.43.31.png" alt="Theme (Dark Teal) Choosing" width="250"> |
| Screenshot 4: Screen Sizes | Screenshot 5: Civitai Metadata | |
| <img src=".github/Github Screenshots/Screenshot 2025-05-26 at 19.43.21.png" alt="Screen Sizes" width="250"> | <img src=".github/Github Screenshots/Screenshot 2025-05-26 at 19.43.10.png" alt="Civitai Metadata" width="250"> |

### Future Ideas (TODO)

- [ ] Enhanced metadata display and editing for model files (.safetensors, .gguf).
- [ ] Full metadata editing and saving capabilities for images.
- [ ] Batch operations: e.g., export all metadata from a folder, rename files based on metadata.
- [ ] Advanced search and filtering capabilities within loaded datasets based on metadata content.
- [ ] Support for more image, text, and model metadata formats.
- [ ] A plugin architecture to allow for easier addition of custom parsers or functionalities.
- [ ] Improved UI/UX for text/schema file viewing (e.g., syntax highlighting for JSON/TOML, better text wrapping).
- [ ] Packaging for PyPI for easier pip install dataset-tools.
- [ ] Creation of standalone executables for Windows, macOS, and Linux.
- [ ] Comprehensive automated test suite to ensure stability and prevent regressions.

## Contributing
Your contributions are welcome! Whether it's bug reports, feature requests, documentation improvements, or code contributions, please feel free to get involved.
   *  Issues: Please check the issues tab for existing bugs or ideas. If you don't see your issue, please open a new one with a clear description and steps to reproduce (for bugs).
   *  Pull Requests:
         Fork the repository.
         Create a new branch for your feature or bugfix (git checkout -b feature/your-feature-name or bugfix/issue-number).
         Make your changes and commit them with clear, descriptive messages.
         Push your branch to your fork (git push origin feature/your-feature-name).
         Submit a pull request to the main branch of the Ktiseos-Nyx/Dataset-Tools repository. Please provide a clear description of your changes in the PR.
## License
This project is licensed under the terms of the <YOUR_NEW_LICENSE_NAME_HERE, e.g., Apache License 2.0 / MIT License / etc.>
Please see the LICENSE file in the repository root for the full license text.


## Acknowledgements
   *  Core Parsing Logic & Inspiration: This project incorporates and significantly adapts parsing functionalities from Stable Diffusion Prompt Reader by  **[receyuki](https://github.com/receyuki)** . Our sincere thanks for this foundational work.
      Original Repository: [stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader)
      The original MIT license for this vendored code is included in the NOTICE.md file.
   *  UI Theming: The beautiful PyQt themes are made possible by [qt-material](https://github.com/dunderlab/qt-material) by [DunderLab](https://github.com/dunderlab)
   *  Essential Libraries: This project relies on great open-source Python libraries including [Pillow,](https://github.com/python-pillow/Pillow), [PyQt6](https://www.riverbankcomputing.com/software/pyqt/), [piexif](https://github.com/hMatoba/Piexif), [pyexiv2](https://github.com/LeoHsiao1/pyexiv2), [toml](https://github.com/uiri/toml), [Pydantic](https://docs.pydantic.dev/latest/), and [Rich](https://github.com/Textualize/rich). Their respective licenses apply.
   *  **[Anzhc](https://github.com/anzhc)** for continued support and motivation.
   *  Our peers and the wider AI and open-source communities for their continuous support and inspiration.
   *  AI Language Models (like those from Google, OpenAI, Anthropic) for assistance with code generation, documentation, and problem-solving during development.
   *  ...and many more!
<hr>

## Support Us

If you find Dataset Tools useful, please consider supporting the creators!

<a href="https://discord.gg/5t2kYxt7An" target="_blank"><img src="https://img.shields.io/badge/Join%20us%20on-Discord-5865F2?style=for-the-badge&logo=discord" alt="Join us on Discord"></a>
<a href="https://ko-fi.com/duskfallcrew" target="_blank"><img src="https://img.shields.io/badge/Support%20us%20on-Ko--Fi-FF5E5B?style=for-the-badge&logo=kofi" alt="Support us on Ko-fi"></a>
<a href="https://twitch.tv/duskfallcrew" target="_blank"><img src="https://img.shields.io/badge/Follow%20us%20on-Twitch-9146FF?style=for-the-badge&logo=twitch" alt="Follow us on Twitch"></a>

<hr>
