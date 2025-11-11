# dataset_tools/metadata_engine/extractors/comfyui_dynamicprompts.py

"""ComfyUI DynamicPrompts extractor.

Handles DynamicPrompts nodes (https://github.com/adieyal/comfyui-dynamicprompts)
for procedural prompt generation, wildcards, and combinatorial prompts.
"""

import json
import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIDynamicPromptsExtractor:
    """Handles DynamicPrompts ecosystem nodes."""

    # DynamicPrompts node types
    DYNAMICPROMPTS_NODES = [
        "DPRandomGenerator",
        "DPCombinatorialGenerator",
        "DPMagicPrompt",
        "DPWildcard",
        "DPTemplate",
        "DPFeelingLucky",
        "DPJinja",
        "DPOutput",
        "RandomPrompt",
        "WildcardEncode",
        "PromptGenerator",
        "DynamicPrompt",
    ]

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the DynamicPrompts extractor."""
        self.logger = logger

    def _parse_json_data(self, data: Any) -> Any:
        """Helper to parse JSON string data if needed."""
        if isinstance(data, str):
            try:
                return json.loads(data)
            except (json.JSONDecodeError, ValueError):
                self.logger.warning("[DynamicPrompts] Failed to parse workflow JSON string.")
                return {}
        return data

    def _initialize_workflow_data(self, workflow_data: dict[str, Any] | str) -> dict[str, Any]:
        """Set up nodes and links for easier lookup."""
        workflow = self._parse_json_data(workflow_data)
        return workflow

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "dynamicprompts_detect_workflow": self.detect_dynamicprompts_workflow,
            "dynamicprompts_extract_generators": self._extract_generators,
            "dynamicprompts_extract_wildcards": self._extract_wildcards,
            "dynamicprompts_extract_templates": self._extract_templates,
            "dynamicprompts_extract_summary": self.extract_dynamicprompts_workflow_summary,
            "dynamicprompts_get_generation_mode": self._get_generation_mode,
            "dynamicprompts_count_variants": self._count_variants,
            "comfyui_extract_dynamic_prompt_from_workflow": self.extract_dynamic_prompt_from_workflow,
        }

    def _get_nodes(self, data: dict) -> dict:
        """Helper to robustly get the nodes dictionary from workflow or API data."""
        if not isinstance(data, dict):
            return {}
        # Handle both {"prompt": {"1": ...}} and {"nodes": [...]} formats
        if "nodes" in data and isinstance(data["nodes"], list):
            return {str(node.get("id", i)): node for i, node in enumerate(data["nodes"])}
        if "prompt" in data and isinstance(data["prompt"], dict):
            return data["prompt"]
        if all(isinstance(v, dict) and "class_type" in v for v in data.values()):
            return data
        return {}

    def detect_dynamicprompts_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Detect if this workflow uses DynamicPrompts nodes."""
        nodes = self._get_nodes(data)
        if not nodes:
            return False

        for node_data in nodes.values():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "")
                if any(dp_node in class_type for dp_node in self.DYNAMICPROMPTS_NODES):
                    return True
                # Also check for wildcard patterns in text
                widgets = node_data.get("widgets_values", [])
                for widget in widgets:
                    if isinstance(widget, str) and ("{" in widget and "}" in widget):
                        return True

        return False

    def _extract_generators(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list[dict]:
        """Extract DynamicPrompts generator configurations."""
        nodes = self._get_nodes(data)
        if not nodes:
            return []

        generators = []
        generator_types = [
            "DPRandomGenerator",
            "DPCombinatorialGenerator",
            "DPFeelingLucky",
        ]

        for node_id, node_data in nodes.items():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "")
                if any(gen_type in class_type for gen_type in generator_types):
                    widgets = node_data.get("widgets_values", [])
                    inputs = node_data.get("inputs", {})

                    generator_config = {
                        "node_id": node_id,
                        "type": class_type,
                        "widgets": widgets,
                        "inputs": inputs,
                    }

                    # Extract common parameters
                    if "DPRandomGenerator" in class_type:
                        generator_config["mode"] = "random"
                        if widgets and len(widgets) > 0:
                            generator_config["seed"] = widgets[0] if isinstance(widgets[0], (int, float)) else None
                    elif "DPCombinatorialGenerator" in class_type:
                        generator_config["mode"] = "combinatorial"
                        if widgets and len(widgets) > 0:
                            generator_config["max_combinations"] = (
                                widgets[0] if isinstance(widgets[0], (int, float)) else None
                            )

                    generators.append(generator_config)

        return generators

    def _extract_wildcards(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list[dict]:
        """Extract wildcard patterns and configurations."""
        nodes = self._get_nodes(data)
        if not nodes:
            return []

        wildcards = []
        wildcard_types = ["DPWildcard", "WildcardEncode", "DPTemplate"]

        for node_id, node_data in nodes.items():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "")
                widgets = node_data.get("widgets_values", [])

                # Check for wildcard nodes
                if any(wc_type in class_type for wc_type in wildcard_types):
                    wildcard_config = {
                        "node_id": node_id,
                        "type": class_type,
                        "patterns": [],
                    }

                    # Extract wildcard patterns from widgets
                    for widget in widgets:
                        if isinstance(widget, str) and ("{" in widget and "}" in widget):
                            wildcard_config["patterns"].append(widget)

                    if wildcard_config["patterns"]:
                        wildcards.append(wildcard_config)

                # Also check text nodes for wildcard patterns
                elif "CLIPTextEncode" in class_type or "Text" in class_type:
                    for widget in widgets:
                        if isinstance(widget, str) and ("{" in widget and "}" in widget):
                            wildcard_config = {
                                "node_id": node_id,
                                "type": "text_with_wildcards",
                                "patterns": [widget],
                            }
                            wildcards.append(wildcard_config)
                            break

        return wildcards

    def _extract_templates(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list[dict]:
        """Extract template configurations."""
        nodes = self._get_nodes(data)
        if not nodes:
            return []

        templates = []
        template_types = ["DPTemplate", "DPJinja"]

        for node_id, node_data in nodes.items():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "")
                if any(tmpl_type in class_type for tmpl_type in template_types):
                    widgets = node_data.get("widgets_values", [])

                    template_config = {
                        "node_id": node_id,
                        "type": class_type,
                        "template": (widgets[0] if widgets and isinstance(widgets[0], str) else ""),
                        "parameters": widgets[1:] if len(widgets) > 1 else [],
                    }

                    templates.append(template_config)

        return templates

    def _get_generation_mode(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Determine the primary generation mode used."""
        generators = self._extract_generators(data, method_def, context, fields)

        if not generators:
            # Check for wildcard usage without explicit generators
            wildcards = self._extract_wildcards(data, method_def, context, fields)
            return "wildcards" if wildcards else "none"

        # Priority: combinatorial > random > other
        modes = [gen.get("mode", "unknown") for gen in generators]
        if "combinatorial" in modes:
            return "combinatorial"
        if "random" in modes:
            return "random"
        return modes[0] if modes else "unknown"

    def _count_variants(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict:
        """Estimate the number of possible prompt variants."""
        wildcards = self._extract_wildcards(data, method_def, context, fields)
        generators = self._extract_generators(data, method_def, context, fields)

        variant_info = {
            "has_wildcards": len(wildcards) > 0,
            "has_generators": len(generators) > 0,
            "wildcard_patterns": len(wildcards),
            "estimated_variants": "unknown",
        }

        # Simple estimation based on wildcard patterns
        if wildcards:
            total_patterns = sum(len(wc.get("patterns", [])) for wc in wildcards)
            if total_patterns > 0:
                # Very rough estimation - each pattern could have multiple options
                variant_info["estimated_variants"] = f"high (>{total_patterns * 10})"

        return variant_info

    def extract_dynamicprompts_workflow_summary(self, data: dict, *args, **kwargs) -> dict[str, Any]:
        """Extract comprehensive DynamicPrompts workflow summary."""
        if not self.detect_dynamicprompts_workflow(data, {}, {}, {}):
            return {"is_dynamicprompts_workflow": False}

        nodes = self._get_nodes(data)
        summary = {
            "is_dynamicprompts_workflow": True,
            "generation_mode": self._get_generation_mode(data, {}, {}, {}),
            "generators": self._extract_generators(data, {}, {}, {}),
            "wildcards": self._extract_wildcards(data, {}, {}, {}),
            "templates": self._extract_templates(data, {}, {}, {}),
            "variant_info": self._count_variants(data, {}, {}, {}),
            "node_count": len(
                [
                    n
                    for n in nodes.values()
                    if isinstance(n, dict)
                    and any(dp_node in n.get("class_type", "") for dp_node in self.DYNAMICPROMPTS_NODES)
                ]
            ),
        }

        # Add usage statistics
        summary["usage_stats"] = {
            "total_generators": len(summary["generators"]),
            "total_wildcards": len(summary["wildcards"]),
            "total_templates": len(summary["templates"]),
            "uses_random": any("Random" in gen.get("type", "") for gen in summary["generators"]),
            "uses_combinatorial": any("Combinatorial" in gen.get("type", "") for gen in summary["generators"]),
            "uses_magic_prompt": any("Magic" in gen.get("type", "") for gen in summary["generators"]),
        }

        return summary

    def extract_dynamic_prompt_from_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract the actual prompt text from DPRandomGenerator nodes.

        This method FIRST checks API prompt format for resolved values,
        then falls back to workflow format for templates.
        """
        # Check if we're looking for positive or negative
        target_input = method_def.get("target_input", "positive")

        # PRIORITY: Check API format prompt first (has RESOLVED prompts, not templates!)
        api_prompt = context.get("png_chunks", {}).get("prompt")
        if api_prompt:
            self.logger.info(f"[DynamicPrompts] Checking API prompt format for '{target_input}' prompt...")
            try:
                import json
                api_data = json.loads(api_prompt) if isinstance(api_prompt, str) else api_prompt

                # Use targeted extraction to find the right prompt for this input type
                # We'll score based on path to sampler and text quality
                best_text = ""
                best_score = -999

                for node_id, node_data in api_data.items():
                    if isinstance(node_data, dict):
                        inputs = node_data.get("inputs", {})

                        # Check for text/text2 inputs (common in these workflows)
                        for text_key in ["text", "text2", "text_g", "text_l"]:
                            text_value = inputs.get(text_key)
                            if isinstance(text_value, str) and len(text_value) > 20:
                                # Score this candidate
                                score = len(text_value) / 10  # Longer is better

                                # Penalize LoRA-only prompts
                                if "<lora:" in text_value.lower() and text_value.count(",") < 3:
                                    score -= 100

                                # Boost descriptive prompts
                                if any(w in text_value.lower() for w in ["photo", "painting", "portrait", "art", "digital"]):
                                    score += 20

                                # CRITICAL: Filter by target_input type if possible
                                # For negative prompts, look for negative keywords
                                if target_input == "negative":
                                    if any(w in text_value.lower() for w in ["blurry", "worst", "bad", "ugly", "deformed", "watermark"]):
                                        score += 30  # Strong boost for negative keywords
                                    elif any(w in text_value.lower() for w in ["beautiful", "best", "masterpiece", "detailed"]):
                                        score -= 50  # Penalize positive-looking text in negative field
                                else:  # positive
                                    if any(w in text_value.lower() for w in ["beautiful", "detailed", "masterpiece", "1girl", "1boy"]):
                                        score += 30  # Boost positive-looking text
                                    elif any(w in text_value.lower() for w in ["blurry", "worst", "bad", "ugly"]):
                                        score -= 50  # Penalize negative text in positive field

                                if score > best_score:
                                    best_score = score
                                    best_text = text_value
                                    self.logger.debug(f"[DynamicPrompts] API candidate for '{target_input}' (score={score:.1f}): {text_value[:80]}...")

                if best_text:
                    self.logger.info(f"[DynamicPrompts] ✅ Found resolved '{target_input}' prompt in API format: {best_text[:100]}...")
                    return best_text
                else:
                    self.logger.info(f"[DynamicPrompts] No good '{target_input}' prompts in API format, trying workflow format...")

            except Exception as e:
                self.logger.debug(f"[DynamicPrompts] API format parsing failed: {e}, trying workflow format...")

        # FALLBACK: Parse workflow format (templates, not resolved)
        workflow = self._parse_json_data(data)
        nodes = self._get_nodes(workflow)

        self.logger.info(f"[DynamicPrompts] Searching for prompts in {len(nodes)} nodes")

        # Debug: show what node types we have
        node_types = [n.get("class_type") or n.get("type", "unknown") for n in nodes.values() if isinstance(n, dict)]
        self.logger.info(f"[DynamicPrompts] Node types in workflow: {', '.join(set(node_types[:20]))}")

        # Helper function to follow node references recursively
        def follow_node_reference(node_ref: list, depth: int = 0) -> str:
            """Follow a node reference like ["node_id", slot] to extract text.

            Args:
                node_ref: Reference in format [node_id, slot_index]
                depth: Recursion depth to prevent infinite loops

            Returns:
                Extracted text or empty string
            """
            if depth > 10:  # Prevent infinite recursion
                self.logger.warning("[DynamicPrompts] Max recursion depth reached following references")
                return ""

            if not isinstance(node_ref, list) or len(node_ref) < 1:
                return ""

            ref_node_id = str(node_ref[0])
            if ref_node_id not in nodes:
                self.logger.debug(f"[DynamicPrompts] Referenced node {ref_node_id} not found")
                return ""

            ref_node = nodes[ref_node_id]
            if not isinstance(ref_node, dict):
                return ""

            ref_class = ref_node.get("class_type") or ref_node.get("type", "")
            ref_widgets = ref_node.get("widgets_values", [])

            self.logger.debug(f"[DynamicPrompts] Following reference to node {ref_node_id} (type: {ref_class})")

            # If referenced node is also a DPRandomGenerator, extract from it
            if ref_class == "DPRandomGenerator":
                if ref_widgets and len(ref_widgets) > 0:
                    text = ref_widgets[0]
                    if isinstance(text, str) and text.strip():
                        self.logger.info(f"[DynamicPrompts] Found text in referenced DPRandomGenerator: {text[:100]}...")
                        return text
                    # If still empty, try following its reference
                    if len(ref_widgets) > 1 and isinstance(ref_widgets[1], list):
                        return follow_node_reference(ref_widgets[1], depth + 1)

            # If it's a text node or string primitive, try to extract
            if ref_class in ["PrimitiveNode", "String Literal", "easy string"]:
                if ref_widgets and len(ref_widgets) > 0:
                    text = ref_widgets[0]
                    if isinstance(text, str) and text.strip():
                        self.logger.info(f"[DynamicPrompts] Found text in {ref_class}: {text[:100]}...")
                        return text

            # Check if this node has an 'outputs' value we can use
            outputs = ref_node.get("outputs", [])
            if outputs and isinstance(outputs, list):
                for output in outputs:
                    if isinstance(output, dict):
                        value = output.get("value")
                        if isinstance(value, str) and value.strip():
                            self.logger.info(f"[DynamicPrompts] Found text in node output: {value[:100]}...")
                            return value

            return ""

        # Collect ALL DPRandomGenerator candidates with scoring for multi-pass workflows
        candidates = []

        for node_id, node_data in nodes.items():
            if isinstance(node_data, dict):
                # Check both 'class_type' (API format) and 'type' (workflow format)
                class_type = node_data.get("class_type") or node_data.get("type", "")
                if class_type == "DPRandomGenerator":
                    # Extract prompt from widgets_values[0]
                    widgets_values = node_data.get("widgets_values", [])
                    if widgets_values and len(widgets_values) > 0:
                        prompt_template = widgets_values[0]

                        # Try direct text first
                        if isinstance(prompt_template, str) and prompt_template.strip():
                            candidates.append({"node_id": node_id, "text": prompt_template, "source": "direct"})

                        # If widgets_values[0] is empty, try following reference in widgets_values[1]
                        elif len(widgets_values) > 1 and isinstance(widgets_values[1], list):
                            self.logger.debug(f"[DynamicPrompts] Node {node_id}: widgets_values[0] empty, following reference...")
                            referenced_text = follow_node_reference(widgets_values[1])
                            if referenced_text:
                                candidates.append({"node_id": node_id, "text": referenced_text, "source": "reference"})

        # Score candidates to find the MAIN generation prompt (not LoRA/auxiliary)
        if candidates:
            self.logger.info(f"[DynamicPrompts] Found {len(candidates)} candidate prompts, scoring...")

            for candidate in candidates:
                text = candidate["text"]
                score = 0

                # Base score: text length (longer is often better)
                score += min(len(text), 500) / 10  # Cap at 50 points

                # PENALIZE LoRA loading patterns (these are auxiliary, not main prompts)
                if "<lora:" in text.lower() or "<lyco:" in text.lower():
                    score -= 100  # Heavy penalty
                    self.logger.debug(f"[DynamicPrompts] Node {candidate['node_id']}: LoRA pattern detected, penalizing")

                # PENALIZE very short text (likely templates or placeholders)
                if len(text.strip()) < 20:
                    score -= 30

                # PREFER descriptive prompts with commas (tag-based or sentence-based)
                comma_count = text.count(",")
                score += min(comma_count * 2, 20)  # Up to 20 bonus points

                # PREFER prompts with content words
                if any(word in text.lower() for word in ["photo", "image", "portrait", "landscape", "art", "painting"]):
                    score += 10

                candidate["score"] = score
                self.logger.debug(
                    f"[DynamicPrompts] Node {candidate['node_id']}: score={score:.1f}, text={text[:60]}..."
                )

            # Sort by score and return the best one
            candidates.sort(key=lambda x: x["score"], reverse=True)
            best = candidates[0]
            self.logger.info(
                f"[DynamicPrompts] Selected best candidate: Node {best['node_id']} "
                f"(score={best['score']:.1f}, source={best['source']}): {best['text'][:100]}..."
            )
            return best["text"]

        # Fallback: look for any CLIPTextEncode variant connected to the DPRandomGenerator output
        for node_data in nodes.values():
            if isinstance(node_data, dict):
                # Check both 'class_type' (API format) and 'type' (workflow format)
                class_type = node_data.get("class_type") or node_data.get("type", "")
                if class_type.startswith("CLIPTextEncode"):
                    # Check if this node has a STRING input link from a DPRandomGenerator
                    inputs = node_data.get("inputs", {})
                    # inputs is a DICT like {"text": ["node_id", 0], "clip": ["node_id2", 1]}
                    if isinstance(inputs, dict):
                        text_input = inputs.get("text")
                        # Check if text input is connected (list format) vs static (string format)
                        if isinstance(text_input, list) and len(text_input) >= 2:
                            # This means text is CONNECTED from another node
                            # The source node might be a DPRandomGenerator
                            source_node_id = str(text_input[0])
                            if source_node_id in nodes:
                                source_node = nodes[source_node_id]
                                if isinstance(source_node, dict):
                                    # Check both 'class_type' (API format) and 'type' (workflow format)
                                    source_class = source_node.get("class_type") or source_node.get("type", "")
                                    # If connected to a DynamicPrompts node, extract from its widgets
                                    if any(dp_node in source_class for dp_node in self.DYNAMICPROMPTS_NODES):
                                        source_widgets = source_node.get("widgets_values", [])
                                        if source_widgets and len(source_widgets) > 0:
                                            prompt_text = source_widgets[0]
                                            if isinstance(prompt_text, str) and prompt_text.strip():
                                                self.logger.info(
                                                    f"[DynamicPrompts] Found prompt from {source_class}: {prompt_text[:100]}..."
                                                )
                                                return prompt_text

        self.logger.warning("[DynamicPrompts] No valid dynamic prompt found in workflow")
        return ""
