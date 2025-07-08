# dataset_tools/ui/dialogs.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Dialog classes for Dataset Tools.

This module contains all dialog windows used in the application,
including settings configuration and about information dialogs.
"""

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ..logger import info_monitor as nfo

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
# SETTINGS DIALOG
# ============================================================================


class SettingsDialog(QDialog):
    """Application settings configuration dialog.

    Allows users to configure application preferences including:
    - Display theme selection
    - Window size preferences
    - Other application settings
    """

    def __init__(self, parent: QWidget | None = None, current_theme_xml: str = ""):
        super().__init__(parent)

        # Store references
        self.parent_window = parent
        self.current_theme_on_open = current_theme_xml
        self.settings = QSettings("EarthAndDuskMedia", "DatasetViewer")

        # Setup dialog
        self._setup_dialog()
        self._create_theme_section()
        self._create_window_size_section()
        self._create_button_box()
        self._load_current_settings()

    def _setup_dialog(self) -> None:
        """Setup basic dialog properties."""
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(400)
        self.setModal(True)

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(20)

    def _create_theme_section(self) -> None:
        """Create the theme selection section."""
        # Theme label
        theme_label = QLabel("<b>Display Theme:</b>")
        self.layout.addWidget(theme_label)

        # Theme combo box
        self.theme_combo = QComboBox()
        self._populate_theme_combo()
        self.layout.addWidget(self.theme_combo)

    def _populate_theme_combo(self) -> None:
        """Populate the theme combo box with available themes."""
        if QT_MATERIAL_AVAILABLE:
            self.available_themes_xml = list_themes()

            for theme_xml_name in self.available_themes_xml:
                display_name = self._format_theme_display_name(theme_xml_name)
                self.theme_combo.addItem(display_name, theme_xml_name)
        else:
            self.theme_combo.addItem("Default (qt-material not found)")
            self.theme_combo.setEnabled(False)
            self.available_themes_xml = []

    def _format_theme_display_name(self, theme_xml_name: str) -> str:
        """Convert theme XML name to display format."""
        return theme_xml_name.replace(".xml", "").replace("_", " ").title()

    def _create_window_size_section(self) -> None:
        """Create the window size configuration section."""
        # Add spacing
        self.layout.addSpacing(15)

        # Size label
        size_label = QLabel("<b>Window Size:</b>")
        self.layout.addWidget(size_label)

        # Size combo box
        self.size_combo = QComboBox()
        self._populate_size_combo()
        self.layout.addWidget(self.size_combo)

    def _populate_size_combo(self) -> None:
        """Populate the size combo box with available presets."""
        self.size_presets: dict[str, tuple[int, int] | None] = {
            "Remember Last Size": None,
            "Default (1024x768)": (1024, 768),
            "Small (800x600)": (800, 600),
            "Medium (1280x900)": (1280, 900),
            "Large (1600x900)": (1600, 900),
        }

        for display_name in self.size_presets:
            self.size_combo.addItem(display_name)

    def _create_button_box(self) -> None:
        """Create the dialog button box."""
        # Add stretch before buttons
        self.layout.addStretch(1)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )

        # Connect button signals
        self.button_box.accepted.connect(self.accept_settings)
        self.button_box.rejected.connect(self.reject_settings)
        self.button_box.button(
            QDialogButtonBox.StandardButton.Apply
        ).clicked.connect(self.apply_all_settings)

        self.layout.addWidget(self.button_box)

    def _load_current_settings(self) -> None:
        """Load and display current settings."""
        self._load_theme_setting()
        self._load_window_size_setting()

    def _load_theme_setting(self) -> None:
        """Load and set current theme setting."""
        if not QT_MATERIAL_AVAILABLE or not self.current_theme_on_open:
            return

        # Find and select current theme
        display_name = self._format_theme_display_name(self.current_theme_on_open)
        index = self.theme_combo.findText(display_name)

        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        elif self.available_themes_xml:
            self.theme_combo.setCurrentIndex(0)

    def _load_window_size_setting(self) -> None:
        """Load and set current window size setting."""
        remember_geometry = self.settings.value("rememberGeometry", True, type=bool)

        if remember_geometry:
            self.size_combo.setCurrentText("Remember Last Size")
        else:
            saved_preset = self.settings.value("windowSizePreset", "Default (1024x768)")
            if self.size_combo.findText(saved_preset) != -1:
                self.size_combo.setCurrentText(saved_preset)
            else:
                self.size_combo.setCurrentText("Default (1024x768)")

    # ========================================================================
    # SETTINGS APPLICATION METHODS
    # ========================================================================

    def apply_theme_settings(self) -> None:
        """Apply the selected theme settings."""
        if not QT_MATERIAL_AVAILABLE:
            nfo("Cannot apply theme: qt-material not available")
            return

        selected_theme_xml = self.theme_combo.currentData()
        nfo(f"Attempting to apply theme: {selected_theme_xml}")
        if selected_theme_xml and self.parent_window and hasattr(self.parent_window, "apply_theme"):
            result = self.parent_window.apply_theme(selected_theme_xml, initial_load=False)
            nfo(f"Theme application result: {result}")
        else:
            nfo(
                f"Cannot apply theme - conditions not met. Theme: {selected_theme_xml}, "
                f"Parent: {self.parent_window}, Has apply_theme: "
                f"{hasattr(self.parent_window, 'apply_theme') if self.parent_window else False}"
            )

    def apply_window_settings(self) -> None:
        """Apply the selected window size settings."""
        selected_size_text = self.size_combo.currentText()
        size_tuple = self.size_presets.get(selected_size_text)

        if selected_size_text == "Remember Last Size":
            self._apply_remember_geometry_setting()
        elif size_tuple and self._can_resize_parent():
            self._apply_size_preset_setting(selected_size_text, size_tuple)

    def _apply_remember_geometry_setting(self) -> None:
        """Apply the 'remember geometry' setting."""
        self.settings.setValue("rememberGeometry", True)

        # Save current geometry if parent supports it
        if self.parent_window and hasattr(self.parent_window, "saveGeometry"):
            geometry = self.parent_window.saveGeometry()
            self.settings.setValue("geometry", geometry)

    def _can_resize_parent(self) -> bool:
        """Check if parent window can be resized."""
        return self.parent_window and hasattr(self.parent_window, "resize_window")

    def _apply_size_preset_setting(self, preset_name: str, size_tuple: tuple[int, int]) -> None:
        """Apply a specific size preset."""
        self.settings.setValue("rememberGeometry", False)
        self.settings.setValue("windowSizePreset", preset_name)

        # Resize parent window
        if self._can_resize_parent():
            self.parent_window.resize_window(size_tuple[0], size_tuple[1])

        # Remove saved geometry
        self.settings.remove("geometry")

    def apply_all_settings(self) -> None:
        """Apply all settings without closing dialog."""
        self.apply_theme_settings()
        self.apply_window_settings()
        nfo("Settings applied successfully")

    # ========================================================================
    # DIALOG RESULT METHODS
    # ========================================================================

    def accept_settings(self) -> None:
        """Accept and apply all settings, then close dialog."""
        self.apply_all_settings()
        self.current_theme_on_open = self.theme_combo.currentData()
        self.accept()
        nfo("Settings accepted and dialog closed")

    def reject_settings(self) -> None:
        """Reject settings and revert theme if changed."""
        if self._should_revert_theme():
            self._revert_theme()

        self.reject()
        nfo("Settings rejected, dialog closed")

    def _should_revert_theme(self) -> bool:
        """Check if theme should be reverted on cancel."""
        return (
            QT_MATERIAL_AVAILABLE
            and self.parent_window
            and hasattr(self.parent_window, "apply_theme")
            and self.current_theme_on_open
            and self._theme_has_changed()
        )

    def _theme_has_changed(self) -> bool:
        """Check if the theme has changed from the original."""
        current_selection = self.theme_combo.currentData()
        return current_selection != self.current_theme_on_open

    def _revert_theme(self) -> None:
        """Revert to the original theme."""
        if self.parent_window and hasattr(self.parent_window, "apply_theme"):
            self.parent_window.apply_theme(self.current_theme_on_open, initial_load=False)
            nfo("Theme reverted to: %s", self.current_theme_on_open)


# ============================================================================
# ABOUT DIALOG
# ============================================================================


class AboutDialog(QDialog):
    """Application about information dialog.

    Displays version information, credits, and license details
    for the Dataset Tools application.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_dialog()
        self._show_about_info()

    def _setup_dialog(self) -> None:
        """Setup basic dialog properties."""
        self.setWindowTitle("About Dataset Viewer")
        self.setFixedSize(500, 400)
        self.setModal(True)

    def _show_about_info(self) -> None:
        """Display the about information using QMessageBox."""
        about_text = self._build_about_text()

        # Use QMessageBox.about for consistent styling
        QMessageBox.about(self, "About Dataset Viewer", about_text)

        # Close this dialog since QMessageBox.about is modal
        self.accept()

    def _build_about_text(self) -> str:
        """Build the complete about text."""
        version_text = self._get_version_text()
        contributors_text = self._get_contributors_text()
        license_text = self._get_license_text()

        return (
            f"<b>Dataset Viewer</b><br><br>"
            f"{version_text}<br>"
            f"An ultralight metadata viewer for AI-generated content.<br>"
            f"Developed by KTISEOS NYX.<br><br>"
            f"{contributors_text}<br><br>"
            f"{license_text}"
        )

    def _get_version_text(self) -> str:
        """Get formatted version text."""
        try:
            from dataset_tools import __version__ as package_version

            if package_version and package_version != "0.0.0-dev":
                return f"Version: {package_version}"
        except ImportError:
            pass

        return "Version: N/A (development)"

    def _get_contributors_text(self) -> str:
        """Get formatted contributors text."""
        contributors = ["KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA (Lead Developer)"]

        contributor_lines = [f"- {contributor}" for contributor in contributors]
        return "Contributors:<br>" + "<br>".join(contributor_lines)

    def _get_license_text(self) -> str:
        """Get formatted license text."""
        license_name = "GPL-3.0-or-later"
        return f"License: {license_name}<br>(Refer to LICENSE file for details)"


# ============================================================================
# UTILITY DIALOG FUNCTIONS
# ============================================================================


def show_error_dialog(parent: QWidget | None, title: str, message: str) -> None:
    """Show a standardized error dialog.

    Args:
        parent: Parent widget for the dialog
        title: Dialog title
        message: Error message to display

    """
    QMessageBox.critical(parent, title, message)
    nfo("Error dialog shown: %s - %s", title, message)


def show_warning_dialog(parent: QWidget | None, title: str, message: str) -> None:
    """Show a standardized warning dialog.

    Args:
        parent: Parent widget for the dialog
        title: Dialog title
        message: Warning message to display

    """
    QMessageBox.warning(parent, title, message)
    nfo("Warning dialog shown: %s - %s", title, message)


def show_info_dialog(parent: QWidget | None, title: str, message: str) -> None:
    """Show a standardized information dialog.

    Args:
        parent: Parent widget for the dialog
        title: Dialog title
        message: Information message to display

    """
    QMessageBox.information(parent, title, message)
    nfo("Info dialog shown: %s - %s", title, message)


def ask_yes_no_question(parent: QWidget | None, title: str, question: str) -> bool:
    """Ask a yes/no question using a dialog.

    Args:
        parent: Parent widget for the dialog
        title: Dialog title
        question: Question to ask the user

    Returns:
        True if user clicked Yes, False if No or Cancel

    """
    result = QMessageBox.question(
        parent,
        title,
        question,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )

    answer = result == QMessageBox.StandardButton.Yes
    nfo("Yes/No question: %s - Answer: %s", title, "Yes" if answer else "No")
    return answer


# ============================================================================
# DIALOG FACTORY
# ============================================================================


class DialogFactory:
    """Factory class for creating and managing application dialogs.

    Provides a centralized way to create dialogs with consistent
    styling and behavior across the application.
    """

    @staticmethod
    def create_settings_dialog(parent: QWidget, current_theme: str = "") -> SettingsDialog:
        """Create a settings dialog.

        Args:
            parent: Parent widget
            current_theme: Current theme name

        Returns:
            Configured SettingsDialog instance

        """
        return SettingsDialog(parent, current_theme)

    @staticmethod
    def create_about_dialog(parent: QWidget) -> AboutDialog:
        """Create an about dialog.

        Args:
            parent: Parent widget

        Returns:
            Configured AboutDialog instance

        """
        return AboutDialog(parent)

    @staticmethod
    def show_settings(parent: QWidget, current_theme: str = "") -> None:
        """Show the settings dialog.

        Args:
            parent: Parent widget
            current_theme: Current theme name

        """
        dialog = DialogFactory.create_settings_dialog(parent, current_theme)
        dialog.exec()

    @staticmethod
    def show_about(parent: QWidget) -> None:
        """Show the about dialog.

        Args:
            parent: Parent widget

        """
        dialog = DialogFactory.create_about_dialog(parent)
        dialog.exec()
