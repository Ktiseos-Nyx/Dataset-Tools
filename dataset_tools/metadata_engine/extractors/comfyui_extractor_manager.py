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
from .comfyui_pixart import ComfyUIPixArtExtractor
from .comfyui_quadmoons import ComfyUIQuadMoonsExtractor
from .comfyui_rgthree import ComfyUIRGthreeExtractor
from .comfyui_sdxl import ComfyUISDXLExtractor
from .comfyui_searge import ComfyUISeargeExtractor
from .comfyui_was import ComfyUIWASExtractor
from .comfyui_workflow_analyzer import ComfyUIWorkflowAnalyzer  # New Analyzer

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIExtractorManager:
    """Unified manager for all ComfyUI extractors."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the extractor manager."""
        self.logger = logger

        # Initialize the new comprehensive workflow analyzer
        self.workflow_analyzer = ComfyUIWorkflowAnalyzer(logger)

        # Initialize other specialized extractors (some might become redundant later)
        self.complexity = ComfyUIComplexityExtractor(logger)
        self.flux = ComfyUIFluxExtractor(logger)
        self.sdxl = ComfyUISDXLExtractor(logger)
        self.impact = ComfyUIImpactExtractor(logger)
        self.efficiency = ComfyUIEfficiencyExtractor(logger)
        self.was = ComfyUIWASExtractor(logger)
        self.pixart = ComfyUIPixArtExtractor(logger)
        self.animatediff = ComfyUIAnimateDiffExtractor(logger)
        self.controlnet = ComfyUIControlNetExtractor(logger)
        self.searge = ComfyUISeargeExtractor(logger)
        self.rgthree = ComfyUIRGthreeExtractor(logger)
        self.inspire = ComfyUIInspireExtractor(logger)
        self.dynamicprompts = ComfyUIDynamicPromptsExtractor(logger)
        self.quadmoons = ComfyUIQuadMoonsExtractor(logger)

        # Cache for detected workflow types (might be managed by analyzer now)
        self._workflow_type_cache: dict[str, list[str]] = {}

    def get_methods(self) -> dict[str, Callable]:
        """Return unified dictionary of all extraction methods."""
        methods = {}

        # Collect methods from all specialized extractors
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
        methods.update(self.quadmoons.get_methods())

        # Add workflow analyzer methods if needed
        # methods.update(self.workflow_analyzer.get_methods())

        # Add missing methods that parser definitions are looking for
        methods.update(
            {
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
        """Automatically detect workflow types and ecosystems using the new analyzer."""
        if not isinstance(data, dict):
            return []

        # The new analyzer handles comprehensive detection
        analysis_result = self.workflow_analyzer.analyze_workflow(data)

        if not analysis_result.get("is_valid_workflow", False):
            return []

        detected_types = []
        # Extract workflow types from the analysis result
        for gen_pass in analysis_result.get("generation_passes", []):
            sampler_type = gen_pass.get("sampler_node_type", "").lower()
            if "flux" in sampler_type:
                detected_types.append("flux")
            if "sdxl" in sampler_type:
                detected_types.append("sdxl")
            if "pixart" in sampler_type:
                detected_types.append("pixart")
            # Add other architecture detections based on sampler_type or other indicators

        # Add custom node ecosystems detected by the analyzer
        custom_nodes_used = analysis_result.get("custom_nodes_used", {})
        for node_type in custom_nodes_used.keys():
            # This is a simplified mapping, can be expanded based on actual node types
            if "Impact" in node_type:
                detected_types.append("impact")
            if "Efficiency" in node_type:
                detected_types.append("efficiency")
            if "WAS" in node_type:
                detected_types.append("was")
            if "AnimateDiff" in node_type:
                detected_types.append("animatediff")
            if "ControlNet" in node_type:
                detected_types.append("controlnet")
            if "Searge" in node_type:
                detected_types.append("searge")
            if "RGThree" in node_type:
                detected_types.append("rgthree")
            if "Inspire" in node_type:
                detected_types.append("inspire")
            if "DynamicPrompts" in node_type:
                detected_types.append("dynamicprompts")

        return list(set(detected_types))  # Return unique types

    def _extract_comprehensive_summary(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract comprehensive summary using the new workflow analyzer."""
        if not isinstance(data, dict):
            return {}

        analysis_result = self.workflow_analyzer.analyze_workflow(data)

        summary = {
            "is_valid_workflow": analysis_result.get("is_valid_workflow", False),
            "error": analysis_result.get("error"),
            "node_count": analysis_result.get("node_count", 0),
            "link_count": analysis_result.get("link_count", 0),
            "generation_passes": analysis_result.get("generation_passes", []),
            "custom_nodes_used": analysis_result.get("custom_nodes_used", {}),
            "workflow_types": self._auto_detect_workflow(data, method_def, context, fields),  # Keep for compatibility
            "complexity_analysis": self.complexity.analyze_workflow_complexity(
                data, method_def, context, fields
            ),  # Keep for now
            "architecture_summaries": {},
            "ecosystem_summaries": {},
            "node_analysis": {},
        }

        # Populate architecture and ecosystem summaries from generation passes
        for gen_pass in summary["generation_passes"]:
            sampler_type = gen_pass.get("sampler_node_type", "").lower()
            if "flux" in sampler_type:
                summary["architecture_summaries"]["flux"] = gen_pass
            if "sdxl" in sampler_type:
                summary["architecture_summaries"]["sdxl"] = gen_pass
            if "pixart" in sampler_type:
                summary["architecture_summaries"]["pixart"] = gen_pass

            # This part might need more granular mapping based on what each ecosystem extractor provides
            # For now, we'll just indicate presence based on custom nodes used
            for node_type, count in summary["custom_nodes_used"].items():
                if "Impact" in node_type:
                    summary["ecosystem_summaries"]["impact"] = {"nodes_used": count}
                if "Efficiency" in node_type:
                    summary["ecosystem_summaries"]["efficiency"] = {"nodes_used": count}
                # ... and so on for other ecosystems

        # Node analysis from the new analyzer
        summary["node_analysis"] = {
            "total_nodes": summary["node_count"],
            "node_types": analysis_result.get(
                "node_types_found", []
            ),  # This might need to be re-calculated from custom_nodes_used
            "custom_nodes": analysis_result.get("custom_nodes_used", {}),
        }

        return summary

    def _get_workflow_metadata(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract workflow metadata using the new analyzer."""
        if not isinstance(data, dict):
            return {}

        analysis_result = self.workflow_analyzer.analyze_workflow(data)

        metadata = {
            "workflow_info": {
                "format": ("workflow" if analysis_result.get("is_valid_workflow") else "prompt"),
                "node_count": analysis_result.get("node_count", 0),
                "link_count": analysis_result.get("link_count", 0),
                "has_links": analysis_result.get("link_count", 0) > 0,
                "has_version": "version" in data,  # Still check raw data for version
                "has_extra": "extra" in data,  # Still check raw data for extra
            },
            "node_ecosystems": analysis_result.get("custom_nodes_used", {}),  # Use custom_nodes_used from analyzer
            "complexity_metrics": self.complexity.analyze_workflow_complexity(data, method_def, context, fields),
            "generation_passes_summary": analysis_result.get("generation_passes", []),
        }

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
            t5_prompt = self.flux.extract_t5_prompt(data, method_def, context, fields)
            if t5_prompt:
                return t5_prompt

            # Fallback to CLIP prompt
            clip_prompt = self.flux.extract_clip_prompt(data, method_def, context, fields)
            if clip_prompt:
                return clip_prompt

        if "sdxl" in workflow_types:
            # For SDXL, try positive prompt extraction
            positive_prompt = self.sdxl.extract_positive_prompt(data, method_def, context, fields)
            if positive_prompt:
                return positive_prompt

        if "pixart" in workflow_types:
            # For PixArt, try T5 prompt
            t5_prompt = self.pixart.extract_t5_prompt(data, method_def, context, fields)
            if t5_prompt:
                return t5_prompt

        # Try ecosystem-specific extraction
        if "impact" in workflow_types:
            # For Impact workflows, try wildcard prompt
            wildcard_prompt = self.impact.extract_wildcard_prompt(data, method_def, context, fields)
            if wildcard_prompt:
                return wildcard_prompt

        # Try complexity-based extraction
        dynamic_prompt = self.complexity.extract_dynamic_prompt_from_workflow(data, method_def, context, fields)
        if dynamic_prompt:
            return dynamic_prompt

        # Fallback to workflow analyzer extraction
        analysis_result = self.workflow_analyzer.analyze_workflow(data)
        if analysis_result.get("is_valid_workflow", False):
            # Extract prompt from generation passes
            for gen_pass in analysis_result.get("generation_passes", []):
                positive_prompt = gen_pass.get("positive_prompt")
                if positive_prompt:
                    return positive_prompt

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
            detect_method = getattr(extractor, f"detect_{ecosystem_name}_workflow", None)
            if detect_method and detect_method(data, {}, {}, {}):
                # Extract ecosystem-specific information
                summary_method = getattr(extractor, f"extract_{ecosystem_name}_workflow_summary", None)
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
                node_type = node_data.get("class_type", node_data.get("type", "unknown"))
                type_counts[node_type] = type_counts.get(node_type, 0) + 1

        return type_counts

    def _get_custom_node_info(self, workflow_data: Any) -> dict[str, Any]:
        """Get information about custom nodes in the workflow using workflow analyzer."""
        if not isinstance(workflow_data, dict):
            return {}

        # Use workflow analyzer to get custom node information
        analysis_result = self.workflow_analyzer.analyze_workflow(workflow_data)
        custom_nodes_used = analysis_result.get("custom_nodes_used", {})

        custom_info = {
            "total_custom_nodes": sum(custom_nodes_used.values()),
            "ecosystems": {},
            "custom_node_types": list(custom_nodes_used.keys()),
        }

        # Map node types to ecosystems (simplified mapping)
        for node_type in custom_nodes_used.keys():
            ecosystem = "unknown"
            if "Impact" in node_type:
                ecosystem = "impact"
            elif "Efficiency" in node_type:
                ecosystem = "efficiency"
            elif "WAS" in node_type:
                ecosystem = "was"
            elif "Inspire" in node_type:
                ecosystem = "inspire"
            elif "quadMoons" in node_type or "KSampler - Extra Outputs" in node_type:
                ecosystem = "quadmoons"
            # Add more mappings as needed

            custom_info["ecosystems"][ecosystem] = (
                custom_info["ecosystems"].get(ecosystem, 0) + custom_nodes_used[node_type]
            )

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
        # Use workflow analyzer to get nodes
        analysis_result = self.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return False
        nodes = self.workflow_analyzer.nodes

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

        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
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
        return self.complexity.analyze_workflow_complexity(data, method_def, context, fields)

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

        # Use workflow analyzer to get nodes
        analysis_result = self.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return False
        nodes = self.workflow_analyzer.nodes

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
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))

                if any(indicator in class_type for indicator in upscaling_indicators):
                    upscaling_count += 1

                # Check widget values for upscaling models
                widgets = node_data.get("widgets_values", [])
                for widget in widgets:
                    if isinstance(widget, str) and any(
                        indicator in widget for indicator in ["2x-", "4x-", "upscale", "ESRGAN"]
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

        # Use workflow analyzer to get nodes
        analysis_result = self.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return False
        nodes = self.workflow_analyzer.nodes

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
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))

                if any(indicator in class_type for indicator in conditioning_indicators):
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

        # Use workflow analyzer to get nodes
        analysis_result = self.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return False
        nodes = self.workflow_analyzer.nodes

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

        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))

                if any(indicator in class_type for indicator in post_processing_indicators):
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
        """Generic fallback to find basic sampler parameters using the new analyzer."""
        analysis_result = self.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return {}

        # Get parameters from the first generation pass
        generation_passes = analysis_result.get("generation_passes", [])
        if generation_passes:
            return generation_passes[0].get("sampling_info", {})

        return {}
