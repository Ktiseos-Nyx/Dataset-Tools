# dataset_tools/metadata_engine/extractors/comfyui_extractors.py

"""ComfyUI extraction methods.

Handles extraction from ComfyUI workflow JSON structures,
including node traversal and parameter extraction.
"""

import logging
import re
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIExtractor:
    """Handles ComfyUI-specific extraction methods."""

    def __init__(self, logger: logging.Logger):
        """Initialize the ComfyUI extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
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
            # Phase 2 Advanced missing methods - CRIME #2 PHASE 2 SHMANCY POWER!
            "comfy_detect_custom_nodes": self._detect_custom_nodes,
            "comfy_detect_t5_architecture": self._detect_t5_architecture,
            "comfy_extract_loras_from_linked_loaders": self._extract_loras_from_linked_loaders,
            "comfy_find_all_lora_nodes": self._find_all_lora_nodes,
            "comfy_find_clip_skip_in_path": self._find_clip_skip_in_path,
            "comfy_find_input_of_node_type": self._find_input_of_node_type,
            "comfy_find_node_input": self._find_node_input,
            "comfy_find_text_from_sampler_input": self._find_text_from_sampler_input,
            "comfy_find_vae_from_checkpoint_loader": self._find_vae_from_checkpoint_loader,
            # T5/FLUX specialized extraction methods
            "t5_extract_prompt_from_dual_clip_loader": self._t5_extract_prompt_from_dual_clip_loader,
            "t5_extract_parameters_from_modular_sampler": self._t5_extract_parameters_from_modular_sampler,
            "t5_extract_model_from_dual_clip_loader": self._t5_extract_model_from_dual_clip_loader,
            "t5_extract_dimensions_from_empty_latent": self._t5_extract_dimensions_from_empty_latent,
            # Advanced methods for TensorArt/ComfyUI hybrid parsing
            "comfyui_extract_positive_prompt_advanced": self._extract_positive_prompt_advanced,
            "comfyui_extract_negative_prompt_advanced": self._extract_negative_prompt_advanced,
            "comfyui_extract_main_model_advanced": self._extract_main_model_advanced,
            "comfyui_extract_loras_advanced": self._extract_loras_advanced,
            "comfyui_extract_sampler_advanced": self._extract_sampler_advanced,
            "comfyui_extract_scheduler_advanced": self._extract_scheduler_advanced,
            "comfyui_extract_steps_advanced": self._extract_steps_advanced,
            "comfyui_extract_cfg_advanced": self._extract_cfg_advanced,
            "comfyui_extract_seed_advanced": self._extract_seed_advanced,
            "comfyui_extract_width_advanced": self._extract_width_advanced,
            "comfyui_extract_height_advanced": self._extract_height_advanced,
            "comfyui_extract_vae_advanced": self._extract_vae_advanced,
            "comfyui_extract_clip_models_advanced": self._extract_clip_models_advanced,
            "comfyui_extract_denoise_advanced": self._extract_denoise_advanced,
        }

    def _extract_comfy_text_from_clip_encode_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, str]:
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
                            "embedding:negatives" in text
                            or "negatives\\" in text
                            or (text.startswith("(") and ":" in text and len(text) < 100)  # Often negative embeddings
                            or "bad" in text_lower
                            or "worst" in text_lower
                            or "low quality" in text_lower
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

        # Clean embedding prefixes from prompts as suggested by Gemini
        cleaned_prompts = {}
        for key, text in prompts.items():
            if text:
                cleaned_prompts[key] = self._clean_prompt_text(text)
            else:
                cleaned_prompts[key] = text

        return cleaned_prompts

    def _extract_comfy_sampler_settings(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract sampler settings from ComfyUI KSampler nodes."""
        if not isinstance(data, dict):
            return {}

        settings = {}

        # Handle workflow format (nodes array) vs prompt format (nodes dict)
        if "nodes" in data and isinstance(data["nodes"], list):
            # Workflow format - already handled in _extract_workflow_parameters
            return settings
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
                settings.update(
                    {
                        "seed": inputs.get("seed"),
                        "steps": inputs.get("steps"),
                        "cfg_scale": inputs.get("cfg"),
                        "sampler_name": inputs.get("sampler_name"),
                        "scheduler": inputs.get("scheduler"),
                        "denoise": inputs.get("denoise"),
                    }
                )

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
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
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

    def _node_matches_criteria(self, node_data: dict[str, Any], criteria: dict[str, Any]) -> bool:
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

    def _extract_field_from_node(self, node_data: dict[str, Any], target_field: str) -> Any:
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
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract data from a ComfyUI node by class type."""
        if not isinstance(data, dict):
            return None

        class_type = method_def.get("class_type")
        field_name = method_def.get("field_name")

        if not class_type or not field_name:
            return None

        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", data)

        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            node_class = node_data.get("class_type", node_data.get("type", ""))
            if node_class == class_type:
                return self._extract_field_from_node(node_data, field_name)

        return None

    def _extract_comfy_workflow_input(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
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
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
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
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
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
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
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
                                parameters["cfg_scale"] = (
                                    float(widgets_values[2]) if widgets_values[2] is not None else None
                                )
                                parameters["sampler_name"] = (
                                    str(widgets_values[3]) if widgets_values[3] is not None else None
                                )
                                parameters["scheduler"] = (
                                    str(widgets_values[4]) if widgets_values[4] is not None else None
                                )
                                parameters["denoise"] = (
                                    float(widgets_values[5]) if widgets_values[5] is not None else None
                                )
                            except (ValueError, TypeError, IndexError):
                                self.logger.debug("Could not parse KSampler widgets from workflow node")

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

    def _clean_prompt_text(self, text: str) -> str:
        """Clean embedding prefixes and other artifacts from prompt text."""
        if not isinstance(text, str):
            return text

        text = re.sub(r"^embedding:negatives\\?", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^embedding:", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^negatives\\", "", text, flags=re.IGNORECASE)
        text = text.strip()

        return text

    def _extract_raw_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract raw workflow data as string."""
        import json

        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            try:
                return json.dumps(data, indent=2)
            except (TypeError, ValueError):
                return str(data)
        else:
            return str(data)

    def _find_node_by_id(self, nodes: Any, node_id: int | str) -> dict[str, Any] | None:
        """Find a node by its ID in either list or dict format."""
        if isinstance(nodes, dict):
            return nodes.get(str(node_id))
        if isinstance(nodes, list):
            for node in nodes:
                if str(node.get("id", "")) == str(node_id):
                    return node
        return None

    def _find_text_from_main_sampler_input(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Find text from main sampler input by traversing ComfyUI workflow connections.
        This method now performs a backward traversal from the sampler to find the
        originating text encoder, navigating through reroute nodes.
        """
        self.logger.debug("[ComfyUI] Starting advanced text traversal...")
        if not isinstance(data, dict):
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

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        if isinstance(data, dict) and "nodes" in data:
            # Workflow format: {"nodes": [...]}
            nodes = data["nodes"]
        elif isinstance(data, dict) and all(isinstance(v, dict) for v in data.values()):
            # Prompt format: {"1": {...}, "2": {...}, ...}
            nodes = data
        else:
            return ""

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
                    self.logger.debug(
                        f"[ComfyUI] Found main sampler: {class_type} (ID: {node_data.get('id', node_id)})"
                    )
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
            self.logger.debug(f"[ComfyUI] Traversal depth {i + 1}, current node ID: {current_node_id}")

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

            self.logger.debug(
                f"[ComfyUI] Traversal stopped at node type: {class_type}. Not a recognized text encoder or passthrough node."
            )
            return ""

        self.logger.warning("[ComfyUI] Traversal depth limit reached, could not find text encoder.")
        return ""

    def _find_input_of_main_sampler(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Find a specific input value from the main sampler node.

        This method:
        1. Finds sampler nodes (KSampler, KSamplerAdvanced, etc.)
        2. Extracts the specified input key (seed, steps, cfg, etc.)
        3. Returns the value with proper type conversion
        """
        self.logger.debug(f"[ComfyUI] _find_input_of_main_sampler called for: {method_def.get('input_key')}")
        if not isinstance(data, dict):
            self.logger.debug("[ComfyUI] Data is not dict, returning None")
            return None

        # Get parameters from method definition
        sampler_node_types = method_def.get(
            "sampler_node_types",
            ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        )
        input_key = method_def.get("input_key")
        value_type = method_def.get("value_type", "string")

        if not input_key:
            return None

        # Handle different parameter names for different node types
        def get_input_key_for_node_type(node_type: str, requested_key: str) -> str:
            """Map requested input key to actual key used by specific node types."""
            if "SamplerCustomAdvanced" in node_type:
                if requested_key == "seed":
                    return "noise_seed"  # SamplerCustomAdvanced uses noise_seed
            return requested_key

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        # Find the main sampler node
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))
            if any(sampler_type in class_type for sampler_type in sampler_node_types):
                # Found a sampler node, extract the input
                actual_input_key = get_input_key_for_node_type(class_type, input_key)
                self.logger.debug(
                    f"[ComfyUI] Found sampler {node_id}: {class_type}, looking for input: {input_key} -> {actual_input_key}"
                )
                inputs = node_data.get("inputs", {})

                # Handle both dictionary format (prompt) and list format (workflow)
                value = None
                if isinstance(inputs, dict):
                    self.logger.debug(f"[ComfyUI] Sampler inputs (dict): {list(inputs.keys())}")
                    value = inputs.get(actual_input_key)
                elif isinstance(inputs, list):
                    self.logger.debug(f"[ComfyUI] Sampler inputs (list): {len(inputs)} items")
                    # For workflow format, inputs is a list of objects with "name" and "link"
                    # We can't get values directly from connections, but we might find widget values
                    for input_item in inputs:
                        if isinstance(input_item, dict) and input_item.get("name") == input_key:
                            # This input exists but we need the actual value from connections
                            # For now, we'll fall back to widgets below
                            break

                if value is not None:
                    # Type conversion
                    try:
                        if value_type == "integer":
                            return int(value)
                        if value_type == "float":
                            return float(value)
                        if value_type == "string":
                            return str(value)
                        return value
                    except (ValueError, TypeError):
                        self.logger.debug(f"Could not convert {input_key}={value} to {value_type}")
                        return value

                # Fallback to widgets_values for workflow format
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    # Map common input keys to widget positions
                    # Different node types may have different widget orders
                    if "SamplerCustomAdvanced" in class_type:
                        widget_mapping = {
                            "noise_seed": 0,  # SamplerCustomAdvanced uses noise_seed
                            "steps": 1,
                            "cfg": 2,
                            "sampler_name": 3,
                            "scheduler": 4,
                            "denoise": 5,
                        }
                    else:
                        widget_mapping = {
                            "seed": 0,
                            "steps": 1,
                            "cfg": 2,
                            "sampler_name": 3,
                            "scheduler": 4,
                            "denoise": 5,
                        }

                    widget_index = widget_mapping.get(actual_input_key)
                    if widget_index is not None and len(widgets) > widget_index:
                        value = widgets[widget_index]
                        try:
                            if value_type == "integer":
                                return int(value)
                            if value_type == "float":
                                return float(value)
                            if value_type == "string":
                                return str(value)
                            return value
                        except (ValueError, TypeError):
                            return value

                break  # Found the main sampler, no need to continue

        return None

    def _simple_text_extraction(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Simple fallback text extraction that looks for text in any CLIPTextEncode node.
        This is a more robust fallback when advanced connection traversal fails.
        """
        self.logger.debug("[ComfyUI] _simple_text_extraction called")
        if not isinstance(data, dict):
            return ""

        target_key = method_def.get("target_key", "")
        is_negative = "negative" in target_key.lower()

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        text_nodes = []
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
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

                    is_node_negative = (
                        "negative" in title
                        or "bad" in text.lower()
                        or "worst" in text.lower()
                        or (len(text) < 50 and any(word in text.lower() for word in ["low", "quality", "blurry"]))
                    )

                    text_nodes.append((text, is_node_negative, node_id))

        self.logger.debug(f"[ComfyUI] Found {len(text_nodes)} text nodes, looking for negative={is_negative}")

        # Return the first matching text based on positive/negative requirement
        for text, is_node_negative, node_id in text_nodes:
            if is_negative == is_node_negative:
                self.logger.debug(f"[ComfyUI] Returning text from node {node_id}: {text[:50]}...")
                return self._clean_prompt_text(text)

        # If no exact match, return first available text if we're looking for positive
        if not is_negative and text_nodes:
            text, _, node_id = text_nodes[0]
            self.logger.debug(f"[ComfyUI] Fallback: returning first text from node {node_id}: {text[:50]}...")
            return self._clean_prompt_text(text)

        return ""

    def _simple_parameter_extraction(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Simple fallback parameter extraction that looks for parameters in any KSampler node.
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
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
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
                        "seed": 0,
                        "steps": 1,
                        "cfg": 2,
                        "cfg_scale": 2,
                        "sampler_name": 3,
                        "scheduler": 4,
                        "denoise": 5,
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
            if value_type == "float":
                return float(value)
            if value_type == "string":
                return str(value)
            return value
        except (ValueError, TypeError):
            self.logger.debug(f"[ComfyUI] Could not convert {value} to {value_type}")
            return value

    def _clean_prompt_text(self, text: str) -> str:
        """Clean embedding prefixes and other artifacts from prompt text.

        As suggested by Gemini: Remove 'embedding:' or 'embedding:negatives\' prefixes
        from the extracted prompt text for cleaner output.
        """
        if not isinstance(text, str):
            return text

        import re

        # Remove embedding prefixes
        text = re.sub(r"^embedding:negatives\\?", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^embedding:", "", text, flags=re.IGNORECASE)

        # Remove other common ComfyUI artifacts
        text = re.sub(r"^negatives\\", "", text, flags=re.IGNORECASE)

        # Clean up whitespace
        text = text.strip()

        return text

    def _find_ancestor_node_input_value(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Find input value from ancestor nodes by traversing the workflow graph.

        This method:
        1. Starts from nodes of specific types (start_node_types)
        2. Follows connections through a specific input/output path
        3. Finds ancestor nodes of target types
        4. Extracts the specified input value from those ancestors
        """
        self.logger.debug("[ComfyUI] _find_ancestor_node_input_value called")
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
            self.logger.debug("[ComfyUI] Missing required node types in method definition")
            return None

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        # Find the starting node
        start_node = None
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
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
            self.logger.debug(
                f"[ComfyUI] Ancestor {ancestor_class_type} doesn't match target types: {target_ancestor_types}"
            )
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
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Find value from either node inputs or widget values based on node criteria.

        This method:
        1. Finds nodes matching the given criteria
        2. Tries to extract from inputs first
        3. Falls back to widget values if inputs don't have the value
        4. Handles preset regex extraction for special cases
        """
        self.logger.debug("[ComfyUI] _find_node_input_or_widget_value called")
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
            self.logger.debug("[ComfyUI] No node criteria provided")
            return None

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        # Find nodes matching criteria
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
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
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list:
        """Extract all LoRA information from the workflow.

        This method:
        1. Finds all LoRA loader nodes
        2. Extracts name, model strength, and clip strength
        3. Returns a list of LoRA dictionaries
        """
        self.logger.debug("[ComfyUI] _extract_all_loras called")
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
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
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

    # ==============================
    # CRIME #2 PHASE 2: MAXIMUM FANCY SCHMANCY FUNCTIONALITY
    # Advanced ComfyUI extraction methods for ultimate parsing power
    # ==============================

    def _detect_custom_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list:
        """Detect custom nodes and extensions in ComfyUI workflow.

        Returns a list of detected custom node types and their usage.
        """
        self.logger.debug("[ComfyUI] _detect_custom_nodes called")
        if not isinstance(data, dict):
            return []

        # Known built-in ComfyUI node types
        builtin_nodes = {
            "KSampler",
            "KSamplerAdvanced",
            "CLIPTextEncode",
            "CheckpointLoaderSimple",
            "VAELoader",
            "VAEDecode",
            "VAEEncode",
            "LoraLoader",
            "EmptyLatentImage",
            "LatentUpscale",
            "ImageScale",
            "SaveImage",
            "LoadImage",
            "PreviewImage",
            "ConditioningCombine",
            "ConditioningAverage",
            "ConditioningConcat",
            "ConditioningSetArea",
            "ConditioningSetMask",
            "ControlNetLoader",
            "ControlNetApply",
            "ControlNetApplyAdvanced",
            "unCLIPCheckpointLoader",
            "unCLIPConditioning",
            "PatchModelAddDownscale",
            "PhotoMakerLoader",
            "DiffusersLoader",
            "UNETLoader",
            "DualCLIPLoader",
            "CLIPLoader",
            "BasicGuider",
            "BasicScheduler",
            "KSamplerSelect",
            "SamplerCustomAdvanced",
        }

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        detected_custom = []
        custom_node_stats = {}

        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))
            if not class_type:
                continue

            # Check if this is a custom node (not in builtin list)
            is_custom = class_type not in builtin_nodes
            if is_custom:
                # Count usage
                if class_type not in custom_node_stats:
                    custom_node_stats[class_type] = 0
                custom_node_stats[class_type] += 1

                # Analyze the node to determine its likely purpose
                node_purpose = "unknown"
                if any(word in class_type.lower() for word in ["lora", "lyco", "loha"]):
                    node_purpose = "lora_management"
                elif any(word in class_type.lower() for word in ["controlnet", "control", "cn"]):
                    node_purpose = "controlnet"
                elif any(word in class_type.lower() for word in ["sampler", "sample"]):
                    node_purpose = "sampling"
                elif any(word in class_type.lower() for word in ["text", "prompt", "clip"]):
                    node_purpose = "text_processing"
                elif any(word in class_type.lower() for word in ["upscale", "scale", "resize"]):
                    node_purpose = "image_processing"
                elif any(word in class_type.lower() for word in ["model", "checkpoint", "unet"]):
                    node_purpose = "model_loading"
                elif any(word in class_type.lower() for word in ["vae", "decode", "encode"]):
                    node_purpose = "vae_processing"

                detected_custom.append(
                    {
                        "node_type": class_type,
                        "purpose": node_purpose,
                        "usage_count": custom_node_stats[class_type],
                    }
                )

        # Remove duplicates and sort by usage
        unique_custom = []
        seen_types = set()
        for custom in sorted(detected_custom, key=lambda x: x["usage_count"], reverse=True):
            if custom["node_type"] not in seen_types:
                unique_custom.append(custom)
                seen_types.add(custom["node_type"])

        self.logger.debug(f"[ComfyUI] Detected {len(unique_custom)} custom node types")
        return unique_custom

    def _detect_t5_architecture(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict:
        """Detect T5-based architectures like SD3, Flux, PixArt, etc.

        Returns architecture information and confidence level.
        """
        self.logger.debug("[ComfyUI] _detect_t5_architecture called")
        if not isinstance(data, dict):
            return {"architecture": "unknown", "confidence": 0.0}

        # T5 architecture indicators
        t5_indicators = {
            "flux": {
                "nodes": ["FluxGuidance", "ModelSamplingFlux", "DualCLIPLoader"],
                "keywords": ["flux", "schnell", "dev"],
                "confidence_base": 0.9,
            },
            "sd3": {
                "nodes": ["SD3"],
                "keywords": ["sd3", "stable diffusion 3"],
                "confidence_base": 0.85,
            },
            "pixart": {
                "nodes": ["PixArt"],
                "keywords": ["pixart", "pixel art"],
                "confidence_base": 0.8,
            },
            "hunyuan": {
                "nodes": ["HunyuanDiT"],
                "keywords": ["hunyuan"],
                "confidence_base": 0.8,
            },
        }

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        detected_architectures = {}

        for arch_name, indicators in t5_indicators.items():
            confidence = 0.0
            evidence = []

            # Check for specific node types
            for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
                if not isinstance(node_data, dict):
                    continue

                class_type = node_data.get("class_type", node_data.get("type", ""))
                if not class_type:
                    continue

                # Check for architecture-specific nodes
                for indicator_node in indicators["nodes"]:
                    if indicator_node.lower() in class_type.lower():
                        confidence += 0.3
                        evidence.append(f"Found {class_type} node")

                # Check for T5 text encoders
                if "T5" in class_type or "DualCLIP" in class_type:
                    confidence += 0.2
                    evidence.append(f"Found T5 encoder: {class_type}")

                # Check inputs and widgets for keywords
                inputs = node_data.get("inputs", {})
                widgets = node_data.get("widgets_values", [])

                for keyword in indicators["keywords"]:
                    # Check in input values
                    if isinstance(inputs, dict):
                        for input_key, input_value in inputs.items():
                            if isinstance(input_value, str) and keyword.lower() in input_value.lower():
                                confidence += 0.15
                                evidence.append(f"Found keyword '{keyword}' in {input_key}")

                    # Check in widget values
                    for widget_value in widgets:
                        if isinstance(widget_value, str) and keyword.lower() in widget_value.lower():
                            confidence += 0.1
                            evidence.append(f"Found keyword '{keyword}' in widget")

            if confidence > 0:
                detected_architectures[arch_name] = {
                    "confidence": min(confidence, 1.0),
                    "evidence": evidence,
                }

        # Return the most confident detection
        if detected_architectures:
            best_arch = max(detected_architectures.items(), key=lambda x: x[1]["confidence"])
            result = {
                "architecture": best_arch[0],
                "confidence": best_arch[1]["confidence"],
                "evidence": best_arch[1]["evidence"],
                "all_detections": detected_architectures,
            }
        else:
            # Check for general T5 indicators
            has_dual_clip = any(
                "DualCLIP" in str(node_data.get("class_type", ""))
                for node_data in (nodes.values() if isinstance(nodes, dict) else nodes)
            )

            if has_dual_clip:
                result = {
                    "architecture": "t5_based",
                    "confidence": 0.5,
                    "evidence": ["Found DualCLIPLoader - likely T5-based architecture"],
                    "all_detections": {},
                }
            else:
                result = {
                    "architecture": "unknown",
                    "confidence": 0.0,
                    "evidence": [],
                    "all_detections": {},
                }

        self.logger.debug(
            f"[ComfyUI] T5 Architecture detection: {result['architecture']} (confidence: {result['confidence']})"
        )
        return result

    def _extract_loras_from_linked_loaders(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list:
        """Extract LoRAs by following the connection chain from loader nodes.

        This method provides more sophisticated LoRA extraction by tracing
        connections between LoRA loaders and their usage in the workflow.
        """
        self.logger.debug("[ComfyUI] _extract_loras_from_linked_loaders called")
        if not isinstance(data, dict):
            return []

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        lora_chains = []

        # Find all LoRA loader nodes
        lora_loaders = []
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))
            if any(lora_type in class_type for lora_type in ["LoraLoader", "LoraTagLoader", "LoRALoader"]):
                lora_loaders.append((str(node_id), node_data))

        # For each LoRA loader, trace its connections
        for loader_id, loader_data in lora_loaders:
            inputs = loader_data.get("inputs", {})

            lora_info = {
                "loader_id": loader_id,
                "loader_type": loader_data.get("class_type", ""),
                "name": inputs.get("lora_name", "Unknown"),
                "strength_model": inputs.get("strength_model", 1.0),
                "strength_clip": inputs.get("strength_clip", 1.0),
                "connected_to": [],
            }

            # Find what this LoRA is connected to
            for target_id, target_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
                if str(target_id) == loader_id:
                    continue

                target_inputs = target_data.get("inputs", {})
                for input_key, input_value in target_inputs.items():
                    # Check if this input references our LoRA loader
                    if isinstance(input_value, list) and len(input_value) >= 2:
                        if str(input_value[0]) == loader_id:
                            connection_info = {
                                "target_node": str(target_id),
                                "target_type": target_data.get("class_type", ""),
                                "input_name": input_key,
                                "output_index": (input_value[1] if len(input_value) > 1 else 0),
                            }
                            lora_info["connected_to"].append(connection_info)

            lora_chains.append(lora_info)

        self.logger.debug(f"[ComfyUI] Found {len(lora_chains)} LoRA chains")
        return lora_chains

    def _find_all_lora_nodes(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list:
        """Find all LoRA-related nodes in the workflow.

        Returns comprehensive information about all LoRA usage.
        """
        self.logger.debug("[ComfyUI] _find_all_lora_nodes called")
        if not isinstance(data, dict):
            return []

        # LoRA-related node types
        lora_node_types = [
            "LoraLoader",
            "LoraTagLoader",
            "LoRALoader",
            "LoraStack",
            "LoraLoaderModelOnly",
            "LoraApply",
            "LoraComfy",
        ]

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        all_lora_nodes = []

        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))

            # Check if this is a LoRA-related node
            is_lora_node = any(lora_type.lower() in class_type.lower() for lora_type in lora_node_types)

            if is_lora_node:
                inputs = node_data.get("inputs", {})
                widgets = node_data.get("widgets_values", [])

                node_info = {
                    "node_id": str(node_id),
                    "node_type": class_type,
                    "inputs": inputs,
                    "widgets": widgets,
                    "extracted_loras": [],
                }

                # Extract LoRA information from this node
                if "name" in inputs or "lora_name" in inputs:
                    lora_name = inputs.get("lora_name") or inputs.get("name")
                    if lora_name:
                        lora_entry = {
                            "name": str(lora_name),
                            "strength_model": inputs.get("strength_model", 1.0),
                            "strength_clip": inputs.get("strength_clip", 1.0),
                        }
                        node_info["extracted_loras"].append(lora_entry)

                # For stack nodes, there might be multiple LoRAs
                if "Stack" in class_type:
                    # Try to extract multiple LoRAs from widgets
                    for i, widget in enumerate(widgets):
                        if isinstance(widget, str) and (".safetensors" in widget or ".ckpt" in widget):
                            stack_lora = {
                                "name": widget,
                                "stack_position": i,
                                "strength_model": (widgets[i + 1] if i + 1 < len(widgets) else 1.0),
                                "strength_clip": (widgets[i + 2] if i + 2 < len(widgets) else 1.0),
                            }
                            node_info["extracted_loras"].append(stack_lora)

                all_lora_nodes.append(node_info)

        self.logger.debug(f"[ComfyUI] Found {len(all_lora_nodes)} LoRA-related nodes")
        return all_lora_nodes

    def _find_clip_skip_in_path(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> int | None:
        """Find CLIP skip value by traversing connection paths.

        Looks for CLIP skip in CLIP loaders and text encoders.
        """
        self.logger.debug("[ComfyUI] _find_clip_skip_in_path called")
        if not isinstance(data, dict):
            return None

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        # Look for CLIP-related nodes
        clip_nodes = [
            "CLIPLoader",
            "CheckpointLoaderSimple",
            "DualCLIPLoader",
            "CLIPTextEncode",
        ]

        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))

            if any(clip_node in class_type for clip_node in clip_nodes):
                inputs = node_data.get("inputs", {})
                widgets = node_data.get("widgets_values", [])

                # Check for clip_skip in inputs
                if "clip_skip" in inputs:
                    try:
                        clip_skip = int(inputs["clip_skip"])
                        self.logger.debug(f"[ComfyUI] Found clip_skip={clip_skip} in {class_type}")
                        return clip_skip
                    except (ValueError, TypeError):
                        pass

                # Check for clip_skip in widgets (often the last widget in CLIP loaders)
                for widget in widgets:
                    if isinstance(widget, (int, float)) and 1 <= widget <= 12:
                        # This could be a clip_skip value
                        clip_skip = int(widget)
                        self.logger.debug("[ComfyUI] Found potential clip_skip={clip_skip} in widget")
                        return clip_skip

        self.logger.debug("[ComfyUI] No clip_skip found in connection paths")
        return None

    def _find_input_of_node_type(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Find input value from a specific node type.

        More flexible version of finding inputs from specific node types.
        """
        self.logger.debug("[ComfyUI] _find_input_of_node_type called")
        if not isinstance(data, dict):
            return None

        target_node_types = method_def.get("target_node_types", [])
        input_key = method_def.get("input_key")
        value_type = method_def.get("value_type", "string")

        if not target_node_types or not input_key:
            return None

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))

            # Check if this node matches any target type
            if any(target_type.lower() in class_type.lower() for target_type in target_node_types):
                inputs = node_data.get("inputs", {})

                if input_key in inputs:
                    value = inputs[input_key]
                    self.logger.debug(f"[ComfyUI] Found {input_key}={value} in {class_type}")
                    return self._convert_value_type(value, value_type)

        return None

    def _find_node_input(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Generic node input finder with flexible matching."""
        self.logger.debug("[ComfyUI] _find_node_input called")
        if not isinstance(data, dict):
            return None

        node_id = method_def.get("node_id")
        node_type = method_def.get("node_type")
        input_key = method_def.get("input_key")
        value_type = method_def.get("value_type", "string")

        if not input_key:
            return None

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        for current_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            # Check if this is the target node
            match_found = False

            if node_id and str(current_id) == str(node_id):
                match_found = True
            elif node_type:
                class_type = node_data.get("class_type", node_data.get("type", ""))
                if node_type.lower() in class_type.lower():
                    match_found = True

            if match_found:
                inputs = node_data.get("inputs", {})
                if input_key in inputs:
                    value = inputs[input_key]
                    self.logger.debug(f"[ComfyUI] Found {input_key}={value} in node {current_id}")
                    return self._convert_value_type(value, value_type)

        return None

    def _find_text_from_sampler_input(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str | None:
        """Alternative implementation for finding text from sampler inputs.

        Similar to _find_text_from_main_sampler_input but with different parameter handling.
        """
        self.logger.debug("[ComfyUI] _find_text_from_sampler_input called")
        if not isinstance(data, dict):
            return None

        # Get configuration from method definition
        sampler_types = method_def.get("sampler_types", ["KSampler", "KSamplerAdvanced"])
        input_name = method_def.get("input_name", "positive")
        text_input = method_def.get("text_input", "text")

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        # Find sampler nodes
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))
            if not any(sampler in class_type for sampler in sampler_types):
                continue

            # Found a sampler, now trace the input
            inputs = node_data.get("inputs", {})
            if input_name not in inputs:
                continue

            connection = inputs[input_name]
            if not isinstance(connection, list) or len(connection) < 2:
                continue

            # Follow the connection to the text encoder
            source_node_id = str(connection[0])

            # Find the source node
            for src_id, src_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
                if str(src_id) == source_node_id:
                    # Check if this is a text encoder
                    src_class = src_data.get("class_type", src_data.get("type", ""))
                    if "TextEncode" in src_class or "CLIP" in src_class:
                        src_inputs = src_data.get("inputs", {})
                        if text_input in src_inputs:
                            text_value = src_inputs[text_input]
                            self.logger.debug(f"[ComfyUI] Found text: {text_value[:100]}...")
                            return str(text_value) if text_value else None

        return None

    def _find_vae_from_checkpoint_loader(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str | None:
        """Find VAE information from checkpoint loader nodes.

        Returns VAE name or "baked-in" if using checkpoint VAE.
        """
        self.logger.debug("[ComfyUI] _find_vae_from_checkpoint_loader called")
        if not isinstance(data, dict):
            return None

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = data if all(isinstance(v, dict) for v in data.values()) else data.get("nodes", {})

        # First, look for dedicated VAE loaders
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))

            if "VAELoader" in class_type:
                inputs = node_data.get("inputs", {})
                vae_name = inputs.get("vae_name")
                if vae_name:
                    self.logger.debug("[ComfyUI] Found dedicated VAE: {vae_name}")
                    return str(vae_name)

        # If no dedicated VAE loader, check checkpoint loaders
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))

            if "CheckpointLoader" in class_type:
                # Check if VAE output is being used directly (baked-in VAE)
                vae_connections = 0

                # Count how many nodes use the VAE output from this checkpoint
                for other_id, other_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
                    if str(other_id) == str(node_id):
                        continue

                    other_inputs = other_data.get("inputs", {})
                    for input_key, input_value in other_inputs.items():
                        if isinstance(input_value, list) and len(input_value) >= 2:
                            if (
                                str(input_value[0]) == str(node_id) and input_value[1] == 2
                            ):  # VAE output is typically index 2
                                vae_connections += 1

                if vae_connections > 0:
                    inputs = node_data.get("inputs", {})
                    checkpoint_name = inputs.get("ckpt_name", "checkpoint")
                    self.logger.debug(f"[ComfyUI] Using baked-in VAE from {checkpoint_name}")
                    return f"baked-in ({checkpoint_name})"

        self.logger.debug("[ComfyUI] No VAE information found")
        return None

    # T5/FLUX SPECIALIZED EXTRACTION METHODS
    # These methods handle the modern T5/Flux workflow architecture that uses
    # modular sampling (SamplerCustomAdvanced, BasicScheduler, RandomNoise, FluxGuidance)
    # instead of traditional KSampler workflows

    def _t5_extract_prompt_from_dual_clip_loader(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract prompt from T5/FLUX workflows using DualCLIPLoader architecture."""
        self.logger.debug("[ComfyUI T5] _t5_extract_prompt_from_dual_clip_loader called")
        if not isinstance(data, dict):
            return ""

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        nodes = self._get_nodes_from_data(data)
        if not nodes:
            return ""

        # Find DualCLIPLoader node
        dual_clip_node = None
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))
            if "DualCLIPLoader" in class_type:
                dual_clip_node = (node_id, node_data)
                break

        if not dual_clip_node:
            self.logger.debug("[ComfyUI T5] No DualCLIPLoader found")
            return ""

        # Find T5 text encoder nodes connected to DualCLIPLoader
        dual_clip_id, dual_clip_data = dual_clip_node

        # Look for T5TextEncode nodes that use the DualCLIPLoader's T5 output
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))
            if "T5TextEncode" in class_type:
                inputs = node_data.get("inputs", {})

                # Check if this T5TextEncode uses the DualCLIPLoader's T5 output
                clip_input = inputs.get("clip")
                if isinstance(clip_input, list) and len(clip_input) >= 2:
                    if str(clip_input[0]) == str(dual_clip_id) and clip_input[1] == 0:  # T5 output is typically index 0
                        # Extract the text from this T5TextEncode
                        text = inputs.get("text", "")
                        if text:
                            self.logger.debug(f"[ComfyUI T5] Found T5 prompt: {text[:100]}...")
                            return str(text)

        self.logger.debug("[ComfyUI T5] No T5TextEncode prompt found")
        return ""

    def _t5_extract_parameters_from_modular_sampler(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract specific parameter from T5/FLUX modular sampling nodes."""
        self.logger.debug("[ComfyUI T5] _t5_extract_parameters_from_modular_sampler called")
        if not isinstance(data, dict):
            return None

        # Get the specific parameter to extract
        parameter_key = method_def.get("parameter_key")
        if not parameter_key:
            self.logger.warning("[ComfyUI T5] No parameter_key specified in method_def")
            return None

        nodes = self._get_nodes_from_data(data)
        if not nodes:
            return None

        # Find the main SamplerCustomAdvanced node
        sampler_node = None
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))
            if "SamplerCustomAdvanced" in class_type:
                sampler_node = (node_id, node_data)
                break

        if not sampler_node:
            self.logger.debug("[ComfyUI T5] No SamplerCustomAdvanced found")
            return None

        sampler_id, sampler_data = sampler_node
        sampler_inputs = sampler_data.get("inputs", {})

        # Extract specific parameter based on parameter_key
        if parameter_key == "seed":
            # Extract from RandomNoise node
            noise_input = sampler_inputs.get("noise")
            if isinstance(noise_input, list) and len(noise_input) >= 2:
                noise_node_id = noise_input[0]
                noise_node = self._get_node_by_id(nodes, noise_node_id)
                if noise_node:
                    noise_class = noise_node.get("class_type", "")
                    if "RandomNoise" in noise_class:
                        noise_inputs = noise_node.get("inputs", {})
                        seed = noise_inputs.get("noise_seed")
                        if seed is not None:
                            self.logger.debug(f"[ComfyUI T5] Found seed: {seed}")
                            return int(seed)

        elif parameter_key in ["steps", "scheduler"]:
            # Extract from BasicScheduler node
            scheduler_input = sampler_inputs.get("sigmas")
            if isinstance(scheduler_input, list) and len(scheduler_input) >= 2:
                scheduler_node_id = scheduler_input[0]
                scheduler_node = self._get_node_by_id(nodes, scheduler_node_id)
                if scheduler_node:
                    scheduler_class = scheduler_node.get("class_type", "")
                    if "BasicScheduler" in scheduler_class:
                        scheduler_inputs = scheduler_node.get("inputs", {})
                        if parameter_key == "steps":
                            steps = scheduler_inputs.get("steps")
                            if steps is not None:
                                self.logger.debug(f"[ComfyUI T5] Found steps: {steps}")
                                return int(steps)
                        elif parameter_key == "scheduler":
                            scheduler = scheduler_inputs.get("scheduler")
                            if scheduler:
                                self.logger.debug(f"[ComfyUI T5] Found scheduler: {scheduler}")
                                return str(scheduler)

        elif parameter_key == "cfg_scale":
            # Extract from FluxGuidance node
            guider_input = sampler_inputs.get("guider")
            if isinstance(guider_input, list) and len(guider_input) >= 2:
                guider_node_id = guider_input[0]
                guider_node = self._get_node_by_id(nodes, guider_node_id)
                if guider_node:
                    guider_class = guider_node.get("class_type", "")
                    if "FluxGuidance" in guider_class:
                        guider_inputs = guider_node.get("inputs", {})
                        guidance = guider_inputs.get("guidance")
                        if guidance is not None:
                            self.logger.debug(f"[ComfyUI T5] Found guidance: {guidance}")
                            return float(guidance)

        elif parameter_key == "sampler_name":
            # Extract from SamplerCustomAdvanced directly
            sampler = sampler_inputs.get("sampler")
            if sampler:
                self.logger.debug(f"[ComfyUI T5] Found sampler: {sampler}")
                return str(sampler)

        self.logger.debug(f"[ComfyUI T5] No {parameter_key} found")
        return None

    def _t5_extract_model_from_dual_clip_loader(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract model name from T5/FLUX DualCLIPLoader."""
        self.logger.debug("[ComfyUI T5] _t5_extract_model_from_dual_clip_loader called")
        if not isinstance(data, dict):
            return ""

        nodes = self._get_nodes_from_data(data)
        if not nodes:
            return ""

        # Find DualCLIPLoader node
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))
            if "DualCLIPLoader" in class_type:
                inputs = node_data.get("inputs", {})

                # DualCLIPLoader typically has clip_name1 and clip_name2 for T5 and CLIP
                clip_name1 = inputs.get("clip_name1", "")
                clip_name2 = inputs.get("clip_name2", "")

                if clip_name1 and clip_name2:
                    model_name = f"{clip_name1} + {clip_name2}"
                elif clip_name1:
                    model_name = clip_name1
                elif clip_name2:
                    model_name = clip_name2
                else:
                    model_name = "DualCLIP Model"

                self.logger.debug(f"[ComfyUI T5] Found DualCLIP model: {model_name}")
                return model_name

        self.logger.debug("[ComfyUI T5] No DualCLIPLoader model found")
        return ""

    def _t5_extract_dimensions_from_empty_latent(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract width/height from EmptyLatentImage nodes in T5/FLUX workflows."""
        self.logger.debug("[ComfyUI T5] _t5_extract_dimensions_from_empty_latent called")
        if not isinstance(data, dict):
            return None

        # Get the specific parameter to extract
        parameter_key = method_def.get("parameter_key")
        if not parameter_key:
            self.logger.warning("[ComfyUI T5] No parameter_key specified in method_def")
            return None

        nodes = self._get_nodes_from_data(data)
        if not nodes:
            return None

        # Find EmptyLatentImage or similar nodes
        for node_id, node_data in nodes.items() if isinstance(nodes, dict) else enumerate(nodes):
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", node_data.get("type", ""))
            if "EmptyLatentImage" in class_type:
                inputs = node_data.get("inputs", {})

                if parameter_key == "width":
                    width = inputs.get("width")
                    if width is not None:
                        self.logger.debug(f"[ComfyUI T5] Found width: {width}")
                        return int(width)
                elif parameter_key == "height":
                    height = inputs.get("height")
                    if height is not None:
                        self.logger.debug(f"[ComfyUI T5] Found height: {height}")
                        return int(height)

        self.logger.debug(f"[ComfyUI T5] No {parameter_key} found")
        return None

    def _get_node_by_id(self, nodes: dict | list, node_id: str) -> dict | None:
        """Helper method to get a node by its ID from nodes dict or list."""
        if isinstance(nodes, dict):
            return nodes.get(str(node_id))
        if isinstance(nodes, list):
            try:
                idx = int(node_id)
                if 0 <= idx < len(nodes):
                    return nodes[idx]
            except (ValueError, IndexError):
                pass
        return None

    def _get_nodes_from_data(self, data: dict) -> dict | list:
        """Helper method to extract nodes from data, handling both prompt and workflow formats."""
        if isinstance(data, dict) and "nodes" in data:
            # Workflow format: {"nodes": [...]}
            return data["nodes"]
        if isinstance(data, dict) and all(isinstance(v, dict) for v in data.values()):
            # Prompt format: {"1": {...}, "2": {...}, ...}
            return data
        return {}

    # ==============================
    # ADVANCED TENSORART/COMFYUI HYBRID EXTRACTION METHODS
    # These methods handle both standard ComfyUI and TensorArt formats
    # ==============================

    def _extract_positive_prompt_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract positive prompt using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return ""

        if not isinstance(data, dict):
            return ""

        analysis = analyze_comfyui_workflow(data, self.logger)
        return analysis.get("prompt_info", {}).get("positive_prompt", "")

    def _extract_negative_prompt_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract negative prompt using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return ""

        if not isinstance(data, dict):
            return ""

        analysis = analyze_comfyui_workflow(data, self.logger)
        return analysis.get("prompt_info", {}).get("negative_prompt", "")

    def _extract_main_model_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract main model using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return ""

        if not isinstance(data, dict):
            return ""

        analysis = analyze_comfyui_workflow(data, self.logger)
        return analysis.get("model_info", {}).get("main_model", "")

    def _extract_loras_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list:
        """Extract LoRAs using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return []

        if not isinstance(data, dict):
            return []

        analysis = analyze_comfyui_workflow(data, self.logger)
        return analysis.get("model_info", {}).get("loras", [])

    def _extract_sampler_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract sampler using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return ""

        if not isinstance(data, dict):
            return ""

        analysis = analyze_comfyui_workflow(data, self.logger)
        return analysis.get("sampling_info", {}).get("sampler", "")

    def _extract_scheduler_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract scheduler using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return ""

        if not isinstance(data, dict):
            return ""

        analysis = analyze_comfyui_workflow(data, self.logger)
        return analysis.get("sampling_info", {}).get("scheduler", "")

    def _extract_steps_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> int | None:
        """Extract steps using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return None

        if not isinstance(data, dict):
            return None

        analysis = analyze_comfyui_workflow(data, self.logger)
        steps = analysis.get("sampling_info", {}).get("steps")
        return int(steps) if steps is not None else None

    def _extract_cfg_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> float | None:
        """Extract CFG scale using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return None

        if not isinstance(data, dict):
            return None

        analysis = analyze_comfyui_workflow(data, self.logger)
        cfg = analysis.get("sampling_info", {}).get("cfg_scale")
        if cfg is None:
            cfg = analysis.get("prompt_info", {}).get("guidance_scale")
        return float(cfg) if cfg is not None else None

    def _extract_seed_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> int | None:
        """Extract seed using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return None

        if not isinstance(data, dict):
            return None

        analysis = analyze_comfyui_workflow(data, self.logger)
        seed = analysis.get("sampling_info", {}).get("seed")
        return int(seed) if seed is not None else None

    def _extract_width_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> int | None:
        """Extract width using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return None

        if not isinstance(data, dict):
            return None

        analysis = analyze_comfyui_workflow(data, self.logger)
        width = analysis.get("sampling_info", {}).get("width")
        return int(width) if width is not None else None

    def _extract_height_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> int | None:
        """Extract height using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return None

        if not isinstance(data, dict):
            return None

        analysis = analyze_comfyui_workflow(data, self.logger)
        height = analysis.get("sampling_info", {}).get("height")
        return int(height) if height is not None else None

    def _extract_vae_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract VAE using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return ""

        if not isinstance(data, dict):
            return ""

        analysis = analyze_comfyui_workflow(data, self.logger)
        return analysis.get("model_info", {}).get("vae", "")

    def _extract_clip_models_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list:
        """Extract CLIP models using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return []

        if not isinstance(data, dict):
            return []

        analysis = analyze_comfyui_workflow(data, self.logger)
        return analysis.get("model_info", {}).get("text_encoders", [])

    def _extract_denoise_advanced(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> float | None:
        """Extract denoise strength using the ComfyUI workflow analyzer."""
        from .comfyui_workflow_analyzer import analyze_comfyui_workflow

        if isinstance(data, str):
            try:
                import json

                data = json.loads(data)
            except:
                return None

        if not isinstance(data, dict):
            return None

        analysis = analyze_comfyui_workflow(data, self.logger)
        # Denoise might be in extracted parameters
        denoise = analysis.get("extracted_parameters", {}).get("denoise")
        return float(denoise) if denoise is not None else None
