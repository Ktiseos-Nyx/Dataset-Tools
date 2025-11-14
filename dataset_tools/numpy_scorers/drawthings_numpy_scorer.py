"""Draw Things Numpy Scorer
=======================

Specialized numpy scoring for Draw Things XMP metadata format.
Handles Draw Things' JSON structure in XMP UserComment and provides
enhanced prompt extraction with confidence scoring.
"""

import time
from typing import Any

from ..logger import get_logger
from .base_numpy_scorer import BaseNumpyScorer

logger = get_logger(__name__)


class DrawThingsNumpyScorer(BaseNumpyScorer):
    """Numpy-based analyzer specifically for Draw Things XMP format."""

    def __init__(self):
        """Initialize Draw Things numpy scorer."""
        super().__init__()
        self.format_name = "Draw Things XMP"

    def enhance_engine_result(self, engine_result: dict[str, Any], original_file_path: str | None = None) -> dict[str, Any]:
        """Enhance Draw Things parsing results with numpy analysis."""
        start_time = time.time()

        try:
            logger.debug("Draw Things scorer enhance_engine_result called")
            logger.debug("Draw Things engine_result keys: %s", list(engine_result.keys()))

            # Draw Things data should already be parsed by SDPR format
            # Check what we already have from the base parser
            existing_prompt = engine_result.get("prompt", "")
            existing_negative = engine_result.get("negative_prompt", "")
            existing_params = engine_result.get("parameters", {})

            logger.debug("Existing prompt: %s...", existing_prompt[:100] if existing_prompt else "None")
            logger.debug("Existing negative: %s...", existing_negative[:100] if existing_negative else "None")
            logger.debug("Existing parameters: %s", list(existing_params.keys()))

            # For Draw Things, the SDPR parser should have already extracted the data
            # We just need to verify and enhance what's there
            prompts_found = {
                "positive": bool(existing_prompt and existing_prompt.strip()),
                "negative": bool(existing_negative and existing_negative.strip())
            }

            if not (prompts_found["positive"] or prompts_found["negative"]):
                logger.debug("No prompts found in parsed Draw Things result - parser definition may need fixing")
                engine_result["numpy_analysis"] = {"enhanced": False, "reason": "parser_definition_extraction_failed"}
                return engine_result

            # The data is already extracted by SDPR Draw Things parser
            # We just need to add enhancement metadata
            logger.debug("Draw Things data already parsed by SDPR format")
            logger.debug("Positive prompt available: %s", prompts_found["positive"])
            logger.debug("Negative prompt available: %s", prompts_found["negative"])
            logger.debug("Parameters available: %s", len(existing_params))

            # Add analysis metadata directly to result
            processing_time = time.time() - start_time
            engine_result["numpy_analysis"] = {
                "enhanced": True,
                "scorer": "Draw Things Numpy Scorer",
                "extraction_method": "SDPR Format Enhancement",
                "processing_time": processing_time,
                "prompts_found": prompts_found,
                "parameters_available": len(existing_params)
            }

            logger.info("Draw Things numpy enhancement completed in %.3fs", processing_time)
            logger.debug("Draw Things enhancement completed - Enhanced: True")

            return engine_result

        except Exception as e:
            logger.error("Error in Draw Things numpy enhancement: %s", e, exc_info=True)
            engine_result["numpy_analysis"] = {"enhanced": False, "error": str(e)}
            return engine_result

    def _analyze_drawthings_metadata(self, workflow_metadata: dict[str, Any]) -> dict[str, Any]:
        """Analyze Draw Things workflow metadata and extract prompts/parameters."""
        result = {
            "positive_prompt": "",
            "negative_prompt": "",
            "parameters": {}
        }

        try:
            logger.debug("Draw Things workflow_metadata keys: %s", list(workflow_metadata.keys()) if isinstance(workflow_metadata, dict) else "Not a dict")

            # The workflow_metadata should be the parsed Draw Things data
            # Based on the Draw Things parser, this should contain the JSON structure directly
            json_data = workflow_metadata

            if not isinstance(json_data, dict):
                logger.warning("Draw Things workflow_metadata is not a dictionary")
                return result

            logger.debug("Draw Things JSON keys found: %s", list(json_data.keys()))

            # Extract positive prompt (key: "c")
            if "c" in json_data and isinstance(json_data["c"], str):
                result["positive_prompt"] = json_data["c"].strip()
                logger.debug("Found positive prompt: %s...", result["positive_prompt"][:100])

            # Extract negative prompt (key: "uc")
            if "uc" in json_data and isinstance(json_data["uc"], str):
                result["negative_prompt"] = json_data["uc"].strip()
                logger.debug("Found negative prompt: %s...", result["negative_prompt"][:100])

            # Extract parameters
            param_mapping = {
                "steps": "steps",
                "scale": "cfg_scale",  # Draw Things uses "scale" for CFG scale
                "sampler": "sampler",
                "seed": "seed",
                "size": "dimensions",
                "model": "model",
                "clip_skip": "clip_skip",
                "strength": "strength",
                "aesthetic_score": "aesthetic_score",
                "negative_aesthetic_score": "negative_aesthetic_score"
            }

            for dt_key, standard_key in param_mapping.items():
                if dt_key in json_data:
                    result["parameters"][standard_key] = json_data[dt_key]

            # Handle special cases for dimensions
            if "size" in json_data:
                # Parse dimensions like "832x1216"
                try:
                    size_str = str(json_data["size"])
                    if "x" in size_str:
                        width, height = size_str.split("x", 1)
                        result["parameters"]["width"] = int(width.strip())
                        result["parameters"]["height"] = int(height.strip())
                        # Remove the generic dimensions entry since we have width/height
                        if "dimensions" in result["parameters"]:
                            del result["parameters"]["dimensions"]
                except (ValueError, IndexError):
                    result["parameters"]["dimensions"] = json_data["size"]

            # Extract v2 parameters if available (more detailed parameter structure)
            if "v2" in json_data and isinstance(json_data["v2"], dict):
                v2_data = json_data["v2"]
                logger.debug("Found v2 parameter structure with keys: %s", list(v2_data.keys()))

                # Map v2 parameters to standard names (v2 parameters override basic ones)
                v2_mapping = {
                    "guidanceScale": "cfg_scale",
                    "width": "width",
                    "height": "height",
                    "steps": "steps",
                    "seed": "seed",
                    "strength": "strength",
                    "clipSkip": "clip_skip"
                }

                for v2_key, standard_key in v2_mapping.items():
                    if v2_key in v2_data:
                        result["parameters"][standard_key] = v2_data[v2_key]
                        logger.debug("Extracted v2 parameter %s -> %s: %s", v2_key, standard_key, v2_data[v2_key])

            logger.debug("Draw Things analysis extracted %s parameters", len(result["parameters"]))
            logger.debug("Final extracted parameters: %s", list(result["parameters"].keys()))

        except Exception as e:
            logger.error("Error analyzing Draw Things metadata: %s", e, exc_info=True)

        return result


def should_use_drawthings_numpy_scoring(engine_result: dict[str, Any]) -> bool:
    """Determine if Draw Things numpy scoring should be applied."""
    tool = engine_result.get("tool", "").lower()
    format_name = engine_result.get("format", "").lower()

    # Check for Draw Things specific indicators
    if "draw things" in tool:
        return True

    if "xmp" in format_name and "json" in format_name:
        return True

    # Check for Draw Things metadata structure
    workflow_metadata = engine_result.get("workflow_metadata", {})
    if isinstance(workflow_metadata, dict):
        # Look for Draw Things specific keys
        dt_indicators = ["c", "uc", "v2", "usercomment_json"]
        if any(key in workflow_metadata for key in dt_indicators):
            return True

    return False
