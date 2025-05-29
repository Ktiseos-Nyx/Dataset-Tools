# dataset_tools/vendored_sdpr/format/drawthings.py

__author__ = "receyuki"
__filename__ = "drawthings.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

# from ..format.base_format import BaseFormat # This should be:
from .base_format import BaseFormat

# from ..utility import remove_quotes # This should be:
from ..logger import Logger  # Import your vendored logger
from ..constants import PARAMETER_PLACEHOLDER  # Import placeholder


class DrawThings(BaseFormat):
    tool = "Draw Things"  # Tool name

    # Mapping from DrawThings JSON keys to BaseFormat.PARAMETER_KEY canonical names
    # DrawThings Key : Canonical Key
    PARAMETER_MAP = {
        "model": "model",
        "sampler": "sampler_name",  # DrawThings uses "sampler", canonical might be "sampler_name"
        "seed": "seed",
        "scale": "cfg_scale",  # DrawThings uses "scale", canonical is "cfg_scale"
        "steps": "steps",
        # "size" is handled by width/height parsing
        # Add other mappings as needed
    }
    # Original SETTING_KEY was ["model", "sampler", "seed", "scale", "steps", "size"]
    # This is less flexible than the map above.

    def __init__(self, info: dict = None, raw: str = ""):  # DrawThings doesn't get width/height from ImageDataReader
        super().__init__(info=info, raw=raw)  # Pass info (JSON data) and raw (can be empty)
        self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool.replace(' ', '_')}")
        self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER

    # `parse()` is inherited from BaseFormat, which calls `_process()`

    def _process(self):  # Called by BaseFormat.parse()
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")

        if not self._info or not isinstance(self._info, dict):
            self._logger.warn(f"{self.tool}: Info data is empty or not a dictionary.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "Draw Things metadata (info dict) is missing or invalid."
            return

        # The original _dt_format() logic is now in _process()
        data_json = self._info  # ImageDataReader passes the parsed JSON as self._info

        try:
            self._positive = str(data_json.pop("c", "")).strip()  # "c" is positive prompt
            self._negative = str(data_json.pop("uc", "")).strip()  # "uc" is negative prompt

            # Reconstruct raw string from essential parts for display/consistency
            # This self._raw will be what's shown in the "Raw Data" field by default
            temp_raw_parts = []
            if self._positive:
                temp_raw_parts.append(f"Positive: {self._positive}")
            if self._negative:
                temp_raw_parts.append(f"Negative: {self._negative}")
            # Add remaining items from data_json to raw string
            # temp_raw_parts.append(f"Other Settings: {json.dumps(data_json)}") # If using json for this part
            # For now, use the original approach of setting self._setting from remaining data_json

            # self._parameter is already initialized by BaseFormat
            # Populate self._parameter using PARAMETER_MAP
            for dt_key, canonical_key in self.PARAMETER_MAP.items():
                if dt_key in data_json and canonical_key in self._parameter:
                    self._parameter[canonical_key] = str(data_json.get(dt_key, self.PARAMETER_PLACEHOLDER))

            # Width and Height from "size"
            size_str = data_json.get("size", "0x0")  # Default if not present
            try:
                w_str, h_str = size_str.split("x")
                self._width = str(int(w_str.strip()))
                self._height = str(int(h_str.strip()))
                if "size" in self._parameter:  # If "size" is a canonical key
                    self._parameter["size"] = f"{self._width}x{self._height}"
            except ValueError:
                self._logger.warn(
                    f"Could not parse DrawThings Size '{size_str}'. Using defaults: {self._width}x{self._height}"
                )
                if "size" in self._parameter:  # Still populate with current (possibly PIL-derived) size
                    self._parameter["size"] = f"{self._width}x{self._height}"

            # Create a settings string from remaining items in data_json AFTER known items are popped/used
            # The original used remove_quotes(str(data_json).strip("{ }")) on the *remaining* data_json
            # Create a setting_dict from remaining items for clarity
            setting_dict_for_display = {}
            for key, value in data_json.items():
                if key not in ["c", "uc", "size"] + list(self.PARAMETER_MAP.keys()):  # Keys already handled
                    setting_dict_for_display[key.capitalize()] = str(value)

            self._setting = ", ".join([f"{k}: {v}" for k, v in sorted(setting_dict_for_display.items())])

            # Update self._raw to be more representative of what was parsed
            # The original self._raw was positive + negative + str(data_json AFTER POP).
            # Let's make it positive + negative + self._setting for clarity.
            # The full original JSON is in self._info if needed.
            self._raw = "\n".join(filter(None, [self._positive, self._negative, self._setting])).strip()

            # Basic check for success
            if self._positive or self._parameter.get("seed", self.PARAMETER_PLACEHOLDER) != self.PARAMETER_PLACEHOLDER:
                self._logger.info(f"{self.tool}: Data parsed successfully.")
                self.status = self.Status.READ_SUCCESS
            else:
                self._logger.warn(f"{self.tool}: Parsing completed but no positive prompt or seed extracted.")
                self.status = self.Status.FORMAT_ERROR
                self._error = f"{self.tool}: Key fields (prompt, seed) not found."

        except KeyError as ke:  # If essential keys like "c" or "uc" are missing
            self._logger.error(f"{self.tool}: Missing essential key in JSON data: {ke}")
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Draw Things JSON missing key: {ke}"
        except Exception as e:
            self._logger.error(f"{self.tool}: Unexpected error parsing Draw Things JSON: {e}", exc_info=True)
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Unexpected error: {e}"

    # The original _dt_format was merged into _process.
    # def _dt_format(self):
    #     pass # Now handled by _process
