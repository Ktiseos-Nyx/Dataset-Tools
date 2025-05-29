# dataset_tools/model_parsers/base_model_parser.py
from abc import ABC, abstractmethod
from ..correct_types import UpField, DownField, EmptyField  # Your enums
from ..logger import info_monitor as nfo
from enum import Enum


class ModelParserStatus(Enum):  # Or reuse DtParserStatus if applicable
    UNATTEMPTED = 0
    SUCCESS = 1
    FAILURE = 2
    NOT_APPLICABLE = 3


class BaseModelParser(ABC):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.metadata_header: dict = {}  # For __metadata__ or similar
        self.main_header: dict = {}  # For the main model structure/tensors
        self.tool_name: str = "Unknown Model Type"  # Parser specific
        self.status: ModelParserStatus = ModelParserStatus.UNATTEMPTED
        self._error_message: str | None = None
        self._logger_name = f"DT_ModelParser.{self.__class__.__name__}"

    @abstractmethod
    def _process(self) -> None:
        """Parses self.file_path and populates attributes."""
        pass

    def parse(self) -> ModelParserStatus:
        if self.status == ModelParserStatus.SUCCESS or self.status == ModelParserStatus.NOT_APPLICABLE:
            return self.status
        try:
            self._process()
            self.status = ModelParserStatus.SUCCESS
            nfo(f"[{self._logger_name}] Successfully parsed: {self.file_path}")
        except self.NotApplicableError:
            self.status = ModelParserStatus.NOT_APPLICABLE
        except Exception as e:
            nfo(f"[{self._logger_name}] Error parsing {self.file_path}: {e}")
            self._error_message = str(e)
            self.status = ModelParserStatus.FAILURE
        return self.status

    def get_ui_data(self) -> dict:
        if self.status != ModelParserStatus.SUCCESS:
            return {EmptyField.PLACEHOLDER.value: {"Error": self._error_message or "Model parsing failed."}}

        ui_data = {}
        if self.metadata_header:  # Often from __metadata__
            ui_data[UpField.METADATA.value] = self.metadata_header
        if self.main_header:  # The main tensor structure or other header info
            ui_data[DownField.JSON_DATA.value] = self.main_header  # Or a more specific key like MODEL_STRUCTURE

        # Add tool name if not already in METADATA
        if UpField.METADATA.value not in ui_data:
            ui_data[UpField.METADATA.value] = {}
        ui_data[UpField.METADATA.value]["Detected Model Format"] = self.tool_name

        return ui_data

    class NotApplicableError(Exception):
        pass
