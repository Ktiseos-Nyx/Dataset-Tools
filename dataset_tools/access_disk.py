#// SPDX-License-Identifier: CC0-1.0
#// --<{ Ktiseos Nyx }>--

"""Encapsulate the file loader to pass reader data to other functions"""

from pathlib import Path as p
from encodings import utf_8
from dataset_tools import logger, EXC_INFO
from dataset_tools.widgets import Ext

from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS
from pathlib import Path as p
import piexif
import piexif.helper

class FileReader:
    """Interface for metadata and text read operations"""

    def __init__(self):
        self.show_content = None  # Example placeholder for UI interaction

    def read_header(self, file_path_named: str) -> dict:
        """
        Direct file read operations for various file formats \n
        :param file_path_named: Location of file with file name and path
        :return: A mapping of information contained within it
        """
        ext = p(file_path_named).suffix.lower()
        if ext in (Ext.JPEG, Ext.WEBP):
            return self.read_jpg_header(file_path_named)
        if ext in (Ext.PNG_):
            return self.read_png_header(file_path_named)
        if ext in (Ext.TEXT):
            return {'content': self.read_text_file_contents(file_path_named)}

    def read_jpg_header(self, file_path_named):
        """
        Open jpg format files\n
        :param file_path_named: The path and file name of the jpg file
        :return: Generator element containing header tags
        """
        try:
            img = Image.open(file_path_named)
            exif = piexif.load(img.info.get('exif')) or {}
            user_comment = exif.get("Exif", {}).get(piexif.ExifIFD.UserComment)
            if user_comment:
                try:
                    self._logger.debug(f"exif data is byte string")
                    comment = piexif.helper.UserComment.load(user_comment)
                    logger.debug(f"Metadata from jpg: {file_path_named}: {comment}")
                    return {"parameters":comment}
                except Exception as e:
                    logger.error(f"Error reading user comment: {file_path_named}: {e}")
                    return {}
            else:
               exif = {TAGS.get(key, val): val for key, val in img.info.items() if key in TAGS}
               logger.debug(f"Metadata from jpg: {file_path_named}: {exif}")
               return exif
        except Exception as e:
            logger.error(f"Error in read_jpg_header: {file_path_named}: {e}")
            return None


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
            logger.info("Failed to read image at: %s", f" {file_path_named}  {error_log}", exc_info=EXC_INFO)
            return None

    def read_text_file_contents(self, file_path_named):
        with open(file_path_named, "r", encoding=utf_8) as f:
            return f.read()  # Reads text file into string
