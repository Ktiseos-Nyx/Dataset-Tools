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
            "impact_extract_wildcard_prompt": self.extract_wildcard_prompt,
            "impact_extract_face_detailer_params": self._extract_face_detailer_params,
            "impact_extract_segs_info": self._extract_segs_info,
            "impact_extract_detailer_pipe": self._extract_detailer_pipe,
            "impact_extract_jw_integer": self._extract_jw_integer,
            "impact_extract_impact_switch": self._extract_impact_switch,
            "impact_extract_dp_random_generator": self._extract_dp_random_generator,
            "impact_extract_lora_tag_loader": self._extract_lora_tag_loader,
            "impact_extract_flux_guidance": self._extract_flux_guidance,
            "impact_extract_ksampler_advanced_inspire": self._extract_ksampler_advanced_inspire,
            "impact_extract_dynamic_thresholding_full": self._extract_dynamic_thresholding_full,
            "impact_extract_dynamic_thresholding_simple": self._extract_dynamic_thresholding_simple,
            "impact_extract_impact_wildcard_encode": self._extract_impact_wildcard_encode,
            "impact_extract_wildcard_prompt_from_string": self._extract_wildcard_prompt_from_string,
            "impact_detect_workflow": self.detect_impact_workflow,
        }

    def _get_node_data(self, data: Any) -> dict[str, Any]:
        """Helper to get the prompt data from the workflow."""
        if not isinstance(data, dict):
            return {}
        return data.get("prompt", data)

    def _extract_widgets_values(self, node_data: dict, keys: list[str]) -> dict[str, Any]:
        """Helper to extract values from a node's widgets_values list based on a list of keys."""
        extracted = {}
        widgets = node_data.get("widgets_values", [])
        for i, key in enumerate(keys):
            if i < len(widgets):
                extracted[key] = widgets[i]
        return extracted

    def extract_wildcard_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract processed prompt from ImpactWildcardProcessor."""
        self.logger.debug("[Impact] Extracting wildcard prompt")

        prompt_data = self._get_node_data(data)

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

                    mode = widgets[2] if len(widgets) > 2 else None
                    if mode == 0:  # fixed mode
                        if len(widgets) > 1 and isinstance(widgets[1], str):
                            return widgets[1].strip()
                    elif mode == 1:  # populate mode
                        if len(widgets) > 0 and isinstance(widgets[0], str):
                            return widgets[0].strip()
                    else:  # Fallback for older versions or unknown modes
                        if len(widgets) > 1 and isinstance(widgets[1], str):
                            processed_text = widgets[1].strip()
                            if processed_text and processed_text != widgets[0]:
                                return processed_text
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

        prompt_data = self._get_node_data(data)
        face_detailer_params = {}

        # Look for FaceDetailer nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "FaceDetailer" in class_type:
                face_detailer_params = self._extract_widgets_values(
                    node_data,
                    [
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
                    ],
                )

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

        prompt_data = self._get_node_data(data)
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
                segs_info[class_type] = {
                    "node_id": node_id,
                    "widgets": node_data.get("widgets_values", []),
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

        prompt_data = self._get_node_data(data)
        detailer_pipe = {}

        # Look for DetailerPipe nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "DetailerPipe" in class_type:
                detailer_pipe[class_type] = {
                    "node_id": node_id,
                    "widgets": node_data.get("widgets_values", []),
                    "type": class_type,
                }

        return detailer_pipe

    def _extract_impact_wildcard_encode(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract information from ImpactWildcardEncode nodes."""
        self.logger.debug("[Impact] Extracting ImpactWildcardEncode values")
        prompt_data = self._get_node_data(data)
        wildcard_encodes = {}
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue
            class_type = node_data.get("class_type", "")
            if "ImpactWildcardEncode" in class_type:
                # The text input is usually linked, so we need to trace it.
                # For now, we'll just note its presence.
                wildcard_encodes[node_id] = {"node_type": class_type}
        return wildcard_encodes

    def _extract_wildcard_prompt_from_string(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract information from Wildcard Prompt from String nodes."""
        self.logger.debug("[Impact] Extracting Wildcard Prompt from String values")
        prompt_data = self._get_node_data(data)
        wildcard_strings = {}
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue
            class_type = node_data.get("class_type", "")
            if "Wildcard Prompt from String" in class_type:
                extracted_values = self._extract_widgets_values(node_data, ["text"])
                wildcard_strings[node_id] = extracted_values
        return wildcard_strings

    def _extract_jw_integer(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract value from JWInteger nodes."""
        self.logger.debug("[Impact] Extracting JWInteger values")
        prompt_data = self._get_node_data(data)
        jw_integers = {}
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue
            class_type = node_data.get("class_type", "")
            if "JWInteger" in class_type:
                value = self._extract_widgets_values(node_data, ["value"])
                if "value" in value:
                    jw_integers[node_id] = value["value"]
        return jw_integers

    def _extract_impact_switch(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract selected input/output from ImpactSwitch nodes."""
        self.logger.debug("[Impact] Extracting ImpactSwitch values")
        prompt_data = self._get_node_data(data)
        impact_switches = {}
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue
            class_type = node_data.get("class_type", "")
            if "ImpactSwitch" in class_type:
                # The 'select' widget determines which input is active
                selected_index = self._extract_widgets_values(node_data, ["select"]).get("select")
                impact_switches[node_id] = {"selected_index": selected_index}
        return impact_switches

    def _extract_dp_random_generator(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract information from DPRandomGenerator nodes."""
        self.logger.debug("[Impact] Extracting DPRandomGenerator values")
        prompt_data = self._get_node_data(data)
        dp_generators = {}
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue
            class_type = node_data.get("class_type", "")
            if "DPRandomGenerator" in class_type:
                extracted_values = self._extract_widgets_values(node_data, ["text", "seed", "mode", "enabled"])
                dp_generators[node_id] = extracted_values
        return dp_generators

    def _extract_lora_tag_loader(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract information from LoraTagLoader nodes."""
        self.logger.debug("[Impact] Extracting LoraTagLoader values")
        prompt_data = self._get_node_data(data)
        lora_loaders = {}
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue
            class_type = node_data.get("class_type", "")
            if "LoraTagLoader" in class_type:
                extracted_values = self._extract_widgets_values(
                    node_data, ["lora_name", "strength_model", "strength_clip"]
                )
                lora_loaders[node_id] = extracted_values
        return lora_loaders

    def _extract_flux_guidance(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract information from FluxGuidance nodes."""
        self.logger.debug("[Impact] Extracting FluxGuidance values")
        prompt_data = self._get_node_data(data)
        flux_guidance_nodes = {}
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue
            class_type = node_data.get("class_type", "")
            if "FluxGuidance" in class_type:
                extracted_values = self._extract_widgets_values(node_data, ["guidance_scale"])
                flux_guidance_nodes[node_id] = extracted_values
        return flux_guidance_nodes

    def _extract_ksampler_advanced_inspire(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract information from KSamplerAdvanced //Inspire nodes."""
        self.logger.debug("[Impact] Extracting KSamplerAdvanced //Inspire values")
        prompt_data = self._get_node_data(data)
        ksampler_nodes = {}
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue
            class_type = node_data.get("class_type", "")
            if "KSamplerAdvanced //Inspire" in class_type:
                extracted_values = self._extract_widgets_values(
                    node_data,
                    [
                        "seed",
                        "steps",
                        "cfg",
                        "sampler_name",
                        "scheduler",
                        "denoise",
                        "start_at_step",
                        "end_at_step",
                        "return_with_leftover_noise",
                    ],
                )
                ksampler_nodes[node_id] = extracted_values
        return ksampler_nodes

    def _extract_dynamic_thresholding_full(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract information from DynamicThresholdingFull nodes."""
        self.logger.debug("[Impact] Extracting DynamicThresholdingFull values")
        prompt_data = self._get_node_data(data)
        dt_nodes = {}
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue
            class_type = node_data.get("class_type", "")
            if "DynamicThresholdingFull" in class_type:
                extracted_values = self._extract_widgets_values(
                    node_data,
                    [
                        "mimic_scale",
                        "threshold_scale",
                        "mimic_mode",
                        "mimic_restore_amount",
                        "cfg_mode",
                        "threshold_mode",
                        "min_cfg_value",
                        "max_cfg_value",
                        "separate_feature_channels",
                        "scaling_start_step",
                        "scaling_end_step",
                    ],
                )
                dt_nodes[node_id] = extracted_values
        return dt_nodes

    def _extract_dynamic_thresholding_simple(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract information from DynamicThresholdingSimple nodes."""
        self.logger.debug("[Impact] Extracting DynamicThresholdingSimple values")
        prompt_data = self._get_node_data(data)
        dt_nodes = {}
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue
            class_type = node_data.get("class_type", "")
            if "DynamicThresholdingSimple" in class_type:
                extracted_values = self._extract_widgets_values(node_data, ["mimic_scale", "threshold_scale"])
                dt_nodes[node_id] = extracted_values
        return dt_nodes

    def detect_impact_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this workflow uses Impact Pack nodes."""
        prompt_data = self._get_node_data(data)

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
            "JWInteger",
            "ImpactSwitch",
            "DPRandomGenerator",
            "LoraTagLoader",
            "FluxGuidance",
            "KSamplerAdvanced //Inspire",
            "DynamicThresholdingFull",
            "DynamicThresholdingSimple",
            "Switch any [Crystools]",
            "ImpactWildcardEncode",
            "Wildcard Prompt from String",
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
            "is_impact_workflow": self.detect_impact_workflow(data, {}, {}, {}),
            "wildcard_prompt": self.extract_wildcard_prompt(data, {}, {}, {}),
            "face_detailer_params": self._extract_face_detailer_params(data, {}, {}, {}),
            "segs_info": self._extract_segs_info(data, {}, {}, {}),
            "detailer_pipe": self._extract_detailer_pipe(data, {}, {}, {}),
            "jw_integers": self._extract_jw_integer(data, {}, {}, {}),
            "impact_switches": self._extract_impact_switch(data, {}, {}, {}),
            "dp_random_generators": self._extract_dp_random_generator(data, {}, {}, {}),
            "lora_tag_loaders": self._extract_lora_tag_loader(data, {}, {}, {}),
            "flux_guidance_nodes": self._extract_flux_guidance(data, {}, {}, {}),
            "ksampler_advanced_inspire_nodes": self._extract_ksampler_advanced_inspire(data, {}, {}, {}),
            "dynamic_thresholding_full_nodes": self._extract_dynamic_thresholding_full(data, {}, {}, {}),
            "dynamic_thresholding_simple_nodes": self._extract_dynamic_thresholding_simple(data, {}, {}, {}),
        }

        return summary

    def get_impact_nodes(self, data: dict) -> dict[str, dict]:
        """Get all Impact Pack nodes in the workflow."""
        prompt_data = self._get_node_data(data)
        impact_nodes = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # Check if it's an Impact node or a related custom node
            if self._is_impact_node(class_type):
                impact_nodes[node_id] = {
                    "type": class_type,
                    "widgets": node_data.get("widgets_values", []),
                    "inputs": node_data.get("inputs", {}),
                    "outputs": node_data.get("outputs", []),
                }

        return impact_nodes

    def _is_impact_node(self, class_type: str) -> bool:
        """Check if a class type is an Impact Pack node or a related custom node."""
        impact_node_types = [
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
            "ImpactWildcardEncode",
            "Wildcard Prompt from String",
        ]

        return any(impact_type in class_type for impact_type in impact_node_types)
