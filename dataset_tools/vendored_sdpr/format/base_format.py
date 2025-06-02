# dataset_tools/vendored_sdpr/format/base_format.py

__author__ = "receyuki"  # Original author
__filename__ = "base_format.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
import logging  # Standard Python logging
from enum import Enum
from typing import Any  # CORRECTED: Added List, Optional

from ..constants import PARAMETER_PLACEHOLDER

# Import the factory function from the modified logger.py
from ..logger import get_logger


# pylint: disable=too-many-instance-attributes
class BaseFormat:
    PARAMETER_KEY: list[str] = [  # Type hinted
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

    # __init__ signature using Optional, Dict, Any, Type will now be valid
    # Removed Type[Any] for self as it's not standard and not needed for this fix.
    def __init__(
        self,
        info: dict[str, Any] | None = None,
        raw: str = "",
        width: int = 0,
        height: int = 0,
    ):
        self._width = str(width)
        self._height = str(height)
        self._info: dict[str, Any] = info if info is not None else {}
        self._raw = str(raw)

        self._positive = ""
        self._negative = ""
        self._positive_sdxl: dict[str, Any] = {}
        self._negative_sdxl: dict[str, Any] = {}
        self._setting = ""

        self._parameter: dict[str, Any] = dict.fromkeys(
            BaseFormat.PARAMETER_KEY,
            BaseFormat.DEFAULT_PARAMETER_PLACEHOLDER,
        )

        self._is_sdxl = False
        self._status = self.Status.UNREAD
        self._error = ""

        # Use the get_logger factory function.
        logger_name = (
            f"DSVendored_SDPR.{self.__class__.__module__}.{self.__class__.__name__}"
        )
        if self.__class__ == BaseFormat:  # If it's an instance of BaseFormat itself
            logger_name = "DSVendored_SDPR.Format.Base"

        self._logger: logging.Logger = get_logger(logger_name)
        self.tool = getattr(self.__class__, "tool", "Unknown")

    def parse(self) -> Status:
        if self._status == self.Status.READ_SUCCESS:
            return self._status

        self._status = self.Status.UNREAD
        self._error = ""

        try:
            self._process()
            if self._status == self.Status.UNREAD:
                if (
                    not self._positive
                    and not self._setting
                    and not self._parameter_has_data()
                ):
                    # self._logger.debug (no-member should be fixed by get_logger and type hint for self._logger)
                    self._logger.debug(
                        f"{self.tool}._process completed but no data extracted. Assuming format mismatch.",
                    )
                    self.status = self.Status.FORMAT_ERROR
                    self._error = f"{self.tool}: No usable data extracted."
                else:
                    self.status = self.Status.READ_SUCCESS
        except ValueError as val_err:  # Renamed 've' to 'val_err' for clarity
            # self._logger.error (no-member should be fixed)
            self._logger.error(f"ValueError during {self.tool} parsing: {val_err}")
            self._status = self.Status.FORMAT_ERROR
            self._error = str(val_err)
        except (
            Exception
        ) as general_err:  # Renamed 'e' to 'general_err', added broad-except disable
            # pylint: disable=broad-except
            # self._logger.error (no-member should be fixed)
            self._logger.error(
                f"Unexpected exception during {self.tool} _process: {general_err}",
                exc_info=True,
            )
            self._status = self.Status.FORMAT_ERROR
            self._error = f"Unexpected error: {general_err}"
        return self._status

    def _parameter_has_data(self) -> bool:
        """Checks if any parameter has been populated beyond the placeholder."""
        for value in self._parameter.values():
            if value != self.DEFAULT_PARAMETER_PLACEHOLDER:
                return True
        return False

    def _process(
        self,
    ):  # Pylint: Unnecessary pass statement (Note #6412) - pass is fine for abstract-like method
        # self._logger.debug (no-member should be fixed)
        self._logger.debug(
            f"BaseFormat._process called for tool {self.tool}. Subclass should implement parsing.",
        )
        pass  # This is acceptable for a method designed to be overridden

    @property
    def height(self) -> str:
        return self._height

    @property
    def width(self) -> str:
        return self._width

    @property
    def info(self) -> dict[str, Any]:
        return self._info

    @property
    def positive(self) -> str:
        return self._positive

    @property
    def negative(self) -> str:
        return self._negative

    @property
    def positive_sdxl(self) -> dict[str, Any]:
        return self._positive_sdxl

    @property
    def negative_sdxl(self) -> dict[str, Any]:
        return self._negative_sdxl

    @property
    def setting(self) -> str:
        return self._setting

    @property
    def raw(self) -> str:
        return self._raw

    @property
    def parameter(self) -> dict[str, Any]:
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
            # self._logger.warning (Pylint error #7325: no-member) -> should be fixed now
            self._logger.warning(
                f"Attempted to set invalid status type: {type(value)}. Expected BaseFormat.Status Enum.",
            )

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
            # Corrected hanging indentation for ternary operator
            "raw_metadata_if_any": (
                self._raw[:500] + "..." if len(self._raw) > 500 else self._raw
            ),
        }
        try:
            return json.dumps(properties, indent=2)
        except TypeError:
            safe_properties = {
                k: (
                    str(v)
                    if not isinstance(
                        v,
                        (dict, list, str, int, float, bool, type(None)),
                    )
                    else v
                )
                for k, v in properties.items()
            }
            return json.dumps(safe_properties, indent=2)
