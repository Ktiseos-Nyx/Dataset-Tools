# dataset_tools/vendored_sdpr/format/a1111.py (Corrected Unpacking)

__author__ = "receyuki"
__filename__ = "a1111.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import re

from .base_format import BaseFormat
from .utility import add_quotes, concat_strings # Ensure utility.py is in the same 'format' dir

class A1111(BaseFormat):
    tool = "A1111 webUI"

    PROMPT_MAPPING = {
        "Seed": ("seed", False),
        "Variation seed strength": ("subseed_strength", False),
        "Sampler": ("sampler_name", True),
        "Steps": ("steps", False),
        "CFG scale": ("cfg_scale", False),
        "Face restoration": ("restore_faces", False),
    }

    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info=info, raw=raw)
        self._extra = ""

    def _process(self):
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")
        current_raw_data = self._raw
        if not current_raw_data and self._info and "parameters" in self._info:
            current_raw_data = str(self._info.get("parameters", ""))
            self._logger.debug(f"Using 'parameters' from info dict. Length: {len(current_raw_data)}")
        
        if self._info and "postprocessing" in self._info:
            self._extra = str(self._info.get("postprocessing", ""))
            if self._extra:
                self._logger.debug(f"Found 'postprocessing' data. Length: {len(self._extra)}")
                if current_raw_data:
                    current_raw_data = concat_strings(current_raw_data, self._extra, "\n")
                else:
                    current_raw_data = self._extra
        
        self._raw = current_raw_data

        if not self._raw:
            self._logger.warn(f"{self.tool}: No raw data, 'parameters', or 'postprocessing' in info dict to parse.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "No A1111 parameter string found to parse."
            return

        self._sd_format()

        if self._positive or self._setting:
            self._logger.info(f"{self.tool}: Data parsed successfully.")
            self.status = self.Status.READ_SUCCESS
        else:
            self._logger.warn(f"{self.tool}: _sd_format completed but no positive prompt or settings were extracted.")
            self.status = self.Status.FORMAT_ERROR
            self._error = f"{self.tool}: Failed to extract key fields from the parameter string."

    def _sd_format(self):
        if not self._raw:
            self._logger.debug("A1111 _sd_format: self._raw is empty, cannot parse further.")
            return

        self._positive = ""
        self._negative = ""
        self._setting = ""

        steps_index = self._raw.find("\nSteps:")
        raw_prompt_block = self._raw

        if steps_index != -1:
            raw_prompt_block = self._raw[:steps_index].strip()
            self._setting = self._raw[steps_index:].strip()
        else:
            self._logger.debug("A1111 _sd_format: '\\nSteps:' delineator not found. Assuming raw data is positive prompt or malformed.")
            raw_prompt_block = self._raw.strip()
            self._setting = ""

        negative_prompt_marker = "\nNegative prompt:"
        negative_prompt_index = raw_prompt_block.find(negative_prompt_marker)

        if negative_prompt_index != -1:
            self._positive = raw_prompt_block[:negative_prompt_index].strip()
            self._negative = raw_prompt_block[negative_prompt_index + len(negative_prompt_marker):].strip()
        else:
            self._positive = raw_prompt_block
            self._negative = ""

        if self._setting:
            pattern = r"\s*([^:,]+):\s*([^,]+(?:\([^)]*\))?(?:\s+[^,]+)*)"
            matches = re.findall(pattern, self._setting)
            setting_dict = {}
            # --- THIS IS THE CORRECTED LINE ---
            for key, value in matches: 
            # --- END CORRECTION ---
                key = key.strip()
                value = value.strip()
                if key not in setting_dict:
                    setting_dict[key] = value
            
            self._logger.debug(f"Parsed setting_dict from settings string: {setting_dict}")

            size_str = setting_dict.get("Size")
            if size_str:
                try:
                    w_str, h_str = size_str.split("x")
                    self._width = str(int(w_str.strip()))
                    self._height = str(int(h_str.strip()))
                except ValueError:
                    self._logger.warn(f"Could not parse Size '{size_str}' into width/height. Keeping existing: {self._width}x{self._height}")
            
            for a1111_setting_key, (canonical_param_key, _) in self.PROMPT_MAPPING.items():
                if a1111_setting_key in setting_dict:
                    if canonical_param_key in self._parameter:
                        self._parameter[canonical_param_key] = str(setting_dict[a1111_setting_key])
                    else:
                        self._logger.warn(f"Canonical key '{canonical_param_key}' (for '{a1111_setting_key}') not in BaseFormat.PARAMETER_KEY.")
            
            direct_map_to_canonical = {
                "Model": "model", "Model hash": "model_hash",
            }
            for setting_key, canonical_key in direct_map_to_canonical.items():
                if setting_key in setting_dict and canonical_key in self._parameter:
                    self._parameter[canonical_key] = str(setting_dict[setting_key])
            
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"
        else:
            self._logger.debug("A1111 _sd_format: self._setting string is empty.")

    def prompt_to_line(self):
        if not self._positive and not self._setting :
            return ""
            
        line_parts = []
        if self._positive:
            line_parts.append(f"--prompt {add_quotes(self._positive).replace(chr(10), ' ')}")
        if self._negative:
            line_parts.append(f"--negative_prompt {add_quotes(self._negative).replace(chr(10), ' ')}")

        if self._width != "0" and self._height != "0":
            line_parts.append(f"--width {self._width}")
            line_parts.append(f"--height {self._height}")

        for a1111_key, (cli_arg_name, is_string) in self.PROMPT_MAPPING.items():
            canonical_key = cli_arg_name 
            if canonical_key in self._parameter:
                value = self._parameter[canonical_key]
                if value and value != self.DEFAULT_PARAMETER_PLACEHOLDER:
                    if is_string:
                        line_parts.append(f"--{cli_arg_name} {add_quotes(str(value))}")
                    else:
                        line_parts.append(f"--{cli_arg_name} {value}")
        
        return " ".join(line_parts).strip()