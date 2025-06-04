# dataset_tools/vendored_sdpr/format/novelai.py

__author__ = "receyuki"
__filename__ = "novelai.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import gzip
import json
from typing import Any  # Added Optional

from PIL import Image  # PIL.Image is used directly

from .base_format import BaseFormat

NAI_PARAMETER_MAP: dict[str, str | list[str]] = {
    "sampler": "sampler_name",
    "seed": "seed",
    "strength": "denoising_strength",
    "noise": "noise_offset",
    "scale": "cfg_scale",
    "steps": "steps",
}


class NovelAI(BaseFormat):
    tool = "NovelAI"

    class LSBExtractor:
        def _extract_lsb_data_from_pixels(self):
            """Helper method to perform the LSB extraction from pixel data."""
            current_byte = 0
            bit_count = 0
            # This loop was extracted to reduce __init__ complexity
            for pixel_index in range(self.width * self.height):
                try:
                    alpha_val = self.data[pixel_index][3]
                except IndexError:
                    # Log this specific pixel error if a logger was passed or available
                    # For now, we might skip or let it indicate a problem with the data.
                    # Depending on how critical partial LSB data is.
                    # Consider adding: self.img_pil.getlogger().warning("Pixel %s missing alpha", pixel_index)
                    continue

                lsb = alpha_val & 1
                current_byte = (current_byte << 1) | lsb
                bit_count += 1
                if bit_count == 8:
                    self.lsb_bytes_list.append(current_byte)
                    current_byte = 0
                    bit_count = 0

        def __init__(self, img_pil_object: Image.Image):
            self.img_pil = img_pil_object
            # Ensure data is a list of pixel data. getdata() can return other types for some modes.
            try:
                pixel_data = list(img_pil_object.getdata())
            except Exception as e_getdata:  # Catch potential errors from getdata() itself
                # If a logger was available here, it would be good to log this.
                # For now, if getdata() fails, LSB extraction is not possible.
                print(f"Warning: Could not get pixel data for LSBExtractor: {e_getdata}")  # Basic print
                self.data = []
                self.width, self.height = 0, 0  # Or img_pil_object.size if it's safe
                self.lsb_bytes_list = bytearray()
                self.byte_cursor = 0
                return

            self.data = pixel_data
            self.width, self.height = img_pil_object.size
            self.byte_cursor = 0
            self.lsb_bytes_list = bytearray()

            if not (img_pil_object.mode == "RGBA" and isinstance(self.data, list) and self.data):
                # Logger not available here, but ideally log if mode isn't RGBA or data is empty
                # print("Warning: Image not RGBA or no pixel data for LSBExtractor.")
                return  # lsb_bytes_list will remain empty

            if not isinstance(self.data[0], (tuple, list)) or len(self.data[0]) < 4:
                # print("Warning: Pixel data format not as expected (tuple/list with len >= 4) for LSBExtractor.")
                return  # lsb_bytes_list will remain empty

            self._extract_lsb_data_from_pixels()

        def get_next_n_bytes(self, n_bytes: int) -> bytes | None:  # Use Optional
            if self.byte_cursor + n_bytes > len(self.lsb_bytes_list):
                return None
            result_bytes = self.lsb_bytes_list[self.byte_cursor : self.byte_cursor + n_bytes]
            self.byte_cursor += n_bytes
            return bytes(result_bytes)

        def read_32bit_integer_big_endian(self) -> int | None:  # Use Optional
            byte_chunk = self.get_next_n_bytes(4)
            if byte_chunk and len(byte_chunk) == 4:  # Ensure byte_chunk is not None
                return int.from_bytes(byte_chunk, byteorder="big")
            return None

    def __init__(
        self,
        info: dict[str, Any] | None = None,  # Use Optional
        raw: str = "",
        extractor: LSBExtractor | None = None,  # Use Optional
        width: int = 0,
        height: int = 0,
    ):
        super().__init__(info=info, raw=raw, width=width, height=height)
        self._extractor = extractor

    def _process(self) -> None:
        self._logger.debug("Attempting to parse using %s logic.", self.tool)
        parsed_successfully = False

        if self._info and self._info.get("Software") == "NovelAI":
            self._logger.debug("Found 'Software: NovelAI' tag, attempting legacy PNG parse.")
            parsed_successfully = self._parse_nai_legacy_png()
        elif self._extractor:  # Check if extractor was provided and is valid
            if (
                not self._extractor.lsb_bytes_list and self._extractor.byte_cursor == 0
            ):  # Check if LSB extraction yielded anything
                self._logger.warning(
                    "%s: LSB Extractor provided but contains no extracted data (e.g. image not RGBA or LSB data empty).",
                    self.tool,
                )
                self.status = self.Status.FORMAT_ERROR
                self._error = "LSB data extraction failed or yielded no data."
                return
            self._logger.debug("LSB Extractor provided, attempting stealth PNG parse.")
            parsed_successfully = self._parse_nai_stealth_png()
        else:
            self._logger.warning("%s: Neither legacy PNG info nor LSB extractor provided.", self.tool)
            self.status = self.Status.FORMAT_ERROR
            self._error = "No data source for NovelAI parser (legacy info or LSB extractor)."
            return

        if parsed_successfully:
            self._logger.info("%s: Data parsed successfully.", self.tool)
            # self.status = self.Status.READ_SUCCESS; # Let BaseFormat.parse() handle this
        else:
            if self.status != self.Status.FORMAT_ERROR:  # If not already set by a sub-parser
                self.status = self.Status.FORMAT_ERROR
            if not self._error:
                self._error = f"{self.tool}: Failed to parse metadata."

    def _parse_common_nai_json(self, data_json: dict[str, Any], source_description: str) -> bool:
        handled_keys_in_data_json = set()
        custom_settings_for_display: dict[str, str] = {}

        self._populate_parameters_from_map(data_json, NAI_PARAMETER_MAP, handled_keys_in_data_json)
        self._extract_and_set_dimensions(data_json, "width", "height", handled_keys_in_data_json)

        exclude_from_settings = {
            "uc",
            "prompt",
            "Description",
            "Comment",
            "width",
            "height",
        }
        exclude_from_settings.update(NAI_PARAMETER_MAP.keys())

        for k, v_val in data_json.items():
            if k not in exclude_from_settings and k not in handled_keys_in_data_json:
                custom_settings_for_display[self._format_key_for_display(k)] = str(v_val)
                handled_keys_in_data_json.add(k)

        self._setting = self._build_settings_string(
            custom_settings_dict=custom_settings_for_display,
            include_standard_params=True,
            sort_parts=True,
        )
        return True  # Assuming success if it reaches here

    def _parse_nai_legacy_png(self) -> bool:
        if not self._info:
            self._error = "Legacy PNG parsing called without _info."
            return False
        try:
            self._positive = str(self._info.get("Description", "")).strip()
            comment_str = self._info.get("Comment", "{}")
            data_json: dict[str, Any] = {}
            try:
                loaded_comment = json.loads(comment_str)
                if isinstance(loaded_comment, dict):
                    data_json = loaded_comment
                else:
                    self._logger.warning(
                        "Legacy NovelAI 'Comment' not a JSON dict. Content: %s",
                        comment_str[:200],
                    )
            except json.JSONDecodeError:
                # CORRECTED LOGGING (Line 208 area)
                self._logger.warning(
                    "Invalid JSON in NovelAI legacy 'Comment'. Content snippet: %s",
                    comment_str[:200],
                    exc_info=True,
                )
            self._negative = str(data_json.get("uc", "")).strip()
            self._parse_common_nai_json(data_json, "legacy comment JSON")
            raw_parts = [self._info.get("Description", "")]
            if src := self._info.get("Source"):
                raw_parts.append(f"Source: {src}")  # Use walrus
            raw_parts.append(f"Comment: {comment_str}")
            self._raw = "\n".join(filter(None, raw_parts)).strip()
            return True
        except Exception as general_err:
            self._error = f"Error parsing NovelAI legacy PNG: {general_err}"
            self._logger.error("NovelAI legacy parsing error: %s", general_err, exc_info=True)
            return False

    def _parse_nai_stealth_png(self) -> bool:
        if not self._extractor:
            self._error = "LSB extractor not available."
            return False
        try:
            data_length = self._extractor.read_32bit_integer_big_endian()
            if data_length is None:
                self._error = "Could not read data length from LSB."
                self._logger.warning(self._error)
                return False
            if not (0 < data_length <= 10 * 1024 * 1024):  # Simplified check
                self._error = f"Invalid LSB data length: {data_length}"
                self._logger.warning(self._error)
                return False

            compressed_data = self._extractor.get_next_n_bytes(data_length)
            if compressed_data is None or len(compressed_data) != data_length:
                self._error = f"Could not read {data_length} bytes from LSB."
                self._logger.warning(self._error)
                return False

            json_string = gzip.decompress(compressed_data).decode("utf-8")
            self._raw = json_string
            main_json_data = json.loads(json_string)

            if not isinstance(main_json_data, dict):
                self._error = "Decompressed LSB data not a dict."
                self._logger.warning(self._error)
                return False

            data_to_use_for_prompts_params = main_json_data
            if "Comment" in main_json_data:
                comment_json_str = str(main_json_data.get("Comment", "{}"))
                try:
                    comment_data_dict = json.loads(comment_json_str)
                    if isinstance(comment_data_dict, dict):
                        self._logger.debug("Using nested 'Comment' JSON for NAI stealth.")
                        self._positive = str(comment_data_dict.get("prompt", "")).strip()
                        self._negative = str(comment_data_dict.get("uc", "")).strip()
                        data_to_use_for_prompts_params = comment_data_dict
                    else:
                        self._logger.warning(
                            "NAI stealth 'Comment' not a dict. Using main. Snippet: %s",
                            comment_json_str[:200],
                        )
                        self._positive = str(main_json_data.get("Description", "")).strip()
                except json.JSONDecodeError:
                    self._logger.warning(
                        "NAI stealth 'Comment' invalid JSON. Using main. Snippet: %s",
                        comment_json_str[:200],
                        exc_info=True,
                    )
                    self._positive = str(main_json_data.get("Description", "")).strip()
            else:
                self._logger.debug("No 'Comment' in NAI stealth, using 'Description'.")
                self._positive = str(main_json_data.get("Description", "")).strip()
                self._negative = str(main_json_data.get("uc", "")).strip()  # Try to get 'uc' from main JSON too

            return self._parse_common_nai_json(data_to_use_for_prompts_params, "stealth PNG JSON")

        except gzip.BadGzipFile as e_gzip:
            self._error = f"Invalid GZip in NAI stealth: {e_gzip}"
            self._logger.warning("%s: %s", self.tool, self._error, exc_info=True)
            return False
        except json.JSONDecodeError as e_json:
            self._error = f"Invalid JSON in NAI stealth: {e_json}"
            self._logger.warning("%s: %s", self.tool, self._error, exc_info=True)
            return False
        except Exception as general_err:
            self._error = f"Error parsing NAI stealth: {general_err}"
            self._logger.error("NAI stealth parsing error: %s", general_err, exc_info=True)
            return False
