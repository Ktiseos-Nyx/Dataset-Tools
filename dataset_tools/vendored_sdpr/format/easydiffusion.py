# dataset_tools/vendored_sdpr/format/easydiffusion.py

__author__ = "receyuki"
__filename__ = "easydiffusion.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
from pathlib import PureWindowsPath, PurePosixPath # For parsing model paths

# from ..format.base_format import BaseFormat # This should be:
from .base_format import BaseFormat
# from ..utility import remove_quotes # This should be:
from .utility import remove_quotes
from ..logger import Logger
from ..constants import PARAMETER_PLACEHOLDER

class EasyDiffusion(BaseFormat):
    tool = "Easy Diffusion" # Tool name

    # Unified mapping from Easy Diffusion JSON keys to display names or internal keys.
    # We'll primarily map to BaseFormat.PARAMETER_KEY canonical names.
    # Easy Diffusion JSON key : Canonical Key (or descriptive if not in PARAMETER_KEY)
    ED_TO_CANONICAL_MAP = {
        "prompt": "positive_prompt_text", # Will go into self._positive
        "negative_prompt": "negative_prompt_text", # Will go into self._negative
        "seed": "seed",
        "use_stable_diffusion_model": "model", # Path to model
        "clip_skip": "clip_skip", # Add "clip_skip" to BaseFormat.PARAMETER_KEY if standard
        "use_vae_model": "vae_model", # Path to VAE, add to BaseFormat.PARAMETER_KEY if standard
        "sampler_name": "sampler_name",
        "width": "width", # Will update self._width
        "height": "height", # Will update self._height
        "num_inference_steps": "steps",
        "guidance_scale": "cfg_scale",
        # Other Easy Diffusion keys: "use_hypernetwork_model", "hypernetwork_strength",
        # "use_lora_model", "lora_alpha", "prompt_strength", "show_only_filtered_image",
        # "stream_image_progress", "stream_preview", "save_to_disk_path", "metadata_output_format"
    }
    # Original SETTING_KEY was more for a direct zip, less flexible.

    def __init__(self, info: dict = None, raw: str = ""): # ED doesn't get w/h from ImageDataReader init
        super().__init__(info=info, raw=raw)
        self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool.replace(' ', '_')}")
        self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER

    # `parse()` is inherited from BaseFormat, which calls `_process()`

    def _process(self): # Called by BaseFormat.parse()
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")
        
        json_to_parse = self._raw
        if not json_to_parse and self._info: # Fallback to _info if _raw is empty (e.g. from PNG text chunks)
            # Original ED parser did str(self._info).replace("'", '"') - this is risky if info isn't JSON string.
            # Assuming self._info IS the dict for PNGs from EasyDiffusion if _raw isn't set.
            if isinstance(self._info, dict):
                # If self._info is already the parsed dict (e.g., from PNG)
                json_to_parse = self._info
            elif isinstance(self._info, str):
                json_to_parse = self._info # If info itself is the JSON string
            else:
                self._logger.warn(f"{self.tool}: Info data is not a dict or string. Cannot parse.")
                self.status = self.Status.FORMAT_ERROR
                self._error = "Easy Diffusion metadata (info) is not a usable dict or JSON string."
                return


        if not json_to_parse:
            self._logger.warn(f"{self.tool}: Raw data (or info) is empty. Cannot parse.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "Easy Diffusion metadata string is empty."
            return

        data_json: dict
        if isinstance(json_to_parse, str):
            try:
                data_json = json.loads(json_to_parse)
            except json.JSONDecodeError as e:
                self._logger.error(f"{self.tool}: Failed to decode JSON: {e}")
                self.status = self.Status.FORMAT_ERROR
                self._error = f"Invalid JSON for Easy Diffusion: {e}"
                return
        elif isinstance(json_to_parse, dict):
            data_json = json_to_parse # Already a dict
        else:
            self._logger.error(f"{self.tool}: Input data is not a JSON string or dict.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "Invalid input data type for Easy Diffusion parser."
            return

        # The original parser used two different mappings based on key presence.
        # A simpler way is to check for common prompt keys directly.
        self._positive = str(data_json.get("prompt", data_json.get("Prompt", ""))).strip()
        self._negative = str(data_json.get("negative_prompt", data_json.get("Negative Prompt", ""))).strip()

        # Populate self._parameter
        # self._parameter is already initialized by BaseFormat
        for ed_key, canonical_key in self.ED_TO_CANONICAL_MAP.items():
            if ed_key in data_json and canonical_key in self._parameter:
                value = data_json[ed_key]
                if canonical_key == "model" or canonical_key == "vae_model": # These are paths
                    if value and isinstance(value, str):
                        # Extract filename from path
                        if PureWindowsPath(value).drive: value = PureWindowsPath(value).name
                        else: value = PurePosixPath(value).name
                self._parameter[canonical_key] = str(value)
            elif ed_key in data_json and canonical_key not in ["positive_prompt_text", "negative_prompt_text", "width", "height"]:
                # Store as custom parameter if not mapped to a standard one but exists in ED_TO_CANONICAL_MAP
                # and it's not one of the specially handled ones.
                # (This might be redundant if ED_TO_CANONICAL_MAP only contains mappings to BaseFormat.PARAMETER_KEY)
                 self._logger.debug(f"{self.tool}: Key '{ed_key}' (mapped to '{canonical_key}') not in BaseFormat.PARAMETER_KEY. Storing in settings string.")


        # Width and Height
        if data_json.get("width") is not None: self._width = str(data_json.get("width"))
        if data_json.get("height") is not None: self._height = str(data_json.get("height"))
        if "size" in self._parameter and self._width != "0" and self._height != "0":
             self._parameter["size"] = f"{self._width}x{self._height}"


        # Create a settings string from all other key-value pairs in data_json
        # that weren't the main prompt or negative prompt.
        setting_parts = []
        for key, value in data_json.items():
            if key not in ["prompt", "Prompt", "negative_prompt", "Negative Prompt"]:
                display_key = key.replace("_", " ").capitalize() # Format for display
                # If this key was mapped to a canonical parameter, it's already in self._parameter.
                # We can choose to either duplicate it in settings string or only put unmapped items here.
                # For simplicity, let's include all non-prompt items.
                setting_parts.append(f"{display_key}: {remove_quotes(str(value))}")
        self._setting = ", ".join(sorted(setting_parts))
        
        # Update self._raw to reflect what was actually parsed if needed
        # self._raw = json.dumps(data_json) # Or keep original raw string passed to __init__

        if self._positive or self._parameter.get("seed", self.PARAMETER_PLACEHOLDER) != self.PARAMETER_PLACEHOLDER:
            self._logger.info(f"{self.tool}: Data parsed successfully.")
            self.status = self.Status.READ_SUCCESS
        else:
            self._logger.warn(f"{self.tool}: Parsing completed but no positive prompt or seed extracted.")
            self.status = self.Status.FORMAT_ERROR
            self._error = f"{self.tool}: Key fields (prompt, seed) not found."