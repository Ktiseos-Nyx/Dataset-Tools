# dataset_tools/model_parsers/gguf_parser.py
import struct
from enum import Enum
from .base_model_parser import BaseModelParser  # Your base class
from ..logger import info_monitor as nfo  # Your logger
# from ..correct_types import UpField, DownField # Not strictly needed here but good for context


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
        self.tool_name = "GGUF Model File"  # Set by BaseModelParser if self.tool_name is used
        self.gguf_version = None
        self.tensor_count = None
        self.metadata_kv_count = None
        # self.metadata_header will be populated (from BaseModelParser)
        # self.main_header will be populated (from BaseModelParser)

    def _read_string(self, f) -> str:
        length = struct.unpack("<Q", f.read(8))[0]
        return f.read(length).decode("utf-8", errors="replace")

    def _read_metadata_value(self, f, value_type_enum_val: int):
        try:
            value_type = GGUFValueType(value_type_enum_val)
        except ValueError:
            # If value_type_enum_val is unknown, we can't know how many bytes to read.
            # This is a critical format error.
            raise ValueError(f"Unknown GGUF metadata value type integer: {value_type_enum_val}")

        if value_type == GGUFValueType.UINT8:
            return struct.unpack("<B", f.read(1))[0]
        elif value_type == GGUFValueType.INT8:
            return struct.unpack("<b", f.read(1))[0]
        elif value_type == GGUFValueType.UINT16:
            return struct.unpack("<H", f.read(2))[0]
        elif value_type == GGUFValueType.INT16:
            return struct.unpack("<h", f.read(2))[0]
        elif value_type == GGUFValueType.UINT32:
            return struct.unpack("<I", f.read(4))[0]
        elif value_type == GGUFValueType.INT32:
            return struct.unpack("<i", f.read(4))[0]
        elif value_type == GGUFValueType.FLOAT32:
            return struct.unpack("<f", f.read(4))[0]
        elif value_type == GGUFValueType.BOOL:
            return struct.unpack("?", f.read(1))[0]
        elif value_type == GGUFValueType.STRING:
            return self._read_string(f)
        elif value_type == GGUFValueType.UINT64:
            return struct.unpack("<Q", f.read(8))[0]
        elif value_type == GGUFValueType.INT64:
            return struct.unpack("<q", f.read(8))[0]
        elif value_type == GGUFValueType.FLOAT64:
            return struct.unpack("<d", f.read(8))[0]
        elif value_type == GGUFValueType.ARRAY:
            array_item_type_int = struct.unpack("<I", f.read(4))[0]  # GGUF v2/v3: type is u32
            array_len = struct.unpack("<Q", f.read(8))[0]  # GGUF v2/v3: count is u64

            items = []
            try:
                array_item_gtype = GGUFValueType(array_item_type_int)
                # For simplicity, read first few elements or represent as placeholder
                # A full implementation would loop array_len times.
                # This is just a sketch for now.
                if array_len > 0 and array_len < 20:  # Only try to read small arrays for demo
                    for _ in range(array_len):
                        items.append(self._read_metadata_value(f, array_item_type_int))
                    return items
                else:
                    # For very long arrays, or if we don't want to parse them,
                    # we need to skip the correct number of bytes. This is complex
                    # without knowing each element's size.
                    # For now, represent as placeholder.
                    nfo(
                        f"[{self._logger_name}] GGUF metadata array of type {array_item_gtype.name} with len {array_len}. Content not fully parsed for display."
                    )
                    return f"[Array of {array_item_gtype.name}, len {array_len}]"
            except ValueError:  # Unknown array_item_type_int
                return f"[Array of Unknown Type ({array_item_type_int}), len {array_len} - Not parsed]"
        else:
            # This path should not be reached if GGUFValueType(value_type_enum_val) succeeded
            # and all enum members are handled above.
            raise ValueError(f"Unhandled GGUFValueType enum member: {value_type}")

    def _process(self) -> None:  # Implements abstract method from BaseModelParser
        parsed_metadata_kv = {}  # Store key-value metadata here
        file_summary_info = {}  # Store version, counts etc. here

        try:
            with open(self.file_path, "rb") as f:
                magic = f.read(4)
                if magic != b"GGUF":
                    # This error means the file is not applicable for this parser
                    raise self.NotApplicableError("Not a GGUF file (magic number mismatch).")

                self.gguf_version = struct.unpack("<I", f.read(4))[0]
                file_summary_info["gguf.version"] = self.gguf_version
                if self.gguf_version not in [1, 2, 3]:  # Known GGUF versions
                    nfo(
                        f"[{self._logger_name}] Encountered GGUF version {self.gguf_version}. Parser may have limitations."
                    )

                if self.gguf_version >= 2:  # GGUFv2/v3
                    self.tensor_count = struct.unpack("<Q", f.read(8))[0]
                    self.metadata_kv_count = struct.unpack("<Q", f.read(8))[0]
                else:  # GGUFv1
                    self.tensor_count = struct.unpack("<I", f.read(4))[0]
                    self.metadata_kv_count = struct.unpack("<I", f.read(4))[0]

                file_summary_info["gguf.tensor_count"] = self.tensor_count
                file_summary_info["gguf.metadata_kv_count"] = self.metadata_kv_count
                nfo(
                    f"[{self._logger_name}] GGUF v{self.gguf_version}, Tensors: {self.tensor_count}, Meta KVs: {self.metadata_kv_count}"
                )

                for i in range(self.metadata_kv_count):
                    key = self._read_string(f)
                    value_type_val = struct.unpack("<I", f.read(4))[0]
                    try:
                        value = self._read_metadata_value(f, value_type_val)
                        parsed_metadata_kv[key] = value
                    except ValueError as ve_val:  # Error reading a specific value
                        nfo(
                            f"[{self._logger_name}] Error reading GGUF metadata value for key '{key}': {ve_val}. Storing as error string."
                        )
                        parsed_metadata_kv[key] = f"[Error reading value: {ve_val}]"
                    except struct.error as se_val:  # Struct error often means EOF or corruption for this value
                        nfo(
                            f"[{self._logger_name}] Struct error reading GGUF metadata value for key '{key}': {se_val}. File might be truncated."
                        )
                        parsed_metadata_kv[key] = f"[Struct error reading value: {se_val}]"
                        # Depending on severity, you might want to stop parsing further KVs
                        # For now, we try to continue.

                # Successfully parsed what we could
                self.metadata_header = parsed_metadata_kv  # For UpField.METADATA
                self.main_header = file_summary_info  # For DownField.JSON_DATA (or similar)
                # self.status = ModelParserStatus.SUCCESS # Set by BaseModelParser.parse() if no exception
                # self._error_message is not set if successful

        # NotApplicableError will be caught by BaseModelParser.parse() and set status.
        # FileNotFoundError will also be caught by BaseModelParser.parse().
        except struct.error as e_struct:  # If struct error happens outside value reading (e.g., reading counts)
            self._error_message = f"GGUF file structure error (possibly corrupted or truncated): {e_struct}"
            # Let BaseModelParser.parse() catch this and set status to FAILURE
            raise ValueError(self._error_message)
        except ValueError as e_val:  # Catch ValueErrors from _read_metadata_value or other validation
            self._error_message = f"Error parsing GGUF data: {e_val}"
            raise  # Re-raise for BaseModelParser.parse() to set status to FAILURE
        except Exception as e_general:  # Catch-all for other unexpected errors
            self._error_message = f"Unexpected error parsing GGUF file {self.file_path}: {e_general}"
            # nfo(f"[{self._logger_name}] Unexpected GGUF parsing error: {e_general}", exc_info=True) # For dev
            raise ValueError(self._error_message)  # Re-raise for BaseModelParser.parse()
