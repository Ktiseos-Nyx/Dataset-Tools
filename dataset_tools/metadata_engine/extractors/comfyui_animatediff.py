# dataset_tools/metadata_engine/extractors/comfyui_animatediff.py

"""ComfyUI AnimateDiff ecosystem extractor.

Handles AnimateDiff nodes for video generation, motion modules,
and animation-specific parameters.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIAnimateDiffExtractor:
    """Handles AnimateDiff ecosystem nodes."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the AnimateDiff extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "animatediff_extract_motion_module": self._extract_motion_module,
            "animatediff_extract_animation_params": self._extract_animation_params,
            "animatediff_extract_context_options": self._extract_context_options,
            "animatediff_extract_controlnet_params": self._extract_controlnet_params,
            "animatediff_detect_workflow": self.detect_animatediff_workflow,
        }

    def _extract_motion_module(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract AnimateDiff motion module information."""
        self.logger.debug("[AnimateDiff] Extracting motion module")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        motion_module = {}

        # Look for AnimateDiff motion module loaders
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "AnimateDiffLoader" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    motion_module = {
                        "model_name": (widgets[0] if len(widgets) > 0 and isinstance(widgets[0], str) else ""),
                        "beta_schedule": (widgets[1] if len(widgets) > 1 and isinstance(widgets[1], str) else ""),
                        "motion_scale": (
                            widgets[2] if len(widgets) > 2 and isinstance(widgets[2], (int, float)) else 1.0
                        ),
                        "node_type": class_type,
                        "node_id": node_id,
                    }
                    break

            elif "ADE_AnimateDiffLoaderGen1" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    motion_module = {
                        "model_name": (widgets[0] if len(widgets) > 0 and isinstance(widgets[0], str) else ""),
                        "node_type": class_type,
                        "node_id": node_id,
                    }
                    break

        return motion_module

    def _extract_animation_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract AnimateDiff animation parameters."""
        self.logger.debug("[AnimateDiff] Extracting animation params")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        animation_params = {}

        # Look for AnimateDiff sampling nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "AnimateDiffSampler" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    animation_params = {
                        "frame_count": (widgets[0] if len(widgets) > 0 and isinstance(widgets[0], int) else 16),
                        "fps": (widgets[1] if len(widgets) > 1 and isinstance(widgets[1], (int, float)) else 8.0),
                        "loop_count": (widgets[2] if len(widgets) > 2 and isinstance(widgets[2], int) else 0),
                        "node_type": class_type,
                        "node_id": node_id,
                    }
                    break

            elif "ADE_AnimateDiffSampler" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    animation_params = {
                        "seed": (widgets[0] if len(widgets) > 0 and isinstance(widgets[0], int) else 0),
                        "steps": (widgets[1] if len(widgets) > 1 and isinstance(widgets[1], int) else 50),
                        "cfg": (widgets[2] if len(widgets) > 2 and isinstance(widgets[2], (int, float)) else 7.5),
                        "sampler_name": (widgets[3] if len(widgets) > 3 and isinstance(widgets[3], str) else ""),
                        "scheduler": (widgets[4] if len(widgets) > 4 and isinstance(widgets[4], str) else ""),
                        "denoise": (widgets[5] if len(widgets) > 5 and isinstance(widgets[5], (int, float)) else 1.0),
                        "node_type": class_type,
                        "node_id": node_id,
                    }
                    break

        return animation_params

    def _extract_context_options(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract AnimateDiff context options."""
        self.logger.debug("[AnimateDiff] Extracting context options")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        context_options = {}

        # Look for AnimateDiff context nodes
        context_node_types = [
            "ADE_AnimateDiffUniformContextOptions",
            "ADE_LoopedUniformContextOptions",
            "ADE_AnimateDiffContextOptions",
            "AnimateDiffContextOptions",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(context_type in class_type for context_type in context_node_types):
                widgets = node_data.get("widgets_values", [])
                context_options[class_type] = {
                    "widgets": widgets,
                    "node_type": class_type,
                    "node_id": node_id,
                }

        return context_options

    def _extract_controlnet_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract AnimateDiff ControlNet parameters."""
        self.logger.debug("[AnimateDiff] Extracting ControlNet params")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        controlnet_params = {}

        # Look for AnimateDiff ControlNet nodes
        controlnet_node_types = [
            "ADE_ControlNetLoaderAdvanced",
            "ADE_ControlNetApplyAdvanced",
            "AnimateDiffControlNet",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(controlnet_type in class_type for controlnet_type in controlnet_node_types):
                widgets = node_data.get("widgets_values", [])
                controlnet_params[class_type] = {
                    "widgets": widgets,
                    "node_type": class_type,
                    "node_id": node_id,
                }

        return controlnet_params

    def detect_animatediff_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this workflow uses AnimateDiff."""
        if not isinstance(data, dict):
            return False

        prompt_data = data.get("prompt", data)

        # Look for AnimateDiff indicators
        animatediff_indicators = [
            "AnimateDiff",
            "ADE_AnimateDiff",
            "AnimateDiffLoader",
            "AnimateDiffSampler",
            "AnimateDiffUniformContextOptions",
            "LoopedUniformContextOptions",
            "AnimateDiffContextOptions",
            "ADE_ControlNetLoaderAdvanced",
            "ADE_ControlNetApplyAdvanced",
        ]

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if any(indicator in class_type for indicator in animatediff_indicators):
                return True

        # Also check properties for AnimateDiff cnr_id
        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            properties = node_data.get("properties", {})
            if isinstance(properties, dict):
                cnr_id = properties.get("cnr_id", "")
                if "animatediff" in cnr_id.lower():
                    return True

        return False

    def extract_animatediff_workflow_summary(self, data: dict) -> dict[str, Any]:
        """Extract comprehensive AnimateDiff workflow summary."""
        if not isinstance(data, dict):
            return {}

        summary = {
            "is_animatediff_workflow": self.detect_animatediff_workflow(data, {}, {}, {}),
            "motion_module": self._extract_motion_module(data, {}, {}, {}),
            "animation_params": self._extract_animation_params(data, {}, {}, {}),
            "context_options": self._extract_context_options(data, {}, {}, {}),
            "controlnet_params": self._extract_controlnet_params(data, {}, {}, {}),
        }

        return summary

    def get_animatediff_nodes(self, data: dict) -> dict[str, dict]:
        """Get all AnimateDiff-related nodes in the workflow."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        animatediff_nodes = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if self._is_animatediff_node(class_type):
                animatediff_nodes[node_id] = {
                    "type": class_type,
                    "widgets": node_data.get("widgets_values", []),
                    "inputs": node_data.get("inputs", {}),
                    "outputs": node_data.get("outputs", []),
                }

        return animatediff_nodes

    def _is_animatediff_node(self, class_type: str) -> bool:
        """Check if a class type is an AnimateDiff node."""
        animatediff_node_types = [
            "AnimateDiff",
            "ADE_AnimateDiff",
            "AnimateDiffLoader",
            "AnimateDiffSampler",
            "AnimateDiffUniformContextOptions",
            "LoopedUniformContextOptions",
            "AnimateDiffContextOptions",
            "ADE_ControlNetLoaderAdvanced",
            "ADE_ControlNetApplyAdvanced",
            "ADE_AnimateDiffLoaderGen1",
            "ADE_AnimateDiffSampler",
            "ADE_AnimateDiffUniformContextOptions",
            "ADE_LoopedUniformContextOptions",
        ]

        return any(anim_type in class_type for anim_type in animatediff_node_types)

    def extract_video_generation_info(self, data: dict) -> dict[str, Any]:
        """Extract video generation specific information."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        video_info = {}

        # Look for video generation nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "VideoLinearCFGGuidance" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    video_info["cfg_guidance"] = {
                        "min_cfg": widgets[0] if len(widgets) > 0 else 1.0,
                        "max_cfg": widgets[1] if len(widgets) > 1 else 7.5,
                        "node_type": class_type,
                    }

            elif "VideoSave" in class_type or "SaveAnimatedWebp" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    video_info["save_options"] = {
                        "filename": (widgets[0] if len(widgets) > 0 and isinstance(widgets[0], str) else ""),
                        "fps": widgets[1] if len(widgets) > 1 else 8,
                        "node_type": class_type,
                    }

        return video_info
