# dataset_tools/vendored_sdpr/format/swarmui.py

__author__ = "receyuki"
__filename__ = "swarmui.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
from typing import Any  # Added Optional

from .base_format import BaseFormat

# Parameter map from SwarmUI keys to canonical keys
SWARM_PARAM_MAP: dict[str, str | list[str]] = {
    # "prompt" and "negativeprompt" are handled separately by _extract_prompts
    "model": "model",
    "seed": "seed",
    "cfgscale": "cfg_scale",  # Note: In SwarmUI JSON, it's often all lowercase
    "steps": "steps",
    # "width" and "height" are handled by _extract_and_set_dimensions
    # Sampler ("comfyuisampler" or "autowebuisampler") is handled by _extract_sampler_info
}


class SwarmUI(BaseFormat):
    tool = "StableSwarmUI"

    def __init__(self, info: dict[str, Any] | None = None, raw: str = ""):
        # BaseFormat __init__ handles width, height, logger, etc.
        # We call super().__init__ first, then potentially modify self._info based on self._raw
        # The 'raw' passed to super might be the original raw, or if _info is None, this raw.

        # If raw is provided and info is not, try to parse raw as JSON to populate info
        # This allows SwarmUI parser to be instantiated with just the raw JSON string
        # (e.g. from UserComment in an EXIF block).
        parsed_info_from_raw = None
        if raw and not info:
            try:
                loaded_json = json.loads(raw)
                if isinstance(loaded_json, dict):
                    parsed_info_from_raw = loaded_json
                    # We will pass this to super()
            except json.JSONDecodeError:
                # If raw isn't valid JSON, info will remain None for now,
                # and BaseFormat will use the raw string as is.
                # Logging for this case can be done in _get_data_json_for_processing
                pass

        # If parsed_info_from_raw is available, use it; otherwise, use the passed 'info'.
        # The raw string itself is always passed to BaseFormat.
        super().__init__(
            info=(parsed_info_from_raw if parsed_info_from_raw is not None else info),
            raw=raw,
        )

        # If self._info got populated by super() from parsed_info_from_raw,
        # and self._raw was that JSON string, it's fine.
        # If self._raw was something else (e.g. different chunk) and self._info came from 'info' param, also fine.
        # If self._info is *still* empty but self._raw has content (and wasn't the JSON parsed above),
        # _get_data_json_for_processing will attempt to parse self._raw again.

    def _get_data_json_for_processing(self) -> dict[str, Any] | None:
        """Determines the correct JSON dictionary to use for parameter extraction.
        SwarmUI data might be directly in self._info (if parsed from raw in __init__ or passed directly),
        nested under 'sui_image_params' in self._info, or self._raw might be the JSON string itself.
        """
        source_description = ""
        json_source_material = None

        if self._info and isinstance(self._info, dict):
            # Prefer 'sui_image_params' if it exists and is a dict
            if "sui_image_params" in self._info and isinstance(self._info["sui_image_params"], dict):
                self._logger.debug("Using 'sui_image_params' from self._info for %s.", self.tool)
                return self._info["sui_image_params"]
            # Otherwise, self._info itself might be the data (e.g., if parsed from raw in __init__)
            self._logger.debug("Using self._info directly as data source for %s.", self.tool)
            return self._info

        # If self._info wasn't useful, try self._raw (if it wasn't already parsed into self._info by __init__)
        if self._raw:
            json_source_material = self._raw
            source_description = "self._raw string"
        else:  # No self._info dict and no self._raw
            self._logger.warning("%s: No data source (self._info or self._raw) available.", self.tool)
            self.status = self.Status.FORMAT_ERROR
            self._error = "SwarmUI metadata source is missing."
            return None

        # If we are here, json_source_material is from self._raw
        self._logger.debug("Attempting to parse JSON from %s for %s.", source_description, self.tool)
        try:
            data_json = json.loads(json_source_material)
            if not isinstance(data_json, dict):
                self._logger.error(
                    "%s: Parsed JSON from %s is not a dictionary.",
                    self.tool,
                    source_description,
                )
                self.status = self.Status.FORMAT_ERROR
                self._error = f"Invalid JSON structure (not a dict) from {source_description}."
                return None
            # If 'sui_image_params' is in this newly parsed JSON, use that
            if "sui_image_params" in data_json and isinstance(data_json["sui_image_params"], dict):
                self._logger.debug(
                    "Using nested 'sui_image_params' from parsed %s.",
                    source_description,
                )
                return data_json["sui_image_params"]
            return data_json  # Use the root of the parsed JSON
        except json.JSONDecodeError as json_decode_err:
            self._logger.error(
                "%s: Failed to decode JSON from %s: %s",
                self.tool,
                source_description,
                json_decode_err,
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Invalid JSON for SwarmUI from {source_description}: {json_decode_err}"
            return None

    def _extract_prompts(self, data_json: dict[str, Any], handled_keys_set: set[str]):
        """Extracts positive and negative prompts from the data dictionary."""
        self._positive = str(data_json.get("prompt", "")).strip()
        self._negative = str(data_json.get("negativeprompt", "")).strip()
        handled_keys_set.add("prompt")
        handled_keys_set.add("negativeprompt")

    def _extract_sampler_info(self, data_json: dict[str, Any], handled_keys_set: set[str]):
        """Extracts sampler information."""
        comfy_sampler = data_json.get("comfyuisampler")
        auto_sampler = data_json.get("autowebuisampler")
        # Prioritize comfyuisampler if both exist, or take whichever is available
        sampler_to_use = comfy_sampler if comfy_sampler is not None else auto_sampler

        if sampler_to_use is not None:  # Ensure it's not None before populating
            self._populate_parameter("sampler_name", sampler_to_use, "comfyuisampler/autowebuisampler")

        # Add to handled keys regardless of whether they had a value, if the key itself exists
        if "comfyuisampler" in data_json:
            handled_keys_set.add("comfyuisampler")
        if "autowebuisampler" in data_json:
            handled_keys_set.add("autowebuisampler")

    def _process(
        self,
    ) -> None:
        self._logger.debug("Attempting to parse using %s logic.", self.tool)

        # Check if this is a known non-SwarmUI software - SwarmUI should not parse these
        if self._info and "software_tag" in self._info:
            software_tag = str(self._info["software_tag"]).lower()
            non_swarmui_software = [
                "adobe",
                "photoshop",
                "gimp",
                "paint.net",
                "affinity",
                "canva",
                "figma",
                "sketch",
                "procreate",
                "clip studio",
            ]

            for non_swarm_software in non_swarmui_software:
                if non_swarm_software in software_tag:
                    self._logger.debug(
                        "%s: Detected non-SwarmUI software tag ('%s'). This is not a SwarmUI image.",
                        self.tool,
                        self._info["software_tag"],
                    )
                    self.status = self.Status.FORMAT_DETECTION_ERROR
                    self._error = (
                        f"Non-SwarmUI software detected ('{self._info['software_tag']}') - not SwarmUI format."
                    )
                    return

        data_json = self._get_data_json_for_processing()
        if data_json is None:
            # _get_data_json_for_processing has already set status and error
            return

        try:
            handled_keys_for_settings: set[str] = set()

            self._extract_prompts(data_json, handled_keys_for_settings)

            self._populate_parameters_from_map(data_json, SWARM_PARAM_MAP, handled_keys_for_settings)

            self._extract_sampler_info(data_json, handled_keys_for_settings)

            self._extract_and_set_dimensions(  # From BaseFormat
                data_json, "width", "height", handled_keys_for_settings
            )

            self._setting = self._build_settings_string(
                include_standard_params=False,
                remaining_data_dict=data_json,
                remaining_handled_keys=handled_keys_for_settings,
                sort_parts=True,
            )

            self._set_raw_from_info_if_empty()  # Ensure self._raw is populated if needed

            if self._positive or self._parameter_has_data():
                self._logger.info("%s: Data parsed successfully.", self.tool)
                # self.status will be set to READ_SUCCESS by BaseFormat.parse() if no exceptions
            else:
                self._logger.warning(
                    "%s: Parsing completed but no key data (prompt/params) extracted.",
                    self.tool,
                )
                if self.status != self.Status.FORMAT_ERROR:  # Don't overwrite more specific error
                    self.status = self.Status.FORMAT_ERROR
                    self._error = f"{self.tool}: Key fields (prompt, parameters) not found after parsing."

        except Exception as general_err:
            # This broad except is a fallback; specific errors should ideally be caught if known
            self._logger.error(
                "%s: Unexpected error during SwarmUI data processing: %s",
                self.tool,
                general_err,
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Unexpected error processing SwarmUI data: {general_err!s}"
