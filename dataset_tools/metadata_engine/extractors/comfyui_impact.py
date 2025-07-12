# dataset_tools/metadata_engine/extractors/comfyui_impact.py

"""ComfyUI Impact Pack ecosystem extractor.

Handles Impact Pack nodes including ImpactWildcardProcessor,
FaceDetailer, and other Impact-specific functionality.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIImpactExtractor:
    """Handles Impact Pack ecosystem nodes."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the Impact extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "impact_extract_wildcard_prompt": self._extract_wildcard_prompt,
            "impact_extract_face_detailer_params": self._extract_face_detailer_params,
            "impact_extract_segs_info": self._extract_segs_info,
            "impact_extract_detailer_pipe": self._extract_detailer_pipe,
            "impact_detect_workflow": self._detect_impact_workflow,
        }

    def _extract_wildcard_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract processed prompt from ImpactWildcardProcessor."""
        self.logger.debug("[Impact] Extracting wildcard prompt")

        if not isinstance(data, dict):
            return ""

        prompt_data = data.get("prompt", data)

        # Look for ImpactWildcardProcessor nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "ImpactWildcardProcessor" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    # ImpactWildcardProcessor typically has:
                    # [0] = input text (with wildcards)
                    # [1] = processed text (wildcards resolved)
                    # [2] = mode (reproduce/randomize)
                    # [3] = seed
                    # [4] = etc.

                    # Return the processed text (usually index 1)
                    if len(widgets) > 1 and isinstance(widgets[1], str):
                        processed_text = widgets[1].strip()
                        if processed_text and processed_text != widgets[0]:
                            return processed_text

                    # Fallback to input text if processed text is empty
                    if len(widgets) > 0 and isinstance(widgets[0], str):
                        return widgets[0].strip()

        return ""

    def _extract_face_detailer_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract FaceDetailer parameters."""
        self.logger.debug("[Impact] Extracting FaceDetailer params")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        face_detailer_params = {}

        # Look for FaceDetailer nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "FaceDetailer" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    # FaceDetailer typically has parameters like:
                    # guide_size, guide_size_for, max_size, seed, steps, cfg, etc.

                    param_names = [
                        "guide_size",
                        "guide_size_for",
                        "max_size",
                        "seed",
                        "steps",
                        "cfg",
                        "sampler_name",
                        "scheduler",
                        "denoise",
                        "feather",
                        "crop_factor",
                        "drop_size",
                    ]

                    for i, param_name in enumerate(param_names):
                        if i < len(widgets):
                            face_detailer_params[param_name] = widgets[i]

                    face_detailer_params["node_type"] = class_type
                    break

        return face_detailer_params

    def _extract_segs_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract SEGS (segmentation) information."""
        self.logger.debug("[Impact] Extracting SEGS info")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        segs_info = {}

        # Look for SEGS-related nodes
        segs_nodes = [
            "SEGSDetailer",
            "SEGSPreview",
            "SEGSToImageList",
            "SEGSUpscaler",
            "SEGSPaste",
            "SEGSControlNetProvider",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(segs_node in class_type for segs_node in segs_nodes):
                widgets = node_data.get("widgets_values", [])
                segs_info[class_type] = {
                    "node_id": node_id,
                    "widgets": widgets,
                    "type": class_type,
                }

        return segs_info

    def _extract_detailer_pipe(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract DetailerPipe information."""
        self.logger.debug("[Impact] Extracting DetailerPipe")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        detailer_pipe = {}

        # Look for DetailerPipe nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "DetailerPipe" in class_type:
                widgets = node_data.get("widgets_values", [])
                detailer_pipe[class_type] = {
                    "node_id": node_id,
                    "widgets": widgets,
                    "type": class_type,
                }

        return detailer_pipe

    def _detect_impact_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this workflow uses Impact Pack nodes."""
        if not isinstance(data, dict):
            return False

        prompt_data = data.get("prompt", data)

        # Look for Impact Pack node indicators
        impact_indicators = [
            "Impact",
            "ImpactWildcardProcessor",
            "FaceDetailer",
            "SEGSDetailer",
            "DetailerPipe",
            "SEGS",
            "UltralyticsDetectorProvider",
            "SAMDetectorProvider",
            "BboxDetectorProvider",
            "SegmDetectorProvider",
        ]

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if any(indicator in class_type for indicator in impact_indicators):
                return True

        # Also check properties for Impact Pack cnr_id
        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            properties = node_data.get("properties", {})
            if isinstance(properties, dict):
                cnr_id = properties.get("cnr_id", "")
                if "impact" in cnr_id.lower():
                    return True

        return False

    def extract_impact_workflow_summary(self, data: dict) -> dict[str, Any]:
        """Extract comprehensive Impact Pack workflow summary."""
        if not isinstance(data, dict):
            return {}

        summary = {
            "is_impact_workflow": self._detect_impact_workflow(data, {}, {}, {}),
            "wildcard_prompt": self._extract_wildcard_prompt(data, {}, {}, {}),
            "face_detailer_params": self._extract_face_detailer_params(
                data, {}, {}, {}
            ),
            "segs_info": self._extract_segs_info(data, {}, {}, {}),
            "detailer_pipe": self._extract_detailer_pipe(data, {}, {}, {}),
        }

        return summary

    def get_impact_nodes(self, data: dict) -> dict[str, dict]:
        """Get all Impact Pack nodes in the workflow."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        impact_nodes = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # Check if it's an Impact node
            if "Impact" in class_type or self._is_impact_node(class_type):
                impact_nodes[node_id] = {
                    "type": class_type,
                    "widgets": node_data.get("widgets_values", []),
                    "inputs": node_data.get("inputs", {}),
                    "outputs": node_data.get("outputs", []),
                }

        return impact_nodes

    def _is_impact_node(self, class_type: str) -> bool:
        """Check if a class type is an Impact Pack node."""
        impact_node_types = [
            "FaceDetailer",
            "SEGSDetailer",
            "DetailerPipe",
            "SEGS",
            "UltralyticsDetectorProvider",
            "SAMDetectorProvider",
            "BboxDetectorProvider",
            "SegmDetectorProvider",
            "ImpactWildcardProcessor",
            "ImpactImageBatchToImageList",
            "ImpactImageInfo",
            "ImpactInt",
            "ImpactFloat",
            "ImpactString",
            "ImpactConditionalBranch",
            "ImpactControlNetApply",
            "ImpactDecomposeSEGS",
            "ImpactDilateErode",
            "ImpactGaussianBlur",
            "ImpactMakeTileSEGS",
            "ImpactSEGSClassify",
            "ImpactSEGSConcat",
            "ImpactSEGSOrderedFilter",
            "ImpactSEGSRangeFilter",
            "ImpactSEGSToMaskList",
            "ImpactSimpleDetectorProvider",
        ]

        return any(impact_type in class_type for impact_type in impact_node_types)
