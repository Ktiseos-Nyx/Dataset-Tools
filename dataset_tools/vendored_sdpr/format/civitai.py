# dataset_tools/vendored_sdpr/format/civitai.py
import json
import logging  # For type hinting
import re
from typing import Any  # For type hints

# from ..logger import Logger # OLD
from ..logger import get_logger  # NEW
from .base_format import BaseFormat


class CivitaiComfyUIFormat(BaseFormat):
    tool = "Civitai ComfyUI"

    def __init__(
        self,
        info: dict[str, Any] | None = None,
        raw: str = "",
        width: int = 0,
        height: int = 0,
    ):  # Added type hints
        super().__init__(
            info=info,
            raw=raw,
            width=width,
            height=height,
        )  # Pass all args
        # self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool.replace(' ', '_')}") # OLD
        self._logger: logging.Logger = get_logger(
            f"DSVendored_SDPR.Format.{self.tool.replace(' ', '_')}",
        )  # NEW
        self.workflow_data: dict[str, Any] | None = None  # Type hint
        # self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER # Inherited

    # Return type hint
    def _decode_user_comment_for_civitai(self, uc_string: str) -> str | None:
        # pylint: disable=no-member # Temporarily add if Pylint still complains
        self._logger.debug(
            f"Attempting to decode UserComment (first 70): '{uc_string[:70]}'",
        )
        if not uc_string or not isinstance(uc_string, str):
            self._logger.warn("UserComment string is empty or not a string.")
            return None

        data_to_process = uc_string
        prefix_pattern = r'^charset\s*=\s*["\']?(UNICODE|UTF-16|UTF-16LE)["\']?\s*'
        match = re.match(prefix_pattern, uc_string, re.IGNORECASE)
        if match:
            data_to_process = uc_string[len(match.group(0)) :].strip()
            self._logger.debug(
                f"Stripped 'charset=Unicode' prefix. Remaining: '{data_to_process[:50]}'",
            )

        # Mojibake handling is complex. The encode('latin-1').decode('utf-16le') is a common pattern for piexif issues.
        if (
            "笀" in data_to_process
            or "∀" in data_to_process
            or "izarea" in data_to_process
        ) and not (data_to_process.startswith("{") and data_to_process.endswith("}")):
            self._logger.debug(
                "Mojibake characters detected. Attempting latin-1 -> utf-16le decode.",
            )
            try:
                # This is a common fix for data mangled by piexif or similar UserComment issues
                json_string = data_to_process.encode("latin-1", "replace").decode(
                    "utf-16le",
                    "replace",
                )
                # Remove null terminators often present after this decode
                json_string = json_string.strip("\x00")
                json.loads(json_string)  # Validate if it's JSON
                self._logger.debug(
                    "Mojibake reversal/decode (latin-1 -> utf-16le) successful.",
                )
                return json_string
            except Exception as e_moji:  # pylint: disable=broad-except
                self._logger.warn(
                    f"Mojibake reversal/decode (latin-1 -> utf-16le) attempt failed: {e_moji}",
                )
                # Fall through to check if it's plain JSON already if reversal failed

        if data_to_process.startswith("{") and data_to_process.endswith("}"):
            self._logger.debug(
                "Data (post-prefix/post-mojibake-attempt) looks like plain JSON. Validating.",
            )
            try:
                data_to_process = data_to_process.strip("\x00")  # Clean before parsing
                json.loads(data_to_process)
                self._logger.debug("Plain JSON validation successful.")
                return data_to_process
            except json.JSONDecodeError as json_decode_err:  # Renamed 'e'
                self._logger.warn(f"Plain JSON validation failed: {json_decode_err}")
                return None

        self._logger.debug(
            "UserComment string not recognized as Civitai JSON after processing.",
        )
        return None

    def parse(self) -> BaseFormat.Status:  # Return type hint
        # pylint: disable=no-member # Temporarily add if Pylint still complains
        if self.status == self.Status.READ_SUCCESS:
            return self.status

        self._logger.info(f"Attempting to parse as {self.tool}.")
        if not self._raw:
            self._logger.warn("Raw UserComment data is empty.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "Raw UserComment empty."
            return self.status

        cleaned_workflow_json_str = self._decode_user_comment_for_civitai(self._raw)

        if not cleaned_workflow_json_str:
            self._logger.warn("Failed to decode UserComment or not Civitai JSON.")
            self.status = self.Status.FORMAT_ERROR
            # self._error is likely already set by _decode_user_comment_for_civitai
            if not self._error:
                self._error = "UserComment decode/validation failed."
            return self.status

        try:
            self.workflow_data = json.loads(cleaned_workflow_json_str)
            self._logger.info(
                "Successfully parsed main workflow JSON from UserComment.",
            )
        except json.JSONDecodeError as json_decode_err:  # Renamed 'e'
            self._logger.error(
                f"Decoded UserComment is not valid JSON: {json_decode_err}",
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Invalid JSON: {json_decode_err}"
            return self.status

        extra_metadata_str = self.workflow_data.get("extraMetadata")
        if not (extra_metadata_str and isinstance(extra_metadata_str, str)):
            self._logger.warn("'extraMetadata' not found or not a string.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "'extraMetadata' missing/invalid."
            return self.status

        try:
            extra_meta_dict = json.loads(extra_metadata_str)
            self._logger.debug("'extraMetadata' parsed successfully.")

            self._positive = str(extra_meta_dict.get("prompt", ""))
            self._negative = str(extra_meta_dict.get("negativePrompt", ""))
            self._parameter = dict.fromkeys(
                self.PARAMETER_KEY,
                self.DEFAULT_PARAMETER_PLACEHOLDER,
            )

            if "steps" in self._parameter and extra_meta_dict.get("steps") is not None:
                self._parameter["steps"] = str(extra_meta_dict["steps"])
            cfg_val = extra_meta_dict.get("CFG scale", extra_meta_dict.get("cfgScale"))
            if "cfg_scale" in self._parameter and cfg_val is not None:
                self._parameter["cfg_scale"] = str(cfg_val)
            sampler_val = extra_meta_dict.get(
                "sampler",
                extra_meta_dict.get("sampler_name"),
            )
            if "sampler_name" in self._parameter and sampler_val is not None:
                self._parameter["sampler_name"] = str(sampler_val)
            if "seed" in self._parameter and extra_meta_dict.get("seed") is not None:
                self._parameter["seed"] = str(extra_meta_dict["seed"])

            if extra_meta_dict.get("width") is not None:
                self._width = str(extra_meta_dict.get("width"))
            if extra_meta_dict.get("height") is not None:
                self._height = str(extra_meta_dict.get("height"))
            if "size" in self._parameter and self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

            setting_parts = []
            handled_extra_keys = {
                "prompt",
                "negativePrompt",
                "steps",
                "CFG scale",
                "cfgScale",
                "sampler",
                "sampler_name",
                "seed",
                "width",
                "height",
            }
            for k, v_val in extra_meta_dict.items():  # Renamed v to v_val
                if k not in handled_extra_keys:
                    setting_parts.append(f"{k.replace('_', ' ').capitalize()}: {v_val}")
            self._setting = ", ".join(sorted(setting_parts))
            self._raw = cleaned_workflow_json_str

            self._logger.info("Successfully extracted parameters from 'extraMetadata'.")
            self.status = self.Status.READ_SUCCESS

        except json.JSONDecodeError as e_extra:
            self._logger.error(f"Failed to parse JSON from 'extraMetadata': {e_extra}")
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Invalid 'extraMetadata' JSON: {e_extra}"
        except Exception as e_final:  # pylint: disable=broad-except
            self._logger.error(
                f"Unexpected error processing Civitai 'extraMetadata': {e_final}",
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Processing error: {e_final}"

        return self.status
