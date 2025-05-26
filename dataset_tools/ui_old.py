# dataset_tools/ui.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT # Or GPL-3.0-or-later if you changed it

"""App UI"""

# pylint: disable=line-too-long
# pylint: disable=c-extension-no-member
# pylint: disable=attribute-defined-outside-init

import os
import sys
from pathlib import Path
from collections import defaultdict
from typing import Any

import PyQt6 # Or PySide6 if you switched for licensing
from PyQt6 import QtWidgets as Qw # Or PySide6.QtWidgets
from PyQt6 import QtCore, QtGui # Or PySide6.QtCore, PySide6.QtGui
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QDialogButtonBox, QLabel, QCheckBox, QApplication 

# Conditional import for qt_material for theme listing
try:
    from qt_material import list_themes, apply_stylesheet
    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False
    def list_themes(): return ["default_light.xml", "default_dark.xml"] # Fallback
    def apply_stylesheet(app, theme, invert_secondary=False): pass # No-op, added invert_secondary
    print("WARNING: qt-material library not found. Theme functionality will be limited.")


from dataset_tools.logger import debug_monitor
from dataset_tools.logger import info_monitor as nfo
from dataset_tools.metadata_parser import parse_metadata
from dataset_tools.widgets import FileLoader 
from dataset_tools.correct_types import EmptyField, UpField, DownField
from dataset_tools.correct_types import ExtensionType as Ext

# --- Custom ImageLabel for better rescaling ---
class ImageLabel(Qw.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QtGui.QPixmap()
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setSizePolicy(Qw.QSizePolicy.Policy.Ignored, Qw.QSizePolicy.Policy.Ignored)
        self.setWordWrap(True)
        self.setFrameShape(Qw.QFrame.Shape.StyledPanel)
        self.setText("Image Preview Area")

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
        super().setText("Image Preview Area")

    def _update_scaled_pixmap(self):
        if self._pixmap.isNull() or self.width() <= 10 or self.height() <= 10 :
            if self._pixmap.isNull() and not self.text():
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

# --- SettingsDialog Class ---
class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_theme_xml=""):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(400) # Increased width for more content

        self.parent_window = parent
        self.current_theme_on_open = current_theme_xml
        self.settings = QSettings("EarthAndDuskMedia", "DatasetViewer") # For convenience

        layout = QVBoxLayout(self)

        # --- Theme Selection ---
        theme_label = QLabel("<b>Display Theme:</b>")
        layout.addWidget(theme_label)
        self.theme_combo = QComboBox()
        if QT_MATERIAL_AVAILABLE:
            self.available_themes_xml = list_themes()
            for theme_xml_name in self.available_themes_xml:
                display_name = theme_xml_name.replace(".xml", "").replace("_", " ").title()
                self.theme_combo.addItem(display_name, theme_xml_name)
            if current_theme_xml in self.available_themes_xml:
                index = self.theme_combo.findData(current_theme_xml)
                if index >= 0: self.theme_combo.setCurrentIndex(index)
        else:
            self.theme_combo.addItem("Default (qt-material not found)")
            self.theme_combo.setEnabled(False)
        layout.addWidget(self.theme_combo)

        layout.addSpacing(15)

        # --- Window Size Settings ---
        size_label = QLabel("<b>Window Size:</b>")
        layout.addWidget(size_label)
        
        self.size_combo = QComboBox()
        self.size_presets = {
            # Display Name: (width, height) or None for "Remember"
            "Remember Last Size": None,
            "Default (1024x768)": (1024, 768),
            "Small (800x600)": (800, 600),
            "Medium (1280x900)": (1280, 900),
            "Large (1600x900)": (1600, 900), # Changed from 1920x1080 to be more common
        }
        for display_name in self.size_presets.keys():
            self.size_combo.addItem(display_name)
        
        # Set initial selection for size_combo
        remember_geom = self.settings.value("rememberGeometry", True, type=bool)
        if remember_geom:
            self.size_combo.setCurrentText("Remember Last Size")
        else:
            # If not remembering, try to find a saved preset or default
            saved_preset_name = self.settings.value("windowSizePreset", "Default (1024x768)")
            index = self.size_combo.findText(saved_preset_name)
            if index >=0: self.size_combo.setCurrentIndex(index)
            else: self.size_combo.setCurrentText("Default (1024x768)")
        layout.addWidget(self.size_combo)

        # self.remember_geometry_checkbox = QCheckBox("Remember window size and position on exit")
        # self.remember_geometry_checkbox.setChecked(self.settings.value("rememberGeometry", True, type=bool))
        # layout.addWidget(self.remember_geometry_checkbox) # Replaced by "Remember Last Size" in combo

        layout.addStretch(1)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel | 
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject_settings)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_all_settings)
        layout.addWidget(button_box)

    def apply_theme_settings(self):
        if not QT_MATERIAL_AVAILABLE: return
        selected_theme_xml = self.theme_combo.currentData()
        if selected_theme_xml and self.parent_window and hasattr(self.parent_window, 'apply_theme'):
            self.parent_window.apply_theme(selected_theme_xml, initial_load=False)

    def apply_window_settings(self):
        selected_size_text = self.size_combo.currentText()
        size_tuple = self.size_presets.get(selected_size_text)

        if selected_size_text == "Remember Last Size":
            self.settings.setValue("rememberGeometry", True)
            # No immediate resize, will use last saved geometry on next launch or if user resizes manually
            # Or, if a geometry was saved, apply it now? For now, just set the flag.
            last_geom = self.settings.value("geometry")
            if last_geom and self.parent_window and hasattr(self.parent_window, 'restoreGeometry'):
                 self.parent_window.restoreGeometry(last_geom) # Apply last saved size now
        elif size_tuple and self.parent_window and hasattr(self.parent_window, 'resize_window'):
            self.settings.setValue("rememberGeometry", False)
            self.settings.setValue("windowSizePreset", selected_size_text) # Save the chosen preset name
            self.parent_window.resize_window(size_tuple[0], size_tuple[1])
            # When a preset is chosen and "remember" is off, clear any old saved specific geometry
            self.settings.remove("geometry") 
        
    def apply_all_settings(self):
        self.apply_theme_settings()
        self.apply_window_settings()
        # current_theme_on_open is NOT updated by "Apply" button, only by "Ok" or when dialog opens

    def accept_settings(self):
        self.apply_all_settings()
        self.current_theme_on_open = self.theme_combo.currentData() # Lock in theme for revert logic
        self.accept()

    def reject_settings(self):
        # Revert theme if changed by "Apply" then "Cancel"
        if QT_MATERIAL_AVAILABLE and self.parent_window and hasattr(self.parent_window, 'apply_theme'):
            # This assumes currentData reflects what's shown, current_theme_on_open is the original
            if self.theme_combo.currentData() != self.current_theme_on_open:
                 self.parent_window.apply_theme(self.current_theme_on_open, initial_load=False)
        # Window size changes are harder to "revert" cleanly without storing more state.
        # Usually, cancel just closes.
        self.reject()


class MainWindow(Qw.QMainWindow):
    """Consolidated raw functions and behavior of window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dataset Viewer")
        self.setMinimumSize(800, 600) # Your desired absolute minimum

        self.settings = QSettings("EarthAndDuskMedia", "DatasetViewer")
        
        # --- Initial Geometry & Theme ---
        # Apply theme first, then geometry, as theme might affect size hints slightly
        saved_theme_name_xml = self.settings.value("theme", "dark_teal.xml")

        # Menu needs to be created before applying theme so actions can be checked
        self._setup_menus() # Moved menu setup to a helper

        if QT_MATERIAL_AVAILABLE:
            if saved_theme_name_xml and saved_theme_name_xml in self.theme_actions:
                self.apply_theme(saved_theme_name_xml, initial_load=True)
            elif "dark_teal.xml" in self.theme_actions:
                self.apply_theme("dark_teal.xml", initial_load=True)
            elif self.theme_actions: # Fallback to first available
                first_theme = next(iter(self.theme_actions.keys()))
                self.apply_theme(first_theme, initial_load=True)
        else: # No themes, apply OS default look
            pass


        remember_geom = self.settings.value("rememberGeometry", True, type=bool)
        saved_geom = self.settings.value("geometry")

        if remember_geom and saved_geom:
            self.restoreGeometry(saved_geom)
        else:
            # Default to a specific preset or your current self.setGeometry()
            default_preset_name = self.settings.value("windowSizePreset", "Default (1024x768)")
            # Define size_presets here too or pass from settings dialog logic if more complex
            size_presets_local = { 
                "Default (1024x768)": (1024, 768), "Small (800x600)": (800, 600) 
            } # simplified
            default_w, default_h = size_presets_local.get(default_preset_name, (1024,768))
            self.resize_window(default_w, default_h)
            # self.setGeometry(100, 100, default_w, default_h) # Alternative


        self._setup_ui_layout() # Moved main UI layout to a helper

        # --- Final initializations ---
        self.file_loader = None
        self.current_folder = self.settings.value("lastFolderPath", os.getcwd())
        self.clear_file_list()
        self.load_files(self.current_folder)

    def _setup_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        change_folder_action = QtGui.QAction("Change &Folder...", self)
        change_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(change_folder_action)
        file_menu.addSeparator()
        close_action = QtGui.QAction("&Close Window", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        view_menu = menu_bar.addMenu("&View")
        themes_menu = Qw.QMenu("&Themes", self)
        view_menu.addMenu(themes_menu)

        self.theme_actions = {}
        if QT_MATERIAL_AVAILABLE:
            theme_action_group = QtGui.QActionGroup(self)
            theme_action_group.setExclusive(True)
            available_themes_xml = list_themes()
            for theme_xml in available_themes_xml:
                display_name = theme_xml.replace(".xml", "").replace("_", " ").title()
                action = QtGui.QAction(display_name, self, checkable=True)
                action.setData(theme_xml)
                action.triggered.connect(self.on_theme_action_triggered)
                themes_menu.addAction(action)
                theme_action_group.addAction(action)
                self.theme_actions[theme_xml] = action
        else:
            no_themes_action = QtGui.QAction("qt-material not found", self)
            no_themes_action.setEnabled(False)
            themes_menu.addAction(no_themes_action)

        about_menu = menu_bar.addMenu("&Help")
        about_action = QtGui.QAction("&About Dataset Viewer...", self)
        about_action.triggered.connect(self.show_about_dialog)
        about_menu.addAction(about_action)

    def _setup_ui_layout(self):
        main_content_area_widget = Qw.QWidget()
        self.setCentralWidget(main_content_area_widget)
        
        overall_layout = Qw.QVBoxLayout(main_content_area_widget)
        overall_layout.setContentsMargins(5, 5, 5, 5)
        overall_layout.setSpacing(5)

        self.main_splitter = Qw.QSplitter(QtCore.Qt.Orientation.Horizontal)
        overall_layout.addWidget(self.main_splitter, 1)

        left_panel_widget = Qw.QWidget()
        left_layout = Qw.QVBoxLayout(left_panel_widget)
        self.current_folder_label = Qw.QLabel("Current Folder: None")
        self.current_folder_label.setWordWrap(True)
        left_layout.addWidget(self.current_folder_label)
        button_layout = Qw.QHBoxLayout()
        self.open_folder_button = Qw.QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_folder)
        button_layout.addWidget(self.open_folder_button)
        self.sort_button = Qw.QPushButton("Sort Files")
        self.sort_button.clicked.connect(self.sort_files_list)
        button_layout.addWidget(self.sort_button)
        self.copy_button = Qw.QPushButton("Copy Metadata")
        self.copy_button.clicked.connect(self.copy_metadata_to_clipboard)
        button_layout.addWidget(self.copy_button)
        left_layout.addLayout(button_layout)
        self.message_label = Qw.QLabel("Select a folder to view its contents.")
        self.message_label.setWordWrap(True)
        left_layout.addWidget(self.message_label)
        self.files_list = Qw.QListWidget()
        self.files_list.setSelectionMode(Qw.QAbstractItemView.SelectionMode.SingleSelection)
        self.files_list.currentItemChanged.connect(self.on_file_selected)
        self.files_list.setSizePolicy(Qw.QSizePolicy.Policy.Preferred, Qw.QSizePolicy.Policy.Expanding)
        left_layout.addWidget(self.files_list, 1)
        self.progress_bar = Qw.QProgressBar()
        self.progress_bar.hide()
        left_layout.addWidget(self.progress_bar)
        self.main_splitter.addWidget(left_panel_widget)

        right_panel_widget = Qw.QWidget()
        right_layout = Qw.QVBoxLayout(right_panel_widget)
        self.image_preview = ImageLabel()
        right_layout.addWidget(self.image_preview, stretch=3)
        self.top_separator = Qw.QLabel("Prompt Info")
        self.top_separator.setWordWrap(True)
        right_layout.addWidget(self.top_separator, stretch=0)
        self.upper_box = Qw.QTextEdit()
        self.upper_box.setReadOnly(True)
        self.upper_box.setSizePolicy(Qw.QSizePolicy.Policy.Expanding, Qw.QSizePolicy.Policy.Expanding)
        right_layout.addWidget(self.upper_box, stretch=2)
        self.mid_separator = Qw.QLabel("Generation Info")
        self.mid_separator.setWordWrap(True)
        right_layout.addWidget(self.mid_separator, stretch=0)
        self.lower_box = Qw.QTextEdit()
        self.lower_box.setReadOnly(True)
        self.lower_box.setSizePolicy(Qw.QSizePolicy.Policy.Expanding, Qw.QSizePolicy.Policy.Expanding)
        right_layout.addWidget(self.lower_box, stretch=2)
        self.main_splitter.addWidget(right_panel_widget)
        
        bottom_button_bar_widget = Qw.QWidget()
        bottom_button_layout = Qw.QHBoxLayout(bottom_button_bar_widget)
        bottom_button_layout.setContentsMargins(0,0,0,0)
        bottom_button_layout.addStretch(1)
        self.settings_button = Qw.QPushButton("Settings...")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        bottom_button_layout.addWidget(self.settings_button)
        self.exit_button = Qw.QPushButton("Exit Application")
        self.exit_button.clicked.connect(self.close)
        bottom_button_layout.addWidget(self.exit_button)
        overall_layout.addWidget(bottom_button_bar_widget, 0)

        # Restore splitter state AFTER widgets are added to it
        splitter_state = self.settings.value("splitterSizes")
        if hasattr(self, 'main_splitter') and splitter_state:
            self.main_splitter.restoreState(splitter_state)
        elif hasattr(self, 'main_splitter'):
            self.main_splitter.setSizes([self.width() // 3, self.width() * 2 // 3])


    def on_theme_action_triggered(self): # SLOT for theme menu actions
        action = self.sender()
        if action and isinstance(action, QtGui.QAction) and action.isChecked():
            theme_xml_from_action = action.data() # Get stored theme_name.xml
            if theme_xml_from_action:
                self.apply_theme(theme_xml_from_action, initial_load=False)

    def open_settings_dialog(self):
        current_theme_xml = ""
        if QT_MATERIAL_AVAILABLE:
            for theme_name, action in self.theme_actions.items():
                if action.isChecked():
                    current_theme_xml = theme_name
                    break
            if not current_theme_xml and self.theme_actions: # Fallback if none checked
                current_theme_xml = next(iter(self.theme_actions.keys()))
        
        dialog = SettingsDialog(self, current_theme_xml=current_theme_xml)
        dialog.exec() # Modal execution

    def resize_window(self, width, height):
        # Ensure window is not smaller than minimum size
        min_w, min_h = self.minimumSize().width(), self.minimumSize().height()
        new_width = max(width, min_w)
        new_height = max(height, min_h)

        # Clamp to screen dimensions if necessary
        if QApplication.instance(): # Check if app instance exists
            screen_geometry = QApplication.primaryScreen().availableGeometry()
            new_width = min(new_width, screen_geometry.width() - 20) # Some margin
            new_height = min(new_height, screen_geometry.height() - 50) # Some margin
        
        self.resize(new_width, new_height)
        # Optionally center after resize, if not restoring geometry which includes position
        # if QApplication.instance():
        #     self.move(QApplication.primaryScreen().availableGeometry().center() - self.rect().center())


    def closeEvent(self, event: QtGui.QCloseEvent):
        nfo("Saving application settings on close...")
        # self.settings is already defined in __init__
        if self.settings.value("rememberGeometry", True, type=bool):
            self.settings.setValue("geometry", self.saveGeometry())
        else:
            self.settings.remove("geometry") # If not remembering, clear saved specific geometry

        if hasattr(self, 'main_splitter'):
            self.settings.setValue("splitterSizes", self.main_splitter.saveState())
        
        self.settings.setValue("lastFolderPath", self.current_folder) # Also save current folder on explicit close
        nfo("Settings saved.")
        super().closeEvent(event)

    # ... (rest of your MainWindow methods: open_folder, clear_file_list, etc. as before) ...
    # Make sure they are correctly indented within the MainWindow class
    # /______________________________________________________________________________________________________________________ File Browser
    def open_folder(self):
        # self.settings is already defined in __init__
        last_folder = self.settings.value("lastFolderPath", os.getcwd())
        folder_path = Qw.QFileDialog.getExistingDirectory(self, "Select a folder", last_folder)
        if folder_path:
            self.settings.setValue("lastFolderPath", folder_path)
            self.load_files(folder_path)

    def clear_file_list(self):
        self.image_files = []
        self.text_files = []
        self.model_files = []

    def clear_selection(self):
        self.image_preview.clear()
        self.lower_box.clear()
        ph_gen = getattr(EmptyField, 'PLACEHOLDER_GEN', "Generation Info")
        self.mid_separator.setText(ph_gen)
        self.upper_box.clear()
        ph_prompt = getattr(EmptyField, 'PLACEHOLDER_PROMPT', "Prompt Info")
        self.top_separator.setText(ph_prompt)

    def load_files(self, folder_path):
        self.current_folder = folder_path
        # Display only the folder name, not the full path, for brevity
        self.current_folder_label.setText(f"Current Folder: {Path(folder_path).name}")
        self.message_label.setText("Loading files...")
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        if self.file_loader and self.file_loader.isRunning():
            try:
                self.file_loader.progress.disconnect(self.update_progress)
                self.file_loader.finished.disconnect(self.on_files_loaded)
            except TypeError: 
                pass
        self.file_loader = FileLoader(folder_path)
        self.file_loader.progress.connect(self.update_progress)
        self.file_loader.finished.connect(self.on_files_loaded)
        self.file_loader.start()

    def update_progress(self, progress: int):
        self.progress_bar.setValue(progress)

    def on_files_loaded(self, image_list: list, text_files: list, model_files: list, loaded_folder: str):
        if self.current_folder != loaded_folder:
            nfo(f"Ignoring loaded files from '{loaded_folder}' as current folder is '{self.current_folder}'")
            return
        self.image_files = sorted(image_list)
        self.text_files = sorted(text_files)
        self.model_files = sorted(model_files)
        
        self.message_label.setText(f"Loaded {len(self.image_files)} images, "
                                   f"{len(self.text_files)} text, "
                                   f"{len(self.model_files)} model files.")
        self.progress_bar.hide()

        self.files_list.clear()
        self.files_list.addItems(self.image_files)
        self.files_list.addItems(self.text_files)
        self.files_list.addItems(self.model_files)
        if self.files_list.count() > 0:
            self.files_list.setCurrentRow(0)

    # /______________________________________________________________________________________________________________________ UI Actions
    def sort_files_list(self):
        nfo("Sort Files button clicked. Sorting file list.")
        if self.files_list.count() == 0:
            nfo("File list is empty, nothing to sort.")
            self.message_label.setText("Nothing to sort.")
            return

        self.image_files.sort()
        self.text_files.sort()
        self.model_files.sort()

        self.files_list.clear()
        self.files_list.addItems(self.image_files)
        self.files_list.addItems(self.text_files)
        self.files_list.addItems(self.model_files)
        if self.files_list.count() > 0:
            self.files_list.setCurrentRow(0)

        self.message_label.setText(f"Sorted {self.files_list.count()} items.")
        nfo(f"Sorted {self.files_list.count()} items in the file list.")

    def copy_metadata_to_clipboard(self):
        nfo("Copy Metadata button clicked.")
        current_selection = self.files_list.currentItem()
        if not current_selection:
            self.message_label.setText("No file selected to copy metadata from.")
            nfo("No file selected.")
            return

        prompt_info_title = self.top_separator.text()
        prompt_info_content = self.upper_box.toPlainText().strip()
        generation_info_title = self.mid_separator.text()
        generation_info_content = self.lower_box.toPlainText().strip()
        
        ph_prompt = getattr(EmptyField, 'PLACEHOLDER_PROMPT', "Prompt Info")
        ph_gen = getattr(EmptyField, 'PLACEHOLDER_GEN', "Generation Info")
        ph_details = getattr(EmptyField, 'PLACEHOLDER_DETAILS', "N/A")

        is_prompt_empty = not prompt_info_content or prompt_info_content == ph_details or prompt_info_title == ph_prompt
        is_gen_empty = not generation_info_content or generation_info_content == ph_details or generation_info_title == ph_gen
        
        if is_prompt_empty and is_gen_empty:
            self.message_label.setText("No metadata displayed to copy.")
            nfo("No metadata content in text boxes.")
            return

        clipboard_text = [] # Build as a list of strings
        if not is_prompt_empty:
            clipboard_text.append(f"{prompt_info_title}:\n{prompt_info_content}")
        if not is_gen_empty:
             clipboard_text.append(f"{generation_info_title}:\n{generation_info_content}")
        
        final_clipboard_text = "\n\n".join(clipboard_text) # Join with double newline

        if final_clipboard_text:
            clipboard = QtGui.QGuiApplication.clipboard()
            clipboard.setText(final_clipboard_text)
            self.message_label.setText("Metadata copied to clipboard!")
            nfo("Metadata copied to clipboard.")
        else:
            self.message_label.setText("No actual metadata to copy.")
            nfo("No metadata found to copy after formatting.")

    # /______________________________________________________________________________________________________________________ Fetch & Display Metadata
    @debug_monitor
    def load_metadata(self, file_name: str) -> dict[str, Any] | None:
        metadata: dict[str, Any] | None = None
        full_file_path = os.path.join(self.current_folder, file_name)
        try:
            metadata = parse_metadata(full_file_path)
        except Exception as error_log: 
            nfo(f"Error during parse_metadata for {full_file_path}: {error_log}")
        return metadata

    @debug_monitor
    def on_file_selected(self, current_item: Qw.QListWidgetItem | None, previous_item: Qw.QListWidgetItem | None):
        if not current_item:
            self.clear_selection()
            self.message_label.setText("No file selected.")
            return

        file_name = current_item.text()
        self.message_label.setText(f"Selected: {file_name}")
        self.clear_selection()
        
        full_file_path = os.path.join(self.current_folder, file_name)

        is_image = False
        file_suffix_lower = Path(full_file_path).suffix.lower()
        for image_format_set in Ext.IMAGE:
            if file_suffix_lower in image_format_set:
                self.display_image_of(full_file_path)
                is_image = True
                break
        
        if not is_image:
            self.image_preview.setPixmap(None)
            self.image_preview.setText("No preview for this file type or image is invalid.")

        metadata_dict: dict[str, Any] | None = self.load_metadata(file_name)
        try:
            self.display_text_of(metadata_dict)
            if not metadata_dict or (len(metadata_dict) == 1 and EmptyField.PLACEHOLDER in metadata_dict):
                 nfo(f"No meaningful metadata found or error loading metadata for {file_name}")
        except Exception as e:
            nfo(f"Error displaying text metadata for {file_name}: {e}")
            self.display_text_of(None)

    @debug_monitor
    def unpack_content_of(self, metadata_dict: dict[str, Any], labels_to_extract: list[str], separators: list[str]) -> defaultdict[str, str]:
        key_value_sep, item_sep, block_sep, _, title_joiner = separators
        display_output = defaultdict(lambda: "") # Changed variable name
        title_parts: list[str] = []
        
        all_section_texts = []

        for section_key_label in labels_to_extract:
            section_data = metadata_dict.get(section_key_label)
            if section_data is not None:
                title_parts.append(section_key_label)
                current_section_text_parts = []
                if isinstance(section_data, dict):
                    for sub_key, sub_value in section_data.items():
                        if sub_value is not None:
                            if isinstance(sub_value, dict): # For nested dicts like SDXL prompts
                                nested_parts = [f"  {nk}{key_value_sep}{nv}" for nk, nv in sub_value.items() if nv is not None]
                                if nested_parts: # Only add if there's content
                                     current_section_text_parts.append(f"{sub_key}{key_value_sep.strip()}:\n" + item_sep.join(nested_parts))
                            else:
                                current_section_text_parts.append(f"{sub_key}{key_value_sep}{str(sub_value)}")
                elif isinstance(section_data, list):
                    current_section_text_parts.extend(str(item) for item in section_data)
                else:
                    current_section_text_parts.append(str(section_data))
                
                if current_section_text_parts:
                    all_section_texts.append(item_sep.join(current_section_text_parts))
        
        display_output["display"] = block_sep.join(all_section_texts) # Join collected sections with block_sep

        if title_parts:
            display_output["title"] = title_joiner.join(title_parts)
        else:
            display_output["title"] = "Info"
            
        return display_output

    def display_image_of(self, image_file_path: str) -> None:
        try:
            pixmap = QtGui.QPixmap(image_file_path)
            self.image_preview.setPixmap(pixmap) 
        except Exception as e:
            nfo(f"Error creating QPixmap for {image_file_path}: {e}")
            self.image_preview.setPixmap(None)

    def display_text_of(self, metadata_dict: dict[str, Any] | None) -> None:
        ph_prompt = getattr(EmptyField, 'PLACEHOLDER_PROMPT', "Prompt Info")
        ph_gen = getattr(EmptyField, 'PLACEHOLDER_GEN', "Generation Info")
        ph_details = getattr(EmptyField, 'PLACEHOLDER_DETAILS', "N/A")

        if metadata_dict and EmptyField.PLACEHOLDER not in metadata_dict:
            separators = [": ", "\n", "\n\n", "", " & "]

            metadata_display_upper = self.unpack_content_of(metadata_dict, UpField.LABELS, separators)
            self.top_separator.setText(metadata_display_upper.get("title", ph_prompt).strip(" & "))
            self.upper_box.setText(metadata_display_upper.get("display", "").strip())

            metadata_display_lower = self.unpack_content_of(metadata_dict, DownField.LABELS, separators)
            self.mid_separator.setText(metadata_display_lower.get("title", ph_gen).strip(" & "))
            self.lower_box.setText(metadata_display_lower.get("display", "").strip())
        else:
            self.top_separator.setText(ph_prompt)
            self.mid_separator.setText(ph_gen)
            error_msg_to_display = ph_details
            if metadata_dict and EmptyField.PLACEHOLDER in metadata_dict:
                placeholder_content = metadata_dict[EmptyField.PLACEHOLDER]
                if isinstance(placeholder_content, dict) and "Error" in placeholder_content:
                    error_msg_to_display = f"Error loading metadata:\n{placeholder_content['Error']}"
                elif isinstance(placeholder_content, dict) and "Info" in placeholder_content:
                     error_msg_to_display = placeholder_content["Info"]
                elif isinstance(placeholder_content, str): # If placeholder itself is a string
                     error_msg_to_display = placeholder_content

            self.upper_box.setText(error_msg_to_display)
            self.lower_box.setText("") # Keep lower box clear or show different placeholder for errors

    def apply_theme(self, theme_name_xml: str, initial_load=False):
        if not QT_MATERIAL_AVAILABLE:
            nfo("Cannot apply theme, qt-material not available.")
            return
        app = QApplication.instance()
        if not app: return

        for theme_key, action in self.theme_actions.items():
            action.setChecked(theme_key == theme_name_xml)
        
        try:
            # Example: some themes might look better with invert_secondary
            invert = theme_name_xml in ("dark_teal.xml", "dark_blue.xml") 
            apply_stylesheet(app, theme=theme_name_xml, invert_secondary=invert)
        except Exception as e:
            nfo(f"Error applying theme {theme_name_xml}: {e}")
            return

        if not initial_load:
            nfo(f"Theme applied and saved: {theme_name_xml}")
            self.settings.setValue("theme", theme_name_xml) # Use self.settings
        else:
            nfo(f"Initial theme loaded: {theme_name_xml}")

    def show_about_dialog(self):
        from PyQt6.QtWidgets import QMessageBox 
        version_text = "" 
        try:
            # Try importing from a dedicated version file first
            from dataset_tools.version import __version__ as file_version 
            version_text = f"Version: {file_version}\n"
        except ImportError:
            # Fallback to __version__ from package __init__
            try:
                from dataset_tools import __version__ as pkg_version
                if pkg_version and pkg_version != "0.0.0-dev": # Check if it's a meaningful version
                    version_text = f"Version: {pkg_version}\n"
                else:
                    nfo("Placeholder package version found ('0.0.0-dev').")
            except ImportError:
                 nfo("Version information not found.")
                 pass 

        contributors_list = ["KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA (Lead Developer)"]
        contributors_text = "\nContributors:\n" + "\n".join(f"- {c}" for c in contributors_list)
        license_name = "GPL-3.0-or-later" # Assuming you changed to GPL
        license_text = f"License: {license_name}\n(Refer to LICENSE file for full text)\n\n" 
        
        about_text = (
            f"<b>Dataset Viewer</b>\n"
            f"{version_text}"
            f"An ultralight metadata viewer and dataset handler.\n\n"
            f"Developed by KTISEOS NYX of EARTH & DUSK MEDIA.\n" 
            f"{contributors_text}\n\n"
            f"{license_text}"
        )
        QMessageBox.about(self, "About Dataset Viewer", about_text)

if __name__ == "__main__":
    app = Qw.QApplication(sys.argv if hasattr(sys, 'argv') else [])
    if QT_MATERIAL_AVAILABLE:
        try:
            # Attempt to load saved theme or default for direct ui.py run
            temp_settings = QSettings("EarthAndDuskMedia", "DatasetViewer")
            theme_to_load = temp_settings.value("theme", "dark_teal.xml")
            apply_stylesheet(app, theme=theme_to_load, invert_secondary=(theme_to_load=="dark_teal.xml"))
        except Exception as e:
            print(f"Could not apply theme for direct ui.py test: {e}")
    window = MainWindow()
    window.show()
    if hasattr(app, 'exec'):
        sys.exit(app.exec())
