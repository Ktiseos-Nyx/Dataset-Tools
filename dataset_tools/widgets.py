"""Widget contents"""

import os
from pathlib import Path as p
from PyQt6 import QtCore

from dataset_tools import logger, EXC_INFO

class Ext:
    """Valid file formats for metadata reading"""
    PNG_ = [".png"]
    JPEG = ['.jpg','.jpeg']
    WEBP = ['.webp']
    TEXT = ['.txt']

class FileLoader(QtCore.QThread): # pylint: disable=c-extension-no-member
    """Opens files in the UI"""
    finished = QtCore.pyqtSignal(list, list, str) # pylint: disable=c-extension-no-member
    progress = QtCore.pyqtSignal(int) # pylint: disable=c-extension-no-member

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.files = []
        self.images = []
        self.text_files = []

    def run(self):
        """Open selected folder"""
        folder_contents              = self.scan_directory(self.folder_path)
        self.images, self.text_files = self.populate_index_from_list(folder_contents)
        self.finished.emit(self.images, self.text_files, self.folder_path)

    def scan_directory(self, folder_path:str ) -> list:
        """
        # Gather paths to all files in the selected folder\n
        :param folder_path: `str` The directory to scan
        :return: `list` The file contents of the directory
        """

        try:
            folder_contents = [os.path.join(folder_path, f) for f in os.listdir(folder_path)]
        except FileNotFoundError as error_log:
            logger.info("Error loading folder %s",f"{folder_path} {error_log}", exc_info=EXC_INFO)
        else:
            return folder_contents

    def populate_index_from_list(self,folder_contents: list)-> tuple[list]:
        """
        Create an index of relevant files from a list\n
        :param :
        :return: `tuple[list]` Images and text files that can be loaded by the system
        """
        image_files = []
        text_files = []
        file_count = len(folder_contents)
        progress = 0
        for index, file_path in enumerate(folder_contents):
            if os.path.isfile(file_path) and not file_path.endswith(".DS_Store"): #Filter out .DS_Store
            # Filter the file types as needed
                if p(file_path).suffix.lower() in Ext.PNG_ or p(file_path).suffix.lower() in Ext.JPEG or p(file_path).suffix.lower() in Ext.WEBP:
                    image_files.append(file_path)
                if p(file_path).suffix.lower() in Ext.TEXT:
                    text_files.append(file_path)
            progress = (index + 1)/file_count * 100
            self.progress.emit(int(progress))
        logger.debug("%s",f"{image_files, text_files}")
        return image_files, text_files

    def clear_files(self):
        """Empty file ilst"""
        self.files = []
