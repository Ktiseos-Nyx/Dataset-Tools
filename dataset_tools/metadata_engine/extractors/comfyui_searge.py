# dataset_tools/metadata_engine/extractors/comfyui_searge.py

"""ComfyUI Searge ecosystem extractor.

Handles Searge-SDXL nodes for SDXL workflows with advanced parameter control,
style prompting, and generation parameters.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUISeargeExtractor:
    """Handles Searge-SDXL ecosystem nodes."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the Searge extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "searge_extract_generation_params": self._extract_generation_params,
            "searge_extract_style_prompts": self._extract_style_prompts,
            "searge_extract_model_params": self._extract_model_params,
            "searge_extract_sampler_params": self._extract_sampler_params,
            "searge_extract_image_params": self._extract_image_params,
            "searge_detect_workflow": self.detect_searge_workflow,
            "searge_extract_summary": self.extract_searge_workflow_summary,
        }

    def _get_nodes(self, data: dict) -> dict:
        """Helper to robustly get the nodes dictionary from workflow or API data."""
        if not isinstance(data, dict):
            return {}
        # This handles both {"prompt": {"1": ...}} and {"nodes": [...]} formats
        if "nodes" in data and isinstance(data["nodes"], list):
            return {str(node.get("id", i)): node for i, node in enumerate(data["nodes"])}
        if "prompt" in data and isinstance(data["prompt"], dict):
            return data["prompt"]
        if all(isinstance(v, dict) and "class_type" in v for v in data.values()):
            return data
        return {}

    def _extract_generation_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Searge generation parameters."""
        self.logger.debug("[Searge] Extracting generation params")
        nodes = self._get_nodes(data)
        if not nodes:
            return {}

        generation_params = {}
        searge_gen_nodes = [
            "SeargeGenerationParameters",
            "SeargeParameterProcessor",
            "SeargeSDXLParameters",
            "SeargeSDXLBaseParameters",
        ]

        for node_id, node_data in nodes.items():
            class_type = node_data.get("class_type", "")
            if any(gen_node in class_type for gen_node in searge_gen_nodes):
                widgets = node_data.get("widgets_values", [])
                if "SeargeGenerationParameters" in class_type:
                    generation_params = self._parse_generation_params(widgets)

        return generation_params

    def _extract_style_prompts(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Searge style prompts."""
        self.logger.debug("[Searge] Extracting style prompts")
        nodes = self._get_nodes(data)
        if not nodes:
            return {}

        style_prompts = {}

        for node_id, node_data in nodes.items():
            class_type = node_data.get("class_type", "")
            widgets = node_data.get("widgets_values", [])

            if "SeargeStylePrompts" in class_type and widgets:
                style_prompts["style_prompt"] = widgets[0] if isinstance(widgets[0], str) else ""
            elif "SeargePromptText" in class_type and widgets:
                style_prompts["prompt_text"] = widgets[0] if isinstance(widgets[0], str) else ""
            elif "SeargePromptCombiner" in class_type and widgets:
                style_prompts["combined_prompt"] = widgets[0] if isinstance(widgets[0], str) else ""

        return style_prompts

    def _extract_model_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Searge model parameters."""
        self.logger.debug("[Searge] Extracting model params")
        nodes = self._get_nodes(data)
        if not nodes:
            return {}

        model_params = {}

        for node_id, node_data in nodes.items():
            class_type = node_data.get("class_type", "")
            widgets = node_data.get("widgets_values", [])

            if "SeargeCheckpointLoader" in class_type and widgets:
                model_params["checkpoint"] = widgets[0] if isinstance(widgets[0], str) else ""
            elif "SeargeLoraLoader" in class_type and widgets:
                if "loras" not in model_params:
                    model_params["loras"] = []
                model_params["loras"].append(
                    {
                        "name": widgets[0] if isinstance(widgets[0], str) else "",
                        "strength": widgets[1] if len(widgets) > 1 else 1.0,
                    }
                )
            elif "SeargeVAELoader" in class_type and widgets:
                model_params["vae"] = widgets[0] if isinstance(widgets[0], str) else ""

        return model_params

    def _extract_sampler_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Searge sampler parameters."""
        self.logger.debug("[Searge] Extracting sampler params")
        nodes = self._get_nodes(data)
        if not nodes:
            return {}

        sampler_params = {}

        for node_id, node_data in nodes.items():
            class_type = node_data.get("class_type", "")
            widgets = node_data.get("widgets_values", [])

            if any(sampler_node in class_type for sampler_node in ["SeargeSamplerInputs", "SeargeAdvancedParameters"]):
                sampler_params.update(self._parse_sampler_params(widgets))

        return sampler_params

    def _extract_image_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Searge image parameters."""
        self.logger.debug("[Searge] Extracting image params")
        nodes = self._get_nodes(data)
        if not nodes:
            return {}

        image_params = {}

        for node_id, node_data in nodes.items():
            class_type = node_data.get("class_type", "")
            widgets = node_data.get("widgets_values", [])

            if "SeargeImageInputs" in class_type and widgets:
                image_params = self._parse_image_params(widgets)

        return image_params

    def detect_searge_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this workflow uses Searge nodes."""
        nodes = self._get_nodes(data)
        if not nodes:
            return False

        searge_indicators = ["Searge", "SeargeSDXL"]

        for node_data in nodes.values():
            class_type = node_data.get("class_type", "")
            if any(indicator in class_type for indicator in searge_indicators):
                return True

        return False

    def _parse_generation_params(self, widgets: list) -> dict[str, Any]:
        """Parse generation parameters from widgets."""
        if not isinstance(widgets, list) or len(widgets) == 0:
            return {}

        params = {}
        param_mapping = {
            0: "seed",
            1: "steps",
            2: "cfg_scale",
            3: "sampler_name",
            4: "scheduler",
            5: "denoise",
            6: "width",
            7: "height",
            8: "batch_size",
            9: "refiner_switch",
            10: "refiner_denoise",
        }

        for i, param_name in param_mapping.items():
            if i < len(widgets):  # Check to prevent IndexError
                params[param_name] = widgets[i]

        return params

    def _parse_sampler_params(self, widgets: list) -> dict[str, Any]:
        """Parse sampler parameters from widgets."""
        if not isinstance(widgets, list) or len(widgets) == 0:
            return {}

        params = {}
        param_mapping = {
            0: "base_steps",
            1: "refiner_steps",
            2: "cfg_scale",
            3: "sampler_name",
            4: "scheduler",
            5: "base_denoise",
            6: "refiner_denoise",
            7: "refiner_switch",
        }

        for i, param_name in param_mapping.items():
            if i < len(widgets):
                params[param_name] = widgets[i]

        return params

    def _parse_image_params(self, widgets: list) -> dict[str, Any]:
        """Parse image parameters from widgets."""
        if not isinstance(widgets, list) or len(widgets) == 0:
            return {}

        params = {}
        param_mapping = {
            0: "width",
            1: "height",
            2: "upscale_factor",
            3: "interpolation_mode",
        }

        for i, param_name in param_mapping.items():
            if i < len(widgets):
                params[param_name] = widgets[i]

        return params

    def extract_searge_workflow_summary(self, data: dict, *args, **kwargs) -> dict[str, Any]:
        """Extract comprehensive Searge workflow summary."""
        if not self.detect_searge_workflow(data, {}, {}, {}):
            return {"is_searge_workflow": False}

        # Simplified extraction logic
        nodes = self._get_nodes(data)
        summary = {
            "is_searge_workflow": True,
            "main_prompt": "",
            "style_prompt": "",
            "parameters": {},
            "model": "",
            "loras": [],
        }

        for node_id, node_data in nodes.items():
            class_type = node_data.get("class_type", "")
            widgets = node_data.get("widgets_values", [])
            if not widgets:
                continue

            if class_type == "SeargePromptText" and not summary["main_prompt"]:
                summary["main_prompt"] = widgets[0] if isinstance(widgets[0], str) else ""
            elif class_type == "SeargeStylePrompts" and not summary["style_prompt"]:
                summary["style_prompt"] = widgets[0] if isinstance(widgets[0], str) else ""
            elif class_type == "SeargeGenerationParameters":
                summary["parameters"] = self._parse_generation_params(widgets)
            elif class_type == "SeargeCheckpointLoader":
                summary["model"] = widgets[0] if isinstance(widgets[0], str) else ""
            elif class_type == "SeargeLoraLoader":
                summary["loras"].append(
                    {
                        "name": widgets[0] if isinstance(widgets[0], str) else "",
                        "strength": widgets[1] if len(widgets) > 1 else 1.0,
                    }
                )

        return summary
