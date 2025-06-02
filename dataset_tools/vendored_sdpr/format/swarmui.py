# dataset_tools/vendored_sdpr/format/swarmui.py

__author__ = "receyuki"
__filename__ = "swarmui.py"
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


class SwarmUI(BaseFormat):
    tool = "StableSwarmUI"

    PARAMETER_MAP = {
        "prompt": "positive_prompt_text",
        "negativeprompt": "negative_prompt_text",
        "model": "model",
        "seed": "seed",
        "cfgscale": "cfg_scale",
        "steps": "steps",
        "width": "width",
        "height": "height",
    }

    # Added type hints
    def __init__(self, info: dict[str, Any] | None = None, raw: str = ""):
        super().__init__(info=info, raw=raw)
        # self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool.replace(' ', '_')}") # OLD
        self._logger: logging.Logger = get_logger(
            f"DSVendored_SDPR.Format.{self.tool.replace(' ', '_')}",
        )  # NEW
        # self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER # Inherited

        if self._raw and not self._info:
            try:
                # pylint: disable=no-member # Temporary if _logger gives issues before full Pylint run
                self._info = json.loads(self._raw)
            except json.JSONDecodeError:
                self._logger.warn(
                    f"{self.tool}: Raw string provided but is not valid JSON. Info remains empty.",
                )
                self._info = {}

    def _process(self):
        # pylint: disable=no-member # Temporary
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")

        if not self._info or not isinstance(self._info, dict):
            self._logger.warn(
                f"{self.tool}: Info data (parsed JSON) is empty or not a dictionary.",
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "SwarmUI metadata (info dict) is missing or invalid."
            return

        data_json = self._info.get("sui_image_params", self._info)

        if not isinstance(data_json, dict):
            self._logger.warn(
                f"{self.tool}: 'sui_image_params' not found or not a dict. Data: {str(data_json)[:100]}",
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "'sui_image_params' key missing or data not a dictionary."
            return

        try:
            self._positive = str(data_json.get("prompt", "")).strip()
            self._negative = str(data_json.get("negativeprompt", "")).strip()

            for swarm_key, canonical_key in self.PARAMETER_MAP.items():
                if swarm_key in data_json and canonical_key in self._parameter:
                    value = data_json.get(swarm_key)
                    self._parameter[canonical_key] = str(
                        (
                            value
                            if value is not None
                            else self.DEFAULT_PARAMETER_PLACEHOLDER
                        ),
                    )

            comfy_sampler = data_json.get("comfyuisampler")
            auto_sampler = data_json.get("autowebuisampler")
            sampler_to_use = comfy_sampler or auto_sampler
            if "sampler_name" in self._parameter and sampler_to_use:
                self._parameter["sampler_name"] = str(
                    remove_quotes(str(sampler_to_use)),
                )

            if data_json.get("width") is not None:
                self._width = str(data_json.get("width"))
            if data_json.get("height") is not None:
                self._height = str(data_json.get("height"))
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            setting_parts = []
            handled_keys = set(self.PARAMETER_MAP.keys()) | {
                "prompt",
                "negativeprompt",
                "comfyuisampler",
                "autowebuisampler",
                "sui_image_params",  # also exclude sui_image_params if it was top level
            }
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
                self._error = f"{self.tool}: Key fields (prompt, seed) not found."

        except Exception as general_err:  # Renamed 'e', pylint: disable=broad-except
            self._logger.error(
                f"{self.tool}: Unexpected error parsing SwarmUI JSON data: {general_err}",
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Unexpected error: {general_err}"
