# dataset_tools/metadata_engine/extractors/comfyui_node_checker.py

"""ComfyUI node validation and checking methods.

Handles node type detection, validation, and classification.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUINodeChecker:
    """Handles ComfyUI node validation and checking."""

    # --- SUGGESTION 2: Use class constants for indicators for better readability and maintenance.
    _TEXT_INDICATORS = [
        "text",
        "prompt",
        "wildcard",
        "string",
        "cliptextencode",
        "dprandomgenerator",
        "randomgenerator",
        "impactwildcard",
    ]
    _SAMPLER_INDICATORS = [
        "sampler",
        "ksampler",
        "sample",
        "generate",
        "euler",
        "dpm",
        "ddim",
        "plms",
        "unipc",
        "dpmsolver",
    ]
    _MODEL_LOADER_INDICATORS = [
        "checkpointloader",
        "modelloader",
        "diffusersloader",
        "unclipcheckpointloader",
    ]
    _LORA_INDICATORS = ["lora", "loraloader"]
    _VAE_INDICATORS = ["vae", "vaeloader", "vaedecode", "vaeencode"]
    _CONDITIONING_INDICATORS = [
        "conditioning",
        "clip",
        "cliptextencode",
        "controlnet",
        "t2iadapter",
        "ipadapter",
    ]
    _CUSTOM_NODE_PREFIXES = [
        "impact",
        "efficiency",
        "was",
        "comfyui-",
        "rgthree",
        "inspire",
        "animatediff",
        "controlnet",
        "ipadapter",
        "segment",
        "face",
        "ultimate",
        "advanced",
        "custom",
        "dp",
        "dynamicprompt",
        "wildcard",
    ]
    _NEGATIVE_PROMPT_INDICATORS = [
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
    ]
    _ECOSYSTEMS_MAP = {
        "impact": ["impact", "impactwildcard"],
        "efficiency": ["efficiency", "efficient"],
        "was": ["was", "was_"],
        "rgthree": ["rgthree", "rg_"],
        "inspire": ["inspire", "inspirepack"],
        "animatediff": ["animatediff", "animate"],
        "controlnet": ["controlnet", "control"],
        "ipadapter": ["ipadapter", "ip_adapter"],
        "ultimate": ["ultimate", "ultimatesdupscale"],
        "advanced": ["advanced", "advancedcontrolnet"],
        "segment": ["segment", "sam", "segs"],
        "face": ["face", "facedetailer", "faceswap"],
        "dynamicprompts": [
            "dp",
            "dynamicprompt",
            "wildcard",
            "randomgenerator",
            "combinatorial",
        ],
        "core": ["cliptextencode", "ksampler", "checkpointloader", "vae"],
    }

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the node checker."""
        self.logger = logger

    # --- SUGGESTION 1: Use case-insensitive matching for robustness.
    def is_text_node(self, node: dict) -> bool:
        """Check if a node is a text-generating or text-holding node."""
        if not isinstance(node, dict):
            return False
        node_type = node.get("class_type", node.get("type", "")).lower()
        return any(indicator in node_type for indicator in self._TEXT_INDICATORS)

    def is_sampler_node(self, node: dict) -> bool:
        """Check if a node is a sampler node."""
        if not isinstance(node, dict):
            return False
        node_type = node.get("class_type", node.get("type", "")).lower()
        return any(indicator in node_type for indicator in self._SAMPLER_INDICATORS)

    def is_model_loader_node(self, node: dict) -> bool:
        """Check if a node is a model loader node (e.g., CheckpointLoader)."""
        if not isinstance(node, dict):
            return False
        node_type = node.get("class_type", node.get("type", "")).lower()
        return any(indicator in node_type for indicator in self._MODEL_LOADER_INDICATORS)

    def is_lora_node(self, node: dict) -> bool:
        """Check if a node is a LoRA loader or application node."""
        if not isinstance(node, dict):
            return False
        node_type = node.get("class_type", node.get("type", "")).lower()
        return any(indicator in node_type for indicator in self._LORA_INDICATORS)

    def is_vae_node(self, node: dict) -> bool:
        """Check if a node is related to VAE operations (load, encode, decode)."""
        if not isinstance(node, dict):
            return False
        node_type = node.get("class_type", node.get("type", "")).lower()
        return any(indicator in node_type for indicator in self._VAE_INDICATORS)

    def is_conditioning_node(self, node: dict) -> bool:
        """Check if a node handles or produces conditioning data."""
        if not isinstance(node, dict):
            return False
        node_type = node.get("class_type", node.get("type", "")).lower()
        return any(indicator in node_type for indicator in self._CONDITIONING_INDICATORS)

    def is_custom_node(self, node: dict) -> bool:
        """Check if a node likely originates from a custom node pack."""
        if not isinstance(node, dict):
            return False
        properties = node.get("properties", {})
        if isinstance(properties, dict) and properties.get("Node name for S&R"):
            return True  # A very strong indicator of a custom node or a named core node.

        node_type = node.get("class_type", node.get("type", "")).lower()
        return any(prefix in node_type for prefix in self._CUSTOM_NODE_PREFIXES)

    def get_node_ecosystem(self, node: dict) -> str:
        """Determine which ecosystem or node pack a node likely belongs to."""
        if not isinstance(node, dict):
            return "unknown"

        # Fallback to node type analysis
        node_type = node.get("class_type", node.get("type", "")).lower()

        for ecosystem, indicators in self._ECOSYSTEMS_MAP.items():
            if any(indicator in node_type for indicator in indicators):
                return ecosystem

        # Check properties as a secondary source, especially for manager-installed nodes
        properties = node.get("properties", {})
        if isinstance(properties, dict):
            s_and_r_name = properties.get("Node name for S&R", "")
            if s_and_r_name:
                # Attempt to guess from the Save & Restore name
                s_and_r_name_lower = s_and_r_name.lower()
                for ecosystem, indicators in self._ECOSYSTEMS_MAP.items():
                    if any(indicator in s_and_r_name_lower for indicator in indicators):
                        return ecosystem

        if self.is_custom_node(node):
            return "custom_other"

        return "core"

    def get_node_complexity(self, node: dict) -> str:
        """Determine the complexity level of a node based on its connections."""
        if not isinstance(node, dict):
            return "unknown"
        inputs = node.get("inputs", [])
        outputs = node.get("outputs", [])
        widgets = node.get("widgets_values", [])

        input_count = len(inputs) if isinstance(inputs, (list, dict)) else 0
        output_count = len(outputs) if isinstance(outputs, list) else 0
        widget_count = len(widgets) if isinstance(widgets, list) else 0

        total_complexity = input_count + output_count + widget_count

        if total_complexity <= 3:
            return "simple"
        if total_complexity <= 8:
            return "medium"
        return "complex"

    def validate_node_structure(self, node: dict) -> dict[str, Any]:
        """Validate a node's structure and return a summary.

        Args:
            node: The node dictionary to validate.

        Returns:
            A dictionary containing validation results.

        """
        if not isinstance(node, dict):
            return {"valid": False, "errors": ["Node is not a dictionary"]}

        errors = []
        warnings = []

        # Check required fields
        required_fields = ["inputs", "outputs"]
        if "class_type" not in node and "type" not in node:
            errors.append("Missing 'class_type' or 'type' field")

        for field in required_fields:
            if field not in node:
                errors.append(f"Missing required field: {field}")

        # Validate structure of fields
        if "inputs" in node and not isinstance(node["inputs"], (list, dict)):
            errors.append("Field 'inputs' must be a list or dict")
        if "outputs" in node and not isinstance(node["outputs"], list):
            errors.append("Field 'outputs' must be a list")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "complexity": self.get_node_complexity(node),
            "ecosystem": self.get_node_ecosystem(node),
        }

    def looks_like_negative_prompt(self, text: str) -> bool:
        """Heuristically check if a string of text is a negative prompt."""
        if not isinstance(text, str) or not text.strip():
            return False

        text_lower = text.lower()
        negative_count = sum(1 for indicator in self._NEGATIVE_PROMPT_INDICATORS if indicator in text_lower)

        # If 2 or more negative indicators are found, it's very likely a negative prompt.
        # This threshold prevents false positives on words like "text" or "blurry".
        return negative_count >= 2

    def extract_node_metadata(self, node: dict) -> dict[str, Any]:
        """Extract a full suite of metadata from a single node."""
        if not isinstance(node, dict):
            return {}

        return {
            "type": node.get("class_type", node.get("type", "")),
            "title": node.get("title", ""),
            "ecosystem": self.get_node_ecosystem(node),
            "complexity": self.get_node_complexity(node),
            "is_text": self.is_text_node(node),
            "is_sampler": self.is_sampler_node(node),
            "is_model_loader": self.is_model_loader_node(node),
            "is_lora": self.is_lora_node(node),
            "is_vae": self.is_vae_node(node),
            "is_conditioning": self.is_conditioning_node(node),
            "is_custom": self.is_custom_node(node),
            "properties": node.get("properties", {}),
        }

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "comfyui_is_text_node": self._is_text_node_method,
            "comfyui_is_sampler_node": self._is_sampler_node_method,
            "comfyui_is_model_loader_node": self._is_model_loader_node_method,
            "comfyui_is_lora_node": self._is_lora_node_method,
            "comfyui_is_vae_node": self._is_vae_node_method,
            "comfyui_is_conditioning_node": self._is_conditioning_node_method,
            "comfyui_is_custom_node": self._is_custom_node_method,
            "comfyui_get_node_ecosystem": self._get_node_ecosystem_method,
            "comfyui_get_node_complexity": self._get_node_complexity_method,
            "comfyui_validate_node_structure": self._validate_node_structure_method,
            "comfyui_extract_node_metadata": self._extract_node_metadata_method,
            "comfyui_looks_like_negative_prompt": self._looks_like_negative_prompt_method,
        }

    def _is_text_node_method(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Check if workflow contains text nodes."""
        if isinstance(data, dict) and "class_type" in data:
            return self.is_text_node(data)
        return False

    def _is_sampler_node_method(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Check if workflow contains sampler nodes."""
        if isinstance(data, dict) and "class_type" in data:
            return self.is_sampler_node(data)
        return False

    def _is_model_loader_node_method(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Check if workflow contains model loader nodes."""
        if isinstance(data, dict) and "class_type" in data:
            return self.is_model_loader_node(data)
        return False

    def _is_lora_node_method(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Check if workflow contains LoRA nodes."""
        if isinstance(data, dict) and "class_type" in data:
            return self.is_lora_node(data)
        return False

    def _is_vae_node_method(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Check if workflow contains VAE nodes."""
        if isinstance(data, dict) and "class_type" in data:
            return self.is_vae_node(data)
        return False

    def _is_conditioning_node_method(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Check if workflow contains conditioning nodes."""
        if isinstance(data, dict) and "class_type" in data:
            return self.is_conditioning_node(data)
        return False

    def _is_custom_node_method(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Check if workflow contains custom nodes."""
        if isinstance(data, dict) and "class_type" in data:
            return self.is_custom_node(data)
        return False

    def _get_node_ecosystem_method(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Get node ecosystem information."""
        if isinstance(data, dict) and "class_type" in data:
            return self.get_node_ecosystem(data)
        return "unknown"

    def _get_node_complexity_method(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Get node complexity information."""
        if isinstance(data, dict) and "class_type" in data:
            return self.get_node_complexity(data)
        return "unknown"

    def _validate_node_structure_method(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Validate node structure."""
        if isinstance(data, dict):
            return self.validate_node_structure(data)
        return {"valid": False, "errors": ["Data is not a dictionary"]}

    def _extract_node_metadata_method(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract comprehensive node metadata."""
        if isinstance(data, dict):
            return self.extract_node_metadata(data)
        return {}

    def _looks_like_negative_prompt_method(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Check if text looks like a negative prompt."""
        text = method_def.get("target_text", "")
        if not text and isinstance(data, str):
            text = data
        return self.looks_like_negative_prompt(text)
