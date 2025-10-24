# dataset_tools/model_parsers/safetensors_parser.py
import hashlib
import json
import struct
from pathlib import Path

from ..civitai_api import get_model_info_by_hash
from ..logger import info_monitor
from .base_model_parser import BaseModelParser, ModelParserStatus


class SafetensorsParser(BaseModelParser):
    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.tool_name = "Safetensors Model File"
        self.parameters = {}
        self.full_hash = None
        self.autov2_hash = None
        self.civitai_api_info = None  # To store results from Civitai API

    def _calculate_hashes(self) -> None:
        """Calculate the full SHA256 hash and the Civitai AutoV2 hash."""
        sha256_hash = hashlib.sha256()
        try:
            with open(self.file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            self.full_hash = sha256_hash.hexdigest()
            self.autov2_hash = self.full_hash[:10]
            info_monitor("[%s] Calculated Hashes for %s: AutoV2=%s", self._logger_name, self.file_path, self.autov2_hash)
        except Exception as e:
            info_monitor("[%s] Error calculating hash for %s: %s", self._logger_name, self.file_path, e)

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
                        "Reported safetensors header size is excessively large: %d bytes." % length_of_header
                    )

                header_json_bytes = f.read(length_of_header)
                if len(header_json_bytes) < length_of_header:
                    raise ValueError(
                        "Corrupted safetensors file: Expected header of %d bytes, got %d." % (length_of_header, len(header_json_bytes))
                    )

                header_json_str = header_json_bytes.decode("utf-8", errors="strict")
                header_data = json.loads(header_json_str)  # Don't strip, spec implies no leading/trailing whitespace

            # Store the entire header as raw metadata before modifying it
            self.raw_metadata = header_data.copy()

            # Successfully parsed header JSON
            if "__metadata__" in header_data:
                self.metadata_header = header_data.pop("__metadata__")
                # NEW: Explicitly parse training parameters
                self.parameters = {}
                for key, value in self.metadata_header.items():
                    if key.startswith("ss_") or key.startswith("modelspec."):
                        self.parameters[key] = value

                if self.parameters:
                    self.tool_name = "Safetensors (LoRA Training Meta)"
                elif self.metadata_header:
                    self.tool_name = "Safetensors (with metadata)"
                else:
                    self.tool_name = "Safetensors (empty __metadata__)"
            else:
                self.metadata_header = {}  # Ensure it's a dict
                self.tool_name = "Safetensors (no __metadata__ section)"

            self.main_header = header_data  # The rest of the header (tensor index)

            # Calculate file hashes for API lookup
            self._calculate_hashes()

            # If we have a hash, query the Civitai API
            if self.autov2_hash:
                try:
                    self.civitai_api_info = get_model_info_by_hash(self.autov2_hash)
                except Exception as e:
                    self.logger.error("Civitai API lookup failed within SafetensorsParser: %s", e)

            self.status = ModelParserStatus.SUCCESS  # Explicitly set success

        except struct.error as e_struct:
            # This typically means the first 8 bytes weren't a valid u64, so not safetensors.
            self._error_message = (
                "Safetensors struct error (likely not safetensors or corrupted header length): %s" % e_struct
            )
            raise self.NotApplicableError(self._error_message) from e_struct
        except (json.JSONDecodeError, UnicodeDecodeError) as e_decode:
            # This means it looked like safetensors (header length read), but header content was bad.
            self._error_message = "Safetensors header content error (JSON or UTF-8 invalid): %s" % e_decode
            # This is a FAILURE of a safetensors file, not "Not Applicable".
            self.status = ModelParserStatus.FAILURE  # Set status before raising ValueError
            raise ValueError(self._error_message) from e_decode
        except ValueError as e_val:  # Catches our "large header", "zero header", "corrupted header"
            self._error_message = "Safetensors format validation error: %s" % e_val
            self.status = ModelParserStatus.FAILURE
            raise ValueError(self._error_message) from e_val
        # FileNotFoundError is handled by BaseModelParser
        # Other OSErrors, MemoryErrors will be caught by BaseModelParser's generic handlers
