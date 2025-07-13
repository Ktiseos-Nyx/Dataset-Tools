# dataset_tools/metadata_engine/extractors/comfyui_pixart.py

"""ComfyUI PixArt-specific extraction methods.

Handles PixArt Sigma workflows, T5 conditioning, and PixArt-specific parameters.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIPixArtExtractor:
    """Handles PixArt-specific ComfyUI workflows."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the PixArt extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "pixart_extract_t5_prompt": self.extract_t5_prompt,
            "pixart_extract_model_info": self._extract_model_info,
            "pixart_extract_sampler_params": self._extract_sampler_params,
            "pixart_extract_conditioning_params": self._extract_conditioning_params,
            "pixart_detect_workflow": self.detect_pixart_workflow,
        }

    def extract_t5_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract T5 text encoder prompt from PixArt workflows."""
        self.logger.debug("[PixArt] Extracting T5 prompt")

        if not isinstance(data, dict):
            return ""

        prompt_data = data.get("prompt", data)

        # Look for PixArt T5 text encoder nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "PixArtT5TextEncode" in class_type or "T5TextEncode" in class_type:
                # Get the text from widget or input
                text = self._get_text_from_node(node_data, prompt_data)
                if text:
                    return text

        return ""

    def _extract_model_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract PixArt model information."""
        self.logger.debug("[PixArt] Extracting model info")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        model_info = {}

        # Look for PixArt model loaders
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "PixArtCheckpointLoader" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    model_info["checkpoint"] = widgets[0] if isinstance(widgets[0], str) else ""

            elif "PixArtModelLoader" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    model_info["model"] = widgets[0] if isinstance(widgets[0], str) else ""

            elif "PixArtVAELoader" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    model_info["vae"] = widgets[0] if isinstance(widgets[0], str) else ""

            elif "PixArtT5Loader" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    model_info["t5_model"] = widgets[0] if isinstance(widgets[0], str) else ""

        return model_info

    def _extract_sampler_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract PixArt sampler parameters."""
        self.logger.debug("[PixArt] Extracting sampler params")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        sampler_params = {}

        # Look for PixArt sampler nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "PixArtSampler" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    # PixArt sampler parameters
                    param_mapping = {
                        0: "seed",
                        1: "steps",
                        2: "cfg_scale",
                        3: "sampler_name",
                        4: "scheduler",
                        5: "denoise",
                        6: "dpm_solver_order",
                        7: "guidance_scale",
                    }

                    for i, param_name in param_mapping.items():
                        if i < len(widgets):
                            sampler_params[param_name] = widgets[i]

                    sampler_params["node_type"] = class_type
                    break

        return sampler_params

    def _extract_conditioning_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract PixArt conditioning parameters."""
        self.logger.debug("[PixArt] Extracting conditioning params")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        conditioning_params = {}

        # Look for PixArt conditioning nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "PixArtT5TextEncode" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    conditioning_params["t5_conditioning"] = {
                        "text": (widgets[0] if len(widgets) > 0 and isinstance(widgets[0], str) else ""),
                        "max_length": widgets[1] if len(widgets) > 1 else 256,
                        "guidance_scale": widgets[2] if len(widgets) > 2 else 7.5,
                        "node_type": class_type,
                    }

            elif "PixArtConditioning" in class_type:
                widgets = node_data.get("widgets_values", [])
                conditioning_params["conditioning"] = {
                    "widgets": widgets,
                    "node_type": class_type,
                }

        return conditioning_params

    def detect_pixart_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this is a PixArt workflow."""
        if not isinstance(data, dict):
            return False

        prompt_data = data.get("prompt", data)

        # Look for PixArt-specific node types
        pixart_indicators = [
            "PixArt",
            "PixArtCheckpointLoader",
            "PixArtModelLoader",
            "PixArtVAELoader",
            "PixArtT5Loader",
            "PixArtT5TextEncode",
            "PixArtSampler",
            "PixArtConditioning",
            "PixArtSigma",
        ]

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if any(indicator in class_type for indicator in pixart_indicators):
                return True

        # Also check for models with PixArt in the name
        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if "CheckpointLoader" in class_type or "ModelLoader" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets and isinstance(widgets[0], str):
                    model_name = widgets[0].lower()
                    if "pixart" in model_name or "sigma" in model_name:
                        return True

        return False

    def _get_text_from_node(self, node_data: dict, prompt_data: dict) -> str:
        """Extract text from a PixArt node's widgets or inputs."""
        # First try widget values
        widgets = node_data.get("widgets_values", [])
        if widgets:
            for widget in widgets:
                if isinstance(widget, str) and len(widget.strip()) > 0:
                    return widget.strip()

        # Then try input connections (would need traversal extractor)
        inputs = node_data.get("inputs", {})
        if isinstance(inputs, dict) and "text" in inputs:
            input_info = inputs["text"]
            if isinstance(input_info, list) and len(input_info) > 0:
                source_node_id = str(input_info[0])
                if source_node_id in prompt_data:
                    source_node = prompt_data[source_node_id]
                    source_widgets = source_node.get("widgets_values", [])
                    if source_widgets and isinstance(source_widgets[0], str):
                        return source_widgets[0].strip()

        return ""

    def extract_pixart_workflow_summary(self, data: dict) -> dict[str, Any]:
        """Extract comprehensive PixArt workflow summary."""
        if not isinstance(data, dict):
            return {}

        summary = {
            "is_pixart_workflow": self.detect_pixart_workflow(data, {}, {}, {}),
            "t5_prompt": self.extract_t5_prompt(data, {}, {}, {}),
            "model_info": self._extract_model_info(data, {}, {}, {}),
            "sampler_params": self._extract_sampler_params(data, {}, {}, {}),
            "conditioning_params": self._extract_conditioning_params(data, {}, {}, {}),
        }

        return summary

    def get_pixart_nodes(self, data: dict) -> dict[str, dict]:
        """Get all PixArt-related nodes in the workflow."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        pixart_nodes = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "PixArt" in class_type or "Sigma" in class_type:
                pixart_nodes[node_id] = {
                    "type": class_type,
                    "widgets": node_data.get("widgets_values", []),
                    "inputs": node_data.get("inputs", {}),
                    "outputs": node_data.get("outputs", []),
                }

        return pixart_nodes
