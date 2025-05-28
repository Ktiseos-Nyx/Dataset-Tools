# Dataset-Tools/metadata_parser.py
# Refactored to primarily use a vendored version of SDPR's ImageDataReader for AI parsing
# and configures its logging to use Dataset-Tools' Rich console.

import json
from pathlib import Path
import traceback
import re # For make_paired_str_dict
import logging as pylog # For getting logger instances by name

from .correct_types import UpField, DownField, EmptyField
from .logger import info_monitor as nfo
from .logger import setup_rich_handler_for_external_logger # Import the new helper
from .logger import _dataset_tools_main_rich_console     # Import your Rich Console instance
from dataset_tools import LOG_LEVEL as CURRENT_APP_LOG_LEVEL # Get current level string from __init__
from .access_disk import MetadataFileReader # For pyexiv2 fallback for standard EXIF/XMP

# --- Import VENDORED sd-prompt-reader components ---
VENDORED_SDPR_OK = False
ImageDataReader = None
BaseFormat = None
PARAMETER_PLACEHOLDER = "                    "

try:
    from .vendored_sdpr.image_data_reader import ImageDataReader
    from .vendored_sdpr.format import BaseFormat
    from .vendored_sdpr.constants import PARAMETER_PLACEHOLDER

    VENDORED_SDPR_OK = True
    nfo(f"[DT.metadata_parser]: Successfully imported VENDORED SDPR components.")

    vendored_parent_logger_instance = pylog.getLogger("DSVendored_SDPR")
    setup_rich_handler_for_external_logger(
        logger_to_configure=vendored_parent_logger_instance,
        rich_console_to_use=_dataset_tools_main_rich_console,
        log_level_to_set_str=CURRENT_APP_LOG_LEVEL
    )
    nfo(f"[DT.metadata_parser]: Configured Rich logging for 'DSVendored_SDPR' logger tree at level {CURRENT_APP_LOG_LEVEL}.")

except ImportError as e_vendor:
    nfo(f"CRITICAL WARNING [DT.metadata_parser]: Failed to import VENDORED SDPR components: {e_vendor}. AI Parsing will be severely limited.")
    traceback.print_exc()
    VENDORED_SDPR_OK = False
    # Define Dummies only if the import fails
    class DummyImageDataReader:
        def __init__(self, f, is_txt=False): self.status=None;self.tool=None;self.positive="";self.negative="";self.parameter={};self.width="0";self.height="0";self.setting="";self.raw="";self.is_sdxl=False;self.positive_sdxl={};self.negative_sdxl={}; self.format=""
    class DummyBaseFormat: # This class will be defined if import fails
        class Status: UNREAD=object();READ_SUCCESS=object();FORMAT_ERROR=object();COMFYUI_ERROR=object()
        PARAMETER_PLACEHOLDER = "                    "
    ImageDataReader = DummyImageDataReader
    BaseFormat = DummyBaseFormat # BaseFormat will now refer to DummyBaseFormat
    PARAMETER_PLACEHOLDER = BaseFormat.PARAMETER_PLACEHOLDER


# --- Debug print for EmptyField (before its first major use in parse_metadata) ---
# This should be placed before parse_metadata or at the top of parse_metadata
# if EmptyField is only used there. For clarity, putting it here at module level once.
print(f"DEBUG METADATA_PARSER (module level): Type of EmptyField: {type(EmptyField)}, Type of EmptyField.PLACEHOLDER: {type(EmptyField.PLACEHOLDER)}")
try:
    print(f"DEBUG METADATA_PARSER (module level): Value of EmptyField.PLACEHOLDER.value: {EmptyField.PLACEHOLDER.value}")
    # If the above works, we can define placeholder_key_str to be used throughout
    # However, since it's used inside parse_metadata, let's define it there for scope.
except AttributeError:
    print(f"DEBUG METADATA_PARSER (module level): EmptyField.PLACEHOLDER does not have .value, it is: {EmptyField.PLACEHOLDER}")
# --- End Debug print for EmptyField ---


# --- Helper Functions ---

def make_paired_str_dict(text_to_convert: str) -> dict:
    if not text_to_convert or not isinstance(text_to_convert, str): return {}
    converted_text = {};
    pattern = re.compile(r"""([\w\s().\-/]+?):\s*((?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|(?:.(?!(?:,\s*[\w\s().\-/]+?:)))*?))""", re.VERBOSE)
    last_end = 0
    for match in pattern.finditer(text_to_convert):
        if match.start() > last_end:
            unparsed_gap = text_to_convert[last_end:match.start()].strip(" ,");
            if unparsed_gap and unparsed_gap not in [",", ":"]: nfo(f"[DT.make_paired_str_dict] Unparsed gap: '{unparsed_gap[:50]}...'")
        key = match.group(1).strip(); value_str = match.group(2).strip()
        if (value_str.startswith('"') and value_str.endswith('"')) or (value_str.startswith("'") and value_str.endswith("'")): value_str = value_str[1:-1]
        converted_text[key] = value_str; last_end = match.end()
        if last_end < len(text_to_convert) and text_to_convert[last_end] == ',': last_end += 1
        while last_end < len(text_to_convert) and text_to_convert[last_end].isspace(): last_end +=1
    if last_end < len(text_to_convert):
        remaining_unparsed = text_to_convert[last_end:].strip()
        if remaining_unparsed:
            nfo(f"[DT.make_paired_str_dict] Final unparsed: '{remaining_unparsed[:100]}...'")
            if ":" not in remaining_unparsed and "," not in remaining_unparsed and len(remaining_unparsed.split()) < 5:
                if "Lora hashes" not in converted_text and "Version" not in converted_text : converted_text["Uncategorized Suffix"] = remaining_unparsed
    return converted_text

def _populate_ui_from_vendored_reader(reader_instance, ui_dict_to_update: dict):
    # Ensure BaseFormat.Status.READ_SUCCESS is correctly referenced
    # This depends on whether the real or dummy BaseFormat is in scope.
    # The 'BaseFormat' variable will point to the correct one (real or dummy).
    current_base_format_status_class = getattr(BaseFormat, 'Status', None)
    if not current_base_format_status_class:
        nfo("[DT._populate_ui] CRITICAL: BaseFormat.Status not found.")
        return
    expected_read_success_status = getattr(current_base_format_status_class, 'READ_SUCCESS', object())

    if not (reader_instance and hasattr(reader_instance, 'status') and \
            reader_instance.status == expected_read_success_status and \
            hasattr(reader_instance, 'tool') and reader_instance.tool):
        status_val = getattr(reader_instance, 'status', 'N/A')
        nfo(f"[DT._populate_ui] Pre-condition not met. Reader status: {status_val}, Expected: READ_SUCCESS ({expected_read_success_status})")
        return

    nfo(f"[DT._populate_ui] Populating UI from vendored SDPR. Tool: {reader_instance.tool}")

    temp_prompt_data = ui_dict_to_update.get(UpField.PROMPT.value, {}) # Use .value for Enum key
    if reader_instance.positive: temp_prompt_data["Positive"] = str(reader_instance.positive)
    if reader_instance.negative: temp_prompt_data["Negative"] = str(reader_instance.negative)
    if reader_instance.is_sdxl:
        if reader_instance.positive_sdxl: temp_prompt_data["Positive SDXL"] = reader_instance.positive_sdxl
        if reader_instance.negative_sdxl: temp_prompt_data["Negative SDXL"] = reader_instance.negative_sdxl
    if temp_prompt_data: ui_dict_to_update[UpField.PROMPT.value] = temp_prompt_data

    temp_gen_data = ui_dict_to_update.get(DownField.GENERATION_DATA.value, {}) # Use .value
    if reader_instance.parameter:
        for key, value in reader_instance.parameter.items():
            if value and value != PARAMETER_PLACEHOLDER: # PARAMETER_PLACEHOLDER is already a string
                display_key = key.replace("_", " ").capitalize()
                temp_gen_data[display_key] = str(value)

    if reader_instance.width and str(reader_instance.width) != "0": temp_gen_data["Width"] = str(reader_instance.width)
    if reader_instance.height and str(reader_instance.height) != "0": temp_gen_data["Height"] = str(reader_instance.height)

    setting_display_val = reader_instance.setting
    if setting_display_val:
        current_tool = reader_instance.tool
        if any(t in current_tool for t in ["A1111", "Forge", "SD.Next"]):
            additional_settings = make_paired_str_dict(str(setting_display_val))
            for key_add, value_add in additional_settings.items():
                display_key_add = key_add.replace("_", " ").capitalize()
                if display_key_add not in temp_gen_data or temp_gen_data.get(display_key_add) in [None, "None", PARAMETER_PLACEHOLDER, ""]:
                    temp_gen_data[display_key_add] = str(value_add)
        elif current_tool != "Unknown":
             temp_gen_data["Tool Specific Data Block"] = str(setting_display_val)

    if temp_gen_data: ui_dict_to_update[DownField.GENERATION_DATA.value] = temp_gen_data # Use .value

    if reader_instance.raw: ui_dict_to_update[DownField.RAW_DATA.value] = str(reader_instance.raw) # Use .value

    if reader_instance.tool and reader_instance.tool != "Unknown":
        if UpField.METADATA.value not in ui_dict_to_update: ui_dict_to_update[UpField.METADATA.value] = {} # Use .value
        ui_dict_to_update[UpField.METADATA.value]["Detected Tool"] = reader_instance.tool

def process_pyexiv2_data(pyexiv2_header_data: dict, ai_tool_parsed: bool = False) -> dict:
    final_ui_meta = {}
    if not pyexiv2_header_data: return final_ui_meta
    exif_data = pyexiv2_header_data.get("EXIF", {})
    if exif_data:
        displayable_exif = {}
        if 'Exif.Image.Make' in exif_data: displayable_exif['Camera Make'] = str(exif_data['Exif.Image.Make'])
        if 'Exif.Image.Model' in exif_data: displayable_exif['Camera Model'] = str(exif_data['Exif.Image.Model'])
        if 'Exif.Photo.DateTimeOriginal' in exif_data: displayable_exif['Date Taken'] = str(exif_data['Exif.Photo.DateTimeOriginal'])
        if 'Exif.Photo.UserComment' in exif_data and not ai_tool_parsed:
            uc_val = exif_data['Exif.Photo.UserComment']
            uc_text_for_display = ""
            if isinstance(uc_val, bytes):
                if uc_val.startswith(b'ASCII\x00\x00\x00'): uc_text_for_display = uc_val[8:].decode('ascii', 'replace')
                elif uc_val.startswith(b'UNICODE\x00'): uc_text_for_display = uc_val[8:].decode('utf-16', 'replace')
                else:
                    try: uc_text_for_display = uc_val.decode('utf-8', 'replace')
                    except: uc_text_for_display = f"<bytes len {len(uc_val)}>"
            elif isinstance(uc_val, str): uc_text_for_display = uc_val
            cleaned_uc_display = uc_text_for_display.strip('\x00 ').strip()
            if cleaned_uc_display: displayable_exif['UserComment (Std.)'] = cleaned_uc_display
        if displayable_exif: final_ui_meta[DownField.EXIF.value] = displayable_exif # Use .value

    xmp_data = pyexiv2_header_data.get("XMP", {})
    if xmp_data:
        displayable_xmp = {}
        if xmp_data.get('Xmp.dc.creator'):
            creator = xmp_data['Xmp.dc.creator']
            displayable_xmp['Artist'] = ", ".join(creator) if isinstance(creator, list) else str(creator)
        if xmp_data.get('Xmp.dc.description'):
            desc_val = xmp_data['Xmp.dc.description']
            desc_text = desc_val.get('x-default', str(desc_val)) if isinstance(desc_val, dict) else str(desc_val)
            if not ai_tool_parsed or len(desc_text) < 300:
                 displayable_xmp['Description'] = desc_text
            elif ai_tool_parsed:
                 displayable_xmp['Description (XMP)'] = f"Exists (length {len(desc_text)})"
        if xmp_data.get('Xmp.photoshop.DateCreated'):
             displayable_xmp['Date Created (XMP)'] = str(xmp_data['Xmp.photoshop.DateCreated'])
        if displayable_xmp:
            if UpField.TAGS.value not in final_ui_meta: final_ui_meta[UpField.TAGS.value] = {} # Use .value
            final_ui_meta[UpField.TAGS.value].update(displayable_xmp) # Use .value

    iptc_data = pyexiv2_header_data.get("IPTC", {})
    if iptc_data:
        displayable_iptc = {}
        if iptc_data.get('Iptc.Application2.Keywords'):
            keywords = iptc_data['Iptc.Application2.Keywords']
            displayable_iptc['Keywords (IPTC)'] = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
        if iptc_data.get('Iptc.Application2.Caption'):
            displayable_iptc['Caption (IPTC)'] = str(iptc_data['Iptc.Application2.Caption'])
        if displayable_iptc:
            if UpField.TAGS.value not in final_ui_meta: final_ui_meta[UpField.TAGS.value] = {} # Use .value
            final_ui_meta[UpField.TAGS.value].update(displayable_iptc) # Use .value
    return final_ui_meta

# --- Main Parsing Function ---
def parse_metadata(file_path_named: str) -> dict:
    final_ui_dict = {}
    path_obj = Path(file_path_named)
    file_ext_lower = path_obj.suffix.lower()
    is_txt_file = file_ext_lower == ".txt"
    potential_ai_parsed = False

    # --- Define placeholder_key_str using EmptyField.PLACEHOLDER.value ---
    # This assumes EmptyField.PLACEHOLDER is a valid Enum member with a .value attribute
    # The debug prints at the module level should help verify this.
    placeholder_key_str: str
    try:
        placeholder_key_str = EmptyField.PLACEHOLDER.value
    except AttributeError:
        # Fallback if EmptyField.PLACEHOLDER is not an Enum or .value is missing
        # This case should be diagnosed by the module-level debug prints
        nfo("CRITICAL [DT.metadata_parser]: EmptyField.PLACEHOLDER.value is not accessible. Using fallback key.")
        placeholder_key_str = "metadata_placeholder_key_fallback" # Define a raw string fallback

    nfo(f"[DT.metadata_parser]: >>> ENTERING parse_metadata for: {file_path_named}")

    # --- Primary Parsing: Use VENDORED ImageDataReader ---
    if VENDORED_SDPR_OK:
        vendored_reader_instance = None
        try:
            nfo(f"[DT.metadata_parser]: Attempting to init VENDORED ImageDataReader (is_txt: {is_txt_file})")
            if is_txt_file:
                with open(file_path_named, "r", encoding="utf-8", errors="replace") as f_obj:
                    vendored_reader_instance = ImageDataReader(f_obj, is_txt=True)
            else:
                vendored_reader_instance = ImageDataReader(file_path_named)

            if vendored_reader_instance:
                status_obj = getattr(vendored_reader_instance, 'status', None)

                # --- MODIFIED SECTION for Error 1 (NameError: DummyBaseFormat) ---
                # BaseFormat refers to the real one if VENDORED_SDPR_OK is True.
                # It should have a 'Status' attribute.
                status_class_from_real_baseformat = getattr(BaseFormat, 'Status', None)
                vendored_success_status = object() # Default to a unique object that won't match

                if status_class_from_real_baseformat:
                    vendored_success_status = getattr(status_class_from_real_baseformat, 'READ_SUCCESS', object())
                    if vendored_success_status is object(): # Check if getattr defaulted
                        nfo(f"WARNING [DT.metadata_parser]: Real BaseFormat.Status does not have 'READ_SUCCESS'.")
                else:
                    nfo(f"WARNING [DT.metadata_parser]: Real BaseFormat from vendored_sdpr does not have a 'Status' attribute.")
                # --- END MODIFIED SECTION ---

                status_name = status_obj.name if status_obj and hasattr(status_obj, 'name') else 'N/A'
                tool_name = getattr(vendored_reader_instance, 'tool', 'N/A')

                nfo(f"[DT.metadata_parser]: VENDORED ImageDataReader init. Status: {status_name}, Tool: {tool_name}")

                if status_obj == vendored_success_status and tool_name and tool_name != "Unknown":
                    nfo(f"VENDORED SDPR components parsed successfully. Tool: {tool_name}")
                    _populate_ui_from_vendored_reader(vendored_reader_instance, final_ui_dict)
                    potential_ai_parsed = True
                else:
                    nfo(f"Vendored SDPR ImageDataReader did not fully parse or identify AI tool. Status: {status_name}, Tool: {tool_name}")
            else:
                nfo("Vendored ImageDataReader instantiation returned None (unexpected).")

        except FileNotFoundError:
            nfo(f"File not found by VENDORED ImageDataReader: {file_path_named}")
            if is_txt_file: return {placeholder_key_str: {"Error": "Text file not found."}}
        except Exception as e_vsdpr:
            nfo(f"Error with VENDORED ImageDataReader or its parsers: {e_vsdpr}")
            traceback.print_exc() # This will show the A1111 width error if it occurs here
    else:
        nfo("[DT.metadata_parser]: VENDORED SDPR components NOT LOADED (initial import error). Relying on pyexiv2 only for standard EXIF/XMP.")

    # --- Standard EXIF/XMP/IPTC via pyexiv2 ---
    if not is_txt_file:
        std_reader = MetadataFileReader()
        pyexiv2_raw_data = None

        if file_ext_lower.endswith((".jpg", ".jpeg", ".webp")):
            pyexiv2_raw_data = std_reader.read_jpg_header_pyexiv2(file_path_named)
        elif file_ext_lower.endswith(".png"):
            pyexiv2_raw_data = std_reader.read_png_header_pyexiv2(file_path_named)

        if pyexiv2_raw_data:
            standard_photo_meta = process_pyexiv2_data(pyexiv2_raw_data, ai_tool_parsed=potential_ai_parsed)
            if standard_photo_meta:
                for key, value in standard_photo_meta.items():
                    # Ensure 'key' is a string if it comes from Enum.value
                    key_str = str(key) # Should already be a string from .value in process_pyexiv2_data
                    if key_str not in final_ui_dict:
                        final_ui_dict[key_str] = value
                    elif isinstance(final_ui_dict.get(key_str), dict) and isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if sub_key not in final_ui_dict[key_str]:
                                final_ui_dict[key_str][sub_key] = sub_value
                if not potential_ai_parsed and DownField.EXIF.value in final_ui_dict :
                    nfo("Displayed standard EXIF/XMP data (via pyexiv2).")
                elif DownField.EXIF.value in final_ui_dict or UpField.TAGS.value in final_ui_dict:
                    nfo("Added standard EXIF/XMP data alongside AI data (if any).")

            elif not potential_ai_parsed and not final_ui_dict.get(placeholder_key_str):
                final_ui_dict[placeholder_key_str] = {"Info": "Standard image, but no processable EXIF/XMP fields found by pyexiv2."}
        elif not potential_ai_parsed and not final_ui_dict.get(placeholder_key_str):
             final_ui_dict[placeholder_key_str] = {"Info": "Standard image, no EXIF/XMP block found by pyexiv2."}

    # --- Final check for empty results ---
    if not final_ui_dict:
        if not (placeholder_key_str in final_ui_dict and "Error" in final_ui_dict.get(placeholder_key_str, {})):
            final_ui_dict[placeholder_key_str] = {"Error": "No processable metadata found after all attempts."}
        nfo(f"Failed to find/load any metadata for file: {file_path_named}")

    nfo(f"[DT.metadata_parser]: <<< EXITING parse_metadata. Returning keys: {list(final_ui_dict.keys())}")
    return final_ui_dict