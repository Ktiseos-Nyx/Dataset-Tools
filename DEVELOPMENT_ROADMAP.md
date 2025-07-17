# Development Roadmap

This document outlines the future development plans for the Dataset-Tools project. The primary goal is to enhance the tool's stability, expand its functionality, and improve the user experience.

## 1. UI Framework Migration: Return to Tkinter

The current UI is built with PyQt6, but the original plan was to use Tkinter. To align with the project's initial vision and simplify the UI framework, we will migrate back to Tkinter.

**Key Tasks:**

- **Re-implement Core UI:** Recreate the main window, file browser, and metadata display using Tkinter widgets.
- **Theme System for Tkinter:** Develop a robust and flexible theme management system specifically for Tkinter. This will include light, dark, and custom theme options.
- **Widget Replacement:** Replace all PyQt6-specific widgets with their Tkinter equivalents.

## 2. Civitai Integration: Metadata Lookup

To enhance the tool's utility, we will implement a feature to look up metadata directly from Civitai.

**Key Tasks:**

- **API Integration:** Develop a module to interact with the Civitai API.
- **UI Integration:** Add a button or context menu option to trigger a Civitai lookup for the selected image.
- **Display Results:** Create a clean and readable display for the retrieved Civitai metadata.

## 3. Parser Hardening and Enhancement

The metadata parsers are a core component of this tool. To ensure they are robust and reliable, we will focus on hardening and improving them.

**Key Tasks:**

- **Comprehensive Testing:** Expand the test suite to cover a wider range of edge cases and malformed metadata.
- **Error Handling:** Improve error handling to provide more informative feedback to the user when a parser fails.
- **Performance Optimization:** Profile the parsers and optimize them for speed and efficiency.

## 4. Theme System Refinement for Tkinter

As part of the migration to Tkinter, we will create a new theme system from the ground up.

**Key Tasks:**

- **Theme Definition:** Define a clear and simple format for creating custom themes.
- **Theme Loading:** Implement a system for loading themes from a dedicated directory.
- **Theme Application:** Ensure that themes are applied consistently across all UI elements.

## 5. Packaging and Distribution

To make the tool more accessible to a wider audience, we will create installers and distribute it through popular package managers.

**Key Tasks:**

- **Executable Bundling:** Create standalone executables for Windows, macOS, and Linux.
- **Package Manager Integration:**
  - **Windows:** Publish to Chocolatey.
  - **macOS:** Publish to Homebrew.
  - **Linux:** Explore options for distributing through popular repositories (e.g., APT, DNF, Pacman).

## 6. Power User Features

We will add features specifically for advanced users and those with specialized workflows.

**Key Tasks:**

- **Android Support:** Develop a version of the tool that runs on Android devices.
- **WD/KohyaSS Tagging Support:** Add support for reading and writing tags in the format used by WD and KohyaSS.

## 7. A Note for Future Developers

This is a long-term project that has been in development for over a year. We are always looking for passionate developers to join our community and help us build the future of this tool. If you are interested in contributing, please reach out to us on our GitHub repository.

## 8. Localization

To make the tool accessible to a global audience, we will implement a localization system.

**Key Tasks:**

- **Community-Driven Translations:** Establish a process for community members to contribute translations for different languages.
- **Icon-Based UI:** Explore the possibility of replacing text-based buttons with icons to reduce the reliance on text and improve the user experience for all languages.

## 9. Accessibility

We are committed to making this tool usable by as many people as possible. Accessibility will be a key consideration in all future development.

**Key Tasks:**

- **Screen Reader Support:** Ensure that all UI elements are properly labeled and accessible to screen readers.
- **Keyboard Navigation:** Implement full keyboard navigation to allow users to control the application without a mouse.
- **High-Contrast Themes:** Develop high-contrast themes to improve readability for users with visual impairments.
