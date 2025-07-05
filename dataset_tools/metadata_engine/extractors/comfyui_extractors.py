# dataset_tools/metadata_engine/extractors/comfyui_extractors.py

"""
ComfyUI extraction methods.

Handles extraction from ComfyUI workflow JSON structures,
including node traversal and parameter extraction.
"""

import logging
from typing import Any, Dict, Optional

# Type aliases
ContextData = Dict[str, Any]
ExtractedFields = Dict[str, Any]
MethodDefinition = Dict[str, Any]


class ComfyUIExtractor:
    """Handles ComfyUI-specific extraction methods."""

    def __init__(self, logger: logging.Logger):
        """Initialize the ComfyUI extractor."""
        self.logger = logger

    def get_methods(self) -> Dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "comfy_extract_prompts": self._extract_comfy_text_from_clip_encode_nodes,
            "comfy_extract_sampler_settings": self._extract_comfy_sampler_settings,
            "comfy_traverse_for_field": self._extract_comfy_traverse_field,
            "comfy_get_node_by_class": self._extract_comfy_node_by_class,
            "comfy_get_workflow_input": self._extract_comfy_workflow_input,
            # Simple ComfyUI parser methods
            "comfyui_extract_prompt_from_workflow": self._extract_prompt_from_workflow,
            "comfyui_extract_negative_prompt_from_workflow": self._extract_negative_prompt_from_workflow,
            "comfyui_extract_workflow_parameters": self._extract_workflow_parameters,
            "comfyui_extract_raw_workflow": self._extract_raw_workflow,
        }

    def _extract_comfy_text_from_clip_encode_nodes(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> Dict[str, str]:
        """Extract positive/negative prompts from ComfyUI CLIPTextEncode nodes."""
        if not isinstance(data, dict):
            return {}

        prompts = {"positive": "", "negative": ""}

        # Handle workflow format (nodes array)
        if "nodes" in data and isinstance(data["nodes"], list):
            nodes = data["nodes"]
            for node in nodes:
                if not isinstance(node, dict):
                    continue

                # Check if this is a CLIPTextEncode node
                node_type = node.get("type", "")
                if "CLIPTextEncode" not in node_type:
                    continue

                # Extract the text from widgets_values
                widgets_values = node.get("widgets_values", [])
                if widgets_values and len(widgets_values) > 0:
                    text = str(widgets_values[0])
                    
                    if text:
                        # Smart heuristic: detect negative prompts by content
                        text_lower = text.lower()
                        is_negative = (
                            "embedding:negatives" in text or
                            "negatives\\" in text or
                            text.startswith("(") and ":" in text and len(text) < 100 or  # Often negative embeddings
                            "bad" in text_lower or
                            "worst" in text_lower or
                            "low quality" in text_lower
                        )
                        
                        if is_negative and not prompts["negative"]:
                            prompts["negative"] = text
                        elif not is_negative and not prompts["positive"]:
                            prompts["positive"] = text
                        elif not prompts["negative"] and prompts["positive"]:
                            # If we have positive but no negative, this might be negative
                            prompts["negative"] = text
                        elif not prompts["positive"] and prompts["negative"]:
                            # If we have negative but no positive, this might be positive
                            prompts["positive"] = text

        # Handle prompt format (nodes dict) - fallback to original logic
        else:
            nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

            for node_id, node_data in nodes.items():
                if not isinstance(node_data, dict):
                    continue

                # Check if this is a CLIPTextEncode node
                class_type = node_data.get("class_type", node_data.get("type", ""))
                if "CLIPTextEncode" not in class_type:
                    continue

                # Extract the text
                text = ""
                inputs = node_data.get("inputs", {})
                if "text" in inputs:
                    text = str(inputs["text"])
                else:
                    # Fallback to widget values
                    widgets = node_data.get("widgets_values", [])
                    if widgets:
                        text = str(widgets[0])

                if not text:
                    continue

                # Determine if it's positive or negative
                meta = node_data.get("_meta", {})
                title = meta.get("title", "").lower()

                if "negative" in title:
                    prompts["negative"] = text
                elif "positive" in title or not prompts["positive"]:
                    # Use as positive if explicitly marked or if we don't have one yet
                    prompts["positive"] = text

        return prompts

    def _extract_comfy_sampler_settings(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> Dict[str, Any]:
        """Extract sampler settings from ComfyUI KSampler nodes."""
        if not isinstance(data, dict):
            return {}

        settings = {}
        
        # Handle workflow format (nodes array) vs prompt format (nodes dict)
        if "nodes" in data and isinstance(data["nodes"], list):
            # Workflow format - already handled in _extract_workflow_parameters
            return settings
        else:
            # Prompt format
            nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        for node_id, node_data in nodes.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))
            if "KSampler" not in class_type:
                continue

            # Extract from inputs (ComfyUI prompt format)
            inputs = node_data.get("inputs", {})
            if inputs:
                settings.update({
                    "seed": inputs.get("seed"),
                    "steps": inputs.get("steps"),
                    "cfg_scale": inputs.get("cfg"),
                    "sampler_name": inputs.get("sampler_name"),
                    "scheduler": inputs.get("scheduler"),
                    "denoise": inputs.get("denoise")
                })

            # Extract from widgets (ComfyUI workflow format)
            widgets = node_data.get("widgets_values", [])
            if widgets and len(widgets) >= 5:
                try:
                    if not settings.get("seed"):
                        settings["seed"] = int(widgets[0]) if widgets[0] is not None else None
                    if not settings.get("steps"):
                        settings["steps"] = int(widgets[1]) if widgets[1] is not None else None
                    if not settings.get("cfg_scale"):
                        settings["cfg_scale"] = float(widgets[2]) if widgets[2] is not None else None
                    if not settings.get("sampler_name"):
                        settings["sampler_name"] = str(widgets[3]) if widgets[3] is not None else None
                    if not settings.get("scheduler"):
                        settings["scheduler"] = str(widgets[4]) if widgets[4] is not None else None
                except (ValueError, TypeError, IndexError):
                    self.logger.debug(f"Could not parse KSampler widgets from node {node_id}")

            break  # Usually only one main sampler

        # Clean up None values
        return {k: v for k, v in settings.items() if v is not None}

    def _extract_comfy_traverse_field(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> Any:
        """Traverse ComfyUI workflow to extract specific field."""
        if not isinstance(data, dict):
            return None

        node_criteria = method_def.get("node_criteria_list", [])
        target_field = method_def.get("target_input_key")

        # Look for nodes in the data
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", data)

        for node_id, node_data in nodes.items():
            if not isinstance(node_data, dict):
                continue

            # Check against criteria
            for criteria in node_criteria:
                if self._node_matches_criteria(node_data, criteria):
                    return self._extract_field_from_node(node_data, target_field)

        return None

    def _node_matches_criteria(self, node_data: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if a node matches the given criteria."""
        # Check class_type
        if "class_type" in criteria:
            node_class = node_data.get("class_type", node_data.get("type", ""))
            if node_class != criteria["class_type"]:
                return False

        # Check inputs
        if "inputs" in criteria:
            node_inputs = node_data.get("inputs", {})
            for input_key, expected_value in criteria["inputs"].items():
                if node_inputs.get(input_key) != expected_value:
                    return False

        return True

    def _extract_field_from_node(self, node_data: Dict[str, Any], target_field: str) -> Any:
        """Extract a specific field from a ComfyUI node."""
        if target_field == "text":
            inputs = node_data.get("inputs", {})
            if "text" in inputs:
                return inputs["text"]
            widgets = node_data.get("widgets_values", [])
            if widgets:
                return widgets[0]
        elif target_field in node_data.get("inputs", {}):
            return node_data["inputs"][target_field]
        elif target_field in node_data:
            return node_data[target_field]

        return None

    def _extract_comfy_node_by_class(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> Any:
        """Extract data from a ComfyUI node by class type."""
        if not isinstance(data, dict):
            return None

        class_type = method_def.get("class_type")
        field_name = method_def.get("field_name")

        if not class_type or not field_name:
            return None

        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", data)

        for node_id, node_data in nodes.items():
            if not isinstance(node_data, dict):
                continue

            node_class = node_data.get("class_type", node_data.get("type", ""))
            if node_class == class_type:
                return self._extract_field_from_node(node_data, field_name)

        return None

    def _extract_comfy_workflow_input(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> Any:
        """Extract workflow input from ComfyUI data."""
        if not isinstance(data, dict):
            return None

        input_name = method_def.get("input_name")
        if not input_name:
            return None

        # Look for workflow inputs
        if "inputs" in data:
            return data["inputs"].get(input_name)

        # Look in the workflow metadata
        if "workflow" in data:
            workflow = data["workflow"]
            if isinstance(workflow, dict) and "inputs" in workflow:
                return workflow["inputs"].get(input_name)

        return None

    # Simple ComfyUI parser methods for ComfyUI_Simple parser
    
    def _extract_prompt_from_workflow(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> str:
        """Extract positive prompt from ComfyUI workflow."""
        # Parse JSON string if needed
        if isinstance(data, str):
            try:
                import json
                data = json.loads(data)
            except (json.JSONDecodeError, ValueError):
                self.logger.warning("ComfyUI: Failed to parse workflow JSON string")
                return ""
        
        prompts = self._extract_comfy_text_from_clip_encode_nodes(data, method_def, context, fields)
        return prompts.get("positive", "")
    
    def _extract_negative_prompt_from_workflow(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> str:
        """Extract negative prompt from ComfyUI workflow."""
        # Parse JSON string if needed
        if isinstance(data, str):
            try:
                import json
                data = json.loads(data)
            except (json.JSONDecodeError, ValueError):
                self.logger.warning("ComfyUI: Failed to parse workflow JSON string")
                return ""
        
        prompts = self._extract_comfy_text_from_clip_encode_nodes(data, method_def, context, fields)
        return prompts.get("negative", "")
    
    def _extract_workflow_parameters(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> Dict[str, Any]:
        """Extract workflow parameters from ComfyUI data."""
        # Parse JSON string if needed
        if isinstance(data, str):
            try:
                import json
                data = json.loads(data)
            except (json.JSONDecodeError, ValueError):
                self.logger.warning("ComfyUI: Failed to parse workflow JSON string")
                return {}
        
        # Get sampler settings
        sampler_params = self._extract_comfy_sampler_settings(data, method_def, context, fields)
        
        # Add workflow metadata if available
        parameters = {}
        parameters.update(sampler_params)
        
        # Extract model information - handle both prompt and workflow formats
        if isinstance(data, dict):
            # Handle workflow format (nodes array)
            if "nodes" in data and isinstance(data["nodes"], list):
                nodes = data["nodes"]
                for node in nodes:
                    if not isinstance(node, dict):
                        continue
                    
                    node_type = node.get("type", "")
                    widgets_values = node.get("widgets_values", [])
                    
                    # Extract checkpoint/model info
                    if "CheckpointLoader" in node_type:
                        if widgets_values and len(widgets_values) > 0:
                            parameters["model"] = str(widgets_values[0])
                    
                    # Extract KSampler parameters from widgets_values
                    elif "KSampler" in node_type:
                        if widgets_values and len(widgets_values) >= 6:
                            try:
                                parameters["seed"] = int(widgets_values[0]) if widgets_values[0] is not None else None
                                parameters["steps"] = int(widgets_values[1]) if widgets_values[1] is not None else None
                                parameters["cfg_scale"] = float(widgets_values[2]) if widgets_values[2] is not None else None
                                parameters["sampler_name"] = str(widgets_values[3]) if widgets_values[3] is not None else None
                                parameters["scheduler"] = str(widgets_values[4]) if widgets_values[4] is not None else None
                                parameters["denoise"] = float(widgets_values[5]) if widgets_values[5] is not None else None
                            except (ValueError, TypeError, IndexError):
                                self.logger.debug(f"Could not parse KSampler widgets from workflow node")
            
            # Handle prompt format (nodes dict) - fallback to original logic
            else:
                nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})
                
                for node_id, node_data in nodes.items():
                    if not isinstance(node_data, dict):
                        continue
                    
                    class_type = node_data.get("class_type", node_data.get("type", ""))
                    inputs = node_data.get("inputs", {})
                    
                    # Extract checkpoint/model info
                    if "CheckpointLoader" in class_type or "ModelLoader" in class_type:
                        if "ckpt_name" in inputs:
                            parameters["model"] = inputs["ckpt_name"]
                        elif "model_name" in inputs:
                            parameters["model"] = inputs["model_name"]
                    
                    # Extract VAE info
                    elif "VAELoader" in class_type:
                        if "vae_name" in inputs:
                            parameters["vae"] = inputs["vae_name"]
                    
                    # Extract LoRA info
                    elif "LoraLoader" in class_type:
                        if "lora_name" in inputs:
                            lora_name = inputs["lora_name"]
                            lora_strength = inputs.get("strength_model", inputs.get("strength_clip", 1.0))
                            if "loras" not in parameters:
                                parameters["loras"] = []
                            parameters["loras"].append(f"{lora_name}:{lora_strength}")
        
        # Clean up None values
        return {k: v for k, v in parameters.items() if v is not None}
    
    def _extract_raw_workflow(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> str:
        """Extract raw workflow data as string."""
        import json
        
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            try:
                return json.dumps(data, indent=2)
            except (TypeError, ValueError):
                return str(data)
        else:
            return str(data)
