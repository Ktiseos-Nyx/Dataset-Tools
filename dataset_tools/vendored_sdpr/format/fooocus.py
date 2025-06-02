# dataset_tools/vendored_sdpr/format/fooocus.py

__author__ = "receyuki"
__filename__ = "fooocus.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
import logging  # For type hinting
from typing import Any  # For type hints

# from ..logger import Logger # OLD
from ..logger import get_logger  # NEW
from .base_format import BaseFormat
from .utility import remove_quotes


class Fooocus(BaseFormat):
    tool = "Fooocus"

    PARAMETER_MAP = {
        "prompt": "positive_prompt_text",
        "negative_prompt": "negative_prompt_text",
        "sampler_name": "sampler_name",
        "seed": "seed",
        "guidance_scale": "cfg_scale",
        "steps": "steps",
        "base_model_name": "model",
        "base_model_hash": "model_hash",
        "lora_loras": "loras",
        "width": "width",
        "height": "height",
        "scheduler": "scheduler",
    }

    # Added type hints
    def __init__(self, info: dict[str, Any] | None = None, raw: str = ""):
        super().__init__(info=info, raw=raw)
        # self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool}") # OLD
        self._logger: logging.Logger = get_logger(
            f"DSVendored_SDPR.Format.{self.tool}",
        )  # NEW
        # self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER # Inherited

    def _process(self):
        # pylint: disable=no-member # Temporary
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")

        if not self._info or not isinstance(self._info, dict):
            self._logger.warn(
                f"{self.tool}: Info data (parsed JSON) is empty or not a dictionary.",
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "Fooocus metadata (info dict) is missing or invalid."
            return

        data_json = self._info

        try:
            self._positive = str(data_json.get("prompt", "")).strip()
            self._negative = str(data_json.get("negative_prompt", "")).strip()

            for fc_key, canonical_key in self.PARAMETER_MAP.items():
                if fc_key in data_json and canonical_key in self._parameter:
                    value = data_json.get(fc_key)
                    self._parameter[canonical_key] = str(
                        (
                            value
                            if value is not None
                            else self.DEFAULT_PARAMETER_PLACEHOLDER
                        ),
                    )

            if data_json.get("width") is not None:
                self._width = str(data_json.get("width"))
            if data_json.get("height") is not None:
                self._height = str(data_json.get("height"))
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            setting_parts = []
            handled_keys = {
                "prompt",
                "negative_prompt",
            }  # Keys already explicitly handled for positive/negative
            for key, value in data_json.items():
                if key not in handled_keys:
                    display_key = key.replace("_", " ").capitalize()
                    setting_parts.append(f"{display_key}: {remove_quotes(str(value))}")
            self._setting = ", ".join(sorted(setting_parts))

            if not self._raw and self._info:
                try:
                    self._raw = json.dumps(self._info)
                except TypeError:
                    self._raw = str(self._info)

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
                self._error = (
                    f"{self.tool}: Key fields (prompt, seed) not found in Fooocus JSON."
                )

        except Exception as general_err:  # Renamed 'e', pylint: disable=broad-except
            self._logger.error(
                f"{self.tool}: Unexpected error parsing Fooocus JSON data: {general_err}",
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Unexpected error: {general_err}"
