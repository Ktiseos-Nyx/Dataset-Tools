# dataset_tools/metadata_engine/extractors/comfyui_text_combiners.py

"""ComfyUI Text Combiner Node Extractor.

Handles text combiner nodes that merge multiple text inputs:
- Text Concatenate
- String Append
- Text Join
- Other text combination nodes

These nodes are COMBINERS not SOURCES - they have no text themselves,
they combine text from multiple inputs (text_a, text_b, etc.).
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUITextCombinerExtractor:
    """Handles text combiner nodes in ComfyUI workflows."""

    # Node types that combine text from multiple sources
    TEXT_COMBINER_TYPES = {
        "Text Concatenate": {
            "delimiter_index": 0,  # widgets_values[0] is delimiter
            "default_delimiter": ", ",
            "inputs": ["text_a", "text_b", "text_c", "text_d"],
        },
        "Text Concatenate (JPS)": {
            "delimiter_index": 0,  # widgets_values[0] is delimiter
            "default_delimiter": " ",
            "inputs": ["text1", "text2", "text3", "text4"],  # JPS uses different naming!
        },
        "String Append": {
            "delimiter_index": None,  # No delimiter, just appends
            "default_delimiter": "",
            "inputs": ["text_a", "text_b"],
        },
        "Text Join": {
            "delimiter_index": 0,
            "default_delimiter": "\n",
            "inputs": ["text_1", "text_2", "text_3", "text_4"],
        },
    }

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the Text Combiner extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "text_combiner_extract_combined_text": self.extract_combined_text,
            "text_combiner_detect_workflow": self.detect_combiner_workflow,
        }

    def _get_node_data(self, data: Any) -> dict[str, Any]:
        """Helper to get the prompt data from the workflow."""
        if not isinstance(data, dict):
            return {}
        return data.get("prompt", data)

    def _is_combiner_node(self, class_type: str) -> bool:
        """Check if a node is a text combiner type."""
        return class_type in self.TEXT_COMBINER_TYPES

    def _get_combiner_config(self, class_type: str) -> dict[str, Any] | None:
        """Get configuration for a combiner node type."""
        return self.TEXT_COMBINER_TYPES.get(class_type)

    def _extract_delimiter(self, node_data: dict, config: dict) -> str:
        """Extract delimiter from node widgets or use default."""
        delimiter_index = config.get("delimiter_index")
        if delimiter_index is None:
            return config["default_delimiter"]

        widgets = node_data.get("widgets_values", [])
        if delimiter_index < len(widgets):
            return str(widgets[delimiter_index])

        return config["default_delimiter"]

    def _find_source_node_for_input(
        self, node_data: dict, input_name: str, links: list, node_lookup: dict
    ) -> dict | None:
        """Find the source node connected to a specific input."""
        inputs = node_data.get("inputs", [])

        for inp in inputs:
            if not isinstance(inp, dict):
                continue

            if inp.get("name") == input_name and "link" in inp:
                link_id = inp["link"]

                # Find the link in the links array
                for link in links:
                    if isinstance(link, list) and len(link) >= 6 and link[0] == link_id:
                        # link format: [link_id, source_node_id, source_slot, target_node_id, target_slot, type]
                        source_node_id = str(link[1])
                        return node_lookup.get(source_node_id)

        return None

    def _extract_text_from_node(self, node_data: dict, text_encoder_types: list) -> str:
        """Extract text from a text encoder node."""
        if not isinstance(node_data, dict):
            return ""

        class_type = node_data.get("class_type", "")

        # Check if this is a text encoder node
        if not any(encoder in class_type for encoder in text_encoder_types):
            return ""

        # Try widget_values first
        widget_values = node_data.get("widgets_values", [])
        if widget_values and len(widget_values) > 0:
            text_value = widget_values[0]

            # Handle nested arrays (HiDream "easy showAnything" format: [[text]])
            if isinstance(text_value, list) and len(text_value) > 0:
                text_value = text_value[0]

            return str(text_value)

        # Try inputs["text"] for smZ CLIPTextEncode and similar
        inputs = node_data.get("inputs", {})
        if isinstance(inputs, dict) and "text" in inputs:
            return str(inputs["text"])

        return ""

    def _traverse_combiner_inputs(
        self,
        node_data: dict,
        config: dict,
        links: list,
        node_lookup: dict,
        text_encoder_types: list,
        visited: set,
        max_depth: int = 10,
    ) -> list[str]:
        """Recursively traverse combiner inputs to find text sources.

        Args:
            node_data: The combiner node
            config: Configuration for this combiner type
            links: Workflow links array
            node_lookup: Dict of node_id -> node_data
            text_encoder_types: List of text encoder node types to look for
            visited: Set of visited node IDs to prevent loops
            max_depth: Maximum recursion depth

        Returns:
            List of text strings found from inputs
        """
        if max_depth <= 0:
            self.logger.warning("[TEXT COMBINER] Max depth reached, stopping traversal")
            return []

        text_parts = []
        input_names = config.get("inputs", [])

        for input_name in input_names:
            source_node = self._find_source_node_for_input(node_data, input_name, links, node_lookup)

            if source_node is None:
                continue

            source_node_id = source_node.get("id", "")
            if source_node_id in visited:
                self.logger.debug("[TEXT COMBINER] Already visited node %s, skipping", source_node_id)
                continue

            visited.add(str(source_node_id))
            source_class_type = source_node.get("class_type", "")

            # Check if source is another combiner (nested combiners)
            if self._is_combiner_node(source_class_type):
                self.logger.info("[TEXT COMBINER] Found nested combiner: %s", source_class_type)
                nested_config = self._get_combiner_config(source_class_type)

                if nested_config:
                    nested_parts = self._traverse_combiner_inputs(
                        source_node,
                        nested_config,
                        links,
                        node_lookup,
                        text_encoder_types,
                        visited.copy(),  # Use copy to allow revisiting in other branches
                        max_depth - 1,
                    )

                    if nested_parts:
                        # Combine nested parts with nested combiner's delimiter
                        nested_delimiter = self._extract_delimiter(source_node, nested_config)
                        combined_nested = nested_delimiter.join(nested_parts)
                        text_parts.append(combined_nested)
                        self.logger.info(
                            "[TEXT COMBINER] Nested combiner result from %s: %s",
                            input_name,
                            combined_nested[:50],
                        )
            else:
                # Not a combiner, try to extract text directly
                text = self._extract_text_from_node(source_node, text_encoder_types)

                if text:
                    text_parts.append(text)
                    self.logger.info(
                        "[TEXT COMBINER] Found text from %s: %s", input_name, text[:50]
                    )

        return text_parts

    def extract_combined_text(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract combined text from text combiner nodes.

        This method searches the workflow for text combiner nodes (Text Concatenate, etc.),
        recursively traverses their inputs to find source text, and combines them
        according to the combiner's configuration.

        Args:
            data: Workflow data
            method_def: Method definition from parser
            context: Extraction context
            fields: Previously extracted fields

        Returns:
            Combined text string or empty string
        """
        self.logger.debug("[TEXT COMBINER] Extracting combined text")

        prompt_data = self._get_node_data(data)
        if not prompt_data:
            return ""

        # Get text encoder types from method definition
        text_encoder_types = method_def.get("text_encoder_node_types", [
            "CLIPTextEncode",
            "BNK_CLIPTextEncodeAdvanced",
            "T5TextEncode",
            "PrimitiveStringMultiline",
            "easy positive",
        ])

        # Get workflow structure
        workflow = data if isinstance(data, dict) else {}
        links = workflow.get("links", [])

        # Build node lookup
        node_lookup = {}
        if isinstance(prompt_data, dict):
            for node_id, node_data in prompt_data.items():
                if isinstance(node_data, dict):
                    node_data["id"] = node_id  # Ensure ID is set
                    node_lookup[str(node_id)] = node_data

        # Search for combiner nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if self._is_combiner_node(class_type):
                self.logger.info("[TEXT COMBINER] Found combiner node: %s (ID: %s)", class_type, node_id)

                config = self._get_combiner_config(class_type)
                if not config:
                    continue

                # Traverse inputs to find text
                visited = set()
                text_parts = self._traverse_combiner_inputs(
                    node_data, config, links, node_lookup, text_encoder_types, visited
                )

                if text_parts:
                    # Get delimiter and combine
                    delimiter = self._extract_delimiter(node_data, config)
                    combined = delimiter.join(text_parts)

                    self.logger.info(
                        "[TEXT COMBINER] Successfully combined %d text parts: %s",
                        len(text_parts),
                        combined[:100],
                    )

                    return combined

        self.logger.debug("[TEXT COMBINER] No combiner nodes found or no text extracted")
        return ""

    def detect_combiner_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if workflow uses text combiner nodes.

        Returns:
            True if combiner nodes are detected
        """
        prompt_data = self._get_node_data(data)
        if not prompt_data:
            return False

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if self._is_combiner_node(class_type):
                self.logger.info("[TEXT COMBINER] Detected combiner workflow using: %s", class_type)
                return True

        return False
