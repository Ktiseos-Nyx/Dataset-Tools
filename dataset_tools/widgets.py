# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""Widgets"""

import os
from pathlib import Path
from PyQt6 import QtCore

from dataset_tools.correct_types import ExtensionType as Ext
from dataset_tools.logger import debug_monitor
from dataset_tools.logger import info_monitor as nfo


class FileLoader(QtCore.QThread):  # pylint: disable=c-extension-no-member - PyQt6 properties are dynamically added by C extensions, Pylint can't see them.
    """Opens files in the UI"""

    finished = QtCore.pyqtSignal(list, list, list, str)  # pylint: disable=c-extension-no-member - PyQt6 properties are dynamically added by C extensions, Pylint can't see them.
    progress = QtCore.pyqtSignal(int)  # pylint: disable=c-extension-no-member - PyQt6 properties are dynamically added by C extensions, Pylint can't see them.

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.files = []
        self.images = []
        self.text_files = []
        self.model_files = []

    def run(self):
        """Open selected folder"""
        folder_contents = self.scan_directory(self.folder_path)
        self.images, self.text_files, self.model_files = self.populate_index_from_list(folder_contents)  # pylint: disable=line-too-long
        self.finished.emit(self.images, self.text_files, self.model_files, self.folder_path)

    # In widgets.py, inside the FileLoader class

    @debug_monitor
    def scan_directory(self, folder_path: str) -> list:
        """
        Gather paths to all files in the selected folder\n
        :param folder_path: `str` The directory to scan
        :return: `list` The file contents of the directory
        """
        folder_contents = None
        try:
            folder_contents = [os.path.join(folder_path, f) for f in os.listdir(folder_path)]
        except FileNotFoundError as error_log:
            nfo(f"FileNotFoundError: Error loading folder '{folder_path}'. Folder not found.", error_log) # More specific message
        except PermissionError as error_log: # Catch PermissionError specifically
            nfo(f"PermissionError: Error loading folder '{folder_path}'. Insufficient permissions.", error_log) # More specific message
        except OSError as error_log: # Catch other OS errors
            nfo(f"OSError: General error loading folder '{folder_path}'. OS related issue.", error_log) # More general OS error
        except Exception as error_log: # Catch any other unexpected errors
            nfo(f"Unexpected error loading folder '{folder_path}'.", error_log) # Catch-all for other exceptions
        return folder_contents

    @debug_monitor
    def populate_index_from_list(self, folder_contents: list) -> tuple[list]:
        """
        Create an index of relevant files from a list\n
        :param folder_contents: The absolute paths of the contents of a folder
        :type folder_contents: `list`
        :return: `tuple[list]` Images and text files that can be loaded by the system
        """
        types = {"image": Ext.IMAGE, "plain": [Ext.PLAIN, Ext.SCHEMA], "model": Ext.MODEL}
        categorized_files = {key: [] for key in types}

        for f_path in folder_contents:
            path = Path(f_path)
            if path.is_file() and path.name not in Ext.IGNORE:
                suffix = path.suffix.lower()
                for cat, exts in types.items():
                    if any(suffix in ext for ext in exts):
                        categorized_files[cat].append(str(path))

        for files in categorized_files.values():
            files.sort()

        return (*categorized_files.values(),)

    def clear_files(self):
        """Empty file ilst"""
        self.files = []
