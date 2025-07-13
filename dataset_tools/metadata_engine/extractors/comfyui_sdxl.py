# dataset_tools/metadata_engine/extractors/comfyui_sdxl.py

"""ComfyUI SDXL-specific extraction methods.

Handles SDXL model workflows, dual text encoders, and SDXL-specific parameters.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUISDXLExtractor:
    """Handles SDXL-specific ComfyUI workflows."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the SDXL extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "sdxl_extract_positive_prompt": self.extract_positive_prompt,
            "sdxl_extract_negative_prompt": self._extract_negative_prompt,
            "sdxl_extract_clip_g_prompt": self._extract_clip_g_prompt,
            "sdxl_extract_clip_l_prompt": self._extract_clip_l_prompt,
            "sdxl_extract_model_info": self._extract_model_info,
            "sdxl_extract_refiner_info": self._extract_refiner_info,
            "sdxl_extract_primitive_prompts": self._extract_primitive_prompts,
            "sdxl_detect_workflow": self.detect_sdxl_workflow,
        }

    def extract_positive_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract positive prompt from SDXL workflows."""
        self.logger.debug("[SDXL] Extracting positive prompt")

        if not isinstance(data, dict):
            return ""

        prompt_data = data.get("prompt", data)

        # Strategy 1: Find CLIPTextEncodeSDXL nodes (base, not refiner)
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "CLIPTextEncodeSDXL" in class_type and "Refiner" not in class_type:
                # Check for primitive node connections or widget values
                text = self._get_text_from_sdxl_node(node_data, prompt_data)
                if text and not self._looks_like_negative_prompt(text):
                    return text

        # Strategy 2: Look for PrimitiveNode connections
        primitive_positive = self._find_primitive_positive_prompt(prompt_data)
        if primitive_positive:
            return primitive_positive

        # Strategy 3: Standard CLIPTextEncode fallback
        return self._extract_standard_clip_prompt(prompt_data, positive=True)

    def _extract_negative_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract negative prompt from SDXL workflows."""
        self.logger.debug("[SDXL] Extracting negative prompt")

        if not isinstance(data, dict):
            return ""

        prompt_data = data.get("prompt", data)

        # Strategy 1: Find CLIPTextEncodeSDXL nodes for negative conditioning
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "CLIPTextEncodeSDXL" in class_type and "Refiner" not in class_type:
                text = self._get_text_from_sdxl_node(node_data, prompt_data)
                if text and self._looks_like_negative_prompt(text):
                    return text

        # Strategy 2: Look for dedicated negative prompt nodes
        primitive_negative = self._find_primitive_negative_prompt(prompt_data)
        if primitive_negative:
            return primitive_negative

        # Strategy 3: Standard CLIPTextEncode fallback
        return self._extract_standard_clip_prompt(prompt_data, positive=False)

    def _extract_clip_g_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract CLIP-G (OpenCLIP) prompt from SDXL workflows."""
        self.logger.debug("[SDXL] Extracting CLIP-G prompt")

        if not isinstance(data, dict):
            return ""

        prompt_data = data.get("prompt", data)

        # Look for CLIPTextEncodeSDXL nodes and extract text_g input
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "CLIPTextEncodeSDXL" in class_type:
                text_g = self._get_sdxl_text_input(node_data, prompt_data, "text_g")
                if text_g:
                    return text_g

        return ""

    def _extract_clip_l_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract CLIP-L prompt from SDXL workflows."""
        self.logger.debug("[SDXL] Extracting CLIP-L prompt")

        if not isinstance(data, dict):
            return ""

        prompt_data = data.get("prompt", data)

        # Look for CLIPTextEncodeSDXL nodes and extract text_l input
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "CLIPTextEncodeSDXL" in class_type:
                text_l = self._get_sdxl_text_input(node_data, prompt_data, "text_l")
                if text_l:
                    return text_l

        return ""

    def _extract_model_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract SDXL model information."""
        self.logger.debug("[SDXL] Extracting model info")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        model_info = {}

        # Look for SDXL checkpoint loaders
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "CheckpointLoaderSimple" in class_type or "CheckpointLoader" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    model_name = widgets[0] if isinstance(widgets[0], str) else ""
                    # Check if it's an SDXL model
                    if "sdxl" in model_name.lower() or "xl" in model_name.lower():
                        model_info["base_model"] = model_name

            elif "SDXLCheckpointLoader" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    model_info["base_model"] = widgets[0] if isinstance(widgets[0], str) else ""

        return model_info

    def _extract_refiner_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract SDXL refiner information."""
        self.logger.debug("[SDXL] Extracting refiner info")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        refiner_info = {}

        # Look for refiner-related nodes
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "Refiner" in class_type:
                widgets = node_data.get("widgets_values", [])
                refiner_info[class_type] = {"node_id": node_id, "widgets": widgets}

        return refiner_info

    def _extract_primitive_prompts(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, str]:
        """Extract prompts from PrimitiveNode connections."""
        self.logger.debug("[SDXL] Extracting primitive prompts")

        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)

        return {
            "positive": self._find_primitive_positive_prompt(prompt_data),
            "negative": self._find_primitive_negative_prompt(prompt_data),
        }

    def detect_sdxl_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this is an SDXL workflow."""
        if not isinstance(data, dict):
            return False

        prompt_data = data.get("prompt", data)

        # Look for SDXL-specific node types
        sdxl_indicators = [
            "CLIPTextEncodeSDXL",
            "SDXLCheckpointLoader",
            "SDXLPromptStyler",
            "SDXLRefiner",
            "SDXLSampler",
        ]

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if any(indicator in class_type for indicator in sdxl_indicators):
                return True

        # Also check for models with SDXL in the name
        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if "CheckpointLoader" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets and isinstance(widgets[0], str):
                    model_name = widgets[0].lower()
                    if "sdxl" in model_name or "xl" in model_name:
                        return True

        return False

    def _get_text_from_sdxl_node(self, node_data: dict, prompt_data: dict) -> str:
        """Extract text from SDXL text encode node."""
        # First check widget values
        widgets = node_data.get("widgets_values", [])
        if widgets:
            for widget in widgets:
                if isinstance(widget, str) and len(widget.strip()) > 0:
                    return widget.strip()

        # Then check for PrimitiveNode connections
        inputs = node_data.get("inputs", {})
        if isinstance(inputs, dict):
            # Check text_g and text_l inputs
            for text_input in ["text_g", "text_l"]:
                if text_input in inputs:
                    input_info = inputs[text_input]
                    if isinstance(input_info, list) and len(input_info) > 0:
                        primitive_node_id = str(input_info[0])
                        if primitive_node_id in prompt_data:
                            primitive_node = prompt_data[primitive_node_id]
                            if "PrimitiveNode" in primitive_node.get("class_type", ""):
                                primitive_widgets = primitive_node.get("widgets_values", [])
                                if primitive_widgets and isinstance(primitive_widgets[0], str):
                                    return primitive_widgets[0].strip()

        return ""

    def _get_sdxl_text_input(self, node_data: dict, prompt_data: dict, input_name: str) -> str:
        """Get specific text input (text_g or text_l) from SDXL node."""
        inputs = node_data.get("inputs", {})
        if isinstance(inputs, dict) and input_name in inputs:
            input_info = inputs[input_name]
            if isinstance(input_info, list) and len(input_info) > 0:
                source_node_id = str(input_info[0])
                if source_node_id in prompt_data:
                    source_node = prompt_data[source_node_id]
                    if "PrimitiveNode" in source_node.get("class_type", ""):
                        widgets = source_node.get("widgets_values", [])
                        if widgets and isinstance(widgets[0], str):
                            return widgets[0].strip()

        return ""

    def _find_primitive_positive_prompt(self, prompt_data: dict) -> str:
        """Find positive prompt from PrimitiveNode connections."""
        # Look for PrimitiveNodes that are connected to positive conditioning
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "PrimitiveNode" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets and isinstance(widgets[0], str):
                    text = widgets[0].strip()
                    if text and not self._looks_like_negative_prompt(text):
                        return text

        return ""

    def _find_primitive_negative_prompt(self, prompt_data: dict) -> str:
        """Find negative prompt from PrimitiveNode connections."""
        # Look for PrimitiveNodes that contain negative prompt indicators
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if "PrimitiveNode" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets and isinstance(widgets[0], str):
                    text = widgets[0].strip()
                    if text and self._looks_like_negative_prompt(text):
                        return text

        return ""

    def _extract_standard_clip_prompt(self, prompt_data: dict, positive: bool = True) -> str:
        """Extract from standard CLIPTextEncode nodes."""
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            if class_type == "CLIPTextEncode":
                widgets = node_data.get("widgets_values", [])
                if widgets and isinstance(widgets[0], str):
                    text = widgets[0].strip()
                    if text:
                        is_negative = self._looks_like_negative_prompt(text)
                        if (positive and not is_negative) or (not positive and is_negative):
                            return text

        return ""

    def _looks_like_negative_prompt(self, text: str) -> bool:
        """Check if text looks like a negative prompt."""
        if not isinstance(text, str):
            return False

        negative_indicators = [
            "worst quality",
            "low quality",
            "normal quality",
            "lowres",
            "bad anatomy",
            "bad hands",
            "text",
            "error",
            "missing fingers",
            "extra digit",
            "fewer digits",
            "cropped",
            "jpeg artifacts",
            "signature",
            "watermark",
            "username",
            "blurry",
            "bad feet",
            "poorly drawn",
            "extra limbs",
            "disfigured",
            "deformed",
            "body out of frame",
            "bad proportions",
            "duplicate",
            "morbid",
            "mutilated",
            "mutation",
            "blurry",
        ]

        text_lower = text.lower()
        negative_count = sum(1 for indicator in negative_indicators if indicator in text_lower)

        return negative_count >= 2

    def extract_sdxl_workflow_summary(self, data: dict) -> dict[str, Any]:
        """Extract comprehensive SDXL workflow summary."""
        if not isinstance(data, dict):
            return {}

        summary = {
            "is_sdxl_workflow": self.detect_sdxl_workflow(data, {}, {}, {}),
            "positive_prompt": self.extract_positive_prompt(data, {}, {}, {}),
            "negative_prompt": self._extract_negative_prompt(data, {}, {}, {}),
            "clip_g_prompt": self._extract_clip_g_prompt(data, {}, {}, {}),
            "clip_l_prompt": self._extract_clip_l_prompt(data, {}, {}, {}),
            "model_info": self._extract_model_info(data, {}, {}, {}),
            "refiner_info": self._extract_refiner_info(data, {}, {}, {}),
            "primitive_prompts": self._extract_primitive_prompts(data, {}, {}, {}),
        }

        return summary
