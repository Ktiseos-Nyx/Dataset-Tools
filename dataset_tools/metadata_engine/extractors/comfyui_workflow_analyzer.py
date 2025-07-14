# dataset_tools/metadata_engine/extractors/comfyui_workflow_analyzer.py

"""IMPROVED ComfyUI workflow analyzer.

This version moves to a "trace-everything" paradigm. Instead of reading widget
values by index, it traces every key input (model, seed, steps, cfg, etc.)
back to its source node to find the literal value. This makes the parser
far more robust against custom nodes and complex workflows. It also correctly
identifies and analyzes multi-stage workflows (e.g., base pass + hires fix).
"""

import json
import logging
from pathlib import Path
from typing import Any

# Assume utils is in a sibling directory or accessible via python path

# Type aliases
ContextData = dict[str, Any]
NodeData = dict[str, Any]
WorkflowData = dict[str, Any]
Link = list[Any]


class ComfyUIWorkflowAnalyzer:
    """Analyzes ComfyUI workflows using a robust tracing methodology."""

    def __init__(self, logger: logging.Logger, dictionary_path: str | None = None):
        """Initialize the workflow analyzer."""
        self.logger = logger
        self.node_dictionary = self._load_node_dictionary(dictionary_path)
        # Store workflow data for access during recursive calls
        self.nodes: dict[str, NodeData] = {}
        self.links: list[Link] = []

    def _load_node_dictionary(self, dictionary_path: str | None = None) -> dict[str, Any]:
        """Load the ComfyUI node dictionary."""
        # Your existing dictionary loading logic is good.
        if dictionary_path is None:
            current_dir = Path(__file__).parent.parent.parent
            dictionary_path = current_dir / "comfyui_node_dictionary.json"
        try:
            with open(dictionary_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load ComfyUI node dictionary: {e}")
            return {}

    def analyze_workflow(self, workflow_data: WorkflowData) -> dict[str, Any]:
        """Analyze a ComfyUI workflow and extract key metadata."""
        if not workflow_data or not isinstance(workflow_data, dict):
            return {
                "is_valid_workflow": False,
                "error": "Input data is not a valid workflow dictionary.",
            }

        self.nodes = self._extract_nodes(workflow_data)
        self.links = workflow_data.get("links", [])

        if not self.nodes:
            return {
                "is_valid_workflow": False,
                "error": "No nodes found in workflow data",
            }

        sampler_nodes = self._find_sampler_nodes()

        generation_passes = []
        for sampler_node in sampler_nodes:
            pass_info = self._analyze_generation_pass(sampler_node)
            generation_passes.append(pass_info)

        return {
            "is_valid_workflow": True,
            "node_count": len(self.nodes),
            "link_count": len(self.links),
            "generation_passes": generation_passes,
            "custom_nodes_used": self._get_custom_node_types(),
        }

    def _extract_nodes(self, workflow_data: WorkflowData) -> dict[str, NodeData]:
        """Extracts and standardizes the node dictionary from the workflow."""
        nodes_data = workflow_data.get("nodes", {})
        if isinstance(nodes_data, list):
            return {str(node.get("id", i)): node for i, node in enumerate(nodes_data)}
        if isinstance(nodes_data, dict):
            # Handles both {"1": {...}} and old formats
            return {k: v for k, v in nodes_data.items() if isinstance(v, dict)}
        return {}

    def _find_sampler_nodes(self) -> list[NodeData]:
        """Finds all KSampler (or equivalent) nodes in the workflow."""
        sampler_types = ["KSampler", "KSamplerAdvanced", "SamplerCustom"]
        found_samplers = []
        for node in self.nodes.values():
            node_type = node.get("type") or node.get("class_type")
            if node_type in sampler_types:
                found_samplers.append(node)
        # Sort by vertical position as a heuristic for execution order
        return sorted(found_samplers, key=lambda n: n.get("pos", [0, 0])[1])

    def _analyze_generation_pass(self, sampler_node: NodeData) -> dict[str, Any]:
        """Analyzes a single generation pass starting from a sampler node."""
        sampler_id = str(sampler_node.get("id"))

        # Use the new unified tracing method for everything
        model_info = {
            "model": self._trace_to_source_value(sampler_id, "model", "ckpt_name"),
            "vae": self._trace_to_source_value(sampler_id, "vae", "vae_name"),
        }

        prompt_info = {
            "positive_prompt": self._trace_conditioning_source(sampler_id, "positive"),
            "negative_prompt": self._trace_conditioning_source(sampler_id, "negative"),
        }

        sampling_info = {
            "seed": self._trace_to_source_value(sampler_id, "seed", "seed", "INT"),
            "steps": self._trace_to_source_value(sampler_id, "steps", "steps", "INT"),
            "cfg": self._trace_to_source_value(sampler_id, "cfg", "cfg", "FLOAT"),
            "sampler_name": self._trace_to_source_value(sampler_id, "sampler_name", "sampler_name", "STRING"),
            "scheduler": self._trace_to_source_value(sampler_id, "scheduler", "scheduler", "STRING"),
            "denoise": self._trace_to_source_value(sampler_id, "denoise", "denoise", "FLOAT"),
        }

        latent_info = {
            "width": self._trace_to_source_value(sampler_id, "latent_image", "width", "INT"),
            "height": self._trace_to_source_value(sampler_id, "latent_image", "height", "INT"),
        }

        return {
            "sampler_node_id": sampler_id,
            "sampler_node_type": sampler_node.get("type") or sampler_node.get("class_type"),
            "model_info": model_info,
            "prompt_info": prompt_info,
            "sampling_info": sampling_info,
            "latent_info": latent_info,
        }

    def _find_input_link(self, node_id: str, input_name: str) -> Link | None:
        """Finds the link connected to a specific input of a node."""
        node = self.nodes.get(node_id)
        if not node:
            return None

        # Standard format: inputs is a list of dicts
        for i, inp in enumerate(node.get("inputs", [])):
            if inp.get("name") == input_name:
                link_index = inp.get("link")
                if link_index is not None:
                    # Find the link by its ID
                    for link in self.links:
                        if link[0] == link_index:
                            return link
                return None  # Input found but not linked

        # Fallback for some formats where inputs is a dict
        inputs_dict = node.get("inputs", {})
        if isinstance(inputs_dict, dict) and input_name in inputs_dict:
            link_info = inputs_dict[input_name]
            if isinstance(link_info, list) and len(link_info) >= 2:
                # Format: [source_node_id, source_slot_index]
                for link in self.links:
                    if link[1] == link_info[0] and link[2] == link_info[1]:
                        return link
        return None

    def _trace_to_source_value(
        self,
        start_node_id: str,
        input_to_trace: str,
        target_widget_name: str,
        target_type: str = "STRING",
        depth=0,
    ) -> Any:
        """The new powerhouse function. Traces any input back to its literal source value."""
        if depth > 20:
            return None  # Safety break

        link = self._find_input_link(start_node_id, input_to_trace)
        if not link:
            return None

        source_node_id = str(link[1])
        source_node = self.nodes.get(source_node_id)
        if not source_node:
            return None

        node_type = source_node.get("type") or source_node.get("class_type")
        widgets = source_node.get("widgets_values", [])

        # Check if the source node IS the provider of the value
        if node_type in [
            "CheckpointLoaderSimple",
            "VAELoader",
            "LoraLoader",
            "EmptyLatentImage",
            "PrimitiveNode",
        ]:
            if widgets:
                # For EmptyLatentImage, find width/height
                if node_type == "EmptyLatentImage" and target_widget_name in [
                    "width",
                    "height",
                ]:
                    return widgets[0] if target_widget_name == "width" else widgets[1]
                # For PrimitiveNode, the value is the only widget
                if node_type == "PrimitiveNode":
                    return widgets[0]
                # For loaders, it's the first widget
                return widgets[0]

        # If the source is another passthrough/logic node, recurse
        # This list can be expanded with more passthrough-type nodes
        passthrough_inputs = ["model", "vae", "latent", "LATENT", "MODEL", "VAE"]
        if input_to_trace in passthrough_inputs:
            return self._trace_to_source_value(
                source_node_id,
                input_to_trace,
                target_widget_name,
                target_type,
                depth + 1,
            )

        return None

    def _trace_conditioning_source(self, start_node_id: str, conditioning_type: str, depth=0) -> str | None:
        """Improved prompt tracer. Now handles string concatenation."""
        if depth > 20:
            return None

        link = self._find_input_link(start_node_id, conditioning_type)
        if not link:
            return None

        source_node_id = str(link[1])
        source_node = self.nodes.get(source_node_id)
        if not source_node:
            return None

        node_type = source_node.get("type") or source_node.get("class_type")
        widgets = source_node.get("widgets_values", [])

        # --- Base Cases: Nodes that provide text ---
        if node_type in ["CLIPTextEncode", "CLIPTextEncodeSDXL", "T5TextEncode"]:
            # In modern formats, the text is often a linked input, not a widget
            traced_text = self._trace_to_source_value(source_node_id, "text", "text", "STRING")
            if traced_text:
                return traced_text
            return widgets[0] if widgets else None

        # --- Impact Pack text processing nodes ---
        if node_type == "ImpactWildcardProcessor":
            # This node processes wildcard text - the processed text is in widgets[1] (populate mode result)
            # widgets[0] = original text, widgets[1] = processed text
            if len(widgets) >= 2:
                return widgets[1]  # Return the processed text
            if len(widgets) >= 1:
                return widgets[0]  # Fallback to original text
            return None

        if node_type == "ImpactWildcardEncode":
            # This node encodes wildcard text into conditioning
            wildcard_text = self._trace_to_source_value(source_node_id, "wildcard", "wildcard", "STRING")
            if wildcard_text:
                return wildcard_text
            return widgets[0] if widgets else None

        if node_type == "Wildcard Prompt from String":
            # This is the source of wildcard strings
            return widgets[0] if widgets else None

        if node_type == "AutoNegativePrompt":
            # This node automatically generates negative prompts
            # The output negative prompt is usually in widgets[1]
            if len(widgets) >= 2:
                return widgets[1]  # Return the generated negative prompt
            return widgets[0] if widgets else None

        if node_type in ["DPRandomGenerator", "Dynamic Prompts Text Generator"]:
            # Dynamic prompt generators from various packs
            return widgets[0] if widgets else None

        if node_type == "String Literal":
            return widgets[0] if widgets else None

        # --- NEW: Handle string concatenation ---
        if node_type == "ConcatString":
            text_a = self._trace_to_source_value(source_node_id, "string_a", "string_a", "STRING") or ""
            text_b = self._trace_to_source_value(source_node_id, "string_b", "string_b", "STRING") or ""
            return text_a + text_b

        # --- Recursive Cases: Nodes that pass conditioning through ---
        # This list can be expanded
        passthrough_nodes = [
            "Reroute",
            "ConditioningCombine",
            "ConditioningSetArea",
            "ConditioningConcat",
            "ImpactSwitch",
            "ImpactConditionalBranch",
            "Switch any [Crystools]",
        ]
        if node_type in passthrough_nodes:
            # Find the first conditioning input and trace it
            for i in range(5):  # Check up to 5 inputs
                cond_input_name = f"conditioning_{i}" if i > 0 else "conditioning"
                traced = self._trace_conditioning_source(source_node_id, cond_input_name, depth + 1)
                if traced:
                    return traced

            # For switch nodes, also check common switch input names
            if "Switch" in node_type or "ImpactSwitch" in node_type:
                for switch_input in [
                    "input1",
                    "input2",
                    "input_a",
                    "input_b",
                    "positive",
                    "negative",
                ]:
                    traced = self._trace_conditioning_source(source_node_id, switch_input, depth + 1)
                    if traced:
                        return traced

        return None

    def _get_custom_node_types(self) -> dict[str, int]:
        """Gets a summary of all non-standard node types used."""
        standard_nodes = [
            # Add a list of default ComfyUI nodes here from a config or hardcode
            "KSampler",
            "CheckpointLoaderSimple",
            "CLIPTextEncode",
            "VAELoader",
            "VAEDecode",
            "SaveImage",
            "EmptyLatentImage",
            "Reroute",
        ]
        custom_nodes: dict[str, int] = {}
        for node in self.nodes.values():
            node_type = node.get("type") or node.get("class_type")
            if node_type and node_type not in standard_nodes:
                custom_nodes[node_type] = custom_nodes.get(node_type, 0) + 1
        return custom_nodes
