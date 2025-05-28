# dataset_tools/parsers/base_dt_parser.py
from abc import ABC, abstractmethod
from enum import Enum
# Use absolute imports for modules within the same top-level package
from dataset_tools.correct_types import UpField, DownField, EmptyField 
from dataset_tools.logger import info_monitor as nfo

class DtParserStatus(Enum): # Renamed from ParserStatus to avoid potential clashes
    UNATTEMPTED = 0 # New status
    SUCCESS = 1
    FAILURE = 2 # General failure for this parser
    NOT_APPLICABLE = 3 # This parser doesn't handle this data type/format

class BaseDtParser(ABC):
    def __init__(self, raw_data_chunk, source_hint: str = "Unknown"):
        self.raw_data_chunk = raw_data_chunk 
        self.source_hint = source_hint
        
        self.positive_prompt: str = ""
        self.negative_prompt: str = ""
        self.parameters: dict = {} 
        self.width: str = ""       
        self.height: str = ""
        self.tool_name: str = "Unknown"
        self.processed_raw_data_display: str = "" # The "raw" data relevant to this parser
        
        self.status: DtParserStatus = DtParserStatus.UNATTEMPTED
        self._error_message: str | None = None
        self._logger_name = f"DT_Parser.{self.__class__.__name__}"


    @abstractmethod
    def _process(self) -> None:
        """
        Internal method to be implemented by subclasses.
        Should attempt to parse self.raw_data_chunk.
        If successful:
            - Populate self.positive_prompt, self.negative_prompt, self.parameters, etc.
            - Set self.tool_name.
            - Set self.processed_raw_data_display.
        If not applicable for this parser, it should raise a specific exception
        or return in a way that parse() can set status to NOT_APPLICABLE.
        If an error occurs during parsing of an applicable format, raise an exception
        or set self._error_message.
        """
        pass

    def parse(self) -> DtParserStatus:
        if self.status == DtParserStatus.SUCCESS or self.status == DtParserStatus.NOT_APPLICABLE:
            # nfo(f"[{self._logger_name}] Skipping re-parse, status: {self.status.name}")
            return self.status
        
        # nfo(f"[{self._logger_name}] Attempting to parse data from {self.source_hint}...")
        try:
            self._process() # Subclass implements its specific logic here
            # If _process completes without raising an error, assume success for now.
            # Subclass's _process should set tool_name, prompts, params etc.
            # If it determines it's not applicable, it should ideally raise a custom NotApplicableError
            self.status = DtParserStatus.SUCCESS
            nfo(f"[{self._logger_name}] Successfully parsed data from {self.source_hint}. Tool: {self.tool_name}")
        except self.NotApplicableError: # Custom exception subclasses can define
            # nfo(f"[{self._logger_name}] Parser not applicable for data from {self.source_hint}.")
            self.status = DtParserStatus.NOT_APPLICABLE
        except Exception as e:
            nfo(f"[{self._logger_name}] Error parsing data from {self.source_hint}: {e}")
            self._error_message = str(e)
            self.status = DtParserStatus.FAILURE
        return self.status

    def get_ui_data(self) -> dict:
        if self.status != DtParserStatus.SUCCESS:
            return {}

        ui_data = {}
        prompt_data = {}
        if self.positive_prompt: prompt_data["Positive"] = self.positive_prompt
        if self.negative_prompt: prompt_data["Negative"] = self.negative_prompt
        if prompt_data: ui_data[UpField.PROMPT.value] = prompt_data

        gen_data = {}
        if self.width: gen_data["Width"] = self.width
        if self.height: gen_data["Height"] = self.height
        for key, value in self.parameters.items():
            display_key = key.replace("_", " ").capitalize()
            gen_data[display_key] = str(value) if value is not None else ""
        if gen_data: ui_data[DownField.GENERATION_DATA.value] = gen_data
        
        if self.tool_name and self.tool_name != "Unknown":
            if UpField.METADATA.value not in ui_data:
                ui_data[UpField.METADATA.value] = {}
            ui_data[UpField.METADATA.value]["Detected Tool"] = self.tool_name
        
        if self.processed_raw_data_display:
            ui_data[DownField.RAW_DATA.value] = self.processed_raw_data_display
        
        return ui_data

    class NotApplicableError(Exception):
        """Custom exception to indicate the parser is not suitable for the given data."""
        pass