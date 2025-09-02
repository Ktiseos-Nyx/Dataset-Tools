# dataset_tools/metadata_engine/extractors/__init__.py

"""Extraction modules for different metadata formats.

This package contains specialized extractors for different AI image formats:
- DirectValueExtractor: Basic value extraction
- A1111Extractor: AUTOMATIC1111 WebUI format
- CivitaiExtractor: Civitai platform formats
- ComfyUIExtractor: ComfyUI workflow format
- DrawThingsExtractor: Draw Things app XMP metadata
- InvokeAIExtractor: InvokeAI metadata formats
- JSONExtractor: JSON processing utilities
- ModelExtractor: AI model files (SafeTensors, GGUF)
- RegexExtractor: Regular expression text extraction
"""

from .a1111_extractors import A1111Extractor
from .civitai_extractors import CivitaiExtractor
from .comfyui_enhanced_extractor import ComfyUIEnhancedExtractor
from .comfyui_extractors import ComfyUIExtractor
from .comfyui_griptape import ComfyUIGriptapeExtractor
from .comfyui_quadmoons import ComfyUIQuadMoonsExtractor
from .direct_extractors import DirectValueExtractor
from .drawthings_extractors import DrawThingsExtractor
from .invokeai_extractors import InvokeAIExtractor
from .json_extractors import JSONExtractor
from .model_extractors import ModelExtractor
from .regex_extractors import RegexExtractor

__all__ = [
    "A1111Extractor",
    "CivitaiExtractor",
    "ComfyUIEnhancedExtractor",
    "ComfyUIExtractor",
    "ComfyUIGriptapeExtractor",
    "ComfyUIQuadMoonsExtractor",
    "DirectValueExtractor",
    "DrawThingsExtractor",
    "InvokeAIExtractor",
    "JSONExtractor",
    "ModelExtractor",
    "RegexExtractor",
]
