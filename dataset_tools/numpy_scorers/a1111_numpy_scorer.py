"""A1111-Specific Numpy Scorer
===========================

Specialized numpy scoring for Automatic1111 format metadata.
Handles A1111-specific prompt patterns and parameter extraction.
"""

import re
import time
from typing import Any

import numpy as np

from ..logger import get_logger
from .base_numpy_scorer import BaseNumpyScorer

logger = get_logger(__name__)

# A1111-specific parameter weights
A1111_PARAMETER_WEIGHTS = {
    "steps": 0.1,         # Generation steps
    "cfg_scale": 0.1,     # CFG scale
    "sampler": 0.05,      # Sampler method
    "seed": 0.05,         # Seed value
    "size": 0.1,          # Image dimensions
    "model": 0.15,        # Model name
    "clip_skip": 0.05,    # CLIP skip
    "ensd": 0.02,         # Eta noise seed delta
}

# A1111 template indicators
A1111_TEMPLATE_INDICATORS = [
    "prompt",
    "positive:",
    "negative:",
    "parameters:",
    "steps:",
    "sampler:",
    "cfg scale:",
    "seed:",
    "size:",
    "model hash:",
    "model:",
]


class A1111NumpyScorer(BaseNumpyScorer):
    """Numpy-based analyzer specifically for Automatic1111 format."""

    def __init__(self):
        """Initialize the A1111 numpy analyzer."""
        super().__init__()
        self.logger = get_logger(f"{__name__}.A1111NumpyScorer")

        # A1111-specific quality indicators
        self.quality_keywords = [
            "masterpiece", "best quality", "ultra detailed", "extremely detailed",
            "highly detailed", "high resolution", "sharp focus", "professional",
            "award winning", "perfect", "stunning", "beautiful", "gorgeous",
            "photorealistic", "realistic", "detailed", "intricate", "fine art"
        ]

        # A1111-specific negative prompt indicators
        self.negative_indicators = [
            "worst quality", "low quality", "blurry", "bad anatomy", "ugly",
            "deformed", "mutated", "extra limbs", "missing limbs", "watermark",
            "signature", "text", "error", "jpeg artifacts", "lowres"
        ]

        # Common A1111 style patterns
        self.style_patterns = [
            ["portrait", "detailed", "realistic"],
            ["anime", "girl", "detailed"],
            ["landscape", "beautiful", "detailed"],
            ["photorealistic", "portrait", "professional"],
            ["masterpiece", "detailed", "art"]
        ]

    def _is_a1111_template_text(self, text: str) -> bool:
        """Check if text appears to be A1111 template content."""
        if self._is_template_text(text):  # Use base template detection
            return True

        text_lower = text.lower().strip()

        # Check for A1111 parameter indicators (which shouldn't be in prompts)
        for indicator in A1111_TEMPLATE_INDICATORS:
            if text_lower.startswith(indicator.lower()):
                return True

        # Check for overly generic quality stacking (common in templates)
        quality_count = sum(1 for keyword in self.quality_keywords if keyword in text_lower)
        if quality_count > 5:  # Too many quality keywords suggests template
            return True

        return False

    def _parse_a1111_raw_data(self, raw_data: str) -> dict[str, Any]:
        """Intelligently parse A1111 raw metadata with numpy-enhanced logic."""
        if not raw_data or not isinstance(raw_data, str):
            return {}

        try:
            parsed = {
                "prompt": "",
                "negative_prompt": "",
                "parameters": {},
                "raw_text": raw_data,
                "parsing_confidence": 0.0
            }

            # Split into sections using numpy array operations for efficiency
            lines = np.array(raw_data.split("\n"))
            non_empty_lines = lines[lines != ""]

            # Find negative prompt delimiter
            neg_indices = np.where([bool(re.search(r"Negative prompt\s*:", line, re.IGNORECASE))
                                   for line in non_empty_lines])[0]

            # Find parameter section (lines with colons and key patterns)
            param_patterns = ["Steps:", "Sampler:", "CFG scale:", "Seed:", "Size:", "Model:"]
            param_line_indices = []

            for i, line in enumerate(non_empty_lines):
                if any(pattern in line for pattern in param_patterns):
                    param_line_indices.append(i)

            param_start_idx = min(param_line_indices) if param_line_indices else len(non_empty_lines)

            # Extract positive prompt (everything before negative or parameters)
            prompt_end_idx = len(non_empty_lines)
            if len(neg_indices) > 0:
                prompt_end_idx = min(prompt_end_idx, neg_indices[0])
            prompt_end_idx = min(prompt_end_idx, param_start_idx)

            if prompt_end_idx > 0:
                parsed["prompt"] = "\n".join(non_empty_lines[:prompt_end_idx]).strip()

            # Extract negative prompt
            if len(neg_indices) > 0:
                neg_start = neg_indices[0]
                neg_end = min(param_start_idx, len(non_empty_lines))

                # Get the negative prompt line and any following lines before parameters
                neg_lines = []
                for i in range(neg_start, neg_end):
                    if i < len(non_empty_lines):
                        neg_lines.append(non_empty_lines[i])

                if neg_lines:
                    neg_text = "\n".join(neg_lines)
                    # Clean up the negative prompt line
                    neg_match = re.search(r"Negative prompt\s*:\s*(.*)", neg_text, re.IGNORECASE | re.DOTALL)
                    if neg_match:
                        parsed["negative_prompt"] = neg_match.group(1).strip()

            # Extract parameters with numpy-enhanced parsing
            if param_line_indices:
                param_text = "\n".join(non_empty_lines[param_start_idx:])
                parsed["parameters"] = self._extract_parameters_numpy(param_text)

            # Calculate parsing confidence based on what we found
            confidence = 0.0
            if parsed["prompt"]:
                confidence += 0.4
            if parsed["negative_prompt"]:
                confidence += 0.2
            if parsed["parameters"]:
                confidence += 0.3 + (len(parsed["parameters"]) * 0.01)

            parsed["parsing_confidence"] = min(1.0, confidence)

            return parsed

        except Exception as e:
            self.logger.error(f"Error in numpy A1111 parsing: {e}")
            return {"parsing_error": str(e), "raw_text": raw_data}

    def _extract_parameters_numpy(self, param_text: str) -> dict[str, Any]:
        """Extract A1111 parameters using numpy-enhanced regex parsing."""
        parameters = {}

        try:
            # Common A1111 parameter patterns
            param_patterns = {
                "steps": r"Steps\s*:\s*(\d+)",
                "sampler_name": r"Sampler\s*:\s*([^,\n]+)",
                "cfg_scale": r"CFG scale\s*:\s*([\d.]+)",
                "seed": r"Seed\s*:\s*(\d+)",
                "size": r"Size\s*:\s*(\d+x\d+)",
                "model": r"Model\s*:\s*([^,\n]+)",
                "model_hash": r"Model hash\s*:\s*([a-fA-F0-9]+)",
                "clip_skip": r"Clip skip\s*:\s*(\d+)",
                "denoising_strength": r"Denoising strength\s*:\s*([\d.]+)",
                "version": r"Version\s*:\s*([^,\n]+)",
            }

            for key, pattern in param_patterns.items():
                match = re.search(pattern, param_text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()

                    # Type conversion
                    if key in ["steps", "seed", "clip_skip"]:
                        try:
                            parameters[key] = int(value)
                        except ValueError:
                            parameters[key] = value
                    elif key in ["cfg_scale", "denoising_strength"]:
                        try:
                            parameters[key] = float(value)
                        except ValueError:
                            parameters[key] = value
                    elif key == "size":
                        size_match = re.match(r"(\d+)x(\d+)", value)
                        if size_match:
                            parameters["width"] = int(size_match.group(1))
                            parameters["height"] = int(size_match.group(2))
                        parameters[key] = value
                    else:
                        parameters[key] = value

        except Exception as e:
            self.logger.error(f"Error extracting parameters: {e}")

        return parameters

    def _calculate_a1111_confidence(self, candidate: dict[str, Any]) -> float:
        """Calculate A1111-specific confidence score."""
        confidence = self._calculate_base_confidence(candidate)
        text = candidate.get("text", "")

        if not text:
            return 0.0

        text_lower = text.lower()

        # A1111 template detection penalty
        if self._is_a1111_template_text(text):
            confidence *= 0.2  # Heavy penalty for templates

        # Quality keyword analysis
        quality_count = sum(1 for keyword in self.quality_keywords if keyword in text_lower)
        if 1 <= quality_count <= 3:  # Reasonable amount of quality keywords
            confidence += 0.1
        elif quality_count > 5:  # Too many suggests template
            confidence *= 0.5

        # Style pattern bonus
        for pattern in self.style_patterns:
            if all(word in text_lower for word in pattern):
                confidence += 0.05
                break

        # Length-based scoring for A1111
        text_len = len(text.strip())
        if 20 <= text_len <= 300:  # Typical A1111 prompt length
            confidence += 0.1
        elif text_len > 500:  # Very long prompts are less common in A1111
            confidence *= 0.8

        # Structural indicators
        if "," in text:  # Comma-separated tags (common in A1111)
            confidence += 0.05
        if "(" in text and ")" in text:  # Weighted tokens
            confidence += 0.1

        return min(1.0, max(0.0, confidence))

    def _analyze_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Analyze A1111 parameters for additional confidence scoring."""
        analysis = {
            "parameter_count": len(parameters),
            "completeness_score": 0.0,
            "quality_indicators": []
        }

        # Calculate completeness score based on common A1111 parameters
        expected_params = ["steps", "cfg_scale", "sampler", "seed", "size"]
        present_params = [param for param in expected_params if param in parameters]
        analysis["completeness_score"] = len(present_params) / len(expected_params)

        # Check for quality indicators in parameters
        steps = parameters.get("steps", 0)
        if isinstance(steps, (int, float)) and steps >= 20:
            analysis["quality_indicators"].append("adequate_steps")
        elif isinstance(steps, str):
            try:
                if int(steps) >= 20:
                    analysis["quality_indicators"].append("adequate_steps")
            except ValueError:
                pass

        cfg_scale = parameters.get("cfg_scale", 0)
        if isinstance(cfg_scale, (int, float)) and 5.0 <= cfg_scale <= 15.0:
            analysis["quality_indicators"].append("reasonable_cfg")
        elif isinstance(cfg_scale, str):
            try:
                if 5.0 <= float(cfg_scale) <= 15.0:
                    analysis["quality_indicators"].append("reasonable_cfg")
            except ValueError:
                pass

        seed = parameters.get("seed", -1)
        if isinstance(seed, (int, float)) and seed != -1:
            analysis["quality_indicators"].append("specific_seed")
        elif isinstance(seed, str):
            try:
                if int(seed) != -1:
                    analysis["quality_indicators"].append("specific_seed")
            except ValueError:
                pass

        return analysis

    def score_candidate(self, candidate: dict[str, Any], format_type: str = "a1111") -> dict[str, Any]:
        """Score an A1111 text candidate with format-specific knowledge."""
        start_time = time.time()

        try:
            # Calculate A1111-specific confidence
            confidence = self._calculate_a1111_confidence(candidate)

            # Analyze parameters if present
            parameters = candidate.get("parameters", {})
            param_analysis = self._analyze_parameters(parameters) if parameters else {}

            # Adjust confidence based on parameter analysis
            if param_analysis:
                completeness_bonus = param_analysis.get("completeness_score", 0) * 0.1
                quality_bonus = len(param_analysis.get("quality_indicators", [])) * 0.02
                confidence += completeness_bonus + quality_bonus

            # Create scored candidate
            scored_candidate = candidate.copy()
            scored_candidate["confidence"] = min(1.0, max(0.0, confidence))
            scored_candidate["scoring_method"] = "a1111_numpy"
            scored_candidate["format_type"] = format_type

            if param_analysis:
                scored_candidate["parameter_analysis"] = param_analysis

            processing_time = time.time() - start_time
            self._track_analytics("score_candidate", True, processing_time, format_type)

            return scored_candidate

        except Exception as e:
            self.logger.error(f"Error scoring A1111 candidate: {e}")
            processing_time = time.time() - start_time
            self._track_analytics("score_candidate", False, processing_time, format_type)

            # Return low-confidence result
            return {
                **candidate,
                "confidence": 0.1,
                "scoring_method": "a1111_numpy_error",
                "error": str(e)
            }

    def enhance_engine_result(self, engine_result: dict[str, Any], original_file_path: str | None = None) -> dict[str, Any]:
        """Enhance engine results with A1111-specific numpy analysis and smart fallback parsing."""
        try:
            # Check if this looks like A1111 data
            tool = engine_result.get("tool", "").lower()
            format_name = engine_result.get("format", "").lower()

            is_a1111_format = ("a1111" in tool or "automatic1111" in format_name or "automatic" in tool)

            # Get current data
            prompt = engine_result.get("prompt", "")
            negative_prompt = engine_result.get("negative_prompt", "")
            parameters = engine_result.get("parameters", {})
            raw_metadata = engine_result.get("raw_metadata", {})

            # Check if extraction failed or data is incomplete
            extraction_failed = (not prompt and not negative_prompt) or not parameters

            # If extraction failed and we have raw metadata, try smart parsing
            if extraction_failed and raw_metadata:
                self.logger.info("A1111 extraction appears incomplete, attempting numpy fallback parsing")

                # Try to get raw text from various sources
                raw_text = None
                if isinstance(raw_metadata, dict):
                    raw_text = raw_metadata.get("parameters", "") or raw_metadata.get("UserComment", "")
                elif isinstance(raw_metadata, str):
                    raw_text = raw_metadata

                if raw_text:
                    parsed_data = self._parse_a1111_raw_data(raw_text)

                    if parsed_data.get("parsing_confidence", 0) > 0.5:
                        self.logger.info(f"Numpy fallback parsing successful with confidence {parsed_data['parsing_confidence']}")

                        # Create enhanced result with fallback data
                        enhanced_result = engine_result.copy()

                        # Use parsed data if current data is empty
                        if not prompt and parsed_data.get("prompt"):
                            enhanced_result["prompt"] = parsed_data["prompt"]
                        if not negative_prompt and parsed_data.get("negative_prompt"):
                            enhanced_result["negative_prompt"] = parsed_data["negative_prompt"]
                        if not parameters and parsed_data.get("parameters"):
                            enhanced_result["parameters"] = parsed_data["parameters"]

                        enhanced_result["numpy_analysis"] = {
                            "enhancement_applied": True,
                            "fallback_parsing_used": True,
                            "parsing_confidence": parsed_data["parsing_confidence"],
                            "scoring_method": "a1111_numpy_fallback",
                            "extracted_fields": list(parsed_data.keys())
                        }

                        return enhanced_result

            # Regular enhancement for successful extractions
            if is_a1111_format or (prompt and parameters):
                # Create candidates for analysis
                candidates = []

                if prompt:
                    candidates.append({
                        "text": prompt,
                        "type": "positive",
                        "parameters": parameters
                    })

                if negative_prompt:
                    candidates.append({
                        "text": negative_prompt,
                        "type": "negative",
                        "parameters": parameters
                    })

                # Score candidates
                if candidates:
                    enhanced_candidates = [self.score_candidate(c, "a1111") for c in candidates]

                    # Find best positive candidate
                    positive_candidates = [c for c in enhanced_candidates if c.get("type") == "positive"]
                    if positive_candidates:
                        best_positive = max(positive_candidates, key=lambda x: x.get("confidence", 0))

                        enhanced_result = engine_result.copy()
                        enhanced_result["numpy_analysis"] = {
                            "enhancement_applied": True,
                            "best_positive_confidence": best_positive.get("confidence"),
                            "scoring_method": "a1111_numpy",
                            "parameter_analysis": best_positive.get("parameter_analysis", {}),
                            "fallback_parsing_used": False
                        }

                        return enhanced_result

        except Exception as e:
            self.logger.error(f"Error in A1111 numpy enhancement: {e}")

        return engine_result


def should_use_a1111_numpy_scoring(engine_result: dict[str, Any]) -> bool:
    """Determine if A1111 numpy scoring should be applied."""
    tool = engine_result.get("tool", "").lower()
    format_name = engine_result.get("format", "").lower()

    # Check for A1111-specific indicators
    if "a1111" in tool or "automatic1111" in format_name or "automatic" in tool:
        return True

    # Check for A1111-style parameters
    parameters = engine_result.get("parameters", {})
    if isinstance(parameters, dict):
        a1111_param_indicators = ["steps", "cfg_scale", "sampler_name", "seed"]
        if any(param in parameters for param in a1111_param_indicators):
            return True

    return False
