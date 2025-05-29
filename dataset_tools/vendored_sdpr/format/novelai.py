# dataset_tools/vendored_sdpr/format/novelai.py

__author__ = "receyuki"
__filename__ = "novelai.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
import gzip  # For decompressing stealth PNG data

from .base_format import BaseFormat
from .utility import remove_quotes  # Assuming utility.py is in the same 'format' directory
from ..logger import Logger
from ..constants import PARAMETER_PLACEHOLDER


class NovelAI(BaseFormat):
    tool = "NovelAI"  # Tool name

    # These were for the fragile zip mapping.
    # SETTING_KEY_LEGACY = [ ... ]
    # SETTING_KEY_STEALTH = [ ... ]

    class LSBExtractor:  # Inner class specific to NovelAI
        # ... (Your LSBExtractor code is quite specific and likely correct from original SDPR) ...
        # Minor: Ensure it handles end-of-data gracefully if n bytes aren't available.
        def __init__(self, img_pil_object):  # Expects a PIL Image object
            self.img_pil = img_pil_object
            self.data = list(img_pil_object.getdata())  # List of pixel tuples
            self.width, self.height = img_pil_object.size
            # Re-arrange data into rows for easier access if that's how original worked
            # self.data_rows = [self.data[i * self.width : (i + 1) * self.width] for i in range(self.height)]

            self.byte_cursor = 0  # Instead of row/col, use a flat byte cursor over alpha LSBs
            self.bit_buffer = 0
            self.bits_in_buffer = 0

            # Extract all LSBs from alpha channel into a bit stream (or byte stream)
            # This is a common way to implement LSB extraction.
            # The original might have done it on-the-fly per bit.
            self.lsb_bytes_list = bytearray()
            current_byte = 0
            bit_count = 0
            if img_pil_object.mode == "RGBA":
                for pixel_index in range(self.width * self.height):
                    alpha_val = self.data[pixel_index][3]  # Alpha channel
                    lsb = alpha_val & 1
                    current_byte = (current_byte << 1) | lsb
                    bit_count += 1
                    if bit_count == 8:
                        self.lsb_bytes_list.append(current_byte)
                        current_byte = 0
                        bit_count = 0
            # If bit_count != 0 at the end, there are partial byte LSBs, usually ignored or padded.

        def get_next_n_bytes(self, n: int) -> bytes | None:
            if self.byte_cursor + n > len(self.lsb_bytes_list):
                # Not enough bytes remaining
                # Logger for LSBExtractor might be useful here.
                # print(f"LSBExtractor: Requested {n} bytes, but only {len(self.lsb_bytes_list) - self.byte_cursor} available.")
                return None

            result_bytes = self.lsb_bytes_list[self.byte_cursor : self.byte_cursor + n]
            self.byte_cursor += n
            return bytes(result_bytes)

        def read_32bit_integer_big_endian(self) -> int | None:  # NAI uses big-endian for length
            byte_chunk = self.get_next_n_bytes(4)
            if byte_chunk and len(byte_chunk) == 4:
                return int.from_bytes(byte_chunk, byteorder="big")
            return None

    def __init__(
        self,
        info: dict = None,
        raw: str = "",
        extractor: LSBExtractor = None,  # Changed from width, height to extractor
        width: int = 0,
        height: int = 0,  # Keep width/height from ImageDataReader for legacy if info is used
    ):
        super().__init__(info=info, raw=raw, width=width, height=height)
        self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool}")
        self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER
        self._extractor = extractor  # This will be an LSBExtractor instance for stealth PNGs

    # `parse()` is inherited from BaseFormat, which calls `_process()`

    def _process(self):  # Called by BaseFormat.parse()
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")

        parsed_successfully = False
        if self._info and self._info.get("Software") == "NovelAI":  # Legacy PNG format check
            self._logger.debug("Found 'Software: NovelAI' tag, attempting legacy PNG parse.")
            parsed_successfully = self._parse_nai_legacy_png()
        elif self._extractor:  # Stealth PNG format, extractor was passed
            self._logger.debug("LSB Extractor provided, attempting stealth PNG parse.")
            parsed_successfully = self._parse_nai_stealth_png()
        else:
            self._logger.warn(f"{self.tool}: Neither legacy PNG info nor LSB extractor provided.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "No data source for NovelAI parser (legacy info or LSB extractor)."
            return

        if parsed_successfully:
            self.status = self.Status.READ_SUCCESS
            self._logger.info(f"{self.tool}: Data parsed successfully.")
        else:
            self.status = self.Status.FORMAT_ERROR
            if not self._error:  # If sub-parser didn't set a specific error
                self._error = f"{self.tool}: Failed to parse metadata."

    def _parse_nai_legacy_png(self) -> bool:
        try:
            self._positive = str(self._info.get("Description", "")).strip()

            comment_str = self._info.get("Comment", "{}")  # Default to empty JSON string
            data_json = json.loads(comment_str)  # Comment field contains JSON
            if not isinstance(data_json, dict):
                self._error = "Legacy NovelAI 'Comment' field is not a valid JSON dictionary."
                return False

            self._negative = str(data_json.get("uc", "")).strip()  # Negative prompt from "uc"

            # Populate self._parameter
            param_map = {
                "sampler": "sampler_name",
                "seed": "seed",
                "strength": "denoising_strength",  # NAI "strength" is like denoise
                "noise": "noise_offset",  # NAI "noise" is noise offset. Add to PARAMETER_KEY if needed
                "scale": "cfg_scale",
                "steps": "steps",
            }
            for nai_key, canonical_key in param_map.items():
                if nai_key in data_json and canonical_key in self._parameter:
                    self._parameter[canonical_key] = str(data_json[nai_key])

            # Width and height for legacy are from PIL (passed to __init__, stored in self._width/height)
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            # Create settings string from remaining items in data_json
            setting_parts = []
            for k, v in data_json.items():
                if k not in ["uc"] + list(param_map.keys()):  # Don't repeat already mapped items
                    setting_parts.append(f"{k.capitalize()}: {remove_quotes(str(v))}")
            self._setting = ", ".join(sorted(setting_parts))

            # Consolidate raw data
            self._raw = "\n".join(filter(None, [self._positive, self._negative, f"Comment: {comment_str}"])).strip()
            return True
        except json.JSONDecodeError as e:
            self._error = f"Invalid JSON in NovelAI legacy 'Comment': {e}"
            return False
        except Exception as e:
            self._error = f"Error parsing NovelAI legacy PNG: {e}"
            self._logger.error(f"NovelAI legacy parsing error: {e}", exc_info=True)
            return False

    def _parse_nai_stealth_png(self) -> bool:
        try:
            # The LSBExtractor logic from original SDPR:
            # Reads length, then gzipped JSON data.
            # NOVELAI_MAGIC was already checked by ImageDataReader before creating LSBExtractor.

            data_length_bytes = self._extractor.read_32bit_integer_big_endian()
            if data_length_bytes is None:
                self._error = "Could not read data length from LSB stream."
                return False

            # Original SDPR used data_length_bytes // 8. This seems like a misunderstanding.
            # If data_length_bytes is the length of the *uncompressed JSON string*, we don't know compressed size.
            # If data_length_bytes is the length of the *gzipped data*, then it's correct.
            # NAI spec usually indicates length of *compressed* data.
            # Let's assume data_length_bytes is the length of the compressed data to read.
            compressed_data = self._extractor.get_next_n_bytes(data_length_bytes)
            if compressed_data is None or len(compressed_data) != data_length_bytes:
                self._error = f"Could not read {data_length_bytes} bytes of compressed data from LSB stream."
                return False

            json_string = gzip.decompress(compressed_data).decode("utf-8")
            data_json = json.loads(json_string)
            if not isinstance(data_json, dict):
                self._error = "Decompressed LSB data is not a valid JSON dictionary."
                return False

            self._raw = json_string  # Store the decompressed JSON as raw

            # NAI stealth PNGs can have "Comment" which itself is JSON, or "Description"
            if "Comment" in data_json:
                comment_json_str = data_json.pop("Comment", "{}")  # Pop to remove from main data_json
                try:
                    comment_data = json.loads(comment_json_str)
                    if isinstance(comment_data, dict):
                        # Merge comment_data into data_json, data_json takes precedence for overlapping keys
                        # Or, specific fields:
                        self._positive = str(comment_data.get("prompt", "")).strip()
                        self._negative = str(comment_data.get("uc", "")).strip()
                        # And then use remaining items from comment_data for parameters
                        data_for_params = comment_data
                except json.JSONDecodeError:
                    self._logger.warn("NovelAI stealth 'Comment' field was not valid JSON. Ignoring.")
                    data_for_params = data_json  # Fallback to use main data_json for params
            else:  # No "Comment", use "Description" for prompt and main data_json for params
                self._positive = str(data_json.get("Description", "")).strip()
                # Negative might not be present directly if no "Comment"
                data_for_params = data_json  # Use main data_json for params

            # Populate parameters from data_for_params
            param_map = {
                "sampler": "sampler_name",
                "seed": "seed",
                "strength": "denoising_strength",
                "noise": "noise_offset",
                "scale": "cfg_scale",
                "steps": "steps",
                "width": "width",
                "height": "height",
            }  # NAI JSON often has width/height

            for nai_key, canonical_key in param_map.items():
                if nai_key in data_for_params and canonical_key in self._parameter:
                    self._parameter[canonical_key] = str(data_for_params.get(nai_key))

            if data_for_params.get("width") is not None:
                self._width = str(data_for_params.get("width"))
            if data_for_params.get("height") is not None:
                self._height = str(data_for_params.get("height"))
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            # Create settings string from remaining items in data_for_params
            setting_parts = []
            for k, v in data_for_params.items():
                if k not in ["prompt", "uc", "Description", "Comment"] + list(param_map.keys()):
                    setting_parts.append(f"{k.capitalize()}: {remove_quotes(str(v))}")
            self._setting = ", ".join(sorted(setting_parts))
            return True

        except gzip.BadGzipFile as e_gzip:
            self._error = f"Invalid GZip data in NovelAI stealth PNG: {e_gzip}"
            return False
        except json.JSONDecodeError as e_json:
            self._error = f"Invalid JSON in NovelAI stealth PNG: {e_json}"
            return False
        except Exception as e:
            self._error = f"Error parsing NovelAI stealth PNG: {e}"
            self._logger.error(f"NovelAI stealth parsing error: {e}", exc_info=True)
            return False
