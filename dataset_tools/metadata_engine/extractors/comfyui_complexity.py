# dataset_tools/metadata_engine/extractors/comfyui_complexity.py

"""ComfyUI complex workflow handling.

Handles advanced workflows with dynamic prompts, multi-step processes,
and complex parameter extraction.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIComplexityExtractor:
    """Handles complex ComfyUI workflows and advanced extraction patterns."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the complexity extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "comfy_extract_dynamic_prompt": self.extract_dynamic_prompt_from_workflow,
            "comfy_trace_active_prompt_path": self._trace_active_prompt_path,
            "comfy_extract_multi_step_workflow": self._extract_multi_step_workflow,
            "comfy_analyze_workflow_complexity": self.analyze_workflow_complexity,
            "comfy_extract_conditional_prompts": self._extract_conditional_prompts,
            "comfy_resolve_parameter_chains": self._resolve_parameter_chains,
        }

    def extract_dynamic_prompt_from_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract dynamic prompts from complex workflows with generators and processors."""
        self.logger.debug("[ComfyUI Complex] Extracting dynamic prompt from workflow")

        if not isinstance(data, dict):
            return ""

        # Handle both prompt and workflow formats
        if "prompt" in data and "workflow" in data:
            prompt_data = data["prompt"]
            workflow_data = data["workflow"]
        elif "nodes" in data:
            # Workflow format
            workflow_data = data
            prompt_data = self._convert_workflow_to_prompt_format(data)
        else:
            # Prompt format
            prompt_data = data
            workflow_data = data

        # Strategy 1: Find dynamic prompt generators
        dynamic_generators = self._find_dynamic_prompt_generators(prompt_data)
        if dynamic_generators:
            return self._process_dynamic_generators(dynamic_generators, prompt_data)

        # Strategy 2: Trace from final output backwards
        final_prompt = self._trace_from_final_output(prompt_data, workflow_data)
        if final_prompt:
            return final_prompt

        # Strategy 3: Find complex text processors
        complex_processors = self._find_complex_text_processors(prompt_data)
        if complex_processors:
            return self._process_complex_processors(complex_processors, prompt_data)

        return ""

    def _find_dynamic_prompt_generators(self, prompt_data: dict) -> list[dict]:
        """Find nodes that generate dynamic prompts."""
        generators = []

        dynamic_node_types = [
            "DPRandomGenerator",
            "RandomGenerator",
            "ImpactWildcardProcessor",
            "WildcardProcessor",
            "DynamicPrompts",
            "AdvancedPromptGenerator",
            "ConditionalPrompt",
            "PromptGenerator",
            "TextGenerator",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if any(gen_type in class_type for gen_type in dynamic_node_types):
                generators.append({"node_id": node_id, "node_data": node_data, "type": class_type})

        return generators

    def _process_dynamic_generators(self, generators: list[dict], prompt_data: dict) -> str:
        """Process dynamic prompt generators to extract final text."""
        for gen in generators:
            node_data = gen["node_data"]
            widgets = node_data.get("widgets_values", [])

            if widgets:
                # For most generators, the first widget is the generated/processed text
                if isinstance(widgets[0], str) and len(widgets[0].strip()) > 10:
                    return widgets[0].strip()

                # Some generators store the result in a different position
                for widget in widgets:
                    if isinstance(widget, str) and len(widget.strip()) > 20:
                        # Check if it looks like a prompt (has descriptive words)
                        if any(
                            word in widget.lower()
                            for word in [
                                "score_",
                                "rating_",
                                "source_",
                                "photograph",
                                "realistic",
                                "quality",
                            ]
                        ):
                            return widget.strip()

        return ""

    def _trace_from_final_output(self, prompt_data: dict, workflow_data: dict) -> str:
        """Trace backwards from final output nodes to find the prompt source."""
        # Find the final sampler or output node
        final_nodes = self._find_final_nodes(prompt_data)

        for node_id, node_data in final_nodes.items():
            # For samplers, trace the positive conditioning input
            if "sampler" in node_data.get("class_type", "").lower():
                positive_input = self._get_input_connection(node_data, "positive")
                if positive_input:
                    return self._trace_conditioning_chain(positive_input, prompt_data)

        return ""

    def _find_final_nodes(self, prompt_data: dict) -> dict:
        """Find nodes that are likely final output nodes."""
        final_nodes = {}

        final_node_types = [
            "KSampler",
            "KSamplerAdvanced",
            "SamplerCustom",
            "SamplerCustomAdvanced",
            "DPMSolverMultistep",
            "EulerAncestralSampler",
            "UniPCMultistep",
            "SaveImage",
            "PreviewImage",
            "VaeEncode",
            "VaeDecode",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if any(final_type in class_type for final_type in final_node_types):
                final_nodes[node_id] = node_data

        return final_nodes

    def _get_input_connection(self, node_data: dict, input_name: str) -> str | None:
        """Get the connection for a specific input."""
        inputs = node_data.get("inputs", {})

        if isinstance(inputs, dict) and input_name in inputs:
            input_info = inputs[input_name]
            if isinstance(input_info, list) and len(input_info) > 0:
                return str(input_info[0])  # Return source node ID

        return None

    def _trace_conditioning_chain(self, start_node_id: str, prompt_data: dict) -> str:
        """Trace a conditioning chain to find the text source."""
        visited = set()

        def trace_recursive(node_id: str, depth: int = 0) -> str:
            if depth > 10 or node_id in visited:
                return ""

            visited.add(node_id)

            if node_id not in prompt_data:
                return ""

            node_data = prompt_data[node_id]
            class_type = node_data.get("class_type", "")

            # If this is a text encoder, check its text input
            if "CLIPTextEncode" in class_type:
                text_input = self._get_input_connection(node_data, "text")
                if text_input:
                    return trace_recursive(text_input, depth + 1)
                # Check widget values
                widgets = node_data.get("widgets_values", [])
                if widgets and isinstance(widgets[0], str):
                    return widgets[0]

            # If this is a text processor, get the processed text
            elif any(proc in class_type for proc in ["Wildcard", "Text", "Prompt", "Generator"]):
                widgets = node_data.get("widgets_values", [])
                if widgets and isinstance(widgets[0], str):
                    return widgets[0]

            return ""

        return trace_recursive(start_node_id)

    def _find_complex_text_processors(self, prompt_data: dict) -> list[dict]:
        """Find complex text processing nodes."""
        processors = []

        complex_types = [
            "AdvancedPromptGenerator",
            "ConditionalPrompt",
            "PromptMixer",
            "TextProcessor",
            "PromptEnhancer",
            "StyleApplicator",
            "PromptWeighting",
            "AttentionProcessor",
        ]

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if any(proc_type in class_type for proc_type in complex_types):
                processors.append({"node_id": node_id, "node_data": node_data, "type": class_type})

        return processors

    def _process_complex_processors(self, processors: list[dict], prompt_data: dict) -> str:
        """Process complex text processors to extract final text."""
        for proc in processors:
            node_data = proc["node_data"]
            widgets = node_data.get("widgets_values", [])

            # Look for the processed/output text
            for widget in widgets:
                if isinstance(widget, str) and len(widget.strip()) > 20:
                    return widget.strip()

        return ""

    def _convert_workflow_to_prompt_format(self, workflow_data: dict) -> dict:
        """Convert workflow format to prompt format for easier processing."""
        if "nodes" not in workflow_data:
            return {}

        prompt_format = {}
        nodes = workflow_data["nodes"]

        for i, node in enumerate(nodes):
            if isinstance(node, dict):
                node_id = node.get("id", str(i))
                prompt_format[str(node_id)] = node

        return prompt_format

    def _trace_active_prompt_path(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Trace the active prompt path by following workflow connections."""
        if not isinstance(data, dict):
            return ""

        # Use the dynamic extraction method for now
        return self.extract_dynamic_prompt_from_workflow(data, method_def, context, fields)

    def _extract_multi_step_workflow(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract information from multi-step workflows."""
        if not isinstance(data, dict):
            return {}

        steps = []

        # Find all processing steps
        prompt_data = data.get("prompt", data)

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # Identify different types of processing steps
            step_type = self._classify_processing_step(class_type)
            if step_type:
                steps.append(
                    {
                        "node_id": node_id,
                        "step_type": step_type,
                        "class_type": class_type,
                        "order": len(steps),
                    }
                )

        return {
            "steps": steps,
            "total_steps": len(steps),
            "complexity": "multi_step" if len(steps) > 3 else "simple",
        }

    def _classify_processing_step(self, class_type: str) -> str | None:
        """Classify a node as a processing step type."""
        step_types = {
            "input": ["Load", "Input", "Primitive"],
            "processing": ["Process", "Transform", "Enhance", "Filter"],
            "conditioning": ["CLIP", "Conditioning", "Encode"],
            "generation": ["Sample", "Generate", "Diffuse"],
            "output": ["Save", "Preview", "Export", "Output"],
        }

        for step_type, indicators in step_types.items():
            if any(indicator in class_type for indicator in indicators):
                return step_type

        return None

    def analyze_workflow_complexity(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Analyze the complexity of a workflow."""
        if not isinstance(data, dict):
            return {"complexity": "unknown", "score": 0}

        prompt_data = data.get("prompt", data)

        # Count different types of complexity indicators
        node_count = len(prompt_data)
        custom_node_count = 0
        connection_count = 0
        processing_steps = 0

        for node_data in prompt_data.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # Count custom nodes
            if not self._is_core_node(class_type):
                custom_node_count += 1

            # Count connections
            inputs = node_data.get("inputs", {})
            if isinstance(inputs, dict):
                connection_count += len(inputs)

            # Count processing steps
            if self._classify_processing_step(class_type):
                processing_steps += 1

        # Calculate complexity score
        complexity_score = node_count * 0.3 + custom_node_count * 0.5 + connection_count * 0.2 + processing_steps * 0.4

        if complexity_score < 10:
            complexity_level = "simple"
        elif complexity_score < 25:
            complexity_level = "medium"
        else:
            complexity_level = "complex"

        return {
            "complexity": complexity_level,
            "score": complexity_score,
            "node_count": node_count,
            "custom_node_count": custom_node_count,
            "connection_count": connection_count,
            "processing_steps": processing_steps,
        }

    def _is_core_node(self, class_type: str) -> bool:
        """Check if a node is a core ComfyUI node."""
        core_nodes = [
            "CLIPTextEncode",
            "KSampler",
            "CheckpointLoader",
            "VAELoader",
            "VAEDecode",
            "VAEEncode",
            "SaveImage",
            "PreviewImage",
            "LoraLoader",
            "ControlNetLoader",
            "ControlNetApply",
        ]
        return any(core in class_type for core in core_nodes)

    def _extract_conditional_prompts(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> list[dict]:
        """Extract conditional prompts from workflows."""
        if not isinstance(data, dict):
            return []

        prompt_data = data.get("prompt", data)
        conditional_prompts = []

        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # Look for conditional prompt nodes
            if "Conditional" in class_type or "Switch" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    conditional_prompts.append({"node_id": node_id, "type": class_type, "conditions": widgets})

        return conditional_prompts

    def _resolve_parameter_chains(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Resolve complex parameter chains in workflows."""
        if not isinstance(data, dict):
            return {}

        prompt_data = data.get("prompt", data)
        parameter_chains = {}

        # Find nodes that create parameter chains
        for node_id, node_data in prompt_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")

            # Look for parameter nodes
            if "Parameter" in class_type or "Value" in class_type:
                widgets = node_data.get("widgets_values", [])
                if widgets:
                    parameter_chains[node_id] = {"type": class_type, "values": widgets}

        return parameter_chains
