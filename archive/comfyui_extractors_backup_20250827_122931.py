# dataset_tools/metadata_engine/extractors/comfyui_extractors.py

"""ComfyUI extraction methods.

Handles extraction from ComfyUI workflow JSON structures,
including node traversal and parameter extraction.

This is now a facade that delegates to the specialized extractors.
"""

import logging
from typing import Any

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
            "comfyui_extract_sdxl_refiner_prompt": self._extract_sdxl_refiner_prompt,
            "comfyui_extract_sdxl_refiner_negative": self._extract_sdxl_refiner_negative,
            "comfyui_extract_sdxl_base_steps": self._extract_sdxl_base_steps,
            "comfyui_extract_sdxl_refiner_steps": self._extract_sdxl_refiner_steps,
            "comfyui_extract_sdxl_total_steps": self._extract_sdxl_total_steps,
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
        # print("\n--- [FACADE] Running: _find_legacy_input_of_node_type ---")
        data = self._parse_json_data(data)

        if not isinstance(data, dict):
            return method_def.get("fallback")

        node_types = method_def.get("node_types", [])
        input_field = method_def.get("input_field", "")
        data_type = method_def.get("data_type", "string")
        fallback = method_def.get("fallback")

        if not node_types or not input_field:
            self.logger.warning("_find_legacy_input_of_node_type: missing node_types or input_field")
            return fallback

        # Get nodes from the workflow data
        nodes = data.get("nodes", data)
        if not isinstance(nodes, (dict, list)):
            self.logger.debug("No nodes found in data")
            return fallback

        # Search through nodes
        node_iterator = nodes.items() if isinstance(nodes, dict) else enumerate(nodes)

        for node_id, node_data in node_iterator:
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))

            # Check if this node matches any of our target types
            if any(target_type in class_type for target_type in node_types):
                self.logger.info(f"Found matching node type '{class_type}' for {node_types}")

                # Try to get value from inputs first
                inputs = node_data.get("inputs", {})
                if isinstance(inputs, dict) and input_field in inputs:
                    value = inputs[input_field]
                    return self._convert_data_type(value, data_type, fallback)

                # Try to get value from widgets_values
                widgets = node_data.get("widgets_values", [])
                if isinstance(widgets, list):
                    # For common fields, try to map to widget indices
                    if input_field == "width" and len(widgets) >= 1:
                        return self._convert_data_type(widgets[0], data_type, fallback)
                    if input_field == "height" and len(widgets) >= 2:
                        return self._convert_data_type(widgets[1], data_type, fallback)
                    if input_field == "ckpt_name" and len(widgets) >= 1:
                        return self._convert_data_type(widgets[0], data_type, fallback)

                # Try direct field access
                if input_field in node_data:
                    value = node_data[input_field]
                    return self._convert_data_type(value, data_type, fallback)

        self.logger.debug(f"No matching node found for types {node_types}")
        return fallback

    def _convert_data_type(self, value: Any, data_type: str, fallback: Any) -> Any:
        """Convert value to the specified data type."""
        try:
            if data_type == "integer":
                return int(value)
            if data_type == "float":
                return float(value)
            if data_type == "string":
                return str(value)
            return value
        except (ValueError, TypeError):
            self.logger.warning(f"Failed to convert {value} to {data_type}, using fallback")
            return fallback

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

        # Use workflow analyzer to get nodes
        analysis_result = self.manager.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return ""
        nodes = self.manager.workflow_analyzer.nodes
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
        negative_indicators = [
            "embedding:negatives",
            "negatives\\",
            "negative",
            "bad",
            "worst",
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in negative_indicators)

    def _clean_prompt_text(self, text: str) -> str:
        """Clean embedding prefixes and other artifacts from prompt text."""
        if not isinstance(text, str):
            return str(text)

        import re

        # Remove embedding prefixes
        # Remove embedding prefixes and similar artifacts
        text = re.sub(
            r"^embedding:negatives\\?|embedding:|negatives\\|embedding:negatives\\",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = text.strip()

        return text

    def _find_sampler_input_text(self, nodes: list | dict, data: dict, input_type: str) -> str:
        """Find text from sampler input by following workflow connections."""
        # Find the sampler node (support multiple sampler types)
        sampler_node = None
        sampler_id = None

        # List of all supported sampler types
        sampler_types = [
            "KSampler",
            "KSamplerAdvanced",
            "SamplerCustom",
            "SamplerCustomAdvanced",
        ]

        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
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
        if "sdxl" in workflow_types:
            return {"sampler_type": "sdxl", "detected": True}
        if "efficiency" in workflow_types:
            return self.manager.efficiency._extract_sampler_params(data, method_def, context, fields)
        if "searge" in workflow_types:
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
        # Use workflow analyzer to get nodes
        analysis_result = self.manager.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return None
        nodes = self.manager.workflow_analyzer.nodes
        if not nodes:
            return None

        # Find the field in the workflow
        field_name = method_def.get("field_name", "")
        if not field_name:
            return None

        # Simple field search
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
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

        # Use workflow analyzer to get nodes
        analysis_result = self.manager.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return {}
        nodes = self.manager.workflow_analyzer.nodes
        if not nodes:
            return {}

        # Find nodes by class
        matching_nodes = {}
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
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
        # Use workflow analyzer to get nodes
        analysis_result = self.manager.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return None
        nodes = self.manager.workflow_analyzer.nodes
        if not nodes:
            return None

        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
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
        """Find text from main sampler input by traversing ComfyUI workflow connections.
        This method performs a backward traversal from the sampler to find the
        originating text encoder, navigating through reroute nodes.
        """
        # print("\n--- [FACADE] Running: _find_legacy_text_from_main_sampler_input ---")
        # print(f"Method def: {method_def}")

        data = self._parse_json_data(data)

        if not isinstance(data, dict):
            return ""

        try:
            self.logger.info("[ComfyUI EXTRACTOR] ============ STARTING EXTRACTION ============")
            self.logger.info(f"[ComfyUI EXTRACTOR] Method def: {method_def}")
        except Exception:
            return ""

        sampler_node_types = method_def.get(
            "sampler_node_types",
            ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        )
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
            # print(f"No nodes found, data keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
            return ""

        # print(f"Found nodes: {list(nodes.keys()) if isinstance(nodes, dict) else f'list with {len(nodes)} items'}")

        # Debug: Show all nodes
        try:
            node_iterator = nodes.items() if isinstance(nodes, dict) else enumerate(nodes)

            for node_id, node_data in node_iterator:
                if isinstance(node_data, dict):
                    class_type = node_data.get("class_type", node_data.get("type", ""))

        except Exception:
            return ""

        # 1. Find the main sampler node or FLUX BasicGuider

        # Quick extraction for Civitai workflows - look for KSampler and follow connections
        # Build node lookup dictionary first
        node_lookup = {}
        node_iterator = nodes.items() if isinstance(nodes, dict) else enumerate(nodes)
        for node_id, node_data in node_iterator:
            if isinstance(node_data, dict):
                # Use the actual node ID from the data, not the index
                actual_id = node_data.get("id", node_id)
                node_lookup[str(actual_id)] = node_data
                class_type = node_data.get("class_type", node_data.get("type", "unknown"))

        for node_id, node_data in node_lookup.items():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))
                if any(sampler_type in class_type for sampler_type in sampler_node_types):
                    inputs = node_data.get("inputs", {})
                    # print(f"Found KSampler node {node_id}, inputs: {inputs}")

                    # Find the target input connection
                    target_connection = None
                    source_node_id = None

                    # Handle both formats: dict (direct) and list (API format)
                    if isinstance(inputs, dict):
                        # Direct format: {"positive": ["6", 0], "negative": ["7", 0]}
                        if target_input_name in inputs:
                            connection = inputs[target_input_name]
                            if isinstance(connection, list) and len(connection) >= 1:
                                source_node_id = str(connection[0])
                                # print(f"Direct connection found: {target_input_name} -> {source_node_id}")
                    elif isinstance(inputs, list):
                        # API format: [{"name": "positive", "link": 123}, ...]
                        for inp in inputs:
                            if isinstance(inp, dict) and inp.get("name") == target_input_name:
                                target_connection = inp.get("link")
                                break

                    # FLUX fallback: SamplerCustomAdvanced uses "guider" instead of positive/negative
                    if target_connection is None and source_node_id is None and class_type == "SamplerCustomAdvanced":
                        if isinstance(inputs, dict) and "guider" in inputs:
                            connection = inputs["guider"]
                            if isinstance(connection, list) and len(connection) >= 1:
                                source_node_id = str(connection[0])
                                print(f"FLUX guider connection found: {source_node_id}")
                        elif isinstance(inputs, list):
                            for inp in inputs:
                                if isinstance(inp, dict) and inp.get("name") == "guider":
                                    target_connection = inp.get("link")
                                    break

                    # Handle direct connections (source_node_id found)
                    if source_node_id is not None:
                        # print(f"Using direct connection to node: {source_node_id}")
                        if source_node_id in node_lookup:
                            # Recursively traverse to find text encoders
                            found_text = self._traverse_for_text(
                                source_node_id,
                                node_lookup,
                                data,
                                text_encoder_types,
                                visited=set(),
                            )
                            if found_text is not None:  # Allow empty strings
                                # print(f"Found text via direct connection: '{found_text}' (length: {len(found_text)})")
                                return found_text
                        # else:
                        # print(f"Source node {source_node_id} not found in node_lookup")

                    # Handle link-based connections (traditional format)
                    elif target_connection is not None:
                        print(f"Using link-based connection: {target_connection}")
                        # Look through links to find where this connection comes from
                        links = data.get("links", [])
                        for link in links:
                            if isinstance(link, list) and len(link) >= 6 and link[0] == target_connection:
                                source_node_id = str(link[1])  # Source node ID

                                if source_node_id in node_lookup:
                                    # Recursively traverse to find text encoders
                                    found_text = self._traverse_for_text(
                                        source_node_id,
                                        node_lookup,
                                        data,
                                        text_encoder_types,
                                        visited=set(),
                                    )
                                    if found_text:
                                        return found_text
                                break
                    else:
                        print(f"No connection found for {target_input_name}")

                    break  # Found the sampler, stop looking

        return method_def.get("fallback", "")

    def _traverse_for_text(
        self,
        node_id: str,
        node_lookup: dict,
        data: dict,
        text_encoder_types: list,
        visited: set,
        max_depth: int = 5,
    ) -> str:
        """Recursively traverse node connections to find text encoders."""
        # print(f"_traverse_for_text: node_id={node_id}, max_depth={max_depth}")

        if max_depth <= 0 or node_id in visited:
            # print(f"_traverse_for_text: stopping - max_depth={max_depth}, visited={node_id in visited}")
            return ""

        visited.add(node_id)

        if node_id not in node_lookup:
            # print(f"_traverse_for_text: node {node_id} not in node_lookup")
            return ""

        node = node_lookup[node_id]
        if not isinstance(node, dict):
            # print(f"_traverse_for_text: node {node_id} is not a dict")
            return ""

        # Check if this node is a text encoder
        class_type = node.get("class_type", node.get("type", ""))
        self.logger.info(f"[TRAVERSE] Visiting node {node_id}, class_type: {class_type}")
        # print(f"_traverse_for_text: node {node_id} class_type={class_type}")

        # --- PRIORITY: Check for Impact Pack and special text processing nodes FIRST ---
        if class_type == "ImpactWildcardProcessor":
            # This node processes wildcard text - the processed text is in widgets[1]
            widget_values = node.get("widgets_values", [])
            self.logger.info(f"[IMPACT FIX] Found ImpactWildcardProcessor node {node_id}!")
            self.logger.info(f"[IMPACT FIX] Widget values: {widget_values}")
            if len(widget_values) >= 2:
                result = str(widget_values[1])  # Return the processed text
                self.logger.info(f"[IMPACT FIX] Returning processed text: {result}")
                return result
            if len(widget_values) >= 1:
                result = str(widget_values[0])  # Fallback to original text
                self.logger.info(f"[IMPACT FIX] Returning original text: {result}")
                return result
            self.logger.info("[IMPACT FIX] No widget values found, returning empty")
            return ""

        if class_type == "AutoNegativePrompt":
            # This node automatically generates negative prompts - output is in widgets[1]
            widget_values = node.get("widgets_values", [])
            if len(widget_values) >= 2:
                return str(widget_values[1])  # Return the generated negative prompt
            return str(widget_values[0]) if widget_values else ""

        if class_type == "Wildcard Prompt from String":
            # This is the source of wildcard strings
            widget_values = node.get("widgets_values", [])
            return str(widget_values[0]) if widget_values else ""

        # --- EXISTING LOGIC: Check if this node is a text encoder ---
        # print(f"_traverse_for_text: checking if {class_type} matches any of {text_encoder_types}")
        # matches = [encoder for encoder in text_encoder_types if encoder in class_type]
        # print(f"_traverse_for_text: matches found: {matches}")

        if any(encoder in class_type for encoder in text_encoder_types):
            # print(f"_traverse_for_text: Found a text encoder! Extracting text from node {node_id}")
            # Found a text encoder, extract text
            widget_values = node.get("widgets_values", [])
            inputs = node.get("inputs", {})
            # print(f"_traverse_for_text: widget_values={widget_values}")
            # print(f"_traverse_for_text: inputs={inputs}")

            # Try widget_values first
            if widget_values and len(widget_values) > 0:
                text_value = widget_values[0]
                # print(f"_traverse_for_text: extracted from widgets: {text_value}")
                return str(text_value)

            # Try inputs["text"] for smZ CLIPTextEncode
            if isinstance(inputs, dict) and "text" in inputs:
                text_value = inputs["text"]
                # print(f"_traverse_for_text: extracted from inputs.text: '{text_value}' (type: {type(text_value)})")
                result = str(text_value)
                # print(f"_traverse_for_text: returning: '{result}'")
                return result

        # Check for "String Literal" nodes (common in efficiency workflows)
        if "String" in class_type and "Literal" in class_type:
            widget_values = node.get("widgets_values", [])
            if widget_values and len(widget_values) > 0:
                text_value = widget_values[0]
                return str(text_value)

        # Check for BasicGuider (FLUX architecture)
        if "BasicGuider" in class_type:
            # BasicGuider just passes conditioning through, continue traversal
            pass

        # Check if this is an Efficient Loader with prompts
        if "Efficient" in class_type and "Loader" in class_type:
            widget_values = node.get("widgets_values", [])
            # Efficient Loader typically has: [ckpt_name, vae_name, clip_skip, lora_name, lora_model_strength, lora_clip_strength, positive, negative, ...]
            if widget_values and len(widget_values) >= 8:
                positive_prompt = widget_values[6] if len(widget_values) > 6 else ""
                negative_prompt = widget_values[7] if len(widget_values) > 7 else ""
                # Return the appropriate prompt based on the current extraction
                # This is a bit hacky but works for most cases
                if positive_prompt and isinstance(positive_prompt, str):
                    return positive_prompt
                if negative_prompt and isinstance(negative_prompt, str):
                    return negative_prompt

        # Continue traversing up the chain
        inputs = node.get("inputs", [])
        links = data.get("links", [])

        for inp in inputs:
            if isinstance(inp, dict) and "link" in inp:
                link_id = inp["link"]
                for link in links:
                    if isinstance(link, list) and len(link) >= 6 and link[0] == link_id:
                        parent_node_id = str(link[1])
                        result = self._traverse_for_text(
                            parent_node_id,
                            node_lookup,
                            data,
                            text_encoder_types,
                            visited,
                            max_depth - 1,
                        )
                        if result:
                            return result

        return ""

    def _extract_from_workflow_text_nodes(self, data: dict, target_input_name: str) -> str:
        """Extract text from workflow nodes directly for modern architectures.

        Modern architectures like FLUX, SD3/3.5, PixArt, HiDream, and Auraflow use
        KSamplerSelect which has no meaningful inputs/outputs, so we need to search
        the workflow directly for text nodes.

        Args:
            data: The workflow data
            target_input_name: "positive" or "negative"

        Returns:
            Extracted text or empty string

        """
        self.logger.info(f"[ComfyUI EXTRACTOR] *** WORKFLOW-ONLY EXTRACTION for {target_input_name} ***")

        # Use workflow analyzer to get nodes
        analysis_result = self.manager.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return ""
        nodes = self.manager.workflow_analyzer.nodes
        if not nodes:
            return ""

        # For modern architectures, look for text encoder nodes that match the target type
        text_encoders = []

        # Convert nodes to dict format for easier processing
        if isinstance(nodes, list):
            nodes_dict = {str(node.get("id", i)): node for i, node in enumerate(nodes)}
        else:
            nodes_dict = nodes

        for node_id, node in nodes_dict.items():
            if not isinstance(node, dict):
                continue

            node_type = node.get("class_type", "")

            # Look for different types of text encoders
            if any(
                encoder_type in node_type
                for encoder_type in [
                    "CLIPTextEncode",
                    "T5TextEncode",
                    "PixArtT5TextEncode",
                    "ImpactWildcardEncode",
                    "BNK_CLIPTextEncodeAdvanced",
                    "CLIPTextEncodeAdvanced",
                    "DPRandomGenerator",
                ]
            ):
                widgets = node.get("widgets_values", [])
                if widgets and isinstance(widgets[0], str) and widgets[0].strip():
                    text_encoders.append({"id": node_id, "type": node_type, "text": widgets[0].strip()})

        self.logger.info(
            f"[ComfyUI EXTRACTOR] Found {len(text_encoders)} text encoder nodes: {[(e['id'], e['type'], e['text'][:50]) for e in text_encoders]}"
        )

        # For positive prompts, try to find the main/primary text
        if target_input_name == "positive":
            self.logger.debug("[ComfyUI EXTRACTOR] Attempting to extract POSITIVE prompt.")
            # Strategy 1: Look for T5TextEncode (FLUX) or PixArtT5TextEncode (PixArt) first
            for encoder in text_encoders:
                self.logger.debug(f"[ComfyUI EXTRACTOR] Checking encoder type: {encoder['type']}")
                if "T5TextEncode" in encoder["type"] or "PixArt" in encoder["type"]:
                    self.logger.info(f"[ComfyUI EXTRACTOR] *** Found T5/PixArt encoder: {encoder['text'][:100]}... ***")
                    return self._clean_prompt_text(encoder["text"])

            # Strategy 2: Look for any CLIP encoder
            for encoder in text_encoders:
                self.logger.debug(f"[ComfyUI EXTRACTOR] Checking encoder type: {encoder['type']}")
                if "CLIPTextEncode" in encoder["type"]:
                    self.logger.info(f"[ComfyUI EXTRACTOR] *** Found CLIP encoder: {encoder['text'][:100]}... ***")
                    return self._clean_prompt_text(encoder["text"])

            # Strategy 3: Take any text encoder
            if text_encoders:
                encoder = text_encoders[0]
                self.logger.info(f"[ComfyUI EXTRACTOR] *** Taking first encoder: {encoder['text'][:100]}... ***")
                return self._clean_prompt_text(encoder["text"])

        # For negative prompts, look for CLIP encoders for negative prompts
        elif target_input_name == "negative":
            self.logger.debug("[ComfyUI EXTRACTOR] Attempting to extract NEGATIVE prompt.")
            # Look for CLIP encoders for negative prompts
            for encoder in text_encoders:
                self.logger.debug(f"[ComfyUI EXTRACTOR] Checking encoder type: {encoder['type']}")
                if "CLIPTextEncode" in encoder["type"]:
                    text = encoder["text"]
                    if text.strip():  # Only return non-empty text
                        self.logger.info(
                            f"[ComfyUI EXTRACTOR] *** Found CLIP encoder for negative prompt: {text[:100]}... ***"
                        )
                        return self._clean_prompt_text(text)

            # For modern architectures, negative prompts might be empty (especially FLUX)
            self.logger.info("[ComfyUI EXTRACTOR] No negative prompt found (common in modern architectures)")
            return ""

        self.logger.info(f"[ComfyUI EXTRACTOR] No suitable text encoder found for {target_input_name}")
        return ""

    def _find_node_by_id(self, nodes: Any, node_id: int | str) -> dict[str, Any] | None:
        """Find a node by its ID in either list or dict format."""
        if isinstance(nodes, dict):
            return nodes.get(str(node_id))
        if isinstance(nodes, list):
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

        # Use traversal to get the text from the source node
        traced_text = self.manager.traversal.trace_text_flow(data, source_node_id)
        if traced_text:
            self.logger.debug(f"[FLUX] Traced positive text: {traced_text[:100]}...")
            return self._clean_prompt_text(traced_text)

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

        # Use traversal to get the text from the source node
        traced_text = self.manager.traversal.trace_text_flow(data, source_node_id)
        if traced_text:
            self.logger.debug(f"[FLUX] Traced negative text: {traced_text[:100]}...")
            return self._clean_prompt_text(traced_text)

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
        # Use workflow analyzer to get nodes
        analysis_result = self.manager.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return {}
        nodes = self.manager.workflow_analyzer.nodes
        if not nodes:
            return {}

        # Find sampler nodes and extract specific input field
        input_field = method_def.get("input_field", "")
        data_type = method_def.get("data_type", "string")
        fallback = method_def.get("fallback")

        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))
                if any(sampler in class_type for sampler in ["KSampler", "KSamplerAdvanced", "SamplerCustom"]):
                    inputs = node_data.get("inputs", {})
                    if input_field in inputs:
                        value = inputs[input_field]
                        # Convert to appropriate data type
                        try:
                            if data_type == "integer":
                                return int(value)
                            if data_type == "float":
                                return float(value)
                            if data_type == "string":
                                return str(value)
                            return value
                        except (ValueError, TypeError):
                            return fallback
                    else:
                        return fallback

        return fallback if fallback is not None else {}

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

        # Use workflow analyzer to get nodes
        analysis_result = self.manager.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return None
        nodes = self.manager.workflow_analyzer.nodes
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

        # Use workflow analyzer to get nodes
        analysis_result = self.manager.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return None
        nodes = self.manager.workflow_analyzer.nodes
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
        # Use workflow analyzer to get nodes
        analysis_result = self.manager.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return []
        nodes = self.manager.workflow_analyzer.nodes
        if not nodes:
            return []

        loras = []
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))
                if "Lora" in class_type or "LoRA" in class_type:
                    widgets = node_data.get("widgets_values", [])
                    if widgets:
                        loras.append(
                            {
                                "node_id": str(node_id),
                                "lora_name": (widgets[0] if isinstance(widgets[0], str) else ""),
                                "strength": widgets[1] if len(widgets) > 1 else 1.0,
                                "class_type": node_data.get("class_type", ""),
                            }
                        )

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
            "sampler_node_types": [
                "KSampler",
                "KSamplerAdvanced",
                "SamplerCustomAdvanced",
                "KSampler_A1111",
            ],
            "positive_input_name": "positive",
            "text_input_name_in_encoder": "text",
            "text_encoder_node_types": [
                "CLIPTextEncode",
                "BNK_CLIPTextEncodeAdvanced",
                "CLIPTextEncodeAdvanced",
                "PixArtT5TextEncode",
            ],
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
            "sampler_node_types": [
                "KSampler",
                "KSamplerAdvanced",
                "SamplerCustomAdvanced",
                "KSampler_A1111",
            ],
            "negative_input_name": "negative",
            "text_input_name_in_encoder": "text",
            "text_encoder_node_types": [
                "CLIPTextEncode",
                "BNK_CLIPTextEncodeAdvanced",
                "CLIPTextEncodeAdvanced",
                "PixArtT5TextEncode",
            ],
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
            all_params["loras"] = loras

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
        # Use workflow analyzer to get nodes
        analysis_result = self.manager.workflow_analyzer.analyze_workflow(data)
        if not analysis_result.get("is_valid_workflow", False):
            return []
        nodes = self.manager.workflow_analyzer.nodes
        if not nodes:
            return []

        custom_nodes = []
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))
                # Simple custom node detection - if not in standard ComfyUI nodes
                standard_nodes = [
                    "KSampler",
                    "KSamplerAdvanced",
                    "CheckpointLoaderSimple",
                    "CLIPTextEncode",
                    "VAEDecode",
                    "SaveImage",
                    "EmptyLatentImage",
                ]
                if class_type and not any(std in class_type for std in standard_nodes):
                    # Determine ecosystem based on class_type
                    ecosystem = "unknown"
                    if "Impact" in class_type:
                        ecosystem = "impact"
                    elif "Efficiency" in class_type:
                        ecosystem = "efficiency"
                    elif "WAS" in class_type:
                        ecosystem = "was"
                    elif "Lora" in class_type:
                        ecosystem = "lora"

                    custom_nodes.append(
                        {
                            "node_id": str(node_id),
                            "class_type": class_type,
                            "ecosystem": ecosystem,
                            "complexity": "unknown",
                        }
                    )

        return custom_nodes

    # Helper methods for SDXL extraction
    def _get_workflow_nodes(self, data: Any) -> list[dict[str, Any]]:
        """Parse JSON data and return workflow nodes."""
        try:
            workflow = self._parse_json_data(data)
            if not isinstance(workflow, dict):
                return []
            nodes = workflow.get("nodes", [])
            if not isinstance(nodes, list):
                self.logger.warning("Workflow nodes is not a list")
                return []
            return nodes
        except Exception as e:
            self.logger.error(f"Error parsing workflow data: {e}")
            return []

    def _extract_text_from_refiner_node(self, node: dict[str, Any], prompt_type: str = "positive") -> str:
        """Extract text from CLIPTextEncodeSDXLRefiner node."""
        try:
            if not isinstance(node, dict) or node.get("type") != "CLIPTextEncodeSDXLRefiner":
                return ""

            # For negative prompts, check title
            if prompt_type == "negative":
                title = node.get("title", "").lower()
                if "negative" not in title and "refiner" not in title:
                    return ""

            widgets_values = node.get("widgets_values", [])
            if not isinstance(widgets_values, list):
                self.logger.warning(f"Invalid widgets_values type in refiner node: {type(widgets_values)}")
                return ""

            if len(widgets_values) >= 4:
                prompt_text = widgets_values[3]  # Text is at index 3
                if isinstance(prompt_text, str) and prompt_text.strip():
                    self.logger.info(f"[SDXL Refiner] Found {prompt_type} prompt: {prompt_text[:100]}...")
                    return prompt_text
            else:
                self.logger.debug(f"Insufficient widgets_values in refiner node: {len(widgets_values)} < 4")
            return ""
        except Exception as e:
            self.logger.error(f"Error extracting text from refiner node: {e}")
            return ""

    def _extract_text_from_primitive_node(self, nodes: list[dict[str, Any]], titles: list[str]) -> str:
        """Extract text from PrimitiveNode with matching titles."""
        try:
            for node in nodes:
                if not isinstance(node, dict):
                    continue

                if node.get("type") == "PrimitiveNode":
                    node_title = node.get("title", "").lower()
                    if node_title in titles:
                        widgets_values = node.get("widgets_values", [])
                        if not isinstance(widgets_values, list):
                            self.logger.warning(
                                f"Invalid widgets_values type in primitive node: {type(widgets_values)}"
                            )
                            continue

                        if widgets_values and isinstance(widgets_values[0], str):
                            return widgets_values[0]
            return ""
        except Exception as e:
            self.logger.error(f"Error extracting text from primitive node: {e}")
            return ""

    # Convenience methods for direct access to the manager
    def _extract_sdxl_refiner_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract positive prompt from CLIPTextEncodeSDXLRefiner nodes."""
        nodes = self._get_workflow_nodes(data)
        if not nodes:
            return ""

        # Look for CLIPTextEncodeSDXLRefiner nodes
        for node in nodes:
            result = self._extract_text_from_refiner_node(node, "positive")
            if result:
                return result

        # Fallback: look in PrimitiveNode with title "Positive Prompt"
        return self._extract_text_from_primitive_node(nodes, ["positive prompt", "positive"])

    def _extract_sdxl_refiner_negative(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract negative prompt from CLIPTextEncodeSDXLRefiner nodes."""
        nodes = self._get_workflow_nodes(data)
        if not nodes:
            return ""

        # Look for CLIPTextEncodeSDXLRefiner nodes with negative title/purpose
        for node in nodes:
            result = self._extract_text_from_refiner_node(node, "negative")
            if result:
                return result

        # Fallback: look in PrimitiveNode with title "Negative Prompt"
        return self._extract_text_from_primitive_node(nodes, ["negative prompt", "negative"])

    def _extract_sdxl_base_steps(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> int:
        """Extract base model steps from SDXL workflow."""
        try:
            nodes = self._get_workflow_nodes(data)
            if not nodes:
                return 32

            # Look for PrimitiveNode with title containing "Base Model" or "Steps On Base"
            for node in nodes:
                if not isinstance(node, dict):
                    continue

                if node.get("type") == "PrimitiveNode":
                    title = node.get("title", "").lower()
                    if "base" in title and "step" in title:
                        widgets_values = node.get("widgets_values", [])
                        if isinstance(widgets_values, list) and widgets_values and isinstance(widgets_values[0], int):
                            return widgets_values[0]

            # Fallback: look for KSamplerAdvanced with end_at_step
            for node in nodes:
                if not isinstance(node, dict):
                    continue

                if node.get("type") == "KSamplerAdvanced":
                    widgets_values = node.get("widgets_values", [])
                    if isinstance(widgets_values, list) and len(widgets_values) >= 10:
                        end_step = widgets_values[9]  # end_at_step is usually at index 9
                        if isinstance(end_step, int) and end_step > 0:
                            return end_step

            return 50  # Default base steps (reasonable for SDXL)
        except Exception as e:
            self.logger.error(f"Error extracting SDXL base steps: {e}")
            return 50

    def _extract_sdxl_refiner_steps(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> int:
        """Extract refiner steps from SDXL workflow."""
        try:
            total_steps = self._extract_sdxl_total_steps(data, method_def, context, fields)
            base_steps = self._extract_sdxl_base_steps(data, method_def, context, fields)
            refiner_steps = total_steps - base_steps
            return max(0, refiner_steps)  # Ensure non-negative
        except Exception as e:
            self.logger.error(f"Error extracting SDXL refiner steps: {e}")
            return 0

    def _extract_sdxl_total_steps(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> int:
        """Extract total steps from SDXL workflow."""
        try:
            nodes = self._get_workflow_nodes(data)
            if not nodes:
                return 40

            # Look for PrimitiveNode with title "Total Steps"
            for node in nodes:
                if not isinstance(node, dict):
                    continue

                if node.get("type") == "PrimitiveNode":
                    title = node.get("title", "").lower()
                    if "total" in title and "step" in title:
                        widgets_values = node.get("widgets_values", [])
                        if isinstance(widgets_values, list) and widgets_values and isinstance(widgets_values[0], int):
                            return widgets_values[0]

            # Fallback: find the highest steps value in any sampler
            max_steps = 80  # Higher default for modern workflows
            for node in nodes:
                if not isinstance(node, dict):
                    continue

                node_type = node.get("type", "")
                if isinstance(node_type, str) and "sampler" in node_type.lower():
                    widgets_values = node.get("widgets_values", [])
                    if isinstance(widgets_values, list) and len(widgets_values) >= 4:
                        steps = widgets_values[3]  # steps is usually at index 3
                        if isinstance(steps, int) and steps > max_steps:
                            max_steps = steps

            return max_steps
        except Exception as e:
            self.logger.error(f"Error extracting SDXL total steps: {e}")
            return 80  # Higher fallback for modern workflows

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

    # --- Cache Management ---
    def clear_cache(self) -> None:
        """Clear the workflow detection cache."""
        self.manager.clear_cache()
