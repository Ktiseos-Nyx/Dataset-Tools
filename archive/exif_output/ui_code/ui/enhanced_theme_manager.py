# dataset_tools/ui/enhanced_theme_manager.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Enhanced theme management with multiple theme systems.

This module extends the base ThemeManager to support:
- qt-material themes (existing)
- qt-themes color palettes
- BreezeStyleSheets QSS themes
- unreal-stylesheet theming
"""

import re
from pathlib import Path

from PyQt6 import QtGui
from PyQt6 import QtWidgets as Qw
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from ..logger import info_monitor as nfo

# Import theme libraries with fallbacks
try:
    import qt_themes

    QT_THEMES_AVAILABLE = True
except ImportError:
    QT_THEMES_AVAILABLE = False

try:
    import unreal_stylesheet

    UNREAL_STYLESHEET_AVAILABLE = True
except ImportError:
    UNREAL_STYLESHEET_AVAILABLE = False

# Import qt-material with fallback
try:
    from qt_material import apply_stylesheet, list_themes

    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False

    def list_themes():
        return []

    def apply_stylesheet(app, theme, invert_secondary=False):
        pass


class EnhancedThemeManager:
    """Enhanced theme manager supporting multiple theme systems."""

    # qt-themes palette themes (conflict-free with stylesheets)
    # These are dynamically loaded from qt_themes.get_themes()
    QT_THEMES_PALETTES = []

    THEME_CATEGORIES = {
        "qt_material": "Material Design",
        "qt_themes": "Color Palettes",
        "unreal": "Unreal Style",
        "GTRONICK_QSS": "GTRONICK's Themes",
        "KTISEOS_NYX_THEMES": "Ktiseos Nyx's Themes",
        "custom_qss": "Custom Themes",
    }

    def __init__(self, main_window: Qw.QMainWindow, settings: QSettings):
        self.main_window = main_window
        self.settings = settings
        self.theme_actions: dict[str, QtGui.QAction] = {}
        self.current_theme = "qt_material:dark_teal.xml"
        self.current_palette_theme: str | None = None
        self.current_qt_material_theme: str | None = None

        # Load qt-themes palettes dynamically
        self._load_qt_themes_palettes()

        nfo("Enhanced ThemeManager initialized")
        nfo(
            "Available systems: qt-material=%s, qt-themes=%s, unreal=%s",
            QT_MATERIAL_AVAILABLE,
            QT_THEMES_AVAILABLE,
            UNREAL_STYLESHEET_AVAILABLE,
        )

    def _load_qt_themes_palettes(self) -> None:
        """Load available qt-themes palettes dynamically."""
        if QT_THEMES_AVAILABLE:
            try:
                # Get themes using the get_themes function
                if hasattr(qt_themes, "get_themes"):
                    themes_dict = qt_themes.get_themes()
                    # Extract theme names from the dictionary
                    self.QT_THEMES_PALETTES = list(themes_dict.keys())
                else:
                    # Fallback to hardcoded list if get_themes not available
                    self.QT_THEMES_PALETTES = [
                        "one_dark_two",
                        "monokai",
                        "nord",
                        "catppuccin_mocha",
                        "catppuccin_macchiato",
                        "catppuccin_frappe",
                        "catppuccin_latte",
                        "atom_one",
                        "github_dark",
                        "github_light",
                        "dracula",
                        "blender",
                    ]
                nfo("Loaded %d qt-themes palettes", len(self.QT_THEMES_PALETTES))
            except Exception as e:
                nfo("Error loading qt-themes palettes: %s", e)
                self.QT_THEMES_PALETTES = []
        else:
            self.QT_THEMES_PALETTES = []

    def get_available_themes(self) -> dict[str, list[str]]:
        """Get all available themes organized by category."""
        themes = {}

        # qt-material themes
        if QT_MATERIAL_AVAILABLE:
            themes["qt_material"] = sorted(list_themes(), key=self._natural_sort_key)

        # qt-themes color palettes
        if QT_THEMES_AVAILABLE:
            themes["qt_themes"] = sorted(self.QT_THEMES_PALETTES.copy(), key=self._natural_sort_key)

        # Unreal stylesheet
        if UNREAL_STYLESHEET_AVAILABLE:
            themes["unreal"] = ["unreal_engine_5"]

        # Custom QSS themes from subfolders
        custom_themes = self._load_custom_qss_themes_from_subfolders()

        # Filter KTISEOS_NYX_THEMES based on chaos unlock status
        if "KTISEOS_NYX_THEMES" in custom_themes:
            chaos_unlocked = self.settings.value("chaosCollection/unlocked", False, type=bool)
            if not chaos_unlocked:
                # Remove 'moms_2am_' themes if not unlocked
                custom_themes["KTISEOS_NYX_THEMES"] = [
                    theme for theme in custom_themes["KTISEOS_NYX_THEMES"] if not theme.startswith("moms_2am_")
                ]
                if not custom_themes["KTISEOS_NYX_THEMES"]:
                    del custom_themes["KTISEOS_NYX_THEMES"]

        themes.update(custom_themes)

        return themes

    def _natural_sort_key(self, s: str) -> list[str]:
        """Create a sort key for natural sorting (handles numbers in strings)."""
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r"([0-9]+)", s)]

    def _load_custom_qss_themes_from_subfolders(self) -> dict[str, list[str]]:
        """Load custom QSS themes from subdirectories in the 'themes' directory."""
        custom_themes = {}
        themes_dir = Path(__file__).parent.parent / "themes"
        if themes_dir.exists() and themes_dir.is_dir():
            for sub_dir in themes_dir.iterdir():
                if sub_dir.is_dir():
                    category_name = sub_dir.name
                    qss_files = [qss_file.stem for qss_file in sub_dir.glob("*.qss")]
                    if qss_files:
                        custom_themes[category_name] = sorted(qss_files, key=str.lower)
            # also load any loose qss files
            loose_qss_files = [qss_file.stem for qss_file in themes_dir.glob("*.qss")]
            if loose_qss_files:
                custom_themes["custom_qss"] = sorted(loose_qss_files, key=str.lower)
        return custom_themes

    def _validate_asset_support(self, assets_dir: Path) -> dict[str, bool]:
        """Validate which asset formats are available and supported."""
        supported_formats = {
            ".png": True,  # Always supported
            ".jpg": True,  # Always supported
            ".jpeg": True,  # Always supported
            ".bmp": True,  # Always supported
            ".gif": True,  # Supported but may have limitations
            ".svg": False,  # Limited support in Qt stylesheets
            ".webp": False,  # Not widely supported
        }

        available_assets = {}
        if assets_dir.exists():
            for asset_file in assets_dir.iterdir():
                if asset_file.is_file():
                    ext = asset_file.suffix.lower()
                    available_assets[asset_file.name] = {
                        "path": asset_file,
                        "format": ext,
                        "supported": supported_formats.get(ext, False),
                        "size": asset_file.stat().st_size,
                    }

        return available_assets

    def apply_theme(self, theme_id: str, initial_load: bool = False) -> bool:
        """Apply a theme by its ID (category:name format).

        Args:
            theme_id: Theme identifier in format "category:name"
            initial_load: Whether this is the initial theme load

        Returns:
            True if theme was applied successfully

        """
        try:
            category, name = theme_id.split(":", 1)
        except ValueError:
            nfo("Invalid theme ID format: %s", theme_id)
            return False

        app = QApplication.instance()
        if not app:
            nfo("No QApplication instance found")
            return False

        success = False

        if category == "qt_material" and QT_MATERIAL_AVAILABLE:
            success = self._apply_qt_material_theme(name, app)

        elif category == "qt_themes" and QT_THEMES_AVAILABLE:
            success = self._apply_qt_themes_palette(name, app)

        elif category == "unreal" and UNREAL_STYLESHEET_AVAILABLE:
            success = self._apply_unreal_theme(app)

        elif category in self.THEME_CATEGORIES:
            success = self._apply_custom_qss_theme(theme_id, app)

        if success:
            self.current_theme = theme_id

            # Update theme action states
            for action_id, action in self.theme_actions.items():
                action.setChecked(action_id == theme_id)

            # Save theme preference (but not on initial load)
            if not initial_load:
                self.settings.setValue("enhanced_theme", theme_id)

            action_text = "Initial theme loaded" if initial_load else "Theme applied and saved"
            nfo("%s: %s", action_text, theme_id)

            # Re-apply fonts after theme to ensure they don't get overridden
            if not initial_load and hasattr(self, "main_window") and hasattr(self.main_window, "apply_global_font"):
                # Use a timer to delay font application slightly to ensure theme is fully applied first
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(100, self.main_window.apply_global_font)

        return success

    def _apply_qt_material_theme(self, theme_name: str, app: QApplication) -> bool:
        """Apply a qt-material theme."""
        try:
            invert_secondary = theme_name.startswith("dark_")
            apply_stylesheet(app, theme=theme_name, invert_secondary=invert_secondary)

            # Track the current qt-material theme
            self.current_qt_material_theme = theme_name

            # Clear any qt-themes palette
            if self.current_palette_theme:
                self.current_palette_theme = None

            nfo(f"Successfully applied qt-material theme: {theme_name}")
            return True
        except Exception as e:
            nfo("Error applying qt-material theme %s: %s", theme_name, e)
            return False

    def _apply_qt_themes_palette(self, palette_name: str, app: QApplication) -> bool:
        """Apply a qt-themes color palette."""
        try:
            # qt-themes uses set_theme(app, theme_name) format
            qt_themes.set_theme(app, palette_name)
            self.current_palette_theme = palette_name
            return True
        except Exception as e:
            nfo("Error applying qt-themes palette %s: %s", palette_name, e)
            return False

    def _apply_custom_qss_theme(self, theme_id: str, app: QApplication) -> bool:
        """Apply a custom QSS theme from the 'themes' directory."""
        try:
            category, theme_name = theme_id.split(":", 1)
        except ValueError:
            # for backward compatibility with old theme saving
            category = "custom_qss"
            theme_name = theme_id

        try:
            themes_dir = Path(__file__).parent.parent / "themes"
            # Look for the theme in its category sub-directory
            qss_file = themes_dir / category / f"{theme_name}.qss"
            if not qss_file.exists():
                # Fallback for loose files
                qss_file = themes_dir / f"{theme_name}.qss"

            if not qss_file.exists():
                nfo("Custom QSS theme file not found: %s", qss_file)
                return False

            with open(qss_file, encoding="utf-8") as f:
                stylesheet = f.read()

            # Handle both local assets and GitHub URLs
            import re

            # First, handle GitHub URLs - download them to local cache
            def replace_github_url(match):
                github_url = match.group(1)
                if "github.com" in github_url or "githubusercontent.com" in github_url:
                    # Extract filename from URL
                    filename = github_url.split("/")[-1]
                    cache_dir = themes_dir / "cache"
                    cache_dir.mkdir(exist_ok=True)
                    cached_file = cache_dir / filename

                    # Download if not cached
                    if not cached_file.exists():
                        try:
                            import urllib.request

                            nfo(f"Downloading GitHub asset: {github_url}")
                            urllib.request.urlretrieve(
                                github_url, cached_file
                            )  # URL scheme is validated to be GitHub, which is trusted for asset downloads.
                            nfo(f"Cached asset: {cached_file}")
                        except Exception as e:
                            nfo(f"Failed to download asset {github_url}: {e}")
                            return match.group(0)  # Return original if download fails

                    return f'url("{cached_file}")'
                return match.group(0)

            # Replace GitHub URLs
            stylesheet = re.sub(
                r'url\("(https://[^"]*github[^"]*\.png)"\)',
                replace_github_url,
                stylesheet,
            )
            stylesheet = re.sub(
                r"url\('(https://[^']*github[^']*\.png)'\)",
                replace_github_url,
                stylesheet,
            )

            # Then handle local assets
            assets_dir = themes_dir / "assets"
            if assets_dir.exists():
                # Validate available assets
                available_assets = self._validate_asset_support(assets_dir)
                nfo(f"Found {len(available_assets)} assets for theme {theme_name}")

                def replace_asset_url_enhanced(match):
                    relative_path = match.group(1)
                    if relative_path.startswith("assets/"):
                        asset_file = relative_path.replace("assets/", "")
                        absolute_path = assets_dir / asset_file

                        if absolute_path.exists():
                            return f'url("{absolute_path}")'
                        nfo(f"Asset not found: {absolute_path}")
                    return match.group(0)

                # Replace local asset URLs
                stylesheet = re.sub(r'url\("(assets/[^"]+)"\)', replace_asset_url_enhanced, stylesheet)
                stylesheet = re.sub(r"url\('(assets/[^']+)'\)", replace_asset_url_enhanced, stylesheet)

            nfo(f"Processed custom QSS theme: {theme_name}, asset replacements applied")

            # IMPORTANT: Clear qt-material styling before applying custom QSS
            # qt-material's apply_stylesheet sets comprehensive styles that override custom QSS
            app.setStyleSheet("")  # Clear any existing stylesheets first

            # Apply the custom QSS theme
            app.setStyleSheet(stylesheet)

            # Clear any qt-themes palette and qt-material theme tracking
            if self.current_palette_theme:
                self.current_palette_theme = None
            if self.current_qt_material_theme:
                self.current_qt_material_theme = None

            nfo(f"Successfully applied custom QSS theme: {theme_name}")
            return True
        except Exception as e:
            nfo("Error applying custom QSS theme %s: %s", theme_name, e)
            return False

    def _apply_unreal_theme(self, app: QApplication) -> bool:
        """Apply the Unreal Engine stylesheet."""
        try:
            unreal_stylesheet.setup(app)

            # Clear any qt-themes palette
            if self.current_palette_theme:
                self.current_palette_theme = None

            return True
        except Exception as e:
            nfo("Error applying Unreal theme: %s", e)
            return False

    def apply_saved_theme(self) -> None:
        """Apply the saved theme from settings."""
        saved_theme = self.settings.value("enhanced_theme", "qt_material:dark_teal.xml")

        # Validate saved theme exists
        available_themes = self.get_available_themes()

        try:
            category, name = saved_theme.split(":", 1)
            if category in available_themes and name in available_themes[category]:
                self.apply_theme(saved_theme, initial_load=True)
                return
        except ValueError:
            pass

        # Fallback to default theme
        if QT_MATERIAL_AVAILABLE and "qt_material" in available_themes:
            fallback = "qt_material:dark_teal.xml"
            if "dark_teal.xml" in available_themes["qt_material"]:
                self.apply_theme(fallback, initial_load=True)
            elif available_themes["qt_material"]:
                fallback = f"qt_material:{available_themes['qt_material'][0]}"
                self.apply_theme(fallback, initial_load=True)

    def create_theme_menus(self, parent_menu: Qw.QMenu) -> None:
        """Create organized theme menus."""
        self._populate_theme_menus(parent_menu)

    def _populate_theme_menus(self, parent_menu: Qw.QMenu) -> None:
        """Helper to populate theme menus, allowing refresh."""
        # Clear existing actions to repopulate
        parent_menu.clear()
        self.theme_actions.clear()

        available_themes = self.get_available_themes()

        if not available_themes:
            no_themes_action = QtGui.QAction("No themes available", self.main_window)
            no_themes_action.setEnabled(False)
            parent_menu.addAction(no_themes_action)
            return

        # Create action group for exclusive selection
        theme_group = QtGui.QActionGroup(self.main_window)
        theme_group.setExclusive(True)

        for category, themes in available_themes.items():
            if not themes:
                continue

            # Create submenu for category
            category_name = self.THEME_CATEGORIES.get(category, category.title())
            submenu = parent_menu.addMenu(category_name)

            for theme_name in themes:
                theme_id = f"{category}:{theme_name}"
                display_name = theme_name.replace("_", " ").replace(".xml", "").title()

                action = QtGui.QAction(display_name, self.main_window)
                action.setCheckable(True)
                action.setData(theme_id)
                action.triggered.connect(self._on_theme_action_triggered)

                submenu.addAction(action)
                theme_group.addAction(action)
                self.theme_actions[theme_id] = action

    def _on_theme_action_triggered(self) -> None:
        """Handle theme action being triggered."""
        action = self.main_window.sender()
        if action and isinstance(action, QtGui.QAction):
            theme_id = action.data()
            if theme_id:
                self.apply_theme(theme_id)

    def refresh_theme_categories(self) -> None:
        """Refreshes the theme menus, typically after a setting change (e.g., unlock)."""
        if hasattr(self.main_window, "menu_manager"):
            # Assuming menu_manager has a reference to the themes menu
            # This might need adjustment based on actual menu structure
            theme_menu = self.main_window.menu_manager.themes_menu  # Assuming this attribute exists
            if theme_menu:
                self._populate_theme_menus(theme_menu)
                nfo("Theme menus refreshed.")
            else:
                nfo("Could not find themes menu to refresh.")
        else:
            nfo("Menu manager not available to refresh themes.")

    def get_theme_info(self) -> dict[str, any]:
        """Get information about available theme systems."""
        available_themes = self.get_available_themes()

        info = {
            "current_theme": self.current_theme,
            "current_palette": self.current_palette_theme,
            "available_systems": {
                "qt_material": QT_MATERIAL_AVAILABLE,
                "qt_themes": QT_THEMES_AVAILABLE,
                "unreal_stylesheet": UNREAL_STYLESHEET_AVAILABLE,
                "custom_qss": True,
            },
            "available_themes": available_themes,
            "total_themes": sum(len(themes) for themes in available_themes.values()),
        }

        return info

    def print_theme_report(self) -> None:
        """Print a comprehensive theme availability report."""
        info = self.get_theme_info()

        print("=" * 60)
        print("ENHANCED THEME SYSTEM REPORT")
        print("=" * 60)
        print(f"Current theme: {info['current_theme']}")
        if info["current_palette"]:
            print(f"Current palette: {info['current_palette']}")
        print(f"Total themes available: {info['total_themes']}")
        print()

        print("THEME SYSTEMS:")
        for system, available in info["available_systems"].items():
            status = "✓" if available else "✗"
            print(f"  {status} {system}")
        print()

        print("AVAILABLE THEMES BY CATEGORY:")
        for category, themes in info["available_themes"].items():
            category_name = self.THEME_CATEGORIES.get(category, category.title())
            print(f"  {category_name}: {len(themes)} themes")
            for theme in themes[:5]:  # Show first 5
                print(f"    • {theme}")
            if len(themes) > 5:
                print(f"    ... and {len(themes) - 5} more")

        print("=" * 60)


# Convenience functions for backward compatibility
def get_enhanced_theme_manager(main_window: Qw.QMainWindow, settings: QSettings) -> EnhancedThemeManager:
    """Get an enhanced theme manager instance."""
    return EnhancedThemeManager(main_window, settings)


def get_theme_manager(main_window: Qw.QMainWindow, settings: QSettings) -> EnhancedThemeManager:
    """Alias for get_enhanced_theme_manager."""
    return get_enhanced_theme_manager(main_window, settings)
