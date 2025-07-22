# Dataset-Tools/model_tool.py
# Refactored to use specific parser classes

from pathlib import Path

from .correct_types import EmptyField
from .logger import info_monitor as nfo
from .model_parsers import GGUFParser, ModelParserStatus, SafetensorsParser


class ModelTool:
    def __init__(self) -> None:
        self.parser_map = {
            ".safetensors": SafetensorsParser,
            ".sft": SafetensorsParser,
            ".gguf": GGUFParser,
        }

    def read_metadata_from(self, file_path_named: str) -> dict:
        nfo("[ModelTool] Attempting to read metadata from: %s", file_path_named)  # % logging
        file_path_obj = Path(file_path_named)  # Create Path object once
        extension = file_path_obj.suffix.lower()
        file_name_for_log = file_path_obj.name  # Use for logging messages

        ParserClass = self.parser_map.get(extension)  # noqa: N806

        if ParserClass:
            nfo(
                "[ModelTool] Using parser: %s for extension: %s",
                ParserClass.__name__,
                extension,
            )  # % logging
            parser_instance = ParserClass(file_path_named)
            status = parser_instance.parse()

            if status == ModelParserStatus.SUCCESS:
                nfo(
                    "[ModelTool] Successfully parsed with %s.",
                    parser_instance.tool_name,
                )  # % logging
                return parser_instance.get_ui_data()

            if status == ModelParserStatus.FAILURE:
                error_msg = parser_instance._error_message or "Unknown parsing error"
                nfo(
                    "[ModelTool] Parser %s failed: %s",
                    parser_instance.tool_name,
                    error_msg,
                )  # % logging
                return {
                    EmptyField.PLACEHOLDER.value: {
                        "Error": f"{parser_instance.tool_name} parsing failed: {error_msg}",
                        "File": file_name_for_log,
                    },
                }

            if status == ModelParserStatus.NOT_APPLICABLE:
                nfo(  # % logging
                    "[ModelTool] Parser %s found file not applicable: %s",
                    ParserClass.__name__,
                    file_name_for_log,
                )
                # Fall through: handled by the final "Unsupported" block
            else:  # UNATTEMPTED or other unexpected status
                status_display_name = status.name if hasattr(status, "name") else str(status)
                # Corrected E501 on original line 62 and using % logging:
                nfo(
                    ("[ModelTool] Parser %s returned unexpected status '%s' for %s"),
                    ParserClass.__name__,
                    status_display_name,
                    file_name_for_log,
                )
                # Fall through

        # If no parser, or parser returned NOT_APPLICABLE or an unexpected status not handled above
        nfo(  # % logging
            (
                "[ModelTool] Unsupported model file extension '%s' or no suitable "
                "parser successfully processed the file: %s"
            ),
            extension,
            file_name_for_log,
        )
        return {
            EmptyField.PLACEHOLDER.value: {
                "Error": f"Unsupported model file extension: {extension}",
                "File": file_name_for_log,
            },
        }
