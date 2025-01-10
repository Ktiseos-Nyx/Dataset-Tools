from typing import Dict, Literal, LiteralString, TypedDict
from typing_extensions import Annotated
from pydantic import AfterValidator, BaseModel, TypeAdapter,ValidationError

class NodeDataMap(TypedDict):
    class_type: str = Literal["class_type"]
    inputs: str = Literal["inputs"]

test = TypeAdapter(NodeDataMap)

print(test.validate_python({'class_type':"class_type", 'inputs':"inputs"}))
