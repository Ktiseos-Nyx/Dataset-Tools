# dataset_tools/vendored_sdpr/format/invokeai.py

__author__ = "receyuki"
__filename__ = "invokeai.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json

# import logging # Not needed for type hinting if self._logger from BaseFormat
import re

# from ..logger import get_logger # Not needed if self._logger from BaseFormat
from .base_format import BaseFormat

# from .utility import remove_quotes # Handled by _build_settings_string

# Parameter map for 'invokeai_metadata' format
INVOKE_METADATA_PARAM_MAP: dict[str, str | list[str]] = {
    "seed": "seed",
    "steps": "steps",
    "cfg_scale": "cfg_scale",
    "scheduler": "scheduler",
    "refiner_steps": "refiner_steps",
    "refiner_cfg_scale": "refiner_cfg_scale",
    "refiner_scheduler": "refiner_scheduler",
    "refiner_positive_aesthetic_score": "refiner_positive_aesthetic_score",
    "refiner_negative_aesthetic_score": "refiner_negative_aesthetic_score",
    "refiner_start": "refiner_start",
}

# Parameter map for 'sd-metadata' format (from image_data sub-dict)
SD_METADATA_IMAGE_PARAM_MAP: dict[str, str | list[str]] = {
    "sampler": "sampler_name",
    "seed": "seed",
    "cfg_scale": "cfg_scale",
    "steps": "steps",
}

# Parameter map for 'Dream' format (short keys to canonical)
DREAM_FORMAT_PARAM_MAP: dict[str, str | list[str]] = {
    "s": "steps",
    "S": "seed",
    "C": "cfg_scale",
    "A": "sampler_name",
}


class InvokeAI(BaseFormat):
    tool = "InvokeAI"

    # This mapping is for the 'Dream' format's settings string generation
    DREAM_MAPPING = {
        # Display Key : Short Key from Dream string options
        "Steps": "s",
        "Seed": "S",
        "CFG scale": "C",
        "Sampler": "A",
        # Add "Width": "W", "Height": "H" if they were part of original settings display
    }

    # __init__ is inherited from BaseFormat.

    def _process(self) -> None:
        self._logger.debug("Attempting to parse using %s logic.", self.tool)
        parsed_successfully = False

        if not self._info:
            self._logger.warning("%s: _info dictionary is empty. Cannot parse.", self.tool)
            self.status = self.Status.FORMAT_ERROR
            self._error = "InvokeAI metadata (_info dict) is missing."
            return

        if "invokeai_metadata" in self._info:
            self._logger.debug("Found 'invokeai_metadata', attempting that format for %s.", self.tool)
            parsed_successfully = self._parse_invoke_metadata_format()
        elif "sd-metadata" in self._info:
            self._logger.debug("Found 'sd-metadata', attempting that format for %s.", self.tool)
            parsed_successfully = self._parse_sd_metadata_format()
        elif "Dream" in self._info:
            self._logger.debug("Found 'Dream' string, attempting that format for %s.", self.tool)
            parsed_successfully = self._parse_dream_format()
        else:
            self._logger.warning("%s: No known InvokeAI metadata keys found in info dict.", self.tool)
            self.status = self.Status.FORMAT_ERROR
            self._error = "No InvokeAI metadata keys (invokeai_metadata, sd-metadata, Dream) found."
            return

        if parsed_successfully:
            self._logger.info("%s: Data parsed successfully.", self.tool)
            # self.status = self.Status.READ_SUCCESS # Let BaseFormat.parse() handle
        else:
            if self.status != self.Status.FORMAT_ERROR:
                self.status = self.Status.FORMAT_ERROR
            if not self._error:
                self._error = f"{self.tool}: Failed to parse identified InvokeAI metadata structure."

    def _parse_invoke_metadata_format(self) -> bool:
        raw_json_str = self._info.get("invokeai_metadata", "{}")
        try:
            data_json = json.loads(raw_json_str)
            if not isinstance(data_json, dict):
                self._error = "'invokeai_metadata' is not a valid JSON dictionary."
                self._logger.warning("%s: %s", self.tool, self._error)
                return False

            self._positive = str(data_json.pop("positive_prompt", "")).strip()
            self._negative = str(data_json.pop("negative_prompt", "")).strip()

            if data_json.get("positive_style_prompt"):
                self._positive_sdxl["style"] = str(data_json.pop("positive_style_prompt", "")).strip()
            if data_json.get("negative_style_prompt"):
                self._negative_sdxl["style"] = str(data_json.pop("negative_style_prompt", "")).strip()
            if self._positive_sdxl or self._negative_sdxl:
                self._is_sdxl = True

            handled_keys = {
                "positive_prompt",
                "negative_prompt",
                "positive_style_prompt",
                "negative_style_prompt",
            }

            model_info = data_json.get("model")
            if isinstance(model_info, dict):
                self._populate_parameter("model", model_info.get("model_name"), "model.model_name")
                self._populate_parameter("model_hash", model_info.get("hash"), "model.hash")
                handled_keys.add("model")

            self._populate_parameters_from_map(data_json, INVOKE_METADATA_PARAM_MAP, handled_keys)
            self._extract_and_set_dimensions(data_json, "width", "height", handled_keys)

            self._setting = self._build_settings_string(
                remaining_data_dict=data_json,
                remaining_handled_keys=handled_keys,
                include_standard_params=False,
            )
            self._raw = raw_json_str
            return True
        except json.JSONDecodeError as json_decode_err:
            self._error = f"Invalid JSON in invokeai_metadata: {json_decode_err}"
            self._logger.warning("%s: %s", self.tool, self._error, exc_info=True)
            return False
        except Exception as general_err:  # pylint: disable=broad-except
            self._error = f"Error parsing invokeai_metadata: {general_err}"
            self._logger.error("InvokeAI metadata parsing error: %s", general_err, exc_info=True)
            return False

    def _parse_sd_metadata_format(self) -> bool:
        raw_json_str = self._info.get("sd-metadata", "{}")
        try:
            data_json = json.loads(raw_json_str)
            if not isinstance(data_json, dict):
                self._error = "'sd-metadata' is not a valid JSON dictionary."
                self._logger.warning("%s: %s", self.tool, self._error)
                return False

            image_data = data_json.get("image")
            if not isinstance(image_data, dict):
                self._error = "'image' field missing or not a dict in sd-metadata."
                self._logger.warning("%s: %s", self.tool, self._error)
                return False

            prompt_field = image_data.get("prompt")
            prompt_text = ""
            if isinstance(prompt_field, list) and prompt_field:
                prompt_entry = prompt_field[0]
                if isinstance(prompt_entry, dict):
                    prompt_text = str(prompt_entry.get("prompt", ""))
            elif isinstance(prompt_field, str):
                prompt_text = prompt_field
            self._positive, self._negative = self.split_invokeai_prompt(prompt_text)

            handled_keys_image_data = {"prompt"}
            handled_keys_top_level = {"image", "model_weights"}

            if "model_weights" in data_json:
                self._populate_parameter("model", data_json.get("model_weights"), "model_weights")

            self._populate_parameters_from_map(image_data, SD_METADATA_IMAGE_PARAM_MAP, handled_keys_image_data)
            self._extract_and_set_dimensions(image_data, "width", "height", handled_keys_image_data)

            custom_settings_parts = []
            for k, v_val in image_data.items():
                if k not in handled_keys_image_data:
                    custom_settings_parts.append(
                        f"{self._format_key_for_display(k)}: {self._remove_quotes_from_string(v_val)}"
                    )
            for k, v_val in data_json.items():
                if k not in handled_keys_top_level:
                    custom_settings_parts.append(
                        f"{self._format_key_for_display(k)}: {self._remove_quotes_from_string(v_val)}"
                    )

            if custom_settings_parts:
                self._setting = ", ".join(sorted(list(set(custom_settings_parts))))

            self._raw = raw_json_str
            return True
        except json.JSONDecodeError as json_decode_err:
            self._error = f"Invalid JSON in sd-metadata: {json_decode_err}"
            self._logger.warning("%s: %s", self.tool, self._error, exc_info=True)
            return False
        except Exception as general_err:  # pylint: disable=broad-except
            self._error = f"Error parsing sd-metadata: {general_err}"
            self._logger.error("InvokeAI sd-metadata parsing error: %s", general_err, exc_info=True)
            return False

    def _parse_dream_format(self) -> bool:
        dream_data_str = self._info.get("Dream", "")
        if not dream_data_str:
            self._error = "'Dream' string is empty."
            self._logger.warning("%s: %s", self.tool, self._error)
            return False

        try:
            main_pattern = r'"(.*?)"\s*(-\S.*)?$'
            match = re.search(main_pattern, dream_data_str)

            if not match:
                self._error = "Could not parse 'Dream' string structure."
                self._logger.warning("%s: %s. String: %s", self.tool, self._error, dream_data_str[:100])
                return False

            full_prompt_text = match.group(1).strip('" ')
            options_str = (match.group(2) or "").strip()

            self._positive, self._negative = self.split_invokeai_prompt(full_prompt_text)

            option_pattern = r"-(\w+)\s+([\w.-]+)"
            parsed_options_dict = dict(re.findall(option_pattern, options_str))

            handled_option_keys = set()
            self._populate_parameters_from_map(parsed_options_dict, DREAM_FORMAT_PARAM_MAP, handled_option_keys)

            dim_source_dict = {}
            if "W" in parsed_options_dict:
                dim_source_dict["width"] = parsed_options_dict["W"]
            if "H" in parsed_options_dict:
                dim_source_dict["height"] = parsed_options_dict["H"]
            if dim_source_dict:
                self._extract_and_set_dimensions(dim_source_dict, "width", "height")
            if "W" in parsed_options_dict:
                handled_option_keys.add("W")
            if "H" in parsed_options_dict:
                handled_option_keys.add("H")

            # Use self.DREAM_MAPPING (which is DisplayKey: ShortKey)
            # We need to map ShortKey (from parsed_options_dict) to DisplayKey
            short_to_display_dream_map = {v_short: k_display for k_display, v_short in self.DREAM_MAPPING.items()}

            def dream_key_formatter(short_key_from_options: str) -> str:
                return short_to_display_dream_map.get(short_key_from_options, short_key_from_options.capitalize())

            self._setting = self._build_settings_string(
                remaining_data_dict=parsed_options_dict,
                remaining_handled_keys=handled_option_keys,
                remaining_key_formatter=dream_key_formatter,
                include_standard_params=False,
            )
            self._raw = dream_data_str
            return True
        except Exception as general_err:  # pylint: disable=broad-except
            self._error = f"Error parsing Dream string: {general_err}"
            self._logger.error("InvokeAI Dream parsing error: %s", general_err, exc_info=True)
            return False

    @staticmethod
    def split_invokeai_prompt(prompt: str) -> tuple[str, str]:
        pattern = r"^(.*?)(?:\s*\[(.*?)\])?$"
        match = re.fullmatch(pattern, prompt.strip())
        if match:
            positive = match.group(1).strip()
            negative = (match.group(2) or "").strip()
        else:
            positive = prompt.strip()
            negative = ""
        return positive, negative
