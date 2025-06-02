# dataset_tools/vendored_sdpr/format/novelai.py

__author__ = "receyuki"
__filename__ = "novelai.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import gzip
import json
import logging  # For type hinting
from typing import Any  # For type hints

from PIL import Image  # For type hint of LSBExtractor input

# from ..logger import Logger # OLD
from ..logger import get_logger  # NEW
from .base_format import BaseFormat
from .utility import remove_quotes


class NovelAI(BaseFormat):
    tool = "NovelAI"

    class LSBExtractor:
        def __init__(self, img_pil_object: Image.Image):  # Type hint for img_pil_object
            self.img_pil = img_pil_object
            self.data = list(img_pil_object.getdata())
            self.width, self.height = img_pil_object.size
            self.byte_cursor = 0
            self.lsb_bytes_list = bytearray()
            current_byte = 0
            bit_count = 0
            if img_pil_object.mode == "RGBA":
                for pixel_index in range(self.width * self.height):
                    alpha_val = self.data[pixel_index][3]
                    lsb = alpha_val & 1
                    current_byte = (current_byte << 1) | lsb
                    bit_count += 1
                    if bit_count == 8:
                        self.lsb_bytes_list.append(current_byte)
                        current_byte = 0
                        bit_count = 0

        # Renamed n to n_bytes, return Optional
        def get_next_n_bytes(self, n_bytes: int) -> bytes | None:
            if self.byte_cursor + n_bytes > len(self.lsb_bytes_list):
                return None
            result_bytes = self.lsb_bytes_list[
                self.byte_cursor : self.byte_cursor + n_bytes
            ]
            self.byte_cursor += n_bytes
            return bytes(result_bytes)

        # Return Optional
        def read_32bit_integer_big_endian(self) -> int | None:
            byte_chunk = self.get_next_n_bytes(4)
            if byte_chunk and len(byte_chunk) == 4:
                return int.from_bytes(byte_chunk, byteorder="big")
            return None

    def __init__(
        self,
        info: dict[str, Any] | None = None,  # Added Optional, Dict, Any
        raw: str = "",
        extractor: LSBExtractor | None = None,  # Type hint, Optional
        width: int = 0,
        height: int = 0,
    ):
        super().__init__(info=info, raw=raw, width=width, height=height)
        # self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool}") # OLD
        self._logger: logging.Logger = get_logger(
            f"DSVendored_SDPR.Format.{self.tool}",
        )  # NEW
        # self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER # Inherited
        self._extractor = extractor

    def _process(self):
        # pylint: disable=no-member # Temporarily add if Pylint still complains
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")
        parsed_successfully = False
        if self._info and self._info.get("Software") == "NovelAI":
            self._logger.debug(
                "Found 'Software: NovelAI' tag, attempting legacy PNG parse.",
            )
            parsed_successfully = self._parse_nai_legacy_png()
        elif self._extractor:
            self._logger.debug("LSB Extractor provided, attempting stealth PNG parse.")
            parsed_successfully = self._parse_nai_stealth_png()
        else:
            self._logger.warn(
                f"{self.tool}: Neither legacy PNG info nor LSB extractor provided.",
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = (
                "No data source for NovelAI parser (legacy info or LSB extractor)."
            )
            return

        if parsed_successfully:
            self.status = self.Status.READ_SUCCESS
            self._logger.info(f"{self.tool}: Data parsed successfully.")
        else:
            self.status = self.Status.FORMAT_ERROR
            if not self._error:
                self._error = f"{self.tool}: Failed to parse metadata."

    def _parse_nai_legacy_png(self) -> bool:
        # pylint: disable=no-member
        try:
            self._positive = str(self._info.get("Description", "")).strip()
            comment_str = self._info.get("Comment", "{}")
            data_json = json.loads(comment_str)
            if not isinstance(data_json, dict):
                self._error = (
                    "Legacy NovelAI 'Comment' field is not a valid JSON dictionary."
                )
                return False
            self._negative = str(data_json.get("uc", "")).strip()
            param_map = {
                "sampler": "sampler_name",
                "seed": "seed",
                "strength": "denoising_strength",
                "noise": "noise_offset",
                "scale": "cfg_scale",
                "steps": "steps",
            }
            for nai_key, canonical_key in param_map.items():
                if nai_key in data_json and canonical_key in self._parameter:
                    self._parameter[canonical_key] = str(data_json[nai_key])
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"
            setting_parts = []
            for k, v_val in data_json.items():  # Renamed v to v_val
                if k not in ["uc"] + list(param_map.keys()):
                    setting_parts.append(
                        f"{k.capitalize()}: {remove_quotes(str(v_val))}",
                    )
            self._setting = ", ".join(sorted(setting_parts))
            self._raw = "\n".join(
                filter(
                    None,
                    [self._positive, self._negative, f"Comment: {comment_str}"],
                ),
            ).strip()
            return True
        except json.JSONDecodeError as json_decode_err:  # Renamed 'e'
            self._error = f"Invalid JSON in NovelAI legacy 'Comment': {json_decode_err}"
            return False
        except Exception as general_err:  # Renamed 'e', pylint: disable=broad-except
            self._error = f"Error parsing NovelAI legacy PNG: {general_err}"
            self._logger.error(
                f"NovelAI legacy parsing error: {general_err}",
                exc_info=True,
            )
            return False

    def _parse_nai_stealth_png(self) -> bool:
        # pylint: disable=no-member
        if not self._extractor:  # Should not happen if _process logic is correct
            self._error = "LSB extractor not available for stealth PNG."
            return False
        try:
            data_length_bytes = self._extractor.read_32bit_integer_big_endian()
            if data_length_bytes is None:
                self._error = "Could not read data length from LSB stream."
                return False
            compressed_data = self._extractor.get_next_n_bytes(data_length_bytes)
            if compressed_data is None or len(compressed_data) != data_length_bytes:
                self._error = f"Could not read {data_length_bytes} bytes of compressed data from LSB stream."
                return False

            json_string = gzip.decompress(compressed_data).decode("utf-8")
            data_json = json.loads(json_string)
            if not isinstance(data_json, dict):
                self._error = "Decompressed LSB data is not a valid JSON dictionary."
                return False
            self._raw = json_string
            data_for_params = data_json  # Default

            if "Comment" in data_json:
                comment_json_str = data_json.pop("Comment", "{}")
                try:
                    comment_data = json.loads(comment_json_str)
                    if isinstance(comment_data, dict):
                        self._positive = str(comment_data.get("prompt", "")).strip()
                        self._negative = str(comment_data.get("uc", "")).strip()
                        data_for_params = comment_data
                except json.JSONDecodeError:
                    self._logger.warn(
                        "NovelAI stealth 'Comment' field was not valid JSON. Using main JSON for prompt/params.",
                    )
                    # Fallback to Description
                    self._positive = str(data_json.get("Description", "")).strip()
            else:
                self._positive = str(data_json.get("Description", "")).strip()

            param_map = {
                "sampler": "sampler_name",
                "seed": "seed",
                "strength": "denoising_strength",
                "noise": "noise_offset",
                "scale": "cfg_scale",
                "steps": "steps",
                "width": "width",
                "height": "height",
            }
            for nai_key, canonical_key in param_map.items():
                if nai_key in data_for_params and canonical_key in self._parameter:
                    self._parameter[canonical_key] = str(data_for_params.get(nai_key))

            if data_for_params.get("width") is not None:
                self._width = str(data_for_params.get("width"))
            if data_for_params.get("height") is not None:
                self._height = str(data_for_params.get("height"))
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            setting_parts = []
            for k, v_val in data_for_params.items():  # Renamed v to v_val
                if k not in ["prompt", "uc", "Description", "Comment"] + list(
                    param_map.keys(),
                ):
                    setting_parts.append(
                        f"{k.capitalize()}: {remove_quotes(str(v_val))}",
                    )
            self._setting = ", ".join(sorted(setting_parts))
            return True
        except gzip.BadGzipFile as e_gzip:
            self._error = f"Invalid GZip data in NovelAI stealth PNG: {e_gzip}"
            return False
        except json.JSONDecodeError as e_json:
            self._error = f"Invalid JSON in NovelAI stealth PNG: {e_json}"
            return False
        except Exception as general_err:  # Renamed 'e', pylint: disable=broad-except
            self._error = f"Error parsing NovelAI stealth PNG: {general_err}"
            self._logger.error(
                f"NovelAI stealth parsing error: {general_err}",
                exc_info=True,
            )
            return False
