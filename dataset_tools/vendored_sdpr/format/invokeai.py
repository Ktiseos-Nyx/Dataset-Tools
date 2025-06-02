# dataset_tools/vendored_sdpr/format/invokeai.py

__author__ = "receyuki"
__filename__ = "invokeai.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
import logging  # For type hinting
import re
from typing import Any  # For type hints

# from ..logger import Logger # OLD
from ..logger import get_logger  # NEW
from .base_format import BaseFormat
from .utility import remove_quotes


class InvokeAI(BaseFormat):
    tool = "InvokeAI"

    DREAM_MAPPING = {
        "Steps": "s",
        "Seed": "S",
        "CFG scale": "C",
        "Sampler": "A",
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
        parsed_successfully = False
        if self._info and "invokeai_metadata" in self._info:
            self._logger.debug("Found 'invokeai_metadata', attempting that format.")
            parsed_successfully = self._parse_invoke_metadata_format()
        elif self._info and "sd-metadata" in self._info:
            self._logger.debug("Found 'sd-metadata', attempting that format.")
            parsed_successfully = self._parse_sd_metadata_format()
        elif self._info and "Dream" in self._info:
            self._logger.debug("Found 'Dream' string, attempting that format.")
            parsed_successfully = self._parse_dream_format()
        else:
            self._logger.warn(
                f"{self.tool}: No known InvokeAI metadata keys found in info dict.",
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "No InvokeAI metadata keys (invokeai_metadata, sd-metadata, Dream) found."
            return

        if parsed_successfully:
            self.status = self.Status.READ_SUCCESS
            self._logger.info(f"{self.tool}: Data parsed successfully.")
        else:
            self.status = self.Status.FORMAT_ERROR
            if not self._error:
                self._error = f"{self.tool}: Failed to parse identified InvokeAI metadata structure."

    def _parse_invoke_metadata_format(self) -> bool:
        # pylint: disable=no-member,too-many-locals # Temporarily disable for complexity
        try:
            data_json = json.loads(self._info.get("invokeai_metadata", "{}"))
            if not isinstance(data_json, dict):
                self._error = "invokeai_metadata is not a valid JSON dictionary."
                return False

            self._positive = str(data_json.pop("positive_prompt", "")).strip()
            self._negative = str(data_json.pop("negative_prompt", "")).strip()

            if data_json.get("positive_style_prompt"):
                self._positive_sdxl["style"] = str(
                    data_json.pop("positive_style_prompt", ""),
                ).strip()
            if data_json.get("negative_style_prompt"):
                self._negative_sdxl["style"] = str(
                    data_json.pop("negative_style_prompt", ""),
                ).strip()
            if self._positive_sdxl or self._negative_sdxl:
                self._is_sdxl = True

            if "model" in self._parameter and data_json.get("model"):
                model_info = data_json.get("model", {})
                self._parameter["model"] = str(
                    model_info.get("model_name", self.DEFAULT_PARAMETER_PLACEHOLDER),
                )
                if "model_hash" in self._parameter and model_info.get("hash"):
                    self._parameter["model_hash"] = str(model_info.get("hash"))

            param_map = {
                "seed": "seed",
                "steps": "steps",
                "cfg_scale": "cfg_scale",
                "scheduler": "scheduler",
                "width": "width",
                "height": "height",
                "refiner_steps": "refiner_steps",
                "refiner_cfg_scale": "refiner_cfg_scale",
                "refiner_scheduler": "refiner_scheduler",
                "refiner_positive_aesthetic_score": "refiner_positive_aesthetic_score",
                "refiner_negative_aesthetic_score": "refiner_negative_aesthetic_score",
                "refiner_start": "refiner_start",
            }
            for invoke_key, canonical_key in param_map.items():
                if invoke_key in data_json and canonical_key in self._parameter:
                    self._parameter[canonical_key] = str(
                        data_json.get(invoke_key),
                    )  # Use .get for safety
                # Keep unmapped invoke_key in data_json for settings string construction

            if data_json.get("width") is not None:
                self._width = str(data_json.get("width"))
            if data_json.get("height") is not None:
                self._height = str(data_json.get("height"))
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            setting_parts = [
                f"{k.replace('_', ' ').capitalize()}: {remove_quotes(str(v_val))}"
                for k, v_val in data_json.items()  # Renamed v to v_val
            ]
            self._setting = ", ".join(sorted(setting_parts))
            self._raw = self._info.get("invokeai_metadata", "")
            return True
        except json.JSONDecodeError as json_decode_err:  # Renamed 'e'
            self._error = f"Invalid JSON in invokeai_metadata: {json_decode_err}"
            return False
        except Exception as general_err:  # Renamed 'e', pylint: disable=broad-except
            self._error = f"Error parsing invokeai_metadata: {general_err}"
            self._logger.error(
                f"InvokeAI metadata parsing error: {general_err}",
                exc_info=True,
            )
            return False

    def _parse_sd_metadata_format(self) -> bool:
        # pylint: disable=no-member,too-many-locals # Temporary
        try:
            data_json = json.loads(self._info.get("sd-metadata", "{}"))
            if not isinstance(data_json, dict):
                self._error = "sd-metadata is not a valid JSON dictionary."
                return False

            image_data = data_json.get("image", {})
            if not image_data:
                self._error = "'image' field missing in sd-metadata."
                return False

            prompt_field = image_data.get("prompt")
            prompt_text = ""
            if isinstance(prompt_field, list) and prompt_field:
                prompt_text = str(prompt_field[0].get("prompt", ""))
            elif isinstance(prompt_field, str):
                prompt_text = prompt_field
            self._positive, self._negative = self.split_invokeai_prompt(prompt_text)

            param_map = {
                "model": "model",
                "sampler": "sampler_name",
                "seed": "seed",
                "cfg_scale": "cfg_scale",
                "steps": "steps",
                "width": "width",
                "height": "height",
            }
            for sd_meta_key, canonical_key in param_map.items():
                if (
                    sd_meta_key == "model"
                    and "model_weights" in data_json
                    and canonical_key in self._parameter
                ):
                    self._parameter[canonical_key] = str(data_json.get("model_weights"))
                elif sd_meta_key in image_data and canonical_key in self._parameter:
                    self._parameter[canonical_key] = str(image_data.get(sd_meta_key))

            if image_data.get("width") is not None:
                self._width = str(image_data.get("width"))
            if image_data.get("height") is not None:
                self._height = str(image_data.get("height"))
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            setting_parts = []
            handled_image_keys = {"prompt", "width", "height"} | set(param_map.keys())
            for k, v_val in image_data.items():  # Renamed v to v_val
                if k not in handled_image_keys:
                    setting_parts.append(
                        f"{k.replace('_', ' ').capitalize()}: {remove_quotes(str(v_val))}",
                    )
            handled_data_keys = {"image", "model_weights"}
            for k, v_val in data_json.items():  # Renamed v to v_val
                if k not in handled_data_keys:
                    setting_parts.append(
                        f"{k.replace('_', ' ').capitalize()}: {remove_quotes(str(v_val))}",
                    )
            self._setting = ", ".join(sorted(list(set(setting_parts))))
            self._raw = self._info.get("sd-metadata", "")
            return True
        except json.JSONDecodeError as json_decode_err:  # Renamed 'e'
            self._error = f"Invalid JSON in sd-metadata: {json_decode_err}"
            return False
        except Exception as general_err:  # Renamed 'e', pylint: disable=broad-except
            self._error = f"Error parsing sd-metadata: {general_err}"
            self._logger.error(
                f"InvokeAI sd-metadata parsing error: {general_err}",
                exc_info=True,
            )
            return False

    def _parse_dream_format(self) -> bool:
        # pylint: disable=no-member,too-many-locals # Temporary
        try:
            data_str = self._info.get("Dream", "")
            if not data_str:
                self._error = "'Dream' string is empty."
                return False

            pattern = r'"(.*?)"\s*(-\S.*)?$'
            match = re.search(pattern, data_str)
            if not match:
                self._error = "Could not parse 'Dream' string structure."
                return False

            prompt_text = match.group(1).strip('" ')
            settings_str = (match.group(2) or "").strip()
            self._positive, self._negative = self.split_invokeai_prompt(prompt_text)

            param_pattern = r"-(\w+)\s+([\w.-]+)"
            parsed_settings_dict = dict(
                re.findall(param_pattern, settings_str),
            )  # Renamed parsed_settings

            if "s" in parsed_settings_dict and "steps" in self._parameter:
                self._parameter["steps"] = parsed_settings_dict["s"]
            if "S" in parsed_settings_dict and "seed" in self._parameter:
                self._parameter["seed"] = parsed_settings_dict["S"]
            if "C" in parsed_settings_dict and "cfg_scale" in self._parameter:
                self._parameter["cfg_scale"] = parsed_settings_dict["C"]
            if "A" in parsed_settings_dict and "sampler_name" in self._parameter:
                self._parameter["sampler_name"] = parsed_settings_dict["A"]

            if "W" in parsed_settings_dict:
                self._width = parsed_settings_dict["W"]
            if "H" in parsed_settings_dict:
                self._height = parsed_settings_dict["H"]
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            setting_parts = []
            for (
                short_key,
                value_str,
            ) in parsed_settings_dict.items():  # Renamed k,v to short_key, value_str
                display_key = short_key
                for (
                    name,
                    dream_short_key,
                ) in self.DREAM_MAPPING.items():  # Renamed short_key to dream_short_key
                    if dream_short_key == short_key:
                        display_key = name
                        break
                setting_parts.append(f"{display_key.capitalize()}: {value_str}")
            self._setting = ", ".join(sorted(setting_parts))
            self._raw = data_str
            return True
        except Exception as general_err:  # Renamed 'e', pylint: disable=broad-except
            self._error = f"Error parsing Dream string: {general_err}"
            self._logger.error(
                f"InvokeAI Dream parsing error: {general_err}",
                exc_info=True,
            )
            return False

    @staticmethod
    # Return type hint
    def split_invokeai_prompt(prompt: str) -> tuple[str, str]:
        pattern = r"^(.*?)\[(.*?)\]$"
        match = re.fullmatch(pattern, prompt.strip())
        if match:
            positive = match.group(1).strip()
            negative = match.group(2).strip()
        else:
            positive = prompt.strip()
            negative = ""
        return positive, negative
