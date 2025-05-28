# dataset_tools/vendored_sdpr/format/base_format.py

__author__ = "receyuki" # Original author
__filename__ = "base_format.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
from enum import Enum
from ..logger import Logger # Your vendored logger
from ..constants import PARAMETER_PLACEHOLDER # Your defined placeholder string

class BaseFormat:
    # Define a comprehensive list of canonical parameter keys that parsers might try to populate.
    # Specific parsers will map their unique field names to these canonical keys.
    PARAMETER_KEY = [
        "model",            # Name or path of the primary model
        "model_hash",       # Hash of the primary model
        "sampler_name",     # Sampler used (e.g., "Euler a", "DPM++ 2M Karras")
        "seed",
        "subseed",          # For variation seeds
        "subseed_strength",
        "cfg_scale",        # CFG scale value
        "steps",
        "size",             # Combined "WidthxHeight" string
        "width",            # Parsed width (though often handled by self._width directly)
        "height",           # Parsed height (similarly)
        "scheduler",        # Scheduler if specified (e.g., "karras", "sgm_uniform")
        "loras",            # String representation of LoRAs used
        "hires_fix",        # Boolean or details about Hires. fix
        "hires_upscaler",   # Upscaler used for Hires. fix
        "denoising_strength",
        "restore_faces",    # Face restoration method or boolean
        "version",          # Software version
        # Add any other common parameters you want to standardize across formats
    ]

    # Make PARAMETER_PLACEHOLDER available to instances and subclasses
    DEFAULT_PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER

    class Status(Enum): # Inner class for status codes
        UNREAD = 1
        READ_SUCCESS = 2
        FORMAT_ERROR = 3
        COMFYUI_ERROR = 4 # Specific error for ComfyUI if needed

    def __init__(
        self, info: dict = None, raw: str = "", width: int = 0, height: int = 0
    ):
        # Initialize core attributes
        self._width = str(width)    # Store as string for consistent property return
        self._height = str(height)  # Store as string
        self._info = info if info is not None else {} # Raw info dict from PIL or other source
        self._raw = str(raw)        # Full raw metadata string, ensure it's a string

        # Initialize prompt and parameter attributes
        self._positive = ""
        self._negative = ""
        self._positive_sdxl = {} # For SDXL-specific positive prompts
        self._negative_sdxl = {} # For SDXL-specific negative prompts
        self._setting = ""       # Reconstructed or raw settings string from the tool
        
        # Initialize the parameter dictionary with defined keys and a placeholder
        self._parameter = dict.fromkeys(
            BaseFormat.PARAMETER_KEY, 
            BaseFormat.DEFAULT_PARAMETER_PLACEHOLDER # Use the consistent placeholder
        )
        
        self._is_sdxl = False # Flag for SDXL specific content
        self._status = self.Status.UNREAD # Initial parsing status
        self._error = ""     # To store any specific error message during parsing
        
        # Logger: Use a more specific name if possible, or a generic one for the base.
        # Specific parsers (A1111, ComfyUI) will create their own loggers.
        # The name used here will be the parent if not overridden by subclass.
        self._logger = Logger("DSVendored_SDPR.Format.Base") # Consistent naming

        # Some parsers might set their tool name as a class attribute.
        # If not, it can be set in the subclass's __init__ or by ImageDataReader.
        self.tool = getattr(self.__class__, 'tool', "Unknown")


    def parse(self):
        """
        Public method to trigger parsing.
        It calls the internal _process method which should be implemented by subclasses.
        Handles basic status updates and error catching.
        """
        if self._status == self.Status.READ_SUCCESS:
            # Already parsed successfully
            return self._status
        
        # Reset status and error before attempting to parse
        self._status = self.Status.UNREAD
        self._error = ""

        try:
            self._process() # Subclasses will implement their specific parsing logic here
            # If _process completes without raising an exception, and doesn't set an error status:
            if self._status == self.Status.UNREAD: # If subclass _process didn't update status
                 # This implies _process might not have found its format or had an issue
                 # but didn't explicitly set FORMAT_ERROR. We assume success if no error.
                 # More robustly, _process should set self.status itself.
                 self.status = self.Status.READ_SUCCESS # Default to success if no error from _process
            
        except ValueError as ve: # Catch specific errors like JSONDecodeError if _process raises them
            self._logger.error(f"ValueError during {self.tool} parsing: {ve}")
            self._status = self.Status.FORMAT_ERROR
            self._error = str(ve)
        except Exception as e:
            self._logger.error(f"Unexpected exception during {self.tool} _process: {e}", exc_info=True)
            self._status = self.Status.FORMAT_ERROR
            self._error = f"Unexpected error: {e}"
            
        return self._status

    def _process(self):
        """
        Internal processing method to be implemented by specific format parser subclasses.
        This method should parse self._raw or self._info and populate attributes like
        self._positive, self._negative, self._parameter, self._width, self._height (if found in metadata),
        and self._setting. It should also set self._status and self._error if issues occur.
        """
        # Default implementation: do nothing, assume format not recognized by this base.
        # Subclasses *must* override this.
        self._logger.debug(f"BaseFormat._process called for tool {self.tool}. Subclass should implement parsing.")
        # If a subclass calls super()._process() without implementing its own,
        # it effectively means the format wasn't matched by that subclass.
        # Consider setting status to FORMAT_ERROR here if it's not meant to be called directly.
        # However, parse() handles the default status update.
        pass

    # --- Properties to access the parsed data ---
    @property
    def height(self) -> str:
        return self._height

    @property
    def width(self) -> str:
        return self._width

    @property
    def info(self) -> dict:
        return self._info

    @property
    def positive(self) -> str:
        return self._positive

    @property
    def negative(self) -> str:
        return self._negative

    @property
    def positive_sdxl(self) -> dict:
        return self._positive_sdxl

    @property
    def negative_sdxl(self) -> dict:
        return self._negative_sdxl

    @property
    def setting(self) -> str: # The string of parameters, e.g., "Steps: 20, Sampler: Euler a, ..."
        return self._setting

    @property
    def raw(self) -> str: # The full raw metadata string
        return self._raw

    @property
    def parameter(self) -> dict: # Dictionary of parsed parameters
        return self._parameter

    @property
    def is_sdxl(self) -> bool:
        return self._is_sdxl

    @property
    def status(self) -> Status: # Returns the Status Enum member
        return self._status
    
    @status.setter
    def status(self, value: Status): # Allow setting status
        if isinstance(value, self.Status):
            self._status = value
        else:
            self._logger.warn(f"Attempted to set invalid status type: {type(value)}. Expected BaseFormat.Status Enum.")


    @property
    def error(self) -> str: # Read-only access to the error message
        return self._error

    @property
    def props(self) -> str: # For dumping all relevant data as a JSON string (from original SDPR)
        """Returns a JSON string representation of key properties."""
        properties = {
            "positive": self._positive,
            "negative": self._negative,
            "positive_sdxl": self._positive_sdxl,
            "negative_sdxl": self._negative_sdxl,
            "is_sdxl": self._is_sdxl,
            **self._parameter, # Unpack all parameters
            "height": self._height, # Include width/height if not already in _parameter as "size"
            "width": self._width,
            "setting_string": self._setting, # The reconstructed settings string
            "tool_detected": self.tool,
            "raw_metadata_if_any": self._raw[:500] + "..." if len(self._raw) > 500 else self._raw # Truncate long raw data
        }
        try:
            return json.dumps(properties, indent=2) # Pretty print
        except TypeError: # Handle non-serializable data if any creeps in
            # Fallback: convert problematic values to strings
            safe_properties = {k: str(v) if not isinstance(v, (dict, list, str, int, float, bool, type(None))) else v 
                               for k, v in properties.items()}
            return json.dumps(safe_properties, indent=2)