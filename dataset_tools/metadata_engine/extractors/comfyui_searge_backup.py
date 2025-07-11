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
            "searge_detect_workflow": self._detect_searge_workflow,
        }

    def _extract_generation_params(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract Searge generation parameters."""
        self.logger.debug("[Searge] Extracting generation params")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        generation_params = {}

        # Look for Searge generation parameter nodes
        searge_gen_nodes = [
            "SeargeGenerationParameters",
            "SeargeParameterProcessor",
            "SeargeSDXLParameters",
            "SeargeSDXLBaseParameters",
            "SeargeSDXLRefinerParameters",
            "SeargeAdvancedParameters",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(gen_node in class_type for gen_node in searge_gen_nodes):
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    generation_params[class_type] = {
                        "node_id": node_id,
                        "widgets": widgets,
                        "type": class_type,
                    }

                    # Parse common parameters
                    if "SeargeGenerationParameters" in class_type:
                        generation_params["parsed_params"] = self._parse_generation_params(widgets)

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

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        style_prompts = {}

        # Look for Searge style prompt nodes
        searge_style_nodes = [
            "SeargeStylePreprocessor",
            "SeargePromptProcessor",
            "SeargePromptCombiner",
            "SeargePromptAdapterV2",
            "SeargeStylePrompts",
            "SeargePromptText",
            "SeargeInput1",
            "SeargeInput2",
            "SeargeInput3",
            "SeargeInput4",
            "SeargeInput5",
            "SeargeInput6",
            "SeargeInput7",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(style_node in class_type for style_node in searge_style_nodes):
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    style_prompts[class_type] = {
                        "node_id": node_id,
                        "widgets": widgets,
                        "type": class_type,
                    }

                    # Extract text content
                    for widget in widgets:
                        if isinstance(widget, str) and len(widget.strip()) > 0:
                            style_prompts[f"{class_type}_text"] = widget.strip()
                            break

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

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        model_params = {}

        # Look for Searge model parameter nodes
        searge_model_nodes = [
            "SeargeCheckpointLoader",
            "SeargeModelSelector",
            "SeargeVAELoader",
            "SeargeUpscaleModelLoader",
            "SeargeLoraLoader",
            "SeargeEmbeddingLoader",
            "SeargeRefinerModelLoader",
            "SeargeCustomModelLoader",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(model_node in class_type for model_node in searge_model_nodes):
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    model_params[class_type] = {
                        "node_id": node_id,
                        "widgets": widgets,
                        "type": class_type,
                    }

                    # Parse model names
                    if widgets and isinstance(widgets[0], str):
                        model_params[f"{class_type}_model"] = widgets[0]

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

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        sampler_params = {}

        # Look for Searge sampler nodes
        searge_sampler_nodes = [
            "SeargeSDXLSampler",
            "SeargeSDXLSampler2",
            "SeargeAdvancedSampler",
            "SeargeSamplerInputs",
            "SeargeCustomSampler",
            "SeargeHiResFix",
            "SeargeUpscaler",
            "SeargeDetailer",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(sampler_node in class_type for sampler_node in searge_sampler_nodes):
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    sampler_params[class_type] = {
                        "node_id": node_id,
                        "widgets": widgets,
                        "type": class_type,
                    }

                    # Parse sampler parameters
                    if "SeargeSDXLSampler" in class_type:
                        sampler_params["parsed_sampler"] = self._parse_sampler_params(widgets)

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

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        image_params = {}

        # Look for Searge image parameter nodes
        searge_image_nodes = [
            "SeargeImageSaving",
            "SeargeImageProcessor",
            "SeargeOutput1",
            "SeargeOutput2",
            "SeargeOutput3",
            "SeargeOutput4",
            "SeargeOutput5",
            "SeargeOutput6",
            "SeargeOutput7",
            "SeargePreview",
            "SeargeImageAdapter",
            "SeargeImageInput",
            "SeargeImageOutput",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if any(image_node in class_type for image_node in searge_image_nodes):
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    image_params[class_type] = {
                        "node_id": node_id,
                        "widgets": widgets,
                        "type": class_type,
                    }

        return image_params

    def _detect_searge_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this workflow uses Searge nodes."""
        if not isinstance(data, dict):
            return False

        prompt_data = data.get("prompt", data)

        # Look for Searge indicators
        searge_indicators = [
            "Searge",
            "SeargeSDXL",
            "SeargeInput",
            "SeargeOutput",
            "SeargeGeneration",
            "SeargeStyle",
            "SeargePrompt",
            "SeargeModel",
            "SeargeSampler",
            "SeargeImage",
            "SeargeParameter",
            "SeargeCustom",
            "SeargeAdvanced",
        ]

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if any(indicator in class_type for indicator in searge_indicators):
                return True

        # Also check properties for Searge cnr_id
        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            properties = node_data.get("properties", {})
            if isinstance(properties, dict):
                cnr_id = properties.get("cnr_id", "")
                if "searge" in cnr_id.lower():
                    return True

        return False

    def _parse_generation_params(self, widgets: list) -> dict[str, Any]:
        """Parse generation parameters from widgets."""
        if not widgets:
            return {}

        # Common Searge generation parameter structure
        params = {}

        # Map widget indices to parameter names (approximate)
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
            if i < len(widgets):
                params[param_name] = widgets[i]

        return params

    def _parse_sampler_params(self, widgets: list) -> dict[str, Any]:
        """Parse sampler parameters from widgets."""
        if not widgets:
            return {}

        params = {}

        # Common Searge sampler parameter structure
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

    def extract_searge_workflow_summary(self, data: dict) -> dict[str, Any]:
        """Extract comprehensive Searge workflow summary."""
        if not isinstance(data, dict):
            return {}

        summary = {
            "is_searge_workflow": self._detect_searge_workflow(data, {}, {}, {}),
            "generation_params": self._extract_generation_params(data, {}, {}, {}),
            "style_prompts": self._extract_style_prompts(data, {}, {}, {}),
            "model_params": self._extract_model_params(data, {}, {}, {}),
            "sampler_params": self._extract_sampler_params(data, {}, {}, {}),
            "image_params": self._extract_image_params(data, {}, {}, {}),
        }

        return summary

    def get_searge_nodes(self, data: dict) -> dict[str, dict]:
        """Get all Searge nodes in the workflow."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        searge_nodes = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if self._is_searge_node(class_type):
                searge_nodes[node_id] = {
                    "type": class_type,
                    "widgets": node_data.get("widgets_values", []),
                    "inputs": node_data.get("inputs", {}),
                    "outputs": node_data.get("outputs", []),
                }

        return searge_nodes

    def _is_searge_node(self, class_type: str) -> bool:
        """Check if a class type is a Searge node."""
        searge_indicators = [
            "Searge",
            "SeargeSDXL",
            "SeargeInput",
            "SeargeOutput",
            "SeargeGeneration",
            "SeargeStyle",
            "SeargePrompt",
            "SeargeModel",
            "SeargeSampler",
            "SeargeImage",
            "SeargeParameter",
            "SeargeCustom",
            "SeargeAdvanced",
            "SeargeCheckpoint",
            "SeargeVAE",
            "SeargeUpscale",
            "SeargePreview",
            "SeargeProcessor",
            "SeargeAdapter",
            "SeargeHiResFix",
            "SeargeDetailer",
            "SeargeRefiner",
        ]

        return any(indicator in class_type for indicator in searge_indicators)

    def extract_searge_prompts(self, data: dict) -> dict[str, str]:
        """Extract all prompts from Searge nodes."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        prompts = {}

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if self._is_searge_node(class_type) and ("Input" in class_type or "Prompt" in class_type):
                widgets = node_data.get("widgets_values", [])
                for i, widget in enumerate(widgets):
                    if isinstance(widget, str) and len(widget.strip()) > 0:
                        prompts[f"{class_type}_{i}"] = widget.strip()

        return prompts

    def get_searge_workflow_flow(self, data: dict) -> list[dict]:
        """Get the flow of Searge nodes in the workflow."""
        if not isinstance(data, dict):
            return []

        prompt_data = data.get("prompt", data)
        flow = []

        # Input nodes
        input_nodes = []
        # Processing nodes
        processing_nodes = []
        # Output nodes
        output_nodes = []

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if self._is_searge_node(class_type):
                node_info = {
                    "node_id": node_id,
                    "type": class_type,
                    "category": self._get_searge_node_category(class_type),
                }

                if "Input" in class_type:
                    input_nodes.append(node_info)
                elif "Output" in class_type:
                    output_nodes.append(node_info)
                else:
                    processing_nodes.append(node_info)

        # Sort by node ID for consistent ordering
        input_nodes.sort(key=lambda x: x["node_id"])
        processing_nodes.sort(key=lambda x: x["node_id"])
        output_nodes.sort(key=lambda x: x["node_id"])

        flow.extend(input_nodes)
        flow.extend(processing_nodes)
        flow.extend(output_nodes)

        return flow

    def _get_searge_node_category(self, class_type: str) -> str:
        """Get the category of a Searge node."""
        if "Input" in class_type:
            return "input"
        if "Output" in class_type:
            return "output"
        if "Generation" in class_type or "Parameter" in class_type:
            return "generation"
        if "Style" in class_type or "Prompt" in class_type:
            return "prompt"
        if "Model" in class_type or "Checkpoint" in class_type:
            return "model"
        if "Sampler" in class_type:
            return "sampler"
        if "Image" in class_type:
            return "image"
        return "processing"
