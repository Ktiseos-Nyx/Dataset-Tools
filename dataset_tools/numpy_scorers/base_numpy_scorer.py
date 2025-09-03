"""Base Numpy Scorer
================

Core shared utilities and scoring logic for all numpy-based parsers.
Provides fundamental confidence scoring, template detection, and caching.
"""

import hashlib
import time
from collections import defaultdict
from typing import Any

from ..logger import get_logger

logger = get_logger(__name__)

# Global caches for performance optimization
WORKFLOW_CACHE = {}  # Hash workflow structure → analyzed results
NODE_TYPE_CACHE = {}  # Node signatures → classified types
RUNTIME_ANALYTICS = {
    "method_success_count": defaultdict(int),
    "method_failure_count": defaultdict(int),
    "workflow_types_processed": defaultdict(int),
    "total_processing_time": 0,
    "cache_hits": 0,
    "cache_misses": 0
}

# Core confidence scoring system
CONFIDENCE_INDICATORS = {
    "exact_node_match": 0.9,        # Found in known good node types
    "template_detected": 0.1,        # Looks like placeholder text
    "length_appropriate": 0.7,       # Reasonable prompt length
    "multiple_sources_agree": 0.8,   # Both systems find same content
    "domain_knowledge_match": 0.85,  # Format-specific node priority
    "structural_complexity": 0.6,    # Complex prompt structure
    "semantic_indicators": 0.75      # Strong positive/negative indicators
}


class BaseNumpyScorer:
    """Base class for all numpy-based scoring systems."""

    def __init__(self):
        """Initialize the base numpy scorer."""
        self.logger = get_logger(f"{__name__}.BaseNumpyScorer")
        self.start_time = None

    def _get_workflow_hash(self, workflow_data: dict[str, Any]) -> str:
        """Generate a hash for workflow data for caching."""
        try:
            # Create a stable hash of the workflow structure
            workflow_str = str(sorted(workflow_data.items()))
            return hashlib.md5(workflow_str.encode()).hexdigest()
        except Exception as e:
            self.logger.warning(f"Could not hash workflow data: {e}")
            return str(time.time())  # Fallback to timestamp

    def _is_template_text(self, text: str) -> bool:
        """Check if text appears to be template/placeholder content."""
        if not text or not isinstance(text, str):
            return True

        text_lower = text.lower().strip()

        # Empty or whitespace only
        if not text_lower:
            return True

        # Common template indicators
        template_indicators = [
            "your prompt here",
            "enter prompt",
            "type prompt",
            "prompt goes here",
            "sample prompt",
            "example prompt",
            "default prompt",
            "placeholder",
            "template",
            "lorem ipsum",
            "test prompt",
            "debug",
            "<prompt>",
            "[prompt]",
            "{prompt}",
            "{{prompt}}",
        ]

        for indicator in template_indicators:
            if indicator in text_lower:
                return True

        # Very short prompts are often templates
        if len(text.strip()) < 3:
            return True

        # Repetitive patterns
        words = text_lower.split()
        if len(words) > 1 and len(set(words)) == 1:  # All words identical
            return True

        return False

    def _calculate_base_confidence(self, candidate: dict[str, Any]) -> float:
        """Calculate base confidence score for a candidate."""
        confidence = 0.5  # Start neutral

        # Prefer 'text' or 'prompt' as the main prompt field
        text = candidate.get("text") or candidate.get("prompt") or ""
        negative_prompt = candidate.get("negative_prompt", "")

        # If only negative prompt is present, penalize confidence
        if not text.strip() and negative_prompt.strip():
            return 0.1  # Very low confidence

        # Template detection (negative indicator)
        if self._is_template_text(text):
            confidence += CONFIDENCE_INDICATORS["template_detected"]
        else:
            confidence += 0.3  # Not a template is good

        # Length appropriateness
        text_len = len(text.strip()) if text else 0
        if 10 <= text_len <= 500:  # Reasonable prompt length
            confidence += CONFIDENCE_INDICATORS["length_appropriate"]
        elif text_len > 500:
            confidence += 0.4  # Long prompts are often real
        elif text_len > 0:
            confidence += 0.2  # At least has content

        # Structural complexity indicators
        if text and isinstance(text, str):
            # Has punctuation (commas, periods)
            if "," in text or "." in text:
                confidence += 0.1
            # Has descriptive words
            descriptive_words = ["detailed", "beautiful", "artistic", "masterpiece", "high quality"]
            if any(word in text.lower() for word in descriptive_words):
                confidence += 0.15
            # Has style indicators
            style_indicators = ["style", "art", "painting", "photo", "render"]
            if any(word in text.lower() for word in style_indicators):
                confidence += 0.1

        return min(1.0, max(0.0, confidence))  # Clamp to 0-1

    def _calculate_negative_confidence(self, candidate: dict[str, Any]) -> float:
        """Calculate confidence score for a negative prompt."""
        negative_prompt = candidate.get("negative_prompt", "")
        if not negative_prompt.strip():
            return 0.1  # No negative prompt, low confidence

        # Use similar logic as positive, but on negative_prompt
        confidence = 0.5
        if self._is_template_text(negative_prompt):
            confidence += CONFIDENCE_INDICATORS["template_detected"]
        else:
            confidence += 0.3
        text_len = len(negative_prompt.strip())
        if 10 <= text_len <= 500:
            confidence += CONFIDENCE_INDICATORS["length_appropriate"]
        elif text_len > 500:
            confidence += 0.4
        elif text_len > 0:
            confidence += 0.2
        # Add more negative-specific logic if needed
        return min(1.0, max(0.0, confidence))

    def _track_analytics(self, method: str, success: bool, processing_time: float, format_type: str):
        """Track analytics for performance monitoring."""
        if success:
            RUNTIME_ANALYTICS["method_success_count"][method] += 1
        else:
            RUNTIME_ANALYTICS["method_failure_count"][method] += 1

        RUNTIME_ANALYTICS["workflow_types_processed"][format_type] += 1
        RUNTIME_ANALYTICS["total_processing_time"] += processing_time

    def score_candidate(self, candidate: dict[str, Any], format_type: str = "unknown", prompt_type: str = "positive") -> dict[str, Any]:
        """Score a text candidate. prompt_type: 'positive' or 'negative'."""
        start_time = time.time()

        try:
            # Calculate confidence based on prompt type
            if prompt_type == "negative":
                base_confidence = self._calculate_negative_confidence(candidate)
                scoring_method = "base_numpy_negative"
            else:
                base_confidence = self._calculate_base_confidence(candidate)
                scoring_method = "base_numpy"

            # Create scored candidate
            scored_candidate = candidate.copy()
            scored_candidate["confidence"] = base_confidence
            scored_candidate["scoring_method"] = scoring_method
            scored_candidate["format_type"] = format_type

            processing_time = time.time() - start_time
            self._track_analytics("score_candidate", True, processing_time, format_type)

            return scored_candidate

        except Exception as e:
            self.logger.error(f"Error scoring candidate: {e}")
            processing_time = time.time() - start_time
            self._track_analytics("score_candidate", False, processing_time, format_type)

            # Return low-confidence result
            return {
                **candidate,
                "confidence": 0.1,
                "scoring_method": "base_numpy_error",
                "error": str(e)
            }


def get_runtime_analytics() -> dict[str, Any]:
    """Get current runtime analytics."""
    return dict(RUNTIME_ANALYTICS)


def clear_cache():
    """Clear all caches."""
    global WORKFLOW_CACHE, NODE_TYPE_CACHE
    WORKFLOW_CACHE.clear()
    NODE_TYPE_CACHE.clear()
    logger.info("All numpy scorer caches cleared")


def get_cache_info() -> dict[str, Any]:
    """Get information about current cache state."""
    return {
        "workflow_cache_size": len(WORKFLOW_CACHE),
        "node_type_cache_size": len(NODE_TYPE_CACHE),
        "cache_hits": RUNTIME_ANALYTICS["cache_hits"],
        "cache_misses": RUNTIME_ANALYTICS["cache_misses"]
    }
