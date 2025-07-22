# dataset_tools/metadata_engine/extractors/comfyui_efficiency.py

"""ComfyUI Efficiency Nodes ecosystem extractor.

Handles Efficiency Nodes including Efficient Loader, Efficient Sampler,
and other efficiency-focused workflow optimizations.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIEfficiencyExtractor:
    """Handles Efficiency Nodes ecosystem."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the Efficiency extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "efficiency_extract_loader_params": self._extract_loader_params,
            "efficiency_extract_sampler_params": self._extract_sampler_params,
            "efficiency_extract_ksampler_params": self._extract_ksampler_params,
            "efficiency_extract_script_params": self._extract_script_params,
            "efficiency_detect_workflow": self.detect_efficiency_workflow,
        }

    def _extract_loader_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Efficient Loader parameters."""
        self.logger.debug("[Efficiency] Extracting loader params")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        loader_params = {}

        # Look for Efficient Loader nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "Efficient Loader" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    # Efficient Loader typically has:
                    # [0] = ckpt_name
                    # [1] = vae_name
                    # [2] = clip_skip
                    # [3] = lora_name
                    # [4] = lora_model_strength
                    # [5] = lora_clip_strength
                    # [6] = positive prompt
                    # [7] = negative prompt
                    # [8] = token_normalization
                    # [9] = weight_interpretation
                    # [10] = empty_latent_width
                    # [11] = empty_latent_height
                    # [12] = batch_size

                    param_names = [
                        "ckpt_name",
                        "vae_name",
                        "clip_skip",
                        "lora_name",
                        "lora_model_strength",
                        "lora_clip_strength",
                        "positive_prompt",
                        "negative_prompt",
                        "token_normalization",
                        "weight_interpretation",
                        "empty_latent_width",
                        "empty_latent_height",
                        "batch_size",
                    ]

                    for i, param_name in enumerate(param_names):
                        if i < len(widgets):
                            loader_params[param_name] = widgets[i]

                    loader_params["node_type"] = class_type
                    loader_params["node_id"] = node_id
                    break

        return loader_params

    def _extract_sampler_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Efficient Sampler parameters."""
        self.logger.debug("[Efficiency] Extracting sampler params")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        sampler_params = {}

        # Look for Efficient Sampler nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "Efficient Sampler" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    # Efficient Sampler typically has:
                    # [0] = seed
                    # [1] = steps
                    # [2] = cfg
                    # [3] = sampler_name
                    # [4] = scheduler
                    # [5] = denoise
                    # [6] = preview_method
                    # [7] = vae_decode

                    param_names = [
                        "seed",
                        "steps",
                        "cfg",
                        "sampler_name",
                        "scheduler",
                        "denoise",
                        "preview_method",
                        "vae_decode",
                    ]

                    for i, param_name in enumerate(param_names):
                        if i < len(widgets):
                            sampler_params[param_name] = widgets[i]

                    sampler_params["node_type"] = class_type
                    sampler_params["node_id"] = node_id
                    break

        return sampler_params

    def _extract_ksampler_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Efficient KSampler parameters."""
        self.logger.debug("[Efficiency] Extracting KSampler params")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        ksampler_params = {}

        # Look for Efficient KSampler nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "Efficient KSampler" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    # Efficient KSampler parameters
                    param_names = [
                        "seed",
                        "steps",
                        "cfg",
                        "sampler_name",
                        "scheduler",
                        "denoise",
                        "preview_method",
                        "vae_decode",
                        "use_tiled_vae",
                        "tile_size",
                    ]

                    for i, param_name in enumerate(param_names):
                        if i < len(widgets):
                            ksampler_params[param_name] = widgets[i]

                    ksampler_params["node_type"] = class_type
                    ksampler_params["node_id"] = node_id
                    break

        return ksampler_params

    def _extract_script_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Efficiency Script parameters."""
        self.logger.debug("[Efficiency] Extracting script params")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        script_params = {}

        # Look for Efficiency Script nodes
        efficiency_script_nodes = [
            "Script",
            "HighRes-Fix Script",
            "NoiseControl Script",
            "AnimateDiff Script",
            "Upscale Script",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(script_node in class_type for script_node in efficiency_script_nodes):
                widgets = node_data.get("widgets_values", [])
                script_params[class_type] = {
                    "node_id": node_id,
                    "widgets": widgets,
                    "type": class_type,
                }

        return script_params

    def detect_efficiency_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this workflow uses Efficiency Nodes."""
        if not isinstance(data, dict):
            return False

        prompt_data = data.get("prompt", data)

        # Look for Efficiency Nodes indicators
        efficiency_indicators = [
            "Efficient Loader",
            "Efficient Sampler",
            "Efficient KSampler",
            "HighRes-Fix Script",
            "NoiseControl Script",
            "AnimateDiff Script",
            "Upscale Script",
            "XY Plot",
            "Evaluate Integers",
            "Evaluate Floats",
            "Evaluate Strings",
            "Simple Eval Examples",
            "Control Script",
            "Tiled Sampler",
            "Tiled KSampler",
        ]

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if any(indicator in class_type for indicator in efficiency_indicators):
                return True

        # Also check properties for efficiency cnr_id
        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            properties = node_data.get("properties", {})
            if isinstance(properties, dict):
                cnr_id = properties.get("cnr_id", "")
                if "efficiency" in cnr_id.lower():
                    return True

        return False

    def extract_efficiency_workflow_summary(self, data: dict) -> dict[str, Any]:
        """Extract comprehensive Efficiency Nodes workflow summary."""
        if not isinstance(data, dict):
            return {}

        summary = {
            "is_efficiency_workflow": self.detect_efficiency_workflow(data, {}, {}, {}),
            "loader_params": self._extract_loader_params(data, {}, {}, {}),
            "sampler_params": self._extract_sampler_params(data, {}, {}, {}),
            "ksampler_params": self._extract_ksampler_params(data, {}, {}, {}),
            "script_params": self._extract_script_params(data, {}, {}, {}),
        }

        return summary

    def get_efficiency_nodes(self, data: dict) -> dict[str, dict]:
        """Get all Efficiency Nodes in the workflow."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        efficiency_nodes = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # Check if it's an Efficiency node
            if self._is_efficiency_node(class_type):
                efficiency_nodes[node_id] = {
                    "type": class_type,
                    "widgets": node_data.get("widgets_values", []),
                    "inputs": node_data.get("inputs", {}),
                    "outputs": node_data.get("outputs", []),
                }

        return efficiency_nodes

    def _is_efficiency_node(self, class_type: str) -> bool:
        """Check if a class type is an Efficiency node."""
        efficiency_node_types = [
            "Efficient Loader",
            "Efficient Sampler",
            "Efficient KSampler",
            "HighRes-Fix Script",
            "NoiseControl Script",
            "AnimateDiff Script",
            "Upscale Script",
            "XY Plot",
            "Evaluate Integers",
            "Evaluate Floats",
            "Evaluate Strings",
            "Simple Eval Examples",
            "Control Script",
            "Tiled Sampler",
            "Tiled KSampler",
            "Image Scale",
            "Image Scale by Factor",
            "Unsampler",
            "Noise Control Script",
            "HiRes-Fix Script",
            "Efficient Attention",
            "Efficient LoRA Stack",
            "Efficient ControlNet Stack",
        ]

        return any(efficiency_type in class_type for efficiency_type in efficiency_node_types)
