# dataset_tools/metadata_engine/extractors/comfyui_traversal.py

"""ComfyUI workflow traversal methods.

Handles node traversal, link following, and workflow analysis.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUITraversalExtractor:
    """Handles ComfyUI workflow traversal and link following."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the traversal extractor."""
        self.logger = logger

    def get_node_by_id(self, nodes: dict | list, node_id: str) -> dict | None:
        """Helper method to get a node by its ID from nodes dict or list."""
        if isinstance(nodes, dict):
            return nodes.get(str(node_id))
        if isinstance(nodes, list):
            try:
                idx = int(node_id)
                if 0 <= idx < len(nodes):
                    return nodes[idx]
            except (ValueError, IndexError):
                pass
        return None

    def get_nodes_from_data(self, data: dict) -> dict | list:
        """Helper method to extract nodes from data, handling both prompt and workflow formats."""
        if isinstance(data, dict) and "nodes" in data:
            # Workflow format: {"nodes": [...]}
            return data["nodes"]
        if isinstance(data, dict) and "prompt" in data:
            # API format: {"prompt": {"1": {...}, "2": {...}, ...}}
            return data["prompt"]
        if isinstance(data, dict) and all(isinstance(v, dict) for v in data.values()):
            # Prompt format: {"1": {...}, "2": {...}, ...}
            return data
        return {}

    def follow_input_link(self, nodes: dict | list, node_id: str, input_name: str) -> tuple[str, str] | None:
        """Follow an input link to find the source node and output slot.
        
        Args:
            nodes: The nodes dictionary or list
            node_id: ID of the node to check
            input_name: Name of the input to follow
            
        Returns:
            Tuple of (source_node_id, output_slot_name) or None if not found
        """
        node = self.get_node_by_id(nodes, node_id)
        if not node:
            return None
            
        # Check inputs for the specified input_name
        inputs = node.get("inputs", [])
        if isinstance(inputs, list):
            # Workflow format: inputs is a list of dicts
            for input_info in inputs:
                if isinstance(input_info, dict) and input_info.get("name") == input_name:
                    link_id = input_info.get("link")
                    if link_id is not None:
                        # Find the source node that has this link in its outputs
                        return self.find_node_by_output_link(nodes, link_id)
        elif isinstance(inputs, dict):
            # Prompt format: inputs is a dict
            if input_name in inputs:
                input_info = inputs[input_name]
                if isinstance(input_info, list) and len(input_info) >= 2:
                    # Format: [source_node_id, output_slot_index]
                    source_node_id = str(input_info[0])
                    output_slot_index = input_info[1]
                    source_node = self.get_node_by_id(nodes, source_node_id)
                    if source_node:
                        # Get the output slot name by index
                        outputs = source_node.get("outputs", [])
                        if isinstance(outputs, list) and output_slot_index < len(outputs):
                            output_slot_name = outputs[output_slot_index].get("name", "")
                            return (source_node_id, output_slot_name)
        
        return None

    def find_node_by_output_link(self, nodes: dict | list, link_id: int) -> tuple[str, str] | None:
        """Find a node that has the specified link_id in its outputs.
        
        Args:
            nodes: The nodes dictionary or list
            link_id: The link ID to search for
            
        Returns:
            Tuple of (node_id, output_slot_name) or None if not found
        """
        if isinstance(nodes, dict):
            node_items = nodes.items()
        else:
            node_items = enumerate(nodes)
            
        for node_id, node_data in node_items:
            if not isinstance(node_data, dict):
                continue
                
            outputs = node_data.get("outputs", [])
            if isinstance(outputs, list):
                for output_info in outputs:
                    if isinstance(output_info, dict):
                        links = output_info.get("links", [])
                        if isinstance(links, list) and link_id in links:
                            return (str(node_id), output_info.get("name", ""))
        
        return None

    def trace_text_flow(self, nodes: dict | list, start_node_id: str) -> str:
        """Trace text flow from a node backwards through the workflow.
        
        Args:
            nodes: The nodes dictionary or list
            start_node_id: ID of the node to start tracing from
            
        Returns:
            The traced text content or empty string if not found
        """
        visited = set()
        
        def trace_recursive(node_id: str, depth: int = 0) -> str:
            if depth > 20 or node_id in visited:  # Prevent infinite loops
                return ""
                
            visited.add(node_id)
            node = self.get_node_by_id(nodes, node_id)
            if not node:
                return ""
                
            node_type = node.get("class_type", node.get("type", ""))

            # Base Case: If this node is a primitive string holder, return its value.
            # This is the ultimate source of the text.
            if "Primitive" in node_type and node.get("widgets_values"):
                return node["widgets_values"][0]

            # Recursive Step: Check known text-processing or text-holding nodes.
            # The order matters: check for specific processors before generic text nodes.
            
            # For nodes that process text (like wildcards), we need to trace their INPUTS.
            if "WildcardProcessor" in node_type or "PowerPrompt" in node_type:
                # Try to trace common input names for these processor nodes.
                for input_name in ["text", "prompt", "wildcard_text"]:
                    link_info = self.follow_input_link(nodes, node_id, input_name)
                    if link_info:
                        source_node_id, _ = link_info
                        return trace_recursive(source_node_id, depth + 1)

            # For text encoders, trace their "text" input link.
            if "CLIPTextEncode" in node_type:
                link_info = self.follow_input_link(nodes, node_id, "text")
                if link_info:
                    source_node_id, _ = link_info
                    return trace_recursive(source_node_id, depth + 1)
            
            # Fallback/Default Case: If no link is followed, the node itself might hold the text.
            # This applies to simple text nodes or processors where the input is a direct widget.
            inputs = node.get("inputs", {})
            if isinstance(inputs, dict) and "text" in inputs:
                text_value = inputs["text"]
                if isinstance(text_value, str):
                    return text_value

            widgets = node.get("widgets_values", [])
            if widgets and isinstance(widgets[0], str):
                return widgets[0]
            
            return ""
        
        return trace_recursive(start_node_id)

    def find_connected_nodes(self, nodes: dict | list, start_node_id: str, connection_type: str = "input") -> list[str]:
        """Find all nodes connected to a given node.
        
        Args:
            nodes: The nodes dictionary or list
            start_node_id: ID of the node to start from
            connection_type: "input" or "output" connections
            
        Returns:
            List of connected node IDs
        """
        connected = []
        start_node = self.get_node_by_id(nodes, start_node_id)
        if not start_node:
            return connected
            
        if connection_type == "input":
            inputs = start_node.get("inputs", [])
            if isinstance(inputs, list):
                for input_info in inputs:
                    if isinstance(input_info, dict):
                        link_id = input_info.get("link")
                        if link_id is not None:
                            result = self.find_node_by_output_link(nodes, link_id)
                            if result:
                                connected.append(result[0])
            elif isinstance(inputs, dict):
                for input_info in inputs.values():
                    if isinstance(input_info, list) and len(input_info) >= 1:
                        connected.append(str(input_info[0]))
        
        elif connection_type == "output":
            outputs = start_node.get("outputs", [])
            if isinstance(outputs, list):
                for output_info in outputs:
                    if isinstance(output_info, dict):
                        links = output_info.get("links", [])
                        if isinstance(links, list):
                            for link_id in links:
                                # Find nodes that have this link in their inputs
                                target_nodes = self.find_nodes_with_input_link(nodes, link_id)
                                connected.extend(target_nodes)
        
        return connected

    def find_nodes_with_input_link(self, nodes: dict | list, link_id: int) -> list[str]:
        """Find all nodes that have the specified link_id in their inputs."""
        result = []
        if isinstance(nodes, dict):
            node_items = nodes.items()
        else:
            node_items = enumerate(nodes)
            
        for node_id, node_data in node_items:
            if not isinstance(node_data, dict):
                continue
                
            inputs = node_data.get("inputs", [])
            if isinstance(inputs, list):
                for input_info in inputs:
                    if isinstance(input_info, dict) and input_info.get("link") == link_id:
                        result.append(str(node_id))
        
        return result