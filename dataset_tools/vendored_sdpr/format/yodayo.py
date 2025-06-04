# dataset_tools/vendored_sdpr/format/yodayo.py

import logging  # For type hint
import re
from typing import Any  # Use Dict from typing

from .a1111 import A1111


class YodayoFormat(A1111):
    # Class variable for the tool name this parser identifies.
    # BaseFormat.__init__ will pick this up.
    # It will be overridden in _process if Yodayo characteristics are confirmed.
    tool = "Yodayo/Moescape"

    YODAYO_PARAM_MAP = {
        "Version": "tool_version",  # Yodayo often has a "Version" key in its settings
        "NGMS": "yodayo_ngms",  # "NGMS" seems specific to Yodayo examples
        # "Model" is handled by A1111; its format (UUID vs filename) is a hint in _is_yodayo_candidate.
        # "Lora hashes" (the specific key name) is a positive Yodayo indicator.
    }

    def __init__(
        self,
        info: dict[str, Any] | None = None,
        raw: str = "",
        width: Any = 0,
        height: Any = 0,
        logger_obj: logging.Logger | None = None,  # Explicitly accept
        **kwargs: Any,
    ):
        # Call A1111's __init__ which will call BaseFormat's __init__
        # All these named args (info, raw, width, height, logger_obj) and **kwargs
        # will be correctly passed to BaseFormat.__init__ if A1111.__init__
        # also passes them correctly (i.e., A1111.__init__ must accept them or **kwargs).
        super().__init__(
            info=info,
            raw=raw,
            width=width,
            height=height,
            logger_obj=logger_obj,
            **kwargs,
        )
        self.parsed_loras_from_hashes: list[dict[str, str]] = []

    def _is_yodayo_candidate(self, settings_dict: dict[str, str]) -> bool:
        """Checks for Yodayo/Moescape specific markers in the parsed A1111 settings_dict.
        Called after the parent A1111 class has successfully parsed the text.
        """
        # Use the tool name this class *intends* to identify for logging.
        # self.tool might currently be "A1111 webUI" from the parent A1111._process().
        intended_parser_tool_name = self.__class__.tool

        # Priority 1: EXIF:Software tag (most reliable if present)
        if self._info and "software_tag" in self._info:
            software = str(self._info["software_tag"]).lower()
            if "yodayo" in software or "moescape" in software:
                self._logger.debug(
                    "[%s] Identified by EXIF:Software tag: '%s'",
                    intended_parser_tool_name,
                    self._info["software_tag"],
                )
                return True
            # If software tag explicitly indicates A1111/Forge, it's NOT Yodayo
            if "automatic1111" in software or "forge" in software or "sd.next" in software:
                self._logger.debug(
                    "[%s] EXIF:Software indicates A1111/Forge/SD.Next ('%s'). Not Yodayo/Moescape.",
                    intended_parser_tool_name,
                    self._info["software_tag"],
                )
                return False

        # Priority 2: Yodayo-specific parameter keys from settings_dict
        has_ngms = "NGMS" in settings_dict
        has_yodayo_specific_lora_hashes_key = "Lora hashes" in settings_dict
        # Note: A1111 often uses "Hashes: {..." (plural "Hashes", value is a dict string)
        # Yodayo example showed "Lora hashes: id:hash,id:hash" (plural "hashes", value is comma-separated string)

        if has_ngms:
            self._logger.debug(
                "[%s] Identified by presence of 'NGMS' parameter.",
                intended_parser_tool_name,
            )
            return True

        if has_yodayo_specific_lora_hashes_key:
            model_value = settings_dict.get("Model")  # Yodayo might use UUID for model name here
            if model_value and re.fullmatch(r"[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}", model_value, re.IGNORECASE):
                self._logger.debug(
                    "[%s] Identified by 'Lora hashes' key AND UUID-like Model value.",
                    intended_parser_tool_name,
                )
            else:
                self._logger.debug(
                    "[%s] Identified by 'Lora hashes' key (Model name is '%s', not UUID). This is a strong Yodayo signal.",
                    intended_parser_tool_name,
                    model_value,
                )
            return True  # The key "Lora hashes" itself is quite specific.

        # Priority 3: Negative indicators - presence of strong A1111/Forge markers
        # These suggest it's more likely advanced A1111/Forge than Yodayo's typical output.
        has_a1111_forge_hires_params = (
            "Hires upscale" in settings_dict and "Hires upscaler" in settings_dict and "Hires steps" in settings_dict
        )
        has_ultimate_sd_upscale_params = any(k.startswith("Ultimate SD upscale") for k in settings_dict)
        has_adetailer_params = any(k.startswith("ADetailer") for k in settings_dict)

        version_str = settings_dict.get("Version", "")
        # Matches common Forge version strings like "v1.7.0- GIBBERISH-v1.8.0- GIBBERISH" or "f0.0.1v1.8.0..."
        is_likely_forge_version = (
            "forge" in version_str.lower()
            or re.match(r"v\d+\.\d+\.\d+.*-v\d+\.\d+\.\d+", version_str)
            or re.match(r"f\d+\.\d+\.\d+v\d+\.\d+\.\d+", version_str)
        )

        if (
            has_a1111_forge_hires_params
            or has_ultimate_sd_upscale_params
            or is_likely_forge_version
            or has_adetailer_params
        ):
            self._logger.debug(
                "[%s] Found strong A1111/Forge specific markers (Hires, Ultimate Upscale, ADetailer, or Forge Version string). Not Yodayo/Moescape.",
                intended_parser_tool_name,
            )
            return False

        self._logger.debug(
            "[%s] No definitive Yodayo/Moescape positive markers (EXIF Software, NGMS, 'Lora hashes' key) found, "
            "and no strong A1111/Forge negative markers found to explicitly exclude. Declining to ensure no misidentification of plain A1111.",
            intended_parser_tool_name,
        )
        return False

    def _parse_lora_hashes(self, lora_hashes_str: str | None) -> list[dict[str, str]]:
        if not lora_hashes_str:
            return []
        loras: list[dict[str, str]] = []
        parts = lora_hashes_str.split(",")
        for part_str in parts:  # Renamed part to part_str to avoid conflict with re.match var
            part_str = part_str.strip()
            if not part_str:
                continue
            match = re.match(r"([^:]+):\s*([0-9a-fA-F]+)", part_str)
            if match:
                loras.append(
                    {
                        "id_or_name": match.group(1).strip(),
                        "hash": match.group(2).strip(),
                    }
                )
            else:
                self._logger.warning(
                    "[%s] Could not parse Lora hash part: '%s' from string '%s'",
                    self.tool,
                    part_str,
                    lora_hashes_str,
                )
        return loras

    def _extract_loras_from_prompt_text(self, prompt_text: str) -> tuple[str, list[dict[str, str]]]:
        if not prompt_text:
            return "", []
        lora_pattern = re.compile(r"<lora:([^:]+):([0-9\.]+)(:[^>]+)?>")
        loras: list[dict[str, str]] = []
        current_offset = 0
        cleaned_prompt_parts = []
        for match in lora_pattern.finditer(prompt_text):
            cleaned_prompt_parts.append(prompt_text[current_offset : match.start()])
            current_offset = match.end()
            name_or_id, weight = match.group(1), match.group(2)
            lora_info: dict[str, str] = {"name_or_id": name_or_id, "weight": weight}
            loras.append(lora_info)
            self._logger.debug(
                "[%s] Extracted LoRA from prompt: %s, weight: %s",
                self.tool,
                name_or_id,
                weight,
            )
        cleaned_prompt_parts.append(prompt_text[current_offset:])
        cleaned_prompt = "".join(cleaned_prompt_parts)
        cleaned_prompt = re.sub(r"\s{2,}", " ", cleaned_prompt).strip(" ,")
        return cleaned_prompt, loras

    def _process(self) -> None:
        # Call A1111's _process() to parse the A1111-style text first.
        # This will set self.status, self._positive, self._negative, self._setting,
        # self._parameter (with A1111 common keys), and self.tool (likely to "A1111 webUI").
        super()._process()

        if self.status != self.Status.READ_SUCCESS:
            # If the parent A1111 parser failed, then this Yodayo parser also fails.
            # The status and error message are already set by the parent.
            self._logger.debug(
                "[%s] Parent A1111 _process did not result in READ_SUCCESS (status: %s). Yodayo parsing cannot proceed further.",
                self.__class__.tool,
                self.status.name,  # Use class tool name for logging context
            )
            return

        # A1111 text was successfully parsed. Now, determine if it's *specifically* Yodayo.
        a1111_settings_dict: dict[str, str] = {}
        if self._setting:  # self._setting was populated by A1111._process()
            # Use the _parse_settings_string_to_dict method inherited from A1111
            a1111_settings_dict = self._parse_settings_string_to_dict(self._setting)

        # If no settings block was found by A1111, it's hard to check for Yodayo specifics from parameters.
        # Rely on software tag if available, otherwise, it's not Yodayo.
        is_yodayo_sw_tag = (
            self._info
            and "software_tag" in self._info
            and (
                "yodayo" in str(self._info["software_tag"]).lower()
                or "moescape" in str(self._info["software_tag"]).lower()
            )
        )

        if not a1111_settings_dict and not is_yodayo_sw_tag:
            self._logger.debug(
                "[%s] A1111 parsing yielded no settings dictionary, and no Yodayo software tag. Declining.",
                self.__class__.tool,
            )
            self.status = self.Status.FORMAT_DETECTION_ERROR
            self._error = "A1111 found no settings block and no Yodayo software tag to check for Yodayo specifics."
            return

        if not self._is_yodayo_candidate(a1111_settings_dict):
            # It parsed as A1111, but doesn't meet specific Yodayo criteria.
            # Set status to FORMAT_DETECTION_ERROR to signal ImageDataReader.
            self.status = self.Status.FORMAT_DETECTION_ERROR
            self._error = "A1111-like text parsed, but not identified as Yodayo/Moescape by specific markers."
            # Log message is already handled within _is_yodayo_candidate
            return

        # --- If we reach here, it's confirmed as Yodayo/Moescape ---
        self.tool = self.__class__.tool  # Set self.tool to "Yodayo/Moescape"

        # Populate Yodayo-specific parameters into self._parameter.
        # self._parameter already contains common A1111 params from parent call.
        handled_yodayo_keys_in_settings_dict = set()
        self._populate_parameters_from_map(
            a1111_settings_dict,
            self.YODAYO_PARAM_MAP,
            handled_yodayo_keys_in_settings_dict,
        )

        lora_hashes_str = a1111_settings_dict.get("Lora hashes")
        if lora_hashes_str:
            self.parsed_loras_from_hashes = self._parse_lora_hashes(lora_hashes_str)
            if self.parsed_loras_from_hashes:
                self._parameter["lora_hashes_data"] = self.parsed_loras_from_hashes
            handled_yodayo_keys_in_settings_dict.add("Lora hashes")

        # Extract <lora:...> from prompts if parent A1111 didn't (it usually doesn't)
        if self._positive:
            cleaned_positive, extracted_loras_pos = self._extract_loras_from_prompt_text(self._positive)
            if extracted_loras_pos:
                self._positive = cleaned_positive
                self._parameter["loras_from_prompt_positive"] = extracted_loras_pos

        if self._negative:
            cleaned_negative, extracted_loras_neg = self._extract_loras_from_prompt_text(self._negative)
            if extracted_loras_neg:
                self._negative = cleaned_negative
                self._parameter["loras_from_prompt_negative"] = extracted_loras_neg

        # Rebuild self._setting to only include Yodayo-specific unhandled items,
        # or items not part of A1111's standard SETTINGS_TO_PARAM_MAP or YODAYO_PARAM_MAP.
        # For now, self._setting still holds the original A1111 settings block, which is usually acceptable.
        # If a cleaner Yodayo-only settings string is desired:
        # all_handled_keys = handled_yodayo_keys_in_settings_dict.copy()
        # all_handled_keys.update(A1111.SETTINGS_TO_PARAM_MAP.keys()) # Keys handled by parent A1111
        # self._setting = self._build_settings_string(
        #     remaining_data_dict=a1111_settings_dict,
        #     remaining_handled_keys=all_handled_keys,
        #     include_standard_params=False # Already in self._parameter
        # )

        self._logger.info("[%s] Successfully processed and identified as Yodayo/Moescape.", self.tool)
        # self.status is already READ_SUCCESS (from A1111 parent's successful parse).
        # We have now refined self.tool and potentially self._parameter and prompts.
