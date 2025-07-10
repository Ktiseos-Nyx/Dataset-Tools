from typing import Any, Dict, Optional, Union
import logging
import re

# Assuming ContextData, ExtractedFields, MethodDefinition are defined elsewhere or can be imported
# For this snippet, we'll define them as simple dicts for clarity.
ContextData = Dict[str, Any]
ExtractedFields = Dict[str, Any]
MethodDefinition = Dict[str, Any]

class ComfyUIExtractor:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def _clean_prompt_text(self, text: str) -> str:
        """
        Clean embedding prefixes and other artifacts from prompt text.
        """
        if not isinstance(text, str):
            return text
        
        text = re.sub(r'^embedding:negatives\\?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^embedding:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^negatives\\', '', text, flags=re.IGNORECASE)
        text = text.strip()
        
        return text

    def _find_node_by_id(self, nodes: Any, node_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Find a node by its ID in either list or dict format."""
        if isinstance(nodes, dict):
            return nodes.get(str(node_id))
        elif isinstance(nodes, list):
            for node in nodes:
                if str(node.get("id", "")) == str(node_id):
                    return node
        return None

    def _find_text_from_main_sampler_input(
        self, data: Any, method_def: MethodDefinition, context: ContextData, fields: ExtractedFields
    ) -> str:
        """
        Find text from main sampler input by traversing ComfyUI workflow connections.
        This method now performs a backward traversal from the sampler to find the
        originating text encoder, navigating through reroute nodes.
        """
        self.logger.debug("[ComfyUI] Starting advanced text traversal...")
        if not isinstance(data, dict):
            return ""

        sampler_node_types = method_def.get("sampler_node_types", ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"])
        text_input_name_in_encoder = method_def.get("text_input_name_in_encoder", "text")
        text_encoder_types = method_def.get("text_encoder_node_types", ["CLIPTextEncode", "BNK_CLIPTextEncodeAdvanced"])
        
        # Determine which input to follow (positive or negative)
        if method_def.get("positive_input_name"):
            target_input_name = method_def.get("positive_input_name")
        elif method_def.get("negative_input_name"):
            target_input_name = method_def.get("negative_input_name")
        else:
            target_input_name = "positive"

        nodes = data.get("nodes", data)
        if not isinstance(nodes, (dict, list)):
            return ""

        # 1. Find the main sampler node
        main_sampler = None
        node_iterator = nodes.items() if isinstance(nodes, dict) else enumerate(nodes)
        for node_id, node_data in node_iterator:
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))
                if any(sampler_type in class_type for sampler_type in sampler_node_types):
                    main_sampler = node_data
                    self.logger.debug(f"[ComfyUI] Found main sampler: {class_type} (ID: {node_data.get('id', node_id)})")
                    break
        
        if not main_sampler:
            self.logger.debug("[ComfyUI] No main sampler node found.")
            return ""

        # 2. Get the initial connection from the sampler
        inputs = main_sampler.get("inputs", {})
        target_connection = None
        if isinstance(inputs, dict):
            target_connection = inputs.get(target_input_name)
        elif isinstance(inputs, list):
            for input_item in inputs:
                if isinstance(input_item, dict) and input_item.get("name") == target_input_name:
                    link_id = input_item.get("link")
                    if link_id is not None:
                        target_connection = [link_id, 0]
                    break
        
        if not target_connection or not isinstance(target_connection, list) or len(target_connection) == 0:
            self.logger.debug(f"[ComfyUI] No initial connection found for '{target_input_name}'.")
            return ""

        # 3. Traverse backwards from the connection
        current_node_id = target_connection[0]
        
        MAX_TRAVERSAL_DEPTH = 20
        for i in range(MAX_TRAVERSAL_DEPTH):
            self.logger.debug(f"[ComfyUI] Traversal depth {i+1}, current node ID: {current_node_id}")
            
            current_node = self._find_node_by_id(nodes, current_node_id)
            if not current_node:
                self.logger.debug(f"[ComfyUI] Traversal failed: Node ID {current_node_id} not found.")
                return ""

            class_type = current_node.get("class_type", current_node.get("type", ""))
            
            # 4a. Check if we found a text encoder
            if any(encoder_type in class_type for encoder_type in text_encoder_types):
                self.logger.debug(f"[ComfyUI] Found text encoder: {class_type}")
                encoder_inputs = current_node.get("inputs", {})
                if text_input_name_in_encoder in encoder_inputs:
                    text = str(encoder_inputs[text_input_name_in_encoder])
                    return self._clean_prompt_text(text)
                
                widgets = current_node.get("widgets_values", [])
                if widgets:
                    text = str(widgets[0])
                    return self._clean_prompt_text(text)
                return ""

            # 4b. Check if it's a passthrough/reroute node
            node_inputs = current_node.get("inputs", {})
            if "Reroute" in class_type or len(node_inputs) == 1:
                self.logger.debug(f"[ComfyUI] Traversing through passthrough node: {class_type}.")
                
                next_connection = None
                if isinstance(node_inputs, dict) and node_inputs:
                    first_input_key = next(iter(node_inputs))
                    next_connection = node_inputs.get(first_input_key)
                elif isinstance(node_inputs, list) and node_inputs:
                    link_id = node_inputs[0].get("link")
                    if link_id is not None:
                        next_connection = [link_id, 0]

                if isinstance(next_connection, list) and len(next_connection) > 0:
                    current_node_id = next_connection[0]
                    continue
            
            self.logger.debug(f"[ComfyUI] Traversal stopped at node type: {class_type}. Not a recognized text encoder or passthrough node.")
            return ""

        self.logger.warning("[ComfyUI] Traversal depth limit reached, could not find text encoder.")
        return ""