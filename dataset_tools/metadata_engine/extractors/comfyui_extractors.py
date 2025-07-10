# dataset_tools/metadata_engine/extractors/comfyui_extractors.py

"""ComfyUI extraction methods.

Handles extraction from ComfyUI workflow JSON structures,
including node traversal and parameter extraction.

This is now a facade that delegates to the specialized extractors.
"""

import logging
from typing import Any, Dict, Optional, Union

from .comfyui_extractor_manager import ComfyUIExtractorManager

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIExtractor:
    """Handles ComfyUI-specific extraction methods.
    
    This class now acts as a facade that delegates to the 
    ComfyUIExtractorManager and its specialized extractors.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the ComfyUI extractor."""
        self.logger = logger
        self.logger.info("[ComfyUI EXTRACTOR] ComfyUIExtractor starting initialization...")
        try:
            # Initialize the extractor manager that handles all the specialized extractors
            self.manager = ComfyUIExtractorManager(logger)
            self.logger.info("[ComfyUI EXTRACTOR] ComfyUIExtractor initialized successfully!")
        except Exception as e:
            self.logger.error(f"[ComfyUI EXTRACTOR] Failed to initialize: {e}")
            raise
    
    def _parse_json_data(self, data: Any) -> Any:
        """Helper to parse JSON string data if needed."""
        if isinstance(data, str):
            try:
                import json
                return json.loads(data)
            except:
                return {}
        return data

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        self.logger.info("[ComfyUI EXTRACTOR] get_methods() called")
        # Get all methods from the manager
        methods = self.manager.get_methods()
        
        # Add legacy method mappings for backward compatibility
        legacy_methods = {
            "comfy_extract_prompts": self._extract_legacy_prompts,
            "comfy_extract_sampler_settings": self._extract_legacy_sampler_settings,
            "comfy_traverse_for_field": self._extract_legacy_traverse_field,
            "comfy_get_node_by_class": self._extract_legacy_node_by_class,
            "comfy_get_workflow_input": self._extract_legacy_workflow_input,
            "comfy_find_text_from_main_sampler_input": self._find_legacy_text_from_main_sampler_input,
            "comfyui_extract_flux_positive_prompt": self._extract_flux_positive_prompt,
            "comfyui_extract_flux_negative_prompt": self._extract_flux_negative_prompt,
            "comfy_find_input_of_main_sampler": self._find_legacy_input_of_main_sampler,
            "comfy_simple_text_extraction": self._simple_legacy_text_extraction,
            "comfy_simple_parameter_extraction": self._simple_legacy_parameter_extraction,
            "comfy_find_ancestor_node_input_value": self._find_legacy_ancestor_node_input_value,
            "comfy_find_node_input_or_widget_value": self._find_legacy_node_input_or_widget_value,
            "comfy_extract_all_loras": self._extract_legacy_all_loras,
            "comfyui_extract_prompt_from_workflow": self._extract_legacy_prompt_from_workflow,
            "comfyui_extract_negative_prompt_from_workflow": self._extract_legacy_negative_prompt_from_workflow,
            "comfyui_extract_workflow_parameters": self._extract_legacy_workflow_parameters,
            "comfyui_extract_raw_workflow": self._extract_legacy_raw_workflow,
            "comfy_detect_custom_nodes": self._detect_legacy_custom_nodes,
            "comfy_find_input_of_node_type": self._find_legacy_input_of_node_type,
            "comfy_find_all_lora_nodes": self._extract_legacy_all_loras,
        }
        
        # Merge methods, with new methods taking precedence
        methods.update(legacy_methods)
        
        return methods

    def _find_legacy_input_of_node_type(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Legacy find input of node type."""
        print(f"\n--- [FACADE] Running: _find_legacy_input_of_node_type ---")
        data = self._parse_json_data(data)
        # This method is not fully implemented in the manager yet, returning placeholder
        self.logger.info("Placeholder for _find_legacy_input_of_node_type called.")
        return None

    # Legacy method implementations that delegate to the new system
    def _extract_legacy_prompts(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Legacy prompt extraction - NEW BRUTE-FORCE WIRING."""
        data = self._parse_json_data(data)
        if not isinstance(data, dict):
            return ""

        nodes = self.manager.traversal.get_nodes_from_data(data)
        if not nodes:
            return ""

        # Find the KSampler node and follow its positive input back to the source text node
        positive_text = self._find_sampler_input_text(nodes, data, "positive")
        if positive_text:
            return self._clean_prompt_text(positive_text)
        
        return ""
    
    def _is_text_node(self, node_data: dict) -> bool:
        """Check if a node is a text node."""
        class_type = node_data.get("class_type", node_data.get("type", ""))
        text_node_types = ["CLIPTextEncode", "BNK_CLIPTextEncodeAdvanced", "TextInput"]
        return any(text_type in class_type for text_type in text_node_types)
    
    def _looks_like_negative_prompt(self, text: str) -> bool:
        """Check if text looks like a negative prompt."""
        if not isinstance(text, str):
            return False
        negative_indicators = ["embedding:negatives", "negatives\\", "negative", "bad", "worst"]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in negative_indicators)
    
    def _clean_prompt_text(self, text: str) -> str:
        """Clean embedding prefixes and other artifacts from prompt text."""
        if not isinstance(text, str):
            return str(text)
        
        import re
        # Remove embedding prefixes
        text = re.sub(r'^embedding:negatives\\?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^embedding:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^negatives\\', '', text, flags=re.IGNORECASE)
        text = text.strip()
        
        return text
    
    def _find_sampler_input_text(self, nodes: list | dict, data: dict, input_type: str) -> str:
        """Find text from sampler input by following workflow connections."""
        # Find the sampler node (support multiple sampler types)
        sampler_node = None
        sampler_id = None
        
        # List of all supported sampler types
        sampler_types = ["KSampler", "KSamplerAdvanced", "SamplerCustom", "SamplerCustomAdvanced"]
        
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))
                if any(sampler_type in class_type for sampler_type in sampler_types):
                    sampler_node = node_data
                    sampler_id = node_data.get("id", node_id)
                    break
        
        if not sampler_node:
            return ""
        
        # Find the input link for positive/negative
        target_link_id = None
        inputs = sampler_node.get("inputs", [])
        
        for input_info in inputs:
            if isinstance(input_info, dict) and input_info.get("name") == input_type:
                target_link_id = input_info.get("link")
                break
        
        if not target_link_id:
            return ""
        
        # Find the source node for this link
        # Links format: [link_id, source_node_id, source_output_index, target_node_id, target_input_index, connection_type]
        links = data.get("links", [])
        source_node_id = None
        
        # Find the link that matches our target_link_id
        for link in links:
            if len(link) >= 4 and link[0] == target_link_id:
                source_node_id = link[1]
                break
        
        if not source_node_id:
            return ""
        
        # Get the text from the source node
        source_node = self._find_node_by_id(nodes, source_node_id)
        if source_node and self._is_text_node(source_node):
            widgets_values = source_node.get("widgets_values", [])
            if widgets_values:
                return str(widgets_values[0])
        
        return ""

    def _extract_legacy_sampler_settings(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Legacy sampler settings extraction."""
        # Parse JSON data if needed
        data = self._parse_json_data(data)
        workflow_types = self.manager._auto_detect_workflow(data, method_def, context, fields)
        
        # Try architecture-specific extraction first
        if "flux" in workflow_types:
            return self.manager.flux._extract_scheduler_params(data, method_def, context, fields)
        elif "sdxl" in workflow_types:
            return {"sampler_type": "sdxl", "detected": True}
        elif "efficiency" in workflow_types:
            return self.manager.efficiency._extract_sampler_params(data, method_def, context, fields)
        elif "searge" in workflow_types:
            return self.manager.searge._extract_sampler_params(data, method_def, context, fields)
        
        # Fallback to generic extraction
        return {"sampler_type": "unknown", "detected": False}

    def _extract_legacy_traverse_field(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Legacy traverse field - now uses proper traversal."""
        # Use the traversal extractor
        nodes = self.manager.traversal.get_nodes_from_data(data)
        if not nodes:
            return None
            
        # Find the field in the workflow
        field_name = method_def.get("field_name", "")
        if not field_name:
            return None
            
        # Simple field search
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if isinstance(node_data, dict):
                if field_name in node_data:
                    return node_data[field_name]
                    
                # Check widgets
                widgets = node_data.get("widgets_values", [])
                if widgets and field_name == "text" and isinstance(widgets[0], str):
                    return widgets[0]
        
        return None

    def _extract_legacy_node_by_class(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Legacy node by class - now uses node checker."""
        target_class = method_def.get("class_name", "")
        if not target_class:
            return {}
            
        nodes = self.manager.traversal.get_nodes_from_data(data)
        if not nodes:
            return {}
            
        # Find nodes by class
        matching_nodes = {}
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))
                if target_class in class_type:
                    matching_nodes[str(node_id)] = node_data
        
        return matching_nodes

    def _extract_legacy_workflow_input(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Legacy workflow input extraction."""
        input_name = method_def.get("input_name", "")
        if not input_name:
            return None
            
        # Check if it's directly in the data
        if isinstance(data, dict) and input_name in data:
            return data[input_name]
            
        # Check nodes for input
        nodes = self.manager.traversal.get_nodes_from_data(data)
        if not nodes:
            return None
            
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if isinstance(node_data, dict):
                inputs = node_data.get("inputs", {})
                if isinstance(inputs, dict) and input_name in inputs:
                    return inputs[input_name]
        
        return None

    def _find_legacy_text_from_main_sampler_input(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """
        Find text from main sampler input by traversing ComfyUI workflow connections.
        This method performs a backward traversal from the sampler to find the
        originating text encoder, navigating through reroute nodes.
        """
        self.logger.info(f"[ComfyUI EXTRACTOR] ============ STARTING EXTRACTION ============")
        self.logger.info(f"[ComfyUI EXTRACTOR] Method def: {method_def}")
        data = self._parse_json_data(data)
        if not isinstance(data, dict):
            return ""

        sampler_node_types = method_def.get("sampler_node_types", ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"])
        text_input_name_in_encoder = method_def.get("text_input_name_in_encoder", "text")
        text_encoder_types = method_def.get("text_encoder_node_types", ["CLIPTextEncode", "BNK_CLIPTextEncodeAdvanced"])
        
        # Determine which input to follow (positive or negative)
        if method_def.get("positive_input_name"):
            target_input_name = method_def.get("positive_input_name")
            self.logger.info(f"[ComfyUI EXTRACTOR] EXTRACTING POSITIVE PROMPT")
        elif method_def.get("negative_input_name"):
            target_input_name = method_def.get("negative_input_name")
            self.logger.info(f"[ComfyUI EXTRACTOR] EXTRACTING NEGATIVE PROMPT")
        else:
            target_input_name = "positive"
            self.logger.info(f"[ComfyUI EXTRACTOR] DEFAULTING TO POSITIVE")
        
        self.logger.info(f"[ComfyUI EXTRACTOR] Target input name: {target_input_name}")

        nodes = data.get("nodes", data)
        if not isinstance(nodes, (dict, list)):
            return ""

        # Debug: Show all nodes
        self.logger.info(f"[ComfyUI EXTRACTOR] === WORKFLOW NODES ===")
        node_iterator = nodes.items() if isinstance(nodes, dict) else enumerate(nodes)
        for node_id, node_data in node_iterator:
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))
                widgets = node_data.get("widgets_values", [])
                text_preview = str(widgets[0])[:50] if widgets else "No text"
                self.logger.info(f"[ComfyUI EXTRACTOR] Node {node_data.get('id', node_id)}: {class_type} - {text_preview}")

        # 1. Find the main sampler node or FLUX BasicGuider
        main_sampler = None
        # Support multiple sampler types including FLUX samplers and BasicGuider
        all_sampler_types = sampler_node_types + ["SamplerCustom", "SamplerCustomAdvanced", "BasicGuider"]
        node_iterator = nodes.items() if isinstance(nodes, dict) else enumerate(nodes)
        for node_id, node_data in node_iterator:
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))
                if any(sampler_type in class_type for sampler_type in all_sampler_types):
                    main_sampler = node_data
                    self.logger.info(f"[ComfyUI EXTRACTOR] *** Found main sampler/guider: {class_type} (ID: {node_data.get('id', node_id)}) ***")
                    # Debug sampler inputs
                    inputs = main_sampler.get("inputs", [])
                    self.logger.info(f"[ComfyUI EXTRACTOR] Sampler/Guider inputs: {inputs}")
                    break
        
        if not main_sampler:
            self.logger.info("[ComfyUI EXTRACTOR] ❌ No main sampler or guider node found.")
            return ""

        # 2. Get the link ID for the target input (positive or negative)
        target_link_id = None
        inputs = main_sampler.get("inputs", [])
        
        self.logger.info(f"[ComfyUI EXTRACTOR] Looking for '{target_input_name}' input in sampler/guider inputs: {inputs}")
        
        # First try exact match
        for input_item in inputs:
            if isinstance(input_item, dict) and input_item.get("name") == target_input_name:
                target_link_id = input_item.get("link")
                self.logger.info(f"[ComfyUI EXTRACTOR] *** Found '{target_input_name}' input with link: {target_link_id} ***")
                break
        
        # FLUX fallback: If looking for positive and no exact match, try "conditioning"
        if target_link_id is None and target_input_name == "positive":
            for input_item in inputs:
                if isinstance(input_item, dict) and input_item.get("name") == "conditioning":
                    target_link_id = input_item.get("link")
                    self.logger.info(f"[ComfyUI EXTRACTOR] *** FLUX fallback: Found 'conditioning' input with link: {target_link_id} ***")
                    break
        
        # If looking for negative and no exact match found, return empty (FLUX often has no negative)
        if target_link_id is None:
            if target_input_name == "negative":
                self.logger.info(f"[ComfyUI EXTRACTOR] ❓ No negative input found (common in FLUX workflows)")
                return ""
            else:
                self.logger.info(f"[ComfyUI EXTRACTOR] ❌ No link found for '{target_input_name}' input.")
                return ""

        # Debug: Show all links
        links = data.get("links", [])
        self.logger.info(f"[ComfyUI EXTRACTOR] === ALL LINKS ===")
        for link in links:
            if len(link) >= 6:
                self.logger.info(f"[ComfyUI EXTRACTOR] Link {link[0]}: Node {link[1]} output {link[2]} → Node {link[3]} input {link[4]} ({link[5]})")

        # 3. Find the source node for this link using the links array
        source_node_id = None
        
        # Links format: [link_id, source_node_id, source_output_idx, target_node_id, target_input_idx, type]
        # We need to find the link where link_id matches our target_link_id
        for link in links:
            if len(link) >= 4 and link[0] == target_link_id:
                source_node_id = link[1]  # Source node ID is at index 1
                self.logger.info(f"[ComfyUI EXTRACTOR] *** Found link {target_link_id}: source node {source_node_id} ***")
                break
        
        if source_node_id is None:
            self.logger.info(f"[ComfyUI EXTRACTOR] ❌ No source node found for link {target_link_id}.")
            return ""

        # 4. Traverse to find the actual text content (handling complex workflows)
        current_node_id = source_node_id
        
        MAX_TRAVERSAL_DEPTH = 10
        for depth in range(MAX_TRAVERSAL_DEPTH):
            current_node = self._find_node_by_id(nodes, current_node_id)
            if not current_node:
                self.logger.info(f"[ComfyUI EXTRACTOR] ❌ Node {current_node_id} not found at depth {depth}.")
                return ""

            class_type = current_node.get("class_type", current_node.get("type", ""))
            self.logger.info(f"[ComfyUI EXTRACTOR] *** Depth {depth}: Examining node {current_node_id} of type: {class_type} ***")
            
            # Check if it's a text encoder
            if any(encoder_type in class_type for encoder_type in text_encoder_types):
                self.logger.info(f"[ComfyUI EXTRACTOR] ✅ Found text encoder: {class_type}")
                
                # Get text from widgets_values
                widgets = current_node.get("widgets_values", [])
                if widgets:
                    text = str(widgets[0])
                    self.logger.info(f"[ComfyUI EXTRACTOR] *** EXTRACTED TEXT: {text[:100]}... ***")
                    return self._clean_prompt_text(text)
                    
                # Fallback: check inputs
                encoder_inputs = current_node.get("inputs", {})
                if text_input_name_in_encoder in encoder_inputs:
                    text = str(encoder_inputs[text_input_name_in_encoder])
                    self.logger.info(f"[ComfyUI EXTRACTOR] *** EXTRACTED TEXT FROM INPUTS: {text[:100]}... ***")
                    return self._clean_prompt_text(text)
                    
                self.logger.info(f"[ComfyUI EXTRACTOR] ❌ No text found in encoder node")
                return ""
            
            # Handle Efficient Loader pattern - look for String Literal inputs
            elif "Loader" in class_type:
                self.logger.info(f"[ComfyUI EXTRACTOR] 🔄 Found loader node: {class_type}, checking inputs...")
                
                # Look for string inputs that might be our text
                node_inputs = current_node.get("inputs", [])
                for input_item in node_inputs:
                    input_name = input_item.get("name", "")
                    # Check if this input matches what we're looking for
                    if (target_input_name == "positive" and input_name in ["positive", "pos"]) or \
                       (target_input_name == "negative" and input_name in ["negative", "neg"]):
                        
                        input_link = input_item.get("link")
                        if input_link:
                            # Find the source of this input
                            for link in links:
                                if len(link) >= 4 and link[0] == input_link:
                                    current_node_id = link[1]
                                    self.logger.info(f"[ComfyUI EXTRACTOR] 🔄 Following {input_name} input to node {current_node_id}")
                                    break
                            else:
                                self.logger.info(f"[ComfyUI EXTRACTOR] ❌ Link {input_link} not found")
                                return ""
                            break
                else:
                    self.logger.info(f"[ComfyUI EXTRACTOR] ❌ No matching input found in loader")
                    return ""
                continue
            
            # Handle FluxGuidance and other intermediate nodes (just follow the input)
            elif class_type in ["FluxGuidance", "ConditioningSubtract", "ConditioningAddConDelta", "CFGlessNegativePrompt"]:
                self.logger.info(f"[ComfyUI EXTRACTOR] 🔄 Found intermediate node: {class_type}, following input...")
                
                # For these nodes, just follow the first conditioning input
                node_inputs = current_node.get("inputs", [])
                for input_item in node_inputs:
                    input_name = input_item.get("name", "")
                    if "conditioning" in input_name.lower():
                        input_link = input_item.get("link")
                        if input_link:
                            # Find the source of this input
                            for link in links:
                                if len(link) >= 4 and link[0] == input_link:
                                    current_node_id = link[1]
                                    self.logger.info(f"[ComfyUI EXTRACTOR] 🔄 Following conditioning input to node {current_node_id}")
                                    break
                            else:
                                self.logger.info(f"[ComfyUI EXTRACTOR] ❌ Link {input_link} not found")
                                return ""
                            break
                else:
                    self.logger.info(f"[ComfyUI EXTRACTOR] ❌ No conditioning input found in {class_type}")
                    return ""
                continue
            
            # Handle String Literal nodes (direct text input)
            elif "String Literal" in class_type:
                self.logger.info(f"[ComfyUI EXTRACTOR] ✅ Found String Literal node")
                widgets = current_node.get("widgets_values", [])
                if widgets:
                    text = str(widgets[0])
                    self.logger.info(f"[ComfyUI EXTRACTOR] *** EXTRACTED TEXT FROM STRING LITERAL: {text[:100]}... ***")
                    return self._clean_prompt_text(text)
                else:
                    self.logger.info(f"[ComfyUI EXTRACTOR] ❌ No text in String Literal")
                    return ""
            
            else:
                self.logger.info(f"[ComfyUI EXTRACTOR] ❌ Unhandled node type: {class_type}")
                return ""
        
        self.logger.info(f"[ComfyUI EXTRACTOR] ❌ Max traversal depth reached")
        return ""
    
    def _find_node_by_id(self, nodes: Any, node_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Find a node by its ID in either list or dict format."""
        if isinstance(nodes, dict):
            return nodes.get(str(node_id))
        elif isinstance(nodes, list):
            for node in nodes:
                if str(node.get("id", "")) == str(node_id):
                    return node
        return None

    def _extract_flux_positive_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract positive prompt from FLUX workflow via BasicGuider."""
        self.logger.debug("[FLUX] Extracting positive prompt")
        data = self._parse_json_data(data)
        if not isinstance(data, dict):
            return ""

        nodes = data.get("nodes", [])
        links = data.get("links", [])
        
        # Find BasicGuider node
        guider_node = None
        guider_id = None
        for node in nodes:
            if node.get("class_type") == "BasicGuider":
                guider_node = node
                guider_id = node.get("id")
                break
        
        if not guider_node:
            self.logger.debug("[FLUX] No BasicGuider found, fallback to direct T5 search")
            return self._find_flux_text_direct(nodes, "T5TextEncode")
        
        # Find positive input link
        positive_link_id = None
        for input_item in guider_node.get("inputs", []):
            if input_item.get("name") == "positive":
                positive_link_id = input_item.get("link")
                break
        
        if not positive_link_id:
            return ""
        
        # Find source node for positive link
        source_node_id = None
        for link in links:
            if len(link) >= 4 and link[0] == positive_link_id:
                source_node_id = link[1]
                break
        
        if not source_node_id:
            return ""
        
        # Get the source node (should be T5TextEncode)
        source_node = self._find_node_by_id(nodes, source_node_id)
        if source_node:
            widgets_values = source_node.get("widgets_values", [])
            if widgets_values:
                return self._clean_prompt_text(str(widgets_values[0]))
        
        return ""

    def _extract_flux_negative_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract negative prompt from FLUX workflow via BasicGuider."""
        self.logger.debug("[FLUX] Extracting negative prompt")
        data = self._parse_json_data(data)
        if not isinstance(data, dict):
            return ""

        nodes = data.get("nodes", [])
        links = data.get("links", [])
        
        # Find BasicGuider node
        guider_node = None
        guider_id = None
        for node in nodes:
            if node.get("class_type") == "BasicGuider":
                guider_node = node
                guider_id = node.get("id")
                break
        
        if not guider_node:
            self.logger.debug("[FLUX] No BasicGuider found, fallback to direct CLIP search")
            return self._find_flux_text_direct(nodes, "CLIPTextEncode")
        
        # Find negative input link
        negative_link_id = None
        for input_item in guider_node.get("inputs", []):
            if input_item.get("name") == "negative":
                negative_link_id = input_item.get("link")
                break
        
        if not negative_link_id:
            return ""
        
        # Find source node for negative link
        source_node_id = None
        for link in links:
            if len(link) >= 4 and link[0] == negative_link_id:
                source_node_id = link[1]
                break
        
        if not source_node_id:
            return ""
        
        # Get the source node (should be CLIPTextEncode)
        source_node = self._find_node_by_id(nodes, source_node_id)
        if source_node:
            widgets_values = source_node.get("widgets_values", [])
            if widgets_values:
                return self._clean_prompt_text(str(widgets_values[0]))
        
        return ""

    def _find_flux_text_direct(self, nodes: list, encoder_type: str) -> str:
        """Fallback method to find text directly from encoder nodes."""
        for node in nodes:
            if node.get("class_type") == encoder_type:
                widgets_values = node.get("widgets_values", [])
                if widgets_values:
                    text = str(widgets_values[0])
                    if text.strip():  # Only return non-empty text
                        return self._clean_prompt_text(text)
        return ""

    def _find_legacy_input_of_main_sampler(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Legacy input of main sampler."""
        nodes = self.manager.traversal.get_nodes_from_data(data)
        if not nodes:
            return {}
            
        # Find sampler nodes
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if isinstance(node_data, dict):
                if self.manager.node_checker.is_sampler_node(node_data):
                    return {
                        "node_id": str(node_id),
                        "inputs": node_data.get("inputs", {}),
                        "class_type": node_data.get("class_type", "")
                    }
        
        return {}

    def _simple_legacy_text_extraction(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Legacy simple text extraction."""
        # Parse JSON data if needed
        data = self._parse_json_data(data)
        return self.manager._extract_smart_prompt(data, method_def, context, fields)

    def _simple_legacy_parameter_extraction(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Legacy simple parameter extraction."""
        return self.manager._get_workflow_metadata(data, method_def, context, fields)

    def _find_legacy_ancestor_node_input_value(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Legacy ancestor node input value - now uses traversal."""
        node_id = method_def.get("node_id", "")
        input_name = method_def.get("input_name", "")
        
        if not node_id or not input_name:
            return None
            
        nodes = self.manager.traversal.get_nodes_from_data(data)
        if not nodes:
            return None
            
        # Use traversal to follow the input
        link_info = self.manager.traversal.follow_input_link(nodes, node_id, input_name)
        if link_info:
            source_node_id, _ = link_info
            source_node = self.manager.traversal.get_node_by_id(nodes, source_node_id)
            if source_node:
                widgets = source_node.get("widgets_values", [])
                if widgets:
                    return widgets[0]
        
        return None

    def _find_legacy_node_input_or_widget_value(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Legacy node input or widget value."""
        node_id = method_def.get("node_id", "")
        field_name = method_def.get("field_name", "")
        
        if not node_id:
            return None
            
        nodes = self.manager.traversal.get_nodes_from_data(data)
        if not nodes:
            return None
            
        node = self.manager.traversal.get_node_by_id(nodes, node_id)
        if not node:
            return None
            
        # Check inputs first
        inputs = node.get("inputs", {})
        if isinstance(inputs, dict) and field_name in inputs:
            return inputs[field_name]
            
        # Check widgets
        widgets = node.get("widgets_values", [])
        if widgets and field_name == "text" and isinstance(widgets[0], str):
            return widgets[0]
            
        return None

    def _extract_legacy_all_loras(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list[dict[str, Any]]:
        """Legacy extract all loras."""
        nodes = self.manager.traversal.get_nodes_from_data(data)
        if not nodes:
            return []
            
        loras = []
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if isinstance(node_data, dict):
                if self.manager.node_checker.is_lora_node(node_data):
                    widgets = node_data.get("widgets_values", [])
                    if widgets:
                        loras.append({
                            "node_id": str(node_id),
                            "lora_name": widgets[0] if isinstance(widgets[0], str) else "",
                            "strength": widgets[1] if len(widgets) > 1 else 1.0,
                            "class_type": node_data.get("class_type", "")
                        })
        
        return loras

    def _extract_legacy_prompt_from_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Legacy prompt from workflow - FIXED TO USE PROPER LINK TRAVERSAL."""
        self.logger.info("[ComfyUI EXTRACTOR] === EXTRACTING POSITIVE PROMPT ===")
        
        # Use the same traversal logic as the main method, but specifically for positive
        fake_method_def = {
            "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced", "KSampler_A1111"],
            "positive_input_name": "positive",
            "text_input_name_in_encoder": "text",
            "text_encoder_node_types": ["CLIPTextEncode", "BNK_CLIPTextEncodeAdvanced", "CLIPTextEncodeAdvanced"]
        }
        
        # Call the fixed traversal method
        result = self._find_legacy_text_from_main_sampler_input(data, fake_method_def, context, fields)
        self.logger.info(f"[ComfyUI EXTRACTOR] Positive prompt result: {result[:100]}...")
        return result

    def _extract_legacy_negative_prompt_from_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Legacy negative prompt from workflow - FIXED TO USE PROPER LINK TRAVERSAL."""
        self.logger.info("[ComfyUI EXTRACTOR] === EXTRACTING NEGATIVE PROMPT ===")
        
        # Use the same traversal logic as the main method, but specifically for negative
        fake_method_def = {
            "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced", "KSampler_A1111"],
            "negative_input_name": "negative",
            "text_input_name_in_encoder": "text",
            "text_encoder_node_types": ["CLIPTextEncode", "BNK_CLIPTextEncodeAdvanced", "CLIPTextEncodeAdvanced"]
        }
        
        # Call the fixed traversal method
        result = self._find_legacy_text_from_main_sampler_input(data, fake_method_def, context, fields)
        self.logger.info(f"[ComfyUI EXTRACTOR] Negative prompt result: {result[:100]}...")
        return result

    def _extract_legacy_workflow_parameters(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Legacy workflow parameters - NEW BRUTE-FORCE WIRING."""
        data = self._parse_json_data(data)
        if not isinstance(data, dict):
            return {}

        self.logger.debug("[FACADE] Extracting parameters using direct-call method.")
        
        all_params = {}

        # --- Call multiple extractors and merge their results ---

        # 1. Get generic sampler parameters (seed, steps, etc.)
        generic_params = self.manager._extract_generic_parameters(data)
        all_params.update(generic_params)

        # 2. Get model information
        # Assuming sdxl._extract_model_info is generic enough for now
        model_info = self.manager.sdxl._extract_model_info(data, {}, {}, {})
        all_params.update(model_info)

        # 3. Get LoRA information
        # The old facade method for this is simple and can be used directly
        loras = self._extract_legacy_all_loras(data, {}, {}, {})
        if loras:
            all_params['loras'] = loras

        # 4. Get any other key parameters from specialized extractors
        # Example for efficiency nodes, which has its own sampler params
        efficiency_params = self.manager.efficiency._extract_sampler_params(data, {}, {}, {})
        all_params.update(efficiency_params)

        self.logger.debug(f"[FACADE] Final extracted params: {all_params}")

        return {k: v for k, v in all_params.items() if v is not None}

    def _extract_legacy_raw_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Legacy raw workflow."""
        data = self._parse_json_data(data)
        if isinstance(data, dict):
            return data
        return {}

    def _detect_legacy_custom_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list[dict[str, Any]]:
        """Legacy detect custom nodes."""
        nodes = self.manager.traversal.get_nodes_from_data(data)
        if not nodes:
            return []
            
        custom_nodes = []
        for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
            if isinstance(node_data, dict):
                if self.manager.node_checker.is_custom_node(node_data):
                    custom_nodes.append({
                        "node_id": str(node_id),
                        "class_type": node_data.get("class_type", ""),
                        "ecosystem": self.manager.node_checker.get_node_ecosystem(node_data),
                        "complexity": self.manager.node_checker.get_node_complexity(node_data)
                    })
        
        return custom_nodes

    # Convenience methods for direct access to the manager
    def get_manager(self) -> ComfyUIExtractorManager:
        """Get the underlying extractor manager."""
        return self.manager

    def get_extractor_stats(self) -> dict[str, Any]:
        """Get statistics about available extractors."""
        return self.manager.get_extractor_stats()

    def auto_detect_workflow(self, data: dict[str, Any]) -> list[str]:
        """Auto-detect workflow types."""
        return self.manager._auto_detect_workflow(data, {}, {}, {})

    def extract_comprehensive_summary(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract comprehensive workflow summary."""
        return self.manager._extract_comprehensive_summary(data, {}, {}, {})

    def clear_cache(self) -> None:
        """Clear the workflow detection cache."""
        self.manager.clear_cache()