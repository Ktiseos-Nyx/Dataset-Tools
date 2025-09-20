# dataset_tools/ui/font_manager.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Font management for Dataset Tools.

This module provides centralized font management with open source fonts
and graceful fallbacks to system defaults.
"""

from pathlib import Path

from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication

from ..logger import info_monitor as nfo


class FontManager:
    """Manages application fonts with open source alternatives."""

    # Bundled fonts (loaded from fonts/ directory)
    # Complete collection of all fonts in the fonts folder
    BUNDLED_FONTS = {
        # Professional fonts
        "Open Sans": [
            "OpenSans-VariableFont_wdth,wght.ttf",
            "OpenSans-Italic-VariableFont_wdth,wght.ttf",
        ],
        "Inter": [
            "Inter-VariableFont_opsz,wght.ttf",
            "Inter-Italic-VariableFont_opsz,wght.ttf",
        ],
        "DM Sans": [
            "DMSans-VariableFont_opsz,wght.ttf",
            "DMSans-Italic-VariableFont_opsz,wght.ttf",
        ],
        "Work Sans": [
            "WorkSans-VariableFont_wght.ttf",
            "WorkSans-Italic-VariableFont_wght.ttf",
        ],
        "Roboto": [
            "Roboto-VariableFont_wdth,wght.ttf",
            "Roboto-Italic-VariableFont_wdth,wght.ttf",
        ],
        "IBM Plex Sans": [
            "IBMPlexSans-VariableFont_wdth,wght.ttf",
            "IBMPlexSans-Italic-VariableFont_wdth,wght.ttf",
        ],
        "Nunito": [
            "Nunito-VariableFont_wght.ttf",
            "Nunito-Italic-VariableFont_wght.ttf",
        ],
        "PT Sans": [
            "PTSans-Regular.ttf",
            "PTSans-Bold.ttf",
            "PTSans-Italic.ttf",
            "PTSans-BoldItalic.ttf",
        ],
        "Radio Canada": [
            "RadioCanada-VariableFont_wdth,wght.ttf",
            "RadioCanada-Italic-VariableFont_wdth,wght.ttf",
        ],
        # Monospace fonts
        "JetBrains Mono": ["JetBrainsMono-Regular.ttf", "JetBrainsMono-Bold.ttf"],
        "Syne Mono": ["SyneMono-Regular.ttf"],
        "VT323": ["VT323-Regular.ttf"],
        # Display and decorative fonts
        "Orbitron": ["Orbitron-VariableFont_wght.ttf"],
        "Jura": ["Jura-VariableFont_wght.ttf"],
        "Turret Road": [
            "TurretRoad-Regular.ttf",
            "TurretRoad-Light.ttf",
            "TurretRoad-Medium.ttf",
            "TurretRoad-Bold.ttf",
            "TurretRoad-ExtraLight.ttf",
            "TurretRoad-ExtraBold.ttf",
        ],
        # Pixel and retro fonts
        "Pixelify Sans": [
            "PixelifySans-Regular.ttf",
            "PixelifySans-Medium.ttf",
            "PixelifySans-SemiBold.ttf",
            "PixelifySans-Bold.ttf",
            "PixelifySans-VariableFont_wght.ttf",
        ],
        "Silkscreen": ["Silkscreen-Regular.ttf", "Silkscreen-Bold.ttf"],
        # Unique and specialty fonts
        "Dongle": ["Dongle-Regular.ttf", "Dongle-Light.ttf", "Dongle-Bold.ttf"],
        "Doppio One": ["DoppioOne-Regular.ttf"],
        "Kosugi Maru": ["KosugiMaru-Regular.ttf"],
        "Mandali": ["Mandali-Regular.ttf"],
        "Tsukimi Rounded": [
            "TsukimiRounded-Regular.ttf",
            "TsukimiRounded-Light.ttf",
            "TsukimiRounded-Medium.ttf",
            "TsukimiRounded-SemiBold.ttf",
            "TsukimiRounded-Bold.ttf",
        ],
    }

    # Font stacks with bundled fonts prioritized
    FONT_STACKS = {
        "ui": [
            "Open Sans",  # Our primary bundled font
            "Inter",  # Modern and clean
            "DM Sans",  # Professional alternative
            "Nunito",  # Friendly rounded
            "Roboto",  # Google's system font
            "IBM Plex Sans",  # Technical but readable
            "Work Sans",  # Clean and versatile
            "PT Sans",  # Classic and readable
            "Radio Canada",  # Government standard
            "system-ui",  # System UI font fallback
            "sans-serif",  # Generic fallback
        ],
        "monospace": [
            "JetBrains Mono",  # Our primary monospace font
            "Syne Mono",  # Modern monospace
            "VT323",  # Retro terminal style
            "Silkscreen",  # Pixel perfect monospace
            "Source Code Pro",  # Adobe's open source monospace
            "Consolas",  # Windows system font
            "Monaco",  # macOS system font
            "monospace",  # Generic fallback
        ],
        "display": [  # New category for decorative/theme fonts
            "Orbitron",  # Futuristic
            "Jura",  # Sci-fi style
            "Turret Road",  # Bold and distinctive
            "Pixelify Sans",  # Pixel art style
            "Dongle",  # Quirky and fun
            "Tsukimi Rounded",  # Soft and rounded
            "Doppio One",  # Unique display
            "Kosugi Maru",  # Japanese style
            "Mandali",  # Clean geometric
        ],
        "reading": [
            "PT Sans",  # Our best serif alternative
            "Nunito",  # Readable and friendly
            "Open Sans",  # Clean and readable
            "system-ui",  # Use system font for reading
            "serif",  # Generic fallback
        ],
    }

    def __init__(self):
        self.app = QApplication.instance()

        # Load bundled fonts first
        self._load_bundled_fonts()

        self.available_fonts = set(QFontDatabase.families())

        # Cache for resolved fonts
        self._font_cache = {}

        nfo("FontManager initialized with %d available fonts", len(self.available_fonts))

    def _load_bundled_fonts(self) -> None:
        """Load bundled fonts from the fonts/ directory."""
        # Get the fonts directory relative to this file
        current_dir = Path(__file__).parent.parent
        fonts_dir = current_dir / "fonts"

        if not fonts_dir.exists():
            nfo("Fonts directory not found: %s", fonts_dir)
            return

        loaded_count = 0

        for font_family, font_files in self.BUNDLED_FONTS.items():
            for font_file in font_files:
                font_path = fonts_dir / font_file

                if font_path.exists():
                    try:
                        font_id = QFontDatabase.addApplicationFont(str(font_path))
                        if font_id != -1:
                            loaded_families = QFontDatabase.applicationFontFamilies(font_id)
                            if loaded_families:
                                nfo(
                                    "Loaded bundled font: %s from %s",
                                    loaded_families[0],
                                    font_file,
                                )
                                loaded_count += 1
                            else:
                                nfo(
                                    "Warning: Font loaded but no families found: %s",
                                    font_file,
                                )
                        else:
                            nfo("Failed to load bundled font: %s", font_file)
                    except Exception as e:
                        nfo("Error loading bundled font %s: %s", font_file, e)
                else:
                    nfo("Bundled font file not found: %s", font_path)

        nfo("Loaded %d bundled font files", loaded_count)

    def get_best_font(
        self,
        font_type: str = "ui",
        size: int = 9,
        weight: QFont.Weight = QFont.Weight.Normal,
    ) -> QFont:
        """Get the best available font from a font stack.

        Args:
            font_type: Type of font ('ui', 'monospace', 'reading')
            size: Font size in points
            weight: Font weight

        Returns:
            QFont object with the best available font

        """
        cache_key = (font_type, size, weight)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        font_stack = self.FONT_STACKS.get(font_type, self.FONT_STACKS["ui"])

        # Try each font in the stack
        for font_name in font_stack:
            if font_name in {"system-ui", "sans-serif", "serif", "monospace"}:
                # Use system default for generic names
                font = QFont()
                if font_name == "monospace":
                    font.setFamily("monospace")
                    font.setStyleHint(QFont.StyleHint.Monospace)
                elif font_name == "serif":
                    font.setStyleHint(QFont.StyleHint.Serif)
                else:
                    font.setStyleHint(QFont.StyleHint.SansSerif)

                font.setPointSize(size)
                font.setWeight(weight)

                self._font_cache[cache_key] = font
                nfo("Using system font for %s: %s", font_type, font_name)
                return font

            if font_name in self.available_fonts:
                # Found an available font
                font = QFont(font_name, size, weight)
                self._font_cache[cache_key] = font
                nfo("Using font for %s: %s", font_type, font_name)
                return font

        # Fallback to system default
        font = QFont()
        font.setPointSize(size)
        font.setWeight(weight)
        self._font_cache[cache_key] = font
        nfo("Using system default font for %s", font_type)
        return font

    def get_ui_font(self, size: int = 9, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
        """Get the best UI font."""
        return self.get_best_font("ui", size, weight)

    def get_monospace_font(self, size: int = 9, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
        """Get the best monospace font."""
        return self.get_best_font("monospace", size, weight)

    def get_reading_font(self, size: int = 10, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
        """Get the best reading font."""
        return self.get_best_font("reading", size, weight)

    def apply_fonts_to_app(self) -> None:
        """Apply optimal fonts to the application."""
        if not self.app:
            nfo("No QApplication instance found")
            return

        # Set default application font
        default_font = self.get_ui_font(size=9)
        self.app.setFont(default_font)
        nfo("Applied default font to application: %s", default_font.family())

    def get_font_info(self) -> dict:
        """Get information about available fonts."""
        info = {
            "total_fonts": len(self.available_fonts),
            "bundled_fonts": {},
            "available_priority_fonts": {},
            "recommended_fonts": [],
        }

        # Check bundled fonts status
        for font_family, font_files in self.BUNDLED_FONTS.items():
            bundled_status = []
            for font_file in font_files:
                font_path = Path(__file__).parent.parent / "fonts" / font_file
                bundled_status.append(
                    {
                        "file": font_file,
                        "exists": font_path.exists(),
                        "loaded": font_family in self.available_fonts,
                    }
                )
            info["bundled_fonts"][font_family] = bundled_status

        # Check which priority fonts are available
        for font_type, font_stack in self.FONT_STACKS.items():
            available = []
            for font_name in font_stack:
                if font_name in self.available_fonts:
                    available.append(font_name)
            info["available_priority_fonts"][font_type] = available

        # Recommend fonts to install
        recommended = set()
        for font_stack in self.FONT_STACKS.values():
            for font_name in font_stack[:3]:  # Top 3 from each stack
                if font_name not in self.available_fonts and font_name not in {
                    "system-ui",
                    "sans-serif",
                    "serif",
                    "monospace",
                }:
                    recommended.add(font_name)

        info["recommended_fonts"] = sorted(recommended)
        return info

    def print_font_report(self) -> None:
        """Print a report of available fonts."""
        info = self.get_font_info()

        print("=" * 60)
        print("FONT AVAILABILITY REPORT")
        print("=" * 60)
        print(f"Total fonts available: {info['total_fonts']}")
        print()

        # Show bundled fonts status
        print("BUNDLED FONTS STATUS:")
        for font_family, statuses in info["bundled_fonts"].items():
            print(f"  {font_family}:")
            for status in statuses:
                exists_icon = "✓" if status["exists"] else "✗"
                loaded_icon = "✓" if status["loaded"] else "✗"
                print(f"    {exists_icon} File: {status['file']}")
                print(f"    {loaded_icon} Loaded: {status['loaded']}")
        print()

        for font_type, available in info["available_priority_fonts"].items():
            print(f"{font_type.upper()} FONTS:")
            if available:
                for font in available:
                    print(f"  ✓ {font}")
            else:
                print("  ✗ No priority fonts available")
            print()

        if info["recommended_fonts"]:
            print("RECOMMENDED FONTS TO INSTALL:")
            for font in info["recommended_fonts"]:
                print(f"  • {font}")
        else:
            print("✓ All recommended fonts are available!")

        print("=" * 60)


# Global font manager instance
_font_manager = None


def get_font_manager() -> FontManager:
    """Get the global font manager instance."""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager


def apply_fonts_to_app() -> None:
    """Apply optimal fonts to the current application."""
    manager = get_font_manager()
    manager.apply_fonts_to_app()


def get_ui_font(size: int = 9, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Get the best UI font."""
    manager = get_font_manager()
    return manager.get_ui_font(size, weight)


def get_monospace_font(size: int = 9, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Get the best monospace font."""
    manager = get_font_manager()
    return manager.get_monospace_font(size, weight)


def get_reading_font(size: int = 10, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Get the best reading font."""
    manager = get_font_manager()
    return manager.get_reading_font(size, weight)
