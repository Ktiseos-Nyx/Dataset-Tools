# dataset_tools/vendored_sdpr/format/a1111.py

__author__ = "receyuki"
__filename__ = "a1111.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import re
from typing import Any

from .base_format import BaseFormat
from .utility import add_quotes, concat_strings


class A1111(BaseFormat):
    tool = "A1111 webUI"

    PROMPT_MAPPING: dict[str, tuple[str, bool]] = {
        "Seed": ("seed", False),
        "Variation seed strength": ("subseed_strength", False),
        "Sampler": ("sampler_name", True),
        "Steps": ("steps", False),
        "CFG scale": ("cfg_scale", False),
        "Face restoration": ("restore_faces", False),
    }

    def __init__(
        self,
        info: dict[str, Any] | None = None,
        raw: str = "",
    ):  # Added Optional, Dict, Any for type hints
        super().__init__(info=info, raw=raw)
        # self._logger is inherited from BaseFormat
        self._extra: str = ""

    def _extract_raw_data_from_info(self) -> str:
        """Extracts raw parameter string from _info, prioritizing 'parameters' then 'postprocessing'."""
        current_raw_data = ""
        if self._info:
            parameters_str = str(self._info.get("parameters", ""))
            if parameters_str:
                self._logger.debug(
                    f"Using 'parameters' from info dict. Length: {len(parameters_str)}",
                )  # pylint: disable=no-member
                current_raw_data = parameters_str

            postprocessing_str = str(self._info.get("postprocessing", ""))
            if postprocessing_str:
                self._logger.debug(
                    f"Found 'postprocessing' data. Length: {len(postprocessing_str)}",
                )  # pylint: disable=no-member
                if current_raw_data:
                    current_raw_data = concat_strings(
                        current_raw_data,
                        postprocessing_str,
                        "\n",
                    )
                else:
                    current_raw_data = postprocessing_str
            self._extra = postprocessing_str
        return current_raw_data

    def _process(self):
        self._logger.debug(
            f"Attempting to parse using {self.tool} logic.",
        )  # pylint: disable=no-member

        raw_data_from_info = self._extract_raw_data_from_info()

        if not self._raw and raw_data_from_info:
            self._raw = raw_data_from_info
        elif self._raw and raw_data_from_info and self._raw != raw_data_from_info:
            if self._extra and self._extra not in self._raw:
                self._raw = concat_strings(self._raw, self._extra, "\n")

        if not self._raw:
            self._logger.warn(
                f"{self.tool}: No raw data, 'parameters', or 'postprocessing' in info dict to parse.",
            )  # pylint: disable=no-member
            self.status = self.Status.FORMAT_ERROR
            self._error = "No A1111 parameter string found to parse."
            return

        self._sd_format()

        if self._positive or self._parameter_has_data():
            self._logger.info(
                f"{self.tool}: Data parsed successfully.",
            )  # pylint: disable=no-member
            self.status = self.Status.READ_SUCCESS
        else:
            self._logger.warn(
                f"{self.tool}: _sd_format completed but no positive prompt or settings were extracted.",
            )  # pylint: disable=no-member
            self.status = self.Status.FORMAT_ERROR
            self._error = (
                f"{self.tool}: Failed to extract key fields from the parameter string."
            )

    def _parse_prompt_blocks(self, raw_data: str) -> tuple[str, str, str]:
        """Parses the raw data into positive, negative, and settings blocks."""
        positive_prompt = ""
        negative_prompt = ""
        settings_block = ""

        steps_index = raw_data.find("\nSteps:")
        prompt_block_raw = raw_data

        if steps_index != -1:
            prompt_block_raw = raw_data[:steps_index].strip()
            settings_block = raw_data[steps_index:].strip()
        else:
            self._logger.debug(  # pylint: disable=no-member
                "A1111 _sd_format: '\\nSteps:' delineator not found. Assuming all raw data is positive prompt or malformed.",
            )

        negative_prompt_marker = "\nNegative prompt:"
        negative_prompt_index = prompt_block_raw.find(negative_prompt_marker)

        if negative_prompt_index != -1:
            positive_prompt = prompt_block_raw[:negative_prompt_index].strip()
            negative_prompt = prompt_block_raw[
                negative_prompt_index + len(negative_prompt_marker) :
            ].strip()
        else:
            positive_prompt = prompt_block_raw.strip()

        return positive_prompt, negative_prompt, settings_block

    def _parse_settings_string(self, settings_str: str) -> dict[str, str]:
        """Parses the 'Steps: ...' block into a dictionary."""
        if not settings_str:
            return {}

        pattern = r"([^:]+):\s*((?:[^,]|,(?=\s*\w+:\s*))+)"
        # Alternative, potentially more robust for values with parentheses:
        # pattern = r"\s*([^:,]+):\s*([^,]+(?:\([^)]*\))?(?:\s+[^,]+(?<!\sENSD:\s\d+))*)"

        matches = re.findall(pattern, settings_str)
        parsed_settings: dict[str, str] = {}
        for key, value in matches:
            key = key.strip()
            value = value.strip()
            if key not in parsed_settings:
                parsed_settings[key] = value
        self._logger.debug(
            f"Parsed settings_dict from settings string: {parsed_settings}",
        )  # pylint: disable=no-member
        return parsed_settings

    def _populate_parameters_from_settings(self, settings_dict: dict[str, str]):
        """Populates self._width, self._height, and self._parameter from parsed settings."""
        if not settings_dict:
            return

        size_str = settings_dict.get("Size")
        if size_str:
            try:
                w_str, h_str = size_str.split("x")
                self._width = str(int(w_str.strip()))
                self._height = str(int(h_str.strip()))
            except ValueError:
                self._logger.warn(  # pylint: disable=no-member
                    f"Could not parse Size '{size_str}' into width/height. Keeping existing: {self._width}x{self._height}",
                )

        # Populate parameters based on PROMPT_MAPPING
        # Using a clear ASCII variable name like 'a1111_map_key'
        for a1111_map_key, (canonical_param_key, _) in self.PROMPT_MAPPING.items():
            if a1111_map_key in settings_dict:
                # Use the same ASCII variable name
                value = str(settings_dict[a1111_map_key])
                if canonical_param_key in self._parameter:
                    self._parameter[canonical_param_key] = value
                else:
                    self._logger.warn(  # pylint: disable=no-member
                        f"Canonical key '{canonical_param_key}' (for A1111 key '{a1111_map_key}') not in BaseFormat.PARAMETER_KEY.",
                    )

        direct_map_to_canonical = {
            "Model": "model",
            "Model hash": "model_hash",
        }
        for setting_key, canonical_key in direct_map_to_canonical.items():
            if setting_key in settings_dict:
                value = str(settings_dict[setting_key])
                if canonical_key in self._parameter:
                    self._parameter[canonical_key] = value

        if self._width != "0" and self._height != "0" and "size" in self._parameter:
            self._parameter["size"] = f"{self._width}x{self._height}"

    # pylint: disable=too-many-locals # This method might still be complex for pylint's default
    def _sd_format(self):
        """Main parsing function for A1111 format. Populates prompt and parameter attributes."""
        if not self._raw:
            self._logger.debug(
                "A1111 _sd_format: self._raw is empty, cannot parse further.",
            )  # pylint: disable=no-member
            return

        self._positive, self._negative, settings_str = self._parse_prompt_blocks(
            self._raw,
        )
        self._setting = settings_str

        if self._setting:
            settings_dict = self._parse_settings_string(self._setting)
            self._populate_parameters_from_settings(settings_dict)
        else:
            self._logger.debug(
                "A1111 _sd_format: self._setting string is empty after parsing prompt blocks.",
            )  # pylint: disable=no-member

    def prompt_to_line(self) -> str:
        """Converts parsed data back into a CLI-like string."""
        # Use self.DEFAULT_PARAMETER_PLACEHOLDER inherited from BaseFormat
        if (
            not self._positive and not self._parameter_has_data()
        ):  # _parameter_has_data is from BaseFormat
            return ""

        line_parts = []
        if self._positive:
            line_parts.append(
                f"--prompt {add_quotes(self._positive).replace(chr(10), ' ')}",
            )
        if self._negative:
            line_parts.append(
                f"--negative_prompt {add_quotes(self._negative).replace(chr(10), ' ')}",
            )

        if self._width != "0" and self._height != "0":
            line_parts.append(f"--width {self._width}")
            line_parts.append(f"--height {self._height}")

        for _, (cli_arg_name, is_string) in self.PROMPT_MAPPING.items():
            if cli_arg_name in self._parameter:
                value = self._parameter[cli_arg_name]
                if value and value != self.DEFAULT_PARAMETER_PLACEHOLDER:
                    if is_string:
                        line_parts.append(f"--{cli_arg_name} {add_quotes(str(value))}")
                    else:
                        line_parts.append(f"--{cli_arg_name} {value}")

        model_val = self._parameter.get("model")  # Use .get for safety
        if model_val and model_val != self.DEFAULT_PARAMETER_PLACEHOLDER:
            line_parts.append(f"--model {add_quotes(str(model_val))}")

        return " ".join(line_parts).strip()
