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

        This method traverses the workflow to find DPRandomGenerator nodes
        and extracts the prompt template from their widgets_values.
        """
        workflow = self._parse_json_data(data)
        nodes = self._get_nodes(workflow)

        # Look for DPRandomGenerator nodes
        for node_data in nodes.values():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "")
                if class_type == "DPRandomGenerator":
                    # Extract prompt from widgets_values[0]
                    widgets_values = node_data.get("widgets_values", [])
                    if widgets_values and len(widgets_values) > 0:
                        prompt_template = widgets_values[0]
                        if isinstance(prompt_template, str) and prompt_template.strip():
                            self.logger.info(
                                f"[DynamicPrompts] Found DPRandomGenerator prompt: {prompt_template[:100]}..."
                            )
                            return prompt_template

        # Fallback: look for any CLIPTextEncode connected to the DPRandomGenerator output
        for node_data in nodes.values():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "")
                if class_type == "CLIPTextEncode":
                    # Check if this node has a STRING input link from a DPRandomGenerator
                    inputs = node_data.get("inputs", [])
                    for input_def in inputs:
                        if isinstance(input_def, dict) and input_def.get("type") == "STRING":
                            # This CLIPTextEncode is receiving string input, likely from DPRandomGenerator
                            widgets_values = node_data.get("widgets_values", [])
                            if widgets_values and len(widgets_values) > 0:
                                prompt_text = widgets_values[0]
                                if isinstance(prompt_text, str) and prompt_text.strip():
                                    # Skip default placeholder text
                                    if prompt_text not in ["chibi anime style", ""]:
                                        self.logger.info(
                                            f"[DynamicPrompts] Found connected prompt: {prompt_text[:100]}..."
                                        )
                                        return prompt_text

        self.logger.warning("[DynamicPrompts] No valid dynamic prompt found in workflow")
        return ""
