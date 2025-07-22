# dataset_tools/metadata_engine/extractors/xmp_extractors.py

"""XMP metadata extractors for various AI image generation tools.

Direct XMP parsing for DrawThings, InvokeAI, and other tools that store
metadata in XMP format, providing more robust extraction than fallback methods.
"""

import json
import logging
import re
from typing import Any

import defusedxml.ElementTree as ET

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class XMPExtractor:
    """Direct XMP metadata extractor for AI image generation tools."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the XMP extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "xmp_extract_drawthings": self.extract_drawthings_from_xmp,
            "xmp_extract_invokeai": self.extract_invokeai_from_xmp,
            "xmp_extract_json_usercomment": self.extract_json_from_usercomment,
            "xmp_extract_creator_tool": self.extract_creator_tool,
            "xmp_extract_software": self.extract_software_info,
            "xmp_parse_json_field": self.parse_json_field,
            "xmp_detect_ai_tool": self.detect_ai_tool_from_xmp,
        }

    def _parse_xmp_string(self, xmp_content: str) -> ET.Element | None:
        """Parse XMP string content into XML tree."""
        if not xmp_content:
            return None

        try:
            # Clean up XMP content - remove any leading/trailing whitespace
            xmp_clean = xmp_content.strip()

            # Remove or replace invalid XML characters
            xmp_clean = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", xmp_clean)

            # Parse the XML
            root = ET.fromstring(xmp_clean)
            return root
        except ET.ParseError as e:
            self.logger.warning(f"[XMP] Failed to parse XMP as XML: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"[XMP] Unexpected error parsing XMP: {e}")
            return None

    def _find_xmp_field(self, root: ET.Element, field_name: str) -> str | None:
        """Find a specific field in XMP tree with namespace handling."""
        if root is None:
            return None

        # Common XMP namespaces
        namespaces = {
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "exif": "http://ns.adobe.com/exif/1.0/",
            "xmp": "http://ns.adobe.com/xap/1.0/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "tiff": "http://ns.adobe.com/tiff/1.0/",
        }

        # Try different namespace combinations
        search_patterns = [
            f".//{field_name}",
            f".//exif:{field_name}",
            f".//xmp:{field_name}",
            f".//dc:{field_name}",
            f".//tiff:{field_name}",
        ]

        for pattern in search_patterns:
            try:
                element = root.find(pattern, namespaces)
                if element is not None:
                    return element.text
            except Exception as e:
                self.logger.debug(f"[XMP] Error finding XMP field '{field_name}' with pattern '{pattern}': {e}")
                continue

        # Fallback: search without namespaces
        for elem in root.iter():
            if elem.tag.endswith(field_name) or elem.tag == field_name:
                return elem.text

        return None

    def extract_drawthings_from_xmp(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract DrawThings metadata from XMP."""
        xmp_content = context.get("xmp_string_content", "")
        if not xmp_content:
            return {}

        root = self._parse_xmp_string(xmp_content)
        if root is None:
            return {}

        # Extract UserComment which contains DrawThings JSON
        user_comment = self._find_xmp_field(root, "UserComment")
        if not user_comment:
            return {}

        # Parse JSON from UserComment
        try:
            drawthings_data = json.loads(user_comment)
            if not isinstance(drawthings_data, dict):
                return {}

            result = {
                "tool": "Draw Things",
                "format": "XMP UserComment JSON",
                "prompt": drawthings_data.get("c", ""),
                "negative_prompt": drawthings_data.get("uc", ""),
                "parameters": {
                    "seed": drawthings_data.get("seed"),
                    "steps": drawthings_data.get("steps"),
                    "cfg_scale": drawthings_data.get("scale"),
                    "sampler_name": drawthings_data.get("sampler"),
                    "model": drawthings_data.get("model"),
                    "denoising_strength": drawthings_data.get("strength"),
                },
                "raw_data": drawthings_data,
            }

            # Handle dimensions
            size_str = drawthings_data.get("size", "")
            if "x" in size_str:
                try:
                    w_str, h_str = size_str.split("x", 1)
                    result["parameters"]["width"] = int(w_str.strip())
                    result["parameters"]["height"] = int(h_str.strip())
                except ValueError:
                    pass

            # Handle v2 metadata if present
            if "v2" in drawthings_data:
                v2_data = drawthings_data["v2"]
                result["v2_metadata"] = {
                    "aesthetic_score": v2_data.get("aestheticScore"),
                    "negative_aesthetic_score": v2_data.get("negativeAestheticScore"),
                    "loras": v2_data.get("loras", []),
                }

            return result

        except json.JSONDecodeError as e:
            self.logger.warning(f"[XMP] Failed to parse DrawThings JSON: {e}")
            return {}

    def extract_invokeai_from_xmp(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract InvokeAI metadata from XMP."""
        xmp_content = context.get("xmp_string_content", "")
        if not xmp_content:
            return {}

        root = self._parse_xmp_string(xmp_content)
        if root is None:
            return {}

        result = {}

        # Look for InvokeAI-specific fields
        user_comment = self._find_xmp_field(root, "UserComment")
        if user_comment:
            # Try to parse as InvokeAI JSON
            try:
                invoke_data = json.loads(user_comment)
                if isinstance(invoke_data, dict):
                    result = {
                        "tool": "InvokeAI",
                        "format": "XMP UserComment JSON",
                        "raw_data": invoke_data,
                    }

                    # Extract common InvokeAI fields
                    if "positive_prompt" in invoke_data:
                        result["prompt"] = invoke_data["positive_prompt"]
                    if "negative_prompt" in invoke_data:
                        result["negative_prompt"] = invoke_data["negative_prompt"]

                    # Extract parameters
                    params = {}
                    param_mappings = {
                        "seed": "seed",
                        "steps": "steps",
                        "cfg_scale": "cfg_scale",
                        "scheduler": "scheduler",
                        "width": "width",
                        "height": "height",
                    }

                    for invoke_key, param_key in param_mappings.items():
                        if invoke_key in invoke_data:
                            params[param_key] = invoke_data[invoke_key]

                    if params:
                        result["parameters"] = params

            except json.JSONDecodeError:
                pass

        # Also check for Dream format in description or other fields
        description = self._find_xmp_field(root, "Description")
        if description and "Dream" in description:
            result.update(self._parse_invokeai_dream_format(description))

        return result

    def _parse_invokeai_dream_format(self, dream_string: str) -> dict[str, Any]:
        """Parse InvokeAI Dream format string."""
        try:
            # Pattern: "prompt" -s steps -S seed -C cfg -A sampler
            main_pattern = r'"(.*?)"\s*(-\S.*)?$'
            match = re.search(main_pattern, dream_string)

            if not match:
                return {}

            prompt_text = match.group(1).strip()
            options_str = (match.group(2) or "").strip()

            # Split positive and negative prompts
            positive, negative = self._split_invokeai_prompt(prompt_text)

            result = {
                "tool": "InvokeAI",
                "format": "Dream Format",
                "prompt": positive,
                "negative_prompt": negative,
                "parameters": {},
            }

            # Parse options
            option_pattern = r"-(\w+)\s+([\w.-]+)"
            options = dict(re.findall(option_pattern, options_str))

            option_mappings = {
                "s": "steps",
                "S": "seed",
                "C": "cfg_scale",
                "A": "sampler_name",
                "W": "width",
                "H": "height",
            }

            for opt_key, param_key in option_mappings.items():
                if opt_key in options:
                    try:
                        value = options[opt_key]
                        if param_key in ["steps", "seed", "width", "height"]:
                            result["parameters"][param_key] = int(value)
                        elif param_key == "cfg_scale":
                            result["parameters"][param_key] = float(value)
                        else:
                            result["parameters"][param_key] = value
                    except ValueError:
                        pass

            return result

        except Exception as e:
            self.logger.warning(f"[XMP] Failed to parse Dream format: {e}")
            return {}

    def _split_invokeai_prompt(self, prompt: str) -> tuple[str, str]:
        """Split InvokeAI prompt into positive and negative parts."""
        pattern = r"^(.*?)(?:\s*\[(.*?)\])?$"
        match = re.fullmatch(pattern, prompt.strip())
        if match:
            positive = match.group(1).strip()
            negative = (match.group(2) or "").strip()
        else:
            positive = prompt.strip()
            negative = ""
        return positive, negative

    def extract_json_from_usercomment(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract and parse JSON from XMP UserComment field."""
        xmp_content = context.get("xmp_string_content", "")
        if not xmp_content:
            return {}

        root = self._parse_xmp_string(xmp_content)
        if root is None:
            return {}

        user_comment = self._find_xmp_field(root, "UserComment")
        if not user_comment:
            return {}

        try:
            json_data = json.loads(user_comment)
            return {"usercomment_json": json_data} if isinstance(json_data, dict) else {}
        except json.JSONDecodeError:
            return {}

    def extract_creator_tool(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract creator tool from XMP metadata."""
        xmp_content = context.get("xmp_string_content", "")
        if not xmp_content:
            return ""

        root = self._parse_xmp_string(xmp_content)
        if root is None:
            return ""

        # Check various creator/tool fields
        tool_fields = ["CreatorTool", "Creator", "Software", "Tool"]
        for field in tool_fields:
            tool = self._find_xmp_field(root, field)
            if tool:
                return tool

        return ""

    def extract_software_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, str]:
        """Extract software information from XMP."""
        xmp_content = context.get("xmp_string_content", "")
        if not xmp_content:
            return {}

        root = self._parse_xmp_string(xmp_content)
        if root is None:
            return {}

        software_info = {}

        # Extract various software-related fields
        fields_to_extract = {
            "Software": "software",
            "CreatorTool": "creator_tool",
            "Creator": "creator",
            "Tool": "tool",
            "Application": "application",
        }

        for xmp_field, result_key in fields_to_extract.items():
            value = self._find_xmp_field(root, xmp_field)
            if value:
                software_info[result_key] = value

        return software_info

    def parse_json_field(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Parse a JSON field from XMP metadata."""
        field_name = method_def.get("field_name", "UserComment")
        xmp_content = context.get("xmp_string_content", "")

        if not xmp_content:
            return {}

        root = self._parse_xmp_string(xmp_content)
        if root is None:
            return {}

        field_value = self._find_xmp_field(root, field_name)
        if not field_value:
            return {}

        try:
            json_data = json.loads(field_value)
            return {f"{field_name.lower()}_data": json_data} if isinstance(json_data, dict) else {}
        except json.JSONDecodeError:
            return {"raw_field": field_value}

    def detect_ai_tool_from_xmp(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Detect AI tool from XMP metadata patterns."""
        xmp_content = context.get("xmp_string_content", "")
        if not xmp_content:
            return {"detected_tool": "unknown", "confidence": "none"}

        # Quick pattern matching for known tools
        tool_patterns = {
            "Draw Things": ["Draw Things", "draw-things"],
            "InvokeAI": ["InvokeAI", "invoke-ai", "Dream"],
            "ComfyUI": ["ComfyUI", "comfy-ui"],
            "AUTOMATIC1111": ["AUTOMATIC1111", "A1111", "stable-diffusion-webui"],
            "NovelAI": ["NovelAI", "novel-ai"],
            "Midjourney": ["Midjourney", "midjourney"],
        }

        detected_tools = []
        confidence = "low"

        for tool_name, patterns in tool_patterns.items():
            for pattern in patterns:
                if pattern.lower() in xmp_content.lower():
                    detected_tools.append(tool_name)
                    confidence = "high" if pattern in xmp_content else "medium"
                    break

        if len(detected_tools) == 1:
            return {"detected_tool": detected_tools[0], "confidence": confidence}
        if len(detected_tools) > 1:
            return {
                "detected_tool": detected_tools[0],
                "confidence": "medium",
                "alternatives": detected_tools[1:],
            }
        return {"detected_tool": "unknown", "confidence": "none"}
