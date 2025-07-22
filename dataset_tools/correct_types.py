# dataset_tools/correct_types.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Confirm & Correct Data Type."""

from enum import Enum
from platform import python_version_tuple
from typing import Any, ClassVar  # Standard types for Python 3.9+

from pydantic import BaseModel, TypeAdapter, field_validator

from dataset_tools import LOG_LEVEL

# Conditional import for TypedDict specifically for Pydantic V2 compatibility
# Pydantic V2 wants typing_extensions.TypedDict for Python < 3.12.
# Your project requires Python >= 3.10.
# So for 3.10 and 3.11, use typing_extensions.TypedDict.
# For 3.12+, typing.TypedDict is fine with Pydantic V2.
py_version_major_str, py_version_minor_str, _ = python_version_tuple()
py_version_major = int(py_version_major_str)
py_version_minor = int(py_version_minor_str)

if py_version_major == 3 and py_version_minor < 12:
    from typing_extensions import TypedDict
else:  # Python 3.12+ (or other major versions, though unlikely for this project)
    from typing import TypedDict


# Define constants for magic numbers used in comparisons (for PLR2004)
# Not strictly needed for python_version_tuple comparison as it's clear, but for consistency:
# PYTHON_VERSION_TARGET_MAJOR = 3.0 # If you were comparing float(python_version_tuple()[0])
# PYTHON_VERSION_TARGET_MINOR_MAX = 12.0 # If you were comparing float(python_version_tuple()[1])
MAX_REMAINING_UNPARSED_SPLIT_LEN = 5
MAX_RAW_METADATA_DISPLAY_LEN = 500


class EmptyField(Enum):
    """Represent placeholder or empty field states.

    Used as keys in metadata dictionaries or as UI placeholder text sources.
    """

    PLACEHOLDER = "_dt_internal_placeholder_"
    EMPTY = "_dt_internal_empty_value_"
    # --- ADDED MEMBERS ---
    PLACEHOLDER_POSITIVE = "Positive prompt will appear here."
    PLACEHOLDER_NEGATIVE = "Negative prompt will appear here."
    PLACEHOLDER_DETAILS = "Generation details and other metadata will appear here."
    # --- END OF ADDED MEMBERS ---


class UpField(Enum):
    """Define sections for the upper display area in the UI.

    The string values are used as keys in the metadata dictionary.
    """

    METADATA = "metadata_info_section"
    PROMPT = "prompt_data_section"
    TAGS = "tags_and_keywords_section"
    TEXT_DATA = "text_file_content_section"
    WORKFLOW_ANALYSIS = "workflow_analysis_section"
    # DATA = "generic_data_block_section" # Keep if used

    @classmethod
    def get_ordered_labels(cls) -> list["UpField"]:
        """Return a list of UpField members for UI iteration."""
        return [
            cls.PROMPT,
            cls.TAGS,
            cls.METADATA,
            cls.TEXT_DATA,
            cls.WORKFLOW_ANALYSIS,
        ]


class DownField(Enum):
    """Define sections for the lower display area in the UI.

    The string values are used as keys in the metadata dictionary.
    """

    GENERATION_DATA = "generation_parameters_section"
    RAW_DATA = "raw_tool_specific_data_section"
    EXIF = "standard_exif_data_section"
    JSON_DATA = "json_file_content_section"
    TOML_DATA = "toml_file_content_section"
    # SYSTEM = "system_and_software_section" # Keep if used
    # ICC = "icc_profile_section" # Keep if used
    # LAYER_DATA = "image_layer_data_section" # Keep if used

    @classmethod
    def get_ordered_labels(cls) -> list["DownField"]:
        """Return a list of DownField members for UI iteration."""
        return [
            cls.GENERATION_DATA,
            cls.RAW_DATA,
            cls.EXIF,
            cls.JSON_DATA,
            cls.TOML_DATA,
        ]


class ExtensionType:
    """Contain valid file extensions, categorized for processing."""

    # Individual file types
    PNG_: ClassVar[set[str]] = {".png"}
    JPEG: ClassVar[set[str]] = {".jpg", ".jpeg"}
    WEBP: ClassVar[set[str]] = {".webp"}
    JSON: ClassVar[set[str]] = {".json"}
    TOML: ClassVar[set[str]] = {".toml"}
    TEXT: ClassVar[set[str]] = {".txt", ".text"}
    HTML: ClassVar[set[str]] = {".html", ".htm"}
    XML_: ClassVar[set[str]] = {".xml"}
    GGUF: ClassVar[set[str]] = {".gguf"}
    SAFE: ClassVar[set[str]] = {".safetensors", ".sft"}
    PICK: ClassVar[set[str]] = {".pt", ".pth", ".ckpt", ".pickletensor"}

    # Grouped categories
    IMAGE: ClassVar[list[set[str]]] = [PNG_, JPEG, WEBP]
    EXIF_CAPABLE: ClassVar[list[set[str]]] = [JPEG, WEBP]
    SCHEMA_FILES: ClassVar[list[set[str]]] = [JSON, TOML]
    PLAIN_TEXT_LIKE: ClassVar[list[set[str]]] = [TEXT, XML_, HTML]
    MODEL_FILES: ClassVar[list[set[str]]] = [SAFE, GGUF, PICK]

    IGNORE: ClassVar[list[str]] = [
        "Thumbs.db",
        "desktop.ini",
        ".DS_Store",
        ".fseventsd",
        "._*",
        "~$*",
        "~$*.tmp",
        "*.tmp",
    ]


class NodeNames:
    """Hold constants related to ComfyUI node names and data parsing."""

    ENCODERS: ClassVar[set[str]] = {
        "CLIPTextEncodeFlux",
        "CLIPTextEncodeSD3",
        "CLIPTextEncodeSDXL",
        "CLIPTextEncodeHunyuanDiT",
        "CLIPTextEncodePixArtAlpha",
        "CLIPTextEncodeSDXLRefiner",
        "ImpactWildcardEncodeCLIPTextEncode",
        "BNK_CLIPTextEncodeAdvanced",
        "BNK_CLIPTextEncodeSDXLAdvanced",
        "WildcardEncode //Inspire",
        "TSC_EfficientLoader",
        "TSC_EfficientLoaderSDXL",
        "RgthreePowerPrompt",
        "RgthreePowerPromptSimple",
        "RgthreeSDXLPowerPromptPositive",
        "RgthreeSDXLPowerPromptSimple",
        "AdvancedCLIPTextEncode",
        "AdvancedCLIPTextEncodeWithBreak",
        "Text2Prompt",
        "smZ CLIPTextEncode",
        "CLIPTextEncode",
    }
    STRING_INPUT: ClassVar[set[str]] = {
        "RecourseStrings",
        "StringSelector",
        "ImpactWildcardProcessor",
        "CText",
        "CTextML",
        "CListString",
        "CSwitchString",
        "CR_PromptText",
        "StringLiteral",
        "CR_CombinePromptSDParameterGenerator",
        "WidgetToString",
        "Show Text 🐍",
    }
    PROMPT_LABELS: ClassVar[list[str]] = [
        "Positive prompt",
        "Negative prompt",
        "Prompt",
    ]
    IGNORE_KEYS: ClassVar[list[str]] = [
        "type",
        "link",
        "shape",
        "id",
        "pos",
        "size",
        "node_id",
        "empty_padding",
    ]
    DATA_KEYS: ClassVar[dict[str, str]] = {
        "class_type": "inputs",
        "nodes": "widget_values",
    }
    PROMPT_NODE_FIELDS: ClassVar[set[str]] = {
        "text",
        "t5xxl",
        "clip-l",
        "clip-g",
        "mt5",
        "mt5xl",
        "bert",
        "clip-h",
        "wildcard",
        "string",
        "positive",
        "negative",
        "text_g",
        "text_l",
        "wildcard_text",
        "populated_text",
    }


EXC_INFO: bool = LOG_LEVEL.strip().upper() in ["DEBUG", "TRACE", "NOTSET", "ALL"]


def bracket_check(maybe_brackets: str | dict[str, Any]) -> str | dict[str, Any]:
    """Ensure a string is bracket-enclosed if not a dict, for later parsing."""
    if isinstance(maybe_brackets, dict):
        return maybe_brackets
    if isinstance(maybe_brackets, str):
        corrected_str = maybe_brackets.strip()
        if not corrected_str.startswith("{"):
            corrected_str = "{" + corrected_str
        if not corrected_str.endswith("}"):
            corrected_str = corrected_str + "}"
        return corrected_str
    # Pylint no-else-return: No else needed here as prior conditions return
    raise TypeError("Input for bracket_check must be a string or a dictionary.")


class NodeDataMap(TypedDict):
    class_type: str
    inputs: dict[str, Any] | float | str | list[Any] | None


class NodeWorkflow(TypedDict):
    last_node_id: int
    last_link_id: int | dict[str, Any] | None
    nodes: list[NodeDataMap]
    links: list[Any]
    groups: list[Any]
    config: dict[str, Any]
    extra: dict[str, Any]
    version: float


class BracketedDict(BaseModel):  # pylint: disable=unnecessary-pass
    """Placeholder for a Pydantic model that might use bracket_check."""

    pass  # Or use ... if it's truly empty and a placeholder


class IsThisNode:
    """Hold TypeAdapters for validating parts of ComfyUI JSON data."""

    data: TypeAdapter[NodeDataMap] = TypeAdapter(NodeDataMap)
    workflow: TypeAdapter[NodeWorkflow] = TypeAdapter(NodeWorkflow)


class ListOfDelineatedStr(BaseModel):
    convert: list[Any]

    @field_validator("convert")
    @classmethod
    def drop_tuple(cls, v: list[Any]) -> list[Any]:
        if v and isinstance(v[0], tuple):  # Simplified from original, assuming v is non-empty list if v[0] is accessed
            first_tuple_first_element = next(iter(v[0]), None)
            return [first_tuple_first_element] if first_tuple_first_element is not None else []
        return v
