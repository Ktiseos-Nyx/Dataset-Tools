# Dataset-Tools/model_tool.py
# Refactored to use specific parser classes

from pathlib import Path
from .logger import info_monitor as nfo
from .correct_types import EmptyField  # For default error return

# Import your new model parsers
from .model_parsers import (
    SafetensorsParser,
    # PickletensorParser,  # Remains commented out as requested
    GGUFParser,  # Corrected Casing and Uncommented
    ModelParserStatus,
)


class ModelTool:
    def __init__(self):
        # Map extensions to parser classes
        self.parser_map = {
            ".safetensors": SafetensorsParser,
            ".sft": SafetensorsParser,
            ".gguf": GGUFParser,  # Uncommented and correctly cased
            # ".pt": PickletensorParser,
            # ".pth": PickletensorParser,
            # ".ckpt": PickletensorParser,
        }

    def read_metadata_from(self, file_path_named: str) -> dict:
        nfo(f"[ModelTool] Attempting to read metadata from: {file_path_named}")
        extension = Path(file_path_named).suffix.lower()

        ParserClass = self.parser_map.get(extension)

        if ParserClass:
            nfo(f"[ModelTool] Using parser: {ParserClass.__name__} for extension: {extension}")
            parser_instance = ParserClass(file_path_named)
            status = parser_instance.parse()  # This calls BaseModelParser.parse()

            if status == ModelParserStatus.SUCCESS:
                nfo(f"[ModelTool] Successfully parsed with {parser_instance.tool_name}.")
                return parser_instance.get_ui_data()
            elif status == ModelParserStatus.FAILURE:
                error_msg = parser_instance._error_message or "Unknown parsing error"
                nfo(f"[ModelTool] Parser {parser_instance.tool_name} failed: {error_msg}")
                return {
                    EmptyField.PLACEHOLDER.value: {
                        "Error": f"{parser_instance.tool_name} parsing failed: {error_msg}",
                        "File": Path(file_path_named).name,  # Show only filename for brevity in UI
                    }
                }
            elif status == ModelParserStatus.NOT_APPLICABLE:
                nfo(
                    f"[ModelTool] Parser {ParserClass.__name__} found file not applicable: {Path(file_path_named).name}"
                )
                # This case will fall through to the "Unsupported extension" if no other parser handles it.
                # This is correct behavior.
            else:  # UNATTEMPTED or other unexpected status
                nfo(
                    f"[ModelTool] Parser {ParserClass.__name__} returned unexpected status '{status.name if hasattr(status, 'name') else status}' for {Path(file_path_named).name}"
                )
                # Fall through to unsupported extension message

        # If no parser was found for the extension, or if the found parser returned NOT_APPLICABLE
        nfo(
            f"[ModelTool] Unsupported model file extension '{extension}' or no suitable parser successfully processed the file: {Path(file_path_named).name}"
        )
        return {
            EmptyField.PLACEHOLDER.value: {
                "Error": f"Unsupported model file extension: {extension}",
                "File": Path(file_path_named).name,
            }
        }


# Example Usage (for testing, not part of the class)
# if __name__ == '__main__':
#     # Ensure correct_types.py and logger.py can be imported if running this standalone
#     # This might require adjusting sys.path or running from the project root with python -m ...
#     # For direct test, you might need to mock nfo and EmptyField or provide simple versions.
#
#     # Simple mock for nfo if logger isn't fully set up for standalone run
#     def nfo_mock(msg): print(f"INFO: {msg}")
#     global nfo # Make sure nfo is defined, or pass it, or mock it.
#     nfo = nfo_mock
#
#     # Simple mock for EmptyField if correct_types isn't fully set up for standalone run
#     class MockEmptyField: class PLACEHOLDER: value = "_placeholder_"
#     global EmptyField
#     EmptyField = MockEmptyField
#
#     # Mock model_parsers for standalone testing if they are not easily importable
#     class MockModelParserStatus: SUCCESS="SUCCESS_STATUS"; FAILURE="FAILURE_STATUS"; NOT_APPLICABLE="NOT_APP_STATUS"
#     class MockBaseParser:
#         def __init__(self, fp): self.file_path = fp; self.tool_name = "MockedParser"; self._error_message = "mock error"
#         def parse(self): print(f"MockParse called for {self.file_path}"); return MockModelParserStatus.NOT_APPLICABLE # or SUCCESS
#         def get_ui_data(self): return {"mock_data": "some data from " + self.file_path}
#
#     global SafetensorsParser, GGUFParser, ModelParserStatus # Make sure they are defined
#     SafetensorsParser = MockBaseParser
#     GGUFParser = MockBaseParser
#     ModelParserStatus = MockModelParserStatus
#
#     mt = ModelTool()
#     # Create dummy files for testing
#     Path("test.safetensors").write_text("dummy")
#     Path("test.gguf").write_text("dummy")
#     Path("test.unknown").write_text("dummy")
#
#     import pprint
#     print("\n--- Testing .safetensors ---")
#     pprint.pprint(mt.read_metadata_from("test.safetensors"))
#     print("\n--- Testing .gguf ---")
#     pprint.pprint(mt.read_metadata_from("test.gguf"))
#     print("\n--- Testing .unknown ---")
#     pprint.pprint(mt.read_metadata_from("test.unknown"))
#
#     # Clean up dummy files
#     Path("test.safetensors").unlink(missing_ok=True)
#     Path("test.gguf").unlink(missing_ok=True)
#     Path("test.unknown").unlink(missing_ok=True)
