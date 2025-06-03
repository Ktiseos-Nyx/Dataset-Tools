# dataset_tools/vendored_sdpr/format/drawthings.py

__author__ = "receyuki"
__filename__ = "drawthings.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

# import logging # Not needed for type hinting if self._logger from BaseFormat

# from ..logger import get_logger # Not needed if self._logger from BaseFormat
from .base_format import BaseFormat

# from .utility import remove_quotes # Handled by _build_settings_string

# Parameter map from DrawThings keys to canonical keys
DRAWTHINGS_PARAM_MAP: dict[str, str | list[str]] = {
    "model": "model",
    "sampler": "sampler_name",
    "seed": "seed",
    "scale": "cfg_scale",
    "steps": "steps",
    # "c" (positive prompt) and "uc" (negative prompt) are handled directly.
    # "size" (dimensions) is handled specially.
}


class DrawThings(BaseFormat):
    tool = "Draw Things"

    # PARAMETER_MAP is effectively replaced by DRAWTHINGS_PARAM_MAP

    # __init__ is inherited from BaseFormat.
    # The logger is also inherited and named correctly by BaseFormat.
    # If a specific logger name was crucial (e.g., with self.tool.replace(' ', '_')),
    # __init__ would need to be overridden just for that.
    # The current BaseFormat logger name generation should be fine:
    # DSVendored_SDPR.format.drawthings.DrawThings

    def _process(self) -> None: self._validate_info()  # Extracted validation logic to a new method.
        # self.status is managed by BaseFormat.parse()
        self._logger.debug("Attempting to parse using %s logic.", self.tool)

        if not self._info or not isinstance(self._info, dict):
            self._logger.warning(
                "%s: Info data is empty or not a dictionary.", self.tool
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "Draw Things metadata (info dict) is missing or invalid."
            return

        data_json = self._info.copy()  # Work on a copy if we're popping keys

        try:
            # --- Positive and Negative Prompts ---
            # .pop() is used here, so these keys are removed from data_json
            self._positive = str(data_json.pop("c", "")).strip()
            self._negative = str(data_json.pop("uc", "")).strip()

            handled_keys_for_settings = {"c", "uc"}  # Keys already processed

            # --- Populate Standard Parameters ---
            # We use _populate_parameters_from_map on the (modified) data_json
            self._populate_parameters_from_map(
                data_json,
                DRAWTHINGS_PARAM_MAP,
                handled_keys_for_settings,  # This will mark keys from DRAWTHINGS_PARAM_MAP as handled
            )

            # --- Handle Dimensions from "size" string ---
            size_str = str(
                data_json.get("size", "0x0")
            )  # Use .get before marking as handled
            if "size" in data_json:  # Mark "size" as handled if it existed
                handled_keys_for_settings.add("size")

            parsed_w, parsed_h = "0", "0"
            if "x" in size_str:
                try:
                    w_str, h_str = size_str.split("x", 1)
                    parsed_w = str(int(w_str.strip()))
                    parsed_h = str(int(h_str.strip()))
                except ValueError:
                    self._logger.warning(
                        "Could not parse DrawThings Size '%s'. Using defaults: %sx%s",
                        size_str,
                        self._width,
                        self._height,  # Log current self._width/_height as defaults
                        exc_info=True,  # Helpful for unexpected format
                    )
                    # If parsing fails, self._width and self._height retain their initial values (often "0")
                    # or values passed to __init__.
                    # No explicit assignment to self._width/_height here if parsing fails.

            # Update internal dimensions and parameters only if parsing was successful
            if parsed_w != "0" or parsed_h != "0":  # Check if we got valid numbers
                self._width = parsed_w
                self._height = parsed_h

            # Update parameters "width", "height", "size" using current self._width, self._height
            # This ensures consistency even if parsing size_str failed and we use defaults.
            if "width" in self._parameter and self._width != "0":
                self._parameter["width"] = self._width
            if "height" in self._parameter and self._height != "0":
                self._parameter["height"] = self._height
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"
            elif (
                "size" in self._parameter and size_str != "0x0"
            ):  # If we couldn't parse but original size_str was non-default
                self._parameter["size"] = (
                    size_str  # Store original "size" string if it was valid-looking
                )

            # --- Build Settings String ---
            # Original code added all *other* keys from data_json.
            # data_json has had "c", "uc" popped, and keys from DRAWTHINGS_PARAM_MAP
            # and "size" were added to handled_keys_for_settings.
            self._setting = self._build_settings_string(
                include_standard_params=False,  # Standard params are in self.parameter
                custom_settings_dict=None,
                remaining_data_dict=data_json,  # Use the modified data_json
                remaining_handled_keys=handled_keys_for_settings,
                # remaining_key_formatter=lambda k: k.capitalize(), # Original used .capitalize()
                sort_parts=True,
            )
            # Note: _build_settings_string uses self._format_key_for_display (snake_case to Title Case)
            # The original `key.capitalize()` is slightly different. If exact match is needed,
            # pass a custom formatter lambda k: k.capitalize(). For most keys, it's similar.

            # --- Raw Data Population ---
            self._set_raw_from_info_if_empty()  # If self._raw wasn't set, use original self._info

            # --- Final Status Check ---
            if self._positive or self._parameter_has_data():
                self._logger.info("%s: Data parsed successfully.", self.tool)
                # self.status = self.Status.READ_SUCCESS # Let BaseFormat.parse() handle
            else:
                self._logger.warning(
                    "%s: Parsing completed but no positive prompt or seed extracted.",
                    self.tool,
                )
                if self.status != self.Status.FORMAT_ERROR:
                    self.status = self.Status.FORMAT_ERROR
                    self._error = f"{self.tool}: Key fields (prompt, seed) not found."

        except (
            KeyError
        ) as key_err:  # Should be less likely with .pop("key", default) and .get()
            self._logger.error(
                "%s: Missing essential key in JSON data: %s",
                self.tool,
                key_err,
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Draw Things JSON missing key: {key_err}"
        # General exceptions are caught by BaseFormat.parse()
