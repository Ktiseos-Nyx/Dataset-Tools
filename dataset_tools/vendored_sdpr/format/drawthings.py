# dataset_tools/vendored_sdpr/format/drawthings.py

__author__ = "receyuki"
__filename__ = "drawthings.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"


from .base_format import BaseFormat

DRAWTHINGS_PARAM_MAP: dict[str, str | list[str]] = {
    "model": "model",
    "sampler": "sampler_name",
    "seed": "seed",
    "scale": "cfg_scale",
    "steps": "steps",
}


class DrawThings(BaseFormat):
    tool = "Draw Things"

    def _validate_info(self) -> bool:
        """Validates that self._info is present and is a dictionary."""
        if not self._info or not isinstance(self._info, dict):
            self._logger.warning("%s: Info data is empty or not a dictionary.", self.tool)
            self.status = self.Status.FORMAT_ERROR  # Set status here
            self._error = "Draw Things metadata (info dict) is missing or invalid."
            return False
        return True

    def _parse_info_data(self) -> None:
        """Parses the validated self._info dictionary to extract metadata."""
        # Assumes self._info has already been validated by _validate_info()
        data_json = self._info.copy()  # Work on a copy

        # --- Positive and Negative Prompts ---
        self._positive = data_json.pop("c", "").strip()
        self._negative = data_json.pop("uc", "").strip()

        handled_keys_for_settings = {"c", "uc"}

        # --- Populate Standard Parameters ---
        self._populate_parameters_from_map(
            data_json,
            DRAWTHINGS_PARAM_MAP,
            handled_keys_for_settings,
        )

        # --- Handle Dimensions from "size" string ---
        size_str = data_json.get("size", "0x0")
        if "size" in data_json:
            handled_keys_for_settings.add("size")

        parsed_w, parsed_h = "0", "0"
        if "x" in size_str:
            try:
                w_str, h_str = size_str.split("x", 1)
                parsed_w = str(int(w_str.strip()))
                parsed_h = str(int(h_str.strip()))
            except ValueError:
                self._logger.warning(
                    "Could not parse DrawThings Size '%s'. Using defaults.",
                    size_str,
                    exc_info=True,
                )

        if parsed_w != "0" or parsed_h != "0":
            self._width = parsed_w
            self._height = parsed_h

        if "width" in self._parameter and self._width != "0":
            self._parameter["width"] = self._width
        if "height" in self._parameter and self._height != "0":
            self._parameter["height"] = self._height

        if "size" in self._parameter:
            if self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"
            elif size_str != "0x0":
                self._parameter["size"] = size_str

        # --- Build Settings String ---
        self._setting = self._build_settings_string(
            include_standard_params=False,
            custom_settings_dict=None,
            remaining_data_dict=data_json,
            remaining_handled_keys=handled_keys_for_settings,
            sort_parts=True,
        )

        # --- Raw Data Population ---
        self._set_raw_from_info_if_empty()

    def _process(self) -> None:
        # self.status is managed by BaseFormat.parse() when exceptions occur or _process completes.
        self._logger.debug("Attempting to parse using %s logic.", self.tool)

        if not self._validate_info():
            # _validate_info already set status and error, so just return
            return

        try:
            self._parse_info_data()  # Call the new method for parsing

            # --- Final Status Check (after successful parsing attempt) ---
            if self._positive or self._parameter_has_data():
                self._logger.info("%s: Data parsed successfully.", self.tool)
                # Let BaseFormat.parse() set READ_SUCCESS upon no exceptions from _process
            else:
                self._logger.warning(
                    "%s: Parsing completed but no positive prompt or key parameters extracted.",
                    self.tool,
                )
                # If we reach here without an exception, but no data, it's a format error.
                # We need to ensure BaseFormat.parse() sees this.
                # One way is to set an error and status here, or raise a specific error.
                # For now, let's set status and error directly, as BaseFormat.parse()
                # only sets SUCCESS if _process completes without exception.
                self.status = self.Status.FORMAT_ERROR  # Explicitly set for this case
                self._error = f"{self.tool}: Key fields (prompt, parameters) not found after parsing."

        except KeyError as key_err:  # Should be less likely now with .pop/get defaults
            self._logger.error("%s: Missing key: %s", self.tool, key_err, exc_info=True)
            # Raise a ValueError to be caught by BaseFormat.parse() and set status to FAILURE
            raise ValueError(f"Draw Things JSON missing key: {key_err}") from key_err
        # Other specific exceptions from _parse_info_data (like ValueError from int conversion)
        # will also propagate to BaseFormat.parse() and be handled there.
