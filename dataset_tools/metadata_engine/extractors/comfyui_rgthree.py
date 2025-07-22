# dataset_tools/metadata_engine/extractors/comfyui_rgthree.py

"""ComfyUI RGthree ecosystem extractor.

Handles RGthree nodes including context nodes, reroute nodes,
power prompts, and workflow optimization utilities.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIRGthreeExtractor:
    """Handles RGthree ecosystem nodes."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the RGthree extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "rgthree_extract_context_nodes": self._extract_context_nodes,
            "rgthree_extract_power_prompts": self._extract_power_prompts,
            "rgthree_extract_reroute_nodes": self._extract_reroute_nodes,
            "rgthree_extract_utility_nodes": self._extract_utility_nodes,
            "rgthree_extract_workflow_nodes": self._extract_workflow_nodes,
            "rgthree_detect_workflow": self.detect_rgthree_workflow,
        }

    def _extract_context_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract RGthree context nodes."""
        self.logger.debug("[RGthree] Extracting context nodes")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        context_nodes = {}

        # RGthree context nodes
        rgthree_context_nodes = [
            "Context",
            "Context Switch",
            "Context Merge",
            "Context Big",
            "Context Switch Big",
            "Context Merge Big",
            "SDXL Context",
            "SDXL Context Big",
            "SDXL Context Switch",
            "Fast Groups Bypasser",
            "Fast Groups Muter",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(context_node in class_type for context_node in rgthree_context_nodes):
                widgets = node_data.get("widgets_values", [])
                context_nodes[node_id] = {
                    "type": class_type,
                    "widgets": widgets,
                    "node_id": node_id,
                }

                # Parse context parameters
                if "Context" in class_type:
                    context_nodes[f"{node_id}_parsed"] = self._parse_context_params(widgets)

        return context_nodes

    def _extract_power_prompts(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract RGthree power prompt nodes."""
        self.logger.debug("[RGthree] Extracting power prompts")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        power_prompts = {}

        # RGthree power prompt nodes
        rgthree_prompt_nodes = [
            "Power Prompt",
            "Power Prompt Simple",
            "Power Prompt Advanced",
            "Prompt Combiner",
            "Prompt Combiner +",
            "Prompt Combiner ++",
            "Power Lora Loader",
            "Power Lora Loader Simple",
            "Power Lora Loader Advanced",
            "Power Lora Stack",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(prompt_node in class_type for prompt_node in rgthree_prompt_nodes):
                widgets = node_data.get("widgets_values", [])
                power_prompts[node_id] = {
                    "type": class_type,
                    "widgets": widgets,
                    "node_id": node_id,
                }

                # Extract prompt text
                for i, widget in enumerate(widgets):
                    if isinstance(widget, str) and len(widget.strip()) > 0:
                        power_prompts[f"{node_id}_text_{i}"] = widget.strip()

        return power_prompts

    def _extract_reroute_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract RGthree reroute nodes."""
        self.logger.debug("[RGthree] Extracting reroute nodes")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        reroute_nodes = {}

        # RGthree reroute nodes
        rgthree_reroute_nodes = [
            "Reroute",
            "Reroute Resizer",
            "Reroute Big",
            "Any Switch",
            "Any Switch Big",
            "Any Switch ++",
            "String Switch",
            "Integer Switch",
            "Float Switch",
            "Boolean Switch",
            "Latent Switch",
            "Image Switch",
            "Conditioning Switch",
            "Model Switch",
            "VAE Switch",
            "CLIP Switch",
            "ControlNet Switch",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(reroute_node in class_type for reroute_node in rgthree_reroute_nodes):
                widgets = node_data.get("widgets_values", [])
                reroute_nodes[node_id] = {
                    "type": class_type,
                    "widgets": widgets,
                    "node_id": node_id,
                }

        return reroute_nodes

    def _extract_utility_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract RGthree utility nodes."""
        self.logger.debug("[RGthree] Extracting utility nodes")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        utility_nodes = {}

        # RGthree utility nodes
        rgthree_utility_nodes = [
            "Bookmark",
            "Config File",
            "Display Text",
            "Display Int",
            "Display Float",
            "Display Boolean",
            "Display Latent",
            "Display Image",
            "Display Any",
            "Random Unmuter",
            "Random Bypasser",
            "Random Bool",
            "Random Int",
            "Random Float",
            "Random String",
            "Seed",
            "Seed ++",
            "Seed O' Plenty",
            "Image Comparer",
            "Image Comparer Simple",
            "Image Saver",
            "Image Saver Simple",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(utility_node in class_type for utility_node in rgthree_utility_nodes):
                widgets = node_data.get("widgets_values", [])
                utility_nodes[node_id] = {
                    "type": class_type,
                    "widgets": widgets,
                    "node_id": node_id,
                }

        return utility_nodes

    def _extract_workflow_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract RGthree workflow management nodes."""
        self.logger.debug("[RGthree] Extracting workflow nodes")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        workflow_nodes = {}

        # RGthree workflow nodes
        rgthree_workflow_nodes = [
            "Queue",
            "Queue Simple",
            "Queue Advanced",
            "Workflow",
            "Workflow Simple",
            "Workflow Advanced",
            "Checkpoint",
            "Checkpoint Simple",
            "Checkpoint Advanced",
            "Progress",
            "Progress Simple",
            "Progress Advanced",
            "Timer",
            "Timer Simple",
            "Timer Advanced",
            "Logger",
            "Logger Simple",
            "Logger Advanced",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(workflow_node in class_type for workflow_node in rgthree_workflow_nodes):
                widgets = node_data.get("widgets_values", [])
                workflow_nodes[node_id] = {
                    "type": class_type,
                    "widgets": widgets,
                    "node_id": node_id,
                }

        return workflow_nodes

    def detect_rgthree_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this workflow uses RGthree nodes."""
        if not isinstance(data, dict):
            return False

        prompt_data = data.get("prompt", data)

        # Look for RGthree indicators
        rgthree_indicators = [
            "Context",
            "Power Prompt",
            "Reroute",
            "Switch",
            "Bookmark",
            "Display",
            "Random",
            "Seed",
            "Config",
            "Image Comparer",
            "Image Saver",
            "Queue",
            "Workflow",
            "Checkpoint",
            "Progress",
            "Timer",
            "Logger",
            "Bypasser",
            "Muter",
            "Combiner",
            "Lora Stack",
        ]

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if any(indicator in class_type for indicator in rgthree_indicators):
                return True

        # Also check properties for RGthree cnr_id
        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            properties = node_data.get("properties", {})
            if isinstance(properties, dict):
                cnr_id = properties.get("cnr_id", "")
                if "rgthree" in cnr_id.lower():
                    return True

        return False

    def _parse_context_params(self, widgets: list) -> dict[str, Any]:
        """Parse context parameters from widgets."""
        if not widgets:
            return {}

        context_params = {}

        # Common context widget structure (approximate)
        param_mapping = {
            0: "model",
            1: "clip",
            2: "vae",
            3: "positive",
            4: "negative",
            5: "latent",
            6: "seed",
            7: "steps",
            8: "cfg",
            9: "sampler_name",
            10: "scheduler",
            11: "denoise",
        }

        for i, param_name in param_mapping.items():
            if i < len(widgets):
                context_params[param_name] = widgets[i]

        return context_params

    def extract_rgthree_workflow_summary(self, data: dict) -> dict[str, Any]:
        """Extract comprehensive RGthree workflow summary."""
        if not isinstance(data, dict):
            return {}

        summary = {
            "is_rgthree_workflow": self.detect_rgthree_workflow(data, {}, {}, {}),
            "context_nodes": self._extract_context_nodes(data, {}, {}, {}),
            "power_prompts": self._extract_power_prompts(data, {}, {}, {}),
            "reroute_nodes": self._extract_reroute_nodes(data, {}, {}, {}),
            "utility_nodes": self._extract_utility_nodes(data, {}, {}, {}),
            "workflow_nodes": self._extract_workflow_nodes(data, {}, {}, {}),
        }

        return summary

    def get_rgthree_nodes(self, data: dict) -> dict[str, dict]:
        """Get all RGthree nodes in the workflow."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        rgthree_nodes = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if self._is_rgthree_node(class_type):
                rgthree_nodes[node_id] = {
                    "type": class_type,
                    "widgets": node_data.get("widgets_values", []),
                    "inputs": node_data.get("inputs", {}),
                    "outputs": node_data.get("outputs", []),
                }

        return rgthree_nodes

    def _is_rgthree_node(self, class_type: str) -> bool:
        """Check if a class type is an RGthree node."""
        rgthree_indicators = [
            "Context",
            "Power Prompt",
            "Reroute",
            "Switch",
            "Bookmark",
            "Display",
            "Random",
            "Seed",
            "Config",
            "Image Comparer",
            "Image Saver",
            "Queue",
            "Workflow",
            "Checkpoint",
            "Progress",
            "Timer",
            "Logger",
            "Bypasser",
            "Muter",
            "Combiner",
            "Lora Stack",
            "Power Lora",
            "Fast Groups",
            "String Switch",
            "Integer Switch",
            "Float Switch",
            "Boolean Switch",
        ]

        return any(indicator in class_type for indicator in rgthree_indicators)

    def extract_rgthree_prompts(self, data: dict) -> dict[str, str]:
        """Extract all prompts from RGthree nodes."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        prompts = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if self._is_rgthree_node(class_type) and "Prompt" in class_type:
                widgets = node_data.get("widgets_values", [])
                for i, widget in enumerate(widgets):
                    if isinstance(widget, str) and len(widget.strip()) > 0:
                        prompts[f"{class_type}_{node_id}_{i}"] = widget.strip()

        return prompts

    def get_rgthree_optimization_info(self, data: dict) -> dict[str, Any]:
        """Get information about RGthree optimization nodes."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        optimization_info = {
            "context_nodes": 0,
            "reroute_nodes": 0,
            "switch_nodes": 0,
            "display_nodes": 0,
            "utility_nodes": 0,
            "workflow_efficiency": "unknown",
        }

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "Context" in class_type:
                optimization_info["context_nodes"] += 1
            elif "Reroute" in class_type:
                optimization_info["reroute_nodes"] += 1
            elif "Switch" in class_type:
                optimization_info["switch_nodes"] += 1
            elif "Display" in class_type:
                optimization_info["display_nodes"] += 1
            elif self._is_rgthree_node(class_type):
                optimization_info["utility_nodes"] += 1

        # Calculate workflow efficiency
        total_optimization_nodes = (
            optimization_info["context_nodes"] + optimization_info["reroute_nodes"] + optimization_info["switch_nodes"]
        )

        if total_optimization_nodes > 5:
            optimization_info["workflow_efficiency"] = "high"
        elif total_optimization_nodes > 2:
            optimization_info["workflow_efficiency"] = "medium"
        elif total_optimization_nodes > 0:
            optimization_info["workflow_efficiency"] = "low"
        else:
            optimization_info["workflow_efficiency"] = "none"

        return optimization_info
