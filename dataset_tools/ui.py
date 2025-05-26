# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""App UI"""

# pylint: disable=line-too-long
# pylint: disable=c-extension-no-member
# pylint: disable=attribute-defined-outside-init

import os
import sys # Added for __main__ block if not already present
from pathlib import Path
from collections import defaultdict
from typing import Any # Added for type hinting

import PyQt6
from PyQt6 import QtWidgets as Qw
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QSettings

from dataset_tools.logger import debug_monitor  # , debug_monitor_solo
from dataset_tools.logger import info_monitor as nfo
from dataset_tools.metadata_parser import parse_metadata
from dataset_tools.widgets import FileLoader
from dataset_tools.correct_types import EmptyField, UpField, DownField
from dataset_tools.correct_types import ExtensionType as Ext


class MainWindow(Qw.QMainWindow):
    """ "Consolidated raw functions and behavior of window"""

    # @debug_monitor_solo
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dataset Viewer")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height
        self.setMinimumSize(800, 600)  # set minimum size for standard window.

        settings = QSettings("YourOrganization", "DatasetViewer")
        saved_theme_name = settings.value("theme", "")

        # --- Menu Bar ---
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("File")
        change_folder_action = QtGui.QAction("Change Folder...", self)
        change_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(change_folder_action)
        close_action = QtGui.QAction("Close", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        # View Menu
        view_menu = menu_bar.addMenu("View")
        themes_menu = Qw.QMenu("Themes", self)
        view_menu.addMenu(themes_menu)

        from qt_material import list_themes # Import here as it's UI-specific
        available_themes = list_themes()
        self.theme_actions = {}
        for theme_name in available_themes:
            action = QtGui.QAction(theme_name.replace(".xml", "").replace("_", " ").title(), self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, theme=theme_name: self.apply_theme(theme))
            themes_menu.addAction(action)
            self.theme_actions[theme_name] = action

        # About Menu
        about_menu = menu_bar.addMenu("About")
        about_action = QtGui.QAction("About...", self)
        about_action.triggered.connect(self.show_about_dialog)
        about_menu.addAction(about_action)


        if saved_theme_name and saved_theme_name in self.theme_actions:
            self.theme_actions[saved_theme_name].setChecked(True)
            self.apply_theme(saved_theme_name, initial_load=True)
        else:
            default_theme = "dark_teal.xml"
            if default_theme in self.theme_actions:
                self.theme_actions[default_theme].setChecked(True)
                self.apply_theme(default_theme, initial_load=True)

        central_widget = PyQt6.QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        main_layout = Qw.QHBoxLayout(central_widget)

        left_panel = Qw.QWidget()
        left_layout = Qw.QVBoxLayout(left_panel)
        main_layout.addWidget(left_panel)

        self.current_folder_label = Qw.QLabel("Current Folder: None")
        left_layout.addWidget(self.current_folder_label)

        self.open_folder_button = Qw.QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_folder)
        left_layout.addWidget(self.open_folder_button)

        self.sort_button = Qw.QPushButton("Sort Files")
        self.sort_button.clicked.connect(self.sort_files_list)
        left_layout.addWidget(self.sort_button)

        self.copy_button = Qw.QPushButton("Copy Metadata")
        self.copy_button.clicked.connect(self.copy_metadata_to_clipboard)
        left_layout.addWidget(self.copy_button)

        self.message_label = Qw.QLabel("Select a folder!")
        left_layout.addWidget(self.message_label)

        self.files_list = Qw.QListWidget()
        self.files_list.setSelectionMode(Qw.QAbstractItemView.SelectionMode.SingleSelection)
        self.files_list.currentItemChanged.connect(self.on_file_selected)
        left_layout.addWidget(self.files_list)

        self.progress_bar = Qw.QProgressBar()
        self.progress_bar.hide()
        left_layout.addWidget(self.progress_bar)

        right_panel = Qw.QWidget()
        right_layout = Qw.QVBoxLayout(right_panel)
        main_layout.addWidget(right_panel)

        self.image_preview = Qw.QLabel()
        self.image_preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumHeight(300)
        right_layout.addWidget(self.image_preview)

        self.top_separator = Qw.QLabel()
        self.top_separator.setText("Prompt Info will show here")
        self.top_separator.setMinimumWidth(400)
        right_layout.addWidget(self.top_separator)

        self.upper_box = Qw.QTextEdit()
        self.upper_box.setReadOnly(True)
        self.upper_box.setMinimumWidth(400)
        right_layout.addWidget(self.upper_box)

        self.mid_separator = Qw.QLabel()
        self.mid_separator.setText("Generation Info will show here")
        self.mid_separator.setMinimumWidth(400)
        right_layout.addWidget(self.mid_separator)

        self.lower_box = Qw.QTextEdit()
        self.lower_box.setMinimumWidth(400)
        self.lower_box.setReadOnly(True)
        right_layout.addWidget(self.lower_box)

        self.file_loader = None
        self.current_folder = os.getcwd()
        self.clear_file_list()
        self.load_files(os.getcwd())

    # /______________________________________________________________________________________________________________________ File Browser

    def open_folder(self):
        folder_path = Qw.QFileDialog.getExistingDirectory(self, "Select a folder")
        if folder_path:
            self.load_files(folder_path)

    def clear_file_list(self):
        self.file_list = []
        self.image_files = []
        self.text_files = []
        self.model_files = []

    def clear_selection(self):
        self.image_preview.clear()
        self.lower_box.clear()
        self.mid_separator.setText(EmptyField.PLACEHOLDER_GEN if hasattr(EmptyField, 'PLACEHOLDER_GEN') else "Generation Info")
        self.upper_box.clear()
        self.top_separator.setText(EmptyField.PLACEHOLDER_PROMPT if hasattr(EmptyField, 'PLACEHOLDER_PROMPT') else "Prompt Info")


    def load_files(self, folder_path):
        self.current_folder = folder_path
        self.current_folder_label.setText(f"Current Folder: {folder_path}")
        self.message_label.setText("Loading files...")
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        if self.file_loader and self.file_loader.isRunning():
            try:
                self.file_loader.progress.disconnect()
                self.file_loader.finished.disconnect()
            except TypeError:
                pass
        self.file_loader = FileLoader(folder_path)
        self.file_loader.progress.connect(self.update_progress)
        self.file_loader.finished.connect(self.on_files_loaded)
        self.file_loader.start()

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)

    def on_files_loaded(self, image_list, text_files, model_files, loaded_folder):
        if self.current_folder != loaded_folder:
            nfo(f"Ignoring loaded files from '{loaded_folder}' as current folder is '{self.current_folder}'")
            return
        self.image_files = sorted(image_list)
        self.text_files = sorted(text_files)
        self.model_files = sorted(model_files)

        self.message_label.setText(f"Loaded {len(self.image_files)} image, {len(self.text_files)} text, and {len(self.model_files)} model files.")
        self.progress_bar.hide()

        self.files_list.clear()
        self.files_list.addItems(self.image_files)
        self.files_list.addItems(self.text_files)
        self.files_list.addItems(self.model_files)

    # /______________________________________________________________________________________________________________________ UI Actions (Sort, Copy)

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

        self.message_label.setText(f"Sorted {self.files_list.count()} items.")
        nfo(f"Sorted {self.files_list.count()} items in the file list.")

    def copy_metadata_to_clipboard(self):
        nfo("Copy Metadata button clicked.")
        selected_items = self.files_list.selectedItems()
        if not selected_items:
            self.message_label.setText("No file selected to copy metadata from.")
            nfo("No file selected.")
            return

        prompt_info_title = self.top_separator.text()
        prompt_info_content = self.upper_box.toPlainText()
        generation_info_title = self.mid_separator.text()
        generation_info_content = self.lower_box.toPlainText()

        # Check against actual placeholder values if they exist in EmptyField
        ph_prompt = getattr(EmptyField, 'PLACEHOLDER_PROMPT', "Prompt Info will show here")
        ph_gen = getattr(EmptyField, 'PLACEHOLDER_GEN', "Generation Info will show here")
        ph_details = getattr(EmptyField, 'PLACEHOLDER_DETAILS', "No details available or file not supported.")

        if (not prompt_info_content.strip() or prompt_info_content == ph_details) and \
           (not generation_info_content.strip() or generation_info_content == ph_details):
            self.message_label.setText("No metadata displayed to copy.")
            nfo("No metadata content in text boxes.")
            return

        clipboard_text = ""
        if prompt_info_content.strip() and prompt_info_title != ph_prompt and prompt_info_content != ph_details :
            clipboard_text += f"{prompt_info_title}:\n{prompt_info_content}\n\n"
        if generation_info_content.strip() and generation_info_title != ph_gen and generation_info_content != ph_details:
             clipboard_text += f"{generation_info_title}:\n{generation_info_content}"

        clipboard_text = clipboard_text.strip()

        if clipboard_text:
            clipboard = QtGui.QGuiApplication.clipboard()
            clipboard.setText(clipboard_text)
            self.message_label.setText("Metadata copied to clipboard!")
            nfo("Metadata copied to clipboard.")
        else:
            self.message_label.setText("No metadata to copy.")
            nfo("No metadata found to copy after formatting.")

    # /______________________________________________________________________________________________________________________ Fetch Metadata

    @debug_monitor
    def load_metadata(self, file_path: str) -> dict[str, Any] | None:
        metadata: dict[str, Any] | None = None
        full_file_path = os.path.join(self.current_folder, file_path)
        try:
            metadata = parse_metadata(full_file_path)
        except IndexError as error_log:
            nfo(f"Unexpected list position, out of range error for metadata in {full_file_path}, {error_log}")
        except StopIteration as error_log:
            nfo(f"Overflow length on data operation for {full_file_path}, {error_log}")
        except TypeError as error_log:
            nfo(f"Attempted invalid operation on {full_file_path}, {error_log}")
        except ValueError as error_log:
            nfo(f"Invalid dictionary formatting while extracting metadata from {full_file_path}, {error_log}")
        except Exception as error_log:
            nfo(f"An unexpected error occurred while parsing metadata for {full_file_path}: {error_log}")
        return metadata

    @debug_monitor
    def on_file_selected(self, current_item: Qw.QListWidgetItem | None, previous_item: Qw.QListWidgetItem | None): # Allow None for items
        if not current_item:
            self.clear_selection()
            self.message_label.setText("No file selected.")
            return

        file_name = current_item.text()
        self.message_label.setText(f"Selected {file_name}")
        self.clear_selection()
        full_file_path = os.path.join(self.current_folder, file_name)

        is_image = False
        for file_type_group in Ext.IMAGE:
            for ext_type in file_type_group:
                if Path(full_file_path).suffix.lower() == ext_type.lower():
                    self.display_image_of(full_file_path)
                    is_image = True
                    break
            if is_image:
                break
        
        if not is_image:
            self.image_preview.setText("No preview available for this file type.")

        metadata: dict[str, Any] | None = self.load_metadata(file_name)

        try:
            if metadata:
                self.display_text_of(metadata)
            else:
                self.display_text_of(None)
                nfo(f"No metadata found or error loading metadata for {file_name}")
        except TypeError as error_log:
            nfo(f"Invalid data in prompt fields {type(metadata)} from {file_name} {metadata} : {error_log}")
            self.display_text_of(None)
        except KeyError as error_log:
            nfo(f"Invalid key name for {type(metadata)} from {file_name} {metadata} : {error_log}")
            self.display_text_of(None)
        except AttributeError as error_log:
            nfo(f"Attribute cannot be applied to type {type(metadata)} from {file_name} {metadata} : {error_log}")
            self.display_text_of(None)

    # /______________________________________________________________________________________________________________________ Display Metadata

    @debug_monitor
    def unpack_content_of(self, metadata: dict[str, Any], labels: list[str], separators: list[str]) -> defaultdict[str, str]:
        metadata_display: defaultdict[str, str] = defaultdict(lambda: "")
        has_content = False
        title_parts: list[str] = [] # Ensure title_parts is typed

        for i, tag in enumerate(labels): # Use enumerate for easier last item check
            value = metadata.get(tag)
            if value is not None:
                has_content = True
                title_parts.append(tag)
                current_tag_text = ""
                if isinstance(value, dict):
                    dict_items = [f"{k}{separators[0]}{v}" for k, v in value.items()] # separators[0] is key-value separator
                    current_tag_text = separators[1].join(dict_items) # separators[1] is item separator
                elif isinstance(value, list):
                    current_tag_text = separators[1].join(str(item) for item in value) # separators[1] is item separator
                else:
                    current_tag_text = str(value)

                metadata_display["display"] += current_tag_text

                # Add block separator if it's not the last tag that has content
                # This requires a bit more lookahead or post-processing to be perfect for variable content
                # For simplicity, add block separator if not the absolute last tag in labels list
                if i < len(labels) - 1:
                     metadata_display["display"] += separators[2] # separators[2] is block separator (e.g. "\n\n")


        if has_content:
            metadata_display["title"] = separators[4].join(title_parts) # separators[4] is title joiner
        else:
            metadata_display["title"] = "Info" # Default if no tags found

        # Clean up trailing block separator if the last item was empty or it was added excessively
        if metadata_display["display"] and separators[2] and metadata_display["display"].endswith(separators[2]):
             metadata_display["display"] = metadata_display["display"][:-len(separators[2])]

        return metadata_display

    @debug_monitor
    def display_image_of(self, image_file_path: str) -> None:
        try:
            pixmap = QtGui.QPixmap(image_file_path)
            if pixmap.isNull():
                nfo(f"Failed to load image (pixmap isNull): {image_file_path}")
                self.image_preview.setText(f"Cannot load image:\n{os.path.basename(image_file_path)}")
                return

            self.image_preview.setPixmap(
                pixmap.scaled(
                    self.image_preview.size(),
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
            )
        except Exception as e:
            nfo(f"Error displaying image {image_file_path}: {e}")
            self.image_preview.setText(f"Error displaying image:\n{os.path.basename(image_file_path)}")

    @debug_monitor
    def display_text_of(self, metadata: dict[str, Any] | None) -> None:  # fmt: skip
        ph_prompt = getattr(EmptyField, 'PLACEHOLDER_PROMPT', "Prompt Info")
        ph_gen = getattr(EmptyField, 'PLACEHOLDER_GEN', "Generation Info")
        ph_details = getattr(EmptyField, 'PLACEHOLDER_DETAILS', "N/A")

        if metadata:
            # separators: [value_sep_in_dict_item, item_sep, block_sep, title_prefix_unused, title_joiner]
            up_separators = [": ", "\n", "\n\n", "", " + "]
            metadata_display_upper: defaultdict[str, str] = self.unpack_content_of(metadata, UpField.LABELS, up_separators)

            self.top_separator.setText(metadata_display_upper.get("title", ph_prompt))
            self.upper_box.setText(metadata_display_upper.get("display", ""))

            down_separators = [": ", "\n", "\n\n", "", " + "]
            metadata_display_lower: defaultdict[str, str] = self.unpack_content_of(metadata, DownField.LABELS, down_separators)

            self.mid_separator.setText(metadata_display_lower.get("title", ph_gen))
            self.lower_box.setText(metadata_display_lower.get("display", ""))
        else:
            self.top_separator.setText(ph_prompt)
            self.mid_separator.setText(ph_gen)
            self.upper_box.setText(ph_details)
            self.lower_box.setText(ph_details)

    def apply_theme(self, theme_name, initial_load=False):
        from qt_material import apply_stylesheet # Local import
        app = PyQt6.QtWidgets.QApplication.instance()

        for action_theme_name, action in self.theme_actions.items():
            if action_theme_name != theme_name:
                action.setChecked(False)
            elif not self.theme_actions[theme_name].isChecked():
                self.theme_actions[theme_name].setChecked(True)

        apply_stylesheet(app, theme=theme_name)

        if not initial_load:
            nfo(f"Theme applied and saved: {theme_name}")
            settings = QSettings("YourOrganization", "DatasetViewer")
            settings.setValue("theme", theme_name)

    def show_about_dialog(self):
        from PyQt6.QtWidgets import QMessageBox # Local import

        version_text = ""
        try:
            from dataset_tools.version import __version__
            version_text = f"Version: {__version__}\n"
        except ImportError:
            nfo("Version information (dataset_tools.version) not found.")
            pass

        contributors_list = [
            "KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA (Lead Developer)",
        ]
        contributors_text = "\nContributors:\n" + "\n".join(f"- {c}" for c in contributors_list)

        license_name = "MIT License"
        license_text = f"License: {license_name}\n\n"

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
    window = MainWindow()
    window.show()
    if hasattr(app, 'exec'):
        sys.exit(app.exec()) # Ensure sys.exit is used for proper exit codes