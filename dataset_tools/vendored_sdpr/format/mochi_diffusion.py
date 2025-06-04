# dataset_tools/vendored_sdpr/format/mochi_diffusion.py
from typing import Any

from .base_format import BaseFormat


class MochiDiffusionFormat(BaseFormat):
    tool = "Mochi Diffusion"  # Default, will be updated by "Generator" field from metadata

    # Mapping Mochi's IPTC keys (from Metadata.swift) to our standard parameter names
    MOCHI_IPTC_KEY_TO_PARAM_MAP = {
        "Guidance Scale": "cfg_scale",
        "Steps": "steps",
        "Model": "model",
        "Seed": "seed",
        "Scheduler": "sampler_name",  # Mochi's "Scheduler" is their sampler concept
        "Upscaler": "upscaler",  # Add "upscaler" to BaseFormat.PARAMETER_KEY if standard
        "Date": "date",  # Add "date" if standard
        "ML Compute Unit": "mochi_ml_compute_unit",
        "Generator": "tool_version_detail",  # e.g., "Mochi Diffusion 3.0.1"
        # "Include in Image" -> positive prompt
        # "Exclude from Image" -> negative prompt
        # "Size" -> width/height
    }

    def __init__(self, info: dict[str, Any] | None = None, raw: str = "", **kwargs):
        # `raw` will be the IPTC:Caption-Abstract string.
        # `info` might contain other IPTC fields like OriginatingProgram.
        super().__init__(info=info, raw=raw, **kwargs)

    def _process(self) -> None:
        # Primary identification: Check IPTC:OriginatingProgram if available in self._info
        # ImageDataReader should populate self._info with relevant IPTC fields.
        # For example: self._info["iptc_originating_program"]
        #              self._info["iptc_caption_abstract"] (this would be self._raw)

        originating_program = str(self._info.get("iptc_originating_program", "")).strip()
        if "Mochi Diffusion" not in originating_program:
            # If OriginatingProgram is missing or doesn't say Mochi,
            # we can still try to parse self._raw if it looks like Mochi's format,
            # but the confidence is lower.
            # For now, let's make OriginatingProgram a strong requirement for high confidence.
            # A fallback could check if self._raw contains "Generator: Mochi Diffusion".
            self._logger.debug(
                "%s: 'IPTC:OriginatingProgram' is not 'Mochi Diffusion' (found: '%s'). Not for this parser.",
                self.tool,
                originating_program,
            )
            self.status = self.Status.FORMAT_DETECTION_ERROR
            self._error = "Not Mochi Diffusion (IPTC:OriginatingProgram mismatch)."
            # If self._raw contains "Generator: Mochi Diffusion" this could be a fallback check
            if self._raw and "Generator: Mochi Diffusion" in self._raw:
                self._logger.debug(
                    "%s: Found 'Generator: Mochi Diffusion' in raw string, attempting parse despite missing OriginatingProgram.",
                    self.tool,
                )
            else:
                return

        if not self._raw:  # self._raw should be the IPTC:Caption-Abstract string
            self._logger.warning("%s: Raw data (IPTC Caption-Abstract string) is empty.", self.tool)
            self.status = self.Status.MISSING_INFO
            self._error = "IPTC Caption-Abstract data empty for Mochi Diffusion."
            return

        try:
            # Parse the semicolon-separated key: value string
            # Example: "Key1: Value1; Key2: Value2; ..."
            # The string might have newlines for readability in Swift, clean them.
            cleaned_raw = self._raw.replace("\n", " ").strip()

            # Split by semicolon, but be careful if values themselves can contain semicolons
            # (unlikely for this format based on Swift code).
            # A more robust split might use regex if keys are well-defined.
            # For now, simple split, then key-value split.

            # Use regex to find "Key: Value" pairs separated by ";"
            # Pattern: (Key name before colon): (Value after colon up to next semicolon or end)
            # This handles values that might accidentally contain colons if keys are simple.
            # For Mochi, keys are like "Include in Image", "Guidance Scale".
            # Regex: ([^:]+):\s*([^;]+(?:;(?!\s*[^:]+:\s))?)(?:;|$)
            # Simpler: split by ';' then by first ':'

            metadata_dict: dict[str, str] = {}
            parts = cleaned_raw.split(";")
            for part in parts:
                part = part.strip()
                if not part:
                    continue

                # Split only on the first occurrence of ":"
                kv = part.split(":", 1)
                if len(kv) == 2:
                    key = kv[0].strip()
                    value = kv[1].strip()
                    if key and value:  # Ensure both key and value are non-empty
                        metadata_dict[key] = value
                else:
                    self._logger.debug("%s: Malformed part in IPTC string: '%s'", self.tool, part)

            if not metadata_dict:
                self._logger.warning("%s: Failed to parse key-value pairs from IPTC string.", self.tool)
                self.status = self.Status.FORMAT_ERROR
                self._error = "Could not parse Mochi Diffusion IPTC metadata string."
                return

            # --- Parameter Extraction ---
            self._positive = metadata_dict.get("Include in Image", "").strip()
            self._negative = metadata_dict.get("Exclude from Image", "").strip()

            # Update tool name with version from "Generator" if present
            generator_full_value = metadata_dict.get("Generator", "")
            if generator_full_value:
                self.tool = generator_full_value  # e.g., "Mochi Diffusion 3.0.1"
            elif originating_program:  # Fallback to originating program if Generator key is missing
                self.tool = originating_program

            # Keys handled by direct assignment or special parsing
            handled_keys = {
                "Include in Image",
                "Exclude from Image",
                "Generator",
                "Size",
            }

            self._populate_parameters_from_map(
                metadata_dict,
                self.MOCHI_IPTC_KEY_TO_PARAM_MAP,
                handled_keys,  # This set is for _build_settings_string if used later
            )

            # Handle "Size" -> width, height
            size_str = metadata_dict.get("Size")
            if size_str:
                self._extract_and_set_dimensions_from_string(size_str, "Size", metadata_dict, handled_keys)
            # If "Size" is not present, self.width and self.height (from image dimensions) will be used.

            # The raw settings string (self._setting) could be a reconstruction of unhandled key-values,
            # or simply the original self._raw if preferred. For Mochi, the structure is flat.
            # Let's build it from unhandled keys.
            self._setting = self._build_settings_string(
                remaining_data_dict=metadata_dict,
                remaining_handled_keys=handled_keys,
                kv_separator=": ",  # Mochi uses ": "
                pair_separator="; ",  # Mochi uses "; "
                sort_parts=True,
            )

            self.status = self.Status.READ_SUCCESS
            self._logger.info("%s: Data parsed successfully from IPTC.", self.tool)

        except Exception as e_gen:
            self._logger.error(
                "%s: Unexpected error during IPTC parsing: %s",
                self.tool,
                e_gen,
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Unexpected error parsing Mochi Diffusion IPTC: {e_gen}"
