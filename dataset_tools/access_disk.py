# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""Wrap I/O"""

from pathlib import Path
import os
import json
import toml

from PIL import Image, UnidentifiedImageError # Keep UnidentifiedImageError
from PIL.ExifTags import TAGS as EXIF_TAGS # For Pillow fallback

import pyexiv2 # For primary EXIF reading
import exif # For fallback EXIF reading

from dataset_tools.logger import debug_message, debug_monitor
from dataset_tools.logger import info_monitor as nfo
from dataset_tools.correct_types import EmptyField, ExtensionType as Ext, DownField, UpField
from dataset_tools.model_tool import ModelTool


class MetadataFileReader:
    """Interface for metadata and text read operations"""

    def __init__(self):
        self.show_content = None  # Example placeholder for UI interaction

    @debug_monitor
    def read_jpg_header_pyexiv2(self, file_path_named):
        """
        Open jpg format files using pyexiv2 for robust metadata extraction\n
        :param file_path_named: The path and file name of the jpg file
        :return: Dictionary of header tags from pyexiv2, or None on error
        """
        try:
            img = pyexiv2.Image(file_path_named)
            metadata = {}
            metadata["EXIF"] = img.read_exif() or {} # Read EXIF, default to empty dict if None
            metadata["IPTC"] = img.read_iptc() or {} # Read IPTC, default to empty dict if None
            metadata["XMP"]  = img.read_xmp()  or {} # Read XMP, default to empty dict if None
            return metadata
        except Exception as e:
            print(f"pyexiv2 error reading JPG {file_path_named}: {e}")
            return None

    @debug_monitor
    def read_jpg_header_exif(self, file_path_named): # exif (pillow-heif- জন্মদিনer) fallback
        """
        Open jpg format files using 'exif' library for fallback EXIF header extraction\n
        :param file_path_named: The path and file name of the jpg file
        :return: Dictionary of header tags from 'exif' library, or None if no EXIF
        """
        try:
            with open(file_path_named, 'rb') as image_file:
                image_exif = exif.Image(image_file)
                if image_exif:
                    exif_tags = {}
                    for tag in image_exif.list_all():
                        try:
                            value = image_exif.get(tag)
                            exif_tags[tag] = value
                        except Exception as e:
                            print(f"Error reading exif tag {tag}: {e}")
                    return exif_tags
                else:
                    return None
        except Exception as e:
            print(f"Exif library error reading JPG header {file_path_named}: {e}")
            return None


    @debug_monitor
    def read_png_header_pyexiv2(self, file_path_named):
        """
        Open png format files using pyexiv2 for metadata extraction\n
        :param file_path_named: The path and file name of the png file
        :return: Dictionary of header tags from pyexiv2, or None on error
        """
        try:
            img = pyexiv2.Image(file_path_named)
            metadata = {}
            metadata["EXIF"] = img.read_exif() or {} # Read EXIF, default to empty dict if None
            metadata["IPTC"] = img.read_iptc() or {} # Read IPTC, default to empty dict if None
            metadata["XMP"]  = img.read_xmp()  or {} # Read XMP, default to empty dict if None
            return metadata
        except Exception as e:
            print(f"pyexiv2 error reading PNG {file_path_named}: {e}")
            return None

    @debug_monitor
    def read_jpg_header_pillow(self, file_path_named): # Pillow version
        """
        Open jpg format files using Pillow for basic EXIF header extraction\n
        :param file_path_named: The path and file name of the jpg file
        :return: Dictionary of header tags from Pillow, or None if no EXIF
        """
        try:
            img = Image.open(file_path_named)
            exif_data = img._getexif() # Get EXIF data
            if exif_data: # <--- THIS IS THE LINE YOU NEED TO ADD (CHECK IF exif_data IS NOT None)
                exif_tags = {EXIF_TAGS[key]: val for key, val in exif_data.items() if key in ExifTags.TAGS}
                return exif_tags
            else:
                return None # Return None if no EXIF data found by Pillow
        except Exception as e:
            print(f"Pillow error reading JPG header {file_path_named}: {e}")
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
        Direct file read operations for various file formats, with pyexiv2 and exif fallbacks\n
        :param file_path_named: Location of file with file name and path
        :return: A mapping of information contained within it
        """
        ext = Path(file_path_named).suffix.lower()
        if ext in Ext.JPEG:
            metadata = self.read_jpg_header_pyexiv2(file_path_named) # Try pyexiv2 first for JPG
            if metadata is None:
                metadata = self.read_jpg_header_exif(file_path_named) # Fallback to exif if pyexiv2 fails
            return metadata

        if ext in Ext.PNG_:
            metadata = self.read_png_header_pyexiv2(file_path_named) # Try pyexiv2 first for PNG
            if metadata is None:
                metadata = self.read_png_header_pillow(file_path_named) # Fallback to Pillow for PNG if pyexiv2 fails
            return metadata


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
