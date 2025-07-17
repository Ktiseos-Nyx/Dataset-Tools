# dataset_tools/access_disk.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Disk access utilities for reading and writing configuration files.

This module handles reading and writing of various configuration file formats
including JSON, TOML, and provides utilities for safe file operations.
"""

import json
import logging as pylog
import traceback
from pathlib import Path

import pyexiv2  # Assuming pyexiv2 is a required dependency
import toml

from .correct_types import DownField, EmptyField, UpField
from .correct_types import ExtensionType as Ext
from .logger import debug_monitor
from .logger import info_monitor as nfo


class MetadataFileReader:
    """Interface for metadata and text read operations"""

    def __init__(self):
        self._logger = pylog.getLogger(
            f"dataset_tools.access_disk.{self.__class__.__name__}",
        )

    @debug_monitor
    def read_png_header_pyexiv2(self, file_path_named: str) -> dict | None:
        """Read PNG metadata using pyexiv2.

        Args:
            file_path_named: Path to the PNG file

        Returns:
            Dictionary containing EXIF, IPTC, and XMP metadata, or None if failed

        """
        nfo(
            f"[MDFileReader] Reading PNG with pyexiv2 for standard metadata: {file_path_named}",
        )
        try:
            img = pyexiv2.Image(file_path_named)
            metadata = {
                "EXIF": img.read_exif() or {},
                "IPTC": img.read_iptc() or {},
                "XMP": img.read_xmp() or {},
            }
            img.close()
            if not metadata["EXIF"] and not metadata["IPTC"] and not metadata["XMP"]:
                nfo(
                    f"[MDFileReader] pyexiv2 found no standard EXIF/IPTC/XMP in PNG: {file_path_named}",
                )
                return None
            return metadata
        except pyexiv2.Exiv2Error as exiv_err:
            nfo(
                f"[MDFileReader] pyexiv2 Exiv2Error reading PNG standard metadata {file_path_named}: {exiv_err}",
            )
            return None
        except OSError as io_err:
            nfo(
                f"[MDFileReader] pyexiv2 IOError reading PNG standard metadata {file_path_named}: {io_err}",
            )
            return None
        except Exception as e:  # pylint: disable=broad-except
            nfo(
                f"[MDFileReader] pyexiv2 general error reading PNG standard metadata {file_path_named}: {e}",
            )
            # self._logger.error("pyexiv2 PNG error for %s", file_path_named, exc_info=True) # Example of lazy logging for error
            return None

    @debug_monitor
    def read_txt_contents(self, file_path_named: str) -> dict | None:
        nfo(f"[MDFileReader] Reading TXT: {file_path_named}")
        encodings_to_try = ["utf-8", "utf-16", "latin-1"]
        for enc in encodings_to_try:
            try:
                with open(file_path_named, encoding=enc) as open_file:
                    file_contents = open_file.read()
                    return {UpField.TEXT_DATA.value: file_contents}
            except UnicodeDecodeError:
                continue
            except OSError as file_err:
                nfo(
                    f"[MDFileReader] File Error reading TXT {file_path_named} with encoding {enc}: {file_err}",
                )
                return None  # Or perhaps `break` to stop trying other encodings if it's a file system error
            except Exception as e:  # pylint: disable=broad-except
                nfo(
                    f"[MDFileReader] General Error reading TXT {file_path_named} with encoding {enc}: {e}",
                )
                return None
        nfo(
            f"[MDFileReader] Failed to decode TXT {file_path_named} with common encodings.",
        )
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
            mode = "rb"  # toml usually prefers binary mode for load(file_obj)
            header_field_enum = DownField.TOML_DATA
        elif is_json:
            loader = json.load
            mode = "r"
            header_field_enum = DownField.JSON_DATA
        else:
            nfo(
                f"[MDFileReader] Unknown schema file type for {file_path_named} (ext: {ext})",
            )
            return None
        try:
            # For toml in 'rb' mode, no encoding kwarg. For json in 'r', utf-8 is good default.
            open_kwargs = {"encoding": "utf-8"} if mode == "r" and is_json else {}
            # type: ignore # open_kwargs might make mode check complex for mypy
            with open(file_path_named, mode, **open_kwargs) as open_file:
                file_contents = loader(open_file)
                return {header_field_enum.value: file_contents}
        except (
            toml.TomlDecodeError,
            json.JSONDecodeError,
        ) as decode_err:  # Renamed error_log
            nfo(
                f"[MDFileReader] Schema decode error for {file_path_named}: {decode_err}",
            )
            return {
                EmptyField.PLACEHOLDER.value: {
                    "Error": f"Invalid {ext.upper()[1:]} format.",
                },
            }
        except OSError as file_err:
            nfo(
                f"[MDFileReader] File Error reading schema file {file_path_named}: {file_err}",
            )
            return None
        except Exception as e:  # pylint: disable=broad-except
            nfo(
                f"[MDFileReader] General Error reading schema file {file_path_named}: {e}",
            )
            return None

    @debug_monitor
    def read_jpg_header_pyexiv2(self, file_path_named: str) -> dict | None:
        nfo(f"[MDFileReader] Reading JPG with pyexiv2: {file_path_named}")
        try:
            img = pyexiv2.Image(file_path_named)
            exif_tags = img.read_exif()
            iptc_tags = img.read_iptc()
            xmp_tags = img.read_xmp()

            metadata = {
                "EXIF": exif_tags or {},
                "IPTC": iptc_tags or {},
                "XMP": xmp_tags or {},
            }

            if exif_tags and "Exif.Photo.UserComment" in exif_tags:
                uc_val_from_read_exif = exif_tags["Exif.Photo.UserComment"]
                # Corrected lazy logging:
                self._logger.debug(
                    "[MDFileReader] UserComment type from read_exif for %s: %s",
                    Path(file_path_named).name,
                    type(uc_val_from_read_exif),
                )
                if isinstance(
                    uc_val_from_read_exif,
                    str,
                ) and uc_val_from_read_exif.startswith("charset="):
                    # Corrected lazy logging:
                    self._logger.debug(
                        "[MDFileReader] UserComment from read_exif appears to be an already decoded string with charset prefix for %s.",
                        Path(file_path_named).name,
                    )
            img.close()
            if not metadata["EXIF"] and not metadata["IPTC"] and not metadata["XMP"]:
                nfo(
                    f"[MDFileReader] pyexiv2 found no EXIF/IPTC/XMP in JPG: {file_path_named}",
                )
                return None
            return metadata
        except pyexiv2.Exiv2Error as exiv_err:
            nfo(
                f"[MDFileReader] pyexiv2 Exiv2Error reading JPG {file_path_named}: {exiv_err}",
            )
            traceback.print_exc()
            return None
        except OSError as io_err:
            nfo(
                f"[MDFileReader] pyexiv2 IOError reading JPG {file_path_named}: {io_err}",
            )
            traceback.print_exc()
            return None
        except Exception as e:  # pylint: disable=broad-except
            nfo(
                f"[MDFileReader] pyexiv2 general error reading JPG {file_path_named}: {e}",
            )
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
        # Changed to if, not elif, to allow a file to be both (though unlikely to be handled this way)
        if is_schema:
            return self.read_schema_file(file_path_named)
        if is_jpg:
            return self.read_jpg_header_pyexiv2(file_path_named)
        if is_png:
            return self.read_png_header_pyexiv2(file_path_named)
        if is_model_file:
            try:
                from .model_tool import ModelTool  # Local import

                tool = ModelTool()
                return tool.read_metadata_from(file_path_named)
            except ImportError:  # pragma: no cover
                nfo(
                    f"[MDFileReader] ModelTool not available for import. Cannot process model file: {path_obj.name}",
                )
                return {
                    EmptyField.PLACEHOLDER.value: {
                        "Info": f"Model file ({ext_lower}) - ModelTool parser not available.",
                    },
                }
            except Exception as e_model:  # pylint: disable=broad-except # pragma: no cover
                nfo(
                    f"[MDFileReader] Error using ModelTool for {path_obj.name}: {e_model}",
                )
                return {
                    EmptyField.PLACEHOLDER.value: {
                        "Error": f"Could not parse model file: {e_model}",
                    },
                }
        # Fallthrough if none of the above
        nfo(
            f"[MDFileReader] File type {ext_lower} for {path_obj.name} is not handled by this dispatcher.",
        )
        return None
