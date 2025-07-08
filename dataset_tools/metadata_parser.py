# Dataset-Tools/metadata_parser.py
"""This module serves as the primary interface for parsing metadata from files.

It utilizes the new modular metadata engine to identify and extract data,
then formats it into a standardized dictionary for UI consumption.
"""

import traceback
from pathlib import Path
from typing import Any

from .correct_types import DownField, UpField
from .logger import info_monitor as nfo
from .metadata_engine.engine import create_metadata_engine
from .metadata_engine.parser_registry import register_parser_class
from .vendored_sdpr.format.a1111 import A1111
from .vendored_sdpr.format.civitai import CivitaiFormat
from .vendored_sdpr.format.comfyui import ComfyUI

# Import vendored parser classes for registration
from .vendored_sdpr.format.drawthings import DrawThings
from .vendored_sdpr.format.easydiffusion import EasyDiffusion
from .vendored_sdpr.format.fooocus import Fooocus
from .vendored_sdpr.format.invokeai import InvokeAI
from .vendored_sdpr.format.novelai import NovelAI
from .vendored_sdpr.format.swarmui import SwarmUI

# --- Constants ---
PARSER_DEFINITIONS_PATH = str(Path(__file__).parent / "parser_definitions")


# Register vendored parser classes
def _register_vendored_parsers():
    """Register all vendored parser classes for use with base_format_class."""
    register_parser_class("DrawThings", DrawThings)
    register_parser_class("NovelAI", NovelAI)
    register_parser_class("A1111", A1111)
    register_parser_class("ComfyUI", ComfyUI)
    register_parser_class("CivitaiFormat", CivitaiFormat)
    register_parser_class("EasyDiffusion", EasyDiffusion)
    register_parser_class("Fooocus", Fooocus)
    register_parser_class("InvokeAI", InvokeAI)
    register_parser_class("SwarmUI", SwarmUI)


# Register parsers on module import
_register_vendored_parsers()


def parse_metadata(file_path_named: str) -> dict[str, Any]:
    """Parses metadata from a given file using the modular metadata engine.

    This function initializes the metadata engine, processes the file,
    and then transforms the extracted data into the format expected by the UI.

    Args:
        file_path_named: The absolute path to the file to be parsed.

    Returns:
        A dictionary containing the parsed metadata, formatted for the UI.

    """
    nfo(f"[DT.metadata_parser]: >>> ENTERING parse_metadata for: {file_path_named}")
    final_ui_dict: dict[str, Any] = {}

    try:
        # Create the metadata engine
        engine = create_metadata_engine(PARSER_DEFINITIONS_PATH)

        # Process the file
        result = engine.get_parser_for_file(file_path_named)

        if result and isinstance(result, dict) and result:
            # Transform the engine result to UI format
            _transform_engine_result_to_ui_dict(result, final_ui_dict)
            potential_ai_parsed = True
            nfo(f"[DT.metadata_parser]: Successfully parsed metadata with engine. Keys: {list(result.keys())}")
        else:
            nfo("[DT.metadata_parser]: Engine found no matching parser or returned invalid data.")
            potential_ai_parsed = False

    except Exception as e:
        nfo(f"[DT.metadata_parser]: ❌ MetadataEngine failed: {e}")
        traceback.print_exc()
        final_ui_dict["error"] = {
            "Error": f"Metadata Engine failed: {e}",
        }
        potential_ai_parsed = False

    # 4. (Optional) Future placeholder for adding non-AI metadata (like EXIF)
    # if not potential_ai_parsed:
    #     nfo("[DT.metadata_parser]: No AI metadata found, could add standard EXIF/XMP here.")
    #     pass

    if not final_ui_dict:
        final_ui_dict["info"] = {
            "Info": "No processable metadata found.",
        }
        nfo(f"Failed to find/load any metadata for file: {file_path_named}")

    nfo(f"[DT.metadata_parser]: <<< EXITING parse_metadata. Returning keys: {list(final_ui_dict.keys())}")
    return final_ui_dict


def _transform_engine_result_to_ui_dict(result: dict[str, Any], ui_dict: dict[str, Any]) -> None:
    """Transforms the raw result from the metadata engine into the structured UI dictionary."""
    # --- Main Prompts ---
    prompt_data = {
        "Positive": result.get("prompt", ""),
        "Negative": result.get("negative_prompt", ""),
    }
    if result.get("is_sdxl", False):
        prompt_data["Positive SDXL"] = result.get("positive_sdxl", {})
        prompt_data["Negative SDXL"] = result.get("negative_sdxl", {})
    ui_dict[UpField.PROMPT.value] = prompt_data

    # --- Generation Parameters ---
    parameters = result.get("parameters", {})
    if isinstance(parameters, dict):
        ui_dict[DownField.GENERATION_DATA.value] = parameters

    # --- Raw Data ---
    ui_dict[DownField.RAW_DATA.value] = result.get("raw_metadata", str(result))

    # --- Detected Tool ---
    tool_name = result.get("tool", "Unknown")
    if tool_name != "Unknown":
        if UpField.METADATA.value not in ui_dict:
            ui_dict[UpField.METADATA.value] = {}
        ui_dict[UpField.METADATA.value]["Detected Tool"] = tool_name

    # --- Add any other top-level fields from the result ---
    for key, value in result.items():
        if key not in [
            "prompt",
            "negative_prompt",
            "positive_sdxl",
            "negative_sdxl",
            "parameters",
            "raw_metadata",
            "tool",
            "is_sdxl",
        ]:
            if "unclassified" not in ui_dict:
                ui_dict["unclassified"] = {}
            ui_dict["unclassified"][key] = value
