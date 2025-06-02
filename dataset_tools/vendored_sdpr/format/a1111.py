# dataset_tools/vendored_sdpr/format/a1111.py

__author__ = "receyuki"
__filename__ = "a1111.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import re
import logging # For type hinting, though _logger comes from BaseFormat
from typing import Dict, Any, Tuple, Optional

from .base_format import BaseFormat
from .utility import add_quotes, concat_strings


class A1111(BaseFormat):
    tool = "A1111 webUI"

    # Mappings from A1111 webUI parameter names to canonical keys and CLI argument properties
    # (canonical_key, is_string_for_cli)
    PROMPT_MAPPING: Dict[str, Tuple[str, bool]] = {
        "Seed": ("seed", False),
        "Variation seed strength": ("subseed_strength", False),
        "Sampler": ("sampler_name", True),
        "Steps": ("steps", False),
        "CFG scale": ("cfg_scale", False),
        "Face restoration": ("restore_faces", False), # Assuming this is a boolean or simple string
        # Add other mappings as needed, e.g., for specific hires fix parameters if they appear in the settings string
    }

    def __init__(self, info: Optional[Dict[str, Any]] = None, raw: str = ""):
        super().__init__(info=info, raw=raw)
        # self._logger should be inherited from BaseFormat and correctly typed
        # self._logger: logging.Logger (this is just a comment for clarity)
        self._extra: str = "" # Specific to A1111 for postprocessing data

    def _extract_raw_data_from_info(self) -> str:
        """Extracts raw parameter string from _info, prioritizing 'parameters' then 'postprocessing'."""
        current_raw_data = ""
        if self._info:
            parameters_str = str(self._info.get("parameters", ""))
            if parameters_str:
                # pylint: disable=no-member
                self._logger.debug(f"Using 'parameters' from info dict. Length: {len(parameters_str)}")
                current_raw_data = parameters_str

            postprocessing_str = str(self._info.get("postprocessing", ""))
            if postprocessing_str:
                # pylint: disable=no-member
                self._logger.debug(f"Found 'postprocessing' data. Length: {len(postprocessing_str)}")
                if current_raw_data:
                    current_raw_data = concat_strings(current_raw_data, postprocessing_str, "\n")
                else:
                    current_raw_data = postprocessing_str
            self._extra = postprocessing_str # Store postprocessing separately if needed elsewhere
        return current_raw_data

    def _process(self):
        # pylint: disable=no-member
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")

        raw_data_from_info = self._extract_raw_data_from_info()

        # If self._raw was initially empty, use data from _info.
        # If self._raw had content, append data from _info (if any, and if appropriate).
        # For A1111, typically 'parameters' is the primary source.
        if not self._raw and raw_data_from_info:
            self._raw = raw_data_from_info
        elif self._raw and raw_data_from_info and self._raw != raw_data_from_info : # Avoid duplicating if _raw was already parameters
             # This logic might need refinement based on how _raw and _info are populated upstream.
             # Assuming if _raw exists, it might be the primary source, and _info['postprocessing'] could be appended.
             if self._extra and self._extra not in self._raw: # Append postprocessing if distinct
                 self._raw = concat_strings(self._raw, self._extra, "\n")


        if not self._raw:
            # pylint: disable=no-member
            self._logger.warn(f"{self.tool}: No raw data, 'parameters', or 'postprocessing' in info dict to parse.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "No A1111 parameter string found to parse."
            return

        self._sd_format() # Call the main parsing logic

        if self._positive or self._parameter_has_data(): # Check if any useful data was parsed
            # pylint: disable=no-member
            self._logger.info(f"{self.tool}: Data parsed successfully.")
            self.status = self.Status.READ_SUCCESS
        else:
            # pylint: disable=no-member
            self._logger.warn(f"{self.tool}: _sd_format completed but no positive prompt or settings were extracted.")
            self.status = self.Status.FORMAT_ERROR
            self._error = f"{self.tool}: Failed to extract key fields from the parameter string."

    def _parse_prompt_blocks(self, raw_data: str) -> Tuple[str, str, str]:
        """Parses the raw data into positive, negative, and settings blocks."""
        positive_prompt = ""
        negative_prompt = ""
        settings_block = ""

        # Find the start of the "Steps:" line, which delineates prompts from settings
        steps_index = raw_data.find("\nSteps:")
        prompt_block_raw = raw_data # Assume all is prompt if "Steps:" not found

        if steps_index != -1:
            prompt_block_raw = raw_data[:steps_index].strip()
            settings_block = raw_data[steps_index:].strip()
        else:
            # pylint: disable=no-member
            self._logger.debug(
                "A1111 _sd_format: '\\nSteps:' delineator not found. Assuming all raw data is prompt or malformed."
            )
            # settings_block remains empty

        # Find "Negative prompt:" within the identified prompt block
        negative_prompt_marker = "\nNegative prompt:"
        negative_prompt_index = prompt_block_raw.find(negative_prompt_marker)

        if negative_prompt_index != -1:
            positive_prompt = prompt_block_raw[:negative_prompt_index].strip()
            negative_prompt = prompt_block_raw[negative_prompt_index + len(negative_prompt_marker):].strip()
        else:
            positive_prompt = prompt_block_raw.strip() # All of prompt_block_raw is positive

        return positive_prompt, negative_prompt, settings_block

    def _parse_settings_string(self, settings_str: str) -> Dict[str, str]:
        """Parses the 'Steps: ...' block into a dictionary."""
        if not settings_str:
            return {}

        # Regex to capture "Key: Value" pairs, Value can contain spaces and parentheses
        # It looks for a key (not containing colon or comma), followed by ':', then captures the value
        # until a comma followed by another potential key, or end of string.
        # This regex is a common one for A1111 style parameter strings.
        pattern = r"\s*([^:,]+):\s*([^,]+(?:\([^)]*\))?(?:\s+[^,]+(?<!\sENSD:\s\d+))*)"
        # Corrected pattern to handle cases like "Foo: Bar, Baz: Quux (blah)"
        # Simpler pattern if values don't contain commas that are not part of a key-value pair:
        # pattern = r"([\w\s-]+):\s*([^,]+(?:,\s*[\w\s-]+:\s*[^,]+)*)" # This might be too greedy
        # Sticking to a simpler, more common pattern for A1111:
        pattern = r"([^:]+):\s*((?:[^,]|,(?=\s*\w+:\s*))+)" # Key: Value, Key2: Value2
        # The one from original code seemed more robust for values with parentheses:
        # pattern = r"\s*([^:,]+):\s*([^,]+(?:\([^)]*\))?(?:\s+[^,]+)*)" # Using this one

        matches = re.findall(pattern, settings_str)
        parsed_settings: Dict[str, str] = {}
        for key, value in matches:
            key = key.strip()
            value = value.strip()
            if key not in parsed_settings: # Take the first occurrence
                parsed_settings[key] = value
        # pylint: disable=no-member
        self._logger.debug(f"Parsed settings_dict from settings string: {parsed_settings}")
        return parsed_settings

    def _populate_parameters_from_settings(self, settings_dict: Dict[str, str]):
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
                # pylint: disable=no-member
                self._logger.warn(
                    f"Could not parse Size '{size_str}' into width/height. Keeping existing: {self._width}x{self._height}"
                )

        # Populate parameters based on PROMPT_MAPPING
        for খায়_setting_key, (canonical_param_key, _) in self.PROMPT_MAPPING.items():
            if খায়_setting_key in settings_dict:
                value = str(settings_dict[khay_setting_key])
                if canonical_param_key in self._parameter:
                    self._parameter[canonical_param_key] = value
                else: # Should not happen if PARAMETER_KEY in BaseFormat is comprehensive
                    # pylint: disable=no-member
                    self._logger.warn(
                        f"Canonical key '{canonical_param_key}' (for A1111 key '{khay_setting_key}') not in BaseFormat.PARAMETER_KEY."
                    )

        # Direct mapping for other common parameters
        direct_map_to_canonical = {
            "Model": "model",
            "Model hash": "model_hash",
            # Add other direct mappings if they appear in the A1111 settings string
            # e.g., "Hires upscaler": "hires_upscaler", "Denoising strength": "denoising_strength"
        }
        for setting_key, canonical_key in direct_map_to_canonical.items():
            if setting_key in settings_dict:
                value = str(settings_dict[setting_key])
                if canonical_key in self._parameter:
                    self._parameter[canonical_key] = value
                # else: log warning if canonical_key is unexpectedly missing from _parameter template

        # Update the "size" parameter if width and height were successfully parsed
        if self._width != "0" and self._height != "0" and "size" in self._parameter:
            self._parameter["size"] = f"{self._width}x{self._height}"

    def _sd_format(self):
        """Main parsing function for A1111 format. Populates prompt and parameter attributes."""
        if not self._raw:
            # pylint: disable=no-member
            self._logger.debug("A1111 _sd_format: self._raw is empty, cannot parse further.")
            return

        self._positive, self._negative, settings_str = self._parse_prompt_blocks(self._raw)
        self._setting = settings_str # Store the raw settings string

        if self._setting:
            settings_dict = self._parse_settings_string(self._setting)
            self._populate_parameters_from_settings(settings_dict)
        else:
            # pylint: disable=no-member
            self._logger.debug("A1111 _sd_format: self._setting string is empty after parsing prompt blocks.")

    def prompt_to_line(self) -> str: # Not affected by the local variable count
        """Converts parsed data back into a CLI-like string."""
        if not self._positive and not self._parameter_has_data():
            return ""

        line_parts = []
        if self._positive:
            line_parts.append(f"--prompt {add_quotes(self._positive).replace(chr(10), ' ')}")
        if self._negative:
            line_parts.append(f"--negative_prompt {add_quotes(self._negative).replace(chr(10), ' ')}")

        if self._width != "0" and self._height != "0": # Use parsed width/height directly
            line_parts.append(f"--width {self._width}")
            line_parts.append(f"--height {self._height}")

        # Use PROMPT_MAPPING for other parameters
        for _, (cli_arg_name, is_string) in self.PROMPT_MAPPING.items():
            # cli_arg_name is the canonical_param_key here
            if cli_arg_name in self._parameter:
                value = self._parameter[cli_arg_name]
                # Check if value is not the default placeholder and is not None or empty
                if value and value != self.DEFAULT_PARAMETER_PLACEHOLDER:
                    if is_string:
                        line_parts.append(f"--{cli_arg_name} {add_quotes(str(value))}")
                    else:
                        line_parts.append(f"--{cli_arg_name} {value}")
        
        # Add other specific parameters like model if available
        if self._parameter.get("model") and self._parameter["model"] != self.DEFAULT_PARAMETER_PLACEHOLDER:
            line_parts.append(f"--model {add_quotes(str(self._parameter['model']))}")


        return " ".join(line_parts).strip()
