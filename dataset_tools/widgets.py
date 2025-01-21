# // SPDX-License-Identifier: CC0-1.0
# // --<{ Ktiseos Nyx }>--

"""資料夾內容"""

import os
from pathlib import Path as p
from PyQt6 import QtCore

from dataset_tools.correct_types import ExtensionType as Ext
from dataset_tools.logger import debug_monitor
from dataset_tools.logger import info_monitor as nfo


class FileLoader(QtCore.QThread):  # pylint: disable=c-extension-no-member
    """Opens files in the UI"""

    finished = QtCore.pyqtSignal(list, list, str)  # pylint: disable=c-extension-no-member
    progress = QtCore.pyqtSignal(int)  # pylint: disable=c-extension-no-member

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.files = []
        self.images = []
        self.text_files = []
        # self.model_files = []

    def run(self):
        """Open selected folder"""
        folder_contents = self.scan_directory(self.folder_path)
        self.images, self.text_files = self.populate_index_from_list(folder_contents)  # self.model_files
        self.finished.emit(self.images, self.text_files, self.folder_path)  # self.model_files,

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
            nfo("Error loading folder", folder_path, error_log)
        return folder_contents

    @debug_monitor
    def populate_index_from_list(self, folder_contents: list) -> tuple[list]:
        """
        Create an index of relevant files from a list\n
        :param folder_contents: The absolute paths of the contents of a folder
        :type folder_contents: `list`
        :return: `tuple[list]` Images and text files that can be loaded by the system
        """
        image_files = []
        text_files = []
        # model_files = []
        file_count = len(folder_contents)
        progress = 0
        for index, file_path in enumerate(folder_contents):
            if os.path.isfile(file_path) and os.path.basename(file_path) not in Ext.IGNORE:  # Filter out .DS_Store
                suffix = p(file_path).suffix.lower()
                extension_types = [Ext.IMAGE, Ext.EXIF, Ext.SCHEMA, Ext.PLAIN]  # , Ext.MODEL]
                for extension in extension_types:
                    for file_type in extension:
                        if suffix in file_type and file_type in Ext.IMAGE:
                            image_files.append(file_path)
                        elif suffix in file_type and file_type in Ext.PLAIN or file_type in Ext.SCHEMA:
                            text_files.append(file_path)
                        # elif suffix in file_type and file_type in Ext.MODEL:
                        #     model_files.append(file_path)
            progress = (index + 1) / file_count * 100
            self.progress.emit(int(progress))

        if image_files:
            image_files.sort()
        if text_files:
            text_files.sort()
        return image_files, text_files  # , model_files

    def clear_files(self):
        """Empty file ilst"""
        self.files = []
