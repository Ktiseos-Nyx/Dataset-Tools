# // SPDX-License-Identifier: CC0-1.0
# // --<{ Ktiseos Nyx }>--

"""確認 Data Type"""

from ast import Constant
from typing_extensions import TypedDict, Annotated, List

from dataset_tools import LOG_LEVEL

from pydantic import TypeAdapter, BaseModel, Field, AfterValidator, field_validator, ValidationError


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
        "WildcardEncode //Inspire",
        "ImpactWildcardProcessor",
        "CLIPTextEncode",
    ]
    IGNORE_KEYS = [
        "type",
        "link",
        "shape",
        "id",
        "pos",
        "size",
    ]


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
    inputs: dict


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


class ListOfDelineatedStr(BaseModel):
    convert: list

    @field_validator("convert")
    @classmethod
    def drop_tuple(cls, regex_match: list):
        regex_match = list(next(iter(regex_match), None))
        return regex_match
