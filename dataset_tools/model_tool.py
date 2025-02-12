# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""Load model metadata"""

from pathlib import Path

# import mmap
# import pickle
import struct
import json

from dataset_tools.logger import info_monitor as nfo
from dataset_tools.correct_types import EmptyField, UpField, DownField


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
        metadata = None
        extension = Path(file_path_named).suffix
        import_map = {
            ".safetensors": self.metadata_from_safetensors,
            ".sft": self.metadata_from_safetensors,
            # ".gguf": self.metadata_from_gguf, # Removed GGUF
            # ".pt": self.metadata_from_pickletensor,
            # ".pth": self.metadata_from_pickletensor,
            # ".ckpt": self.metadata_from_pickletensor,
        }
        if extension in import_map:
            self.read_method = import_map.get(extension)
            metadata = self.read_method(file_path_named)
        else:
            nfo(f"Unsupported file extension: {extension}")
        return metadata

    # def metadata_from_pickletensor(self, file_path_named: str) -> dict:
    #     """
    #     Collect metadata from a pickletensor file header\n
    #     :param file_path: `str` the full path to the file being opened
    #     :return: `dict` the key value pair structure found in the file
    #     """
    #     with open(file_path_named, "r+b") as file_contents_to:
    #         mem_map_data = mmap.mmap(file_contents_to.fileno(), 0)
    #         return pickle.loads(memoryview(mem_map_data))

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
