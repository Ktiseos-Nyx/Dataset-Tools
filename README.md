
# Dataset-Tools: A Simple Viewer for EXIF and AI Metadata

<span style="text-align: center">

[__How to use Dataset-Tools__](#how-to-use-dataset-tools)<br>
[__Launching the Application__](#launching-the-application)<br>
[__User Interface Overview__](#user-interface-overview)<br>
[__Improve the Project__](CONTRIBUTING.md)<br>
[__Help the Creators__](#help-the-creators)<br>

</span>

| Badge                                   | Description                               |
| :-------------------------------------- | :---------------------------------------- |
| [![GitHub](https://img.shields.io/badge/GitHub-View%20on%20GitHub-181717?logo=github&style=for-the-badge)](https://github.com/Ktiseos-Nyx) | Our Github |
| ![Build Status](https://img.shields.io/badge/build-passing-brightgreen) | Indicates the build status of the project. |
| [![PyTest](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/pytest.yml/badge.svg)](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/pytest.yml)        | PyTest results. |
| ![CC0 1.0 License](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg) | Creative Commons Zero v1.0 Universal (Public Domain Dedication) |
| [![Discord](https://img.shields.io/discord/1024442483750490222?logo=discord&style=for-the-badge&color=5865F2)](https://discord.gg/5t2kYxt7An) | Discord Server |
| [![Ko-Fi](https://img.shields.io/badge/Ko--fi-Support%20on%20Ko--fi-FF5E5B?logo=kofi&style=for-the-badge)](https://ko-fi.com/duskfallcrew) | Duskfallcrew Ko-FI | 
| [![Twitch](https://img.shields.io/badge/Twitch-Follow%20on%20Twitch-9146FF?logo=twitch&style=for-the-badge)](https://twitch.tv/duskfallcrew) | Watch on Twitch | 
| [![Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20on%20Ko--fi-FF5E5B?logo=kofi&style=for-the-badge)](https://ko-fi.com/exdysa) | Exdysa Ko-Fi | 




<hr>

Dataset-Tools is a desktop application designed to help users browse and manage their image and text datasets, particularly those used with AI art generation tools like Stable Diffusion. Developed using PyQt6, it provides a simple and intuitive graphical interface for browsing images, viewing metadata, and examining associated text prompts. As of recently this has also extended it's use case to reading metadata from LoRa safetensor file formats, as well as reading metadata from sites such as [Civitai](https://civitai.com/). This project is inspired by tools within the AI art community (☮️[receyuki](https://github.com/receyuki/stable-diffusion-prompt-reader)🤍) and aims to empower users in improving their dataset curation workflow. If you're interested in getting involved, feel free to fork and contribute!

https://github.com/user-attachments/assets/f8b4187b-2603-4bae-aa4a-dc3f621b5696


## How to Use Dataset-Tools

### Requirements

To run the program, you will need the following software:

#### Python:
- [Python.org](https://www.python.org/downloads/) or [Try `uv`](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)

#### Python Versions:
- Requires at least Python 3.10, older versions may not react well with the installation commands. 

####  Git:
- [Windows](https://gitforwindows.org/)
- [MacOS first option](https://git-scm.com/downloads/mac), [or second option](https://brew.sh/)
- [Linux](https://git-scm.com/downloads/linux)

### Launching the Application

#### 1. Open your ``terminal`` shell console of choice.🐣  (ie:  ```powershell```,```cmd```,```zsh```,```bash```, etc.)

#### 2. ``git clone`` or download the Dataset-Tools repository from GitHub.

```sh
git clone https://github.com/Ktiseos-Nyx/Dataset-Tools.git
```

#### 3. Move into Dataset-Tools folder and `pip install`the required dependencies:

```sh
cd Dataset-Tools
pip install .
```

> [!NOTE]
> `uv` users
> ```sh
> cd Dataset-Tools
> uv pip install .
> ```

#### 4. Run the application with `dataset-tools` command:

```sh
dataset-tools
```

#### You're in!

<br>

### User Interface Overview
<hr>

The application window has the following main components:

*   **Current Folder:** Displays the path of the currently loaded folder.
*   **Open Folder:** A button to select a folder containing images and text files.
*   **Image List:** Displays a list of images and text files found in the selected folder.
*   **Image Preview:** An area to display a selected image.
*   **Metadata Box:** A text area to display the extracted metadata from the selected image or safetensors file (including Stable Diffusion prompt, settings, etc.).

### Managing Images and Text

*   **Selecting Images:** Click on an image or text file in the list to display its preview, metadata, and associated text content.
*   **Viewing Metadata:** Metadata associated with the selected image is displayed on the text area, such as steps, samplers, seeds, and more.
*   **Viewing Text:** The content of any text file associated with the selected image is displayed on the text box.


## Key Features

*   **Graphical User Interface (GUI):** Built with PyQt6 for a modern and cross-platform experience.
*   **Image Previews:** Quickly view images in a dedicated preview area.
*   **Metadata Extraction:** Extract and display relevant metadata from PNG image files, especially those generated from Stable Diffusion. Now including support for Safetensors files, please note this at the moment includes LoRA, and NOT Embeddings. This at the moment also includes for support beyond SDXL base models, as well as Flux, Aura, SD3 and more to come!
*   **Text Viewing:** Display the content of text files.
*   **Clear Layout:** A simple and intuitive layout, with list view on the left, and preview on the right.

## Future Developments

*   **Filtering/Sorting:** Options to filter and sort files.
*   **Thumbnail Generation:** Implement thumbnails for faster browsing.
*   **Themes:** Introduce customizable themes for appearance.
*   **Better User Experience:** Test on different operating systems and screen resolutions to optimize user experience.
*   **Video Tutorials:** Create video tutorials to show users how to use the program.
*   **Text Tutorials:** Create detailed tutorials in text and image to show the user how to use the program.

## Help the Creators

<a href="https://discord.gg/5t2kYxt7An" target="_blank">

![A flat logo for Discord](https://img.shields.io/badge/%20Discord%20_%20_%20_%20_%20_%7C-_?style=flat-square&labelColor=rgb(65%2C69%2C191)&color=rgb(65%2C69%2C191))

</a>

### --**__<{ Ktiseos Nyx }>__**--

is a creator collective consisting of





#### [Duskfall Portal Crew on GitHub](https://github.com/duskfallcrew)

Ktiseos Nyx would like to thank -

*   The use of Gemini, ChatGPT, Claude/Anthropic as well as Llama and other tools that structured K/N's base of this tool.
*   Support of our peers, and the community at Large.
*   Inspired by [receyuki/stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader)
*   The ever growing taunts & support by [Anzhc](https://github.com/anzhc)

#### [EXDYSA on GitHub](https://github.com/exdysa)
#### [Exdysa on Ko-Fi](https://ko-fi.com/exdysa)

...and more to come!
