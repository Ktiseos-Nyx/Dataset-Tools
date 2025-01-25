"""Load model metadata"""
# // SPDX-License-Identifier: CC0-1.0, blessing
# // d a r k s h a p e s
# // --<{ Ktiseos Nyx }>--

from pathlib import Path
import mmap
import pickle
import struct
import json
from gguf import GGUFReader

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

    def create_gguf_reader(self, file_path_named: str):
        try:  # method using gguf library, better for LDM conversions
            reader = GGUFReader(file_path_named, "r")  # obsolete in numpy 2, also slower
        except ValueError as error_log:
            print(error_log)  # >:V
        else:
            arch = reader.fields.get("general.architecture")  # model type category, prevents the need to block scan for id
            reader_data = {"architecture_name": str(bytes(arch.parts[arch.data[0]]), encoding="utf-8")}
            general_name_raw = reader.fields.get("general.name")
            if general_name_raw:
                try:
                    general_name = (str(bytes(general_name_raw.parts[general_name_raw.data[0]]), encoding="utf-8"),)
                except KeyError as error_log:
                    nfo("Failed to get expected field within model metadata: %s", file_path_named, general_name_raw, error_log)
                else:
                    reader_data.setdefault("general_name", general_name)
            # retrieve model name from the dict data
            tensor_data = {
                "dtype": reader.data.dtype.name,
                "types": arch.types if len(arch.types) > 1 else "",
            }
            # get dtype from metadata here
            for tensor in reader.tensors:
                tensor_info = {"shape": str(tensor.shape), "dtype": str(tensor.tensor_type.name)}
                tensor_data.setdefault(str(tensor.name), tensor_info)  # create dict similar to safetensors/pt results
            file_metadata = {UpField.METADATA: reader_data, DownField.LAYER_DATA: tensor_data}
            return file_metadata

    def create_llama_parser(self, file_path_named: str) -> dict:
        """
        Llama handler for gguf file header\n
        :param file_path_named: `str` the full path to the file being opened
        :return: `dict` The entire header with Llama parser formatting
        """
        parser = Llama(model_path=file_path_named, vocab_only=True, verbose=False)
        if parser:
            llama_data = {}

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
                    llama_data.setdefault("name", value)
                    break

            # Determine the dtype from parser.scores.dtype, if available
            scores_dtype = getattr(parser.scores, "dtype", None)
            if scores_dtype is not None:
                llama_data.setdefault("dtype", scores_dtype.name)  # e.g., 'float32'
            file_metadata = {UpField.METADATA: llama_data, DownField.LAYER_DATA: EmptyField.PLACEHOLDER}

            return file_metadata
        return None

    def attempt_file_open(self, file_path_named: str) -> dict:
        """
        Try two methods of extracting the metadata from the file\n
        :param file_path_named: The full path to the file being opened
        :type file_path_named: str
        :return: A `dict` with the header data prepared to read
        """
        metadata = None
        metadata = self.create_gguf_reader(file_path_named)
        if metadata:
            return metadata
        else:
            try:
                metadata = self.create_llama_parser(file_path_named)
            except ValueError as error_log:
                nfo("Parsing .gguf file failed for %s", file_path_named, error_log)
            else:
                if metadata:
                    return metadata
        return None

    def metadata_from_gguf(self, file_path_named: str) -> dict:
        """
        Collect metadata from a gguf file header\n
        :param file_path_named: `str` the full path to the file being opened
        :return: `dict` the key value pair structure found in the file
        """

        if self.gguf_check(file_path_named):
            file_metadata = self.attempt_file_open(file_path_named)
            if file_metadata is not None:
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
            if subtracted_data.get("__metadata__"):
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
