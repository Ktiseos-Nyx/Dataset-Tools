# dataset_tools/ui/icon_manager.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Icon management for Dataset Tools.

This module provides SVG icon loading and theme-aware coloring
to ensure icons work perfectly with Qt Material themes.
"""

from pathlib import Path

from PyQt6 import QtCore, QtGui
from PyQt6 import QtWidgets as Qw
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from ..logger import info_monitor as nfo


class IconManager:
    """Manages SVG icons with theme-aware coloring.

    This class handles loading SVG icons and automatically adjusts
    their colors to match the current Qt Material theme.
    """

    def __init__(self, icons_directory: str | None = None):
        """Initialize the icon manager.

        Args:
            icons_directory: Path to directory containing SVG icons

        """
        self.icons_directory = Path(icons_directory) if icons_directory else Path(__file__).parent / "icons"
        self.icon_cache: dict[str, QIcon] = {}
        self.current_theme_colors: dict[str, QColor] = {}

        # Default icon colors for different themes
        self.theme_color_schemes = {
            "dark": {
                "primary": QColor(255, 255, 255),  # White for dark themes
                "secondary": QColor(180, 180, 180),  # Light gray
                "accent": QColor(0, 188, 212),  # Cyan accent
                "disabled": QColor(100, 100, 100),  # Dark gray
            },
            "light": {
                "primary": QColor(33, 33, 33),  # Dark gray for light themes
                "secondary": QColor(117, 117, 117),  # Medium gray
                "accent": QColor(0, 150, 136),  # Teal accent
                "disabled": QColor(200, 200, 200),  # Light gray
            },
        }

        # Detect initial theme
        self._detect_current_theme()

    def _detect_current_theme(self) -> None:
        """Detect if we're using a dark or light theme."""
        app = Qw.QApplication.instance()
        if app:
            palette = app.palette()
            bg_color = palette.color(QtGui.QPalette.ColorRole.Window)

            # Simple heuristic: if background is closer to black, it's dark theme
            brightness = (bg_color.red() + bg_color.green() + bg_color.blue()) / 3
            theme_type = "dark" if brightness < 128 else "light"

            self.current_theme_colors = self.theme_color_schemes[theme_type].copy()
            nfo(f"Detected {theme_type} theme, adjusting icon colors accordingly")
        else:
            # Fallback to dark theme if no app instance
            self.current_theme_colors = self.theme_color_schemes["dark"].copy()
            nfo("No QApplication instance found, defaulting to dark theme colors")

    def set_theme_colors(self, primary: QColor, secondary: QColor, accent: QColor) -> None:
        """Manually set theme colors for icon generation.

        Args:
            primary: Primary color (main text/icon color)
            secondary: Secondary color (less prominent elements)
            accent: Accent color (highlights, active states)

        """
        self.current_theme_colors = {
            "primary": primary,
            "secondary": secondary,
            "accent": accent,
            "disabled": QColor(primary.red() // 3, primary.green() // 3, primary.blue() // 3),
        }

        # Clear cache to force regeneration with new colors
        self.icon_cache.clear()
        nfo("Icon colors updated, cache cleared")

    def get_icon(self, icon_name: str, color_type: str = "primary", size: QSize = QSize(24, 24)) -> QIcon:
        """Get a theme-aware icon.

        Args:
            icon_name: Name of the SVG icon file (without .svg extension)
            color_type: Type of color to use ("primary", "secondary", "accent", "disabled")
            size: Desired icon size

        Returns:
            QIcon object ready for use in widgets

        """
        cache_key = f"{icon_name}_{color_type}_{size.width()}x{size.height()}"

        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]

        icon_path = self.icons_directory / f"{icon_name}.svg"

        if not icon_path.exists():
            nfo(f"Icon not found: {icon_path}")
            return self._create_fallback_icon(icon_name, size)

        try:
            # Now that Font Awesome icons use currentColor, we can colorize them
            colored_pixmap = self._colorize_svg(str(icon_path), color_type, size)
            icon = QIcon(colored_pixmap)

            self.icon_cache[cache_key] = icon
            return icon

        except Exception as e:
            nfo(f"Error loading icon {icon_name}: {e}")
            return self._create_fallback_icon(icon_name, size)

    def _colorize_svg(self, svg_path: str, color_type: str, size: QSize) -> QPixmap:
        """Colorize an SVG file with theme-appropriate colors.

        Args:
            svg_path: Path to the SVG file
            color_type: Type of color to apply
            size: Size for the resulting pixmap

        Returns:
            Colored QPixmap

        """
        # Get the color first
        color = self.current_theme_colors.get(
            color_type, self.current_theme_colors.get("primary", QColor(128, 128, 128))
        )

        # Read the SVG file and replace currentColor with our theme color
        try:
            with open(svg_path, encoding="utf-8") as f:
                svg_content = f.read()

            # Replace currentColor with our theme color
            color_hex = color.name()  # Get hex color like #ffffff
            svg_content = svg_content.replace("currentColor", color_hex)

            # Create renderer from modified content
            renderer = QSvgRenderer(svg_content.encode("utf-8"))

            # Create pixmap with the desired size
            pixmap = QPixmap(size)
            pixmap.fill(QtCore.Qt.GlobalColor.transparent)

            # Paint the SVG onto the pixmap
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Render the SVG
            renderer.render(painter)

            painter.end()
            return pixmap

        except Exception as e:
            nfo(f"Error processing SVG {svg_path}: {e}")
            # Fallback to simple rendering without colorization
            return self._render_svg_fallback(svg_path, size)

    def _render_svg_fallback(self, svg_path: str, size: QSize) -> QPixmap:
        """Simple SVG rendering without colorization as fallback.

        Args:
            svg_path: Path to the SVG file
            size: Size for the resulting pixmap

        Returns:
            Rendered QPixmap

        """
        renderer = QSvgRenderer(svg_path)

        # Create pixmap with the desired size
        pixmap = QPixmap(size)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)

        # Paint the SVG onto the pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Render the SVG
        renderer.render(painter)

        painter.end()
        return pixmap

    def _create_fallback_icon(self, icon_name: str, size: QSize) -> QIcon:
        """Create a simple fallback icon when SVG is not found.

        Args:
            icon_name: Name of the requested icon (for text fallback)
            size: Desired icon size

        Returns:
            Simple QIcon with text or basic shape

        """
        pixmap = QPixmap(size)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw a simple colored rectangle as fallback
        color = self.current_theme_colors.get("secondary", QColor(128, 128, 128))
        painter.fillRect(pixmap.rect().adjusted(2, 2, -2, -2), color)

        # Add text if space allows
        if size.width() >= 16:
            painter.setPen(self.current_theme_colors.get("primary", QColor(255, 255, 255)))
            painter.drawText(
                pixmap.rect(),
                QtCore.Qt.AlignmentFlag.AlignCenter,
                icon_name[:2].upper(),
            )

        painter.end()
        return QIcon(pixmap)

    def add_icon_to_button(
        self,
        button: Qw.QPushButton,
        icon_name: str,
        color_type: str = "primary",
        icon_size: QSize = QSize(16, 16),
    ) -> None:
        """Add an icon to a button with theme-aware coloring.

        Args:
            button: QPushButton to add icon to
            icon_name: Name of the SVG icon
            color_type: Color type for the icon
            icon_size: Size of the icon

        """
        icon = self.get_icon(icon_name, color_type, icon_size)
        button.setIcon(icon)
        button.setIconSize(icon_size)

    def create_icon_directory(self) -> None:
        """Create the icons directory if it doesn't exist."""
        self.icons_directory.mkdir(parents=True, exist_ok=True)
        nfo(f"Icons directory ensured at: {self.icons_directory}")

    def list_available_icons(self) -> list[str]:
        """List all available SVG icons.

        Returns:
            List of icon names (without .svg extension)

        """
        if not self.icons_directory.exists():
            return []

        return [f.stem for f in self.icons_directory.glob("*.svg")]


def get_icon_manager() -> IconManager:
    """Get the global icon manager instance."""
    if not hasattr(get_icon_manager, "_icon_manager"):
        get_icon_manager._icon_manager = IconManager()
    return get_icon_manager._icon_manager


def get_themed_icon(icon_name: str, color_type: str = "primary", size: QSize | None = None) -> QIcon:
    if size is None:
        size = QSize(24, 24)
    """Convenience function to get a themed icon.

    Args:
        icon_name: Name of the SVG icon
        color_type: Color type ("primary", "secondary", "accent", "disabled")
        size: Icon size

    Returns:
        Theme-aware QIcon

    """
    return get_icon_manager().get_icon(icon_name, color_type, size)
