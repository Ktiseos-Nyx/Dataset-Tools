# Dataset-Tools/metadata_parser.py

import logging as pylog
import re
import traceback
from pathlib import Path
from typing import Any  # Using Union for Python 3.9+ for Optional[X] -> X | None

# First-party (absolute imports from your project)
from dataset_tools import LOG_LEVEL as CURRENT_APP_LOG_LEVEL  # Assuming this is in __init__.py

from .access_disk import MetadataFileReader

# First-party (relative imports for the current subpackage)
from .correct_types import DownField, EmptyField, UpField
from .logger import _dataset_tools_main_rich_console
from .logger import info_monitor as nfo  # Assuming info_monitor is your nfo
from .logger import setup_rich_handler_for_external_logger
# from .model_tool import ModelTool # ADD THIS IMPORT
# --- NEW: Import MetadataEngine ---
from .metadata_engine import MetadataEngine
# Our main fixer function
from .vendored_sdpr.image_data_reader import get_generation_parameters
from .vendored_sdpr.format import (
    A1111, CivitaiFormat, ComfyUI, DrawThings, EasyDiffusion,
    Fooocus, InvokeAI, NovelAI, RuinedFooocusFormat, SwarmUI,
    TensorArtFormat as TensorArt, YodayoFormat as Yodayo
)
# We need the list of parsers to try and the BaseFormat to check for success

# from .vendored_sdpr.format import BaseFormat
# --- Import VENDORED sd-prompt-reader components (for fallback and BaseFormat type) ---
VENDORED_SDPR_OK = False
ImageDataReader = None  # type: Any
BaseFormat = None  # type: Any
PARAMETER_PLACEHOLDER = "                    "

try:
    from .vendored_sdpr.constants import PARAMETER_PLACEHOLDER as VENDORED_PARAMETER_PLACEHOLDER
    from .vendored_sdpr.format import BaseFormat as RealBaseFormat  # Actual class import
    from .vendored_sdpr.image_data_reader import ImageDataReader as RealImageDataReader

    # Assign real classes
    ImageDataReader = RealImageDataReader
    BaseFormat = RealBaseFormat
    PARAMETER_PLACEHOLDER = VENDORED_PARAMETER_PLACEHOLDER
    VENDORED_SDPR_OK = True
    nfo("[DT.metadata_parser]: Successfully imported VENDORED SDPR components.")

    vendored_parent_logger_instance = pylog.getLogger("DSVendored_SDPR")
    setup_rich_handler_for_external_logger(
        logger_to_configure=vendored_parent_logger_instance,
        rich_console_to_use=_dataset_tools_main_rich_console,
        log_level_to_set_str=CURRENT_APP_LOG_LEVEL,
    )
    nfo(
        f"[DT.metadata_parser]: Configured Rich logging for 'DSVendored_SDPR' logger tree at level {CURRENT_APP_LOG_LEVEL}."
    )

except ImportError as import_err_vendor:
    nfo(
        f"CRITICAL WARNING [DT.metadata_parser]: Failed to import VENDORED SDPR components: {import_err_vendor}. AI Parsing will be severely limited."
    )
    traceback.print_exc()
    VENDORED_SDPR_OK = False

    class DummyImageDataReader:
        def __init__(self, _file_obj: Any, _is_txt: bool = False) -> None:
            self.status = None
            self.tool = None
            self.positive = ""
            self.negative = ""
            self.parameter: dict[str, Any] = {}
            self.width = "0"
            self.height = "0"
            self.setting = ""
            self.raw = ""
            self.is_sdxl = False
            self.positive_sdxl: dict[str, Any] = {}
            self.negative_sdxl: dict[str, Any] = {}
            self.format = ""
            self.error = ""

    class DummyBaseFormat:  # type: ignore
        class Status:
            UNREAD = object()
            READ_SUCCESS = object()
            FORMAT_ERROR = object()
            COMFYUI_ERROR = object()
            MISSING_INFO = object()
            FORMAT_DETECTION_ERROR = object()

        PARAMETER_PLACEHOLDER = "                    "
        tool = "Unknown Dummy"

    ImageDataReader = DummyImageDataReader
    BaseFormat = DummyBaseFormat  # type: ignore
    PARAMETER_PLACEHOLDER = DummyBaseFormat.PARAMETER_PLACEHOLDER


# --- Utility Functions ---
def make_paired_str_dict(
    text_to_convert: str,
) -> dict[str, str]:  # Added type hint for return  # noqa: C901
    if not text_to_convert or not isinstance(text_to_convert, str):
        return {}
    converted_text: dict[str, str] = {}  # Added type hint
    # This is the more robust regex pattern you provided
    pattern_string = r"""
        ([\w\s().\-/]+?)        # Group 1: Key (non-greedy, allows specified chars like '.', '-', '/')
        :\s*                    # Colon and optional whitespace
        (                       # Group 2: Value
            "(?:\\.|[^"\\])*"   # Option 1: Double-quoted string (handles escaped quotes)
          |                     # OR
            '(?:\\.|[^'\\])*'   # Option 2: Single-quoted string (handles escaped quotes)
          |                     # OR
            (?:                 # Option 3: Unquoted value - match until next key or EOL
                .+?             # Match one or more characters, non-greedily
                (?=             # Positive lookahead: stop BEFORE
                    \s*,\s*[\w\s().\-/]+?: # optional whitespace, a comma, space, and the next key pattern
                  |             # OR
                    $           # End of the string
                )
            )
        )
    """
    pattern = re.compile(pattern_string, re.VERBOSE)
    last_end = 0
    for match in pattern.finditer(text_to_convert):
        # Check for unparsed text between the last match and current match (gaps)
        if match.start() > last_end:
            unparsed_gap = text_to_convert[last_end : match.start()].strip(" ,")
            if unparsed_gap and unparsed_gap not in [
                ",",
                ":",
            ]:  # Avoid logging just delimiters
                nfo(f"[DT.make_paired_str_dict] Unparsed gap: '{unparsed_gap[:50]}...'")  # Use your logger

        key = match.group(1).strip()
        value_str = match.group(2).strip()

        # Remove surrounding quotes from the captured value string if they exist
        if (value_str.startswith('"') and value_str.endswith('"')) or (
            value_str.startswith("'") and value_str.endswith("'")
        ):
            value_str = value_str[1:-1]
            # Potentially handle escaped quotes within the string here if needed, e.g. value_str = value_str.replace('\\"', '"')
            # but the regex (?:\\.|[^"\\])* already handles consuming escaped characters.

        converted_text[key] = value_str
        last_end = match.end()

        # Advance last_end past the delimiter (comma and spaces) if present
        match_delimiter = re.match(r"\s*,\s*", text_to_convert[last_end:])
        if match_delimiter:
            last_end += len(match_delimiter.group(0))
        else:
            # Also skip any standalone spaces if no comma (for cases like "Key1: Val1  Key2: Val2")
            match_spaces = re.match(r"\s*", text_to_convert[last_end:])
            if match_spaces:
                last_end += len(match_spaces.group(0))

    # Check for any remaining unparsed text at the end of the string
    if last_end < len(text_to_convert):
        remaining_unparsed = text_to_convert[last_end:].strip()
        if remaining_unparsed:
            nfo(f"[DT.make_paired_str_dict] Final unparsed segment: '{remaining_unparsed[:100]}...'")  # Use your logger
            # Attempt to capture simple, non-key-value suffix data (like A1111 version string often at end)
            if ":" not in remaining_unparsed and "," not in remaining_unparsed and len(remaining_unparsed.split()) < 5:  # noqa: PLR2004
                # Avoid capturing if it looks like a malformed KV or too many words
                if (
                    "Lora hashes" not in converted_text and "Version" not in converted_text
                ):  # Avoid if these common multi-part keys are expected
                    converted_text["Uncategorized Suffix"] = remaining_unparsed
    return converted_text


# PLACE THIS DEFINITION IN YOUR metadata_parser.py
# WITH OTHER HELPER FUNCTIONS, BEFORE parse_metadata


def _populate_ui_from_base_format_instance(  # Ensure this name matches EXACTLY  # noqa: C901
    parser_instance: Any,
    ui_dict_to_update: dict[str, Any],
    source_description: str = "Python Parser",
) -> None:
    # Make globally defined constants/enums accessible if they are not imported directly
    # This depends on how PARAMETER_PLACEHOLDER, UpField, DownField, BaseFormat etc.
    # are available in the scope of metadata_parser.py


    if not parser_instance or not hasattr(parser_instance, "status"):
        nfo(f"[DT._populate_ui_base_fmt] Invalid parser_instance for {source_description}.")
        return

    CurrentBaseFormat = BaseFormat if VENDORED_SDPR_OK else DummyBaseFormat  # type: ignore
    # Check if Status and READ_SUCCESS exist on the determined BaseFormat class
    if not hasattr(CurrentBaseFormat, "Status") or not hasattr(CurrentBaseFormat.Status, "READ_SUCCESS"):  # type: ignore
        nfo(f"[DT._populate_ui_base_fmt] BaseFormat.Status.READ_SUCCESS not found for {source_description}.")
        return

    expected_success_status = CurrentBaseFormat.Status.READ_SUCCESS  # type: ignore

    if parser_instance.status != expected_success_status:
        status_name = getattr(parser_instance.status, "name", str(parser_instance.status))
        error_message = getattr(parser_instance, "error", "N/A")
        tool_name_for_log = getattr(parser_instance, "tool", "UnknownTool")
        nfo(
            f"[DT._populate_ui_base_fmt] {source_description} ({tool_name_for_log}) did not succeed. Status: {status_name}. Error: {error_message}"
        )
        return

    tool_name = getattr(parser_instance, "tool", "UnknownTool")
    nfo(f"[DT._populate_ui_base_fmt] Populating UI from {source_description}. Tool: {tool_name}")

    # Prompts
    temp_prompt_data = ui_dict_to_update.get(UpField.PROMPT.value, {})
    if hasattr(parser_instance, "positive") and parser_instance.positive:
        temp_prompt_data["Positive"] = str(parser_instance.positive)
    if hasattr(parser_instance, "negative") and parser_instance.negative:
        temp_prompt_data["Negative"] = str(parser_instance.negative)
    if getattr(parser_instance, "is_sdxl", False):
        if getattr(parser_instance, "positive_sdxl", None):
            temp_prompt_data["Positive SDXL"] = parser_instance.positive_sdxl
        if getattr(parser_instance, "negative_sdxl", None):
            temp_prompt_data["Negative SDXL"] = parser_instance.negative_sdxl
    if temp_prompt_data:
        ui_dict_to_update[UpField.PROMPT.value] = temp_prompt_data

    # Generation Data
    temp_gen_data = ui_dict_to_update.get(DownField.GENERATION_DATA.value, {})
    if hasattr(parser_instance, "parameter") and parser_instance.parameter:
        for key, value in parser_instance.parameter.items():
            if value and value != PARAMETER_PLACEHOLDER:  # PARAMETER_PLACEHOLDER needs to be defined/imported
                display_key = key.replace("_", " ").capitalize()
                temp_gen_data[display_key] = str(value)

    parser_width = str(getattr(parser_instance, "width", "0"))
    parser_height = str(getattr(parser_instance, "height", "0"))
    if parser_width != "0" and parser_width != PARAMETER_PLACEHOLDER:
        temp_gen_data["Width"] = parser_width
    if parser_height != "0" and parser_height != PARAMETER_PLACEHOLDER:
        temp_gen_data["Height"] = parser_height

    # Ensure "Size" is consistent or removed
    if (
        "Width" in temp_gen_data
        and "Height" in temp_gen_data
        and temp_gen_data["Width"] != "0"
        and temp_gen_data["Height"] != "0"
        and temp_gen_data["Width"] != PARAMETER_PLACEHOLDER
        and temp_gen_data["Height"] != PARAMETER_PLACEHOLDER
    ):
        temp_gen_data["Size"] = f"{temp_gen_data['Width']}x{temp_gen_data['Height']}"
    elif "Size" in temp_gen_data and (temp_gen_data["Size"] == PARAMETER_PLACEHOLDER or temp_gen_data["Size"] == "0x0"):
        del temp_gen_data["Size"]

    setting_display_val = getattr(parser_instance, "setting", "")
    if setting_display_val:
        current_tool = getattr(parser_instance, "tool", "UnknownTool")
        if isinstance(current_tool, str) and any(
            t in current_tool for t in ["A1111", "Forge", "SD.Next", "Yodayo", "Kohya"]
        ):
            additional_settings = make_paired_str_dict(
                str(setting_display_val)
            )  # Assumes make_paired_str_dict is defined
            for key_add, value_add in additional_settings.items():
                display_key_add = key_add.replace("_", " ").capitalize()
                if display_key_add not in temp_gen_data or temp_gen_data.get(display_key_add) in [
                    None,
                    "None",
                    PARAMETER_PLACEHOLDER,
                    "",
                ]:
                    temp_gen_data[display_key_add] = str(value_add)
        elif isinstance(current_tool, str) and current_tool not in {
            "Unknown",
            "Unknown Dummy",
        }:
            temp_gen_data["Tool Specific Data Block"] = str(setting_display_val)
    if temp_gen_data:
        ui_dict_to_update[DownField.GENERATION_DATA.value] = temp_gen_data

    # Raw Data
    if hasattr(parser_instance, "raw") and parser_instance.raw:
        ui_dict_to_update[DownField.RAW_DATA.value] = str(parser_instance.raw)

    # Metadata (Tool Name)
    tool_name_for_meta = getattr(parser_instance, "tool", "UnknownTool")
    if tool_name_for_meta and tool_name_for_meta != "Unknown" and tool_name_for_meta != "Unknown Dummy":
        if UpField.METADATA.value not in ui_dict_to_update:
            ui_dict_to_update[UpField.METADATA.value] = {}
        ui_dict_to_update[UpField.METADATA.value]["Detected Tool"] = tool_name_for_meta


def _populate_ui_from_engine_dict(engine_dict_output: dict[str, Any], ui_dict_to_update: dict[str, Any]) -> None:  # noqa: C901
    nfo(f"[DT._populate_ui_engine_dict] Received engine_dict_output: {engine_dict_output}") # Log the input
    tool_name = engine_dict_output.get("tool", "Unknown (Engine JSON)")

    prompt_data = ui_dict_to_update.get(UpField.PROMPT.value, {})
    if engine_dict_output.get("prompt") is not None:
        prompt_data["Positive"] = str(engine_dict_output["prompt"])
    if engine_dict_output.get("negative_prompt") is not None:
        prompt_data["Negative"] = str(engine_dict_output["negative_prompt"])
    # Add SDXL prompt handling from engine_dict_output["parameters"]["sdxl_prompts"] if your template produces it
    if prompt_data:
        ui_dict_to_update[UpField.PROMPT.value] = prompt_data

    gen_data = ui_dict_to_update.get(DownField.GENERATION_DATA.value, {})
    engine_params = engine_dict_output.get("parameters", {})
    if isinstance(engine_params, dict):
        for key, value in engine_params.items():
            if key == "tool_specific" and isinstance(value, dict):
                for ts_key, ts_value in value.items():
                    if ts_value is not None and ts_value != PARAMETER_PLACEHOLDER:
                        display_key = ts_key.replace("_", " ").capitalize() + " (Tool Specific)"
                        gen_data[display_key] = str(ts_value)
            elif value is not None and value != PARAMETER_PLACEHOLDER:
                display_key = key.replace("_", " ").capitalize()
                gen_data[display_key] = str(value)
    if gen_data:
        ui_dict_to_update[DownField.GENERATION_DATA.value] = gen_data

    # Raw Data (examples based on your JSON output_template ideas)
    raw_keys_to_check = [
        "workflow",
        "source_raw_input_string",
        "raw_json_content",
        "INPUT_JSON_OBJECT_AS_STRING",
    ]
    for raw_key in raw_keys_to_check:
        if engine_dict_output.get(raw_key) is not None:
            ui_dict_to_update[DownField.RAW_DATA.value] = str(engine_dict_output[raw_key])
            break  # Take the first one found

    if UpField.METADATA.value not in ui_dict_to_update:
        ui_dict_to_update[UpField.METADATA.value] = {}
    ui_dict_to_update[UpField.METADATA.value]["Detected Tool"] = tool_name
    if engine_dict_output.get("parser_name_from_engine"):  # If engine adds this for clarity
        ui_dict_to_update[UpField.METADATA.value]["Engine Parser Def"] = engine_dict_output["parser_name_from_engine"]


def process_pyexiv2_data(pyexiv2_header_data: dict[str, Any], ai_tool_parsed: bool = False) -> dict[str, Any]:  # noqa: C901
    # ... (Your existing process_pyexiv2_data function) ...
    final_ui_meta: dict[str, Any] = {}
    if not pyexiv2_header_data:
        return final_ui_meta
        # --- THIS IS THE UPGRADED LOGIC ---
    # We will only process the UserComment if our main AI parser has FAILED.
    if "Exif.Photo.UserComment" in pyexiv2_header_data.get("EXIF", {}) and not ai_tool_parsed:
        # ai_tool_parsed is False, meaning our main fallback failed.
        # It's safe to show the raw UserComment because it's our only option.
        nfo("[DT.process_pyexiv2_data] AI parse failed, processing raw UserComment as a fallback.")
        uc_val = pyexiv2_header_data["EXIF"]["Exif.Photo.UserComment"]
        uc_text_for_display = ""
        if isinstance(uc_val, bytes):
            # This logic is fine, it just decodes the raw bytes
            if uc_val.startswith(b"ASCII\x00\x00\x00"):
                uc_text_for_display = uc_val[8:].decode("ascii", "replace")
            elif uc_val.startswith(b"UNICODE\x00"):
                uc_text_for_display = uc_val[8:].decode("utf-16", "replace")
            else:
                try:
                    uc_text_for_display = uc_val.decode("utf-8", "replace")
                except UnicodeDecodeError:
                    uc_text_for_display = f"<bytes len {len(uc_val)} unable to decode>"
        elif isinstance(uc_val, str):
            uc_text_for_display = uc_val

        cleaned_uc_display = uc_text_for_display.strip("\x00 ").strip()
        if cleaned_uc_display:
            if DownField.EXIF.value not in final_ui_meta:
                 final_ui_meta[DownField.EXIF.value] = {}
            final_ui_meta[DownField.EXIF.value]["UserComment (Std.)"] = cleaned_uc_display
    elif ai_tool_parsed:
        # If the AI tool was successfully parsed, we explicitly DO NOT show the raw UserComment.
        nfo("[DT.process_pyexiv2_data] AI data was parsed successfully. Skipping raw UserComment to avoid showing garbled text.")
    xmp_data = pyexiv2_header_data.get("XMP", {})
    if xmp_data:
        displayable_xmp: dict[str, str] = {}
        if xmp_data.get("Xmp.dc.creator"):
            creator = xmp_data["Xmp.dc.creator"]
            displayable_xmp["Artist"] = ", ".join(creator) if isinstance(creator, list) else str(creator)
        if xmp_data.get("Xmp.dc.description"):
            desc_val = xmp_data["Xmp.dc.description"]
            desc_text = desc_val.get("x-default", str(desc_val)) if isinstance(desc_val, dict) else str(desc_val)
            if not ai_tool_parsed or len(desc_text) < 300:
                displayable_xmp["Description"] = desc_text
            elif ai_tool_parsed:
                displayable_xmp["Description (XMP)"] = f"Exists (length {len(desc_text)})"
        if xmp_data.get("Xmp.photoshop.DateCreated"):
            displayable_xmp["Date Created (XMP)"] = str(xmp_data["Xmp.photoshop.DateCreated"])
        if displayable_xmp:
            if UpField.TAGS.value not in final_ui_meta:
                final_ui_meta[UpField.TAGS.value] = {}
            final_ui_meta[UpField.TAGS.value].update(displayable_xmp)
    iptc_data = pyexiv2_header_data.get("IPTC", {})
    if iptc_data:
        displayable_iptc: dict[str, str] = {}
        if iptc_data.get("Iptc.Application2.Keywords"):
            keywords = iptc_data["Iptc.Application2.Keywords"]
            displayable_iptc["Keywords (IPTC)"] = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
        if iptc_data.get("Iptc.Application2.Caption"):
            displayable_iptc["Caption (IPTC)"] = str(iptc_data["Iptc.Application2.Caption"])
        if displayable_iptc:
            if UpField.TAGS.value not in final_ui_meta:
                final_ui_meta[UpField.TAGS.value] = {}
            final_ui_meta[UpField.TAGS.value].update(displayable_iptc)
    return final_ui_meta

# --- MAIN PARSING FUNCTION ---
def parse_metadata(file_path_named: str) -> dict[str, Any]:
    nfo("####################################################")
    nfo("[ModelTool] ##### read_metadata_from CALLED for: %s #####", file_path_named)
    nfo("####################################################")
    final_ui_dict: dict[str, Any] = {}
    path_obj = Path(file_path_named)
    file_ext_lower = path_obj.suffix.lower()
    potential_ai_parsed = False
    # VVVV This is the pyexiv2_raw_data we are fixing VVVV
    pyexiv2_raw_data: dict[str, Any] | None = None
    placeholder_key_str: str = getattr(EmptyField.PLACEHOLDER, "value", "_dt_internal_placeholder_")

    nfo(f"[DT.metadata_parser]: >>> ENTERING parse_metadata for: {file_path_named} (Engine Primary Flow)")

    # --- SECTION 1: MetadataEngine Call ---

    # --- PASTE THIS NEW, SIMPLIFIED SECTION IN ITS PLACE ---

    # --- Simplified Section 1: Always attempt to parse with MetadataEngine ---
    nfo("[DT.metadata_parser]: Attempting to parse with MetadataEngine (Model check temporarily disabled).")

    # Define paths and initialize the engine cleanly and only once
    current_script_path = Path(__file__).resolve().parent
    definitions_path = current_script_path / "parser_definitions"
    engine = MetadataEngine(parser_definitions_path=definitions_path, logger_obj=pylog.getLogger("MetadataEngine"))

    # Try to get a parser from the engine
    engine_result: Any | None = None
    try:
        engine_result = engine.get_parser_for_file(file_path_named)
    except Exception as e_engine_call:
        nfo(f"CRITICAL ERROR calling MetadataEngine: {e_engine_call}", exc_info=True)
        final_ui_dict.setdefault(placeholder_key_str, {})["Error"] = f"MetadataEngine execution error: {e_engine_call}"

# --- END OF REPLACEMENT ---
    # ^^^^ END OF YOUR EXISTING LOGIC FOR THIS SECTION ^^^^

    # --- SECTION 2: Processing MetadataEngine Result OR Fallback to VENDORED_SDPR ---
    # VVVV YOUR EXISTING LOGIC FOR THIS SECTION SHOULD BE HERE VVVV
    if engine_result:
        parser_def_name = "Unknown"
        if isinstance(engine_result, dict):
            parser_def_name = engine_result.get("parser_name_from_engine", "JSON_Instruction_Parser")
        nfo(
            f"[DT.metadata_parser]: MetadataEngine returned result. Type: {type(engine_result).__name__}. Parser Def: {parser_def_name}"
        )
        if BaseFormat and isinstance(engine_result, BaseFormat): # Check BaseFormat exists
            if engine_result.status == BaseFormat.Status.READ_SUCCESS:
                nfo(f"  Engine used Python class: {engine_result.tool}, success.")
                _populate_ui_from_base_format_instance( # Calls your helper
                    engine_result,
                    final_ui_dict,
                    source_description="Engine (Python Class)",
                )
                potential_ai_parsed = True
            else: # Handle failed BaseFormat from engine
                status_name = getattr(engine_result.status, "name", str(engine_result.status))
                error_msg = getattr(engine_result, "error", "No error details")
                nfo(f"  Engine used Python class: {engine_result.tool}, but failed. Status: {status_name}. Error: {error_msg}")
                # Optionally add error to final_ui_dict here if needed
        elif isinstance(engine_result, dict):
            nfo(f"  Engine used JSON instructions. Tool: {engine_result.get('tool')}")
            _populate_ui_from_engine_dict(engine_result, final_ui_dict) # Calls your helper
            potential_ai_parsed = True
        else:
            nfo(f"  Engine returned unknown result type: {type(engine_result).__name__}")
            final_ui_dict.setdefault(placeholder_key_str, {})["Error"] = f"MetadataEngine returned unhandled type: {type(engine_result).__name__}"

    # --- REPLACE THE DELETED BLOCK WITH THIS ---

# --- REPLACE THE ENTIRE `else: # engine_result is None` BLOCK WITH THIS ---

    else:  # engine_result is None
        nfo("[DT.metadata_parser]: MetadataEngine found no parser. Attempting NEW intelligent fallback.")
        try:
            # 1. Call our robust function to rescue the clean text from the file.
            nfo("[DT.metadata_parser]: Fallback: Calling get_generation_parameters to rescue garbled text...")
            clean_metadata_text = get_generation_parameters(file_path_named)

            if clean_metadata_text:
                nfo(f"[DT.metadata_parser]: Fallback success! Rescued clean text (len: {len(clean_metadata_text)}). Now testing all parsers on it...")

                # 2. THIS IS THE FIXED LINE. We use the lists from the ImageDataReader class itself.
                # --- REPLACE IT WITH THIS SMARTER, ORDERED LIST ---

                # 2. Re-order the parsers to be from MOST specific to LEAST specific.
                #    This prevents a "greedy" parser like A1111 from claiming JSON data.
                all_parsers_to_try = [
                    # JSON-based and specific formats first
                    ComfyUI,
                    Fooocus,
                    RuinedFooocusFormat,
                    DrawThings,
                    EasyDiffusion,
                    SwarmUI,
                    InvokeAI,
                    TensorArt,
                    # Text-based formats last
                    CivitaiFormat, # This one is hybrid, tries JSON then text
                    A1111,
                    Yodayo,
                    NovelAI,
                ]

# --- END REPLACEMENT ---

                # 3. Loop through every parser to find the one that understands the rescued text.
                for parser_class in all_parsers_to_try:
                    try:
                        temp_parser = parser_class(raw=clean_metadata_text)
                        temp_parser.parse()

                        if temp_parser.status == BaseFormat.Status.READ_SUCCESS:
                            nfo(f"[DT.metadata_parser]: SUCCESS! Fallback text was identified by: {temp_parser.tool}")
                            _populate_ui_from_base_format_instance(
                                temp_parser,
                                final_ui_dict,
                                source_description=f"Intelligent Fallback ({temp_parser.tool})"
                            )
                            potential_ai_parsed = True
                            break  # Exit the loop since we found the right parser.

                    except Exception as e_parser_loop:
                        nfo(f"[DT.metadata_parser]: Parser {parser_class.__name__} did not match fallback text. Error: {e_parser_loop}", exc_info=False)

                if not potential_ai_parsed:
                    nfo("[DT.metadata_parser]: Fallback text was rescued but not understood by any known parser.")
            else:
                nfo("[DT.metadata_parser]: Fallback (get_generation_parameters) found no data in the file.")

        except Exception as e:
            nfo(f"[DT.metadata_parser]: A critical error occurred in the new fallback logic: {e}", exc_info=True)

# --- END OF REPLACEMENT ---


# --- PASTE THIS IN ITS PLACE ---

        else:  # engine_result is None
            nfo("[DT.metadata_parser]: MetadataEngine found no parser. Attempting NEW intelligent fallback.")
        try:
            # 1. Call our robust function to rescue the clean text from the file.
            nfo("[DT.metadata_parser]: Fallback: Calling get_generation_parameters to rescue garbled text...")
            clean_metadata_text = get_generation_parameters(file_path_named)

            if clean_metadata_text:
                nfo(f"[DT.metadata_parser]: Fallback success! Rescued clean text (len: {len(clean_metadata_text)}). Now testing all parsers on it...")

                # 2. Combine all known parser classes to try against the clean text.
                # --- REPLACE IT WITH THIS SMARTER, ORDERED LIST ---

                # 2. Re-order the parsers to be from MOST specific to LEAST specific.
                #    This prevents a "greedy" parser like A1111 from claiming JSON data.
                all_parsers_to_try = [
                    # JSON-based and specific formats first
                    ComfyUI,
                    Fooocus,
                    RuinedFooocusFormat,
                    DrawThings,
                    EasyDiffusion,
                    SwarmUI,
                    InvokeAI,
                    TensorArt,
                    # Text-based formats last
                    CivitaiFormat, # This one is hybrid, tries JSON then text
                    A1111,
                    Yodayo,
                    NovelAI,
                ]

# --- END REPLACEMENT ---

                # 3. Loop through every parser to find the one that understands the rescued text.
                for parser_class in all_parsers_to_try:
                    try:
                        temp_parser = parser_class(raw=clean_metadata_text)
                        temp_parser.parse()

                        if temp_parser.status == BaseFormat.Status.READ_SUCCESS:
                            nfo(f"[DT.metadata_parser]: SUCCESS! Fallback text was identified by: {temp_parser.tool}")
                            _populate_ui_from_base_format_instance(
                                temp_parser,
                                final_ui_dict,
                                source_description=f"Intelligent Fallback ({temp_parser.tool})"
                            )
                            potential_ai_parsed = True
                            break  # Exit the loop since we found the right parser.

                    except Exception as e_parser_loop:
                        nfo(f"[DT.metadata_parser]: Parser {parser_class.__name__} did not match fallback text. Error: {e_parser_loop}", exc_info=False)

                if not potential_ai_parsed:
                    nfo("[DT.metadata_parser]: Fallback text was rescued but not understood by any known parser.")
            else:
                nfo("[DT.metadata_parser]: Fallback (get_generation_parameters) found no data in the file.")

        except Exception as e:
            nfo(f"[DT.metadata_parser]: A critical error occurred in the new fallback logic: {e}", exc_info=True)

# --- END OF REPLACEMENT ---


    # --- SECTION 3: Standard EXIF/XMP (pyexiv2 part) ---
    # VVVV THIS IS THE SECTION WE MODIFIED FOR pyexiv2_raw_data VVVV
    is_std_image_format = file_ext_lower in [
        ".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif",
    ]
    if is_std_image_format:
        nfo("[DT.metadata_parser]: Attempting to read standard photo EXIF/XMP with pyexiv2.")
        std_reader = MetadataFileReader() # Assuming MetadataFileReader is imported or defined

        # Use the function-scoped pyexiv2_raw_data, DO NOT redeclare with _local
        if file_ext_lower.endswith((".jpg", ".jpeg", ".webp")):
            pyexiv2_raw_data = std_reader.read_jpg_header_pyexiv2(file_path_named)
        elif file_ext_lower.endswith((".png", ".tif", ".tiff")): # Added .tif for completeness
            pyexiv2_raw_data = std_reader.read_png_header_pyexiv2(file_path_named)

        if pyexiv2_raw_data: # Now correctly uses the function-scoped variable
            standard_photo_meta = process_pyexiv2_data(pyexiv2_raw_data, ai_tool_parsed=potential_ai_parsed)
            if standard_photo_meta:
                # VVVV YOUR EXISTING MERGING LOGIC SHOULD BE HERE VVVV
                # Example (you'll have your specific merging logic):
                for key, value_dict in standard_photo_meta.items():
                    if key not in final_ui_dict:
                        final_ui_dict[key] = value_dict
                    elif isinstance(final_ui_dict[key], dict) and isinstance(value_dict, dict):
                        # Simple dict update, be careful about overwriting
                        for sub_key, sub_value in value_dict.items():
                            if sub_key not in final_ui_dict[key] or not final_ui_dict[key][sub_key]: # Don't overwrite existing AI data with generic if generic is empty
                                final_ui_dict[key][sub_key] = sub_value
                    else: # Fallback if types don't match for merging
                        final_ui_dict[f"{key}_pyexiv2"] = value_dict
                # ^^^^ END OF YOUR EXISTING MERGING LOGIC ^^^^
                nfo("[DT.metadata_parser]: Added/merged standard EXIF/XMP data (via pyexiv2).")
        elif not potential_ai_parsed and not final_ui_dict.get(placeholder_key_str, {}).get("Error"): # Check if an error was already set
            final_ui_dict.setdefault(placeholder_key_str, {})["Info"] = (
                "Standard image, but no processable EXIF/XMP fields found by pyexiv2."
            )
    else:
        nfo(
            f"[DT.metadata_parser]: File type '{file_ext_lower}' not a std image for pyexiv2 pass, or already handled."
        )
    # ^^^^ END OF MODIFIED SECTION ^^^^

    # --- SECTION 4: Final Placeholder/Error Message Logic ---
    # VVVV YOUR EXISTING LOGIC FOR THIS SECTION SHOULD BE HERE VVVV
    # Ensure this block is at the correct indentation (same level as the `is_std_image_format = ...` line)
    has_error_already = placeholder_key_str in final_ui_dict and "Error" in final_ui_dict.get(placeholder_key_str, {})

    if not final_ui_dict or (
        len(final_ui_dict) == 1
        and placeholder_key_str in final_ui_dict
        and not has_error_already # Check if error wasn't already set
        and not potential_ai_parsed
    ):
        final_ui_dict.setdefault(placeholder_key_str, {}).update(
            {"Info": "No processable metadata found after all attempts."}
        )
        nfo(f"Failed to find/load significant metadata for file: {file_path_named}")
    elif not potential_ai_parsed and not has_error_already: # Check if error wasn't already set
        is_model_file_key = UpField.METADATA.value # Get the actual key value
        is_model_file = final_ui_dict.get(is_model_file_key, {}).get("Detected Model Format")
        if not is_model_file:
            final_ui_dict.setdefault(placeholder_key_str, {}).update(
                {"Info": "No AI generation parameters found. Displaying other metadata."}
            )
    # ^^^^ END OF YOUR EXISTING LOGIC FOR THIS SECTION ^^^^

    nfo(f"[DT.metadata_parser]: <<< EXITING parse_metadata. Returning keys: {list(final_ui_dict.keys())}")
    return final_ui_dict
