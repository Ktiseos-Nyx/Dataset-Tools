# Frequently Asked Questions (FAQ)

## 📦 Installation & Distribution

### Why is there no EXE file download?

**Short Answer:** Dataset Tools is a Python application distributed as source code, not as a pre-compiled executable.

**Detailed Explanation:**
- **Security & Trust**: Python source code allows users to inspect exactly what the application does before running it
- **Cross-Platform**: Works on Windows, macOS, and Linux without separate builds
- **Dependency Management**: Uses modern Python packaging (pip/uv) for reliable dependency resolution
- **Development Transparency**: Open source nature allows community contributions and verification
- **Size Efficiency**: No need to bundle a Python interpreter, reducing download size
- **Easy Updates**: `pip install --upgrade` provides seamless updates

**How to Install:**
```bash
# Recommended method
pip install kn-dataset-tools

# Or from source
git clone https://github.com/Ktiseos-Nyx/Dataset-Tools
cd Dataset-Tools
pip install -e .
```

### Can I create my own EXE file?

Yes! Advanced users can create their own executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed dataset_tools/main.py
```

**Note:** Self-built executables may trigger antivirus warnings since they're not digitally signed.

---

## 🖥️ System Requirements

### What Python version do I need?

- **Minimum:** Python 3.10
- **Recommended:** Python 3.11 or 3.12
- **Not Supported:** Python 3.9 or earlier

### What operating systems are supported?

- ✅ **Windows 10/11** (x64)
- ✅ **macOS 10.15+** (Intel & Apple Silicon)
- ✅ **Linux** (Ubuntu 20.04+, most modern distributions)

### Why won't it work on Python 3.9?

Dataset Tools uses modern Python features like:
- Enhanced type hints (`list[str]` instead of `List[str]`)
- Pattern matching (Python 3.10+)
- Modern dataclass features

---

## 🎨 Usage & Features

### How do I change themes?

1. Go to **View → Themes** in the menu bar
2. Choose from categories:
   - **Qt-Material**: Material Design themes
   - **Custom QSS**: Hand-crafted themes (retro, aesthetic, etc.)
   - **Qt-Themes**: Color palettes (Dracula, Nord, etc.)
   - **Unreal**: Unreal Engine-style interface

Your theme selection is automatically saved.

### What file formats are supported?

**Images:**
- PNG, JPEG, JPG, WEBP, GIF, BMP
- Supports EXIF, XMP, and AI generation metadata

**Text Files:**
- TXT, JSON, YAML, XML
- ComfyUI workflow files

**Model Files:**
- Safetensors (.safetensors)
- GGUF (.gguf)
- PyTorch (.pt, .pth)
- Checkpoint (.ckpt)

### How do I view metadata from AI generation tools?

Dataset Tools automatically detects and parses metadata from:
- **Automatic1111 (A1111)**
- **ComfyUI workflows**
- **NovelAI**
- **Stable Diffusion WebUI**
- **Civitai**
- **And many more...**

Simply load an image or text file containing metadata.

---

## 🎨 Themes & Customization

### How do I change themes?

**Access Themes Menu:**
1. Go to **View → Themes** in the menu bar
2. Choose from **4 different theme categories**
3. Your selection is **automatically saved** and restored on restart

### What theme categories are available?

#### 🎨 **Qt-Material Themes**
- **Description:** Google Material Design themes with modern components
- **Examples:** Dark Teal, Light Blue, Purple, Cyan, etc.
- **Features:** Dynamic color schemes, Material Design components
- **Best For:** Clean, professional look

#### 🌈 **Qt-Themes Color Palettes**  
- **Description:** Popular programmer color schemes
- **Available Palettes:**
  - `One Dark`, `Monokai`, `Nord` 
  - `Catppuccin` (Mocha, Macchiato, Frappe, Latte)
  - `Atom One`, `GitHub Dark/Light`, `Dracula`, `Blender`
- **Features:** Color-only themes (no layout changes)
- **Best For:** Developers who want familiar editor colors

#### 🎮 **Custom QSS Themes**
Hand-crafted themes with unique aesthetics:

**🕹️ Gaming & Tech:**
- `Steam Deck` - Gaming handheld inspired with Valve's design language
- `Terminal Hacker` - Matrix-inspired green-on-black with monospace fonts
- `Cyberpunk 2077` - Green-on-black matrix/cyberpunk aesthetic

**🎭 Retro & Nostalgic:**
- `Windows XP` - Classic Luna theme with gradients
- `Windows 3.1 Blue` - Vintage Windows 3.1 styling
- `Mac 90s Greyscale` - Classic 90s Mac aesthetic
- `AOL Classic` - AOL Instant Messenger throwback

**🌐 Web Culture:**
- `Geocities Nightmare` - 90s web aesthetic with background images
- `Vaporwave Aesthetic` - Neon gradients and retro-futuristic styling
- `Kawaii Pastel Overload` - Pastel rainbow gradients

**☕ Cozy & Professional:**
- `Cozy Coffee Shop` - Warm browns and creams with serif fonts
- `Arctic Minimalist` - Clean ice-inspired design with cool blues
- `Sunset Gradient` - Warm oranges, pinks, and purples with glass effects

**🎬 Social & Entertainment:**
- `Facebook Light/Dark` - Social media inspired themes
- `FF6 Classic Flat` - Final Fantasy VI inspired
- `Firefox Classic` - Classic browser styling

#### 🎯 **Unreal Stylesheet**
- **Description:** Unreal Engine-like interface styling
- **Theme:** `Unreal Engine 5` - Professional game development aesthetic
- **Best For:** Game developers and 3D artists

### How do I install custom fonts?

**Automatic Font Loading:**
Dataset Tools automatically loads fonts from the `fonts/` directory:

1. **Create fonts folder:** Place `.ttf` or `.otf` files in `dataset_tools/fonts/`
2. **Restart application:** Fonts are loaded on startup
3. **Apply fonts:** Use **View → Font Settings** to select loaded fonts

**Supported Font Formats:**
- ✅ **TrueType (.ttf)**
- ✅ **OpenType (.otf)**  
- ❌ WOFF, WOFF2 (web fonts not supported)

**Font Application:**
- **Global:** Apply to entire application
- **Persistent:** Font choices saved and restored
- **Theme Compatible:** Fonts work with all themes

### Can I create my own themes?

**Absolutely!** Custom QSS themes are easy to create:

#### **Theme Creation Steps:**
1. **Study existing themes** in `dataset_tools/themes/`
2. **Create new .qss file** with your Qt StyleSheet code
3. **Test thoroughly** with different UI elements
4. **Place in themes directory** for automatic detection

#### **Basic Theme Template:**
```css
/* YOUR THEME NAME */
QMainWindow { 
    background-color: #your-main-color; 
    color: #your-text-color;
}

QPushButton { 
    background-color: #button-color;
    border: 1px solid #border-color;
    border-radius: 4px;
    padding: 8px;
}

QPushButton:hover {
    background-color: #hover-color;
}

QTextEdit, QPlainTextEdit {
    background-color: #text-area-color;
    border: 1px solid #border-color;
    color: #text-color;
}

/* ... style other Qt widgets ... */
```

#### **Advanced Features:**
- **Gradients:** Use `qlineargradient()` for smooth color transitions
- **Images:** Reference assets with `url(path/to/image.png)`
- **Animations:** Hover and pressed states for interactive elements
- **Transparency:** Use `rgba()` colors for glass effects

#### **Sharing Your Theme:**
- Submit via **GitHub Pull Request** to share with community
- Include **screenshots** and **description** of your theme
- Follow **existing naming conventions**

### Why isn't my theme applying correctly?

**Common Theme Issues:**

1. **File Location:** Ensure `.qss` file is in `dataset_tools/themes/`
2. **File Extension:** Must be `.qss` (not `.css`)
3. **Syntax Errors:** Use Qt StyleSheet syntax, not regular CSS
4. **Restart Required:** Restart application to detect new themes
5. **Case Sensitivity:** Theme names are case-sensitive on some systems

**Debugging Tips:**
- Check console output for theme loading errors
- Start with a simple theme and add complexity gradually
- Use existing themes as reference for proper syntax

### How do fonts interact with themes?

**Font-Theme Compatibility:**
- ✅ **Fonts work with ALL themes** - they're applied globally
- ✅ **Theme switching preserves** your selected font
- ✅ **Custom fonts override** theme font specifications
- ⚠️ **Some themes specify** font families (like Terminal Hacker using monospace)

**Best Practices:**
- **Choose readable fonts** that work well at different sizes
- **Test font-theme combinations** before settling on your setup
- **Consider theme aesthetics** - serif fonts work well with classical themes, sans-serif with modern ones

---

## 📋 Log Files & Debugging Support

### Where are the log files created?

Dataset Tools **automatically creates detailed log files** every time you run the application:

- **📁 Location:** `logs/` directory (created in the same folder where you run Dataset Tools)
- **📄 File Name:** `dataset_tools_YYYYMMDD_HHMMSS.log` (timestamped for each session)
- **🔄 Fresh File:** New log file created every time you start the application
- **📝 Content:** Everything that happens during your session

**Example log file:** `dataset_tools_20250112_143015.log`

### What's included in the log files?

**Complete Application Activity:**
- ✅ Dataset Tools startup and shutdown
- ✅ File loading and metadata parsing  
- ✅ Theme changes and UI operations
- ✅ Error messages with full details
- ✅ PyQt6 (GUI framework) messages
- ✅ PIL/Pillow (image processing) activities
- ✅ External library interactions

**Sample log entry:**
```
2025-01-12 14:30:15 | INFO     | dataset_tools_app | main:140 | Dataset Tools v1.0.0 launching...
2025-01-12 14:30:16 | ERROR    | PyQt6 | widget_creation:45 | Widget failed to load: Invalid theme
2025-01-12 14:30:17 | DEBUG    | PIL | image_loader:123 | Loading image: /path/to/your/image.png
```

### How do I find my log file for bug reports?

**Step-by-Step:**
1. **Navigate** to the folder where you run Dataset Tools
2. **Look for** the `logs/` subdirectory 
3. **Find** the most recent file (newest timestamp)
4. **Attach** this file to your GitHub issue or support request

**Quick Tips:**
- 🕒 **Most Recent:** Files are timestamped - grab the newest one
- 💾 **File Size:** Log files are small (usually under 1MB) and safe to share
- 🔒 **Privacy:** Logs contain file paths but no file contents or personal data
- 📧 **Sharing:** Safe to attach to GitHub issues or email for support

### What if I can't find the logs directory?

**Troubleshooting Log Location:**
- **Default Location:** Same directory where you run `dataset-tools` command
- **Windows:** Usually in your user directory or where you opened Command Prompt
- **macOS/Linux:** Usually in your home directory or current terminal location
- **Alternative:** Run Dataset Tools with `--log-level DEBUG` to see more verbose output

**Still Can't Find Logs?**
1. Run Dataset Tools from a known location (like your Desktop)
2. The `logs/` folder will be created there
3. Or check the application startup messages - the log file path is displayed

### How do log levels affect what's recorded?

**Log Levels (use `--log-level LEVEL`):**
- **DEBUG:** Everything (most verbose) - best for troubleshooting
- **INFO:** Normal operations and important events (default)
- **WARNING:** Potential issues and important notices
- **ERROR:** Only errors and critical problems

**For Bug Reports:** Use `--log-level DEBUG` to get the most detailed information.

**Example:**
```bash
# Run with maximum logging detail
dataset-tools --log-level DEBUG
```

---

## 🔧 Troubleshooting

### "ModuleNotFoundError" when starting

**Solution:**
```bash
# Reinstall with all dependencies
pip install --force-reinstall kn-dataset-tools

# Or install missing module specifically
pip install [missing-module-name]
```

### Application crashes on startup

1. **Check Python version:** `python --version` (must be 3.10+)
2. **Try safe mode:** Start with minimal theme
3. **Clear settings:** Delete config files in `~/.config/DatasetViewer/`
4. **Check logs:** Look in the `logs/` directory for error details

### Fonts look wrong or missing

**Windows:**
```bash
# Install with font support
pip install kn-dataset-tools[fonts]
```

**macOS/Linux:**
- Install system fonts: `sudo apt install fonts-liberation` (Ubuntu)
- Restart the application after font installation

### Images won't load or display incorrectly

1. **Check file permissions:** Ensure files are readable
2. **Verify image format:** Use common formats (PNG, JPEG)
3. **Memory issues:** Try with smaller images first
4. **Missing codecs:** Install additional image libraries:
   ```bash
   pip install pillow[all]
   ```

### ComfyUI metadata not showing

1. **Verify format:** Ensure it's a valid ComfyUI workflow JSON
2. **Check file size:** Very large workflows may take time to parse
3. **Validate JSON:** Use a JSON validator to check file structure

### "Well, you said it worked on your machine!"

Sometimes, a feature may work in a development environment but not in the packaged application. This can happen because the lead developer, Duskfallcrew, often works in "editable mode" (`pip install -e .`), which can cause minor discrepancies in how files and dependencies are handled compared to a standard installation.

If you encounter an issue that seems to stem from this, please know that it is not your fault. We appreciate you bringing it to our attention so we can resolve it for all users. Please open a bug report on our GitHub repository, and we will address it as quickly as possible.

---

## 🚀 Performance & Optimization

### The application runs slowly

**Solutions:**
- **Reduce image size:** Large images (>4K) take time to load
- **Close other applications:** Free up system memory
- **Use SSD storage:** Faster disk access improves load times
- **Update dependencies:** `pip install --upgrade kn-dataset-tools`

### Memory usage is high

- **Expected behavior:** Large images require substantial memory
- **Workaround:** Process smaller batches of files
- **Monitoring:** Use Task Manager/Activity Monitor to track usage

---

## 🛠️ Development & Contributing

### How can I contribute?

1. **Report Bugs:** Use GitHub Issues with detailed descriptions
2. **Feature Requests:** Explain your use case and expected behavior
3. **Code Contributions:** Fork the repository and submit pull requests
4. **Theme Creation:** Add custom QSS themes to the themes directory
5. **Documentation:** Improve README, FAQ, or code comments

### Can I modify the source code?

Absolutely! Dataset Tools is GPL-3.0 licensed:
- ✅ Use for personal and commercial purposes
- ✅ Modify and distribute changes
- ✅ Create derivative works
- ⚠️ Must maintain GPL-3.0 license for derivatives
- ⚠️ Include copyright and license notices

### How do I create custom themes?

1. **Study existing themes** in `dataset_tools/themes/`
2. **Create a new .qss file** with your styling
3. **Test thoroughly** with different UI elements
4. **Submit via pull request** to share with community

**Theme Template:**
```css
/* YOUR THEME NAME */
QMainWindow { background-color: #your-color; }
QPushButton { /* your button styling */ }
/* ... other Qt widgets ... */
```

---

## 📞 Getting Help

### Where can I get support?

1. **GitHub Issues:** [Report bugs and request features](https://github.com/Ktiseos-Nyx/Dataset-Tools/issues)
2. **Documentation:** Check README.md and this FAQ first
3. **Community:** Join discussions in GitHub Discussions
4. **Email:** Contact via repository contact information

### What information should I include in bug reports?

- **Python version:** `python --version`
- **Dataset Tools version:** `pip show kn-dataset-tools`
- **Operating system:** Windows/macOS/Linux version
- **Error message:** Full traceback if available
- **Steps to reproduce:** Detailed description
- **Log files:** From the `logs/` directory (automatically created each session)
- **Screenshots:** If UI-related issue

**📁 Log File Location:**
Dataset Tools automatically creates detailed log files in a `logs/` directory:
- **File format:** `dataset_tools_YYYYMMDD_HHMMSS.log`
- **Content:** All application activities, errors, and external library messages
- **Location:** Same directory where you run Dataset Tools
- **Automatic:** Created fresh for each session

**To find your log file:**
1. Look for the `logs/` folder where you ran Dataset Tools
2. Find the most recent file (newest timestamp)
3. Attach this file to your bug report for fastest support

### How often is Dataset Tools updated?

- **Bug fixes:** Released as needed
- **Feature updates:** Regular releases based on community feedback
- **Security updates:** Immediate priority when necessary

---

## 🎯 Common Use Cases

### I'm a dataset curator

**Workflow:**
1. Load your dataset folder
2. Use batch metadata extraction
3. Export metadata summaries
4. Apply consistent tagging across files

### I'm a researcher/academic

**Features for you:**
- Metadata analysis and export
- Batch processing capabilities
- JSON/CSV export for analysis
- Reproducible metadata extraction

### I'm an AI artist/creator

**What you'll love:**
- View generation parameters easily
- Compare different model outputs
- Organize by sampler, model, settings
- Preview images with full metadata

### I'm a developer

**Integration options:**
- Use as Python library: `from dataset_tools import parse_metadata`
- Extend with custom parsers
- Add new file format support
- Create specialized themes

---

*Last Updated: January 2025*
*For the most current information, always check the [GitHub repository](https://github.com/Ktiseos-Nyx/Dataset-Tools)*