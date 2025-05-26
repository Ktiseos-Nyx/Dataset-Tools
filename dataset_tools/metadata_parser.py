# dataset_tools/metadata_parser.py

import re # For decode_exif_user_comment_to_json_string and make_paired_str_dict
import json # For decode_exif_user_comment_to_json_string and JSON parsing
from pathlib import Path # Used in parse_metadata
import importlib # For metadata.version if you were to move __version__ logic here (not used in snippet but keep if needed)
import traceback # For printing full tracebacks in debug prints

from .correct_types import UpField, DownField, EmptyField # Removed Ext as it's not in this version of the file
from .logger import info_monitor as nfo
# from .logger import debug_message # If you use it

# --- Imports for sd-prompt-reader ---
try:
    from sd_prompt_reader.image_data_reader import ImageDataReader
    from sd_prompt_reader.format import BaseFormat, A1111 as SDPR_A1111Parser, ComfyUI as SDPR_ComfyUIParser # Added Parsers
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
    # Add dummy SDPR parsers if they are used in the main logic when SDPR_AVAILABLE is False
    class SDPR_A1111Parser:
        def __init__(self, raw, width=0, height=0): self.status = BaseFormat.Status.FORMAT_ERROR; self.raw=str(raw) if raw else ""; self.positive=""; self.negative=""; self.parameter={}; self.setting=""; self.width=str(width); self.height=str(height); self.is_sdxl=False; self.positive_sdxl={}; self.negative_sdxl={}
        def parse(self): return self.status
    class SDPR_ComfyUIParser:
        def __init__(self, info, width=0, height=0): self.status = BaseFormat.Status.FORMAT_ERROR; self.raw=str(info) if info else ""; self.positive=""; self.negative=""; self.parameter={}; self.setting=""; self.width=str(width); self.height=str(height); self.is_sdxl=False; self.positive_sdxl={}; self.negative_sdxl={}
        def parse(self): return self.status
    SDPR_PARAMETER_PLACEHOLDER = "                    "

# --- Helper Functions ---

def make_paired_str_dict(text_to_convert: str) -> dict:
    """
    Convert an A1111-style settings string (e.g., "Steps: 20, Sampler: Euler")
    into a dictionary.
    """
    if not text_to_convert or not isinstance(text_to_convert, str):
        return {}
    
    # print(f"DEBUG [make_paired_str_dict] INPUT (first 150): '{text_to_convert[:150]}'") # Optional debug
    converted_text = {}
    # Using a more robust regex from one of the previous versions that handles quotes better
    pattern = re.compile(r"""
        ([\w\s().\-/]+?)        # Key (word chars, spaces, (), ., -, / non-greedy)
        :\s*                   # Colon and optional space
        (                      # Start of Value group
            "(?:\\.|[^"\\])*"  # Double-quoted string (handles escaped quotes within)
            |
            '(?:\\.|[^'\\])*'  # Single-quoted string (handles escaped quotes within)
            |
            (?:.(?!(?:,\s*[\w\s().\-/]+?:)))*? # Unquoted value: any char, non-greedy, stops if it sees ", Key:"
        )                      # End of Value group
    """, re.VERBOSE)

    last_end = 0
    for match in pattern.finditer(text_to_convert):
        if match.start() > last_end:
            unparsed_gap = text_to_convert[last_end:match.start()].strip(" ,")
            if unparsed_gap and unparsed_gap not in [",", ":"]: # Avoid logging just separators
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
             # A very simple attempt to grab a final value if it's simple (e.g. version string)
             # but be careful not to misinterpret complex structures.
             # This part might need refinement if it causes issues.
             if ":" not in remaining_unparsed and "," not in remaining_unparsed and len(remaining_unparsed.split()) < 5: # Heuristic
                 if "Lora hashes" not in converted_text and "Version" not in converted_text : # Avoid common complex fields
                    converted_text["Uncategorized Suffix"] = remaining_unparsed


    # print(f"DEBUG [make_paired_str_dict] OUTPUT: {converted_text}") # Optional debug
    return converted_text

# --- START OF DECODER FUNCTION TO BE PASTED ---
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
                    
            except UnicodeDecodeError as ude:
                print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: UnicodeDecodeError during mojibake reversal: {ude}. Fallback.")
            except json.JSONDecodeError as jde:
                print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: JSONDecodeError after mojibake reversal: {jde}. Fallback.")
            except Exception as e_civitai:
                print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Mojibake reversal/validation failed with general error: {e_civitai}. Fallback.")
        
        elif data_to_fix and data_to_fix.strip().startswith('{'): 
            print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Data looks like JSON after prefix strip (or no prefix/mojibake). Validating '{data_to_fix.strip()[:50]}...'")
            try:
                clean_data_to_fix = data_to_fix.strip('\x00').strip()
                json.loads(clean_data_to_fix)
                print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Valid JSON after prefix strip. Returning string.")
                return clean_data_to_fix
            except json.JSONDecodeError as e_direct:
                print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style: Looked JSON-like but failed parse: {e_direct}. Fallback.")

        print(f"DEBUG [decode_exif_user_comment_to_json_string]: Civitai-style logic failed/skipped or data not suitable. Trying generic JSON search in original string input: '{uc_input[:50]}...'")
        json_start_index = uc_input.find('{')
        json_end_index = uc_input.rfind('}') 
        if json_start_index != -1 and json_end_index > json_start_index:
            potential_json = uc_input[json_start_index : json_end_index + 1].strip('\x00').strip()
            try:
                json.loads(potential_json)
                print(f"DEBUG [decode_exif_user_comment_to_json_string]: Generic string search: Found valid JSON: {potential_json[:100]}...")
                return potential_json
            except json.JSONDecodeError:
                print(f"DEBUG [decode_exif_user_comment_to_json_string]: Generic string search: Looked JSON-like but failed parse.")
        
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
                    except json.JSONDecodeError as je:
                        print(f"DEBUG [decode_exif_user_comment_to_json_string]: Bytes: Decoded with '{enc}', looked JSON-like, but failed json.loads(): {je}")

            except UnicodeDecodeError:
                print(f"DEBUG [decode_exif_user_comment_to_json_string]: Bytes: Failed UnicodeDecodeError with '{enc}'.")
                continue
    
    print(f"DEBUG [decode_exif_user_comment_to_json_string]: Failed all decoding attempts for UserComment (bytes path).")
    return None
# --- END OF DECODER FUNCTION ---


def process_pyexiv2_data(pyexiv2_header_data: dict) -> dict:
    """
    Formats standard photographic EXIF/XMP/IPTC data (from pyexiv2)
    into the UI's expected dictionary structure.
    This function is called AFTER attempting to parse UserComment for AI data.
    So, UserComment displayed here is typically non-AI or unparsed.
    """
    final_ui_meta = {}
    if not pyexiv2_header_data:
        return final_ui_meta

    exif_data = pyexiv2_header_data.get("EXIF", {})
    if exif_data:
        displayable_exif = {}
        # Populate common EXIF fields for display
        if 'Exif.Image.Make' in exif_data: displayable_exif['Camera Make'] = str(exif_data['Exif.Image.Make'])
        if 'Exif.Image.Model' in exif_data: displayable_exif['Camera Model'] = str(exif_data['Exif.Image.Model'])
        if 'Exif.Photo.DateTimeOriginal' in exif_data: displayable_exif['Date Taken'] = str(exif_data['Exif.Photo.DateTimeOriginal'])
        if 'Exif.Photo.FNumber' in exif_data: displayable_exif['F-Number'] = str(exif_data['Exif.Photo.FNumber'])
        if 'Exif.Photo.ExposureTime' in exif_data: displayable_exif['Exposure Time'] = str(exif_data['Exif.Photo.ExposureTime'])
        if 'Exif.Photo.ISOSpeedRatings' in exif_data: displayable_exif['ISO'] = str(exif_data['Exif.Photo.ISOSpeedRatings'])
        
        # Display UserComment as standard text if it exists and wasn't successfully parsed as AI JSON earlier
        # The 'user_comment_successfully_parsed_as_ai' flag would be set in the calling function (parse_metadata)
        # For simplicity here, we just display what pyexiv2 provided if it's not empty.
        # If `decode_exif_user_comment_to_json_string` was successful, UserComment might not be shown here again,
        # or it might be shown as its original mangled form.
        # This part focuses on showing standard EXIF data.
        if 'Exif.Photo.UserComment' in exif_data:
            uc_val = exif_data['Exif.Photo.UserComment']
            uc_text_for_display = ""
            if isinstance(uc_val, bytes):
                # Try simple decodes for display
                if uc_val.startswith(b'ASCII\x00\x00\x00'): uc_text_for_display = uc_val[8:].decode('ascii', 'replace')
                elif uc_val.startswith(b'UNICODE\x00'): uc_text_for_display = uc_val[8:].decode('utf-16', 'replace')
                else: 
                    try: uc_text_for_display = uc_val.decode('utf-8', 'replace')
                    except: uc_text_for_display = str(uc_val) # Fallback to string representation of bytes
            elif isinstance(uc_val, str):
                uc_text_for_display = uc_val
            
            cleaned_uc_display = uc_text_for_display.strip('\x00 ').strip()
            if cleaned_uc_display:
                # Add a "(Std.)" suffix to differentiate from potentially parsed AI data from UserComment
                displayable_exif['UserComment (Std.)'] = cleaned_uc_display
        
        if displayable_exif: final_ui_meta[DownField.EXIF] = displayable_exif
    
    xmp_data = pyexiv2_header_data.get("XMP", {})
    if xmp_data:
        displayable_xmp = {}
        if xmp_data.get('Xmp.dc.creator'):
            creator = xmp_data['Xmp.dc.creator']
            displayable_xmp['Artist'] = ", ".join(creator) if isinstance(creator, list) else str(creator)
        if xmp_data.get('Xmp.dc.description'):
            desc = xmp_data['Xmp.dc.description']
            displayable_xmp['Description'] = desc.get('x-default') if isinstance(desc, dict) else str(desc) # Handle x-default
        if xmp_data.get('Xmp.photoshop.DateCreated'):
             displayable_xmp['Date Created (XMP)'] = str(xmp_data['Xmp.photoshop.DateCreated'])
        if displayable_xmp: 
            if UpField.TAGS not in final_ui_meta: final_ui_meta[UpField.TAGS] = {}
            final_ui_meta[UpField.TAGS].update(displayable_xmp) # Merge XMP into TAGS
            
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
            final_ui_meta[UpField.TAGS].update(displayable_iptc) # Merge IPTC into TAGS
            
    return final_ui_meta


# --- Main Parsing Function ---
def parse_metadata(file_path_named: str) -> dict:
    final_ui_dict = {}
    # Convert to Path object for easier suffix handling
    path_obj = Path(file_path_named)
    file_ext_lower = path_obj.suffix.lower()
    is_txt_file = file_ext_lower == ".txt"

    print(f"\nDEBUG: >>> ENTERING parse_metadata for: {file_path_named}")

    data_reader = None 
    pyexiv2_raw_data = None 
    potential_ai_parsed = False # Flag to track if any AI parser succeeded

    if SDPR_AVAILABLE:
        try:
            print(f"DEBUG: Attempting to init ImageDataReader (is_txt: {is_txt_file})")
            if is_txt_file:
                # sd-prompt-reader expects a file-like object for text files
                with open(file_path_named, "r", encoding="utf-8", errors="replace") as f_obj:
                    data_reader = ImageDataReader(f_obj, is_txt=True)
            else:
                data_reader = ImageDataReader(file_path_named) # For image files
            
            print(f"DEBUG: ImageDataReader initialized.")
            if data_reader: # Should always be true if no exception
                status_name = data_reader.status.name if data_reader.status and hasattr(data_reader.status, 'name') else 'N/A'
                print(f"    Status: {status_name}")
                print(f"    Tool: {data_reader.tool}")
                print(f"    Format: {data_reader.format}") # PNG, JPEG etc.
                if not is_txt_file and hasattr(data_reader, '_info') and data_reader._info:
                     print(f"    SDPR _info keys: {list(data_reader._info.keys())}")
                     if "parameters" in data_reader._info: print(f"    _info['parameters'][:100]: {str(data_reader._info['parameters'])[:100]}...")
                     elif "prompt" in data_reader._info: print(f"    _info['prompt'][:100]: {str(data_reader._info['prompt'])[:100]}...")
                elif is_txt_file and data_reader.raw: print(f"    SDPR raw (from TXT)[:100]: {data_reader.raw[:100]}...")

                if data_reader.status == BaseFormat.Status.READ_SUCCESS and data_reader.tool:
                    nfo(f"SDPR parsed successfully. Tool: {data_reader.tool}")
                    print(f"DEBUG: SDPR READ_SUCCESS. Tool: {data_reader.tool}")
                    
                    # --- Populate final_ui_dict from data_reader (moved from original code block) ---
                    temp_prompt_data = {}
                    if data_reader.positive: temp_prompt_data["Positive"] = str(data_reader.positive)
                    if data_reader.negative: temp_prompt_data["Negative"] = str(data_reader.negative)
                    # ... (SDXL prompt data)
                    if temp_prompt_data: final_ui_dict[UpField.PROMPT] = temp_prompt_data

                    temp_gen_data = {}
                    for key, value in data_reader.parameter.items():
                        if value and value != SDPR_PARAMETER_PLACEHOLDER:
                            temp_gen_data[key.replace("_", " ").capitalize()] = str(value)
                    # ... (width, height, setting from data_reader)
                    if data_reader.setting:
                         if data_reader.tool and any(t in str(data_reader.tool) for t in ["A1111", "Forge", "SD.Next"]):
                            additional_settings = make_paired_str_dict(str(data_reader.setting))
                            # ... (merge additional_settings)
                         else: # ComfyUI, etc.
                            temp_gen_data["Tool Settings String"] = str(data_reader.setting)

                    if temp_gen_data: final_ui_dict[DownField.GENERATION_DATA] = temp_gen_data
                    if data_reader.raw: final_ui_dict[DownField.RAW_DATA] = str(data_reader.raw)
                    # ... (Detected Tool)
                    # --- End populate from data_reader ---
                    potential_ai_parsed = True

        except FileNotFoundError:
            nfo(f"File not found by SDPR: {file_path_named}")
            print("DEBUG: FileNotFoundError caught for ImageDataReader")
            # Don't return yet, allow pyexiv2 fallback for images
            if is_txt_file: return {EmptyField.PLACEHOLDER: {"Error": "Text file not found."}}
        except Exception as e_sdpr:
            nfo(f"Error with ImageDataReader for {file_path_named}: {e_sdpr.__class__.__name__} - {e_sdpr}")
            print(f"DEBUG: Exception during ImageDataReader processing: {e_sdpr.__class__.__name__} - {e_sdpr}")
            traceback.print_exc()
            # Continue to pyexiv2 fallback even if SDPR had an internal error
    else: # SDPR_AVAILABLE is False
        print("DEBUG: sd-prompt-reader not available. Skipping initial AI metadata parsing with it.")


    # --- Fallback to pyexiv2 for UserComment AI data OR standard EXIF/XMP ---
    # This block runs if:
    # 1. SDPR is not available.
    # 2. SDPR is available but failed to parse AI data (potential_ai_parsed is False).
    # 3. It's not a TXT file (TXT files are assumed to be handled by SDPR if available, or not at all by pyexiv2 path).
    if not potential_ai_parsed and not is_txt_file:
        status_name_from_sdpr = data_reader.status.name if data_reader and data_reader.status and hasattr(data_reader.status, 'name') else 'N/A'
        tool_name_from_sdpr = data_reader.tool if data_reader and data_reader.tool else 'N/A'
        nfo(f"SDPR did not fully parse AI data (Tool: {tool_name_from_sdpr}, Status: {status_name_from_sdpr}). Trying pyexiv2 UserComment AI parse then standard EXIF/XMP.")
        print(f"DEBUG: SDPR did not fully parse (Tool: {tool_name_from_sdpr}, Status: {status_name_from_sdpr}). Attempting pyexiv2 UserComment AI parse then standard fallback.")
        
        from .access_disk import MetadataFileReader # Import here, only used in this block
        std_reader = MetadataFileReader()
        
        # Get raw EXIF/XMP/IPTC data using pyexiv2
        if file_ext_lower.endswith((".jpg", ".jpeg", ".webp")):
            pyexiv2_raw_data = std_reader.read_jpg_header_pyexiv2(file_path_named)
        elif file_ext_lower.endswith(".png"): # PNGs might have EXIF too, or primarily rely on tEXt/iTXt (handled by SDPR)
            pyexiv2_raw_data = std_reader.read_png_header_pyexiv2(file_path_named)

        if pyexiv2_raw_data:
            print(f"DEBUG: pyexiv2 fallback got data with keys: {list(pyexiv2_raw_data.keys())}")
            exif_part = pyexiv2_raw_data.get("EXIF", {}) # Ensure EXIF key exists
            user_comment_value = exif_part.get("Exif.Photo.UserComment") if exif_part else None

            if user_comment_value:
                print(f"DEBUG: Found UserComment from pyexiv2. Type: {type(user_comment_value)}. Value (first 50): {repr(user_comment_value[:50]) if isinstance(user_comment_value, (str,bytes)) else repr(user_comment_value)}")
                
                # Call the robust decoder for UserComment
                json_str_from_uc = decode_exif_user_comment_to_json_string(user_comment_value)
                
                if json_str_from_uc:
                    print(f"DEBUG: Decoded UserComment (pyexiv2) to JSON string, trying AI parse: {json_str_from_uc[:150]}...")
                    if SDPR_AVAILABLE: # Only use SDPR parsers if available
                        try:
                            main_uc_json_obj = json.loads(json_str_from_uc)
                            
                            # Attempt to parse with A1111Parser if extraMetadata suggests it (Civitai ComfyUI often has this)
                            if "extraMetadata" in main_uc_json_obj and isinstance(main_uc_json_obj["extraMetadata"], str):
                                extra_meta_str = main_uc_json_obj["extraMetadata"]
                                print(f"DEBUG: Found 'extraMetadata' in UserComment, trying SDPR_A1111Parser: {extra_meta_str[:100]}...")
                                # SDPR_A1111Parser usually takes `raw` text, width, height.
                                # Here, we don't have width/height easily, let parser default.
                                parser_a1111_uc = SDPR_A1111Parser(raw=extra_meta_str)
                                status = parser_a1111_uc.parse()
                                if status == BaseFormat.Status.READ_SUCCESS:
                                    print("DEBUG: UserComment.extraMetadata parsed as A1111 by SDPR_A1111Parser.")
                                    # Populate final_ui_dict using a helper or directly
                                    # For now, just marking as parsed. You'd call _populate_ui_dict_from_sdpr_parser here.
                                    # final_ui_dict = _populate_ui_dict_from_sdpr_parser(parser_a1111_uc, "Civitai/A1111 (UC.extraMeta)")
                                    print("      -> Positive:", parser_a1111_uc.positive[:50])
                                    print("      -> Negative:", parser_a1111_uc.negative[:50])
                                    print("      -> Parameters:", parser_a1111_uc.parameter)
                                    potential_ai_parsed = True # Mark as parsed

                            # If not A1111 from extraMetadata, try full ComfyUI on main UC JSON
                            # Heuristic for ComfyUI workflow: presence of "nodes" and "class_type" in a node
                            if not potential_ai_parsed and "nodes" in main_uc_json_obj:
                                is_likely_comfy = False
                                if isinstance(main_uc_json_obj["nodes"], dict):
                                    first_node_key = next(iter(main_uc_json_obj["nodes"]), None)
                                    if first_node_key and isinstance(main_uc_json_obj["nodes"][first_node_key], dict) and \
                                       "class_type" in main_uc_json_obj["nodes"][first_node_key]:
                                        is_likely_comfy = True
                                
                                if is_likely_comfy:
                                    print("DEBUG: UserComment JSON looks like ComfyUI graph. Trying SDPR_ComfyUIParser.")
                                    # SDPR_ComfyUIParser expects `info` to be the workflow dict (or string)
                                    parser_comfy_uc = SDPR_ComfyUIParser(info=main_uc_json_obj) # Pass the dict
                                    status = parser_comfy_uc.parse()
                                    if status == BaseFormat.Status.READ_SUCCESS:
                                        print("DEBUG: UserComment parsed as ComfyUI graph by SDPR_ComfyUIParser.")
                                        # final_ui_dict = _populate_ui_dict_from_sdpr_parser(parser_comfy_uc, "Civitai/ComfyUI (UC graph)")
                                        print("      -> Positive:", parser_comfy_uc.positive[:50])
                                        print("      -> Negative:", parser_comfy_uc.negative[:50])
                                        print("      -> Parameters:", parser_comfy_uc.parameter) # Comfy parameters are different
                                        potential_ai_parsed = True
                        except json.JSONDecodeError as e_json_load:
                             print(f"DEBUG: UserComment (pyexiv2) was decoded to string, but it's not valid JSON, or SDPR parsing failed: {e_json_load}")
                        except Exception as e_uc_ai:
                             print(f"DEBUG: Error parsing AI data from UserComment (pyexiv2 path with SDPR): {e_uc_ai}"); traceback.print_exc()
                    else: # SDPR Not Available, but we have a JSON string from UserComment
                        print("DEBUG: SDPR not available. Decoded UserComment to JSON, storing raw.")
                        final_ui_dict[DownField.RAW_DATA] = json_str_from_uc # Store the raw JSON string
                        # You could add a "Detected Tool: Unknown (Raw UserComment JSON)" here.
                        if UpField.METADATA not in final_ui_dict: final_ui_dict[UpField.METADATA] = {}
                        final_ui_dict[UpField.METADATA]["Detected Tool"] = "Unknown (Raw UserComment JSON)"
                        potential_ai_parsed = True # We got some form of AI data
            
            # After attempting UserComment AI parse, if not successful, process standard EXIF/XMP
            if not potential_ai_parsed: 
                print("DEBUG: UserComment (pyexiv2) did not yield AI data. Processing pyexiv2_raw_data for standard EXIF/XMP.")
                standard_photo_meta = process_pyexiv2_data(pyexiv2_raw_data)
                if standard_photo_meta:
                    final_ui_dict.update(standard_photo_meta)
                    nfo("Displayed standard EXIF/XMP data.")
                    print("DEBUG: Populated final_ui_dict with standard EXIF/XMP.")
                elif not final_ui_dict.get(EmptyField.PLACEHOLDER): # Avoid overwriting other placeholders
                    final_ui_dict[EmptyField.PLACEHOLDER] = {"Info": "Standard image, but no processable EXIF/XMP fields found."}
            elif potential_ai_parsed and not final_ui_dict: # AI parsed from UC, but final_ui_dict not populated by SDPR parsers
                # This happens if SDPR was available but the _populate_ui_dict_from_sdpr_parser calls were commented out
                # Or if SDPR was not available and we just stored raw JSON.
                # We need to ensure final_ui_dict is populated if potential_ai_parsed is True.
                # This section needs the _populate_ui_dict_from_sdpr_parser calls reinstated or equivalent logic.
                # For now, if SDPR was available and parsers ran, this block shouldn't be hit if they populated final_ui_dict.
                # If SDPR was NOT available, RAW_DATA and METADATA[Detected Tool] were set above.
                print("DEBUG: AI data potentially parsed from UserComment, but final_ui_dict is empty. Ensure SDPR parsers populate it if SDPR is available.")


        else: # pyexiv2_raw_data is None
            print("DEBUG: pyexiv2 fallback got NO raw data (pyexiv2_raw_data is None).")
            if not final_ui_dict.get(EmptyField.PLACEHOLDER):
                final_ui_dict[EmptyField.PLACEHOLDER] = {"Info": "Standard image, no EXIF/XMP block found via pyexiv2."}
    
    # This handles if SDPR ran but resulted in an error status AND no AI was parsed from UC fallback
    # And it's not a TXT file (which might have other reasons for SDPR failure not warranting this message)
    elif not potential_ai_parsed and not is_txt_file and data_reader and data_reader.status != BaseFormat.Status.READ_SUCCESS : 
        status_name = data_reader.status.name if data_reader.status and hasattr(data_reader.status, 'name') else 'N/A'
        tool_name = data_reader.tool if data_reader.tool else 'N/A'
        error_message = f"Could not read AI metadata ({status_name})."
        if data_reader.tool: error_message += f" Detected tool: {tool_name}."
        # Avoid overwriting if pyexiv2 path already put something more specific or useful
        if not final_ui_dict or (EmptyField.PLACEHOLDER in final_ui_dict and "Error" not in final_ui_dict[EmptyField.PLACEHOLDER]):
            final_ui_dict[EmptyField.PLACEHOLDER] = {"Error": error_message}
        if data_reader.raw and DownField.RAW_DATA not in final_ui_dict:
             final_ui_dict[DownField.RAW_DATA] = str(data_reader.raw)
        print(f"DEBUG: SDPR parsing failed (image). Status: {status_name}, Tool: {tool_name}")

    # Final check for emptiness
    is_effectively_empty = not final_ui_dict or \
                           (len(final_ui_dict) == 1 and EmptyField.PLACEHOLDER in final_ui_dict and \
                            list(final_ui_dict[EmptyField.PLACEHOLDER].keys()) == [EmptyField.PLACEHOLDER]) # Your old check for {"":""}

    if is_effectively_empty and not potential_ai_parsed: # Only if AI wasn't found
        loggable_header_info = "Unknown header data"
        if data_reader and data_reader.raw: loggable_header_info = str(data_reader.raw)[:200]
        elif pyexiv2_raw_data: loggable_header_info = str(list(pyexiv2_raw_data.keys()) if isinstance(pyexiv2_raw_data, dict) else pyexiv2_raw_data)[:200]
        
        nfo("Failed to find/load metadata for file. Last available data: %s", loggable_header_info)
        if EmptyField.PLACEHOLDER not in final_ui_dict :
            final_ui_dict[EmptyField.PLACEHOLDER] = {"Error": "No processable metadata found."}
        print("DEBUG: final_ui_dict is effectively empty after all checks.")
         
    print(f"DEBUG: <<< EXITING parse_metadata. Returning keys: {list(final_ui_dict.keys())}")
    return final_ui_dict
