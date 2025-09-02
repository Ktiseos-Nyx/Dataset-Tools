"""Negative Indicators Loader

Loads and manages the negative indicators JSON dictionary for ComfyUI numpy scoring.
Allows for easy maintenance and updates of negative prompt detection rules.
"""

import json
import re
from pathlib import Path

from ..logger import get_logger

logger = get_logger(__name__)


class NegativeIndicatorsManager:
    """Manages loading and using negative indicators from JSON config."""

    def __init__(self, config_path: str | None = None):
        """Initialize the negative indicators manager."""
        if config_path is None:
            config_path = Path(__file__).parent / "negative_indicators.json"

        self.config_path = Path(config_path)
        self.config = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load the negative indicators configuration."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                self.config = json.load(f)
            logger.info(f"Loaded negative indicators config v{self.config.get('version', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to load negative indicators config: {e}")
            # Fallback to minimal hardcoded config
            self.config = {
                "categories": {"basic": {"indicators": ["bad quality", "watermark", "nsfw"]}},
                "detection_rules": {"minimum_matches_for_negative": 2, "strong_negative_single_match": ["watermark"]}
            }

    def get_all_indicators(self) -> list[str]:
        """Get all negative indicators from all categories."""
        indicators = []
        categories = self.config.get("categories", {})

        for category_name, category_data in categories.items():
            if category_name == "embedding_negatives":
                continue  # Handle patterns separately

            category_indicators = category_data.get("indicators", [])
            indicators.extend(category_indicators)

        return indicators

    def get_embedding_patterns(self) -> list[str]:
        """Get regex patterns for detecting negative embeddings."""
        embedding_category = self.config.get("categories", {}).get("embedding_negatives", {})
        return embedding_category.get("patterns", [])

    def get_strong_negatives(self) -> list[str]:
        """Get indicators that are strong negatives (single match = negative)."""
        rules = self.config.get("detection_rules", {})
        return rules.get("strong_negative_single_match", [])

    def get_minimum_matches(self) -> int:
        """Get minimum number of matches needed for negative classification."""
        rules = self.config.get("detection_rules", {})
        return rules.get("minimum_matches_for_negative", 2)

    def is_negative_text(self, text: str) -> bool:
        """Determine if text should be classified as negative."""
        text_lower = text.lower()

        # Check for positive context overrides first
        rules = self.config.get("detection_rules", {})
        positive_overrides = rules.get("positive_context_overrides", [])
        for override in positive_overrides:
            if override.lower() in text_lower:
                logger.debug(f"Positive context override detected: '{override}' - skipping negative classification")
                return False

        # Check for embedding negatives using patterns
        embedding_patterns = self.get_embedding_patterns()
        if "embedding:" in text_lower:
            for pattern in embedding_patterns:
                if re.search(pattern, text_lower):
                    logger.debug(f"Detected negative embedding pattern: {pattern}")
                    return True

        # Check for strong single negatives
        strong_negatives = self.get_strong_negatives()
        for strong_neg in strong_negatives:
            # Use word boundaries for strong negatives too
            strong_pattern = r"\b" + re.escape(strong_neg.lower()) + r"\b"
            if re.search(strong_pattern, text_lower):
                logger.debug(f"Detected strong negative: {strong_neg} in text: '{text[:60]}...'")
                return True

        # Get all indicators and artistic descriptors
        all_indicators = self.get_all_indicators()
        artistic_descriptors = self._get_artistic_descriptors()

        # Count non-artistic indicators
        non_artistic_matches = []
        artistic_matches = []

        for indicator in all_indicators:
            # Use word boundaries to avoid partial matches (e.g., "bad" shouldn't match "badge")
            indicator_pattern = r"\b" + re.escape(indicator.lower()) + r"\b"
            if re.search(indicator_pattern, text_lower):
                if indicator.lower() in [ad.lower() for ad in artistic_descriptors]:
                    artistic_matches.append(indicator)
                else:
                    non_artistic_matches.append(indicator)
                logger.debug(f"Matched indicator: '{indicator}' in text: '{text[:60]}...')")

        # Apply smarter context-aware logic
        rules = self.config.get("detection_rules", {})
        min_matches = rules.get("minimum_matches_for_negative", 2)
        artistic_context_boost = rules.get("artistic_context_boost_threshold", 2)

        # If we have many non-artistic negative indicators, it's probably negative
        if len(non_artistic_matches) >= min_matches:
            logger.debug(f"Detected negative with {len(non_artistic_matches)} non-artistic matches")
            return True

        # If we have artistic terms but also other negative context, it might be negative
        total_matches = len(non_artistic_matches) + len(artistic_matches)
        if total_matches >= min_matches and len(artistic_matches) >= artistic_context_boost:
            # Look for additional negative context clues
            negative_context_words = ["bad", "ugly", "worst", "terrible", "awful"]
            context_matches = sum(1 for word in negative_context_words if word in text_lower)

            if context_matches >= 1:
                logger.debug("Detected negative with artistic terms but negative context")
                return True

        # Additional check for very short embedding-only content
        short_threshold = rules.get("short_text_threshold", 50)

        if (len(text.strip()) < short_threshold and
            "neg" in text_lower and
            ("embedding" in text_lower or len(text.split()) < 5)):
            logger.debug(f"Detected short negative content: {text[:30]}...")
            return True

        return False

    def _get_artistic_descriptors(self) -> list[str]:
        """Get artistic descriptors that require context for negative classification."""
        rules = self.config.get("detection_rules", {})
        return rules.get("artistic_descriptors_require_context", [])


# Global instance for easy importing
negative_indicators = NegativeIndicatorsManager()
