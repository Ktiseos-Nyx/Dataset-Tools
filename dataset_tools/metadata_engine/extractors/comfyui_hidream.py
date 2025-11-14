# dataset_tools/metadata_engine/extractors/comfyui_hidream.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""
Specialized extractor for HiDream ComfyUI workflows.

HiDream workflows use:
- DPRandomGenerator nodes for dynamic prompt generation
- ConcatStringSingle nodes to combine multiple DPRandomGenerator outputs
- ConDelta conditioning mathematics (ConditioningSubtract, ConditioningAddConDelta)
- CFGless negative prompts
"""

import json
from typing import Any

from dataset_tools.logger import get_logger

logger = get_logger(__name__)


class ComfyUIHiDreamExtractor:
    """Specialized extractor for HiDream workflow patterns."""

    def __init__(self, parent_logger):
        """Initialize the HiDream extractor."""
        self.logger = parent_logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "hidream_extract_concatenated_prompt": self.extract_concatenated_prompt,
            "hidream_extract_dprandom_prompts": self.extract_dprandom_prompts,
        }

    def _parse_json_data(self, data: Any) -> Any:
        """Helper to parse JSON string data if needed."""
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return data

    def _get_nodes_from_workflow(self, workflow: dict) -> dict:
        """Extract nodes from workflow data (handles both workflow and prompt formats).

        Creates a converted copy of workflow format nodes without modifying the original.
        """
        if not isinstance(workflow, dict):
            return {}

        # Handle workflow format with nodes array
        if "nodes" in workflow and isinstance(workflow["nodes"], list):
            # First, build a link ID -> (source_node, output_index) mapping
            links_map = {}
            if "links" in workflow and isinstance(workflow["links"], list):
                for link in workflow["links"]:
                    # Link format: [link_id, source_node_id, source_output_idx, target_node_id, target_input_idx, type]
                    if isinstance(link, list) and len(link) >= 3:
                        link_id = link[0]
                        source_node_id = str(link[1])
                        output_index = link[2]
                        links_map[link_id] = [source_node_id, output_index]

            nodes_dict = {}
            for i, node in enumerate(workflow["nodes"]):
                node_id = str(node.get("id", i))

                # Create a COPY of the node to avoid modifying the original
                node_copy = {}

                # Convert workflow format to API format for consistency
                # Workflow uses 'type', API uses 'class_type'
                if "type" in node:
                    node_copy["class_type"] = node["type"]
                elif "class_type" in node:
                    node_copy["class_type"] = node["class_type"]

                # Convert workflow format inputs array to API format dict
                # Workflow: 'inputs': [{'name': 'string_a', 'link': 791}, ...]
                # API: 'inputs': {'string_a': [node_id, output_index], ...}
                if "inputs" in node and isinstance(node["inputs"], list):
                    inputs_dict = {}
                    for input_def in node["inputs"]:
                        if isinstance(input_def, dict) and "name" in input_def:
                            input_name = input_def["name"]
                            # If there's a link, resolve it using the links map
                            if "link" in input_def and input_def["link"] in links_map:
                                inputs_dict[input_name] = links_map[input_def["link"]]
                            # Otherwise check for direct value
                            elif "value" in input_def:
                                inputs_dict[input_name] = input_def["value"]
                    node_copy["inputs"] = inputs_dict
                elif "inputs" in node:
                    # Already in dict format, copy it
                    node_copy["inputs"] = node["inputs"]

                # Copy widgets_values if present
                if "widgets_values" in node:
                    node_copy["widgets_values"] = node["widgets_values"]

                nodes_dict[node_id] = node_copy
            return nodes_dict

        # Handle prompt format (API format) where nodes are keyed by ID
        # Check if it looks like API format (has class_type fields)
        sample_keys = list(workflow.keys())[:5]
        if sample_keys and all(
            isinstance(workflow.get(k), dict) and "class_type" in workflow.get(k, {})
            for k in sample_keys
        ):
            return workflow

        return {}

    def _get_nodes_from_prompt_data(self, prompt_data: dict) -> dict:
        """Extract nodes from prompt data (API format)."""
        if not isinstance(prompt_data, dict):
            return {}

        # Prompt data is already node_id -> node_data format
        return prompt_data

    def _find_node_by_id(self, node_id: str, nodes: dict) -> dict | None:
        """Find a node by its ID."""
        return nodes.get(str(node_id))

    def _traverse_concat_single(self, node_id: str, nodes: dict, visited: set) -> list[str]:
        """Recursively traverse ConcatStringSingle nodes to collect all text parts.

        Args:
            node_id: The ID of the ConcatStringSingle node to traverse
            nodes: Dictionary of all nodes
            visited: Set of already visited node IDs to prevent cycles

        Returns:
            List of text strings found by traversing the concat tree
        """
        if node_id in visited:
            return []

        visited.add(node_id)
        node = self._find_node_by_id(node_id, nodes)

        if not node:
            return []

        class_type = node.get("class_type", "")

        # If this is a ConcatStringSingle, traverse its inputs
        if class_type == "ConcatStringSingle":
            self.logger.info("[HiDream] Traversing ConcatStringSingle node %s", node_id)
            self.logger.info("[HiDream]   Node structure: %s", node)
            text_parts = []
            inputs = node.get("inputs", {})
            self.logger.info("[HiDream]   Inputs dict: %s", inputs)

            # ConcatStringSingle has string_a and string_b inputs
            for input_key in ["string_a", "string_b"]:
                if input_key in inputs:
                    input_value = inputs[input_key]
                    self.logger.info("[HiDream]   %s = %s", input_key, input_value)

                    # Check if it's a link to another node [node_id, output_index]
                    if isinstance(input_value, list) and len(input_value) >= 2:
                        source_node_id = str(input_value[0])
                        self.logger.info("[HiDream]   Following link to node %s", source_node_id)
                        # Recursively traverse the source node
                        sub_parts = self._traverse_concat_single(source_node_id, nodes, visited.copy())
                        if sub_parts:
                            self.logger.info("[HiDream]   Got %s parts from %s", len(sub_parts), input_key)
                            text_parts.extend(sub_parts)
                        else:
                            self.logger.warning("[HiDream]   No parts found from %s node %s", input_key, source_node_id)

                    # Check if it's a direct string value
                    elif isinstance(input_value, str) and input_value.strip():
                        text_parts.append(input_value)

            return text_parts

        # If this is a DPRandomGenerator, extract its prompt template
        if class_type == "DPRandomGenerator":
            self.logger.info("[HiDream] Found DPRandomGenerator node %s", node_id)

            # Check inputs.text first (API format)
            inputs = node.get("inputs", {})
            if isinstance(inputs, dict) and "text" in inputs:
                text = inputs["text"]
                if isinstance(text, str) and text.strip():
                    # Skip placeholder text
                    if text not in ["chibi anime style", ""]:
                        self.logger.info("[HiDream] Extracted from DPRandomGenerator inputs: %s...", text[:100])
                        return [text]

            # Check widgets_values (workflow format)
            widgets_values = node.get("widgets_values", [])
            if widgets_values and len(widgets_values) > 0:
                text = widgets_values[0]
                if isinstance(text, str) and text.strip():
                    # Skip placeholder text
                    if text not in ["chibi anime style", ""]:
                        self.logger.info("[HiDream] Extracted from DPRandomGenerator widgets: %s...", text[:100])
                        return [text]

        # For any other node type, return empty
        return []

    def extract_concatenated_prompt(
        self,
        data: Any,
        method_def: dict,
        context: dict,
        fields: dict,
    ) -> str:
        """Extract prompts from ConcatStringSingle + DPRandomGenerator workflows.

        This method handles HiDream's complex prompt architecture:
        1. Finds ConcatStringSingle nodes
        2. Recursively traverses their inputs to find DPRandomGenerator sources
        3. Combines all found prompt templates

        Args:
            data: Workflow or prompt data
            method_def: Method definition from parser
            context: Context data
            fields: Extracted fields

        Returns:
            Combined prompt string from all DPRandomGenerator nodes
        """
        workflow = self._parse_json_data(data)

        # Try to get nodes from workflow format first
        nodes = self._get_nodes_from_workflow(workflow)

        # If that didn't work, try prompt data format
        if not nodes:
            nodes = self._get_nodes_from_prompt_data(workflow)

        if not nodes:
            self.logger.warning("[HiDream] No nodes found in workflow data")
            return ""

        # Debug: Log all node types to understand the workflow structure
        self.logger.info("[HiDream] Found %s nodes total", len(nodes))
        node_types = {}
        for nid, ndata in nodes.items():
            if isinstance(ndata, dict):
                ctype = ndata.get("class_type", "unknown")
                if ctype not in node_types:
                    node_types[ctype] = []
                node_types[ctype].append(nid)
        self.logger.info("[HiDream] Node types in workflow: %s", node_types)

        # Find ConcatStringSingle nodes
        concat_nodes = []
        for node_id, node_data in nodes.items():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "")
                if class_type == "ConcatStringSingle":
                    concat_nodes.append(node_id)

        if not concat_nodes:
            self.logger.info("[HiDream] No ConcatStringSingle nodes found, trying direct DPRandomGenerator")
            # Fallback: look for DPRandomGenerator directly
            for node_id, node_data in nodes.items():
                if isinstance(node_data, dict):
                    class_type = node_data.get("class_type", "")
                    if class_type == "DPRandomGenerator":
                        parts = self._traverse_concat_single(node_id, nodes, set())
                        if parts:
                            combined = " ".join(parts)
                            self.logger.info("[HiDream] Direct DPRandomGenerator result: %s...", combined[:100])
                            return combined
            return ""

        # Traverse the first ConcatStringSingle node we find
        # (usually there's only one that combines all the prompt parts)
        concat_node_id = concat_nodes[0]
        self.logger.info("[HiDream] Starting traversal from ConcatStringSingle node %s", concat_node_id)

        text_parts = self._traverse_concat_single(concat_node_id, nodes, set())

        if text_parts:
            # Combine all parts with a space
            combined = " ".join(text_parts)
            self.logger.info("[HiDream] Successfully extracted combined prompt (%s parts): %s...", len(text_parts), combined[:150])
            return combined

        self.logger.warning("[HiDream] No text parts found in ConcatStringSingle traversal")
        return ""

    def extract_dprandom_prompts(
        self,
        data: Any,
        method_def: dict,
        context: dict,
        fields: dict,
    ) -> dict:
        """Extract all DPRandomGenerator prompts as a dictionary.

        Returns:
            Dictionary with keys for each DPRandomGenerator found
        """
        workflow = self._parse_json_data(data)
        nodes = self._get_nodes_from_workflow(workflow)

        if not nodes:
            nodes = self._get_nodes_from_prompt_data(workflow)

        if not nodes:
            return {}

        prompts = {}
        for node_id, node_data in nodes.items():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "")
                if class_type == "DPRandomGenerator":
                    # Try to get title/label
                    meta = node_data.get("_meta", {})
                    title = meta.get("title", f"DPRandom_{node_id}")

                    # Extract text
                    inputs = node_data.get("inputs", {})
                    if isinstance(inputs, dict) and "text" in inputs:
                        text = inputs["text"]
                        if isinstance(text, str) and text.strip():
                            prompts[title] = text[:200]  # Limit length for display

                    widgets_values = node_data.get("widgets_values", [])
                    if widgets_values and len(widgets_values) > 0:
                        text = widgets_values[0]
                        if isinstance(text, str) and text.strip():
                            prompts[title] = text[:200]

        return prompts
