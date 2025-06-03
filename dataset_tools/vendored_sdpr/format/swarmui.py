# dataset_tools/vendored_sdpr/format/swarmui.py

__author__ = "receyuki"
__filename__ = "swarmui.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json

# import logging # Not needed for type hinting if self._logger from BaseFormat is used
from typing import Any

# from ..logger import get_logger # Not needed if self._logger from BaseFormat is used
from .base_format import BaseFormat

# from .utility import remove_quotes # Handled by _build_settings_string

# Parameter map from SwarmUI keys to canonical keys
SWARM_PARAM_MAP: dict[str, str | list[str]] = {
    # "prompt" and "negativeprompt" are handled separately
    "model": "model",
    "seed": "seed",
    "cfgscale": "cfg_scale",
    "steps": "steps",
    # "width" and "height" are handled by _extract_and_set_dimensions
    # Sampler is handled specially due to comfyuisampler/autowebuisampler
}


class SwarmUI(BaseFormat):
    tool = "StableSwarmUI"  # Corrected tool name casing as per original

    # PARAMETER_MAP is effectively replaced by SWARM_PARAM_MAP for parameter population

    def __init__(self, info: dict[str, Any] | None = None, raw: str = ""):
        super().__init__(info=info, raw=raw)  # BaseFormat logger is initialized here
        # Custom logic: if _raw is provided and _info is not, try to parse _raw as JSON into _info
        # This is done *before* _process is called by BaseFormat.parse()
        if self._raw and not self._info:
            try:
                loaded_info = json.loads(self._raw)
                if isinstance(loaded_info, dict):
                    self._info = loaded_info  # Now self._info is populated
                    self._logger.debug(
                        "Populated self._info from self._raw JSON for %s.", self.tool
                    )
                else:
                    self._logger.warning(
                        "%s: Raw string provided was JSON, but not a dictionary. self._info remains empty.",
                        self.tool,
                    )
                    # self._info remains the default empty dict from BaseFormat.__init__
            except json.JSONDecodeError:
                self._logger.warning(
                    "%s: Raw string provided but is not valid JSON. self._info remains empty. Raw snippet: %s",
                    self.tool,
                    self._raw[:100],
                )
                # self._info remains the default empty dict

    def _get_data_json_for_processing(self) -> dict[str, Any] | None:
        """Determines the correct JSON dictionary to use for parameter extraction.
        SwarmUI data might be directly in self._info or nested under 'sui_image_params'.
        """
        if not self._info or not isinstance(self._info, dict):
            self._logger.warning(
                "%s: Info data (parsed JSON) is empty or not a dictionary.", self.tool
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "SwarmUI metadata (info dict) is missing or invalid."
            return None

        # Prefer 'sui_image_params' if it exists and is a dict, otherwise use self._info directly
        data_to_process = self._info.get("sui_image_params", self._info)

        if not isinstance(data_to_process, dict):
            self._logger.warning(
                "%s: Target data block ('sui_image_params' or root) is not a dictionary. Data snippet: %s",
                self.tool,
                str(data_to_process)[:100],
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "SwarmUI parameter data is not a dictionary."
            return None
        return data_to_process

    def _process(self) -> None:  # Add a line break here
        # self.status is managed by BaseFormat.parse()
        self._logger.debug("Attempting to parse using %s logic.", self.tool)

        data_json = self._get_data_json_for_processing()
        if data_json is None:
            # _get_data_json_for_processing already sets status and error
            return

        try:
            # --- Positive and Negative Prompts ---
            self._positive = str(data_json.get("prompt", "")).strip()
            self._negative = str(data_json.get("negativeprompt", "")).strip()

            handled_keys_for_settings = {"prompt", "negativeprompt"}
            # Add "sui_image_params" to handled if it was the key for data_json itself
            if (
                "sui_image_params" in self._info
                and self._info["sui_image_params"] is data_json
            ):
                # This check is a bit tricky because data_json could *be* self._info.
                # We only want to mark "sui_image_params" as handled at the self._info level
                # if it was explicitly used to *get* data_json.
                # This is more about what keys from self._info NOT to put in the settings string
                # if self._info itself is used for remaining_data_dict later.
                # For now, assume _build_settings_string will use data_json as remaining_data_dict.
                pass

            # --- Populate Standard Parameters using SWARM_PARAM_MAP ---
            self._populate_parameters_from_map(
                data_json, SWARM_PARAM_MAP, handled_keys_for_settings
            )

            # --- Handle Sampler (special case for SwarmUI) ---
            comfy_sampler = data_json.get("comfyuisampler")
            auto_sampler = data_json.get("autowebuisampler")
            sampler_to_use = comfy_sampler or auto_sampler
            if sampler_to_use:
                # self._populate_parameter directly handles str() conversion and placeholder.
                self._populate_parameter(
                    "sampler_name", sampler_to_use, "comfyuisampler/autowebuisampler"
                )
            if comfy_sampler:
                handled_keys_for_settings.add("comfyuisampler")
            if auto_sampler:
                handled_keys_for_settings.add("autowebuisampler")

            # --- Handle Dimensions ---
            self._extract_and_set_dimensions(
                data_json, "width", "height", handled_keys_for_settings
            )

            # --- Build Settings String ---
            # Original code included all *other* keys from data_json.
            self._setting = self._build_settings_string(
                include_standard_params=False,  # Standard params are in self.parameter
                custom_settings_dict=None,
                remaining_data_dict=data_json,
                remaining_handled_keys=handled_keys_for_settings,
                sort_parts=True,
            )

            # --- Raw Data Population (if not already set and _info was the source) ---
            # If self._raw was initially empty and self._info was used (either directly or parsed from original _raw),
            # then self._raw should reflect the entirety of self._info.
            self._set_raw_from_info_if_empty()  # This helper does the job.

            # --- Final Status Check ---
            if self._positive or self._parameter_has_data():
                self._logger.info("%s: Data parsed successfully.", self.tool)
                # self.status = self.Status.READ_SUCCESS # Let BaseFormat.parse() handle
            else:
                self._logger.warning(
                    "%s: Parsing completed but no positive prompt or seed extracted.",
                    self.tool,
                )
                if (
                    self.status != self.Status.FORMAT_ERROR
                ):  # Avoid overwriting specific error
                    self.status = self.Status.FORMAT_ERROR
                    self._error = f"{self.tool}: Key fields (prompt, seed) not found."

        except (
            Exception
        ) as general_err:  # This will catch unexpected errors during processing.
            # JSONDecodeError for self._raw should be caught in __init__
            # or by BaseFormat.parse if _process raises it.
            self._logger.error(
                "%s: Unexpected error parsing SwarmUI JSON data: %s",
                self.tool,
                general_err,
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR  # Ensure status is error
            self._error = f"Unexpected error: {general_err}"
