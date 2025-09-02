# dataset_tools/metadata_engine/extractors/drawthings_extractors.py

"""DrawThings extraction methods.

Handles parsing of Draw Things app metadata from XMP data, including prompts
and generation parameters. Based on the vendored format code but adapted
for the metadata_engine system.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]

# Parameter mapping for DrawThings format (from vendored code)
DRAWTHINGS_PARAM_MAP: dict[str, str] = {
    "model": "model",
    "sampler": "sampler_name",
    "seed": "seed",
    "scale": "cfg_scale",
    "steps": "steps",
}


class DrawThingsExtractor:
    """Handles Draw Things-specific extraction methods."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the DrawThings extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "drawthings_extract_prompt": self.extract_drawthings_prompt,
            "drawthings_extract_negative_prompt": self.extract_drawthings_negative_prompt,
            "drawthings_extract_parameters": self.extract_drawthings_parameters,
            "drawthings_extract_dimensions": self.extract_drawthings_dimensions,
        }

    def extract_drawthings_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract positive prompt from DrawThings XMP data."""
        if not isinstance(data, dict):
            self.logger.debug("DrawThings prompt extraction: data is not a dict")
            return ""

        # DrawThings stores positive prompt in "c" field
        prompt = data.get("c", "")
        if isinstance(prompt, str):
            return prompt.strip()

        self.logger.debug(f"DrawThings prompt extraction: 'c' field type: {type(prompt)}")
        return ""

    def extract_drawthings_negative_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract negative prompt from DrawThings XMP data."""
        if not isinstance(data, dict):
            self.logger.debug("DrawThings negative prompt extraction: data is not a dict")
            return ""

        # DrawThings stores negative prompt in "uc" field
        negative_prompt = data.get("uc", "")
        if isinstance(negative_prompt, str):
            return negative_prompt.strip()

        self.logger.debug(f"DrawThings negative prompt extraction: 'uc' field type: {type(negative_prompt)}")
        return ""

    def extract_drawthings_parameters(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract generation parameters from DrawThings XMP data."""
        if not isinstance(data, dict):
            return {}

        parameters = {}

        # Map DrawThings parameters to standard names
        for dt_key, std_key in DRAWTHINGS_PARAM_MAP.items():
            if dt_key in data:
                value = data[dt_key]

                # Convert to appropriate type
                if std_key in ["seed", "steps"]:
                    try:
                        parameters[std_key] = int(value)
                    except (ValueError, TypeError):
                        self.logger.debug(f"Could not convert {std_key} to int: {value}")
                elif std_key == "cfg_scale":
                    try:
                        parameters[std_key] = float(value)
                    except (ValueError, TypeError):
                        self.logger.debug(f"Could not convert cfg_scale to float: {value}")
                else:
                    parameters[std_key] = str(value)

        self.logger.debug(f"DrawThings parameters extracted: {list(parameters.keys())}")
        return parameters

    def extract_drawthings_dimensions(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract image dimensions from DrawThings XMP data."""
        if not isinstance(data, dict):
            return {}

        dimensions = {}
        size_str = data.get("size", "0x0")

        if isinstance(size_str, str) and "x" in size_str:
            try:
                width_str, height_str = size_str.split("x", 1)
                width = int(width_str.strip())
                height = int(height_str.strip())

                if width > 0 and height > 0:
                    dimensions["width"] = width
                    dimensions["height"] = height
                    dimensions["size"] = f"{width}x{height}"

            except (ValueError, AttributeError) as e:
                self.logger.debug(f"Could not parse DrawThings size '{size_str}': {e}")

        return dimensions
