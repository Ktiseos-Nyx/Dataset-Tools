# dataset_tools/metadata_engine/rule_engine.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Rule-based evaluation engine for metadata parser detection.

This module provides a sophisticated rule evaluation system that can determine
which metadata parser should be used for a given file based on configurable
TOML rules and complex conditional logic.
"""

import json
import re
from pathlib import Path
from typing import Any

import toml

from ..logger import get_logger
from .utils import json_path_get_utility

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

RuleDict = dict[str, Any]
ContextData = dict[str, Any]
RuleResult = bool

# ============================================================================
# RULE OPERATORS
# ============================================================================


class RuleOperators:
    """Collection of rule operators for evaluating conditions.

    Each operator method takes the data to check, rule configuration,
    and context data, returning a boolean result.
    """

    def __init__(self, logger):
        self.logger = logger

    def exists(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data exists (is not None)."""
        return data is not None

    def not_exists(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data does not exist (is None)."""
        return data is None

    def is_none(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data is None."""
        return data is None

    def is_not_none(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data is not None."""
        return data is not None

    def equals(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data equals expected value."""
        expected = rule.get("value")
        if data is None and expected is not None:
            return False
        if data is not None and expected is None:
            return False
        if data is None and expected is None:
            return True
        return str(data).strip() == str(expected).strip()

    def equals_case_insensitive(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data equals expected value (case insensitive)."""
        expected = rule.get("value")
        if data is None and expected is not None:
            return False
        if data is not None and expected is None:
            return False
        if data is None and expected is None:
            return True
        return str(data).strip().lower() == str(expected).strip().lower()

    def contains(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data contains expected value."""
        if not isinstance(data, str):
            return False
        expected = rule.get("value")
        return str(expected) in data

    def contains_case_insensitive(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data contains expected value (case insensitive)."""
        if not isinstance(data, str):
            return False
        expected = rule.get("value")
        return str(expected).lower() in data.lower()

    def does_not_contain(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data does not contain expected value."""
        if not isinstance(data, str):
            return True  # Non-strings don't contain the value
        expected = rule.get("value")
        return str(expected) not in data

    def startswith(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data starts with expected value."""
        if not isinstance(data, str):
            return False
        expected = rule.get("value")
        return data.startswith(str(expected))

    def endswith(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data ends with expected value."""
        if not isinstance(data, str):
            return False
        expected = rule.get("value")
        return data.endswith(str(expected))

    def regex_match(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data matches regex pattern."""
        if not isinstance(data, str):
            return False
        pattern = rule.get("regex_pattern")
        if not pattern:
            self.logger.warning("regex_match operator missing 'regex_pattern'")
            return False
        return re.search(pattern, data) is not None

    def regex_match_all(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data matches all regex patterns."""
        if not isinstance(data, str):
            return False
        patterns = rule.get("regex_patterns")
        if not patterns or not isinstance(patterns, list):
            self.logger.warning("regex_match_all operator missing 'regex_patterns' list")
            return False
        return all(re.search(pattern, data) for pattern in patterns)

    def regex_match_any(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data matches any regex patterns."""
        if not isinstance(data, str):
            return False
        patterns = rule.get("regex_patterns")
        if not patterns or not isinstance(patterns, list):
            self.logger.warning("regex_match_any operator missing 'regex_patterns' list")
            return False
        return any(re.search(pattern, data) for pattern in patterns)

    def is_string(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data is a string."""
        return isinstance(data, str)

    def is_true(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data is True (with special handling for complex queries)."""
        source_type = rule.get("source_type")
        if source_type == "pil_info_key_json_path_query":
            return self._handle_json_path_query(data, rule)
        return data is True

    def is_in_list(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data is in a list of values."""
        if data is None:
            return False
        value_list = rule.get("value_list")
        if not value_list or not isinstance(value_list, list):
            self.logger.warning("is_in_list operator missing 'value_list'")
            return False
        return str(data) in value_list

    def is_valid_json(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data is valid JSON."""
        source_type = rule.get("source_type")
        if source_type == "file_content_json":
            return isinstance(context.get("parsed_root_json_object"), (dict, list))

        if isinstance(data, (dict, list)):
            return True
        if not isinstance(data, str):
            return False

        try:
            json.loads(data)
            return True
        except json.JSONDecodeError:
            return False

    def is_valid_json_structure(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if context has valid JSON structure."""
        return isinstance(context.get("parsed_root_json_object"), (dict, list))

    def json_path_exists(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if JSON path exists in data."""
        json_path = rule.get("json_path")
        if not json_path:
            self.logger.warning("json_path_exists operator missing 'json_path'")
            return False

        target_obj = self._get_json_object(data)
        if target_obj is None:
            return False

        return json_path_get_utility(target_obj, json_path) is not None

    def json_path_value_equals(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if value at JSON path equals expected value."""
        json_path = rule.get("json_path")
        expected = rule.get("value")

        if not json_path:
            self.logger.warning("json_path_value_equals operator missing 'json_path'")
            return False

        target_obj = self._get_json_object(data)
        if target_obj is None:
            return False

        value_at_path = json_path_get_utility(target_obj, json_path)

        if value_at_path is None and expected is not None:
            return False
        if value_at_path is not None and expected is None:
            return False
        if value_at_path is None and expected is None:
            return True

        return str(value_at_path).strip() == str(expected).strip()

    def json_contains_any_key(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if JSON object contains any of the expected keys."""
        expected_keys = rule.get("expected_keys")
        if not expected_keys or not isinstance(expected_keys, list):
            self.logger.warning("json_contains_any_key operator missing 'expected_keys' list")
            return False

        target_obj = self._get_json_object(data)
        if not isinstance(target_obj, dict):
            return False

        return any(key in target_obj for key in expected_keys)

    def json_contains_all_keys(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if JSON object contains all expected keys."""
        expected_keys = rule.get("expected_keys")
        if not expected_keys or not isinstance(expected_keys, list):
            self.logger.warning("json_contains_all_keys operator missing 'expected_keys' list")
            return False

        target_obj = self._get_json_object(data)
        if not isinstance(target_obj, dict):
            return False

        return all(key in target_obj for key in expected_keys)

    def has_keys(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data (expected to be a dict) contains all specified keys."""
        expected_keys = rule.get("value")  # Using 'value' as per the parser definition
        if not isinstance(data, dict):
            self.logger.debug(f"has_keys operator: data is not a dictionary (type: {type(data)})")
            return False
        if not isinstance(expected_keys, list) or not expected_keys:
            self.logger.warning("has_keys operator: 'value' must be a non-empty list of keys")
            return False
        return all(key in data for key in expected_keys)

    def exists_and_is_dictionary(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data exists and is a non-empty dictionary."""
        is_dict = isinstance(data, dict)
        is_not_empty = bool(data) if is_dict else False

        self.logger.debug(
            f"exists_and_is_dictionary: data type {type(data)}, is_dict={is_dict}, is_not_empty={is_not_empty}"
        )

        return is_dict and is_not_empty

    def not_strictly_simple_json_object_with_prompt_key(self, data: Any, rule: RuleDict, context: ContextData) -> bool:
        """Check if data is NOT a simple JSON object with prompt key."""
        if not isinstance(data, str):
            return False

        try:
            parsed_json = json.loads(data)
            if isinstance(parsed_json, dict):
                has_prompt_key = any(key in parsed_json for key in ["prompt", "Prompt", "positive_prompt"])
                if has_prompt_key:
                    return False  # It IS a simple JSON with prompt, so return False
        except json.JSONDecodeError:
            return True  # Not JSON, so it's not a simple JSON object

        return True  # Wasn't the specific structure we're avoiding

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_json_object(self, data: Any) -> dict | list | None:
        """Convert data to JSON object if possible."""
        if isinstance(data, (dict, list)):
            return data

        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                self.logger.debug("Data string is not valid JSON")
                return None

        self.logger.debug(f"Data type {type(data)} not suitable for JSON operations")
        return None

    def _handle_json_path_query(self, data: Any, rule: RuleDict) -> bool:
        """Handle complex JSON path queries for is_true operator."""
        if not isinstance(data, str):
            self.logger.debug(f"Expected string data for JSON path query, got {type(data)}")
            return False

        json_query_type = rule.get("json_query_type")
        if not json_query_type:
            self.logger.warning("JSON path query missing 'json_query_type'")
            return False

        try:
            json_obj = json.loads(data)

            if json_query_type == "has_numeric_string_keys":
                return isinstance(json_obj, dict) and any(key.isdigit() for key in json_obj)

            if json_query_type == "has_any_node_class_type":
                class_types = rule.get("class_types_to_check")
                if not class_types or not isinstance(class_types, list):
                    self.logger.warning("Query 'has_any_node_class_type' missing 'class_types_to_check'")
                    return False

                if not isinstance(json_obj, dict):
                    return False

                nodes_container = json_obj.get("nodes", json_obj)
                if not isinstance(nodes_container, dict):
                    return False

                return any(
                    isinstance(node_val, dict) and node_val.get("type") in class_types
                    for node_val in nodes_container.values()
                )

            self.logger.warning(f"Unknown json_query_type: {json_query_type}")
            return False

        except json.JSONDecodeError:
            self.logger.debug("Data is not valid JSON for path query")
            return False


# ============================================================================
# DATA SOURCE HANDLERS
# ============================================================================


class DataSourceHandler:
    """Handles extraction of data from various sources for rule evaluation.

    This class knows how to extract data from different source types
    like PIL info, EXIF data, XMP strings, etc.
    """

    def __init__(self, logger):
        self.logger = logger

    def get_source_data(self, rule: RuleDict, context: ContextData) -> tuple[Any, bool]:
        """Extract source data based on rule configuration.

        Args:
            rule: Rule dictionary containing source configuration
            context: Context data dictionary

        Returns:
            Tuple of (data, found) where found indicates if data was located

        """
        source_type = rule.get("source_type")
        source_key = rule.get("source_key")

        # Simple direct lookups
        simple_sources = {
            "pil_info_key": lambda: context.get("pil_info", {}).get(source_key),
            "png_chunk": lambda: context.get("png_chunks", {}).get(source_key),
            "software_tag": lambda: context.get("software_tag"),
            "exif_software_tag": lambda: context.get("software_tag"),
            "exif_user_comment": lambda: context.get("raw_user_comment_str"),
            "exif_field": lambda: context.get("exif_dict", {}).get("0th", {}).get(source_key),
            "xmp_string_content": lambda: context.get("xmp_string"),
            "file_format": lambda: context.get("file_format"),
            "file_extension": lambda: context.get("file_extension"),
            "raw_file_content_text": lambda: context.get("raw_file_content_text"),
            "parsed_root_json_object": lambda: context.get("parsed_root_json_object"),
            "direct_context_key": lambda: context.get(source_key),
            "pil_info_pil_mode": lambda: context.get("pil_mode"),
            "pil_info_object": lambda: context.get("pil_info"),
            "context_iptc_field_value": lambda: context.get("parsed_iptc", {}).get(rule.get("iptc_field_name")),
        }

        if source_type in simple_sources:
            data = simple_sources[source_type]()
            return data, data is not None

        # Complex source types
        if source_type == "pil_info_key_or_exif_user_comment_json_path":
            return self._handle_pil_info_or_exif_json_path(rule, context)

        if source_type == "direct_context_key_path_value":
            data = json_path_get_utility(context, source_key)
            return data, data is not None

        if source_type == "auto_detect_parameters_or_usercomment":
            param_str = context.get("pil_info", {}).get("parameters")
            uc_str = context.get("raw_user_comment_str")
            data = param_str if param_str is not None else uc_str
            return data, data is not None

        if source_type == "a1111_parameter_string_content":
            return self._handle_a1111_parameter_string(context)

        if source_type == "any_metadata_source":
            return self._handle_any_metadata_source(rule, context)

        if source_type == "pil_info_key_json_path" or source_type == "pil_info_key_json_path_string_is_json":
            return self._handle_pil_info_json_path(rule, context)

        # TODO: Implement these complex types when needed
        if source_type in [
            "json_from_xmp_exif_user_comment",
            "json_from_usercomment_or_png_chunk",
            "pil_info_key_json_path_query",
        ]:
            self.logger.warning(f"Source type '{source_type}' is not yet implemented")
            return None, False

        if source_type is not None:
            self.logger.warning(f"Unknown source_type: '{source_type}'")
        else:
            self.logger.debug("Rule missing 'source_type'")
        return None, False

    def _handle_pil_info_or_exif_json_path(self, rule: RuleDict, context: ContextData) -> tuple[Any, bool]:
        """Handle PIL info or EXIF user comment JSON path extraction."""
        json_path = rule.get("json_path")
        source_key = rule.get("source_key")

        # Try PIL info first
        initial_json_str = None
        if source_key and source_key in context.get("pil_info", {}):
            initial_json_str = context["pil_info"].get(source_key)

        # Fall back to user comment
        if not initial_json_str:
            initial_json_str = context.get("raw_user_comment_str")

        if not isinstance(initial_json_str, str):
            return None, False

        try:
            parsed_json = json.loads(initial_json_str)
            data = json_path_get_utility(parsed_json, json_path)
            return data, data is not None
        except json.JSONDecodeError:
            return None, False

    def _handle_a1111_parameter_string(self, context: ContextData) -> tuple[Any, bool]:
        """Handle A1111 parameter string extraction."""
        # Try parameters chunk first
        param_str = context.get("pil_info", {}).get("parameters")
        if param_str is None:
            param_str = context.get("raw_user_comment_str")

        if param_str is None:
            return None, False

        # Check if it's wrapped in JSON
        try:
            wrapper = json.loads(param_str)
            if isinstance(wrapper, dict) and "parameters" in wrapper and isinstance(wrapper["parameters"], str):
                return wrapper["parameters"], True
        except json.JSONDecodeError:
            pass

        return param_str, True

    def _handle_pil_info_json_path(self, rule: RuleDict, context: ContextData) -> tuple[Any, bool]:
        """Handle PIL info JSON path extraction."""
        source_keys = rule.get("source_key_options") or [rule.get("source_key")]
        json_path = rule.get("json_path")

        initial_json_str = None
        for source_key in source_keys:
            if source_key and source_key in context.get("pil_info", {}):
                initial_json_str = context["pil_info"].get(source_key)
                if initial_json_str is not None:
                    break

        if not isinstance(initial_json_str, str):
            return None, False

        try:
            parsed_json = json.loads(initial_json_str)
            value_at_path = json_path_get_utility(parsed_json, json_path)
            return value_at_path, value_at_path is not None
        except json.JSONDecodeError:
            self.logger.debug("Could not parse JSON for JSON path rule")
            return None, False

    def _handle_any_metadata_source(self, rule: RuleDict, context: ContextData) -> tuple[Any, bool]:
        """Handle any metadata source - checks PNG chunks, EXIF UserComment, etc."""
        # Try PNG chunks first (for PNG files)
        png_chunks = context.get("pil_info", {})
        for chunk_key in ["prompt", "workflow", "parameters"]:
            chunk_data = png_chunks.get(chunk_key)
            if chunk_data is not None:
                return chunk_data, True

        # Try EXIF UserComment (for JPEG files)
        user_comment = context.get("raw_user_comment_str")
        if user_comment is not None:
            return user_comment, True

        # Try XMP string
        xmp_string = context.get("xmp_string")
        if xmp_string is not None:
            return xmp_string, True

        # No metadata found
        return None, False


# ============================================================================
# MAIN RULE ENGINE
# ============================================================================


class RuleEngine:
    """Main rule evaluation engine.

    This class coordinates rule evaluation by loading rules from TOML files
    and applying them to context data using the appropriate operators and
    data source handlers.
    """

    def __init__(self, config_path: Path | None = None, logger=None):
        """Initialize the rule engine.

        Args:
            config_path: Path to rules.toml file
            logger: Logger instance to use

        """
        self.logger = logger or get_logger("RuleEngine")
        self.rules: list[RuleDict] = []

        # Initialize handlers
        self.operators = RuleOperators(self.logger)
        self.data_source = DataSourceHandler(self.logger)

        # Load rules if config path provided
        if config_path:
            self.load_rules(config_path)

    def load_rules(self, config_path: Path) -> None:
        """Load rules from a TOML configuration file.

        Args:
            config_path: Path to the rules.toml file

        """
        self.logger.debug(f"Loading rules from: {config_path}")

        if not config_path.is_file():
            self.logger.warning(f"Rules file not found: {config_path}")
            return

        try:
            with open(config_path, encoding="utf-8") as f:
                config = toml.load(f)

            # Load global rules
            if "global_rules" in config:
                self.rules.extend(config["global_rules"])

            # Load parser-specific rules
            if "parsers" in config:
                for parser_name, parser_config in config["parsers"].items():
                    if "detection_rules" in parser_config:
                        for rule in parser_config["detection_rules"]:
                            rule["parser_name"] = parser_name
                        self.rules.extend(parser_config["detection_rules"])

            self.logger.info(f"Loaded {len(self.rules)} rules from {config_path}")

        except Exception as e:
            self.logger.error(f"Failed to load rules from {config_path}: {e}", exc_info=True)

    def evaluate_rule(self, rule: RuleDict, context: ContextData) -> RuleResult:
        """Evaluate a single rule against context data.

        Args:
            rule: Rule dictionary to evaluate
            context: Context data dictionary

        Returns:
            Boolean result of rule evaluation

        """
        try:
            # Handle complex rules (AND/OR conditions)
            if "condition" in rule and "rules" in rule:
                return self._evaluate_complex_rule(rule, context)

            # Handle simple rules
            return self._evaluate_simple_rule(rule, context)

        except Exception as e:
            rule_comment = rule.get("comment", f"source_type: {rule.get('source_type')}")
            self.logger.error(f"Error evaluating rule '{rule_comment}': {e}", exc_info=True)
            return False

    def _evaluate_complex_rule(self, rule: RuleDict, context: ContextData) -> RuleResult:
        """Evaluate a complex rule with AND/OR conditions."""
        condition = rule.get("condition", "").upper()
        sub_rules = rule.get("rules", [])

        if not sub_rules:
            self.logger.warning("Complex rule has no sub-rules")
            return False

        if condition == "OR":
            return any(self.evaluate_rule(sub_rule, context) for sub_rule in sub_rules)
        if condition == "AND":
            return all(self.evaluate_rule(sub_rule, context) for sub_rule in sub_rules)
        self.logger.warning(f"Unknown complex condition: '{condition}'")
        return False

    def _evaluate_simple_rule(self, rule: RuleDict, context: ContextData) -> RuleResult:
        """Evaluate a simple rule."""
        operator = rule.get("operator", "exists")

        # Get source data
        data, source_found = self.data_source.get_source_data(rule, context)

        # Check if source was found for operators that require it
        if not source_found and operator not in ["not_exists", "is_none"]:
            rule_comment = rule.get("comment", f"source_type: {rule.get('source_type')}")
            self.logger.debug(f"Source data not found for rule: {rule_comment}")
            return False

        # Apply operator
        return self._apply_operator(operator, data, rule, context)

    def _apply_operator(self, operator: str, data: Any, rule: RuleDict, context: ContextData) -> RuleResult:
        """Apply the specified operator to the data."""
        # Get operator method
        self.logger.debug(f"_apply_operator: Checking for operator '{operator}' on {type(self.operators)}")
        operator_method = getattr(self.operators, operator, None)

        if operator_method is None:
            self.logger.warning(f"Unknown operator: '{operator}'")
            self.logger.debug(
                f"_apply_operator: hasattr(self.operators, '{operator}') returned {hasattr(self.operators, operator)}"
            )
            return False

        try:
            return operator_method(data, rule, context)
        except Exception as e:
            rule_comment = rule.get("comment", "Unnamed rule")
            self.logger.error(
                f"Error applying operator '{operator}' for rule '{rule_comment}': {e}",
                exc_info=True,
            )
            return False

    def get_rules_for_parser(self, parser_name: str) -> list[RuleDict]:
        """Get all rules associated with a specific parser.

        Args:
            parser_name: Name of the parser

        Returns:
            List of rules for the parser

        """
        return [rule for rule in self.rules if rule.get("parser_name") == parser_name]

    def evaluate_parser_rules(self, parser_name: str, context: ContextData) -> bool:
        """Evaluate all rules for a specific parser.

        Args:
            parser_name: Name of the parser
            context: Context data dictionary

        Returns:
            True if all rules pass, False otherwise

        """
        parser_rules = self.get_rules_for_parser(parser_name)

        if not parser_rules:
            self.logger.debug(f"No rules found for parser: {parser_name}")
            return True  # No rules means no restrictions

        for rule in parser_rules:
            if not self.evaluate_rule(rule, context):
                return False

        return True

    def get_matching_parsers(self, context: ContextData) -> list[str]:
        """Get list of parser names that match the context data.

        Args:
            context: Context data dictionary

        Returns:
            List of matching parser names

        """
        matching_parsers = []
        parser_names = set(rule.get("parser_name") for rule in self.rules if rule.get("parser_name"))

        for parser_name in parser_names:
            if self.evaluate_parser_rules(parser_name, context):
                matching_parsers.append(parser_name)

        return matching_parsers

    def clear_rules(self) -> None:
        """Clear all loaded rules."""
        self.rules.clear()
        self.logger.debug("All rules cleared")

    def get_rule_count(self) -> int:
        """Get the total number of loaded rules."""
        return len(self.rules)

    def get_parser_names(self) -> list[str]:
        """Get list of all parser names that have rules."""
        return list(set(rule.get("parser_name") for rule in self.rules if rule.get("parser_name")))


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def create_rule_engine(config_path: Path | None = None) -> RuleEngine:
    """Create a rule engine instance with default configuration.

    Args:
        config_path: Optional path to rules configuration file

    Returns:
        Configured RuleEngine instance

    """
    return RuleEngine(config_path)


def evaluate_detection_rules(rules: list[RuleDict], context: ContextData, logger=None) -> bool:
    """Evaluate a list of detection rules against context data.

    Args:
        rules: List of rule dictionaries
        context: Context data dictionary
        logger: Optional logger instance

    Returns:
        True if all rules pass, False otherwise

    """
    engine = RuleEngine(logger=logger)
    engine.rules = rules

    for rule in rules:
        if not engine.evaluate_rule(rule, context):
            return False

    return True


# ============================================================================
# RULE BUILDER HELPERS
# ============================================================================


class RuleBuilder:
    """Helper class for building rule dictionaries programmatically.

    This provides a fluent interface for creating rules without having
    to manually construct dictionary structures.
    """

    def __init__(self):
        self.rule_data: RuleDict = {}

    def source_type(self, source_type: str) -> "RuleBuilder":
        """Set the source type for the rule."""
        self.rule_data["source_type"] = source_type
        return self

    def source_key(self, source_key: str) -> "RuleBuilder":
        """Set the source key for the rule."""
        self.rule_data["source_key"] = source_key
        return self

    def operator(self, operator: str) -> "RuleBuilder":
        """Set the operator for the rule."""
        self.rule_data["operator"] = operator
        return self

    def value(self, value: Any) -> "RuleBuilder":
        """Set the expected value for the rule."""
        self.rule_data["value"] = value
        return self

    def regex_pattern(self, pattern: str) -> "RuleBuilder":
        """Set a regex pattern for the rule."""
        self.rule_data["regex_pattern"] = pattern
        return self

    def regex_patterns(self, patterns: list[str]) -> "RuleBuilder":
        """Set multiple regex patterns for the rule."""
        self.rule_data["regex_patterns"] = patterns
        return self

    def json_path(self, path: str) -> "RuleBuilder":
        """Set a JSON path for the rule."""
        self.rule_data["json_path"] = path
        return self

    def expected_keys(self, keys: list[str]) -> "RuleBuilder":
        """Set expected keys for JSON operations."""
        self.rule_data["expected_keys"] = keys
        return self

    def comment(self, comment: str) -> "RuleBuilder":
        """Add a comment to the rule."""
        self.rule_data["comment"] = comment
        return self

    def optional(self, is_optional: bool = True) -> "RuleBuilder":
        """Mark the rule as optional."""
        self.rule_data["optional"] = is_optional
        return self

    def build(self) -> RuleDict:
        """Build and return the rule dictionary."""
        return self.rule_data.copy()

    @classmethod
    def create(cls) -> "RuleBuilder":
        """Create a new rule builder instance."""
        return cls()

    @classmethod
    def exists_rule(cls, source_type: str, source_key: str = None, comment: str = None) -> RuleDict:
        """Create a simple exists rule."""
        builder = cls().source_type(source_type).operator("exists")
        if source_key:
            builder.source_key(source_key)
        if comment:
            builder.comment(comment)
        return builder.build()

    @classmethod
    def equals_rule(cls, source_type: str, value: Any, source_key: str = None, comment: str = None) -> RuleDict:
        """Create a simple equals rule."""
        builder = cls().source_type(source_type).operator("equals").value(value)
        if source_key:
            builder.source_key(source_key)
        if comment:
            builder.comment(comment)
        return builder.build()

    @classmethod
    def regex_rule(cls, source_type: str, pattern: str, source_key: str = None, comment: str = None) -> RuleDict:
        """Create a simple regex rule."""
        builder = cls().source_type(source_type).operator("regex_match").regex_pattern(pattern)
        if source_key:
            builder.source_key(source_key)
        if comment:
            builder.comment(comment)
        return builder.build()

    @classmethod
    def json_path_rule(
        cls,
        source_type: str,
        json_path: str,
        source_key: str = None,
        comment: str = None,
    ) -> RuleDict:
        """Create a JSON path exists rule."""
        builder = cls().source_type(source_type).operator("json_path_exists").json_path(json_path)
        if source_key:
            builder.source_key(source_key)
        if comment:
            builder.comment(comment)
        return builder.build()


# ============================================================================
# RULE VALIDATION
# ============================================================================


class RuleValidator:
    """Validates rule dictionaries for correctness and completeness.

    This helps catch configuration errors before rules are used
    in the evaluation engine.
    """

    def __init__(self, logger=None, operators_instance=None):
        self.logger = logger or get_logger("RuleValidator")
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.operators = (
            operators_instance if operators_instance is not None else RuleOperators(self.logger)
        )  # Initialize RuleOperators

    def validate_rule(self, rule: RuleDict) -> bool:
        """Validate a single rule dictionary.

        Args:
            rule: Rule dictionary to validate

        Returns:
            True if rule is valid, False otherwise

        """
        self.errors.clear()
        self.warnings.clear()

        # Check for complex rule structure
        if "condition" in rule and "rules" in rule:
            return self._validate_complex_rule(rule)

        # Validate simple rule
        return self._validate_simple_rule(rule)

    def _validate_simple_rule(self, rule: RuleDict) -> bool:
        """Validate a simple rule."""
        # Check required fields
        if "operator" not in rule:
            self.errors.append("Rule missing required 'operator' field")

        operator = rule.get("operator")
        self.logger.debug(f"RuleValidator: Validating operator: {operator}")

        # Validate operator exists
        if operator and not hasattr(self.operators, operator):  # Check operator existence on instance
            self.errors.append(f"Unknown operator: '{operator}'")
            self.logger.error("RuleValidator: Operator '%s' not found in RuleOperators.", operator)
            return False

        # Validate operator-specific requirements
        if operator in [
            "equals",
            "equals_case_insensitive",
            "contains",
            "contains_case_insensitive",
            "startswith",
            "endswith",
            "is_in_list",
        ]:
            if operator == "is_in_list":
                if "value_list" not in rule:
                    self.errors.append(f"Operator '{operator}' requires 'value_list' field")
            elif "value" not in rule:
                self.errors.append(f"Operator '{operator}' requires 'value' field")

        elif operator == "regex_match":
            if "regex_pattern" not in rule:
                self.errors.append(f"Operator '{operator}' requires 'regex_pattern' field")

        elif operator in ["regex_match_all", "regex_match_any"]:
            if "regex_patterns" not in rule:
                self.errors.append(f"Operator '{operator}' requires 'regex_patterns' field")

        # elif operator == "has_keys":
        #     if "value" not in rule or not isinstance(rule["value"], list):
        #         self.errors.append(f"Operator '{operator}' requires a 'value' field which is a list of keys")

        elif operator in ["json_path_exists", "json_path_value_equals"]:
            if "json_path" not in rule:
                self.errors.append(f"Operator '{operator}' requires 'json_path' field")

        elif operator in ["json_contains_any_key", "json_contains_all_keys"]:
            if "expected_keys" not in rule:
                self.errors.append(f"Operator '{operator}' requires 'expected_keys' field")

        # Validate source type
        source_type = rule.get("source_type")
        if not source_type and operator not in ["not_exists", "is_none"]:
            self.warnings.append("Rule missing 'source_type' - may not work as expected")

        # Log validation results
        if self.errors:
            for error in self.errors:
                self.logger.error(f"Rule validation error: {error}")

        if self.warnings:
            for warning in self.warnings:
                self.logger.warning(f"Rule validation warning: {warning}")

        return len(self.errors) == 0

    def _validate_complex_rule(self, rule: RuleDict) -> bool:
        """Validate a complex rule with conditions."""
        condition = rule.get("condition", "").upper()
        sub_rules = rule.get("rules", [])

        if condition not in ["AND", "OR"]:
            self.errors.append(f"Invalid condition '{condition}'. Must be 'AND' or 'OR'")

        if not sub_rules:
            self.errors.append("Complex rule has no sub-rules")
        elif not isinstance(sub_rules, list):
            self.errors.append("Complex rule 'rules' field must be a list")
        else:
            # Validate each sub-rule
            for i, sub_rule in enumerate(sub_rules):
                if not isinstance(sub_rule, dict):
                    self.errors.append(f"Sub-rule {i} is not a dictionary")
                    continue

                # Recursively validate sub-rules
                sub_validator = RuleValidator(self.logger, operators_instance=self.operators)
                if not sub_validator.validate_rule(sub_rule):
                    self.errors.extend([f"Sub-rule {i}: {error}" for error in sub_validator.errors])
                    self.warnings.extend([f"Sub-rule {i}: {warning}" for warning in sub_validator.warnings])

        return len(self.errors) == 0

    def validate_rules_list(self, rules: list[RuleDict]) -> bool:
        """Validate a list of rules.

        Args:
            rules: List of rule dictionaries

        Returns:
            True if all rules are valid, False otherwise

        """
        all_valid = True

        for i, rule in enumerate(rules):
            if not self.validate_rule(rule):
                self.logger.error(f"Rule {i} failed validation")
                all_valid = False

        return all_valid


# ============================================================================
# TESTING AND DEBUGGING UTILITIES
# ============================================================================


def create_test_context() -> ContextData:
    """Create a test context data dictionary for testing rules."""
    return {
        "pil_info": {
            "parameters": "test positive prompt\nNegative prompt: test negative\nSteps: 20, Sampler: Euler a",
            "Comment": '{"prompt": "test json prompt"}',
        },
        "raw_user_comment_str": "Steps: 20, Sampler: Euler a, CFG scale: 7",
        "software_tag": "AUTOMATIC1111",
        "file_format": "PNG",
        "file_extension": "png",
        "width": 512,
        "height": 512,
    }


def test_rule_engine():
    """Test the rule engine with sample rules and data."""
    logger = get_logger("RuleEngineTest")

    # Create test rules
    rules = [
        RuleBuilder.exists_rule("pil_info_key", "parameters", "PNG parameters chunk exists"),
        RuleBuilder.equals_rule("software_tag", "AUTOMATIC1111", comment="EXIF software tag is A1111"),
        RuleBuilder.regex_rule("raw_user_comment_str", r"Steps:", comment="UserComment has Steps parameter"),
    ]

    # Create test context
    context = create_test_context()

    # Test rule engine
    engine = RuleEngine(logger=logger)
    engine.rules = rules

    logger.info("Testing rule engine...")

    for i, rule in enumerate(rules):
        result = engine.evaluate_rule(rule, context)
        comment = rule.get("comment", f"Rule {i}")
        logger.info(f"Rule '{comment}': {'PASS' if result else 'FAIL'}")

    logger.info("Rule engine test completed")


if __name__ == "__main__":
    # Run tests if module is executed directly
    test_rule_engine()
