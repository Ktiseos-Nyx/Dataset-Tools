# dataset_tools/metadata_engine/extractors/comfyui_node_dictionary_manager.py

"""ComfyUI Node Dictionary Manager.

Enhanced utility for leveraging the comprehensive ComfyUI node dictionary
to provide intelligent node detection, parameter extraction, and workflow analysis.
This replaces generic traversal with dictionary-driven precision extraction.
"""

import json
import logging
from pathlib import Path
from typing import Any

# Type aliases
NodeData = dict[str, Any]
WorkflowData = dict[str, Any]
ExtractionResult = dict[str, Any]


class ComfyUINodeDictionaryManager:
    """Manages the ComfyUI node dictionary for intelligent extraction."""

    def __init__(self, logger: logging.Logger, dictionary_path: str | None = None):
        """Initialize the node dictionary manager."""
        self.logger = logger
        self.dictionary = self._load_dictionary(dictionary_path)
        self.node_types = self.dictionary.get("node_types", {})
        self.extraction_priorities = self.dictionary.get("extraction_priorities", {})
        self.common_connections = self.dictionary.get("common_connections", {})

        # Build reverse lookup maps for faster searches
        self._build_lookup_maps()

    def _load_dictionary(self, dictionary_path: str | None = None) -> dict[str, Any]:
        """Load the ComfyUI node dictionary."""
        if dictionary_path is None:
            current_dir = Path(__file__).parent.parent.parent
            dictionary_path = current_dir / "comfyui_node_dictionary.json"

        try:
            with open(dictionary_path, encoding="utf-8") as f:
                dictionary = json.load(f)
                self.logger.info(f"Loaded ComfyUI node dictionary v{dictionary.get('metadata', {}).get('version', 'unknown')}")
                return dictionary
        except Exception as e:
            self.logger.error(f"Failed to load ComfyUI node dictionary: {e}")
            return {"node_types": {}, "extraction_priorities": {}, "common_connections": {}}

    def _build_lookup_maps(self):
        """Build reverse lookup maps for efficient node searching."""
        # Map node class names to their definitions
        self.node_class_to_definition = {}

        # Map categories to node lists
        self.category_to_nodes = {}

        # Map parameter types to prioritized node lists
        self.parameter_to_nodes = self.extraction_priorities.copy()

        for category, nodes in self.node_types.items():
            self.category_to_nodes[category] = list(nodes.keys())
            for node_class, node_def in nodes.items():
                self.node_class_to_definition[node_class] = {
                    "category": category,
                    **node_def
                }

    def get_node_definition(self, node_class: str) -> dict[str, Any] | None:
        """Get the definition for a specific node class."""
        return self.node_class_to_definition.get(node_class)

    def get_nodes_by_category(self, category: str) -> list[str]:
        """Get all node class names in a specific category."""
        return self.category_to_nodes.get(category, [])

    def get_priority_nodes_for_parameter(self, parameter_type: str) -> list[str]:
        """Get prioritized list of nodes that can extract a specific parameter."""
        return self.parameter_to_nodes.get(parameter_type, [])

    def extract_parameter_from_node(self, node_data: NodeData, node_class: str, parameter_type: str) -> Any:
        """Extract a specific parameter from a node using dictionary patterns."""
        node_def = self.get_node_definition(node_class)
        if not node_def:
            self.logger.debug(f"No dictionary definition found for node class: {node_class}")
            return None

        extraction_patterns = node_def.get("parameter_extraction", {})

        # Try direct parameter extraction first
        if parameter_type in extraction_patterns:
            pattern = extraction_patterns[parameter_type]
            return self._extract_using_pattern(node_data, pattern)

        # Try common parameter mappings
        common_mappings = {
            "prompt": ["prompt_text", "text", "positive"],
            "negative_prompt": ["negative_text", "negative"],
            "model": ["model_name", "ckpt_name"],
            "seed": ["seed"],
            "steps": ["steps"],
            "cfg_scale": ["cfg", "guidance"],
            "sampler": ["sampler_name"],
            "scheduler": ["scheduler"]
        }

        mapped_keys = common_mappings.get(parameter_type, [parameter_type])
        for key in mapped_keys:
            if key in extraction_patterns:
                pattern = extraction_patterns[key]
                result = self._extract_using_pattern(node_data, pattern)
                if result is not None:
                    return result

        return None

    def _extract_using_pattern(self, node_data: NodeData, pattern: str) -> Any:
        """Extract data using a dictionary extraction pattern."""
        try:
            # Handle widgets_values patterns
            if pattern.startswith("widgets_values[") and pattern.endswith("]"):
                index_str = pattern[15:-1]  # Extract index from "widgets_values[X]"
                index = int(index_str)
                widgets = node_data.get("widgets_values", [])
                if 0 <= index < len(widgets):
                    return widgets[index]

            # Handle input patterns
            elif pattern.startswith("inputs."):
                input_path = pattern[7:]  # Remove "inputs."
                inputs = node_data.get("inputs", {})
                return self._get_nested_value(inputs, input_path)

            # Handle direct key access
            else:
                return node_data.get(pattern)

        except Exception as e:
            self.logger.debug(f"Failed to extract using pattern '{pattern}': {e}")

        return None

    def _get_nested_value(self, data: dict, path: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def find_best_node_for_parameter(self, workflow_nodes: dict[str, NodeData], parameter_type: str) -> tuple[str, NodeData] | None:
        """Find the best node in a workflow for extracting a specific parameter."""
        priority_nodes = self.get_priority_nodes_for_parameter(parameter_type)

        # Search in priority order
        for node_class in priority_nodes:
            for node_id, node_data in workflow_nodes.items():
                if self._node_matches_class(node_data, node_class):
                    # Verify this node actually has the parameter
                    extracted_value = self.extract_parameter_from_node(node_data, node_class, parameter_type)
                    if extracted_value is not None:
                        self.logger.debug(f"Found {parameter_type} in {node_class} (node {node_id})")
                        return node_id, node_data

        return None

    def _node_matches_class(self, node_data: NodeData, node_class: str) -> bool:
        """Check if a node matches a specific class."""
        return node_data.get("class_type") == node_class or node_data.get("type") == node_class

    def analyze_workflow_structure(self, workflow_data: WorkflowData) -> dict[str, Any]:
        """Analyze workflow structure using dictionary knowledge."""
        nodes = self._get_nodes_from_workflow(workflow_data)
        if not nodes:
            return {"error": "No nodes found in workflow"}

        analysis = {
            "total_nodes": len(nodes),
            "node_categories": {},
            "custom_nodes": [],
            "known_nodes": [],
            "workflow_patterns": [],
            "extraction_coverage": {}
        }

        # Categorize nodes
        for node_id, node_data in nodes.items():
            node_class = node_data.get("class_type") or node_data.get("type", "unknown")
            node_def = self.get_node_definition(node_class)

            if node_def:
                category = node_def["category"]
                analysis["node_categories"][category] = analysis["node_categories"].get(category, 0) + 1
                analysis["known_nodes"].append(node_class)
            else:
                analysis["custom_nodes"].append(node_class)

        # Detect workflow patterns
        analysis["workflow_patterns"] = self._detect_workflow_patterns(nodes)

        # Check extraction coverage
        analysis["extraction_coverage"] = self._check_extraction_coverage(nodes)

        return analysis

    def _get_nodes_from_workflow(self, workflow_data: WorkflowData) -> dict[str, NodeData]:
        """Extract nodes from workflow data in various formats."""
        if "nodes" in workflow_data:
            # Workflow format: {"nodes": [list]}
            nodes = {}
            for node in workflow_data.get("nodes", []):
                node_id = str(node.get("id", len(nodes)))
                nodes[node_id] = node
            return nodes
        if isinstance(workflow_data, dict) and all(isinstance(v, dict) for v in workflow_data.values()):
            # Prompt format: {"1": {node}, "2": {node}, ...}
            return workflow_data
        return {}

    def _detect_workflow_patterns(self, nodes: dict[str, NodeData]) -> list[str]:
        """Detect common workflow patterns."""
        patterns = []
        node_classes = [node.get("class_type", "") for node in nodes.values()]

        # Check for known connection patterns
        for pattern_name, pattern_nodes in self.common_connections.items():
            if any(node_class in node_classes for node_class in pattern_nodes):
                patterns.append(pattern_name)

        # Detect architecture patterns
        if any("Flux" in node_class for node_class in node_classes):
            patterns.append("flux_architecture")
        if any("SDXL" in node_class for node_class in node_classes):
            patterns.append("sdxl_architecture")
        if any("ControlNet" in node_class for node_class in node_classes):
            patterns.append("controlnet_workflow")
        if any("Lora" in node_class for node_class in node_classes):
            patterns.append("lora_enhanced")

        return patterns

    def _check_extraction_coverage(self, nodes: dict[str, NodeData]) -> dict[str, bool]:
        """Check which parameters can be extracted from the workflow."""
        coverage = {}

        for parameter_type in self.extraction_priorities.keys():
            result = self.find_best_node_for_parameter(nodes, parameter_type)
            coverage[parameter_type] = result is not None

        return coverage

    def get_extraction_report(self, workflow_data: WorkflowData) -> dict[str, Any]:
        """Generate a comprehensive extraction report for a workflow."""
        nodes = self._get_nodes_from_workflow(workflow_data)
        analysis = self.analyze_workflow_structure(workflow_data)

        # Extract all available parameters
        extracted_parameters = {}
        for parameter_type in self.extraction_priorities.keys():
            result = self.find_best_node_for_parameter(nodes, parameter_type)
            if result:
                node_id, node_data = result
                node_class = node_data.get("class_type", node_data.get("type", "unknown"))
                value = self.extract_parameter_from_node(node_data, node_class, parameter_type)
                extracted_parameters[parameter_type] = {
                    "value": value,
                    "source_node": node_id,
                    "source_class": node_class
                }

        return {
            "workflow_analysis": analysis,
            "extracted_parameters": extracted_parameters,
            "extraction_success_rate": len(extracted_parameters) / len(self.extraction_priorities),
            "recommendations": self._generate_recommendations(analysis, extracted_parameters)
        }

    def _generate_recommendations(self, analysis: dict, extracted_parameters: dict) -> list[str]:
        """Generate recommendations for improving extraction."""
        recommendations = []

        missing_params = []
        for param_type in self.extraction_priorities.keys():
            if param_type not in extracted_parameters:
                missing_params.append(param_type)

        if missing_params:
            recommendations.append(f"Missing parameters: {', '.join(missing_params)}")

        if analysis["custom_nodes"]:
            recommendations.append(f"Custom nodes detected: {', '.join(set(analysis['custom_nodes'])[:5])}")
            recommendations.append("Consider updating node dictionary for custom nodes")

        if analysis["extraction_coverage"]["prompt"] and not analysis["extraction_coverage"]["negative_prompt"]:
            recommendations.append("Positive prompt found but negative prompt missing - check for conditioning setup")

        return recommendations
