import re
from typing import TypedDict, Any
from typing_extensions import Annotated
from pydantic import TypeAdapter, BaseModel, Field, AfterValidator, field_serializer


from pydantic_core import ValidationError

def bracket_check(maybe_brackets:str | dict):
    """
    \n
    :param maybe_brackets: The data that may or may not have brackets
    :type maybe_brackets: `str`
    :param :
    :return:
    """
    if not isinstance(maybe_brackets, dict):
        if next(iter(maybe_brackets)) != "{":
            maybe_brackets = "{" + maybe_brackets
        if maybe_brackets[-1:] != "}":
            maybe_brackets += "}"
    return maybe_brackets

class NodeDataMap(TypedDict):
    class_type: str
    inputs: dict[str,Any]
    outputs: list[Any]

class BracketedDict(BaseModel):

    """
    Ensure a string value is formatted correctly for a dictionary\n
    :param node_data: k/v pairs with or without brackets
    :type node_data: `str`, required
    """
    brackets: Annotated[str, Field(init=False), AfterValidator(bracket_check)]

#class ValidityCheck: #TypeAdapter was removed
    """
    Confirm the data input of a ComfyUI dict\n
    :param node_data: The data to verify
    :type node_data: `str | dict`
    """
    #node_data = TypeAdapter(NodeDataMap) # TypeAdapter was removed
