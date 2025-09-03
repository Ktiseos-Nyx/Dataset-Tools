"""Coordinating Numpy Scorer
=========================

Lightweight coordinator that selects the appropriate numpy scorer based on metadata format.
This replaces the old monolithic numpy_scorer.py with a modular approach.
"""

from typing import Any

from .logger import get_logger
from .numpy_scorers import (
    A1111NumpyScorer,
    ComfyUINumpyScorer,
    DrawThingsNumpyScorer,
    clear_cache,
    get_cache_info,
    get_runtime_analytics,
    should_use_a1111_numpy_scoring,
    should_use_comfyui_numpy_scoring,
    should_use_drawthings_numpy_scoring,
)

# Advanced ComfyUI scoring is now integrated into metadata_engine/extractors/
# No separate advanced scorer needed since Griptape is handled by ComfyUIGriptapeExtractor

logger = get_logger(__name__)

# Global scorer instances (lazy-loaded)
_comfyui_scorer = None
_a1111_scorer = None
_drawthings_scorer = None


def _get_comfyui_scorer() -> ComfyUINumpyScorer:
    """Get or create the ComfyUI scorer instance."""
    global _comfyui_scorer
    if _comfyui_scorer is None:
        _comfyui_scorer = ComfyUINumpyScorer()
    return _comfyui_scorer


def _get_a1111_scorer() -> A1111NumpyScorer:
    """Get or create the A1111 scorer instance."""
    global _a1111_scorer
    if _a1111_scorer is None:
        _a1111_scorer = A1111NumpyScorer()
    return _a1111_scorer


def _get_drawthings_scorer() -> DrawThingsNumpyScorer:
    """Get or create the Draw Things scorer instance."""
    global _drawthings_scorer
    if _drawthings_scorer is None:
        _drawthings_scorer = DrawThingsNumpyScorer()
    return _drawthings_scorer


def should_use_numpy_scoring(engine_result: dict[str, Any]) -> bool:
    """Determine if ANY numpy scoring should be applied.
    
    This replaces the conditional check - now we ALWAYS use numpy scoring
    but select the appropriate scorer based on the format.
    """
    # Always return True to make numpy scoring mandatory for all parsers
    return True


def enhance_result(engine_result: dict[str, Any], original_file_path: str | None = None, status_callback=None) -> dict[str, Any]:
    """Enhance engine results with the appropriate numpy scorer.
    
    This is the main entry point that selects and applies the right scorer.
    """
    try:
        print(f"[DEBUG] numpy scorer called with engine_result keys: {list(engine_result.keys())}")
        print(f"[DEBUG] Tool: {engine_result.get('tool', 'NONE')}, Format: {engine_result.get('format', 'NONE')}")
        print(f"[DEBUG] Has raw_metadata: {'raw_metadata' in engine_result}")
        logger.info(f"numpy scorer called with engine_result keys: {list(engine_result.keys())}")
        logger.info(f"Tool: {engine_result.get('tool', 'NONE')}, Format: {engine_result.get('format', 'NONE')}")
        logger.info(f"Has raw_metadata: {'raw_metadata' in engine_result}")

        # Always apply numpy scoring, but choose the right scorer
        # Advanced ComfyUI functionality (like Griptape) is now handled by metadata_engine/extractors

        # Try standard ComfyUI scoring
        if should_use_comfyui_numpy_scoring(engine_result):
            logger.info("Using standard ComfyUI numpy scoring")
            scorer = _get_comfyui_scorer()
            return scorer.enhance_engine_result(engine_result, original_file_path)

        # Try Draw Things specific scoring
        if should_use_drawthings_numpy_scoring(engine_result):
            logger.info("Using Draw Things numpy scoring")
            scorer = _get_drawthings_scorer()
            return scorer.enhance_engine_result(engine_result, original_file_path)

        # Try A1111-specific scoring
        if should_use_a1111_numpy_scoring(engine_result):
            logger.info("Using A1111 numpy scoring")
            scorer = _get_a1111_scorer()
            return scorer.enhance_engine_result(engine_result, original_file_path)

        # Fallback to A1111 scorer for generic enhancement
        # (A1111 scorer is simpler and works well as a general-purpose scorer)
        logger.info("Using A1111 numpy scoring as fallback for generic format")
        scorer = _get_a1111_scorer()
        return scorer.enhance_engine_result(engine_result, original_file_path)

    except Exception as e:
        logger.error(f"Error in numpy scoring coordination: {e}")
        # Return original result if scoring fails
        return engine_result


# Legacy compatibility functions for the old interface
def get_numpy_analyzer():
    """Legacy compatibility - returns A1111 scorer as default."""
    return _get_a1111_scorer()


# Re-export utility functions
__all__ = [
    "clear_cache",
    "enhance_result",
    "get_cache_info",
    "get_numpy_analyzer",
    "get_runtime_analytics",
    "should_use_numpy_scoring"
]
