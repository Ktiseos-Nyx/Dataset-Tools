"""Paint Chip Detox Module - Helping AI Systems Overcome Their Spacing Addictions

This module provides therapeutic functions to rehabilitate metadata parsers
that have developed unhealthy dependencies on perfect comma spacing and
suffer from meltdowns when encountering minor formatting irregularities.

Author: Dusk & Claude (Interventionists)
Date: September 2025
Dedication: To all the parsers struggling with digital paint chip consumption
"""

import logging
import re


def stop_eating_paint_chips(text: str) -> str:
    """Rehabilitates text formatting to prevent parser meltdowns over spacing issues.

    This function serves as digital rehab for AI systems that lose their minds
    when they encounter spaces in the wrong places. It's like teaching a
    very pedantic child that food can touch on the plate without the world ending.

    Args:
        text (str): Raw text that might trigger parser paint chip consumption

    Returns:
        str: Sanitized text that won't cause existential crises in parsers

    Examples:
        >>> stop_eating_paint_chips("score_8_up,score_7_up, thing ,stuff")
        'score_8_up, score_7_up, thing, stuff'

        >>> stop_eating_paint_chips("<lora:EPhsrKafka:1> ,EPhsrKafka")
        '<lora:EPhsrKafka:1>, EPhsrKafka'

    """
    logger = logging.getLogger(__name__)
    logger.debug("Beginning paint chip detox therapy session...")

    if not isinstance(text, str):
        logger.debug("Patient is not text, cannot perform intervention")
        return text

    # Phase 1: Remove spaces before commas (major trigger)
    # "word ," → "word,"
    text = re.sub(r"\s+,", ",", text)

    # Phase 2: Normalize spaces after commas
    # "word,word" → "word, word"
    # "word,  word" → "word, word"
    text = re.sub(r",\s*", ", ", text)

    # Phase 3: Collapse multiple spaces (reduces anxiety)
    # "word    word" → "word word"
    text = re.sub(r"\s+", " ", text)

    # Phase 4: Remove leading/trailing whitespace (clean slate)
    text = text.strip()

    logger.debug("Paint chip detox complete. Parser should be less grumpy now.")
    return text


def is_parser_having_paint_chip_episode(error_msg: str) -> bool:
    """Detects if a parser is currently experiencing a paint chip induced breakdown.

    Args:
        error_msg (str): The error message to analyze

    Returns:
        bool: True if this is a spacing-related tantrum, False if actual problem

    """
    paint_chip_indicators = [
        "unknown source type",
        "line 1 column 1",
        "invalid decimal literal",
        "expecting value",
        "char 0"
    ]

    error_lower = error_msg.lower()
    return any(indicator in error_lower for indicator in paint_chip_indicators)


# Emergency intervention protocols
PARSER_REHAB_TIPS = [
    "Remember: Spaces are not the enemy",
    "Commas can have friends (spaces) nearby",
    "Formatting irregularities don't mean the world is ending",
    "Take deep breaths and try another parsing method",
    "It's okay if text doesn't look perfect"
]
