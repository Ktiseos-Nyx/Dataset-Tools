# dataset_tools/file_readers/schema_file_reader.py

"""Schema file reader for JSON, TOML, YAML, and other structured data files.

This module handles reading and parsing various structured data formats.
Think of it as your data wizard who can understand any magical configuration
scroll or data crystal! 🔮📋
"""

import json
from pathlib import Path
from typing import Any

try:
    import toml

    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import defusedxml.ElementTree as ET

    XML_AVAILABLE = True
except ImportError:
    # Do NOT fall back to xml.etree.ElementTree to avoid XXE vulnerabilities
    XML_AVAILABLE = False

from ..correct_types import DownField, EmptyField
from ..logger import debug_monitor, get_logger
from ..logger import info_monitor as nfo


class SchemaFileReader:
    """Specialized reader for structured data files.

    This class handles reading JSON, TOML, YAML, XML and other structured
    formats with proper error handling and validation.
    """

    def __init__(self):
        """Initialize the schema file reader."""
        self.logger = get_logger(f"{__name__}.SchemaFileReader")

        # File format handlers
        self.format_handlers = {
            ".json": self._read_json_file,
            ".toml": self._read_toml_file,
            ".yaml": self._read_yaml_file,
            ".yml": self._read_yaml_file,
            ".xml": self._read_xml_file,
        }

        # Supported formats (based on what's available)
        self.supported_formats = {".json"}  # JSON is always supported

        if TOML_AVAILABLE:
            self.supported_formats.add(".toml")

        if YAML_AVAILABLE:
            self.supported_formats.update({".yaml", ".yml"})

        if XML_AVAILABLE:
            self.supported_formats.add(".xml")

    def can_read_file(self, file_path: str) -> bool:
        """Check if this reader can handle the given file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if this reader supports the file format

        """
        suffix = Path(file_path).suffix.lower()
        return suffix in self.supported_formats

    @debug_monitor
    def read_file(self, file_path: str) -> dict[str, Any] | None:
        """Read a schema file and parse its contents.

        Args:
            file_path: Path to the schema file

        Returns:
            Dictionary containing parsed data or error information

        """
        if not self.can_read_file(file_path):
            self.logger.warning(f"Unsupported schema file format: {file_path}")
            return None

        file_path_obj = Path(file_path)
        suffix = file_path_obj.suffix.lower()

        nfo(f"[SchemaReader] Reading {suffix.upper()} file: {file_path_obj.name}")

        # Get the appropriate handler
        handler = self.format_handlers.get(suffix)
        if not handler:
            self.logger.error(f"No handler found for format: {suffix}")
            return None

        try:
            # Read and parse the file
            parsed_data = handler(file_path)

            if parsed_data is None:
                return self._create_error_result(f"Failed to parse {suffix.upper()} file", suffix)

            # Add metadata about the parsing
            result = {
                self._get_data_field(suffix).value: parsed_data,
                "file_format": suffix.upper().lstrip("."),
                "file_size": (file_path_obj.stat().st_size if file_path_obj.exists() else 0),
                "parsing_success": True,
            }

            # Add format-specific analysis
            analysis = self._analyze_structure(parsed_data, suffix)
            result.update(analysis)

            return result

        except Exception as e:
            self.logger.error(f"Error reading schema file {file_path}: {e}")
            return self._create_error_result(f"Error reading {suffix.upper()}: {e!s}", suffix)

    def _read_json_file(self, file_path: str) -> dict | list | None:
        """Read and parse a JSON file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON decode error in {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading JSON file {file_path}: {e}")
            return None

    def _read_toml_file(self, file_path: str) -> dict[str, Any] | None:
        """Read and parse a TOML file."""
        if not TOML_AVAILABLE:
            self.logger.error("TOML library not available")
            return None

        try:
            with open(file_path, "rb") as f:
                return toml.load(f)
        except toml.TomlDecodeError as e:
            self.logger.warning(f"TOML decode error in {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading TOML file {file_path}: {e}")
            return None

    def _read_yaml_file(self, file_path: str) -> dict | list | None:
        """Read and parse a YAML file."""
        if not YAML_AVAILABLE:
            self.logger.error("YAML library not available")
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.logger.warning(f"YAML parse error in {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading YAML file {file_path}: {e}")
            return None

    def _read_xml_file(self, file_path: str) -> dict[str, Any] | None:
        """Read and parse an XML file securely (prevents XXE attacks)."""
        if not XML_AVAILABLE:
            self.logger.error("defusedxml library not available for secure XML parsing")
            return None

        try:
            # defusedxml handles XXE prevention by default
            tree = ET.parse(file_path)
            root = tree.getroot()
            return self._xml_to_dict(root)
        except ET.ParseError as e:
            self.logger.warning(f"XML parse error in {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading XML file {file_path}: {e}")
            return None
            return None

    def _xml_to_dict(self, element) -> dict[str, Any]:
        """Convert XML element to dictionary."""
        result = {}

        # Add attributes
        if element.attrib:
            result["@attributes"] = element.attrib

        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:  # No child elements
                return element.text.strip()
            result["#text"] = element.text.strip()

        # Add child elements
        children = {}
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in children:
                # Multiple elements with same tag - convert to list
                if not isinstance(children[child.tag], list):
                    children[child.tag] = [children[child.tag]]
                children[child.tag].append(child_data)
            else:
                children[child.tag] = child_data

        result.update(children)
        return (
            result
            if len(result) > 1 or "@attributes" in result
            else result.get(list(result.keys())[0])
            if result
            else {}
        )

    def _get_data_field(self, suffix: str) -> DownField:
        """Get the appropriate data field enum for a file suffix."""
        if suffix == ".json":
            return DownField.JSON_DATA
        if suffix == ".toml":
            return DownField.TOML_DATA
        if suffix in {".yaml", ".yml"}:
            return getattr(DownField, "YAML_DATA", DownField.JSON_DATA)  # Fallback to JSON_DATA
        if suffix == ".xml":
            return getattr(DownField, "XML_DATA", DownField.JSON_DATA)  # Fallback to JSON_DATA
        return DownField.JSON_DATA

    def _create_error_result(self, error_message: str, suffix: str) -> dict[str, Any]:
        """Create an error result dictionary."""
        return {
            EmptyField.PLACEHOLDER.value: {"Error": error_message},
            "file_format": suffix.upper().lstrip("."),
            "parsing_success": False,
        }

    def _analyze_structure(self, data: dict | list, suffix: str) -> dict[str, Any]:
        """Analyze the structure of parsed data."""
        analysis = {}

        try:
            if isinstance(data, dict):
                analysis.update(
                    {
                        "data_type": "object",
                        "key_count": len(data),
                        "top_level_keys": list(data.keys())[:10],  # First 10 keys
                        "nested_levels": self._count_nested_levels(data),
                    }
                )

                # Check for common patterns
                analysis.update(self._detect_common_patterns(data))

            elif isinstance(data, list):
                analysis.update(
                    {
                        "data_type": "array",
                        "item_count": len(data),
                        "item_types": self._analyze_list_types(data),
                    }
                )

            else:
                analysis.update(
                    {
                        "data_type": "primitive",
                        "value_type": type(data).__name__,
                    }
                )

        except Exception as e:
            self.logger.debug(f"Error analyzing structure: {e}")

        return analysis

    def _count_nested_levels(self, obj: Any, current_level: int = 0) -> int:
        """Count the maximum nesting level in a data structure."""
        if not isinstance(obj, (dict, list)):
            return current_level

        max_level = current_level

        if isinstance(obj, dict):
            for value in obj.values():
                level = self._count_nested_levels(value, current_level + 1)
                max_level = max(max_level, level)
        elif isinstance(obj, list):
            for item in obj:
                level = self._count_nested_levels(item, current_level + 1)
                max_level = max(max_level, level)

        return max_level

    def _analyze_list_types(self, data_list: list[Any]) -> dict[str, int]:
        """Analyze the types of items in a list."""
        type_counts = {}

        for item in data_list[:100]:  # Sample first 100 items
            item_type = type(item).__name__
            type_counts[item_type] = type_counts.get(item_type, 0) + 1

        return type_counts

    def _detect_common_patterns(self, data: dict[str, Any]) -> dict[str, Any]:
        """Detect common data patterns."""
        patterns = {}

        # Check for configuration patterns
        config_indicators = ["settings", "config", "options", "preferences"]
        if any(key.lower() in config_indicators for key in data):
            patterns["appears_to_be_config"] = True

        # Check for API response patterns
        api_indicators = ["data", "status", "message", "error", "success"]
        if any(key.lower() in api_indicators for key in data):
            patterns["appears_to_be_api_response"] = True

        # Check for metadata patterns
        metadata_indicators = [
            "metadata",
            "meta",
            "info",
            "version",
            "created",
            "modified",
        ]
        if any(key.lower() in metadata_indicators for key in data):
            patterns["appears_to_have_metadata"] = True

        # Check for workflow patterns (ComfyUI, etc.)
        workflow_indicators = ["nodes", "workflow", "connections", "links"]
        if any(key.lower() in workflow_indicators for key in data):
            patterns["appears_to_be_workflow"] = True

        return patterns

    def get_supported_formats(self) -> set[str]:
        """Get the set of supported schema file formats."""
        return self.supported_formats.copy()


class StructuredDataAnalyzer:
    """Advanced analyzer for structured data content.

    This class provides detailed analysis of parsed structured data,
    including schema validation and content extraction.
    """

    def __init__(self):
        """Initialize the structured data analyzer."""
        self.logger = get_logger(f"{__name__}.StructuredDataAnalyzer")

    def analyze_comfyui_workflow(self, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze ComfyUI workflow data.

        Args:
            data: Parsed workflow data

        Returns:
            Dictionary with workflow analysis

        """
        analysis = {
            "is_comfyui_workflow": False,
            "node_count": 0,
            "connection_count": 0,
            "node_types": [],
            "has_prompt_nodes": False,
            "has_sampler_nodes": False,
            "has_model_nodes": False,
        }

        try:
            # Check if it looks like a ComfyUI workflow
            if not isinstance(data, dict):
                return analysis

            # Look for workflow indicators
            has_nodes = "nodes" in data or any(key.isdigit() for key in data)

            if not has_nodes:
                return analysis

            analysis["is_comfyui_workflow"] = True

            # Analyze nodes
            nodes = data.get("nodes", data) if "nodes" in data else data

            if isinstance(nodes, dict):
                analysis["node_count"] = len(nodes)

                node_types = []
                for node_id, node_data in nodes.items():
                    if isinstance(node_data, dict):
                        node_type = node_data.get("type") or node_data.get("class_type")
                        if node_type:
                            node_types.append(node_type)

                analysis["node_types"] = list(set(node_types))

                # Check for specific node types
                analysis["has_prompt_nodes"] = any("text" in nt.lower() or "prompt" in nt.lower() for nt in node_types)
                analysis["has_sampler_nodes"] = any("sampler" in nt.lower() for nt in node_types)
                analysis["has_model_nodes"] = any("model" in nt.lower() for nt in node_types)

            # Look for connections/links
            if "links" in data:
                links = data["links"]
                if isinstance(links, list):
                    analysis["connection_count"] = len(links)

        except Exception as e:
            self.logger.debug(f"Error analyzing ComfyUI workflow: {e}")

        return analysis

    def extract_metadata_fields(self, data: dict | list) -> dict[str, Any]:
        """Extract common metadata fields from structured data.

        Args:
            data: Parsed structured data

        Returns:
            Dictionary with extracted metadata

        """
        metadata = {}

        if not isinstance(data, dict):
            return metadata

        # Common metadata field mappings
        field_mappings = {
            "title": ["title", "name", "filename"],
            "description": ["description", "desc", "summary"],
            "version": ["version", "ver", "v"],
            "author": ["author", "creator", "by"],
            "created": ["created", "created_at", "date_created", "timestamp"],
            "modified": ["modified", "updated", "modified_at", "last_modified"],
            "tags": ["tags", "keywords", "labels"],
            "category": ["category", "type", "kind"],
        }

        # Extract fields using case-insensitive matching
        for meta_key, possible_keys in field_mappings.items():
            for data_key, value in data.items():
                if data_key.lower() in possible_keys:
                    metadata[meta_key] = value
                    break

        return metadata


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def read_schema_file(file_path: str) -> dict[str, Any] | None:
    """Convenience function to read a schema file.

    Args:
        file_path: Path to the schema file

    Returns:
        Dictionary with parsed data and analysis

    """
    reader = SchemaFileReader()
    return reader.read_file(file_path)


def read_json_file(file_path: str) -> dict | list | None:
    """Convenience function to read a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON data or None

    """
    reader = SchemaFileReader()
    result = reader.read_file(file_path)
    return result


def analyze_comfyui_workflow(file_path: str) -> dict[str, Any]:
    """Convenience function to analyze a ComfyUI workflow file.

    Args:
        file_path: Path to the workflow file

    Returns:
        Dictionary with workflow analysis

    """
    data = read_schema_file(file_path)
    if not data or not data.get("parsing_success"):
        return {"error": "Could not read workflow file"}

    # Get the actual data (JSON_DATA, etc.)
    workflow_data = None
    for key, value in data.items():
        if key.endswith("_DATA") and isinstance(value, dict):
            workflow_data = value
            break

    if not workflow_data:
        return {"error": "No workflow data found"}

    analyzer = StructuredDataAnalyzer()
    return analyzer.analyze_comfyui_workflow(workflow_data)


# ============================================================================
# TESTING UTILITIES
# ============================================================================


def test_schema_file_reader():
    """Test the schema file reader with sample data."""
    logger = get_logger("SchemaFileReaderTest")

    reader = SchemaFileReader()
    analyzer = StructuredDataAnalyzer()

    logger.info("Testing SchemaFileReader...")
    logger.info(f"Supported formats: {reader.get_supported_formats()}")

    # Test JSON data
    test_json_data = {
        "title": "Test Configuration",
        "version": "1.0",
        "author": "Test User",
        "settings": {
            "quality": "high",
            "format": "png",
            "options": ["option1", "option2"],
        },
        "metadata": {"created": "2025-01-01", "tags": ["test", "config"]},
    }

    # Test ComfyUI workflow data
    test_workflow_data = {
        "nodes": {
            "1": {"type": "CLIPTextEncode", "widgets_values": ["beautiful landscape"]},
            "2": {"type": "KSampler", "widgets_values": [42, 20, 7.0]},
            "3": {"type": "CheckpointLoaderSimple", "widgets_values": ["model.ckpt"]},
        },
        "links": [[1, 2, "CONDITIONING"], [2, 3, "LATENT"]],
    }

    # Create temporary test files
    test_files = [
        ("temp_test_config.json", test_json_data),
        ("temp_test_workflow.json", test_workflow_data),
    ]

    for file_name, data in test_files:
        test_file = Path(file_name)
        try:
            # Create test file
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.info(f"\nTesting with: {file_name}")

            # Test reading
            result = reader.read_file(str(test_file))
            if result:
                logger.info(f"Reading successful: {result.get('parsing_success')}")
                logger.info(f"File format: {result.get('file_format')}")
                logger.info(f"Data type: {result.get('data_type')}")
                logger.info(f"Key count: {result.get('key_count')}")

                if result.get("top_level_keys"):
                    logger.info(f"Top level keys: {result['top_level_keys']}")

                # Test pattern detection
                patterns = {k: v for k, v in result.items() if k.startswith("appears_to_be")}
                if patterns:
                    logger.info(f"Detected patterns: {patterns}")

                # Test ComfyUI workflow analysis if applicable
                if "workflow" in file_name:
                    workflow_analysis = analyze_comfyui_workflow(str(test_file))
                    logger.info(f"Workflow analysis: {workflow_analysis}")

                # Test metadata extraction
                if "JSON_DATA" in result:
                    metadata = analyzer.extract_metadata_fields(result["JSON_DATA"])
                    if metadata:
                        logger.info(f"Extracted metadata: {metadata}")

        except Exception as e:
            logger.error(f"Error testing {file_name}: {e}")

        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()

    # Test TOML if available
    if TOML_AVAILABLE:
        logger.info("\nTesting TOML support...")
        test_toml_file = Path("temp_test.toml")
        try:
            toml_content = """
title = "Test TOML Config"
version = "1.0"

[settings]
quality = "high"
format = "png"

[metadata]
created = "2025-01-01"
tags = ["test", "toml"]
"""
            test_toml_file.write_text(toml_content)

            result = reader.read_file(str(test_toml_file))
            if result:
                logger.info(f"TOML reading successful: {result.get('parsing_success')}")
                logger.info(f"TOML data type: {result.get('data_type')}")

        finally:
            if test_toml_file.exists():
                test_toml_file.unlink()

    logger.info("SchemaFileReader test completed!")


if __name__ == "__main__":
    # Run tests if module is executed directly
    test_schema_file_reader()
