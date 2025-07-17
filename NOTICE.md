# Third-Party Software Notices and Information

This project incorporates code from the following open-source software:

## 1. Core Dependencies

This project relies on the following third-party libraries, which are automatically installed as dependencies:

- **Pillow:** A powerful imaging library.
  - **License:** PIL Software License
  - **Copyright:** © 1997-2011 by Secret Labs AB, © 2011-2024 by Alex Clark and contributors.

- **PyQt6:** A comprehensive set of Python bindings for the Qt application framework.
  - **License:** GPL v3
  - **Copyright:** © Riverbank Computing Limited

- **qt-material:** A library for styling PyQt applications with Material Design themes.
  - **License:** MIT License
  - **Copyright:** © 2020-2024 Gonzalo Odiard

- **Rich:** A library for rich text and beautiful formatting in the terminal.
  - **License:** MIT License
  - **Copyright:** © 2020-2024 Will McGugan

- **Pydantic:** A library for data validation and settings management using Python type hints.
  - **License:** MIT License
  - **Copyright:** © 2017-2024 Pydantic Team

- **pyexiv2:** A Python binding to the Exiv2 library for reading and writing image metadata.
  - **License:** GPL-2.0-or-later
  - **Copyright:** © 2006-2024 The Exiv2 Team

- **piexif:** A pure Python library for reading and writing EXIF data.
  - **License:** MIT License
  - **Copyright:** © 2014, hMatoba

- **defusedxml:** A library for parsing XML data safely.
  - **License:** Python Software Foundation License 2.0
  - **Copyright:** © 2013-2024 Christian Heimes

- **toml:** A library for parsing TOML configuration files.
  - **License:** MIT License
  - **Copyright:** © 2015-2024 William Pearson

## 2. Vendored Code

### Stable Diffusion Prompt Reader

This project includes a modified, or "vendored," version of the **Stable Diffusion Prompt Reader** library.

- **Original Author:** receyuki
- **Project Repository:** [https://github.com/receyuki/stable-diffusion-prompt-reader](https://github.com/receyuki/stable-diffusion-prompt-reader)
- **Original License:** MIT License
- **Modifications:** The vendored code has been adapted for integration and resides in the `dataset_tools/vendored_sdpr/` directory.

The original MIT license for this library is included below:

```
MIT License

Copyright (c) 2023 receyuki

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 3. Test Data and Workflows

This repository contains test images and workflow data used for development and testing purposes. This data is not owned by the project and may be subject to different licenses.

We gratefully acknowledge contributions from community members, including **Quadmoon** and **Tatersbarn**, who have provided test data.

If you are the creator of any test data included in this project, please contact the maintainers for proper attribution.