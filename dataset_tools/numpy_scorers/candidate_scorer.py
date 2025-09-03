"""Candidate Scoring Module
========================

Handles scoring and ranking of text candidates extracted from ComfyUI workflows.
Includes specialized scoring for different workflow types and node ecosystems.
"""

import re  # noqa: F401
from typing import Any

# Advanced ComfyUI Node type scoring with domain knowledge
ADVANCED_NODE_TYPE_SCORES = {
    # Dynamic content generators (highest priority)
    "DPRandomGenerator": 4.5,  # Dynamic Prompts with graph traversal
    "ImpactWildcardProcessor": 3.0,
    "WildcardProcessor": 2.8,
    "Wildcard Processor": 2.8,  # Mikey nodes version with space
    "RandomPrompt": 2.5,
    "Wildcard": 2.5,
    "WildCardProcessor": 2.5,

    # HiDream ecosystem nodes (high priority)
    "easy positive": 2.3,  # HiDream positive prompt node
    "Text Concatenate (JPS)": 2.0,  # JPS text concatenation
    "Prompt Multiple Styles Selector": 1.9,  # Style selector

    # Advanced prompt nodes
    "ChatGptPrompt": 2.2,
    "PixArtT5TextEncode": 1.8,
    "T5TextEncode": 1.6,
    "BNK_CLIPTextEncodeAdvanced": 1.4,
    "CLIP Text Encode (Positive Prompt)": 1.3,  # Flux/Aurum positive prompt nodes

    # Standard nodes (lower priority in advanced mode)
    "CLIPTextEncode": 1.0,
    "CLIPTextEncodeSD3": 1.1,  # SD3 text encoding
    "SD3TextEncode": 1.1,  # Alternative SD3 text encoding
    "ConditioningCombine": 1.0,
    "ConditioningConcat": 1.0,

    # Display/intermediate nodes (for tracing)
    "ShowText|pysssss": 0.8,
    "ConcatStringSingle": 0.6,
    "StringConstant": 0.4,
}


class CandidateScorer:
    """Scores and ranks text candidates from ComfyUI workflows."""

    def __init__(self):
        # Keywords for prompt type identification
        self.positive_keywords = [
            "masterpiece", "high quality", "detailed", "beautiful", "best quality",
            "intricate", "photorealistic", "cinematic", "portrait", "landscape",
            "anime", "realistic", "stunning", "gorgeous", "amazing", "professional",
            "artstation", "8k", "4k", "ultra detailed", "sharp focus", "vivid colors"
        ]

        self.negative_keywords = [
            "worst quality", "low quality", "bad", "blurry", "ugly", "deformed",
            "nsfw", "bad anatomy", "missing", "distorted", "jpeg artifacts",
            "watermark", "signature", "logo", "cropped", "out of frame",
            "text overlay", "boring", "amateur", "pixelated", "overexposed",
            "mutation", "mutated", "extra limb", "extra hands", "poorly drawn", "lowres"
            r"embedding:negatives\IllusGen_Neg",
        ]

        self.technical_terms = [
            "lanczos", "bilinear", "ddim", "euler", "dpmpp", "cfg", "randomize",
            "steps", "sampler", "scheduler", "denoise", "seed", "checkpoint",
            "lora", "embedding", "hypernetwork", "vae", "controlnet"
        ]

    def score_text_candidate(self, candidate: dict[str, Any], workflow_type: str = "standard") -> dict[str, Any]:
        """Enhanced scoring system with workflow-specific logic and domain knowledge."""
        text = candidate.get("text", "").strip()
        node_type = candidate.get("source_node_type", "")
        is_connected = candidate.get("is_connected", False)

        if not text:
            return {"score": 0, "reasons": ["NO_TEXT"], "confidence_modifier": 0}

        # Base scoring
        score = 5.0  # Base score
        reasons = []
        confidence_modifier = 0

        # Node type bonus from lookup table
        node_bonus = ADVANCED_NODE_TYPE_SCORES.get(node_type, 0)
        if node_bonus > 0:
            score += node_bonus
            reasons.append(f"NODE_TYPE_BONUS_{node_type.upper().replace(' ', '_')}")

        # Length-based scoring (with caps to prevent runaway scores)
        text_length = len(text)
        if text_length > 200:
            length_bonus = min(3.0, text_length / 100)  # Cap at +3
            score += length_bonus
            reasons.append("SUBSTANTIAL_LENGTH")
        elif text_length > 50:
            score += 1.5
            reasons.append("GOOD_LENGTH")
        elif text_length < 10:
            score -= 1
            reasons.append("SHORT_TEXT")

        # Connection bonus - connected nodes are more reliable
        if is_connected:
            score += 1.5
            reasons.append("CONNECTED_NODE")
        else:
            reasons.append("primary widget (no connections)")
            if candidate.get("node_type") in ["CLIPTextEncode", "CLIPTextEncodeSDXL", "T5TextEncode", "PixArtT5TextEncode", "CLIP Text Encode (Positive Prompt)", "CLIPTextEncodeSD3", "SD3TextEncode"]:
                score += 3 # Add a significant boost for direct input on a main encoder
                reasons.append("MAIN_ENCODER_WIDGET")

        # Workflow-specific boosts
        if workflow_type == "randomizer":
            # Extra boost for randomizer workflows with high-value nodes
            if node_bonus >= 2.0 and workflow_type == "randomizer":
                extra_boost = 2 if is_connected else 1
                score += extra_boost

        # Contextual boost for Text Multiline in Griptape workflows
        if node_type == "Text Multiline" and workflow_type == "griptape" and len(text) > 50:
            # In Griptape workflows, Text Multiline often contains the REAL user prompt
            # while CLIPTextEncode might have junk/templates/NSFW content
            # Increased boost to +8 to beat CLIPTextEncode base+boosts (~6.0)
            score += 8
            reasons.append("SUBSTANTIAL TEXT MULTILINE IN GRIPTAPE")
            confidence_modifier += 1
            print(f"Griptape Text Multiline boost: '{text[:40]}...' -> score +8")

        # Enhanced ShowText|pysssss scoring - prioritize more detailed content
        if node_type == "ShowText|pysssss" and len(text) > 100:
            base_showtext_boost = 6

            # Additional boost based on content length (more detailed = higher priority)
            if len(text) > 300:
                base_showtext_boost += 3  # Very detailed content gets +9 total
                reasons.append("VERY_DETAILED_SHOWTEXT")
            elif len(text) > 200:
                base_showtext_boost += 2  # Detailed content gets +8 total
                reasons.append("DETAILED_SHOWTEXT")
            else:
                reasons.append("SUBSTANTIAL_SHOWTEXT_CONTENT")

            # Content quality scoring for ShowText
            score += base_showtext_boost

            # Check for descriptive keywords
            descriptive_keywords = ["hyperreal", "digital painting", "anime style", "photorealistic", "cinematic"]
            keyword_count = sum(1 for keyword in descriptive_keywords if keyword in text.lower())

            # Check for character descriptors
            character_descriptors = ["japanese", "caucasian", "albino", "athletic", "thicc"]
            char_descriptor_count = sum(1 for desc in character_descriptors if desc in text.lower())

            if keyword_count >= 3:
                score += 2
                reasons.append("HIGHLY_DESCRIPTIVE_SHOWTEXT")
            elif keyword_count >= 1:
                score += 1
                reasons.append("DESCRIPTIVE_SHOWTEXT")

            if char_descriptor_count >= 2:
                score += 1
                reasons.append("DETAILED_CHARACTER_SHOWTEXT")

        return {
            "score": round(score, 2),
            "reasons": reasons,
            "confidence_modifier": confidence_modifier,
            "node_bonus": node_bonus,
            "text_length": text_length
        }

    def is_complex_scene_vs_simple_style(self, complex_text: str, simple_text: str) -> bool:
        """Check if complex_text is a detailed scene description vs simple_text being just style tags."""
        # Scene description indicators
        scene_words = ["girl", "woman", "man", "person", "character", "sitting", "standing", "wearing",
                      "holding", "room", "background", "scene", "portrait", "full body", "dress"]
        # Style/technical indicators
        style_words = ["masterpiece", "best quality", "8k", "detailed", "realistic", "photorealistic"]

        complex_scene_count = sum(1 for word in scene_words if word in complex_text.lower())
        simple_style_count = sum(1 for word in style_words if word in simple_text.lower())

        # If complex text has scene descriptors and simple text is mostly style tags
        return complex_scene_count >= 2 and simple_style_count >= 2 and len(simple_text) < len(complex_text) * 0.7

    def is_simple_style_prompt(self, text: str) -> bool:
        """Check if text is just a simple style prompt (like 'chibi anime style')."""
        words = text.lower().split()
        style_words = {"masterpiece", "best", "quality", "detailed", "realistic", "8k", "4k", "hd", "uhd"}
        return len(words) <= 10 and sum(1 for w in words if w in style_words) >= len(words) // 2
