# // SPDX-License-Identifier: CC0-1.0
# // --<{ Ktiseos Nyx }>--

"""Encapsulate the file loader to pass reader data to other functions"""

from encodings import utf_8
from dataset_tools import logger, EXC_INFO
from dataset_tools.widgets import Ext

from PIL import Image, UnidentifiedImageError, ExifTags
from pathlib import Path


class MetadataFileReader:
    """Interface for metadata and text read operations"""

    def __init__(self):
        self.show_content = None  # Example placeholder for UI interaction

    def read_header(self, file_path_named: str) -> dict:
        """
        Direct file read operations for various file formats \n
        :param file_path_named: Location of file with file name and path
        :return: A mapping of information contained within it
        """
        ext = Path(file_path_named).suffix.lower()
        if ext in (Ext.JPEG, Ext.WEBP):
            return self.read_jpg_header(file_path_named)
        if ext in (Ext.PNG_):
            return self.read_png_header(file_path_named)
        if ext in (Ext.TEXT):
            return {"content": self.read_text_file_contents(file_path_named)}

    def read_jpg_header(self, file_path_named):
        """
        Open jpg format files\n
        :param file_path_named: The path and file name of the jpg file
        :return: Generator element containing header tags
        """

        img = Image.open(file_path_named)
        exif = {
            ExifTags.TAGS[label]: content
            for label, content in img._getexif().items()
            if label in ExifTags.TAGS
        }
        logger.debug("exif:: %s", f"{type(exif)} {exif}")
        return exif

    def read_png_header(self, file_path_named):
        """
        Open pnv format files\n
        :param file_path_named: The path and file name of the jpg file
        :return: Generator element containing header tags
        """
        try:
            img = Image.open(file_path_named)
            if img is None:  # We dont need to load completely unless totally necessary
                img.load()  # This is the case when we have no choice but to load (slower)
            logger.debug(f"Metadata from png: {file_path_named}: {img.info}")
            return img.info  # PNG info directly used here
        except UnidentifiedImageError as error_log:
            logger.info(
                "Failed to read image at: %s",
                f" {file_path_named}  {error_log}",
                exc_info=EXC_INFO,
            )
            return None

    def read_text_file_contents(self, file_path_named):
        with open(file_path_named, "r", encoding=utf_8) as f:
            return f.read()  # Reads text file into string
