# dataset_tools/metadata_engine/extractors/a1111_extractors.py

"""AUTOMATIC1111 extraction methods.

Handles parsing of A1111 WebUI parameter strings, including prompts,
negative prompts, and generation parameters.
"""

import logging
import re
from typing import Any

from ..utils import get_a1111_kv_block_utility

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class A1111Extractor:
    """Handles AUTOMATIC1111-specific extraction methods."""

    def __init__(self, logger: logging.Logger):
        """Initialize the A1111 extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "a1111_extract_prompt_positive": self._extract_a1111_prompt_positive,
            "a1111_extract_prompt_negative": self._extract_a1111_prompt_negative,
            "key_value_extract_from_a1111_block": self._extract_a1111_key_value,
            "key_value_extract_transform_from_a1111_block": self._extract_a1111_key_value_transform,
        }

    def _extract_a1111_prompt_positive(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str | None:
        """Extract positive prompt from A1111 format."""
        if not isinstance(data, str):
            return None

        # Find where negative prompt starts
        neg_match = re.search(r"\nNegative prompt:", data, re.IGNORECASE)
        end_index = len(data)

        if neg_match:
            end_index = min(end_index, neg_match.start())

        # Find where key-value block starts
        kv_block = get_a1111_kv_block_utility(data)
        if kv_block:
            try:
                first_kv_line = kv_block.split("\n", 1)[0].strip()
                if first_kv_line:
                    kv_start = data.rfind(first_kv_line)
                    if kv_start != -1:
                        end_index = min(end_index, kv_start)
            except (ValueError, AttributeError):
                pass

        return data[:end_index].strip()

    def _extract_a1111_prompt_negative(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract negative prompt from A1111 format."""
        if not isinstance(data, str):
            return ""

        # Pattern to match negative prompt section
        pattern = (
            r"\nNegative prompt:(.*?)"
            r"(?=(\n(?:Steps:|Sampler:|CFG scale:|Seed:|Size:|Model hash:|Model:|Version:|$)))"
        )

        neg_match = re.search(pattern, data, re.IGNORECASE | re.DOTALL)
        return neg_match.group(1).strip() if neg_match else ""

    def _extract_a1111_key_value(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str | None:
        """Extract a specific key-value pair from A1111 parameter block."""
        if not isinstance(data, str):
            return None

        kv_block = get_a1111_kv_block_utility(data)
        key_name = method_def.get("key_name")

        if not kv_block or not key_name:
            return None

        # Create pattern to find the key and its value
        lookahead_pattern = (
            r"(?:,\s*(?:Steps:|Sampler:|CFG scale:|Seed:|Size:|Model hash:|Model:|"
            r"Version:|Clip skip:|Denoising strength:|Hires upscale:|Hires steps:|"
            r"Hires upscaler:|Lora hashes:|TI hashes:|Emphasis:|NGMS:|ADetailer model:|"
            r"Schedule type:))|$"
        )

        key_pattern = re.escape(key_name)
        match = re.search(rf"{key_pattern}:\s*(.*?)(?={lookahead_pattern})", kv_block, re.IGNORECASE)

        return match.group(1).strip() if match else None

    def _extract_a1111_key_value_transform(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str | None:
        """Extract and transform a key-value pair from A1111 format."""
        # First extract the raw value
        raw_value = self._extract_a1111_key_value(data, method_def, context, fields)

        if raw_value is None:
            return None

        # Apply transformation if specified
        transform_regex = method_def.get("transform_regex")
        if not transform_regex:
            return raw_value

        transform_match = re.search(transform_regex, raw_value)
        if transform_match:
            group_num = method_def.get("transform_group", 1)
            return transform_match.group(group_num)

        return None
