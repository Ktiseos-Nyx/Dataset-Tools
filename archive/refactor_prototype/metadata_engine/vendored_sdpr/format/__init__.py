# dataset_tools/vendored_sdpr/format/__init__.py

__author__ = "receyuki & Ktiseos Nyx"  # Acknowledge both
__filename__ = "__init__.py"
__copyright__ = "Copyright 2023, Receyuki; Modified 2025, Ktiseos Nyx"
__email__ = "receyuki@gmail.com; your_email@example.com"


from .a1111 import A1111

# Core and original SDPR exports
from .base_format import BaseFormat

# Your new/modified parsers
from .civitai import CivitaiFormat  # <<< CORRECTED: Using the combined CivitaiFormat
from .comfyui import ComfyUI  # Assuming you named the file comfyui.py for ComfyUI parser
from .drawthings import DrawThings
from .easydiffusion import EasyDiffusion
from .fooocus import Fooocus
from .invokeai import InvokeAI
from .mochi_diffusion import MochiDiffusionFormat  # <<< ADDED
from .novelai import NovelAI
from .ruinedfooocus import RuinedFooocusFormat
from .swarmui import SwarmUI

# from .yodayo import YodayoFormat  # <<< ADDED

# List all exported names for `from .format import *` if ever used,
# and for clarity of what this package provides, making them available for
# `from .format import ...` in image_data_reader.py
__all__ = [
    "BaseFormat",
    "A1111",
    "ComfyUI",
    "CivitaiFormat",  # <<< CORRECTED
    # "YodayoFormat",  # <<< ADDED
    "MochiDiffusionFormat",  # <<< ADDED
    "DrawThings",
    "EasyDiffusion",
    "Fooocus",
    "InvokeAI",
    "NovelAI",
    "RuinedFooocusFormat",
    "SwarmUI",
]
