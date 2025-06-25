# dataset_tools/vendored_sdpr/format/drawthings.py
import json

from .base_format import BaseFormat

DRAWTHINGS_PARAM_MAP: dict[str, str | list[str]] = {
    "model": "model",
    "sampler": "sampler_name",
    "seed": "seed",
    "scale": "cfg_scale",
    "steps": "steps",
    # "size" is handled separately
}


class DrawThings(BaseFormat):
    tool = "Draw Things"

    # _validate_info and _parse_info_data are effectively merged into _process

    def _process(self) -> None:
        self._logger.debug("[%s] Attempting to parse metadata.", self.tool)

        if not self._raw:
            self._logger.debug(
                "[%s] Raw data (expected from XMP exif:UserComment) is empty.",
                self.tool,
            )
            self.status = self.Status.FORMAT_DETECTION_ERROR  # Correct status
            self._error = "Raw data for Draw Things is empty."
            return

        try:
            # self._raw is the string content from XMP exif:UserComment
            data_json = json.loads(self._raw)
        except json.JSONDecodeError as e:
            self._logger.debug(
                "[%s] Raw data is not valid JSON. Not Draw Things. Error: %s",
                self.tool,
                e,
            )
            self.status = self.Status.FORMAT_DETECTION_ERROR  # Correct status
            self._error = f"Not Draw Things: data is not valid JSON ({e})"
            return

        if not isinstance(data_json, dict):
            self._logger.debug("[%s] Parsed data is not a dictionary. Not Draw Things.", self.tool)
            self.status = self.Status.FORMAT_DETECTION_ERROR  # Correct status
            self._error = "Not Draw Things: parsed data is not a dictionary."
            return

        # Add a more specific check for Draw Things content.
        # For example, presence of "c" (prompt) and "sampler" might be good indicators.
        # Or a specific "software" or "tool" key if Draw Things adds one to its JSON.
        # If Draw Things JSON *always* has a "c" (prompt) key:
        if "c" not in data_json and "sampler" not in data_json:  # Example check
            self._logger.debug(
                "[%s] Parsed JSON dictionary does not contain characteristic Draw Things keys (e.g., 'c', 'sampler').",
                self.tool,
            )
            self.status = self.Status.FORMAT_DETECTION_ERROR  # Correct status
            self._error = "Not Draw Things: JSON lacks characteristic keys."
            return

        # If we reach here, it's likely Draw Things JSON. Proceed with parsing.
        # self._info can be updated to this data_json if helper methods expect it there,
        # or helper methods can take data_json as an argument.
        # For now, let's assume helper methods will take data_json.

        # --- Positive and Negative Prompts ---
        self._positive = data_json.get("c", "").strip()  # DrawThings uses 'c' for positive
        self._negative = data_json.get("uc", "").strip()  # 'uc' for negative

        handled_keys_for_settings = {"c", "uc"}

        # --- Populate Standard Parameters ---
        self._populate_parameters_from_map(
            data_json,  # Pass the parsed JSON dict
            DRAWTHINGS_PARAM_MAP,
            handled_keys_for_settings,
        )

        # --- Handle Dimensions from "size" string ---
        size_str = str(data_json.get("size", "0x0"))  # Ensure it's a string
        if "size" in data_json:
            handled_keys_for_settings.add("size")

        # Use the _extract_and_set_dimensions_from_string helper from BaseFormat
        self._extract_and_set_dimensions_from_string(size_str, "size", handled_keys_set=handled_keys_for_settings)
        # This helper will set self._width, self._height and populate "width", "height", "size" in self._parameter

        # --- Build Settings String ---
        self._setting = self._build_settings_string(
            include_standard_params=False,  # Already handled by _populate_parameters_from_map
            custom_settings_dict=None,
            remaining_data_dict=data_json,  # Pass the parsed JSON dict
            remaining_handled_keys=handled_keys_for_settings,
            sort_parts=True,
        )

        # Raw data is already self._raw (the original JSON string)

        # --- Final Status Check ---
        if self._positive or self._parameter_has_data():
            self._logger.info("[%s] Data parsed successfully.", self.tool)
            # No need to set self.status = self.Status.READ_SUCCESS here;
            # BaseFormat.parse() will do it if _process completes without raising an exception
            # and status isn't already an error type.
        else:
            self._logger.warning(
                "[%s] Parsing completed but no positive prompt or key parameters extracted.",
                self.tool,
            )
            # This indicates that while it might be JSON, it didn't yield useful DrawThings data.
            self.status = (
                self.Status.FORMAT_ERROR
            )  # Or perhaps FORMAT_DETECTION_ERROR if it's more like "not our format"
            self._error = (
                f"{self.tool}: Key fields (prompt, parameters) not found after parsing supposed Draw Things JSON."
            )
