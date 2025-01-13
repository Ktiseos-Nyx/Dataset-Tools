# // SPDX-License-Identifier: CC0-1.0
# // --<{ Ktiseos Nyx }>--

"""Wrap I/O"""

from pathlib import Path
import os
import json
import toml

from dataset_tools.logger import debug_monitor
from dataset_tools.logger import info_monitor as nfo
from dataset_tools.correct_types import ExtensionType as Ext

from PIL import Image, UnidentifiedImageError, ExifTags


class MetadataFileReader:
    """Interface for metadata and text read operations"""

    def __init__(self):
        self.show_content = None  # Example placeholder for UI interaction

    @debug_monitor
    def read_jpg_header(self, file_path_named):
        """
        Open jpg format files\n
        :param file_path_named: The path and file name of the jpg file
        :return: Generator element containing header tags
        """

        img = Image.open(file_path_named)
        exif = {ExifTags.TAGS[label]: content for label, content in img.getexif().items() if label in ExifTags.TAGS}
        return exif

    @debug_monitor
    def read_png_header(self, file_path_named):
        """
        Open png format files\n
        :param file_path_named: The path and file name of the png file
        :return: Generator element containing header tags
        """
        try:
            img = Image.open(file_path_named)
            if img is None:  # We dont need to load completely unless totally necessary
                img.load()  # This is the case when we have no choice but to load (slower)
            return img.info  # PNG info directly used here
        except UnidentifiedImageError as error_log:
            nfo("Failed to read image at:", file_path_named, error_log)
            return None

    def read_text_file_contents(self, file_path_named):
        """
        Open plaintext files\n
        :param file_path_named: The path and file name of the text file
        :return: Generator element containing content
        """
        with open(file_path_named, "r", encoding="utf_8") as f:
            contents = f.read()
            return {"Content": contents}  # Reads text file into string

    def read_schema_file(self, file_path_named: str, mode="r"):
        """
        Open .json or toml files\n
        :param file_path_named: The path and file name of the json file
        :return: Generator element containing content
        """
        _, ext = os.path.splitext(file_path_named)
        loader, mode = (toml.load, "rb") if ext == Ext.TOML else (json.load, "r")
        with open(file_path_named, mode) as f:
            try:
                file_contents = loader(f)
            except (toml.TomlDecodeError, json.decoder.JSONDecodeError) as errorlog:
                raise SyntaxError(f"Couldn't read file {file_path_named}") from errorlog
        return file_contents

    @debug_monitor
    def read_header(self, file_path_named: str) -> dict:
        """
        Direct file read operations for various file formats\n
        :param file_path_named: Location of file with file name and path
        :return: A mapping of information contained within it
        """
        ext = Path(file_path_named).suffix.lower()
        if ext in (Ext.EXIF):
            return self.read_jpg_header(file_path_named)
        elif ext in (Ext.PNG_):
            return self.read_png_header(file_path_named)
        elif ext in (Ext.PLAIN):
            return self.read_text_file_contents(file_path_named)
        elif ext in (Ext.SCHEMA):
            return self.read_text_file_contents(file_path_named)
