# Dataset-Tools/metadata_parser.py
"""This module serves as the primary interface for parsing metadata from files.

It utilizes the new modular metadata engine to identify and extract data,
then formats it into a standardized dictionary for UI consumption.
"""

import traceback
from pathlib import Path
from typing import Any

from . import numpy_scorer
from .correct_types import DownField, UpField
from .logger import get_logger, info_monitor as nfo
from .metadata_engine.engine import create_metadata_engine
from .metadata_engine.parser_registry import register_parser_class
from .vendored_sdpr.format.a1111 import A1111
from .vendored_sdpr.format.civitai import CivitaiFormat

# Import vendored parser classes for registration
from .vendored_sdpr.format.drawthings import DrawThings
from .vendored_sdpr.format.easydiffusion import EasyDiffusion
from .vendored_sdpr.format.fooocus import Fooocus
from .vendored_sdpr.format.invokeai import InvokeAI
from .vendored_sdpr.format.novelai import NovelAI
from .vendored_sdpr.format.swarmui import SwarmUI

# --- Constants ---
PARSER_DEFINITIONS_PATH = str(Path(__file__).parent / "parser_definitions")


# Register vendored parser classes
def _register_vendored_parsers():
    """Register all vendored parser classes for use with base_format_class."""
    register_parser_class("DrawThings", DrawThings)
    register_parser_class("NovelAI", NovelAI)
    register_parser_class("A1111", A1111)
    # register_parser_class("ComfyUI", ComfyUI)  # Disabled: Use modern extraction system via parser definitions
    register_parser_class("CivitaiFormat", CivitaiFormat)
    register_parser_class("EasyDiffusion", EasyDiffusion)
    register_parser_class("Fooocus", Fooocus)
    register_parser_class("InvokeAI", InvokeAI)
    register_parser_class("SwarmUI", SwarmUI)


# Register parsers on module import
_register_vendored_parsers()


def parse_metadata(file_path_named: str, status_callback=None, extract_exif_fallback: bool = True) -> dict[str, Any]:
    """Parses metadata from a given file using the modular metadata engine.

    This function initializes the metadata engine, processes the file,
    and then transforms the extracted data into the format expected by the UI.

    Args:
        file_path_named: The absolute path to the file to be parsed.

    Returns:
        A dictionary containing the parsed metadata, formatted for the UI.

    """
    nfo("[DT.metadata_parser]: >>> ENTERING parse_metadata for: %s", file_path_named)
    final_ui_dict: dict[str, Any] = {}

    try:
        # Create the metadata engine with proper logger
        nfo("[DT.metadata_parser]: Creating metadata engine with path: %s", PARSER_DEFINITIONS_PATH)
        engine_logger = get_logger()  # Use the same logger as the rest of the app
        engine = create_metadata_engine(PARSER_DEFINITIONS_PATH, logger=engine_logger)
        nfo("[DT.metadata_parser]: Engine created successfully, calling get_parser_for_file")

        # Process the file
        result = engine.get_parser_for_file(file_path_named)
        nfo("[DT.metadata_parser]: get_parser_for_file returned: %s - %s", type(result), bool(result))

        if result and isinstance(result, dict) and result:
            # This is the robust, architecturally correct fix.
            # First, ensure the raw_metadata is a dictionary before proceeding.
            raw_meta = result.get("raw_metadata")
            if isinstance(raw_meta, str):
                # Check if this looks like A1111 text format (should stay as string)
                # A1111 format has patterns like "Steps: 30, Sampler: euler" or "Negative prompt:"
                is_a1111_format = ("Steps:" in raw_meta or "Negative prompt:" in raw_meta or
                                   "Sampler:" in raw_meta or "CFG scale:" in raw_meta)

                if is_a1111_format:
                    # Keep as string - A1111 format will be parsed by numpy enhancement
                    nfo("[DT.metadata_parser]: Detected A1111 text format, keeping as string for numpy enhancement")
                else:
                    # Try parsing as structured data (JSON/Python literal)
                    try:
                        import json

                        # First try standard JSON parsing (handles escaped quotes properly)
                        result["raw_metadata"] = json.loads(raw_meta)
                        nfo("[DT.metadata_parser]: Successfully parsed raw_metadata string as JSON.")
                    except json.JSONDecodeError as e:
                        try:
                            # Fallback: try ast.literal_eval for Python dict strings
                            import ast
                            result["raw_metadata"] = ast.literal_eval(raw_meta)
                            nfo("[DT.metadata_parser]: Successfully parsed raw_metadata string as Python literal.")
                        except (ValueError, SyntaxError) as e2:
                            nfo("[DT.metadata_parser]: Could not parse raw_metadata string (JSON error: %s, AST error: %s)", e, e2)
                            # If parsing fails, we cannot proceed with numpy enhancement.
                            result["raw_metadata"] = {"error": "unparseable_string", "original_string": raw_meta}

            # Apply numpy enhancement to ALL parsing results (no longer conditional)
            try:
                if status_callback:
                    status_callback("Analyzing workflow with numpy enhancement...")

                # DEBUG: Log what parser extracted BEFORE numpy enhancement
                parser_prompt = result.get("prompt", "")
                parser_negative = result.get("negative_prompt", "")
                nfo("[DT.metadata_parser]: BEFORE NUMPY - Parser extracted prompt: %s", parser_prompt[:100] if parser_prompt else "NONE")
                nfo("[DT.metadata_parser]: BEFORE NUMPY - Parser extracted negative: %s", parser_negative[:100] if parser_negative else "NONE")

                # FALLBACK: If A1111 hybrid parser found no prompts, try extracting from ComfyUI workflow
                parser_name = result.get("parser", "")
                if parser_name == "a1111_string_with_workflow":
                    if (not parser_prompt or not parser_negative):
                        nfo("[DT.metadata_parser]: A1111 hybrid parser missing prompts, attempting ComfyUI workflow fallback...")

                        # Get the workflow from the engine's context (prepared during file processing)
                        workflow_data = None

                        # First try: Get from raw_workflow_json field (debug field from parser)
                        import json
                        raw_workflow = result.get("raw_workflow_json", "")
                        if raw_workflow:
                            if isinstance(raw_workflow, str):
                                try:
                                    workflow_data = json.loads(raw_workflow)
                                    nfo("[DT.metadata_parser]: Found workflow in raw_workflow_json (string)")
                                except Exception as e:
                                    logger.debug("Failed to parse raw_workflow_json as JSON: %s", e)
                            elif isinstance(raw_workflow, dict):
                                workflow_data = raw_workflow
                                nfo("[DT.metadata_parser]: Found workflow in raw_workflow_json (dict)")

                        # Second try: Get from the engine context directly (this is where it actually is!)
                        if not workflow_data:
                            # The workflow was loaded into context during file preparation
                            # We need to re-parse it from the file since we don't have context access here
                            try:
                                from PIL import Image
                                with Image.open(file_path_named) as img:
                                    workflow_json = img.info.get('workflow', '')
                                    if workflow_json:
                                        if isinstance(workflow_json, str):
                                            workflow_data = json.loads(workflow_json)
                                        else:
                                            workflow_data = workflow_json
                                        nfo("[DT.metadata_parser]: Loaded workflow directly from image file")
                            except Exception as e:
                                nfo("[DT.metadata_parser]: Failed to load workflow from file: %s", e)

                        if workflow_data and isinstance(workflow_data, dict):
                            # Use the ComfyUI extractor to get prompts from workflow
                            try:
                                comfyui_extractor = engine.field_extractor.comfyui_extractor

                                # Extract positive prompt if missing
                                if not parser_prompt:
                                    positive_result = comfyui_extractor._find_legacy_text_from_main_sampler_input(
                                        data=workflow_data,
                                        method_def={"positive_input_name": "positive"},
                                        context={},  # Empty context - not needed for basic extraction
                                        fields={}    # Empty fields - not needed for basic extraction
                                    )
                                    if positive_result:
                                        result["prompt"] = positive_result
                                        nfo("[DT.metadata_parser]: ✅ Fallback extracted positive prompt from workflow: %s", positive_result[:100])

                                # Extract negative prompt if missing
                                if not parser_negative:
                                    negative_result = comfyui_extractor._find_legacy_text_from_main_sampler_input(
                                        data=workflow_data,
                                        method_def={"negative_input_name": "negative"},
                                        context={},  # Empty context - not needed for basic extraction
                                        fields={}    # Empty fields - not needed for basic extraction
                                    )
                                    if negative_result:
                                        result["negative_prompt"] = negative_result
                                        nfo("[DT.metadata_parser]: ✅ Fallback extracted negative prompt from workflow: %s", negative_result[:100])

                            except Exception as fallback_error:
                                nfo("[DT.metadata_parser]: ⚠️ Workflow fallback failed: %s", fallback_error)
                        else:
                            nfo("[DT.metadata_parser]: ⚠️ No valid workflow data found for fallback")

                nfo("[DT.metadata_parser]: Applying numpy enhancement to all parsing results")
                enhanced_result = numpy_scorer.enhance_result(result, file_path_named)
                result = enhanced_result
                if status_callback:
                    status_callback("Numpy enhancement completed")

                # DEBUG: Log what numpy changed it to AFTER enhancement
                numpy_prompt = result.get("prompt", "")
                numpy_negative = result.get("negative_prompt", "")
                nfo("[DT.metadata_parser]: AFTER NUMPY - Final prompt: %s", numpy_prompt[:100] if numpy_prompt else "NONE")
                nfo("[DT.metadata_parser]: AFTER NUMPY - Final negative: %s", numpy_negative[:100] if numpy_negative else "NONE")

                nfo("[DT.metadata_parser]: Numpy enhancement completed. Enhanced: %s", enhanced_result.get("numpy_analysis", {}).get("enhancement_applied", False))
            except Exception as numpy_error:
                nfo("[DT.metadata_parser]: Numpy enhancement failed: %s, using original result", numpy_error)
                # Continue with original result if numpy fails

            # Transform the engine result to UI format
            _transform_engine_result_to_ui_dict(result, final_ui_dict)
            potential_ai_parsed = True
            nfo("[DT.metadata_parser]: Successfully parsed metadata with engine. Keys: %s", list(result.keys()))
        else:
            nfo("[DT.metadata_parser]: Engine found no matching parser or returned invalid data.")
            potential_ai_parsed = False

    except Exception as e:
        nfo("[DT.metadata_parser]: ❌ MetadataEngine failed: %s", e)
        traceback.print_exc()
        final_ui_dict["error"] = {
            "Error": "Metadata Engine failed: %s" % e,
        }
        potential_ai_parsed = False

    # 4. Add standard EXIF metadata if no AI metadata was found (only for full detail view, not thumbnails)
    if not potential_ai_parsed and extract_exif_fallback:
        nfo("[DT.metadata_parser]: No AI metadata found, extracting standard EXIF data...")
        exif_data = _extract_basic_exif(file_path_named)
        if exif_data:
            final_ui_dict[DownField.GENERATION_DATA.value] = exif_data
            final_ui_dict[UpField.METADATA.value] = {
                "Source": "EXIF Data (No AI metadata detected)"
            }
            nfo("[DT.metadata_parser]: Extracted basic EXIF metadata")

    if not final_ui_dict:
        final_ui_dict["info"] = {
            "Info": "No processable metadata found.",
        }
        nfo("Failed to find/load any metadata for file: %s", file_path_named)

    nfo("[DT.metadata_parser]: <<< EXITING parse_metadata. Returning keys: %s", list(final_ui_dict.keys()))
    return final_ui_dict


def _transform_engine_result_to_ui_dict(result: dict[str, Any], ui_dict: dict[str, Any]) -> None:
    """Transforms the raw result from the metadata engine into the structured UI dictionary."""
    # --- Main Prompts ---
    prompt_data = {
        "Positive": result.get("prompt", ""),
        "Negative": result.get("negative_prompt", ""),
    }
    if result.get("is_sdxl", False):
        prompt_data["Positive SDXL"] = result.get("positive_sdxl", {})
        prompt_data["Negative SDXL"] = result.get("negative_sdxl", {})
    ui_dict[UpField.PROMPT.value] = prompt_data

    # --- Generation Parameters ---
    parameters = result.get("parameters", {})
    if isinstance(parameters, dict):
        ui_dict[DownField.GENERATION_DATA.value] = parameters

    # --- Raw Data ---
    raw_data = result.get("raw_metadata")
    if not isinstance(raw_data, dict):
        raw_data = {"raw_content": str(raw_data)}  # Wrap non-dict raw_metadata in a dict
    ui_dict[DownField.RAW_DATA.value] = raw_data

    # --- Detected Tool ---
    tool_name = result.get("tool", "Unknown")
    format_name = result.get("format", "Unknown")
    if tool_name != "Unknown" or format_name != "Unknown":
        if UpField.METADATA.value not in ui_dict:
            ui_dict[UpField.METADATA.value] = {}
        if tool_name != "Unknown":
            ui_dict[UpField.METADATA.value]["Detected Tool"] = tool_name
        if format_name != "Unknown":
            ui_dict[UpField.METADATA.value]["format"] = format_name

    # --- Add any other top-level fields from the result ---
    for key, value in result.items():
        if key not in [
            "prompt",
            "negative_prompt",
            "positive_sdxl",
            "negative_sdxl",
            "parameters",
            "raw_metadata",
            "tool",
            "is_sdxl",
            "tipo_enhancement",
            "workflow_complexity",
            "advanced_upscaling",
            "multi_stage_conditioning",
            "post_processing_effects",
            "custom_node_ecosystems",
            "workflow_techniques",
        ]:
            if "unclassified" not in ui_dict:
                ui_dict["unclassified"] = {}
            ui_dict["unclassified"][key] = value

    # --- Workflow Analysis ---
    workflow_analysis_data = {}
    if "tipo_enhancement" in result:
        workflow_analysis_data["TIPO Enhancement"] = result["tipo_enhancement"]
    if "workflow_complexity" in result:
        workflow_analysis_data["Workflow Complexity"] = result["workflow_complexity"]
    if "advanced_upscaling" in result:
        workflow_analysis_data["Advanced Upscaling"] = result["advanced_upscaling"]
    if "multi_stage_conditioning" in result:
        workflow_analysis_data["Multi-Stage Conditioning"] = result["multi_stage_conditioning"]
    if "post_processing_effects" in result:
        workflow_analysis_data["Post-Processing Effects"] = result["post_processing_effects"]
    if "custom_node_ecosystems" in result:
        workflow_analysis_data["Custom Node Ecosystems"] = result["custom_node_ecosystems"]
    if "workflow_techniques" in result:
        workflow_analysis_data["Workflow Techniques"] = result["workflow_techniques"]

    if workflow_analysis_data:
        ui_dict[UpField.WORKFLOW_ANALYSIS.value] = workflow_analysis_data

    # --- Civitai API Info ---
    # Check both top-level (from Safetensors) and parameters (from ComfyUI/A1111 parsers)
    civitai_api_info = None
    if "civitai_api_info" in result and result["civitai_api_info"]:
        civitai_api_info = result["civitai_api_info"]
    elif "parameters" in result and isinstance(result["parameters"], dict):
        if "civitai_api_info" in result["parameters"] and result["parameters"]["civitai_api_info"]:
            civitai_api_info = result["parameters"]["civitai_api_info"]

    if civitai_api_info:
        ui_dict[UpField.CIVITAI_INFO.value] = civitai_api_info


def _extract_basic_exif(file_path: str) -> dict[str, Any] | None:
    """Extract basic EXIF metadata when no AI metadata is found.

    Args:
        file_path: Path to the image file

    Returns:
        Dictionary of EXIF fields or None if no useful EXIF data found
    """
    try:
        from PIL import Image
        import piexif
        import io

        img = Image.open(file_path)
        result = {}

        # Get basic image info
        result["Format"] = img.format or "Unknown"
        result["Dimensions"] = f"{img.width} x {img.height}"

        # ICC Color Profile
        if "icc_profile" in img.info:
            try:
                from PIL import ImageCms
                icc_bytes = img.info["icc_profile"]
                profile = ImageCms.ImageCmsProfile(io.BytesIO(icc_bytes))
                # Get profile description (e.g., "sRGB IEC61966-2.1")
                profile_desc = ImageCms.getProfileDescription(profile)
                if profile_desc:
                    result["Color Profile"] = profile_desc.strip()
            except Exception:
                # If we can't parse the profile, just note that it exists
                result["Color Profile"] = "Present (unknown)"

        # Progressive JPEG info
        if img.format == "JPEG" and img.info.get("progressive"):
            result["JPEG Encoding"] = "Progressive"

        # Try to get EXIF data
        exif_dict = piexif.load(img.info.get("exif", b""))
        if not exif_dict:
            return result if result else None

        # EXIF tag numbers (IFD0 - main tags)
        exif_0th = exif_dict.get("0th", {})
        exif_exif = exif_dict.get("Exif", {})  # Exif-specific tags
        exif_gps = exif_dict.get("GPS", {})    # GPS tags

        # Camera Make (271) and Model (272)
        if 271 in exif_0th:
            make_bytes = exif_0th[271]
            if isinstance(make_bytes, bytes):
                try:
                    make = make_bytes.decode("ascii", "ignore").strip("\x00")
                    if make:
                        result["Camera Make"] = make
                except Exception as e:
                    logger.debug("Failed to decode Camera Make EXIF field: %s", e)

        if 272 in exif_0th:
            model_bytes = exif_0th[272]
            if isinstance(model_bytes, bytes):
                try:
                    model = model_bytes.decode("ascii", "ignore").strip("\x00")
                    if model:
                        result["Camera Model"] = model
                except Exception as e:
                    logger.debug("Failed to decode Camera Model EXIF field: %s", e)

        # Software (305)
        if 305 in exif_0th:
            software_bytes = exif_0th[305]
            if isinstance(software_bytes, bytes):
                try:
                    software = software_bytes.decode("ascii", "ignore").strip("\x00")
                    if software:
                        result["Software"] = software
                except Exception as e:
                    logger.debug("Failed to decode Software EXIF field: %s", e)

        # DateTime (306)
        if 306 in exif_0th:
            datetime_bytes = exif_0th[306]
            if isinstance(datetime_bytes, bytes):
                try:
                    datetime_str = datetime_bytes.decode("ascii", "ignore").strip("\x00")
                    if datetime_str:
                        result["DateTime"] = datetime_str
                except Exception as e:
                    logger.debug("Failed to decode DateTime EXIF field: %s", e)

        # Resolution (282, 283)
        if 282 in exif_0th:
            try:
                x_res = exif_0th[282]
                if isinstance(x_res, tuple) and len(x_res) == 2:
                    # Rational format: (numerator, denominator)
                    if x_res[1] != 0:
                        dpi = x_res[0] / x_res[1]
                        result["Resolution"] = f"{int(dpi)} DPI"
            except Exception as e:
                logger.debug("Failed to parse Resolution EXIF field: %s", e)

        # Exposure Time (33434) - in Exif IFD
        if 33434 in exif_exif:
            try:
                exp_time = exif_exif[33434]
                if isinstance(exp_time, tuple) and len(exp_time) == 2:
                    if exp_time[1] != 0:
                        exp_val = exp_time[0] / exp_time[1]
                        if exp_val < 1:
                            result["Exposure Time"] = f"1/{int(1/exp_val)} sec"
                        else:
                            result["Exposure Time"] = f"{exp_val:.2f} sec"
            except Exception as e:
                logger.debug("Failed to parse Exposure Time EXIF field: %s", e)

        # F-Number (33437) - in Exif IFD
        if 33437 in exif_exif:
            try:
                f_num = exif_exif[33437]
                if isinstance(f_num, tuple) and len(f_num) == 2:
                    if f_num[1] != 0:
                        f_val = f_num[0] / f_num[1]
                        result["Aperture"] = f"f/{f_val:.1f}"
            except Exception as e:
                logger.debug("Failed to parse Aperture EXIF field: %s", e)

        # ISO Speed (34855) - in Exif IFD
        if 34855 in exif_exif:
            try:
                iso = exif_exif[34855]
                if isinstance(iso, int):
                    result["ISO"] = str(iso)
                elif isinstance(iso, tuple) and len(iso) > 0:
                    result["ISO"] = str(iso[0])
            except Exception as e:
                logger.debug("Failed to parse ISO EXIF field: %s", e)

        # Focal Length (37386) - in Exif IFD
        if 37386 in exif_exif:
            try:
                focal = exif_exif[37386]
                if isinstance(focal, tuple) and len(focal) == 2:
                    if focal[1] != 0:
                        focal_val = focal[0] / focal[1]
                        result["Focal Length"] = f"{focal_val:.1f}mm"
            except Exception as e:
                logger.debug("Failed to parse Focal Length EXIF field: %s", e)

        # Focal Length in 35mm (41989) - in Exif IFD
        if 41989 in exif_exif:
            try:
                focal_35 = exif_exif[41989]
                if isinstance(focal_35, int):
                    result["Focal Length (35mm equiv)"] = f"{focal_35}mm"
                elif isinstance(focal_35, tuple) and len(focal_35) > 0:
                    result["Focal Length (35mm equiv)"] = f"{focal_35[0]}mm"
            except Exception as e:
                logger.debug("Failed to parse Focal Length (35mm) EXIF field: %s", e)

        # Flash (37385) - in Exif IFD
        if 37385 in exif_exif:
            try:
                flash = exif_exif[37385]
                if isinstance(flash, int):
                    # Flash tag is a bitmask, but simple check: 0 = no flash
                    flash_status = "Fired" if (flash & 0x01) else "Did not fire"
                    result["Flash"] = flash_status
                elif isinstance(flash, tuple) and len(flash) > 0:
                    flash_val = flash[0]
                    flash_status = "Fired" if (flash_val & 0x01) else "Did not fire"
                    result["Flash"] = flash_status
            except Exception as e:
                logger.debug("Failed to parse Flash EXIF field: %s", e)

        # GPS Coordinates - DISABLED for privacy reasons
        # Extracting GPS data can trigger macOS location/Bluetooth permission prompts
        # and displaying exact coordinates could be a privacy/security concern.
        # Users can use dedicated EXIF tools if they need GPS data.

        return result if result else None

    except Exception as e:
        nfo("[DT.metadata_parser]: Failed to extract EXIF: %s", e)
        return None
