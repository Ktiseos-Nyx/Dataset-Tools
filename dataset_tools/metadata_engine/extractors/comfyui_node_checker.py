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

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the node checker."""
        self.logger = logger

    def is_text_node(self, node: dict) -> bool:
        """Check if a node is a text-generating node."""
        if not isinstance(node, dict):
            return False
            
        node_type = node.get("class_type", node.get("type", ""))
        text_indicators = [
            "Text", "Prompt", "Wildcard", "String", "CLIPTextEncode",
            "DPRandomGenerator", "RandomGenerator", "ImpactWildcard"
        ]
        return any(indicator in node_type for indicator in text_indicators)

    def is_sampler_node(self, node: dict) -> bool:
        """Check if a node is a sampler node."""
        if not isinstance(node, dict):
            return False
            
        node_type = node.get("class_type", node.get("type", ""))
        sampler_indicators = [
            "Sampler", "KSampler", "Sample", "Generate", "Euler", "DPM",
            "DDIM", "PLMS", "UniPC", "DPMSolver"
        ]
        return any(indicator in node_type for indicator in sampler_indicators)

    def is_model_loader_node(self, node: dict) -> bool:
        """Check if a node is a model loader node."""
        if not isinstance(node, dict):
            return False
            
        node_type = node.get("class_type", node.get("type", ""))
        loader_indicators = [
            "CheckpointLoader", "ModelLoader", "DiffusersLoader",
            "UnCLIPCheckpointLoader", "CheckpointLoaderSimple"
        ]
        return any(indicator in node_type for indicator in loader_indicators)

    def is_lora_node(self, node: dict) -> bool:
        """Check if a node is a LoRA node."""
        if not isinstance(node, dict):
            return False
            
        node_type = node.get("class_type", node.get("type", ""))
        lora_indicators = ["LoRA", "Lora", "LoraLoader", "LoRALoader"]
        return any(indicator in node_type for indicator in lora_indicators)

    def is_vae_node(self, node: dict) -> bool:
        """Check if a node is a VAE node."""
        if not isinstance(node, dict):
            return False
            
        node_type = node.get("class_type", node.get("type", ""))
        vae_indicators = ["VAE", "VaeLoader", "VAELoader", "VAEDecode", "VAEEncode"]
        return any(indicator in node_type for indicator in vae_indicators)

    def is_conditioning_node(self, node: dict) -> bool:
        """Check if a node is a conditioning node."""
        if not isinstance(node, dict):
            return False
            
        node_type = node.get("class_type", node.get("type", ""))
        conditioning_indicators = [
            "Conditioning", "CLIP", "CLIPTextEncode", "CLIPTextEncodeSDXL",
            "ControlNet", "T2IAdapter", "IPAdapter"
        ]
        return any(indicator in node_type for indicator in conditioning_indicators)

    def is_custom_node(self, node: dict) -> bool:
        """Check if a node is from a custom node pack."""
        if not isinstance(node, dict):
            return False
            
        # Check for custom node indicators in properties
        properties = node.get("properties", {})
        if isinstance(properties, dict):
            cnr_id = properties.get("cnr_id", "")
            if cnr_id and cnr_id != "comfy-core":
                return True
        
        # Check for common custom node prefixes
        node_type = node.get("class_type", node.get("type", ""))
        custom_prefixes = [
            "Impact", "Efficiency", "WAS", "ComfyUI-", "rgthree",
            "Inspire", "AnimateDiff", "ControlNet", "IPAdapter",
            "Segment", "Face", "Ultimate", "Advanced", "Custom"
        ]
        return any(prefix in node_type for prefix in custom_prefixes)

    def get_node_ecosystem(self, node: dict) -> str:
        """Determine which ecosystem/node pack a node belongs to."""
        if not isinstance(node, dict):
            return "unknown"
            
        # Check properties for explicit ecosystem info
        properties = node.get("properties", {})
        if isinstance(properties, dict):
            cnr_id = properties.get("cnr_id", "")
            if cnr_id:
                if cnr_id == "comfy-core":
                    return "core"
                return cnr_id.replace("comfyui-", "").replace("-", "_")
        
        # Fallback to node type analysis
        node_type = node.get("class_type", node.get("type", ""))
        
        ecosystems = {
            "impact": ["Impact", "ImpactWildcard"],
            "efficiency": ["Efficiency", "Efficient"],
            "was": ["WAS", "WAS_"],
            "rgthree": ["rgthree", "rg_"],
            "inspire": ["Inspire", "InspirePack"],
            "animatediff": ["AnimateDiff", "Animate"],
            "controlnet": ["ControlNet", "Control"],
            "ipadapter": ["IPAdapter", "IP_Adapter"],
            "ultimate": ["Ultimate", "UltimateSDUpscale"],
            "advanced": ["Advanced", "AdvancedControlNet"],
            "segment": ["Segment", "SAM", "SEGS"],
            "face": ["Face", "FaceDetailer", "FaceSwap"],
            "core": ["CLIPTextEncode", "KSampler", "CheckpointLoader", "VAE"]
        }
        
        for ecosystem, indicators in ecosystems.items():
            if any(indicator in node_type for indicator in indicators):
                return ecosystem
        
        return "custom"

    def get_node_complexity(self, node: dict) -> str:
        """Determine the complexity level of a node."""
        if not isinstance(node, dict):
            return "unknown"
            
        # Count inputs and outputs
        inputs = node.get("inputs", [])
        outputs = node.get("outputs", [])
        widgets = node.get("widgets_values", [])
        
        input_count = len(inputs) if isinstance(inputs, list) else len(inputs) if isinstance(inputs, dict) else 0
        output_count = len(outputs) if isinstance(outputs, list) else 0
        widget_count = len(widgets) if isinstance(widgets, list) else 0
        
        total_complexity = input_count + output_count + widget_count
        
        if total_complexity <= 3:
            return "simple"
        elif total_complexity <= 8:
            return "medium"
        else:
            return "complex"

    def validate_node_structure(self, node: dict) -> dict[str, Any]:
        """Validate a node's structure and return validation results."""
        if not isinstance(node, dict):
            return {"valid": False, "errors": ["Node is not a dictionary"]}
        
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["class_type", "inputs", "outputs"]
        for field in required_fields:
            if field not in node:
                if field == "class_type" and "type" in node:
                    warnings.append(f"Using 'type' instead of 'class_type'")
                else:
                    errors.append(f"Missing required field: {field}")
        
        # Validate inputs structure
        inputs = node.get("inputs", [])
        if inputs and not isinstance(inputs, (list, dict)):
            errors.append("Inputs must be a list or dict")
        
        # Validate outputs structure
        outputs = node.get("outputs", [])
        if outputs and not isinstance(outputs, list):
            errors.append("Outputs must be a list")
        
        # Check for potential issues
        if not node.get("class_type") and not node.get("type"):
            errors.append("Node missing type information")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "complexity": self.get_node_complexity(node),
            "ecosystem": self.get_node_ecosystem(node)
        }

    def looks_like_negative_prompt(self, text: str) -> bool:
        """Check if text looks like a negative prompt."""
        if not isinstance(text, str):
            return False
            
        negative_indicators = [
            "worst quality", "low quality", "normal quality", "lowres",
            "bad anatomy", "bad hands", "text", "error", "missing fingers",
            "extra digit", "fewer digits", "cropped", "worst quality",
            "jpeg artifacts", "signature", "watermark", "username", "blurry",
            "bad feet", "poorly drawn", "extra limbs", "disfigured",
            "deformed", "body out of frame", "bad proportions", "duplicate",
            "morbid", "mutilated", "mutation", "deformed", "blurry"
        ]
        
        text_lower = text.lower()
        negative_count = sum(1 for indicator in negative_indicators if indicator in text_lower)
        
        # If more than 2 negative indicators, likely a negative prompt
        return negative_count >= 2

    def extract_node_metadata(self, node: dict) -> dict[str, Any]:
        """Extract metadata from a node."""
        if not isinstance(node, dict):
            return {}
            
        metadata = {
            "type": node.get("class_type", node.get("type", "")),
            "ecosystem": self.get_node_ecosystem(node),
            "complexity": self.get_node_complexity(node),
            "is_text_node": self.is_text_node(node),
            "is_sampler_node": self.is_sampler_node(node),
            "is_model_loader": self.is_model_loader_node(node),
            "is_lora_node": self.is_lora_node(node),
            "is_vae_node": self.is_vae_node(node),
            "is_conditioning_node": self.is_conditioning_node(node),
            "is_custom_node": self.is_custom_node(node)
        }
        
        # Add properties if available
        properties = node.get("properties", {})
        if isinstance(properties, dict):
            metadata.update({
                "cnr_id": properties.get("cnr_id", ""),
                "version": properties.get("ver", ""),
                "node_name": properties.get("Node name for S&R", "")
            })
        
        return metadata