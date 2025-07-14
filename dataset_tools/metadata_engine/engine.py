# dataset_tools/metadata_engine/engine.py

"""Refactored MetadataEngine - Main Orchestrator

This is the main engine that coordinates all the metadata parsing components.
Think of it as your main job class in FFXIV - it brings together all your
skills (modules) to complete complex tasks! 🎯⚔️

The engine handles:
- Parser definition loading and matching
- Context data preparation
- Field extraction coordination
- Template processing
- Python class fallback integration
"""

import json
import logging
from pathlib import Path
from typing import Any, BinaryIO, Union


# Simplified imports - use standard logging instead of custom logger
def get_logger(name=None):
    """Fallback logger function"""
    return logging.getLogger(name or __name__)


try:
    from .parser_registry import get_parser_class_by_name
except ImportError:
    # Create a minimal parser registry
    def get_parser_class_by_name(name):
        return None


try:
    from .rule_engine import RuleEngine
except ImportError:
    # Create a minimal rule engine
    class RuleEngine:
        def __init__(self, *args, **kwargs):
            pass

        def evaluate_parser_rules(self, *args, **kwargs):
            return True


try:
    from ..vendored_sdpr.format.base_format import BaseFormat
except ImportError:
    # Create a minimal BaseFormat fallback
    class BaseFormat:
        pass


try:
    from .context_preparation import ContextDataPreparer
except ImportError:

    class ContextDataPreparer:
        def __init__(self, *args, **kwargs):
            pass

        def prepare_context_data(self, *args, **kwargs):
            return {}


try:
    from .field_extraction import FieldExtractor
except ImportError:

    class FieldExtractor:
        def __init__(self, *args, **kwargs):
            pass

        def extract_fields(self, *args, **kwargs):
            return {}


try:
    from .template_system import OutputFormatter, TemplateProcessor
except ImportError:

    class TemplateProcessor:
        def __init__(self, *args, **kwargs):
            pass

        def process_template(self, *args, **kwargs):
            return {}

    class OutputFormatter:
        def __init__(self, *args, **kwargs):
            pass

        def format_output(self, *args, **kwargs):
            return {}


# Type aliases
FileInput = Union[str, Path, BinaryIO]
ContextData = dict[str, Any]
ParserDefinition = dict[str, Any]
ExtractedFields = dict[str, Any]


class MetadataEngine:
    """Main metadata parsing engine.

    This class coordinates all the components to provide a unified
    interface for metadata extraction from various file types.
    """

    def __init__(
        self,
        parser_definitions_path: str | Path,
        logger_obj: logging.Logger | None = None,
    ):
        """Initialize the metadata engine.

        Args:
            parser_definitions_path: Path to parser definition files
            logger_obj: Optional logger instance

        """
        self.parser_definitions_path = Path(parser_definitions_path)
        self.logger = logger_obj or get_logger("MetadataEngine")
        self.logger.debug(f"MetadataEngine: __init__ called, logger type: {type(self.logger)}")

        # Initialize components
        self.context_preparer = ContextDataPreparer(self.logger)
        self.field_extractor = FieldExtractor(self.logger)
        self.template_processor = TemplateProcessor(self.logger)
        self.output_formatter = OutputFormatter(self.logger)
        self.rule_engine = RuleEngine(logger=self.logger)

        # Load parser definitions
        self.parser_definitions = self._load_parser_definitions()
        self.sorted_definitions = self._sort_definitions_by_priority()

        self.logger.info(
            f"MetadataEngine initialized with {len(self.sorted_definitions)} "
            f"parser definitions from {self.parser_definitions_path}"
        )

    def get_parser_for_file(self, file_input: FileInput) -> dict[str, Any] | BaseFormat | None:
        """Get the appropriate parser result for a file.

        Args:
            file_input: File path string, Path object, or BinaryIO object

        Returns:
            Parser result (dict or BaseFormat instance) or None if no parser found

        """
        try:
            self.logger.debug(f"get_parser_for_file called with: {file_input}, type: {type(file_input)}")
            display_name = getattr(file_input, "name", str(file_input))
            self.logger.debug(f"display_name: {display_name}")
            self.logger.info(f"MetadataEngine: Starting metadata parsing for: {display_name}")
            self.logger.debug("Logger info call completed")
        except Exception as e:
            self.logger.debug(f"Exception in get_parser_for_file start: {e}")
            self.logger.error(f"MetadataEngine: Exception at very start: {e}")
            return None

        # Prepare context data
        self.logger.debug("About to call context_preparer.prepare_context")
        context_data = self.context_preparer.prepare_context(file_input)
        self.logger.debug(f"prepare_context returned: {type(context_data)} - {bool(context_data)}")
        if not context_data:
            self.logger.debug("Context data is None/empty, returning None")
            self.logger.warning(f"Failed to prepare context data for {display_name}")
            return None

        self.logger.debug("Context data looks good, continuing to find matching parser")
        self.logger.debug(f"Context data keys: {list(context_data.keys())}")
        self.logger.debug(
            f"raw_user_comment_str: {context_data.get('raw_user_comment_str', 'NOT_FOUND')[:100] if context_data.get('raw_user_comment_str') else 'EMPTY'}"
        )

        # Find matching parser definition
        chosen_parser_def = self._find_matching_parser(context_data)
        self.logger.debug(f"_find_matching_parser returned: {chosen_parser_def}")
        if not chosen_parser_def:
            self.logger.info(f"No suitable parser definition matched for {display_name}")
            return None

        parser_name = chosen_parser_def["parser_name"]
        self.logger.info(f"MetadataEngine: Matched parser definition: {parser_name}")

        # Process based on parser type
        if "parsing_instructions" in chosen_parser_def:
            return self._process_json_instructions(chosen_parser_def, context_data)
        if "base_format_class" in chosen_parser_def:
            return self._process_python_class(chosen_parser_def, context_data)
        self.logger.error(f"Parser definition '{parser_name}' has neither instructions nor class")
        return None

    def _load_parser_definitions(self) -> list[ParserDefinition]:
        """Load parser definitions from JSON files."""
        definitions = []

        if not self.parser_definitions_path.is_dir():
            self.logger.error(f"Parser definitions path is not a directory: {self.parser_definitions_path}")
            return definitions

        for filepath in self.parser_definitions_path.glob("*.json"):
            self.logger.debug(f"Loading parser definition: {filepath.name}")

            try:
                with open(filepath, encoding="utf-8") as f:
                    definition = json.load(f)

                if "parser_name" in definition:
                    definitions.append(definition)
                    self.logger.debug(f"Loaded parser: {definition['parser_name']}")
                else:
                    self.logger.warning(f"Skipping invalid parser definition (missing parser_name): {filepath.name}")

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to decode JSON from {filepath.name}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error loading {filepath.name}: {e}")

        return definitions

    def _sort_definitions_by_priority(self) -> list[ParserDefinition]:
        """Sort parser definitions by priority (highest first)."""
        return sorted(self.parser_definitions, key=lambda p: p.get("priority", 0), reverse=True)

    def _find_matching_parser(self, context_data: ContextData) -> ParserDefinition | None:
        """Find the first parser definition that matches the context data.

        Args:
            context_data: Prepared context data

        Returns:
            Matching parser definition or None

        """
        for parser_def in self.sorted_definitions:
            if self._parser_matches_context(parser_def, context_data):
                return parser_def

        return None

    def _parser_matches_context(self, parser_def: ParserDefinition, context_data: ContextData) -> bool:
        """Check if a parser definition matches the context data.

        Args:
            parser_def: Parser definition to check
            context_data: Context data to match against

        Returns:
            True if parser matches, False otherwise

        """
        # Check target file types
        if not self._check_file_type_match(parser_def, context_data):
            return False

        # Check detection rules
        self.logger.debug(f"Evaluating detection rules for parser: {parser_def['parser_name']}")
        return self._check_detection_rules(parser_def, context_data)

    def _check_file_type_match(self, parser_def: ParserDefinition, context_data: ContextData) -> bool:
        """Check if file type matches parser target types."""
        parser_name = parser_def["parser_name"]
        target_types_cfg = parser_def.get("target_file_types", ["*"])
        if not isinstance(target_types_cfg, list):
            target_types_cfg = [str(target_types_cfg)]

        target_types = [ft.upper() for ft in target_types_cfg]
        current_file_format = context_data.get("file_format", "").upper()
        current_file_ext = context_data.get("file_extension", "").upper()

        self.logger.debug(f"  Checking file type for parser: {parser_name}")
        self.logger.debug(f"    Parser target types: {target_types}")
        self.logger.debug(f"    Current file format: {current_file_format}, extension: {current_file_ext}")

        match = (
            "*" in target_types
            or (current_file_format and current_file_format in target_types)
            or (current_file_ext and current_file_ext in target_types)
        )
        self.logger.debug(f"    File type match result for {parser_name}: {match}")
        return match

    def _check_detection_rules(self, parser_def: ParserDefinition, context_data: ContextData) -> bool:
        """Check if detection rules pass for this parser."""
        detection_rules = parser_def.get("detection_rules", [])

        # No rules means match (file type was already checked)
        if not detection_rules:
            self.logger.debug(f"No detection rules for {parser_def['parser_name']}, matching.")
            return True

        # All rules must pass
        for rule in detection_rules:
            rule_comment = rule.get("comment", "Unnamed Rule")
            rule_passed = self.rule_engine.evaluate_rule(rule, context_data)
            self.logger.debug(f"  Rule '{rule_comment}' for {parser_def['parser_name']} evaluated to: {rule_passed}")
            if not rule_passed:
                self.logger.debug(f"Rule failed for {parser_def['parser_name']}: {rule.get('comment', rule)}")
                return False

        self.logger.debug(f"All detection rules passed for parser: {parser_def['parser_name']}")
        return True

    def _process_json_instructions(
        self, parser_def: ParserDefinition, context_data: ContextData
    ) -> dict[str, Any] | None:
        """Process parser definition with JSON instructions.

        Args:
            parser_def: Parser definition with parsing_instructions
            context_data: Prepared context data

        Returns:
            Processed result dictionary or None

        """
        parser_name = parser_def["parser_name"]
        instructions = parser_def["parsing_instructions"]

        self.logger.info(f"Using JSON-defined parsing instructions for {parser_name}")

        # Prepare input data
        input_data, original_input = self._prepare_input_data(instructions, context_data)
        if input_data is None:
            self.logger.warning(f"No input data found for {parser_name}")
            return None

        # Transform input data if needed
        transformed_data = self._transform_input_data(input_data, instructions, original_input)

        # Extract fields
        extracted_fields = self._extract_fields(instructions, transformed_data, context_data)

        # Process output template
        return self._process_output_template(
            parser_def, extracted_fields, context_data, original_input, transformed_data
        )

    def _prepare_input_data(self, instructions: dict[str, Any], context_data: ContextData) -> tuple[Any, Any]:
        """Prepare input data based on instruction configuration.

        Returns:
            Tuple of (input_data, original_input_for_template)

        """
        input_data_def = instructions.get("input_data", {})
        source_options = input_data_def.get("source_options", [])

        # Handle legacy single source format
        if not source_options and input_data_def.get("source_type"):
            source_options = [input_data_def]

        # Try each source option until we find data
        for source_opt in source_options:
            data = self._get_data_from_source(source_opt, context_data)
            if data is not None:
                return data, data

        return None, None

    def _get_data_from_source(self, source_def: dict[str, Any], context_data: ContextData) -> Any:
        """Get data from a specific source definition."""
        source_type = source_def.get("source_type")
        source_key = source_def.get("source_key")

        source_map = {
            "pil_info_key": lambda: context_data.get("pil_info", {}).get(source_key),
            "exif_user_comment": lambda: context_data.get("raw_user_comment_str"),
            "xmp_string_content": lambda: context_data.get("xmp_string"),
            "file_content_raw_text": lambda: context_data.get("raw_file_content_text"),
            "raw_file_content_text": lambda: context_data.get("raw_file_content_text"),  # Add alias
            "file_content_json_object": lambda: context_data.get("parsed_root_json_object"),
            "parsed_root_json_object": lambda: context_data.get("parsed_root_json_object"),  # Add alias
            "direct_context_key": lambda: context_data.get(source_key),  # Add direct context access
            "png_chunk": lambda: context_data.get("png_chunks", {}).get(source_key),
            "exif_field": lambda: context_data.get("exif_data", {}).get(source_key),
        }

        if source_type in source_map:
            return source_map[source_type]()

        self.logger.warning(f"Unknown source type: {source_type}")
        return None

    def _transform_input_data(self, input_data: Any, instructions: dict[str, Any], original_input: Any) -> Any:
        """Apply transformations to input data."""
        transformations = instructions.get("input_data", {}).get("transformations", [])
        current_data = input_data

        for transform in transformations:
            if current_data is None:
                break

            current_data = self._apply_single_transformation(transform, current_data)

        return current_data

    def _apply_single_transformation(self, transform: dict[str, Any], data: Any) -> Any:
        """Apply a single transformation to data."""
        transform_type = transform.get("type")

        if transform_type == "json_decode_string_value" and isinstance(data, str):
            try:
                json_obj = json.loads(data)
                path = transform.get("path")
                if path:
                    from .utils import json_path_get_utility

                    return json_path_get_utility(json_obj, path)
                return json_obj
            except json.JSONDecodeError:
                self.logger.debug("Failed to decode JSON in transformation")
                return None

        elif transform_type == "conditional_json_unwrap_parameters_string" and isinstance(data, str):
            try:
                potential_wrapper = json.loads(data)
                if (
                    isinstance(potential_wrapper, dict)
                    and "parameters" in potential_wrapper
                    and isinstance(potential_wrapper["parameters"], str)
                ):
                    return potential_wrapper["parameters"]
            except json.JSONDecodeError:
                pass  # Not JSON, return as-is

        elif transform_type == "json_decode_string_itself" and isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None

        elif transform_type == "filter_dict_nodes_only" and isinstance(data, dict):
            # Filter out non-dict values to keep only node data for ComfyUI workflows
            return {k: v for k, v in data.items() if isinstance(v, dict)}

        elif transform_type == "extract_json_from_xmp_user_comment" and isinstance(data, str):
            # Extract JSON from XMP exif:UserComment element (for Draw Things)
            try:
                from defusedxml.minidom import parseString  # type: ignore

                xmp_dom = parseString(data)
                description_nodes = xmp_dom.getElementsByTagName("rdf:Description")
                for desc_node in description_nodes:
                    uc_nodes = desc_node.getElementsByTagName("exif:UserComment")
                    if not uc_nodes or not uc_nodes[0].childNodes:
                        continue
                    first_child = uc_nodes[0].childNodes[0]
                    if first_child.nodeType == first_child.TEXT_NODE:
                        return first_child.data.strip()
                    if first_child.nodeName == "rdf:Alt":
                        alt_node = first_child
                        li_nodes = alt_node.getElementsByTagName("rdf:li")
                        if (
                            li_nodes
                            and li_nodes[0].childNodes
                            and li_nodes[0].childNodes[0].nodeType == li_nodes[0].TEXT_NODE
                        ):
                            return li_nodes[0].childNodes[0].data.strip()
                return None
            except Exception as e:
                self.logger.debug(f"Failed to extract JSON from XMP UserComment: {e}")
                return None

        return data

    def _extract_fields(
        self, instructions: dict[str, Any], input_data: Any, context_data: ContextData
    ) -> ExtractedFields:
        """Extract fields according to instruction definitions."""
        extracted_fields: ExtractedFields = {"parameters": {}}

        field_definitions = instructions.get("fields", [])
        for field_def in field_definitions:
            target_key_path = field_def.get("target_key")
            if not target_key_path:
                continue

            # Extract the field value
            value = self.field_extractor.extract_field(field_def, input_data, context_data, extracted_fields)

            # Store in cache for variable references
            cache_key = target_key_path.replace(".", "_VAR_")
            extracted_fields[cache_key] = value

            # Store in nested structure
            self._set_nested_value(extracted_fields, target_key_path, value, field_def)

        return extracted_fields

    def _set_nested_value(
        self,
        target_dict: dict[str, Any],
        key_path: str,
        value: Any,
        field_def: dict[str, Any],
    ) -> None:
        """Set a nested value in the target dictionary."""
        keys = key_path.split(".")
        current_dict = target_dict

        # Navigate to the parent dictionary
        for key_segment in keys[:-1]:
            current_dict = current_dict.setdefault(key_segment, {})

        # Set the final value if it's not None or field is not optional
        final_key = keys[-1]
        if value is not None or not field_def.get("optional", False):
            current_dict[final_key] = value

    def _process_output_template(
        self,
        parser_def: ParserDefinition,
        extracted_fields: ExtractedFields,
        context_data: ContextData,
        original_input: Any,
        transformed_data: Any,
    ) -> dict[str, Any] | None:
        """Process the output template with extracted data."""
        # Get template from instructions or parser definition
        instructions = parser_def.get("parsing_instructions", {})
        output_template = instructions.get("output_template") or parser_def.get("output_template")

        if not output_template:
            self.logger.debug("No output template found, returning raw extracted fields")
            # Return fields without variable cache keys
            return {
                k: v for k, v in extracted_fields.items() if "_VAR_" not in k and k != "_input_data_object_for_template"
            }

        # Prepare data for template processing
        original_input_str = str(original_input) if isinstance(original_input, (str, int, float, bool)) else None

        input_json_object = transformed_data if isinstance(transformed_data, (dict, list)) else None

        # Process template with variable substitution
        processed_template = self.template_processor.process_template(
            output_template,
            extracted_fields,
            context_data,
            original_input_str,
            input_json_object,
        )

        # Add context width/height to parameters if missing
        if isinstance(processed_template, dict) and "parameters" in processed_template:
            params = processed_template["parameters"]
            if isinstance(params, dict):
                if params.get("width") is None and context_data.get("width", 0) > 0:
                    params["width"] = context_data["width"]
                if params.get("height") is None and context_data.get("height", 0) > 0:
                    params["height"] = context_data["height"]

        # Format the final output
        return self.output_formatter.format_output(processed_template, format_type="standard", cleanup_empty=True)

    def _process_python_class(self, parser_def: ParserDefinition, context_data: ContextData) -> BaseFormat | None:
        """Process parser definition with Python class.

        Args:
            parser_def: Parser definition with base_format_class
            context_data: Prepared context data

        Returns:
            BaseFormat instance or None if processing failed

        """
        parser_name = parser_def["parser_name"]
        class_name = parser_def["base_format_class"]

        self.logger.info(f"Using Python class-based parser {class_name} for {parser_name}")

        # Get the parser class
        ParserClass = get_parser_class_by_name(class_name)
        if not ParserClass:
            self.logger.error(f"Python class '{class_name}' not found for {parser_name}")
            return None

        # Prepare raw input data for the parser
        raw_input = self._prepare_raw_input_for_class(parser_def, context_data)

        # Create parser instance
        parser_instance = ParserClass(
            info=context_data,
            raw=raw_input,
            width=str(context_data.get("width", 0)),
            height=str(context_data.get("height", 0)),
            logger_obj=self.logger,
        )

        # Parse the data
        try:
            parser_status = parser_instance.parse()

            if parser_status == BaseFormat.Status.READ_SUCCESS:
                self.logger.info(f"Python Parser {parser_instance.tool} succeeded")
                return parser_instance
            status_name = getattr(parser_status, "name", str(parser_status))
            error_msg = getattr(parser_instance, "error", "No error details")
            self.logger.warning(
                f"Python Parser {parser_instance.tool} failed. Status: {status_name}. Error: {error_msg}"
            )
            return None

        except Exception as e:
            self.logger.error(f"Exception in Python parser {class_name}: {e}", exc_info=True)
            return None

    def _prepare_raw_input_for_class(self, parser_def: ParserDefinition, context_data: ContextData) -> str:
        """Prepare raw input string for Python class parser."""
        primary_data_def = parser_def.get("primary_data_source_for_raw", {})
        source_type = primary_data_def.get("source_type")
        source_key = primary_data_def.get("source_key")

        if source_type == "png_chunk" and source_key:
            return context_data.get("png_chunks", {}).get(source_key, "")
        if source_type == "exif_user_comment":
            return context_data.get("raw_user_comment_str", "")
        if source_type == "xmp_string_content":
            return context_data.get("xmp_string", "")
        # Default fallback - try common sources
        return (
            context_data.get("pil_info", {}).get("parameters", "")
            or context_data.get("raw_user_comment_str", "")
            or context_data.get("raw_file_content_text", "")
        )


class MetadataEngineBuilder:
    """Builder class for creating MetadataEngine instances with custom configuration.

    This provides a fluent interface for setting up the engine with
    different components and settings.
    """

    def __init__(self):
        """Initialize the builder."""
        self.parser_definitions_path: Path | None = None
        self.logger: logging.Logger | None = None
        self.custom_context_preparer: ContextDataPreparer | None = None
        self.custom_field_extractor: FieldExtractor | None = None
        self.custom_template_processor: TemplateProcessor | None = None

    def with_parser_definitions(self, path: str | Path) -> "MetadataEngineBuilder":
        """Set the parser definitions path."""
        self.parser_definitions_path = Path(path)
        return self

    def with_logger(self, logger: logging.Logger) -> "MetadataEngineBuilder":
        """Set the logger instance."""
        self.logger = logger
        return self

    def with_context_preparer(self, preparer: ContextDataPreparer) -> "MetadataEngineBuilder":
        """Set a custom context preparer."""
        self.custom_context_preparer = preparer
        return self

    def with_field_extractor(self, extractor: FieldExtractor) -> "MetadataEngineBuilder":
        """Set a custom field extractor."""
        self.custom_field_extractor = extractor
        return self

    def with_template_processor(self, processor: TemplateProcessor) -> "MetadataEngineBuilder":
        """Set a custom template processor."""
        self.custom_template_processor = processor
        return self

    def build(self) -> MetadataEngine:
        """Build and return the MetadataEngine instance."""
        if not self.parser_definitions_path:
            raise ValueError("Parser definitions path is required")

        # Create the engine
        engine = MetadataEngine(self.parser_definitions_path, self.logger)

        # Replace components if custom ones were provided
        if self.custom_context_preparer:
            engine.context_preparer = self.custom_context_preparer

        if self.custom_field_extractor:
            engine.field_extractor = self.custom_field_extractor

        if self.custom_template_processor:
            engine.template_processor = self.custom_template_processor

        return engine


class MetadataEngineManager:
    """Manager class for handling multiple MetadataEngine instances.

    This is useful when you need different engine configurations
    for different types of files or use cases.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize the manager."""
        self.logger = logger or get_logger("MetadataEngineManager")
        self.engines: dict[str, MetadataEngine] = {}
        self.default_engine: str | None = None

    def register_engine(self, name: str, engine: MetadataEngine, set_as_default: bool = False) -> None:
        """Register a MetadataEngine instance.

        Args:
            name: Name identifier for the engine
            engine: MetadataEngine instance
            set_as_default: Whether to set this as the default engine

        """
        self.engines[name] = engine
        self.logger.info(f"Registered MetadataEngine: {name}")

        if set_as_default or not self.default_engine:
            self.default_engine = name
            self.logger.info(f"Set default engine to: {name}")

    def get_engine(self, name: str | None = None) -> MetadataEngine | None:
        """Get a MetadataEngine by name.

        Args:
            name: Engine name, or None to get the default engine

        Returns:
            MetadataEngine instance or None if not found

        """
        if name is None:
            name = self.default_engine

        if name is None:
            self.logger.warning("No default engine set and no name provided")
            return None

        return self.engines.get(name)

    def parse_file(self, file_input: FileInput, engine_name: str | None = None) -> dict[str, Any] | BaseFormat | None:
        """Parse a file using the specified or default engine.

        Args:
            file_input: File to parse
            engine_name: Engine name, or None to use default

        Returns:
            Parser result or None if parsing failed

        """
        engine = self.get_engine(engine_name)
        if not engine:
            self.logger.error(f"Engine '{engine_name or 'default'}' not found")
            return None

        return engine.get_parser_for_file(file_input)

    def list_engines(self) -> list[str]:
        """Get list of registered engine names."""
        return list(self.engines.keys())


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def create_metadata_engine(
    parser_definitions_path: str | Path,
    logger: logging.Logger | None = None,
) -> MetadataEngine:
    """Convenience function to create a MetadataEngine.

    Args:
        parser_definitions_path: Path to parser definition files
        logger: Optional logger instance

    Returns:
        Configured MetadataEngine instance

    """
    return MetadataEngine(parser_definitions_path, logger)


def create_engine_builder() -> MetadataEngineBuilder:
    """Convenience function to create a MetadataEngineBuilder.

    Returns:
        MetadataEngineBuilder instance

    """
    return MetadataEngineBuilder()


def parse_file_metadata(
    file_input: FileInput,
    parser_definitions_path: str | Path,
    logger: logging.Logger | None = None,
) -> dict[str, Any] | BaseFormat | None:
    """Convenience function to parse file metadata.

    Args:
        file_input: File to parse
        parser_definitions_path: Path to parser definitions
        logger: Optional logger instance

    Returns:
        Parser result or None if parsing failed

    """
    engine = create_metadata_engine(parser_definitions_path, logger)
    return engine.get_parser_for_file(file_input)


# ============================================================================
# TESTING UTILITIES
# ============================================================================


def test_metadata_engine():
    """Test the refactored metadata engine."""
    logger = get_logger("MetadataEngineTest")
    logger.setLevel(logging.DEBUG)

    # Create a temporary test parser definition
    test_definitions_path = Path("./temp_test_definitions")
    test_definitions_path.mkdir(exist_ok=True)

    # Simple test parser definition
    test_parser_def = {
        "parser_name": "Test Text Parser",
        "priority": 100,
        "target_file_types": ["TXT"],
        "detection_rules": [
            {
                "source_type": "file_extension",
                "operator": "equals_case_insensitive",
                "value": "txt",
            }
        ],
        "parsing_instructions": {
            "input_data": {"source_type": "file_content_raw_text"},
            "fields": [{"target_key": "content", "method": "direct_string_value"}],
            "output_template": {
                "tool": "TestTextParser",
                "content": "$content",
                "file_info": {"name": "$FILE_NAME", "extension": "$FILE_EXTENSION"},
            },
        },
    }

    # Save test definition
    with open(test_definitions_path / "test_parser.json", "w") as f:
        json.dump(test_parser_def, f, indent=2)

    try:
        # Test engine creation
        logger.info("Creating MetadataEngine...")
        engine = create_metadata_engine(test_definitions_path, logger)

        # Create a test file
        test_file = Path("./test_content.txt")
        test_file.write_text("This is test content for the metadata engine!")

        # Test parsing
        logger.info("Testing file parsing...")
        result = engine.get_parser_for_file(test_file)

        if result:
            logger.info(f"Parsing successful! Result: {json.dumps(result, indent=2)}")
        else:
            logger.warning("Parsing failed or returned None")

        # Test engine builder
        logger.info("Testing engine builder...")
        builder_engine = (
            create_engine_builder().with_parser_definitions(test_definitions_path).with_logger(logger).build()
        )

        builder_result = builder_engine.get_parser_for_file(test_file)
        logger.info(f"Builder engine result: {builder_result is not None}")

        # Test engine manager
        logger.info("Testing engine manager...")
        manager = MetadataEngineManager(logger)
        manager.register_engine("test", engine, set_as_default=True)
        manager.register_engine("builder", builder_engine)

        manager_result = manager.parse_file(test_file)
        logger.info(f"Manager parsing result: {manager_result is not None}")

        logger.info("All tests completed successfully!")

    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)

    finally:
        # Cleanup
        try:
            test_file.unlink(missing_ok=True)
            for json_file in test_definitions_path.glob("*.json"):
                json_file.unlink()
            test_definitions_path.rmdir()
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")


if __name__ == "__main__":
    # Run tests if module is executed directly
    test_metadata_engine()
