"""Modular Numpy Scoring System
===========================

This package provides specialized numpy-based scoring for different metadata formats.
Each scorer is optimized for specific formats while sharing common base functionality.
"""

from .a1111_numpy_scorer import A1111NumpyScorer, should_use_a1111_numpy_scoring
from .base_numpy_scorer import BaseNumpyScorer, clear_cache, get_cache_info, get_runtime_analytics
from .comfyui_numpy_scorer import ComfyUINumpyScorer, should_use_comfyui_numpy_scoring
from .drawthings_numpy_scorer import DrawThingsNumpyScorer, should_use_drawthings_numpy_scoring

__all__ = [
    "A1111NumpyScorer",
    "BaseNumpyScorer",
    "ComfyUINumpyScorer",
    "DrawThingsNumpyScorer",
    "clear_cache",
    "get_cache_info",
    "get_runtime_analytics",
    "should_use_a1111_numpy_scoring",
    "should_use_comfyui_numpy_scoring",
    "should_use_drawthings_numpy_scoring"
]
