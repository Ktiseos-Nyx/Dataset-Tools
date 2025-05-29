# dataset_tools/correct_types.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Confirm & Correct Data Type"""

from platform import python_version_tuple
from enum import Enum  # Essential for defining Enums

# from ast import Constant # This was not needed for the Enum structure

from pydantic import TypeAdapter, BaseModel, field_validator

# IMPORTANT: Import LOG_LEVEL directly into this module for EXC_INFO
from dataset_tools import LOG_LEVEL

# Typing imports conditional on Python version
if float(python_version_tuple()[0]) == 3.0 and float(python_version_tuple()[1]) <= 12.0:
    from typing_extensions import TypedDict, List, Union, Set  # Use List from typing_extensions
else:
    from typing import TypedDict, List, Union, Set  # Use List from typing


class EmptyField(Enum):
    """When no data is available. Used as keys in metadata dictionaries."""

    PLACEHOLDER = "_dt_internal_placeholder_"  # Key for placeholder messages
    EMPTY = "_dt_internal_empty_value_"  # Key for an intentionally empty field state
    # If you had specific placeholder messages for UI, they might be defined elsewhere or here:
    # PLACEHOLDER_PROMPT_TEXT = "Prompt Information Area" # Example
    # PLACEHOLDER_GEN_TEXT = "Generation Details Area"    # Example
    # PLACEHOLDER_DETAILS_TEXT = "No specific details available." # Example


class UpField(Enum):
    """Defines sections for the upper display area in the UI.
    The string values are used as keys in the metadata dictionary.
    """

    METADATA = "metadata_info_section"
    PROMPT = "prompt_data_section"
    TAGS = "tags_and_keywords_section"
    TEXT_DATA = "text_file_content_section"  # For .txt file content
    # DATA = "generic_data_block_section" # This was present, keep if used

    @classmethod
    def get_ordered_labels(cls) -> List["UpField"]:
        """Returns a list of UpField members in their definition order for UI iteration."""
        # Define the explicit order you want them to appear in the UI if it's specific
        # If definition order is fine, list(cls) is okay.
        # For example, if you want a specific order:
        return [cls.PROMPT, cls.TAGS, cls.METADATA, cls.TEXT_DATA]  # Add DATA if used
        # Or if definition order is fine:
        # return list(cls)


class DownField(Enum):
    """Defines sections for the lower display area in the UI.
    The string values are used as keys in the metadata dictionary.
    """

    GENERATION_DATA = "generation_parameters_section"
    RAW_DATA = "raw_tool_specific_data_section"  # Raw metadata string from AI tool
    EXIF = "standard_exif_data_section"
    # SYSTEM = "system_and_software_section" # Keep if used
    # ICC = "icc_profile_section" # Keep if used
    # LAYER_DATA = "image_layer_data_section" # Keep if used
    JSON_DATA = "json_file_content_section"  # For .json file content
    TOML_DATA = "toml_file_content_section"  # For .toml file content

    @classmethod
    def get_ordered_labels(cls) -> List["DownField"]:
        """Returns a list of DownField members in a specific order for UI iteration."""
        # Define the explicit order
        return [cls.GENERATION_DATA, cls.RAW_DATA, cls.EXIF, cls.JSON_DATA, cls.TOML_DATA]  # Add others if used
        # Or if definition order is fine:
        # return list(cls)


class ExtensionType:
    """Container for valid file extensions, categorized for processing."""

    # Individual file types
    PNG_: Set[str] = {".png"}
    JPEG: Set[str] = {".jpg", ".jpeg"}
    WEBP: Set[str] = {".webp"}
    JSON: Set[str] = {".json"}
    TOML: Set[str] = {".toml"}
    TEXT: Set[str] = {".txt", ".text"}
    HTML: Set[str] = {".html", ".htm"}
    XML_: Set[str] = {".xml"}
    GGUF: Set[str] = {".gguf"}
    SAFE: Set[str] = {".safetensors", ".sft"}
    PICK: Set[str] = {".pt", ".pth", ".ckpt", ".pickletensor"}

    # Grouped categories - these are the attributes widgets.py will use
    IMAGE: List[Set[str]] = [PNG_, JPEG, WEBP]
    EXIF_CAPABLE: List[Set[str]] = [JPEG, WEBP]  # Files typically supporting rich EXIF
    SCHEMA_FILES: List[Set[str]] = [JSON, TOML]  # Corrected attribute name for widgets.py
    PLAIN_TEXT_LIKE: List[Set[str]] = [TEXT, XML_, HTML]  # Corrected attribute name
    MODEL_FILES: List[Set[str]] = [SAFE, GGUF, PICK]  # Corrected attribute name

    # Filenames/patterns to ignore during directory scanning
    IGNORE: List[str] = [
        "Thumbs.db",
        "desktop.ini",
        ".DS_Store",
        ".fseventsd",
        "._*",
        "~$*",  # Common system/temp files
        "~$*.tmp",
        "*.tmp",  # More temp files
    ]


class NodeNames:
    """Constants related to ComfyUI node names and data parsing."""

    ENCODERS = {
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
    STRING_INPUT = {
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
    PROMPT_LABELS = ["Positive prompt", "Negative prompt", "Prompt"]
    IGNORE_KEYS = [
        "type",
        "link",
        "shape",
        "id",
        "pos",
        "size",
        "node_id",
        "empty_padding",
    ]
    DATA_KEYS = {"class_type": "inputs", "nodes": "widget_values"}
    PROMPT_NODE_FIELDS = {
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


# Determine if extended exception info should be logged based on LOG_LEVEL from package __init__
EXC_INFO: bool = LOG_LEVEL.strip().upper() in ["DEBUG", "TRACE", "NOTSET", "ALL"]


def bracket_check(maybe_brackets: str | dict) -> str | dict:
    """Ensures a string is bracket-enclosed if it's not a dict, for later parsing."""
    if isinstance(maybe_brackets, dict):
        return maybe_brackets
    elif isinstance(maybe_brackets, str):
        corrected_str = maybe_brackets.strip()
        if not corrected_str.startswith("{"):
            corrected_str = "{" + corrected_str
        if not corrected_str.endswith("}"):
            corrected_str = corrected_str + "}"
        return corrected_str
    else:
        raise TypeError("Input for bracket_check must be a string or a dictionary.")


# TypedDicts for ComfyUI workflow structures
class NodeDataMap(TypedDict):
    class_type: str
    inputs: Union[dict, float, str, list, None]  # Inputs can be varied


class NodeWorkflow(TypedDict):
    last_node_id: int
    last_link_id: Union[int, dict, None]
    nodes: List[NodeDataMap]  # Assuming nodes are lists of NodeDataMap-like structures
    links: list
    groups: list
    config: dict
    extra: dict
    version: float


# Pydantic Models
class BracketedDict(BaseModel):  # Currently unused, but kept for potential future use
    """Placeholder for a Pydantic model that might use bracket_check."""

    pass


class IsThisNode:  # Container for TypeAdapters
    """TypeAdapters for validating parts of ComfyUI JSON data."""

    data = TypeAdapter(NodeDataMap)
    workflow = TypeAdapter(NodeWorkflow)


class ListOfDelineatedStr(BaseModel):  # Specific Pydantic model
    convert: list

    @field_validator("convert")
    @classmethod
    def drop_tuple(cls, v: list) -> list:  # Changed 'regex_match' to 'v' for clarity
        if v and isinstance(v, list) and v[0] and isinstance(v[0], tuple):
            # This logic seems to want to take the first element of the first tuple in the list
            # and make that the new list. This is very specific.
            first_tuple_first_element = next(iter(v[0]), None)
            return [first_tuple_first_element] if first_tuple_first_element is not None else []
        return v
