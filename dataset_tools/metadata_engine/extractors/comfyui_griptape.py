"""ComfyUI Griptape AI Extractor.

Specialized extractor for ComfyUI workflows using Griptape AI framework.
Handles intelligent prompt generation and agent-based workflows with 
numpy-enhanced candidate scoring.
"""

import logging
from typing import Any

from .comfyui_node_dictionary_manager import ComfyUINodeDictionaryManager

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ComfyUIGriptapeExtractor:
    """Extracts data from ComfyUI workflows using Griptape AI nodes."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the Griptape extractor."""
        self.logger = logger

        # Initialize dictionary manager for enhanced extraction
        self.dictionary_manager = ComfyUINodeDictionaryManager(logger)

        # Node type scoring for candidate prioritization (from numpy research)
        self.node_scores = {
            "Text Multiline": 2.5,  # High priority for user input
            "Griptape Display: Text": 2.0,  # AI-generated content
            "Griptape Create: Agent": 1.8,  # Agent prompts
            "Griptape Create: Rules": 1.5,  # Rule definitions
            "CLIPTextEncode": 1.0,  # Standard encoding (may contain templates)
        }

    def extract_griptape_smart_prompt(self, data: ContextData, fields: ExtractedFields, definition: MethodDefinition) -> None:
        """Extract the best prompt from Griptape AI workflow using smart candidate scoring."""
        workflow = self._get_workflow_data(data)
        if not workflow:
            return

        # Find all potential prompt candidates
        candidates = self._find_prompt_candidates(workflow)

        if not candidates:
            self.logger.debug("[Griptape] No prompt candidates found")
            return

        # Score and rank candidates using numpy-enhanced logic
        scored_candidates = self._score_candidates(candidates)

        # Select the best candidate
        best_candidate = max(scored_candidates, key=lambda c: c["score"])

        # Extract target field from definition
        target_field = definition.get("target_field", "prompt")

        # Store the result
        fields[target_field] = best_candidate["text"]

        self.logger.info(f"[Griptape] Selected {best_candidate['node_type']} with score {best_candidate['score']:.2f}")

    def _get_workflow_data(self, data: ContextData) -> dict[str, Any] | None:
        """Extract workflow data from context."""
        for key in ["workflow", "workflow_api", "raw_workflow"]:
            if key in data and isinstance(data[key], dict):
                return data[key]
        return None

    def _find_prompt_candidates(self, workflow: dict[str, Any]) -> list[dict[str, Any]]:
        """Find all potential prompt sources in the workflow."""
        candidates = []
        nodes = workflow.get("nodes", [])

        for node in nodes:
            if not isinstance(node, dict):
                continue

            node_type = node.get("type", "")
            node_id = node.get("id")
            widgets = node.get("widgets_values", [])

            # Extract text based on node type (from our research)
            text = self._extract_text_from_node(node_type, widgets)

            if text and len(text.strip()) > 5:  # Minimum viable text
                candidates.append({
                    "text": text.strip(),
                    "node_type": node_type,
                    "node_id": node_id,
                    "widgets": widgets
                })

        return candidates

    def _extract_text_from_node(self, node_type: str, widgets: list) -> str:
        """Extract text from specific node types (based on numpy research)."""
        if not widgets:
            return ""

        if node_type == "Text Multiline":
            # Text Multiline: simple text content in widgets[0]
            if len(widgets) > 0 and isinstance(widgets[0], str):
                return widgets[0]

        elif node_type == "Griptape Display: Text":
            # Griptape Display: Text - content in widgets[1]
            if len(widgets) > 1 and isinstance(widgets[1], str):
                content = widgets[1]
                # Skip API error messages (from numpy research)
                if "api_key" in content.lower() and "environment variable" in content.lower():
                    return ""
                return content

        elif node_type == "Griptape Create: Agent":
            # Griptape Agent - main prompt in widgets[1]
            if len(widgets) > 1 and isinstance(widgets[1], str):
                return widgets[1]

        elif node_type == "Griptape Create: Rules":
            # Griptape Rules - rule content in widgets[1]
            if len(widgets) > 1 and isinstance(widgets[1], str):
                return widgets[1]

        elif node_type == "CLIPTextEncode":
            # Standard CLIP encoding - widgets[0]
            if len(widgets) > 0 and isinstance(widgets[0], str):
                return widgets[0]

        return ""

    def _score_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Score candidates using numpy-enhanced logic from our research."""
        for candidate in candidates:
            score = self._calculate_candidate_score(candidate)
            candidate["score"] = score

        return candidates

    def _calculate_candidate_score(self, candidate: dict[str, Any]) -> float:
        """Calculate score for a candidate (key logic from numpy research)."""
        text = candidate["text"]
        node_type = candidate["node_type"]

        # Base score
        score = 5.0

        # Node type bonus
        node_bonus = self.node_scores.get(node_type, 0)
        score += node_bonus

        # Length bonus (capped to prevent runaway scores)
        text_length = len(text)
        if text_length > 200:
            score += min(3.0, text_length / 100)  # Cap at +3
        elif text_length > 50:
            score += 1.5
        elif text_length < 10:
            score -= 1

        # Griptape-specific boost for Text Multiline (KEY FIX from numpy research)
        if node_type == "Text Multiline" and text_length > 50:
            # In Griptape workflows, Text Multiline often contains the REAL user prompt
            # while CLIPTextEncode might have template/NSFW content
            score += 8.0  # Strong boost to beat CLIPTextEncode
            self.logger.debug("[Griptape] Text Multiline boost applied: +8.0")

        # Template detection penalty (from numpy research)
        if self._is_template_text(text):
            score -= 5.0

        return score

    def _is_template_text(self, text: str) -> bool:
        """Check if text appears to be template/placeholder content."""
        text_lower = text.lower().strip()

        # Common template patterns
        template_indicators = [
            "positive", "negative", "prompt", "text", "input",
            "enter text here", "placeholder"
        ]

        return any(indicator == text_lower for indicator in template_indicators)

    def get_methods(self) -> dict[str, Any]:
        """Return available extraction methods."""
        return {
            "extract_griptape_smart_prompt": self.extract_griptape_smart_prompt,
        }
