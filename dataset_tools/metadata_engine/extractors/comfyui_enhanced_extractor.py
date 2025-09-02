# dataset_tools/metadata_engine/extractors/comfyui_enhanced_extractor.py

"""Enhanced ComfyUI Extractor with Dictionary Intelligence.

This extractor leverages the comprehensive ComfyUI node dictionary to provide
intelligent, precise parameter extraction instead of generic traversal.
Addresses the "zero candidates extracted" and "missing node types" issues
by using priority-based extraction and comprehensive node coverage.
"""

import logging
from typing import Any

from .comfyui_node_dictionary_manager import ComfyUINodeDictionaryManager
from .comfyui_traversal import ComfyUITraversalExtractor

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIEnhancedExtractor:
    """Enhanced ComfyUI extractor using dictionary-driven extraction."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the enhanced ComfyUI extractor."""
        self.logger = logger

        # Initialize the dictionary manager and fallback traversal extractor
        self.dictionary_manager = ComfyUINodeDictionaryManager(logger)
        self.traversal_extractor = ComfyUITraversalExtractor(logger)

        # Statistics for debugging
        self.extraction_stats = {
            "dictionary_successes": 0,
            "traversal_fallbacks": 0,
            "total_extractions": 0
        }

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "comfyui_smart_extract_prompt": self.smart_extract_prompt,
            "comfyui_smart_extract_negative_prompt": self.smart_extract_negative_prompt,
            "comfyui_smart_extract_parameters": self.smart_extract_parameters,
            "comfyui_smart_extract_model_info": self.smart_extract_model_info,
            "comfyui_analyze_workflow_intelligence": self.analyze_workflow_intelligence,
            "comfyui_extract_with_priority": self.extract_with_priority,
            "comfyui_get_extraction_report": self.get_extraction_report,
        }

    def smart_extract_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Smart prompt extraction using dictionary priorities, returns candidate dict."""
        self.extraction_stats["total_extractions"] += 1

        if not isinstance(data, dict):
            self.logger.debug("Smart prompt extraction: data is not a dict")
            return {}

        # Try dictionary-based extraction first
        nodes = self.dictionary_manager._get_nodes_from_workflow(data)
        if nodes:
            result = self.dictionary_manager.find_best_node_for_parameter(nodes, "prompt")
            if result:
                node_id, node_data = result
                node_class = node_data.get("class_type", node_data.get("type", "unknown"))
                prompt = self.dictionary_manager.extract_parameter_from_node(node_data, node_class, "prompt")

                if prompt and isinstance(prompt, str) and len(prompt.strip()) > 5:
                    self.extraction_stats["dictionary_successes"] += 1
                    self.logger.info(f"Dictionary extracted prompt from {node_class}: {len(prompt)} chars")
                    return {
                        "text": prompt.strip(),
                        "source_node_id": node_id,
                        "source_node_class": node_class,
                        "prompt_type": "positive"
                    }

        # Fallback to traversal extraction
        self.logger.debug("Dictionary extraction failed, falling back to traversal")
        self.extraction_stats["traversal_fallbacks"] += 1

        fallback_prompt = self._extract_prompt_via_traversal(data)
        if fallback_prompt and len(fallback_prompt.strip()) > 5:
            return {
                "text": fallback_prompt.strip(),
                "prompt_type": "positive"
            }
        return {}

    def smart_extract_negative_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Smart negative prompt extraction using dictionary priorities."""
        if not isinstance(data, dict):
            return {}

        nodes = self.dictionary_manager._get_nodes_from_workflow(data)
        if nodes:
            result = self.dictionary_manager.find_best_node_for_parameter(nodes, "negative_prompt")
            if result:
                node_id, node_data = result
                node_class = node_data.get("class_type", node_data.get("type", "unknown"))
                negative_prompt = self.dictionary_manager.extract_parameter_from_node(node_data, node_class, "negative_prompt")

                if negative_prompt and isinstance(negative_prompt, str):
                    self.logger.info(f"Dictionary extracted negative prompt from {node_class}: {len(negative_prompt)} chars")
                    return {
                        "negative_prompt": negative_prompt.strip(),
                        "source_node_id": node_id,
                        "source_node_class": node_class,
                        "prompt_type": "negative"
                    }

        # Fallback to traversal extraction
        fallback_prompt = self._extract_negative_prompt_via_traversal(data)
        if fallback_prompt:
            return {
                "negative_prompt": fallback_prompt.strip(),
                "prompt_type": "negative"
            }
        return {}

    def smart_extract_parameters(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Smart parameter extraction using dictionary priorities."""
        if not isinstance(data, dict):
            return {}

        parameters = {}
        nodes = self.dictionary_manager._get_nodes_from_workflow(data)
        if not nodes:
            return parameters

        # Extract all known parameters using dictionary priorities
        parameter_types = ["seed", "steps", "cfg_scale", "sampler", "scheduler", "model"]

        for param_type in parameter_types:
            result = self.dictionary_manager.find_best_node_for_parameter(nodes, param_type)
            if result:
                node_id, node_data = result
                node_class = node_data.get("class_type", node_data.get("type", "unknown"))
                value = self.dictionary_manager.extract_parameter_from_node(node_data, node_class, param_type)

                if value is not None:
                    # Type conversion
                    if param_type in ["seed", "steps"] and isinstance(value, (int, str)):
                        try:
                            parameters[param_type] = int(value)
                        except (ValueError, TypeError):
                            parameters[param_type] = value
                    elif param_type == "cfg_scale" and isinstance(value, (float, int, str)):
                        try:
                            parameters[param_type] = float(value)
                        except (ValueError, TypeError):
                            parameters[param_type] = value
                    else:
                        parameters[param_type] = value

                    self.logger.debug(f"Dictionary extracted {param_type}: {value} from {node_class}")

        # Add extraction metadata
        parameters["_extraction_method"] = "dictionary_enhanced"
        parameters["_dictionary_coverage"] = len(parameters) - 1  # Exclude metadata key

        return parameters

    def smart_extract_model_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Smart model information extraction."""
        if not isinstance(data, dict):
            return {}

        model_info = {}
        nodes = self.dictionary_manager._get_nodes_from_workflow(data)
        if not nodes:
            return model_info

        # Extract model information
        model_types = ["model", "lora", "vae"]

        for model_type in model_types:
            result = self.dictionary_manager.find_best_node_for_parameter(nodes, model_type)
            if result:
                node_id, node_data = result
                node_class = node_data.get("class_type", node_data.get("type", "unknown"))
                value = self.dictionary_manager.extract_parameter_from_node(node_data, node_class, model_type)

                if value:
                    model_info[model_type] = value
                    self.logger.debug(f"Dictionary extracted {model_type}: {value} from {node_class}")

        return model_info

    def analyze_workflow_intelligence(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Analyze workflow using dictionary intelligence."""
        if not isinstance(data, dict):
            return {"error": "Invalid workflow data"}

        return self.dictionary_manager.analyze_workflow_structure(data)

    def extract_with_priority(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract specific parameter using priority-based node selection."""
        parameter_type = method_def.get("parameter_type", "prompt")

        if not isinstance(data, dict):
            return {"error": f"Cannot extract {parameter_type} from non-dict data"}

        nodes = self.dictionary_manager._get_nodes_from_workflow(data)
        if not nodes:
            return {"error": "No nodes found in workflow"}

        result = self.dictionary_manager.find_best_node_for_parameter(nodes, parameter_type)
        if not result:
            return {"error": f"No suitable node found for {parameter_type}"}

        node_id, node_data = result
        node_class = node_data.get("class_type", node_data.get("type", "unknown"))
        value = self.dictionary_manager.extract_parameter_from_node(node_data, node_class, parameter_type)

        return {
            "parameter_type": parameter_type,
            "value": value,
            "source_node_id": node_id,
            "source_node_class": node_class,
            "extraction_method": "dictionary_priority"
        }

    def get_extraction_report(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Generate comprehensive extraction report."""
        if not isinstance(data, dict):
            return {"error": "Invalid workflow data"}

        report = self.dictionary_manager.get_extraction_report(data)
        report["extractor_stats"] = self.extraction_stats.copy()

        return report

    def _extract_prompt_via_traversal(self, data: dict) -> str:
        """Fallback prompt extraction using traversal methods."""
        # Try to find a main sampling node and trace backwards
        nodes = self.dictionary_manager._get_nodes_from_workflow(data)

        # Look for main sampling nodes in priority order
        sampling_nodes = ["SamplerCustomAdvanced", "KSampler", "KSampler_A1111"]

        for sampling_node_type in sampling_nodes:
            for node_id, node_data in nodes.items():
                if node_data.get("class_type") == sampling_node_type:
                    # Found a sampling node, trace back to find text
                    traced_text = self.traversal_extractor.trace_text_flow(data, node_id)
                    if traced_text and len(traced_text.strip()) > 5:
                        self.logger.debug(f"Traversal extracted {len(traced_text)} chars from {sampling_node_type}")
                        return traced_text.strip()

        return ""

    def _extract_negative_prompt_via_traversal(self, data: dict) -> str:
        """Fallback negative prompt extraction using traversal methods."""
        # Similar to prompt extraction but look for negative conditioning
        # This is a simplified version - could be enhanced further
        nodes = self.dictionary_manager._get_nodes_from_workflow(data)

        # Look for nodes that commonly have negative prompts
        for node_id, node_data in nodes.items():
            widgets = node_data.get("widgets_values", [])
            if len(widgets) > 1 and isinstance(widgets[1], str):
                # Check if this might be a negative prompt (simple heuristic)
                text = widgets[1].strip()
                if len(text) > 5 and ("negative" in text.lower() or len(text) < 200):
                    return text

        return ""

    def get_extraction_stats(self) -> dict[str, Any]:
        """Get extraction statistics for debugging."""
        stats = self.extraction_stats.copy()
        if stats["total_extractions"] > 0:
            stats["dictionary_success_rate"] = stats["dictionary_successes"] / stats["total_extractions"]
            stats["traversal_fallback_rate"] = stats["traversal_fallbacks"] / stats["total_extractions"]
        else:
            stats["dictionary_success_rate"] = 0.0
            stats["traversal_fallback_rate"] = 0.0

        return stats
