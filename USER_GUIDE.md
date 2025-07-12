# Dataset Tools User Guide

Welcome to Dataset Tools! This guide will walk you through everything you need to know about the application.

## Table of Contents
- [Getting Started](#getting-started)
- [Basic Navigation](#basic-navigation)
- [Loading and Viewing Files](#loading-and-viewing-files)
- [Customizing Your Experience](#customizing-your-experience)
  - [Changing Themes](#changing-themes)
  - [Font Customization](#font-customization)
  - [Window Sizing and Layout](#window-sizing-and-layout)
- [Metadata Features](#metadata-features)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Getting Help and Reporting Issues](#getting-help-and-reporting-issues)
- [Community and Support](#community-and-support)
- [Important Notice: PyQt6 Status](#important-notice-pyqt6-branch-status)

---

## Getting Started

### First Launch
When you first open Dataset Tools, you'll see the main interface with:

- A file list panel on the left (initially empty)
- An image preview area on the right
- Metadata display areas below the preview
- A menu bar at the top with File, View, and Settings options

### Loading Your First Dataset
1. **Method 1: Use the Open Folder Button**
   - Click the "Open Folder" button in the toolbar
   - Navigate to your image dataset folder
   - Click "Select Folder"

2. **Method 2: Drag and Drop**
   - Simply drag a folder from your file manager onto the Dataset Tools window
   - The folder will be loaded automatically

3. **Method 3: Menu Option**
   - Go to File → Change Folder...
   - Browse to your desired folder

## Basic Navigation

### File List
- **Single Click**: Select a file to view its preview and metadata
- **Scroll**: Use mouse wheel or scrollbar to navigate long file lists
- **Sort Files**: Click the "Sort Files" button to organize by type (images, text files, models)

### Image Preview
- **Zoom**: Use Ctrl + Mouse Wheel to zoom in/out
- **Pan**: Click and drag to move around zoomed images
- **Reset View**: Double-click to fit image to window

### Metadata Display
- **Copy Metadata**: Click the "Copy Metadata" button to copy all parsed information to clipboard
- **Scroll**: Use the scrollbars in metadata text areas for long metadata

## Loading and Viewing Files

### Supported File Types
Dataset Tools can handle various file types:

**Images with AI Metadata:**
- PNG files (A1111, ComfyUI, NovelAI, InvokeAI, etc.)
- JPEG/JPG files (Various AI tools)
- WEBP files (Easy Diffusion, A1111)

**Model Files:**
- Safetensors files (partial support)
- GGUF files (coming soon)

**Text Files:**
- TXT files (displays content)
- JSON files (displays formatted content)
- TOML files (displays content)

### Understanding Metadata Display
When you select a file with AI-generated metadata, you'll see:

1. **Prompt Information**
   - Positive prompts
   - Negative prompts
   - SDXL-specific prompts (if applicable)

2. **Generation Parameters**
   - Steps, Sampler, CFG Scale
   - Seed, Model information
   - Resolution and other technical details

3. **Tool-Specific Information**
   - ComfyUI workflow data
   - CivitAI resource information
   - Platform-specific metadata

## Customizing Your Experience

### Changing Themes

Dataset Tools comes with multiple beautiful themes to suit your preference:

#### Quick Theme Change
1. Go to **View → Themes** in the menu bar
2. Select from available themes:
   - **Dark Pink**: Dark theme with pink accents
   - **Light Green**: Light theme with green accents
   - **Dark Teal**: Dark theme with teal accents
   - **Hide Pink Spider**: Special high-contrast theme
   - And many more!

#### Advanced Theme Settings
1. Click the **Settings** button at the bottom of the window
2. In the Settings dialog:
   - Use the **Theme** dropdown to select your preferred theme
   - Changes apply immediately
   - Click **OK** to save your selection

### Font Customization

Personalize your text display with custom fonts:

#### Changing Fonts
1. Click the **Settings** button
2. In the Settings dialog:
   - Use the **Font Family** dropdown to choose from bundled fonts
   - Adjust **Font Size** using the number input (8-72pt range)
   - See the preview update in real-time

#### Available Font Families
Dataset Tools includes 22 carefully selected font families:
- **Professional Fonts**: Open Sans, Inter, Roboto, Source Sans Pro
- **Monospace Fonts**: JetBrains Mono, Source Code Pro, Ubuntu Mono
- **Creative Fonts**: Orbitron, Pixelify Sans, VT323
- **Serif Fonts**: Crimson Text, Playfair Display
- And many more!

#### Font Tips
- **Monospace fonts** (like JetBrains Mono) are great for viewing code and technical metadata
- **Sans-serif fonts** (like Open Sans) are ideal for general readability
- **Larger font sizes** help with accessibility and extended reading sessions

### Window Sizing and Layout

#### Window Management
1. **Resize**: Drag window edges or corners to resize
2. **Maximize**: Double-click the title bar or use the maximize button
3. **Settings**: Your window size preferences are automatically saved

#### Layout Customization
- **Panel Sizing**: Drag the divider between the file list and preview panels to adjust sizes
- **Optimal Setup**: A 70/30 split (preview/file list) works well for most datasets

## Metadata Features

### Advanced Metadata Viewing
- **Copy Specific Sections**: Select text in metadata areas and copy with Ctrl+C
- **Search Within Metadata**: Use Ctrl+F when focused on metadata text areas
- **Export Options**: Use the Copy Metadata button for full export

### Understanding Different AI Tools
Dataset Tools recognizes metadata from:
- **Automatic1111/Forge**: Standard PNG parameters and JPEG UserComment
- **ComfyUI**: Embedded workflows with node analysis
- **NovelAI**: Both legacy and stealth metadata formats
- **CivitAI**: Dual metadata formats with resource extraction
- **And 20+ other AI generation tools**

## Keyboard Shortcuts

### Navigation
- **Ctrl+O**: Open folder dialog
- **F5**: Refresh current folder
- **Up/Down Arrows**: Navigate file list (when focused)

### View Controls
- **Ctrl + Mouse Wheel**: Zoom image preview
- **Ctrl+0**: Reset image zoom
- **F11**: Toggle fullscreen (if available)

### Metadata
- **Ctrl+C**: Copy selected text or use Copy Metadata button
- **Ctrl+A**: Select all text in focused metadata area

## Getting Help and Reporting Issues

### GitHub Issues (Primary Support)
For bugs, feature requests, and technical issues:

1. **Visit**: [Dataset Tools Issues](https://github.com/Ktiseos-Nyx/Dataset-Tools/issues)
2. **Search First**: Check if your issue already exists
3. **Create New Issue**:
   - Click "New Issue"
   - Choose the appropriate template:
     - 🐛 **Bug Report**: For crashes, errors, or unexpected behavior
     - 💡 **Feature Request**: For new functionality suggestions
     - 📚 **Documentation**: For guide improvements or clarifications
     - ❓ **Question**: For usage help and general questions

#### What to Include in Bug Reports
- **Dataset Tools Version**: Found in Help → About (when available)
- **Operating System**: Windows, macOS, or Linux
- **Python Version**: Run `python --version`
- **Steps to Reproduce**: Detailed steps that led to the issue
- **Expected vs Actual Behavior**: What should happen vs what actually happens
- **Screenshots**: Visual evidence of the problem
- **Sample Files**: If possible, include problematic files (remove sensitive content)
- **Error Messages**: Full error text from console or error dialogs

### Community Discussions
For general discussion, tips, and community support:
- **GitHub Discussions**: [Join the conversation](https://github.com/Ktiseos-Nyx/Dataset-Tools/discussions)

## Community and Support

### Discord Community
Join our active Discord server for:
- **Real-time Help**: Quick questions and community support
- **Feature Discussions**: Share ideas and feedback
- **Beta Testing**: Early access to new features
- **Community Sharing**: Share your datasets and workflows

**Join Here**: [Discord Server](https://discord.gg/HhBSvM9gBY)

#### Discord Etiquette
- Use appropriate channels for different topics
- Search previous messages before asking common questions
- Be respectful and helpful to other users
- Don't spam or post sensitive/personal information

### Support the Project
If Dataset Tools helps your workflow:
- ⭐ **Star the Repo**: [GitHub](https://github.com/Ktiseos-Nyx/Dataset-Tools)
- ☕ **Support Development**: [Ko-fi](https://ko-fi.com/duskfallcrew)
- 📺 **Follow Development**: [Twitch](https://twitch.tv/duskfallcrew)

### Additional Resources
- **Wiki**: [Dataset Tools Wiki](https://github.com/Ktiseos-Nyx/Dataset-Tools/wiki) (when available)
- **Changelog**: Check releases for update information
- **Security**: Review [SECURITY.md](SECURITY.md) for security-related information

## Important Notice: PyQt6 Branch Status

### Current Development Status
**Important**: The PyQt6 branch of Dataset Tools is in **maintenance mode** as of this release.

#### What This Means
- **Bug Fixes**: We will continue to fix critical bugs and security issues
- **Minor Updates**: Small improvements and compatibility fixes will be applied
- **No Major Features**: No new major features will be added to the PyQt6 version

#### Future Development: Tkinter Migration
We are planning a major migration to **Tkinter** for broader platform support:

**Why Tkinter?**
- **Better Compatibility**: Fewer dependency issues across different systems
- **Easier Installation**: Tkinter comes with Python by default
- **Reduced Complexity**: Simpler deployment and distribution
- **Cross-Platform Stability**: More consistent behavior across operating systems

**Timeline**
- **Current**: PyQt6 maintenance and bug fixes continue
- **Future**: New major features will be developed in the Tkinter version
- **Migration**: Users will be guided through the transition when ready

#### For Users
- **Keep Using PyQt6**: The current version remains fully functional
- **Stay Updated**: Follow our Discord and GitHub for migration announcements
- **Backup Settings**: Your themes and preferences will be preserved in the migration

#### For Developers
- **Contributing**: Bug fixes and small improvements to PyQt6 are still welcome
- **New Features**: Consider waiting for the Tkinter version for major contributions
- **Migration Help**: We welcome assistance with the Tkinter migration effort

---

## Troubleshooting

### Common Issues

#### "No preview available"
- **Cause**: File format not supported or corrupted file
- **Solution**: Check file integrity and supported formats list

#### Missing Metadata
- **Cause**: File doesn't contain AI generation metadata
- **Solution**: Verify the file was generated with supported AI tools

#### Font Not Applying
- **Cause**: Theme override or application timing
- **Solution**: Restart the application after changing fonts

#### Performance Issues
- **Cause**: Large datasets or high-resolution images
- **Solution**: Close unused applications, consider smaller preview sizes

### Getting More Help
If you encounter issues not covered here:
1. Check the [GitHub Issues](https://github.com/Ktiseos-Nyx/Dataset-Tools/issues) page
2. Ask in our [Discord community](https://discord.gg/HhBSvM9gBY)
3. Create a detailed bug report following the guidelines above

---

**Thank you for using Dataset Tools!**

🎨✨

*For the latest version of this guide, visit our [GitHub](https://github.com/Ktiseos-Nyx/Dataset-Tools).*