# dataset_tools/analysis/features.py

import re

# <<< FIX 1: CLEANED UP IMPORTS >>>
# We have a single, clean, absolute import for everything we need.
from dataset_tools.analysis.data_models import FeatureAnalysisResult
from dataset_tools.dispatcher import ImageReaderInstance
from dataset_tools.vendored_sdpr.format.base_format import BaseFormat

# --- Constants ---
# Using constants makes the code more readable and maintainable.
SDXL_MIN_DIMENSION = 1024
MIN_VIABLE_SDXL_AREA = 768 * 768


def _is_parser_report_valid(parser_instance: ImageReaderInstance | None) -> bool:
    """Check if the parser instance is valid and successful."""
    if not parser_instance:
        return False
    status_class = getattr(BaseFormat, "Status", None)
    return status_class and parser_instance.status == status_class.READ_SUCCESS


# --- All the individual checker functions are correct and stay the same ---


def check_for_flux(parser_instance: ImageReaderInstance | None) -> bool:
    """Check if the generation used a FLUX model."""
    if not _is_parser_report_valid(parser_instance):
        return False
    params = getattr(parser_instance, "parameter", {})
    if "flux" in params.get("model", "").lower():
        return True
    resources = params.get("civitai_resources") or params.get("civitai_resources_data")
    if isinstance(resources, list):
        for res in resources:
            if isinstance(res, dict) and "flux" in res.get("modelName", "").lower():
                return True
    raw_data = getattr(parser_instance, "raw", "")
    if "ComfyUI" in getattr(parser_instance, "tool", "") and isinstance(raw_data, str):
        if '"class_type": "FluxGuidance"' in raw_data or '"unet_name": "flux' in raw_data:
            return True
    return False


def check_for_ponyx(parser_instance: ImageReaderInstance | None) -> bool:
    """Check if the generation used a PonyXL finetune."""
    if not _is_parser_report_valid(parser_instance):
        return False
    prompt = getattr(parser_instance, "positive", "")
    if not isinstance(prompt, str):
        return False
    prompt_lower = prompt.lower()
    if "ponyxscores" in prompt_lower or "ponyxv6_scores" in prompt_lower:
        return True
    if re.search(r"score_\d+(_up)?", prompt_lower):
        return True
    return "source_" in prompt_lower


def check_for_illustriousxl(parser_instance: ImageReaderInstance | None) -> bool:
    """Check for IllustriousXL finetunes."""
    if not _is_parser_report_valid(parser_instance):
        return False
    params = getattr(parser_instance, "parameter", {})
    if "illustrious" in params.get("model", "").lower():
        return True
    resources = params.get("civitai_resources") or params.get("civitai_resources_data")
    if isinstance(resources, list):
        for res in resources:
            if isinstance(res, dict) and res.get("type") == "checkpoint":
                if "illustrious" in res.get("modelName", "").lower():
                    return True
    return False


def check_for_lora(parser_instance: ImageReaderInstance | None) -> bool:
    """Check if a LoRA was used in the generation."""
    if not _is_parser_report_valid(parser_instance):
        return False
    params = getattr(parser_instance, "parameter", {})
    if params.get("Lora hashes") or params.get("Lora hashes data"):
        return True
    prompt = getattr(parser_instance, "positive", "")
    return isinstance(prompt, str) and "<lora:" in prompt


def check_for_sd15(parser_instance: ImageReaderInstance | None) -> bool:
    """Check if the image is likely from the SD 1.5 architecture using a heuristic scoring system."""
    if not _is_parser_report_valid(parser_instance):
        return False
    if check_for_ponyx(parser_instance) or check_for_illustriousxl(parser_instance) or check_for_flux(parser_instance):
        return False
    params = getattr(parser_instance, "parameter", {})
    score = 0
    if "xl" in params.get("Model", "").lower():
        score += 2
    if "xl" in params.get("Vae model", "").lower():
        score += 2
    try:
        width = int(params.get("Width", 0))
        height = int(params.get("Height", 0))
        if (width * height) >= MIN_VIABLE_SDXL_AREA:
            score += 2
        else:
            score -= 1
    except (ValueError, TypeError):
        pass
    return score <= 0


# <<< FIX 2: RESTORED THE CORRECT PYDANTIC-ENABLED FUNCTION >>>
def analyze_features(
    parser_instance: ImageReaderInstance | None,
) -> FeatureAnalysisResult | None:
    """Analyze all known features from a parsed object and return a validated
    Pydantic model. Returns None if the parser instance is not valid.
    """
    if not _is_parser_report_valid(parser_instance):
        return None

    raw_results = {
        "is_flux": check_for_flux(parser_instance),
        "is_ponyx": check_for_ponyx(parser_instance),
        "is_illustriousxl": check_for_illustriousxl(parser_instance),
        "has_lora": check_for_lora(parser_instance),
    }
    raw_results["architecture"] = "SD1.5" if check_for_sd15(parser_instance) else "SDXL/Other"
    raw_results["has_known_finetune_or_lora"] = (
        raw_results["is_ponyx"] or raw_results["is_illustriousxl"] or raw_results["has_lora"]
    )

    # Return the validated Pydantic object, ensuring data integrity.
    return FeatureAnalysisResult(**raw_results)
