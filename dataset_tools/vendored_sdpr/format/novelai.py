# dataset_tools/vendored_sdpr/format/novelai.py

__author__ = "receyuki"
__filename__ = "novelai.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import gzip
import json
from typing import Any

from PIL import Image

from .base_format import BaseFormat

# from .utility import remove_quotes # _build_settings_string handles this

NAI_PARAMETER_MAP: dict[str, str | list[str]] = {
    # NAI key: canonical_param_key or list of keys
    "sampler": "sampler_name",
    "seed": "seed",
    "strength": "denoising_strength",  # Assuming this is in BaseFormat.PARAMETER_KEY
    "noise": "noise_offset",  # Custom, will go to settings string if not standard
    "scale": "cfg_scale",
    "steps": "steps",
    # width & height are handled by _extract_and_set_dimensions
}


class NovelAI(BaseFormat):
    tool = "NovelAI"

    class LSBExtractor:
        def __init__(self, img_pil_object: Image.Image):
            self.img_pil = img_pil_object
            self.data = list(img_pil_object.getdata())
            self.width, self.height = img_pil_object.size
            self.byte_cursor = 0
            self.lsb_bytes_list = bytearray()
            current_byte = 0
            bit_count = 0
            # Ensure it's RGBA before trying to access alpha
            if (
                img_pil_object.mode == "RGBA"
                and isinstance(self.data, list)
                and self.data
            ):
                # Ensure data is not empty and pixels are tuples/lists with enough elements
                if not isinstance(self.data[0], (tuple, list)) or len(self.data[0]) < 4:
                    # Log this issue, LSB extraction won't work
                    # (Need a logger here or raise an error)
                    # For now, lsb_bytes_list will remain empty.
                    return

                for pixel_index in range(self.width * self.height):
                    # Add safety check for pixel format if necessary, though getdata() usually standardizes
                    try:
                        alpha_val = self.data[pixel_index][3]
                    except IndexError:
                        # Pixel doesn't have an alpha channel, or data is malformed
                        # (Log or handle this error)
                        # For now, break or skip this pixel. For simplicity, we'll let it error
                        # if data format is unexpected, or a more robust check would be needed.
                        # This situation should ideally not occur if mode is 'RGBA'.
                        continue  # Or raise error

                    lsb = alpha_val & 1
                    current_byte = (current_byte << 1) | lsb
                    bit_count += 1
                    if bit_count == 8:
                        self.lsb_bytes_list.append(current_byte)
                        current_byte = 0
                        bit_count = 0
            # else:
            # Logger not available here, but ideally log if mode isn't RGBA or data is empty

        def get_next_n_bytes(self, n_bytes: int) -> bytes | None:
            if self.byte_cursor + n_bytes > len(self.lsb_bytes_list):
                return None
            result_bytes = self.lsb_bytes_list[
                self.byte_cursor : self.byte_cursor + n_bytes
            ]
            self.byte_cursor += n_bytes
            return bytes(result_bytes)

        def read_32bit_integer_big_endian(self) -> int | None:
            byte_chunk = self.get_next_n_bytes(4)
            if byte_chunk and len(byte_chunk) == 4:
                return int.from_bytes(byte_chunk, byteorder="big")
            return None

    def __init__(
        self,
        info: dict[str, Any] | None = None,
        raw: str = "",
        extractor: LSBExtractor | None = None,
        width: int = 0,
        height: int = 0,
    ):
        super().__init__(info=info, raw=raw, width=width, height=height)
        # self._logger is inherited and initialized by BaseFormat
        self._extractor = extractor

    def _process(self) -> None:
        # self.status is managed by BaseFormat.parse()
        self._logger.debug("Attempting to parse using %s logic.", self.tool)
        parsed_successfully = False

        if self._info and self._info.get("Software") == "NovelAI":
            self._logger.debug(
                "Found 'Software: NovelAI' tag, attempting legacy PNG parse."
            )
            parsed_successfully = self._parse_nai_legacy_png()
        elif self._extractor:
            self._logger.debug("LSB Extractor provided, attempting stealth PNG parse.")
            parsed_successfully = self._parse_nai_stealth_png()
        else:
            self._logger.warning(
                "%s: Neither legacy PNG info nor LSB extractor provided.", self.tool
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = (
                "No data source for NovelAI parser (legacy info or LSB extractor)."
            )
            return  # Let BaseFormat.parse() handle the rest

        if parsed_successfully:
            # self.status = self.Status.READ_SUCCESS # Let BaseFormat.parse() handle this
            self._logger.info("%s: Data parsed successfully.", self.tool)
        else:
            # Ensure status is error if not already set by specific parsing methods
            if self.status != self.Status.FORMAT_ERROR:
                self.status = self.Status.FORMAT_ERROR
            if not self._error:  # If sub-parser didn't set a specific error
                self._error = f"{self.tool}: Failed to parse metadata."

    def _parse_common_nai_json(
        self, data_json: dict[str, Any], source_description: str
    ) -> bool:
        """Common logic to parse parameters from a NovelAI JSON structure."""
        handled_keys_in_data_json = set()
        custom_settings_for_display: dict[str, str] = {}

        # Parameters from NAI_PARAMETER_MAP
        self._populate_parameters_from_map(
            data_json, NAI_PARAMETER_MAP, handled_keys_in_data_json
        )

        # Handle width/height specifically if present
        self._extract_and_set_dimensions(
            data_json, "width", "height", handled_keys_in_data_json
        )

        # Add remaining items from data_json to custom_settings_for_display
        # These are keys not in NAI_PARAMETER_MAP and not "width"/"height"
        # Also exclude "uc", "prompt", "Description", "Comment" as they are handled separately
        # or are containers.
        exclude_from_settings = {
            "uc",
            "prompt",
            "Description",
            "Comment",
            "width",
            "height",
        }
        exclude_from_settings.update(
            NAI_PARAMETER_MAP.keys()
        )  # Add keys already mapped

        for k, v_val in data_json.items():
            if k not in exclude_from_settings and k not in handled_keys_in_data_json:
                # Format key for display and add to custom settings
                # Keys like "sm", "sm_dyn" might appear here.
                custom_settings_for_display[self._format_key_for_display(k)] = str(
                    v_val
                )
                handled_keys_in_data_json.add(k)

        self._setting = self._build_settings_string(
            custom_settings_dict=custom_settings_for_display,
            include_standard_params=True,
            sort_parts=True,
        )
        return True

    def _parse_nai_legacy_png(self) -> bool:
        if not self._info:  # Should be checked by caller (_process)
            self._error = "Legacy PNG parsing called without _info."
            return False
        try:
            self._positive = str(self._info.get("Description", "")).strip()
            comment_str = self._info.get(
                "Comment", "{}"
            )  # Default to empty JSON string
            data_json: dict[str, Any] = {}
            try:
                loaded_comment = json.loads(comment_str)
                if isinstance(loaded_comment, dict):
                    data_json = loaded_comment
                else:
                    self._logger.warning(
                        "Legacy NovelAI 'Comment' field was not a JSON dictionary. Content: %s",
                        comment_str[:200],  # Log snippet
                    )
                    # Keep data_json empty, prompts/params won't be read from here
            except json.JSONDecodeError:
                self._logger.warning(
                    "Invalid JSON in NovelAI legacy 'Comment': %s. Content: %s",
                    comment_str[:200],  # Log snippet
                    exc_info=True,  # Add exception info
                )
                # Keep data_json empty

            # Negative prompt from "uc" key in the comment JSON
            self._negative = str(data_json.get("uc", "")).strip()

            # Use common parser for parameters from the comment JSON
            self._parse_common_nai_json(data_json, "legacy comment JSON")

            # Construct raw data representation for legacy format
            raw_parts = [self._info.get("Description", "")]
            if self._info.get("Source"):
                raw_parts.append(f"Source: {self._info.get('Source')}")
            raw_parts.append(
                f"Comment: {comment_str}"
            )  # Include original comment string
            self._raw = "\n".join(filter(None, raw_parts)).strip()

            return True

        except Exception as general_err:
            self._error = f"Error parsing NovelAI legacy PNG: {general_err}"
            self._logger.error(
                "NovelAI legacy parsing error: %s", general_err, exc_info=True
            )
            return False

    def _parse_nai_stealth_png(self) -> bool:
        if not self._extractor:
            self._error = "LSB extractor not available for stealth PNG."
            return False
        try:
            data_length = self._extractor.read_32bit_integer_big_endian()
            if data_length is None:
                self._error = "Could not read data length from LSB stream."
                self._logger.warning(self._error)
                return False
            if (
                data_length <= 0 or data_length > 10 * 1024 * 1024
            ):  # Sanity check length
                self._error = f"Invalid data length from LSB stream: {data_length}"
                self._logger.warning(self._error)
                return False

            compressed_data = self._extractor.get_next_n_bytes(data_length)
            if compressed_data is None or len(compressed_data) != data_length:
                self._error = f"Could not read {data_length} bytes of compressed data from LSB stream."
                self._logger.warning(self._error)
                return False

            json_string = gzip.decompress(compressed_data).decode("utf-8")
            self._raw = json_string  # Store the full decompressed JSON as raw
            main_json_data = json.loads(json_string)

            if not isinstance(main_json_data, dict):
                self._error = "Decompressed LSB data is not a valid JSON dictionary."
                self._logger.warning(self._error)
                return False

            data_to_use_for_prompts_params = main_json_data  # Default

            # NovelAI stealth PNGs can have metadata in a nested "Comment" JSON string
            # or directly in the main JSON ("Description" for positive prompt).
            if "Comment" in main_json_data:
                comment_json_str = str(main_json_data.get("Comment", "{}"))
                try:
                    comment_data_dict = json.loads(comment_json_str)
                    if isinstance(comment_data_dict, dict):
                        self._logger.debug(
                            "Using nested 'Comment' JSON for prompts and parameters."
                        )
                        self._positive = str(
                            comment_data_dict.get("prompt", "")
                        ).strip()
                        self._negative = str(comment_data_dict.get("uc", "")).strip()
                        data_to_use_for_prompts_params = (
                            comment_data_dict  # Use this for params
                        )
                    else:
                        self._logger.warning(
                            "NovelAI stealth 'Comment' field was not a JSON dictionary. Using main JSON. Content: %s",
                            comment_json_str[:200],
                        )
                        self._positive = str(
                            main_json_data.get("Description", "")
                        ).strip()
                        # Negative might not be available if only Description is present
                except json.JSONDecodeError:
                    self._logger.warning(
                        "NovelAI stealth 'Comment' field was not valid JSON. Using main JSON. Content: %s",
                        comment_json_str[:200],
                        exc_info=True,
                    )
                    self._positive = str(main_json_data.get("Description", "")).strip()
            else:
                self._logger.debug(
                    "No 'Comment' field in stealth PNG, using 'Description' for positive prompt."
                )
                self._positive = str(main_json_data.get("Description", "")).strip()
                # Negative prompt might be absent or in the main_json_data directly if structure varies
                self._negative = str(main_json_data.get("uc", "")).strip()

            # Use common parser for parameters
            return self._parse_common_nai_json(
                data_to_use_for_prompts_params, "stealth PNG JSON"
            )

        except gzip.BadGzipFile as e_gzip:
            self._error = f"Invalid GZip data in NovelAI stealth PNG: {e_gzip}"
            self._logger.warning("%s: %s", self.tool, self._error, exc_info=True)
            return False
        except json.JSONDecodeError as e_json:
            self._error = f"Invalid JSON in NovelAI stealth PNG: {e_json}"
            self._logger.warning("%s: %s", self.tool, self._error, exc_info=True)
            return False
        except Exception as general_err:
            self._error = f"Error parsing NovelAI stealth PNG: {general_err}"
            self._logger.error(
                "NovelAI stealth parsing error: %s", general_err, exc_info=True
            )
            return False
