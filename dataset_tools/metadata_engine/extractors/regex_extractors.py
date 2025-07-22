# dataset_tools/metadata_engine/extractors/regex_extractors.py

"""Regex-based extraction methods.

Text processing extractors that use regular expressions for pattern matching
and extraction from text-based metadata.
"""

import logging
import re
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class RegexExtractor:
    """Handles regex-based text extraction methods."""

    def __init__(self, logger: logging.Logger):
        """Initialize the regex extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "regex_extract_group": self._extract_regex_group,
            "regex_extract_before_pattern": self._extract_before_pattern,
            "regex_extract_after_pattern": self._extract_after_pattern,
            "regex_extract_between_patterns": self._extract_between_patterns,
            "regex_replace_pattern": self._replace_pattern,
            "regex_split_on_pattern": self._split_on_pattern,
        }

    def _extract_regex_group(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract a specific group from a regex match.

        Method definition should contain:
        - pattern: The regex pattern to match
        - group: The group number to extract (default: 1)
        - value_type: Type conversion (string, integer, float)
        """
        if not isinstance(data, str):
            self.logger.debug("regex_extract_group: data is not a string")
            return None

        pattern = method_def.get("pattern")
        if not pattern:
            self.logger.warning("regex_extract_group method missing 'pattern'")
            return None

        group_num = method_def.get("group", 1)
        value_type = method_def.get("value_type", "string")

        try:
            match = re.search(pattern, data, re.IGNORECASE)
            if match and len(match.groups()) >= group_num:
                extracted_value = match.group(group_num)
                return self._convert_value_type(extracted_value, value_type)
            self.logger.debug(f"regex_extract_group: no match found for pattern '{pattern}' in data")
            return None
        except re.error as e:
            self.logger.error(f"regex_extract_group: invalid regex pattern '{pattern}': {e}")
            return None

    def _extract_before_pattern(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract text that appears before a specific pattern.

        Method definition should contain:
        - pattern: The regex pattern to match
        - value_type: Type conversion (default: string)
        """
        if not isinstance(data, str):
            self.logger.debug("regex_extract_before_pattern: data is not a string")
            return None

        pattern = method_def.get("pattern")
        if not pattern:
            self.logger.warning("regex_extract_before_pattern method missing 'pattern'")
            return None

        value_type = method_def.get("value_type", "string")

        try:
            match = re.search(pattern, data, re.IGNORECASE)
            if match:
                extracted_value = data[: match.start()].strip()
                return self._convert_value_type(extracted_value, value_type)
            # If no pattern match, return the entire string
            self.logger.debug(
                f"regex_extract_before_pattern: no match found for pattern '{pattern}', returning full text"
            )
            return self._convert_value_type(data.strip(), value_type)
        except re.error as e:
            self.logger.error(f"regex_extract_before_pattern: invalid regex pattern '{pattern}': {e}")
            return None

    def _extract_after_pattern(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract text that appears after a specific pattern.

        Method definition should contain:
        - pattern: The regex pattern to match
        - value_type: Type conversion (default: string)
        """
        if not isinstance(data, str):
            self.logger.debug("regex_extract_after_pattern: data is not a string")
            return None

        pattern = method_def.get("pattern")
        if not pattern:
            self.logger.warning("regex_extract_after_pattern method missing 'pattern'")
            return None

        value_type = method_def.get("value_type", "string")

        try:
            match = re.search(pattern, data, re.IGNORECASE)
            if match:
                extracted_value = data[match.end() :].strip()
                return self._convert_value_type(extracted_value, value_type)
            self.logger.debug(f"regex_extract_after_pattern: no match found for pattern '{pattern}'")
            return None
        except re.error as e:
            self.logger.error(f"regex_extract_after_pattern: invalid regex pattern '{pattern}': {e}")
            return None

    def _extract_between_patterns(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract text between two patterns.

        Method definition should contain:
        - start_pattern: The regex pattern for the start
        - end_pattern: The regex pattern for the end
        - value_type: Type conversion (default: string)
        """
        if not isinstance(data, str):
            self.logger.debug("regex_extract_between_patterns: data is not a string")
            return None

        start_pattern = method_def.get("start_pattern")
        end_pattern = method_def.get("end_pattern")

        if not start_pattern or not end_pattern:
            self.logger.warning("regex_extract_between_patterns method missing 'start_pattern' or 'end_pattern'")
            return None

        value_type = method_def.get("value_type", "string")

        try:
            start_match = re.search(start_pattern, data, re.IGNORECASE)
            if not start_match:
                self.logger.debug(f"regex_extract_between_patterns: no match found for start pattern '{start_pattern}'")
                return None

            remaining_text = data[start_match.end() :]
            end_match = re.search(end_pattern, remaining_text, re.IGNORECASE)

            if end_match:
                extracted_value = remaining_text[: end_match.start()].strip()
            else:
                # If no end pattern, take everything after start pattern
                extracted_value = remaining_text.strip()

            return self._convert_value_type(extracted_value, value_type)
        except re.error as e:
            self.logger.error(f"regex_extract_between_patterns: invalid regex pattern: {e}")
            return None

    def _replace_pattern(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Replace text matching a pattern with replacement text.

        Method definition should contain:
        - pattern: The regex pattern to match
        - replacement: The replacement text
        - value_type: Type conversion (default: string)
        """
        if not isinstance(data, str):
            self.logger.debug("regex_replace_pattern: data is not a string")
            return None

        pattern = method_def.get("pattern")
        replacement = method_def.get("replacement", "")

        if not pattern:
            self.logger.warning("regex_replace_pattern method missing 'pattern'")
            return None

        value_type = method_def.get("value_type", "string")

        try:
            result = re.sub(pattern, replacement, data, flags=re.IGNORECASE)
            return self._convert_value_type(result, value_type)
        except re.error as e:
            self.logger.error(f"regex_replace_pattern: invalid regex pattern '{pattern}': {e}")
            return None

    def _split_on_pattern(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Split text on a pattern and return specific part.

        Method definition should contain:
        - pattern: The regex pattern to split on
        - part_index: Which part to return (default: 0)
        - value_type: Type conversion (default: string)
        """
        if not isinstance(data, str):
            self.logger.debug("regex_split_on_pattern: data is not a string")
            return None

        pattern = method_def.get("pattern")
        if not pattern:
            self.logger.warning("regex_split_on_pattern method missing 'pattern'")
            return None

        part_index = method_def.get("part_index", 0)
        value_type = method_def.get("value_type", "string")

        try:
            parts = re.split(pattern, data, flags=re.IGNORECASE)
            if len(parts) > part_index:
                extracted_value = parts[part_index].strip()
                return self._convert_value_type(extracted_value, value_type)
            self.logger.debug(
                f"regex_split_on_pattern: not enough parts after split, got {len(parts)} parts, requested index {part_index}"
            )
            return None
        except re.error as e:
            self.logger.error(f"regex_split_on_pattern: invalid regex pattern '{pattern}': {e}")
            return None

    def _convert_value_type(self, value: Any, value_type: str) -> Any:
        """Convert value to the specified type."""
        if value is None:
            return None

        try:
            if value_type == "integer":
                return int(value)
            if value_type == "float":
                return float(value)
            if value_type == "boolean":
                return bool(value) if not isinstance(value, str) else value.lower() in ("true", "1", "yes", "on")
            # string or any other type
            return str(value).strip()
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to convert '{value}' to {value_type}: {e}")
            return value  # Return original value if conversion fails
