# dataset_tools/metadata_engine/extractors/comfyui_quadmoons.py

"""Extractor for ComfyUI workflows using quadMoons custom nodes."""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIQuadMoonsExtractor:
    """Extracts data from ComfyUI workflows using quadMoons nodes."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the quadMoons extractor."""
        self.logger = logger
        self.nodes = {}
        self.links = {}

    def _initialize_workflow_data(self, workflow: dict[str, Any]) -> bool:
        """Set up nodes and links for easier lookup."""
        if not workflow or "nodes" not in workflow or "links" not in workflow:
            self.logger.error("[QuadMoons] Workflow data is missing 'nodes' or 'links'.")
            return False

        self.nodes = {str(node["id"]): node for node in workflow["nodes"]}

        # Create a map for easy link lookup by target_node_id and target_input_name
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

    def extract_quadmoons_data(self, data: ContextData, fields: ExtractedFields, definition: MethodDefinition) -> None:
        """Main extraction method called by the parser definition."""
        workflow = data.get("workflow_api") or data.get("workflow")
        if not self._initialize_workflow_data(workflow):
            return

        primary_ksampler_nodes = [
            "KSampler (Efficient)",
            "KSampler Adv. (Efficient)",
            "KSampler SDXL (Eff.)",
            "KSampler - Extra Outputs", # Keep this for backward compatibility if needed
        ]
        mappings = definition.get("mappings", {})

        for node_id, node in self.nodes.items():
            if node.get("type") in primary_ksampler_nodes:
                self.logger.debug(f"[QuadMoons] Found primary KSampler node '{node.get('type')}' with ID: {node_id}")
                for field, input_name in mappings.items():
                    value = self._trace_input_value(node_id, input_name)
                    if value is not None:
                        fields[field] = value
                # Stop after finding the first matching node to avoid overwriting data
                break

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of extraction methods."""
        return {
            "quadmoons_data": self.extract_quadmoons_data,
        }

    def _trace_input_value(self, node_id: str, input_name: str) -> Any | None:
        """Recursively trace an input to its source value."""
        # Check for a direct widget value on the current node first
        node = self.nodes.get(node_id)
        if node and "widgets_values" in node:
            # Find the index of the input to match with widget_values
            input_index = -1
            for i, inp in enumerate(node.get("inputs", [])):
                if inp.get("name") == input_name:
                    input_index = i
                    break

            if input_index != -1 and input_index < len(node["widgets_values"]):
                widget_val = node["widgets_values"][input_index]
                if widget_val is not None:
                    self.logger.debug(
                        f"[QuadMoons] Found widget value for '{input_name}' in node {node_id}: {widget_val}"
                    )
                    return widget_val

        # If no widget, follow the link
        link_info = self.links.get((node_id, input_name))
        if not link_info:
            self.logger.debug(f"[QuadMoons] No link found for input '{input_name}' on node {node_id}")
            return None

        origin_id = link_info["origin_id"]
        origin_slot_idx = link_info["origin_slot"]
        origin_node = self.nodes.get(origin_id)

        if not origin_node:
            self.logger.warning(f"[QuadMoons] Origin node {origin_id} not found.")
            return None

        origin_node_type = origin_node.get("type")
        self.logger.debug(
            f"[QuadMoons] Tracing back from '{input_name}' on node {node_id} to node {origin_id} (type: {origin_node_type})"
        )

        # Get the name of the output slot we are connected to
        try:
            output_name = origin_node["outputs"][origin_slot_idx]["name"]
        except (IndexError, KeyError):
            self.logger.error(
                f"[QuadMoons] Could not determine output name for slot {origin_slot_idx} on node {origin_id}"
            )
            return None

        # If it's a bus/efficiency node, we trace back using the output name as the new input name
        if origin_node_type in [
            "KSampler - Extra Outputs",
            "Smart Negative",
            "BusNode",
            "KSampler (Efficient)",
            "KSampler Adv. (Efficient)",
            "KSampler SDXL (Eff.)",
            "Efficient Loader",
            "Eff. Loader SDXL",
            "LoRA Stacker",
            "Control Net Stacker",
            "Apply ControlNet Stack",
            "Unpack SDXL Tuple",
            "Pack SDXL Tuple",
            "Noise Control Script",
            "HighRes-Fix Script",
            "Tiled Upscaler Script",
            "LoRA Stack to String converter",
        ]:
            return self._trace_input_value(origin_id, output_name)

        # If it's a primitive or a node with a text widget, get the value
        if origin_node_type == "PrimitiveNode" or "CLIPTextEncode" in origin_node_type:
            if origin_node.get("widgets_values"):
                return origin_node["widgets_values"][0]

        # For any other node, we assume the value is in a widget corresponding to the output name
        if "widgets_values" in origin_node:
            for i, inp in enumerate(origin_node.get("inputs", [])):
                if inp.get("name") == output_name:
                    if i < len(origin_node["widgets_values"]):
                        return origin_node["widgets_values"][i]

        self.logger.debug(f"[QuadMoons] Could not resolve value for '{input_name}' on node {node_id}")
        return None
