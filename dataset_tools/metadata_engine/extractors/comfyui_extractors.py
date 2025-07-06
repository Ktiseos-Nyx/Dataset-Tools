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
            # Universal ComfyUI parser methods
            "comfy_find_text_from_main_sampler_input": self._find_text_from_main_sampler_input,
            "comfy_find_input_of_main_sampler": self._find_input_of_main_sampler,
            # Fallback methods for simpler extraction
            "comfy_simple_text_extraction": self._simple_text_extraction,
            "comfy_simple_parameter_extraction": self._simple_parameter_extraction,
            # Phase 1 Core missing methods - CRIME #2!
            "comfy_find_ancestor_node_input_value": self._find_ancestor_node_input_value,
            "comfy_find_node_input_or_widget_value": self._find_node_input_or_widget_value,
            "comfy_extract_all_loras": self._extract_all_loras,
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

    def _find_text_from_main_sampler_input(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> str:
        """
        Find text from main sampler input by traversing ComfyUI workflow connections.
        
        This method:
        1. Finds sampler nodes (KSampler, KSamplerAdvanced, etc.)
        2. Follows their positive/negative input connections
        3. Finds the connected text encoder nodes (CLIPTextEncode, etc.)
        4. Extracts the text from those nodes
        """
        self.logger.debug(f"[ComfyUI] _find_text_from_main_sampler_input called with data type: {type(data)}")
        self.logger.debug(f"[ComfyUI] Method definition: {method_def}")
        
        if not isinstance(data, dict):
            self.logger.debug(f"[ComfyUI] Data is not dict, returning empty string")
            return ""

        # Get parameters from method definition
        sampler_node_types = method_def.get("sampler_node_types", ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"])
        positive_input_name = method_def.get("positive_input_name", "positive")
        negative_input_name = method_def.get("negative_input_name", "negative")
        text_input_name = method_def.get("text_input_name_in_encoder", "text")
        text_encoder_types = method_def.get("text_encoder_node_types", ["CLIPTextEncode", "BNK_CLIPTextEncodeAdvanced"])

        # Determine which input to follow (positive or negative)
        target_input_name = positive_input_name  # Default to positive
        if negative_input_name in method_def.get("target_key", ""):
            target_input_name = negative_input_name

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})
        self.logger.debug(f"[ComfyUI] Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}")
        self.logger.debug(f"[ComfyUI] Nodes type: {type(nodes)}, count: {len(nodes) if nodes else 0}")
        
        # Find the main sampler node
        main_sampler = None
        found_samplers = []
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get("class_type", node_data.get("type", ""))
            found_samplers.append(class_type)
            if any(sampler_type in class_type for sampler_type in sampler_node_types):
                main_sampler = (node_id, node_data)
                self.logger.debug(f"[ComfyUI] Found sampler node {node_id}: {class_type}")
                break

        self.logger.debug(f"[ComfyUI] All node types found: {found_samplers[:10]}...")  # First 10 to avoid spam
        if not main_sampler:
            self.logger.debug(f"[ComfyUI] No sampler found matching: {sampler_node_types}")
            return ""

        sampler_id, sampler_node = main_sampler
        
        # Get the input connection for positive/negative
        inputs = sampler_node.get("inputs", {})
        target_connection = inputs.get(target_input_name)
        
        if not target_connection:
            return ""

        # Handle connection format: usually [node_id, output_index]
        if isinstance(target_connection, list) and len(target_connection) >= 1:
            connected_node_id = target_connection[0]
        else:
            return ""

        # Find the connected text encoder node
        if isinstance(nodes, dict):
            # Prompt format
            connected_node = nodes.get(str(connected_node_id))
        else:
            # Workflow format - find by ID
            connected_node = None
            for node in nodes:
                if node.get("id") == connected_node_id or str(node.get("id")) == str(connected_node_id):
                    connected_node = node
                    break

        if not connected_node:
            return ""

        # Check if it's a text encoder node
        connected_class_type = connected_node.get("class_type", connected_node.get("type", ""))
        if not any(encoder_type in connected_class_type for encoder_type in text_encoder_types):
            return ""

        # Extract text from the encoder node
        encoder_inputs = connected_node.get("inputs", {})
        if text_input_name in encoder_inputs:
            return str(encoder_inputs[text_input_name])
        
        # Fallback to widgets_values
        widgets = connected_node.get("widgets_values", [])
        if widgets:
            return str(widgets[0])

        return ""

    def _find_input_of_main_sampler(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> Any:
        """
        Find a specific input value from the main sampler node.
        
        This method:
        1. Finds sampler nodes (KSampler, KSamplerAdvanced, etc.)
        2. Extracts the specified input key (seed, steps, cfg, etc.)
        3. Returns the value with proper type conversion
        """
        self.logger.debug(f"[ComfyUI] _find_input_of_main_sampler called for: {method_def.get('input_key')}")
        if not isinstance(data, dict):
            self.logger.debug(f"[ComfyUI] Data is not dict, returning None")
            return None

        # Get parameters from method definition
        sampler_node_types = method_def.get("sampler_node_types", ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"])
        input_key = method_def.get("input_key")
        value_type = method_def.get("value_type", "string")

        if not input_key:
            return None

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})
        
        # Find the main sampler node
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get("class_type", node_data.get("type", ""))
            if any(sampler_type in class_type for sampler_type in sampler_node_types):
                # Found a sampler node, extract the input
                self.logger.debug(f"[ComfyUI] Found sampler {node_id}: {class_type}, looking for input: {input_key}")
                inputs = node_data.get("inputs", {})
                self.logger.debug(f"[ComfyUI] Sampler inputs: {list(inputs.keys())}")
                value = inputs.get(input_key)
                
                if value is not None:
                    # Type conversion
                    try:
                        if value_type == "integer":
                            return int(value)
                        elif value_type == "float":
                            return float(value)
                        elif value_type == "string":
                            return str(value)
                        else:
                            return value
                    except (ValueError, TypeError):
                        self.logger.debug(f"Could not convert {input_key}={value} to {value_type}")
                        return value
                
                # Fallback to widgets_values for workflow format
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    # Map common input keys to widget positions
                    widget_mapping = {
                        "seed": 0,
                        "steps": 1, 
                        "cfg": 2,
                        "sampler_name": 3,
                        "scheduler": 4,
                        "denoise": 5
                    }
                    
                    widget_index = widget_mapping.get(input_key)
                    if widget_index is not None and len(widgets) > widget_index:
                        value = widgets[widget_index]
                        try:
                            if value_type == "integer":
                                return int(value)
                            elif value_type == "float":
                                return float(value)
                            elif value_type == "string":
                                return str(value)
                            else:
                                return value
                        except (ValueError, TypeError):
                            return value

                break  # Found the main sampler, no need to continue

        return None

    def _simple_text_extraction(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> str:
        """
        Simple fallback text extraction that looks for text in any CLIPTextEncode node.
        This is a more robust fallback when advanced connection traversal fails.
        """
        self.logger.debug(f"[ComfyUI] _simple_text_extraction called")
        if not isinstance(data, dict):
            return ""

        target_key = method_def.get("target_key", "")
        is_negative = "negative" in target_key.lower()
        
        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})
        
        text_nodes = []
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get("class_type", node_data.get("type", ""))
            if "CLIPTextEncode" in class_type or "TextEncode" in class_type:
                # Extract text from this node
                text = ""
                inputs = node_data.get("inputs", {})
                if "text" in inputs:
                    text = str(inputs["text"])
                else:
                    widgets = node_data.get("widgets_values", [])
                    if widgets:
                        text = str(widgets[0])
                
                if text:
                    # Try to determine if it's positive or negative based on content or metadata
                    meta = node_data.get("_meta", {})
                    title = meta.get("title", "").lower()
                    
                    is_node_negative = ("negative" in title or 
                                      "bad" in text.lower() or 
                                      "worst" in text.lower() or
                                      len(text) < 50 and any(word in text.lower() for word in ["low", "quality", "blurry"]))
                    
                    text_nodes.append((text, is_node_negative, node_id))
        
        self.logger.debug(f"[ComfyUI] Found {len(text_nodes)} text nodes, looking for negative={is_negative}")
        
        # Return the first matching text based on positive/negative requirement
        for text, is_node_negative, node_id in text_nodes:
            if is_negative == is_node_negative:
                self.logger.debug(f"[ComfyUI] Returning text from node {node_id}: {text[:50]}...")
                return text
        
        # If no exact match, return first available text if we're looking for positive
        if not is_negative and text_nodes:
            text, _, node_id = text_nodes[0]
            self.logger.debug(f"[ComfyUI] Fallback: returning first text from node {node_id}: {text[:50]}...")
            return text
            
        return ""

    def _simple_parameter_extraction(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> Any:
        """
        Simple fallback parameter extraction that looks for parameters in any KSampler node.
        This is a more robust fallback when advanced connection traversal fails.
        """
        input_key = method_def.get("input_key")
        value_type = method_def.get("value_type", "string")
        
        self.logger.debug(f"[ComfyUI] _simple_parameter_extraction called for: {input_key}")
        if not isinstance(data, dict) or not input_key:
            return None

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})
        
        # Look for any sampler node
        sampler_types = ["KSampler", "Sampler", "CustomSampler"]
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get("class_type", node_data.get("type", ""))
            if any(sampler_type in class_type for sampler_type in sampler_types):
                self.logger.debug(f"[ComfyUI] Found sampler node {node_id}: {class_type}")
                
                # Try to extract from inputs first
                inputs = node_data.get("inputs", {})
                if input_key in inputs:
                    value = inputs[input_key]
                    self.logger.debug(f"[ComfyUI] Found {input_key}={value} in inputs")
                    return self._convert_value_type(value, value_type)
                
                # Fallback to widgets_values
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    widget_mapping = {
                        "seed": 0, "steps": 1, "cfg": 2, "cfg_scale": 2,
                        "sampler_name": 3, "scheduler": 4, "denoise": 5
                    }
                    widget_index = widget_mapping.get(input_key)
                    if widget_index is not None and len(widgets) > widget_index:
                        value = widgets[widget_index]
                        self.logger.debug(f"[ComfyUI] Found {input_key}={value} in widgets[{widget_index}]")
                        return self._convert_value_type(value, value_type)
                
                break  # Found a sampler, don't need to check others
        
        self.logger.debug(f"[ComfyUI] Could not find {input_key} in any sampler node")
        return None

    def _convert_value_type(self, value: Any, value_type: str) -> Any:
        """Helper method to convert values to the specified type."""
        if value is None:
            return None
            
        try:
            if value_type == "integer":
                return int(value)
            elif value_type == "float":
                return float(value)
            elif value_type == "string":
                return str(value)
            else:
                return value
        except (ValueError, TypeError):
            self.logger.debug(f"[ComfyUI] Could not convert {value} to {value_type}")
            return value

    def _find_ancestor_node_input_value(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> Any:
        """
        Find input value from ancestor nodes by traversing the workflow graph.
        
        This method:
        1. Starts from nodes of specific types (start_node_types)
        2. Follows connections through a specific input/output path
        3. Finds ancestor nodes of target types
        4. Extracts the specified input value from those ancestors
        """
        self.logger.debug(f"[ComfyUI] _find_ancestor_node_input_value called")
        if not isinstance(data, dict):
            return None

        # Get parameters from method definition
        start_node_types = method_def.get("start_node_types", [])
        start_node_input_name = method_def.get("start_node_input_name", "model")
        start_node_output_slot_name = method_def.get("start_node_output_slot_name")
        target_ancestor_types = method_def.get("target_ancestor_types", [])
        target_input_key = method_def.get("target_input_key_in_ancestor", "ckpt_name")
        fallback_widget_key = method_def.get("fallback_widget_key_in_ancestor", "ckpt_name")
        value_type = method_def.get("value_type", "string")

        if not start_node_types or not target_ancestor_types:
            self.logger.debug(f"[ComfyUI] Missing required node types in method definition")
            return None

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        # Find the starting node
        start_node = None
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get("class_type", node_data.get("type", ""))
            if any(start_type in class_type for start_type in start_node_types):
                start_node = (node_id, node_data)
                self.logger.debug(f"[ComfyUI] Found start node {node_id}: {class_type}")
                break

        if not start_node:
            self.logger.debug(f"[ComfyUI] No start node found matching: {start_node_types}")
            return None

        start_id, start_data = start_node
        
        # Get the connection to follow
        if start_node_output_slot_name:
            # Following an output connection (for VAE, etc.)
            connection_id = None
            # This would need more complex logic to follow output connections
            # For now, let's implement the simpler input-following logic
        else:
            # Following an input connection (more common)
            inputs = start_data.get("inputs", {})
            connection = inputs.get(start_node_input_name)
            
            if not connection or not isinstance(connection, list) or len(connection) < 1:
                self.logger.debug(f"[ComfyUI] No valid connection found for {start_node_input_name}")
                return None
                
            connection_id = connection[0]

        # Find the ancestor node
        if isinstance(nodes, dict):
            ancestor_node = nodes.get(str(connection_id))
        else:
            ancestor_node = None
            for node in nodes:
                if node.get("id") == connection_id or str(node.get("id")) == str(connection_id):
                    ancestor_node = node
                    break

        if not ancestor_node:
            self.logger.debug(f"[ComfyUI] Ancestor node {connection_id} not found")
            return None

        # Check if it's the target ancestor type
        ancestor_class_type = ancestor_node.get("class_type", ancestor_node.get("type", ""))
        if not any(target_type in ancestor_class_type for target_type in target_ancestor_types):
            self.logger.debug(f"[ComfyUI] Ancestor {ancestor_class_type} doesn't match target types: {target_ancestor_types}")
            return None

        self.logger.debug(f"[ComfyUI] Found target ancestor: {ancestor_class_type}")

        # Extract the value from the ancestor
        ancestor_inputs = ancestor_node.get("inputs", {})
        if target_input_key in ancestor_inputs:
            value = ancestor_inputs[target_input_key]
            self.logger.debug(f"[ComfyUI] Found {target_input_key}={value} in ancestor inputs")
            return self._convert_value_type(value, value_type)

        # Fallback to widget values
        ancestor_widgets = ancestor_node.get("widgets_values", [])
        if ancestor_widgets and fallback_widget_key:
            # For now, assume the widget is the first value
            value = ancestor_widgets[0] if ancestor_widgets else None
            if value is not None:
                self.logger.debug(f"[ComfyUI] Found {fallback_widget_key}={value} in ancestor widgets")
                return self._convert_value_type(value, value_type)

        self.logger.debug(f"[ComfyUI] Could not find {target_input_key} in ancestor node")
        return None

    def _find_node_input_or_widget_value(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> Any:
        """
        Find value from either node inputs or widget values based on node criteria.
        
        This method:
        1. Finds nodes matching the given criteria
        2. Tries to extract from inputs first
        3. Falls back to widget values if inputs don't have the value
        4. Handles preset regex extraction for special cases
        """
        self.logger.debug(f"[ComfyUI] _find_node_input_or_widget_value called")
        if not isinstance(data, dict):
            return None

        # Get parameters from method definition
        node_criteria = method_def.get("node_criteria", [])
        input_key = method_def.get("input_key", "width")
        widget_key_for_preset = method_def.get("widget_key_for_preset")
        preset_regex_width = method_def.get("preset_regex_width")
        preset_regex_height = method_def.get("preset_regex_height")
        value_type = method_def.get("value_type", "string")

        if not node_criteria:
            self.logger.debug(f"[ComfyUI] No node criteria provided")
            return None

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        # Find nodes matching criteria
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if not isinstance(node_data, dict):
                continue

            # Check if node matches any of the criteria
            node_class_type = node_data.get("class_type", node_data.get("type", ""))
            matches_criteria = False
            
            for criteria in node_criteria:
                required_class_type = criteria.get("class_type")
                if required_class_type and required_class_type in node_class_type:
                    matches_criteria = True
                    break

            if not matches_criteria:
                continue

            self.logger.debug(f"[ComfyUI] Found matching node {node_id}: {node_class_type}")

            # Try to extract from inputs first
            inputs = node_data.get("inputs", {})
            if input_key in inputs:
                value = inputs[input_key]
                self.logger.debug(f"[ComfyUI] Found {input_key}={value} in node inputs")
                return self._convert_value_type(value, value_type)

            # Handle preset regex extraction
            if widget_key_for_preset and (preset_regex_width or preset_regex_height):
                widgets = node_data.get("widgets_values", [])
                # Look for preset in inputs or widgets
                preset_value = inputs.get(widget_key_for_preset)
                if not preset_value and widgets:
                    # Assume preset is the first widget if not in inputs
                    preset_value = widgets[0] if widgets else None

                if preset_value:
                    import re
                    preset_str = str(preset_value)
                    
                    if preset_regex_width and input_key == "width":
                        match = re.search(preset_regex_width, preset_str)
                        if match:
                            value = match.group(1)
                            self.logger.debug(f"[ComfyUI] Extracted width={value} from preset: {preset_str}")
                            return self._convert_value_type(value, value_type)
                    
                    if preset_regex_height and input_key == "height":
                        match = re.search(preset_regex_height, preset_str)
                        if match:
                            value = match.group(1)
                            self.logger.debug(f"[ComfyUI] Extracted height={value} from preset: {preset_str}")
                            return self._convert_value_type(value, value_type)

            # Fallback to direct widget value (for simple cases)
            widgets = node_data.get("widgets_values", [])
            if widgets:
                # For width/height, often the first two widgets
                widget_mapping = {"width": 0, "height": 1}
                widget_index = widget_mapping.get(input_key, 0)
                if len(widgets) > widget_index:
                    value = widgets[widget_index]
                    self.logger.debug(f"[ComfyUI] Found {input_key}={value} in widget[{widget_index}]")
                    return self._convert_value_type(value, value_type)

            break  # Found matching node, no need to continue

        self.logger.debug(f"[ComfyUI] Could not find {input_key} in any matching node")
        return None

    def _extract_all_loras(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> list:
        """
        Extract all LoRA information from the workflow.
        
        This method:
        1. Finds all LoRA loader nodes
        2. Extracts name, model strength, and clip strength
        3. Returns a list of LoRA dictionaries
        """
        self.logger.debug(f"[ComfyUI] _extract_all_loras called")
        if not isinstance(data, dict):
            return []

        # Get parameters from method definition
        lora_node_types = method_def.get("lora_node_types", ["LoraLoader", "LoraTagLoader"])
        name_input_key = method_def.get("name_input_key", "lora_name")
        strength_model_key = method_def.get("strength_model_key", "strength_model")
        strength_clip_key = method_def.get("strength_clip_key", "strength_clip")
        text_key_for_tag_loader = method_def.get("text_key_for_tag_loader", "text")

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        loras = []
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))
            if not any(lora_type in class_type for lora_type in lora_node_types):
                continue

            self.logger.debug(f"[ComfyUI] Found LoRA node {node_id}: {class_type}")

            inputs = node_data.get("inputs", {})
            lora_info = {}

            # Extract LoRA name
            lora_name = inputs.get(name_input_key)
            if lora_name:
                lora_info["name"] = str(lora_name)
            elif "TagLoader" in class_type:
                # For tag loaders, the name might be in the text field
                lora_name = inputs.get(text_key_for_tag_loader)
                if lora_name:
                    lora_info["name"] = str(lora_name)

            # Extract strengths
            strength_model = inputs.get(strength_model_key)
            if strength_model is not None:
                try:
                    lora_info["strength_model"] = float(strength_model)
                except (ValueError, TypeError):
                    lora_info["strength_model"] = 1.0

            strength_clip = inputs.get(strength_clip_key)
            if strength_clip is not None:
                try:
                    lora_info["strength_clip"] = float(strength_clip)
                except (ValueError, TypeError):
                    lora_info["strength_clip"] = 1.0

            # Only add if we found a name
            if "name" in lora_info:
                loras.append(lora_info)
                self.logger.debug(f"[ComfyUI] Added LoRA: {lora_info}")

        self.logger.debug(f"[ComfyUI] Found {len(loras)} LoRAs total")
        return loras
