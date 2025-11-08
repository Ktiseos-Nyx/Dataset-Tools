"""Coordinating Numpy Scorer
=========================

Lightweight coordinator that selects the appropriate numpy scorer
based on metadata format. This replaces the old monolithic
numpy_scorer.py with a modular approach.
"""

import re
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

logger = get_logger(__name__)

# 🔴 KILL SWITCH: Set to True to disable numpy scoring temporarily
NUMPY_DISABLED = False

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

def _slice_griptape_prompt(text: str) -> str:
    """
    Slices the prompt from a Griptape agent's output.
    It looks for common keywords like 'PROMPT:', 'Prompt:', etc.,
    or JSON-like structures and extracts the text that follows.
    """
    if not isinstance(text, str):
        return ""

    # Pattern to find 'PROMPT:', 'Positive Prompt:', etc., and capture everything after it
    # This is case-insensitive and handles optional surrounding quotes or newlines.
    patterns = [
        re.compile(r'(?:positive prompt|prompt)\s*:\s*"?\s*(.*)', re.IGNORECASE | re.DOTALL),
        re.compile(r'```json\s*\n\s*{\s*"(?:positive_prompt|prompt)"\s*:\s*"(.*?)"', re.IGNORECASE | re.DOTALL),
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if match:
            # Extract the captured group, strip leading/trailing whitespace/quotes
            prompt = match.group(1).strip().strip('"').strip()
            # If the prompt ends with a code block or json closing, remove it
            prompt = re.sub(r'"\s*}\s*```$', '', prompt, flags=re.DOTALL).strip()
            logger.debug(f"[NUMPY-GRIPTAPE] Sliced prompt: '{prompt[:100]}...'")
            return prompt

    logger.debug("[NUMPY-GRIPTAPE] No slice pattern matched. Returning original text.")
    return text.strip()


def enhance_result(
    engine_result: dict[str, Any],
    original_file_path: str | None = None,
) -> dict[str, Any]:
    """
    Enhance engine results with the appropriate numpy scorer.
    This is the main entry point that selects and applies the right scorer.
    """
    if NUMPY_DISABLED:
        logger.info("[NUMPY] ⚠️ NUMPY SCORING DISABLED - returning parser result unchanged")
        return engine_result

    try:
        logger.debug("[NUMPY] =" * 40)
        logger.debug("[NUMPY] ENHANCE_RESULT: Tool: '%s'", engine_result.get("tool", "NONE"))

        # ===================================================================
        # NEW: Griptape Special Handling (The "SLICE" feature)
        # Check if the result came from our Griptape parser before anything else.
        # ===================================================================
        if engine_result.get("parser_name_from_engine") == "ComfyUI Griptape":
            logger.debug("[NUMPY] ✅ Detected Griptape result. Applying prompt slicing.")

            if "prompt" in engine_result and engine_result["prompt"]:
                engine_result["prompt"] = _slice_griptape_prompt(engine_result["prompt"])

            # After slicing, we can still apply the standard ComfyUI scoring
            logger.debug("[NUMPY] Proceeding with standard ComfyUI numpy scoring for Griptape result.")
            scorer = _get_comfyui_scorer()
            return scorer.enhance_engine_result(engine_result, original_file_path)

        # Try standard ComfyUI scoring
        logger.debug("[NUMPY] Checking for standard ComfyUI workflow...")
        if should_use_comfyui_numpy_scoring(engine_result):
            logger.debug("[NUMPY] ✅ Using standard ComfyUI numpy scoring")
            scorer = _get_comfyui_scorer()
            return scorer.enhance_engine_result(engine_result, original_file_path)

        # Try Draw Things specific scoring
        if should_use_drawthings_numpy_scoring(engine_result):
            logger.debug("[NUMPY] ✅ Using Draw Things numpy scoring")
            scorer = _get_drawthings_scorer()
            return scorer.enhance_engine_result(engine_result, original_file_path)

        logger.debug("[NUMPY] ❌ No specific scorer matched - returning original result")
        return engine_result

    except Exception as e:
        logger.error("[NUMPY] Error in numpy scoring coordination: %s", e, exc_info=True)
        # Return original result if scoring fails
        return engine_result

# Re-export utility functions
__all__ = [
    "clear_cache",
    "enhance_result",
    "get_cache_info",
    "get_runtime_analytics",
]
