# Dataset-Tools: A Simple Dataset Viewer for AI Art

<div style="text-align: center">

[__How to use Dataset-Tools__](#how-to-use-dataset-tools)<br>
[__Launching the Application__](#launching-the-application)<br>
[__User Interface Overview__](#user-interface-overview)<br>
[__Improve the Project__](CONTRIBUTING.md)<br>
[__Help the Creators__](#help-the-creators)<br>

</div>

Dataset-Tools is a desktop application designed to help users browse and manage their image and text datasets, particularly those used with AI art generation tools like Stable Diffusion. Developed using PyQt6, it provides a simple and intuitive graphical interface for browsing images, viewing metadata, and examining associated text prompts. This project is inspired by tools within the AI art community and aims to empower users in improving their dataset curation workflow.

<img width="797" alt="Screenshot of the Application" src="https://github.com/user-attachments/assets/7e14c542-482d-42f4-a9ae-4305c9e2c383" />





## How to Use Dataset-Tools

### Requirements

To run the program, you will need the following software:

#### Python:
- [Python.org](https://www.python.org/downloads/) or [Try `uv`](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)

####  Git:
- [Windows](https://gitforwindows.org/)
- [MacOS step A](https://brew.sh/), [MacOS step B](https://git-scm.com/downloads/mac)
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
<br>

### User Interface Overview
<hr>

The application window has the following main components:

*   **Current Folder:** Displays the path of the currently loaded folder.
*   **Open Folder:** A button to select a folder containing images and text files.
*   **Image List:** Displays a list of images and text files found in the selected folder.
*   **Image Preview:** An area to display a selected image.
*   **Metadata Box:** A text area to display the extracted metadata from the selected image (including Stable Diffusion prompt, settings, etc.).
*   **Prompt Text:** A text label to display the prompt from the selected image.
*   **Text File Content Area:** A text area to display the content of any associated text files.

### Managing Images and Text

*   **Selecting Images:** Click on an image or text file in the list to display its preview, metadata, and associated text content.
*   **Viewing Metadata:** Metadata associated with the selected image is displayed on the text area, such as steps, samplers, seeds, and more.
*   **Viewing Text:** The content of any text file associated with the selected image is displayed on the text box.

## Key Features

*   **Graphical User Interface (GUI):** Built with PyQt6 for a modern and cross-platform experience.
*   **Image Previews:** Quickly view images in a dedicated preview area.
*   **Metadata Extraction:** Extract and display relevant metadata from PNG image files, especially those generated from Stable Diffusion.
*   **Text Viewing:** Display the content of text files.
*   **Clear Layout:** A simple and intuitive layout, with list view on the left, and preview on the right.

## Future Developments

*   **Thumbnail Generation:** Implement thumbnails for faster browsing.
*   **JPEG Metadata:** Add support for extracting metadata from JPEG files.
*   **Themes:** Introduce customizable themes for appearance.
*   **Filtering/Sorting:** Options to filter and sort files.
*   **Better User Experience:** Test on different operating systems and screen resolutions to optimize user experience.
*   **Video Tutorials:** Create video tutorials to show users how to use the program.
*   **Text Tutorials:** Create detailed tutorials in text and image to show the user how to use the program.

## Help the Creators

### --**__<{ Ktiseos Nyx }>__**--

 <!-- ![Static Badge](https://img.shields.io/badge/%20Discord%20_%20_%20_%20_%20_%7C-_?style=flat-square&labelColor=rgb(65%2C69%2C191)&color=rgb(65%2C69%2C191)&link=https%3A%2F%2Fdiscord.gg%2F5t2kYxt7An)
# https://img.shields.io/badge/%20Discord%20_%20_%20_%20_%20_%7C-_?style=flat-square&labelColor=rgb(65%2C69%2C191)&color=rgb(65%2C69%2C191)&link=https%3A%2F%2Fdiscord.gg%2F5t2kYxt7An -->


is a creator collective consisting of Duskfall Portal Crew, EXDYSA, and more to come!

<img alt="Static Badge" src="https://img.shields.io/badge/%20Discord%20_%20_%20_%20_%20_%7C-_?style=flat-square&labelColor=rgb(65%2C69%2C191)&color=rgb(65%2C69%2C191)&link=https%3A%2F%2Fdiscord.gg%2F5t2kYxt7An">

#### More about the Duskfall Portal crew [Link here]()

The Duskfall Portal crew would like to thank -

*   ChatGPT 3.5 & 4o: Powering innovative solutions and creative endeavors.
*   Support of my peers, and the community at Large.
*   [Canvas icons created by Freepik - Flaticon](https://www.flaticon.com/free-icons/canvas)
*   Inspired by [receyuki/stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader)

#### More about EXDYSA [Link here]()