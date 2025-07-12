# dataset_tools/model_parsers/gguf_parser.py
import struct
from enum import Enum
from typing import Any

from ..logger import info_monitor  # Assuming info_monitor is correctly imported
from .base_model_parser import BaseModelParser, ModelParserStatus


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
        # self.tool_name will be set by BaseModelParser as "GGUFModelFile" (or similar)
        # It can be refined in _process if more specific info is found.
        # self._logger_name is also set by BaseModelParser.
        self.gguf_version = None
        self.tensor_count = None
        self.metadata_kv_count = None
        # Default tool name before specific parsing
        self.tool_name = "GGUF Model File"

    def _read_bytes_or_raise(self, f: Any, num_bytes: int, error_context: str) -> bytes:
        data_bytes = f.read(num_bytes)
        if len(data_bytes) != num_bytes:
            raise GGUFReadError(
                f"{error_context}: Expected {num_bytes} bytes, got {len(data_bytes)}. EOF or truncated file?"
            )
        return data_bytes

    def _read_string(self, f: Any) -> str:
        length_bytes = self._read_bytes_or_raise(f, 8, "Reading string length")
        length = struct.unpack("<Q", length_bytes)[0]
        if length == 0:
            return ""
        string_bytes = self._read_bytes_or_raise(f, int(length), "Reading string data")
        return string_bytes.decode("utf-8", errors="replace")

    def _read_metadata_value(self, f: Any, value_type_enum_val: int) -> Any:
        try:
            value_type = GGUFValueType(value_type_enum_val)
        except ValueError as exc:
            raise GGUFReadError(f"Unknown GGUF metadata value type integer: {value_type_enum_val}") from exc

        type_size_map = {
            GGUFValueType.UINT8: ("<B", 1, "UINT8"),
            GGUFValueType.INT8: ("<b", 1, "INT8"),
            GGUFValueType.UINT16: ("<H", 2, "UINT16"),
            GGUFValueType.INT16: ("<h", 2, "INT16"),
            GGUFValueType.UINT32: ("<I", 4, "UINT32"),
            GGUFValueType.INT32: ("<i", 4, "INT32"),
            GGUFValueType.FLOAT32: ("<f", 4, "FLOAT32"),
            GGUFValueType.BOOL: ("?", 1, "BOOL"),
            GGUFValueType.UINT64: ("<Q", 8, "UINT64"),
            GGUFValueType.INT64: ("<q", 8, "INT64"),
            GGUFValueType.FLOAT64: ("<d", 8, "FLOAT64"),
        }

        if value_type in type_size_map:
            fmt, size, name = type_size_map[value_type]
            return struct.unpack(fmt, self._read_bytes_or_raise(f, size, name))[0]

        if value_type == GGUFValueType.STRING:
            return self._read_string(f)

        if value_type == GGUFValueType.ARRAY:
            array_item_type_bytes = self._read_bytes_or_raise(f, 4, "Array item type")
            array_item_type_int = struct.unpack("<I", array_item_type_bytes)[0]
            array_len_bytes = self._read_bytes_or_raise(f, 8, "Array length")
            array_len = struct.unpack("<Q", array_len_bytes)[0]

            items_for_display = []
            parsed_item_type_name = f"UnknownType({array_item_type_int})"
            try:
                array_item_gtype = GGUFValueType(array_item_type_int)
                parsed_item_type_name = array_item_gtype.name
            except ValueError:  # Unknown array item type int
                # This is critical for the integrity of subsequent KV pairs.
                raise GGUFReadError(
                    f"Unknown array item type {array_item_type_int} for array (len {array_len}). Cannot reliably parse rest of GGUF metadata."
                )

            if array_len == 0:
                return []

            max_array_items_to_store_for_display = 10  # Arbitrary limit for display
            info_monitor(
                "[%s] GGUF: Processing array of %s, len %d.",
                self._logger_name,
                parsed_item_type_name,
                array_len,
            )

            for i in range(int(array_len)):
                try:
                    item_value = self._read_metadata_value(f, array_item_type_int)
                    if i < max_array_items_to_store_for_display:
                        items_for_display.append(item_value)
                except GGUFReadError as e_item:
                    info_monitor(
                        "[%s] GGUF: Error reading item %d in array of %s (len %d): %s. Array parsing incomplete.",
                        self._logger_name,
                        i,
                        parsed_item_type_name,
                        array_len,
                        e_item,
                    )
                    # Returning a string representation indicating partial data and error
                    return f"[Array of {parsed_item_type_name}, len {array_len}, error at item {i}: {items_for_display}... (partial)]"

            if array_len > max_array_items_to_store_for_display:
                return f"[Array of {parsed_item_type_name}, len {array_len}, showing first {max_array_items_to_store_for_display} items: {items_for_display} ... (all items processed)]"
            return items_for_display

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
                self.tool_name = f"GGUF v{self.gguf_version} Model File"  # Refine tool name

                if self.gguf_version not in [1, 2, 3]:  # Known versions
                    info_monitor(
                        "[%s] Encountered GGUF version %d. Parser may have limitations for unknown future versions.",
                        self._logger_name,
                        self.gguf_version,
                    )

                if self.gguf_version >= 2:
                    tc_bytes = self._read_bytes_or_raise(f, 8, "Tensor count")
                    self.tensor_count = struct.unpack("<Q", tc_bytes)[0]
                    mc_bytes = self._read_bytes_or_raise(f, 8, "Metadata KV count")
                    self.metadata_kv_count = struct.unpack("<Q", mc_bytes)[0]
                else:  # Version 1
                    tc_bytes = self._read_bytes_or_raise(f, 4, "Tensor count v1")
                    self.tensor_count = struct.unpack("<I", tc_bytes)[0]
                    mc_bytes = self._read_bytes_or_raise(f, 4, "Metadata KV count v1")
                    self.metadata_kv_count = struct.unpack("<I", mc_bytes)[0]

                file_summary_info["gguf.tensor_count"] = self.tensor_count
                file_summary_info["gguf.metadata_kv_count"] = self.metadata_kv_count
                info_monitor(
                    "[%s] GGUF v%d, Tensors: %d, Meta KVs: %d",
                    self._logger_name,
                    self.gguf_version,
                    self.tensor_count,
                    self.metadata_kv_count,
                )

                for i in range(int(self.metadata_kv_count)):
                    key = ""
                    try:
                        key = self._read_string(f)
                        value_type_bytes = self._read_bytes_or_raise(f, 4, f"Value type for key '{key}'")
                        value_type_val = struct.unpack("<I", value_type_bytes)[0]
                        value = self._read_metadata_value(f, value_type_val)
                        parsed_metadata_kv[key] = value
                    except GGUFReadError as e_kv:
                        error_key_name = key if key else f"KV pair at index {i}"
                        info_monitor(
                            "[%s] GGUFReadError for '%s': %s. Stopping metadata read.",
                            self._logger_name,
                            error_key_name,
                            e_kv,
                        )
                        parsed_metadata_kv[error_key_name] = f"[Error reading value: {e_kv}]"
                        self._error_message = f"Failed reading GGUF KV pair '{error_key_name}': {e_kv}"
                        self.status = ModelParserStatus.FAILURE  # Mark as failure due to incomplete metadata
                        break  # Stop processing further KVs
                    # struct.error should ideally be caught within _read_bytes_or_raise and turned into GGUFReadError

                self.metadata_header = parsed_metadata_kv
                self.main_header = file_summary_info  # Contains version, tensor_count, kv_count

                # If status is still UNATTEMPTED here, it means the KV loop completed without errors.
                if self.status == ModelParserStatus.UNATTEMPTED:
                    self.status = ModelParserStatus.SUCCESS
                # If self.status became FAILURE inside the loop, it remains FAILURE.

        except FileNotFoundError:  # Let BaseModelParser handle this
            raise
        except self.NotApplicableError:  # Let BaseModelParser handle this
            raise
        except GGUFReadError as e_gguf_critical:  # Errors in header or unrecoverable array type
            self._error_message = f"Critical GGUF parsing error: {e_gguf_critical}"
            self.status = ModelParserStatus.FAILURE
            # Re-raise as ValueError for BaseModelParser's general error handling,
            # or just let it be, as status is already set.
            # For consistency with BaseModelParser, re-raising is good.
            raise ValueError(self._error_message) from e_gguf_critical
        # General exceptions are caught by BaseModelParser.parse()
