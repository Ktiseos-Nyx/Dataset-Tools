# dataset_tools/vendored_sdpr/format/fooocus.py

__author__ = "receyuki"
__filename__ = "fooocus.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json # For parsing the metadata if it's JSON

from .base_format import BaseFormat
from .utility import remove_quotes # Assuming utility.py is in the same 'format' directory
from ..logger import Logger
from ..constants import PARAMETER_PLACEHOLDER

class Fooocus(BaseFormat):
    tool = "Fooocus" # Tool name

    # Mapping from Fooocus JSON keys to BaseFormat.PARAMETER_KEY canonical names
    # Fooocus Key : Canonical Key
    PARAMETER_MAP = {
        "prompt": "positive_prompt_text", # Goes to self._positive
        "negative_prompt": "negative_prompt_text", # Goes to self._negative
        "sampler_name": "sampler_name", # Or "sampler"
        "seed": "seed",
        "guidance_scale": "cfg_scale", # Or "cfg"
        "steps": "steps",
        "base_model_name": "model",    # Or "Model"
        "base_model_hash": "model_hash", # If you want to store this
        "lora_loras": "loras",        # String of LoRAs
        "width": "width",             # Updates self._width
        "height": "height",           # Updates self._height
        "scheduler": "scheduler",
        # Add other Fooocus specific keys like "sharpness", "adm_guidance", "refiner_model", etc.
        # and map them if they have canonical equivalents or should be in settings.
    }
    # Original SETTING_KEY was more for a direct zip, less flexible.

    def __init__(self, info: dict = None, raw: str = ""): # Fooocus doesn't get w/h from ImageDataReader init
        # For Fooocus, 'info' is expected to be the parsed JSON dict
        # 'raw' might be unused if 'info' is the primary source.
        super().__init__(info=info, raw=raw) # BaseFormat handles width/height defaults
        self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool}")
        self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER

    # `parse()` is inherited from BaseFormat, which calls `_process()`

    def _process(self): # Called by BaseFormat.parse()
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")
        
        # Fooocus data comes from ImageDataReader as a dictionary in self._info
        # (parsed from JFIF comment or PNG Comment chunk).
        if not self._info or not isinstance(self._info, dict):
            self._logger.warn(f"{self.tool}: Info data (parsed JSON) is empty or not a dictionary.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "Fooocus metadata (info dict) is missing or invalid."
            return

        data_json = self._info # Use the pre-parsed JSON dict

        try:
            self._positive = str(data_json.get("prompt", "")).strip()
            self._negative = str(data_json.get("negative_prompt", "")).strip()
            
            # Populate self._parameter
            for fc_key, canonical_key in self.PARAMETER_MAP.items():
                if fc_key in data_json and canonical_key in self._parameter:
                    value = data_json.get(fc_key)
                    self._parameter[canonical_key] = str(value if value is not None else self.PARAMETER_PLACEHOLDER)
            
            # Width and Height
            if data_json.get("width") is not None: self._width = str(data_json.get("width"))
            if data_json.get("height") is not None: self._height = str(data_json.get("height"))
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                 self._parameter["size"] = f"{self._width}x{self._height}"

            # Create a settings string from all items in data_json
            # excluding prompts, for display.
            setting_parts = []
            for key, value in data_json.items():
                if key not in ["prompt", "negative_prompt"]: # Already handled
                    display_key = key.replace("_", " ").capitalize()
                    setting_parts.append(f"{display_key}: {remove_quotes(str(value))}")
            self._setting = ", ".join(sorted(setting_parts))

            # For Fooocus, self._raw could be the original comment string if ImageDataReader passed it,
            # or we can reconstruct the JSON string.
            # If ImageDataReader only passed the parsed dict as self._info, then:
            if not self._raw: # If raw wasn't set by ImageDataReader (e.g. if it parsed the JSON itself)
                try:
                    self._raw = json.dumps(self._info) # Store the input JSON as raw
                except TypeError: # Should not happen if self._info is from json.loads
                    self._raw = str(self._info)


            if self._positive or self._parameter.get("seed", self.PARAMETER_PLACEHOLDER) != self.PARAMETER_PLACEHOLDER:
                self._logger.info(f"{self.tool}: Data parsed successfully.")
                self.status = self.Status.READ_SUCCESS
            else:
                self._logger.warn(f"{self.tool}: Parsing completed but no positive prompt or seed extracted.")
                self.status = self.Status.FORMAT_ERROR
                self._error = f"{self.tool}: Key fields (prompt, seed) not found in Fooocus JSON."

        except Exception as e:
            self._logger.error(f"{self.tool}: Unexpected error parsing Fooocus JSON data: {e}", exc_info=True)
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Unexpected error: {e}"

    # Original _fc_format was merged into _process