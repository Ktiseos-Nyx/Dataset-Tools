[![GitHub](https://img.shields.io/badge/GitHub-View%20on%20GitHub-181717?logo=github&style=for-the-badge)](https://github.com/Ktiseos-Nyx) ![Build Status](https://img.shields.io/badge/build-passing-brightgreen) [![PyTest](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/pytest.yml/badge.svg)](https://github.com/Ktiseos-Nyx/Dataset-Tools/actions/workflows/pytest.yml) ![CC0 1.0 License](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg) [![Discord](https://img.shields.io/discord/1024442483750490222?logo=discord&style=for-the-badge&color=5865F2)](https://discord.gg/5t2kYxt7An) [![Twitch](https://img.shields.io/badge/Twitch-Follow%20on%20Twitch-9146FF?logo=twitch&style=for-the-badge)](https://twitch.tv/duskfallcrew) 

<hr>

# Dataset-Tools: A Simple Viewer for EXIF and AI Metadata

<hr>

<span style="text-align: center">

## Contents
    
[__How this Differs from Other Tools__](#how-this-differs-from-other-tools) <br>
  - [Intersectionality 💖✨🌈](#intersectionality-💖✨🌈) <br>
[__How to use Dataset-Tools__](#how-to-use-dataset-tools) <br>
  - [Requirements](#requirements)
  - [Git](#git) 
  - [Installation on Linux (Ubuntu/Debian) Systems under 22.04](#installation-on-linux-ubuntu-debian-systems) <br>
[__Launching the Application__](#launching-the-application)<br>
  -  [1. Open your terminal shell console of choice.🐣 (ie: powershell, cmd, zsh, bash, etc.)](#1-open-your-terminal-shell-console-of-choice-ie-powershell-cmd-zsh-bash-etc)
  -  [VENV Instructions](#venv-instructions)
  -  [2. git clone or download the Dataset-Tools repository from GitHub.](#2-git-clone-or-download-the-dataset-tools-repository-from-github)
  -  [3. Move into Dataset-Tools folder and pip installthe required dependencies:](#3-move-into-dataset-tools-folder-and-pip-installthe-required-dependencies)
  -  [4. Run the application with dataset-tools command:](#4-run-the-application-with-dataset-tools-command) <br>
   
[__User Interface Overview__](#user-interface-overview)<br>
  - [__Managing Images and Text__](#managing-images-and-text)
  - [__Key Features__](#key-features)<br>
  - [__Future Developments__](#future-developments) <br>
[__Fish Shell_Terminal_Extension__](#non-required-extensions---fish-shell)<br>
[__Improve the Project__](CONTRIBUTING.md)<br>
[__ABOUT US__](#about-us) <br>
  - [__Help the Creators__](#help-the-creators) 
  - [__Ktiseos Nyx would like to thank -__](#ktiseos-nyx-would-like-to-thank--)  <br>

</span>


<hr>

Dataset-Tools is a desktop application designed to help users browse and manage their image and text datasets, particularly those used with AI art generation tools like Stable Diffusion. Developed using PyQt6, it provides a simple and intuitive graphical interface for browsing images, viewing metadata, and examining associated text prompts. As of recently this has also extended it's use case to reading metadata from LoRa safetensor file formats, as well as reading metadata from sites such as [Civitai](https://civitai.com/). This project is inspired by tools within the AI art community (☮️[receyuki](https://github.com/receyuki/stable-diffusion-prompt-reader)🤍) and aims to empower users in improving their dataset curation workflow. If you're interested in getting involved, feel free to fork and contribute!

https://github.com/user-attachments/assets/f8b4187b-2603-4bae-aa4a-dc3f621b5696

<hr>

## How this Differs from Other Tools:

Unlike other metadata readers, this tool is designed to be fully up-to-date with Python 3.12 and above, while maintaining compatibility with Python 3.10. It extends beyond basic image metadata, offering robust support for `safetensors` files commonly used in models and checkpoints across diverse AI platforms like Stable Diffusion, Aura, and Flux. Furthermore, it incorporates specific readers for ComfyUI and Automatic1111 EXIF data, as well as non-AI related metadata, and we are working to improve user customizability with more color themes. Our aim is to provide a simple, user-friendly tool that is easily verifiable for accuracy and ease of use.

### Intersectionality 💖✨🌈

*   🏳️‍🌈🏳️‍⚧️ The development of this app is driven by individuals who are either neurodivergent, or who actively support neurodiversity. We're also a team that identifies with, or actively supports the LGBTQIA2S+ community. Ktiseos Nyx is run by Earth & Dusk, which is a project run by a community of amazing and welcoming people.

*   ✨🧠♾️ Neurodivergence encompasses so much more than just Autism & ADHD. Whatever your specific form of neurodivergence may be, you are wholeheartedly welcome here.

*   🦄🚀💫 As the creator of this project (duskfallcrew), I personally navigate life with CPTSD, DID, Autism, & ADHD, and the buck doesn't stop there. While I've utilized LLMs at various stages of this project's development, this is not the end all be all, and whatever your insights, ideas, or contributions may be, you're welcome to be heard, and to contribute.

<hr>

## How to Use Dataset-Tools

### Requirements

To run the program, you will need the following software:

#### Python:

*   [Python.org](https://www.python.org/downloads/) or  [Try `uv`](https://github.com/astral-sh/uv?tab=readme-ov-file#installation) (Optional)

*   Requires at least Python 3.10; older versions may not react well with the installation commands.

*  You'll also note that certain Ubuntu systems may not install the required packages correctly. If you're having problems with this, please follow the guide below, or let us know in the issues section above!

*  `uv` is available and usable on Linux, Windows, and macOS. It's extremely fast and written in rust! It is also optional.

#### Git:

*   [Windows](https://gitforwindows.org/)
*   [MacOS first option](https://git-scm.com/downloads/mac), [or second option](https://brew.sh/)
*   [Linux](https://git-scm.com/downloads/linux)

<hr>

#### Installation on Linux (Ubuntu/Debian) Systems

<hr>

This section provides instructions on how to install the necessary tools for PyQt6 on Linux systems.

**Supported Ubuntu Versions**

The PyQt6 environment tools are typically included by default in these Ubuntu versions and newer:

*   Ubuntu 20.04 LTS (Focal Fossa)
*   Ubuntu 22.04 LTS (Jammy Jellyfish)
*   Ubuntu 23.04 (Lunar Lobster), and other non-LTS releases

**If You're on an Older Version of Ubuntu**

If you are using an older version of Ubuntu or Debian than those listed above, you might encounter errors when trying to install PyQt6. If you see errors related to PyQt6, please follow the steps below to install the required Qt6 development libraries.

**Installation Steps**

To install the necessary Qt6 development tools, use one of the following methods:

**Method 1 (Recommended):**

1.  **Update your package list:**

    ```bash
    sudo apt update
    ```

2.  **Install Qt6 development tools:**

    ```bash
    sudo apt install qt6-base-dev qt6-tools-dev
    ```

**Method 2 (If Method 1 Fails):**

1.  **Update your package list:**

    ```bash
    sudo apt update
    ```

2.  **Install the default Qt6 packages:**

    ```bash
    sudo apt install qt6-default
    ```

**Verify Installation**

After installing the Qt6 libraries, you need to check if the `qmake` or `qt6-qmake` command is available on your system. Here's how:

1.  **Check for `qmake` or `qt6-qmake`:**

    Open your terminal and run the following commands one at a time:

    ```bash
    which qmake
    ```
    or

    ```bash
    which qt6-qmake
    ```

2.  **If `qmake` or `qt6-qmake` is NOT found:** This means that you have not installed `qmake` yet and should run the `sudo apt install` commands above.

3.  **If `qmake` or `qt6-qmake` is found:** This means that the tool is installed, but is not currently in your path. You can add it to your path by using the following command:

    ```bash
    export PATH="/usr/lib/qt6/bin:$PATH"
    ```

    **Important:** You might need to change `/usr/lib/qt6/bin` to the actual location of `qmake` or `qt6-qmake` on your system (returned from the `which` command).

**Note**: Please copy and paste each command individually and execute them one by one.

Then, you can install the package using pip within a virtual environment:

```bash
      python3 -m venv <env_name>
      source <env_name>/bin/activate
      pip install .
```
### Launching the Application

<hr>

#### 1. Open your terminal shell console of choice.🐣 (ie: ``powershell``, ``cmd``, ``zsh``, ``bash``, etc.)

####VENV Instructions

It's customary for safety and sanity to use a Virtual environment! Trust me on this one, multiple python installations is always a mess and a half! 

* If you're wanting to use a VENV via main python, you can set one up this way:

```bash
python3 -m venv <env_name>
source <env_name>/bin/activate
pip install .
```

* If you're wanting to use a VENV via main UV, you can set one up this way :

Python 3.12 Example

```bash
uv venv .venv
Using Python 3.12.3
Creating virtual environment at: .venv
Activate with: source .venv/bin/activate
```

* If you're wanting to activate it and you have FISH?
```bash
source .venv/bin/activate.fish
```

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

<hr>

### User Interface Overview

<hr>

The application window has the following main components:

*   **Current Folder:** Displays the path of the currently loaded folder.
*   **Open Folder:** A button to select a folder containing images and text files, as well as if you have safetensors files.
*   **Image List:** Displays a list of images and text files found in the selected folder.
*   **Image Preview:** An area to display a selected image.
*   **Metadata Box:** A text area to display the extracted metadata from the selected image or safetensors file (including Stable Diffusion prompt, settings, etc.).

### Managing Images and Text

*   **Selecting Images:** Click on an image or text file in the list to display its preview, metadata, and associated text content.
*   **Viewing Metadata:** Metadata associated with the selected image is displayed on the text area, such as steps, samplers, seeds, and more.
*   **Viewing Text:** The content of any text file associated with the selected image is displayed on the text box.


## Key Features

*   **Graphical User Interface (GUI):** Built with PyQt6 for a modern and cross-platform experience.
*   **Resizeable Interface** Easily stretch the interface like goo!
*   **Image Previews:** Quickly view images in a dedicated preview area.
*   **Metadata Extraction:** Extract and display relevant metadata from PNG image files, especially those generated from Stable Diffusion.
    * Now including support for Safetensors files, please note this at the moment includes LoRA, and NOT Embeddings.
    * This at the moment also includes for support beyond SDXL base models, as well as Flux, Aura, SD3 and more to come!
    * We've also recently added support for images from [Civitai](https://civitai.com/), supporting their EXIF formats! 
*   **Text Viewing:** Display the content of text files.
*   **Clear Layout:** A simple and intuitive layout, with list view on the left, and preview on the right.

## Future Developments

*   **Filtering/Sorting:** Options to filter and sort files.
*   **Thumbnail Generation:** Implement thumbnails for faster browsing.
*   **Themes:** Introduce customizable themes for appearance.
*   **Better User Experience:** Test on different operating systems and screen resolutions to optimize user experience.
*   **Video Tutorials:** Create video tutorials to show users how to use the program.
*   **Text Tutorials:** Create detailed tutorials in text and image to show the user how to use the program.

<hr>

## Non-Required Extensions - Fish Shell

This section describes how to install and configure Fish shell, a powerful terminal shell that offers enhanced quality-of-life features like syntax highlighting, autocompletion, and more. **This is not a required extension**, but it can significantly improve your terminal experience.

**What is Fish Shell?**

[Fish shell](https://github.com/fish-shell/fish-shell) is a modern, user-friendly command-line shell that provides a more comfortable and efficient terminal environment. It includes helpful features like:

*   Syntax highlighting to make commands easier to read
*   Smart autocompletion for faster typing
*   Tab completion for directories and commands
*   A more intuitive interface

**Installation**

Here are the installation instructions for various operating systems:

### macOS

Fish can be installed on macOS using several methods:

*   **Homebrew:** (Recommended)
    ```bash
    brew install fish
    ```
*   **MacPorts:**
    ```bash
    sudo port install fish
    ```
*   **Directly from the Fish Shell Website:**
    *   [Download the installer from fishshell.com](https://fishshell.com/)
    *   [Download a standalone app from fishshell.com](https://fishshell.com/)

    **Note:** The minimum supported macOS version is 10.10 "Yosemite."

### Linux

#### Debian/Ubuntu

Packages for Ubuntu are available from the [fish PPA](https://launchpad.net/~fish-shell/+archive/ubuntu/release-3), and can be installed using the following commands:

*   ```bash
    sudo apt-add-repository ppa:fish-shell/release-3
    sudo apt update
    sudo apt install fish
    ```
#### Fedora/openSUSE/Red Hat/CentOS
Packages for Debian, Fedora, openSUSE, and Red Hat Enterprise Linux/CentOS are available from the [openSUSE Build Service](https://software.opensuse.org/download.html?project=shells%3Afish&package=fish).

#### Other Linux distributions
Instructions for other distributions may be found at [fishshell.com](https://fishshell.com/).

### Windows

On Windows 10/11, Fish can be installed:

*   **Under WSL (Windows Subsystem for Linux):**  Follow the instructions for the appropriate Linux distribution listed above.

*  **From source:** Follow the instructions on the [fish shell homepage](https://fishshell.com/)

**Note:** Fish (4.0 and onwards) cannot be installed in Cygwin, due to a lack of Rust support.

<hr>

### ABOUT US

### --**__<{ Ktiseos Nyx }>__**--

is a creator collective consisting of

#### [EXDYSA on GitHub](https://github.com/exdysa)

#### [Duskfall Portal Crew on GitHub](https://github.com/duskfallcrew)

### Ktiseos Nyx would like to thank -

*   The use of Gemini, ChatGPT, Claude/Anthropic as well as Llama and other tools that structured K/N's base of this tool.
*   Support of our peers, and the community at Large.
*   Inspired by [receyuki/stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader)
*   The ever growing taunts & support by [Anzhc](https://github.com/anzhc)
*   [Civitai](https://civitai.com/) for giving us the space to learn and grow in the open source community!



...and more to come!

<hr>

## Help the Creators

<a href="https://discord.gg/5t2kYxt7An" target="_blank">

![A flat logo for Discord](https://img.shields.io/badge/%20Discord%20_%20_%20_%20_%20_%7C-_?style=flat-square&labelColor=rgb(65%2C69%2C191)&color=rgb(65%2C69%2C191))

</a>

<hr>

### Sponsor us on Ko-Fi!
#### [Duskfall on Ko-fi](https://ko-fi.com/duskfallcrew) 
[![Ko-Fi](https://img.shields.io/badge/Ko--fi-Support%20on%20Ko--fi-FF5E5B?logo=kofi&style=for-the-badge)](https://ko-fi.com/duskfallcrew) 
#### [Exdysa on Ko-Fi](https://ko-fi.com/exdysa) 
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20on%20Ko--fi-FF5E5B?logo=kofi&style=for-the-badge)](https://ko-fi.com/exdysa)

