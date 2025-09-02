"""Workflow Classification Module
===========================

Identifies and classifies different types of ComfyUI workflows
for optimized processing strategies.
"""

from typing import Any

# Advanced workflow detection patterns
WORKFLOW_INDICATORS = {
    "dynamic_prompts": ["DPRandomGenerator", "WildcardProcessor", "Wildcard Processor", "ImpactWildcardProcessor"],
    "multi_stage": ["StableCascade", "StageA", "StageB", "StageC"],
    "custom_ecosystem": ["hidream", "pixart", "flux", "auraflow", "griptape"],
    "complex_conditioning": ["ConditioningCombine", "ConditioningConcat", "ConditioningSetArea"],
    "template_systems": ["ShowText", "StringConstant", "ConcatStringSingle"]
}


class WorkflowClassifier:
    """Classifies ComfyUI workflows by type and complexity."""

    def classify_workflow_type(self, workflow_data: dict[str, Any]) -> str:
        """Classify the workflow type for optimized processing."""
        nodes = workflow_data.get("nodes", [])
        if not nodes:
            return "unknown"

        node_types = [node.get("type", "") for node in nodes if isinstance(node, dict)]

        # Check for specific workflow patterns
        if any(t in node_types for t in ["DPRandomGenerator", "ImpactWildcardProcessor"]):
            return "randomizer"
        if any(t in node_types for t in ["Griptape Display: Text", "Griptape Create: Agent"]):
            print(f"NUMPY DEBUG: Found Griptape nodes in workflow, detected node types: {node_types}")
            return "griptape"
        if any(t in node_types for t in ["T5TextEncode", "PixArtT5TextEncode", "BasicGuider"]):
            return "flux_t5"
        if any(t in node_types for t in ["easy positive", "Text Concatenate (JPS)"]):
            return "hidream"
        return "standard"
