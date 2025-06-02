# dataset_tools/vendored_sdpr/format/__init__.py

# Original SDPR exports (ensure these match the files you vendored)
from .a1111 import A1111
from .base_format import BaseFormat

# Your new parsers
from .civitai import CivitaiComfyUIFormat
from .comfyui import ComfyUI
from .drawthings import DrawThings
from .easydiffusion import EasyDiffusion
from .fooocus import Fooocus
from .invokeai import InvokeAI
from .novelai import NovelAI
from .ruinedfooocus import RuinedFooocusFormat  # Add this line
from .swarmui import SwarmUI

__all__ = [
    "A1111",
    "BaseFormat",
    "CivitaiComfyUIFormat",
    "ComfyUI",
    "DrawThings",
    "EasyDiffusion",
    "Fooocus",
    "InvokeAI",
    "NovelAI",
    "RuinedFooocusFormat",  # Add to __all__
    "SwarmUI",
]
