# dataset_tools/model_parsers/base_model_parser.py
from abc import ABC, abstractmethod
from enum import Enum

from ..correct_types import DownField, EmptyField, UpField
from ..logger import info_monitor as nfo


class ModelParserStatus(Enum):
    UNATTEMPTED = 0
    SUCCESS = 1
    FAILURE = 2
    NOT_APPLICABLE = 3


class BaseModelParser(ABC):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.metadata_header: dict = {}
        self.main_header: dict = {}
        self.tool_name: str = "Unknown Model Type"
        self.status: ModelParserStatus = ModelParserStatus.UNATTEMPTED
        self._error_message: str | None = None
        self._logger_name = f"DT_ModelParser.{self.__class__.__name__}"

    @abstractmethod
    def _process(self) -> None:
        pass

    def parse(self) -> ModelParserStatus:
        if self.status in (ModelParserStatus.SUCCESS, ModelParserStatus.NOT_APPLICABLE):
            return self.status
        try:
            self._process()
            self.status = ModelParserStatus.SUCCESS
            nfo("[%s] Successfully parsed: %s", self._logger_name, self.file_path)
        except FileNotFoundError:
            nfo("[%s] File not found: %s", self._logger_name, self.file_path)
            self._error_message = "File not found."
            self.status = ModelParserStatus.FAILURE
        except self.NotApplicableError as e_na:
            self._error_message = (
                str(e_na) or "File format not applicable for this parser."
            )
            # nfo(f"[{self._logger_name}] Not applicable for {self.file_path}: {self._error_message}") # Optional log
            self.status = ModelParserStatus.NOT_APPLICABLE
        except (
            ValueError,
            TypeError,
            AttributeError,
            KeyError,
            IndexError,
            OSError,
            MemoryError,
        ) as e_parser:
            # Catch a range of common errors that might occur during a parser's _process method
            nfo(
                "[%s] Error parsing %s: %s",
                self._logger_name,
                self.file_path,
                e_parser,
                exc_info=True,
            )
            self._error_message = str(e_parser)
            self.status = ModelParserStatus.FAILURE
        except Exception as e_unhandled:  # noqa: BLE001 # For truly unexpected issues
            nfo(
                "[%s] UNHANDLED error parsing %s: %s",
                self._logger_name,
                self.file_path,
                e_unhandled,
                exc_info=True,
            )
            self._error_message = f"An unexpected error occurred: {e_unhandled!s}"
            self.status = ModelParserStatus.FAILURE
        return self.status

    def get_ui_data(self) -> dict:
        if self.status != ModelParserStatus.SUCCESS:
            return {
                EmptyField.PLACEHOLDER.value: {
                    "Error": self._error_message
                    or "Model parsing failed or not applicable.",
                },
            }
        ui_data = {}
        if self.metadata_header:
            ui_data[UpField.METADATA.value] = self.metadata_header
        if self.main_header:
            ui_data[DownField.JSON_DATA.value] = self.main_header
        if UpField.METADATA.value not in ui_data:
            ui_data[UpField.METADATA.value] = {}
        ui_data[UpField.METADATA.value]["Detected Model Format"] = self.tool_name
        return ui_data

    class NotApplicableError(Exception):
        pass
