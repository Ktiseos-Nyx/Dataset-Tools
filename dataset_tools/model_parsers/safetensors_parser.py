# dataset_tools/model_parsers/safetensors_parser.py
import json
import struct

from .base_model_parser import BaseModelParser


class SafetensorsParser(BaseModelParser):
    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.tool_name = "Safetensors"

    def _process(self) -> None:
        try:
            with open(self.file_path, "rb") as f:
                first_8_bytes = f.read(8)
                if len(first_8_bytes) < 8:
                    # This indicates it's not a valid safetensor, so NotApplicable or specific ValueError
                    raise ValueError("File too small to be a valid safetensors file.")

                length_of_header = struct.unpack("<Q", first_8_bytes)[0]

                # Basic sanity check (example: header > 1GB is unreasonable)
                # This value might need tuning.
                if length_of_header > 1 * 1024 * 1024 * 1024:
                    raise ValueError(
                        f"Reported safetensors header size is excessively large: {length_of_header} bytes."
                    )

                header_json_str = f.read(length_of_header).decode(
                    "utf-8", errors="strict"
                )
                header_data = json.loads(header_json_str.strip())

            if "__metadata__" in header_data:
                self.metadata_header = header_data.pop("__metadata__")
            self.main_header = header_data

        except (
            FileNotFoundError
        ):  # Let BaseModelParser handle this for consistent status
            raise
        except struct.error as e_struct:
            self._error_message = f"Safetensors struct error (likely not safetensors or corrupted): {e_struct}"
            raise self.NotApplicableError(self._error_message) from e_struct
        except (json.JSONDecodeError, UnicodeDecodeError) as e_decode:
            self._error_message = (
                f"Safetensors header decode error (JSON or UTF-8): {e_decode}"
            )
            raise ValueError(
                self._error_message
            ) from e_decode  # Indicates parsing failure for this type
        except ValueError as e_val:  # Catches our "file too small" or "large header"
            self._error_message = f"Safetensors format validation error: {e_val}"
            # Could be NotApplicableError if "file too small" means it's not this type.
            # Or ValueError if "large header" means it's corrupted but claims to be safetensors.
            # For now, let it be ValueError, which BaseModelParser will turn into FAILURE.
            raise ValueError(self._error_message) from e_val
        except (OSError, MemoryError) as e_os_mem:  # Other system-level issues
            self._error_message = f"System error parsing safetensors: {e_os_mem}"
            raise ValueError(self._error_message) from e_os_mem
        except Exception as e_general:
            self._error_message = f"Unexpected error parsing safetensors: {e_general}"
            raise ValueError(self._error_message) from e_general
