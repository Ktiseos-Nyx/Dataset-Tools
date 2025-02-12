# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""Wrap I/O"""

from pathlib import Path
import os
import json
import toml

from PIL import Image, UnidentifiedImageError, ExifTags # Keep ExifTags import
from exiftool import ExifToolHelper  # Import python-exiftool

from dataset_tools.logger import debug_message, debug_monitor
from dataset_tools.logger import info_monitor as nfo
from dataset_tools.correct_types import EmptyField, ExtensionType as Ext, DownField, UpField
from dataset_tools.model_tool import ModelTool


class MetadataFileReader:
    """Interface for metadata and text read operations"""

    def __init__(self):
        self.show_content = None  # Example placeholder for UI interaction

    @debug_monitor
    def read_jpg_header_exiftool(self, file_path_named):
        """
        Open jpg format files using ExifTool for robust metadata extraction\n
        :param file_path_named: The path and file name of the jpg file
        :return: Dictionary of header tags from ExifTool, or None on error
        """
        with ExifToolHelper() as et:
            try:
                exiftool_metadata_list = et.get_metadata([file_path_named])
                if exiftool_metadata_list:
                    return exiftool_metadata_list[0]
                else:
                    return None
            except Exception as e:
                print(f"ExifTool error reading JPG {file_path_named}: {e}")
                return None

    @debug_monitor
    def read_jpg_header_pillow(self, file_path_named): # Pillow version for fallback
        """
        Open jpg format files using Pillow for basic EXIF header extraction\n
        :param file_path_named: The path and file name of the jpg file
        :return: Dictionary of header tags from Pillow, or None if no EXIF
        """
        try:
            img = Image.open(file_path_named)
            exif_data = img._getexif() # Use _getexif for Pillow
            if exif_data:
                exif_tags = {EXIF_TAGS[key]: val for key, val in exif_data.items() if key in EXIF_TAGS}
                return exif_tags
            else:
                return None # No EXIF data found by Pillow
        except Exception as e: # More general exception catching for Pillow too
            print(f"Pillow error reading JPG header {file_path_named}: {e}")
            return None


    @debug_monitor
    def read_png_header_exiftool(self, file_path_named):
        """
        Open png format files using ExifTool for metadata extraction\n
        :param file_path_named: The path and file name of the png file
        :return: Dictionary of header tags from ExifTool, or None on error
        """
        with ExifToolHelper() as et:
            try:
                exiftool_metadata_list = et.get_metadata([file_path_named])
                if exiftool_metadata_list:
                    return exiftool_metadata_list[0]
                else:
                    return None
            except Exception as e:
                print(f"ExifTool error reading PNG {file_path_named}: {e}")
                return None

    @debug_monitor
    def read_png_header_pillow(self, file_path_named): # Pillow version for fallback
        """
        Open png format files using Pillow for basic info (can switch to ExifTool if needed)\n
        :param file_path_named: The path and file name of the png file
        :return: Dictionary of header tags (from Pillow info for PNG), or None on error
        """
        try:
            img = Image.open(file_path_named)
            if img is None:
                img.load()
            return img.info  # Use Pillow for PNG info
        except UnidentifiedImageError as error_log:
            nfo("Failed to read PNG image at:", file_path_named, error_log)
            return None
        except Exception as e: # More general exception catching for Pillow too
            print(f"Pillow error reading PNG header {file_path_named}: {e}")
            return None


    def read_txt_contents(self, file_path_named):
        """
        Open plaintext files\n
        :param file_path_named: The path and file name of the text file
        :return: Generator element containing content
        """
        # ... (rest of read_txt_contents - no changes needed) ...


    def read_schema_file(self, file_path_named: str, mode="r"):
        """
        Open .json or toml files\n
        :param file_path_named: The path and file name of the json file
        :return: Generator element containing content
        """
        # ... (rest of read_schema_file - no changes needed) ...


    @debug_monitor
    def read_header(self, file_path_named: str) -> dict:
        """
        Direct file read operations for various file formats, with ExifTool fallback\n
        :param file_path_named: Location of file with file name and path
        :return: A mapping of information contained within it
        """
        ext = Path(file_path_named).suffix.lower()
        if ext in Ext.JPEG:
            metadata = self.read_jpg_header_exiftool(file_path_named) # Try ExifTool first for JPG
            if metadata is None:
                metadata = self.read_jpg_header_pillow(file_path_named) # Fallback to Pillow if ExifTool fails
            return metadata

        if ext in Ext.PNG_:
            metadata = self.read_png_header_exiftool(file_path_named) # Try ExifTool first for PNG
            if metadata is None:
                metadata = self.read_png_header_pillow(file_path_named) # Fallback to Pillow if ExifTool fails
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
