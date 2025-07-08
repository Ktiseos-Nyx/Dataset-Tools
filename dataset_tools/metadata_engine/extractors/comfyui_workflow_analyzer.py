# dataset_tools/metadata_engine/extractors/comfyui_workflow_analyzer.py

"""ComfyUI workflow analyzer using node dictionary.

This module provides intelligent parsing of ComfyUI workflows using a comprehensive
node dictionary to extract meaningful metadata from complex workflow structures.
"""

import json
import logging
from pathlib import Path
from typing import Any

from ..utils import json_path_get_utility

# Type aliases
ContextData = dict[str, Any]
NodeData = dict[str, Any]
WorkflowData = dict[str, Any]


class ComfyUIWorkflowAnalyzer:
    """Analyzes ComfyUI workflows using node dictionary for intelligent extraction."""

    def __init__(self, logger: logging.Logger, dictionary_path: str | None = None):
        """Initialize the workflow analyzer."""
        self.logger = logger
        self.node_dictionary = self._load_node_dictionary(dictionary_path)

    def _load_node_dictionary(self, dictionary_path: str | None = None) -> dict[str, Any]:
        """Load the ComfyUI node dictionary."""
        if dictionary_path is None:
            # Default path relative to this file
            current_dir = Path(__file__).parent.parent.parent
            dictionary_path = current_dir / "comfyui_node_dictionary.json"

        try:
            with open(dictionary_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load ComfyUI node dictionary: {e}")
            return {"node_types": {}, "extraction_priorities": {}}

    def analyze_workflow(self, workflow_data: WorkflowData) -> dict[str, Any]:
        """Analyze a ComfyUI workflow and extract key metadata.

        Args:
            workflow_data: The parsed ComfyUI workflow JSON

        Returns:
            Dictionary with extracted workflow metadata

        """
        analysis = {
            "is_comfyui_workflow": True,
            "node_count": 0,
            "node_types_found": [],
            "extracted_parameters": {},
            "model_info": {},
            "prompt_info": {},
            "sampling_info": {},
            "workflow_chains": {},
            "errors": [],
        }

        try:
            # Extract nodes from workflow
            nodes = self._extract_nodes(workflow_data)
            if not nodes:
                analysis["is_comfyui_workflow"] = False
                analysis["errors"].append("No nodes found in workflow data")
                return analysis

            analysis["node_count"] = len(nodes)

            # Analyze each node
            node_analysis = self._analyze_nodes(nodes)
            analysis.update(node_analysis)

            # Extract parameters using priority system
            parameters = self._extract_parameters_by_priority(nodes)
            analysis["extracted_parameters"] = parameters

            # Group related information
            analysis["model_info"] = self._extract_model_info(nodes)
            analysis["prompt_info"] = self._extract_prompt_info(nodes)
            analysis["sampling_info"] = self._extract_sampling_info(nodes)

            # Analyze workflow structure
            links = workflow_data.get("links", [])
            analysis["workflow_chains"] = self._analyze_workflow_chains(nodes, links)

        except Exception as e:
            self.logger.error(f"Error analyzing ComfyUI workflow: {e}")
            analysis["errors"].append(f"Analysis error: {e!s}")

        return analysis

    def _extract_nodes(self, workflow_data: WorkflowData) -> dict[str, NodeData]:
        """Extract nodes from workflow data."""
        # ComfyUI workflows can have nodes in different formats
        if "nodes" in workflow_data:
            # Format: {"nodes": [{"id": 1, "type": "...", ...}, ...]}
            if isinstance(workflow_data["nodes"], list):
                return {str(node.get("id", i)): node for i, node in enumerate(workflow_data["nodes"])}
            if isinstance(workflow_data["nodes"], dict):
                return workflow_data["nodes"]

        # Format: {"1": {"type": "...", ...}, "2": {...}, ...}
        if all(key.isdigit() for key in workflow_data.keys() if isinstance(workflow_data[key], dict)):
            return {k: v for k, v in workflow_data.items() if isinstance(v, dict)}

        return {}

    def _analyze_nodes(self, nodes: dict[str, NodeData]) -> dict[str, Any]:
        """Analyze the nodes in the workflow."""
        node_types = []
        categories = {}

        for node_id, node_data in nodes.items():
            node_type = node_data.get("type") or node_data.get("class_type")
            if node_type:
                node_types.append(node_type)

                # Find category from dictionary
                category = self._get_node_category(node_type)
                if category:
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(node_type)

        return {
            "node_types_found": list(set(node_types)),
            "categories_used": categories,
            "has_model_loading": "loaders" in categories,
            "has_sampling": "sampling" in categories,
            "has_conditioning": "conditioning" in categories,
        }

    def _get_node_category(self, node_type: str) -> str | None:
        """Get the category of a node type from the dictionary."""
        node_types = self.node_dictionary.get("node_types", {})
        for category, types in node_types.items():
            if node_type in types:
                return category
        return None

    def _get_node_definition(self, node_type: str) -> dict[str, Any] | None:
        """Get the full definition of a node type."""
        node_types = self.node_dictionary.get("node_types", {})
        for category, types in node_types.items():
            if node_type in types:
                return types[node_type]
        return None

    def _extract_parameters_by_priority(self, nodes: dict[str, NodeData]) -> dict[str, Any]:
        """Extract parameters using the priority system from the dictionary."""
        parameters = {}
        priorities = self.node_dictionary.get("extraction_priorities", {})

        for param_name, priority_node_types in priorities.items():
            for node_type in priority_node_types:
                value = self._find_parameter_in_nodes(nodes, node_type, param_name)
                if value is not None:
                    parameters[param_name] = value
                    break  # Use first (highest priority) match

        return parameters

    def _find_parameter_in_nodes(self, nodes: dict[str, NodeData], node_type: str, param_name: str) -> Any:
        """Find a specific parameter from nodes of a given type."""
        node_def = self._get_node_definition(node_type)
        if not node_def:
            return None

        # Find nodes of this type
        matching_nodes = [
            node for node in nodes.values() if node.get("type") == node_type or node.get("class_type") == node_type
        ]

        if not matching_nodes:
            return None

        # Use the first matching node
        node = matching_nodes[0]

        # Extract based on node definition
        param_extraction = node_def.get("parameter_extraction", {})

        # Map parameter names to extraction patterns
        extraction_map = {
            "model": ["model_name", "ckpt_name"],
            "lora": ["lora_name"],
            "vae": ["vae_name"],
            "prompt": ["string", "prompt_text"],
            "sampler": ["sampler_name"],
            "scheduler": ["scheduler"],
            "steps": ["steps"],
            "cfg": ["cfg", "guidance"],
            "seed": ["noise_seed", "seed"],
            "dimensions": ["width", "height"],
        }

        # Try to extract the parameter
        possible_keys = extraction_map.get(param_name, [param_name])
        for key in possible_keys:
            if key in param_extraction:
                extraction_path = param_extraction[key]
                value = self._extract_value_from_node(node, extraction_path)
                if value is not None:
                    return value

        return None

    def _extract_value_from_node(self, node: NodeData, extraction_path: str) -> Any:
        """Extract a value from a node using the extraction path."""
        try:
            if extraction_path.startswith("widgets_values["):
                # Extract from widgets_values array
                index_str = extraction_path.split("[")[1].split("]")[0]
                index = int(index_str)
                widgets = node.get("widgets_values", [])
                if index < len(widgets):
                    return widgets[index]

            elif extraction_path.startswith("inputs."):
                # Extract from inputs object (TensorArt format)
                input_key = extraction_path.replace("inputs.", "", 1)
                inputs = node.get("inputs", {})
                return inputs.get(input_key)

            elif "." in extraction_path:
                # JSON path extraction
                return json_path_get_utility(node, extraction_path)

            else:
                # Direct key access
                return node.get(extraction_path)

        except Exception as e:
            self.logger.debug(f"Error extracting value with path '{extraction_path}': {e}")

        return None

    def _extract_model_info(self, nodes: dict[str, NodeData]) -> dict[str, Any]:
        """Extract model-related information."""
        model_info = {"main_model": None, "loras": [], "vae": None, "text_encoders": []}

        for node in nodes.values():
            node_type = node.get("type") or node.get("class_type")
            widgets = node.get("widgets_values", [])
            inputs = node.get("inputs", {})

            if node_type in ["UNETLoader", "CheckpointLoaderSimple"]:
                if widgets:
                    model_info["main_model"] = widgets[0]

            elif node_type == "ECHOCheckpointLoaderSimple":
                if inputs and "ckpt_name" in inputs:
                    model_info["main_model"] = inputs["ckpt_name"]

            elif node_type in ["LoraLoader", "LoraLoaderModelOnly"]:
                if len(widgets) >= 2:
                    model_info["loras"].append({"name": widgets[0], "strength": widgets[1]})

            elif node_type == "LoraTagLoader":
                if inputs and "text" in inputs:
                    # Parse LoRA tags like "<lora:name:strength>"
                    lora_text = inputs["text"]
                    import re

                    lora_matches = re.findall(r"<lora:([^:]+):([^>]+)>", lora_text)
                    for name, strength in lora_matches:
                        model_info["loras"].append(
                            {
                                "name": name,
                                "strength": (float(strength) if strength.replace(".", "").isdigit() else strength),
                            }
                        )

            elif node_type == "VAELoader":
                if widgets:
                    model_info["vae"] = widgets[0]

            elif node_type == "DualCLIPLoader":
                if len(widgets) >= 2:
                    model_info["text_encoders"] = [widgets[0], widgets[1]]

        return model_info

    def _extract_prompt_info(self, nodes: dict[str, NodeData]) -> dict[str, Any]:
        """Extract prompt-related information."""
        prompt_info = {
            "positive_prompt": None,
            "negative_prompt": None,
            "guidance_scale": None,
        }

        positive_found = False

        # Extract prompts from various text encoding nodes
        for node in nodes.values():
            node_type = node.get("type") or node.get("class_type")

            if node_type == "String Literal":
                widgets = node.get("widgets_values", [])
                if widgets and widgets[0]:
                    # Assume first non-empty string is positive prompt
                    if not prompt_info["positive_prompt"]:
                        prompt_info["positive_prompt"] = widgets[0]
                        positive_found = True
                    elif not prompt_info["negative_prompt"]:
                        prompt_info["negative_prompt"] = widgets[0]

            elif node_type in ["BNK_CLIPTextEncodeAdvanced", "CLIPTextEncode"]:
                # Extract text from inputs or widgets
                text = None
                if "inputs" in node and "text" in node["inputs"]:
                    text = node["inputs"]["text"]
                elif node.get("widgets_values"):
                    text = node["widgets_values"][0]

                if text:
                    # Heuristic: shorter texts or those with negative keywords are likely negative prompts
                    is_negative = (
                        any(
                            neg_word in text.lower()
                            for neg_word in [
                                "nsfw",
                                "bare",
                                "nipple",
                                "breast",
                                "bad",
                                "worst",
                                "ugly",
                                "deformed",
                            ]
                        )
                        or len(text) < 100
                    )

                    if is_negative and not prompt_info["negative_prompt"]:
                        prompt_info["negative_prompt"] = text
                    elif not is_negative and not prompt_info["positive_prompt"]:
                        prompt_info["positive_prompt"] = text
                        positive_found = True

            elif node_type == "ImpactWildcardEncode":
                widgets = node.get("widgets_values", [])
                if widgets and widgets[0] and not prompt_info["positive_prompt"]:
                    prompt_info["positive_prompt"] = widgets[0]
                    positive_found = True

            elif node_type == "FluxGuidance":
                widgets = node.get("widgets_values", [])
                if widgets:
                    prompt_info["guidance_scale"] = widgets[0]

        return prompt_info

    def _extract_sampling_info(self, nodes: dict[str, NodeData]) -> dict[str, Any]:
        """Extract sampling-related information."""
        sampling_info = {
            "sampler": None,
            "scheduler": None,
            "steps": None,
            "cfg_scale": None,
            "seed": None,
            "width": None,
            "height": None,
        }

        for node in nodes.values():
            node_type = node.get("type") or node.get("class_type")
            widgets = node.get("widgets_values", [])
            inputs = node.get("inputs", {})

            if node_type == "KSamplerSelect" and widgets:
                sampling_info["sampler"] = widgets[0]

            elif node_type == "BasicScheduler" and len(widgets) >= 2:
                sampling_info["scheduler"] = widgets[0]
                sampling_info["steps"] = widgets[1]

            elif node_type == "RandomNoise" and widgets:
                sampling_info["seed"] = widgets[0]

            elif node_type == "EmptyLatentImage":
                if len(widgets) >= 2:
                    sampling_info["width"] = widgets[0]
                    sampling_info["height"] = widgets[1]
                elif inputs:
                    sampling_info["width"] = inputs.get("width")
                    sampling_info["height"] = inputs.get("height")

            elif node_type == "KSampler_A1111" and inputs:
                sampling_info["sampler"] = inputs.get("sampler_name")
                sampling_info["scheduler"] = inputs.get("scheduler")
                sampling_info["steps"] = inputs.get("steps")
                sampling_info["cfg_scale"] = inputs.get("cfg")
                sampling_info["seed"] = inputs.get("seed")

            elif node_type == "Int Literal" and widgets:
                # Try to determine if this is width or height based on title
                title = node.get("title", "").lower()
                if "width" in title:
                    sampling_info["width"] = widgets[0]
                elif "height" in title:
                    sampling_info["height"] = widgets[0]

        return sampling_info

    def _analyze_workflow_chains(self, nodes: dict[str, NodeData], links: list[Any]) -> dict[str, list[str]]:
        """Analyze the workflow connection chains."""
        chains = {
            "model_chain": [],
            "conditioning_chain": [],
            "sampling_chain": [],
            "output_chain": [],
        }

        # Identify chains based on common patterns
        common_chains = self.node_dictionary.get("common_connections", {})

        for chain_name, expected_types in common_chains.items():
            found_types = []
            for node in nodes.values():
                node_type = node.get("type") or node.get("class_type")
                if node_type in expected_types:
                    found_types.append(node_type)

            chains[chain_name] = found_types

        return chains


# Convenience function for easy access
def analyze_comfyui_workflow(workflow_data: WorkflowData, logger: logging.Logger | None = None) -> dict[str, Any]:
    """Convenience function to analyze a ComfyUI workflow.

    Args:
        workflow_data: The parsed ComfyUI workflow JSON
        logger: Optional logger instance

    Returns:
        Dictionary with extracted workflow metadata

    """
    if logger is None:
        import logging

        logger = logging.getLogger(__name__)

    analyzer = ComfyUIWorkflowAnalyzer(logger)
    return analyzer.analyze_workflow(workflow_data)
