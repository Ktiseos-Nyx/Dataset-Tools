# dataset_tools/metadata_engine/extractors/json_extractors.py

"""JSON processing extraction methods.

Handles parsing and extraction from JSON data structures,
including variable-based JSON parsing.
"""

import json
import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class JSONExtractor:
    """Handles JSON-specific extraction methods."""

    def __init__(self, logger: logging.Logger):
        """Initialize the JSON extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "json_from_string_variable": self._extract_json_from_string_variable,
            "json_path_exists_boolean": self._json_path_exists_boolean,
        }

    def _extract_json_from_string_variable(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict | list | None:
        """Parse JSON from a string stored in a variable."""
        source_var_key = method_def.get("source_variable_key")
        if not source_var_key:
            self.logger.warning("json_from_string_variable missing 'source_variable_key'")
            return None

        variable_name = source_var_key.replace(".", "_") + "_VAR_"
        string_to_parse = fields.get(variable_name)

        if not isinstance(string_to_parse, str):
            if string_to_parse is not None:
                self.logger.warning(
                    f"Variable '{variable_name}' is not a string (type: {type(string_to_parse)}), cannot parse as JSON"
                )
            return None

        try:
            result = json.loads(string_to_parse)
            self.logger.debug(f"Successfully parsed JSON from variable '{variable_name}'")
            return result
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON from variable '{variable_name}': {e}")
            return None

    def _json_path_exists_boolean(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Check if a JSON path exists in the data and return a boolean.

        This method addresses the missing 'json_path_exists_boolean' error mentioned by Gemini.
        Returns True if the specified JSON path exists, False otherwise.
        """
        json_path = method_def.get("json_path", method_def.get("path"))
        if not json_path:
            self.logger.warning("json_path_exists_boolean missing 'json_path' or 'path' parameter")
            return False

        try:
            # Navigate the JSON path
            current = data
            path_parts = json_path.split(".")

            for part in path_parts:
                if isinstance(current, dict):
                    if part in current:
                        current = current[part]
                    else:
                        return False
                elif isinstance(current, list):
                    try:
                        index = int(part)
                        if 0 <= index < len(current):
                            current = current[index]
                        else:
                            return False
                    except ValueError:
                        return False
                else:
                    return False

            # If we made it here, the path exists
            return True

        except Exception as e:
            self.logger.debug(f"Error checking JSON path '{json_path}': {e}")
            return False
