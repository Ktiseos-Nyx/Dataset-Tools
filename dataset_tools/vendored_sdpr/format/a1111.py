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

    SETTINGS_TO_PARAM_MAP: dict[str, str | list[str]] = {
        "Seed": "seed",
        "Variation seed strength": "subseed_strength",
        "Sampler": "sampler_name",
        "Steps": "steps",
        "CFG scale": "cfg_scale",
        "Face restoration": "restore_faces",
        "Model": "model",
        "Model hash": "model_hash",
    }

    def __init__(self, info: dict[str, Any] | None = None, raw: str = ""):
        super().__init__(info=info, raw=raw)
        self._extra: str = ""  # Stores postprocessing string if separate

    def _extract_raw_data_from_info(self) -> str:
        current_raw_data = ""
        if self._info:
            parameters_str = str(self._info.get("parameters", ""))
            if parameters_str:
                self._logger.debug(
                    "Using 'parameters' from info dict. Length: %s", len(parameters_str)
                )
                current_raw_data = parameters_str

            self._extra = str(self._info.get("postprocessing", ""))
            if self._extra:
                self._logger.debug(
                    "Found 'postprocessing' data. Length: %s", len(self._extra)
                )
                if not current_raw_data:  # Only use if 'parameters' wasn't found
                    current_raw_data = self._extra
        return current_raw_data

    def _process(self):
        raw_data_from_info = self._extract_raw_data_from_info()

        if not self._raw and raw_data_from_info:
            self._raw = raw_data_from_info
            self._logger.debug("Using raw data from _info dictionary for A1111.")
        elif self._raw and raw_data_from_info and self._raw != raw_data_from_info:
            # If _raw (e.g., from UserComment) is different from _info['parameters'],
            # and _extra (from _info['postprocessing']) exists and isn't already in _raw, append it.
            # This prioritizes _raw if both exist but allows supplementing with _extra.
            if self._extra and self._extra not in self._raw:
                self._logger.debug(
                    "Appending _extra (postprocessing from _info) to existing _raw for A1111."
                )
                self._raw = concat_strings(self._raw, self._extra, "\n")
        elif not self._raw and not raw_data_from_info:
            self._logger.warn(
                "%s: No raw data provided and no 'parameters' or 'postprocessing' in info dict.",
                self.tool,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "No A1111 parameter string found to parse."
            return

        if not self._raw:  # Final check
            self._logger.warn(
                "%s: Effective raw data is empty after processing _info.", self.tool
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "A1111 parameter string is empty after consolidation."
            return

        self._parse_a1111_format()

        if self.status != self.Status.FORMAT_ERROR:
            if (
                self._positive
                or self._parameter_has_data()
                or self._width != "0"
                or self._setting
            ):
                self._logger.info("%s: Data parsed successfully.", self.tool)
            else:
                self._logger.warning(
                    "%s: Parsing completed but no key data (prompt, params, size, settings) extracted.",
                    self.tool,
                )
                self.status = self.Status.FORMAT_ERROR
                self._error = f"{self.tool}: Failed to extract meaningful data."

    def _parse_prompt_blocks(self, raw_data: str) -> tuple[str, str, str]:
        positive_prompt, negative_prompt, settings_block = "", "", ""

        # Regex to find the start of the settings block, which often starts with "Steps:"
        # but can also be other known parameter names.
        # This regex looks for a newline followed by a known parameter name and a colon.
        # The (?i) flag makes it case-insensitive for parameter names.
        # Corrected regex to be more robust and handle variations in settings block start
        settings_marker_pattern = (
            r"\n(?i)(?:Steps:|CFG scale:|Seed:|Size:|Model hash:|Model:|Sampler:|Face restoration:|"
            r"Clip skip:|ENSD:|Hires fix:|Hires steps:|Hires upscale:|Hires upscaler:|Denoising strength:|Version:)"
        )

        # Find "Negative prompt:" first
        neg_prompt_keyword = "\nNegative prompt:"
        parts_at_negative = raw_data.split(neg_prompt_keyword, 1)

        if len(parts_at_negative) > 1:  # "Negative prompt:" was found
            positive_candidate = parts_at_negative[0].strip()
            after_negative_marker = parts_at_negative[1]

            # Search for settings block *after* the negative prompt
            settings_match = re.search(settings_marker_pattern, after_negative_marker)
            if settings_match:
                positive_prompt = positive_candidate
                negative_prompt = after_negative_marker[
                    : settings_match.start()
                ].strip()
                settings_block = after_negative_marker[settings_match.start() :].strip()
            else:  # No settings block after negative prompt
                positive_prompt = positive_candidate
                negative_prompt = after_negative_marker.strip()
        else:  # "Negative prompt:" was NOT found
            positive_candidate = raw_data.strip()
            # Search for settings block in the whole raw_data (which is all positive_candidate here)
            settings_match = re.search(settings_marker_pattern, positive_candidate)
            if settings_match:
                positive_prompt = positive_candidate[: settings_match.start()].strip()
                settings_block = positive_candidate[settings_match.start() :].strip()
            else:  # No settings block found at all
                positive_prompt = positive_candidate

        return positive_prompt, negative_prompt, settings_block

    def _parse_settings_string_to_dict(self, settings_str: str) -> dict[str, str]:
        if not settings_str:
            return {}

        # Pattern to capture "Key: Value" pairs, where Value can extend until the next "Key:",
        # handling commas within values more robustly than simple comma split.
        # This regex looks for "Key: Value" pairs separated by ", " or newline.
        # (?:\s*,\s*|\n) is the delimiter between Key:Value pairs.
        # Value part `((?:(?!(?:\s*,\s*|\n)[\w\s-]+:).)+)` means:
        # match any char (`.`) one or more times (`+`), non-greedily (`?`),
        # as long as it's NOT followed by (delimiter AND another Key: pattern).
        pattern = re.compile(r"([\w\s-]+):\s*((?:(?!(?:\s*,\s*|\n)[\w\s-]+:).)+)")

        parsed_settings: dict[str, str] = {}
        matches = pattern.findall(settings_str)

        for key, value in matches:
            key = key.strip()
            value = value.strip(" ,")  # Strip trailing comma/space from value
            if (
                key and key not in parsed_settings
            ):  # Ensure key is not empty and first one wins
                parsed_settings[key] = value

        self._logger.debug(
            "Parsed settings_dict from settings string: %s", parsed_settings
        )
        return parsed_settings

    def _parse_a1111_format(self):
        if not self._raw:
            self._logger.debug(
                "%s _parse_a1111_format: self._raw is empty, cannot parse.", self.tool
            )
            return

        self._positive, self._negative, settings_block_str = self._parse_prompt_blocks(
            self._raw
        )
        self._setting = (
            settings_block_str  # Store the raw settings block as self._setting
        )

        handled_keys_from_settings_dict = set()  # Keys handled from the settings_dict

        if settings_block_str:
            settings_dict = self._parse_settings_string_to_dict(settings_block_str)

            # Populate standard parameters from settings_dict
            self._populate_parameters_from_map(
                settings_dict,
                self.SETTINGS_TO_PARAM_MAP,  # Use the class map
                handled_keys_from_settings_dict,
            )

            # Handle Size -> width, height
            size_str = settings_dict.get("Size")
            if size_str:
                try:
                    w_str, h_str = size_str.split("x", 1)
                    # Create a temporary dict for _extract_and_set_dimensions
                    temp_dim_data = {
                        "width_from_size": w_str.strip(),
                        "height_from_size": h_str.strip(),
                    }
                    self._extract_and_set_dimensions(
                        temp_dim_data,
                        "width_from_size",
                        "height_from_size",
                        # handled_keys_set is not needed here as we handle "Size" below
                    )
                except ValueError:
                    self._logger.warning(
                        "Could not parse Size '%s' into width/height. Keeping existing: %sx%s",
                        size_str,
                        self._width,
                        self._height,
                    )
                handled_keys_from_settings_dict.add("Size")  # Mark "Size" as handled

            # Note: self._setting is already the raw settings_block_str.
            # If a *cleaned* settings string from unhandled key-value pairs in settings_dict
            # was desired, it would be built here using _build_settings_string
            # with remaining_data_dict=settings_dict and remaining_handled_keys=handled_keys_from_settings_dict.
            # For A1111, usually the raw block is sufficient and expected as self._setting.
        else:
            self._logger.debug("%s: self._setting string (block) is empty.", self.tool)

    def prompt_to_line(self) -> str:
        if not self._positive and not self._parameter_has_data():
            return ""
        line_parts = []
        if self._positive:
            # F-string for CLI construction is fine, ensure no excessively long lines
            prompt_val = add_quotes(self._positive).replace(chr(10), " ")
            line_parts.append(f"--prompt {prompt_val}")
        if self._negative:
            neg_prompt_val = add_quotes(self._negative).replace(chr(10), " ")
            line_parts.append(f"--negative_prompt {neg_prompt_val}")

        if self.width != "0" and self.width != self.DEFAULT_PARAMETER_PLACEHOLDER:
            line_parts.append(f"--width {self.width}")
        if self.height != "0" and self.height != self.DEFAULT_PARAMETER_PLACEHOLDER:
            line_parts.append(f"--height {self.height}")

        # CLI argument mapping (could be a class constant for clarity if reused)
        # This map is specific to how A1111 CLI arguments are named.
        param_to_cli_map = {
            "seed": ("seed", False),
            "subseed_strength": ("subseed_strength", False),
            "sampler_name": ("sampler", True),
            "steps": ("steps", False),
            "cfg_scale": ("cfg_scale", False),
            "restore_faces": ("restore_faces", False),
            "model": ("model", True),
            # Add "model_hash" if it has a CLI arg, etc.
        }
        for param_key, (cli_arg_name, is_string) in param_to_cli_map.items():
            value = self._parameter.get(param_key)
            if value is not None and value != self.DEFAULT_PARAMETER_PLACEHOLDER:
                processed_value = str(value)
                arg_str = f"--{cli_arg_name} "
                arg_str += add_quotes(processed_value) if is_string else processed_value
                line_parts.append(arg_str)
        return " ".join(line_parts).strip()
