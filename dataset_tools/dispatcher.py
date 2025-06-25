# dataset_tools/dispatcher.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Dispatch a parsed data object.

to the correct tool-specific parser class.

This acts as a central registry for all supported metadata formats.
"""

from typing import Any

from .logger import info_monitor as nfo
from .model_parsers import safetensors_parser as safetensors  # Assuming this has SafetensorsParser class
from .model_parsers.gguf_parser import GGUFParser
from .vendored_sdpr.format.a1111 import A1111
from .vendored_sdpr.format.base_format import BaseFormat
from .vendored_sdpr.format.civitai import CivitaiFormat
from .vendored_sdpr.format.comfyui import ComfyUI
from .vendored_sdpr.format.drawthings import DrawThings
from .vendored_sdpr.format.easydiffusion import EasyDiffusion
from .vendored_sdpr.format.fooocus import Fooocus
from .vendored_sdpr.format.forge_format import ForgeFormat
from .vendored_sdpr.format.invokeai import InvokeAI
from .vendored_sdpr.format.midjourney import MidjourneyFormat  # Actual class name
from .vendored_sdpr.format.mochi_diffusion import MochiDiffusionFormat
from .vendored_sdpr.format.novelai import NovelAI
from .vendored_sdpr.format.ruinedfooocus import RuinedFooocusFormat
from .vendored_sdpr.format.swarmui import SwarmUI
from .vendored_sdpr.format.tensorart import TensorArtFormat  # Actual class name
from .vendored_sdpr.format.yodayo import YodayoFormat

# Define the type alias for the reader instance for clarity
ImageReaderInstance = Any  # This is okay, it's the result from ImageDataReader in metadata_parser.py

# --- The Central Dispatcher Map ---
# This dictionary maps the tool name string (identified by the initial parse or refinement)
# to the full, specialized parser class that knows how to handle it.
TOOL_CLASS_MAP: dict[str, type[BaseFormat]] = {
    "A1111 webUI": A1111,
    "ComfyUI": ComfyUI,
    "Civitai": CivitaiFormat,  # CivitaiFormat might set its tool to "Civitai ComfyUI" or "Civitai A1111"
    "Civitai ComfyUI": CivitaiFormat,  # Add specific entry if CivitaiFormat sets this tool name
    "Civitai A1111": CivitaiFormat,  # Add specific entry if CivitaiFormat sets this tool name
    "Forge": ForgeFormat,
    "Yodayo": YodayoFormat,  # If YodayoFormat's tool name is just "Yodayo"
    "Yodayo/Moescape": YodayoFormat,  # If YodayoFormat's tool name is "Yodayo/Moescape"
    "TensorArt": TensorArtFormat,  # Tool name set by TensorArtFormat class
    "Midjourney": MidjourneyFormat,  # Tool name set by MidjourneyFormat class
    "Fooocus": Fooocus,
    "RuinedFooocus": RuinedFooocusFormat,
    "StableSwarmUI": SwarmUI,  # Note: SwarmUI.tool might be "SwarmUI" or "StableSwarmUI"
    "Draw Things": DrawThings,
    "NovelAI": NovelAI,
    "InvokeAI": InvokeAI,
    "Easy Diffusion": EasyDiffusion,
    "Mochi Diffusion": MochiDiffusionFormat,
    "Safetensors": safetensors.SafetensorsParser,  # Ensure this is a BaseFormat subclass or compatible
    "Gguf": GGUFParser,  # Ensure this is a BaseFormat subclass or compatible
    # --- Add your new entries ---
    # Add any other tool names that ImageDataReader or your metadata_parser.py refinement might set
}


def dispatch_to_specific_parser(reader_instance: ImageReaderInstance) -> dict[str, Any]:
    """Take a successful reader_instance, identifies the tool, and uses the
    correct full parser class to extract clean,
    tool-specific generation parameters.

    Args:
        reader_instance: The initial, generic reader instance after a successful read.

    Returns:
        A dictionary of cleaned, tool-specific generation parameters.
        Returns the raw parameter dictionary as a fallback if no specific parser is found.

    """
    tool_name = getattr(reader_instance, "tool", "Unknown")

    ParserClass = TOOL_CLASS_MAP.get(tool_name)

    if not ParserClass:
        nfo(
            f"No specific parser class found in TOOL_CLASS_MAP for tool '{tool_name}'. Returning raw parameters as fallback."
        )
        return getattr(reader_instance, "parameter", {})

    nfo(f"Dispatching to specialized parser via TOOL_CLASS_MAP: {ParserClass.__name__} for tool '{tool_name}'")

    try:
        # Ensure all necessary data from reader_instance is passed.
        # The __init__ of these ParserClasses should be BaseFormat compatible.
        specific_parser = ParserClass(
            info=getattr(reader_instance, "info", {}),
            raw=getattr(reader_instance, "raw", ""),
            width=getattr(reader_instance, "width", 0),  # Ensure these are correctly typed for BaseFormat
            height=getattr(reader_instance, "height", 0),  # Ensure these are correctly typed for BaseFormat
            logger_obj=getattr(reader_instance, "_logger", None),  # Pass the logger if available
            # Pass the LSB extractor if it exists (for NovelAI from ImageDataReader)
            extractor=getattr(reader_instance, "extractor", None),
        )

        # The parser's own .parse() method (which calls _process) does the work.
        # This assumes these classes are designed to potentially re-parse or refine.
        status = specific_parser.parse()

        # It's good practice to check the status after parsing
        if status == BaseFormat.Status.READ_SUCCESS:
            nfo(f"Successfully re-parsed/refined with {ParserClass.__name__}.")
            return specific_parser.parameter
        error_msg = getattr(specific_parser, "error", "Unknown error during re-parse/refinement")
        status_name = status.name if hasattr(status, "name") else str(status)
        nfo(
            f"Re-parse/refinement with {ParserClass.__name__} did not succeed. Status: {status_name}. Error: {error_msg}. Returning original parameters."
        )
        return getattr(reader_instance, "parameter", {})  # Fallback to original reader's params

    except Exception as e:
        nfo(
            f"Error during instantiation or parsing with {ParserClass.__name__} via TOOL_CLASS_MAP: {e}",
            exc_info=True,
        )
        return getattr(reader_instance, "parameter", {})
