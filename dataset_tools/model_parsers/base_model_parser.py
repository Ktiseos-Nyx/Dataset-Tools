# dataset_tools/model_parsers/base_model_parser.py
from abc import ABC, abstractmethod
from enum import Enum

from ..correct_types import DownField, EmptyField, UpField

# Corrected: Import the modified info_monitor directly
from ..logger import info_monitor  # Assuming info_monitor is the new name for nfo


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
            # If _process completes without raising an exception, and hasn't set status to FAILURE/NOT_APPLICABLE itself:
            if self.status == ModelParserStatus.UNATTEMPTED:  # Or if it could be PARTIAL
                self.status = ModelParserStatus.SUCCESS
            # Log success only if status is indeed SUCCESS
            if self.status == ModelParserStatus.SUCCESS:
                info_monitor("[%s] Successfully parsed: %s", self._logger_name, self.file_path)
        except FileNotFoundError:
            info_monitor("[%s] File not found: %s", self._logger_name, self.file_path)
            self._error_message = "File not found."
            self.status = ModelParserStatus.FAILURE
        except self.NotApplicableError as e_na:
            self._error_message = str(e_na) or "File format not applicable for this parser."
            # Optional: Log this at DEBUG or INFO if desired for NotApplicable cases
            # info_monitor("[%s] Not applicable for %s: %s", self._logger_name, self.file_path, self._error_message)
            self.status = ModelParserStatus.NOT_APPLICABLE
        except (
            ValueError,  # Includes GGUFReadError if it inherits from ValueError
            TypeError,
            AttributeError,
            KeyError,
            IndexError,
            OSError,
            MemoryError,
            # Add GGUFReadError here if it's a direct import and doesn't inherit ValueError
            # from ..gguf_parser import GGUFReadError # Example if needed
            # except (..., GGUFReadError)
        ) as e_parser:
            # Catch a range of common errors that might occur during a parser's _process method
            info_monitor(  # This call should now work correctly with exc_info
                "[%s] Error parsing %s: %s",
                self._logger_name,
                self.file_path,
                e_parser,
                exc_info=True,
            )
            self._error_message = str(e_parser)
            self.status = ModelParserStatus.FAILURE
        except Exception as e_unhandled:  # noqa: BLE001 # For truly unexpected issues
            info_monitor(  # This call should now work correctly with exc_info
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
            # Provide more context if available, even for partial success if implemented
            error_info = self._error_message or "Model parsing failed, not applicable, or no data extracted."
            if self.status == ModelParserStatus.NOT_APPLICABLE:
                error_info = self._error_message or "Format not applicable for this model type."

            return {
                EmptyField.PLACEHOLDER.value: {"Error": error_info},
            }

        ui_data = {}
        # Ensure UpField.METADATA.value exists before trying to add "Detected Model Format"
        # and before adding self.metadata_header to it.
        ui_data[UpField.METADATA.value] = {}

        if self.metadata_header:
            # Could merge or update if specific keys are expected, for now, direct assignment
            ui_data[UpField.METADATA.value].update(self.metadata_header)
        if self.main_header:
            # Typically main_header might go into a more specific field like DownField.JSON_DATA
            # or a custom key within UpField.METADATA if it's general model info.
            # Assuming it's general info to be merged into METADATA for now, or placed as JSON_DATA.
            ui_data[DownField.JSON_DATA.value] = self.main_header  # As per original

        # Add Detected Model Format to the metadata section
        ui_data[UpField.METADATA.value]["Detected Model Format"] = self.tool_name

        # If metadata_header was empty, but main_header exists, METADATA might still be just {"Detected Model Format": ...}
        # If both are empty, it's just {"Detected Model Format": ...}
        # This ensures the "Detected Model Format" is always present on success.

        return ui_data

    class NotApplicableError(Exception):
        """Custom exception to indicate a parser is not suitable for a given file."""

        pass
