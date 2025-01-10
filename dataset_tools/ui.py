#// SPDX-License-Identifier: CC0-1.0
#// --<{ Ktiseos Nyx }>--
"""App Ui"""

# pylint: disable=line-too-long
# pylint: disable=c-extension-no-member
# pylint: disable=attribute-defined-outside-init

import os
import pprint  # Import the pprint module
from dataset_tools import logger
from dataset_tools import EXC_INFO
from dataset_tools.metadata_parser import parse_metadata
from dataset_tools.widgets import FileLoader
from PyQt6 import QtWidgets as Qw
from PyQt6 import QtCore, QtGui
from dataset_tools.widgets import Ext


class MainWindow(Qw.QMainWindow):
    """ "Consolidated raw functions and behavior of window"""

    def __init__(self):
        super().__init__()
        # Set a default font for the app
        # app_font = QtGui.QFont("Arial", 12)
        # self.setFont(app_font)

        self.setWindowTitle("Dataset Viewer")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height
        self.setMinimumSize(800, 600)  # set minimum size for standard window.

        # Central widget to hold our layout
        central_widget = Qw.QWidget()
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
        self.current_folder = None
        self.clear_file_list()
        logger.debug("%s", "File List cleared")

    def open_folder(self):
        """Open a dialog to select the folder"""
        folder_path = Qw.QFileDialog.getExistingDirectory(self, "Select a folder")
        if folder_path:
            logger.debug("%s", f"Folder opened {folder_path}")
            # Call the file loading function
            self.load_files(folder_path)

    def clear_files(self):
        """Empty all field displays"""
        if self.file_loader:
            self.file_loader.clear_files()
        self.files_list.clear()
        self.clear_file_list()
        logger.debug("%s", "File List cleared anew")
        self.clear_selection()
        logger.debug("%s", "Selection cleared")

    def clear_file_list(self):
        """Initialize or re-initialize display of files"""
        self.file_list = []
        logger.debug("%s", f"File List Initialized {self.file_list}")
        self.image_list = []
        self.text_files = []

    def clear_selection(self):
        """Empty file metadata display"""
        self.image_preview.clear()
        self.lower_box.clear()
        self.mid_separator.clear()
        self.upper_box.clear()
        self.top_separator.clear()

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
        logger.debug("%s", f"Loading files from {folder_path}...")

    def update_progress(self, progress):
        """Update progress bar"""
        self.progress_bar.setValue(progress)

    def on_files_loaded(self, image_list, text_files, loaded_folder):
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

    def load_metadata(self, file_path: str, extension: str = '.png') -> dict:
        """
        Fetch metadata from file\n
        :param file_path: `str` The file to interpret
        :return: a dictionary of metadata
        """
        metadata = None
        try:
            metadata = parse_metadata(file_path)
        except IndexError as error_log:
            logger.info("Unexpected list position, out of range error for metadata in %s", f"{file_path}, {error_log}", exc_info=EXC_INFO)
        except StopIteration as error_log:
            logger.info("Overflow length on data operation for %s", f"{file_path}, {error_log}", exc_info=EXC_INFO)
        except TypeError as error_log:
            logger.info("Attempted invalid operation on %s", f"{file_path}, {error_log}", exc_info=EXC_INFO)
        except IndexError as error_log:
            logger.info("Unexpected list position, out of range error for metadata in %s", f"{file_path}, {error_log}", exc_info=EXC_INFO)

        except ValueError as error_log:
            logger.info("Invalid dictionary formatting while extracting metadata from %s", f"{file_path}, {error_log}", exc_info=EXC_INFO)
        return metadata

    def on_file_selected(self, item):
        """Activate metadta on nab function"""
        file_path = item.text()
        self.message_label.setText(f"Selected {os.path.normpath(os.path.basename(file_path))}")

        # Clear any previous selection
        self.clear_selection()

        pixmap = QtGui.QPixmap(file_path)
        # scale the image
        self.image_preview.setPixmap(pixmap.scaled(self.image_preview.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))

        metadata = self.load_metadata(file_path)

        self.display_metadata(metadata, file_path)

    def display_metadata(self, metadata, file_path):
        """direct collated data to fields and pretty print there"""
        if metadata is not None:
            logger.debug("%s", f"{metadata}")
            prompt_keys = ['Positive prompt', 'Negative prompt', 'Prompt']
            self.top_separator.setText('Prompt Data:')
            self.mid_separator.setText('Generation Data:')
            text_separator = "\n"
            try:
                prompt_data = metadata.get('Prompts')
                self.upper_box.setText(''.join(f"{prompt_data.get(k)}\n" for k in prompt_keys if prompt_data.get(k)))
                positive_data = f"Positive prompt: {metadata['Prompts'].get('Positive prompt')}"
                negative_data = f"Negative prompt: {metadata['Prompts'].get('Negative prompt')}"
            except TypeError as error_log:
                logger.info("Invalid data in prompt fields %s", f" {type(metadata)} from {file_path}, {metadata} : {error_log}", exc_info=EXC_INFO)
            except KeyError as error_log:
                logger.info("Invalid key name for %s", f" {type(metadata)} from {file_path}, {metadata} : {error_log}", exc_info=EXC_INFO)
            except AttributeError as error_log:
                logger.info("Attribute cannot be applied to type %s", f" {type(metadata)} from  {file_path}, {metadata} : {error_log}", exc_info=EXC_INFO)
            else:
                self.upper_box.setText(positive_data + text_separator * 2 + negative_data)

            try:
                not_prompt = {k: v for k, v in metadata.get('Prompts', {}).items() if k not in prompt_keys}  # Default to {}
                generation_data = (not_prompt or {}) | (metadata.get('Settings') or {}) | (metadata.get('System') or {})
                self.lower_box.setText(pprint.pformat(generation_data))
                sys_data_str = "\n"
                gen_data_str = "\n"
                if metadata.get('Generation_Data', None) is not None:
                    gen_data_str = "\n".join(f"{k}: {v}" for k, v in metadata.get('Generation_Data', {}).items()) + "\n"
                if metadata.get('System', None):
                    sys_data_str = "\n".join(f"{k,v} \n" for k, v in metadata.get('System').items()) + "\n"
            except AttributeError as error_log:
                logger.info("'items' attribute cannot be applied to type %s", f" {type(metadata)} from {file_path}, {metadata} : {error_log}", exc_info=EXC_INFO)
            except TypeError as error_log:
                logger.info("Invalid data in generation fields  %s", f" {type(metadata)} from {file_path}, {metadata} : {error_log}", exc_info=EXC_INFO)
            else:
                display = f"{gen_data_str}{text_separator * 2}{sys_data_str}"
                self.lower_box.setText(display)


if __name__ == "__main__":
    app = Qw.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
