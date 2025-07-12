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
            "flux_extract_t5_prompt": self._extract_t5_prompt,
            "flux_extract_clip_prompt": self._extract_clip_prompt,
            "flux_extract_model_info": self._extract_flux_model_info,
            "flux_extract_guidance_scale": self._extract_guidance_scale,
            "flux_extract_scheduler_params": self._extract_scheduler_params,
            "flux_detect_workflow": self._detect_flux_workflow,
        }

    def _extract_t5_prompt(
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

    def _extract_clip_prompt(
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

            # FLUX checkpoint loaders
            if "FluxCheckpointLoader" in class_type or "DiffusionModel" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    model_info["checkpoint"] = (
                        widgets[0] if isinstance(widgets[0], str) else ""
                    )

            # FLUX UNET loaders
            elif "FluxUNETLoader" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    model_info["unet"] = (
                        widgets[0] if isinstance(widgets[0], str) else ""
                    )

            # FLUX VAE loaders
            elif "FluxVAELoader" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    model_info["vae"] = (
                        widgets[0] if isinstance(widgets[0], str) else ""
                    )

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
            if (
                "FluxScheduler" in class_type
                or "FlowMatchEulerDiscreteScheduler" in class_type
            ):
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    scheduler_params.update(
                        {
                            "scheduler_type": class_type,
                            "steps": (
                                widgets[0]
                                if len(widgets) > 0
                                and isinstance(widgets[0], (int, float))
                                else 20
                            ),
                            "denoise": (
                                widgets[1]
                                if len(widgets) > 1
                                and isinstance(widgets[1], (int, float))
                                else 1.0
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
                            "steps": (
                                widgets[0]
                                if len(widgets) > 0
                                and isinstance(widgets[0], (int, float))
                                else 20
                            ),
                            "max_shift": (
                                widgets[1]
                                if len(widgets) > 1
                                and isinstance(widgets[1], (int, float))
                                else 1.15
                            ),
                            "base_shift": (
                                widgets[2]
                                if len(widgets) > 2
                                and isinstance(widgets[2], (int, float))
                                else 0.5
                            ),
                        }
                    )

        return scheduler_params

    def _detect_flux_workflow(
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

        # Look for FLUX-specific node types
        flux_indicators = [
            "FluxCheckpointLoader",
            "FluxUNETLoader",
            "FluxVAELoader",
            "FluxGuidance",
            "FluxScheduler",
            "FluxSampler",
            "FlowMatchEulerDiscreteScheduler",
            "T5TextEncode",
            "DiffusionModel",
            "FluxModelLoader",
        ]

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
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

            # CLIP text encoders (but not T5)
            if "CLIPTextEncode" in class_type and "T5" not in class_type:
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

        # Then try input connections (would need traversal extractor)
        inputs = node_data.get("inputs", {})
        if isinstance(inputs, dict) and "text" in inputs:
            # This would need the traversal extractor to follow the connection
            pass

        return ""

    def extract_flux_workflow_summary(self, data: dict) -> dict[str, Any]:
        """Extract a comprehensive summary of FLUX workflow."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)

        summary = {
            "is_flux_workflow": self._detect_flux_workflow(data, {}, {}, {}),
            "t5_prompt": self._extract_t5_prompt(data, {}, {}, {}),
            "clip_prompt": self._extract_clip_prompt(data, {}, {}, {}),
            "model_info": self._extract_flux_model_info(data, {}, {}, {}),
            "guidance_scale": self._extract_guidance_scale(data, {}, {}, {}),
            "scheduler_params": self._extract_scheduler_params(data, {}, {}, {}),
        }

        return summary
