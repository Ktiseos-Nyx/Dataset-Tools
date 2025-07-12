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
    QFormLayout,
    QLabel,
    QMessageBox,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..logger import info_monitor as nfo

# ============================================================================
# SETTINGS DIALOG
# ============================================================================


class SettingsDialog(QDialog):
    """Application settings configuration dialog with a tabbed interface."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.parent_window = parent
        self.settings = QSettings("EarthAndDuskMedia", "DatasetViewer")

        self._setup_dialog()
        self._create_tabs()
        self._create_button_box()
        self._load_current_settings()

    def _setup_dialog(self) -> None:
        """Setup basic dialog properties."""
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(500)
        self.setModal(True)
        self.layout = QVBoxLayout(self)

    def _create_tabs(self) -> None:
        """Create the tab widget and populate it."""
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_theme_tab()
        self._create_appearance_tab()
        self._create_font_tab()

    def _create_theme_tab(self) -> None:
        """Create the Themes tab."""
        theme_widget = QWidget()
        layout = QVBoxLayout(theme_widget)
        layout.setSpacing(20)

        # Theme Section
        theme_label = QLabel("<b>Display Theme:</b>")
        self.theme_combo = QComboBox()
        self._populate_theme_combo()
        layout.addWidget(theme_label)
        layout.addWidget(self.theme_combo)

        layout.addStretch(1)
        self.tab_widget.addTab(theme_widget, "Themes")

    def _create_appearance_tab(self) -> None:
        """Create the Appearance tab with window size options."""
        appearance_widget = QWidget()
        layout = QVBoxLayout(appearance_widget)
        layout.setSpacing(20)

        # Window Size Section
        size_label = QLabel("<b>Window Size:</b>")
        self.size_combo = QComboBox()
        self._populate_size_combo()
        layout.addWidget(size_label)
        layout.addWidget(self.size_combo)

        layout.addStretch(1)
        self.tab_widget.addTab(appearance_widget, "Appearance")

    def _create_font_tab(self) -> None:
        """Create the Font tab with font family and size options."""
        font_widget = QWidget()
        layout = QFormLayout(font_widget)
        layout.setSpacing(15)

        # Font Family - Only bundled fonts
        self.font_combo = QComboBox()
        self.font_combo.setEditable(False)
        self._populate_font_combo()
        layout.addRow("Font Family:", self.font_combo)

        # Font Size
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 24)
        self.font_size_spinbox.setSuffix(" pt")
        layout.addRow("Font Size:", self.font_size_spinbox)

        self.tab_widget.addTab(font_widget, "Fonts")

    def _populate_theme_combo(self) -> None:
        """Populate the theme combo box."""
        if hasattr(self.parent_window, "enhanced_theme_manager"):
            enhanced_manager = self.parent_window.enhanced_theme_manager
            available_themes = enhanced_manager.get_available_themes()
            for category, themes in available_themes.items():
                if not themes:
                    continue
                category_name = enhanced_manager.THEME_CATEGORIES.get(
                    category, category.title()
                )
                for theme_name in themes:
                    theme_id = f"{category}:{theme_name}"
                    display_name = f"{category_name} - {theme_name.replace('_', ' ').replace('.xml', '').title()}"
                    self.theme_combo.addItem(display_name, theme_id)
        else:
            self.theme_combo.addItem("No themes available")
            self.theme_combo.setEnabled(False)

    def _populate_size_combo(self) -> None:
        """Populate the size combo box."""
        self.size_presets: dict[str, tuple[int, int] | None] = {
            "Remember Last Size": None,
            "Default (1024x768)": (1024, 768),
            "Small (800x600)": (800, 600),
            "Medium (1280x900)": (1280, 900),
            "Large (1600x900)": (1600, 900),
        }
        for display_name in self.size_presets:
            self.size_combo.addItem(display_name)

    def _populate_font_combo(self) -> None:
        """Populate combo box with ONLY bundled fonts."""
        try:
            from ..ui.font_manager import get_font_manager

            font_manager = get_font_manager()
            bundled_font_names = list(font_manager.BUNDLED_FONTS.keys())

            if bundled_font_names:
                # Add only bundled fonts - no system fonts at all
                for family in sorted(bundled_font_names):
                    self.font_combo.addItem(family)

                nfo(
                    f"Added {len(bundled_font_names)} bundled fonts to combo box (no system fonts)"
                )
            else:
                nfo("No bundled fonts found - adding fallback option")
                self.font_combo.addItem("Open Sans")  # Fallback

        except Exception as e:
            nfo(f"Could not load bundled fonts for combo: {e}")
            self.font_combo.addItem("Open Sans")  # Fallback

    def _create_button_box(self) -> None:
        """Create the dialog button box."""
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        self.button_box.accepted.connect(self.accept_settings)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self.apply_all_settings
        )
        self.layout.addWidget(self.button_box)

    def _load_current_settings(self) -> None:
        """Load and display current settings for all tabs."""
        self._load_theme_setting()
        self._load_window_size_setting()
        self._load_font_setting()

    def _load_theme_setting(self) -> None:
        """Load and set current theme setting."""
        if hasattr(self.parent_window, "enhanced_theme_manager"):
            current_theme = self.parent_window.enhanced_theme_manager.current_theme
            for i in range(self.theme_combo.count()):
                if self.theme_combo.itemData(i) == current_theme:
                    self.theme_combo.setCurrentIndex(i)
                    return

    def _load_window_size_setting(self) -> None:
        """Load and set current window size setting."""
        remember = self.settings.value("rememberGeometry", True, type=bool)
        if remember:
            self.size_combo.setCurrentText("Remember Last Size")
        else:
            preset = self.settings.value("windowSizePreset", "Default (1024x768)")
            self.size_combo.setCurrentText(preset)

    def _load_font_setting(self) -> None:
        """Load and set current font family and size."""
        font_family = self.settings.value("fontFamily", "Open Sans", type=str)
        font_size = self.settings.value("fontSize", 10, type=int)

        # Find and select the font in our bundled fonts combo
        index = self.font_combo.findText(font_family)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        else:
            # Default to first item (usually Open Sans) if not found
            self.font_combo.setCurrentIndex(0)

        self.font_size_spinbox.setValue(font_size)

    def apply_all_settings(self) -> None:
        """Apply all settings without closing the dialog."""
        self._apply_theme_settings()
        self._apply_window_settings()
        self._apply_font_settings()
        # Re-apply fonts after theme to ensure they override any theme font settings
        if self.parent_window and hasattr(self.parent_window, "apply_global_font"):
            self.parent_window.apply_global_font()
        nfo("All settings applied.")

    def _apply_theme_settings(self) -> None:
        """Apply the selected theme."""
        selected_theme_id = self.theme_combo.currentData()
        if selected_theme_id and hasattr(self.parent_window, "enhanced_theme_manager"):
            self.parent_window.enhanced_theme_manager.apply_theme(selected_theme_id)

    def _apply_window_settings(self) -> None:
        """Apply the selected window size settings."""
        selected_size_text = self.size_combo.currentText()
        size_tuple = self.size_presets.get(selected_size_text)
        if selected_size_text == "Remember Last Size":
            self.settings.setValue("rememberGeometry", True)
        elif size_tuple and hasattr(self.parent_window, "resize_window"):
            self.settings.setValue("rememberGeometry", False)
            self.settings.setValue("windowSizePreset", selected_size_text)
            self.parent_window.resize_window(*size_tuple)

    def _apply_font_settings(self) -> None:
        """Apply the selected font family and size globally."""
        font_family = self.font_combo.currentText()
        font_size = self.font_size_spinbox.value()

        # Save settings
        self.settings.setValue("fontFamily", font_family)
        self.settings.setValue("fontSize", font_size)

        # Apply globally
        if self.parent_window and hasattr(self.parent_window, "apply_global_font"):
            self.parent_window.apply_global_font()
            nfo(f"Applied global font: {font_family}, {font_size}pt")

    def accept_settings(self) -> None:
        """Apply all settings and close the dialog."""
        self.apply_all_settings()
        self.accept()


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
        contributors = [
            "KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA (Lead Developer)"
        ]

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
    def create_settings_dialog(
        parent: QWidget, current_theme: str = ""
    ) -> SettingsDialog:
        """Create a settings dialog.

        Args:
            parent: Parent widget
            current_theme: Current theme name

        Returns:
            Configured SettingsDialog instance

        """
        return SettingsDialog(parent)

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
