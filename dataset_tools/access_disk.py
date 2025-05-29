# dataset_tools/access_disk.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

from pathlib import Path

# import os # Not currently used directly in this file's active code
import json
import toml
import traceback
import logging as pylog  # For self._logger initialization

import pyexiv2

from .logger import debug_monitor
from .logger import info_monitor as nfo
from .correct_types import EmptyField, ExtensionType as Ext, DownField, UpField
# from .model_tool import ModelTool # Using local import in read_file_data_by_type


class MetadataFileReader:
    """Interface for metadata and text read operations"""

    def __init__(self):  # THIS IS THE __INIT__ TO KEEP
        # Using a named logger for this class
        self._logger = pylog.getLogger(f"dataset_tools.access_disk.{self.__class__.__name__}")
        # Ensure this logger is configured by your main setup to output desired levels.
        # If it's not configured, its messages (like self._logger.debug) might not appear.

    # --- Methods for Standard Photographic EXIF/XMP/IPTC (using pyexiv2) ---

    @debug_monitor
    def read_png_header_pyexiv2(self, file_path_named: str) -> dict | None:
        nfo(f"[MDFileReader] Reading PNG with pyexiv2 for standard metadata: {file_path_named}")
        try:
            img = pyexiv2.Image(file_path_named)
            metadata = {"EXIF": img.read_exif() or {}, "IPTC": img.read_iptc() or {}, "XMP": img.read_xmp() or {}}
            img.close()
            if not metadata["EXIF"] and not metadata["IPTC"] and not metadata["XMP"]:
                nfo(f"[MDFileReader] pyexiv2 found no standard EXIF/IPTC/XMP in PNG: {file_path_named}")
                return None
            return metadata
        except Exception as e:
            nfo(f"[MDFileReader] pyexiv2 error reading PNG standard metadata {file_path_named}: {e}")
            # self._logger.error(f"pyexiv2 PNG error for {file_path_named}", exc_info=True) # More detailed log
            return None

    @debug_monitor
    def read_txt_contents(self, file_path_named: str) -> dict | None:
        nfo(f"[MDFileReader] Reading TXT: {file_path_named}")
        encodings_to_try = ["utf-8", "utf-16", "latin-1"]
        for enc in encodings_to_try:
            try:
                with open(file_path_named, "r", encoding=enc) as open_file:
                    file_contents = open_file.read()
                    return {UpField.TEXT_DATA.value: file_contents}
            except UnicodeDecodeError:
                continue
            except Exception as e:
                nfo(f"[MDFileReader] Error reading TXT {file_path_named} with encoding {enc}: {e}")
                return None
        nfo(f"[MDFileReader] Failed to decode TXT {file_path_named} with common encodings.")
        return None

    @debug_monitor
    def read_schema_file(self, file_path_named: str) -> dict | None:
        nfo(f"[MDFileReader] Reading schema file: {file_path_named}")
        header_field_enum = DownField.JSON_DATA
        loader = None
        mode = "r"
        path_obj = Path(file_path_named)
        ext = path_obj.suffix.lower()

        is_toml = any(ext in ext_set for ext_set in Ext.TOML) if isinstance(Ext.TOML, list) else ext in Ext.TOML
        is_json = any(ext in ext_set for ext_set in Ext.JSON) if isinstance(Ext.JSON, list) else ext in Ext.JSON

        if is_toml:
            loader = toml.load
            mode = "rb"
            header_field_enum = DownField.TOML_DATA
        elif is_json:
            loader = json.load
            mode = "r"
            header_field_enum = DownField.JSON_DATA
        else:
            nfo(f"[MDFileReader] Unknown schema file type for {file_path_named} (ext: {ext})")
            return None
        try:
            open_kwargs = {"encoding": "utf-8"} if mode == "r" else {}
            with open(file_path_named, mode, **open_kwargs) as open_file:
                file_contents = loader(open_file)
                return {header_field_enum.value: file_contents}
        except (toml.TomlDecodeError, json.JSONDecodeError) as error_log:
            nfo(f"[MDFileReader] Schema decode error for {file_path_named}: {error_log}")
            return {EmptyField.PLACEHOLDER.value: {"Error": f"Invalid {ext.upper()[1:]} format."}}
        except Exception as e:
            nfo(f"[MDFileReader] Error reading schema file {file_path_named}: {e}")
            return None

    @debug_monitor
    def read_jpg_header_pyexiv2(self, file_path_named: str) -> dict | None:
        nfo(f"[MDFileReader] Reading JPG with pyexiv2: {file_path_named}")
        try:
            img = pyexiv2.Image(file_path_named)
            exif_tags = img.read_exif()
            iptc_tags = img.read_iptc()
            xmp_tags = img.read_xmp()

            metadata = {"EXIF": exif_tags or {}, "IPTC": iptc_tags or {}, "XMP": xmp_tags or {}}

            if exif_tags and "Exif.Photo.UserComment" in exif_tags:
                uc_val_from_read_exif = exif_tags["Exif.Photo.UserComment"]
                self._logger.debug(  # Using self._logger now that it's initialized
                    f"[MDFileReader] UserComment type from read_exif for {Path(file_path_named).name}: {type(uc_val_from_read_exif)}"
                )
                if isinstance(uc_val_from_read_exif, str) and uc_val_from_read_exif.startswith("charset="):
                    self._logger.debug(
                        f"[MDFileReader] UserComment from read_exif appears to be an already decoded string with charset prefix for {Path(file_path_named).name}."
                    )
            img.close()
            if not metadata["EXIF"] and not metadata["IPTC"] and not metadata["XMP"]:
                nfo(f"[MDFileReader] pyexiv2 found no EXIF/IPTC/XMP in JPG: {file_path_named}")
                return None
            return metadata
        except Exception as e:
            nfo(f"[MDFileReader] pyexiv2 error reading JPG {file_path_named}: {e}")
            traceback.print_exc()
            return None

    @debug_monitor
    def read_file_data_by_type(self, file_path_named: str) -> dict | None:
        nfo(f"[MDFileReader] Dispatching read for: {file_path_named}")
        path_obj = Path(file_path_named)
        ext_lower = path_obj.suffix.lower()

        is_text_plain = (
            any(ext_lower in ext_set for ext_set in Ext.PLAIN_TEXT_LIKE)
            if isinstance(Ext.PLAIN_TEXT_LIKE, list)
            else ext_lower in Ext.PLAIN_TEXT_LIKE
        )
        is_schema = (
            any(ext_lower in ext_set for ext_set in Ext.SCHEMA_FILES)
            if isinstance(Ext.SCHEMA_FILES, list)
            else ext_lower in Ext.SCHEMA_FILES
        )
        is_jpg = (
            any(ext_lower in ext_set for ext_set in Ext.JPEG) if isinstance(Ext.JPEG, list) else ext_lower in Ext.JPEG
        )
        is_png = (
            any(ext_lower in ext_set for ext_set in Ext.PNG_) if isinstance(Ext.PNG_, list) else ext_lower in Ext.PNG_
        )
        is_model_file = (
            any(ext_lower in ext_set for ext_set in Ext.MODEL_FILES)
            if isinstance(Ext.MODEL_FILES, list)
            else ext_lower in Ext.MODEL_FILES
        )

        if is_text_plain:
            return self.read_txt_contents(file_path_named)
        elif is_schema:
            return self.read_schema_file(file_path_named)
        elif is_jpg:
            return self.read_jpg_header_pyexiv2(file_path_named)
        elif is_png:
            return self.read_png_header_pyexiv2(file_path_named)
        elif is_model_file:
            try:
                from .model_tool import ModelTool

                tool = ModelTool()
                return tool.read_metadata_from(file_path_named)
            except ImportError:  # pragma: no cover
                nfo(f"[MDFileReader] ModelTool not available for import. Cannot process model file: {path_obj.name}")
                return {
                    EmptyField.PLACEHOLDER.value: {
                        "Info": f"Model file ({ext_lower}) - ModelTool parser not available."
                    }
                }
            except Exception as e_model:  # pragma: no cover
                nfo(f"[MDFileReader] Error using ModelTool for {path_obj.name}: {e_model}")
                return {EmptyField.PLACEHOLDER.value: {"Error": f"Could not parse model file: {e_model}"}}
        else:
            nfo(f"[MDFileReader] File type {ext_lower} for {path_obj.name} is not handled by this dispatcher.")
            return None
