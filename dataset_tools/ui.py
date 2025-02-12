# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""App UI"""

# pylint: disable=line-too-long
# pylint: disable=c-extension-no-member
# pylint: disable=attribute-defined-outside-init

import os
from pathlib import Path
from collections import defaultdict

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

        settings = QSettings("YourOrganization", "DatasetViewer") # Same organization and app name as in apply_theme
        saved_theme_name = settings.value("theme", "") # Try to load saved theme, default to empty string if not found

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

        # Dynamically create theme menu actions
        from qt_material import list_themes
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


        if saved_theme_name and saved_theme_name in self.theme_actions: # Check if saved theme is valid
            self.theme_actions[saved_theme_name].setChecked(True) # Check the saved theme action in menu
            self.apply_theme(saved_theme_name) # Apply the saved theme
        else:
            default_theme = "dark_teal.xml" # Default theme if no saved theme or saved theme is invalid
            if default_theme in self.theme_actions:
                self.theme_actions[default_theme].setChecked(True)
                self.apply_theme(default_theme)


        # Central widget to hold our layout
        central_widget = PyQt6.QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = Qw.QHBoxLayout(central_widget)

        # Left panel layout
        left_panel = Qw.QWidget()
        left_layout = Qw.QVBoxLayout(left_panel)
        main_layout.addWidget(left_panel)

        # Folder Path Label
        self.current_folder_label = Qw.QLabel("Current Folder: None")
        left_layout.addWidget(self.current_folder_label)

        # Open Folder Button
        self.open_folder_button = Qw.QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_folder)
        left_layout.addWidget(self.open_folder_button)

        # Sort Files Button
        self.sort_button = Qw.QPushButton("Sort Files")
        self.sort_button.clicked.connect(self.sort_files_list)
        left_layout.addWidget(self.sort_button)

        # Copy Metadata Button
        self.copy_button = Qw.QPushButton("Copy Metadata")
        self.copy_button.clicked.connect(self.copy_metadata_to_clipboard)
        left_layout.addWidget(self.copy_button)


        # Placeholder label, you can remove this later
        self.message_label = Qw.QLabel("Select a folder!")
        left_layout.addWidget(self.message_label)

        # File list (replaced Qw.QLabel with Qw.QListWidget)
        self.files_list = Qw.QListWidget()
        if not self.files_list.item:
            self.files_list.item = self.currentItem()
        self.files_list.setSelectionMode(Qw.QAbstractItemView.SelectionMode.SingleSelection)
        self.files_list.currentItemChanged.connect(self.on_file_selected)
        left_layout.addWidget(self.files_list)

        # Add a progress bar for file loading
        self.progress_bar = Qw.QProgressBar()
        self.progress_bar.hide()
        left_layout.addWidget(self.progress_bar)

        # Right panel Layout
        right_panel = Qw.QWidget()
        right_layout = Qw.QVBoxLayout(right_panel)
        main_layout.addWidget(right_panel)

        # Image preview area
        self.image_preview = Qw.QLabel()
        self.image_preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumHeight(300)
        right_layout.addWidget(self.image_preview)

        # Right top separator
        self.top_separator = Qw.QLabel()
        self.top_separator.setText("Prompt Info will show here")
        self.top_separator.setMinimumWidth(400)
        right_layout.addWidget(self.top_separator)

        # Upper Right box
        self.upper_box = Qw.QTextEdit()
        self.upper_box.setReadOnly(True)
        self.upper_box.setMinimumWidth(400)
        right_layout.addWidget(self.upper_box)

        # Right boxes separator
        self.mid_separator = Qw.QLabel()
        self.mid_separator.setText("Generation Info will show here")
        self.mid_separator.setMinimumWidth(400)
        right_layout.addWidget(self.mid_separator)

        # Lower Right box
        self.lower_box = Qw.QTextEdit()
        self.lower_box.setMinimumWidth(400)
        self.lower_box.setReadOnly(True)
        right_layout.addWidget(self.lower_box)

        self.file_loader = None
        self.current_folder = os.getcwd()
        self.clear_file_list()
        self.load_files(os.getcwd())

    # /______________________________________________________________________________________________________________________ File Browser

    # @debug_monitor_solo
    def open_folder(self):
        """Open a dialog to select the folder"""
        folder_path = Qw.QFileDialog.getExistingDirectory(self, "Select a folder")
        if folder_path:
            # Call the file loading function
            self.load_files(folder_path)

    # @debug_monitor_solo
    def clear_files(self):
        """Empty all field displays"""
        if self.file_loader:
            self.file_loader.clear_files()
        self.files_list.clear()
        self.clear_file_list()
        self.clear_selection()

    # @debug_monitor_solo
    def clear_file_list(self):
        """Initialize or re-initialize display of files"""
        self.file_list = []
        self.image_files = []
        self.text_files = []
        self.model_files = []

    def clear_selection(self):
        """Empty file metadata display"""
        self.image_preview.clear()
        self.lower_box.clear()
        self.mid_separator.clear()
        self.upper_box.clear()
        self.top_separator.clear()

    # @debug_monitor_solo
    def load_files(self, folder_path):
        """Start background loading of files using QThread"""
        self.current_folder = folder_path
        self.current_folder_label.setText(f"Current Folder: {folder_path}")
        self.message_label.setText("Loading files...")
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        if self.file_loader:
            self.file_loader.finished.disconnect()
        self.file_loader = FileLoader(folder_path)
        self.file_loader.progress.connect(self.update_progress)
        self.file_loader.finished.connect(self.on_files_loaded)
        self.file_loader.start()

    def update_progress(self, progress):
        """Update progress bar"""
        self.progress_bar.setValue(progress)

    def on_files_loaded(self, image_list, text_files, model_files, loaded_folder):
        """Callback for working folder contents"""
        if self.current_folder != loaded_folder:
            # We are loading files from a different folder
            # than what's currently selected, so we need to ignore this.
            return  # x - ?????
        self.image_files = image_list
        self.text_files = text_files
        self.model_files = model_files
        # update the message and hide the loading bar

        self.message_label.setText(f"Loaded {len(self.image_files)} image, {len(self.text_files)} text, and {len(self.model_files)} model files.")
        self.progress_bar.hide()

        # Clear and populate the Qw.QListWidget
        self.files_list.clear()
        self.files_list.addItems(self.image_files)
        self.files_list.addItems(self.text_files)
        self.files_list.addItems(self.model_files)

    # /______________________________________________________________________________________________________________________ Fetch Metadata

    @debug_monitor
    def load_metadata(self, file_path: str) -> dict:
        """
        Fetch metadata from file\n
        :param file_path: `str` The file to interpret
        :return: a dictionary of metadata
        """
        metadata = None
        try:
            metadata = parse_metadata(file_path)
        except IndexError as error_log:
            nfo("Unexpected list position, out of range error for metadata in", file_path, ",", error_log)
        except StopIteration as error_log:
            nfo("Overflow length on data operation for ", file_path, ",", error_log)
        except TypeError as error_log:
            nfo("Attempted invalid operation on", file_path, ",", error_log)
        except ValueError as error_log:
            nfo("Invalid dictionary formatting while extracting metadata from", file_path, ",", error_log)
        return metadata

    @debug_monitor
    def on_file_selected(self, *args):  # x - I don't yet know whats getting passed as a third argument here...
        """Activate metadata on nab function"""
        if args:
            file_path = next(x.text() for x in args if hasattr(x, "text"))
            self.message_label.setText(f"Selected {os.path.normpath(os.path.basename(file_path))}")

            # Clear any previous selection
            self.clear_selection()

            for file_type in Ext.IMAGE:
                if Path(file_path).suffix in file_type:
                    self.display_image_of(file_path)
                    break

            metadata = self.load_metadata(file_path)

            try:
                self.display_text_of(metadata)
            except TypeError as error_log:
                nfo("Invalid data in prompt fields", type(metadata), "from", file_path, metadata, ":", error_log)
            except KeyError as error_log:
                nfo("Invalid key name for", type(metadata), "from", file_path, metadata, ":", error_log)
            except AttributeError as error_log:
                nfo("Attribute cannot be applied to type", type(metadata), "from", file_path, metadata, ":", error_log)

    # /______________________________________________________________________________________________________________________ Display Metadata

    @debug_monitor
    def unpack_content_of(self, metadata: dict, labels: list, separators: list) -> dict:
        """
        Open and format dictionary content to feed to a display\n
        :param metadata: A previously arranged dictionary
        :type metadata: dict
        :param labels: The names of keys within the existing dictionary
        :type labels: list
        :param separators: Padding for the text display
        :type separators: list
        :return: `dict` The arranged content
        """
        metadata_display = defaultdict(lambda: "")
        for tag in labels:
            if metadata.get(tag, False) and isinstance(metadata.get(tag, False), dict):
                incoming_text = separators[0].join(f"{k}: {v} {separators[1]}" for k, v in metadata.get(tag).items()) + separators[2]
                metadata_display["display"] += incoming_text + separators[3]
                if metadata_display.get("title"):
                    metadata_display["title"] += separators[4] + tag
                else:
                    metadata_display["title"] += tag
            elif metadata.get(tag, False):
                incoming_text = str(metadata.get(tag))
                metadata_display["display"] += incoming_text + separators[3]
                if metadata_display.get("title"):
                    metadata_display["title"] += separators[4] + tag
                else:
                    metadata_display["title"] += tag
        return metadata_display

    @debug_monitor
    def display_image_of(self, image_file: str) -> None:
        """
        Send an image to the previwer\n
        :param image_file: Absolute path of the image to display
        :type image_file: str
        :return: None, sends an image to display
        """

        pixmap = QtGui.QPixmap(image_file)

        # scale the image
        self.image_preview.setPixmap(
            pixmap.scaled(
                self.image_preview.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
        )

    @debug_monitor
    def display_text_of(self, metadata: dict) -> None:  # fmt: skip
        """
        Use dictionary information to populate a QT text field\n
        :param metadata: A previously arranged dictionary
        :type metadata: dict
        :return: None, information is sent to QT UI fields via calls
        """
        if metadata:
            metadata_display = self.unpack_content_of(metadata, UpField.LABELS, ["\n", "\n", "\n", "", ""])

            self.top_separator.setText(metadata_display["title"])
            self.upper_box.setText(metadata_display["display"])

            metadata_display = self.unpack_content_of(metadata, DownField.LABELS, ["", "\n", "", "", ""])

            self.mid_separator.setText(metadata_display["title"])
            self.lower_box.setText(metadata_display["display"])
        else:
            self.top_separator.setText(EmptyField.PLACEHOLDER)
            self.mid_separator.setText(EmptyField.PLACEHOLDER)
            self.upper_box.setText(EmptyField.PLACEHOLDER)
            self.lower_box.setText(EmptyField.PLACEHOLDER)

    def apply_theme(self, theme_name):
        """Apply the selected qt-material theme and save to settings"""
        from qt_material import apply_stylesheet
        app = PyQt6.QtWidgets.QApplication.instance() # Get the QApplication instance

        # Uncheck all other theme actions (radio-button behavior)
        for action_theme_name, action in self.theme_actions.items():
            if action_theme_name != theme_name:
                action.setChecked(False)

        apply_stylesheet(app, theme=theme_name) # Apply the selected theme
        print(f"Theme applied and saved: {theme_name}") # Optional feedback to console

        settings = QSettings("YourOrganization", "DatasetViewer") # Replace "YourOrganization" and "DatasetViewer"
        settings.setValue("theme", theme_name) # Save theme name to settings


    def show_about_dialog(self):
        """Show the About dialog with application information and contributors"""
        from PyQt6.QtWidgets import QMessageBox

        version_text = "" # Default if version info not found
        try:
            from dataset_tools.version import __version__ # Try to import version
            version_text = f"Version: {__version__}\n"
        except ImportError:
            pass # Handle case if version.py is not available

        contributors_list = [ # Define your list of contributors here
            "Your Name (Current Maintainer)",
            "Previous Developer (Even if 'Asshole', credit is good practice)",
            # Add other contributors here...
        ]
        contributors_text = "\nContributors:\n" + "\n".join(contributors_list)

        license_text = "License: MIT License\n\n" # Update if you change license, link to full license in README/LICENSE file
        license_link_text = "See LICENSE file for full license text.\n" # Add if you want to mention external license file

        about_text = (
            f"<b>Dataset Viewer</b>\n"
            f"{version_text}"
            f"An ultralight metadata viewer and dataset handler.\n\n"
            f"{contributors_text}\n\n"
            f"{license_text}"
            f"{license_link_text}"
        )

        QMessageBox.about(self, "About Dataset Viewer", about_text) # Create and show about dialog


if __name__ == "__main__":
    app = Qw.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
