# dataset_tools/metadata_engine/field_extraction.py

"""Clean, focused field extraction system.

This is the main FieldExtractor class that coordinates all extraction methods.
Individual extraction logic is split into separate modules for maintainability.
"""

import logging
from typing import Any

from ..logger import get_logger
from .extractors.a1111_extractors import A1111Extractor
from .extractors.civitai_extractors import CivitaiExtractor
from .extractors.comfyui_extractors import ComfyUIExtractor

# Import extraction modules
from .extractors.direct_extractors import DirectValueExtractor
from .extractors.json_extractors import JSONExtractor
from .extractors.regex_extractors import RegexExtractor

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class FieldExtractor:
    """Main field extraction coordinator.

    This class delegates extraction work to specialized extractor modules,
    keeping the code organized and maintainable.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize the field extractor with all sub-extractors."""
        self.logger = logger or get_logger("FieldExtractor")

        # Initialize specialized extractors
        self.direct_extractor = DirectValueExtractor(self.logger)
        self.a1111_extractor = A1111Extractor(self.logger)
        self.civitai_extractor = CivitaiExtractor(self.logger)
        self.comfyui_extractor = ComfyUIExtractor(self.logger)
        self.json_extractor = JSONExtractor(self.logger)
        self.regex_extractor = RegexExtractor(self.logger)

        # Build method registry from all extractors
        self._method_registry = {}
        self._register_extractor_methods()

    def _register_extractor_methods(self):
        """Register all extraction methods from sub-extractors."""
        # Direct value methods
        self._method_registry.update(self.direct_extractor.get_methods())

        # A1111 methods
        self._method_registry.update(self.a1111_extractor.get_methods())

        # Civitai methods
        self._method_registry.update(self.civitai_extractor.get_methods())

        # ComfyUI methods
        self._method_registry.update(self.comfyui_extractor.get_methods())

        # JSON methods
        self._method_registry.update(self.json_extractor.get_methods())

        # Regex methods
        self._method_registry.update(self.regex_extractor.get_methods())

    def extract_field(
        self,
        method_def: MethodDefinition,
        input_data: Any,
        context_data: ContextData,
        extracted_fields: ExtractedFields,
    ) -> Any:
        """Extract a field using the specified method.

        Args:
            method_def: Method definition containing extraction instructions
            input_data: Current input data being processed
            context_data: Full context data dictionary
            extracted_fields: Previously extracted fields (for variable references)

        Returns:
            Extracted value or None if extraction failed

        """
        method_name = method_def.get("method")
        if not method_name:
            self.logger.warning("Method definition missing 'method' field")
            return None

        # Get the actual data to work with
        data_for_method = self._get_source_data(method_def, input_data, context_data, extracted_fields)

        # Get the extraction method
        extraction_method = self._method_registry.get(method_name)
        if not extraction_method:
            self.logger.warning(f"Unknown extraction method: '{method_name}'")
            return None

        try:
            # Execute the extraction
            value = extraction_method(data_for_method, method_def, context_data, extracted_fields)

            # Apply type conversion if specified
            return self._apply_type_conversion(value, method_def)

        except Exception as e:
            self.logger.error("Error in extraction method '%s': %s", method_name, e, exc_info=True)
            return None

    def _get_source_data(
        self,
        method_def: MethodDefinition,
        input_data: Any,
        context_data: ContextData,
        extracted_fields: ExtractedFields,
    ) -> Any:
        """Get the source data for the extraction method."""
        source_config = method_def.get("source_data_from_context")
        if not source_config:
            return input_data

        source_type = source_config.get("type")
        source_key = source_config.get("key")

        source_map = {
            "pil_info_key": lambda: context_data.get("pil_info", {}).get(source_key),
            "png_chunk": lambda: context_data.get("png_chunks", {}).get(source_key),
            "exif_user_comment": lambda: context_data.get("raw_user_comment_str"),
            "xmp_string": lambda: context_data.get("xmp_string"),
            "file_content_raw_text": lambda: context_data.get("raw_file_content_text"),
            "raw_file_content_text": lambda: context_data.get("raw_file_content_text"),  # Add this alias
            "file_content_json_object": lambda: context_data.get("parsed_root_json_object"),
            "parsed_root_json_object": lambda: context_data.get("parsed_root_json_object"),  # Add this alias
            "direct_context_key": lambda: context_data.get(source_key),
            "variable": lambda: extracted_fields.get(source_key.replace(".", "_") + "_VAR_"),
            "exif_field": lambda: context_data.get("exif_data", {}).get(source_key),
        }

        getter = source_map.get(source_type)
        if getter:
            return getter()
        self.logger.warning(f"Unknown source type: '{source_type}'")
        return input_data

    def _apply_type_conversion(self, value: Any, method_def: MethodDefinition) -> Any:
        """Apply type conversion to the extracted value."""
        if value is None:
            return None

        value_type = method_def.get("value_type")
        if not value_type:
            return value

        try:
            converters = {
                "integer": lambda v: int(float(str(v))),
                "float": lambda v: float(str(v)),
                "string": lambda v: str(v),
                "boolean": lambda v: (v if isinstance(v, bool) else str(v).lower() in ("true", "1", "yes", "on")),
                "array": lambda v: v if isinstance(v, list) else [v],
            }

            converter = converters.get(value_type)
            if converter:
                return converter(value)
            self.logger.warning(f"Unknown value type: '{value_type}'")
            return value

        except (ValueError, TypeError) as e:
            self.logger.debug(f"Could not convert value to '{value_type}': {e}")
            return None


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def create_field_extractor(logger: logging.Logger | None = None) -> FieldExtractor:
    """Create a field extractor instance."""
    return FieldExtractor(logger)


# ============================================================================
# TESTING
# ============================================================================


def test_field_extraction():
    """Test the field extraction system."""
    logger = get_logger("FieldExtractionTest")
    logger.info("Testing clean field extraction system...")

    extractor = create_field_extractor(logger)

    # Test direct string extraction
    method_def = {"method": "direct_string_value", "value_type": "string"}

    result = extractor.extract_field(method_def, "test data", {}, {})
    logger.info("Direct string extraction result: %s", result)

    logger.info("Field extraction tests completed!")


if __name__ == "__main__":
    test_field_extraction()

# Add these imports and classes to the bottom of your cleaned field_extraction.py

# ============================================================================
# BACKWARD COMPATIBILITY - Keep existing imports working
# ============================================================================

# Import the extractors so other code can still access them


# Create compatibility classes for existing imports
class A1111ParameterExtractor:
    """Backward compatibility wrapper for A1111Extractor."""

    def __init__(self, logger=None):
        self.extractor = A1111Extractor(logger or get_logger("A1111ParameterExtractor"))

    def extract_all_parameters(self, param_string: str) -> dict[str, Any]:
        """Extract all parameters from an A1111 parameter string."""
        if not isinstance(param_string, str):
            return {}

        # Use the new extractor methods
        context = {"raw_user_comment_str": param_string}
        method_def = {}
        fields = {}

        methods = self.extractor.get_methods()

        result = {}
        result["positive_prompt"] = (
            methods["a1111_extract_prompt_positive"](param_string, method_def, context, fields) or ""
        )
        result["negative_prompt"] = (
            methods["a1111_extract_prompt_negative"](param_string, method_def, context, fields) or ""
        )

        return result


class ComfyUIWorkflowExtractor:
    """Backward compatibility wrapper for ComfyUIExtractor."""

    def __init__(self, logger=None):
        self.extractor = ComfyUIExtractor(logger or get_logger("ComfyUIWorkflowExtractor"))

    def extract_workflow_metadata(self, workflow_data: dict[str, Any]) -> dict[str, Any]:
        """Extract metadata from a ComfyUI workflow."""
        if not isinstance(workflow_data, dict):
            return {}

        methods = self.extractor.get_methods()
        context = {}
        method_def = {}
        fields = {}

        return methods["comfy_extract_prompts"](workflow_data, method_def, context, fields)


# Keep the convenience functions for backward compatibility
def extract_a1111_parameters(param_string: str, logger=None) -> dict[str, Any]:
    """Convenience function to extract all A1111 parameters."""
    extractor = A1111ParameterExtractor(logger)
    return extractor.extract_all_parameters(param_string)


def extract_comfyui_metadata(workflow_data: dict[str, Any], logger=None) -> dict[str, Any]:
    """Convenience function to extract ComfyUI workflow metadata."""
    extractor = ComfyUIWorkflowExtractor(logger)
    return extractor.extract_workflow_metadata(workflow_data)
