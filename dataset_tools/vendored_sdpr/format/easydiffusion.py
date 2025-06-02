# dataset_tools/vendored_sdpr/format/easydiffusion.py

__author__ = "receyuki"
__filename__ = "easydiffusion.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
import logging  # For type hinting
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any  # For type hints used in __init__

# from ..logger import Logger # OLD
from ..logger import get_logger  # NEW
from .base_format import BaseFormat
from .utility import remove_quotes


class EasyDiffusion(BaseFormat):
    tool = "Easy Diffusion"

    ED_TO_CANONICAL_MAP = {
        "prompt": "positive_prompt_text",
        "negative_prompt": "negative_prompt_text",
        "seed": "seed",
        "use_stable_diffusion_model": "model",
        "clip_skip": "clip_skip",
        "use_vae_model": "vae_model",
        "sampler_name": "sampler_name",
        "width": "width",
        "height": "height",
        "num_inference_steps": "steps",
        "guidance_scale": "cfg_scale",
    }

    # Added Optional, Dict, Any
    def __init__(self, info: dict[str, Any] | None = None, raw: str = ""):
        super().__init__(info=info, raw=raw)
        # self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool.replace(' ', '_')}") # OLD
        self._logger: logging.Logger = get_logger(
            f"DSVendored_SDPR.Format.{self.tool.replace(' ', '_')}",
        )  # NEW
        # self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER # This is inherited from BaseFormat
        # No need to assign it to self here, access via self.DEFAULT_PARAMETER_PLACEHOLDER or BaseFormat.DEFAULT_PARAMETER_PLACEHOLDER

    def _process(self):
        # pylint: disable=no-member # Temporarily add if Pylint still complains after get_logger fix
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")

        json_to_parse = self._raw
        if not json_to_parse and self._info:
            if isinstance(self._info, dict) or isinstance(self._info, str):
                json_to_parse = self._info
            else:
                self._logger.warn(
                    f"{self.tool}: Info data is not a dict or string. Cannot parse.",
                )
                self.status = self.Status.FORMAT_ERROR
                self._error = "Easy Diffusion metadata (info) is not a usable dict or JSON string."
                return

        if not json_to_parse:
            self._logger.warn(
                f"{self.tool}: Raw data (or info) is empty. Cannot parse.",
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "Easy Diffusion metadata string is empty."
            return

        data_json: dict
        if isinstance(json_to_parse, str):
            try:
                data_json = json.loads(json_to_parse)
            except json.JSONDecodeError as json_decode_err:  # Renamed 'e'
                self._logger.error(
                    f"{self.tool}: Failed to decode JSON: {json_decode_err}",
                )
                self.status = self.Status.FORMAT_ERROR
                self._error = f"Invalid JSON for Easy Diffusion: {json_decode_err}"
                return
        elif isinstance(json_to_parse, dict):
            data_json = json_to_parse
        else:
            self._logger.error(f"{self.tool}: Input data is not a JSON string or dict.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "Invalid input data type for Easy Diffusion parser."
            return

        self._positive = str(
            data_json.get("prompt", data_json.get("Prompt", "")),
        ).strip()
        self._negative = str(
            data_json.get("negative_prompt", data_json.get("Negative Prompt", "")),
        ).strip()

        for ed_key, canonical_key in self.ED_TO_CANONICAL_MAP.items():
            if ed_key in data_json and canonical_key in self._parameter:
                value = data_json[ed_key]
                if canonical_key in ["model", "vae_model"]:
                    if value and isinstance(value, str):
                        if PureWindowsPath(value).drive:
                            value = PureWindowsPath(value).name
                        else:
                            value = PurePosixPath(value).name
                self._parameter[canonical_key] = str(value)
            elif ed_key in data_json and canonical_key not in [
                "positive_prompt_text",
                "negative_prompt_text",
                "width",
                "height",
            ]:
                self._logger.debug(
                    f"{self.tool}: Key '{ed_key}' (mapped to '{canonical_key}') not in BaseFormat.PARAMETER_KEY. Storing in settings string.",
                )

        if data_json.get("width") is not None:
            self._width = str(data_json.get("width"))
        if data_json.get("height") is not None:
            self._height = str(data_json.get("height"))
        if "size" in self._parameter and self._width != "0" and self._height != "0":
            self._parameter["size"] = f"{self._width}x{self._height}"

        setting_parts = []
        for key, value in data_json.items():
            if key not in ["prompt", "Prompt", "negative_prompt", "Negative Prompt"]:
                display_key = key.replace("_", " ").capitalize()
                setting_parts.append(f"{display_key}: {remove_quotes(str(value))}")
        self._setting = ", ".join(sorted(setting_parts))

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
