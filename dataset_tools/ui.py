# dataset_tools/ui.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""App UI for Dataset-Tools"""

import os
import sys
from pathlib import Path
from collections import defaultdict
from typing import Any, List as TypingList # Import List for type hinting

import PyQt6
from PyQt6 import QtWidgets as Qw
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QDialogButtonBox, QLabel, QCheckBox, QApplication

try:
    from qt_material import list_themes, apply_stylesheet
    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False
    def list_themes(): return ["default_light.xml", "default_dark.xml"]
    def apply_stylesheet(app, theme, invert_secondary=False): pass
    print("WARNING: qt-material library not found. Theme functionality will be limited.")


from .logger import debug_monitor, info_monitor as nfo # Assuming logger.py is in the same package or sys.path
from .metadata_parser import parse_metadata # Your main parsing function
from .widgets import FileLoader # Assuming FileLoader is in widgets.py
from .correct_types import EmptyField, UpField, DownField # Import your Enums
from .correct_types import ExtensionType as Ext # If Ext is used, ensure it's defined

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
        if self._pixmap.isNull() or self.width() <= 10 or self.height() <= 10 :
            if self._pixmap.isNull() and (not self.text() or self.text() == ""):
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

# --- SettingsDialog Class (No changes needed here based on Enum fix) ---
class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_theme_xml=""):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(400)
        self.parent_window = parent
        self.current_theme_on_open = current_theme_xml
        self.settings = QSettings("EarthAndDuskMedia", "DatasetViewer")
        layout = QVBoxLayout(self)
        theme_label = QLabel("<b>Display Theme:</b>"); layout.addWidget(theme_label)
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
            self.theme_combo.addItem("Default (qt-material not found)"); self.theme_combo.setEnabled(False)
        layout.addWidget(self.theme_combo)
        layout.addSpacing(15)
        size_label = QLabel("<b>Window Size:</b>"); layout.addWidget(size_label)
        self.size_combo = QComboBox()
        self.size_presets = {
            "Remember Last Size": None, "Default (1024x768)": (1024, 768),
            "Small (800x600)": (800, 600), "Medium (1280x900)": (1280, 900),
            "Large (1600x900)": (1600, 900),
        }
        for display_name in self.size_presets.keys(): self.size_combo.addItem(display_name)
        remember_geom = self.settings.value("rememberGeometry", True, type=bool)
        if remember_geom: self.size_combo.setCurrentText("Remember Last Size")
        else:
            saved_preset_name = self.settings.value("windowSizePreset", "Default (1024x768)")
            index = self.size_combo.findText(saved_preset_name)
            if index >=0: self.size_combo.setCurrentIndex(index)
            else: self.size_combo.setCurrentText("Default (1024x768)")
        layout.addWidget(self.size_combo)
        layout.addStretch(1)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Apply)
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
            last_geom = self.settings.value("geometry")
            if last_geom and self.parent_window and hasattr(self.parent_window, 'restoreGeometry'):
                 self.parent_window.restoreGeometry(last_geom)
        elif size_tuple and self.parent_window and hasattr(self.parent_window, 'resize_window'):
            self.settings.setValue("rememberGeometry", False)
            self.settings.setValue("windowSizePreset", selected_size_text)
            self.parent_window.resize_window(size_tuple[0], size_tuple[1])
            self.settings.remove("geometry")

    def apply_all_settings(self): self.apply_theme_settings(); self.apply_window_settings()
    def accept_settings(self): self.apply_all_settings(); self.current_theme_on_open = self.theme_combo.currentData(); self.accept()
    def reject_settings(self):
        if QT_MATERIAL_AVAILABLE and self.parent_window and hasattr(self.parent_window, 'apply_theme'):
            if self.theme_combo.currentData() != self.current_theme_on_open:
                 self.parent_window.apply_theme(self.current_theme_on_open, initial_load=False)
        self.reject()


class MainWindow(Qw.QMainWindow):
    """Consolidated raw functions and behavior of window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dataset Viewer")
        self.setMinimumSize(800, 600)
        self.settings = QSettings("EarthAndDuskMedia", "DatasetViewer")
        self.setAcceptDrops(True)

        saved_theme_name_xml = self.settings.value("theme", "dark_teal.xml")
        self._setup_menus()
        if QT_MATERIAL_AVAILABLE:
            if saved_theme_name_xml and saved_theme_name_xml in self.theme_actions:
                self.apply_theme(saved_theme_name_xml, initial_load=True)
            elif "dark_teal.xml" in self.theme_actions: self.apply_theme("dark_teal.xml", initial_load=True)
            elif self.theme_actions: self.apply_theme(next(iter(self.theme_actions.keys())), initial_load=True)

        remember_geom = self.settings.value("rememberGeometry", True, type=bool)
        saved_geom = self.settings.value("geometry")
        if remember_geom and saved_geom: self.restoreGeometry(saved_geom)
        else:
            default_preset_name = self.settings.value("windowSizePreset", "Default (1024x768)")
            size_presets_local = {"Default (1024x768)": (1024, 768), "Small (800x600)": (800, 600)} # Example
            default_w, default_h = size_presets_local.get(default_preset_name, (1024,768))
            self.resize_window(default_w, default_h)

        self._setup_ui_layout()
        self.file_loader = None
        self.current_folder = self.settings.value("lastFolderPath", os.getcwd())
        self.clear_file_list()
        self.load_files(self.current_folder)

    def _setup_menus(self):
        menu_bar = self.menuBar(); file_menu = menu_bar.addMenu("&File")
        change_folder_action = QtGui.QAction("Change &Folder...", self); change_folder_action.triggered.connect(self.open_folder); file_menu.addAction(change_folder_action)
        file_menu.addSeparator()
        close_action = QtGui.QAction("&Close Window", self); close_action.triggered.connect(self.close); file_menu.addAction(close_action)
        view_menu = menu_bar.addMenu("&View"); themes_menu = Qw.QMenu("&Themes", self); view_menu.addMenu(themes_menu)
        self.theme_actions = {}
        if QT_MATERIAL_AVAILABLE:
            theme_action_group = QtGui.QActionGroup(self); theme_action_group.setExclusive(True)
            available_themes_xml = list_themes()
            for theme_xml in available_themes_xml:
                display_name = theme_xml.replace(".xml", "").replace("_", " ").title()
                action = QtGui.QAction(display_name, self, checkable=True); action.setData(theme_xml)
                action.triggered.connect(self.on_theme_action_triggered); themes_menu.addAction(action)
                theme_action_group.addAction(action); self.theme_actions[theme_xml] = action
        else:
            no_themes_action = QtGui.QAction("qt-material not found", self); no_themes_action.setEnabled(False); themes_menu.addAction(no_themes_action)
        about_menu = menu_bar.addMenu("&Help"); about_action = QtGui.QAction("&About Dataset Viewer...", self)
        about_action.triggered.connect(self.show_about_dialog); about_menu.addAction(about_action)

    def _setup_ui_layout(self):
        main_content_area_widget = Qw.QWidget(); self.setCentralWidget(main_content_area_widget)
        overall_layout = Qw.QVBoxLayout(main_content_area_widget); overall_layout.setContentsMargins(5,5,5,5); overall_layout.setSpacing(5)
        self.main_splitter = Qw.QSplitter(QtCore.Qt.Orientation.Horizontal); overall_layout.addWidget(self.main_splitter, 1)
        left_panel_widget = Qw.QWidget(); left_layout = Qw.QVBoxLayout(left_panel_widget)
        self.current_folder_label = Qw.QLabel("Current Folder: None"); self.current_folder_label.setWordWrap(True); left_layout.addWidget(self.current_folder_label)
        button_layout = Qw.QHBoxLayout()
        self.open_folder_button = Qw.QPushButton("Open Folder"); self.open_folder_button.clicked.connect(self.open_folder); button_layout.addWidget(self.open_folder_button)
        self.sort_button = Qw.QPushButton("Sort Files"); self.sort_button.clicked.connect(self.sort_files_list); button_layout.addWidget(self.sort_button)
        self.copy_button = Qw.QPushButton("Copy Metadata"); self.copy_button.clicked.connect(self.copy_metadata_to_clipboard); button_layout.addWidget(self.copy_button)
        left_layout.addLayout(button_layout)
        self.message_label = Qw.QLabel("Select a folder to view its contents."); self.message_label.setWordWrap(True); left_layout.addWidget(self.message_label)
        self.files_list = Qw.QListWidget(); self.files_list.setSelectionMode(Qw.QAbstractItemView.SelectionMode.SingleSelection)
        self.files_list.currentItemChanged.connect(self.on_file_selected)
        self.files_list.setSizePolicy(Qw.QSizePolicy.Policy.Preferred, Qw.QSizePolicy.Policy.Expanding); left_layout.addWidget(self.files_list, 1)
        self.progress_bar = Qw.QProgressBar(); self.progress_bar.hide(); left_layout.addWidget(self.progress_bar)
        self.main_splitter.addWidget(left_panel_widget)
        right_panel_widget = Qw.QWidget(); right_layout = Qw.QVBoxLayout(right_panel_widget)
        self.image_preview = ImageLabel(); right_layout.addWidget(self.image_preview, stretch=3)
        self.top_separator = Qw.QLabel("Prompt Info"); self.top_separator.setWordWrap(True); right_layout.addWidget(self.top_separator, stretch=0)
        self.upper_box = Qw.QTextEdit(); self.upper_box.setReadOnly(True); self.upper_box.setSizePolicy(Qw.QSizePolicy.Policy.Expanding, Qw.QSizePolicy.Policy.Expanding); right_layout.addWidget(self.upper_box, stretch=2)
        self.mid_separator = Qw.QLabel("Generation Info"); self.mid_separator.setWordWrap(True); right_layout.addWidget(self.mid_separator, stretch=0)
        self.lower_box = Qw.QTextEdit(); self.lower_box.setReadOnly(True); self.lower_box.setSizePolicy(Qw.QSizePolicy.Policy.Expanding, Qw.QSizePolicy.Policy.Expanding); right_layout.addWidget(self.lower_box, stretch=2)
        self.main_splitter.addWidget(right_panel_widget)
        bottom_button_bar_widget = Qw.QWidget(); bottom_button_layout = Qw.QHBoxLayout(bottom_button_bar_widget)
        bottom_button_layout.setContentsMargins(0,0,0,0); bottom_button_layout.addStretch(1)
        self.settings_button = Qw.QPushButton("Settings..."); self.settings_button.clicked.connect(self.open_settings_dialog); bottom_button_layout.addWidget(self.settings_button)
        self.exit_button = Qw.QPushButton("Exit Application"); self.exit_button.clicked.connect(self.close); bottom_button_layout.addWidget(self.exit_button)
        overall_layout.addWidget(bottom_button_bar_widget, 0)
        splitter_state = self.settings.value("splitterSizes")
        if hasattr(self, 'main_splitter') and splitter_state: self.main_splitter.restoreState(splitter_state)
        elif hasattr(self, 'main_splitter'): self.main_splitter.setSizes([self.width() // 3, self.width() * 2 // 3])

    def on_theme_action_triggered(self):
        action = self.sender()
        if action and isinstance(action, QtGui.QAction) and action.isChecked():
            theme_xml_from_action = action.data()
            if theme_xml_from_action: self.apply_theme(theme_xml_from_action, initial_load=False)

    def open_settings_dialog(self):
        current_theme_xml = "";
        if QT_MATERIAL_AVAILABLE:
            for theme_name, action in self.theme_actions.items():
                if action.isChecked(): current_theme_xml = theme_name; break
            if not current_theme_xml and self.theme_actions: current_theme_xml = next(iter(self.theme_actions.keys()))
        dialog = SettingsDialog(self, current_theme_xml=current_theme_xml); dialog.exec()

    def resize_window(self, width, height):
        min_w, min_h = self.minimumSize().width(), self.minimumSize().height()
        new_width = max(width, min_w); new_height = max(height, min_h)
        if QApplication.instance():
            screen_geometry = QApplication.primaryScreen().availableGeometry()
            new_width = min(new_width, screen_geometry.width() - 20)
            new_height = min(new_height, screen_geometry.height() - 50)
        self.resize(new_width, new_height)

    def closeEvent(self, event: QtGui.QCloseEvent):
        nfo("Saving application settings on close...")
        if self.settings.value("rememberGeometry", True, type=bool): self.settings.setValue("geometry", self.saveGeometry())
        else: self.settings.remove("geometry")
        if hasattr(self, 'main_splitter'): self.settings.setValue("splitterSizes", self.main_splitter.saveState())
        self.settings.setValue("lastFolderPath", self.current_folder)
        nfo("Settings saved.")
        super().closeEvent(event)

    def open_folder(self):
        last_folder = self.settings.value("lastFolderPath", os.getcwd())
        folder_path = Qw.QFileDialog.getExistingDirectory(self, "Select a folder", last_folder)
        if folder_path:
            self.settings.setValue("lastFolderPath", folder_path)
            self.load_files(folder_path)

    def clear_file_list(self):
        self.image_files = []; self.text_files = []; self.model_files = []

    def clear_selection(self):
        self.image_preview.clear()
        # Use getattr for placeholders in case EmptyField definition changes or attribute is missing
        # Also ensure EmptyField.PLACEHOLDER_GEN.value is used if they are enums
        ph_gen_val = EmptyField.PLACEHOLDER.value # Default if specific not found
        if hasattr(EmptyField, 'PLACEHOLDER_GEN') and hasattr(EmptyField.PLACEHOLDER_GEN, 'value'):
            ph_gen_val = EmptyField.PLACEHOLDER_GEN.value
        elif hasattr(EmptyField, 'PLACEHOLDER_GEN'): # If it's a direct string attribute
            ph_gen_val = EmptyField.PLACEHOLDER_GEN
        self.lower_box.clear(); self.mid_separator.setText(getattr(EmptyField, '_fallback_gen_placeholder_text', ph_gen_val))


        ph_prompt_val = EmptyField.PLACEHOLDER.value # Default
        if hasattr(EmptyField, 'PLACEHOLDER_PROMPT') and hasattr(EmptyField.PLACEHOLDER_PROMPT, 'value'):
            ph_prompt_val = EmptyField.PLACEHOLDER_PROMPT.value
        elif hasattr(EmptyField, 'PLACEHOLDER_PROMPT'):
            ph_prompt_val = EmptyField.PLACEHOLDER_PROMPT

        self.upper_box.clear(); self.top_separator.setText(getattr(EmptyField, '_fallback_prompt_placeholder_text', ph_prompt_val))


    def load_files(self, folder_path: str, file_to_select_after_load: str | None = None):
        self.current_folder = folder_path
        self.current_folder_label.setText(f"Current Folder: {Path(folder_path).name}")
        self.message_label.setText("Loading files...")
        self.progress_bar.setValue(0); self.progress_bar.show()
        if self.file_loader and self.file_loader.isRunning():
            try:
                self.file_loader.progress.disconnect(self.update_progress)
                self.file_loader.finished.disconnect(self.on_files_loaded)
            except TypeError: pass
        self.file_loader = FileLoader(folder_path, file_to_select_after_load)
        self.file_loader.progress.connect(self.update_progress)
        self.file_loader.finished.connect(self.on_files_loaded)
        self.file_loader.start()

    def update_progress(self, progress: int): self.progress_bar.setValue(progress)

    def on_files_loaded(self, image_list: list, text_files: list, model_files: list, loaded_folder: str, file_to_select: str | None = None):
        if self.current_folder != loaded_folder:
            nfo(f"Ignoring loaded files from '{loaded_folder}' as current folder changed to '{self.current_folder}'")
            return
        self.image_files = sorted(image_list); self.text_files = sorted(text_files); self.model_files = sorted(model_files)
        self.message_label.setText(f"Loaded {len(self.image_files)} images, {len(self.text_files)} text, {len(self.model_files)} model files.")
        self.progress_bar.hide()
        self.files_list.clear()
        self.files_list.addItems(self.image_files); self.files_list.addItems(self.text_files); self.files_list.addItems(self.model_files)

        if file_to_select:
            items = self.files_list.findItems(file_to_select, QtCore.Qt.MatchFlag.MatchExactly)
            if items:
                self.files_list.setCurrentItem(items[0])
                nfo(f"[UI] Auto-selected dropped/specified file: {file_to_select}")
            elif self.files_list.count() > 0:
                self.files_list.setCurrentRow(0)
        elif self.files_list.count() > 0:
            self.files_list.setCurrentRow(0)

    def sort_files_list(self):
        nfo("Sort Files button clicked. Sorting file list.")
        if self.files_list.count() == 0: nfo("File list is empty, nothing to sort."); self.message_label.setText("Nothing to sort."); return
        self.image_files.sort(); self.text_files.sort(); self.model_files.sort()
        self.files_list.clear(); self.files_list.addItems(self.image_files); self.files_list.addItems(self.text_files); self.files_list.addItems(self.model_files)
        if self.files_list.count() > 0: self.files_list.setCurrentRow(0)
        self.message_label.setText(f"Sorted {self.files_list.count()} items."); nfo(f"Sorted {self.files_list.count()} items in the file list.")

    def copy_metadata_to_clipboard(self):
        nfo("Copy Metadata button clicked."); current_selection = self.files_list.currentItem()
        if not current_selection: self.message_label.setText("No file selected to copy metadata from."); nfo("No file selected."); return
        prompt_info_title = self.top_separator.text(); prompt_info_content = self.upper_box.toPlainText().strip()
        generation_info_title = self.mid_separator.text(); generation_info_content = self.lower_box.toPlainText().strip()

        # Assuming EmptyField.PLACEHOLDER.value, etc. will be the actual string values
        # Default to a generic string if specific placeholders aren't defined or .value fails
        ph_prompt_default = "Prompt Info"
        ph_gen_default = "Generation Info"
        ph_details_default = "N/A"

        try: ph_prompt = EmptyField.PLACEHOLDER_PROMPT.value if hasattr(EmptyField, 'PLACEHOLDER_PROMPT') else ph_prompt_default
        except AttributeError: ph_prompt = getattr(EmptyField, 'PLACEHOLDER_PROMPT', ph_prompt_default)

        try: ph_gen = EmptyField.PLACEHOLDER_GEN.value if hasattr(EmptyField, 'PLACEHOLDER_GEN') else ph_gen_default
        except AttributeError: ph_gen = getattr(EmptyField, 'PLACEHOLDER_GEN', ph_gen_default)
        
        try: ph_details = EmptyField.PLACEHOLDER_DETAILS.value if hasattr(EmptyField, 'PLACEHOLDER_DETAILS') else ph_details_default
        except AttributeError: ph_details = getattr(EmptyField, 'PLACEHOLDER_DETAILS', ph_details_default)


        is_prompt_empty = not prompt_info_content or prompt_info_content == ph_details or prompt_info_title == ph_prompt
        is_gen_empty = not generation_info_content or generation_info_content == ph_details or generation_info_title == ph_gen
        if is_prompt_empty and is_gen_empty: self.message_label.setText("No metadata displayed to copy."); nfo("No metadata content in text boxes."); return
        clipboard_text = [];
        if not is_prompt_empty: clipboard_text.append(f"{prompt_info_title}:\n{prompt_info_content}")
        if not is_gen_empty: clipboard_text.append(f"{generation_info_title}:\n{generation_info_content}")
        final_clipboard_text = "\n\n".join(clipboard_text)
        if final_clipboard_text:
            QtGui.QGuiApplication.clipboard().setText(final_clipboard_text)
            self.message_label.setText("Metadata copied to clipboard!"); nfo("Metadata copied to clipboard.")
        else: self.message_label.setText("No actual metadata to copy."); nfo("No metadata found to copy after formatting.")

    @debug_monitor
    def load_metadata(self, file_name: str) -> dict[str, Any] | None:
        metadata: dict[str, Any] | None = None; full_file_path = os.path.join(self.current_folder, file_name)
        try: metadata = parse_metadata(full_file_path)
        except Exception as error_log: nfo(f"Error in parse_metadata for {full_file_path}: {error_log}") # Log full error
        return metadata

    @debug_monitor
    def on_file_selected(self, current_item: Qw.QListWidgetItem | None, previous_item: Qw.QListWidgetItem | None):
        if not current_item: self.clear_selection(); self.message_label.setText("No file selected."); return
        file_name = current_item.text(); self.message_label.setText(f"Selected: {file_name}"); self.clear_selection()
        full_file_path = os.path.join(self.current_folder, file_name)
        is_image = False; file_suffix_lower = Path(full_file_path).suffix.lower()

        if hasattr(Ext, 'IMAGE') and isinstance(Ext.IMAGE, list): # Check if Ext.IMAGE is a list of sets
            for image_format_set in Ext.IMAGE:
                if isinstance(image_format_set, set) and file_suffix_lower in image_format_set:
                    self.display_image_of(full_file_path); is_image = True; break
        if not is_image: self.image_preview.setPixmap(None); self.image_preview.setText("No preview for this file type or image is invalid.")

        metadata_dict: dict[str, Any] | None = self.load_metadata(file_name)
        try:
            self.display_text_of(metadata_dict)
            # --- MODIFIED: Use .value for EmptyField.PLACEHOLDER if it's an Enum ---
            placeholder_key = EmptyField.PLACEHOLDER.value if hasattr(EmptyField.PLACEHOLDER, 'value') else EmptyField.PLACEHOLDER
            if not metadata_dict or (len(metadata_dict) == 1 and placeholder_key in metadata_dict):
                 nfo(f"No meaningful metadata or error for {file_name}")
        except Exception as e: nfo(f"Error displaying text metadata for {file_name}: {e}"); self.display_text_of(None) # Pass None to display_text_of

    @debug_monitor
    def unpack_content_of(self, metadata_dict: dict[str, Any], labels_to_extract: TypingList[Any], separators: list[str]) -> defaultdict[str, str]:
        # labels_to_extract should be a list of Enum members (e.g., from UpField.get_ordered_labels())
        key_value_sep, item_sep, block_sep, _, title_joiner = separators
        display_output = defaultdict(lambda: ""); title_parts: TypingList[str] = []; all_section_texts = []

        for section_key_enum_member in labels_to_extract: # labels_to_extract is now a list of Enum members
            if not hasattr(section_key_enum_member, 'value'):
                nfo(f"Warning: Item '{section_key_enum_member}' in labels_to_extract is not a valid Enum member with a .value attribute. Skipping.")
                continue
            section_key_label_str = section_key_enum_member.value # Use .value for the string key
            section_data = metadata_dict.get(section_key_label_str)

            if section_data is not None:
                # Use Enum member's name for title parts for better readability, or value if preferred
                title_parts.append(section_key_enum_member.name.replace("_", " ").title())
                current_section_text_parts = []
                if isinstance(section_data, dict):
                    for sub_key, sub_value in section_data.items():
                        if sub_value is not None:
                            if isinstance(sub_value, dict):
                                nested_parts = [f"  {nk}{key_value_sep}{nv}" for nk, nv in sub_value.items() if nv is not None]
                                if nested_parts: current_section_text_parts.append(f"{sub_key}{key_value_sep.strip()}:\n" + item_sep.join(nested_parts))
                            else: current_section_text_parts.append(f"{sub_key}{key_value_sep}{str(sub_value)}")
                elif isinstance(section_data, list): current_section_text_parts.extend(str(item) for item in section_data)
                else: current_section_text_parts.append(str(section_data))
                if current_section_text_parts: all_section_texts.append(item_sep.join(current_section_text_parts))

        display_output["display"] = block_sep.join(all_section_texts)
        if title_parts: display_output["title"] = title_joiner.join(title_parts)
        else: display_output["title"] = "Info" # Default title
        return display_output

    def display_image_of(self, image_file_path: str) -> None:
        try: pixmap = QtGui.QPixmap(image_file_path); self.image_preview.setPixmap(pixmap)
        except Exception as e: nfo(f"Error creating QPixmap for {image_file_path}: {e}"); self.image_preview.setPixmap(None)

    def display_text_of(self, metadata_dict: dict[str, Any] | None) -> None:
        # Get placeholder strings, using .value if Enums, with fallbacks
        ph_prompt_default = "Prompt Info"; ph_gen_default = "Generation Info"; ph_details_default = "N/A"
        try: ph_prompt = EmptyField.PLACEHOLDER_PROMPT.value if hasattr(EmptyField, 'PLACEHOLDER_PROMPT') else ph_prompt_default
        except AttributeError: ph_prompt = getattr(EmptyField, 'PLACEHOLDER_PROMPT', ph_prompt_default)
        try: ph_gen = EmptyField.PLACEHOLDER_GEN.value if hasattr(EmptyField, 'PLACEHOLDER_GEN') else ph_gen_default
        except AttributeError: ph_gen = getattr(EmptyField, 'PLACEHOLDER_GEN', ph_gen_default)
        try: ph_details = EmptyField.PLACEHOLDER_DETAILS.value if hasattr(EmptyField, 'PLACEHOLDER_DETAILS') else ph_details_default
        except AttributeError: ph_details = getattr(EmptyField, 'PLACEHOLDER_DETAILS', ph_details_default)

        # Determine the key for placeholder data in metadata_dict
        placeholder_key = EmptyField.PLACEHOLDER.value if hasattr(EmptyField.PLACEHOLDER, 'value') else EmptyField.PLACEHOLDER

        is_error_or_empty = False
        if metadata_dict is None:
            is_error_or_empty = True
        elif placeholder_key in metadata_dict and len(metadata_dict) == 1: # Only placeholder key exists
            is_error_or_empty = True

        if not is_error_or_empty:
            separators = [": ", "\n", "\n\n", "", " & "]
            # --- MODIFIED: Use .get_ordered_labels() if UpField/DownField are Enums with this method ---
            metadata_display_upper = self.unpack_content_of(metadata_dict, UpField.get_ordered_labels(), separators)
            self.top_separator.setText(metadata_display_upper.get("title", ph_prompt).strip(" & "))
            self.upper_box.setText(metadata_display_upper.get("display", "").strip())

            metadata_display_lower = self.unpack_content_of(metadata_dict, DownField.get_ordered_labels(), separators)
            self.mid_separator.setText(metadata_display_lower.get("title", ph_gen).strip(" & "))
            self.lower_box.setText(metadata_display_lower.get("display", "").strip())
        else:
            self.top_separator.setText(ph_prompt); self.mid_separator.setText(ph_gen)
            error_msg_to_display = ph_details
            if metadata_dict and placeholder_key in metadata_dict: # Check .value
                placeholder_content = metadata_dict[placeholder_key]
                if isinstance(placeholder_content, dict) and "Error" in placeholder_content:
                    error_msg_to_display = f"Error loading metadata:\n{placeholder_content['Error']}"
                elif isinstance(placeholder_content, dict) and "Info" in placeholder_content:
                    error_msg_to_display = placeholder_content["Info"]
                elif isinstance(placeholder_content, str):
                    error_msg_to_display = placeholder_content
            self.upper_box.setText(error_msg_to_display); self.lower_box.setText("")


    def apply_theme(self, theme_name_xml: str, initial_load=False):
        if not QT_MATERIAL_AVAILABLE: nfo("Cannot apply theme, qt-material not available."); return
        app = QApplication.instance();
        if not app: return
        for theme_key, action in self.theme_actions.items(): action.setChecked(theme_key == theme_name_xml)
        try:
            invert = theme_name_xml in ("dark_teal.xml", "dark_blue.xml")
            apply_stylesheet(app, theme=theme_name_xml, invert_secondary=invert)
        except Exception as e: nfo(f"Error applying theme {theme_name_xml}: {e}"); return
        if not initial_load: nfo(f"Theme applied and saved: {theme_name_xml}"); self.settings.setValue("theme", theme_name_xml)
        else: nfo(f"Initial theme loaded: {theme_name_xml}")

    def show_about_dialog(self):
        from PyQt6.QtWidgets import QMessageBox
        version_text = "";
        try:
            from dataset_tools.version import __version__ as file_version; version_text = f"Version: {file_version}\n"
        except ImportError:
            try:
                from dataset_tools import __version__ as pkg_version
                if pkg_version and pkg_version != "0.0.0-dev": version_text = f"Version: {pkg_version}\n"
                else: nfo("Placeholder package version found ('0.0.0-dev').")
            except ImportError: nfo("Version information not found."); pass
        contributors_list = ["KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA (Lead Developer)"]
        contributors_text = "\nContributors:\n" + "\n".join(f"- {c}" for c in contributors_list)
        license_name = "GPL-3.0-or-later"; license_text = f"License: {license_name}\n(Refer to LICENSE file for full text)\n\n"
        about_text = (f"<b>Dataset Viewer</b>\n{version_text}An ultralight metadata viewer and dataset handler.\n\n"
                      f"Developed by KTISEOS NYX of EARTH & DUSK MEDIA.\n{contributors_text}\n\n{license_text}")
        QMessageBox.about(self, "About Dataset Viewer", about_text)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls(): event.acceptProposedAction(); nfo("[UI] Drag enter event accepted for URLs.")
        else: event.ignore(); nfo("[UI] Drag enter event ignored (not URLs).")

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            urls = mime_data.urls()
            if urls:
                dropped_file_path_qurl = urls[0]
                if dropped_file_path_qurl.isLocalFile():
                    dropped_path_str = dropped_file_path_qurl.toLocalFile()
                    nfo(f"[UI] Item dropped: {dropped_path_str}")
                    path_obj = Path(dropped_path_str)
                    folder_to_load = ""; file_to_select_name = None
                    if path_obj.is_file():
                        folder_to_load = str(path_obj.parent); file_to_select_name = path_obj.name
                        nfo(f"[UI] Dropped file. Loading folder: {folder_to_load}. Will select: {file_to_select_name}")
                    elif path_obj.is_dir():
                        folder_to_load = str(path_obj)
                        nfo(f"[UI] Dropped folder. Loading folder: {folder_to_load}")
                    if folder_to_load:
                        self.settings.setValue("lastFolderPath", folder_to_load)
                        self.load_files(folder_to_load, file_to_select_after_load=file_to_select_name)
                        event.acceptProposedAction(); return
        event.ignore(); nfo("[UI] Drop event ignored (no local valid file/folder URL).")

# --- Main execution guard for direct script run (testing) ---
if __name__ == "__main__":
    # This requires correct_types.py to be fixed with Enums first.
    # And also assumes dataset_tools package structure is accessible.
    try:
        from dataset_tools import __version__ as pkg_version_main, LOG_LEVEL as INITIAL_LOG_LEVEL_FROM_INIT_MAIN
        from dataset_tools.logger import logger as main_app_logger_main
        main_app_logger_main.info(f"Dataset Tools UI (Direct Run) v{pkg_version_main} launching...")
        main_app_logger_main.info(f"Application log level (initial from __init__): {INITIAL_LOG_LEVEL_FROM_INIT_MAIN}")
    except ImportError as e_main_import:
        print(f"Direct run: Could not import package components for logging: {e_main_import}")
        # Fallback simple print if logger isn't available
        def nfo(*args): print("NFO:", *args)

    app = Qw.QApplication(sys.argv if hasattr(sys, 'argv') else [])
    if QT_MATERIAL_AVAILABLE:
        try:
            temp_settings = QSettings("EarthAndDuskMedia", "DatasetViewer")
            theme_to_load = temp_settings.value("theme", "dark_teal.xml")
            invert = theme_to_load in ("dark_teal.xml", "dark_blue.xml")
            apply_stylesheet(app, theme=theme_to_load, invert_secondary=invert)
        except Exception as e_theme_main:
            print(f"Could not apply theme for direct ui.py test: {e_theme_main}")

    window = MainWindow()
    window.show()

    if hasattr(app, 'exec'): sys.exit(app.exec())
    elif hasattr(app, 'exec_'): sys.exit(app.exec_())