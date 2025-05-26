![Build Status](https://img.shields.io/badge/build-passing-brightgreen) 

[![GitHub](https://img.shields.io/badge/GitHub-View%20on%20GitHub-181717?logo=github&style=for-the-badge)](https://github.com/Ktiseos-Nyx/Dataset-Tools) [![Discord](https://img.shields.io/discord/1024442483750490222?logo=discord&style=for-the-badge&color=5865F2)](https://discord.gg/5t2kYxt7An) [![Twitch](https://img.shields.io/badge/Twitch-Follow%20on%20Twitch-9146FF?logo=twitch&style=for-the-badge)](https://twitch.tv/duskfallcrew)

<hr>

# Dataset Tools: An AI Metadata Viewer

<p align="center">
  <img src="https://github.com/user-attachments/assets/f8b4187b-2603-4bae-aa4a-dc3f621b5696" alt="Dataset Tools Screenshot" width="700">
</p>

Dataset Tools is a desktop application designed to help users browse and manage their image datasets, particularly those used with AI art generation tools (like Stable Diffusion WebUI Forge, A1111, ComfyUI) and model files (like Safetensors). Developed using Python and PyQt6, it provides an intuitive graphical interface for browsing files, viewing embedded generation parameters, and examining associated metadata.

This project is inspired by tools within the AI art community, notably [stable-diffusion-prompt-reader by receyuki](https://github.com/receyuki/stable-diffusion-prompt-reader), and aims to empower users in improving their dataset curation workflow. We welcome contributions; feel free to fork the repository and submit pull requests!

<hr>

## Contents

*   [How to Use Dataset Tools](#how-to-use-dataset-tools)
    *   [Requirements](#requirements)
    *   [Installation & Launching](#installation--launching-the-application)
*   [User Interface Overview](#user-interface-overview)
*   [Key Features](#key-features)
*   [Future Developments](#future-developments)
*   [License](#license)
*   [Acknowledgments](#acknowledgments)
*   [Support Us](#support-us)

<hr>

## How to Use Dataset Tools

### Requirements

*   **Python:** Version 3.10 or newer. You can download it from [Python.org](https://www.python.org/downloads/).
    *   (Optional) For faster environment and package management, consider [uv](https://github.com/astral-sh/uv).
    *   *Note for Linux users:* Some system Pythons might require additional development headers (e.g., `python3-dev`, `python3-tk`) for all features or dependencies to build correctly.
*   **Git:** Required for cloning the repository. Installation instructions: [Windows](https://gitforwindows.org/), [macOS](https://git-scm.com/downloads/mac) (or via [Homebrew](https://brew.sh/)), [Linux](https://git-scm.com/downloads/linux).

<hr>

### Installation & Launching the Application

1.  **Open your terminal** (e.g., PowerShell, Command Prompt, Terminal, Konsole).

2.  **Clone the repository:**
    ```sh
    git clone https://github.com/Ktiseos-Nyx/Dataset-Tools.git
    cd Dataset-Tools
    ```

3.  **Set up a Python virtual environment (Recommended):**
    ```sh
    python -m venv .venv 
    # Activate it:
    # Windows (cmd.exe): .venv\Scripts\activate.bat
    # Windows (PowerShell): .venv\Scripts\Activate.ps1
    # macOS/Linux (bash/zsh): source .venv/bin/activate
    # macOS/Linux (fish): source .venv/bin/activate.fish 
    ```

4.  **Install the application and its dependencies:**
    ```sh
    # If using standard pip:
    pip install . 
    # For development (changes to code are reflected immediately):
    # pip install -e .
    ```
    > **Note for `uv` users:**
    > ```sh
    > uv pip install .
    > # Or for development:
    > # uv pip install -e .
    > ```

5.  **Run the application:**
    ```sh
    dataset-tools
    ```
    (If the command isn't found, ensure your virtual environment's `bin` or `Scripts` directory is in your PATH, or run `python -m dataset_tools.main` from the project root.)

<hr>

## User Interface Overview

The application window is divided into a few main sections:

*   **Left Panel:**
    *   **Current Folder:** Displays the name of the currently loaded folder.
    *   **Buttons:** "Open Folder", "Sort Files", "Copy Metadata".
    *   **Status Message:** Shows loading progress or selected file info.
    *   **File List:** Displays images, text files, model files, etc., found in the selected folder.
*   **Right Panel:**
    *   **Image Preview:** Displays a preview of the selected image.
    *   **Prompt Info:** (e.g., Positive/Negative prompts from AI images)
    *   **Generation Info:** (e.g., Steps, Sampler, Seed, CFG, Model from AI images or EXIF details)
    *   **Raw Data:** Displays the full raw metadata string if available.
*   **Bottom Bar:**
    *   **Settings Button:** Opens a dialog for application settings (e.g., themes).
    *   **Exit Button:** Closes the application.
*   **Menu Bar:** Standard File, View, Help menus.

<hr>

## Key Features

*   **Graphical User Interface (GUI):** Built with Python and PyQt6 for a modern, cross-platform experience.
*   **Resizable Interface:** Main panels can be resized using a splitter.
*   **AI Metadata Extraction:** Extracts and displays generation parameters from images created by popular AI tools (e.g., Stable Diffusion WebUI Forge/A1111, ComfyUI).
*   **Safetensors Metadata:** Reads and displays metadata from `.safetensors` model files (LoRa, checkpoints, etc.).
*   **Standard EXIF/XMP Display:** Shows standard photographic EXIF and XMP metadata for regular images.
*   **Text/JSON/TOML Viewing:** Displays the content of associated text, JSON, or TOML files.
*   **Image Previews:** Quickly view images.
*   **Theming:** Supports themes via `qt-material` for a customizable look.
*   **Settings Persistence:** Remembers last used folder, window geometry, and theme.

<hr>

## Future Developments

We're always looking to improve! Planned features include:
*   Advanced filtering and sorting options for the file list.
*   Thumbnail generation for faster browsing of large image sets.
*   More comprehensive settings and customization options.
*   Enhanced support for more AI tool metadata formats and model types.
*   Video and text tutorials.

<hr>

## License

This program is free software: you can redistribute it and/or modify it under the terms of the **GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.**

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

The full license text is available in the `LICENSE` file in this repository.

### Regarding Dependencies

This project uses several third-party libraries, each with its own license:
*   **PyQt6:** Licensed under GPLv3 (which is why this project is also GPLv3+) or a commercial license.
*   **sd-prompt-reader (by receyuki):** MIT License.
*   Other dependencies (Pillow, rich, pyexiv2, etc.) generally use permissive licenses like MIT, BSD, or similar.

Please ensure compliance with all relevant licenses if you fork, modify, or distribute this software or its components.

<hr>

## Acknowledgments

### Ktiseos Nyx would like to thank:

*   Our peers and the wider AI and open-source communities for their continuous support and inspiration.
*   **[receyuki](https://github.com/receyuki)** for the excellent [stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader), which served as a key inspiration and whose library is now a core component for AI metadata parsing in this tool.
*   **[Anzhc](https://github.com/anzhc)** for continued support and motivation.
*   The developers of Python and the many open-source libraries that make this project possible.
*   AI Language Models (like those from Google, OpenAI, Anthropic) for assistance with code generation, documentation, and problem-solving during development.

...and many more!

<hr>

## Support Us

If you find Dataset Tools useful, please consider supporting the creators!

<a href="https://discord.gg/5t2kYxt7An" target="_blank"><img src="https://img.shields.io/badge/Join%20us%20on-Discord-5865F2?style=for-the-badge&logo=discord" alt="Join us on Discord"></a>
<a href="https://ko-fi.com/duskfallcrew" target="_blank"><img src="https://img.shields.io/badge/Support%20us%20on-Ko--Fi-FF5E5B?style=for-the-badge&logo=kofi" alt="Support us on Ko-fi"></a>
<a href="https://twitch.tv/duskfallcrew" target="_blank"><img src="https://img.shields.io/badge/Follow%20us%20on-Twitch-9146FF?style=for-the-badge&logo=twitch" alt="Follow us on Twitch"></a>

<hr>
