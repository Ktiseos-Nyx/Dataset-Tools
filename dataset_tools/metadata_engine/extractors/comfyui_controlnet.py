# dataset_tools/metadata_engine/extractors/comfyui_controlnet.py

"""ComfyUI ControlNet ecosystem extractor.

Handles ControlNet nodes, preprocessors, and control conditioning.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIControlNetExtractor:
    """Handles ControlNet ecosystem nodes."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the ControlNet extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "controlnet_extract_models": self._extract_controlnet_models,
            "controlnet_extract_preprocessors": self._extract_preprocessors,
            "controlnet_extract_apply_params": self._extract_apply_params,
            "controlnet_extract_advanced_params": self._extract_advanced_params,
            "controlnet_detect_workflow": self.detect_controlnet_workflow,
        }

    def _extract_controlnet_models(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract ControlNet model information."""
        self.logger.debug("[ControlNet] Extracting models")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        controlnet_models = {}

        # Look for ControlNet loader nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "ControlNetLoader" in class_type or "DiffControlNetLoader" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    model_name = widgets[0] if isinstance(widgets[0], str) else ""
                    controlnet_models[node_id] = {
                        "model_name": model_name,
                        "node_type": class_type,
                        "node_id": node_id,
                    }

        return controlnet_models

    def _extract_preprocessors(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract ControlNet preprocessor information."""
        self.logger.debug("[ControlNet] Extracting preprocessors")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        preprocessors = {}

        # Common ControlNet preprocessors
        preprocessor_types = [
            "CannyEdgePreprocessor",
            "HEDPreprocessor",
            "ScribblePreprocessor",
            "FakeScribblePreprocessor",
            "M-LSDPreprocessor",
            "OpenposePreprocessor",
            "DWPreprocessor",
            "MiDaS-DepthMapPreprocessor",
            "LeReS-DepthMapPreprocessor",
            "Zoe-DepthMapPreprocessor",
            "NormalMapPreprocessor",
            "BAE-NormalMapPreprocessor",
            "LineArtPreprocessor",
            "ContentShufflePreprocessor",
            "ColorPreprocessor",
            "MediaPipe-FaceMeshPreprocessor",
            "SemSegPreprocessor",
            "BinaryPreprocessor",
            "InpaintPreprocessor",
            "AnyLinePreprocessor",
            "PIDI-LineArtPreprocessor",
            "TEEDPreprocessor",
            "UnimatchOptFlowPreprocessor",
            "MeshGraphormerPreprocessor",
            "OpenposePreprocessor",
            "MediaPipeHandPosePreprocessor",
            "MediaPipeFaceMeshPreprocessor",
            "DensePosePreprocessor",
            "AnimeLineArtPreprocessor",
            "MangaLineExtractor",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(prep_type in class_type for prep_type in preprocessor_types):
                widgets = node_data.get("widgets_values", [])
                preprocessors[node_id] = {
                    "type": class_type,
                    "widgets": widgets,
                    "node_id": node_id,
                }

        return preprocessors

    def _extract_apply_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract ControlNet apply parameters."""
        self.logger.debug("[ControlNet] Extracting apply params")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        apply_params = {}

        # Look for ControlNet apply nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "ControlNetApply" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    apply_params[node_id] = {
                        "strength": (widgets[0] if len(widgets) > 0 and isinstance(widgets[0], (int, float)) else 1.0),
                        "start_percent": (
                            widgets[1] if len(widgets) > 1 and isinstance(widgets[1], (int, float)) else 0.0
                        ),
                        "end_percent": (
                            widgets[2] if len(widgets) > 2 and isinstance(widgets[2], (int, float)) else 1.0
                        ),
                        "node_type": class_type,
                        "node_id": node_id,
                    }

            elif "ControlNetApplyAdvanced" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    apply_params[node_id] = {
                        "strength": (widgets[0] if len(widgets) > 0 and isinstance(widgets[0], (int, float)) else 1.0),
                        "start_percent": (
                            widgets[1] if len(widgets) > 1 and isinstance(widgets[1], (int, float)) else 0.0
                        ),
                        "end_percent": (
                            widgets[2] if len(widgets) > 2 and isinstance(widgets[2], (int, float)) else 1.0
                        ),
                        "mask_optional": widgets[3] if len(widgets) > 3 else None,
                        "node_type": class_type,
                        "node_id": node_id,
                    }

        return apply_params

    def _extract_advanced_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract advanced ControlNet parameters."""
        self.logger.debug("[ControlNet] Extracting advanced params")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        advanced_params = {}

        # Look for advanced ControlNet nodes
        advanced_node_types = [
            "ControlNetLoaderAdvanced",
            "ControlNetApplyAdvanced",
            "ControlNetInpaintingAliMamaApply",
            "ControlNetReference",
            "ControlNetTileApply",
            "ControlNetMultiApply",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(advanced_type in class_type for advanced_type in advanced_node_types):
                widgets = node_data.get("widgets_values", [])
                advanced_params[node_id] = {
                    "type": class_type,
                    "widgets": widgets,
                    "node_id": node_id,
                }

        return advanced_params

    def detect_controlnet_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this workflow uses ControlNet."""
        if not isinstance(data, dict):
            return False

        prompt_data = data.get("prompt", data)

        # Look for ControlNet indicators
        controlnet_indicators = [
            "ControlNet",
            "ControlNetLoader",
            "ControlNetApply",
            "CannyEdgePreprocessor",
            "HEDPreprocessor",
            "OpenposePreprocessor",
            "MiDaS-DepthMapPreprocessor",
            "LineArtPreprocessor",
            "DWPreprocessor",
            "ScribblePreprocessor",
            "NormalMapPreprocessor",
            "ContentShufflePreprocessor",
            "ColorPreprocessor",
            "MediaPipe",
            "SemSegPreprocessor",
            "PIDI",
            "TEEDPreprocessor",
            "UnimatchOptFlowPreprocessor",
            "MeshGraphormerPreprocessor",
            "DensePosePreprocessor",
            "AnimeLineArtPreprocessor",
            "MangaLineExtractor",
        ]

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if any(indicator in class_type for indicator in controlnet_indicators):
                return True

        return False

    def extract_controlnet_workflow_summary(self, data: dict) -> dict[str, Any]:
        """Extract comprehensive ControlNet workflow summary."""
        if not isinstance(data, dict):
            return {}

        summary = {
            "is_controlnet_workflow": self.detect_controlnet_workflow(data, {}, {}, {}),
            "models": self._extract_controlnet_models(data, {}, {}, {}),
            "preprocessors": self._extract_preprocessors(data, {}, {}, {}),
            "apply_params": self._extract_apply_params(data, {}, {}, {}),
            "advanced_params": self._extract_advanced_params(data, {}, {}, {}),
        }

        return summary

    def get_controlnet_nodes(self, data: dict) -> dict[str, dict]:
        """Get all ControlNet-related nodes in the workflow."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        controlnet_nodes = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if self._is_controlnet_node(class_type):
                controlnet_nodes[node_id] = {
                    "type": class_type,
                    "widgets": node_data.get("widgets_values", []),
                    "inputs": node_data.get("inputs", {}),
                    "outputs": node_data.get("outputs", []),
                }

        return controlnet_nodes

    def _is_controlnet_node(self, class_type: str) -> bool:
        """Check if a class type is a ControlNet node."""
        controlnet_indicators = [
            "ControlNet",
            "CannyEdgePreprocessor",
            "HEDPreprocessor",
            "OpenposePreprocessor",
            "MiDaS-DepthMapPreprocessor",
            "LineArtPreprocessor",
            "DWPreprocessor",
            "ScribblePreprocessor",
            "NormalMapPreprocessor",
            "ContentShufflePreprocessor",
            "ColorPreprocessor",
            "MediaPipe",
            "SemSegPreprocessor",
            "PIDI",
            "TEEDPreprocessor",
            "UnimatchOptFlowPreprocessor",
            "MeshGraphormerPreprocessor",
            "DensePosePreprocessor",
            "AnimeLineArtPreprocessor",
            "MangaLineExtractor",
            "BAE-NormalMapPreprocessor",
            "LeReS-DepthMapPreprocessor",
            "Zoe-DepthMapPreprocessor",
            "FakeScribblePreprocessor",
            "M-LSDPreprocessor",
            "MediaPipeHandPosePreprocessor",
            "MediaPipeFaceMeshPreprocessor",
            "BinaryPreprocessor",
            "InpaintPreprocessor",
            "AnyLinePreprocessor",
        ]

        return any(indicator in class_type for indicator in controlnet_indicators)

    def get_controlnet_control_types(self, data: dict) -> list[str]:
        """Get the types of control being used (canny, depth, openpose, etc.)."""
        if not isinstance(data, dict):
            return []

        prompt_data = data.get("prompt", data)
        control_types = set()

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # Extract control type from preprocessor names
            if "CannyEdgePreprocessor" in class_type:
                control_types.add("canny")
            elif "HEDPreprocessor" in class_type:
                control_types.add("hed")
            elif "OpenposePreprocessor" in class_type:
                control_types.add("openpose")
            elif "DepthMapPreprocessor" in class_type:
                control_types.add("depth")
            elif "LineArtPreprocessor" in class_type:
                control_types.add("lineart")
            elif "ScribblePreprocessor" in class_type:
                control_types.add("scribble")
            elif "NormalMapPreprocessor" in class_type:
                control_types.add("normal")
            elif "ContentShufflePreprocessor" in class_type:
                control_types.add("shuffle")
            elif "ColorPreprocessor" in class_type:
                control_types.add("color")
            elif "MediaPipe" in class_type:
                control_types.add("mediapipe")
            elif "SemSegPreprocessor" in class_type:
                control_types.add("seg")
            elif "PIDI" in class_type:
                control_types.add("pidi")
            elif "TEEDPreprocessor" in class_type:
                control_types.add("teed")
            elif "DensePosePreprocessor" in class_type:
                control_types.add("densepose")
            elif "AnimeLineArtPreprocessor" in class_type:
                control_types.add("anime_lineart")
            elif "MangaLineExtractor" in class_type:
                control_types.add("manga_line")

        return list(control_types)
