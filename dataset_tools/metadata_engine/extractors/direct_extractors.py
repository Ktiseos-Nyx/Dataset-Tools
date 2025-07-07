# dataset_tools/metadata_engine/extractors/direct_extractors.py

"""Direct value extraction methods.

Simple extractors that work with basic data types and direct value access.
"""

import logging
from typing import Any

from ..utils import json_path_get_utility

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class DirectValueExtractor:
    """Handles direct value extraction methods."""

    def __init__(self, logger: logging.Logger):
        """Initialize the direct value extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "direct_json_path": self._extract_direct_json_path,
            "static_value": self._extract_static_value,
            "direct_context_value": self._extract_direct_context_value,
            "direct_string_value": self._extract_direct_string_value,
        }

    def _extract_direct_json_path(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract value using JSON path query."""
        json_path = method_def.get("json_path")
        if not json_path:
            self.logger.warning("direct_json_path method missing 'json_path'")
            return None

        return json_path_get_utility(data, json_path)

    def _extract_static_value(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Return a static value."""
        return method_def.get("value")

    def _extract_direct_context_value(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Return the data directly."""
        return data

    def _extract_direct_string_value(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str | None:
        """Convert data to string."""
        return str(data) if data is not None else None
