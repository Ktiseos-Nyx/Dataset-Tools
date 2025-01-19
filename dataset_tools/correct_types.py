# // SPDX-License-Identifier: CC0-1.0
# // --<{ Ktiseos Nyx }>--

"""確認 Data Type"""

from ast import Constant

from platform import python_version_tuple

if float(python_version_tuple()[0]) == 3.0 and float(python_version_tuple()[1]) <= 12.0:
    from typing_extensions import TypedDict, Annotated, List, Union
else:
    from typing import TypedDict, Annotated, List, Union

from pydantic import TypeAdapter, BaseModel, Field, AfterValidator, field_validator, ValidationError

from dataset_tools import LOG_LEVEL


class UpField:
    """Upper display area for ui\n"""

    PROMPT: str = "Prompt Data"
    TAGS: str = "Tags"
    JSON_DATA: str = "JSON Data"
    TEXT_DATA: str = "TEXT Data"
    TOML_DATA: str = "TOML Data"
    EXIF: str = "EXIF"
    DATA: str = "DATA"
    PLACEHOLDER: str = "No Data"
    LABELS: list[Constant] = [PROMPT, TAGS, TEXT_DATA, TOML_DATA, JSON_DATA, DATA, PLACEHOLDER]


class DownField:
    """Lower display area for ui\n"""

    GENERATION_DATA: str = "Generation Data"
    SYSTEM: str = "System"
    ICC: str = "ICC Profile"
    EXIF: str = "EXIF"
    RAW_DATA: str = "TEXT DATA"
    PLACEHOLDER: str = "No Data"
    DATA: str = "DATA"
    LABELS: list[Constant] = [GENERATION_DATA, SYSTEM, ICC, EXIF, RAW_DATA, PLACEHOLDER]


class ExtensionType:
    """Valid file formats for metadata reading\n"""

    PNG_: List[str] = [".png"]
    JPEG: List[str] = [".jpg", ".jpeg"]
    WEBP: List[str] = [".webp"]
    JSON: List[str] = [".json"]
    TOML: List[str] = [".toml"]
    TEXT: List[str] = [".txt", ".text"]
    HTML: List[str] = [".html", ".htm"]
    XML_: List[str] = [".xml", ".xml"]

    IMAGE: List[Constant] = [JPEG, WEBP, PNG_]
    EXIF: List[Constant] = [JPEG, WEBP]
    SCHEMA: List[Constant] = [JSON, TOML]
    PLAIN: List[Constant] = [TEXT, XML_, HTML]

    IGNORE: List[Constant] = [
        "Thumbs.db",
        "desktop.ini",
        ".fseventsd",
        ".DS_Store",
    ]


class NodeNames:
    """Node names that carry prompts inside"""

    ENCODERS = [
        "CLIPTextEncodeFlux",
        "CLIPTextEncodeSD3",
        "CLIPTextEncodeSDXL",
        "CLIPTextEncodeHunyuanDiT",
        "CLIPTextEncodePixArtAlpha",
        "CLIPTextEncodeSDXLRefiner",
        "WildcardEncode //Inspire",
        "ImpactWildcardProcessor",
        "ImpactWildcardEncodeCLIPTextEncode",
        "CLIPTextEncode",
    ]
    PROMPT_LABELS = ["Positive prompt", "Negative prompt", "Prompt"]

    IGNORE_KEYS = [
        "type",
        "link",
        "shape",
        "id",
        "pos",
        "size",
    ]

    DATA_KEYS = {
        "class_type": "inputs",
        "nodes": "widget_values",
    }
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


EXC_INFO: bool = LOG_LEVEL != "i"


def bracket_check(maybe_brackets: str | dict):
    """
    Check and correct brackets in a kv pair format string\n
    :param maybe_brackets: The data that may or may not have brackets
    :type maybe_brackets: `str` | `dict`
    :return: the corrected string, or a dict
    """
    if isinstance(maybe_brackets, dict):
        pass
    elif isinstance(maybe_brackets, str):
        if next(iter(maybe_brackets)) != "{":
            maybe_brackets = "{" + maybe_brackets
        if maybe_brackets[-1:] != "}":
            maybe_brackets += "}"
    else:
        raise ValidationError("Check input must be str or dict")
    return maybe_brackets


class NodeDataMap(TypedDict):
    class_type: str
    inputs: Union[dict, float]


class NodeWorkflow(TypedDict):
    last_node_id: int
    last_link_id: Union[int, dict]
    nodes: list
    links: list
    groups: list
    config: dict
    extra: dict
    version: float


class BracketedDict(BaseModel):
    """
    Ensure a string value is formatted correctly for a dictionary\n
    :param node_data: k/v pairs with or without brackets
    :type node_data: `str`, required
    """

    brackets: Annotated[str, Field(init=False), AfterValidator(bracket_check)]


class IsThisNode:
    """
    Confirm the data input of a ComfyUI dict\n
    :param node_data: The data to verify
    :type node_data: `str | dict`
    """

    data = TypeAdapter(NodeDataMap)
    workflow = TypeAdapter(NodeWorkflow)


class ListOfDelineatedStr(BaseModel):
    convert: list

    @field_validator("convert")
    @classmethod
    def drop_tuple(cls, regex_match: list):
        regex_match = list(next(iter(regex_match), None))
        return regex_match
