# dataset_tools/vendored_sdpr/format/easydiffusion.py

__author__ = "receyuki"
__filename__ = "easydiffusion.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json

# import logging # No longer needed for type hinting if self._logger from BaseFormat is used
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any

# from ..logger import get_logger # Not needed if self._logger from BaseFormat is used
from .base_format import BaseFormat

# from .utility import remove_quotes # Handled by _build_settings_string in BaseFormat

# Define the map at the module or class level for clarity
ED_PARAM_MAP: dict[str, str | list[str]] = {
    # Easy Diffusion Key : Canonical Param Key (or list of keys)
    # "prompt" and "negative_prompt" are handled separately for self._positive/negative
    "seed": "seed",
    "use_stable_diffusion_model": "model",
    "clip_skip": "clip_skip",  # Assuming "clip_skip" is in BaseFormat.PARAMETER_KEY
    "use_vae_model": "vae_model",  # Assuming "vae_model" is in BaseFormat.PARAMETER_KEY
    "sampler_name": "sampler_name",
    # "width" and "height" handled by _extract_and_set_dimensions
    "num_inference_steps": "steps",
    "guidance_scale": "cfg_scale",
}


class EasyDiffusion(BaseFormat):
    tool = "Easy Diffusion"

    # ED_TO_CANONICAL_MAP is effectively replaced by ED_PARAM_MAP for parameter population
    # and direct handling of prompt/negative_prompt.

    # __init__ is inherited from BaseFormat.
    # The logger is also inherited and named correctly.

    def _get_json_data_to_parse(self) -> dict[str, Any] | None:
        """Determines the JSON data source and parses it into a dictionary."""
        json_source_material = self._raw
        source_description = "raw data"

        if not json_source_material and self._info:
            if isinstance(self._info, dict):
                # If _info is already a dict, it's likely pre-parsed JSON
                self._logger.debug("Using pre-parsed dictionary from self._info for %s.", self.tool)
                return self._info  # Use it directly
            if isinstance(self._info, str):
                json_source_material = self._info
                source_description = "self._info (string)"
            else:
                self._logger.warning(
                    "%s: Info data is not a dict or string. Cannot parse. Type: %s",
                    self.tool,
                    type(self._info).__name__,
                )
                self.status = self.Status.FORMAT_ERROR
                self._error = "Easy Diffusion metadata (info) is not a usable dict or JSON string."
                return None

        if not json_source_material:
            self._logger.warning("%s: Raw data (or info) is empty. Cannot parse.", self.tool)
            self.status = self.Status.FORMAT_ERROR
            self._error = "Easy Diffusion metadata string is empty."
            return None

        self._logger.debug("Attempting to parse JSON from %s for %s.", source_description, self.tool)
        if not isinstance(json_source_material, str) or not json_source_material.strip().startswith("{"):
            self._logger.debug("Easy Diffusion: Source material is not a JSON string.")
            self.status = self.Status.FORMAT_DETECTION_ERROR
            return None
        try:
            data_json = json.loads(json_source_material)
            if not isinstance(data_json, dict):
                self._logger.error(
                    "%s: Parsed JSON from %s is not a dictionary.",
                    self.tool,
                    source_description,
                )
                self.status = self.Status.FORMAT_ERROR
                self._error = f"Invalid JSON structure for Easy Diffusion (not a dict) from {source_description}."
                return None
            return data_json
        except json.JSONDecodeError as json_decode_err:
            self._logger.error(
                "%s: Failed to decode JSON from %s: %s",
                self.tool,
                source_description,
                json_decode_err,
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Invalid JSON for Easy Diffusion from {source_description}: {json_decode_err}"
            return None

    def _process_model_value(self, value: Any) -> str:
        """Helper to process model/VAE paths."""
        if value and isinstance(value, str):
            # Check if it looks like a Windows path with a drive letter
            if PureWindowsPath(value).drive and len(PureWindowsPath(value).parts) > 1:
                return PureWindowsPath(value).name
            # Check if it looks like a Posix path with multiple parts
            if not PureWindowsPath(value).drive and len(PurePosixPath(value).parts) > 1:
                return PurePosixPath(value).name
        return str(value)

    def _process(self) -> None:
        # self.status is managed by BaseFormat.parse()
        self._logger.debug("Attempting to parse using %s logic.", self.tool)

        # Check if this is a non-Easy Diffusion software - Easy Diffusion should not parse these
        if self._info and "software_tag" in self._info:
            software_tag = str(self._info["software_tag"]).lower()
            non_easydiffusion_software = [
                "celsys",
                "clip studio",
                "adobe",
                "photoshop",
                "gimp",
                "paint.net",
                "automatic1111",
                "forge",
                "comfyui",
                "invokeai",
                "novelai",
                "stable diffusion",
            ]

            for non_ed_software in non_easydiffusion_software:
                if non_ed_software in software_tag:
                    self._logger.debug(
                        "%s: Detected non-Easy Diffusion software tag ('%s'). This is not an Easy Diffusion image.",
                        self.tool,
                        self._info["software_tag"],
                    )
                    self.status = self.Status.FORMAT_DETECTION_ERROR
                    self._error = f"Non-Easy Diffusion software detected ('{self._info['software_tag']}') - not Easy Diffusion format."
                    return

        data_json = self._get_json_data_to_parse()
        if data_json is None:
            # _get_json_data_to_parse already sets status and error
            return

        # Additional check: Must have Easy Diffusion-specific fields
        if data_json and isinstance(data_json, dict):
            ed_specific_fields = [
                "num_inference_steps",
                "guidance_scale",
                "use_stable_diffusion_model",
            ]
            has_ed_fields = any(field in data_json for field in ed_specific_fields)

            if not has_ed_fields:
                self._logger.debug(
                    "%s: No Easy Diffusion-specific fields found (%s). This may not be an Easy Diffusion image.",
                    self.tool,
                    ed_specific_fields,
                )
                self.status = self.Status.FORMAT_DETECTION_ERROR
                self._error = "No Easy Diffusion-specific fields found - not Easy Diffusion format."
                return

        # --- Positive and Negative Prompts ---
        # Easy Diffusion uses "prompt" or "Prompt"
        self._positive = str(data_json.get("prompt", data_json.get("Prompt", ""))).strip()
        # And "negative_prompt" or "Negative Prompt"
        self._negative = str(data_json.get("negative_prompt", data_json.get("Negative Prompt", ""))).strip()

        handled_keys_for_settings = {
            "prompt",
            "Prompt",
            "negative_prompt",
            "Negative Prompt",
        }
        # `handled_keys_for_settings` will also be updated by `_populate_parameters_from_map`
        # and `_extract_and_set_dimensions`.

        # --- Populate Standard Parameters ---
        # Create a specific map for ED, applying value processors where needed
        current_ed_param_map = {}
        value_processors_map = {
            "model": self._process_model_value,
            "vae_model": self._process_model_value,
        }

        for ed_key, canonical_key_target in ED_PARAM_MAP.items():
            if ed_key in data_json:
                value_processor = value_processors_map.get(canonical_key_target)  # Check if target needs processor
                if not value_processor and isinstance(
                    canonical_key_target, list
                ):  # Check if any in list need processor
                    for k_target in canonical_key_target:
                        if value_processors_map.get(k_target):
                            value_processor = value_processors_map.get(k_target)
                            break

                self._populate_parameter(
                    canonical_key_target,
                    (value_processor(data_json[ed_key]) if value_processor else data_json[ed_key]),
                    source_key_for_debug=ed_key,
                )
                handled_keys_for_settings.add(ed_key)

        # --- Handle Dimensions ---
        # Easy Diffusion uses "width" and "height" directly.
        self._extract_and_set_dimensions(data_json, "width", "height", handled_keys_for_settings)

        # --- Build Settings String ---
        # The original code included all *other* keys from data_json in the settings string.
        self._setting = self._build_settings_string(
            include_standard_params=False,  # Standard params will be in self.parameter
            custom_settings_dict=None,  # No separately collected custom dict here
            remaining_data_dict=data_json,
            remaining_handled_keys=handled_keys_for_settings,
            sort_parts=True,
        )
        # Note: _build_settings_string has its own value processor for remaining items
        # which includes remove_quotes.

        # --- Final Status Check ---
        # BaseFormat.parse() handles setting READ_SUCCESS if no error status was set.
        if self._positive or self._parameter_has_data():
            self._logger.info("%s: Data parsed successfully.", self.tool)
        else:
            self._logger.warning(
                "%s: Parsing completed but no positive prompt or seed extracted.",
                self.tool,
            )
            # Only set error if not already set by _get_json_data_to_parse
            if self.status != self.Status.FORMAT_ERROR:
                self.status = self.Status.FORMAT_ERROR
                self._error = f"{self.tool}: Key fields (prompt, seed) not found."
