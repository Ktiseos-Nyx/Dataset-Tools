"""Text Extraction Module
=====================

Handles text extraction from various ComfyUI node types
with specialized logic for different node ecosystems.
"""

import re
from typing import Any


class TextExtractor:
    """Extracts text content from ComfyUI nodes with format-specific handling."""

    def extract_text_from_node(self, node: dict[str, Any], source_info: dict[str, Any]) -> str:
        """Extract text content from a source node with comprehensive node type handling."""
        node_type = node.get("type") or node.get("class_type", "")
        widgets = node.get("widgets_values", [])

        # Special handling for dynamic prompt generation nodes
        if node_type == "DPRandomGenerator":
            # DPRandomGenerator: text is in widgets_values[0] (the wildcard template)
            if widgets and len(widgets) > 0 and isinstance(widgets[0], str):
                potential_text = widgets[0].strip()
                # Skip if it looks like seed numbers or metadata
                if potential_text.startswith("[") and potential_text.endswith("]"):
                    return ""
                if potential_text.isdigit() or (potential_text.replace(".", "").isdigit()):
                    return ""
                return potential_text

        elif node_type == "easy showAnything":
            # easy showAnything: text content is in widgets_values[0][0] (nested array)
            if widgets and len(widgets) > 0:
                content = widgets[0]
                if isinstance(content, list) and len(content) > 0 and isinstance(content[0], str):
                    return content[0].strip()
                if isinstance(content, str):
                    return content.strip()

        elif node_type == "ShowText|pysssss":
            # ShowText|pysssss: text content can be nested - widgets_values[0][0] for fox workflow
            if widgets and len(widgets) > 0:
                content = widgets[0]
                if isinstance(content, list) and len(content) > 0:
                    inner_content = content[0]
                    if isinstance(inner_content, str):
                        return inner_content.strip()
                elif isinstance(content, str):
                    return content.strip()

        elif node_type == "Text Multiline":
            # Text Multiline: simple text content in widgets_values[0]
            if widgets and len(widgets) > 0 and isinstance(widgets[0], str):
                return widgets[0].strip()

        elif node_type == "Text _O":
            # Text _O node (Chinese workflow): text content in widgets_values[0]
            if widgets and len(widgets) > 0 and isinstance(widgets[0], str):
                return widgets[0].strip()

        elif node_type == "Griptape Display: Text":
            # Griptape Display: Text - usually contains AI-generated content
            if widgets and len(widgets) > 1:
                content = widgets[1]
                if isinstance(content, str) and content.strip():
                    # Skip obvious error messages but allow other content
                    if "api_key" in content.lower() and "environment variable" in content.lower():
                        return ""
                    return content.strip()
            return ""

        elif node_type == "Griptape Create: Rules":
            # Griptape Rules - extract the rule content, might be useful for context
            if widgets and len(widgets) > 1:
                content = widgets[1]
                if isinstance(content, str) and content.strip():
                    return content.strip()
            return ""

        elif node_type == "Griptape Create: Agent":
            # Griptape Agent - contains the main prompt
            if widgets and len(widgets) > 1:
                content = widgets[1]
                if isinstance(content, str) and content.strip():
                    return content.strip()
            return ""

        elif node_type in ["ConcatStringSingle", "Text Concatenate"]:
            # These nodes combine multiple STRING inputs - check if there are stored results first
            for widget in widgets:
                if isinstance(widget, str) and widget.strip() and len(widget) > 5:
                    return widget.strip()
            return ""

        # Standard ComfyUI nodes
        elif node_type in ["CLIPTextEncode", "CLIPTextEncodeSDXL", "T5TextEncode", "PixArtT5TextEncode"]:
            if widgets and len(widgets) > 0 and isinstance(widgets[0], str):
                return widgets[0].strip()

        return ""

    def is_comfyui_template_text(self, text: str) -> bool:
        """Check if text appears to be template/placeholder content rather than user input."""
        if not text or len(text.strip()) < 3:
            return True

        text_lower = text.lower().strip()

        # Template indicators
        template_patterns = [
            r"^(positive|negative|prompt)$",
            r"^\s*(text|input|enter.*here|placeholder)\s*$",
            r"^\s*\d+\s*$",  # Just numbers
            r"^\s*[.,;:]+\s*$",  # Just punctuation
        ]

        return any(re.match(pattern, text_lower) for pattern in template_patterns)

    def parse_ai_generated_prompt(self, raw_text: str) -> str:
        """Parse AI-generated prompts and clean them up."""
        if not raw_text:
            return ""

        text = raw_text.strip()

        # Remove common AI prompt prefixes
        prefixes_to_remove = [
            "You are an assistant designed to generate anime images based on textual prompts.",
            "<Prompt Start>",
            "Generate an image of:",
            "Create an image showing:",
        ]

        for prefix in prefixes_to_remove:
            if prefix in text:
                text = text.split(prefix)[-1].strip()

        return text.strip()
