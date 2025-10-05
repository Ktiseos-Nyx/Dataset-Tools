# dataset_tools/vendored_sdpr/format/a1111.py

__author__ = "receyuki"
__filename__ = "a1111.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki; Modified 2025, Ktiseos Nyx"
__email__ = "receyuki@gmail.com; your_email@example.com"  # Add your email

import logging
import re
from typing import Any  # Use Dict and Tuple

from .base_format import BaseFormat
from .utility import add_quotes, concat_strings


class A1111(BaseFormat):
    # Default tool name for any A1111-style text.
    # Specific variants like Forge/Yodayo will not be distinguished by this parser.
    tool = "A1111 webUI"

    # This map translates keys found in the A1111 settings string to your canonical parameter names.
    # Keys found in the settings string but NOT in this map will still be part of self._setting
    # but not directly in self._parameter unless they match a BaseFormat.PARAMETER_KEY directly.
    # Add any common A1111/Forge/Yodayo key here if you want it standardized into self._parameter.
    A1111_KEY_ALIAS_TO_CANONICAL_MAP: dict[str, str | list[str]] = {
        "Seed": "seed",
        "Variation seed": "subseed",
        "Variation seed strength": "subseed_strength",
        "Sampler": "sampler_name",  # A1111 uses "Sampler", canonical is "sampler_name"
        "Steps": "steps",
        "CFG scale": "cfg_scale",
        "Face restoration": "restore_faces",  # Boolean flag often
        "Model": "model",  # Can be filename or UUID
        "Model hash": "model_hash",
        # "Size" is handled specially by _extract_and_set_dimensions_from_string
        "Clip skip": "clip_skip",
        "Denoising strength": "denoising_strength",
        "Hires upscale": "hires_upscale",
        "Hires steps": "hires_steps",
        "Hires upscaler": "hires_upscaler",
        "VAE": "vae_model",
        "VAE hash": "vae_hash",
        "Version": "tool_version",  # Will capture any "Version" string
        "Schedule type": "scheduler",
        "NGMS": "yodayo_ngms",  # Treat NGMS as a parameter to capture if present
        "Lora hashes": "lora_hashes_data",  # Capture this specific key if present
        "TI hashes": "ti_hashes_data",
        "Hashes": "hashes_dict_str",  # Capture the "Hashes: {dict_str}" string
        # Common ADetailer keys
        "ADetailer model": "adetailer_model_1",
        "ADetailer version": "adetailer_version",
        "ADetailer confidence": "adetailer_confidence_1",
        "ADetailer dilate erode": "adetailer_dilate_erode_1",
        "ADetailer mask blur": "adetailer_mask_blur_1",
        "ADetailer denoising strength": "adetailer_denoising_strength_1",
        "ADetailer inpaint only masked": "adetailer_inpaint_only_masked_1",
        "ADetailer inpaint padding": "adetailer_inpaint_padding_1",
        # Ultimate SD Upscale keys
        "Ultimate SD upscale upscaler": "ultimate_sd_upscale_upscaler",
        "Ultimate SD upscale tile_width": "ultimate_sd_upscale_tile_width",
        "Ultimate SD upscale tile_height": "ultimate_sd_upscale_tile_height",
        "Ultimate SD upscale padding": "ultimate_sd_upscale_padding",
        "Ultimate SD upscale mask_blur": "ultimate_sd_upscale_mask_blur",
    }

    def __init__(
        self,
        info: dict[str, Any] | None = None,
        raw: str = "",
        width: Any = 0,
        height: Any = 0,
        logger_obj: logging.Logger | None = None,
        **kwargs: Any,
    ):
        # BaseFormat.__init__ handles width, height, logger_obj, and other kwargs.
        super().__init__(
            info=info,
            raw=raw,
            width=width,
            height=height,
            logger_obj=logger_obj,
            **kwargs,
        )
        self._extra: str = ""  # Stores 'postprocessing' string if separate from main params

    def _extract_raw_data_from_info(self) -> str:
        """Consolidates raw parameter string from self._info, checking 'parameters',
        'UserComment', and appending 'postprocessing'.
        """
        consolidated_raw = ""
        parameters_chunk_str = ""
        user_comment_str = ""

        if self._info:
            parameters_chunk_str = str(self._info.get("parameters", ""))
            user_comment_raw = self._info.get("UserComment", "")  # Could be bytes or str

            if isinstance(user_comment_raw, bytes):
                # Try decoding with common encodings for UserComment
                try:
                    user_comment_str = user_comment_raw.decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    try:
                        user_comment_str = user_comment_raw.decode("latin-1", errors="ignore")
                    except UnicodeDecodeError:
                        user_comment_str = str(user_comment_raw, errors="ignore")  # Fallback
            elif isinstance(user_comment_raw, str):
                user_comment_str = user_comment_raw

            # Strip charset prefix from UserComment
            if user_comment_str.startswith("charset=Unicode "):
                user_comment_str = user_comment_str[len("charset=Unicode ") :]
            user_comment_str = user_comment_str.strip()

            # Prioritize parameters chunk (PNG), then UserComment (JPEG/WEBP)
            if parameters_chunk_str.strip():
                self._logger.debug(
                    "Using 'parameters' chunk from info dict. Length: %s",
                    len(parameters_chunk_str),
                )
                consolidated_raw = parameters_chunk_str
            elif user_comment_str:
                self._logger.debug(
                    "Using 'UserComment' from info dict. Length: %s",
                    len(user_comment_str),
                )
                consolidated_raw = user_comment_str

            # Handle 'postprocessing' data, append if relevant
            self._extra = str(self._info.get("postprocessing", ""))
            if self._extra:
                self._logger.debug("Found 'postprocessing' data. Length: %s", len(self._extra))
                if consolidated_raw:
                    # Avoid appending if _extra is already part of consolidated_raw (e.g. if params and postproc were same)
                    if self._extra not in consolidated_raw:
                        consolidated_raw = concat_strings(consolidated_raw, self._extra, "\n")
                else:  # If no main parameters found, postprocessing might be the only source
                    consolidated_raw = self._extra

        return consolidated_raw.strip()

    def _process(self) -> None:
        self._logger.debug("Attempting to parse as A1111-style text (tool: %s).", self.tool)

        # If self._raw was not provided directly (e.g., ImageDataReader gave UserComment as raw for JPEG),
        # try to extract and consolidate from self._info (for PNG parameters/postprocessing).
        if not self._raw:
            self._raw = self._extract_raw_data_from_info()
        # Still check if there's a separate 'postprocessing' chunk in info to append
        elif self._info and "postprocessing" in self._info:
            self._extra = str(self._info.get("postprocessing", ""))
            if self._extra and self._extra not in self._raw:  # Avoid duplication
                self._logger.debug("Appending 'postprocessing' from info to existing self._raw.")
                self._raw = concat_strings(self._raw, self._extra, "\n")

        if not self._raw:
            self._logger.warning(
                "[%s] No parameter string found (from raw input, info:parameters, info:UserComment, or info:postprocessing).",
                self.tool,
            )
            self.status = self.Status.MISSING_INFO
            self._error = "No A1111-style parameter string found to parse."
            return

        # Core parsing of the A1111 text string
        self._parse_a1111_text_format()

        # The tool name remains self.tool (defaulted by BaseFormat from A1111.tool class var)
        # No further tool differentiation logic within this simplified A1111 parser.

        # Final status check based on whether any data was actually extracted
        if self.status not in [
            self.Status.FORMAT_ERROR,
            self.Status.MISSING_INFO,
            self.Status.FORMAT_DETECTION_ERROR,
        ]:
            if (
                self._positive
                or self._negative
                or self._parameter_has_data()
                or (self._width != "0" and self._width != self.DEFAULT_PARAMETER_PLACEHOLDER)
                or (self._height != "0" and self._height != self.DEFAULT_PARAMETER_PLACEHOLDER)
                or self._setting
            ):
                self._logger.info("[%s] Data parsed successfully.", self.tool)
                # BaseFormat.parse() will set READ_SUCCESS if we didn't set an error status
            else:
                self._logger.warning(
                    "[%s] Parsing logic completed, but no meaningful data (prompts, parameters, size, settings) was extracted from the text.",
                    self.tool,
                )
                self.status = self.Status.FORMAT_ERROR  # Or FORMAT_DETECTION_ERROR if it implies wrong format
                self._error = f"[{self.tool}] Failed to extract any meaningful data from the parameter string."

    def _parse_prompt_blocks(self, raw_data: str) -> tuple[str, str, str]:  # Use Tuple
        positive_prompt, negative_prompt, settings_block = "", "", ""
        # Enhanced regex to better identify the start of the settings block
        # Looks for a newline, then common parameter names, ensuring it's not mid-prompt.
        settings_marker_pattern = (
            r"(?i)\n(?:Steps:|CFG scale:|Seed:|Size:|Model hash:|Model:|Sampler:|Face restoration:|"
            r"Clip skip:|ENSD:|Hires fix:|Hires steps:|Hires upscale:|Hires upscaler:|Denoising strength:|Version:|"
            r"Schedule type:|NGMS:|Lora hashes:|TI hashes:|Hashes:|ADetailer model:|Ultimate SD upscale upscaler:)"
        )
        neg_prompt_keyword = "\nNegative prompt:"

        # First, try to find settings block to isolate prompts
        settings_match_for_prompt_isolation = re.search(
            settings_marker_pattern, "\n" + raw_data
        )  # Prepend \n for consistency

        prompt_candidate_area = raw_data
        if settings_match_for_prompt_isolation:
            # Ensure index is relative to original raw_data if \n was prepended for search only
            actual_match_start_in_raw = settings_match_for_prompt_isolation.start()
            if not raw_data.startswith("\n") and settings_match_for_prompt_isolation.group(0).startswith("\n"):
                # if original raw_data didn't start with \n, but pattern matched on prepended \n
                pass  # Match start is already relative to original raw_data as regex included \n
            elif raw_data.startswith("\n") and settings_match_for_prompt_isolation.group(0).startswith("\n"):
                pass  # Match start is fine

            prompt_candidate_area = raw_data[:actual_match_start_in_raw].strip()
            settings_block = raw_data[actual_match_start_in_raw:].strip()

        # Now, find negative prompt within the prompt_candidate_area
        parts_at_negative = prompt_candidate_area.split(neg_prompt_keyword, 1)
        if len(parts_at_negative) > 1:
            positive_prompt = parts_at_negative[0].strip()
            negative_prompt = parts_at_negative[1].strip()
        else:
            positive_prompt = prompt_candidate_area.strip()
            negative_prompt = ""  # No negative prompt found

        # If settings_block was not found initially, it means raw_data was all prompts.
        # This case should be handled by prompt_candidate_area becoming raw_data.
        if not settings_match_for_prompt_isolation and not settings_block:
            # This means the entire raw_data was treated as prompt_candidate_area
            # and if no negative prompt marker, positive_prompt gets everything.
            # Settings block remains empty.
            pass

        return positive_prompt, negative_prompt, settings_block

    def _parse_settings_string_to_dict(self, settings_str: str) -> dict[str, str]:
        if not settings_str:
            return {}
        # Regex: Key (word chars, spaces, dots, hyphens) followed by colon, then optional space.
        # Value: everything until the next ", Key:" or "\nKey:" or end of string.
        # This version is more robust for values containing commas NOT meant as separators.
        pattern = re.compile(r"([\w\s.-]+):\s*((?:(?!(?:\s*,\s*|\n)[\w\s.-]+:).)*)")

        parsed_settings: dict[str, str] = {}
        # To make the regex work consistently, we ensure settings are comma-separated if not already.
        # The original sd-parsers regex was complex. A simpler approach for "Key: Value, Key: Value":
        # Split by ",\s*(?=(?:[\w\s.-]+:\s*))" -> comma followed by lookahead for "Key:"
        # This separates valid "Key: Value" pairs. Then each part is "Key: Value".

        # For now, using the existing complex regex from your A1111:
        matches = pattern.findall(settings_str)
        for key, value in matches:
            key = key.strip()
            value = value.strip(" ,")
            if key and key not in parsed_settings:  # First one wins if duplicate keys (unlikely)
                parsed_settings[key] = value

        # Fallback for very simple "Key: Value" string if the main regex yields nothing.
        if not parsed_settings and ":" in settings_str and "," not in settings_str and "\n" not in settings_str:
            parts = settings_str.split(":", 1)
            if len(parts) == 2:
                key, val = parts[0].strip(), parts[1].strip()
                if key and val:
                    parsed_settings[key] = val

        self._logger.debug("Parsed A1111 settings_dict: %s", parsed_settings)
        return parsed_settings

    def _parse_a1111_text_format(self):
        """Core parsing logic for A1111-style text. Populates prompts, settings string,
        and parameters.
        """
        if not self._raw:
            self._logger.debug(
                "[%s] _parse_a1111_text_format: self._raw is empty. Cannot parse.",
                self.tool,
            )
            self.status = self.Status.MISSING_INFO  # Should be caught by _process
            return

        self._positive, self._negative, settings_block_str = self._parse_prompt_blocks(self._raw)
        self._setting = settings_block_str.strip()  # This is the raw settings block string

        if not (self._positive or self._negative or self._setting):
            # If raw data was present but _parse_prompt_blocks couldn't split it meaningfully
            self._logger.warning(
                "[%s] _parse_prompt_blocks yielded no prompts or settings string from raw data. Raw preview: '%s'",
                self.tool,
                self._raw[:100],
            )
            # Consider this a format detection error if the raw string itself was not empty.
            if self._raw:
                self.status = self.Status.FORMAT_DETECTION_ERROR
            return

        settings_dict: dict[str, str] = {}
        if self._setting:
            settings_dict = self._parse_settings_string_to_dict(self._setting)
            if not settings_dict and self._setting.strip():  # Parsing failed but there was content
                self._logger.warning(
                    "[%s] Failed to parse settings string into dictionary: '%s'",
                    self.tool,
                    self._setting[:100],
                )

        handled_keys_for_params = set()  # To track which keys from settings_dict are processed

        # Populate parameters using the class's A1111_KEY_ALIAS_TO_CANONICAL_MAP
        # This handles common A1111 keys and maps them to canonical names in self._parameter
        self._populate_parameters_from_map(
            settings_dict,
            self.A1111_KEY_ALIAS_TO_CANONICAL_MAP,
            handled_keys_for_params,
            # No special value_processor needed here as values are usually direct strings or numbers
        )

        # Specifically handle "Size" as it sets width, height, and size parameters
        size_val_from_dict = settings_dict.get("Size")
        if size_val_from_dict:
            # _extract_and_set_dimensions_from_string will update self._width, self._height,
            # and self._parameter["width"], self._parameter["height"], self._parameter["size"]
            self._extract_and_set_dimensions_from_string(
                size_val_from_dict, "Size", settings_dict, handled_keys_for_params
            )
            # handled_keys_for_params.add("Size") is done by the method above if successful

        # Ensure self._width, self._height (from BaseFormat init or Size parsing)
        # are reflected in self._parameter if not already handled by A1111_KEY_ALIAS_TO_CANONICAL_MAP
        if (
            self._width != "0"
            and "width" in self._parameter
            and self._parameter["width"] == self.DEFAULT_PARAMETER_PLACEHOLDER
        ):
            self._parameter["width"] = self._width
        if (
            self._height != "0"
            and "height" in self._parameter
            and self._parameter["height"] == self.DEFAULT_PARAMETER_PLACEHOLDER
        ):
            self._parameter["height"] = self._height

        if self._width != "0" and self._height != "0" and "size" in self._parameter:
            self._parameter["size"] = f"{self._width}x{self._height}"
        elif "size" in self._parameter and self._parameter.get("size") == self.DEFAULT_PARAMETER_PLACEHOLDER:
            # If size is still placeholder, but width/height are now known, set size parameter
            if self._width != "0" and self._height != "0":
                self._parameter["size"] = f"{self._width}x{self._height}"

    def prompt_to_line(self) -> str:
        if not self._positive and not self._parameter_has_data():
            return ""
        line_parts = []
        if self._positive:
            prompt_val = add_quotes(self._positive).replace(chr(10), " ")
            line_parts.append(f"--prompt {prompt_val}")
        if self._negative:
            neg_prompt_val = add_quotes(self._negative).replace(chr(10), " ")
            line_parts.append(f"--negative_prompt {neg_prompt_val}")

        # Use self.width and self.height properties, which prioritize self._parameter
        current_width = self.width
        current_height = self.height
        if current_width != "0" and current_width != self.DEFAULT_PARAMETER_PLACEHOLDER:
            line_parts.append(f"--width {current_width}")
        if current_height != "0" and current_height != self.DEFAULT_PARAMETER_PLACEHOLDER:
            line_parts.append(f"--height {current_height}")

        # More generic CLI arg mapping based on common A1111 CLI arguments
        # This map defines how canonical parameter keys map to CLI arguments
        # Format: { canonical_param_key: (cli_arg_name, is_string_value) }
        param_to_cli_arg_map = {
            "seed": ("seed", False),
            "subseed": ("subseed", False),
            "subseed_strength": ("subseed_strength", False),
            "sampler_name": ("sampler", True),  # A1111 CLI uses --sampler
            "steps": ("steps", False),
            "cfg_scale": ("cfg_scale", False),
            "restore_faces": (
                "restore_faces",
                False,
            ),  # Often a boolean flag or string 'true'/'false'
            "model": ("model", True),  # Model name/path
            "model_hash": ("model_hash", True),
            "denoising_strength": ("denoising_strength", False),
            "clip_skip": ("clip_skip", False),
            "hires_upscaler": ("hires_upscaler", True),
            "hires_upscale": ("hires_upscale", False),  # Factor, e.g., 2 or 2.0
            "hires_steps": ("hires_steps", False),
            "vae_model": ("vae", True),  # A1111 CLI often uses --vae
            "scheduler": ("scheduler", True),  # If a scheduler arg exists
            "tool_version": ("version", True),  # If a version arg exists
        }

        for param_key, (cli_arg_name, is_string) in param_to_cli_arg_map.items():
            value = self._parameter.get(param_key)
            if value is not None and value != self.DEFAULT_PARAMETER_PLACEHOLDER:
                # Skip width/height as they are handled above by self.width/self.height properties
                if param_key in ["width", "height", "size"]:
                    continue

                processed_value = str(value)
                # Convert our snake_case param_key to kebab-case for typical CLI args if needed,
                # but cli_arg_name from map is better.
                line_parts.append(f"--{cli_arg_name} {add_quotes(processed_value) if is_string else processed_value}")

        # Note: This prompt_to_line is a basic representation.
        # Not all parameters in self._parameter will have a direct CLI equivalent,
        # especially extension parameters.
        return " ".join(line_parts).strip()
