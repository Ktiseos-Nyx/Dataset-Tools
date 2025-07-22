# dataset_tools/metadata_engine/extractors/__init__.py

"""Extraction modules for different metadata formats.

This package contains specialized extractors for different AI image formats:
- DirectValueExtractor: Basic value extraction
- A1111Extractor: AUTOMATIC1111 WebUI format
- CivitaiExtractor: Civitai platform formats
- ComfyUIExtractor: ComfyUI workflow format
- JSONExtractor: JSON processing utilities
- RegexExtractor: Regular expression text extraction
"""

from .a1111_extractors import A1111Extractor
from .civitai_extractors import CivitaiExtractor
from .comfyui_extractors import ComfyUIExtractor
from .comfyui_quadmoons import ComfyUIQuadMoonsExtractor
from .direct_extractors import DirectValueExtractor
from .json_extractors import JSONExtractor
from .regex_extractors import RegexExtractor

__all__ = [
    "A1111Extractor",
    "CivitaiExtractor",
    "ComfyUIExtractor",
    "ComfyUIQuadMoonsExtractor",
    "DirectValueExtractor",
    "JSONExtractor",
    "RegexExtractor",
]
