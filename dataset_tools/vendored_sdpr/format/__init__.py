# dataset_tools/vendored_sdpr/format/__init__.py

# Original SDPR exports (ensure these match the files you vendored)
from .base_format import BaseFormat
from .a1111 import A1111
from .easydiffusion import EasyDiffusion
from .invokeai import InvokeAI
from .novelai import NovelAI
from .comfyui import ComfyUI
from .drawthings import DrawThings
from .swarmui import SwarmUI
from .fooocus import Fooocus

# Your new parsers
from .civitai import CivitaiComfyUIFormat
from .ruinedfooocus import RuinedFooocusFormat # Add this line

__all__ = [
    "BaseFormat", "A1111", "EasyDiffusion", "InvokeAI", "NovelAI", 
    "ComfyUI", "DrawThings", "SwarmUI", "Fooocus",
    "CivitaiComfyUIFormat", "RuinedFooocusFormat", # Add to __all__
]