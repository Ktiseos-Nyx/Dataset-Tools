# dataset_tools/vendored_sdpr/format/drawthings.py

__author__ = "receyuki"
__filename__ = "drawthings.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json  # Added, as it's used in _process if raw needs to be set
import logging  # For type hinting
from typing import Any  # For type hints

# from ..logger import Logger  # OLD
from ..logger import get_logger  # NEW
from .base_format import BaseFormat


class DrawThings(BaseFormat):
    tool = "Draw Things"

    PARAMETER_MAP = {
        "model": "model",
        "sampler": "sampler_name",
        "seed": "seed",
        "scale": "cfg_scale",
        "steps": "steps",
    }

    # Added Optional, Dict, Any
    def __init__(self, info: dict[str, Any] | None = None, raw: str = ""):
        super().__init__(info=info, raw=raw)
        # self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool.replace(' ', '_')}") # OLD
        self._logger: logging.Logger = get_logger(
            f"DSVendored_SDPR.Format.{self.tool.replace(' ', '_')}",
        )  # NEW
        # self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER # Inherited

    def _process(self):
        # pylint: disable=no-member # Temporarily add if Pylint still complains
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")

        if not self._info or not isinstance(self._info, dict):
            self._logger.warn(f"{self.tool}: Info data is empty or not a dictionary.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "Draw Things metadata (info dict) is missing or invalid."
            return

        data_json = self._info

        try:
            self._positive = str(data_json.pop("c", "")).strip()
            self._negative = str(data_json.pop("uc", "")).strip()

            for dt_key, canonical_key in self.PARAMETER_MAP.items():
                if dt_key in data_json and canonical_key in self._parameter:
                    self._parameter[canonical_key] = str(
                        data_json.get(dt_key, self.DEFAULT_PARAMETER_PLACEHOLDER),
                    )

            size_str = data_json.get("size", "0x0")
            try:
                w_str, h_str = size_str.split("x")
                self._width = str(int(w_str.strip()))
                self._height = str(int(h_str.strip()))
                if "size" in self._parameter:
                    self._parameter["size"] = f"{self._width}x{self._height}"
            except ValueError:
                self._logger.warn(
                    f"Could not parse DrawThings Size '{size_str}'. Using defaults: {self._width}x{self._height}",
                )
                if "size" in self._parameter:
                    self._parameter["size"] = f"{self._width}x{self._height}"

            setting_dict_for_display = {}
            # Iterate over a copy of keys if popping from data_json inside loop
            # or ensure all pops happen before this iteration.
            # Here, pop("c") and pop("uc") happened before.
            # Keys in PARAMETER_MAP were accessed by .get(), not popped.
            # "size" was also .get().
            for key, value in data_json.items():
                # Check against original keys in data_json that are not part of specific handling.
                if key not in ["c", "uc", "size"] + list(self.PARAMETER_MAP.keys()):
                    setting_dict_for_display[key.capitalize()] = str(value)
            self._setting = ", ".join(
                [f"{k}: {v}" for k, v in sorted(setting_dict_for_display.items())],
            )

            # If _raw was not set by ImageDataReader (e.g., if info was directly given from a PNG chunk)
            if not self._raw and self._info:
                # Store the original full JSON as raw
                self._raw = json.dumps(self._info)

            if (
                self._positive
                or self._parameter.get("seed", self.DEFAULT_PARAMETER_PLACEHOLDER)
                != self.DEFAULT_PARAMETER_PLACEHOLDER
            ):
                self._logger.info(f"{self.tool}: Data parsed successfully.")
                self.status = self.Status.READ_SUCCESS
            else:
                self._logger.warn(
                    f"{self.tool}: Parsing completed but no positive prompt or seed extracted.",
                )
                self.status = self.Status.FORMAT_ERROR
                self._error = f"{self.tool}: Key fields (prompt, seed) not found."

        except KeyError as key_err:  # Renamed 'ke'
            self._logger.error(
                f"{self.tool}: Missing essential key in JSON data: {key_err}",
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Draw Things JSON missing key: {key_err}"
        except Exception as general_err:  # Renamed 'e', pylint: disable=broad-except
            self._logger.error(
                f"{self.tool}: Unexpected error parsing Draw Things JSON: {general_err}",
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Unexpected error: {general_err}"
