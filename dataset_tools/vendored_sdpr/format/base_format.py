# dataset_tools/vendored_sdpr/format/base_format.py

__author__ = "receyuki"  # Original author
__filename__ = "base_format.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
import logging # Standard Python logging
from enum import Enum
from typing import Dict, Any, Type # For type hinting

# Import the factory function from the modified logger.py
from ..logger import get_logger
from ..constants import PARAMETER_PLACEHOLDER


class BaseFormat:
    PARAMETER_KEY = [
        "model",
        "model_hash",
        "sampler_name",
        "seed",
        "subseed",
        "subseed_strength",
        "cfg_scale",
        "steps",
        "size",
        "width",
        "height",
        "scheduler",
        "loras",
        "hires_fix",
        "hires_upscaler",
        "denoising_strength",
        "restore_faces",
        "version",
    ]

    DEFAULT_PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER

    class Status(Enum):
        UNREAD = 1
        READ_SUCCESS = 2
        FORMAT_ERROR = 3
        COMFYUI_ERROR = 4

    def __init__(self: Type[Any], info: Optional[Dict[str, Any]] = None, raw: str = "", width: int = 0, height: int = 0): # Added Optional for info
        self._width = str(width)
        self._height = str(height)
        self._info: Dict[str, Any] = info if info is not None else {} # Type hint for _info
        self._raw = str(raw)

        self._positive = ""
        self._negative = ""
        self._positive_sdxl: Dict[str, Any] = {} # Type hint
        self._negative_sdxl: Dict[str, Any] = {} # Type hint
        self._setting = ""

        self._parameter: Dict[str, Any] = dict.fromkeys(
            BaseFormat.PARAMETER_KEY,
            BaseFormat.DEFAULT_PARAMETER_PLACEHOLDER,
        ) # Type hint

        self._is_sdxl = False
        self._status = self.Status.UNREAD
        self._error = ""

        # Use the get_logger factory function.
        # The logger name includes the actual class name for more specific logging.
        logger_name = f"DSVendored_SDPR.{self.__class__.__module__}.{self.__class__.__name__}"
        if self.__class__ == BaseFormat: # If it's an instance of BaseFormat itself
            logger_name = "DSVendored_SDPR.Format.Base"

        # Type hint self._logger for clarity and Pylint
        self._logger: logging.Logger = get_logger(logger_name)
        # Initial level can be set here, or rely on main app's configuration.
        # Example: self._logger = get_logger(logger_name, level="DEBUG")

        self.tool = getattr(self.__class__, "tool", "Unknown")

    def parse(self) -> Status: # Return type hint
        if self._status == self.Status.READ_SUCCESS:
            return self._status

        self._status = self.Status.UNREAD
        self._error = ""

        try:
            self._process()
            if self._status == self.Status.UNREAD:
                # If _process didn't set a status but also didn't error,
                # it implies it might not have found data for its format.
                # Let specific parsers decide success/failure more explicitly.
                # For now, if no positive/setting, it's likely a format mismatch.
                if not self._positive and not self._setting and not self._parameter_has_data():
                    self._logger.debug(f"{self.tool}._process completed but no data extracted. Assuming format mismatch.")
                    self.status = self.Status.FORMAT_ERROR
                    self._error = f"{self.tool}: No usable data extracted."
                else:
                    # If some data was extracted, assume success unless an error was set
                    self.status = self.Status.READ_SUCCESS
        except ValueError as ve:
            self._logger.error(f"ValueError during {self.tool} parsing: {ve}")
            self._status = self.Status.FORMAT_ERROR
            self._error = str(ve)
        except Exception as e:
            self._logger.error(f"Unexpected exception during {self.tool} _process: {e}", exc_info=True)
            self._status = self.Status.FORMAT_ERROR
            self._error = f"Unexpected error: {e}"
        return self._status

    def _parameter_has_data(self) -> bool:
        """Checks if any parameter has been populated beyond the placeholder."""
        for value in self._parameter.values():
            if value != self.DEFAULT_PARAMETER_PLACEHOLDER:
                return True
        return False

    def _process(self):
        self._logger.debug(f"BaseFormat._process called for tool {self.tool}. Subclass should implement parsing.")
        # Subclasses are expected to override this. If they don't and this is called,
        # it means the format likely wasn't recognized or handled.
        # The `parse` method will set FORMAT_ERROR if no data is extracted.
        pass

    @property
    def height(self) -> str:
        return self._height

    @property
    def width(self) -> str:
        return self._width

    @property
    def info(self) -> Dict[str, Any]: # Type hint
        return self._info

    @property
    def positive(self) -> str:
        return self._positive

    @property
    def negative(self) -> str:
        return self._negative

    @property
    def positive_sdxl(self) -> Dict[str, Any]: # Type hint
        return self._positive_sdxl

    @property
    def negative_sdxl(self) -> Dict[str, Any]: # Type hint
        return self._negative_sdxl

    @property
    def setting(self) -> str:
        return self._setting

    @property
    def raw(self) -> str:
        return self._raw

    @property
    def parameter(self) -> Dict[str, Any]: # Type hint
        return self._parameter

    @property
    def is_sdxl(self) -> bool:
        return self._is_sdxl

    @property
    def status(self) -> Status:
        return self._status

    @status.setter
    def status(self, value: Status):
        if isinstance(value, self.Status):
            self._status = value
        else:
            self._logger.warning(f"Attempted to set invalid status type: {type(value)}. Expected BaseFormat.Status Enum.")

    @property
    def error(self) -> str:
        return self._error

    @property
    def props(self) -> str:
        properties = {
            "positive": self._positive,
            "negative": self._negative,
            "positive_sdxl": self._positive_sdxl,
            "negative_sdxl": self._negative_sdxl,
            "is_sdxl": self._is_sdxl,
            **self._parameter,
            "height": self._height,
            "width": self._width,
            "setting_string": self._setting,
            "tool_detected": self.tool,
            "raw_metadata_if_any": self._raw[:500] + "..."
            if len(self._raw) > 500
            else self._raw,
        }
        try:
            return json.dumps(properties, indent=2)
        except TypeError:
            safe_properties = {
                k: str(v) if not isinstance(v, (dict, list, str, int, float, bool, type(None))) else v
                for k, v in properties.items()
            }
            return json.dumps(safe_properties, indent=2)
