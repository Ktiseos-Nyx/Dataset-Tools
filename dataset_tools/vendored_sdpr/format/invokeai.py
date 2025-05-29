# dataset_tools/vendored_sdpr/format/invokeai.py

__author__ = "receyuki"
__filename__ = "invokeai.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
import re

from .base_format import BaseFormat
from .utility import remove_quotes  # Assuming utility.py is in the same 'format' directory
from ..logger import Logger
from ..constants import PARAMETER_PLACEHOLDER


class InvokeAI(BaseFormat):
    tool = "InvokeAI"  # Tool name

    # These SETTING_KEYs were for the fragile zip mapping.
    # We will map more directly from parsed JSON to self._parameter.
    # SETTING_KEY_INVOKEAI_METADATA = [ ... ]
    # SETTING_KEY_METADATA = [ ... ]
    # SETTING_KEY_DREAM = [ ... ]
    DREAM_MAPPING = {  # For parsing the "-X value" style "Dream" string
        "Steps": "s",
        "Seed": "S",
        "CFG scale": "C",
        "Sampler": "A",
        # "Size" is handled by "W" and "H"
    }

    def __init__(self, info: dict = None, raw: str = ""):  # InvokeAI doesn't get w/h from ImageDataReader init
        super().__init__(info=info, raw=raw)
        self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool}")
        self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER

    # `parse()` is inherited from BaseFormat, which calls `_process()`

    def _process(self):  # Called by BaseFormat.parse()
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
            self._logger.warn(f"{self.tool}: No known InvokeAI metadata keys found in info dict.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "No InvokeAI metadata keys (invokeai_metadata, sd-metadata, Dream) found."
            return

        if parsed_successfully:
            self.status = self.Status.READ_SUCCESS
            self._logger.info(f"{self.tool}: Data parsed successfully.")
        else:
            # If none of the specific parse methods succeeded but one was attempted
            self.status = self.Status.FORMAT_ERROR
            if not self._error:  # If a sub-parser didn't set a specific error
                self._error = f"{self.tool}: Failed to parse identified InvokeAI metadata structure."

    def _parse_invoke_metadata_format(self) -> bool:  # New name for original _invoke_metadata
        try:
            data_json = json.loads(self._info.get("invokeai_metadata", "{}"))
            if not isinstance(data_json, dict):
                self._error = "invokeai_metadata is not a valid JSON dictionary."
                return False

            self._positive = str(data_json.pop("positive_prompt", "")).strip()
            self._negative = str(data_json.pop("negative_prompt", "")).strip()

            # SDXL specific prompts
            if data_json.get("positive_style_prompt"):
                self._positive_sdxl["style"] = str(data_json.pop("positive_style_prompt", "")).strip()  # Example key
            if data_json.get("negative_style_prompt"):
                self._negative_sdxl["style"] = str(data_json.pop("negative_style_prompt", "")).strip()  # Example key
            if self._positive_sdxl or self._negative_sdxl:
                self._is_sdxl = True

            # Populate self._parameter
            if "model" in self._parameter and data_json.get("model"):
                model_info = data_json.get("model", {})
                self._parameter["model"] = str(model_info.get("model_name", self.PARAMETER_PLACEHOLDER))
                if "model_hash" in self._parameter and model_info.get("hash"):  # Assuming InvokeAI provides hash here
                    self._parameter["model_hash"] = str(model_info.get("hash"))

            if "refiner_model" in data_json:  # Handle refiner model as well if present
                refiner_info = data_json.get("refiner_model", {})
                # How to store this? Maybe add to settings string or a specific parameter field.
                # For now, let's add to setting string.
                # Could also be self._parameter["refiner_model_name"] etc. if canonical.

            # Other parameters
            param_map = {
                "seed": "seed",
                "steps": "steps",
                "cfg_scale": "cfg_scale",
                "scheduler": "scheduler",
                "width": "width",
                "height": "height",
                "refiner_steps": "refiner_steps",  # If you have canonical keys for these
                "refiner_cfg_scale": "refiner_cfg_scale",
                "refiner_scheduler": "refiner_scheduler",
                "refiner_positive_aesthetic_score": "refiner_positive_aesthetic_score",
                "refiner_negative_aesthetic_score": "refiner_negative_aesthetic_score",
                "refiner_start": "refiner_start",
            }
            for invoke_key, canonical_key in param_map.items():
                if invoke_key in data_json and canonical_key in self._parameter:
                    self._parameter[canonical_key] = str(data_json[invoke_key])
                elif invoke_key in data_json:  # Add to settings if not a canonical key
                    data_json[invoke_key]  # Keep it in data_json for settings string

            if data_json.get("width") is not None:
                self._width = str(data_json.get("width"))
            if data_json.get("height") is not None:
                self._height = str(data_json.get("height"))
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            # Remaining items in data_json go into the setting string
            setting_parts = [
                f"{k.replace('_', ' ').capitalize()}: {remove_quotes(str(v))}" for k, v in data_json.items()
            ]
            self._setting = ", ".join(sorted(setting_parts))
            self._raw = self._info.get("invokeai_metadata")  # Store original JSON string as raw
            return True
        except json.JSONDecodeError as e:
            self._error = f"Invalid JSON in invokeai_metadata: {e}"
            return False
        except Exception as e:
            self._error = f"Error parsing invokeai_metadata: {e}"
            self._logger.error(f"InvokeAI metadata parsing error: {e}", exc_info=True)
            return False

    def _parse_sd_metadata_format(self) -> bool:  # New name for original _invoke_sd_metadata
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
            if isinstance(prompt_field, list) and prompt_field:
                prompt_text = str(prompt_field[0].get("prompt", ""))
            elif isinstance(prompt_field, str):
                prompt_text = prompt_field
            else:
                prompt_text = ""

            self._positive, self._negative = self.split_invokeai_prompt(prompt_text)

            # Populate parameters
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
                # Model is usually in top-level data_json for sd-metadata
                if sd_meta_key == "model" and "model_weights" in data_json and canonical_key in self._parameter:
                    self._parameter[canonical_key] = str(data_json.get("model_weights"))
                # Other params from image_data
                elif sd_meta_key in image_data and canonical_key in self._parameter:
                    self._parameter[canonical_key] = str(image_data[sd_meta_key])

            if image_data.get("width") is not None:
                self._width = str(image_data.get("width"))
            if image_data.get("height") is not None:
                self._height = str(image_data.get("height"))
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            # Construct setting string from remaining image_data and top-level data_json
            setting_parts = []
            for k, v in image_data.items():
                if k not in ["prompt", "width", "height"] + list(param_map.keys()):  # Avoid already handled
                    setting_parts.append(f"{k.replace('_', ' ').capitalize()}: {remove_quotes(str(v))}")
            for k, v in data_json.items():
                if k not in ["image", "model_weights"]:  # Avoid already handled
                    setting_parts.append(f"{k.replace('_', ' ').capitalize()}: {remove_quotes(str(v))}")
            self._setting = ", ".join(sorted(list(set(setting_parts))))  # set to remove potential duplicates

            self._raw = self._info.get("sd-metadata")
            return True
        except json.JSONDecodeError as e:
            self._error = f"Invalid JSON in sd-metadata: {e}"
            return False
        except Exception as e:
            self._error = f"Error parsing sd-metadata: {e}"
            self._logger.error(f"InvokeAI sd-metadata parsing error: {e}", exc_info=True)
            return False

    def _parse_dream_format(self) -> bool:  # New name for original _invoke_dream
        try:
            data_str = self._info.get("Dream", "")
            if not data_str:
                self._error = "'Dream' string is empty."
                return False

            # Regex to separate prompt from settings: "Prompt" -s 100 -S 123 ...
            pattern = r'"(.*?)"\s*(-\S.*)?$'  # Group 1: Prompt, Group 2: Settings string
            match = re.search(pattern, data_str)
            if not match:
                self._error = "Could not parse 'Dream' string structure."
                return False

            prompt_text = match.group(1).strip('" ')
            settings_str = (match.group(2) or "").strip()

            self._positive, self._negative = self.split_invokeai_prompt(prompt_text)

            # Parse settings like "-s 30 -S 12345 -W 512 -H 512 -C 7.5 -A k_lms"
            param_pattern = r"-(\w+)\s+([\w.-]+)"  # -X value
            parsed_settings = dict(re.findall(param_pattern, settings_str))

            # Map to canonical
            if "s" in parsed_settings and "steps" in self._parameter:
                self._parameter["steps"] = parsed_settings["s"]
            if "S" in parsed_settings and "seed" in self._parameter:
                self._parameter["seed"] = parsed_settings["S"]
            if "C" in parsed_settings and "cfg_scale" in self._parameter:
                self._parameter["cfg_scale"] = parsed_settings["C"]
            if "A" in parsed_settings and "sampler_name" in self._parameter:
                self._parameter["sampler_name"] = parsed_settings["A"]

            if "W" in parsed_settings:
                self._width = parsed_settings["W"]
            if "H" in parsed_settings:
                self._height = parsed_settings["H"]
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            # Reconstruct setting string for display
            setting_parts = []
            for dream_key, display_name_start in self.DREAM_MAPPING.items():  # Use DREAM_MAPPING to get display names
                # This needs fixing, DREAM_MAPPING value is the parsed_settings key.
                # Example: DREAM_MAPPING = {"Steps": "s"}
                # parsed_settings_key = self.DREAM_MAPPING.get(display_name_start) # Incorrect
                pass  # This mapping part needs rethink for settings string

            # Simpler settings string from parsed_settings
            for k, v in parsed_settings.items():
                # Try to find a more human-readable key for display
                display_key = k
                for name, short_key in self.DREAM_MAPPING.items():
                    if short_key == k:
                        display_key = name
                        break
                setting_parts.append(f"{display_key.capitalize()}: {v}")
            self._setting = ", ".join(sorted(setting_parts))

            self._raw = data_str
            return True
        except Exception as e:
            self._error = f"Error parsing Dream string: {e}"
            self._logger.error(f"InvokeAI Dream parsing error: {e}", exc_info=True)
            return False

    @staticmethod
    def split_invokeai_prompt(prompt: str) -> tuple[str, str]:  # Renamed from split_prompt
        # InvokeAI often uses "prompt[negative_prompt]"
        pattern = r"^(.*?)\[(.*?)\]$"  # Matches "positive[negative]"
        match = re.fullmatch(pattern, prompt.strip())  # Use fullmatch for entire string

        if match:
            positive = match.group(1).strip()
            negative = match.group(2).strip()
        else:  # No brackets, assume all positive
            positive = prompt.strip()
            negative = ""
        return positive, negative
