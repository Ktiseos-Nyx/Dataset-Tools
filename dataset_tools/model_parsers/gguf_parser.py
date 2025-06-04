# dataset_tools/model_parsers/gguf_parser.py
import struct
from enum import Enum
from typing import Any  # For type hinting file object 'f'

from ..logger import info_monitor as nfo
from .base_model_parser import (
    BaseModelParser,
)  # Assuming GGUFReadError might come from here or be defined below


# Custom exception for GGUF parsing errors if not in BaseModelParser
class GGUFReadError(ValueError):
    """Custom exception for GGUF parsing errors."""

    pass


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
        self._logger_name = "GGUFParser"  # For consistent logging prefix

    def _read_bytes_or_raise(self, f: Any, num_bytes: int, error_message: str) -> bytes:
        """Reads exact number of bytes or raises GGUFReadError."""
        data_bytes = f.read(num_bytes)
        if len(data_bytes) != num_bytes:
            raise GGUFReadError(
                f"{error_message}: Expected {num_bytes} bytes, got {len(data_bytes)}. EOF or truncated file?"
            )
        return data_bytes

    def _read_string(self, f: Any) -> str:
        length_bytes = self._read_bytes_or_raise(f, 8, "Reading string length")
        length = struct.unpack("<Q", length_bytes)[0]
        if length == 0:
            return ""
        string_bytes = self._read_bytes_or_raise(f, int(length), "Reading string data")
        return string_bytes.decode("utf-8", errors="replace")

    def _get_gguf_value_type_size(self, value_type: GGUFValueType) -> int | None:
        """Returns the fixed size in bytes for a GGUFValueType, or None if variable."""
        if value_type == GGUFValueType.UINT8:
            return 1
        if value_type == GGUFValueType.INT8:
            return 1
        if value_type == GGUFValueType.UINT16:
            return 2
        if value_type == GGUFValueType.INT16:
            return 2
        if value_type == GGUFValueType.UINT32:
            return 4
        if value_type == GGUFValueType.INT32:
            return 4
        if value_type == GGUFValueType.FLOAT32:
            return 4
        if value_type == GGUFValueType.BOOL:
            return 1
        if value_type == GGUFValueType.UINT64:
            return 8
        if value_type == GGUFValueType.INT64:
            return 8
        if value_type == GGUFValueType.FLOAT64:
            return 8
        if value_type in [GGUFValueType.STRING, GGUFValueType.ARRAY]:
            return None
        # This should ideally not be reached if GGUFValueType enum is complete
        # and all members are handled above.
        raise GGUFReadError(f"Logic error: Unhandled GGUFValueType in _get_gguf_value_type_size: {value_type.name}")

    def _read_metadata_value(self, f: Any, value_type_enum_val: int) -> Any:
        try:
            value_type = GGUFValueType(value_type_enum_val)
        except ValueError as exc:
            raise GGUFReadError(f"Unknown GGUF metadata value type integer: {value_type_enum_val}") from exc

        if value_type == GGUFValueType.UINT8:
            return struct.unpack("<B", self._read_bytes_or_raise(f, 1, "UINT8"))[0]
        if value_type == GGUFValueType.INT8:
            return struct.unpack("<b", self._read_bytes_or_raise(f, 1, "INT8"))[0]
        if value_type == GGUFValueType.UINT16:
            return struct.unpack("<H", self._read_bytes_or_raise(f, 2, "UINT16"))[0]
        if value_type == GGUFValueType.INT16:
            return struct.unpack("<h", self._read_bytes_or_raise(f, 2, "INT16"))[0]
        if value_type == GGUFValueType.UINT32:
            return struct.unpack("<I", self._read_bytes_or_raise(f, 4, "UINT32"))[0]
        if value_type == GGUFValueType.INT32:
            return struct.unpack("<i", self._read_bytes_or_raise(f, 4, "INT32"))[0]
        if value_type == GGUFValueType.FLOAT32:
            return struct.unpack("<f", self._read_bytes_or_raise(f, 4, "FLOAT32"))[0]
        if value_type == GGUFValueType.BOOL:
            return struct.unpack("?", self._read_bytes_or_raise(f, 1, "BOOL"))[0]
        if value_type == GGUFValueType.STRING:
            return self._read_string(f)
        if value_type == GGUFValueType.UINT64:
            return struct.unpack("<Q", self._read_bytes_or_raise(f, 8, "UINT64"))[0]
        if value_type == GGUFValueType.INT64:
            return struct.unpack("<q", self._read_bytes_or_raise(f, 8, "INT64"))[0]
        if value_type == GGUFValueType.FLOAT64:
            return struct.unpack("<d", self._read_bytes_or_raise(f, 8, "FLOAT64"))[0]

        if value_type == GGUFValueType.ARRAY:
            array_item_type_bytes = self._read_bytes_or_raise(f, 4, "Array item type")
            array_item_type_int = struct.unpack("<I", array_item_type_bytes)[0]

            array_len_bytes = self._read_bytes_or_raise(f, 8, "Array length")
            array_len = struct.unpack("<Q", array_len_bytes)[0]

            items_for_display = []
            parsed_item_type_name = f"UnknownType({array_item_type_int})"  # Default if GGUFValueType conversion fails

            try:
                array_item_gtype = GGUFValueType(array_item_type_int)
                parsed_item_type_name = array_item_gtype.name

                if array_len == 0:
                    return []

                max_array_items_to_store_for_display = 10
                nfo(f"[{self._logger_name}] GGUF: Processing array of {parsed_item_type_name}, len {array_len}.")

                for i in range(int(array_len)):
                    try:
                        item_value = self._read_metadata_value(f, array_item_type_int)
                        if i < max_array_items_to_store_for_display:
                            items_for_display.append(item_value)
                    except GGUFReadError as e_item:
                        # Error reading a specific item. The file pointer might be messed up for *this array's* remainder.
                        # It's hard to reliably skip the rest of THIS array if an item within it is corrupt/unreadable.
                        nfo(
                            f"[{self._logger_name}] GGUF: Error reading item {i} in array of {parsed_item_type_name} (len {array_len}): {e_item}. Array parsing incomplete."
                        )
                        # Return what was parsed so far, plus an error marker for the array.
                        # Subsequent KV pairs *might* still be readable if this error was contained.
                        return f"[Array of {parsed_item_type_name}, len {array_len}, error at item {i}: {items_for_display}... (partial)]"

                if array_len > max_array_items_to_store_for_display:
                    return f"[Array of {parsed_item_type_name}, len {array_len}, showing first {max_array_items_to_store_for_display} items: {items_for_display} ... (all items processed)]"
                return items_for_display

            except ValueError:  # Error converting array_item_type_int to GGUFValueType
                nfo(
                    f"[{self._logger_name}] GGUF: Unknown array item type int: {array_item_type_int} for array (len {array_len}). Cannot read/skip items."
                )
                # This is critical for the integrity of subsequent KV pairs if this array isn't the last one.
                # We cannot reliably skip the rest of this array's data.
                raise GGUFReadError(
                    f"Unknown array item type {array_item_type_int}. Cannot reliably parse rest of GGUF metadata after this key."
                )

        # Safeguard, should not be reached if GGUFValueType enum and handler are complete.
        raise GGUFReadError(f"Internal error: Unhandled GGUFValueType in _read_metadata_value: {value_type.name}")

    def _process(self) -> None:
        parsed_metadata_kv = {}
        file_summary_info = {}
        try:
            with open(self.file_path, "rb") as f:
                magic = self._read_bytes_or_raise(f, 4, "Magic number")
                if magic != b"GGUF":
                    raise self.NotApplicableError("Not a GGUF file (magic number mismatch).")

                version_bytes = self._read_bytes_or_raise(f, 4, "GGUF version")
                self.gguf_version = struct.unpack("<I", version_bytes)[0]
                file_summary_info["gguf.version"] = self.gguf_version
                if self.gguf_version not in [1, 2, 3]:
                    nfo(
                        f"[{self._logger_name}] Encountered GGUF version {self.gguf_version}. Parser may have limitations."
                    )

                if self.gguf_version >= 2:
                    tc_bytes = self._read_bytes_or_raise(f, 8, "Tensor count")
                    self.tensor_count = struct.unpack("<Q", tc_bytes)[0]
                    mc_bytes = self._read_bytes_or_raise(f, 8, "Metadata KV count")
                    self.metadata_kv_count = struct.unpack("<Q", mc_bytes)[0]
                else:
                    tc_bytes = self._read_bytes_or_raise(f, 4, "Tensor count v1")
                    self.tensor_count = struct.unpack("<I", tc_bytes)[0]
                    mc_bytes = self._read_bytes_or_raise(f, 4, "Metadata KV count v1")
                    self.metadata_kv_count = struct.unpack("<I", mc_bytes)[0]

                file_summary_info["gguf.tensor_count"] = self.tensor_count
                file_summary_info["gguf.metadata_kv_count"] = self.metadata_kv_count
                nfo(
                    f"[{self._logger_name}] GGUF v{self.gguf_version}, Tensors: {self.tensor_count}, Meta KVs: {self.metadata_kv_count}"
                )

                for i in range(int(self.metadata_kv_count)):
                    key = ""  # Initialize key in case _read_string fails before assignment
                    try:
                        key = self._read_string(f)
                        value_type_bytes = self._read_bytes_or_raise(f, 4, f"Value type for key '{key}'")
                        value_type_val = struct.unpack("<I", value_type_bytes)[0]

                        value = self._read_metadata_value(f, value_type_val)
                        parsed_metadata_kv[key] = value
                    except GGUFReadError as e_kv:
                        error_key_name = key if key else f"KV pair at index {i}"
                        nfo(
                            f"[{self._logger_name}] GGUFReadError for '{error_key_name}': {e_kv}. Stopping metadata read."
                        )
                        parsed_metadata_kv[error_key_name] = f"[Error reading value: {e_kv}]"
                        self._error_message = (
                            f"Failed reading GGUF KV pair '{error_key_name}': {e_kv}"  # Store specific error
                        )
                        self.status = self.Status.PARTIAL_SUCCESS  # Or FORMAT_ERROR if preferred for fatal read issues
                        break  # Stop processing further KVs
                    except struct.error as e_s:  # Should be caught by GGUFReadError from _read_bytes_or_raise
                        error_key_name = key if key else f"KV pair at index {i}"
                        nfo(
                            f"[{self._logger_name}] Struct error for '{error_key_name}': {e_s}. Stopping metadata read."
                        )
                        parsed_metadata_kv[error_key_name] = f"[Struct error: {e_s}]"
                        self._error_message = f"Struct error for GGUF KV pair '{error_key_name}': {e_s}"
                        self.status = self.Status.FORMAT_ERROR
                        break

                self.metadata_header = parsed_metadata_kv
                self.main_header = file_summary_info
                if not self._error_message:  # If loop completed without fatal errors
                    self.status = self.Status.READ_SUCCESS

        except FileNotFoundError:
            raise
        except self.NotApplicableError:
            raise
        except GGUFReadError as e_gguf_header:  # Catch GGUFReadError for header specific issues
            self._error_message = f"Fatal GGUF header parsing error: {e_gguf_header}"
            self.status = self.Status.FORMAT_ERROR
            raise ValueError(self._error_message) from e_gguf_header  # Re-raise as ValueError for BaseModelParser
        except struct.error as e_struct_header:  # Should be caught by GGUFReadError now
            self._error_message = f"GGUF file structure error (header): {e_struct_header}"
            self.status = self.Status.FORMAT_ERROR
            raise ValueError(self._error_message) from e_struct_header
        except Exception as e_general:
            self._error_message = f"Unexpected error parsing GGUF {self.file_path}: {e_general}"
            self.status = self.Status.FORMAT_ERROR
            raise ValueError(self._error_message) from e_general
