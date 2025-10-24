# dataset_tools/metadata_engine/extractors/comfyui_pixart_extractor.py

"""Extractor for ComfyUI workflows using PixArt nodes."""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIPixArtExtractor:
    """Extracts data from ComfyUI workflows using PixArt nodes."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the PixArt extractor."""
        self.logger = logger
        self.nodes = {}
        self.links = {}

    def _initialize_workflow_data(self, workflow: dict[str, Any]) -> bool:
        """Set up nodes and links for easier lookup."""
        if not workflow or "nodes" not in workflow or "links" not in workflow:
            self.logger.error("[PixArt] Workflow data is missing 'nodes' or 'links'.")
            return False

        self.nodes = {str(node["id"]): node for node in workflow["nodes"]}

        self.links = {}
        for link_details in workflow["links"]:
            target_id = str(link_details[3])
            target_input_idx = link_details[4]

            target_node = self.nodes.get(target_id)
            if target_node and target_input_idx < len(target_node.get("inputs", [])):
                target_input_name = target_node["inputs"][target_input_idx]["name"]
                key = (target_id, target_input_name)
                self.links[key] = {
                    "origin_id": str(link_details[1]),
                    "origin_slot": link_details[2],
                }
        return True

    def extract_pixart_data(self, data: ContextData, fields: ExtractedFields, definition: MethodDefinition) -> None:
        """Main extraction method for PixArt workflows."""
        workflow = data.get("workflow_api") or data.get("workflow")
        if not self._initialize_workflow_data(workflow):
            return

        target_node_type = definition.get("target_node_type", "KSampler")
        mappings = definition.get("mappings", {})

        for node_id, node in self.nodes.items():
            if node.get("type") == target_node_type:
                self.logger.debug("[PixArt] Found target node '%s' with ID: %s", target_node_type, node_id)
                for field, input_name in mappings.items():
                    value = self._trace_input_value(node_id, input_name)
                    if value is not None:
                        fields[field] = value
                break

    def _trace_input_value(self, node_id: str, input_name: str) -> Any | None:
        """Recursively trace an input to its source value."""
        node = self.nodes.get(node_id)
        if node and "widgets_values" in node:
            input_index = -1
            for i, inp in enumerate(node.get("inputs", [])):
                if inp.get("name") == input_name:
                    input_index = i
                    break

            if input_index != -1 and input_index < len(node["widgets_values"]):
                widget_val = node["widgets_values"][input_index]
                if widget_val is not None:
                    self.logger.debug("[PixArt] Found widget value for '%s' in node %s: %s", input_name, node_id, widget_val)
                    return widget_val

        link_info = self.links.get((node_id, input_name))
        if not link_info:
            self.logger.debug("[PixArt] No link found for input '%s' on node %s", input_name, node_id)
            return None

        origin_id = link_info["origin_id"]
        origin_slot_idx = link_info["origin_slot"]
        origin_node = self.nodes.get(origin_id)

        if not origin_node:
            self.logger.warning("[PixArt] Origin node %s not found.", origin_id)
            return None

        origin_node_type = origin_node.get("type")
        self.logger.debug(
            "[PixArt] Tracing back from '%s' on node %s to node %s (type: %s)", input_name, node_id, origin_id, origin_node_type
        )

        if "PixArtT5TextEncode" in origin_node_type:
            if origin_node.get("widgets_values"):
                return origin_node["widgets_values"][0]

        if "PixArtCheckpointLoader" in origin_node_type:
            if origin_node.get("widgets_values"):
                return origin_node["widgets_values"][0]

        try:
            output_name = origin_node["outputs"][origin_slot_idx]["name"]
        except (IndexError, KeyError):
            self.logger.error(
                "[PixArt] Could not determine output name for slot %s on node %s", origin_slot_idx, origin_id
            )
            return None

        return self._trace_input_value(origin_id, output_name)
