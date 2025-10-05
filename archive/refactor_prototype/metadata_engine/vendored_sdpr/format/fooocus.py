# dataset_tools/vendored_sdpr/format/fooocus.py

__author__ = "receyuki"
__filename__ = "fooocus.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

# import logging # Not needed for type hinting if self._logger from BaseFormat

# from ..logger import get_logger # Not needed if self._logger from BaseFormat
from .base_format import BaseFormat

# from .utility import remove_quotes # Handled by _build_settings_string

# Define parameter map for Fooocus keys to canonical keys
FOOOCUS_PARAM_MAP: dict[str, str | list[str]] = {
    # "prompt" and "negative_prompt" are handled separately
    "sampler_name": "sampler_name",
    "seed": "seed",
    "guidance_scale": "cfg_scale",
    "steps": "steps",
    "base_model_name": "model",
    "base_model_hash": "model_hash",
    "lora_loras": "loras",  # Assuming "loras" is a standard parameter key
    # "width" and "height" handled by _extract_and_set_dimensions
    "scheduler": "scheduler",
}


class Fooocus(BaseFormat):
    tool = "Fooocus"

    # PARAMETER_MAP is effectively replaced by FOOOCUS_PARAM_MAP

    # __init__ is inherited from BaseFormat.
    # The logger is also inherited and named correctly by BaseFormat.

    def _process(self) -> None:
        # self.status is managed by BaseFormat.parse()
        self._logger.debug("Attempting to parse using %s logic.", self.tool)

        if not self._info or not isinstance(self._info, dict):
            self._logger.warning("%s: Info data (parsed JSON) is empty or not a dictionary.", self.tool)
            self.status = self.Status.FORMAT_ERROR
            self._error = "Fooocus metadata (info dict) is missing or invalid."
            return

        data_json = self._info  # Fooocus directly uses the info dict

        try:
            # --- Positive and Negative Prompts ---
            self._positive = str(data_json.get("prompt", "")).strip()
            self._negative = str(data_json.get("negative_prompt", "")).strip()

            handled_keys_for_settings = {"prompt", "negative_prompt"}

            # --- Populate Standard Parameters ---
            self._populate_parameters_from_map(data_json, FOOOCUS_PARAM_MAP, handled_keys_for_settings)

            # --- Handle Dimensions ---
            self._extract_and_set_dimensions(data_json, "width", "height", handled_keys_for_settings)

            # --- Build Settings String ---
            # Original code included all *other* keys from data_json in the settings string.
            self._setting = self._build_settings_string(
                include_standard_params=False,  # Standard params are in self.parameter
                custom_settings_dict=None,
                remaining_data_dict=data_json,
                remaining_handled_keys=handled_keys_for_settings,
                sort_parts=True,
            )

            # --- Raw Data Population ---
            self._set_raw_from_info_if_empty()

            # --- Final Status Check ---
            if self._positive or self._parameter_has_data():
                self._logger.info("%s: Data parsed successfully.", self.tool)
                # self.status = self.Status.READ_SUCCESS # Let BaseFormat.parse() handle
            else:
                self._logger.warning(
                    "%s: Parsing completed but no positive prompt or seed extracted.",
                    self.tool,
                )
                # Only set error if not already set (e.g., by _info validation)
                if self.status != self.Status.FORMAT_ERROR:
                    self.status = self.Status.FORMAT_ERROR
                    self._error = f"{self.tool}: Key fields (prompt, seed) not found in Fooocus JSON."

        except Exception as general_err:  # pylint: disable=broad-except
            self._logger.error(
                "%s: Unexpected error parsing Fooocus JSON data: %s",
                self.tool,
                general_err,
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR  # Ensure status is error
            self._error = f"Unexpected error: {general_err}"
