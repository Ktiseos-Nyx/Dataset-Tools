# dataset_tools/vendored_sdpr/format/ruinedfooocus.py
import json

# from ..logger import get_logger # Not needed if self._logger is from BaseFormat
from .base_format import BaseFormat


class RuinedFooocusFormat(BaseFormat):
    tool = "RuinedFooocus"

    # __init__ is inherited from BaseFormat

    def _process(self) -> None:
        self._logger.info("Attempting to parse metadata as %s.", self.tool)

        if not self._raw:
            self._logger.warn("Raw data is empty for %s parser.", self.tool)
            self.status = BaseFormat.Status.FORMAT_ERROR
            self._error = "Raw data for RuinedFooocus is empty."
            return

        try:
            data = json.loads(self._raw)

            if not isinstance(data, dict) or data.get("software") != "RuinedFooocus":
                self._logger.debug(
                    "JSON data is not in %s format (missing 'software' tag or not a dict).",
                    self.tool,
                )
                self.status = BaseFormat.Status.FORMAT_ERROR
                self._error = "JSON is not RuinedFooocus format (software tag mismatch or not a dict)."
                return

            self._positive = str(data.get("Prompt", ""))
            self._negative = str(data.get("Negative", ""))

            handled_keys_in_data = {"Prompt", "Negative", "software"}
            custom_settings_for_display: dict[str, str] = {}

            param_map = {
                "base_model_name": "model",
                "sampler_name": ["sampler_name", "sampler"],
                "seed": "seed",
                "cfg": ["cfg_scale", "cfg"],
                "steps": "steps",
            }
            self._populate_parameters_from_map(data, param_map, handled_keys_in_data)

            self._extract_and_set_dimensions(data, "width", "height", handled_keys_in_data)

            self._assign_param_or_add_to_custom_settings(
                data,
                "scheduler",
                "scheduler",
                custom_settings_for_display,
                "Scheduler",
                handled_keys_in_data,
            )
            self._assign_param_or_add_to_custom_settings(
                data,
                "base_model_hash",
                "model_hash",
                custom_settings_for_display,
                "Model hash",
                handled_keys_in_data,
            )
            self._assign_param_or_add_to_custom_settings(
                data,
                "loras",
                ["loras", "loras_str"],
                custom_settings_for_display,
                "Loras",
                handled_keys_in_data,
            )

            self._add_to_custom_settings(
                data,
                "start_step",
                custom_settings_for_display,
                "Start step",
                handled_keys_in_data,
            )
            self._add_to_custom_settings(
                data,
                "denoise",
                custom_settings_for_display,
                "Denoise",
                handled_keys_in_data,
            )

            self._setting = self._build_settings_string(
                custom_settings_dict=custom_settings_for_display,
                include_standard_params=True,
                remaining_data_dict=None,
                sort_parts=True,
            )
            self._logger.info("Successfully parsed %s data.", self.tool)

        except json.JSONDecodeError as e:
            self._logger.error(
                "Invalid JSON encountered while parsing for %s: %s",
                self.tool,
                e,
                exc_info=True,  # Good to have for JSON errors
            )
            self.status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"Invalid JSON data: {e}"  # f-string for error message is fine
        except KeyError as e_key:
            self._logger.error(
                "Missing expected key in %s JSON data: %s",
                self.tool,
                e_key,
                exc_info=True,  # Good to have for KeyErrors
            )
            self.status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"Missing data key: {e_key}"  # f-string for error message is fine
        # General Exception is handled by BaseFormat.parse() which uses % formatting
