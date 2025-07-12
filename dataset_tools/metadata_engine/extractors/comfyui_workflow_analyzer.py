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

    def _load_node_dictionary(
        self, dictionary_path: str | None = None
    ) -> dict[str, Any]:
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
            links = workflow_data.get("links", [])
            analysis["prompt_info"] = self._extract_prompt_info(nodes, links)
            analysis["sampling_info"] = self._extract_sampling_info(nodes)

            # Analyze workflow structure
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
                return {
                    str(node.get("id", i)): node
                    for i, node in enumerate(workflow_data["nodes"])
                }
            if isinstance(workflow_data["nodes"], dict):
                return workflow_data["nodes"]

        # Format: {"1": {"type": "...", ...}, "2": {...}, ...}
        if all(
            key.isdigit()
            for key in workflow_data.keys()
            if isinstance(workflow_data[key], dict)
        ):
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

    def _extract_parameters_by_priority(
        self, nodes: dict[str, NodeData]
    ) -> dict[str, Any]:
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

    def _find_parameter_in_nodes(
        self, nodes: dict[str, NodeData], node_type: str, param_name: str
    ) -> Any:
        """Find a specific parameter from nodes of a given type."""
        node_def = self._get_node_definition(node_type)
        if not node_def:
            return None

        # Find nodes of this type
        matching_nodes = [
            node
            for node in nodes.values()
            if node.get("type") == node_type or node.get("class_type") == node_type
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
            self.logger.debug(
                f"Error extracting value with path '{extraction_path}': {e}"
            )

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
                    model_info["loras"].append(
                        {"name": widgets[0], "strength": widgets[1]}
                    )

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
                                "strength": (
                                    float(strength)
                                    if strength.replace(".", "").isdigit()
                                    else strength
                                ),
                            }
                        )

            elif node_type == "VAELoader":
                if widgets:
                    model_info["vae"] = widgets[0]

            elif node_type == "DualCLIPLoader":
                if len(widgets) >= 2:
                    model_info["text_encoders"] = [widgets[0], widgets[1]]

        return model_info

    def _extract_prompt_info(
        self, nodes: dict[str, NodeData], links: list[Any]
    ) -> dict[str, Any]:
        """Extract prompt-related information by tracing KSampler inputs."""
        prompt_info = {
            "positive_prompt": None,
            "negative_prompt": None,
            "guidance_scale": None,
        }

        # Find KSampler (or similar) nodes
        sampler_nodes = [
            node
            for node in nodes.values()
            if node.get("type")
            in [
                "KSampler",
                "KSamplerAdvanced",
                "SamplerCustom",
                "SamplerCustomAdvanced",
            ]
            or node.get("class_type")
            in [
                "KSampler",
                "KSamplerAdvanced",
                "SamplerCustom",
                "SamplerCustomAdvanced",
            ]
        ]

        for sampler_node in sampler_nodes:
            sampler_inputs = sampler_node.get("inputs", {})

            # Trace positive conditioning
            positive_link = sampler_inputs.get("positive")
            if (
                positive_link
                and isinstance(positive_link, list)
                and len(positive_link) >= 2
            ):
                source_node_id = str(positive_link[0])
                positive_prompt_text = self._trace_conditioning_source(
                    nodes, links, source_node_id
                )
                if positive_prompt_text:
                    self.logger.debug(f"Traced positive prompt: {positive_prompt_text}")
                    if not prompt_info["positive_prompt"]:
                        prompt_info["positive_prompt"] = positive_prompt_text

            # Trace negative conditioning
            negative_link = sampler_inputs.get("negative")
            if (
                negative_link
                and isinstance(negative_link, list)
                and len(negative_link) >= 2
            ):
                source_node_id = str(negative_link[0])
                negative_prompt_text = self._trace_conditioning_source(
                    nodes, links, source_node_id
                )
                if negative_prompt_text:
                    self.logger.debug(f"Traced negative prompt: {negative_prompt_text}")
                    if not prompt_info["negative_prompt"]:
                        prompt_info["negative_prompt"] = negative_prompt_text

            # Extract guidance scale if available (e.g., from FluxGuidance)
            # This part remains similar to previous logic, but can be refined with tracing if needed
            if "cfg" in sampler_inputs:
                prompt_info["guidance_scale"] = sampler_inputs["cfg"]
            elif (
                "widgets_values" in sampler_node
                and len(sampler_node["widgets_values"]) > 2
            ):
                # KSampler widgets: seed, steps, cfg, sampler_name, scheduler, denoise
                try:
                    prompt_info["guidance_scale"] = float(
                        sampler_node["widgets_values"][2]
                    )
                except (ValueError, TypeError):
                    pass

            # Break after finding prompts from the first sampler, or continue if multiple samplers are relevant
            if prompt_info["positive_prompt"] and prompt_info["negative_prompt"]:
                break

        # Fallback for FluxGuidance if not connected directly to KSampler
        if not prompt_info["guidance_scale"]:
            for node in nodes.values():
                node_type = node.get("type") or node.get("class_type")
                if node_type == "FluxGuidance":
                    widgets = node.get("widgets_values", [])
                    if widgets:
                        prompt_info["guidance_scale"] = widgets[0]
                    break

        return prompt_info

    def _trace_conditioning_source(
        self,
        nodes: dict[str, NodeData],
        links: list[Any],
        start_node_id: str,
        depth: int = 0,
    ) -> str | None:
        """Recursively traces back the conditioning source to find the prompt text."""
        if depth > 10:  # Prevent infinite loops in complex workflows
            self.logger.debug(f"Max tracing depth reached for node {start_node_id}")
            return None

        current_node = nodes.get(start_node_id)
        if not current_node:
            return None

        class_type = current_node.get("type") or current_node.get("class_type")
        inputs = current_node.get("inputs", {})
        widgets = current_node.get("widgets_values", [])

        # Direct text sources
        if class_type == "String Literal":
            if widgets:
                return str(widgets[0])
        elif class_type == "CLIPTextEncode":
            # Prioritize linked 'text' input over widget values if available
            if (
                "text" in inputs
                and isinstance(inputs["text"], list)
                and len(inputs["text"]) >= 2
            ):
                source_node_id = str(inputs["text"][0])
                traced_text = self._trace_conditioning_source(
                    nodes, links, source_node_id, depth + 1
                )
                if traced_text:
                    self.logger.debug(
                        f"CLIPTextEncode (linked input) found text: {traced_text}"
                    )
                    return traced_text
            elif "text" in inputs:  # Direct text input
                self.logger.debug(
                    f"CLIPTextEncode (direct input) found text: {inputs['text']}"
                )
                return str(inputs["text"])
            elif widgets:
                self.logger.debug(f"CLIPTextEncode (widgets) found text: {widgets[0]}")
                return str(widgets[0])
        elif class_type == "CLIPTextEncodeSDXL":
            # For SDXL, we need to know if it's positive or negative branch
            # This method is called from positive/negative links, so we assume the role
            if (
                "text_g" in inputs
            ):  # Assuming text_g is for positive, text_l for negative
                return str(inputs["text_g"])
            if "text_l" in inputs:
                return str(inputs["text_l"])
        elif class_type == "T5TextEncode":
            if "text" in inputs:
                return str(inputs["text"])
        elif class_type == "MZ_ChatGLM3_V2":  # New: ChatGLM3 text encoder
            if widgets and widgets[0]:
                return str(widgets[0])
        elif class_type == "DPRandomGenerator":  # Dynamic Prompts
            # DPRandomGenerator outputs a string, which is the template itself
            if "text" in inputs:
                return str(inputs["text"])
            if widgets and widgets[0]:
                return str(widgets[0])
        elif class_type == "ConcatStringSingle":  # ConcatStringSingle
            # Recursively trace all string inputs and concatenate them
            concatenated_text = []
            for input_name, input_value in inputs.items():
                if input_name.startswith("string"):
                    if isinstance(input_value, list) and len(input_value) >= 2:
                        source_node_id = str(input_value[0])
                        traced_text = self._trace_conditioning_source(
                            nodes, links, source_node_id, depth + 1
                        )
                        if traced_text:
                            concatenated_text.append(traced_text)
                    elif isinstance(input_value, str):
                        concatenated_text.append(input_value)
            return " ".join(concatenated_text).strip()

        # Traverse through passthrough/reroute nodes or conditioning manipulators
        if class_type in [
            "Reroute",
            "ConditioningCombine",
            "ConditioningConcat",
            "ConditioningSetArea",
            "ConditioningSetTimestepRange",
            "ConditioningAverage",
            "ConditioningZeroOut",
            "ConditioningSetAreaPercentage",
            "ConditioningAlign",
            "ConditioningSetAreaLite",
            "ConditioningSetAreaByMask",
            "ConditioningSetAreaByBoundingBox",
            "ConditioningSetAreaByImage",
            "ConditioningSetAreaByImageSize",
            "ConditioningSetAreaByImageSizeRatio",
            "ConditioningSetAreaByImageSizeRatioPercentage",
            "ConditioningSetAreaByImageSizeRatioPercentageByMask",
            "ConditioningSetAreaByImageSizeRatioPercentageByBoundingBox",
            "ConditioningSetAreaByImageSizeRatioPercentageByImage",
            "ConditioningSetAreaByImageSizeRatioPercentageByImageSizeRatio",
            "ConditioningSetAreaByImageSizeRatioPercentageByImageSizeRatioPercentage",
            "ConditioningSubtract",
            "ConditioningAddConDelta",
        ]:
            # Find the incoming link for the conditioning
            for input_name, input_value in inputs.items():
                if isinstance(input_value, list) and len(input_value) >= 2:
                    # This is a connection to another node
                    source_node_id = str(input_value[0])
                    # Recursively trace back
                    result = self._trace_conditioning_source(
                        nodes, links, source_node_id, depth + 1
                    )
                    if result:
                        return result

        # Handle nodes that might pass through conditioning without direct text input
        # e.g., LoraLoader, CheckpointLoaderSimple (if they output conditioning directly)
        # This part might need more specific logic based on how these nodes are used
        # in relation to conditioning in complex workflows.

        return None

    def _extract_sampling_info(self, nodes: dict[str, NodeData]) -> dict[str, Any]:
        """Extract sampling-related information from nodes."""
        sampling_info = {
            "steps": None,
            "cfg": None,
            "sampler_name": None,
            "scheduler": None,
            "denoise": None,
        }
        
        # Find sampler nodes
        for node in nodes.values():
            node_type = node.get("type") or node.get("class_type", "")
            
            if "KSampler" in node_type or "Sampler" in node_type:
                widgets = node.get("widgets_values", [])
                if widgets:
                    try:
                        if len(widgets) >= 3:
                            sampling_info["steps"] = widgets[2] if widgets[2] else None
                            sampling_info["cfg"] = widgets[3] if len(widgets) > 3 and widgets[3] else None
                        if len(widgets) >= 2:
                            sampling_info["sampler_name"] = widgets[0] if widgets[0] else None
                            sampling_info["scheduler"] = widgets[1] if widgets[1] else None
                        if len(widgets) >= 5:
                            sampling_info["denoise"] = widgets[4] if widgets[4] else None
                    except (IndexError, TypeError):
                        continue
                break
                
        return sampling_info

    def _analyze_workflow_chains(self, nodes: dict[str, NodeData], links: list[Any]) -> dict[str, Any]:
        """Analyze workflow connection chains and patterns."""
        chains = {
            "model_chain": [],
            "conditioning_chain": [],
            "image_chain": [],
            "total_nodes": len(nodes),
            "total_links": len(links),
        }
        
        # Basic chain analysis - find major node types in sequence
        node_types = [node.get("type") or node.get("class_type", "") for node in nodes.values()]
        
        # Model loading chain
        model_nodes = [nt for nt in node_types if "Loader" in nt or "Model" in nt]
        chains["model_chain"] = model_nodes
        
        # Conditioning chain  
        conditioning_nodes = [nt for nt in node_types if "CLIP" in nt or "Encode" in nt]
        chains["conditioning_chain"] = conditioning_nodes
        
        # Image processing chain
        image_nodes = [nt for nt in node_types if "Image" in nt or "Save" in nt or "Preview" in nt]
        chains["image_chain"] = image_nodes
        
        return chains


# Convenience function for easy access
def analyze_comfyui_workflow(
    workflow_data: WorkflowData, logger: logging.Logger | None = None
) -> dict[str, Any]:
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
