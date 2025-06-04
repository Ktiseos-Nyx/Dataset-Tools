# dataset_tools/vendored_sdpr/format/civitai.py
import json

# import logging # Not needed for type hinting if self._logger from BaseFormat
import re
from typing import Any

# from ..logger import get_logger # Not needed if self._logger from BaseFormat
from .base_format import BaseFormat

# from .utility import remove_quotes # Handled by _build_settings_string

# Define parameter map for Civitai extra_meta_dict keys to canonical keys
CIVITAI_EXTRA_META_TO_PARAM_MAP: dict[str, str | list[str]] = {
    "steps": "steps",
    # CFG scale has two common keys in Civitai metadata
    "CFG scale": "cfg_scale",
    "cfgScale": "cfg_scale",  # Will try "CFG scale" then "cfgScale" if used in _populate_parameters_from_map
    # Sampler also has two common keys
    "sampler": "sampler_name",
    "sampler_name": "sampler_name",
    "seed": "seed",
    # "width" and "height" handled by _extract_and_set_dimensions
    # "prompt" and "negativePrompt" handled separately
}


class CivitaiComfyUIFormat(BaseFormat):
    tool = "Civitai ComfyUI"

    def __init__(
        self,
        info: dict[str, Any] | None = None,  # Civitai doesn't use _info typically
        raw: str = "",  # Raw is the UserComment string
        width: int = 0,  # Can be passed if known, otherwise from metadata
        height: int = 0,
    ):
        super().__init__(info=info, raw=raw, width=width, height=height)
        # self._logger is inherited. If a specific logger name format was used:
        # self._logger = get_logger(f"DSVendored_SDPR.Format.{self.tool.replace(' ', '_')}")
        self.workflow_data: dict[str, Any] | None = None  # To store the outer workflow JSON

    def _decode_user_comment_for_civitai(self, uc_string: str) -> str | None:
        self._logger.debug("Attempting to decode UserComment (first 70): '%s'", uc_string[:70])
        if not uc_string or not isinstance(uc_string, str):
            self._logger.warning("UserComment string is empty or not a string.")
            return None

        data_to_process = uc_string
        prefix_pattern = r'^charset\s*=\s*["\']?(UNICODE|UTF-16|UTF-16LE)["\']?\s*'
        match = re.match(prefix_pattern, uc_string, re.IGNORECASE)
        if match:
            data_to_process = uc_string[len(match.group(0)) :].strip()
            self._logger.debug(
                "Stripped 'charset=Unicode' prefix. Remaining: '%s'",
                data_to_process[:50],
            )

        if ("笀" in data_to_process or "∀" in data_to_process or "izarea" in data_to_process) and not (
            data_to_process.startswith("{") and data_to_process.endswith("}")
        ):
            self._logger.debug("Mojibake characters detected. Attempting latin-1 -> utf-16le decode.")
            try:
                json_string = data_to_process.encode("latin-1", "replace").decode("utf-16le", "replace")
                json_string = json_string.strip("\x00")
                json.loads(json_string)
                self._logger.debug("Mojibake reversal/decode (latin-1 -> utf-16le) successful.")
                return json_string
            except Exception as e_moji:  # pylint: disable=broad-except
                self._logger.warning(
                    "Mojibake reversal/decode (latin-1 -> utf-16le) attempt failed: %s",
                    e_moji,
                    exc_info=True,  # Good to have for unexpected decode issues
                )

        if data_to_process.startswith("{") and data_to_process.endswith("}"):
            self._logger.debug("Data (post-prefix/post-mojibake-attempt) looks like plain JSON. Validating.")
            try:
                data_to_process = data_to_process.strip("\x00")
                json.loads(data_to_process)
                self._logger.debug("Plain JSON validation successful.")
                return data_to_process
            except json.JSONDecodeError as json_decode_err:
                self._logger.warning("Plain JSON validation failed: %s", json_decode_err, exc_info=True)
                return None

        self._logger.debug("UserComment string not recognized as Civitai JSON after processing.")
        return None

    def _process(self) -> None:  # Changed from parse() to _process()
        # self.status is managed by BaseFormat.parse()
        self._logger.info("Attempting to parse as %s.", self.tool)

        if not self._raw:  # _raw is the UserComment string for Civitai
            self._logger.warning("Raw UserComment data is empty for %s.", self.tool)
            self.status = self.Status.FORMAT_ERROR
            self._error = "Raw UserComment empty."
            return

        cleaned_workflow_json_str = self._decode_user_comment_for_civitai(self._raw)

        if not cleaned_workflow_json_str:
            self._logger.warning("Failed to decode UserComment or not Civitai JSON for %s.", self.tool)
            self.status = self.Status.FORMAT_ERROR
            if not self._error:  # _decode_user_comment_for_civitai might set it
                self._error = "UserComment decode/validation failed."
            return

        try:
            parsed_workflow_data = json.loads(cleaned_workflow_json_str)
            if not isinstance(parsed_workflow_data, dict):
                self._logger.error("Parsed UserComment workflow is not a dictionary for %s.", self.tool)
                self.status = self.Status.FORMAT_ERROR
                self._error = "Workflow data from UserComment is not a dict."
                return
            self.workflow_data = parsed_workflow_data  # Store the full workflow
            self._logger.info(
                "Successfully parsed main workflow JSON from UserComment for %s.",
                self.tool,
            )
        except json.JSONDecodeError as json_decode_err:
            self._logger.error(
                "Decoded UserComment is not valid JSON for %s: %s",
                self.tool,
                json_decode_err,
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Invalid JSON from UserComment: {json_decode_err}"
            return

        # --- Extract from 'extraMetadata' ---
        extra_metadata_str = self.workflow_data.get("extraMetadata")
        if not (extra_metadata_str and isinstance(extra_metadata_str, str)):
            self._logger.warning(
                "'extraMetadata' not found or not a string in workflow for %s.",
                self.tool,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "'extraMetadata' missing/invalid."
            return

        try:
            extra_meta_dict = json.loads(extra_metadata_str)
            if not isinstance(extra_meta_dict, dict):
                self._logger.error("'extraMetadata' content is not a dictionary for %s.", self.tool)
                self.status = self.Status.FORMAT_ERROR
                self._error = "'extraMetadata' content is not a dict."
                return
            self._logger.debug("'extraMetadata' parsed successfully for %s.", self.tool)

            # --- Positive and Negative Prompts ---
            self._positive = str(extra_meta_dict.get("prompt", "")).strip()
            self._negative = str(extra_meta_dict.get("negativePrompt", "")).strip()

            handled_keys_in_extra_meta = {"prompt", "negativePrompt"}

            # --- Populate Standard Parameters ---
            # Need to handle the dual keys for some params like cfg and sampler
            # For this, we can iterate CIVITAI_EXTRA_META_TO_PARAM_MAP or check keys individually.

            # Steps
            if self._populate_parameter("steps", extra_meta_dict.get("steps"), "steps"):
                handled_keys_in_extra_meta.add("steps")

            # CFG Scale
            cfg_val = extra_meta_dict.get("CFG scale", extra_meta_dict.get("cfgScale"))
            if self._populate_parameter("cfg_scale", cfg_val, "CFG scale/cfgScale"):
                handled_keys_in_extra_meta.add("CFG scale")
                handled_keys_in_extra_meta.add("cfgScale")

            # Sampler
            sampler_val = extra_meta_dict.get("sampler", extra_meta_dict.get("sampler_name"))
            if self._populate_parameter("sampler_name", sampler_val, "sampler/sampler_name"):
                handled_keys_in_extra_meta.add("sampler")
                handled_keys_in_extra_meta.add("sampler_name")

            # Seed
            if self._populate_parameter("seed", extra_meta_dict.get("seed"), "seed"):
                handled_keys_in_extra_meta.add("seed")

            # --- Handle Dimensions ---
            self._extract_and_set_dimensions(extra_meta_dict, "width", "height", handled_keys_in_extra_meta)

            # --- Build Settings String ---
            # Original code included all *other* keys from extra_meta_dict.
            self._setting = self._build_settings_string(
                include_standard_params=False,  # Standard params are in self.parameter
                custom_settings_dict=None,
                remaining_data_dict=extra_meta_dict,
                remaining_handled_keys=handled_keys_in_extra_meta,
                sort_parts=True,
            )

            # Update self._raw to be the cleaned workflow JSON string, as this is the "source"
            # The original Civitai format is essentially this workflow string.
            self._raw = cleaned_workflow_json_str

            self._logger.info(
                "Successfully extracted parameters from 'extraMetadata' for %s.",
                self.tool,
            )
            # self.status = self.Status.READ_SUCCESS # Let BaseFormat.parse() handle

        except json.JSONDecodeError as e_extra:
            self._logger.error(
                "Failed to parse JSON from 'extraMetadata' for %s: %s",
                self.tool,
                e_extra,
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Invalid 'extraMetadata' JSON: {e_extra}"
        # General exceptions are caught by BaseFormat.parse()
