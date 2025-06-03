# dataset_tools/ui.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""App UI for Dataset-Tools"""

import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from PyQt6 import QtCore, QtGui
from PyQt6 import QtWidgets as Qw
from PyQt6.QtCore import QSettings  # QTimer, QDateTime, Qt also used from QtCore
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

# --- Logger Setup (Handles Fallback) ---
try:
    from .logger import debug_monitor
    from .logger import info_monitor as nfo

    LOGGER_AVAILABLE = True
except ImportError:

    def nfo_fallback(*args):
        print("NFO (fallback):", *args)

    nfo = nfo_fallback

    def debug_monitor_fallback(func):
        return func

    debug_monitor = debug_monitor_fallback
    LOGGER_AVAILABLE = False
    print(
        "WARNING: Main logger (nfo, debug_monitor) not available. Using fallback print/dummy decorator."
    )

try:
    from qt_material import apply_stylesheet, list_themes

    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False

    def list_themes_fallback():
        return ["default_light.xml", "default_dark.xml"]

    list_themes = list_themes_fallback

    def apply_stylesheet_fallback(app, theme, invert_secondary=False):
        pass

    apply_stylesheet = apply_stylesheet_fallback
    nfo("WARNING: qt-material library not found. Theme functionality will be limited.")


from .correct_types import DownField, EmptyField, UpField
from .correct_types import ExtensionType as Ext
from .metadata_parser import parse_metadata
from .widgets import FileLoader, FileLoadResult


# --- Custom Panel Widget for the Left Column ---
class LeftPanelWidget(Qw.QWidget):
    open_folder_requested = QtCore.pyqtSignal()
    sort_files_requested = QtCore.pyqtSignal()
    list_item_selected = QtCore.pyqtSignal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_panel_ui()

    def _setup_panel_ui(self):
        layout = Qw.QVBoxLayout(self)

        self.current_folder_label = Qw.QLabel("Current Folder: None")
        self.current_folder_label.setWordWrap(True)
        layout.addWidget(self.current_folder_label)

        button_layout_top = Qw.QHBoxLayout()
        self.open_folder_button = Qw.QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_folder_requested.emit)
        button_layout_top.addWidget(self.open_folder_button)

        self.sort_button = Qw.QPushButton("Sort Files")
        self.sort_button.clicked.connect(self.sort_files_requested.emit)
        button_layout_top.addWidget(self.sort_button)
        layout.addLayout(button_layout_top)

        self.message_label = Qw.QLabel("Select a folder to view its contents.")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        self.files_list_widget = Qw.QListWidget()
        self.files_list_widget.setSelectionMode(
            Qw.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.files_list_widget.currentItemChanged.connect(self.list_item_selected.emit)
        self.files_list_widget.setSizePolicy(
            Qw.QSizePolicy.Policy.Preferred, Qw.QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.files_list_widget, 1)

    def set_current_folder_text(self, text: str):
        self.current_folder_label.setText(text)

    def set_message_text(self, text: str):
        self.message_label.setText(text)

    def clear_file_list_display(self):
        self.files_list_widget.clear()

    def add_items_to_file_list(self, items: list[str]):
        self.files_list_widget.addItems(items)

    def set_current_file_by_name(self, file_name: str) -> bool:
        found_items = self.files_list_widget.findItems(
            file_name, QtCore.Qt.MatchFlag.MatchExactly
        )
        if found_items:
            self.files_list_widget.setCurrentItem(found_items[0])
            return True
        return False

    def set_current_file_by_row(self, row: int):
        if 0 <= row < self.files_list_widget.count():
            self.files_list_widget.setCurrentRow(row)

    def get_files_list_widget(self) -> Qw.QListWidget:
        return self.files_list_widget

    def set_buttons_enabled(self, enabled: bool):
        self.open_folder_button.setEnabled(enabled)
        self.sort_button.setEnabled(enabled)
        self.files_list_widget.setEnabled(enabled)


# --- End of LeftPanelWidget ---


class ImageLabel(Qw.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QtGui.QPixmap()
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setSizePolicy(Qw.QSizePolicy.Policy.Ignored, Qw.QSizePolicy.Policy.Ignored)
        self.setWordWrap(True)
        self.setFrameShape(Qw.QFrame.Shape.StyledPanel)
        self.setText("Image Preview Area\n\n(Drag & Drop Image Here)")

    def setPixmap(self, pixmap: QtGui.QPixmap | None):
        if pixmap is None or pixmap.isNull():
            self._pixmap = QtGui.QPixmap()
            super().clear()
            super().setText("No preview available or image failed to load.")
        else:
            self._pixmap = pixmap
            self._update_scaled_pixmap()
        self.update()

    def clear(self):
        super().clear()
        self._pixmap = QtGui.QPixmap()
        super().setText("Image Preview Area\n\n(Drag & Drop Image Here)")

    def _update_scaled_pixmap(self):
        if self._pixmap.isNull() or self.width() <= 10 or self.height() <= 10:
            if self._pixmap.isNull() and not self.text().strip():
                super().setText("No preview available or image failed to load.")
            return
        super().setText("")
        scaled_pixmap = self._pixmap.scaled(
            self.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        super().setPixmap(scaled_pixmap)

    def resizeEvent(self, event: QtGui.QResizeEvent):
        self._update_scaled_pixmap()
        super().resizeEvent(event)


class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_theme_xml=""):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(400)
        self.parent_window = parent
        self.current_theme_on_open = current_theme_xml
        self.settings = QSettings("EarthAndDuskMedia", "DatasetViewer")

        layout = QVBoxLayout(self)
        theme_label = QLabel("<b>Display Theme:</b>")
        layout.addWidget(theme_label)
        self.theme_combo = QComboBox()
        if QT_MATERIAL_AVAILABLE:
            self.available_themes_xml = list_themes()
            for theme_xml_name in self.available_themes_xml:
                display_name = (
                    theme_xml_name.replace(".xml", "").replace("_", " ").title()
                )
                self.theme_combo.addItem(display_name, theme_xml_name)
            current_theme_display_name = (
                current_theme_xml.replace(".xml", "").replace("_", " ").title()
            )
            index = self.theme_combo.findText(current_theme_display_name)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
            elif self.available_themes_xml:
                self.theme_combo.setCurrentIndex(0)
        else:
            self.theme_combo.addItem("Default (qt-material not found)")
            self.theme_combo.setEnabled(False)
        layout.addWidget(self.theme_combo)
        layout.addSpacing(15)

        size_label = QLabel("<b>Window Size:</b>")
        layout.addWidget(size_label)
        self.size_combo = QComboBox()
        self.size_presets = {
            "Remember Last Size": None,
            "Default (1024x768)": (1024, 768),
            "Small (800x600)": (800, 600),
            "Medium (1280x900)": (1280, 900),
            "Large (1600x900)": (1600, 900),
        }
        for display_name in self.size_presets:
            self.size_combo.addItem(display_name)

        remember_geom = self.settings.value("rememberGeometry", True, type=bool)
        if remember_geom:
            self.size_combo.setCurrentText("Remember Last Size")
        else:
            saved_preset_name = self.settings.value(
                "windowSizePreset", "Default (1024x768)"
            )
            if self.size_combo.findText(saved_preset_name) != -1:
                self.size_combo.setCurrentText(saved_preset_name)
            else:
                self.size_combo.setCurrentText("Default (1024x768)")
        layout.addWidget(self.size_combo)
        layout.addStretch(1)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply,
        )
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject_settings)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self.apply_all_settings
        )
        layout.addWidget(button_box)

    def apply_theme_settings(self):
        if not QT_MATERIAL_AVAILABLE:
            return
        selected_theme_xml = self.theme_combo.currentData()
        if (
            selected_theme_xml
            and self.parent_window
            and hasattr(self.parent_window, "apply_theme")
        ):
            self.parent_window.apply_theme(selected_theme_xml, initial_load=False)

    def apply_window_settings(self):
        selected_size_text = self.size_combo.currentText()
        size_tuple = self.size_presets.get(selected_size_text)
        if selected_size_text == "Remember Last Size":
            self.settings.setValue("rememberGeometry", True)
            if self.parent_window and hasattr(self.parent_window, "saveGeometry"):
                self.settings.setValue("geometry", self.parent_window.saveGeometry())
        elif (
            size_tuple
            and self.parent_window
            and hasattr(self.parent_window, "resize_window")
        ):
            self.settings.setValue("rememberGeometry", False)
            self.settings.setValue("windowSizePreset", selected_size_text)
            self.parent_window.resize_window(size_tuple[0], size_tuple[1])
            self.settings.remove("geometry")

    def apply_all_settings(self):
        self.apply_theme_settings()
        self.apply_window_settings()

    def accept_settings(self):
        self.apply_all_settings()
        self.current_theme_on_open = self.theme_combo.currentData()
        self.accept()

    def reject_settings(self):
        if (
            QT_MATERIAL_AVAILABLE
            and self.parent_window
            and hasattr(self.parent_window, "apply_theme")
        ):
            if (
                self.theme_combo.currentData() != self.current_theme_on_open
                and self.current_theme_on_open
            ):
                self.parent_window.apply_theme(
                    self.current_theme_on_open, initial_load=False
                )
        self.reject()


class MainWindow(Qw.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dataset Viewer")
        self.setMinimumSize(800, 600)
        self.settings = QSettings("EarthAndDuskMedia", "DatasetViewer")
        self.setAcceptDrops(True)
        self.theme_actions: dict[str, QtGui.QAction] = {}
        self.file_loader: FileLoader | None = None
        self.current_files_in_list: list[str] = []
        self.current_folder: str = ""

        # --- Status Bar Setup ---
        self.main_status_bar = self.statusBar()  # Get/create the status bar
        self.main_status_bar.showMessage("Ready", 3000)  # Initial message

        self.datetime_label = Qw.QLabel()  # Create a label for date/time
        self.main_status_bar.addPermanentWidget(
            self.datetime_label
        )  # Add to right side

        self.status_timer = QtCore.QTimer(self)  # Timer to update date/time
        self.status_timer.timeout.connect(self._update_datetime_status)
        self.status_timer.start(1000)  # Update every second
        self._update_datetime_status()  # Initial call to set date/time
        # --- End Status Bar Setup ---

        saved_theme_name_xml = self.settings.value("theme", "dark_teal.xml")
        self._setup_menus()

        if QT_MATERIAL_AVAILABLE:
            if saved_theme_name_xml and saved_theme_name_xml in self.theme_actions:
                self.apply_theme(saved_theme_name_xml, initial_load=True)
            elif "dark_teal.xml" in self.theme_actions:
                self.apply_theme("dark_teal.xml", initial_load=True)
            elif self.theme_actions:
                first_theme = next(iter(self.theme_actions.keys()), None)
                if first_theme:
                    self.apply_theme(first_theme, initial_load=True)

        remember_geom = self.settings.value("rememberGeometry", True, type=bool)
        saved_geom = self.settings.value("geometry")
        if remember_geom and saved_geom:
            self.restoreGeometry(saved_geom)
        else:
            default_size_presets = {
                "Default (1024x768)": (1024, 768)
            }  # Simplified for direct use
            default_preset_name = self.settings.value(
                "windowSizePreset", "Default (1024x768)"
            )
            default_w, default_h = default_size_presets.get(
                default_preset_name, (1024, 768)
            )
            self.resize_window(default_w, default_h)

        self._setup_ui_layout()  # self.left_panel is created here

        initial_folder_path = self.settings.value("lastFolderPath", os.getcwd())

        self.clear_file_list()  # This will interact with self.left_panel
        if initial_folder_path and Path(initial_folder_path).is_dir():
            self.load_files(initial_folder_path)
        else:
            if hasattr(self, "left_panel"):
                self.left_panel.set_current_folder_text(
                    "Current Folder: None (Select a folder or drop files)"
                )
                self.left_panel.set_message_text(
                    "Please select a folder to view its contents."
                )
            self.clear_selection()  # Clears metadata and image preview

    def _update_datetime_status(self):
        """Updates the date and time in the status bar."""
        current_dt = QtCore.QDateTime.currentDateTime()
        # Example format: "Mon May 27 15:30:55 2024"
        # Or use: current_dt.toString("yyyy-MM-dd hh:mm:ss")
        self.datetime_label.setText(
            current_dt.toString(QtCore.Qt.DateFormat.RFC2822Date)
        )

    def resize_window(self, width: int, height: int):
        self.resize(width, height)
        nfo(f"[UI] Window resized to: {width}x{height}")

    def _setup_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        change_folder_action = QtGui.QAction("Change &Folder...", self)
        change_folder_action.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        change_folder_action.triggered.connect(
            self.open_folder
        )  # MainWindow.open_folder handles dialog
        file_menu.addAction(change_folder_action)
        file_menu.addSeparator()
        close_action = QtGui.QAction("&Close Window", self)
        close_action.setShortcut(QtGui.QKeySequence.StandardKey.Close)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        view_menu = menu_bar.addMenu("&View")
        themes_menu = Qw.QMenu("&Themes", self)
        view_menu.addMenu(themes_menu)
        if QT_MATERIAL_AVAILABLE:
            group = QtGui.QActionGroup(self)
            group.setExclusive(True)
            for theme_xml in list_themes():
                name = theme_xml.replace(".xml", "").replace("_", " ").title()
                action = QtGui.QAction(name, self, checkable=True)
                action.setData(theme_xml)
                action.triggered.connect(self.on_theme_action_triggered)
                themes_menu.addAction(action)
                group.addAction(action)
                self.theme_actions[theme_xml] = action
        else:
            no_themes = QtGui.QAction("qt-material not found", self)
            no_themes.setEnabled(False)
            themes_menu.addAction(no_themes)

        # Settings menu item can be removed if button on bottom bar is preferred
        # settings_action = QtGui.QAction("&Preferences...", self)
        # settings_action.setShortcut(QtGui.QKeySequence("Ctrl+,"))
        # settings_action.triggered.connect(self.open_settings_dialog)
        # view_menu.addAction(settings_action)

        help_menu = menu_bar.addMenu("&Help")
        about_action = QtGui.QAction("&About Dataset Viewer...", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def on_theme_action_triggered(self):
        action = self.sender()
        if action and isinstance(action, QtGui.QAction):
            theme_xml = action.data()
            if theme_xml:
                self.apply_theme(theme_xml)

    def open_settings_dialog(self):
        current_theme_xml = self.settings.value("theme", "dark_teal.xml")
        dialog = SettingsDialog(self, current_theme_xml=current_theme_xml)
        dialog.exec()

    def _setup_ui_layout(self):
        main_widget = Qw.QWidget()
        self.setCentralWidget(main_widget)
        overall_layout = Qw.QVBoxLayout(main_widget)
        overall_layout.setContentsMargins(5, 5, 5, 5)
        overall_layout.setSpacing(5)

        self.main_splitter = Qw.QSplitter(QtCore.Qt.Orientation.Horizontal)
        overall_layout.addWidget(self.main_splitter, 1)

        self.left_panel = LeftPanelWidget()  # Instantiate LeftPanelWidget
        self.left_panel.open_folder_requested.connect(self.open_folder)
        self.left_panel.sort_files_requested.connect(self.sort_files_list)
        self.left_panel.list_item_selected.connect(self.on_file_selected)
        self.main_splitter.addWidget(self.left_panel)

        middle_right_area_widget = Qw.QWidget()
        middle_right_layout = Qw.QHBoxLayout(middle_right_area_widget)
        middle_right_layout.setContentsMargins(0, 0, 0, 0)
        middle_right_layout.setSpacing(5)
        self.metadata_image_splitter = Qw.QSplitter(QtCore.Qt.Orientation.Horizontal)
        middle_right_layout.addWidget(self.metadata_image_splitter)

        metadata_panel_widget = Qw.QWidget()
        metadata_layout = Qw.QVBoxLayout(metadata_panel_widget)
        metadata_layout.setContentsMargins(10, 20, 10, 20)
        metadata_layout.setSpacing(15)
        metadata_layout.addStretch(1)

        self.positive_prompt_label = Qw.QLabel("Positive Prompt")
        metadata_layout.addWidget(self.positive_prompt_label)
        self.positive_prompt_box = Qw.QTextEdit()
        self.positive_prompt_box.setReadOnly(True)
        self.positive_prompt_box.setSizePolicy(
            Qw.QSizePolicy.Policy.Expanding, Qw.QSizePolicy.Policy.Preferred
        )
        metadata_layout.addWidget(self.positive_prompt_box)

        self.negative_prompt_label = Qw.QLabel("Negative Prompt")
        metadata_layout.addWidget(self.negative_prompt_label)
        self.negative_prompt_box = Qw.QTextEdit()
        self.negative_prompt_box.setReadOnly(True)
        self.negative_prompt_box.setSizePolicy(
            Qw.QSizePolicy.Policy.Expanding, Qw.QSizePolicy.Policy.Preferred
        )
        metadata_layout.addWidget(self.negative_prompt_box)

        self.generation_data_label = Qw.QLabel("Generation Details & Metadata")
        metadata_layout.addWidget(self.generation_data_label)
        self.generation_data_box = Qw.QTextEdit()
        self.generation_data_box.setReadOnly(True)
        self.generation_data_box.setSizePolicy(
            Qw.QSizePolicy.Policy.Expanding, Qw.QSizePolicy.Policy.Preferred
        )
        metadata_layout.addWidget(self.generation_data_box)

        metadata_layout.addStretch(1)
        self.metadata_image_splitter.addWidget(metadata_panel_widget)

        self.image_preview = ImageLabel()
        self.metadata_image_splitter.addWidget(self.image_preview)
        self.main_splitter.addWidget(middle_right_area_widget)

        bottom_bar = Qw.QWidget()
        bottom_layout = Qw.QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(10, 5, 10, 5)
        bottom_layout.addStretch(1)
        action_buttons_layout = Qw.QHBoxLayout()
        action_buttons_layout.setSpacing(10)
        self.copy_metadata_button = Qw.QPushButton("Copy All Metadata")
        self.copy_metadata_button.clicked.connect(self.copy_metadata_to_clipboard)
        action_buttons_layout.addWidget(self.copy_metadata_button)
        self.settings_button = Qw.QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        action_buttons_layout.addWidget(self.settings_button)
        self.exit_button = Qw.QPushButton("Exit Application")
        self.exit_button.clicked.connect(self.close)
        action_buttons_layout.addWidget(self.exit_button)
        bottom_layout.addLayout(action_buttons_layout)
        bottom_layout.addStretch(1)
        overall_layout.addWidget(bottom_bar, 0)

        try:
            win_width = self.width() if self.isVisible() else 1024
        except RuntimeError:
            win_width = 1024  # Fallback if called too early
        main_splitter_sizes = self.settings.value(
            "mainSplitterSizes", [win_width // 4, win_width * 3 // 4], type=list
        )
        if hasattr(self, "main_splitter"):
            self.main_splitter.setSizes([int(s) for s in main_splitter_sizes])
        meta_img_splitter_sizes = self.settings.value(
            "metaImageSplitterSizes", [win_width // 3, win_width * 2 // 3], type=list
        )
        if hasattr(self, "metadata_image_splitter"):
            self.metadata_image_splitter.setSizes(
                [int(s) for s in meta_img_splitter_sizes]
            )

    def clear_file_list(self):
        nfo("[UI] Clearing file list and selections.")
        if hasattr(self, "left_panel"):
            self.left_panel.clear_file_list_display()
            self.left_panel.set_message_text(
                "Select a folder or drop files/folder here."
            )
        self.current_files_in_list = []
        self.clear_selection()

    @debug_monitor
    def open_folder(self):
        nfo("[UI] 'Open Folder' action triggered.")
        start_dir = (
            self.current_folder
            if self.current_folder and Path(self.current_folder).is_dir()
            else self.settings.value("lastFolderPath", os.path.expanduser("~"))
        )
        folder_path = Qw.QFileDialog.getExistingDirectory(
            self, "Select Folder to Load", start_dir
        )
        if folder_path:
            nfo("[UI] Folder selected via dialog: %s", folder_path)
            self.settings.setValue("lastFolderPath", folder_path)
            self.load_files(folder_path)
        else:
            msg = "Folder selection cancelled."
            nfo("[UI] %s", msg)
            if hasattr(self, "left_panel"):
                self.left_panel.set_message_text(msg)
            self.main_status_bar.showMessage(msg, 3000)

    @debug_monitor
    def load_files(
        self, folder_path: str, file_to_select_after_load: str | None = None
    ):
        nfo("[UI] Attempting to load files from: %s", folder_path)
        if self.file_loader and self.file_loader.isRunning():
            nfo("[UI] File loading is already in progress.")
            if hasattr(self, "left_panel"):
                self.left_panel.set_message_text("Loading in progress... Please wait.")
            return
        self.current_folder = str(Path(folder_path).resolve())
        if hasattr(self, "left_panel"):
            self.left_panel.set_current_folder_text(
                f"Current Folder: {self.current_folder}"
            )
            self.left_panel.set_message_text(
                f"Loading files from {Path(self.current_folder).name}..."
            )
            self.left_panel.set_buttons_enabled(False)
        self.file_loader = FileLoader(self.current_folder, file_to_select_after_load)
        self.file_loader.finished.connect(self.on_files_loaded)
        self.file_loader.start()
        nfo("[UI] FileLoader thread started for: %s", self.current_folder)

    @debug_monitor
    def on_files_loaded(self, result: FileLoadResult):
        nfo(
            "[UI] FileLoader finished. Received result for folder: %s",
            result.folder_path,
        )
        if not hasattr(self, "left_panel"):
            nfo("[UI] Error: Left panel not available in on_files_loaded.")
            return

        if result.folder_path != self.current_folder:
            nfo(
                "[UI] Discarding stale FileLoader result for: %s (current is %s)",
                result.folder_path,
                self.current_folder,
            )
            self.left_panel.set_buttons_enabled(
                True
            )  # Re-enable buttons on current panel
            return
        self.left_panel.set_buttons_enabled(True)

        if not result or (not result.images and not result.texts and not result.models):
            msg = f"No compatible files found in {Path(result.folder_path).name}."
            self.left_panel.set_message_text(msg)
            self.main_status_bar.showMessage(msg, 5000)
            nfo(
                "[UI] No compatible files found or result was empty for %s.",
                result.folder_path,
            )
            self.current_files_in_list = []
            self.left_panel.clear_file_list_display()
            return
        self.current_files_in_list = sorted(
            list(set(result.images + result.texts + result.models))
        )
        self.left_panel.clear_file_list_display()
        self.left_panel.add_items_to_file_list(self.current_files_in_list)
        self.left_panel.set_message_text(
            f"Loaded {len(self.current_files_in_list)} file(s) from {Path(result.folder_path).name}."
        )

        selected_item_set = False
        if result.file_to_select and self.left_panel.set_current_file_by_name(
            result.file_to_select
        ):
            nfo("[UI] Auto-selected file: %s", result.file_to_select)
            selected_item_set = True

        if (
            not selected_item_set
            and self.left_panel.get_files_list_widget().count() > 0
        ):
            self.left_panel.set_current_file_by_row(0)
            nfo("[UI] Auto-selected first file in the list.")
        elif not selected_item_set:
            self.clear_selection()  # Clear metadata/image if nothing could be auto-selected

    def sort_files_list(self):
        nfo("[UI] 'Sort Files' button clicked (from LeftPanelWidget).")
        if not hasattr(self, "left_panel"):
            return

        if self.current_files_in_list:
            list_widget = self.left_panel.get_files_list_widget()
            current_qt_item = list_widget.currentItem()
            current_selection_text = current_qt_item.text() if current_qt_item else None

            self.current_files_in_list.sort()
            self.left_panel.clear_file_list_display()
            self.left_panel.add_items_to_file_list(self.current_files_in_list)

            if current_selection_text:
                self.left_panel.set_current_file_by_name(current_selection_text)
            elif list_widget.count() > 0:
                self.left_panel.set_current_file_by_row(0)

            msg = f"Files sorted ({len(self.current_files_in_list)} items)."
            self.left_panel.set_message_text(msg)
            self.main_status_bar.showMessage(msg, 3000)
            nfo("[UI] Files list re-sorted and repopulated.")
        else:
            msg = "No files to sort."
            self.left_panel.set_message_text(msg)
            self.main_status_bar.showMessage(msg, 3000)
            nfo("[UI] %s", msg)

    def clear_selection(self):
        self.image_preview.clear()
        ph_positive_txt = EmptyField.PLACEHOLDER_POSITIVE.value
        ph_negative_txt = EmptyField.PLACEHOLDER_NEGATIVE.value
        ph_details_txt = EmptyField.PLACEHOLDER_DETAILS.value
        if hasattr(self, "positive_prompt_label"):
            self.positive_prompt_label.setText("Positive Prompt")
        if hasattr(self, "positive_prompt_box"):
            self.positive_prompt_box.clear()
            self.positive_prompt_box.setPlaceholderText(ph_positive_txt)
        if hasattr(self, "negative_prompt_label"):
            self.negative_prompt_label.setText("Negative Prompt")
        if hasattr(self, "negative_prompt_box"):
            self.negative_prompt_box.clear()
            self.negative_prompt_box.setPlaceholderText(ph_negative_txt)
        if hasattr(self, "generation_data_label"):
            self.generation_data_label.setText("Generation Details & Metadata")
        if hasattr(self, "generation_data_box"):
            self.generation_data_box.clear()
            self.generation_data_box.setPlaceholderText(ph_details_txt)

    def display_text_of(self, metadata_dict: dict[str, Any] | None) -> None:
        ph_positive_txt = EmptyField.PLACEHOLDER_POSITIVE.value
        ph_negative_txt = EmptyField.PLACEHOLDER_NEGATIVE.value
        ph_details_txt = EmptyField.PLACEHOLDER_DETAILS.value
        if hasattr(self, "positive_prompt_box"):
            self.positive_prompt_box.clear()
            self.positive_prompt_box.setPlaceholderText(ph_positive_txt)
        if hasattr(self, "negative_prompt_box"):
            self.negative_prompt_box.clear()
            self.negative_prompt_box.setPlaceholderText(ph_negative_txt)
        if hasattr(self, "generation_data_box"):
            self.generation_data_box.clear()
            self.generation_data_box.setPlaceholderText(ph_details_txt)

        placeholder_key = EmptyField.PLACEHOLDER.value
        is_error_or_empty = metadata_dict is None or (
            len(metadata_dict) == 1 and placeholder_key in metadata_dict
        )
        if is_error_or_empty:
            error_msg = "N/A"
            if metadata_dict and placeholder_key in metadata_dict:
                content = metadata_dict[placeholder_key]
                error_msg = (
                    content.get("Error", content.get("Info", "N/A"))
                    if isinstance(content, dict)
                    else str(content)
                )
            if hasattr(self, "generation_data_box"):
                self.generation_data_box.setText(f"Info/Error:\n{error_msg}")
            return
        if metadata_dict is None:
            return

        positive_prompt_text = ""
        prompt_section = metadata_dict.get(UpField.PROMPT.value, {})
        if isinstance(prompt_section, dict):
            positive_prompt_text = str(prompt_section.get("Positive", "")).strip()
        if hasattr(self, "positive_prompt_box"):
            self.positive_prompt_box.setText(positive_prompt_text)

        negative_prompt_text = ""
        if isinstance(prompt_section, dict):
            negative_prompt_text = str(prompt_section.get("Negative", "")).strip()
        if hasattr(self, "negative_prompt_box"):
            self.negative_prompt_box.setText(negative_prompt_text)

        details_parts: list[str] = []
        separators = [": ", "\n", "\n\n---\n\n", "", " & "]
        section_separator = "\n\n" + "═" * 30 + "\n\n"

        metadata_s = metadata_dict.get(UpField.METADATA.value)
        if isinstance(metadata_s, dict) and "Detected Tool" in metadata_s:
            details_parts.append(f"Detected Tool: {metadata_s['Detected Tool']}")

        gen_params_dict = metadata_dict.get(DownField.GENERATION_DATA.value, {})
        if isinstance(gen_params_dict, dict) and gen_params_dict:
            param_display_list = [
                f"{k}{separators[0]}{v}" for k, v in sorted(gen_params_dict.items())
            ]
            if param_display_list:
                details_parts.append(
                    f"Generation Parameters:\n{separators[1].join(param_display_list)}"
                )

        def append_unpacked_section(title: str, field_enum_member: Any):
            if (
                hasattr(field_enum_member, "value")
                and field_enum_member.value in metadata_dict
            ):
                unpacked = self.unpack_content_of(
                    metadata_dict, [field_enum_member], separators
                )
                display_text = unpacked.get("display", "").strip()
                if display_text:
                    details_parts.append(f"{title}:\n{display_text}")

        append_unpacked_section("EXIF Details", DownField.EXIF)
        append_unpacked_section("Tags (XMP/IPTC)", UpField.TAGS)

        model_header_content_parts: list[str] = []
        if (
            hasattr(DownField.JSON_DATA, "value")
            and DownField.JSON_DATA.value in metadata_dict
        ):
            unpacked = self.unpack_content_of(
                metadata_dict, [DownField.JSON_DATA], separators
            )
            if unpacked.get("display"):
                model_header_content_parts.append(
                    f"Model Header (JSON):\n{unpacked['display']}"
                )
        if (
            hasattr(DownField.TOML_DATA, "value")
            and DownField.TOML_DATA.value in metadata_dict
        ):
            unpacked = self.unpack_content_of(
                metadata_dict, [DownField.TOML_DATA], separators
            )
            if unpacked.get("display"):
                model_header_content_parts.append(
                    f"Model Header (TOML):\n{unpacked['display']}"
                )
        if model_header_content_parts:
            details_parts.append(separators[1].join(model_header_content_parts))

        if (
            hasattr(DownField.RAW_DATA, "value")
            and DownField.RAW_DATA.value in metadata_dict
        ):
            raw_content = str(metadata_dict[DownField.RAW_DATA.value])
            title = "Raw Data / Workflow"
            raw_strip = raw_content.strip()
            if raw_strip.startswith("{") and raw_strip.endswith("}"):
                title += " (JSON)"
            details_parts.append(f"{title}:\n{raw_content}")

        if hasattr(self, "generation_data_box"):
            self.generation_data_box.setText(
                section_separator.join(filter(None, details_parts))
            )

    def copy_metadata_to_clipboard(self):
        nfo("Copy All Metadata button clicked.")
        text_parts = []
        if (
            hasattr(self, "positive_prompt_box")
            and self.positive_prompt_box.toPlainText().strip()
        ):
            text_parts.append(
                f"{self.positive_prompt_label.text()}:\n{self.positive_prompt_box.toPlainText().strip()}"
            )
        if (
            hasattr(self, "negative_prompt_box")
            and self.negative_prompt_box.toPlainText().strip()
        ):
            text_parts.append(
                f"{self.negative_prompt_label.text()}:\n{self.negative_prompt_box.toPlainText().strip()}"
            )
        if (
            hasattr(self, "generation_data_box")
            and (gen_text := self.generation_data_box.toPlainText().strip())
            and not gen_text.startswith("Info/Error:")
        ):
            text_parts.append(f"{self.generation_data_label.text()}:\n{gen_text}")

        final_text = ("\n\n" + "═" * 20 + "\n\n").join(filter(None, text_parts)).strip()
        if final_text:
            QtGui.QGuiApplication.clipboard().setText(final_text)
            self.main_status_bar.showMessage(
                "Displayed metadata copied to clipboard!", 3000
            )
            nfo("Displayed metadata copied.")
        else:
            self.main_status_bar.showMessage(
                "No actual metadata displayed to copy.", 3000
            )
            nfo("No metadata content in display boxes for copying.")

    @debug_monitor
    def load_metadata(self, file_name: str) -> dict[str, Any] | None:
        if not self.current_folder or not file_name:
            nfo(
                "[UI] load_metadata: current_folder or file_name is empty. Current folder: '%s', File name: '%s'",
                self.current_folder,
                file_name,
            )
            return {
                EmptyField.PLACEHOLDER.value: {
                    "Error": "Cannot load metadata, folder or file name is missing."
                }
            }
        full_file_path = os.path.join(self.current_folder, file_name)
        nfo("[UI] load_metadata: Attempting to parse metadata for: %s", full_file_path)
        try:
            return parse_metadata(full_file_path)
        except Exception as e_parse_meta:
            nfo(
                "Error in parse_metadata for %s: %s",
                full_file_path,
                e_parse_meta,
                exc_info=True,
            )
        return None

    @debug_monitor
    def on_file_selected(
        self,
        current_item: Qw.QListWidgetItem | None,
        _previous_item: Qw.QListWidgetItem | None = None,
    ):
        if not current_item:  # current_item can be None if selection cleared
            self.clear_selection()
            if hasattr(self, "left_panel"):
                self.left_panel.set_message_text("No file selected.")
            self.main_status_bar.showMessage("No file selected.", 3000)
            return

        # If current_item is not None, it's a QListWidgetItem
        self.clear_selection()
        file_name = current_item.text()

        if hasattr(self, "left_panel"):
            # Update left panel message to show general folder status, not "Selected: ..."
            count = len(self.current_files_in_list)
            folder_name = (
                Path(self.current_folder).name
                if self.current_folder
                else "Unknown Folder"
            )
            self.left_panel.set_message_text(f"{count} file(s) in {folder_name}")

        self.main_status_bar.showMessage(
            f"Selected: {file_name}", 4000
        )  # Status bar for selection

        nfo("[UI] ON_FILE_SELECTED: current_item.text() (file_name) = '%s'", file_name)
        nfo("[UI] ON_FILE_SELECTED: self.current_folder = '%s'", self.current_folder)

        if not self.current_folder or not file_name:
            nfo("[UI] ON_FILE_SELECTED: current_folder or file_name is empty.")
            self.display_text_of(
                {
                    EmptyField.PLACEHOLDER.value: {
                        "Error": "Folder or file context missing."
                    }
                }
            )
            return

        full_file_path = os.path.join(self.current_folder, file_name)
        nfo("[UI] ON_FILE_SELECTED: Constructed full_file_path = '%s'", full_file_path)

        path_obj = Path(full_file_path)
        is_a_file = path_obj.is_file()
        nfo(
            "[UI] ON_FILE_SELECTED: Path('%s').is_file() result = %s",
            full_file_path,
            is_a_file,
        )

        file_suffix_lower = path_obj.suffix.lower()
        if not is_a_file:
            nfo(
                "[UI] ON_FILE_SELECTED: Path check FAILED for '%s'. Not processing as image.",
                full_file_path,
            )
        else:
            nfo(
                "[UI] ON_FILE_SELECTED: Path check PASSED for '%s'. Suffix: '%s'. Processing for image display.",
                full_file_path,
                file_suffix_lower,
            )
            is_image_displayed_this_time = False
            if hasattr(Ext, "IMAGE") and isinstance(Ext.IMAGE, list):
                for image_format_set in Ext.IMAGE:
                    if (
                        isinstance(image_format_set, set)
                        and file_suffix_lower in image_format_set
                    ):
                        nfo(
                            "[UI] ON_FILE_SELECTED: File '%s' suffix '%s' MATCHES image format set. Calling display_image_of.",
                            file_name,
                            file_suffix_lower,
                        )
                        self.display_image_of(full_file_path)
                        is_image_displayed_this_time = True
                        break
            if not is_image_displayed_this_time:
                nfo(
                    "[UI] ON_FILE_SELECTED: File '%s' (suffix '%s') did NOT match any image format set or Ext.IMAGE misconfigured.",
                    file_name,
                    file_suffix_lower,
                )

        metadata_dict = self.load_metadata(file_name)
        try:
            self.display_text_of(metadata_dict)
            if metadata_dict:
                if (
                    len(metadata_dict) == 1
                    and EmptyField.PLACEHOLDER.value in metadata_dict
                ):
                    nfo("No meaningful metadata or error for %s", file_name)
            else:
                nfo(
                    "No metadata returned for %s (load_metadata returned None)",
                    file_name,
                )
        except Exception as e_display:
            nfo(
                "Error displaying text metadata for %s: %s",
                file_name,
                e_display,
                exc_info=True,
            )
            self.display_text_of(None)

    def _format_single_section_data(
        self, section_data_item: Any, key_value_sep: str, item_sep: str
    ) -> list[str]:
        parts = []
        if isinstance(section_data_item, dict):
            for sub_key, sub_value in sorted(section_data_item.items()):
                if sub_value is not None:
                    if isinstance(sub_value, dict):
                        nested_parts = [
                            f"  {nk}{key_value_sep}{nv}"
                            for nk, nv in sorted(sub_value.items())
                            if nv is not None
                        ]
                        if nested_parts:
                            parts.append(
                                f"{sub_key}{key_value_sep.strip()}:\n{item_sep.join(nested_parts)}"
                            )
                    else:
                        parts.append(f"{sub_key}{key_value_sep}{sub_value!s}")
        elif isinstance(section_data_item, list):
            parts.extend(str(item) for item in section_data_item)
        elif section_data_item is not None:
            parts.append(str(section_data_item))
        return parts

    @debug_monitor
    def unpack_content_of(
        self,
        metadata_dict: dict[str, Any],
        labels_to_extract: list[Any],
        separators: list[str],
    ) -> defaultdict[str, str]:
        key_value_sep, item_sep, _, _, title_joiner = separators
        display_output = defaultdict(lambda: "")
        title_parts: list[str] = []
        all_formatted_section_texts: list[str] = []
        for section_key_enum_member in labels_to_extract:
            if not hasattr(section_key_enum_member, "value"):
                nfo(
                    "Warning: Item '%s' in labels_to_extract is not valid Enum. Skipping.",
                    section_key_enum_member,
                )
                continue
            section_key_label_str = section_key_enum_member.value
            section_data = metadata_dict.get(section_key_label_str)
            if section_data is None:
                continue
            title_name = getattr(section_key_enum_member, "name", section_key_label_str)
            title_parts.append(title_name.replace("_", " ").title())
            current_section_text_parts = self._format_single_section_data(
                section_data, key_value_sep, item_sep
            )
            if current_section_text_parts:
                all_formatted_section_texts.append(
                    item_sep.join(current_section_text_parts)
                )
        display_output["display"] = ("\n" + item_sep).join(all_formatted_section_texts)
        display_output["title"] = (
            title_joiner.join(title_parts) if title_parts else "Details"
        )
        return display_output

    def display_image_of(self, image_file_path: str) -> None:
        nfo(
            "[UI] display_image_of: Attempting to load pixmap for: '%s'",
            image_file_path,
        )
        try:
            pixmap = QtGui.QPixmap(image_file_path)
            if pixmap.isNull():
                nfo(
                    "[UI] display_image_of: QPixmap loaded as NULL for '%s'.",
                    image_file_path,
                )
                self.image_preview.setPixmap(None)
            else:
                nfo(
                    "[UI] display_image_of: QPixmap loaded successfully for '%s'. Size: %dx%d",
                    image_file_path,
                    pixmap.width(),
                    pixmap.height(),
                )
                self.image_preview.setPixmap(pixmap)
        except Exception as e_pixmap:
            nfo(
                "[UI] display_image_of: Exception creating/setting QPixmap for '%s': %s",
                image_file_path,
                e_pixmap,
                exc_info=True,
            )
            self.image_preview.setPixmap(None)

    def apply_theme(self, theme_name_xml: str, initial_load=False):
        if not QT_MATERIAL_AVAILABLE:
            nfo("Cannot apply theme, qt-material not available.")
            return
        app = QApplication.instance()
        if not app:
            return
        for theme_key, action in self.theme_actions.items():
            action.setChecked(theme_key == theme_name_xml)
        try:
            invert = theme_name_xml.startswith("dark_")
            apply_stylesheet(app, theme=theme_name_xml, invert_secondary=invert)
        except Exception as e_theme:
            nfo("Error applying theme %s: %s", theme_name_xml, e_theme, exc_info=True)
            return
        log_action = (
            "Initial theme loaded" if initial_load else "Theme applied and saved"
        )
        nfo("%s: %s", log_action, theme_name_xml)
        if not initial_load:
            self.settings.setValue("theme", theme_name_xml)

    def show_about_dialog(self):
        from PyQt6.QtWidgets import QMessageBox

        from dataset_tools import __version__ as p_version  # package_version

        version_text = (
            f"Version: {p_version}\n"
            if p_version and p_version != "0.0.0-dev"
            else "Version: N/A (dev)\n"
        )

        contrib = ["KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA (Lead Developer)"]
        contrib_txt = "\nContributors:\n" + "\n".join(f"- {c}" for c in contrib)
        lic_name = "GPL-3.0-or-later"
        lic_txt = f"License: {lic_name}\n(Refer to LICENSE file)\n\n"
        full_about_text = (
            f"<b>Dataset Viewer</b>\n{version_text}An ultralight metadata viewer.\n"
            f"Developed by KTISEOS NYX.{contrib_txt}\n\n{lic_txt}"
        )
        QMessageBox.about(self, "About Dataset Viewer", full_about_text)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            nfo("[UI] Drag enter accepted.")
        else:
            event.ignore()
            nfo("[UI] Drag enter ignored (not URLs).")

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls() and (urls := mime_data.urls()):
            dropped_path_qurl = urls[0]
            if dropped_path_qurl.isLocalFile():
                dropped_path_str = dropped_path_qurl.toLocalFile()
                nfo("[UI] Item dropped: %s", dropped_path_str)
                path_obj = Path(dropped_path_str)
                folder_to_load, file_to_select = "", None
                if path_obj.is_file():
                    folder_to_load, file_to_select = str(path_obj.parent), path_obj.name
                    nfo(
                        ("[UI] Dropped file. Loading folder: '%s'. Will select: '%s'"),
                        folder_to_load,
                        file_to_select,
                    )
                elif path_obj.is_dir():
                    folder_to_load = str(path_obj)
                    nfo("[UI] Dropped folder. Loading folder: '%s'", folder_to_load)
                if folder_to_load:
                    self.settings.setValue("lastFolderPath", folder_to_load)
                    self.load_files(
                        folder_to_load, file_to_select_after_load=file_to_select
                    )
                    event.acceptProposedAction()
                    return
        event.ignore()
        nfo("[UI] Drop event ignored (no local valid file/folder URL).")

    def closeEvent(self, event: QtGui.QCloseEvent):
        nfo("[UI] Close event triggered. Saving settings.")
        app_settings = self.settings  # Cache settings object
        if hasattr(self, "main_splitter"):
            app_settings.setValue("mainSplitterSizes", self.main_splitter.sizes())
        if hasattr(self, "metadata_image_splitter"):
            app_settings.setValue(
                "metaImageSplitterSizes", self.metadata_image_splitter.sizes()
            )
        if app_settings.value("rememberGeometry", True, type=bool):
            app_settings.setValue("geometry", self.saveGeometry())
        else:
            app_settings.remove("geometry")
        super().closeEvent(event)


if __name__ == "__main__":
    # Fallback logger for direct run, actual app uses logger from main.py
    def nfo_direct_run(*args):
        print("NFO (direct_run ui.py):", *args)

    nfo_direct_run("Dataset Tools UI (Direct Run) launching...")
    app = Qw.QApplication(sys.argv if hasattr(sys, "argv") else [])
    if QT_MATERIAL_AVAILABLE:
        try:
            cfg = QSettings("EarthAndDuskMedia", "DatasetViewer")
            theme_to_load = cfg.value("theme", "dark_teal.xml")
            apply_stylesheet(
                app,
                theme=theme_to_load,
                invert_secondary=theme_to_load.startswith("dark_"),
            )
            nfo_direct_run(f"Applied theme: {theme_to_load}")
        except Exception as e_theme_direct:
            nfo_direct_run(f"Could not apply theme for direct test: {e_theme_direct}")
    else:
        nfo_direct_run("qt-material not found, using default Qt style.")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
