# dataset_tools/metadata_engine/extractors/comfyui_flux.py

"""ComfyUI FLUX-specific extraction methods.

Handles FLUX model workflows, T5 text encoding, and FLUX-specific parameters.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIFluxExtractor:
    """Handles FLUX-specific ComfyUI workflows."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the FLUX extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "flux_extract_t5_prompt": self.extract_t5_prompt,
            "flux_extract_clip_prompt": self.extract_clip_prompt,
            "flux_extract_model_info": self._extract_flux_model_info,
            "flux_extract_guidance_scale": self._extract_guidance_scale,
            "flux_extract_scheduler_params": self._extract_scheduler_params,
            "flux_detect_workflow": self.detect_flux_workflow,
            "flux_extract_complex_prompt": self._extract_complex_prompt,
            "flux_extract_wildcard_prompt": self._extract_wildcard_prompt,
        }

    def extract_t5_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract T5 text encoder prompt from FLUX workflows."""
        self.logger.debug("[FLUX] Extracting T5 prompt")

        if not isinstance(data, dict):
            return ""

        # Handle both prompt and workflow formats
        prompt_data = data.get("prompt", data)

        # Look for T5 text encoder nodes
        t5_nodes = self._find_t5_nodes(prompt_data)

        for node_id, node_data in t5_nodes.items():
            # Get the text input
            text = self._get_text_from_node(node_data)
            if text:
                return text

        return ""

    def extract_clip_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract CLIP text encoder prompt from FLUX workflows."""
        self.logger.debug("[FLUX] Extracting CLIP prompt")

        if not isinstance(data, dict):
            return ""

        prompt_data = data.get("prompt", data)

        # Look for CLIP text encoder nodes (separate from T5)
        clip_nodes = self._find_clip_nodes(prompt_data)

        for node_id, node_data in clip_nodes.items():
            text = self._get_text_from_node(node_data)
            if text:
                return text

        return ""

    def _extract_flux_model_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract FLUX model information."""
        self.logger.debug("[FLUX] Extracting model info")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        model_info = {}

        # Look for FLUX model loaders
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            widgets = node_data.get("widgets_values", [])

            # FLUX checkpoint loaders
            if "FluxCheckpointLoader" in class_type or "DiffusionModel" in class_type:
                if widgets:
                    model_info["checkpoint"] = widgets[0] if isinstance(widgets[0], str) else ""

            # FLUX UNET loaders (both dedicated and generic)
            elif "FluxUNETLoader" in class_type or "UNETLoader" in class_type:
                if widgets and widgets[0]:
                    model_name = str(widgets[0]).lower()
                    # Check if this is likely a FLUX model
                    if any(flux_indicator in model_name for flux_indicator in ["flux", "schnell", "dev"]):
                        model_info["unet"] = widgets[0]

            # FLUX VAE loaders
            elif "FluxVAELoader" in class_type or "VAELoader" in class_type:
                if widgets and widgets[0]:
                    vae_name = str(widgets[0]).lower()
                    # Check if this is likely a FLUX VAE (ae.safetensors, etc.)
                    if "ae." in vae_name or "flux" in vae_name:
                        model_info["vae"] = widgets[0]

            # Dual CLIP loaders (common in FLUX)
            elif "DualCLIPLoader" in class_type:
                if widgets and len(widgets) >= 2:
                    model_info["clip_l"] = widgets[0] if isinstance(widgets[0], str) else ""
                    model_info["t5xxl"] = widgets[1] if isinstance(widgets[1], str) else ""

        return model_info

    def _extract_guidance_scale(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> float:
        """Extract guidance scale from FLUX workflows."""
        self.logger.debug("[FLUX] Extracting guidance scale")

        if not isinstance(data, dict):
            return 0.0

        prompt_data = data.get("prompt", data)

        # Look for FLUX guidance nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "FluxGuidance" in class_type or "CFGGuidance" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets and isinstance(widgets[0], (int, float)):
                    return float(widgets[0])

        return 0.0

    def _extract_scheduler_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract scheduler parameters from FLUX workflows."""
        self.logger.debug("[FLUX] Extracting scheduler params")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        scheduler_params = {}

        # Look for FLUX scheduler nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # FLUX schedulers
            if "FluxScheduler" in class_type or "FlowMatchEulerDiscreteScheduler" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    scheduler_params.update(
                        {
                            "scheduler_type": class_type,
                            "steps": (widgets[0] if len(widgets) > 0 and isinstance(widgets[0], (int, float)) else 50),
                            "denoise": (
                                widgets[1] if len(widgets) > 1 and isinstance(widgets[1], (int, float)) else 1.0
                            ),
                        }
                    )

            # FLUX samplers
            elif "FluxSampler" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    scheduler_params.update(
                        {
                            "sampler_type": class_type,
                            "steps": (widgets[0] if len(widgets) > 0 and isinstance(widgets[0], (int, float)) else 50),
                            "max_shift": (
                                widgets[1] if len(widgets) > 1 and isinstance(widgets[1], (int, float)) else 1.15
                            ),
                            "base_shift": (
                                widgets[2] if len(widgets) > 2 and isinstance(widgets[2], (int, float)) else 0.5
                            ),
                        }
                    )

        return scheduler_params

    def detect_flux_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this is a FLUX workflow."""
        if not isinstance(data, dict):
            return False

        prompt_data = data.get("prompt", data)

        # Look for FLUX-specific node types (both dedicated and generic nodes used in FLUX workflows)
        flux_indicators = [
            # Dedicated FLUX nodes
            "FluxCheckpointLoader",
            "FluxUNETLoader",
            "FluxVAELoader",
            "FluxGuidance",
            "FluxScheduler",
            "FluxSampler",
            "FlowMatchEulerDiscreteScheduler",
            "FluxModelLoader",
            "DiffusionModel",
            # Generic nodes commonly used in FLUX workflows
            "CLIPTextEncodeFlux",
            "ModelSamplingFlux",
            "T5TextEncode",
            "BasicGuider",
            "SamplerCustomAdvanced",
            # Model loaders that contain "flux" in the filename pattern
            "UNETLoader",  # Often loads flux1-dev.sft, flux1-schnell.sft
            "DualCLIPLoader",  # FLUX uses dual CLIP (clip_l + t5xxl)
        ]

        # Handle both workflow format (nodes array) and prompt format (dict of nodes)
        nodes_to_check = []

        if "nodes" in prompt_data and isinstance(prompt_data["nodes"], list):
            # Workflow format: {"nodes": [{"type": "..."}, ...]}
            nodes_to_check = prompt_data["nodes"]
        else:
            # Prompt format: {"1": {"class_type": "..."}, "2": {...}, ...}
            nodes_to_check = list(prompt_data.values())

        for node_data in nodes_to_check:
            if not isinstance(node_data, dict):
                continue

            # Check both 'class_type' (prompt format) and 'type' (workflow format)
            class_type = node_data.get("class_type", "") or node_data.get("type", "")
            if any(indicator in class_type for indicator in flux_indicators):
                return True

        return False

    def _find_t5_nodes(self, prompt_data: dict) -> dict:
        """Find T5 text encoder nodes."""
        t5_nodes = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # T5 text encoders
            if "T5TextEncode" in class_type or "T5" in class_type:
                t5_nodes[node_id] = node_data

        return t5_nodes

    def _find_clip_nodes(self, prompt_data: dict) -> dict:
        """Find CLIP text encoder nodes (separate from T5)."""
        clip_nodes = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # CLIP text encoders (but not T5) - includes CLIPTextEncodeFlux
            if ("CLIPTextEncode" in class_type or "CLIPTextEncodeFlux" in class_type) and "T5" not in class_type:
                clip_nodes[node_id] = node_data

        return clip_nodes

    def _get_text_from_node(self, node_data: dict) -> str:
        """Extract text from a node's widgets or inputs."""
        # First try widget values
        widgets = node_data.get("widgets_values", [])
        if widgets:
            for widget in widgets:
                if isinstance(widget, str) and len(widget.strip()) > 0:
                    return widget.strip()

        # For CLIPTextEncodeFlux nodes, check inputs structure
        inputs = node_data.get("inputs", {})
        if isinstance(inputs, dict):
            # Check for text input
            if "text" in inputs:
                text_input = inputs["text"]
                if isinstance(text_input, str) and text_input.strip():
                    return text_input.strip()

            # Check for t5xxl input (FLUX specific)
            if "t5xxl" in inputs:
                t5_input = inputs["t5xxl"]
                if isinstance(t5_input, str) and t5_input.strip():
                    return t5_input.strip()

            # Check for clip_l input (FLUX specific)
            if "clip_l" in inputs:
                clip_input = inputs["clip_l"]
                if isinstance(clip_input, str) and clip_input.strip():
                    return clip_input.strip()

        return ""

    def extract_flux_workflow_summary(self, data: dict) -> dict[str, Any]:
        """Extract a comprehensive summary of FLUX workflow."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)

        summary = {
            "is_flux_workflow": self.detect_flux_workflow(data, {}, {}, {}),
            "t5_prompt": self.extract_t5_prompt(data, {}, {}, {}),
            "clip_prompt": self.extract_clip_prompt(data, {}, {}, {}),
            "model_info": self._extract_flux_model_info(data, {}, {}, {}),
            "guidance_scale": self._extract_guidance_scale(data, {}, {}, {}),
            "scheduler_params": self._extract_scheduler_params(data, {}, {}, {}),
        }

        return summary

    def _extract_complex_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract prompts from complex FLUX workflows with text concatenation and AI generation."""
        self.logger.debug("[FLUX] Extracting complex prompt")

        if not isinstance(data, dict):
            return ""

        prompt_data = data.get("prompt", data)

        # Look for text concatenation nodes that feed into CLIPTextEncodeFlux
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # Find CLIPTextEncodeFlux nodes
            if "CLIPTextEncodeFlux" in class_type:
                inputs = node_data.get("inputs", {})

                # Check if t5xxl or clip_l inputs are connected (not direct text)
                for input_name in ["t5xxl", "clip_l"]:
                    if input_name in inputs:
                        input_data = inputs[input_name]
                        if isinstance(input_data, dict) and "link" in input_data:
                            # This is a connection, need to trace back
                            source_text = self._trace_text_source(prompt_data, input_data["link"])
                            if source_text:
                                return source_text

        return ""

    def _extract_wildcard_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract prompts from wildcard-based FLUX workflows."""
        self.logger.debug("[FLUX] Extracting wildcard prompt")

        if not isinstance(data, dict):
            return ""

        prompt_data = data.get("prompt", data)

        # Look for wildcard processing nodes
        wildcard_nodes = [
            "Wildcard Processor",
            "ImpactWildcardEncode",
            "Wildcards",
            "easy string",
            "Merge Strings",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # Check for wildcard processors that might contain final prompts
            if any(wildcard_type in class_type for wildcard_type in wildcard_nodes):
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    for widget in widgets:
                        if isinstance(widget, str) and len(widget.strip()) > 20:  # Likely a prompt
                            return widget.strip()

                # Also check populated_text output for ImpactWildcardEncode
                if "ImpactWildcardEncode" in class_type:
                    inputs = node_data.get("inputs", {})
                    if isinstance(inputs, dict) and "populated_text" in inputs:
                        text = inputs["populated_text"]
                        if isinstance(text, str) and text.strip():
                            return text.strip()

        return ""

    def _trace_text_source(self, prompt_data: dict, link_id: int) -> str:
        """Trace back through connections to find source text."""
        # This is a simplified implementation - would need full traversal extractor
        # Look for nodes that output to this link

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # Check if this node might be the source
            if "Text" in class_type or "Concatenate" in class_type or "OllamaVision" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    for widget in widgets:
                        if isinstance(widget, str) and len(widget.strip()) > 10:
                            return widget.strip()

        return ""
