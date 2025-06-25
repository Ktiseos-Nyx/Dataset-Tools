# dataset_tools/access_disk.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

import json
import logging as pylog
# import traceback # Keep commented out if not explicitly needed and causing F401
from pathlib import Path # Ensure Path is imported here

import pyexiv2
import toml

# --- Pillow Import for Fallback ---
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
# -----------------------------------


from .correct_types import DownField, EmptyField
from .correct_types import ExtensionType as Ext
from .correct_types import UpField
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
                # --- FALLBACK LOGIC FOR NO METADATA ---
                if PILLOW_AVAILABLE:
                    nfo(f"[MDFileReader] Attempting fallback with Pillow for EXIF data...")
                    # Corrected: Pass file_path_named to the fallback method
                    pillow_exif = self._read_exif_with_pillow(file_path_named)
                    if pillow_exif:
                        nfo(f"[MDFileReader] Successfully read EXIF data with Pillow.")
                        metadata["PILLOW_EXIF"] = pillow_exif
                        return metadata
                    else:
                        nfo(f"[MDFileReader] Pillow also found no EXIF data for {file_path_named}.")
                # --- END FALLBACK LOGIC ---
                return None
            return metadata
        # --- MODIFIED EXCEPTION HANDLING ---
        except Exception as ex:  # Catch any exception during pyexiv2 operations
            nfo(
                f"[MDFileReader] An error occurred with pyexiv2 for PNG {file_path_named}: {ex}",
            )
            self._logger.debug("Traceback for pyexiv2 PNG error:", exc_info=True)
            # --- FALLBACK LOGIC FOR pyexiv2 ERRORS ---
            if PILLOW_AVAILABLE:
                nfo(f"[MDFileReader] Attempting fallback with Pillow due to pyexiv2 error...")
                # Corrected: Pass file_path_named to the fallback method
                pillow_exif = self._read_exif_with_pillow(file_path_named)
                if pillow_exif:
                    nfo(f"[MDFileReader] Successfully read EXIF data with Pillow after pyexiv2 error.")
                    return {"PILLOW_EXIF": pillow_exif}
                else:
                    nfo(f"[MDFileReader] Pillow also found no EXIF data for {file_path_named} after pyexiv2 error.")
            # --- END FALLBACK LOGIC ---
            return None
        # --- END MODIFIED EXCEPTION HANDLING ---


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
                self._logger.debug(
                    "[MDFileReader] UserComment type from read_exif for %s: %s",
                    Path(file_path_named).name, # Path is available here
                    type(uc_val_from_read_exif),
                )
                if isinstance(
                    uc_val_from_read_exif,
                    str,
                ) and uc_val_from_read_exif.startswith("charset="):
                    self._logger.debug(
                        "[MDFileReader] UserComment from read_exif appears to be an already decoded string with charset prefix for %s.",
                        Path(file_path_named).name, # Path is available here
                    )
            img.close()
            if not metadata["EXIF"] and not metadata["IPTC"] and not metadata["XMP"]:
                nfo(
                    f"[MDFileReader] pyexiv2 found no EXIF/IPTC/XMP in JPG: {file_path_named}",
                )
                # --- FALLBACK LOGIC FOR NO METADATA ---
                if PILLOW_AVAILABLE:
                    nfo(f"[MDFileReader] Attempting fallback with Pillow for EXIF data...")
                    pillow_exif = self._read_exif_with_pillow(file_path_named)
                    if pillow_exif:
                        nfo(f"[MDFileReader] Successfully read EXIF data with Pillow.")
                        metadata["PILLOW_EXIF"] = pillow_exif
                        return metadata
                    else:
                        nfo(f"[MDFileReader] Pillow also found no EXIF data for {file_path_named}.")
                # --- END FALLBACK LOGIC ---
                return None
            return metadata
        # --- MODIFIED EXCEPTION HANDLING ---
        except Exception as ex:  # Catch any exception during pyexiv2 operations
            nfo(
                f"[MDFileReader] An error occurred with pyexiv2 for JPG {file_path_named}: {ex}",
            )
            self._logger.debug("Traceback for pyexiv2 JPG error:", exc_info=True)
            # --- FALLBACK LOGIC FOR pyexiv2 ERRORS ---
            if PILLOW_AVAILABLE:
                nfo(f"[MDFileReader] Attempting fallback with Pillow due to pyexiv2 error...")
                pillow_exif = self._read_exif_with_pillow(file_path_named)
                if pillow_exif:
                    nfo(f"[MDFileReader] Successfully read EXIF data with Pillow after pyexiv2 error.")
                    return {"PILLOW_EXIF": pillow_exif}
                else:
                    nfo(f"[MDFileReader] Pillow also found no EXIF data for {file_path_named} after pyexiv2 error.")
            # --- END FALLBACK LOGIC ---
            return None
        # --- END MODIFIED EXCEPTION HANDLING ---


    @debug_monitor
    # pylint: disable=no-member
    def _read_exif_with_pillow(self, file_path: str) -> dict | None:
        """
        Reads EXIF data from an image using Pillow as a fallback.
        Returns a dictionary of EXIF tags, or None if an error occurs or no EXIF is found.
        """
        if not PILLOW_AVAILABLE:
            self._logger.warning("Pillow is not installed. Cannot perform fallback EXIF read.")
            return None

        exif_data = {}
        try:
            with Image.open(file_path) as img:
                exif_info = img.getexif()
                if exif_info:
                    for tag_id, value in exif_info.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if isinstance(value, bytes):
                            try:
                                value = value.decode('utf-8', errors='replace')
                            except UnicodeDecodeError:
                                value = str(value)
                        exif_data[tag] = value
                    # FIX: Ensure Path is available here by using the imported Path
                    nfo(f"[MDFileReader] Pillow successfully extracted EXIF data from {Path(file_path).name}")
                    return exif_data
                else:
                    nfo(f"[MDFileReader] Pillow found no EXIF data in {Path(file_path).name}") # Path is available here
                    return None
        except FileNotFoundError:
            self._logger.error(f"Pillow fallback: File not found at {file_path}")
            return None
        except OSError as e:
            self._logger.error(f"Pillow fallback: OS error reading {file_path}: {e}")
            return None
        except Exception as e:
            self._logger.error(f"Pillow fallback: Unexpected error reading {file_path}: {e}", exc_info=True)
            return None
    # --- END NEW FALLBACK EXIF READING FUNCTION ---


    @debug_monitor
    # pylint: disable=no-member
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
                return None
            except Exception as e:
                nfo(
                    f"[MDFileReader] General Error reading TXT {file_path_named} with encoding {enc}: {e}",
                )
                return None
        nfo(
            f"[MDFileReader] Failed to decode TXT {file_path_named} with common encodings.",
        )
        return None

    @debug_monitor
    # pylint: disable=no-member
    def read_schema_file(self, file_path_named: str) -> dict | None:
        nfo(f"[MDFileReader] Reading schema file: {file_path_named}")
        header_field_enum = DownField.JSON_DATA
        loader = None
        mode = "r"
        path_obj = Path(file_path_named) # Path is available here
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
            nfo(
                f"[MDFileReader] Unknown schema file type for {file_path_named} (ext: {ext})",
            )
            return None
        try:
            open_kwargs = {"encoding": "utf-8"} if mode == "r" and is_json else {}
            with open(file_path_named, mode, **open_kwargs) as open_file:
                file_contents = loader(open_file)
                return {header_field_enum.value: file_contents}
        except (
            toml.TomlDecodeError,
            json.JSONDecodeError,
        ) as decode_err:
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
        except Exception as e:
            nfo(
                f"[MDFileReader] General Error reading schema file {file_path_named}: {e}",
            )
            return None

    @debug_monitor
    def read_file_data_by_type(self, file_path_named: str) -> dict | None:
        nfo(f"[MDFileReader] Dispatching read for: {file_path_named}")
        path_obj = Path(file_path_named) # Path is available here
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
        if is_schema:
            return self.read_schema_file(file_path_named)
        if is_jpg:
            return self.read_jpg_header_pyexiv2(file_path_named)
        if is_png:
            return self.read_png_header_pyexiv2(file_path_named)
        if is_model_file:
            try:
                from .model_tool import ModelTool

                tool = ModelTool()
                return tool.read_metadata_from(file_path_named)
            except ImportError:
                nfo(
                    f"[MDFileReader] ModelTool not available for import. Cannot process model file: {path_obj.name}",
                )
                return {
                    EmptyField.PLACEHOLDER.value: {
                        "Info": f"Model file ({ext_lower}) - ModelTool parser not available.",
                    },
                }
            except Exception as e_model:
                nfo(
                    f"[MDFileReader] Error using ModelTool for {path_obj.name}: {e_model}",
                )
                return {
                    EmptyField.PLACEHOLDER.value: {
                        "Error": f"Could not parse model file: {e_model}",
                    },
                }
        nfo(
            f"[MDFileReader] File type {ext_lower} for {path_obj.name} is not handled by this dispatcher.",
        )
        return None
