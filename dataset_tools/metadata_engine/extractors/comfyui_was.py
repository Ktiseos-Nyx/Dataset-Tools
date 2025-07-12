# dataset_tools/metadata_engine/extractors/comfyui_was.py

"""ComfyUI WAS Node Suite ecosystem extractor.

Handles WAS Node Suite including text processing, image operations,
and utility nodes from the WAS ecosystem.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIWASExtractor:
    """Handles WAS Node Suite ecosystem."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the WAS extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "was_extract_text_processing": self._extract_text_processing,
            "was_extract_image_operations": self._extract_image_operations,
            "was_extract_utility_nodes": self._extract_utility_nodes,
            "was_extract_conditioning_nodes": self._extract_conditioning_nodes,
            "was_detect_workflow": self.detect_was_workflow,
        }

    def _extract_text_processing(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract WAS text processing node information."""
        self.logger.debug("[WAS] Extracting text processing")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        text_processing = {}

        # WAS text processing nodes
        was_text_nodes = [
            "Text Concatenate",
            "Text Replace",
            "Text Random Line",
            "Text Parse A1111",
            "Text Parse Noodle Soup Prompts",
            "Text Load Line From File",
            "Text Save To File",
            "Text String",
            "Text Multiline",
            "Text Switch",
            "Text Compare",
            "Text Contains",
            "Text List",
            "Text Random Choice",
            "Text Split",
            "Text Join",
            "Text Padding",
            "Text Uppercase",
            "Text Lowercase",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(text_node in class_type for text_node in was_text_nodes):
                widgets = node_data.get("widgets_values", [])
                text_processing[class_type] = {
                    "node_id": node_id,
                    "widgets": widgets,
                    "type": class_type,
                }

        return text_processing

    def _extract_image_operations(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract WAS image operation node information."""
        self.logger.debug("[WAS] Extracting image operations")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        image_operations = {}

        # WAS image operation nodes
        was_image_nodes = [
            "Image Resize",
            "Image Crop",
            "Image Rotate",
            "Image Flip",
            "Image Blend",
            "Image Composite",
            "Image Filter",
            "Image Convert",
            "Image Save",
            "Image Load",
            "Image Batch",
            "Image Stack",
            "Image Grid",
            "Image Nova Filter",
            "Image Film Grain",
            "Image Pixelate",
            "Image Threshold",
            "Image Levels",
            "Image Curves",
            "Image Color Correct",
            "Image Gaussian Blur",
            "Image Sharpen",
            "Image Edge Enhance",
            "Image Posterize",
            "Image Solarize",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(image_node in class_type for image_node in was_image_nodes):
                widgets = node_data.get("widgets_values", [])
                image_operations[class_type] = {
                    "node_id": node_id,
                    "widgets": widgets,
                    "type": class_type,
                }

        return image_operations

    def _extract_utility_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract WAS utility node information."""
        self.logger.debug("[WAS] Extracting utility nodes")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        utility_nodes = {}

        # WAS utility nodes
        was_utility_nodes = [
            "Number",
            "Integer",
            "Float",
            "Boolean",
            "String",
            "Number Operation",
            "Number Compare",
            "Number Switch",
            "Logic Boolean",
            "Logic Compare",
            "Logic Switch",
            "Seed",
            "Random Number",
            "Random Choice",
            "Dictionary",
            "List",
            "Tuple",
            "CLIPSeg",
            "Mask",
            "Mask Crop",
            "Mask Expand",
            "Mask Threshold",
            "Mask Blur",
            "Mask Erode",
            "Mask Dilate",
            "Console Debug",
            "Note",
            "Any Switch",
            "Any Type",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(utility_node in class_type for utility_node in was_utility_nodes):
                widgets = node_data.get("widgets_values", [])
                utility_nodes[class_type] = {
                    "node_id": node_id,
                    "widgets": widgets,
                    "type": class_type,
                }

        return utility_nodes

    def _extract_conditioning_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract WAS conditioning node information."""
        self.logger.debug("[WAS] Extracting conditioning nodes")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        conditioning_nodes = {}

        # WAS conditioning nodes
        was_conditioning_nodes = [
            "Conditioning Set Area",
            "Conditioning Set Mask",
            "Conditioning Combine",
            "Conditioning Average",
            "Conditioning Concat",
            "Conditioning Set Timestep Range",
            "CLIP Text Encode",
            "CLIP Text Encode Advanced",
            "CLIP Vision Encode",
            "CLIP Interrogate",
            "Style Prompt",
            "Prompt Styler",
            "Prompt Switch",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(cond_node in class_type for cond_node in was_conditioning_nodes):
                widgets = node_data.get("widgets_values", [])
                conditioning_nodes[class_type] = {
                    "node_id": node_id,
                    "widgets": widgets,
                    "type": class_type,
                }

        return conditioning_nodes

    def detect_was_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this workflow uses WAS Node Suite."""
        if not isinstance(data, dict):
            return False

        prompt_data = data.get("prompt", data)

        # Look for WAS Node Suite indicators
        was_indicators = [
            "WAS_",
            "Text ",
            "Image ",
            "Number",
            "Logic",
            "Mask",
            "CLIPSeg",
            "Console Debug",
            "Note",
            "Any Switch",
            "Random",
            "Dictionary",
            "List",
            "Tuple",
            "Boolean",
            "Style Prompt",
            "Prompt Styler",
        ]

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if any(indicator in class_type for indicator in was_indicators):
                return True

        # Also check properties for WAS cnr_id
        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            properties = node_data.get("properties", {})
            if isinstance(properties, dict):
                cnr_id = properties.get("cnr_id", "")
                if "was" in cnr_id.lower():
                    return True

        return False

    def extract_was_workflow_summary(self, data: dict) -> dict[str, Any]:
        """Extract comprehensive WAS Node Suite workflow summary."""
        if not isinstance(data, dict):
            return {}

        summary = {
            "is_was_workflow": self.detect_was_workflow(data, {}, {}, {}),
            "text_processing": self._extract_text_processing(data, {}, {}, {}),
            "image_operations": self._extract_image_operations(data, {}, {}, {}),
            "utility_nodes": self._extract_utility_nodes(data, {}, {}, {}),
            "conditioning_nodes": self._extract_conditioning_nodes(data, {}, {}, {}),
        }

        return summary

    def get_was_nodes(self, data: dict) -> dict[str, dict]:
        """Get all WAS Node Suite nodes in the workflow."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        was_nodes = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # Check if it's a WAS node
            if self._is_was_node(class_type):
                was_nodes[node_id] = {
                    "type": class_type,
                    "widgets": node_data.get("widgets_values", []),
                    "inputs": node_data.get("inputs", {}),
                    "outputs": node_data.get("outputs", []),
                }

        return was_nodes

    def _is_was_node(self, class_type: str) -> bool:
        """Check if a class type is a WAS node."""
        was_node_prefixes = [
            "WAS_",
            "Text ",
            "Image ",
            "Number",
            "Logic",
            "Mask",
            "CLIPSeg",
            "Console Debug",
            "Note",
            "Any Switch",
            "Random",
            "Dictionary",
            "List",
            "Tuple",
            "Boolean",
            "Style Prompt",
            "Prompt Styler",
            "Seed",
            "Float",
            "Integer",
            "String",
        ]

        return any(prefix in class_type for prefix in was_node_prefixes)

    def extract_was_text_content(self, data: dict) -> list[str]:
        """Extract all text content from WAS text nodes."""
        if not isinstance(data, dict):
            return []

        prompt_data = data.get("prompt", data)
        text_content = []

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # Check for WAS text nodes
            if ("Text " in class_type or "WAS_" in class_type) and any(
                text_type in class_type
                for text_type in [
                    "String",
                    "Multiline",
                    "Concatenate",
                    "Replace",
                    "Random Line",
                    "Parse",
                    "Load Line",
                    "Save",
                ]
            ):
                widgets = node_data.get("widgets_values", [])
                for widget in widgets:
                    if isinstance(widget, str) and len(widget.strip()) > 0:
                        text_content.append(widget.strip())

        return text_content
