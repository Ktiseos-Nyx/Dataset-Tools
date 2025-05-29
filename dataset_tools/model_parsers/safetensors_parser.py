# dataset_tools/model_parsers/safetensors_parser.py
import struct
import json
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
                    raise ValueError("File too small to be a valid safetensors file.")

                length_of_header = struct.unpack("<Q", first_8_bytes)[0]

                # Basic sanity check on header length
                # (e.g., if length_of_header > 50MB, it's probably wrong)
                # max_reasonable_header = 50 * 1024 * 1024
                # if length_of_header > max_reasonable_header:
                #     raise ValueError(f"Unusually large header size reported: {length_of_header} bytes")

                header_json_str = f.read(length_of_header).decode("utf-8", errors="strict")
                header_data = json.loads(header_json_str.strip())

            if "__metadata__" in header_data:
                self.metadata_header = header_data.pop("__metadata__")

            self.main_header = header_data  # The rest of the header
            # self.processed_raw_data_display can be the full header_json_str or a summary

        except struct.error as e:
            self._error_message = f"Safetensors struct error (likely not safetensors): {e}"
            raise self.NotApplicableError(self._error_message)  # Or just raise ValueError
        except json.JSONDecodeError as e:
            self._error_message = f"Safetensors JSON header decode error: {e}"
            raise ValueError(self._error_message)  # This is a parsing failure for this type
        except UnicodeDecodeError as e:
            self._error_message = f"Safetensors header UTF-8 decode error: {e}"
            raise ValueError(self._error_message)
        except FileNotFoundError:
            self._error_message = "File not found."
            raise  # Re-raise FileNotFoundError to be handled by dispatcher
        except Exception as e:  # Catch-all for other unexpected errors
            self._error_message = f"Unexpected error parsing safetensors: {e}"
            raise ValueError(self._error_message)
