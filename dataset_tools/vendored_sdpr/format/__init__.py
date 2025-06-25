# dataset_tools/vendored_sdpr/format/__init__.py

__author__ = "receyuki & Ktiseos Nyx"  # Acknowledge both
__filename__ = "__init__.py"
__copyright__ = "Copyright 2023, Receyuki; Modified 2025, Ktiseos Nyx"
__email__ = "receyuki@gmail.com; your_email@example.com"
# MODIFIED by Ktiseos Nyx for Dataset-Tools: Consolidated format imports and exports.
# Import all necessary format classes from their respective modules

from .a1111 import A1111
from .base_format import BaseFormat
from .civitai import CivitaiFormat
from .comfyui import ComfyUI
from .drawthings import DrawThings
from .easydiffusion import EasyDiffusion
from .fooocus import Fooocus
from .forge_format import ForgeFormat  # Assuming you have this
from .invokeai import InvokeAI
from .mochi_diffusion import MochiDiffusionFormat  # Assuming this is the class name
from .novelai import NovelAI
from .ruinedfooocus import RuinedFooocusFormat  # Assuming this is the class name
from .swarmui import SwarmUI
from .tensorart import TensorArtFormat  # <<< ADD THIS
from .yodayo import YodayoFormat  # <<< MAKE SURE YodayoFormat IS EXPORTED

# Add any other format classes you've created in separate files

try:
    from ...metadata_engine import register_parser_class

    REGISTRATION_POSSIBLE = True
except ImportError:
    print(
        "WARNING: metadata_engine.register_parser_class not found for format registration. This might be okay during linting."
    )

    # Solution for W0613: Prefix unused arguments with an underscore
    def register_parser_class(_name: str, _cls: type):  # Dummy function
        pass

    REGISTRATION_POSSIBLE = False


# --- Register all classes if registration is possible ---
if REGISTRATION_POSSIBLE:
    # Use the actual class name as the string key for clarity,
    # or a specific "tool name" if that's what your engine expects to look up.
    # Using class name string is often safer if the class's `tool` attribute might change.
    register_parser_class("BaseFormat", BaseFormat)  # If BaseFormat itself might be used
    register_parser_class("A1111", A1111)
    register_parser_class("ComfyUI", ComfyUI)
    register_parser_class("CivitaiFormat", CivitaiFormat)
    register_parser_class("DrawThings", DrawThings)
    register_parser_class("EasyDiffusion", EasyDiffusion)
    register_parser_class("Fooocus", Fooocus)
    register_parser_class("ForgeFormat", ForgeFormat)
    register_parser_class("InvokeAI", InvokeAI)
    register_parser_class("MochiDiffusionFormat", MochiDiffusionFormat)
    register_parser_class("NovelAI", NovelAI)
    register_parser_class("RuinedFooocusFormat", RuinedFooocusFormat)
    register_parser_class("SwarmUI", SwarmUI)
    register_parser_class("YodayoFormat", YodayoFormat)
    register_parser_class("TensorArtFormat", TensorArtFormat)
    # ... register all others ...
    print("INFO [format.__init__]: Registered parser classes with MetadataEngine.")


# Optional: Define __all__ to specify what `from .format import *` would import
__all__ = [
    "A1111",
    "BaseFormat",
    "CivitaiFormat",
    "ComfyUI",
    "DrawThings",
    "EasyDiffusion",
    "Fooocus",
    "ForgeFormat",
    "InvokeAI",
    "MochiDiffusionFormat",
    "NovelAI",
    "RuinedFooocusFormat",
    "SwarmUI",
    "TensorArtFormat",
    "YodayoFormat",
]
