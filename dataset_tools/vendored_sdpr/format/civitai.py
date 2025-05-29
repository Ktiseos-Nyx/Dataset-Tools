# dataset_tools/vendored_sdpr/format/civitai.py
import json
import re
from .base_format import BaseFormat
from ..logger import Logger
from ..constants import PARAMETER_PLACEHOLDER  # For consistency if needed


class CivitaiComfyUIFormat(BaseFormat):
    tool = "Civitai ComfyUI"  # Set tool name

    def __init__(self, info: dict = None, raw: str = "", width: int = 0, height: int = 0):
        super().__init__(info, raw, width, height)
        self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool.replace(' ', '_')}")  # Consistent logger name
        self.workflow_data: dict | None = None
        self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER  # Make accessible

    def _decode_user_comment_for_civitai(self, uc_string: str) -> str | None:
        # ... (your existing decoding logic is likely fine, keep it) ...
        # Ensure it returns None on failure to decode or validate structure
        self._logger.debug(f"Attempting to decode UserComment (first 70): '{uc_string[:70]}'")
        if not uc_string or not isinstance(uc_string, str):
            self._logger.warn("UserComment string is empty or not a string.")
            return None

        data_to_process = uc_string
        prefix_pattern = r'^charset\s*=\s*["\']?(UNICODE|UTF-16|UTF-16LE)["\']?\s*'
        match = re.match(prefix_pattern, uc_string, re.IGNORECASE)
        if match:
            data_to_process = uc_string[len(match.group(0)) :].strip()
            self._logger.debug(f"Stripped 'charset=Unicode' prefix. Remaining: '{data_to_process[:50]}'")

        if ("笀" in data_to_process or "∀" in data_to_process or "izarea" in data_to_process) and not (
            data_to_process.startswith("{") and data_to_process.endswith("}")
        ):
            self._logger.debug("Mojibake characters detected. Attempting reversal.")
            try:
                byte_list = [((ord(c) >> 8) & 0xFF) for c in data_to_process] + [
                    (ord(c) & 0xFF) for c in data_to_process
                ]  # Simplified assumption, may need proper pairs
                recovered_bytes = bytes(byte_list[: len(data_to_process) * 2 // 2 * 2])  # Ensure even length for pairs
                # This mojibake logic is highly specific and might need careful byte-level debugging
                # if it's not working. A direct UTF-16LE decode attempt might be better if piexif mangles.
                # For now, assuming your original logic was functional for the specific mojibake.
                # A common pattern is that piexif returns a string that needs to be encoded to latin-1 then decoded as utf-16le
                json_string = data_to_process.encode("latin-1", "replace").decode("utf-16le", "replace")
                json.loads(json_string)
                self._logger.debug("Mojibake reversal/decode attempt successful.")
                return json_string.strip("\x00")  # Remove null terminators
            except Exception as e:
                self._logger.warn(f"Mojibake reversal/decode attempt failed: {e}")
                # Fall through to check if it's plain JSON already

        if data_to_process.startswith("{") and data_to_process.endswith("}"):
            self._logger.debug("Data (post-prefix/post-mojibake-attempt) looks like plain JSON. Validating.")
            try:
                json.loads(data_to_process)
                self._logger.debug("Plain JSON validation successful.")
                return data_to_process.strip("\x00")
            except json.JSONDecodeError as e:
                self._logger.warn(f"Plain JSON validation failed: {e}")
                return None

        self._logger.debug("UserComment string not recognized as Civitai JSON after processing.")
        return None

    def parse(self):  # Overrides BaseFormat.parse directly
        if self.status == self.Status.READ_SUCCESS:
            return self.status  # Already parsed

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
            self._error = "UserComment decode/validation failed."
            return self.status

        try:
            self.workflow_data = json.loads(cleaned_workflow_json_str)
            self._logger.info("Successfully parsed main workflow JSON from UserComment.")
        except json.JSONDecodeError as e:
            self._logger.error(f"Decoded UserComment is not valid JSON: {e}")
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Invalid JSON: {e}"
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

            # Populate self._parameter, aligning with BaseFormat.PARAMETER_KEY
            # Initialize with placeholders from BaseFormat
            self._parameter = dict.fromkeys(self.PARAMETER_KEY, self.DEFAULT_PARAMETER_PLACEHOLDER)

            if "steps" in self._parameter and extra_meta_dict.get("steps") is not None:
                self._parameter["steps"] = str(extra_meta_dict["steps"])

            cfg_val = extra_meta_dict.get("CFG scale", extra_meta_dict.get("cfgScale"))
            if "cfg_scale" in self._parameter and cfg_val is not None:
                self._parameter["cfg_scale"] = str(cfg_val)

            sampler_val = extra_meta_dict.get("sampler", extra_meta_dict.get("sampler_name"))
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

            # Store other extra_meta_dict items into a settings string or directly if they match PARAMETER_KEY
            setting_parts = []
            for k, v in extra_meta_dict.items():
                if k not in [
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
                ]:
                    # If k (normalized) is a canonical key, put it in self._parameter
                    # normalized_k = k.lower().replace(" ", "_")
                    # if normalized_k in self._parameter:
                    #    self._parameter[normalized_k] = str(v)
                    # else: # Otherwise, add to settings string
                    setting_parts.append(f"{k.replace('_', ' ').capitalize()}: {v}")
            self._setting = ", ".join(sorted(setting_parts))

            # self._raw for this parser is the cleaned ComfyUI workflow JSON
            self._raw = cleaned_workflow_json_str  # Store the main workflow JSON as raw
            # Optionally, self._raw_setting from extra_metadata_str (or just use self._setting)

            self._logger.info("Successfully extracted parameters from 'extraMetadata'.")
            self.status = self.Status.READ_SUCCESS

        except json.JSONDecodeError as e_extra:
            self._logger.error(f"Failed to parse JSON from 'extraMetadata': {e_extra}")
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Invalid 'extraMetadata' JSON: {e_extra}"
        except Exception as e_final:
            self._logger.error(f"Unexpected error processing Civitai 'extraMetadata': {e_final}", exc_info=True)
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Processing error: {e_final}"

        return self.status
