# dataset_tools/metadata_engine/extractors/civitai_extractors.py

"""Civitai-specific extraction methods.

Handles extraction from Civitai's special metadata formats, including
their ComfyUI extraMetadata injection system.
"""

import json
import logging
from typing import Any

from ..utils import json_path_get_utility

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class CivitaiExtractor:
    """Handles Civitai-specific extraction methods."""

    def __init__(self, logger: logging.Logger):
        """Initialize the Civitai extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "extract_from_extraMetadata": self._extract_from_extraMetadata,
        }

    def _extract_from_extraMetadata(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract data from Civitai's extraMetadata field.

        This handles Civitai's ComfyUI format where they inject clean metadata
        into the extra.extraMetadata field as a JSON string.
        """
        field_name = method_def.get("field")
        if not field_name:
            self.logger.warning("extract_from_extraMetadata missing 'field'")
            return None

        # Get the extraMetadata from the context
        extra_metadata = self._get_civitai_extra_metadata(context)
        if not extra_metadata:
            return None

        # Extract the requested field
        value = extra_metadata.get(field_name)

        # Handle special field mappings
        if field_name == "negativePrompt" and not value:
            value = extra_metadata.get("negative_prompt", "")
        elif field_name == "cfgScale":
            value = extra_metadata.get("cfg_scale") or extra_metadata.get("cfgScale")
        elif field_name == "sampler":
            value = extra_metadata.get("sampler_name") or extra_metadata.get("sampler")

        self.logger.debug(f"Extracted '{field_name}' from extraMetadata: {value}")
        return value

    def _get_civitai_extra_metadata(self, context: ContextData) -> dict[str, Any] | None:
        """Extract and parse Civitai's extraMetadata from context.

        Returns the parsed extraMetadata dictionary or None if not found.
        """
        # Try to get from workflow first, then prompt
        for chunk_name in ["workflow", "prompt"]:
            chunk_data = context.get("png_chunks", {}).get(chunk_name)
            if not chunk_data:
                continue

            try:
                # Parse the main JSON
                main_json = json.loads(chunk_data) if isinstance(chunk_data, str) else chunk_data

                # Look for extra.extraMetadata
                extra_metadata_str = json_path_get_utility(main_json, "extra.extraMetadata")
                if isinstance(extra_metadata_str, str):
                    # Parse the nested JSON string
                    extra_metadata = json.loads(extra_metadata_str)
                    if isinstance(extra_metadata, dict):
                        self.logger.debug(f"Found Civitai extraMetadata in {chunk_name}")
                        return extra_metadata

            except (json.JSONDecodeError, TypeError) as e:
                self.logger.debug(f"Failed to parse {chunk_name} for extraMetadata: {e}")
                continue

        return None
