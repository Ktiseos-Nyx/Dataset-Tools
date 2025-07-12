# Font Collection for Dataset Tools

This directory contains a collection of high-quality open source fonts
bundled with Dataset Tools to provide users with exceptional typography
choices while maintaining excellent readability and visual appeal.

## Font Philosophy

**Complete Typography Experience:**
- Provide a curated selection of the best open source fonts
- Cover all use cases from professional UI to creative themes
- Include specialized fonts for retro, pixel, and themed experiences
- Respect font licensing and provide proper attribution
- No system font dependencies - complete self-contained typography

## Font Categories

### 📝 Professional Fonts (UI & Reading)
Perfect for daily use, business presentations, and professional interfaces:

- **Open Sans** - Our primary UI font (Google Fonts)
- **Inter** - Modern geometric sans-serif designed for UI
- **DM Sans** - Professional sans-serif with excellent readability
- **Work Sans** - Clean and versatile, great for interfaces  
- **Roboto** - Google's flagship font family
- **IBM Plex Sans** - Technical but friendly, IBM's corporate font
- **Nunito** - Rounded and approachable sans-serif
- **PT Sans** - Comprehensive font family with excellent language support
- **Radio Canada** - Official font of the Government of Canada

### ⌨️ Monospace Fonts (Code & Technical)
Essential for displaying metadata, code, and technical content:

- **JetBrains Mono** - Premium code font with ligatures
- **Syne Mono** - Modern artistic monospace
- **VT323** - Authentic terminal/VT100 recreation
- **Silkscreen** - Pixel-perfect bitmap-style monospace

### 🎮 Display & Theme Fonts
For special themes, creative projects, and visual flair:

- **Orbitron** - Futuristic geometric sans-serif
- **Jura** - Sci-fi inspired display font
- **Turret Road** - Bold military/stencil style (6 weights)
- **Pixelify Sans** - Perfect pixel art recreation (5 weights)
- **Dongle** - Korean-inspired quirky display font (3 weights)
- **Tsukimi Rounded** - Soft Japanese-style rounded font (5 weights)
- **Doppio One** - Unique display font with character
- **Kosugi Maru** - Japanese rounded sans-serif
- **Mandali** - Clean geometric sans-serif

## Font Statistics

- **Total Font Families**: 22
- **Total Font Files**: 52+ individual TTF files
- **License**: All fonts are SIL Open Font License 1.1 or equivalent
- **Languages Supported**: Latin, Cyrillic, Japanese, Korean, and more
- **Estimated Bundle Size**: ~15-20MB (providing immense value)

## Font Loading Strategy

1. **All fonts loaded at startup**: Complete collection available immediately
2. **User choice priority**: Font selection in settings shows only bundled fonts
3. **Theme integration**: Themes use bundled fonts exclusively
4. **No system dependencies**: Consistent appearance across all platforms
5. **Fallback hierarchy**: Intelligent font stacks for each category

## Licensing & Attribution

All fonts included are open source with compatible licenses:

- **Primary License**: SIL Open Font License 1.1 (OFL)
- **Attribution**: See `LICENSE.txt` and `OFL.txt` for complete licensing information
- **Commercial Use**: ✅ All fonts are free for commercial use
- **Modification**: ✅ Fonts can be modified under OFL terms
- **Redistribution**: ✅ Can be bundled and redistributed

## Font Management

The `FontManager` class (`font_manager.py`) handles:
- Automatic font loading at application startup
- Font family organization and categorization  
- Intelligent font stacks for different use cases
- Graceful fallback handling
- Font information reporting and debugging

## Usage in Themes

Theme creators can confidently use any bundled font:

```css
/* Professional themes */
QWidget { font-family: "Open Sans", "Inter", "DM Sans"; }

/* Retro/Gaming themes */  
QWidget { font-family: "VT323", "Pixelify Sans", "Silkscreen"; }

/* Futuristic themes */
QWidget { font-family: "Orbitron", "Jura", "Turret Road"; }

/* Code/Technical themes */
QWidget { font-family: "JetBrains Mono", "Syne Mono"; }
```

## Font Updates

To update the font collection:

1. Download latest versions from [Google Fonts](https://fonts.google.com)
2. All Google Fonts are OFL licensed and compatible ✅
3. Update `BUNDLED_FONTS` dictionary in `font_manager.py`
4. Test font loading with `FontManager.print_font_report()`
5. Update this README with any new additions

**Pro tip**: Google Fonts provides the highest quality, most up-to-date versions of these fonts with perfect licensing!

## Special Thanks

Massive gratitude to **Google Fonts** for making virtually all of these amazing fonts freely available! 🎉

**Google Fonts Collection Includes:**
- **Professional**: Open Sans, Inter, DM Sans, Work Sans, Roboto, Nunito, PT Sans, IBM Plex Sans
- **Monospace**: JetBrains Mono, Syne Mono, VT323, Silkscreen  
- **Display**: Orbitron, Jura, Turret Road, Pixelify Sans, Dongle,
  Tsukimi Rounded, Doppio One, Kosugi Maru, Mandali
- **Government**: Radio Canada (via Google Fonts)

**Sources:**
- **Primary**: [Google Fonts](https://fonts.google.com) - The world's largest free
  font library
- **JetBrains**: [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) (also available on Google Fonts)
- **Special thanks** to the font designers who contributed their work to Google
  Fonts

---

*Dataset Tools - Making beautiful typography accessible to everyone* ✨