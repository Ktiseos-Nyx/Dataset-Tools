# dataset_tools/vendored_sdpr/format/swarmui.py

__author__ = "receyuki"
__filename__ = "swarmui.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json

from .base_format import BaseFormat
from .utility import remove_quotes # Assuming utility.py is in the same 'format' directory
from ..logger import Logger
from ..constants import PARAMETER_PLACEHOLDER

class SwarmUI(BaseFormat):
    tool = "StableSwarmUI" # Tool name

    # Mapping from SwarmUI JSON keys to BaseFormat.PARAMETER_KEY canonical names
    # SwarmUI Key : Canonical Key
    PARAMETER_MAP = {
        "prompt": "positive_prompt_text", # Goes to self._positive
        "negativeprompt": "negative_prompt_text", # Goes to self._negative
        "model": "model",
        "seed": "seed",
        "cfgscale": "cfg_scale", # Swarm uses "cfgscale"
        "steps": "steps",
        "width": "width", # Updates self._width
        "height": "height", # Updates self._height
        # Swarm has "comfyuisampler" and "autowebuisampler" - need to pick or combine for "sampler_name"
        # Add other mappings as needed: " variación_strength", "imagecount", etc.
    }
    # Original SETTING_KEY was ["model", "", "seed", "cfgscale", "steps", ""]

    def __init__(self, info: dict = None, raw: str = ""): # SwarmUI doesn't get w/h from ImageDataReader init
        # `info` might be the full EXIF JSON if from legacy EXIF.
        # `raw` might be the "sui_image_params" string if from PNG parameters.
        super().__init__(info=info, raw=raw)
        self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool.replace(' ', '_')}")
        self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER
        
        # If raw is provided and info is not, assume raw is the sui_image_params JSON string
        if self._raw and not self._info:
            try:
                self._info = json.loads(self._raw) # Parse raw into info
            except json.JSONDecodeError:
                self._logger.warn(f"{self.tool}: Raw string provided but is not valid JSON. Info remains empty.")
                self._info = {} # Ensure _info is a dict

    # `parse()` is inherited from BaseFormat, which calls `_process()`

    def _process(self): # Called by BaseFormat.parse()
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")

        if not self._info or not isinstance(self._info, dict):
            self._logger.warn(f"{self.tool}: Info data (parsed JSON) is empty or not a dictionary.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "SwarmUI metadata (info dict) is missing or invalid."
            return

        # SwarmUI data is expected under "sui_image_params" key if info is from top-level EXIF
        data_json = self._info.get("sui_image_params", self._info) # Use self._info directly if sui_image_params isn't a sub-key
        
        if not isinstance(data_json, dict): # Ensure data_json is a dict after potential .get()
            self._logger.warn(f"{self.tool}: 'sui_image_params' not found or not a dict. Data: {str(data_json)[:100]}")
            self.status = self.Status.FORMAT_ERROR
            self._error = "'sui_image_params' key missing or data not a dictionary."
            return

        try:
            self._positive = str(data_json.get("prompt", "")).strip()
            self._negative = str(data_json.get("negativeprompt", "")).strip() # Note: "negativeprompt" no underscore

            # Populate self._parameter
            for swarm_key, canonical_key in self.PARAMETER_MAP.items():
                if swarm_key in data_json and canonical_key in self._parameter:
                    value = data_json.get(swarm_key)
                    self._parameter[canonical_key] = str(value if value is not None else self.PARAMETER_PLACEHOLDER)
            
            # Handle sampler specifically (comfyuisampler or autowebuisampler)
            comfy_sampler = data_json.get("comfyuisampler")
            auto_sampler = data_json.get("autowebuisampler")
            sampler_to_use = comfy_sampler or auto_sampler # Prefer comfy if both, else whichever exists
            if "sampler_name" in self._parameter and sampler_to_use:
                self._parameter["sampler_name"] = str(remove_quotes(str(sampler_to_use)))


            # Width and Height
            if data_json.get("width") is not None: self._width = str(data_json.get("width"))
            if data_json.get("height") is not None: self._height = str(data_json.get("height"))
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                 self._parameter["size"] = f"{self._width}x{self._height}"

            # Create settings string from remaining items in data_json
            setting_parts = []
            # Keys already handled in PARAMETER_MAP or specifically above
            handled_keys = set(self.PARAMETER_MAP.keys()) | {"prompt", "negativeprompt", "comfyuisampler", "autowebuisampler"}
            for key, value in data_json.items():
                if key not in handled_keys:
                    display_key = key.replace("_", " ").capitalize()
                    setting_parts.append(f"{display_key}: {remove_quotes(str(value))}")
            self._setting = ", ".join(sorted(setting_parts))
            
            # Update self._raw if it wasn't the primary source initially
            if not self._raw: # If raw was empty and we parsed from self._info (e.g. EXIF)
                 try: self._raw = json.dumps(self._info) # Store the full info dict as raw
                 except TypeError: self._raw = str(self._info)


            if self._positive or self._parameter.get("seed", self.PARAMETER_PLACEHOLDER) != self.PARAMETER_PLACEHOLDER:
                self._logger.info(f"{self.tool}: Data parsed successfully.")
                self.status = self.Status.READ_SUCCESS
            else:
                self._logger.warn(f"{self.tool}: Parsing completed but no positive prompt or seed extracted.")
                self.status = self.Status.FORMAT_ERROR
                self._error = f"{self.tool}: Key fields (prompt, seed) not found."

        except Exception as e:
            self._logger.error(f"{self.tool}: Unexpected error parsing SwarmUI JSON data: {e}", exc_info=True)
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Unexpected error: {e}"

    # Original _ss_format was merged into _process