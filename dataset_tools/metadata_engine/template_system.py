# dataset_tools/metadata_engine/template_system.py

"""Template system for metadata output formatting.

This module handles the substitution of variables in output templates,
allowing dynamic generation of structured output based on extracted data.
Think of it as your macro system in FFXIV - predefined actions that get
filled in with the right data! ⚙️✨

The template system supports:
- Variable substitution from extracted fields
- Context data references
- Special placeholder handling
- Nested template structures
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Union

# Assumed to exist based on your other files
from ..logger import get_logger
from .utils import json_path_get_utility

# Type aliases
TemplateData = Union[dict[str, Any], list[Any], str, int, float, bool, None]
ExtractedFields = dict[str, Any]
ContextData = dict[str, Any]


class TemplateProcessor:
    """Processes templates with variable substitution.

    This class handles the transformation of template structures by
    substituting variables with actual values from extracted fields
    and context data.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize the template processor."""
        self.logger = logger or get_logger("TemplateProcessor")
        self.variable_pattern = re.compile(r"\$([\w.]+)")
        self._special_handlers = {
            "INPUT_STRING_ORIGINAL_CHUNK": self._handle_input_string_original,
            "INPUT_JSON_OBJECT_AS_STRING": self._handle_input_json_as_string,
            "CURRENT_TIMESTAMP": self._handle_current_timestamp,
            "FILE_PATH": self._handle_file_path,
            "FILE_NAME": self._handle_file_name,
            "FILE_EXTENSION": self._handle_file_extension,
        }
        self._original_input_data: str | None = None
        self._input_json_object: dict | list | None = None
        self._context_data: ContextData = {}

    def process_template(
        self,
        template: TemplateData,
        extracted_fields: ExtractedFields,
        context_data: ContextData,
        original_input_data: str | None = None,
        input_json_object: dict | list | None = None,
    ) -> TemplateData:
        """Process a template with variable substitution."""
        self.logger.debug("Processing template with variable substitution")
        self._original_input_data = original_input_data
        self._input_json_object = input_json_object
        self._context_data = context_data
        return self._process_recursive(template, extracted_fields, context_data)

    def _process_recursive(
        self,
        template: TemplateData,
        extracted_fields: ExtractedFields,
        context_data: ContextData,
    ) -> TemplateData:
        """Recursively process template structures."""
        if isinstance(template, dict):
            return {
                key: self._process_recursive(value, extracted_fields, context_data) for key, value in template.items()
            }
        if isinstance(template, list):
            return [self._process_recursive(item, extracted_fields, context_data) for item in template]
        if isinstance(template, str):
            return self._substitute_variables(template, extracted_fields, context_data)
        return template

    def _substitute_variables(
        self,
        template_string: str,
        extracted_fields: ExtractedFields,
        context_data: ContextData,
    ) -> str:
        """Substitute variables in a template string."""

        def replacer(match: re.Match) -> str:
            var_path = match.group(1)
            # 1. Handle special variables
            if var_path in self._special_handlers:
                return self._special_handlers[var_path]()
            # 2. Handle context variables
            if var_path.startswith("CONTEXT."):
                context_path = var_path.replace("CONTEXT.", "", 1)
                value = json_path_get_utility(context_data, context_path)
                return str(value) if value is not None else ""
            # 3. Handle regular field variables
            value = json_path_get_utility(extracted_fields, var_path)
            if value is not None:
                return str(value)
            self.logger.debug(f"Template variable '${var_path}' not found, replacing with empty string")
            return ""

        return self.variable_pattern.sub(replacer, template_string)

    def _handle_input_string_original(self) -> str:
        return str(self._original_input_data) if self._original_input_data is not None else ""

    def _handle_input_json_as_string(self) -> str:
        return json.dumps(self._input_json_object, indent=2) if self._input_json_object is not None else ""

    def _handle_current_timestamp(self) -> str:
        import datetime

        return datetime.datetime.now().isoformat()

    def _handle_file_path(self) -> str:
        return str(self._context_data.get("file_path_original", ""))

    def _handle_file_name(self) -> str:
        file_path = self._context_data.get("file_path_original", "")
        return Path(file_path).name if file_path else ""

    def _handle_file_extension(self) -> str:
        return str(self._context_data.get("file_extension", ""))


class TemplateValidator:
    """Validates template structures and variable references."""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or get_logger("TemplateValidator")
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.variable_pattern = re.compile(r"\$([\w.]+)")

    def validate_template(
        self,
        template: TemplateData,
        available_fields: list[str],
        available_context_keys: list[str],
    ) -> bool:
        """Validates a template, returning True if valid."""
        self.errors.clear()
        self.warnings.clear()
        self._validate_recursive(template, available_fields, available_context_keys)
        return len(self.errors) == 0

    def _validate_recursive(self, template: TemplateData, fields: list[str], context_keys: list[str]):
        if isinstance(template, dict):
            [self._validate_recursive(v, fields, context_keys) for v in template.values()]
        elif isinstance(template, list):
            [self._validate_recursive(i, fields, context_keys) for i in template]
        elif isinstance(template, str):
            self._validate_string_template(template, fields, context_keys)

    def _validate_string_template(self, t_string: str, fields: list[str], context_keys: list[str]):
        special_vars = [
            "INPUT_STRING_ORIGINAL_CHUNK",
            "INPUT_JSON_OBJECT_AS_STRING",
            "CURRENT_TIMESTAMP",
            "FILE_PATH",
            "FILE_NAME",
            "FILE_EXTENSION",
        ]
        for match in self.variable_pattern.finditer(t_string):
            var = match.group(1)
            if var in special_vars:
                continue
            if var.startswith("CONTEXT."):
                if var.split(".")[1] not in context_keys:
                    self.warnings.append(f"Context var '${var}' may not be available.")
            elif var.split(".")[0] not in fields:
                self.warnings.append(f"Field var '${var}' may not be available.")


class StandardTemplates:
    """Collection of standard templates for common AI tools."""

    @staticmethod
    def a1111_template() -> dict[str, Any]:
        return {
            "tool": "AUTOMATIC1111",
            "prompt": "$prompt",
            "negative_prompt": "$negative_prompt",
            "parameters": {
                "steps": "$parameters.steps",
                "sampler": "$parameters.sampler",
                "cfg_scale": "$parameters.cfg_scale",
                "seed": "$parameters.seed",
                "width": "$CONTEXT.width",
                "height": "$CONTEXT.height",
                "model": "$parameters.model",
                "model_hash": "$parameters.model_hash",
                "version": "$parameters.version",
            },
        }


class TemplateBuilder:
    """Builder class for creating template structures programmatically."""

    def __init__(self):
        self.template_data: dict[str, Any] = {}

    def add_field(self, key: str, value: Any) -> "TemplateBuilder":
        self.template_data[key] = value
        return self

    def add_variable(self, key: str, var_name: str) -> "TemplateBuilder":
        self.template_data[key] = f"${var_name}"
        return self

    @classmethod
    def create_standard_ai_template(cls, tool_name: str, **kwargs) -> "TemplateBuilder":
        builder = cls().add_field("tool", tool_name)
        if kwargs.get("include_prompts", True):
            builder.add_variable("prompt", "prompt").add_variable("negative_prompt", "negative_prompt")
        if kwargs.get("extra_fields"):
            [builder.add_variable(k, v) for k, v in kwargs["extra_fields"].items()]
        return builder

    def build(self) -> dict[str, Any]:
        return self.template_data


class OutputFormatter:
    """Formats processed templates into different output structures."""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or get_logger("OutputFormatter")

    def format_output(
        self,
        processed_template: TemplateData,
        context_data: ContextData | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        if not isinstance(processed_template, dict):
            self.logger.warning("Processed template is not a dictionary; wrapping it.")
            processed_template = {"data": processed_template}
        output = processed_template.copy()
        if kwargs.get("cleanup_empty", True):
            output = self._cleanup_empty_values(output)
        format_type = kwargs.get("format_type", "standard")
        if format_type == "standard":
            output = self._apply_standard_formatting(output, context_data or {})
        elif format_type == "minimal":
            output = self._apply_minimal_formatting(output)
        if kwargs.get("add_metadata", True):
            output = self._add_processing_metadata(output)
        return output

    def _apply_standard_formatting(self, output: dict[str, Any], context: ContextData) -> dict[str, Any]:
        formatted = output.copy()
        if "tool" in formatted and isinstance(formatted.get("tool"), str):
            formatted["tool"] = formatted["tool"].strip()
        if "parameters" in formatted and isinstance(formatted.get("parameters"), dict):
            if "width" not in formatted["parameters"] and context.get("width", 0) > 0:
                formatted["parameters"]["width"] = context["width"]
            if "height" not in formatted["parameters"] and context.get("height", 0) > 0:
                formatted["parameters"]["height"] = context["height"]
        return formatted

    def _apply_minimal_formatting(self, output: dict[str, Any]) -> dict[str, Any]:
        return {
            f: output[f]
            for f in ["tool", "prompt", "parameters"]
            if f in output and not self._is_empty_value(output[f])
        }

    def _add_processing_metadata(self, output: dict[str, Any]) -> dict[str, Any]:
        if "_metadata" not in output:
            output["_metadata"] = {}
        output["_metadata"].update(
            {
                "processed_at": __import__("datetime").datetime.now().isoformat(),
                "processor": "MetadataEngine",
                "template_processed": True,
            }
        )
        return output

    def _cleanup_empty_values(self, data: TemplateData) -> TemplateData:
        if isinstance(data, dict):
            return {
                k: v
                for k, v in ((k, self._cleanup_empty_values(v)) for k, v in data.items())
                if not self._is_empty_value(v)
            }
        if isinstance(data, list):
            return [v for item in data if not self._is_empty_value(v := self._cleanup_empty_values(item))]
        return data

    def _is_empty_value(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, (dict, list)) and not value:
            return True
        return False


# ============================================================================
# CONVENIENCE FUNCTIONS (To satisfy __init__.py imports)
# ============================================================================


def process_template(
    template: TemplateData,
    extracted_fields: ExtractedFields,
    context_data: ContextData,
    **kwargs,
) -> TemplateData:
    """Convenience function to process a template without manually creating a processor."""
    processor = TemplateProcessor(kwargs.get("logger"))
    return processor.process_template(template, extracted_fields, context_data, **kwargs)


def format_template_output(processed_template: TemplateData, context_data: ContextData, **kwargs) -> dict[str, Any]:
    """Convenience function to format template output."""
    formatter = OutputFormatter(kwargs.get("logger"))
    return formatter.format_output(processed_template, context_data, **kwargs)


# ============================================================================
# TESTING UTILITIES
# ============================================================================


def test_template_system():
    """Test the template system with sample data."""
    logger = get_logger("TemplateSystemTest")
    logging.basicConfig(level=logging.INFO)
    extracted = {
        "prompt": "beautiful landscape",
        "negative_prompt": "blurry",
        "parameters": {"steps": 20, "sampler": "Euler a", "seed": 42},
        "tool_name": "TestTool",
    }
    context = {
        "width": 512,
        "height": 768,
        "file_path_original": "test.png",
        "file_extension": "png",
    }
    template = StandardTemplates.a1111_template()
    logger.info("--- Testing Template Processing ---")
    processed = process_template(template, extracted, context)
    logger.info(f"Processed template: {json.dumps(processed, indent=2)}")
    logger.info("\n--- Testing Output Formatting ---")
    formatted = format_template_output(processed, context_data=context)
    logger.info(f"Formatted output: {json.dumps(formatted, indent=2)}")


if __name__ == "__main__":
    test_template_system()
