# dataset_tools/vendored_sdpr/format/yodayo.py

import re
from typing import Any, Dict  # Use Dict from typing

from .a1111 import A1111
from .base_format import (
    BaseFormat,
)  # For Status enum if needed, though A1111 inherits it


class YodayoFormat(A1111):
    # Tool name for this specific parser when it successfully identifies the format.
    # The parent A1111 might initially set self.tool to "A1111 webUI".
    # This class variable is used by BaseFormat's __init__ if the instance doesn't override.
    # We will override self.tool in _process if _is_yodayo_candidate is true.
    tool = "Yodayo/Moescape"

    YODAYO_PARAM_MAP = {
        "Version": "tool_version",  # Yodayo often has a "Version" key
        "NGMS": "yodayo_ngms",  # Key observed in Yodayo examples
        # "Model" can be a UUID for Yodayo, A1111 already handles "Model" key.
        # We use the Model value format in _is_yodayo_candidate.
        # "Lora hashes" (specific key name) is handled separately.
    }

    def __init__(
        self,
        info: Dict[str, Any] | None = None,  # Use Dict
        raw: str = "",
        width: Any = 0,
        height: Any = 0,
        # logger_obj and **kwargs are accepted by A1111's __init__
        **kwargs: Any,
    ):
        super().__init__(info=info, raw=raw, width=width, height=height, **kwargs)
        self.parsed_loras_from_hashes: list[Dict[str, str]] = []  # Use Dict

    def _is_yodayo_candidate(self, settings_dict: Dict[str, str]) -> bool:
        """
        Checks for Yodayo/Moescape specific markers in the parsed A1111 settings_dict.
        This method is called *after* the parent A1111 class has successfully parsed
        the text into prompts and a settings_dict.
        """
        # Get the tool name this class aims to identify, for logging clarity.
        intended_tool_name = self.__class__.tool

        # Priority 1: EXIF:Software tag provided by ImageDataReader via self._info
        if self._info and "software_tag" in self._info:
            software = str(self._info["software_tag"]).lower()
            if "yodayo" in software or "moescape" in software:
                self._logger.debug(
                    "[%s] Identified by EXIF:Software tag: '%s'",
                    intended_tool_name,
                    self._info["software_tag"],
                )
                return True
            # If software tag explicitly indicates A1111/Forge, it's NOT Yodayo
            if "automatic1111" in software or "forge" in software or "sd.next" in software:
                self._logger.debug(
                    "[%s] Identified as A1111/Forge/SD.Next by EXIF:Software ('%s'). Not Yodayo/Moescape.",
                    intended_tool_name,
                    self._info["software_tag"],
                )
                return False

        # Priority 2: Look for highly Yodayo-specific keys in the settings_dict
        has_ngms = "NGMS" in settings_dict
        # "Lora hashes" is the specific key name Yodayo was observed to use.
        # A1111/Forge often use a more general "Hashes: {..." dict or embed LoRAs in prompt.
        has_yodayo_specific_lora_hashes_key = "Lora hashes" in settings_dict

        if has_ngms:
            self._logger.debug("[%s] Identified by presence of 'NGMS' parameter.", intended_tool_name)
            return True

        if has_yodayo_specific_lora_hashes_key:
            # If "Lora hashes" key is present, it's a strong Yodayo signal.
            # We can optionally check if the Model looks like a UUID, which was another Yodayo pattern.
            model_value = settings_dict.get("Model")
            if model_value and re.fullmatch(r"[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}", model_value, re.IGNORECASE):
                self._logger.debug(
                    "[%s] Identified by 'Lora hashes' key and UUID-like Model.",
                    intended_tool_name,
                )
            else:
                self._logger.debug(
                    "[%s] Identified by 'Lora hashes' key (Model name is '%s').",
                    intended_tool_name,
                    model_value,
                )
            return True

        # Priority 3: Negative indicators - if it has strong A1111/Forge markers, it's less likely Yodayo.
        # This helps prevent misidentification if Yodayo's own positive markers are weak or absent.
        has_a1111_forge_hires_params = (
            "Hires upscale" in settings_dict and "Hires upscaler" in settings_dict and "Hires steps" in settings_dict
        )

        has_ultimate_sd_upscale_params = any(k.startswith("Ultimate SD upscale") for k in settings_dict)

        # Forge often includes a very specific version string format.
        version_str = settings_dict.get("Version", "")
        is_likely_forge_version = (
            "forge" in version_str.lower()
            or re.match(r"v\d+\.\d+\.\d+\S+-v\d+\.\d+\.\d+", version_str)
            or re.match(r"f\d+\.\d+\.\d+v\d+\.\d+\.\d+", version_str)
        )  # Matches your example 'f2.0.1v1.10.1...'

        if has_a1111_forge_hires_params or has_ultimate_sd_upscale_params or is_likely_forge_version:
            self._logger.debug(
                "[%s] Found strong A1111/Forge specific markers (Hires, Ultimate Upscale, or Forge Version string). Not Yodayo/Moescape.",
                intended_tool_name,
            )
            return False

        self._logger.debug(
            "[%s] No definitive Yodayo/Moescape markers found, and no strong A1111/Forge markers to exclude. Declining.",
            intended_tool_name,
        )
        return False

    def _parse_lora_hashes(self, lora_hashes_str: str | None) -> list[Dict[str, str]]:  # Use Dict
        if not lora_hashes_str:
            return []
        loras: list[Dict[str, str]] = []
        parts = lora_hashes_str.split(",")
        for part in parts:
            part = part.strip()
            if not part:
                continue
            match = re.match(r"([^:]+):\s*([0-9a-fA-F]+)", part)
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
                    part,
                    lora_hashes_str,  # self.tool here would be "Yodayo/Moescape" if candidate check passed
                )
        return loras

    def _extract_loras_from_prompt_text(self, prompt_text: str) -> tuple[str, list[Dict[str, str]]]:  # Use Dict
        if not prompt_text:
            return "", []
        lora_pattern = re.compile(r"<lora:([^:]+):([0-9\.]+)(:[^>]+)?>")
        loras: list[Dict[str, str]] = []
        current_offset = 0
        cleaned_prompt_parts = []
        for match in lora_pattern.finditer(prompt_text):
            cleaned_prompt_parts.append(prompt_text[current_offset : match.start()])
            current_offset = match.end()
            name_or_id, weight = match.group(1), match.group(2)
            lora_info: Dict[str, str] = {"name_or_id": name_or_id, "weight": weight}
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
        # Let A1111 (parent) do its initial parsing.
        # This populates self._positive, self._negative, self._setting, self._parameter,
        # and sets self.status (likely to READ_SUCCESS if A1111 text is found).
        # self.tool will be "A1111 webUI" at this point if parent's tool var was used.
        super()._process()

        if self.status != self.Status.READ_SUCCESS:
            # If A1111 parsing failed, YodayoFormat also fails.
            # self._logger.debug already done by parent A1111's _process if it fails.
            return

        # A1111 parsing was successful. Now check if it's specifically Yodayo.
        # self._setting holds the A1111 settings block. Parse it into a dict.
        a1111_settings_dict: Dict[str, str] = {}
        if self._setting:
            # Use the _parse_settings_string_to_dict method from A1111 (which self inherits)
            a1111_settings_dict = self._parse_settings_string_to_dict(self._setting)
        else:  # No settings block found by A1111 parse
            self._logger.debug(
                "[%s] A1111 parsing successful but no settings block found. Cannot check for Yodayo markers.",
                self.__class__.tool,
            )
            self.status = self.Status.FORMAT_DETECTION_ERROR  # Not Yodayo if no settings to check
            self._error = "A1111 found no settings block to check for Yodayo specifics."
            return

        if not self._is_yodayo_candidate(a1111_settings_dict):
            # It parsed as A1111, but isn't Yodayo/Moescape.
            # Set status to signal ImageDataReader to try plain A1111 next (if order allows)
            # or to accept the A1111 parent's parsing result if Yodayo was tried before A1111.
            self.status = self.Status.FORMAT_DETECTION_ERROR
            self._error = "Parsed as A1111, but determined not to be Yodayo/Moescape by specific markers."
            # self._logger.debug is done inside _is_yodayo_candidate
            return

        # --- Confirmed Yodayo/Moescape ---
        self.tool = self.__class__.tool  # Explicitly set self.tool to "Yodayo/Moescape"

        # Populate Yodayo-specific parameters from a1111_settings_dict into self._parameter
        handled_yodayo_keys = set()  # For rebuilding settings string if needed
        self._populate_parameters_from_map(a1111_settings_dict, self.YODAYO_PARAM_MAP, handled_yodayo_keys)

        lora_hashes_str = a1111_settings_dict.get("Lora hashes")
        if lora_hashes_str:
            self.parsed_loras_from_hashes = self._parse_lora_hashes(lora_hashes_str)
            if self.parsed_loras_from_hashes:
                self._parameter["lora_hashes_data"] = self.parsed_loras_from_hashes
            handled_yodayo_keys.add("Lora hashes")

        # Extract <lora:...> from prompts (A1111 parent doesn't do this by default)
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

        # self._setting currently holds the A1111 settings block. This is usually fine.
        # If you wanted to rebuild it excluding Yodayo-handled keys:
        # self._setting = self._build_settings_string(
        #     remaining_data_dict=a1111_settings_dict,
        #     remaining_handled_keys=handled_yodayo_keys, # Add keys handled by A1111.SETTINGS_TO_PARAM_MAP too
        #     include_standard_params=False # Because A1111 settings string is already just settings
        # )

        self._logger.info("[%s] Successfully parsed and identified as Yodayo/Moescape.", self.tool)
        # self.status is already READ_SUCCESS from the A1111 parent's successful parse.
        # We have now refined self.tool and potentially self._parameter.
