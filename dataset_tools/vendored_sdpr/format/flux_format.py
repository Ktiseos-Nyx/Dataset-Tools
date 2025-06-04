# Example sketch for FluxFormat
# In a new file, e.g., flux_format.py
from typing import Any

from .base_format import BaseFormat


class FluxFormat(BaseFormat):
    tool = "Flux (Black Forest Labs)"

    def __init__(self, info: dict[str, Any] | None = None, raw: str = "", **kwargs):
        # 'raw' is not used here as data comes from 'info' (parsed EXIF tags)
        super().__init__(info=info, raw=raw, **kwargs)

    def _process(self) -> None:
        if not self._info:
            self.status = self.Status.MISSING_INFO
            self._error = "No EXIF info provided for Flux parser."
            return

        software_tag = str(self._info.get("software_tag", "")).lower()
        make_tag = str(self._info.get("make_tag", "")).lower()

        is_flux = ";flux" in software_tag
        is_bfl = "black forest labs" in make_tag

        if not (is_flux and is_bfl):  # Require both for high confidence
            if not is_flux and "flux" in software_tag:  # Maybe older format
                pass  # Could be a weaker match
            else:
                self._logger.debug(
                    "%s: EXIF:Software does not contain ';flux' or Make is not 'Black Forest Labs'. software='%s', make='%s'",
                    self.tool_name,
                    self._info.get("software_tag"),
                    self._info.get("make_tag"),
                )
                self.status = self.Status.FORMAT_DETECTION_ERROR
                self._error = "Not Flux BFL metadata (Software/Make tag mismatch)."
                return

        # If identified, try to get specific version from software_tag if possible
        self.tool = self._info.get("software_tag", self.tool)  # e.g., "AI generated;txt2img;flux"

        self._positive = self._info.get("image_description_tag", "").strip()  # This is the prompt

        model_variant = self._info.get("model_tag", "")  # e.g., "flux-dev"
        if model_variant:
            self._parameter["model"] = model_variant  # Or a more specific key like "flux_model_variant"
            # Could refine self.tool based on model_variant too
            self.tool += f" ({model_variant})"

        # Other parameters (seed, steps, CFG, negative_prompt) are NOT saved by this BFL script.
        # They will remain as placeholders.

        # Build a minimal settings string from what we have
        settings_parts = []
        if model_variant:
            settings_parts.append(f"Flux Model Variant: {model_variant}")
        # No other settings are present in this EXIF structure.
        self._setting = "; ".join(settings_parts)

        self.status = self.Status.READ_SUCCESS
        self._logger.info("%s: Data parsed successfully from EXIF.", self.tool)
