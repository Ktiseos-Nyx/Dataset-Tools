# dataset_tools/vendored_sdpr/format/base_format.py

__author__ = "receyuki"  # Original author
__filename__ = "base_format.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
import logging  # Standard Python logging
from collections.abc import Callable
from enum import Enum
from typing import Any

from ..constants import PARAMETER_PLACEHOLDER
from ..logger import get_logger


# pylint: disable=too-many-instance-attributes
class BaseFormat:
    PARAMETER_KEY: list[str] = [
        "model",
        "model_hash",
        "sampler_name",
        "seed",
        "subseed",
        "subseed_strength",
        "cfg_scale",
        "steps",
        "size",
        "width",
        "height",
        "scheduler",
        "loras",
        "hires_fix",
        "hires_upscaler",
        "denoising_strength",
        "restore_faces",
        "version",
        "clip_skip",
        "vae_model",
        "refiner_model",
        "refiner_switch_at",
    ]

    DEFAULT_PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER

    class Status(Enum):
        UNREAD = 1
        READ_SUCCESS = 2
        FORMAT_ERROR = 3
        COMFYUI_ERROR = 4

    def __init__(
        self,
        info: dict[str, Any] | None = None,
        raw: str = "",
        width: int = 0,
        height: int = 0,
    ):
        self._width = str(width)
        self._height = str(height)
        self._info: dict[str, Any] = info if info is not None else {}
        self._raw = str(raw)

        self._positive = ""
        self._negative = ""
        self._positive_sdxl: dict[str, Any] = {}
        self._negative_sdxl: dict[str, Any] = {}
        self._setting = ""

        self._parameter: dict[str, Any] = dict.fromkeys(
            BaseFormat.PARAMETER_KEY,
            BaseFormat.DEFAULT_PARAMETER_PLACEHOLDER,
        )
        if width != 0 and "width" in self._parameter:
            self._parameter["width"] = str(width)
        if height != 0 and "height" in self._parameter:
            self._parameter["height"] = str(height)
        if width != 0 and height != 0 and "size" in self._parameter:
            self._parameter["size"] = f"{width}x{height}"

        self._is_sdxl = False
        self._status = self.Status.UNREAD
        self._error = ""

        logger_name = (
            f"DSVendored_SDPR.{self.__class__.__module__}.{self.__class__.__name__}"
        )
        if self.__class__ == BaseFormat:
            logger_name = "DSVendored_SDPR.Format.Base"

        self._logger: logging.Logger = get_logger(logger_name)
        self.tool = getattr(self.__class__, "tool", "Unknown")

    # --- Core Parsing Logic ---
    def parse(self) -> Status:
        if self._status == self.Status.READ_SUCCESS:
            return self._status

        self._status = self.Status.UNREAD
        self._error = ""

        try:
            self._process()
            if self._status == self.Status.UNREAD:
                if (
                    not self._positive
                    and not self._negative
                    and not self._setting
                    and not self._parameter_has_data()
                    and self._width == "0"
                    and self._height == "0"
                ):
                    self._logger.debug(
                        "%s._process completed but no data extracted. Assuming format mismatch.",
                        self.tool,
                    )
                    self.status = self.Status.FORMAT_ERROR
                    self._error = f"{self.tool}: No usable data extracted."
                else:
                    self.status = self.Status.READ_SUCCESS
        except ValueError as val_err:
            self._logger.error(
                "ValueError during %s parsing: %s", self.tool, val_err, exc_info=True
            )
            self._status = self.Status.FORMAT_ERROR
            self._error = str(val_err)
        except Exception as general_err:  # pylint: disable=broad-except
            self._logger.error(
                "Unexpected exception during %s _process: %s",
                self.tool,
                general_err,
                exc_info=True,
            )
            self._status = self.Status.FORMAT_ERROR
            self._error = f"Unexpected error: {general_err}"
        return self._status

    def _process(self):
        """Subclasses must implement their specific parsing logic here."""
        self._logger.debug(
            "BaseFormat._process called for tool %s. Subclass should implement parsing.",
            self.tool,
        )
        self.status = self.Status.FORMAT_ERROR
        self._error = f"{self.tool} parser's _process method not implemented."
        # Removed unnecessary pass statement here

    def _parameter_has_data(self) -> bool:
        """Checks if any parameter has been populated beyond the placeholder."""
        for value in self._parameter.values():
            if value != self.DEFAULT_PARAMETER_PLACEHOLDER:
                return True
        return False

    # --- Parameter Population Helpers ---
    def _populate_parameter(
        self,
        target_param_key_or_list: str | list[str],
        value: Any,
        source_key_for_debug: str = "unknown_source",
    ) -> bool:
        if value is not None:
            target_keys = (
                [target_param_key_or_list]
                if isinstance(target_param_key_or_list, str)
                else target_param_key_or_list
            )

            for target_key in target_keys:
                if target_key in self._parameter:
                    self._parameter[target_key] = str(value)
                    if target_key == "width":
                        self._width = str(value)
                    elif target_key == "height":
                        self._height = str(value)
                    return True
            self._logger.debug(
                "Key(s) '%s' for source '%s' not in self.PARAMETER_KEY or not applicable for %s. Value '%s' not assigned to standard params.",
                target_keys,
                source_key_for_debug,
                self.tool,
                value,
            )
        return False

    def _populate_parameters_from_map(
        self,
        data_dict: dict[str, Any],
        parameter_map: dict[str, str | list[str]],
        handled_keys_set: set[str] | None = None,
        value_processor: Callable[[Any], Any] | None = None,
    ):
        for source_key, target_param_keys in parameter_map.items():
            if source_key in data_dict:
                raw_value = data_dict[source_key]
                processed_value = (
                    value_processor(raw_value) if value_processor else raw_value
                )

                if self._populate_parameter(
                    target_param_keys,
                    processed_value,
                    source_key_for_debug=source_key,
                ):
                    if handled_keys_set is not None:
                        handled_keys_set.add(source_key)

    def _assign_param_or_add_to_custom_settings(
        self,
        data_dict: dict[str, Any],
        source_key: str,
        param_target_keys: str | list[str],
        custom_settings_dict: dict[str, str],
        custom_settings_display_key: str,
        handled_keys_set: set[str] | None = None,
        value_processor: Callable[[Any], Any] | None = None,
    ):
        value_from_dict = data_dict.get(source_key)
        if value_from_dict is not None:
            processed_value = (
                value_processor(value_from_dict) if value_processor else value_from_dict
            )

            populated_standard = self._populate_parameter(
                param_target_keys, processed_value, source_key_for_debug=source_key
            )

            if not populated_standard:
                custom_settings_dict[custom_settings_display_key] = str(processed_value)

            if handled_keys_set is not None:
                handled_keys_set.add(source_key)

    def _add_to_custom_settings(
        self,
        data_dict: dict[str, Any],
        source_key: str,
        custom_settings_dict: dict[str, str],
        custom_settings_display_key: str,
        handled_keys_set: set[str] | None = None,
        value_processor: Callable[[Any], Any] | None = None,
    ):
        value_from_dict = data_dict.get(source_key)
        if value_from_dict is not None:
            processed_value = (
                value_processor(value_from_dict) if value_processor else value_from_dict
            )
            custom_settings_dict[custom_settings_display_key] = str(processed_value)
            if handled_keys_set is not None:
                handled_keys_set.add(source_key)

    def _extract_and_set_dimensions(
        self,
        data_dict: dict[str, Any],
        width_source_key: str,
        height_source_key: str,
        handled_keys_set: set[str] | None = None,
    ):
        width_val = data_dict.get(width_source_key)
        height_val = data_dict.get(height_source_key)

        if width_val is not None:
            self._width = str(width_val)
            if self._populate_parameter("width", width_val, width_source_key):
                pass
            if handled_keys_set is not None:
                handled_keys_set.add(width_source_key)

        if height_val is not None:
            self._height = str(height_val)
            if self._populate_parameter("height", height_val, height_source_key):
                pass
            if handled_keys_set is not None:
                handled_keys_set.add(height_source_key)

        current_w = self._parameter.get("width", self._width)
        current_h = self._parameter.get("height", self._height)

        if (
            current_w != self.DEFAULT_PARAMETER_PLACEHOLDER
            and current_w != "0"
            and current_h != self.DEFAULT_PARAMETER_PLACEHOLDER
            and current_h != "0"
        ):
            if "size" in self._parameter:
                self._parameter["size"] = f"{current_w}x{current_h}"
        elif self._width != "0" and self._height != "0" and "size" in self._parameter:
            self._parameter["size"] = f"{self._width}x{self._height}"

    # --- Settings String Construction Helper ---
    @staticmethod
    def _format_key_for_display(key: str) -> str:
        return key.replace("_", " ").capitalize()

    @staticmethod
    def _remove_quotes_from_string(text: Any) -> str:
        text_str = str(text)
        if len(text_str) >= 2:
            if text_str.startswith('"') and text_str.endswith('"'):
                return text_str[1:-1]
            if text_str.startswith("'") and text_str.endswith("'"):
                return text_str[1:-1]
        return text_str

    def _build_settings_string(
        self,
        custom_settings_dict: dict[str, str] | None = None,
        remaining_data_dict: dict[str, Any] | None = None,
        remaining_handled_keys: set[str] | None = None,
        remaining_key_formatter: Callable[[str], str] | None = None,
        remaining_value_processor: Callable[[Any], str] | None = None,
        include_standard_params: bool = True,
        sort_parts: bool = True,
    ) -> str:
        setting_parts = []

        if include_standard_params:
            for key in self.PARAMETER_KEY:
                value = self._parameter.get(key)
                if value is not None and value != self.DEFAULT_PARAMETER_PLACEHOLDER:
                    display_key = self._format_key_for_display(key)
                    setting_parts.append(
                        f"{display_key}: {self._remove_quotes_from_string(value)}"
                    )

        if custom_settings_dict:
            for key, value in custom_settings_dict.items():
                setting_parts.append(f"{key}: {self._remove_quotes_from_string(value)}")

        if remaining_data_dict:
            processed_remaining_handled_keys = remaining_handled_keys or set()
            key_formatter = remaining_key_formatter or self._format_key_for_display
            value_processor = (
                remaining_value_processor or self._remove_quotes_from_string
            )

            for key, value in remaining_data_dict.items():
                if key not in processed_remaining_handled_keys:
                    if value is None or (isinstance(value, str) and not value.strip()):
                        continue
                    display_key = key_formatter(key)
                    processed_value = value_processor(value)
                    setting_parts.append(f"{display_key}: {processed_value}")

        if sort_parts:
            setting_parts.sort()

        return ", ".join(setting_parts)

    # --- Other Utility Helpers ---
    def _set_raw_from_info_if_empty(self):
        if not self._raw and self._info:
            try:
                self._raw = json.dumps(self._info)
            except TypeError:
                self._logger.warning(
                    "Could not serialize self._info to JSON for %s. Using str().",
                    self.tool,
                    exc_info=True,
                )
                self._raw = str(self._info)

    # --- Properties ---
    @property
    def height(self) -> str:
        param_h = self._parameter.get("height", self.DEFAULT_PARAMETER_PLACEHOLDER)
        return (
            param_h if param_h != self.DEFAULT_PARAMETER_PLACEHOLDER else self._height
        )

    @property
    def width(self) -> str:
        param_w = self._parameter.get("width", self.DEFAULT_PARAMETER_PLACEHOLDER)
        return param_w if param_w != self.DEFAULT_PARAMETER_PLACEHOLDER else self._width

    @property
    def info(self) -> dict[str, Any]:
        return self._info

    @property
    def positive(self) -> str:
        return self._positive

    @property
    def negative(self) -> str:
        return self._negative

    @property
    def positive_sdxl(self) -> dict[str, Any]:
        return self._positive_sdxl

    @property
    def negative_sdxl(self) -> dict[str, Any]:
        return self._negative_sdxl

    @property
    def setting(self) -> str:
        return self._setting

    @property
    def raw(self) -> str:
        return self._raw

    @property
    def parameter(self) -> dict[str, Any]:
        return self._parameter

    @property
    def is_sdxl(self) -> bool:
        return self._is_sdxl

    @property
    def status(self) -> Status:
        return self._status

    @status.setter
    def status(self, value: Status):
        if isinstance(value, self.Status):
            self._status = value
        else:
            self._logger.warning(
                "Attempted to set invalid status type: %s. Expected BaseFormat.Status Enum.",
                type(value),
            )

    @property
    def error(self) -> str:
        return self._error

    @property
    def props(self) -> str:
        properties = {
            "positive": self.positive,
            "negative": self.negative,
            "positive_sdxl": self.positive_sdxl,
            "negative_sdxl": self.negative_sdxl,
            "is_sdxl": self.is_sdxl,
            **self.parameter,
            "setting_string": self.setting,
            "tool_detected": self.tool,
            "raw_metadata_if_any": (
                self.raw[:500] + "..." if len(self.raw) > 500 else self.raw
            ),
            "status": self.status.name,
            "error_message": self.error,
        }
        props_params_cleaned = {
            k: v
            for k, v in self.parameter.items()
            if v != self.DEFAULT_PARAMETER_PLACEHOLDER
        }
        properties.update(props_params_cleaned)
        if "width" not in props_params_cleaned:
            properties["width"] = self.width
        if "height" not in props_params_cleaned:
            properties["height"] = self.height

        try:
            return json.dumps(properties, indent=2)
        except TypeError:
            safe_properties = {}
            for k, v in properties.items():
                try:
                    json.dumps({k: v})
                    safe_properties[k] = v
                except TypeError:
                    safe_properties[k] = str(v)
            return json.dumps(safe_properties, indent=2)
