# dataset_tools/metadata_engine/extractors/json_extractors.py

"""
JSON processing extraction methods.

Handles parsing and extraction from JSON data structures,
including variable-based JSON parsing.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

# Type aliases
ContextData = Dict[str, Any]
ExtractedFields = Dict[str, Any]
MethodDefinition = Dict[str, Any]


class JSONExtractor:
    """Handles JSON-specific extraction methods."""

    def __init__(self, logger: logging.Logger):
        """Initialize the JSON extractor."""
        self.logger = logger

    def get_methods(self) -> Dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "json_from_string_variable": self._extract_json_from_string_variable,
        }

    def _extract_json_from_string_variable(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> Optional[Union[Dict, List]]:
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
                    f"Variable '{variable_name}' is not a string "
                    f"(type: {type(string_to_parse)}), cannot parse as JSON"
                )
            return None

        try:
            result = json.loads(string_to_parse)
            self.logger.debug(f"Successfully parsed JSON from variable '{variable_name}'")
            return result
        except json.JSONDecodeError as e:
            self.logger.warning(
                f"Failed to parse JSON from variable '{variable_name}': {e}"
            )
            return None
