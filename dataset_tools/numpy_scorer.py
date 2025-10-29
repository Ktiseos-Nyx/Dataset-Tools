"""Coordinating Numpy Scorer
=========================

Lightweight coordinator that selects the appropriate numpy scorer
based on metadata format. This replaces the old monolithic
numpy_scorer.py with a modular approach.
"""

from typing import Any

from .logger import get_logger
from .numpy_scorers import (
    ComfyUINumpyScorer,
    DrawThingsNumpyScorer,
    clear_cache,
    get_cache_info,
    get_runtime_analytics,
    should_use_comfyui_numpy_scoring,
    should_use_drawthings_numpy_scoring,
)

# Advanced ComfyUI scoring is now integrated into metadata_engine/extractors/
# No separate advanced scorer needed since Griptape is handled by
# ComfyUIGriptapeExtractor

logger = get_logger(__name__)

# Global scorer instances (lazy-loaded)
_comfyui_scorer = None
_drawthings_scorer = None



def _get_comfyui_scorer() -> ComfyUINumpyScorer:
    """Get or create the ComfyUI scorer instance."""
    global _comfyui_scorer
    if _comfyui_scorer is None:
        _comfyui_scorer = ComfyUINumpyScorer()
    return _comfyui_scorer


def _get_drawthings_scorer() -> DrawThingsNumpyScorer:
    """Get or create the Draw Things scorer instance."""
    global _drawthings_scorer
    if _drawthings_scorer is None:
        _drawthings_scorer = DrawThingsNumpyScorer()
    return _drawthings_scorer


def should_use_numpy_scoring(_engine_result: dict[str, Any]) -> bool:
    """Determine if ANY numpy scoring should be applied.

    This replaces the conditional check - now we ALWAYS use numpy scoring
    but select the appropriate scorer based on the format.
    """
    # Always return True to make numpy scoring mandatory for all parsers
    return True


def enhance_result(
    engine_result: dict[str, Any],
    original_file_path: str | None = None,
    #    status_callback=None
) -> dict[str, Any]:
    """Enhance engine results with the appropriate numpy scorer.

    This is the main entry point that selects and applies the right scorer.
    """
    try:
        # TEMP DEBUG: Use info_monitor to ensure logs appear
        from .logger import info_monitor as nfo
        logger.debug("[NUMPY] =" * 40)
        logger.debug("[NUMPY] NUMPY SCORER ENHANCE_RESULT CALLED")
        logger.debug("[NUMPY] Engine result keys: %s", list(engine_result.keys()))
        logger.debug("[NUMPY] Tool: '%s', Format: '%s'",
                     engine_result.get("tool", "NONE"),
                     engine_result.get("format", "NONE"))
        logger.debug("[NUMPY] Has raw_metadata: %s (type: %s)",
                     "raw_metadata" in engine_result,
                     type(engine_result.get("raw_metadata", None)))
        logger.debug("[NUMPY] Prompt: '%s...'", engine_result.get("prompt", "NONE")[:80])
        logger.debug("[NUMPY] Negative: '%s...'", engine_result.get("negative_prompt", "NONE")[:80])
        logger.debug("[NUMPY] =" * 40)

        # Always apply numpy scoring, but choose the right scorer
        # Advanced ComfyUI functionality (like Griptape) is now handled by
        # metadata_engine/extractors

        # Try standard ComfyUI scoring
        logger.debug("[NUMPY] Checking if should use ComfyUI numpy scoring...")
        should_use_comfy = should_use_comfyui_numpy_scoring(engine_result)
        logger.debug("[NUMPY] should_use_comfyui_numpy_scoring returned: %s", should_use_comfy)
        if should_use_comfy:
            logger.debug("[NUMPY] ✅ Using standard ComfyUI numpy scoring")
            scorer = _get_comfyui_scorer()
            return scorer.enhance_engine_result(
                engine_result, original_file_path)
        else:
            logger.debug("[NUMPY] ❌ NOT using ComfyUI numpy scoring - check failed")

        # Try Draw Things specific scoring
        if should_use_drawthings_numpy_scoring(engine_result):
            logger.debug("[NUMPY] Using Draw Things numpy scoring")
            scorer = _get_drawthings_scorer()
            return scorer.enhance_engine_result(
                engine_result, original_file_path)

        logger.debug("[NUMPY] No specific scorer matched - returning original result")

    except Exception as e:
        logger.debug("[NUMPY] Error in numpy scoring coordination: %s", e)
        # Return original result if scoring fails
        return engine_result

    # If no specific scorer was matched, return the original result
    logger.debug("[NUMPY] Returning original engine_result unchanged")
    return engine_result


# Re-export utility functions
__all__ = [
    "clear_cache",
    "enhance_result",
    "get_cache_info",
    "get_runtime_analytics",
    "should_use_numpy_scoring"
]
