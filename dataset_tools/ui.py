# // SPDX-License-Identifier: CC0-1.0
# // --<{ Ktiseos Nyx }>--

"""App UI"""

# pylint: disable=line-too-long
# pylint: disable=c-extension-no-member
# pylint: disable=attribute-defined-outside-init

import os
from collections import defaultdict

import PyQt6
from PyQt6 import QtWidgets as Qw
from PyQt6 import QtCore, QtGui

from dataset_tools.logger import debug_monitor  # , debug_monitor_solo
from dataset_tools.logger import info_monitor as nfo
from dataset_tools.metadata_parser import parse_metadata
from dataset_tools.widgets import FileLoader
from dataset_tools.correct_types import UpField, DownField


class MainWindow(Qw.QMainWindow):
    """ "Consolidated raw functions and behavior of window"""

    # @debug_monitor_solo
    def __init__(self):
        super().__init__()
        # Set a default font for the app
        # app_font = QtGui.QFont("Arial", 12)
        # self.setFont(app_font)

        self.setWindowTitle("Dataset Viewer")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height
        self.setMinimumSize(800, 600)  # set minimum size for standard window.

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

        # Placeholder UI
        self.open_folder_button = Qw.QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_folder)
        left_layout.addWidget(self.open_folder_button)

        # Placeholder label, you can remove this later
        self.message_label = Qw.QLabel("Select a folder!")
        left_layout.addWidget(self.message_label)

        # File list (replaced Qw.QLabel with Qw.QListWidget)
        self.files_list = Qw.QListWidget()
        self.files_list.setSelectionMode(Qw.QAbstractItemView.SelectionMode.SingleSelection)
        self.files_list.itemClicked.connect(self.on_file_selected)  # Corrected This

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
        self.image_list = []
        self.text_files = []
        # self.model_files = []

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

    def on_files_loaded(self, image_list, text_files, loaded_folder):  # model_files,
        """Callback for working folder contents"""
        if self.current_folder != loaded_folder:
            # We are loading files from a different folder
            # than what's currently selected, so we need to ignore this.
            return
        self.image_list = image_list
        self.text_files = text_files
        # update the message and hide the loading bar
        self.message_label.setText(f"Loaded {len(self.image_list)} images and {len(self.text_files)} text files")
        self.progress_bar.hide()

        # Clear and populate the Qw.QListWidget
        self.files_list.clear()
        self.files_list.addItems(self.image_list)
        self.files_list.addItems(self.text_files)

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
    def on_file_selected(self, item):
        """Activate metadata on nab function"""
        file_path = item.text()
        self.message_label.setText(f"Selected {os.path.normpath(os.path.basename(file_path))}")

        # Clear any previous selection
        self.clear_selection()

        pixmap = QtGui.QPixmap(file_path)
        # scale the image
        self.image_preview.setPixmap(
            pixmap.scaled(
                self.image_preview.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
        )

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
            if metadata.get(tag, False):
                incoming_text = separators[0].join(f"{k}: {v} {separators[1]}" for k, v in metadata.get(tag).items()) + separators[2]
                metadata_display["display"] += incoming_text + separators[3]
                if metadata_display.get("title"):
                    metadata_display["title"] += separators[4] + tag
                else:
                    metadata_display["title"] += tag
        return metadata_display

    @debug_monitor
    def display_text_of(self, metadata: dict) -> None:  # fmt: skip
        """
        Use dictionary information to populate a QT text field\n
        :param metadata: A previously arranged dictionary
        :type metadata: dict
        :return: None, information is sent to QT UI fields via calls
        """
        if metadata is not None:
            metadata_display = self.unpack_content_of(metadata, UpField.LABELS, ["\n", "\n", "\n", "", ""])

            self.top_separator.setText(metadata_display["title"])
            self.upper_box.setText(metadata_display["display"])

            metadata_display = self.unpack_content_of(metadata, DownField.LABELS, ["", "\n", "", "", ""])

            self.mid_separator.setText(metadata_display["title"])
            self.lower_box.setText(metadata_display["display"])
        else:
            self.top_separator.setText(UpField.PLACEHOLDER)
            self.mid_separator.setText(UpField.PLACEHOLDER)
            self.upper_box.setText(UpField.PLACEHOLDER)
            self.lower_box.setText(UpField.PLACEHOLDER)


if __name__ == "__main__":
    app = Qw.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
