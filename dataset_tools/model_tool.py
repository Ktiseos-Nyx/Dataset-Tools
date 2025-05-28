# Dataset-Tools/model_tool.py
# Refactored to use specific parser classes

from pathlib import Path
from .logger import info_monitor as nfo
from .correct_types import EmptyField # For default error return

# Import your new model parsers
from .model_parsers import (
    SafetensorsParser,
    # PickletensorParser, # Add when implemented
    # GgufParser,         # Add when implemented
    ModelParserStatus
)

class ModelTool:
    def __init__(self):
        # Map extensions to parser classes
        self.parser_map = {
            ".safetensors": SafetensorsParser,
            ".sft": SafetensorsParser,
            # ".gguf": GgufParser,
            # ".pt": PickletensorParser,
            # ".pth": PickletensorParser,
            # ".ckpt": PickletensorParser,
        }

    def read_metadata_from(self, file_path_named: str) -> dict:
        nfo(f"[ModelTool] Attempting to read metadata from: {file_path_named}")
        extension = Path(file_path_named).suffix.lower()
      
        ParserClass = self.parser_map.get(extension)

        if ParserClass:
            parser_instance = ParserClass(file_path_named)
            status = parser_instance.parse()

            if status == ModelParserStatus.SUCCESS:
                return parser_instance.get_ui_data()
            elif status == ModelParserStatus.FAILURE:
                # Parser recognized the type but failed to parse
                return {
                    EmptyField.PLACEHOLDER.value: {
                        "Error": f"{parser_instance.tool_name} parsing failed: {parser_instance._error_message or 'Unknown error'}",
                        "File": file_path_named
                    }
                }
            else: # NOT_APPLICABLE or UNATTEMPTED (shouldn't be UNATTEMPTED after parse call)
                nfo(f"[ModelTool] Parser {ParserClass.__name__} not applicable for {file_path_named}")
                # Fall through to unsupported extension
        
        nfo(f"[ModelTool] Unsupported file extension or no suitable parser found: {extension}")
        return {
            EmptyField.PLACEHOLDER.value: {
                "Error": f"Unsupported model file extension: {extension}",
                "File": file_path_named
            }
        }

# Example Usage (for testing, not part of the class)
# if __name__ == '__main__':
#     mt = ModelTool()
#     test_file = "path/to/your/test.safetensors"
#     if Path(test_file).exists():
#         data = mt.read_metadata_from(test_file)
#         import pprint
#         pprint.pprint(data)
#     else:
#         print(f"Test file not found: {test_file}")