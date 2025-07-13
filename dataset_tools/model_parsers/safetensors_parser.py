# dataset_tools/model_parsers/safetensors_parser.py
import json
import struct
from pathlib import Path  # Used for Path object, not strictly necessary for current logic but good practice

from .base_model_parser import BaseModelParser, ModelParserStatus


class SafetensorsParser(BaseModelParser):
    def __init__(self, file_path: str):
        super().__init__(file_path)
        # self.tool_name will be set by BaseModelParser
        # It can be refined in _process.
        self.tool_name = "Safetensors Model File"  # Default before refinement

    def _process(self) -> None:
        # BaseModelParser's parse() method handles FileNotFoundError.
        # This _process method assumes the file exists.

        # Check file extension first for early exit via NotApplicableError
        file_path_obj = Path(self.file_path)
        if not file_path_obj.suffix.lower() == ".safetensors":
            raise self.NotApplicableError("File is not a .safetensors file (wrong extension).")

        try:
            with open(self.file_path, "rb") as f:
                # Read the length of the JSON header (8 bytes, little-endian unsigned long long)
                header_len_bytes = f.read(8)
                if len(header_len_bytes) < 8:
                    # This indicates it's not a valid safetensor file or is severely truncated.
                    # Raise NotApplicable because it doesn't even have the header length.
                    raise self.NotApplicableError("File too small to contain safetensors header length.")

                length_of_header = struct.unpack("<Q", header_len_bytes)[0]

                # Basic sanity check for header length
                # Max reasonable header size (e.g., 100MB). Adjust if very large headers are common.
                MAX_HEADER_SIZE = 100 * 1024 * 1024
                if length_of_header == 0:
                    raise ValueError("Safetensors header length is zero.")
                if length_of_header > MAX_HEADER_SIZE:
                    raise ValueError(
                        f"Reported safetensors header size is excessively large: {length_of_header} bytes."
                    )

                header_json_bytes = f.read(length_of_header)
                if len(header_json_bytes) < length_of_header:
                    raise ValueError(
                        f"Corrupted safetensors file: Expected header of {length_of_header} bytes, got {len(header_json_bytes)}."
                    )

                header_json_str = header_json_bytes.decode("utf-8", errors="strict")
                header_data = json.loads(header_json_str)  # Don't strip, spec implies no leading/trailing whitespace

            # Successfully parsed header JSON
            if "__metadata__" in header_data:
                self.metadata_header = header_data.pop("__metadata__")
                # Refine tool_name based on metadata if present
                if "ss_sd_model_name" in self.metadata_header:  # Kohya SS specific key
                    self.tool_name = f"Safetensors ({self.metadata_header['ss_sd_model_name']})"
                elif "format" in self.metadata_header:  # Generic format key
                    self.tool_name = f"Safetensors (format: {self.metadata_header['format']})"
                elif self.metadata_header:  # Has some metadata
                    self.tool_name = "Safetensors (with metadata)"
                else:  # __metadata__ was present but empty
                    self.tool_name = "Safetensors (empty __metadata__)"
            else:
                self.metadata_header = {}  # Ensure it's a dict
                self.tool_name = "Safetensors (no __metadata__ section)"

            self.main_header = header_data  # The rest of the header (tensor index)
            self.status = ModelParserStatus.SUCCESS  # Explicitly set success

        except struct.error as e_struct:
            # This typically means the first 8 bytes weren't a valid u64, so not safetensors.
            self._error_message = (
                f"Safetensors struct error (likely not safetensors or corrupted header length): {e_struct}"
            )
            raise self.NotApplicableError(self._error_message) from e_struct
        except (json.JSONDecodeError, UnicodeDecodeError) as e_decode:
            # This means it looked like safetensors (header length read), but header content was bad.
            self._error_message = f"Safetensors header content error (JSON or UTF-8 invalid): {e_decode}"
            # This is a FAILURE of a safetensors file, not "Not Applicable".
            self.status = ModelParserStatus.FAILURE  # Set status before raising ValueError
            raise ValueError(self._error_message) from e_decode
        except ValueError as e_val:  # Catches our "large header", "zero header", "corrupted header"
            self._error_message = f"Safetensors format validation error: {e_val}"
            self.status = ModelParserStatus.FAILURE
            raise ValueError(self._error_message) from e_val
        # FileNotFoundError is handled by BaseModelParser
        # Other OSErrors, MemoryErrors will be caught by BaseModelParser's generic handlers
