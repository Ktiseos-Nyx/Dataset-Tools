# dataset_tools/dispatcher.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Dispatch a parsed data object.

to the correct tool-specific parser class.

This acts as a central registry for all supported metadata formats.
"""

from typing import Any, Type  # noqa: UP035

from .logger import info_monitor as nfo
from .model_parsers import safetensors_parser as safetensors
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
from .vendored_sdpr.format.mochi_diffusion import MochiDiffusionFormat
from .vendored_sdpr.format.novelai import NovelAI
from .vendored_sdpr.format.ruinedfooocus import RuinedFooocusFormat
from .vendored_sdpr.format.swarmui import SwarmUI
from .vendored_sdpr.format.yodayo import YodayoFormat

# Define the type alias for the reader instance for clarity
ImageReaderInstance = Any  # Or your more specific type from metadata_parser

# --- The Central Dispatcher Map ---
# This dictionary maps the tool name string (identified by the initial parse)
# to the full, specialized parser class that knows how to handle it.
TOOL_CLASS_MAP: dict[str, Type[BaseFormat]] = {  # noqa: UP006
    "A1111 webUI": A1111,
    "NovelAI": NovelAI,
    "InvokeAI": InvokeAI,
    "Easy Diffusion": EasyDiffusion,
    "Fooocus": Fooocus,
    "RuinedFooocus": RuinedFooocusFormat,
    "StableSwarmUI": SwarmUI,
    "Draw Things": DrawThings,
    "Forge": ForgeFormat,
    "Mochi Diffusion": MochiDiffusionFormat,
    "Civitai": CivitaiFormat,
    "Yodayo": YodayoFormat,
    "Safetensors": safetensors.SafetensorsParser,
    "Gguf": GGUFParser,
    "ComfyUI": ComfyUI,
    # Add other tool names and their corresponding classes here as you support them.
    # e.g., "Civitai": Civitai,
}


def dispatch_to_specific_parser(reader_instance: ImageReaderInstance) -> dict[str, Any]:
    """Take a successful reader_instance, identifies the tool, and uses the.

    correct full parser
    class to extract clean,
    tool-specific generation parameters.

    Args:
        reader_instance: The initial, generic reader instance after a successful read.

    Returns:
        A dictionary of cleaned, tool-specific generation parameters.
        Returns the raw parameter dictionary as a fallback if no specific parser is found.

    """
    tool_name = getattr(reader_instance, "tool", "Unknown")

    # Find the correct specialized parser class from our map
    ParserClass = TOOL_CLASS_MAP.get(tool_name)  # noqa: N806

    if not ParserClass:
        nfo(f"No specific parser class found for tool '{tool_name}'. Returning raw parameters as fallback.")
        # Fallback for unknown tools: just return the raw parameter dict
        return getattr(reader_instance, "parameter", {})

    nfo(f"Dispatching to specialized parser: {ParserClass.__name__}")

    # Instantiate the *specific* parser class
    # with the data from the initial read.
    # The individual parser's __init__
    # and _process methods will handle the rest.
    try:
        specific_parser = ParserClass(
            info=getattr(reader_instance, "info", {}),
            raw=getattr(reader_instance, "raw", ""),
            width=getattr(reader_instance, "width", 0),
            height=getattr(reader_instance, "height", 0),
            # Pass the LSB extractor if it exists, for NovelAI
            extractor=getattr(reader_instance, "extractor", None),
        )

        # The parser's own .parse() method does all the hard work.
        # This will call the tool-specific _process() method internally.
        specific_parser.parse()

        # We return the clean, processed .parameter dictionary from the specific parser.
        # This dictionary should only contain relevant, non-empty fields.
        return specific_parser.parameter

    except Exception as e:  # noqa: BLE001
        nfo(
            f"Error during specialized parsing with {ParserClass.__name__}: {e}",
            exc_info=True,
        )
        # If the specialized parser fails for any reason, return the raw data as a fallback
        # to ensure the user still sees something.
        return getattr(reader_instance, "parameter", {})
