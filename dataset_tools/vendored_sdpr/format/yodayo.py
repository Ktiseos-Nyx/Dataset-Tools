# dataset_tools/vendored_sdpr/format/yodayo.py

import logging  # For type hint
import re
from typing import Any  # Use Dict from typing

from .a1111 import A1111

# from ...metadata_engine import register_parser_class


class YodayoFormat(A1111):
    # Class variable for the tool name this parser identifies.
    # BaseFormat.__init__ will pick this up.
    # It will be overridden in _process if Yodayo characteristics are confirmed.
    tool = "Yodayo/Moescape"

    YODAYO_PARAM_MAP = {
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
        Relies more on NGMS, specific "Lora hashes" key, and EXIF software tag.
        """
        intended_parser_tool_name = self.__class__.tool

        # Priority 1: EXIF:Software tag (most reliable if present and specific)
        if self._info and "software_tag" in self._info:
            software = str(self._info["software_tag"]).lower()
            if "yodayo" in software or "moescape" in software:
                self._logger.debug(
                    "[%s] Identified by EXIF:Software tag: '%s'",
                    intended_parser_tool_name,
                    self._info["software_tag"],
                )
                return True
            if "automatic1111" in software or "forge" in software or "sd.next" in software:
                self._logger.debug(
                    "[%s] EXIF:Software indicates A1111/Forge/SD.Next ('%s'). Not Yodayo/Moescape.",
                    intended_parser_tool_name,
                    self._info["software_tag"],
                )
                return False

        # --- Strong Positive Yodayo Markers in settings_dict ---
        has_ngms = "NGMS" in settings_dict
        has_yodayo_lora_hashes_key_format = "Lora hashes" in settings_dict

        model_is_uuid_in_settings = False
        if model_value := settings_dict.get("Model"):
            if re.fullmatch(r"[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}", model_value, re.IGNORECASE):
                model_is_uuid_in_settings = True

        # --- Decision based on positive Yodayo markers ---
        # Condition 1: NGMS is present. This is a very strong Yodayo signal.
        if has_ngms:
            self._logger.debug(
                "[%s] Identified by presence of 'NGMS' parameter.",
                intended_parser_tool_name,
            )
            if model_is_uuid_in_settings:
                self._logger.debug(
                    "[%s] 'NGMS' present AND 'Model' is UUID. High confidence Yodayo.",
                    intended_parser_tool_name,
                )
            return True

        # Condition 2: Specific "Lora hashes" key is present AND Model is UUID.
        if has_yodayo_lora_hashes_key_format and model_is_uuid_in_settings:
            self._logger.debug(
                "[%s] Identified by 'Lora hashes' key AND 'Model' is UUID.",
                intended_parser_tool_name,
            )
            return True

        # Condition 3: Specific "Lora hashes" key is present (Model not UUID, NGMS not present).
        # Check if Version string contradicts this by being clearly A1111/Forge.
        if has_yodayo_lora_hashes_key_format:  # And previous conditions (NGMS, Model UUID) were false
            version_str_from_settings = settings_dict.get("Version", "")
            is_a1111_webui_version_pattern = r"v\d+\.\d+\.\d+"
            is_likely_forge_version_pattern = (
                r"forge" in version_str_from_settings.lower()
                or re.match(r"v\d+\.\d+\.\d+.*-v\d+\.\d+\.\d+", version_str_from_settings)
                or re.match(r"f\d+\.\d+\.\d+v\d+\.\d+\.\d+", version_str_from_settings)
            )
            if re.match(is_a1111_webui_version_pattern, version_str_from_settings) or is_likely_forge_version_pattern:
                self._logger.debug(
                    "[%s] Has 'Lora hashes' key, but 'Version' ('%s') looks like A1111/Forge. Declining.",
                    intended_parser_tool_name,
                    version_str_from_settings,
                )
                return False
            self._logger.debug(
                "[%s] Identified by 'Lora hashes' key. Version ('%s') not clearly A1111/Forge.",
                intended_parser_tool_name,
                version_str_from_settings,
            )
            return True

        # --- If no strong positive Yodayo markers, check for strong A1111/Forge/SD.Next negative markers ---
        version_str_from_settings = settings_dict.get("Version", "")
        is_a1111_webui_version_pattern = r"v\d+\.\d+\.\d+"
        is_likely_forge_version_pattern = (
            r"forge" in version_str_from_settings.lower()
            or re.match(r"v\d+\.\d+\.\d+.*-v\d+\.\d+\.\d+", version_str_from_settings)
            or re.match(r"f\d+\.\d+\.\d+v\d+\.\d+\.\d+", version_str_from_settings)
        )

        if re.match(is_a1111_webui_version_pattern, version_str_from_settings) or is_likely_forge_version_pattern:
            self._logger.debug(
                "[%s] 'Version' string ('%s') matches A1111 WebUI or Forge pattern. Not Yodayo.",
                intended_parser_tool_name,
                version_str_from_settings,
            )
            return False

        has_a1111_forge_hires_params = (
            "Hires upscale" in settings_dict and "Hires upscaler" in settings_dict and "Hires steps" in settings_dict
        )
        has_ultimate_sd_upscale_params = any(k.startswith("Ultimate SD upscale") for k in settings_dict)
        has_adetailer_params = any(k.startswith("ADetailer") for k in settings_dict)
        has_controlnet_params = any(k.startswith("ControlNet ") for k in settings_dict)

        if (
            has_a1111_forge_hires_params
            or has_ultimate_sd_upscale_params
            or has_adetailer_params
            or has_controlnet_params
        ):
            self._logger.debug(
                "[%s] Found strong A1111/Forge/SD.Next specific parameter markers. Not Yodayo/Moescape. "
                "(Hires: %s, UltimateUS: %s, ADetailer: %s, ControlNet: %s)",
                intended_parser_tool_name,
                has_a1111_forge_hires_params,
                has_ultimate_sd_upscale_params,
                has_adetailer_params,
                has_controlnet_params,
            )
            return False

        self._logger.debug(
            "[%s] No definitive Yodayo/Moescape positive markers (EXIF Software, NGMS, 'Lora hashes'+Model UUID) found, "
            "and no strong A1111/Forge/SD.Next negative markers. Declining.",
            intended_parser_tool_name,
        )
        return False

    def _parse_lora_hashes(self, lora_hashes_str: str | None) -> list[dict[str, str]]:
        if not lora_hashes_str:
            return []
        loras: list[dict[str, str]] = []
        parts = lora_hashes_str.split(",")
        for part_str in parts:
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
                    self.tool,  # Use self.tool for runtime tool name
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
                self.tool,  # Use self.tool for runtime tool name
                name_or_id,
                weight,
            )
        cleaned_prompt_parts.append(prompt_text[current_offset:])
        cleaned_prompt = "".join(cleaned_prompt_parts)
        cleaned_prompt = re.sub(r"\s{2,}", " ", cleaned_prompt).strip(" ,")
        return cleaned_prompt, loras

    def _process(self) -> None:
        # Call A1111's _process() to parse the A1111-style text first.
        super()._process()

        if self.status != self.Status.READ_SUCCESS:
            self._logger.debug(
                "[%s] Parent A1111 _process did not result in READ_SUCCESS (status: %s). Yodayo parsing cannot proceed further.",
                self.__class__.tool,  # Use class tool for context before self.tool is potentially changed
                self.status.name if hasattr(self.status, "name") else str(self.status),
            )
            return

        a1111_settings_dict: dict[str, str] = {}
        if self._setting:
            a1111_settings_dict = self._parse_settings_string_to_dict(self._setting)

        is_yodayo_sw_tag = (
            self._info
            and "software_tag" in self._info
            and (
                "yodayo" in str(self._info["software_tag"]).lower()
                or "moescape" in str(self._info["software_tag"]).lower()
            )
        )

        # If A1111 parsing found no settings block, we can only rely on the software tag.
        # If software tag also isn't Yodayo, then it's not Yodayo.
        if not a1111_settings_dict and not is_yodayo_sw_tag:
            self._logger.debug(
                "[%s] A1111 parsing yielded no settings dictionary, and no Yodayo software tag. Declining.",
                self.__class__.tool,
            )
            self.status = self.Status.FORMAT_DETECTION_ERROR
            self._error = "A1111 found no settings block and no Yodayo software tag to check for Yodayo specifics."
            return

        if not self._is_yodayo_candidate(a1111_settings_dict):
            self.status = self.Status.FORMAT_DETECTION_ERROR
            self._error = "A1111-like text parsed, but not identified as Yodayo/Moescape by specific markers."
            return

        # --- Confirmed as Yodayo/Moescape ---
        self.tool = self.__class__.tool  # Set self.tool to "Yodayo/Moescape"

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

        # self._setting currently holds the A1111 settings string.
        # If needed, it could be rebuilt to only contain Yodayo-specific unhandled items,
        # but for now, retaining the A1111 block is often fine as "Tool Specific Data Block".

        self._logger.info("[%s] Successfully processed and identified as Yodayo/Moescape.", self.tool)
        # self.status is already READ_SUCCESS from A1111 parent's successful parse.
