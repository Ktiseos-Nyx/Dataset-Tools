# dataset_tools/metadata_parser.py

import re 
import json 
from pathlib import Path 
import importlib 
import traceback 

from .correct_types import UpField, DownField, EmptyField 
from .logger import info_monitor as nfo

# --- Imports for sd-prompt-reader ---
try:
    from sd_prompt_reader.image_data_reader import ImageDataReader
    from sd_prompt_reader.format import BaseFormat, A1111 as SDPR_A1111Parser, ComfyUI as SDPR_ComfyUIParser
    from sd_prompt_reader.constants import PARAMETER_PLACEHOLDER as SDPR_PARAMETER_PLACEHOLDER
    SDPR_AVAILABLE = True
except ImportError as e:
    nfo(f"WARNING: sd-prompt-reader library not found or could not import components: {e}. AI metadata parsing will be limited.")
    SDPR_AVAILABLE = False
    class ImageDataReader:
        def __init__(self, file_path_or_obj, is_txt=False):
            self.status = None; self.tool = None; self.format = None; self.positive = ""; self.negative = ""
            self.is_sdxl = False; self.positive_sdxl = {}; self.negative_sdxl = {}; self.parameter = {}
            self.width = "0"; self.height = "0"; self.setting = ""; self.raw = ""
            nfo("Using dummy ImageDataReader as sd-prompt-reader is not available.")
    class BaseFormat:
        class Status: UNREAD=1; READ_SUCCESS=2; FORMAT_ERROR=3; COMFYUI_ERROR=4
        PARAMETER_PLACEHOLDER = "                    "
    class SDPR_A1111Parser:
        def __init__(self, raw, width=0, height=0): self.status = BaseFormat.Status.FORMAT_ERROR; self.raw=str(raw) if raw else ""; self.positive=""; self.negative=""; self.parameter={}; self.setting=""; self.width=str(width); self.height=str(height); self.is_sdxl=False; self.positive_sdxl={}; self.negative_sdxl={}
        def parse(self): return self.status # Make sure parse exists and returns a status
    class SDPR_ComfyUIParser:
        def __init__(self, info, width=0, height=0): self.status = BaseFormat.Status.FORMAT_ERROR; self.raw=str(info) if info else ""; self.positive=""; self.negative=""; self.parameter={}; self.setting=""; self.width=str(width); self.height=str(height); self.is_sdxl=False; self.positive_sdxl={}; self.negative_sdxl={}
        def parse(self): return self.status # Make sure parse exists and returns a status
    SDPR_PARAMETER_PLACEHOLDER = "                    "

# --- Helper Functions ---

def make_paired_str_dict(text_to_convert: str) -> dict:
    if not text_to_convert or not isinstance(text_to_convert, str):
        return {}
    
    # print(f"DEBUG [make_paired_str_dict] INPUT (first 150): '{text_to_convert[:150]}'") # Optional
    converted_text = {}
    pattern = re.compile(r"""
        ([\w\s().\-/]+?)        # Key
        :\s*                   # Colon and optional space
        (                      # Start of Value group
            "(?:\\.|[^"\\])*"  # Double-quoted string
            |
            '(?:\\.|[^'\\])*'  # Single-quoted string
            |
            (?:.(?!(?:,\s*[\w\s().\-/]+?:)))*? # Unquoted value
        )                      # End of Value group
    """, re.VERBOSE)

    last_end = 0
    for match in pattern.finditer(text_to_convert):
        if match.start() > last_end:
            unparsed_gap = text_to_convert[last_end:match.start()].strip(" ,")
            if unparsed_gap and unparsed_gap not in [",", ":"]:
                nfo(f"[make_paired_str_dict] Unparsed gap before '{match.group(1)[:20]}...': '{unparsed_gap[:50]}...'")
        
        key = match.group(1).strip()
        value_str = match.group(2).strip()

        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            value_str = value_str[1:-1]
        
        converted_text[key] = value_str
        last_end = match.end()
        if last_end < len(text_to_convert) and text_to_convert[last_end] == ',':
            last_end += 1
        while last_end < len(text_to_convert) and text_to_convert[last_end].isspace():
            last_end +=1
            
    if last_end < len(text_to_convert):
        remaining_unparsed = text_to_convert[last_end:].strip()
        if remaining_unparsed:
             nfo(f"[make_paired_str_dict] Final unparsed part: '{remaining_unparsed[:100]}...'")
             if ":" not in remaining_unparsed and "," not in remaining_unparsed and len(remaining_unparsed.split()) < 5:
                 if "Lora hashes" not in converted_text and "Version" not in converted_text : 
                    converted_text["Uncategorized Suffix"] = remaining_unparsed
    # print(f"DEBUG [make_paired_str_dict] OUTPUT: {converted_text}") # Optional
    return converted_text

def decode_exif_user_comment_to_json_string(uc_input: bytes | str) -> str | None:
    print(f"DEBUG [decode_exif_user_comment_to_json_string]: Input type: {type(uc_input)}, value (first 100): {repr(uc_input[:100]) if isinstance(uc_input, bytes) else repr(uc_input[:100])}")

    if isinstance(uc_input, str):
        print(f"DEBUG [decode_exif_user_comment_to_json_string]: Input is string. Attempting Civitai-style mojibake reversal.")
        prefix_pattern = r'^charset\s*=\s*["\']?(UNICODE|UTF-16|UTF-16LE)["\']?\s*'
        match = re.match(prefix_pattern, uc_input, re.IGNORECASE)
        data_to_fix = uc_input
        prefix_was_stripped = False
        if match:
            prefix_len = len(match.group(0))
            data_to_fix = uc_input[prefix_len:]
            prefix_was_stripped = True
            print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Stripped prefix. Remaining (first 50): '{data_to_fix[:50]}'")
        
        needs_mojibake_reversal = False
        if data_to_fix: 
            if (prefix_was_stripped and not data_to_fix.strip().startswith('{')) or \
               (not prefix_was_stripped and ('笀' in data_to_fix or '∀' in data_to_fix) and not data_to_fix.strip().startswith('{')):
                needs_mojibake_reversal = True
        
        if needs_mojibake_reversal:
            print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Attempting mojibake char reversal on '{data_to_fix[:50]}...'")
            try:
                if not data_to_fix:
                    print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Data to fix is empty.")
                else:
                    byte_list = []
                    print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Reconstructing bytes from data_to_fix (first 10 chars): '{data_to_fix[:10]}'")
                    for i, char_from_mojibake in enumerate(data_to_fix):
                        if i < 10: 
                            print(f"  Char {i}: '{char_from_mojibake}' (U+{ord(char_from_mojibake):04X})")
                        codepoint_val = ord(char_from_mojibake)
                        byte1 = (codepoint_val >> 8) & 0xFF
                        byte2 = codepoint_val & 0xFF
                        byte_list.append(byte1)
                        byte_list.append(byte2)
                        if i < 10:
                             print(f"    -> bytes: 0x{byte1:02X} 0x{byte2:02X}")
                    
                    recovered_bytes = bytes(byte_list)
                    print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Reconstructed recovered_bytes (first 20 bytes hex): {recovered_bytes[:20].hex()}")
                    correct_json_string = recovered_bytes.decode('utf-16le', errors='strict')
                    print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Mojibake reversed. Decoded string (first 50, repr): {repr(correct_json_string[:50])}")
                    if not correct_json_string.strip().startswith('{'):
                        print(f"CRITICAL DEBUG: correct_json_string does NOT start with '{{'. It starts with (repr): {repr(correct_json_string[:10])}")
                    json.loads(correct_json_string) 
                    print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Successfully validated as JSON. Returning string.")
                    return correct_json_string
            except UnicodeDecodeError as ude: print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: UnicodeDecodeError during mojibake reversal: {ude}. Fallback.")
            except json.JSONDecodeError as jde: print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: JSONDecodeError after mojibake reversal: {jde}. Fallback.")
            except Exception as e_civitai: print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Mojibake reversal/validation failed with general error: {e_civitai}. Fallback.")
        
        elif data_to_fix and data_to_fix.strip().startswith('{'): 
            print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Data looks like JSON after prefix strip (or no prefix/mojibake). Validating '{data_to_fix.strip()[:50]}...'")
            try:
                clean_data_to_fix = data_to_fix.strip('\x00').strip()
                json.loads(clean_data_to_fix)
                print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Valid JSON after prefix strip. Returning string.")
                return clean_data_to_fix
            except json.JSONDecodeError as e_direct: print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Looked JSON-like but failed parse: {e_direct}. Fallback.")

        print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style logic failed/skipped or data not suitable. Trying generic JSON search in original string input: '{uc_input[:50]}...'")
        json_start_index = uc_input.find('{')
        json_end_index = uc_input.rfind('}') 
        if json_start_index != -1 and json_end_index > json_start_index:
            potential_json = uc_input[json_start_index : json_end_index + 1].strip('\x00').strip()
            try:
                json.loads(potential_json)
                print(f"DEBUG [decode_exif_user_comment_to_json_string]: Generic string search: Found valid JSON: {potential_json[:100]}...")
                return potential_json
            except json.JSONDecodeError: print(f"DEBUG [decode_exif_user_comment_to_json_string]: Generic string search: Looked JSON-like but failed parse.")
        
        print(f"DEBUG [decode_exif_user_comment_to_json_string]: All string processing attempts failed for UserComment.")
        return None

    if not isinstance(uc_input, bytes):
        print(f"DEBUG [decode_exif_user_comment_to_json_string]: Input not string or bytes (logic error or unexpected input), returning None.")
        return None

    print(f"DEBUG [decode_exif_user_comment_to_json_string]: Input is bytes. Processing byte prefixes.")
    payload_to_decode = None
    encodings_to_try = []
    prefix_pattern_bytes_str = r'^charset\s*=\s*["\']?(UNICODE|UTF-16|UTF-16LE)["\']?\s*'
    if uc_input.startswith(b'UNICODE\x00'):
        payload_to_decode = uc_input[8:]
        encodings_to_try = ['utf-16-le', 'utf-16-be', 'utf-16']
        print(f"DEBUG [decode_exif_user_comment_to_json_string]: Bytes: Detected b'UNICODE\\x00' prefix. Payload (first 30): {repr(payload_to_decode[:30])}")
    elif uc_input.startswith(b'ASCII\x00\x00\x00'):
        payload_to_decode = uc_input[8:]
        encodings_to_try = ['ascii', 'utf-8']
        print(f"DEBUG [decode_exif_user_comment_to_json_string]: Bytes: Detected b'ASCII\\x00\\x00\\x00' prefix.")
    else: 
        payload_to_decode = uc_input
        encodings_to_try = ['utf-8', 'utf-16-le', 'utf-16-be', 'latin-1']
        print(f"DEBUG [decode_exif_user_comment_to_json_string]: Bytes: No known 8-byte EXIF prefix. Trying direct decodes on full input (len {len(payload_to_decode)}).")

    if payload_to_decode is not None:
        for enc in encodings_to_try:
            try:
                decoded_str_from_bytes = payload_to_decode.decode(enc, errors='strict').strip('\x00').strip()
                print(f"DEBUG [decode_exif_user_comment_to_json_string]: Bytes: Trying to decode payload with '{enc}'. Result (first 100): '{decoded_str_from_bytes[:100]}...'")
                actual_json_part = decoded_str_from_bytes
                match_bytes_prefix = re.match(prefix_pattern_bytes_str, actual_json_part, re.IGNORECASE)
                if match_bytes_prefix:
                    actual_json_part = actual_json_part[len(match_bytes_prefix.group(0)):].strip()
                    print(f"DEBUG [decode_exif_user_comment_to_json_string]: Bytes: Stripped 'charset=Unicode' from decoded string. Remaining: '{actual_json_part[:50]}'")
                if actual_json_part.startswith('{') and actual_json_part.endswith('}'):
                    try:
                        json.loads(actual_json_part)
                        print(f"DEBUG [decode_exif_user_comment_to_json_string]: Bytes: Successfully validated as JSON with encoding '{enc}'. Returning string.")
                        return actual_json_part
                    except json.JSONDecodeError as je: print(f"DEBUG [decode_exif_user_comment_to_json_string]: Bytes: Decoded with '{enc}', looked JSON-like, but failed json.loads(): {je}")
            except UnicodeDecodeError: print(f"DEBUG [decode_exif_user_comment_to_json_string]: Bytes: Failed UnicodeDecodeError with '{enc}'.")
    print(f"DEBUG [decode_exif_user_comment_to_json_string]: Failed all decoding attempts for UserComment (bytes path).")
    return None

def _populate_ui_dict_from_sdpr_parser(parser_instance, ui_dict_to_update: dict, tool_name_override=None):
    """
    Helper to translate sd-prompt-reader parser output into the final_ui_dict structure.
    Modifies ui_dict_to_update in place.
    """
    # print(f"DEBUG [_populate_ui_dict_from_sdpr_parser] Populating from parser tool: {getattr(parser_instance, 'tool', 'Unknown')}, override: {tool_name_override}")
    temp_prompt_data = ui_dict_to_update.get(UpField.PROMPT, {})
    if parser_instance.positive: temp_prompt_data["Positive"] = str(parser_instance.positive)
    if parser_instance.negative: temp_prompt_data["Negative"] = str(parser_instance.negative)
    if getattr(parser_instance, 'is_sdxl', False): # Check if is_sdxl attr exists
        if getattr(parser_instance, 'positive_sdxl', None): temp_prompt_data["Positive SDXL"] = parser_instance.positive_sdxl
        if getattr(parser_instance, 'negative_sdxl', None): temp_prompt_data["Negative SDXL"] = parser_instance.negative_sdxl
    if temp_prompt_data: ui_dict_to_update[UpField.PROMPT] = temp_prompt_data

    temp_gen_data = ui_dict_to_update.get(DownField.GENERATION_DATA, {})
    if hasattr(parser_instance, 'parameter'): # Check if parameter attr exists
        for key, value in parser_instance.parameter.items():
            if value and value != SDPR_PARAMETER_PLACEHOLDER:
                display_key = key.replace("_", " ").capitalize()
                temp_gen_data[display_key] = str(value)
    
    if getattr(parser_instance, 'width', "0") and str(parser_instance.width) != "0": temp_gen_data["Width"] = str(parser_instance.width)
    if getattr(parser_instance, 'height', "0") and str(parser_instance.height) != "0": temp_gen_data["Height"] = str(parser_instance.height)

    if getattr(parser_instance, 'setting', ""):
        effective_tool = tool_name_override or (str(parser_instance.tool) if hasattr(parser_instance, 'tool') else None)
        if effective_tool and any(t in effective_tool for t in ["A1111", "Forge", "SD.Next", "Easy Diffusion"]):
            additional_settings = make_paired_str_dict(str(parser_instance.setting))
            for key_add, value_add in additional_settings.items():
                display_key_add = key_add.replace("_", " ").capitalize()
                if display_key_add not in temp_gen_data or \
                   temp_gen_data.get(display_key_add) in [None, "None", SDPR_PARAMETER_PLACEHOLDER, ""]:
                    temp_gen_data[display_key_add] = str(value_add)
        else: 
            temp_gen_data["Tool Specific Settings"] = str(parser_instance.setting) # For ComfyUI, etc.
    if temp_gen_data: ui_dict_to_update[DownField.GENERATION_DATA] = temp_gen_data
    
    if getattr(parser_instance, 'raw', ""): ui_dict_to_update[DownField.RAW_DATA] = str(parser_instance.raw)
    
    detected_tool_str = tool_name_override or (str(parser_instance.tool) if hasattr(parser_instance, 'tool') else "Unknown")
    if detected_tool_str and detected_tool_str != "Unknown":
        if UpField.METADATA not in ui_dict_to_update: ui_dict_to_update[UpField.METADATA] = {}
        ui_dict_to_update[UpField.METADATA]["Detected Tool"] = detected_tool_str
    # print(f"DEBUG [_populate_ui_dict_from_sdpr_parser] Resulting dict keys: {list(ui_dict_to_update.keys())}")


def process_pyexiv2_data(pyexiv2_header_data: dict) -> dict:
    final_ui_meta = {}
    if not pyexiv2_header_data: return final_ui_meta
    exif_data = pyexiv2_header_data.get("EXIF", {})
    if exif_data:
        displayable_exif = {}
        if 'Exif.Image.Make' in exif_data: displayable_exif['Camera Make'] = str(exif_data['Exif.Image.Make'])
        if 'Exif.Image.Model' in exif_data: displayable_exif['Camera Model'] = str(exif_data['Exif.Image.Model'])
        if 'Exif.Photo.DateTimeOriginal' in exif_data: displayable_exif['Date Taken'] = str(exif_data['Exif.Photo.DateTimeOriginal'])
        if 'Exif.Photo.FNumber' in exif_data: displayable_exif['F-Number'] = str(exif_data['Exif.Photo.FNumber'])
        if 'Exif.Photo.ExposureTime' in exif_data: displayable_exif['Exposure Time'] = str(exif_data['Exif.Photo.ExposureTime'])
        if 'Exif.Photo.ISOSpeedRatings' in exif_data: displayable_exif['ISO'] = str(exif_data['Exif.Photo.ISOSpeedRatings'])
        if 'Exif.Photo.UserComment' in exif_data: # This is for displaying UserComment if it wasn't parsed as AI
            uc_val = exif_data['Exif.Photo.UserComment']
            uc_text_for_display = ""
            if isinstance(uc_val, bytes):
                if uc_val.startswith(b'ASCII\x00\x00\x00'): uc_text_for_display = uc_val[8:].decode('ascii', 'replace')
                elif uc_val.startswith(b'UNICODE\x00'): uc_text_for_display = uc_val[8:].decode('utf-16', 'replace')
                else: 
                    try: uc_text_for_display = uc_val.decode('utf-8', 'replace')
                    except: uc_text_for_display = str(uc_val)
            elif isinstance(uc_val, str): uc_text_for_display = uc_val
            cleaned_uc_display = uc_text_for_display.strip('\x00 ').strip()
            if cleaned_uc_display: displayable_exif['UserComment (Std.)'] = cleaned_uc_display
        if displayable_exif: final_ui_meta[DownField.EXIF] = displayable_exif
    
    xmp_data = pyexiv2_header_data.get("XMP", {})
    if xmp_data:
        displayable_xmp = {}
        if xmp_data.get('Xmp.dc.creator'):
            creator = xmp_data['Xmp.dc.creator']
            displayable_xmp['Artist'] = ", ".join(creator) if isinstance(creator, list) else str(creator)
        if xmp_data.get('Xmp.dc.description'): # A1111 sometimes puts parameters here for JPEGs
            desc_val = xmp_data['Xmp.dc.description']
            desc_text = desc_val.get('x-default', str(desc_val)) if isinstance(desc_val, dict) else str(desc_val)
            displayable_xmp['Description'] = desc_text
        if xmp_data.get('Xmp.photoshop.DateCreated'):
             displayable_xmp['Date Created (XMP)'] = str(xmp_data['Xmp.photoshop.DateCreated'])
        if displayable_xmp: 
            if UpField.TAGS not in final_ui_meta: final_ui_meta[UpField.TAGS] = {}
            final_ui_meta[UpField.TAGS].update(displayable_xmp)
            
    iptc_data = pyexiv2_header_data.get("IPTC", {})
    if iptc_data:
        displayable_iptc = {}
        if iptc_data.get('Iptc.Application2.Keywords'):
            keywords = iptc_data['Iptc.Application2.Keywords']
            displayable_iptc['Keywords (IPTC)'] = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
        if iptc_data.get('Iptc.Application2.Caption'):
            displayable_iptc['Caption (IPTC)'] = str(iptc_data['Iptc.Application2.Caption'])
        if displayable_iptc:
            if UpField.TAGS not in final_ui_meta: final_ui_meta[UpField.TAGS] = {}
            final_ui_meta[UpField.TAGS].update(displayable_iptc)
    return final_ui_meta

# --- Main Parsing Function ---
def parse_metadata(file_path_named: str) -> dict:
    final_ui_dict = {}
    path_obj = Path(file_path_named)
    file_ext_lower = path_obj.suffix.lower()
    is_txt_file = file_ext_lower == ".txt"

    print(f"\nDEBUG: >>> ENTERING parse_metadata for: {file_path_named}")

    data_reader = None 
    pyexiv2_raw_data = None 
    potential_ai_parsed = False 

    if SDPR_AVAILABLE:
        try:
            print(f"DEBUG: Attempting to init ImageDataReader (is_txt: {is_txt_file})")
            if is_txt_file:
                with open(file_path_named, "r", encoding="utf-8", errors="replace") as f_obj:
                    data_reader = ImageDataReader(f_obj, is_txt=True)
            else:
                data_reader = ImageDataReader(file_path_named)
            
            print(f"DEBUG: ImageDataReader initialized.")
            if data_reader:
                status_name = data_reader.status.name if data_reader.status and hasattr(data_reader.status, 'name') else 'N/A'
                print(f"    Status: {status_name}")
                print(f"    Tool: {data_reader.tool}")
                print(f"    Format: {data_reader.format}")
                if not is_txt_file and hasattr(data_reader, '_info') and data_reader._info:
                     print(f"    SDPR _info keys: {list(data_reader._info.keys())}")
                     if "parameters" in data_reader._info: print(f"    _info['parameters'][:100]: {str(data_reader._info['parameters'])[:100]}...")
                     elif "prompt" in data_reader._info: print(f"    _info['prompt'][:100]: {str(data_reader._info['prompt'])[:100]}...")
                elif is_txt_file and data_reader.raw: print(f"    SDPR raw (from TXT)[:100]: {data_reader.raw[:100]}...")

                if data_reader.status == BaseFormat.Status.READ_SUCCESS and data_reader.tool:
                    nfo(f"SDPR parsed successfully. Tool: {data_reader.tool}")
                    print(f"DEBUG: SDPR READ_SUCCESS. Tool: {data_reader.tool}")
                    _populate_ui_dict_from_sdpr_parser(data_reader, final_ui_dict) # Pass final_ui_dict to be modified
                    potential_ai_parsed = True
        except FileNotFoundError:
            nfo(f"File not found by SDPR: {file_path_named}")
            print("DEBUG: FileNotFoundError caught for ImageDataReader")
            if is_txt_file: return {EmptyField.PLACEHOLDER: {"Error": "Text file not found."}}
        except Exception as e_sdpr:
            nfo(f"Error with ImageDataReader for {file_path_named}: {e_sdpr.__class__.__name__} - {e_sdpr}")
            print(f"DEBUG: Exception during ImageDataReader processing: {e_sdpr.__class__.__name__} - {e_sdpr}")
            traceback.print_exc()
    else: 
        print("DEBUG: sd-prompt-reader not available. Skipping initial AI metadata parsing with it.")

    if not potential_ai_parsed and not is_txt_file:
        status_name_from_sdpr = data_reader.status.name if data_reader and data_reader.status and hasattr(data_reader.status, 'name') else 'N/A'
        tool_name_from_sdpr = data_reader.tool if data_reader and data_reader.tool else 'N/A'
        nfo(f"SDPR did not fully parse AI data (Tool: {tool_name_from_sdpr}, Status: {status_name_from_sdpr}). Trying pyexiv2 UserComment AI parse then standard EXIF/XMP.")
        print(f"DEBUG: SDPR did not fully parse (Tool: {tool_name_from_sdpr}, Status: {status_name_from_sdpr}). Attempting pyexiv2 UserComment AI parse then standard fallback.")
        
        from .access_disk import MetadataFileReader 
        std_reader = MetadataFileReader()
        
        if file_ext_lower.endswith((".jpg", ".jpeg", ".webp")):
            pyexiv2_raw_data = std_reader.read_jpg_header_pyexiv2(file_path_named)
        elif file_ext_lower.endswith(".png"): 
            pyexiv2_raw_data = std_reader.read_png_header_pyexiv2(file_path_named)

        if pyexiv2_raw_data:
            print(f"DEBUG: pyexiv2 fallback got data with keys: {list(pyexiv2_raw_data.keys())}")
            exif_part = pyexiv2_raw_data.get("EXIF", {}) 
            user_comment_value = exif_part.get("Exif.Photo.UserComment") if exif_part else None

            if user_comment_value:
                print(f"DEBUG: Found UserComment from pyexiv2. Type: {type(user_comment_value)}. Value (first 50): {repr(user_comment_value[:50]) if isinstance(user_comment_value, (str,bytes)) else repr(user_comment_value)}")
                json_str_from_uc = decode_exif_user_comment_to_json_string(user_comment_value)
                
                if json_str_from_uc:
                    print(f"DEBUG: Decoded UserComment (pyexiv2) to JSON string, trying AI parse: {json_str_from_uc[:150]}...")
                    if SDPR_AVAILABLE: 
                        try:
                            main_uc_json_obj = json.loads(json_str_from_uc)
                            
                            if "extraMetadata" in main_uc_json_obj and isinstance(main_uc_json_obj["extraMetadata"], str):
                                extra_meta_str = main_uc_json_obj["extraMetadata"]
                                print(f"DEBUG: Found 'extraMetadata' (is JSON string): {extra_meta_str[:100]}...")
                                try:
                                    extra_meta_dict = json.loads(extra_meta_str)
                                    print("DEBUG: Successfully parsed 'extraMetadata' string into dict.")
                                    
                                    # OPTION 1: Direct extraction from extra_meta_dict for A1111-like params
                                    temp_prompt_data = final_ui_dict.get(UpField.PROMPT, {})
                                    if extra_meta_dict.get("prompt"): temp_prompt_data["Positive"] = extra_meta_dict["prompt"]
                                    if extra_meta_dict.get("negativePrompt"): temp_prompt_data["Negative"] = extra_meta_dict["negativePrompt"]
                                    if temp_prompt_data: final_ui_dict[UpField.PROMPT] = temp_prompt_data
                                    
                                    temp_gen_data = final_ui_dict.get(DownField.GENERATION_DATA, {})
                                    if "steps" in extra_meta_dict: temp_gen_data["Steps"] = str(extra_meta_dict["steps"])
                                    if "CFG scale" in extra_meta_dict: temp_gen_data["Cfg scale"] = str(extra_meta_dict["CFG scale"]) # Civitai uses "CFG scale"
                                    elif "cfgScale" in extra_meta_dict: temp_gen_data["Cfg scale"] = str(extra_meta_dict["cfgScale"]) # Or this
                                    if "sampler" in extra_meta_dict: temp_gen_data["Sampler"] = str(extra_meta_dict["sampler"])
                                    if "seed" in extra_meta_dict: temp_gen_data["Seed"] = str(extra_meta_dict["seed"])
                                    # Add other relevant A1111-like params from extra_meta_dict
                                    if temp_gen_data: final_ui_dict[DownField.GENERATION_DATA] = temp_gen_data
                                    
                                    if UpField.METADATA not in final_ui_dict: final_ui_dict[UpField.METADATA] = {}
                                    final_ui_dict[UpField.METADATA]["Detected Tool"] = "Civitai ComfyUI (via UserComment.extraMetadata)"
                                    if DownField.RAW_DATA not in final_ui_dict: final_ui_dict[DownField.RAW_DATA] = json_str_from_uc # Store the whole workflow JSON
                                    
                                    potential_ai_parsed = True
                                    print("DEBUG: Directly extracted A1111-style params from UserComment.extraMetadata JSON.")

                                except json.JSONDecodeError as e_extra:
                                    print(f"DEBUG: Failed to parse JSON from 'extraMetadata' string: {e_extra}")
                            
                            if not potential_ai_parsed and "nodes" in main_uc_json_obj:
                                is_likely_comfy = False # Check for Comfy structure more reliably
                                first_node_key = next(iter(main_uc_json_obj.get("nodes", {})), None)
                                if first_node_key and isinstance(main_uc_json_obj["nodes"].get(first_node_key), dict) and \
                                   "class_type" in main_uc_json_obj["nodes"][first_node_key]:
                                    is_likely_comfy = True
                                
                                if is_likely_comfy:
                                    print("DEBUG: UserComment JSON looks like ComfyUI graph. Trying SDPR_ComfyUIParser.")
                                    parser_comfy_uc = SDPR_ComfyUIParser(info=main_uc_json_obj)
                                    status = parser_comfy_uc.parse()
                                    if status == BaseFormat.Status.READ_SUCCESS:
                                        print("DEBUG: UserComment parsed as ComfyUI graph by SDPR_ComfyUIParser.")
                                        _populate_ui_dict_from_sdpr_parser(parser_comfy_uc, final_ui_dict, tool_name_override="Civitai/ComfyUI (UC graph)")
                                        potential_ai_parsed = True
                        except json.JSONDecodeError as e_json_load: print(f"DEBUG: UserComment (pyexiv2) decoded to string, but it's not valid JSON: {e_json_load}")
                        except Exception as e_uc_ai: print(f"DEBUG: Error parsing AI data from UserComment (pyexiv2 path with SDPR): {e_uc_ai}"); traceback.print_exc()
                    else: # SDPR Not Available, but we have a JSON string
                        print("DEBUG: SDPR not available. Decoded UserComment to JSON, storing raw and trying direct 'extraMetadata' parse.")
                        try:
                            main_uc_json_obj = json.loads(json_str_from_uc)
                            if "extraMetadata" in main_uc_json_obj and isinstance(main_uc_json_obj["extraMetadata"], str):
                                extra_meta_dict = json.loads(main_uc_json_obj["extraMetadata"])
                                temp_prompt_data = final_ui_dict.get(UpField.PROMPT, {})
                                if extra_meta_dict.get("prompt"): temp_prompt_data["Positive"] = extra_meta_dict["prompt"]
                                if extra_meta_dict.get("negativePrompt"): temp_prompt_data["Negative"] = extra_meta_dict["negativePrompt"]
                                if temp_prompt_data: final_ui_dict[UpField.PROMPT] = temp_prompt_data
                                temp_gen_data = final_ui_dict.get(DownField.GENERATION_DATA, {})
                                if "steps" in extra_meta_dict: temp_gen_data["Steps"] = str(extra_meta_dict["steps"])
                                if "CFG scale" in extra_meta_dict: temp_gen_data["Cfg scale"] = str(extra_meta_dict["CFG scale"])
                                elif "cfgScale" in extra_meta_dict: temp_gen_data["Cfg scale"] = str(extra_meta_dict["cfgScale"])
                                if "sampler" in extra_meta_dict: temp_gen_data["Sampler"] = str(extra_meta_dict["sampler"])
                                if "seed" in extra_meta_dict: temp_gen_data["Seed"] = str(extra_meta_dict["seed"])
                                if temp_gen_data: final_ui_dict[DownField.GENERATION_DATA] = temp_gen_data
                                print("DEBUG: Directly extracted from extraMetadata (SDPR not available path).")
                        except Exception as e_direct_extract:
                            print(f"DEBUG: Failed direct extraction from extraMetadata (SDPR not available path): {e_direct_extract}")
                        
                        if DownField.RAW_DATA not in final_ui_dict: final_ui_dict[DownField.RAW_DATA] = json_str_from_uc
                        if UpField.METADATA not in final_ui_dict: final_ui_dict[UpField.METADATA] = {}
                        final_ui_dict[UpField.METADATA]["Detected Tool"] = "Civitai ComfyUI (Raw UserComment JSON)"
                        potential_ai_parsed = True
            
            if potential_ai_parsed:
                nfo("AI metadata found/decoded from EXIF UserComment (via pyexiv2 fallback).")
                print("DEBUG: AI data from UserComment (pyexiv2 path) has been processed into final_ui_dict.")
            else: 
                print("DEBUG: UserComment (pyexiv2) did not yield AI data. Processing pyexiv2_raw_data for standard EXIF/XMP.")
                standard_photo_meta = process_pyexiv2_data(pyexiv2_raw_data)
                if standard_photo_meta:
                    final_ui_dict.update(standard_photo_meta) # Merge standard EXIF if AI not found
                    nfo("Displayed standard EXIF/XMP data.")
                    print("DEBUG: Populated final_ui_dict with standard EXIF/XMP.")
                elif not final_ui_dict.get(EmptyField.PLACEHOLDER):
                    final_ui_dict[EmptyField.PLACEHOLDER] = {"Info": "Standard image, but no processable EXIF/XMP fields found."}
        else: 
            print("DEBUG: pyexiv2 fallback got NO raw data (pyexiv2_raw_data is None).")
            if not final_ui_dict.get(EmptyField.PLACEHOLDER):
                final_ui_dict[EmptyField.PLACEHOLDER] = {"Info": "Standard image, no EXIF/XMP block found via pyexiv2."}
    
    elif not potential_ai_parsed and not is_txt_file and data_reader and data_reader.status != BaseFormat.Status.READ_SUCCESS : 
        status_name = data_reader.status.name if data_reader.status and hasattr(data_reader.status, 'name') else 'N/A'
        tool_name = data_reader.tool if data_reader.tool else 'N/A'
        error_message = f"Could not read AI metadata ({status_name})."
        if data_reader.tool: error_message += f" Detected tool: {tool_name}."
        if not final_ui_dict or (EmptyField.PLACEHOLDER in final_ui_dict and "Error" not in final_ui_dict[EmptyField.PLACEHOLDER]):
            final_ui_dict[EmptyField.PLACEHOLDER] = {"Error": error_message}
        if data_reader.raw and DownField.RAW_DATA not in final_ui_dict:
             final_ui_dict[DownField.RAW_DATA] = str(data_reader.raw)
        print(f"DEBUG: SDPR parsing failed (image). Status: {status_name}, Tool: {tool_name}")

    is_effectively_empty = not final_ui_dict or \
                           (len(final_ui_dict) == 1 and EmptyField.PLACEHOLDER in final_ui_dict and \
                            list(final_ui_dict[EmptyField.PLACEHOLDER].keys()) == [EmptyField.PLACEHOLDER] and \
                            final_ui_dict[EmptyField.PLACEHOLDER][EmptyField.PLACEHOLDER] == EmptyField.EMPTY)


    if is_effectively_empty and not potential_ai_parsed: 
        loggable_header_info = "Unknown header data"
        if data_reader and data_reader.raw: loggable_header_info = str(data_reader.raw)[:200]
        elif pyexiv2_raw_data: loggable_header_info = str(list(pyexiv2_raw_data.keys()) if isinstance(pyexiv2_raw_data, dict) else pyexiv2_raw_data)[:200]
        
        nfo("Failed to find/load metadata for file. Last available data: %s", loggable_header_info)
        if EmptyField.PLACEHOLDER not in final_ui_dict or list(final_ui_dict[EmptyField.PLACEHOLDER].keys()) == [EmptyField.PLACEHOLDER] : # Avoid overwriting specific errors
            final_ui_dict[EmptyField.PLACEHOLDER] = {"Error": "No processable metadata found."}
        print("DEBUG: final_ui_dict is effectively empty after all checks.")
         
    print(f"DEBUG: <<< EXITING parse_metadata. Returning keys: {list(final_ui_dict.keys())}")
    return final_ui_dict
