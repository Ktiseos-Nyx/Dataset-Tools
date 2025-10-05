# dataset_tools/vendored_sdpr/format/civitai.py
import json
import re
from typing import Any

from .a1111 import A1111  # For A1111 text parsing capabilities
from .base_format import BaseFormat


class CivitaiFormat(BaseFormat):
    tool = "Civitai"  # Default, might be refined based on what's found

    def __init__(
        self,
        info: dict[str, Any] | None = None,
        raw: str = "",
        width: int = 0,
        height: int = 0,
        **kwargs,
    ):
        # Pass logger_obj if provided by ImageDataReader to ensure consistent logging context
        # BaseFormat's __init__ handles self._logger initialization.
        super().__init__(info=info, raw=raw, width=width, height=height, **kwargs)
        self.workflow_data: dict[str, Any] | None = None  # For ComfyUI-JSON style
        self.civitai_resources_parsed: list | dict | None = None  # For A1111-text style

    def _decode_user_comment_for_civitai_json(self, uc_string: str) -> str | None:
        """Decodes a UserComment string, handling potential "charset=Unicode" prefixes
        and mojibake for Civitai's ComfyUI JSON format.
        Returns a clean JSON string or None if not decipherable as such.
        """
        self._logger.debug(
            "%s: Attempting to decode UserComment as Civitai ComfyUI JSON (first 70): '%s'",
            self.tool,  # Tool name will be "Civitai" initially
            uc_string[:70],
        )
        if not uc_string or not isinstance(uc_string, str):
            self._logger.warning(
                "%s: UserComment string is empty or not a string for JSON attempt.",
                self.tool,
            )
            return None

        data_to_process = uc_string
        # More robust prefix stripping
        prefix_pattern = r'^charset\s*=\s*["\']?(UNICODE|UTF-16(?:LE|BE)?)["\']?\s*'
        match = re.match(prefix_pattern, uc_string, re.IGNORECASE)
        if match:
            data_to_process = uc_string[len(match.group(0)) :].strip()
            self._logger.debug(
                "%s: Stripped charset prefix. Remaining (first 50): '%s'",
                self.tool,
                data_to_process[:50],
            )

        data_to_process = data_to_process.strip("\x00")  # Strip null chars early

        # Heuristic for mojibake common in some Civitai UserComments
        needs_mojibake_fix = (
            "笀" in data_to_process or "∀" in data_to_process or "izarea" in data_to_process
        ) and not (data_to_process.startswith("{") and data_to_process.endswith("}"))

        if needs_mojibake_fix:
            self._logger.debug(
                "%s: Mojibake characters detected. Attempting latin-1 -> utf-16le decode.",
                self.tool,
            )
            try:
                json_string_bytes = data_to_process.encode("latin-1", "replace")
                json_string = json_string_bytes.decode("utf-16le", "replace")
                json_string = json_string.strip("\x00")  # Strip nulls again after decode
                json.loads(json_string)  # Validate if it's JSON now
                self._logger.debug(
                    "%s: Mojibake reversal/decode (latin-1 -> utf-16le) successful.",
                    self.tool,
                )
                return json_string
            except Exception as e_moji:
                self._logger.warning(
                    "%s: Mojibake reversal/decode (latin-1 -> utf-16le) attempt failed: %s",
                    self.tool,
                    e_moji,
                )
                # Fall through to try parsing as plain JSON if decode failed or wasn't needed

        # If not mojibake or mojibake fix failed/wasn't attempted, try to parse as plain JSON
        if data_to_process.startswith("{") and data_to_process.endswith("}"):
            self._logger.debug("%s: Data looks like plain JSON. Validating.", self.tool)
            try:
                json.loads(data_to_process)  # Validate
                self._logger.debug("%s: Plain JSON validation successful.", self.tool)
                return data_to_process
            except json.JSONDecodeError as json_decode_err:
                self._logger.warning(
                    "%s: Plain JSON validation failed for UserComment: %s",
                    self.tool,
                    json_decode_err,
                )
                return None  # Not valid JSON

        self._logger.debug(
            "%s: UserComment string not recognized as Civitai ComfyUI JSON after processing.",
            self.tool,
        )
        return None

    def _parse_as_civitai_comfyui_json(self) -> bool:
        """Attempts to parse self._raw as Civitai's ComfyUI JSON structure,
        which is a main JSON workflow containing an 'extraMetadata' key
        whose value is another JSON string with parameters.
        Returns True if successful, False otherwise.
        """
        if not self._raw:
            return False

        cleaned_workflow_json_str = self._decode_user_comment_for_civitai_json(self._raw)
        if not cleaned_workflow_json_str:
            return False  # Not the ComfyUI JSON flavor we're looking for

        try:
            parsed_workflow_data = json.loads(cleaned_workflow_json_str)
            if not isinstance(parsed_workflow_data, dict):
                self._logger.debug("%s: Parsed UserComment workflow is not a dictionary.", self.tool)
                return False

            extra_metadata_str = parsed_workflow_data.get("extraMetadata")
            if not (extra_metadata_str and isinstance(extra_metadata_str, str)):
                self._logger.debug(
                    "%s: 'extraMetadata' not found or not a string in workflow.",
                    self.tool,
                )
                return False  # Missing the crucial extraMetadata

            extra_meta_dict = json.loads(extra_metadata_str)
            if not isinstance(extra_meta_dict, dict):
                self._logger.debug("%s: 'extraMetadata' content is not a dictionary.", self.tool)
                return False

            # --- If all checks pass, populate fields ---
            self.tool = "Civitai ComfyUI"  # Refine tool name
            self.workflow_data = parsed_workflow_data  # Store full ComfyUI workflow
            # self._raw should be the main ComfyUI workflow JSON, not the UserComment string if different.
            # The 'cleaned_workflow_json_str' is this main workflow.
            self._raw = cleaned_workflow_json_str

            self._positive = str(extra_meta_dict.get("prompt", "")).strip()
            self._negative = str(extra_meta_dict.get("negativePrompt", "")).strip()
            handled_keys_in_extra_meta = {"prompt", "negativePrompt"}

            steps_val = extra_meta_dict.get("steps")
            if steps_val is not None:
                self._parameter["steps"] = str(steps_val)
                handled_keys_in_extra_meta.add("steps")

            cfg_val = extra_meta_dict.get("CFG scale", extra_meta_dict.get("cfgScale"))
            if cfg_val is not None:
                self._parameter["cfg_scale"] = str(cfg_val)
                handled_keys_in_extra_meta.add("CFG scale")
                handled_keys_in_extra_meta.add("cfgScale")

            sampler_val = extra_meta_dict.get("sampler", extra_meta_dict.get("sampler_name"))
            if sampler_val is not None:
                self._parameter["sampler_name"] = str(sampler_val)
                handled_keys_in_extra_meta.add("sampler")
                handled_keys_in_extra_meta.add("sampler_name")

            seed_val = extra_meta_dict.get("seed")
            if seed_val is not None:
                self._parameter["seed"] = str(seed_val)
                handled_keys_in_extra_meta.add("seed")

            # Extract Civitai-specific resources and workflowId from extra_meta_dict
            # These are important for Civitai ComfyUI identification
            civitai_resources_in_extra = extra_meta_dict.get("resources")
            if civitai_resources_in_extra:
                self._parameter["civitai_resources_from_extra"] = (
                    civitai_resources_in_extra  # Store as is (usually list)
                )
                handled_keys_in_extra_meta.add("resources")

            workflow_id_in_extra = extra_meta_dict.get("workflowId")
            if workflow_id_in_extra:
                self._parameter["civitai_workflowId_from_extra"] = str(workflow_id_in_extra)
                handled_keys_in_extra_meta.add("workflowId")

            self._extract_and_set_dimensions(extra_meta_dict, "width", "height", handled_keys_in_extra_meta)

            self._setting = self._build_settings_string(
                include_standard_params=False,
                custom_settings_dict=None,
                remaining_data_dict=extra_meta_dict,
                remaining_handled_keys=handled_keys_in_extra_meta,
                sort_parts=True,
            )

            self._logger.info("%s: Successfully parsed as Civitai ComfyUI JSON.", self.tool)
            return True

        except json.JSONDecodeError as e_json:
            self._logger.debug(
                "%s: JSON parsing failed during Civitai ComfyUI attempt: %s",
                self.tool,
                e_json,
            )
            return False
        except Exception as e_generic:
            self._logger.warning(
                "%s: Unexpected error during Civitai ComfyUI JSON parse attempt: %s",
                self.tool,
                e_generic,
                exc_info=self._logger.level <= 10,  # DEBUG level or lower for full exc_info
            )
            return False

    def _parse_as_civitai_a1111_text(self) -> bool:
        """Attempts to parse self._raw as A1111-style text, then checks for
        Civitai-specific markers like "Civitai resources" within that text.
        Returns True if successful, False otherwise.
        """
        if not self._raw:
            return False

        # Use an A1111 parser instance as a utility.
        # Pass current width/height in case A1111 string doesn't have "Size".
        # Crucially, pass self._logger so the A1111 utility uses the same logger context.
        a1111_parser_util = A1111(
            raw=self._raw,
            width=self.width,
            height=self.height,
            logger_obj=self._logger,  # Share logger
        )
        a1111_status = a1111_parser_util.parse()

        if a1111_status != self.Status.READ_SUCCESS:
            self._logger.debug("%s: Underlying A1111 text parsing failed or no A1111 data.", self.tool)
            return False  # A1111 parsing itself failed

        # A1111 parsing succeeded. Now check for Civitai markers.
        # The A1111 parser stores the raw settings block in its 'setting' attribute.
        # Its 'parameter' attribute holds parsed key-values.

        # Simpler check: "Civitai resources" key in the raw A1111 settings block or original raw.
        # A1111's `setting` attribute is the identified settings block.
        # A1111's `raw` attribute is the input string it was given.
        raw_settings_block_from_a1111 = a1111_parser_util.setting

        # For more robust check, parse the settings block found by A1111
        # A1111's _parse_settings_string_to_dict is a method, so call on instance
        a1111_parsed_settings_dict = {}
        if raw_settings_block_from_a1111:
            a1111_parsed_settings_dict = a1111_parser_util._parse_settings_string_to_dict(raw_settings_block_from_a1111)

        if "Civitai resources" not in a1111_parsed_settings_dict:
            self._logger.debug(
                "%s: A1111 text parsed, but no 'Civitai resources' key found in its settings. Not Civitai A1111.",
                self.tool,
            )
            return False  # It's plain A1111 or other text

        # --- If we're here, it's A1111-style text AND has the "Civitai resources" key ---
        self.tool = "Civitai A1111"  # Refine tool name

        # Copy relevant data from the a1111_parser_util instance to self
        self._positive = a1111_parser_util.positive
        self._negative = a1111_parser_util.negative
        self._parameter = a1111_parser_util.parameter.copy()  # Important to copy
        self._setting = a1111_parser_util.setting  # This is the A1111 settings block
        self._width = a1111_parser_util.width
        self._height = a1111_parser_util.height
        # self._raw remains the original input string, which is the A1111 text.

        # Specifically parse the "Civitai resources" JSON string
        civitai_resources_str = a1111_parsed_settings_dict.get("Civitai resources")
        if civitai_resources_str:
            try:
                self.civitai_resources_parsed = json.loads(civitai_resources_str)
                # Add to self._parameter for UI display or further processing
                self._parameter["civitai_resources_data"] = self.civitai_resources_parsed
            except json.JSONDecodeError:
                self._logger.warning(
                    "%s: Failed to parse 'Civitai resources' JSON from A1111 text: %s",
                    self.tool,
                    civitai_resources_str,
                )
                # Store raw string if JSON parsing fails
                self._parameter["civitai_resources_raw"] = civitai_resources_str

        # Check for "Civitai metadata" key as well, often an empty dict {}
        civitai_metadata_str = a1111_parsed_settings_dict.get("Civitai metadata")
        if civitai_metadata_str:
            self._parameter["civitai_metadata_raw"] = civitai_metadata_str

        self._logger.info("%s: Successfully parsed as Civitai A1111 text.", self.tool)
        return True

    def _process(self) -> None:
        """Main processing logic for CivitaiFormat.
        Tries to parse as Civitai ComfyUI JSON first. If that fails,
        tries to parse as Civitai A1111 Text.
        Sets status to FORMAT_DETECTION_ERROR if neither matches.
        """
        self._logger.info(
            "%s: Attempting to parse (trying ComfyUI JSON, then A1111 text).",
            self.tool,  # Initial tool name is "Civitai"
        )

        if not self._raw:  # self._raw is typically from UserComment for Civitai
            self._logger.warning("%s: Raw data (UserComment) is empty.", self.tool)
            self.status = self.Status.MISSING_INFO
            self._error = "Raw UserComment empty for Civitai parsing."
            return

        # Try parsing as Civitai ComfyUI JSON first
        if self._parse_as_civitai_comfyui_json():
            self.status = self.Status.READ_SUCCESS
            # self.tool is already updated to "Civitai ComfyUI" by the method
            return  # Successfully parsed

        # If not ComfyUI JSON, try parsing as Civitai A1111 Text
        self._logger.debug("%s: Not Civitai ComfyUI JSON, now trying Civitai A1111 text.", self.tool)
        if self._parse_as_civitai_a1111_text():
            self.status = self.Status.READ_SUCCESS
            # self.tool is already updated to "Civitai A1111" by the method
            return  # Successfully parsed

        # If neither specific Civitai format matched
        self._logger.debug(
            "%s: Does not match known Civitai ComfyUI JSON or A1111 Text formats.",
            self.tool,
        )
        self.status = self.Status.FORMAT_DETECTION_ERROR
        self._error = "Not a recognized Civitai format (ComfyUI JSON or A1111 text with markers)."
