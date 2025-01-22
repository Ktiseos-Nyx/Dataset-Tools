"""Load model metadata"""
# // SPDX-License-Identifier: CC0-1.0, blessing
# // d a r k s h a p e s
# // --<{ Ktiseos Nyx }>--

from pathlib import Path
import mmap
import pickle
import struct
import json
from collections import defaultdict

from dataset_tools.logger import info_monitor as nfo
from dataset_tools.correct_types import EmptyField, UpField, DownField

try:
    from llama_cpp import Llama
except ImportError as error_log:
    nfo("%s", f"{error_log} llama_cpp not installed.")


class ModelTool:
    """Output state dict from a model file at [path] to the ui"""

    def __init__(self):
        self.read_method = None

    def read_metadata_from(self, file_path_named: str) -> dict:
        """
        Detect file type and skim metadata from a model file using the appropriate tools\n
        :param file_path_named: `str` The full path to the file being analyzed
        :return: `dict` a dictionary including the metadata header and external file attributes\n
        (model_header, disk_size, file_name, file_extension)
        """
        extension = Path(file_path_named).suffix
        import_map = {
            ".safetensors": self.metadata_from_safetensors,
            ".sft": self.metadata_from_safetensors,
            ".gguf": self.metadata_from_gguf,
            ".pt": self.metadata_from_pickletensor,
            ".pth": self.metadata_from_pickletensor,
            ".ckpt": self.metadata_from_pickletensor,
        }
        if extension in import_map:
            self.read_method = import_map.get(extension)
            metadata = self.read_method(file_path_named)
            return metadata
        else:
            nfo(f"Unsupported file extension: {extension}")
            return None

    def metadata_from_pickletensor(self, file_path_named: str) -> dict:
        """
        Collect metadata from a pickletensor file header\n
        :param file_path: `str` the full path to the file being opened
        :return: `dict` the key value pair structure found in the file
        """
        with open(file_path_named, "r+b") as file_contents_to:
            mm = mmap.mmap(file_contents_to.fileno(), 0)
            return pickle.loads(memoryview(mm))

    GGUF_MAGIC_NUMBER = b"GGUF"

    def gguf_check(self, file_path_named: str) -> tuple:
        """
        A magic word check to ensure a file is GGUF format\n
        :param file_path_named: `str` the full path to the file being opened
        :return: `tuple' the number
        """
        try:
            with open(file_path_named, "rb") as file_contents_to:
                magic_number = file_contents_to.read(4)
                version = struct.unpack("<I", file_contents_to.read(4))[0]
        except ValueError as error_log:
            nfo(f"Error reading GGUF header from {file_path_named}: {error_log}")
        else:
            if not magic_number and magic_number != self.GGUF_MAGIC_NUMBER:
                nfo(f"Invalid GGUF magic number in '{file_path_named}'")
                return False
            elif version < 2:
                nfo(f"Unsupported GGUF version {version} in '{file_path_named}'")
                return False
            elif magic_number == self.GGUF_MAGIC_NUMBER and version >= 2:
                return True
            else:
                return False
        return None

    def create_llama_parser(self, file_path_named: str) -> dict:
        """
        Llama handler for gguf file header\n
        :param file_path_named: `str` the full path to the file being opened
        :return: `dict` The entire header with Llama parser formatting
        """
        parser = Llama(model_path=file_path_named, vocab_only=True, verbose=False)
        return parser

    def metadata_from_gguf(self, file_path_named: str) -> dict:
        """
        Collect metadata from a gguf file header\n
        :param file_path_named: `str` the full path to the file being opened
        :return: `dict` the key value pair structure found in the file
        """

        if self.gguf_check(file_path_named):
            parser = self.create_llama_parser(file_path_named)
            if parser:
                file_metadata = defaultdict(dict)

                # Extract the name from metadata using predefined keys
                name_keys = [
                    "general.basename",
                    "general.base_model.0",
                    "general.name",
                    "general.architecture",
                ]
                for key in name_keys:
                    value = parser.metadata.get(key)
                    if value is not None:
                        file_metadata["name"] = value
                        break

                # Determine the dtype from parser.scores.dtype, if available
                scores_dtype = getattr(parser.scores, "dtype", None)
                if scores_dtype is not None:
                    file_metadata["dtype"] = scores_dtype.name  # e.g., 'float32'

                return file_metadata

    def metadata_from_safetensors(self, file_path_named: str) -> dict:
        """
        Collect metadata from a safetensors file header\n
        :param file_path_named: `str` the full path to the file being opened
        :return: `dict` the key value pair structure found in the file
        """
        assembled_data = {}
        with open(file_path_named, "rb") as file_contents_to:
            first_8_bytes = file_contents_to.read(8)
            length_of_header = struct.unpack("<Q", first_8_bytes)[0]
            header_data = file_contents_to.read(length_of_header)
            header_data = header_data.decode("utf-8", errors="strict")
            header_data = header_data.strip()
            header_data = json.loads(f"{header_data}")
            subtracted_data = header_data.copy()
            try:
                subtracted_data.pop("__metadata__")
            except KeyError as error_log:
                nfo("Couldnt remove '__metadata__' from header data. %s", header_data, error_log)
            metadata_field = dict(header_data).get("__metadata__", False)
            # metadata_field = json.loads(str(metadata_field).replace("'", '"'))
            if metadata_field:
                assembled_data.setdefault(UpField.METADATA, metadata_field)
                assembled_data.setdefault(DownField.JSON_DATA, subtracted_data)
            else:
                assembled_data = {UpField.METADATA: EmptyField.EMPTY, DownField.JSON_DATA: subtracted_data}
            return assembled_data
