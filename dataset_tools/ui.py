from importlib import metadata
from xml.dom.minidom import parseString
from dataset_tools import logger
import pprint
import os

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QProgressBar,
    QListWidget,
    QAbstractItemView,
    QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from dataset_tools.widgets import FileLoader
import imghdr
from dataset_tools.metadata_parser import parse_metadata, open_jpg_header
from dataset_tools import EXC_INFO
import re

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Launching application...")
        # Set a default font for the app
        # app_font = QFont("Arial", 12)
        # self.setFont(app_font)

        self.setWindowTitle("Dataset Viewer")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height
        self.setMinimumSize(800, 600)  # set minimum size for standard window.

        # Central widget to hold our layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left panel layout
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        main_layout.addWidget(left_panel)

        # Folder Path Label
        self.current_folder_label = QLabel("Current Folder: None")
        left_layout.addWidget(self.current_folder_label)

        # Placeholder UI
        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_folder)
        left_layout.addWidget(self.open_folder_button)

        # Placeholder label, you can remove this later
        self.message_label = QLabel("Select a folder!")
        left_layout.addWidget(self.message_label)

        # File list (replaced QLabel with QListWidget)
        self.files_list = QListWidget()
        self.files_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.files_list.itemClicked.connect(self.on_file_selected)
        left_layout.addWidget(self.files_list)

        # Add a progress bar for file loading
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        left_layout.addWidget(self.progress_bar)

        # Right panel Layout
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        main_layout.addWidget(right_panel)

        # Image preview area
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumHeight(300)
        right_layout.addWidget(self.image_preview)


        # Right top separator
        self.top_separator = QLabel()
        self.top_separator.setText("Prompt Info will show here")
        self.top_separator.setMinimumWidth(400)
        right_layout.addWidget(self.top_separator)


        # Upper Right box
        self.upper_box = QTextEdit()
        self.upper_box.setReadOnly(True)
        self.upper_box.setMinimumWidth(400)
        right_layout.addWidget(self.upper_box)

        # Right boxes separator
        self.separator_text = QLabel()
        self.separator_text.setText("Generation Info will show here")
        self.separator_text.setMinimumWidth(400)
        right_layout.addWidget(self.separator_text)


        # Lower Right box
        self.lower_box = QTextEdit()
        self.lower_box.setMinimumWidth(400)
        self.lower_box.setReadOnly(True)
        right_layout.addWidget(self.lower_box)


        self.file_loader = None
        self.file_list = []
        self.image_list = []
        self.text_files = []
        self.current_folder = None

    def open_folder(self):
        # Open a dialog to select the folder
        folder_path = QFileDialog.getExistingDirectory(self, "Select a folder")
        if folder_path:
            # Call the file loading function
            self.load_files(folder_path)

    def clear_files(self):
      if self.file_loader:
         self.file_loader.clear_files()
      self.file_list = []
      self.image_list = []
      self.text_files = []
      self.files_list.clear()
      self.image_preview.clear()
      self.lower_box.clear()
      self.separator_text.clear()
      self.upper_box.clear()
      self.top_separator.clear()

    def load_files(self, folder_path):
        # Start background loading of files using QThread
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
        # Update progress bar
        self.progress_bar.setValue(progress)

    def on_files_loaded(self, image_list, text_files, loaded_folder):
        if self.current_folder != loaded_folder:
            # We are loading files from a different folder
            # than what's currently selected, so we need to ignore this.
            return
        self.image_list = image_list
        self.text_files = text_files
        # update the message and hide the loading bar
        self.message_label.setText(f"Loaded {len(self.image_list)} images and {len(self.text_files)} text files")
        self.progress_bar.hide()

        # Clear and populate the QListWidget
        self.files_list.clear()
        self.files_list.addItems(self.image_list)
        self.files_list.addItems(self.text_files)


    def on_file_selected(self, item):
        file_path = item.text()
        self.message_label.setText(f"Selected {os.path.normpath(os.path.basename(file_path))}")

        # Clear any previous selection
        self.image_preview.clear()
        self.lower_box.clear()
        self.separator_text.clear()
        self.upper_box.clear()
        self.top_separator.clear()

        if file_path.lower().endswith(('.png','.jpg','.jpeg','.webp')):
            # Load the image
            self.load_image_preview(file_path)
            metadata = self.load_metadata(file_path)
            self.display_metadata(metadata, file_path)

        if file_path.lower().endswith('.txt'):
            # Load the text file
            self.load_text_file(file_path)

    def load_metadata(self, file_path):
        metadata = None
        try:
            if imghdr.what(file_path) == 'png':
                metadata = parse_metadata(file_path)

            elif imghdr.what(file_path) in ['jpeg', 'jpg']:
                metadata = open_jpg_header(file_path)

        except IndexError as error_log:
            logger.info(f"Unexpected list position, out of range error for metadata in {file_path}, {error_log}", exc_info=EXC_INFO)
            pass
        except UnboundLocalError as error_log:
            logger.info(f"Variable not declared while extracting metadata from {file_path}, {error_log}", exc_info=EXC_INFO)
            pass
        except ValueError as error_log:
            logger.info(f"Invalid dictionary formatting while extracting metadata from {file_path}, {error_log}", exc_info=EXC_INFO)
            pass

        else:
            return metadata

    def display_metadata(self, metadata, file_path):
        if metadata is not None:
            prompt_keys = ['Positive prompt','Negative prompt', 'Prompt']
            self.top_separator.setText('Prompt Data:')
            self.separator_text.setText('Generation Data:')
            try:
                prompt_data = metadata['Prompts']
                prompt_fields = f"{prompt_data.get('Positive prompt')}\n{prompt_data.get('Negative prompt')}"
                logger.debug(prompt_data.get('Positive prompt'))
                self.upper_box.setText(prompt_fields)
            except TypeError as error_log:
                logger.info(f"Invalid data in prompt fields {type(metadata)} from {file_path}, {metadata} : {error_log}", exc_info=EXC_INFO)
                pass

            except AttributeError as error_log:
                logger.info(f"Attribute cannot be applied to type {type(metadata)} from  {file_path}, {metadata} : {error_log}", exc_info=EXC_INFO)
                pass

            try:
                not_prompt = {k: v for k, v in metadata.get('Prompts').items() if k not in prompt_keys and metadata.get('Prompts', None) is not None}
                generation_data = not_prompt | metadata.get('Settings') | metadata.get('System')
                self.lower_box.setText(pprint.pformat(generation_data))

            except AttributeError as error_log:
                logger.info(f"'items' attribute cannot be applied to type {type(metadata)} from {file_path}, {metadata} : {error_log}", exc_info=EXC_INFO)
                pass


    def load_image_preview(self, file_path):
        # load image file
        pixmap = QPixmap(file_path)
        # scale the image
        self.image_preview.setPixmap(pixmap.scaled(self.image_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def load_text_file(self, file_path):
        with open(file_path, 'r') as f:
            content = f.read()
            self.lower_box.setText(content)