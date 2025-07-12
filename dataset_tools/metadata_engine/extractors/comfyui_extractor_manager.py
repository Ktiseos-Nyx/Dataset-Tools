# dataset_tools/metadata_engine/extractors/comfyui_extractor_manager.py

"""ComfyUI Extractor Manager.

Unified manager for all ComfyUI extractors, providing centralized access
to all extraction methods and automatic workflow detection.
"""

import logging
from collections.abc import Callable
from typing import Any

from .comfyui_animatediff import ComfyUIAnimateDiffExtractor
from .comfyui_complexity import ComfyUIComplexityExtractor
from .comfyui_controlnet import ComfyUIControlNetExtractor
from .comfyui_dynamicprompts import ComfyUIDynamicPromptsExtractor
from .comfyui_efficiency import ComfyUIEfficiencyExtractor
from .comfyui_flux import ComfyUIFluxExtractor
from .comfyui_impact import ComfyUIImpactExtractor
from .comfyui_inspire import ComfyUIInspireExtractor
from .comfyui_node_checker import ComfyUINodeChecker
from .comfyui_pixart import ComfyUIPixArtExtractor
from .comfyui_rgthree import ComfyUIRGthreeExtractor
from .comfyui_sdxl import ComfyUISDXLExtractor

# --- FIX: Corrected typo from "Searche" to "Searge" ---
from .comfyui_searge import ComfyUISeargeExtractor

# Import all the specialized extractors
from .comfyui_traversal import ComfyUITraversalExtractor
from .comfyui_was import ComfyUIWASExtractor

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIExtractorManager:
    """Unified manager for all ComfyUI extractors."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the extractor manager."""
        self.logger = logger

        # Initialize all extractors
        self.traversal = ComfyUITraversalExtractor(logger)
        self.node_checker = ComfyUINodeChecker(logger)
        self.complexity = ComfyUIComplexityExtractor(logger)
        self.flux = ComfyUIFluxExtractor(logger)
        self.sdxl = ComfyUISDXLExtractor(logger)
        self.impact = ComfyUIImpactExtractor(logger)
        self.efficiency = ComfyUIEfficiencyExtractor(logger)
        self.was = ComfyUIWASExtractor(logger)
        self.pixart = ComfyUIPixArtExtractor(logger)
        self.animatediff = ComfyUIAnimateDiffExtractor(logger)
        self.controlnet = ComfyUIControlNetExtractor(logger)
        # --- FIX: Corrected typo from "Searche" to "Searge" ---
        self.searge = ComfyUISeargeExtractor(logger)
        self.rgthree = ComfyUIRGthreeExtractor(logger)
        self.inspire = ComfyUIInspireExtractor(logger)
        self.dynamicprompts = ComfyUIDynamicPromptsExtractor(logger)

        # Cache for detected workflow types
        self._workflow_type_cache: dict[str, list[str]] = {}

    def get_methods(self) -> dict[str, Callable]:
        """Return unified dictionary of all extraction methods."""
        methods = {}

        # Add methods from all extractors
        methods.update(
            self.traversal.get_methods()
            if hasattr(self.traversal, "get_methods")
            else {}
        )
        methods.update(
            self.node_checker.get_methods()
            if hasattr(self.node_checker, "get_methods")
            else {}
        )
        methods.update(self.complexity.get_methods())
        methods.update(self.flux.get_methods())
        methods.update(self.sdxl.get_methods())
        methods.update(self.impact.get_methods())
        methods.update(self.efficiency.get_methods())
        methods.update(self.was.get_methods())
        methods.update(self.pixart.get_methods())
        methods.update(self.animatediff.get_methods())
        methods.update(self.controlnet.get_methods())
        methods.update(self.searge.get_methods())
        methods.update(self.rgthree.get_methods())
        methods.update(self.inspire.get_methods())
        methods.update(self.dynamicprompts.get_methods())

        # Add manager-specific methods
        methods.update(
            {
                "comfy_auto_detect_workflow": self._auto_detect_workflow,
                "comfy_extract_comprehensive_summary": self._extract_comprehensive_summary,
                "comfy_get_workflow_metadata": self._get_workflow_metadata,
                "comfy_extract_smart_prompt": self._extract_smart_prompt,
                "comfy_extract_all_ecosystems": self._extract_all_ecosystems,
                # Missing methods that parsers are looking for
                "comfyui_detect_tipo_enhancement": self._detect_tipo_enhancement,
                "comfyui_calculate_workflow_complexity": self._calculate_workflow_complexity,
                "comfyui_detect_advanced_upscaling": self._detect_advanced_upscaling,
                "comfyui_detect_multi_stage_conditioning": self._detect_multi_stage_conditioning,
                "comfyui_detect_post_processing_effects": self._detect_post_processing_effects,
                "comfyui_detect_custom_node_ecosystems": self._detect_custom_node_ecosystems,
                "comfyui_extract_workflow_techniques": self._extract_workflow_techniques,
            }
        )

        return methods

    def _auto_detect_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list[str]:
        """Automatically detect workflow types and ecosystems."""
        if not isinstance(data, dict):
            return []

        # Use cache key based on data structure
        cache_key = str(hash(str(sorted(data.keys()))))
        if cache_key in self._workflow_type_cache:
            return self._workflow_type_cache[cache_key]

        workflow_types = []

        # Check architecture types
        if self.flux._detect_flux_workflow(data, {}, {}, {}):
            workflow_types.append("flux")

        if self.sdxl._detect_sdxl_workflow(data, {}, {}, {}):
            workflow_types.append("sdxl")

        if self.pixart._detect_pixart_workflow(data, {}, {}, {}):
            workflow_types.append("pixart")

        # Check ecosystem types
        if self.impact._detect_impact_workflow(data, {}, {}, {}):
            workflow_types.append("impact")

        if self.efficiency._detect_efficiency_workflow(data, {}, {}, {}):
            workflow_types.append("efficiency")

        if self.was._detect_was_workflow(data, {}, {}, {}):
            workflow_types.append("was")

        if self.animatediff._detect_animatediff_workflow(data, {}, {}, {}):
            workflow_types.append("animatediff")

        if self.controlnet._detect_controlnet_workflow(data, {}, {}, {}):
            workflow_types.append("controlnet")

        if self.searge._detect_searge_workflow(data, {}, {}, {}):
            workflow_types.append("searge")

        if self.rgthree._detect_rgthree_workflow(data, {}, {}, {}):
            workflow_types.append("rgthree")

        if self.inspire._detect_inspire_workflow(data, {}, {}, {}):
            workflow_types.append("inspire")

        if self.dynamicprompts._detect_dynamicprompts_workflow(data, {}, {}, {}):
            workflow_types.append("dynamicprompts")

        # Cache the result
        self._workflow_type_cache[cache_key] = workflow_types

        return workflow_types

    def _extract_comprehensive_summary(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract comprehensive summary using all appropriate extractors."""
        if not isinstance(data, dict):
            return {}

        summary = {
            "workflow_types": self._auto_detect_workflow(
                data, method_def, context, fields
            ),
            "complexity_analysis": self.complexity._analyze_workflow_complexity(
                data, method_def, context, fields
            ),
            "architecture_summaries": {},
            "ecosystem_summaries": {},
            "node_analysis": {},
        }

        # Extract architecture-specific summaries
        workflow_types = summary["workflow_types"]

        if "flux" in workflow_types:
            summary["architecture_summaries"]["flux"] = (
                self.flux.extract_flux_workflow_summary(data)
            )

        if "sdxl" in workflow_types:
            summary["architecture_summaries"]["sdxl"] = (
                self.sdxl.extract_sdxl_workflow_summary(data)
            )

        if "pixart" in workflow_types:
            summary["architecture_summaries"]["pixart"] = (
                self.pixart.extract_pixart_workflow_summary(data)
            )

        # Extract ecosystem-specific summaries
        if "impact" in workflow_types:
            summary["ecosystem_summaries"]["impact"] = (
                self.impact.extract_impact_workflow_summary(data)
            )

        if "efficiency" in workflow_types:
            summary["ecosystem_summaries"]["efficiency"] = (
                self.efficiency.extract_efficiency_workflow_summary(data)
            )

        if "was" in workflow_types:
            summary["ecosystem_summaries"]["was"] = (
                self.was.extract_was_workflow_summary(data)
            )

        if "animatediff" in workflow_types:
            summary["ecosystem_summaries"]["animatediff"] = (
                self.animatediff.extract_animatediff_workflow_summary(data)
            )

        if "controlnet" in workflow_types:
            summary["ecosystem_summaries"]["controlnet"] = (
                self.controlnet.extract_controlnet_workflow_summary(data)
            )

        if "searge" in workflow_types:
            summary["ecosystem_summaries"]["searge"] = (
                self.searge.extract_searge_workflow_summary(data)
            )

        if "rgthree" in workflow_types:
            summary["ecosystem_summaries"]["rgthree"] = (
                self.rgthree.extract_rgthree_workflow_summary(data)
            )

        if "inspire" in workflow_types:
            summary["ecosystem_summaries"]["inspire"] = (
                self.inspire.extract_inspire_workflow_summary(data)
            )

        if "dynamicprompts" in workflow_types:
            summary["ecosystem_summaries"]["dynamicprompts"] = (
                self.dynamicprompts.extract_dynamicprompts_workflow_summary(data)
            )

        # Node analysis
        nodes = self.traversal.get_nodes_from_data(data)
        summary["node_analysis"] = {
            "total_nodes": len(nodes) if isinstance(nodes, (dict, list)) else 0,
            "node_types": self._get_node_type_distribution(nodes),
            "custom_nodes": self._get_custom_node_info(nodes),
        }

        return summary

    def _get_workflow_metadata(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract workflow metadata using node checker."""
        if not isinstance(data, dict):
            return {}

        nodes = self.traversal.get_nodes_from_data(data)
        metadata = {
            "workflow_info": {
                "format": "workflow" if "nodes" in data else "prompt",
                "has_links": "links" in data,
                "has_version": "version" in data,
                "has_extra": "extra" in data,
            },
            "node_ecosystems": {},
            "complexity_metrics": {},
        }

        # Analyze node ecosystems
        ecosystem_counts = {}
        for node_id, node_data in (
            nodes.items() if isinstance(nodes, dict) else enumerate(nodes)
        ):
            if isinstance(node_data, dict):
                ecosystem = self.node_checker.get_node_ecosystem(node_data)
                ecosystem_counts[ecosystem] = ecosystem_counts.get(ecosystem, 0) + 1

        metadata["node_ecosystems"] = ecosystem_counts

        # Complexity metrics
        metadata["complexity_metrics"] = self.complexity._analyze_workflow_complexity(
            data, method_def, context, fields
        )

        return metadata

    def _parse_json_data(self, data: Any) -> Any:
        """Helper to parse JSON string data if needed."""
        if isinstance(data, str):
            try:
                import json

                return json.loads(data)
            except (json.JSONDecodeError, ValueError):
                self.logger.warning("[MANAGER] Failed to parse workflow JSON string.")
                return {}
        return data

    def _extract_smart_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Intelligently extract the most relevant prompt using workflow detection."""
        data = self._parse_json_data(data)  # PARSE DATA HERE
        if not isinstance(data, dict):
            return ""

        workflow_types = self._auto_detect_workflow(data, method_def, context, fields)

        # Try architecture-specific extraction first
        if "flux" in workflow_types:
            # For FLUX, prefer T5 prompt
            t5_prompt = self.flux._extract_t5_prompt(data, method_def, context, fields)
            if t5_prompt:
                return t5_prompt

            # Fallback to CLIP prompt
            clip_prompt = self.flux._extract_clip_prompt(
                data, method_def, context, fields
            )
            if clip_prompt:
                return clip_prompt

        if "sdxl" in workflow_types:
            # For SDXL, try positive prompt extraction
            positive_prompt = self.sdxl._extract_positive_prompt(
                data, method_def, context, fields
            )
            if positive_prompt:
                return positive_prompt

        if "pixart" in workflow_types:
            # For PixArt, try T5 prompt
            t5_prompt = self.pixart._extract_t5_prompt(
                data, method_def, context, fields
            )
            if t5_prompt:
                return t5_prompt

        # Try ecosystem-specific extraction
        if "impact" in workflow_types:
            # For Impact workflows, try wildcard prompt
            wildcard_prompt = self.impact._extract_wildcard_prompt(
                data, method_def, context, fields
            )
            if wildcard_prompt:
                return wildcard_prompt

        # Try complexity-based extraction
        dynamic_prompt = self.complexity._extract_dynamic_prompt_from_workflow(
            data, method_def, context, fields
        )
        if dynamic_prompt:
            return dynamic_prompt

        # Fallback to traversal-based extraction
        nodes = self.traversal.get_nodes_from_data(data)
        if nodes:
            # Find the first text node and trace its flow
            for node_id, node_data in (
                nodes.items() if isinstance(nodes, dict) else enumerate(nodes)
            ):
                if isinstance(node_data, dict) and self.node_checker.is_text_node(
                    node_data
                ):
                    traced_text = self.traversal.trace_text_flow(nodes, str(node_id))
                    if traced_text:
                        return traced_text

        return ""

    def _extract_all_ecosystems(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract information from all detected ecosystems."""
        if not isinstance(data, dict):
            return {}

        ecosystems = {}

        # Check each ecosystem
        extractors = [
            ("impact", self.impact),
            ("efficiency", self.efficiency),
            ("was", self.was),
            ("animatediff", self.animatediff),
            ("controlnet", self.controlnet),
            ("searge", self.searge),
            ("rgthree", self.rgthree),
            ("inspire", self.inspire),
            ("dynamicprompts", self.dynamicprompts),
        ]

        for ecosystem_name, extractor in extractors:
            # Check if this ecosystem is present
            detect_method = getattr(
                extractor, f"_detect_{ecosystem_name}_workflow", None
            )
            if detect_method and detect_method(data, {}, {}, {}):
                # Extract ecosystem-specific information
                summary_method = getattr(
                    extractor, f"extract_{ecosystem_name}_workflow_summary", None
                )
                if summary_method:
                    ecosystems[ecosystem_name] = summary_method(data)

        return ecosystems

    def _get_node_type_distribution(self, nodes: Any) -> dict[str, int]:
        """Get distribution of node types in the workflow."""
        if not nodes:
            return {}

        type_counts = {}
        node_items = nodes.items() if isinstance(nodes, dict) else enumerate(nodes)

        for node_id, node_data in node_items:
            if isinstance(node_data, dict):
                node_type = node_data.get(
                    "class_type", node_data.get("type", "unknown")
                )
                type_counts[node_type] = type_counts.get(node_type, 0) + 1

        return type_counts

    def _get_custom_node_info(self, nodes: Any) -> dict[str, Any]:
        """Get information about custom nodes in the workflow."""
        if not nodes:
            return {}

        custom_info = {
            "total_custom_nodes": 0,
            "ecosystems": {},
            "custom_node_types": set(),
        }

        node_items = nodes.items() if isinstance(nodes, dict) else enumerate(nodes)

        for node_id, node_data in node_items:
            if isinstance(node_data, dict):
                if self.node_checker.is_custom_node(node_data):
                    custom_info["total_custom_nodes"] += 1

                    ecosystem = self.node_checker.get_node_ecosystem(node_data)
                    custom_info["ecosystems"][ecosystem] = (
                        custom_info["ecosystems"].get(ecosystem, 0) + 1
                    )

                    node_type = node_data.get(
                        "class_type", node_data.get("type", "unknown")
                    )
                    custom_info["custom_node_types"].add(node_type)

        # Convert set to list for JSON serialization
        custom_info["custom_node_types"] = list(custom_info["custom_node_types"])

        return custom_info

    def get_extractor_for_workflow(self, data: dict[str, Any]) -> Any | None:
        """Get the most appropriate extractor for a workflow."""
        workflow_types = self._auto_detect_workflow(data, {}, {}, {})

        # Return the most specific extractor
        if "flux" in workflow_types:
            return self.flux
        if "sdxl" in workflow_types:
            return self.sdxl
        if "pixart" in workflow_types:
            return self.pixart
        if "impact" in workflow_types:
            return self.impact
        if "efficiency" in workflow_types:
            return self.efficiency
        if "was" in workflow_types:
            return self.was
        if "animatediff" in workflow_types:
            return self.animatediff
        if "controlnet" in workflow_types:
            return self.controlnet
        return self.complexity  # Default to complexity extractor

    def clear_cache(self) -> None:
        """Clear the workflow type detection cache."""
        self._workflow_type_cache.clear()

    def get_available_extractors(self) -> list[str]:
        """Get list of available extractor names."""
        return [
            "traversal",
            "node_checker",
            "complexity",
            "flux",
            "sdxl",
            "impact",
            "efficiency",
            "was",
            "pixart",
            "animatediff",
            "controlnet",
            "searge",
            "rgthree",
            "inspire",
            "dynamicprompts",
        ]

    def get_extractor_stats(self) -> dict[str, Any]:
        """Get statistics about available extractors."""
        stats = {
            "total_extractors": len(self.get_available_extractors()),
            "total_methods": len(self.get_methods()),
            "architecture_extractors": ["flux", "sdxl", "pixart"],
            "ecosystem_extractors": [
                "impact",
                "efficiency",
                "was",
                "animatediff",
                "controlnet",
                "searge",
                "rgthree",
                "inspire",
                "dynamicprompts",
            ],
            "utility_extractors": ["traversal", "node_checker", "complexity"],
        }

        return stats

    # Missing methods that parsers are looking for
    def _detect_tipo_enhancement(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if workflow uses TIPO enhancement nodes."""
        if not isinstance(data, dict):
            return False

        prompt_data = data.get("prompt", data)
        nodes = self.traversal.get_nodes_from_data(data)

        # Look for TIPO nodes specifically
        tipo_indicators = [
            "TIPO",
            "Tags Input",
            "Ban Tags",
            "NL input",
            "Base Prompt",
            "2D_aesthetic",
            "animetune",
        ]

        for node_id, node_data in (
            nodes.items() if isinstance(nodes, dict) else enumerate(nodes)
        ):
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))
                node_name = node_data.get("name", "")

                # Check both class type and node name for TIPO indicators
                if any(indicator in class_type for indicator in tipo_indicators) or any(
                    indicator in node_name for indicator in tipo_indicators
                ):
                    return True

        return False

    def _calculate_workflow_complexity(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Calculate workflow complexity metrics."""
        return self.complexity._analyze_workflow_complexity(
            data, method_def, context, fields
        )

    def _detect_advanced_upscaling(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if workflow uses advanced upscaling techniques."""
        if not isinstance(data, dict):
            return False

        nodes = self.traversal.get_nodes_from_data(data)

        # Look for upscaling indicators
        upscaling_indicators = [
            "Upscale",
            "ImageUpscale",
            "UpscaleModel",
            "ESRGAN",
            "RealESRGAN",
            "Ultimate",
            "UltimateSDUpscale",
            "TileUpscale",
            "IterativeUpscale",
            "ImageSharpen",
            "ProPostFilmGrain",
            "ImageScaleBy",
            "2x-",
            "4x-",
        ]

        upscaling_count = 0
        for node_id, node_data in (
            nodes.items() if isinstance(nodes, dict) else enumerate(nodes)
        ):
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))

                if any(indicator in class_type for indicator in upscaling_indicators):
                    upscaling_count += 1

                # Check widget values for upscaling models
                widgets = node_data.get("widgets_values", [])
                for widget in widgets:
                    if isinstance(widget, str) and any(
                        indicator in widget
                        for indicator in ["2x-", "4x-", "upscale", "ESRGAN"]
                    ):
                        upscaling_count += 1

        return upscaling_count > 0

    def _detect_multi_stage_conditioning(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if workflow uses multi-stage conditioning."""
        if not isinstance(data, dict):
            return False

        nodes = self.traversal.get_nodes_from_data(data)

        # Look for multi-stage conditioning indicators
        conditioning_indicators = [
            "ConditioningConcat",
            "ConditioningCombine",
            "ConditioningAverage",
            "ConditioningSetArea",
            "ConditioningSetMask",
            "ConditioningMultiply",
            "CLIPTextEncode",
            "CLIPTextEncodeSDXL",
            "DualCLIP",
            "MultiConditioning",
        ]

        conditioning_count = 0
        for node_id, node_data in (
            nodes.items() if isinstance(nodes, dict) else enumerate(nodes)
        ):
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))

                if any(
                    indicator in class_type for indicator in conditioning_indicators
                ):
                    conditioning_count += 1

        # Multi-stage if more than 2 conditioning nodes
        return conditioning_count > 2

    def _detect_post_processing_effects(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if workflow uses post-processing effects."""
        if not isinstance(data, dict):
            return False

        nodes = self.traversal.get_nodes_from_data(data)

        # Look for post-processing indicators
        post_processing_indicators = [
            "ImageSharpen",
            "ImageBlur",
            "ImageFilter",
            "ColorCorrect",
            "ProPostFilmGrain",
            "ImageEnhance",
            "ImageAdjust",
            "ImageFX",
            "PostProcess",
            "FilmGrain",
            "ColorGrading",
            "Denoise",
            "FreeU",
            "ImageNormalize",
            "ImageContrast",
        ]

        for node_id, node_data in (
            nodes.items() if isinstance(nodes, dict) else enumerate(nodes)
        ):
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))

                if any(
                    indicator in class_type for indicator in post_processing_indicators
                ):
                    return True

        return False

    def _detect_custom_node_ecosystems(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list[str]:
        """Detect custom node ecosystems in use."""
        if not isinstance(data, dict):
            return []

        return self._auto_detect_workflow(data, method_def, context, fields)

    def _extract_workflow_techniques(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list[str]:
        """Extract workflow techniques being used."""
        if not isinstance(data, dict):
            return []

        techniques = []

        # Check for various techniques
        if self._detect_tipo_enhancement(data, method_def, context, fields):
            techniques.append("tipo_enhancement")

        if self._detect_advanced_upscaling(data, method_def, context, fields):
            techniques.append("advanced_upscaling")

        if self._detect_multi_stage_conditioning(data, method_def, context, fields):
            techniques.append("multi_stage_conditioning")

        if self._detect_post_processing_effects(data, method_def, context, fields):
            techniques.append("post_processing_effects")

        # Check for workflow types
        workflow_types = self._auto_detect_workflow(data, method_def, context, fields)
        techniques.extend(workflow_types)

        return techniques

    def _extract_generic_parameters(self, data: dict) -> dict:
        """Generic fallback to find basic sampler parameters."""
        nodes = self.traversal.get_nodes_from_data(data)
        if not nodes:
            return {}

        for node_id, node_data in (
            nodes.items() if isinstance(nodes, dict) else enumerate(nodes)
        ):
            if isinstance(node_data, dict) and self.node_checker.is_sampler_node(
                node_data
            ):
                inputs = node_data.get("inputs", {})
                if isinstance(inputs, dict):
                    return {
                        "seed": inputs.get("seed"),
                        "steps": inputs.get("steps"),
                        "cfg": inputs.get("cfg"),
                        "sampler_name": inputs.get("sampler_name"),
                        "scheduler": inputs.get("scheduler"),
                        "denoise": inputs.get("denoise"),
                    }
        return {}
