# dataset_tools/vendored_sdpr/format/ruinedfooocus.py
import json
from .base_format import BaseFormat  # Your BaseFormat class
from ..constants import PARAMETER_PLACEHOLDER  # Import your placeholder
from ..logger import Logger  # Your vendored logger


class RuinedFooocusFormat(BaseFormat):
    tool = "RuinedFooocus"  # Tool name for this parser

    def __init__(self, info: dict = None, raw: str = "", width: int = 0, height: int = 0):
        # Call parent __init__ which initializes _width, _height, _raw, _info, _parameter etc.
        super().__init__(info, raw, width, height)
        # Logger specific to this format parser, using your DSVendored_SDPR hierarchy
        self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool}")
        # self.tool is already set as a class attribute, but can be confirmed here if needed
        # self.tool = "RuinedFooocus"
        self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER  # Make placeholder accessible

    def parse(self):  # Overriding BaseFormat.parse() to contain all logic
        if self._status == BaseFormat.Status.READ_SUCCESS:
            # Already successfully parsed, no need to do it again
            return self._status

        self._logger.info(f"Attempting to parse metadata as {self.tool}.")

        if not self._raw:
            self._logger.warn(f"Raw data is empty for {self.tool} parser.")
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = "Raw data for RuinedFooocus is empty."
            return self._status

        try:
            data = json.loads(self._raw)  # self._raw is expected to be the JSON string

            # Validate if it's actually RuinedFooocus data
            if not isinstance(data, dict) or data.get("software") != "RuinedFooocus":
                self._logger.debug("JSON data is not in RuinedFooocus format (missing 'software' tag or not a dict).")
                self._status = BaseFormat.Status.FORMAT_ERROR
                self._error = "JSON is not RuinedFooocus format (software tag mismatch or not a dict)."
                return self._status

            # --- Extract Standard Prompts ---
            self._positive = str(data.get("Prompt", ""))
            self._negative = str(data.get("Negative", ""))

            # --- Populate Standardized Parameters from BaseFormat.PARAMETER_KEY ---
            # BaseFormat.__init__ should have initialized self._parameter with keys from PARAMETER_KEY
            # Example: self._parameter = {"model": "", "sampler_name": "", "seed": "", ...}

            # Mapping RuinedFooocus JSON keys to your canonical BaseFormat.PARAMETER_KEY names
            # If PARAMETER_KEY has "model":
            if "model" in self._parameter and data.get("base_model_name") is not None:
                self._parameter["model"] = str(data.get("base_model_name"))

            # If PARAMETER_KEY has "sampler_name" (or "sampler"):
            if (
                "sampler_name" in self._parameter and data.get("sampler_name") is not None
            ):  # Assuming key "sampler_name"
                self._parameter["sampler_name"] = str(data.get("sampler_name"))
            elif (
                "sampler" in self._parameter and data.get("sampler_name") is not None
            ):  # Fallback if canonical is "sampler"
                self._parameter["sampler"] = str(data.get("sampler_name"))

            if "seed" in self._parameter and data.get("seed") is not None:
                self._parameter["seed"] = str(data.get("seed"))

            # RuinedFooocus uses "cfg", BaseFormat might use "cfg_scale" or "cfg"
            if "cfg_scale" in self._parameter and data.get("cfg") is not None:
                self._parameter["cfg_scale"] = str(data.get("cfg"))
            elif "cfg" in self._parameter and data.get("cfg") is not None:
                self._parameter["cfg"] = str(data.get("cfg"))

            if "steps" in self._parameter and data.get("steps") is not None:
                self._parameter["steps"] = str(data.get("steps"))

            # --- Width and Height ---
            # Update from JSON if available, otherwise keep from __init__ (PIL)
            # BaseFormat stores them as self._width, self._height (as strings)
            if data.get("width") is not None:
                self._width = str(data.get("width"))
            if data.get("height") is not None:
                self._height = str(data.get("height"))

            # Add "size" to parameters if it's a canonical key and width/height are known
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            # --- Additional/Custom Parameters Specific to RuinedFooocus ---
            # These can be added to self._parameter if you want them displayed with other gen data.
            # Or, they can be part of the self._setting string.
            custom_params_for_setting_string = {}

            if data.get("scheduler") is not None:
                # Option 1: Add to self._parameter if "scheduler" is a canonical key or you want it there
                if "scheduler" in self._parameter:  # Assumes "scheduler" is in BaseFormat.PARAMETER_KEY
                    self._parameter["scheduler"] = str(data.get("scheduler"))
                else:  # Option 2: Or just add to custom_params for the settings string
                    custom_params_for_setting_string["Scheduler"] = str(data.get("scheduler"))

            if data.get("base_model_hash") is not None:
                if "model_hash" in self._parameter:  # Assumes "model_hash" is in BaseFormat.PARAMETER_KEY
                    self._parameter["model_hash"] = str(data.get("base_model_hash"))
                else:
                    custom_params_for_setting_string["Model hash"] = str(data.get("base_model_hash"))

            if data.get("loras") is not None:
                # Store the raw LoRA string. Could be a canonical key "loras" or specific "loras_str"
                if "loras" in self._parameter:
                    self._parameter["loras"] = str(data.get("loras"))
                elif "loras_str" in self._parameter:  # If you have a specific key for the string version
                    self._parameter["loras_str"] = str(data.get("loras"))
                else:  # Fallback to adding to the setting string
                    custom_params_for_setting_string["Loras"] = str(data.get("loras"))

            if data.get("start_step") is not None:  # Example of another potential custom param
                custom_params_for_setting_string["Start step"] = str(data.get("start_step"))
            if data.get("denoise") is not None:
                custom_params_for_setting_string["Denoise"] = str(data.get("denoise"))

            # --- Reconstruct a settings string for display (self._setting) ---
            # This will include canonical parameters that have values, and custom ones.
            setting_parts = []
            # Add from canonical parameters that were successfully populated
            for key in BaseFormat.PARAMETER_KEY:  # Iterate through defined canonical keys
                value = self._parameter.get(key)
                if value and value != self.PARAMETER_PLACEHOLDER:
                    # Format key for display (e.g., "cfg_scale" -> "Cfg scale")
                    display_key = key.replace("_", " ").capitalize()
                    setting_parts.append(f"{display_key}: {value}")

            # Add custom parameters that weren't mapped to canonical keys
            for key, value in custom_params_for_setting_string.items():
                setting_parts.append(f"{key}: {value}")  # Key is already display-formatted

            self._setting = ", ".join(sorted(setting_parts))  # Sort for consistent display

            self._logger.info(f"Successfully parsed {self.tool} data.")
            self._status = BaseFormat.Status.READ_SUCCESS

        except json.JSONDecodeError as e:
            self._logger.error(f"Invalid JSON encountered while parsing for {self.tool}: {e}")
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"Invalid JSON data: {e}"
        except Exception as e_parse:
            self._logger.error(f"Unexpected error during {self.tool} data parsing: {e_parse}", exc_info=True)
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"General parsing error: {e_parse}"

        return self._status
