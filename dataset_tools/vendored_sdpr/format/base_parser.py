# dataset_tools/parsers/base_parser.py
# Keeping the copyright because a TON OF THIS CODE is borrowed from SD Prompt Reader.
__author__ = "receyuki"
__filename__ = "base_format.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

# They're using MIT, we're on GPL


from abc import ABC, abstractmethod
from enum import Enum
from ..correct_types import UpField, DownField, EmptyField # Your project's enums
from ..logger import info_monitor as nfo # Your project's logger

class ParserStatus(Enum):
    UNREAD = 1
    READ_SUCCESS = 2
    FORMAT_ERROR = 3
    # Add more specific error statuses if needed

class BaseDtParser(ABC): # "Dt" for Dataset-Tools
    # Common parameter keys your UI might expect, can be extended by subclasses
    # Or subclasses can just populate self.parameters freely.
    EXPECTED_PARAMETERS = ["Model", "Sampler", "Seed", "Cfg scale", "Steps", "Width", "Height"]

    def __init__(self, raw_data_chunk, source_hint: str = "Unknown"):
        self.raw_data_chunk = raw_data_chunk 
        self.source_hint = source_hint
        
        # Attributes to be populated by subclasses
        self.positive_prompt: str = ""
        self.negative_prompt: str = ""
        self.parameters: dict = {} # For steps, cfg, seed, sampler, model, etc.
        self.width: str = ""       
        self.height: str = ""
        self.tool_name: str = "Unknown"
        # Raw data specific to what this parser successfully processed, for display
        self.processed_raw_data_display: str = "" 
        
        self.status: ParserStatus = ParserStatus.UNREAD
        self._error_message: str | None = None

        # Optional: Each parser could have its own logger instance
        # from ..logger import Logger # If you adopt SDPR's Logger style
        # self._logger = Logger(f"DatasetTools.Parser.{self.__class__.__name__}")

    @abstractmethod
    def _process_data(self) -> None:
        """
        Internal method to be implemented by subclasses.
        It should attempt to parse self.raw_data_chunk and populate
        self.positive_prompt, self.negative_prompt, self.parameters, etc.
        It should set self.tool_name and self.processed_raw_data_display.
        If parsing fails, it should raise an exception or set self._error_message.
        """
        pass

    def parse(self) -> bool:
        """
        Public method to trigger parsing.
        Returns True if parsing was successful, False otherwise.
        """
        if self.status == ParserStatus.READ_SUCCESS: # Avoid re-parsing
            return True
        try:
            self._process_data() # Subclass implements its specific logic here
            self.status = ParserStatus.READ_SUCCESS
            nfo(f"[{self.__class__.__name__}] Successfully parsed data from {self.source_hint}.")
            return True
        except Exception as e:
            # self._logger.error(f"Error during parsing for {self.source_hint} with {self.__class__.__name__}: {e}")
            nfo(f"[{self.__class__.__name__}] Error parsing data from {self.source_hint}: {e}")
            self._error_message = str(e)
            self.status = ParserStatus.FORMAT_ERROR
            return False

    def get_ui_data(self) -> dict:
        """
        Constructs a dictionary in the format expected by final_ui_dict
        if parsing was successful.
        """
        if self.status != ParserStatus.READ_SUCCESS:
            return {}

        ui_data = {}
        prompt_data = {}
        if self.positive_prompt: prompt_data["Positive"] = self.positive_prompt
        if self.negative_prompt: prompt_data["Negative"] = self.negative_prompt
        if prompt_data: ui_data[UpField.PROMPT.value] = prompt_data # Use .value for enums as dict keys

        gen_data = {}
        if self.width: gen_data["Width"] = self.width
        if self.height: gen_data["Height"] = self.height
        # Merge common parameters
        for key, value in self.parameters.items():
            display_key = key.replace("_", " ").capitalize() # Standardize display key
            gen_data[display_key] = str(value) if value is not None else ""
            
        if gen_data: ui_data[DownField.GENERATION_DATA.value] = gen_data
        
        if self.tool_name and self.tool_name != "Unknown":
            # Ensure METADATA key exists before trying to add to it
            if UpField.METADATA.value not in ui_data:
                ui_data[UpField.METADATA.value] = {}
            ui_data[UpField.METADATA.value]["Detected Tool"] = self.tool_name
        
        if self.processed_raw_data_display:
            ui_data[DownField.RAW_DATA.value] = self.processed_raw_data_display
        
        return ui_data
