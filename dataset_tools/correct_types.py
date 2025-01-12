# // SPDX-License-Identifier: CC0-1.0
# // --<{ Ktiseos Nyx }>--

from typing import TypedDict, Annotated

from dataset_tools import LOG_LEVEL

# from pydantic_core import ValidationError
from pydantic import TypeAdapter, BaseModel, Field, AfterValidator, field_validator, ValidationError


class UpField:
    """Upper display area for ui\n"""

    PROMPT: str = "Prompt Data"
    TAGS: str = "Tags"
    LABELS: list[str] = [PROMPT, TAGS]


class DownField:
    """Lower display area for ui\n"""

    GENERATION_DATA: str = "Generation Data"
    SYSTEM: str = "System"
    ICC: str = "ICC Profile"
    EXIF: str = "EXIF"
    LABELS: list[str] = [GENERATION_DATA, SYSTEM, ICC, EXIF]


class Ext:
    """Valid file formats for metadata reading"""

    PNG_ = [".png"]
    JPEG = [".jpg", ".jpeg"]
    WEBP = [".webp"]
    TEXT = [".txt"]


EXC_INFO: bool = LOG_LEVEL != "i"


class NodeNames:
    ENCODERS = ["CLIPTextEncodeFlux", "CLIPTextEncodeSD3", "CLIPTextEncodeSDXL", "CLIPTextEncodeHunyuanDiT", "WildcardEncode //Inspire", "CLIPTextEncode"]


def bracket_check(maybe_brackets: str | dict):
    """
    Check and correct brackets in a kv pair format string\n
    :param maybe_brackets: The data that may or may not have brackets
    :type maybe_brackets: `str` | `dict`
    :return: the corrrected string, or a dict
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
        # logger.debug("regex_match: %s:: ", f"{type(regex_match)} {regex_match}")
        regex_match = list(next(iter(regex_match), None))
        return regex_match
