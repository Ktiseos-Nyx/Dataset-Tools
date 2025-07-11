# dataset_tools/display_formatter.py
# --- FINAL CORRECTED AND VERIFIED VERSION 2 ---

import logging
from typing import Any

from .correct_types import DownField, EmptyField, UpField

log = logging.getLogger(__name__)

# This is the main public function for this module


def format_metadata_for_display(metadata_dict: dict[str, Any] | None) -> dict[str, str]:
    """Takes raw metadata and returns a dictionary of formatted strings for UI display.
    This function is a "pure" formatter; it does not interact with the UI.
    """
    if metadata_dict is None:
        return {
            "positive": "",
            "negative": "",
            "details": "Info/Error:\nNo metadata to display.",
        }

    # Check for empty/error states - handle both old and new formats
    if len(metadata_dict) == 1:
        # Old format: _dt_internal_placeholder_
        if EmptyField.PLACEHOLDER.value in metadata_dict:
            content = metadata_dict.get(EmptyField.PLACEHOLDER.value, {})
            error_msg = content.get("Error", content.get("Info", "No metadata to display."))
            return {
                "positive": "",
                "negative": "",
                "details": f"Info/Error:\n{error_msg}",
            }

        # New format: info
        if "info" in metadata_dict:
            content = metadata_dict.get("info", {})
            error_msg = content.get("Error", content.get("Info", "No metadata to display."))
            return {
                "positive": "",
                "negative": "",
                "details": f"Info/Error:\n{error_msg}",
            }

    # If we are here, metadata_dict is valid.
    positive, negative = _format_prompts(metadata_dict)
    details = _build_details_string(metadata_dict)

    return {"positive": positive, "negative": negative, "details": details}


# --- Private Helper Functions for this Module ---


def _format_prompts(metadata_dict: dict[str, Any]) -> tuple[str, str]:
    """Extracts and formats positive and negative prompts."""
    # First check the structured prompt section
    prompt_section = metadata_dict.get(UpField.PROMPT.value, {})
    if isinstance(prompt_section, dict):
        positive = str(prompt_section.get("Positive", "")).strip()
        negative = str(prompt_section.get("Negative", "")).strip()

        # If we found prompts in the structured section, return them
        if positive or negative:
            return positive, negative

    # Fallback: check root level for direct prompt fields (e.g., Drawthings JSON parser)
    positive = str(metadata_dict.get("prompt", "")).strip()
    negative = str(metadata_dict.get("negative_prompt", "")).strip()
    return positive, negative


def _build_details_string(metadata_dict: dict[str, Any]) -> str:
    """Builds the large, formatted string for the main details box."""
    details_parts: list[str] = []
    section_separator = "\n\n" + "═" * 30 + "\n\n"

    # Detected Tool
    if "Detected Tool" in (metadata_s := metadata_dict.get(UpField.METADATA.value, {})):
        details_parts.append(f"Detected Tool: {metadata_s['Detected Tool']}")

    # Generation Parameters
    if gen_params := metadata_dict.get(DownField.GENERATION_DATA.value):
        param_strings = []

        # 🚨 CRIME #3: MAKE TOOL DETECTION LOUD AND PROUD! 🚨
        # Add detected tool as the FIRST parameter for maximum visibility
        if "Detected Tool" in (metadata_s := metadata_dict.get(UpField.METADATA.value, {})):
            param_strings.append(f"Tool: {metadata_s['Detected Tool']}")

        # Add all other generation parameters (sorted for consistency)
        other_params = [f"{k}: {v}" for k, v in sorted(gen_params.items())]
        param_strings.extend(other_params)

        if param_strings:
            joined_params = "\n".join(param_strings)
            details_parts.append(f"Generation Parameters:\n{joined_params}")

    # --- START OF THE CORRECTLY INDENTED BLOCK ---

    # This is a nested function, defined *inside* _build_details_string
    # It has access to 'details_parts' and 'metadata_dict' from its parent scope.
    def append_unpacked_section(title: str, field: Any):  # noqa: ANN401
        if display_text := _unpack_content_of(metadata_dict, [field]).strip():
            details_parts.append(f"{title}:\n{display_text}")

    append_unpacked_section("EXIF Details", DownField.EXIF)
    append_unpacked_section("Tags (XMP/IPTC)", UpField.TAGS)
    append_unpacked_section("Workflow Analysis", UpField.WORKFLOW_ANALYSIS)

    # Raw Data / Workflow
    if raw_content := str(metadata_dict.get(DownField.RAW_DATA.value, "")):
        title = "Raw Data / Workflow (JSON)" if raw_content.strip().startswith("{") else "Raw Data / Workflow"
        details_parts.append(f"{title}:\n{raw_content}")

    # This return is now correctly inside the function
    return section_separator.join(filter(None, details_parts))

    # --- END OF THE CORRECTLY INDENTED BLOCK ---


# --- Formatting Logic Moved from ui.py ---


def _unpack_content_of(metadata_dict: dict[str, Any], labels_to_extract: list[Any]) -> str:
    """Unpacks and formats data from specified sections of the metadata."""
    all_texts: list[str] = []
    for section_enum in labels_to_extract:
        if section_data := metadata_dict.get(section_enum.value):
            all_texts.extend(_format_single_section_data(section_data))
    return "\n".join(all_texts)


def _format_single_section_data(data_item: Any) -> list[str]:  # noqa: ANN401
    """Recursively formats a piece of data (dict, list, or primitive) into a list of strings.
    This function is intentionally dynamic, so we suppress the ANN401 warning.
    """
    parts: list[str] = []
    if isinstance(data_item, dict):
        for key, value in sorted(data_item.items()):
            if value is None:
                continue
            if isinstance(value, dict):
                # Format sub-dictionary with indentation
                nested_parts = _format_single_section_data(value)
                if nested_parts:
                    parts.append(f"{key}:")
                    parts.extend([f"  {p}" for p in nested_parts])
            else:
                parts.append(f"{key}: {value!s}")
    elif isinstance(data_item, list):
        parts.extend(str(item) for item in data_item)
    elif data_item is not None:
        parts.append(str(data_item))
    return parts
