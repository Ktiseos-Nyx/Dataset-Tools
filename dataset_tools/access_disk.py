# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""Wrap I/O"""

from pathlib import Path
import os
import json
import toml

from PIL import Image, UnidentifiedImageError, ExifTags

from dataset_tools.logger import debug_message, debug_monitor
from dataset_tools.logger import info_monitor as nfo
from dataset_tools.correct_types import EmptyField, ExtensionType as Ext, DownField, UpField
from dataset_tools.model_tool import ModelTool


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
        exif_tags = {ExifTags.TAGS[key]: val for key, val in img._getexif().items() if key in ExifTags.TAGS}  # pylint: disable=protected-access, line-too-long
        return exif_tags

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

    def read_txt_contents(self, file_path_named):
        """
        Open plaintext files\n
        :param file_path_named: The path and file name of the text file
        :return: Generator element containing content
        """
        try:
            with open(file_path_named, "r", encoding="utf_8") as open_file:
                file_contents = open_file.read()
                metadata = {
                    UpField.TEXT_DATA: file_contents,
                    EmptyField.EMPTY: {"": "EmptyField.PLACEHOLDER"},
                }
                return metadata  # Reads text file into string
        except UnicodeDecodeError as error_log:
            nfo("File did not match expected unicode format %s", file_path_named)
            debug_message(error_log)
        try:
            with open(file_path_named, "r", encoding="utf_16-be") as open_file:
                file_contents = open_file.read()
                metadata = {
                    UpField.TEXT_DATA: file_contents,
                    EmptyField.EMPTY: {"": "EmptyField.PLACEHOLDER"},
                }
                return metadata  # Reads text file into string
        except UnicodeDecodeError as error_log:
            nfo("File did not match expected unicode format %s", file_path_named)
            debug_message(error_log)

    def read_schema_file(self, file_path_named: str, mode="r"):
        """
        Open .json or toml files\n
        :param file_path_named: The path and file name of the json file
        :return: Generator element containing content
        """
        header_field = DownField.RAW_DATA
        _, ext = os.path.splitext(file_path_named)
        if ext == Ext.TOML:
            loader, mode = (toml.load, "rb")
            header_field = DownField.JSON_DATA
        else:
            loader, mode = (json.load, "r")
            header_field = DownField.JSON_DATA
        with open(file_path_named, mode, encoding="utf_8") as open_file:
            try:
                file_contents = loader(open_file)
            except (toml.TomlDecodeError, json.decoder.JSONDecodeError) as error_log:
                raise SyntaxError(f"Couldn't read file {file_path_named}") from error_log
            else:
                metadata = {
                    EmptyField.EMPTY: {"": "EmptyField.PLACEHOLDER"},
                    header_field: file_contents,
                }
        return metadata

    @debug_monitor
    def read_header(self, file_path_named: str) -> dict:
        """
        Direct file read operations for various file formats\n
        :param file_path_named: Location of file with file name and path
        :return: A mapping of information contained within it
        """
        ext = Path(file_path_named).suffix.lower()
        if ext in Ext.JPEG:
            return self.read_jpg_header(file_path_named)
        if ext in Ext.PNG_:
            return self.read_png_header(file_path_named)
        for file_types in Ext.SCHEMA:
            if ext in file_types:
                return self.read_txt_contents(file_path_named)
        for file_types in Ext.PLAIN:
            if ext in file_types:
                return self.read_txt_contents(file_path_named)

        for file_types in Ext.MODEL:
            if ext in file_types:
                model_tool = ModelTool()
                return model_tool.read_metadata_from(file_path_named)

        # if header:
        #     return header(file_path_named)
