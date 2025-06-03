# dataset_tools/model_parsers/gguf_parser.py
import struct
from enum import Enum

from ..logger import info_monitor as nfo
from .base_model_parser import BaseModelParser


class GGUFValueType(Enum):
    UINT8 = 0
    INT8 = 1
    UINT16 = 2
    INT16 = 3
    UINT32 = 4
    INT32 = 5
    FLOAT32 = 6
    BOOL = 7
    STRING = 8
    ARRAY = 9
    UINT64 = 10
    INT64 = 11
    FLOAT64 = 12


class GGUFParser(BaseModelParser):
    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.tool_name = "GGUF Model File"
        self.gguf_version = None
        self.tensor_count = None
        self.metadata_kv_count = None

    def _read_string(self, f) -> str:
        length = struct.unpack("<Q", f.read(8))[0]
        return f.read(length).decode("utf-8", errors="replace")

    def _read_metadata_value(self, f, value_type_enum_val: int):
        try:
            value_type = GGUFValueType(value_type_enum_val)
        except ValueError as exc:  # Capture original exception
            # If value_type_enum_val is unknown, we can't know how many bytes to read.
            # This is a critical format error.
            raise ValueError(
                f"Unknown GGUF metadata value type integer: {value_type_enum_val}",
            ) from exc  # CORRECTED: Chain the original exception

        if value_type == GGUFValueType.UINT8:
            return struct.unpack("<B", f.read(1))[0]
        if value_type == GGUFValueType.INT8:
            return struct.unpack("<b", f.read(1))[0]
        if value_type == GGUFValueType.UINT16:
            return struct.unpack("<H", f.read(2))[0]
        if value_type == GGUFValueType.INT16:
            return struct.unpack("<h", f.read(2))[0]
        if value_type == GGUFValueType.UINT32:
            return struct.unpack("<I", f.read(4))[0]
        if value_type == GGUFValueType.INT32:
            return struct.unpack("<i", f.read(4))[0]
        if value_type == GGUFValueType.FLOAT32:
            return struct.unpack("<f", f.read(4))[0]
        if value_type == GGUFValueType.BOOL:
            return struct.unpack("?", f.read(1))[0]
        if value_type == GGUFValueType.STRING:
            return self._read_string(f)
        if value_type == GGUFValueType.UINT64:
            return struct.unpack("<Q", f.read(8))[0]
        if value_type == GGUFValueType.INT64:
            return struct.unpack("<q", f.read(8))[0]
        if value_type == GGUFValueType.FLOAT64:
            return struct.unpack("<d", f.read(8))[0]
        if value_type == GGUFValueType.ARRAY:
            array_item_type_int = struct.unpack("<I", f.read(4))[0]
            array_len = struct.unpack("<Q", f.read(8))[0]
            items = []
            try:
                array_item_gtype = GGUFValueType(array_item_type_int)
                # Limit array parsing for display to avoid excessive reads/memory
                max_array_items_to_parse = 20  # Configurable limit
                if 0 < array_len <= max_array_items_to_parse:
                    for _ in range(int(array_len)):  # Ensure array_len is int for range
                        items.append(self._read_metadata_value(f, array_item_type_int))
                    return items
                if array_len > 0:  # If array is too long or parsing is skipped
                    nfo(
                        "[%s] GGUF metadata array of type %s with len %s. Content not fully parsed for display.",
                        self._logger_name,
                        array_item_gtype.name,
                        array_len,
                    )
                    # To correctly skip the rest of the array, we'd need to calculate its byte size,
                    # which is complex if elements have variable sizes (e.g., strings).
                    # For now, we are not skipping, which might lead to issues if this
                    # isn't the last KV pair. This part needs careful handling for robust GGUF parsing.
                    # For a simple metadata viewer, returning a placeholder might be acceptable if full parsing is too complex.
                    return f"[Array of {array_item_gtype.name}, len {array_len}, partially/not parsed]"
                # array_len is 0
                return []  # Empty array
            except ValueError:  # Error determining array item type
                # Log the error and return a placeholder for the array
                nfo(
                    "[%s] Unknown GGUF array item type integer: %s for array of len %s.",
                    self._logger_name,
                    array_item_type_int,
                    array_len,
                )
                # Similar to above, skipping bytes for an unknown type array is hard.
                return f"[Array of Unknown Type ({array_item_type_int}), len {array_len} - Not parsed due to type error]"
        else:
            # This case should ideally not be reached if all GGUFValueType members are handled.
            # It's a safeguard.
            raise ValueError(f"Unhandled GGUFValueType enum member: {value_type}")

    def _process(self) -> None:
        parsed_metadata_kv = {}
        file_summary_info = {}
        try:
            with open(self.file_path, "rb") as f:
                magic = f.read(4)
                if magic != b"GGUF":
                    raise self.NotApplicableError(
                        "Not a GGUF file (magic number mismatch)."
                    )

                self.gguf_version = struct.unpack("<I", f.read(4))[0]
                file_summary_info["gguf.version"] = self.gguf_version
                if self.gguf_version not in [1, 2, 3]:  # Known GGUF versions
                    nfo(
                        "[%s] Encountered GGUF version %s. Parser may have limitations.",
                        self._logger_name,
                        self.gguf_version,
                    )

                if self.gguf_version >= 2:  # GGUFv2/v3 use 64-bit for counts
                    self.tensor_count = struct.unpack("<Q", f.read(8))[0]
                    self.metadata_kv_count = struct.unpack("<Q", f.read(8))[0]
                else:  # GGUFv1 uses 32-bit
                    self.tensor_count = struct.unpack("<I", f.read(4))[0]
                    self.metadata_kv_count = struct.unpack("<I", f.read(4))[0]

                file_summary_info["gguf.tensor_count"] = self.tensor_count
                file_summary_info["gguf.metadata_kv_count"] = self.metadata_kv_count
                nfo(
                    "[%s] GGUF v%s, Tensors: %s, Meta KVs: %s",
                    self._logger_name,
                    self.gguf_version,
                    self.tensor_count,
                    self.metadata_kv_count,
                )

                for i in range(int(self.metadata_kv_count)):  # Ensure count is int
                    key = self._read_string(f)
                    value_type_val = struct.unpack("<I", f.read(4))[
                        0
                    ]  # GGUF type is u32
                    try:
                        value = self._read_metadata_value(f, value_type_val)
                        parsed_metadata_kv[key] = value
                    except ValueError as ve_val:  # Error reading a specific value
                        nfo(
                            "[%s] Error reading GGUF metadata value for key '%s': %s. Storing as error string.",
                            self._logger_name,
                            key,
                            ve_val,
                        )
                        parsed_metadata_kv[key] = f"[Error reading value: {ve_val}]"
                    except (
                        struct.error
                    ) as se_val:  # Struct error often means EOF or corruption for this value
                        nfo(
                            "[%s] Struct error reading GGUF metadata value for key '%s': %s. "
                            "File might be truncated. Stopping metadata read.",
                            self._logger_name,
                            key,
                            se_val,
                        )
                        parsed_metadata_kv[key] = (
                            f"[Struct error reading value: {se_val}]"
                        )
                        break  # Stop processing further KVs if a struct error occurs during value read

                self.metadata_header = parsed_metadata_kv
                self.main_header = file_summary_info

        except FileNotFoundError:  # Let BaseModelParser.parse() handle this
            raise
        except self.NotApplicableError:  # Let BaseModelParser.parse() handle this
            raise
        except (
            struct.error
        ) as e_struct:  # Errors reading initial header fields (magic, version, counts)
            self._error_message = f"GGUF file structure error (possibly corrupted or truncated early): {e_struct}"
            raise ValueError(self._error_message) from e_struct  # Chain exception
        except (
            ValueError
        ) as e_val:  # Catches ValueErrors from _read_metadata_value or other validation
            # If e_val already has a message, self._error_message might be redundant
            # unless we want to prefix it.
            self._error_message = f"Error parsing GGUF data: {e_val}"
            raise  # Re-raise the original ValueError to be caught by BaseModelParser.parse()
        except (
            MemoryError,
            OSError,
            RuntimeError,
        ) as e_runtime:  # Other system/runtime issues
            self._error_message = (
                f"Runtime error parsing GGUF file {self.file_path}: {e_runtime}"
            )
            raise ValueError(self._error_message) from e_runtime
        except (
            Exception
        ) as e_general:  # Fallback for truly unexpected issues
            self._error_message = (
                f"Unexpected error parsing GGUF file {self.file_path}: {e_general}"
            )
            raise ValueError(self._error_message) from e_general
