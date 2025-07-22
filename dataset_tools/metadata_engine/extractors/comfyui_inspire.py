# dataset_tools/metadata_engine/extractors/comfyui_inspire.py

"""ComfyUI Inspire Pack ecosystem extractor.

Handles Inspire Pack nodes including regional prompting,
batch processing, and workflow optimization utilities.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIInspireExtractor:
    """Handles Inspire Pack ecosystem nodes."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the Inspire extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "inspire_extract_regional_prompts": self._extract_regional_prompts,
            "inspire_extract_batch_nodes": self._extract_batch_nodes,
            "inspire_extract_utility_nodes": self._extract_utility_nodes,
            "inspire_extract_sampler_nodes": self._extract_sampler_nodes,
            "inspire_extract_conditioning_nodes": self._extract_conditioning_nodes,
            "inspire_detect_workflow": self.detect_inspire_workflow,
        }

    def _extract_regional_prompts(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Inspire regional prompting nodes."""
        self.logger.debug("[Inspire] Extracting regional prompts")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        regional_prompts = {}

        # Inspire regional prompting nodes
        inspire_regional_nodes = [
            "RegionalPrompt",
            "RegionalConditioningSimple",
            "RegionalConditioningColorMask",
            "RegionalSampler",
            "RegionalSamplerAdvanced",
            "RegionalIPAdapterColorMask",
            "RegionalIPAdapterMask",
            "RegionalControlNetSimple",
            "RegionalControlNetColorMask",
            "RegionalControlNetMask",
            "CombineRegionalPrompts",
            "ApplyRegionalIPAdapters",
            "RegionalPromptColorMask",
            "RegionalPromptSimple",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(regional_node in class_type for regional_node in inspire_regional_nodes):
                widgets = node_data.get("widgets_values", [])
                regional_prompts[node_id] = {
                    "type": class_type,
                    "widgets": widgets,
                    "node_id": node_id,
                }

                # Extract regional prompt text
                for i, widget in enumerate(widgets):
                    if isinstance(widget, str) and len(widget.strip()) > 0:
                        regional_prompts[f"{node_id}_text_{i}"] = widget.strip()

        return regional_prompts

    def _extract_batch_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Inspire batch processing nodes."""
        self.logger.debug("[Inspire] Extracting batch nodes")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        batch_nodes = {}

        # Inspire batch processing nodes
        inspire_batch_nodes = [
            "BatchCreativeInterpolation",
            "BatchPromptSchedule",
            "BatchPromptScheduleSimple",
            "BatchValueSchedule",
            "BatchValueScheduleSimple",
            "BatchFloatSchedule",
            "BatchIntSchedule",
            "BatchStringSchedule",
            "BatchImageLoader",
            "BatchImageSaver",
            "BatchLatentSchedule",
            "BatchConditioningSchedule",
            "BatchModelSchedule",
            "BatchClipSchedule",
            "BatchVaeSchedule",
            "BatchSeedSchedule",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(batch_node in class_type for batch_node in inspire_batch_nodes):
                widgets = node_data.get("widgets_values", [])
                batch_nodes[node_id] = {
                    "type": class_type,
                    "widgets": widgets,
                    "node_id": node_id,
                }

        return batch_nodes

    def _extract_utility_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Inspire utility nodes."""
        self.logger.debug("[Inspire] Extracting utility nodes")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        utility_nodes = {}

        # Inspire utility nodes
        inspire_utility_nodes = [
            "WildcardProcessor",
            "WildcardProcessorSimple",
            "WildcardEncode",
            "WildcardEncodeSimple",
            "GlobalSeed",
            "GlobalSeedSimple",
            "GlobalSeedAdvanced",
            "PromptBuilder",
            "PromptBuilderSimple",
            "PromptExtractor",
            "PromptExtractorSimple",
            "StringFunction",
            "StringFunctionSimple",
            "MathFunction",
            "MathFunctionSimple",
            "CacheBackendData",
            "CacheBackendDataSimple",
            "LoadPromptsFromFile",
            "LoadPromptsFromDir",
            "SavePromptsToFile",
            "CheckpointName",
            "ModelName",
            "LoraName",
            "VaeName",
            "ImageBatchSplitter",
            "ImageBatchMerger",
            "LatentBatchSplitter",
            "LatentBatchMerger",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(utility_node in class_type for utility_node in inspire_utility_nodes):
                widgets = node_data.get("widgets_values", [])
                utility_nodes[node_id] = {
                    "type": class_type,
                    "widgets": widgets,
                    "node_id": node_id,
                }

        return utility_nodes

    def _extract_sampler_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Inspire sampler nodes."""
        self.logger.debug("[Inspire] Extracting sampler nodes")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        sampler_nodes = {}

        # Inspire sampler nodes
        inspire_sampler_nodes = [
            "KSamplerAdvanced",
            "KSamplerPipe",
            "KSamplerProgress",
            "KSamplerProgressSimple",
            "KSamplerInspire",
            "KSamplerInspireSimple",
            "InspireSampler",
            "InspireSamplerAdvanced",
            "InspireSamplerSimple",
            "DualCLIPLoader",
            "DualCLIPLoaderSimple",
            "UnCLIPCheckpointLoader",
            "UnCLIPCheckpointLoaderSimple",
            "DifferentialDiffusion",
            "DifferentialDiffusionSimple",
            "HyperTile",
            "HyperTileSimple",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(sampler_node in class_type for sampler_node in inspire_sampler_nodes):
                widgets = node_data.get("widgets_values", [])
                sampler_nodes[node_id] = {
                    "type": class_type,
                    "widgets": widgets,
                    "node_id": node_id,
                }

        return sampler_nodes

    def _extract_conditioning_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Inspire conditioning nodes."""
        self.logger.debug("[Inspire] Extracting conditioning nodes")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        conditioning_nodes = {}

        # Inspire conditioning nodes
        inspire_conditioning_nodes = [
            "CLIPTextEncodeWithWeight",
            "CLIPTextEncodeSimple",
            "CLIPTextEncodeAdvanced",
            "CLIPTextEncodeRegional",
            "ConditioningUpscale",
            "ConditioningUpscaleSimple",
            "ConditioningStretch",
            "ConditioningStretchSimple",
            "ConditioningMultiply",
            "ConditioningMultiplySimple",
            "ConditioningNormalize",
            "ConditioningNormalizeSimple",
            "ConditioningConcat",
            "ConditioningConcatSimple",
            "ConditioningBlend",
            "ConditioningBlendSimple",
            "ConditioningMix",
            "ConditioningMixSimple",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(conditioning_node in class_type for conditioning_node in inspire_conditioning_nodes):
                widgets = node_data.get("widgets_values", [])
                conditioning_nodes[node_id] = {
                    "type": class_type,
                    "widgets": widgets,
                    "node_id": node_id,
                }

        return conditioning_nodes

    def detect_inspire_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this workflow uses Inspire Pack nodes."""
        if not isinstance(data, dict):
            return False

        prompt_data = data.get("prompt", data)

        # Look for Inspire Pack indicators
        inspire_indicators = [
            "Regional",
            "Batch",
            "Wildcard",
            "GlobalSeed",
            "PromptBuilder",
            "PromptExtractor",
            "StringFunction",
            "MathFunction",
            "CacheBackend",
            "LoadPrompts",
            "SavePrompts",
            "CheckpointName",
            "ModelName",
            "LoraName",
            "VaeName",
            "ImageBatch",
            "LatentBatch",
            "KSamplerInspire",
            "InspireSampler",
            "DualCLIP",
            "UnCLIPCheckpoint",
            "DifferentialDiffusion",
            "HyperTile",
            "CLIPTextEncodeWithWeight",
            "ConditioningUpscale",
            "ConditioningStretch",
            "ConditioningMultiply",
            "ConditioningNormalize",
            "ConditioningConcat",
            "ConditioningBlend",
            "ConditioningMix",
        ]

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if any(indicator in class_type for indicator in inspire_indicators):
                return True

        # Also check properties for Inspire cnr_id
        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            properties = node_data.get("properties", {})
            if isinstance(properties, dict):
                cnr_id = properties.get("cnr_id", "")
                if "inspire" in cnr_id.lower():
                    return True

        return False

    def extract_inspire_workflow_summary(self, data: dict) -> dict[str, Any]:
        """Extract comprehensive Inspire Pack workflow summary."""
        if not isinstance(data, dict):
            return {}

        summary = {
            "is_inspire_workflow": self.detect_inspire_workflow(data, {}, {}, {}),
            "regional_prompts": self._extract_regional_prompts(data, {}, {}, {}),
            "batch_nodes": self._extract_batch_nodes(data, {}, {}, {}),
            "utility_nodes": self._extract_utility_nodes(data, {}, {}, {}),
            "sampler_nodes": self._extract_sampler_nodes(data, {}, {}, {}),
            "conditioning_nodes": self._extract_conditioning_nodes(data, {}, {}, {}),
        }

        return summary

    def get_inspire_nodes(self, data: dict) -> dict[str, dict]:
        """Get all Inspire Pack nodes in the workflow."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        inspire_nodes = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if self._is_inspire_node(class_type):
                inspire_nodes[node_id] = {
                    "type": class_type,
                    "widgets": node_data.get("widgets_values", []),
                    "inputs": node_data.get("inputs", {}),
                    "outputs": node_data.get("outputs", []),
                }

        return inspire_nodes

    def _is_inspire_node(self, class_type: str) -> bool:
        """Check if a class type is an Inspire Pack node."""
        inspire_indicators = [
            "Regional",
            "Batch",
            "Wildcard",
            "GlobalSeed",
            "PromptBuilder",
            "PromptExtractor",
            "StringFunction",
            "MathFunction",
            "CacheBackend",
            "LoadPrompts",
            "SavePrompts",
            "CheckpointName",
            "ModelName",
            "LoraName",
            "VaeName",
            "ImageBatch",
            "LatentBatch",
            "KSamplerInspire",
            "InspireSampler",
            "DualCLIP",
            "UnCLIPCheckpoint",
            "DifferentialDiffusion",
            "HyperTile",
            "CLIPTextEncodeWithWeight",
            "ConditioningUpscale",
            "ConditioningStretch",
            "ConditioningMultiply",
            "ConditioningNormalize",
            "ConditioningConcat",
            "ConditioningBlend",
            "ConditioningMix",
        ]

        return any(indicator in class_type for indicator in inspire_indicators)

    def extract_inspire_prompts(self, data: dict) -> dict[str, str]:
        """Extract all prompts from Inspire Pack nodes."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        prompts = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if self._is_inspire_node(class_type) and any(
                keyword in class_type for keyword in ["Prompt", "Regional", "Wildcard", "Text"]
            ):
                widgets = node_data.get("widgets_values", [])
                for i, widget in enumerate(widgets):
                    if isinstance(widget, str) and len(widget.strip()) > 0:
                        prompts[f"{class_type}_{node_id}_{i}"] = widget.strip()

        return prompts

    def get_inspire_regional_info(self, data: dict) -> dict[str, Any]:
        """Get information about regional prompting setup."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        regional_info = {
            "regional_nodes": 0,
            "regional_masks": 0,
            "regional_prompts": 0,
            "regional_types": set(),
        }

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "Regional" in class_type:
                regional_info["regional_nodes"] += 1

                if "Mask" in class_type:
                    regional_info["regional_masks"] += 1
                    regional_info["regional_types"].add("mask")

                if "Prompt" in class_type:
                    regional_info["regional_prompts"] += 1
                    regional_info["regional_types"].add("prompt")

                if "ColorMask" in class_type:
                    regional_info["regional_types"].add("color_mask")

                if "IPAdapter" in class_type:
                    regional_info["regional_types"].add("ip_adapter")

                if "ControlNet" in class_type:
                    regional_info["regional_types"].add("controlnet")

        # Convert set to list for JSON serialization
        regional_info["regional_types"] = list(regional_info["regional_types"])

        return regional_info

    def get_inspire_batch_info(self, data: dict) -> dict[str, Any]:
        """Get information about batch processing setup."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        batch_info = {
            "batch_nodes": 0,
            "batch_types": set(),
            "schedule_nodes": 0,
            "interpolation_nodes": 0,
        }

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "Batch" in class_type:
                batch_info["batch_nodes"] += 1

                if "Schedule" in class_type:
                    batch_info["schedule_nodes"] += 1
                    batch_info["batch_types"].add("schedule")

                if "Interpolation" in class_type:
                    batch_info["interpolation_nodes"] += 1
                    batch_info["batch_types"].add("interpolation")

                if "Prompt" in class_type:
                    batch_info["batch_types"].add("prompt")

                if "Value" in class_type:
                    batch_info["batch_types"].add("value")

                if "Image" in class_type:
                    batch_info["batch_types"].add("image")

                if "Latent" in class_type:
                    batch_info["batch_types"].add("latent")

        # Convert set to list for JSON serialization
        batch_info["batch_types"] = list(batch_info["batch_types"])

        return batch_info
