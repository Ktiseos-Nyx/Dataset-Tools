# dataset_tools/vendored_sdpr/format/base_format.py

__author__ = "receyuki"  # Original author
__filename__ = "base_format.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki; Modified 2025, Ktiseos Nyx"
__email__ = "receyuki@gmail.com; your_email@example.com"

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any  # Changed from typing.Any to typing.Dict for explicit Dict type hint

from ..constants import PARAMETER_PLACEHOLDER
from ..logger import get_logger


@dataclass
class RemainingDataConfig:
    """Configuration for processing remaining data in _build_settings_string."""

    data_dict: dict[str, Any] | None = None  # Use Dict
    handled_keys: set[str] | None = None
    key_formatter: Callable[[str], str] | None = None
    value_processor: Callable[[Any], str] | None = None


# pylint: disable=too-many-instance-attributes
class BaseFormat:
    # Define common parameter keys that parsers might try to populate.
    # Subclasses can override or extend this if they have a very different core set.
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
        # Keys added from various parsers
        "tool_version",
        "yodayo_ngms",
        "model_internal_id",
        "civitai_resources_data",
        "civitai_metadata",
        "civitai_workflowId_from_extra",
        "civitai_resources_from_extra",  # From Civitai ComfyUI JSON path
        "date",
        "upscaler",
        "mochi_ml_compute_unit",
        "tool_version_detail",
        "loras_from_prompt_positive",
        "loras_from_prompt_negative",
        "lora_hashes_data",
        "aesthetic_score",  # From A1111 JSON example
        "a1111_token_merging_ratio",
        "a1111_token_merging_ratio_hr",
        "a1111_ultimate_sd_upscaler",
        # Add other potential standardized keys here
    ]

    DEFAULT_PARAMETER_PLACEHOLDER: str = PARAMETER_PLACEHOLDER
    tool: str = "Unknown Base"  # Class variable for default tool name

    class Status(Enum):
        UNREAD = 1
        READ_SUCCESS = 2
        FORMAT_ERROR = 3  # General parsing error for the expected format
        COMFYUI_ERROR = 4  # Specific errors from ComfyUI parsing
        MISSING_INFO = 5  # Required info/raw data not provided to parser
        FORMAT_DETECTION_ERROR = 6  # Parser determined the data is not for it
        # PARTIAL_SUCCESS = 7   # Optional: if partial data extraction is considered a state

    def __init__(
        self,
        info: dict[str, Any] | None = None,
        raw: str = "",
        width: Any = 0,
        height: Any = 0,
        logger_obj: logging.Logger | None = None,
        **kwargs: Any,
    ):
        # Initialize core attributes
        self._info: dict[str, Any] = info.copy() if info is not None else {}
        self._raw: str = str(raw)

        try:  # Robust width/height conversion
            self._width: str = str(int(width)) if width and str(width).strip().isdigit() and int(width) > 0 else "0"
        except (ValueError, TypeError):
            self._width: str = "0"
        try:
            self._height: str = (
                str(int(height)) if height and str(height).strip().isdigit() and int(height) > 0 else "0"
            )
        except (ValueError, TypeError):
            self._height: str = "0"

        self.status: BaseFormat.Status = self.Status.UNREAD
        self._error: str = ""

        # Tool name: Use class variable 'tool' if defined by subclass, else BaseFormat's default
        self.tool: str = getattr(self.__class__, "tool", BaseFormat.tool)

        # Logger setup
        if logger_obj:
            self._logger: logging.Logger = logger_obj
        else:
            logger_name_suffix = self.__class__.__name__
            if logger_name_suffix == "BaseFormat":
                logger_name_suffix = "UnknownParserType"
            self._logger = get_logger(f"DSVendored_SDPR.Format.{logger_name_suffix}")

        # Initialize prompt, settings, and SDXL specific attributes
        self._positive: str = ""
        self._negative: str = ""
        self._setting: str = ""
        self._is_sdxl: bool = False
        self._positive_sdxl: dict[str, Any] = {}
        self._negative_sdxl: dict[str, Any] = {}

        # Initialize _parameter dictionary using PARAMETER_KEY
        # Access PARAMETER_KEY via self.__class__ to get it from the actual subclass
        param_keys_to_init = getattr(self.__class__, "PARAMETER_KEY", [])
        self._parameter: dict[str, Any] = {key: self.DEFAULT_PARAMETER_PLACEHOLDER for key in param_keys_to_init}

        # Populate width, height, size in parameters if they are defined keys
        if "width" in self._parameter:
            self._parameter["width"] = self._width
        if "height" in self._parameter:
            self._parameter["height"] = self._height
        if "size" in self._parameter:
            if self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"
            # else, it remains placeholder if width/height are 0

        # Log any kwargs that were not explicitly handled by this __init__
        # These are kwargs beyond 'info', 'raw', 'width', 'height', 'logger_obj'
        if kwargs:  # Check if kwargs dictionary is not empty
            self._logger.debug(
                "%s __init__ received unhandled kwargs: %s. These should be consumed by subclass or are unexpected.",
                self.__class__.__name__,
                list(kwargs.keys()),
            )

    def parse(self) -> Status:
        if self._status == self.Status.READ_SUCCESS:
            return self._status  # Already successfully parsed

        # Reset status for a fresh parse attempt (if re-parsing is allowed/intended)
        # self.status = self.Status.UNREAD # Or handle this in ImageDataReader
        self._error = ""  # Clear previous error

        try:
            self._process()  # Call subclass-specific parsing logic

            # If _process didn't explicitly set a status (e.g., to FAILURE or DETECTION_ERROR)
            if self.status == self.Status.UNREAD:
                # Check if any meaningful data was extracted
                if (
                    not self._positive
                    and not self._negative
                    and not self._setting
                    and not self._parameter_has_data()
                    and self._width == "0"
                    and self._height == "0"
                    and not self._is_sdxl
                ):
                    self._logger.debug(
                        "%s: _process completed but no meaningful data extracted. Setting to FORMAT_DETECTION_ERROR.",
                        self.tool,
                    )
                    self.status = self.Status.FORMAT_DETECTION_ERROR  # More appropriate than FORMAT_ERROR
                    self._error = f"{self.tool}: No usable data extracted after parsing."
                else:
                    # Some data was extracted, or _process implies success by not failing
                    self.status = self.Status.READ_SUCCESS
                    self._logger.info(
                        "%s: Data parsed successfully (status set by BaseFormat).",
                        self.tool,
                    )
            elif self.status == self.Status.READ_SUCCESS:
                self._logger.info("%s: Data parsed successfully (status set by _process).", self.tool)

        except self.NotApplicableError as e_na:  # Custom exception from BaseModelParser or here
            self._status = self.Status.FORMAT_DETECTION_ERROR
            self._error = str(e_na) or f"{self.tool}: Parser not applicable for this data."
            self._logger.debug("%s: %s", self.tool, self._error)
        except ValueError as val_err:  # Includes GGUFReadError etc. if they inherit
            self._logger.error("ValueError during %s parsing: %s", self.tool, val_err, exc_info=True)
            self._status = self.Status.FORMAT_ERROR
            self._error = str(val_err)
        except Exception as general_err:
            self._logger.error(
                "Unexpected exception during %s _process: %s",
                self.tool,
                general_err,
                exc_info=True,
            )
            self._status = self.Status.FORMAT_ERROR
            self._error = f"Unexpected error in {self.tool}: {general_err!s}"
        return self._status

    def _process(self):
        """Subclasses MUST implement their specific parsing logic here."""
        self._logger.warning(
            "BaseFormat._process called directly for tool %s. Subclass should implement its own _process method.",
            self.tool,
        )
        # Default to FORMAT_DETECTION_ERROR if not implemented, so ImageDataReader tries next.
        self.status = self.Status.FORMAT_DETECTION_ERROR
        self._error = f"{self.tool} parser's _process method not implemented."
        raise NotImplementedError(f"{self.__class__.__name__} must implement _process method.")

    def _parameter_has_data(self) -> bool:
        if not self._parameter:
            return False
        for value in self._parameter.values():
            if value != self.DEFAULT_PARAMETER_PLACEHOLDER:
                return True
        return False

    def _populate_parameter(
        self,
        target_param_key_or_list: str | list[str],
        value: Any,
        source_key_for_debug: str = "unknown_source",
    ) -> bool:
        if value is None:
            return False  # Do not populate None

        target_keys = (
            [target_param_key_or_list] if isinstance(target_param_key_or_list, str) else target_param_key_or_list
        )
        value_str = str(value)  # Ensure value is string for storage in _parameter
        populated_any = False

        for target_key in target_keys:
            if target_key in self._parameter:
                self._parameter[target_key] = value_str
                # Update width/height attributes if these specific parameters are set
                if target_key == "width":
                    self._width = value_str
                elif target_key == "height":
                    self._height = value_str
                populated_any = True
            else:
                self._logger.debug(
                    "Target key '%s' for source '%s' not in self.PARAMETER_KEY. Value '%s' not assigned.",
                    target_key,
                    source_key_for_debug,
                    self.tool,
                    value_str,
                )
        return populated_any

    def _populate_parameters_from_map(
        self,
        data_dict: dict[str, Any],
        parameter_map: dict[str, str | list[str]],
        handled_keys_set: set[str] | None = None,
        value_processor: Callable[[Any], Any] | None = None,
    ):
        if handled_keys_set is None:
            handled_keys_set = set()  # Ensure it's a set

        for source_key, target_param_keys in parameter_map.items():
            if source_key in data_dict:
                raw_value = data_dict[source_key]
                processed_value = value_processor(raw_value) if value_processor else raw_value
                if self._populate_parameter(target_param_keys, processed_value, source_key_for_debug=source_key):
                    handled_keys_set.add(source_key)

    def _extract_and_set_dimensions(
        self,
        data_dict: dict[str, Any],
        width_source_key: str,
        height_source_key: str,
        handled_keys_set: set[str] | None = None,
    ):
        if handled_keys_set is None:
            handled_keys_set = set()

        width_val = data_dict.get(width_source_key)
        height_val = data_dict.get(height_source_key)

        # Process width
        if width_val is not None:
            width_val_str = str(width_val).strip()
            if width_val_str and width_val_str != "0":  # Check if not empty or "0"
                self._width = width_val_str
                self._populate_parameter("width", width_val_str, width_source_key)
                handled_keys_set.add(width_source_key)

        # Process height
        if height_val is not None:
            height_val_str = str(height_val).strip()
            if height_val_str and height_val_str != "0":
                self._height = height_val_str
                self._populate_parameter("height", height_val_str, height_source_key)
                handled_keys_set.add(height_source_key)

        # Update "size" parameter if both width and height are validly set
        if self._width != "0" and self._height != "0" and "size" in self._parameter:
            self._parameter["size"] = f"{self._width}x{self._height}"

    def _extract_and_set_dimensions_from_string(
        self,
        size_str: str,
        source_key_for_debug: str,
        data_dict_for_handled_keys: (dict[str, Any] | None) = None,  # Unused here, but for consistency
        handled_keys_set: set[str] | None = None,
    ):
        if handled_keys_set is None:
            handled_keys_set = set()

        size_str = str(size_str).strip()
        if not size_str:
            return

        parts = size_str.lower().split("x")
        if len(parts) == 2:
            w_str, h_str = parts[0].strip(), parts[1].strip()
            if w_str.isdigit() and h_str.isdigit():
                w_int, h_int = int(w_str), int(h_str)
                if w_int > 0 and h_int > 0:
                    self._width = w_str
                    self._height = h_str
                    self._populate_parameter("width", w_str, f"{source_key_for_debug} (width part)")
                    self._populate_parameter("height", h_str, f"{source_key_for_debug} (height part)")
                    if "size" in self._parameter:
                        self._parameter["size"] = size_str  # Use original valid size string
                    handled_keys_set.add(source_key_for_debug)  # Mark original "Size" key as handled
                    return
        self._logger.debug(
            "Could not parse valid width/height from size string '%s' for key '%s'",
            size_str,
            source_key_for_debug,
        )

    @staticmethod
    def _format_key_for_display(key: str) -> str:
        return key.replace("_", " ").capitalize()

    @staticmethod
    def _remove_quotes_from_string(text: Any) -> str:
        text_str = str(text).strip()
        if len(text_str) >= 2:
            if (text_str.startswith('"') and text_str.endswith('"')) or (
                text_str.startswith("'") and text_str.endswith("'")
            ):
                return text_str[1:-1]
        return text_str

    def _build_settings_string(
        self,
        custom_settings_dict: dict[str, str] | None = None,
        remaining_config_obj: RemainingDataConfig | None = None,
        # Deprecated individual remaining_data args, use remaining_config_obj instead
        remaining_data_dict: dict[str, Any] | None = None,
        remaining_handled_keys: set[str] | None = None,
        remaining_key_formatter: Callable[[str], str] | None = None,
        remaining_value_processor: Callable[[Any], str] | None = None,
        include_standard_params: bool = True,
        sort_parts: bool = True,
        kv_separator: str = ": ",
        pair_separator: str = ", ",
    ) -> str:
        setting_parts: list[str] = []

        if include_standard_params:
            for key in self.PARAMETER_KEY:  # Iterate in defined order
                value = self._parameter.get(key)
                if value is not None and value != self.DEFAULT_PARAMETER_PLACEHOLDER:
                    # Skip width/height/size if they are handled separately or part of "Size"
                    if (
                        key in ["width", "height"]
                        and self._parameter.get("size", self.DEFAULT_PARAMETER_PLACEHOLDER)
                        != self.DEFAULT_PARAMETER_PLACEHOLDER
                    ):
                        continue
                    if key == "size" and (
                        self._width != "0" and self._height != "0"
                    ):  # Already handled by width/height if they are primary
                        display_key = self._format_key_for_display(key)
                        setting_parts.append(f"{display_key}{kv_separator}{self._remove_quotes_from_string(value)}")
                        continue  # Ensure size is added if it has a value

                    display_key = self._format_key_for_display(key)
                    setting_parts.append(f"{display_key}{kv_separator}{self._remove_quotes_from_string(value)}")

        if custom_settings_dict:
            items_to_sort = list(custom_settings_dict.items())
            if sort_parts:
                items_to_sort.sort()
            for key, value in items_to_sort:
                setting_parts.append(f"{key}{kv_separator}{self._remove_quotes_from_string(value)}")

        # Handle remaining_config_obj as primary for remaining data
        current_remaining_config = remaining_config_obj
        if not current_remaining_config and remaining_data_dict:  # Fallback to individual args
            current_remaining_config = RemainingDataConfig(
                data_dict=remaining_data_dict,
                handled_keys=remaining_handled_keys,
                key_formatter=remaining_key_formatter or self._format_key_for_display,
                value_processor=remaining_value_processor or self._remove_quotes_from_string,
            )

        if current_remaining_config and current_remaining_config.data_dict:
            key_formatter = current_remaining_config.key_formatter or self._format_key_for_display
            value_processor = current_remaining_config.value_processor or self._remove_quotes_from_string
            r_handled_keys = current_remaining_config.handled_keys or set()

            items_to_sort_remaining = []
            for key, value in current_remaining_config.data_dict.items():
                if key not in r_handled_keys:
                    if value is None or (isinstance(value, str) and not value.strip()):
                        continue
                    items_to_sort_remaining.append((key_formatter(key), value_processor(value)))

            if sort_parts:
                items_to_sort_remaining.sort()
            for disp_key, proc_val in items_to_sort_remaining:
                setting_parts.append(f"{disp_key}{kv_separator}{proc_val}")

        # Filter out any empty parts that might have resulted from processing
        final_parts = [part for part in setting_parts if part.split(kv_separator, 1)[1].strip()]
        return pair_separator.join(final_parts)

    def _set_raw_from_info_if_empty(self):
        """Sets self._raw from self._info (as JSON or str) if self._raw is currently empty."""
        if not self._raw and self._info:
            try:
                self._raw = json.dumps(self._info)  # Attempt to serialize info as JSON
            except TypeError:  # If self._info is not JSON serializable
                self._logger.warning(
                    "Could not serialize self._info to JSON for tool %s. Using str(self._info) as fallback for raw data.",
                    self.tool,
                    exc_info=self._logger.level <= logging.DEBUG,  # More detail on debug
                )
                self._raw = str(self._info)  # Fallback to string representation

    class NotApplicableError(Exception):  # Moved from BaseModelParser, if this is the true base
        """Custom exception to indicate a parser is not suitable for a given file."""

        pass

    # --- Properties ---
    @property
    def height(self) -> str:
        # Prioritize self._parameter["height"] if set and valid, then self._height
        param_h = self._parameter.get("height", self.DEFAULT_PARAMETER_PLACEHOLDER)
        if param_h != self.DEFAULT_PARAMETER_PLACEHOLDER and param_h != "0":
            return param_h
        return self._height if self._height != "0" else self.DEFAULT_PARAMETER_PLACEHOLDER

    @property
    def width(self) -> str:
        param_w = self._parameter.get("width", self.DEFAULT_PARAMETER_PLACEHOLDER)
        if param_w != self.DEFAULT_PARAMETER_PLACEHOLDER and param_w != "0":
            return param_w
        return self._width if self._width != "0" else self.DEFAULT_PARAMETER_PLACEHOLDER

    @property
    def info(self) -> dict[str, Any]:
        return self._info.copy()

    @property
    def positive(self) -> str:
        return self._positive

    @property
    def negative(self) -> str:
        return self._negative

    @property
    def positive_sdxl(self) -> dict[str, Any]:
        return self._positive_sdxl.copy()  # Return copy

    @property
    def negative_sdxl(self) -> dict[str, Any]:
        return self._negative_sdxl.copy()  # Return copy

    @property
    def setting(self) -> str:
        return self._setting

    @property
    def raw(self) -> str:
        return self._raw

    @property
    def parameter(self) -> dict[str, Any]:
        return self._parameter.copy()  # Return copy

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
            self._logger.warning("Invalid status type: %s. Expected BaseFormat.Status.", type(value))

    @property
    def error(self) -> str:
        return self._error

    @property
    def props(self) -> str:
        properties: dict[str, Any] = {
            "positive": self.positive,
            "negative": self.negative,
            "positive_sdxl": self.positive_sdxl,
            "negative_sdxl": self.negative_sdxl,
            "is_sdxl": self.is_sdxl,
            "setting_string": self.setting,
            "tool_detected": self.tool,
            "raw_metadata_preview": (self.raw[:500] + "..." if len(self.raw) > 500 else self.raw),
            "status": (self.status.name if hasattr(self.status, "name") else str(self.status)),
            "error_message": self.error,
        }
        # Add parameters, excluding placeholders AND empty dicts/lists
        for key, value in self.parameter.items():
            if value != self.DEFAULT_PARAMETER_PLACEHOLDER:
                if isinstance(value, (dict, list)) and not value:
                    continue  # Skip empty dict/list
                properties[key] = value

        # Consolidate width/height/size logic for props
        prop_width = self.width
        prop_height = self.height
        if prop_width != "0" and prop_width != self.DEFAULT_PARAMETER_PLACEHOLDER:
            properties["width"] = prop_width
        if prop_height != "0" and prop_height != self.DEFAULT_PARAMETER_PLACEHOLDER:
            properties["height"] = prop_height

        # Ensure 'size' is consistent or removed if width/height are not set
        if "size" in properties:
            if (
                prop_width == "0"
                or prop_width == self.DEFAULT_PARAMETER_PLACEHOLDER
                or prop_height == "0"
                or prop_height == self.DEFAULT_PARAMETER_PLACEHOLDER
            ):
                if properties["size"] == self.DEFAULT_PARAMETER_PLACEHOLDER or properties["size"] == "0x0":
                    del properties["size"]  # Remove if redundant and width/height are zero/placeholder
            elif properties["size"] == self.DEFAULT_PARAMETER_PLACEHOLDER or properties["size"] == "0x0":
                properties["size"] = f"{prop_width}x{prop_height}"  # Reconstruct if valid w/h available

        # Final cleanup of placeholders for serialization
        final_props_to_serialize = {
            k: v
            for k, v in properties.items()
            if v != self.DEFAULT_PARAMETER_PLACEHOLDER and not (isinstance(v, (dict, list)) and not v)
        }
        # Remove width/height if they are "0" after all processing
        if final_props_to_serialize.get("width") == "0":
            del final_props_to_serialize["width"]
        if final_props_to_serialize.get("height") == "0":
            del final_props_to_serialize["height"]

        try:
            return json.dumps(final_props_to_serialize, indent=2)
        except TypeError:  # Fallback for non-serializable types
            self._logger.warning(
                "Encountered non-serializable types in props, converting to string.",
                exc_info=self._logger.level <= logging.DEBUG,
            )
            safe_props = {}
            for k, v_val in final_props_to_serialize.items():
                try:
                    json.dumps({k: v_val})  # Test serializability
                except TypeError:
                    safe_props[k] = str(v_val)
                else:
                    safe_props[k] = v_val
            return json.dumps(safe_props, indent=2)
