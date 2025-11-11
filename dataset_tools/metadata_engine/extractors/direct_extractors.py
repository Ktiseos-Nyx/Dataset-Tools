# dataset_tools/metadata_engine/extractors/direct_extractors.py

"""Direct value extraction methods.

Simple extractors that work with basic data types and direct value access.
"""

import logging
from typing import Any

from ..utils import json_path_get_utility

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class DirectValueExtractor:
    """Handles direct value extraction methods."""

    def __init__(self, logger: logging.Logger):
        """Initialize the direct value extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "direct_json_field": self._extract_direct_json_field,
            "direct_json_path": self._extract_direct_json_path,
            "static_value": self._extract_static_value,
            "direct_context_value": self._extract_direct_context_value,
            "direct_string_value": self._extract_direct_string_value,
            "direct_input_data_as_string": self.direct_input_data_as_string,
            "direct_context_key": self._extract_direct_context_key,
            "context_workflow_contains_string": self._context_workflow_contains_string,
            "swarmui_extract_sampler": self._extract_swarmui_extract_sampler,
            "direct_exif_field": self._extract_direct_exif_field,
            "direct_xmp_field": self._extract_direct_xmp_field,
        }

    def direct_input_data_as_string(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str | None:
        """Return the entire input data as a string."""
        self.logger.debug("Executing direct_input_data_as_string")
        if isinstance(data, (str, bytes)):
            return str(data)
        # For dicts or lists, it's better to use a json-specific method.
        # This is a fallback for simple, non-structured text.
        return str(data) if data is not None else None

    def _extract_direct_json_field(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract a simple field directly from a dictionary."""
        field_name = method_def.get("field_name")
        if not field_name:
            self.logger.warning("direct_json_field method missing 'field_name'")
            return None

        if not isinstance(data, dict):
            self.logger.debug("direct_json_field: data is not a dict, cannot extract field")
            return None

        value = data.get(field_name)
        if value is None and not method_def.get("optional", False):
            self.logger.debug("direct_json_field: field '%s' not found in data", field_name)
        return value

    def _extract_direct_json_path(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract value using JSON path query."""
        json_path = method_def.get("json_path")
        if not json_path:
            self.logger.warning("direct_json_path method missing 'json_path'")
            return None

        return json_path_get_utility(data, json_path)

    def _extract_static_value(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Return a static value."""
        return method_def.get("value")

    def _extract_direct_context_value(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Return the data directly."""
        return data

    def _extract_direct_string_value(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str | None:
        """Convert data to string."""
        return str(data) if data is not None else None

    def _extract_direct_context_key(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract a value directly from the context dictionary by key."""
        context_key = method_def.get("context_key")
        if not context_key:
            self.logger.warning("direct_context_key method missing 'context_key' parameter")
            return None

        value = context.get(context_key)
        self.logger.debug("Extracted context key '%s': %s", context_key, "Found" if value is not None else "Not found")
        return value

    def _context_workflow_contains_string(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> bool:
        """Check if the ComfyUI workflow JSON contains a specific string."""
        search_string = method_def.get("search_string")
        if not search_string:
            self.logger.warning("context_workflow_contains_string method missing 'search_string' parameter")
            return False

        # Get workflow from context
        workflow_json = context.get("comfyui_workflow_json")
        if not workflow_json:
            self.logger.debug("No ComfyUI workflow found in context")
            return False

        # Convert workflow to string for searching
        import json
        try:
            if isinstance(workflow_json, dict):
                workflow_str = json.dumps(workflow_json)
            elif isinstance(workflow_json, str):
                workflow_str = workflow_json
            else:
                self.logger.debug("Workflow JSON is unexpected type: %s", type(workflow_json))
                return False

            contains = search_string in workflow_str
            self.logger.debug(
                "Workflow contains '%s': %s",
                search_string[:50] + "..." if len(search_string) > 50 else search_string,
                contains
            )
            return contains

        except Exception as e:
            self.logger.warning("Error checking workflow for string: %s", e)
            return False

    def _extract_swarmui_extract_sampler(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract sampler name from SwarmUI data (comfyui or autoweb backend)."""
        if not isinstance(data, dict):
            return None

        # Try ComfyUI backend field first
        comfyui_field = method_def.get("comfyui_field", "comfyuisampler")
        sampler = data.get(comfyui_field)
        if sampler:
            self.logger.debug("SwarmUI sampler from ComfyUI backend: %s", sampler)
            return sampler

        # Try AutoWebUI backend field
        autoweb_field = method_def.get("autoweb_field", "autowebuisampler")
        sampler = data.get(autoweb_field)
        if sampler:
            self.logger.debug("SwarmUI sampler from AutoWebUI backend: %s", sampler)
            return sampler

        # Fallback to generic 'sampler' field
        sampler = data.get("sampler")
        if sampler:
            self.logger.debug("SwarmUI sampler from generic field: %s", sampler)
            return sampler

        return None

    def _extract_direct_exif_field(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract EXIF field using pyexiv2 mapped fields.

        Extracts from context['exif_fields'] which contains friendly field names.
        Example: field_name="Make" extracts camera make from mapped EXIF data.
        """
        field_name = method_def.get("field_name")
        if not field_name:
            self.logger.warning("direct_exif_field method missing 'field_name'")
            return None

        # Get mapped EXIF fields from context (friendly names)
        exif_fields = context.get("exif_fields", {})
        value = exif_fields.get(field_name)

        if value is None:
            # Fallback: try raw pyexiv2 EXIF with prefixed keys
            pyexiv2_exif = context.get("pyexiv2_exif", {})
            # Try common prefixes
            for prefix in ["Exif.Photo.", "Exif.Image.", "Exif.GPSInfo."]:
                prefixed_key = f"{prefix}{field_name}"
                value = pyexiv2_exif.get(prefixed_key)
                if value is not None:
                    self.logger.debug("Found EXIF field '%s' with prefix '%s'", field_name, prefix)
                    break

        if value is not None:
            self.logger.debug("Extracted EXIF field '%s': %s", field_name, str(value)[:100])
        else:
            self.logger.debug("EXIF field '%s' not found", field_name)

        return value

    def _extract_direct_xmp_field(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> Any:
        """Extract XMP field using pyexiv2 mapped fields.

        Extracts from context['xmp_fields'] which contains friendly field names.
        Example: field_name="CreatorTool" extracts software name from mapped XMP data.
        """
        field_name = method_def.get("field_name")
        if not field_name:
            self.logger.warning("direct_xmp_field method missing 'field_name'")
            return None

        # Get mapped XMP fields from context (friendly names)
        xmp_fields = context.get("xmp_fields", {})
        value = xmp_fields.get(field_name)

        if value is None:
            # Fallback: try raw pyexiv2 XMP with prefixed keys
            pyexiv2_xmp = context.get("pyexiv2_xmp", {})
            # Try common prefixes
            for prefix in ["Xmp.dc.", "Xmp.xmp.", "Xmp.tiff.", "Xmp.exif.", "Xmp.photoshop."]:
                prefixed_key = f"{prefix}{field_name}"
                value = pyexiv2_xmp.get(prefixed_key)
                if value is not None:
                    self.logger.debug("Found XMP field '%s' with prefix '%s'", field_name, prefix)
                    break

        if value is not None:
            self.logger.debug("Extracted XMP field '%s': %s", field_name, str(value)[:100])
        else:
            self.logger.debug("XMP field '%s' not found", field_name)

        return value
