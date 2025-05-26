# dataset_tools/access_disk.py

from pathlib import Path
import os
import json
import toml

# Keep Pillow for image opening if needed for non-metadata tasks or specific fallbacks,
# but sd-prompt-reader will also use it.
# from PIL import Image, UnidentifiedImageError
# from PIL.ExifTags import TAGS as EXIF_TAGS # Not strictly needed if pyexiv2 is primary for standard EXIF

import pyexiv2 # For primary EXIF/XMP/IPTC reading for standard photos
# import exif # Fallback 'exif' library, keep if pyexiv2 fails often for you

from .logger import debug_message, debug_monitor # Using your existing logger import style
from .logger import info_monitor as nfo
from .correct_types import EmptyField, ExtensionType as Ext, DownField, UpField
from .model_tool import ModelTool


class MetadataFileReader:
    """Interface for metadata and text read operations"""

    def __init__(self):
        pass # self.show_content was unused

    # --- Methods for Standard Photographic EXIF/XMP/IPTC (using pyexiv2) ---
    # These are called by the fallback logic in metadata_parser.py
    # when sd-prompt-reader doesn't identify an AI tool.

    @debug_monitor
    def read_jpg_header_pyexiv2(self, file_path_named: str) -> dict | None:
        nfo(f"[MDFileReader] Reading JPG with pyexiv2: {file_path_named}")
        try:
            img = pyexiv2.Image(file_path_named)
            metadata = {
                "EXIF": img.read_exif() or {},
                "IPTC": img.read_iptc() or {},
                "XMP":  img.read_xmp()  or {}
            }
            img.close()
            # Filter out sections if all their sub-dictionaries are empty
            # (though process_pyexiv2_data should also handle empty inner dicts)
            if not metadata["EXIF"] and not metadata["IPTC"] and not metadata["XMP"]:
                nfo(f"[MDFileReader] pyexiv2 found no EXIF/IPTC/XMP in JPG: {file_path_named}")
                return None # Or return the empty shell, depending on how process_pyexiv2_data handles it
            return metadata
        except Exception as e:
            nfo(f"[MDFileReader] pyexiv2 error reading JPG {file_path_named}: {e}")
            return None

    @debug_monitor
    def read_png_header_pyexiv2(self, file_path_named: str) -> dict | None:
        # PNGs typically don't have rich EXIF/XMP like JPEGs unless specifically added.
        # AI tools store params in tEXt chunks (Pillow/sd-prompt-reader handles this).
        # This pyexiv2 call is for any *standard* metadata that might be in a PNG.
        nfo(f"[MDFileReader] Reading PNG with pyexiv2 for standard metadata: {file_path_named}")
        try:
            img = pyexiv2.Image(file_path_named)
            metadata = {
                "EXIF": img.read_exif() or {},
                "IPTC": img.read_iptc() or {},
                "XMP":  img.read_xmp()  or {}
                # pyexiv2 can also read ICC profiles with img.read_icc() if needed
            }
            img.close()
            if not metadata["EXIF"] and not metadata["IPTC"] and not metadata["XMP"]:
                nfo(f"[MDFileReader] pyexiv2 found no standard EXIF/IPTC/XMP in PNG: {file_path_named}")
                return None
            return metadata
        except Exception as e:
            nfo(f"[MDFileReader] pyexiv2 error reading PNG standard metadata {file_path_named}: {e}")
            return None

    # You can add similar pyexiv2 readers for WEBP if pyexiv2 supports your WEBP files well.
    # def read_webp_header_pyexiv2(self, file_path_named: str) -> dict | None: ...

    # --- Methods for Text and Schema Files (Remain largely the same) ---
    @debug_monitor
    def read_txt_contents(self, file_path_named: str) -> dict | None:
        nfo(f"[MDFileReader] Reading TXT: {file_path_named}")
        # Try common encodings
        encodings_to_try = ["utf-8", "utf-16", "latin-1"]
        for enc in encodings_to_try:
            try:
                with open(file_path_named, "r", encoding=enc) as open_file:
                    file_contents = open_file.read()
                    # Structure for UI:
                    return {
                        UpField.TEXT_DATA: file_contents
                        # No need for EmptyField.EMPTY here as UI will show TEXT_DATA
                    }
            except UnicodeDecodeError:
                continue # Try next encoding
            except Exception as e:
                nfo(f"[MDFileReader] Error reading TXT {file_path_named} with encoding {enc}: {e}")
                return None # Or a dict indicating error
        nfo(f"[MDFileReader] Failed to decode TXT {file_path_named} with common encodings.")
        return None


    @debug_monitor
    def read_schema_file(self, file_path_named: str) -> dict | None:
        nfo(f"[MDFileReader] Reading schema file: {file_path_named}")
        header_field = DownField.JSON_DATA # Default to JSON_DATA for UI display
        loader = None
        mode = "r" # Default mode

        ext = Path(file_path_named).suffix.lower()
        if ext in Ext.TOML: # Assuming Ext.TOML is like {".toml"}
            loader = toml.load
            mode = "rb" # TOML library often prefers binary mode
            header_field = DownField.TOML_DATA
        elif ext in Ext.JSON: # Assuming Ext.JSON is like {".json"}
            loader = json.load
            mode = "r"
            header_field = DownField.JSON_DATA
        else:
            nfo(f"[MDFileReader] Unknown schema file type for {file_path_named}")
            return None

        try:
            # TOML needs 'rb', JSON needs 'r'. Encoding for 'r' mode.
            open_kwargs = {'encoding': 'utf-8'} if mode == 'r' else {}
            with open(file_path_named, mode, **open_kwargs) as open_file:
                file_contents = loader(open_file)
                return {
                    header_field: file_contents
                }
        except (toml.TomlDecodeError, json.JSONDecodeError) as error_log:
            nfo(f"[MDFileReader] Schema decode error for {file_path_named}: {error_log}")
            return {EmptyField.PLACEHOLDER: {"Error": f"Invalid {ext.upper()} format."}}
        except Exception as e:
            nfo(f"[MDFileReader] Error reading schema file {file_path_named}: {e}")
            return None


    # --- Main `read_header` Orchestrator (Simplified) ---
    # This method is now primarily for non-image files OR as a fallback for standard image metadata
    # if sd-prompt-reader doesn't handle an image or for non-AI images.
    # The main `parse_metadata` in `metadata_parser.py` will decide when to call this.
    # For clarity, perhaps rename this or make specific methods more directly callable.
    # However, if `metadata_parser.py` calls `std_reader.read_jpg_header_pyexiv2()` etc.,
    # then this particular `read_header` method here might become less used or just for .txt/.json etc.

    @debug_monitor
    def read_general_file_content(self, file_path_named: str) -> dict | None:
        """
        Reads content for non-image text-based or schema-based files.
        For images, specific methods like read_jpg_header_pyexiv2 should be called by metadata_parser.
        """
        nfo(f"[MDFileReader] Reading general file: {file_path_named}")
        ext = Path(file_path_named).suffix.lower()

        if ext in Ext.JSON or ext in Ext.TOML:
            return self.read_schema_file(file_path_named)
        
        # Broad check for text-like files (PLAIN includes .txt, .xml, .html)
        for file_type_set in Ext.PLAIN:
             if ext in file_type_set:
                  return self.read_txt_contents(file_path_named)

        if ext in Ext.MODEL: # Use set union for checking against Ext.MODEL
            model_tool = ModelTool()
            return model_tool.read_metadata_from(file_path_named)
        
        # If it's an image file but we got here, it means sd-prompt-reader didn't handle it
        # and metadata_parser is asking us for standard EXIF via specific calls.
        # This general read_header shouldn't try to re-read images if specific pyexiv2 methods exist.
        nfo(f"[MDFileReader] No specific general handler for {file_path_named}")
        return None