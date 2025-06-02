# dataset_tools/vendored_sdpr/format/ruinedfooocus.py
import json
import logging  # For type hinting
from typing import Any

from ..logger import get_logger  # CORRECTED: Use get_logger
from .base_format import BaseFormat


class RuinedFooocusFormat(BaseFormat):
    tool = "RuinedFooocus"

    def __init__(
        self,
        info: dict[str, Any] | None = None,
        raw: str = "",
        width: int = 0,
        height: int = 0,
    ):
        super().__init__(
            info=info,
            raw=raw,
            width=width,
            height=height,
        )  # Pass all args to super
        self._logger: logging.Logger = get_logger(f"DSVendored_SDPR.Format.{self.tool}")
        # REMOVED: self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER

    def parse(self) -> BaseFormat.Status:  # Return type hint
        # pylint: disable=no-member # Add this at method level if many logger calls and Pylint still struggles
        # Or add to individual logger calls if preferred.
        # Assuming the get_logger fix in __init__ resolves most no-member issues for self._logger.

        if self._status == BaseFormat.Status.READ_SUCCESS:
            return self._status

        self._logger.info(f"Attempting to parse metadata as {self.tool}.")

        if not self._raw:
            self._logger.warn(f"Raw data is empty for {self.tool} parser.")
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = "Raw data for RuinedFooocus is empty."
            return self._status

        try:
            data = json.loads(self._raw)

            if not isinstance(data, dict) or data.get("software") != "RuinedFooocus":
                self._logger.debug(
                    "JSON data is not in RuinedFooocus format (missing 'software' tag or not a dict).",
                )
                self._status = BaseFormat.Status.FORMAT_ERROR
                self._error = "JSON is not RuinedFooocus format (software tag mismatch or not a dict)."
                return self._status

            self._positive = str(data.get("Prompt", ""))
            self._negative = str(data.get("Negative", ""))

            # Populate parameters
            if "model" in self._parameter and data.get("base_model_name") is not None:
                self._parameter["model"] = str(data.get("base_model_name"))
            if (
                "sampler_name" in self._parameter
                and data.get("sampler_name") is not None
            ):
                self._parameter["sampler_name"] = str(data.get("sampler_name"))
            elif "sampler" in self._parameter and data.get("sampler_name") is not None:
                self._parameter["sampler"] = str(data.get("sampler_name"))
            if "seed" in self._parameter and data.get("seed") is not None:
                self._parameter["seed"] = str(data.get("seed"))
            if "cfg_scale" in self._parameter and data.get("cfg") is not None:
                self._parameter["cfg_scale"] = str(data.get("cfg"))
            elif "cfg" in self._parameter and data.get("cfg") is not None:
                self._parameter["cfg"] = str(data.get("cfg"))
            if "steps" in self._parameter and data.get("steps") is not None:
                self._parameter["steps"] = str(data.get("steps"))

            if data.get("width") is not None:
                self._width = str(data.get("width"))
            if data.get("height") is not None:
                self._height = str(data.get("height"))
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            custom_params_for_setting_string = {}
            if data.get("scheduler") is not None:
                if "scheduler" in self._parameter:
                    self._parameter["scheduler"] = str(data.get("scheduler"))
                else:
                    custom_params_for_setting_string["Scheduler"] = str(
                        data.get("scheduler"),
                    )
            if data.get("base_model_hash") is not None:
                if "model_hash" in self._parameter:
                    self._parameter["model_hash"] = str(data.get("base_model_hash"))
                else:
                    custom_params_for_setting_string["Model hash"] = str(
                        data.get("base_model_hash"),
                    )
            if data.get("loras") is not None:
                if "loras" in self._parameter:
                    self._parameter["loras"] = str(data.get("loras"))
                elif "loras_str" in self._parameter:
                    self._parameter["loras_str"] = str(data.get("loras_str"))
                else:
                    custom_params_for_setting_string["Loras"] = str(data.get("loras"))
            if data.get("start_step") is not None:
                custom_params_for_setting_string["Start step"] = str(
                    data.get("start_step"),
                )
            if data.get("denoise") is not None:
                custom_params_for_setting_string["Denoise"] = str(data.get("denoise"))

            setting_parts = []
            for key in BaseFormat.PARAMETER_KEY:
                value = self._parameter.get(key)
                # Use the class attribute from BaseFormat for the placeholder
                if value and value != BaseFormat.DEFAULT_PARAMETER_PLACEHOLDER:
                    display_key = key.replace("_", " ").capitalize()
                    setting_parts.append(f"{display_key}: {value}")
            for key, value in custom_params_for_setting_string.items():
                setting_parts.append(f"{key}: {value}")
            self._setting = ", ".join(sorted(setting_parts))

            self._logger.info(f"Successfully parsed {self.tool} data.")
            self._status = BaseFormat.Status.READ_SUCCESS

        except json.JSONDecodeError as e:
            self._logger.error(
                f"Invalid JSON encountered while parsing for {self.tool}: {e}",
            )
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"Invalid JSON data: {e}"
        except KeyError as e_key:  # More specific exception
            self._logger.error(
                f"Missing expected key in {self.tool} JSON data: {e_key}",
            )
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"Missing data key: {e_key}"
        except Exception as e_parse:  # pylint: disable=broad-except
            self._logger.error(
                f"Unexpected error during {self.tool} data parsing: {e_parse}",
                exc_info=True,
            )
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"General parsing error: {e_parse}"

        return self._status
