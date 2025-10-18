# dataset_tools/metadata_engine/extractors/civitai_extractors.py

"""Civitai-specific extraction methods.

Handles extraction from Civitai's special metadata formats, including
their ComfyUI extraMetadata injection system and API data fetching.
"""

# Module loading confirmation moved to logger
import logging
_module_logger = logging.getLogger(__name__)
_module_logger.info("=" * 80)
_module_logger.info("[CIVITAI_EXTRACTORS] MODULE LOADING - THIS SHOULD ALWAYS SHOW!")
_module_logger.info("=" * 80)

import json
import logging
import re
from typing import Any

from ... import civitai_api
from ...correct_types import DownField, UpField
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
            "civitai_extract_all_info": self.extract_all_info,
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

    def extract_all_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract CivitAI resource IDs for UI-level async fetching.

        Parses URN:AIR resources from ComfyUI workflows and civitai_resources
        from A1111 metadata. Returns structured ID data for the UI to fetch
        asynchronously (avoids freezing during metadata load).

        Returns:
            Dictionary with 'ids_to_fetch' list for background API calls.
        """
        self.logger.info("=" * 80)
        self.logger.info("[CIVITAI_EXTRACTOR] extract_all_info METHOD CALLED!")
        self.logger.info("=" * 80)

        ids_to_fetch = []

        # ComfyUI URN parsing - check both fields (current extraction) and context (fallback)
        civitai_urns = []

        # DEBUG: Log what's in fields
        self.logger.info("[CIVITAI_EXTRACTOR_DEBUG] fields keys: %s", list(fields.keys()))

        # Check the fields dict for already-extracted civitai_airs
        # Note: The metadata engine stores extracted fields with _VAR_ suffix
        civitai_airs_field = (
            fields.get("parameters_VAR_civitai_airs") or
            fields.get("civitai_airs") or
            fields.get("parameters.civitai_airs")
        )
        self.logger.info("[CIVITAI_EXTRACTOR_DEBUG] civitai_airs = %s", civitai_airs_field)

        if civitai_airs_field and isinstance(civitai_airs_field, list):
            civitai_urns.extend(civitai_airs_field)

        # Also check for model field
        model_field = (
            fields.get("parameters_VAR_model") or
            fields.get("model") or
            fields.get("parameters.model")
        )
        self.logger.info("[CIVITAI_EXTRACTOR_DEBUG] model = %s", model_field)

        if model_field and isinstance(model_field, str):
            civitai_urns.append(model_field)

        # Fallback: check context if fields didn't have it
        if not civitai_urns:
            parameters = context.get(DownField.GENERATION_DATA.value, {})
            if "civitai_airs" in parameters and isinstance(parameters["civitai_airs"], list):
                for air in parameters["civitai_airs"]:
                    if isinstance(air, str):
                        civitai_urns.append(air)
            if "model" in parameters and isinstance(parameters["model"], str):
                civitai_urns.append(parameters["model"])
        prompt_text = context.get(UpField.PROMPT.value, {}).get("Positive", "")
        negative_prompt_text = context.get(UpField.PROMPT.value, {}).get("Negative", "")
        full_prompt = f"{prompt_text} {negative_prompt_text}"

        # Safety check: only search prompts up to 100KB to avoid regex issues
        if len(full_prompt) < 100000:
            civitai_urns.extend(re.findall(r'urn:air:.*?civitai:[0-9]+@[0-9]+', full_prompt))
        else:
            self.logger.warning("[CIVITAI] Prompt too large (%d chars), skipping URN search", len(full_prompt))

        civitai_urns = list(set(civitai_urns))

        for urn_string in civitai_urns:
            if isinstance(urn_string, str):
                urn_match = re.search(r'urn:air:.*?civitai:([0-9]+)@([0-9]+)', urn_string)
                if urn_match:
                    model_id, version_id = urn_match.groups()
                    ids_to_fetch.append({"model_id": model_id, "version_id": version_id})

        # A1111 civitai_resources parsing
        tool_specific = context.get("unclassified", {}).get("tool_specific", {})
        if "civitai_resources" in tool_specific and isinstance(tool_specific["civitai_resources"], str):
            try:
                resources = json.loads(tool_specific["civitai_resources"])
                for resource in resources:
                    if "modelVersionId" in resource:
                        ids_to_fetch.append({"version_id": str(resource["modelVersionId"])})
            except json.JSONDecodeError:
                pass

        self.logger.info("[CIVITAI_EXTRACTOR] Found IDs to fetch: %s", ids_to_fetch)

        # Return IDs for UI to fetch asynchronously - NO API CALLS HERE
        # This keeps metadata loading fast and UI responsive
        return {"ids_to_fetch": ids_to_fetch, "fetch_pending": len(ids_to_fetch) > 0}
