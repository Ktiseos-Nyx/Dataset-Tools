# dataset_tools/ui/managers.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""UI Manager classes for Dataset Tools.

This module contains manager classes that handle different aspects of the UI:
- ThemeManager: Theme application and management
- MenuManager: Menu creation and handling
- LayoutManager: Layout setup and state persistence
- MetadataDisplayManager: Metadata formatting and display
"""

from typing import Any

from PyQt6 import QtCore, QtGui
from PyQt6 import QtWidgets as Qw
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QTextOption
from PyQt6.QtWidgets import QApplication

from ..correct_types import EmptyField
from ..display_formatter import format_metadata_for_display
from ..logger import info_monitor as nfo
from .components import EnhancedImageLabel, EnhancedLeftPanelWidget

# Import icon manager
try:
    from .icon_manager import get_icon_manager

    ICON_MANAGER_AVAILABLE = True
except ImportError:
    ICON_MANAGER_AVAILABLE = False

# Import theme functionality with fallback
try:
    from qt_material import apply_stylesheet, list_themes

    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False

    def list_themes():
        return ["default_light.xml", "default_dark.xml"]

    def apply_stylesheet(app, theme, invert_secondary=False):
        pass


# ============================================================================
# THEME MANAGER
# ============================================================================


class ThemeManager:
    """Manages application themes and visual styling.

    Handles theme loading, application, and persistence using qt-material
    when available, with graceful fallback when not.
    """

    def __init__(self, main_window: Qw.QMainWindow, settings: QSettings):
        self.main_window = main_window
        self.settings = settings
        self.theme_actions: dict[str, QtGui.QAction] = {}
        self.current_theme = "dark_teal.xml"

    def get_available_themes(self) -> list[str]:
        """Get list of available themes."""
        if QT_MATERIAL_AVAILABLE:
            return list_themes()
        return ["default_light.xml", "default_dark.xml"]

    def apply_theme(self, theme_name: str, initial_load: bool = False) -> bool:
        """Apply a theme to the application.

        Args:
            theme_name: Name of the theme to apply
            initial_load: Whether this is the initial theme load

        Returns:
            True if theme was applied successfully, False otherwise

        """
        if not QT_MATERIAL_AVAILABLE:
            nfo("Cannot apply theme: qt-material not available")
            return False

        app = QApplication.instance()
        if not app:
            nfo("Cannot apply theme: no QApplication instance")
            return False

        # Update theme action states
        for theme_key, action in self.theme_actions.items():
            action.setChecked(theme_key == theme_name)

        try:
            # Apply the theme
            invert_secondary = theme_name.startswith("dark_")
            apply_stylesheet(app, theme=theme_name, invert_secondary=invert_secondary)

            self.current_theme = theme_name

            # Save theme preference (but not on initial load)
            if not initial_load:
                self.settings.setValue("theme", theme_name)

            action_text = "Initial theme loaded" if initial_load else "Theme applied and saved"
            nfo("%s: %s", action_text, theme_name)

            # Update icon manager colors when theme changes
            if ICON_MANAGER_AVAILABLE and not initial_load:
                self._update_icon_colors_for_theme(theme_name)

            return True

        except Exception as e:
            nfo("Error applying theme %s: %s", theme_name, e, exc_info=True)
            return False

    def apply_saved_theme(self) -> None:
        """Apply the saved theme from settings."""
        saved_theme = self.settings.value("theme", "dark_teal.xml")

        if QT_MATERIAL_AVAILABLE:
            available_themes = self.get_available_themes()

            if saved_theme in available_themes:
                self.apply_theme(saved_theme, initial_load=True)
            elif "dark_teal.xml" in available_themes:
                self.apply_theme("dark_teal.xml", initial_load=True)
            elif available_themes:
                self.apply_theme(available_themes[0], initial_load=True)

    def create_theme_actions(self, themes_menu: Qw.QMenu) -> None:
        """Create theme selection actions for a menu.

        Args:
            themes_menu: Menu to add theme actions to

        """
        if not QT_MATERIAL_AVAILABLE:
            no_themes_action = QtGui.QAction("qt-material not found", self.main_window)
            no_themes_action.setEnabled(False)
            themes_menu.addAction(no_themes_action)
            return

        # Create action group for exclusive selection
        theme_group = QtGui.QActionGroup(self.main_window)
        theme_group.setExclusive(True)

        for theme_xml in self.get_available_themes():
            # Convert theme name to display format
            display_name = theme_xml.replace(".xml", "").replace("_", " ").title()

            action = QtGui.QAction(display_name, self.main_window)
            action.setCheckable(True)
            action.setData(theme_xml)
            action.triggered.connect(self._on_theme_action_triggered)

            themes_menu.addAction(action)
            theme_group.addAction(action)
            self.theme_actions[theme_xml] = action

    def _update_icon_colors_for_theme(self, theme_name: str) -> None:
        """Update icon manager colors based on the current theme.

        Args:
            theme_name: Name of the applied theme

        """
        try:
            icon_manager = get_icon_manager()

            # Determine colors based on theme name
            if any(dark_indicator in theme_name.lower() for dark_indicator in ["dark", "black"]):
                # Dark theme colors
                from PyQt6.QtGui import QColor

                icon_manager.set_theme_colors(
                    primary=QColor(255, 255, 255),  # White
                    secondary=QColor(180, 180, 180),  # Light gray
                    accent=QColor(0, 188, 212),  # Cyan
                )
            else:
                # Light theme colors
                from PyQt6.QtGui import QColor

                icon_manager.set_theme_colors(
                    primary=QColor(33, 33, 33),  # Dark gray
                    secondary=QColor(117, 117, 117),  # Medium gray
                    accent=QColor(0, 150, 136),  # Teal
                )

            nfo(f"Updated icon colors for theme: {theme_name}")

        except Exception as e:
            nfo(f"Error updating icon colors: {e}")

    def _on_theme_action_triggered(self) -> None:
        """Handle theme action being triggered."""
        action = self.main_window.sender()
        if action and isinstance(action, QtGui.QAction):
            theme_xml = action.data()
            if theme_xml:
                self.apply_theme(theme_xml)

    def restore_window_geometry(self) -> None:
        """Restore window geometry from settings."""
        remember_geometry = self.settings.value("rememberGeometry", True, type=bool)

        if remember_geometry:
            saved_geometry = self.settings.value("geometry")
            if saved_geometry:
                self.main_window.restoreGeometry(saved_geometry)
                return

        # Apply size preset if not remembering geometry
        self._apply_size_preset()

    def _apply_size_preset(self) -> None:
        """Apply a size preset from settings."""
        size_presets = {
            "Default (1024x768)": (1024, 768),
            "Small (800x600)": (800, 600),
            "Medium (1280x900)": (1280, 900),
            "Large (1600x900)": (1600, 900),
        }

        preset_name = self.settings.value("windowSizePreset", "Default (1024x768)")
        width, height = size_presets.get(preset_name, (1024, 768))

        if hasattr(self.main_window, "resize_window"):
            self.main_window.resize_window(width, height)
        else:
            self.main_window.resize(width, height)


# ============================================================================
# MENU MANAGER
# ============================================================================


class MenuManager:
    """Manages application menus and menu actions.

    Handles creation and configuration of the main menu bar,
    including File, View, and Help menus with their respective actions.
    """

    def __init__(self, main_window: Qw.QMainWindow):
        self.main_window = main_window
        self.theme_manager: ThemeManager | None = None

    def set_theme_manager(self, theme_manager: ThemeManager) -> None:
        """Set the theme manager for theme-related menu actions."""
        self.theme_manager = theme_manager

    def setup_menus(self) -> None:
        """Setup all application menus."""
        menu_bar = self.main_window.menuBar()

        self._setup_file_menu(menu_bar)
        self._setup_view_menu(menu_bar)
        self._setup_help_menu(menu_bar)

    def _setup_file_menu(self, menu_bar: Qw.QMenuBar) -> None:
        """Setup the File menu."""
        file_menu = menu_bar.addMenu("&File")

        # Change Folder action
        change_folder_action = QtGui.QAction("Change &Folder...", self.main_window)
        change_folder_action.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        change_folder_action.setToolTip("Select a different folder to browse")

        if hasattr(self.main_window, "open_folder"):
            change_folder_action.triggered.connect(self.main_window.open_folder)

        file_menu.addAction(change_folder_action)
        file_menu.addSeparator()

        # Close action
        close_action = QtGui.QAction("&Close Window", self.main_window)
        close_action.setShortcut(QtGui.QKeySequence.StandardKey.Close)
        close_action.setToolTip("Close the application")
        close_action.triggered.connect(self.main_window.close)

        file_menu.addAction(close_action)

    def _setup_view_menu(self, menu_bar: Qw.QMenuBar) -> None:
        """Setup the View menu."""
        view_menu = menu_bar.addMenu("&View")

        # Themes submenu
        self.themes_menu = Qw.QMenu("&Themes", self.main_window)
        view_menu.addMenu(self.themes_menu)

        # Use enhanced theme manager if available, fallback to standard
        if hasattr(self.main_window, "enhanced_theme_manager"):
            self.main_window.enhanced_theme_manager.create_theme_menus(self.themes_menu)
        elif self.theme_manager:
            self.theme_manager.create_theme_actions(self.themes_menu)

    def _setup_help_menu(self, menu_bar: Qw.QMenuBar) -> None:
        """Setup the Help menu."""
        help_menu = menu_bar.addMenu("&Help")

        # About action
        about_action = QtGui.QAction("&About Dataset Viewer...", self.main_window)
        about_action.setToolTip("Show information about this application")

        if hasattr(self.main_window, "show_about_dialog"):
            about_action.triggered.connect(self.main_window.show_about_dialog)

        help_menu.addAction(about_action)

        # Add theme report action
        if hasattr(self.main_window, "show_theme_report"):
            theme_report_action = QtGui.QAction("&Theme Report...", self.main_window)
            theme_report_action.setToolTip("Show available themes and system report")
            theme_report_action.triggered.connect(self.main_window.show_theme_report)
            help_menu.addAction(theme_report_action)


# ============================================================================
# LAYOUT MANAGER
# ============================================================================


class LayoutManager:
    """Manages UI layout creation and state persistence.

    Handles the creation of the main UI layout including splitters,
    panels, and action buttons. Also manages saving and restoring
    layout state between sessions.
    """

    DEFAULT_WINDOW_WIDTH = 1024
    MAIN_SPLITTER_RATIO = (1, 3)  # left : right
    METADATA_IMAGE_RATIO = (1, 2)  # metadata : image

    def __init__(self, main_window: Qw.QMainWindow, settings: QSettings):
        self.main_window = main_window
        self.settings = settings

    def setup_layout(self) -> None:
        """Setup the complete UI layout."""
        self._setup_main_container()
        self._setup_main_splitter()
        self._setup_left_panel()
        self._setup_middle_right_area()
        self._setup_bottom_bar()
        self._restore_splitter_positions()

    def _setup_main_container(self) -> None:
        """Setup the main container widget."""
        main_widget = Qw.QWidget()
        self.main_window.setCentralWidget(main_widget)

        overall_layout = Qw.QVBoxLayout(main_widget)
        overall_layout.setContentsMargins(5, 5, 5, 5)
        overall_layout.setSpacing(5)

        # Store reference for later use
        self.main_window._overall_layout = overall_layout

    def _setup_main_splitter(self) -> None:
        """Setup the main horizontal splitter."""
        self.main_window.main_splitter = Qw.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.main_window._overall_layout.addWidget(self.main_window.main_splitter, 1)

    def _setup_left_panel(self) -> None:
        """Setup the left file browser panel."""
        self.main_window.left_panel = EnhancedLeftPanelWidget()
        self.main_window.main_splitter.addWidget(self.main_window.left_panel)

    def _setup_middle_right_area(self) -> None:
        """Setup the middle-right area with metadata and image panels."""
        # Container for metadata and image
        middle_right_widget = Qw.QWidget()
        middle_right_layout = Qw.QHBoxLayout(middle_right_widget)
        middle_right_layout.setContentsMargins(0, 0, 0, 0)
        middle_right_layout.setSpacing(5)

        # Metadata-Image splitter
        self.main_window.metadata_image_splitter = Qw.QSplitter(QtCore.Qt.Orientation.Horizontal)
        middle_right_layout.addWidget(self.main_window.metadata_image_splitter)

        # Setup panels
        self._setup_metadata_panel()
        self._setup_image_panel()

        # Add to main splitter
        self.main_window.main_splitter.addWidget(middle_right_widget)

    def _setup_metadata_panel(self) -> None:
        """Setup the metadata display panel."""
        metadata_widget = Qw.QWidget()
        metadata_layout = Qw.QVBoxLayout(metadata_widget)
        metadata_layout.setContentsMargins(10, 20, 10, 20)
        metadata_layout.setSpacing(15)
        metadata_layout.addStretch(1)

        # Create text boxes for metadata display
        self._create_metadata_text_boxes(metadata_layout)

        metadata_layout.addStretch(1)
        self.main_window.metadata_image_splitter.addWidget(metadata_widget)

    def _create_metadata_text_boxes(self, layout: Qw.QVBoxLayout) -> None:
        """Create the metadata text display boxes."""
        text_box_configs = [
            ("positive_prompt", "Positive Prompt"),
            ("negative_prompt", "Negative Prompt"),
            ("generation_data", "Generation Details & Metadata"),
        ]

        for box_name, label_text in text_box_configs:
            # Create label
            label = Qw.QLabel(label_text)
            label_attr = f"{box_name}_label"
            setattr(self.main_window, label_attr, label)
            layout.addWidget(label)

            # Create text box
            text_box = Qw.QTextEdit()
            text_box.setReadOnly(True)
            text_box.setSizePolicy(Qw.QSizePolicy.Policy.Expanding, Qw.QSizePolicy.Policy.Preferred)

            # Enable word wrap for proper text display
            text_box.setWordWrapMode(QTextOption.WrapMode.WordWrap)
            text_box.setLineWrapMode(Qw.QTextEdit.LineWrapMode.WidgetWidth)

            # Font will be inherited from global font settings
            # No explicit font setting - respects user's font choice

            box_attr = f"{box_name}_box"
            setattr(self.main_window, box_attr, text_box)
            layout.addWidget(text_box)

    def _setup_image_panel(self) -> None:
        """Setup the image preview panel."""
        self.main_window.image_preview = EnhancedImageLabel()
        self.main_window.metadata_image_splitter.addWidget(self.main_window.image_preview)

    def _setup_bottom_bar(self) -> None:
        """Setup the bottom action button bar."""
        bottom_bar = Qw.QWidget()
        bottom_layout = Qw.QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(10, 5, 10, 5)
        bottom_layout.addStretch(1)

        # Action buttons
        action_layout = self._create_action_buttons()
        bottom_layout.addLayout(action_layout)
        bottom_layout.addStretch(1)

        self.main_window._overall_layout.addWidget(bottom_bar, 0)

    def _create_action_buttons(self) -> Qw.QHBoxLayout:
        """Create the action button layout."""
        action_layout = Qw.QHBoxLayout()
        action_layout.setSpacing(10)

        # Button configurations
        button_configs = [
            (
                "copy_metadata_button",
                "Copy All Metadata",
                "copy_metadata_to_clipboard",
                "<b>Copy All Metadata</b><br/>Copy all metadata from the current file to "
                "clipboard<br/><i>Shortcut: Ctrl+C</i>",
            ),
            (
                "settings_button",
                "Settings",
                "open_settings_dialog",
                "<b>Settings</b><br/>Open application settings to configure themes, window size, "
                "and other preferences<br/><i>Shortcut: Ctrl+S</i>",
            ),
            (
                "exit_button",
                "Exit Application",
                "close",
                "<b>Exit Application</b><br/>Close the Dataset Tools application<br/><i>Shortcut: Ctrl+Q</i>",
            ),
        ]

        for attr_name, text, slot_name, tooltip in button_configs:
            button = Qw.QPushButton(text)
            button.setToolTip(tooltip)

            # Connect to method if it exists
            if hasattr(self.main_window, slot_name):
                slot = getattr(self.main_window, slot_name)
                button.clicked.connect(slot)

            setattr(self.main_window, attr_name, button)
            action_layout.addWidget(button)

        return action_layout

    def _restore_splitter_positions(self) -> None:
        """Restore splitter positions from saved settings."""
        try:
            window_width = self._get_window_width()

            # Main splitter
            main_default = self._calculate_main_splitter_sizes(window_width)
            main_saved = self.settings.value("mainSplitterSizes", main_default, type=list)
            main_sizes = [int(s) for s in main_saved]
            self.main_window.main_splitter.setSizes(main_sizes)

            # Metadata-image splitter
            meta_default = self._calculate_metadata_image_sizes(window_width)
            meta_saved = self.settings.value("metaImageSplitterSizes", meta_default, type=list)
            meta_sizes = [int(s) for s in meta_saved]
            self.main_window.metadata_image_splitter.setSizes(meta_sizes)

        except Exception as e:
            nfo("Error restoring splitter positions: %s", e)

    def _get_window_width(self) -> int:
        """Get current window width safely."""
        try:
            if self.main_window.isVisible():
                return self.main_window.width()
        except RuntimeError:
            pass
        return self.DEFAULT_WINDOW_WIDTH

    def _calculate_main_splitter_sizes(self, window_width: int) -> list[int]:
        """Calculate default main splitter sizes."""
        total_ratio = sum(self.MAIN_SPLITTER_RATIO)
        left_width = window_width * self.MAIN_SPLITTER_RATIO[0] // total_ratio
        right_width = window_width - left_width
        return [left_width, right_width]

    def _calculate_metadata_image_sizes(self, window_width: int) -> list[int]:
        """Calculate default metadata-image splitter sizes."""
        total_ratio = sum(self.METADATA_IMAGE_RATIO)
        metadata_width = window_width * self.METADATA_IMAGE_RATIO[0] // total_ratio
        image_width = window_width - metadata_width
        return [metadata_width, image_width]

    def save_layout_state(self) -> None:
        """Save current layout state to settings."""
        try:
            if hasattr(self.main_window, "main_splitter"):
                main_sizes = self.main_window.main_splitter.sizes()
                self.settings.setValue("mainSplitterSizes", main_sizes)

            if hasattr(self.main_window, "metadata_image_splitter"):
                meta_sizes = self.main_window.metadata_image_splitter.sizes()
                self.settings.setValue("metaImageSplitterSizes", meta_sizes)

            nfo("Layout state saved successfully")
        except Exception as e:
            nfo("Error saving layout state: %s", e)


# ============================================================================
# METADATA DISPLAY MANAGER
# ============================================================================


class MetadataDisplayManager:
    """Manages metadata formatting and display in the UI.

    This class handles the formatting of metadata for display in the various
    text boxes and provides methods for copying metadata to clipboard.
    """

    def __init__(self, main_window: Qw.QMainWindow):
        self.main_window = main_window

    def display_metadata(self, metadata_dict: dict[str, Any] | None) -> None:
        """Display metadata in the UI text boxes.

        Args:
            metadata_dict: Dictionary containing metadata to display

        """
        # Format the metadata for display
        formatted_data = format_metadata_for_display(metadata_dict)

        # Update the text boxes
        self._update_text_box("positive_prompt_box", formatted_data["positive"])
        self._update_text_box("negative_prompt_box", formatted_data["negative"])
        self._update_text_box("generation_data_box", formatted_data["details"])

        # Set placeholders for empty fields
        self._set_placeholders()

    def _update_text_box(self, box_attr_name: str, content: str) -> None:
        """Update a specific text box with content."""
        if hasattr(self.main_window, box_attr_name):
            text_box = getattr(self.main_window, box_attr_name)
            if isinstance(text_box, Qw.QTextEdit):
                text_box.setText(content)

    def _set_placeholders(self) -> None:
        """Set placeholder text for empty text boxes."""
        placeholder_configs = [
            ("positive_prompt_box", EmptyField.PLACEHOLDER_POSITIVE.value),
            ("negative_prompt_box", EmptyField.PLACEHOLDER_NEGATIVE.value),
            ("generation_data_box", EmptyField.PLACEHOLDER_DETAILS.value),
        ]

        for box_attr, placeholder_text in placeholder_configs:
            if hasattr(self.main_window, box_attr):
                text_box = getattr(self.main_window, box_attr)
                if isinstance(text_box, Qw.QTextEdit):
                    if not text_box.toPlainText().strip():
                        text_box.setPlaceholderText(placeholder_text)

    def clear_all_displays(self) -> None:
        """Clear all metadata display boxes."""
        text_boxes = [
            "positive_prompt_box",
            "negative_prompt_box",
            "generation_data_box",
        ]

        for box_attr in text_boxes:
            if hasattr(self.main_window, box_attr):
                text_box = getattr(self.main_window, box_attr)
                if isinstance(text_box, Qw.QTextEdit):
                    text_box.clear()

        self._set_placeholders()

    def get_all_display_text(self) -> str:
        """Get all displayed metadata as formatted text for clipboard.

        Returns:
            Formatted string containing all displayed metadata

        """
        text_parts = []

        # Get text from each box with its label
        box_configs = [
            ("positive_prompt_box", "positive_prompt_label", "Positive Prompt"),
            ("negative_prompt_box", "negative_prompt_label", "Negative Prompt"),
            (
                "generation_data_box",
                "generation_data_label",
                "Generation Details & Metadata",
            ),
        ]

        for box_attr, label_attr, default_label in box_configs:
            content = self._get_box_content_with_label(box_attr, label_attr, default_label)
            if content:
                text_parts.append(content)

        # Join with separator
        separator = "\n\n" + "═" * 20 + "\n\n"
        return separator.join(text_parts)

    def _get_box_content_with_label(self, box_attr: str, label_attr: str, default_label: str) -> str | None:
        """Get formatted content from a text box with its label."""
        if not hasattr(self.main_window, box_attr):
            return None

        text_box = getattr(self.main_window, box_attr)
        if not isinstance(text_box, Qw.QTextEdit):
            return None

        content = text_box.toPlainText().strip()
        if not content:
            return None

        # Skip error/info content
        if content.startswith("Info/Error:"):
            return None

        # Get label text
        label_text = default_label
        if hasattr(self.main_window, label_attr):
            label_widget = getattr(self.main_window, label_attr)
            if isinstance(label_widget, Qw.QLabel):
                label_text = label_widget.text()

        return f"{label_text}:\n{content}"

    def format_metadata_section(self, metadata_dict: dict[str, Any], section_enum: Any) -> str:
        """Format a specific metadata section for display.

        Args:
            metadata_dict: Complete metadata dictionary
            section_enum: Enum member representing the section to format

        Returns:
            Formatted string for the section

        """
        if not hasattr(section_enum, "value"):
            return ""

        section_data = metadata_dict.get(section_enum.value)
        if not section_data:
            return ""

        return self._format_section_data(section_data)

    def _format_section_data(self, data: Any) -> str:
        """Format section data into a readable string."""
        if isinstance(data, dict):
            parts = []
            for key, value in sorted(data.items()):
                if value is not None:
                    if isinstance(value, dict):
                        nested_parts = [f"  {k}: {v}" for k, v in sorted(value.items()) if v is not None]
                        if nested_parts:
                            parts.append(f"{key}:")
                            parts.extend(nested_parts)
                    else:
                        parts.append(f"{key}: {value}")
            return "\n".join(parts)
        if isinstance(data, list):
            return "\n".join(str(item) for item in data)
        return str(data)

    def update_detected_tool_display(self, tool_name: str) -> None:
        """Update the display to show detected tool information."""
        if hasattr(self.main_window, "generation_data_box"):
            text_box = self.main_window.generation_data_box
            if isinstance(text_box, Qw.QTextEdit):
                current_text = text_box.toPlainText()
                if not current_text.startswith("Detected Tool:"):
                    new_text = f"Detected Tool: {tool_name}\n\n{current_text}"
                    text_box.setText(new_text)


# ============================================================================
# COMBINED MANAGER COORDINATOR
# ============================================================================


class UIManagerCoordinator:
    """Coordinates all UI managers for the main window.

    This class provides a single point of access to all UI managers
    and handles their initialization and coordination.
    """

    def __init__(self, main_window: Qw.QMainWindow, settings: QSettings):
        self.main_window = main_window
        self.settings = settings

        # Initialize managers
        self.theme_manager = ThemeManager(main_window, settings)
        self.menu_manager = MenuManager(main_window)
        self.layout_manager = LayoutManager(main_window, settings)
        self.metadata_display = MetadataDisplayManager(main_window)

        # Connect managers
        self.menu_manager.set_theme_manager(self.theme_manager)

    def initialize_ui(self) -> None:
        """Initialize the complete UI system."""
        # Setup in proper order
        self.menu_manager.setup_menus()
        self.theme_manager.apply_saved_theme()
        self.layout_manager.setup_layout()
        self.theme_manager.restore_window_geometry()

    def save_ui_state(self) -> None:
        """Save the current UI state."""
        self.layout_manager.save_layout_state()

        # Save geometry if enabled
        if self.settings.value("rememberGeometry", True, type=bool):
            self.settings.setValue("geometry", self.main_window.saveGeometry())
        else:
            self.settings.remove("geometry")

    def get_manager(self, manager_type: str):
        """Get a specific manager by type.

        Args:
            manager_type: Type of manager ('theme', 'menu', 'layout', 'metadata')

        Returns:
            The requested manager instance

        """
        managers = {
            "theme": self.theme_manager,
            "menu": self.menu_manager,
            "layout": self.layout_manager,
            "metadata": self.metadata_display,
        }
        return managers.get(manager_type)
