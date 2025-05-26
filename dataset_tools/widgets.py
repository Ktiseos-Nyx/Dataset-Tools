# widgets.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Widgets""" 

import os
from pathlib import Path
from PyQt6 import QtCore

from dataset_tools.correct_types import ExtensionType as Ext
from dataset_tools.logger import debug_monitor
from dataset_tools.logger import info_monitor as nfo


class FileLoader(QtCore.QThread):
    """Opens files in the UI"""

    finished = QtCore.pyqtSignal(list, list, list, str)
    progress = QtCore.pyqtSignal(int)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.files = [] # Still potentially unused, but not causing this error
        self.images = []
        self.text_files = []
        self.model_files = []

    def run(self):
        """Open selected folder"""
        folder_contents = self.scan_directory(self.folder_path)
        # Using the more robust populate_index_from_list I suggested earlier
        self.images, self.text_files, self.model_files = self.populate_index_from_list(folder_contents)
        self.finished.emit(self.images, self.text_files, self.model_files, self.folder_path)

    # Comment like this should also be indented if it refers to class context
    # In widgets.py, inside the FileLoader class 

    @debug_monitor
    def scan_directory(self, folder_path: str) -> list | None: # scan_directory can return None
        """
        Gather paths to all files in the selected folder\n
        :param folder_path: `str` The directory to scan
        :return: `list` The file contents of the directory, or None on error
        """
        folder_contents = None
        try:
            folder_contents = [os.path.join(folder_path, f) for f in os.listdir(folder_path)]
        except FileNotFoundError as error_log:
            nfo(f"FileNotFoundError: Error loading folder '{folder_path}'. Folder not found.", error_log)
        except PermissionError as error_log:
            nfo(f"PermissionError: Error loading folder '{folder_path}'. Insufficient permissions.", error_log)
        except OSError as error_log:
            nfo(f"OSError: General error loading folder '{folder_path}'. OS related issue.", error_log)
        except Exception as error_log:
            nfo(f"Unexpected error loading folder '{folder_path}'.", error_log)
        return folder_contents

    # VV CORRECT INDENTATION FOR THIS METHOD VV
    @debug_monitor
    def populate_index_from_list(self, folder_contents: list | None) -> tuple[list, list, list]:
        if folder_contents is None:
            nfo("populate_index_from_list received None for folder_contents.")
            return [], [], []

        images = []
        text_and_schema_files = []
        model_files = []

        # Flatten extension lists for easier checking
        all_image_exts = {ext for ext_set in Ext.IMAGE for ext in ext_set}
        
        # Ext.PLAIN is List[Set[str]], e.g. [{'.txt'}, {'.xml'}]
        all_plain_exts_final = set()
        for ext_set in Ext.PLAIN: 
            all_plain_exts_final.update(ext_set)

        all_schema_exts = {ext for ext_set in Ext.SCHEMA for ext in ext_set}
        all_model_exts = {ext for ext_set in Ext.MODEL for ext in ext_set}
        
        all_text_like_exts = all_plain_exts_final.union(all_schema_exts)

        for f_path_str in folder_contents:
            path = Path(str(f_path_str)) 
            if path.is_file() and path.name not in Ext.IGNORE:
                suffix = path.suffix.lower()
                
                if suffix in all_image_exts:
                    images.append(str(path))
                elif suffix in all_text_like_exts:
                    text_and_schema_files.append(str(path))
                elif suffix in all_model_exts:
                    model_files.append(str(path))

        images.sort()
        text_and_schema_files.sort()
        model_files.sort()

        return images, text_and_schema_files, model_files

    # VV CORRECT INDENTATION FOR THIS METHOD VV
    def clear_files(self):
        """Empty file list""" # Corrected typo
        self.files = []
