# dataset_tools/ui/dialogs.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Dialog classes for Dataset Tools.

This module contains all dialog windows used in the application,
including settings configuration and about information dialogs.
"""

from PyQt6 import QtCore
from PyQt6 import QtWidgets as Qw
from PyQt6.QtCore import QSettings, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .. import civitai_api
from ..logger import info_monitor as nfo

# ============================================================================
# SETTINGS DIALOG
# ============================================================================


class SettingsDialog(QDialog):
    """Application settings configuration dialog with a tabbed interface."""

    theme_changed = pyqtSignal(str)

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

        self._create_theme_tab()
        self._create_appearance_tab()
        self._create_api_keys_tab()
        self._create_system_tab()
        self._create_about_tab()

    def _create_theme_tab(self) -> None:
        """Create the Themes tab with buttons for each theme pack."""
        theme_widget = QWidget()
        layout = QVBoxLayout(theme_widget)
        layout.setSpacing(10)

        if hasattr(self.parent_window, "enhanced_theme_manager"):
            enhanced_manager = self.parent_window.enhanced_theme_manager
            available_themes_by_cat = enhanced_manager.get_available_themes()

            description = QLabel("Select a theme pack to browse:")
            description.setWordWrap(True)
            layout.addWidget(description)

            for category_id, themes_in_cat in available_themes_by_cat.items():
                if not themes_in_cat:
                    continue

                category_name = enhanced_manager.THEME_CATEGORIES.get(category_id, category_id.title())

                button = QPushButton(f"Browse {category_name} ({len(themes_in_cat)} themes)")
                button.setToolTip(f"Open a new dialog to browse themes in the '{category_name}' collection.")
                button.clicked.connect(
                    lambda checked=False, cat_id=category_id, cat_name=category_name, th=themes_in_cat: self._open_theme_pack_dialog(cat_id, cat_name, th)
                )
                layout.addWidget(button)
        else:
            layout.addWidget(QLabel("Theme manager not available."))

        layout.addStretch(1)
        self.tab_widget.addTab(theme_widget, "Themes")

    def _open_theme_pack_dialog(self, category_id: str, category_name: str, themes: list[str]) -> None:
        """Opens a dedicated dialog for a specific theme pack."""
        if not hasattr(self.parent_window, "enhanced_theme_manager"):
            return

        enhanced_manager = self.parent_window.enhanced_theme_manager

        dialog = ThemeBrowserDialog(category_id, category_name, themes, enhanced_manager, self)
        dialog.exec()

    def _create_appearance_tab(self) -> None:
        """Create the Appearance tab with window size options."""
        appearance_widget = QWidget()
        layout = QVBoxLayout(appearance_widget)
        layout.setSpacing(20)

        size_label = QLabel("<b>Window Size:</b>")
        self.size_combo = QComboBox()
        self._populate_size_combo()
        layout.addWidget(size_label)
        layout.addWidget(self.size_combo)

        view_label = QLabel("<b>File View Mode:</b>")
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItem("List View (Default)", "list")
        self.view_mode_combo.addItem("Thumbnail Grid (Images Only)", "grid")
        self.view_mode_combo.addItem("Tree View (Hierarchical)", "tree")
        layout.addWidget(view_label)
        layout.addWidget(self.view_mode_combo)

        view_help = QLabel(
            "<i>Thumbnail Grid shows image previews with lazy loading.<br/>"
            "Tree View shows folders and files in a hierarchical structure.<br/>"
            "First load may be slow, but thumbnails are cached for instant loading after.</i>"
        )
        view_help.setWordWrap(True)
        layout.addWidget(view_help)

        # Thumbnail Grid Settings
        thumb_label = QLabel("<b>Thumbnail Grid Settings:</b>")
        layout.addWidget(thumb_label)

        thumb_layout = QFormLayout()
        thumb_layout.setSpacing(10)

        # TEMPORARILY DISABLED - Grid sizing was causing layout issues
        # Will re-enable once we figure out the viewport calculation problems
        # TODO: Re-add thumbnail size and grid column controls later

        info_label = QLabel("⚠️ Grid layout controls temporarily disabled due to layout issues.\n"
                           "Thumbnails will auto-size based on window width.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; font-style: italic;")
        thumb_layout.addRow(info_label)

        layout.addLayout(thumb_layout)

        # Font settings
        font_label = QLabel("<b>Fonts:</b>")
        layout.addWidget(font_label)

        font_layout = QFormLayout()
        font_layout.setSpacing(10)

        self.font_combo = QComboBox()
        self.font_combo.setEditable(False)
        self._populate_font_combo()
        font_layout.addRow("App Font:", self.font_combo)

        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 24)
        self.font_size_spinbox.setSuffix(" pt")
        font_layout.addRow("Font Size:", self.font_size_spinbox)

        self.tooltip_font_combo = QComboBox()
        self.tooltip_font_combo.setEditable(False)
        self._populate_tooltip_font_combo()
        font_layout.addRow("Tooltip Font:", self.tooltip_font_combo)

        self.tooltip_size_spinbox = QSpinBox()
        self.tooltip_size_spinbox.setRange(8, 18)
        self.tooltip_size_spinbox.setSuffix(" pt")
        font_layout.addRow("Tooltip Size:", self.tooltip_size_spinbox)

        # Font preview label
        self.font_preview = QLabel("The quick brown fox jumps over the lazy dog")
        self.font_preview.setMinimumHeight(60)
        self.font_preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.font_preview.setStyleSheet("QLabel { border: 1px solid #666; padding: 10px; background: #f0f0f0; color: #000; }")
        font_layout.addRow("Preview:", self.font_preview)

        # Connect signals for live preview
        self.font_combo.currentTextChanged.connect(self._update_font_preview)
        self.font_size_spinbox.valueChanged.connect(self._update_font_preview)

        layout.addLayout(font_layout)

        # Add Apply button at the bottom of Appearance tab
        apply_appearance_btn = QPushButton("Apply Settings")
        apply_appearance_btn.setToolTip("Apply appearance settings without closing the dialog")
        apply_appearance_btn.clicked.connect(self._apply_appearance_only)
        layout.addWidget(apply_appearance_btn)

        layout.addStretch(1)
        self.tab_widget.addTab(appearance_widget, "Appearance")

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
                for family in sorted(bundled_font_names):
                    self.font_combo.addItem(family)
                nfo(f"Added {len(bundled_font_names)} bundled fonts to combo box (no system fonts)")
            else:
                nfo("No bundled fonts found - adding fallback option")
                self.font_combo.addItem("Open Sans")
        except Exception as e:
            nfo(f"Could not load bundled fonts for combo: {e}")
            self.font_combo.addItem("Open Sans")

    def _populate_tooltip_font_combo(self) -> None:
        """Populate tooltip font combo with bundled fonts."""
        try:
            from ..ui.font_manager import get_font_manager
            font_manager = get_font_manager()
            bundled_font_names = list(font_manager.BUNDLED_FONTS.keys())
            if bundled_font_names:
                for family in sorted(bundled_font_names):
                    self.tooltip_font_combo.addItem(family)
                nfo(f"Added {len(bundled_font_names)} bundled fonts to tooltip combo")
            else:
                self.tooltip_font_combo.addItem("Open Sans")
        except Exception as e:
            nfo(f"Could not load bundled fonts for tooltip combo: {e}")
            self.tooltip_font_combo.addItem("Open Sans")

    def _apply_tooltip_font_preview(self) -> None:
        """Apply tooltip font settings immediately for preview."""
        tooltip_family = self.tooltip_font_combo.currentText()
        tooltip_size = self.tooltip_size_spinbox.value()

        from PyQt6.QtWidgets import QToolTip
        from PyQt6.QtGui import QFont
        QToolTip.setFont(QFont(tooltip_family, tooltip_size))
        nfo(f"Preview tooltip font: {tooltip_family} {tooltip_size}pt")

    def _update_font_preview(self) -> None:
        """Update the font preview label with the selected font and size."""
        font_family = self.font_combo.currentText()
        font_size = self.font_size_spinbox.value()

        font = QFont(font_family, font_size)
        self.font_preview.setFont(font)

    def _create_api_keys_tab(self) -> None:
        """Create the API Keys tab."""
        api_keys_widget = QWidget()
        layout = QFormLayout(api_keys_widget)
        layout.setSpacing(15)

        self.civitai_api_key_input = QLineEdit()
        self.civitai_api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.civitai_api_key_input.setPlaceholderText("Enter your Civitai API Key")
        layout.addRow("Civitai API Key:", self.civitai_api_key_input)

        help_text = QLabel("Providing an API key allows for higher rate limits and access to NSFW content if your account is configured for it.")
        help_text.setWordWrap(True)
        layout.addRow(help_text)

        # Cache management
        cache_layout = QHBoxLayout()
        clear_cache_btn = QPushButton("Clear CivitAI Cache")
        clear_cache_btn.setToolTip("Clear all cached API responses. They will be re-fetched on next use.")
        clear_cache_btn.clicked.connect(self._clear_civitai_cache)
        cache_layout.addWidget(clear_cache_btn)
        cache_layout.addStretch()
        layout.addRow("Cache:", cache_layout)

        self.tab_widget.addTab(api_keys_widget, "API Keys")

    def _create_system_tab(self) -> None:
        """Create the System tab with cache management and system resources."""
        system_widget = QWidget()
        layout = QVBoxLayout(system_widget)
        layout.setSpacing(20)

        # Cache Management Section
        cache_group = QLabel("<b>Cache Management:</b>")
        layout.addWidget(cache_group)

        cache_info = QLabel(
            "<i>Caches improve performance but use disk space and memory.<br/>"
            "Clear caches if experiencing issues or to free up resources.</i>"
        )
        cache_info.setWordWrap(True)
        layout.addWidget(cache_info)

        # Thumbnail cache button
        self.clear_thumbnail_button = QPushButton("Clear Thumbnail Cache")
        self.clear_thumbnail_button.setToolTip(
            "Deletes cached thumbnail files from disk.\n"
            "Thumbnails will be regenerated on next view."
        )
        self.clear_thumbnail_button.clicked.connect(self._on_clear_thumbnail_clicked)
        layout.addWidget(self.clear_thumbnail_button)

        # Workflow cache button
        self.clear_workflow_button = QPushButton("Clear Workflow Cache")
        self.clear_workflow_button.setToolTip(
            "Clears in-memory workflow analysis cache.\n"
            "Workflow scoring will be recalculated on next load."
        )
        self.clear_workflow_button.clicked.connect(self._on_clear_workflow_clicked)
        layout.addWidget(self.clear_workflow_button)

        # Clear all caches button
        self.clear_all_button = QPushButton("Clear All Caches")
        self.clear_all_button.setToolTip(
            "Clears both thumbnail and workflow caches.\n"
            "Use this for a complete cache reset."
        )
        self.clear_all_button.clicked.connect(self._on_clear_all_caches_clicked)
        layout.addWidget(self.clear_all_button)

        layout.addStretch(1)
        self.tab_widget.addTab(system_widget, "System")

    def _create_about_tab(self) -> None:
        """Create the About tab with application information."""
        about_widget = QWidget()
        layout = QVBoxLayout(about_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Application title and version
        title_label = QLabel("<h2>Dataset Tools</h2>")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Get version from package metadata
        try:
            from .. import __version__
            version_text = __version__
        except (ImportError, AttributeError):
            version_text = "unknown"

        version_label = QLabel(f"<b>Version:</b> {version_text}")
        version_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        # Description
        description = QLabel(
            "A Simple Viewer for EXIF and AI Metadata. "
            "Extracts from various AI image generation tools including ComfyUI, Forge, A1111, "
            "NovelAI, Draw Things, InvokeAI, and more."
            "Reads from popular sites metadata such"
            "as Civitai, Tensorart and Moescape(Yodayo)"
            "Includes CivitAI API integration for model and asset info."
        )
        description.setWordWrap(True)
        description.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Credits section
        credits_label = QLabel("<b>Developed by:</b>")
        credits_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits_label)

        credits_text = QLabel("KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA")
        credits_text.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits_text)

        credits_text = QLabel("Supervised by: traugdor")
        credits_text.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits_text)

        credits_text = QLabel("Special Thanks to contributors: Open Source Community, Whitevamp, Exdysa, ")
        credits_text.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits_text)

        # License
        license_label = QLabel(
            "<i>Licensed under the GPL-3.0 license<br/>"
            "© 2025 Dataset Tools Contributors</i>"
        )
        license_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        license_label.setWordWrap(True)
        layout.addWidget(license_label)

        # Add separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator2)

        # GitHub link (placeholder - user can update with actual repo)
        github_label = QLabel(
            'Repository: <a href="https://github.com/Ktiseos-Nyx/Dataset-Tools">'
            'github.com/Ktiseos-Nyx/Dataset-Tools</a>' '<br/>'
            'Discord: <a href="https://discord.gg/HhBSvM9gBY">Ktiseos Nyx Discord</a>'
            '<br/>'
            'Membership / Ko-Fi: <a href="https://ko-fi.com/duskfallcrew/">ko-fi.com/duskfallcrew</a>'
        )
        github_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        github_label.setOpenExternalLinks(True)
        layout.addWidget(github_label)

        layout.addStretch(1)
        self.tab_widget.addTab(about_widget, "About")

    def _create_button_box(self) -> None:
        """Create the dialog button box."""
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept_settings)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def _on_clear_thumbnail_clicked(self) -> None:
        """Handle the clear thumbnail cache button click."""
        if hasattr(self.parent_window, "clear_thumbnail_cache"):
            self.parent_window.clear_thumbnail_cache()
        else:
            nfo("Parent window does not have clear_thumbnail_cache method.")

    def _on_clear_workflow_clicked(self) -> None:
        """Handle the clear workflow cache button click."""
        if hasattr(self.parent_window, "clear_workflow_cache"):
            self.parent_window.clear_workflow_cache()
        else:
            nfo("Parent window does not have clear_workflow_cache method.")

    def _on_clear_all_caches_clicked(self) -> None:
        """Handle the clear all caches button click."""
        if hasattr(self.parent_window, "clear_all_caches"):
            self.parent_window.clear_all_caches()
        else:
            nfo("Parent window does not have clear_all_caches method.")

    def _load_current_settings(self) -> None:
        """Load and display current settings for all tabs."""
        self._load_window_size_setting()
        self._load_font_setting()
        self._load_view_mode_setting()
        self._load_api_key_setting()
        self._load_thumbnail_settings()

    def _load_view_mode_setting(self) -> None:
        """Load and set current view mode setting."""
        view_mode = self.settings.value("fileViewMode", "list", type=str)
        index = self.view_mode_combo.findData(view_mode)
        if index >= 0:
            self.view_mode_combo.setCurrentIndex(index)

    def _load_api_key_setting(self) -> None:
        """Load and set current API key setting."""
        api_key = self.settings.value("civitai_api_key", "", type=str)
        self.civitai_api_key_input.setText(api_key)

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
        # App font
        font_family = self.settings.value("fontFamily", "Open Sans", type=str)
        font_size = self.settings.value("fontSize", 10, type=int)
        index = self.font_combo.findText(font_family)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        else:
            self.font_combo.setCurrentIndex(0)
        self.font_size_spinbox.setValue(font_size)

        # Update font preview with loaded settings
        self._update_font_preview()

        # Tooltip font
        tooltip_family = self.settings.value("tooltipFontFamily", "Open Sans", type=str)
        tooltip_size = self.settings.value("tooltipFontSize", 9, type=int)
        tooltip_index = self.tooltip_font_combo.findText(tooltip_family)
        if tooltip_index >= 0:
            self.tooltip_font_combo.setCurrentIndex(tooltip_index)
        else:
            self.tooltip_font_combo.setCurrentIndex(0)
        self.tooltip_size_spinbox.setValue(tooltip_size)

    def _load_thumbnail_settings(self) -> None:
        """Load and set thumbnail grid settings."""
        # Grid sizing controls temporarily disabled - do nothing
        pass

    def _snap_thumb_size_to_64(self, value: int) -> None:
        """Snap slider value to nearest multiple of 64."""
        pass  # Temporarily disabled

    def _update_thumb_size_label(self, value: int = None) -> None:
        """Update the thumbnail size label."""
        pass  # Temporarily disabled

    def _on_thumb_auto_changed(self) -> None:
        """Handle thumbnail size auto checkbox change."""
        pass  # Temporarily disabled

    def _on_grid_auto_changed(self) -> None:
        """Handle grid columns auto checkbox change."""
        pass  # Temporarily disabled

    def _on_grid_cols_changed(self) -> None:
        """Handle grid columns spinbox change - apply immediately for live preview."""
        pass  # Temporarily disabled

    def _apply_appearance_only(self) -> None:
        """Apply only appearance settings (for preview without closing dialog)."""
        self._apply_window_settings()
        self._apply_font_settings()
        self._apply_view_mode_settings()
        self._apply_thumbnail_settings()
        if self.parent_window and hasattr(self.parent_window, "apply_global_font"):
            self.parent_window.apply_global_font()
        self.show_status_message("Appearance settings applied!")
        nfo("Appearance settings applied from tab.")

    def show_status_message(self, message: str) -> None:
        """Show a status message in the parent window."""
        if self.parent_window and hasattr(self.parent_window, "show_status_message"):
            self.parent_window.show_status_message(message)

    def apply_all_settings(self) -> None:
        """Apply all settings without closing the dialog."""
        self._apply_window_settings()
        self._apply_font_settings()
        self._apply_view_mode_settings()
        self._apply_api_key_settings()
        self._apply_thumbnail_settings()
        if self.parent_window and hasattr(self.parent_window, "apply_global_font"):
            self.parent_window.apply_global_font()
        nfo("All settings applied.")

    def _apply_view_mode_settings(self) -> None:
        """Apply the selected view mode."""
        view_mode = self.view_mode_combo.currentData()
        self.settings.setValue("fileViewMode", view_mode)
        if hasattr(self.parent_window, "set_file_view_mode"):
            self.parent_window.set_file_view_mode(view_mode)

    def _apply_api_key_settings(self) -> None:
        """Apply the API key settings."""
        api_key = self.civitai_api_key_input.text()
        self.settings.setValue("civitai_api_key", api_key)

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
        # App font
        font_family = self.font_combo.currentText()
        font_size = self.font_size_spinbox.value()
        self.settings.setValue("fontFamily", font_family)
        self.settings.setValue("fontSize", font_size)

        # Tooltip font
        tooltip_family = self.tooltip_font_combo.currentText()
        tooltip_size = self.tooltip_size_spinbox.value()
        self.settings.setValue("tooltipFontFamily", tooltip_family)
        self.settings.setValue("tooltipFontSize", tooltip_size)

        # Apply tooltip font immediately
        from PyQt6.QtWidgets import QToolTip
        from PyQt6.QtGui import QFont
        QToolTip.setFont(QFont(tooltip_family, tooltip_size))
        nfo(f"Applied tooltip font: {tooltip_family} {tooltip_size}pt")

        # Apply app font
        if self.parent_window and hasattr(self.parent_window, "apply_global_font"):
            self.parent_window.apply_global_font()
            nfo(f"Applied global font: {font_family}, {font_size}pt")

    def _apply_thumbnail_settings(self) -> None:
        """Apply thumbnail grid settings."""
        # Grid sizing controls temporarily disabled - settings use auto defaults
        # Set auto mode by default
        self.settings.setValue("thumbnailSizeAuto", True)
        self.settings.setValue("gridColumnsAuto", True)

    def _clear_civitai_cache(self) -> None:
        """Clear the CivitAI API cache."""
        reply = QMessageBox.question(
            self,
            "Clear Cache",
            "Are you sure you want to clear the CivitAI cache?\n\nAll cached API responses will be deleted and re-fetched on next use.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            files_deleted, bytes_freed = civitai_api.clear_cache()
            kb_freed = bytes_freed / 1024

            if files_deleted > 0:
                QMessageBox.information(
                    self,
                    "Cache Cleared",
                    "Cleared %s cached files (%.2f KB)" % (files_deleted, kb_freed)
                )
            else:
                QMessageBox.information(
                    self,
                    "Cache Empty",
                    "No cached files found."
                )

    def accept_settings(self) -> None:
        """Apply all settings and close the dialog."""
        self.apply_all_settings()
        self.accept()


# ============================================================================
# THEME BROWSER DIALOG
# ============================================================================


class ThemeBrowserDialog(QDialog):
    """A dialog for browsing and selecting themes from a categorized list."""

    def __init__(self, category_id: str, category_name: str, themes: list[str], theme_manager, parent: QWidget | None = None):
        super().__init__(parent)
        self.category_id = category_id
        self.themes = themes
        self.theme_manager = theme_manager

        self.setWindowTitle(f"Theme Browser: {category_name}")
        self.setMinimumSize(500, 600)

        layout = QVBoxLayout(self)

        # Add a search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search themes...")
        self.search_bar.textChanged.connect(self._filter_tree)
        layout.addWidget(self.search_bar)

        # Add the tree widget for all theme packs
        if category_id == "KTISEOS_NYX_THEMES":
            self.tree_widget = QTreeWidget()
            self.tree_widget.setHeaderHidden(True)
            self.tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
            layout.addWidget(self.tree_widget)
            self._populate_tree()
        else:
            self.list_widget = QListWidget()
            self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked_list)
            layout.addWidget(self.list_widget)
            self._populate_list()

        # Add Apply and Close buttons
        self.button_box = QDialogButtonBox()
        self.apply_button = self.button_box.addButton("Apply", QDialogButtonBox.ButtonRole.ApplyRole)
        self.close_button = self.button_box.addButton(QDialogButtonBox.StandardButton.Close)

        self.apply_button.clicked.connect(self.apply_selected_theme)
        self.close_button.clicked.connect(self.reject)

        layout.addWidget(self.button_box)

    def _populate_tree(self):
        """Populate the tree widget with categorized themes."""
        categorized = self._categorize_themes()

        for category, theme_list in sorted(categorized.items()):
            parent_item = QTreeWidgetItem(self.tree_widget)
            parent_item.setText(0, f"{category.replace('_', ' ').title()} ({len(theme_list)}))")
            parent_item.setFlags(parent_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

            for theme_name in sorted(theme_list):
                child_item = QTreeWidgetItem(parent_item)
                display_name = theme_name.replace("_", " ").replace(".xml", "").title()
                if " " in display_name and display_name.split(" ")[0].lower() + "_" in category.lower() + "_":
                    display_name = " ".join(display_name.split(" ")[1:])

                child_item.setText(0, display_name)
                child_item.setData(0, Qt.ItemDataRole.UserRole, f"{self.category_id}:{theme_name}")

        self.tree_widget.expandAll()

    def _populate_list(self):
        """Populate the list widget with themes."""
        for theme_name in self.themes:
            display_name = theme_name.replace("_", " ").replace(".xml", "").title()
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, f"{self.category_id}:{theme_name}")
            self.list_widget.addItem(item)

    def _categorize_themes(self) -> dict[str, list[str]]:
        """Categorize themes based on filename prefixes."""
        categorized_themes = {}
        prefixes = ["immature_", "sports_", "pop_culture_",
                    "pokemon_", "food_",
                    "ffxiv_", "decade_", "aesthetic_",
                    "ai_", "memes_", "games_", "crafts",
                    "movies_", "tv_", "anime_", "comics_",
                    "fantasy_", "horror_", "scifi_", "cyberpunk_",
                    "steampunk_", "vaporwave_", "retro_",
                    "vtubers_", "holiday_", "streamers_",
                    "artists_", "musicians_", "bands_",
                    "nature_", "space_", "weather_",
                    "assaulted_", "ui_", "music_",
                    "food_", "movies", "comics", "cartoons",
                    "color_theme_", "crafts_", "weird_colors_",
                    "pokemon_inspired_"]

        for theme in self.themes:
            found_category = "Uncategorized"
            for prefix in prefixes:
                if theme.startswith(prefix):
                    found_category = prefix.strip("_")
                    break

            if found_category not in categorized_themes:
                categorized_themes[found_category] = []
            categorized_themes[found_category].append(theme)

        return categorized_themes

    def apply_selected_theme(self):
        """Apply the currently selected theme."""
        if hasattr(self, "tree_widget"):
            selected_items = self.tree_widget.selectedItems()
            if selected_items:
                self._apply_theme(selected_items[0])
        elif hasattr(self, "list_widget"):
            selected_items = self.list_widget.selectedItems()
            if selected_items:
                self._apply_theme(selected_items[0])

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle when a theme is double-clicked in the tree."""
        self._apply_theme(item)
        self.accept()

    def _on_item_double_clicked_list(self, item: QListWidgetItem):
        """Handle when a theme is double-clicked in the list."""
        self._apply_theme(item)
        self.accept()

    def _apply_theme(self, item: QTreeWidgetItem | QListWidgetItem):
        """Helper to apply the theme from a given item."""
        if isinstance(item, QTreeWidgetItem):
            theme_id = item.data(0, Qt.ItemDataRole.UserRole)
        else:
            theme_id = item.data(Qt.ItemDataRole.UserRole)

        if theme_id:
            self.theme_manager.apply_theme(theme_id)
            if hasattr(self.parent(), "show_status_message"):
                if isinstance(item, QTreeWidgetItem):
                    self.parent().show_status_message(f"Applied theme: {item.text(0)}")
                else:
                    self.parent().show_status_message(f"Applied theme: {item.text()}")

    def _filter_tree(self, text: str):
        """Filter the tree widget based on the search text."""
        if hasattr(self, "tree_widget"):
            root = self.tree_widget.invisibleRootItem()
            for i in range(root.childCount()):
                category_item = root.child(i)
                has_visible_child = False
                for j in range(category_item.childCount()):
                    theme_item = category_item.child(j)
                    is_match = text.lower() in theme_item.text(0).lower()
                    theme_item.setHidden(not is_match)
                    if is_match:
                        has_visible_child = True
                category_item.setHidden(not has_visible_child)
        elif hasattr(self, "list_widget"):
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                is_match = text.lower() in item.text().lower()
                item.setHidden(not is_match)


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

        QMessageBox.about(self, "About Dataset Viewer", about_text)

        self.accept()

    def _build_about_text(self) -> str:
        """Build the complete about text."""
        version_text = self._get_version_text()

        return (
            f"<b>Dataset Tools</b><br><br>"
            f"{version_text}<br><br>"
            f"A Simple Viewer for EXIF and AI Metadata.<br>"
            f"Extracts from various AI image generation tools including ComfyUI, Forge, A1111, "
            f"NovelAI, Draw Things, InvokeAI, and more.<br>"
            f"Reads from popular sites metadata such as Civitai, Tensorart and Moescape(Yodayo).<br>"
            f"Includes CivitAI API integration for model and asset info.<br><br>"
            f"<b>Copyright © 2025 KTISEOS NYX / EARTH & DUSK MEDIA</b><br>"
            f"Licensed under GPL-3.0<br><br>"
            f"Built with PyQt6 and Pillow for robust metadata extraction."
        )

    def _get_version_text(self) -> str:
        """Get formatted version text."""
        try:
            from .. import __version__
            return f"<b>Version:</b> {__version__}"
        except (ImportError, AttributeError):
            return "<b>Version:</b> unknown"


# ============================================================================
# UTILITY DIALOG FUNCTIONS
# ============================================================================


def show_error_dialog(parent: QWidget | None, title: str, message: str) -> None:
    """Show a standardized error dialog."""
    QMessageBox.critical(parent, title, message)
    nfo("Error dialog shown: %s - %s", title, message)


def show_warning_dialog(parent: QWidget | None, title: str, message: str) -> None:
    """Show a standardized warning dialog."""
    QMessageBox.warning(parent, title, message)
    nfo("Warning dialog shown: %s - %s", title, message)


def show_info_dialog(parent: QWidget | None, title: str, message: str) -> None:
    """Show a standardized information dialog."""
    QMessageBox.information(parent, title, message)
    nfo("Info dialog shown: %s - %s", title, message)


def ask_yes_no_question(parent: QWidget | None, title: str, question: str) -> bool:
    """Ask a yes/no question using a dialog."""
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
# TEXT EDIT DIALOG
# ============================================================================


class TextEditDialog(QDialog):
    """A simple dialog for editing a block of text."""

    def __init__(self, initial_text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Text")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(initial_text)
        font = QFont("Courier New")
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_edit.setFont(font)
        layout.addWidget(self.text_edit)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_text(self) -> str:
        """Return the edited text from the text edit widget."""
        return self.text_edit.toPlainText()

    @staticmethod
    def get_edited_text(parent: QWidget, initial_text: str) -> tuple[bool, str]:
        """Static method to show the dialog and get the result."""
        dialog = TextEditDialog(initial_text, parent)
        if dialog.exec():
            return True, dialog.get_text()
        return False, initial_text


# ============================================================================
# DIALOG FACTORY
# ============================================================================


class DialogFactory:
    """Factory class for creating and managing application dialogs."""

    @staticmethod
    def create_settings_dialog(parent: QWidget, current_theme: str = "") -> SettingsDialog:
        """Create a settings dialog."""
        return SettingsDialog(parent)

    @staticmethod
    def create_about_dialog(parent: QWidget) -> AboutDialog:
        """Create an about dialog."""
        return AboutDialog(parent)

    @staticmethod
    def show_settings(parent: QWidget, current_theme: str = "") -> None:
        """Show the settings dialog."""
        dialog = DialogFactory.create_settings_dialog(parent, current_theme)
        dialog.exec()

    @staticmethod
    def show_about(parent: QWidget) -> None:
        """Show the about dialog."""
        dialog = DialogFactory.create_about_dialog(parent)
        dialog.exec()
