# dataset_tools/metadata_parser.py

import re
import json # Keep for potential direct JSON handling if needed
from .correct_types import UpField, DownField, EmptyField
from .logger import info_monitor as nfo
# If you have a debug_message in logger.py, you can use it too.
# from .logger import debug_message

# --- Imports for sd-prompt-reader ---
try:
    from sd_prompt_reader.image_data_reader import ImageDataReader
    from sd_prompt_reader.format import BaseFormat
    from sd_prompt_reader.constants import PARAMETER_PLACEHOLDER as SDPR_PARAMETER_PLACEHOLDER
    SDPR_AVAILABLE = True
except ImportError as e:
    nfo(f"WARNING: sd-prompt-reader library not found or could not import components: {e}. AI metadata parsing will be limited.")
    SDPR_AVAILABLE = False
    # Define fallbacks if sd-prompt-reader is not available
    class ImageDataReader:  # Dummy class
        def __init__(self, file_path_or_obj, is_txt=False): # Add a basic init
            self.status = None # Initialize dummy attributes
            self.tool = None
            self.format = None
            self.positive = ""
            self.negative = ""
            self.is_sdxl = False
            self.positive_sdxl = {}
            self.negative_sdxl = {}
            self.parameter = {}
            self.width = "0"
            self.height = "0"
            self.setting = ""
            self.raw = ""
            nfo("Using dummy ImageDataReader as sd-prompt-reader is not available.")

    class BaseFormat:  # Dummy class
        class Status:  # Nested class for the enum
            UNREAD = 1
            READ_SUCCESS = 2
            FORMAT_ERROR = 3
            COMFYUI_ERROR = 4
        # Add other attributes or methods if your code specifically checks for them on BaseFormat instances
        PARAMETER_PLACEHOLDER = "                    "

    SDPR_PARAMETER_PLACEHOLDER = "                    " # Default placeholder

# --- Helper Functions ---

def make_paired_str_dict(text_to_convert: str) -> dict:
    """
    Convert an A1111-style settings string (e.g., "Steps: 20, Sampler: Euler")
    into a dictionary.
    """
    if not text_to_convert or not isinstance(text_to_convert, str):
        return {}
    
    # nfo(f"[make_paired_str_dict] Input: {text_to_convert[:150]}...")
    converted_text = {}
    pattern = re.compile(r"([^:]+):\s*((?:\"[^\"]*\"|'[^']*'|[^,])+)(?:,\s*|$)")
    
    current_pos = 0
    while current_pos < len(text_to_convert):
        match = pattern.match(text_to_convert, current_pos)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
                
            converted_text[key] = value
            current_pos = match.end()
            if current_pos < len(text_to_convert) and text_to_convert[current_pos] == ',':
                current_pos += 1
                while current_pos < len(text_to_convert) and text_to_convert[current_pos].isspace():
                    current_pos +=1
            elif current_pos == len(text_to_convert):
                 break
            else:
                 nfo(f"[make_paired_str_dict] Regex stall at pos {current_pos} on: {text_to_convert[current_pos:current_pos+20]}")
                 break 
        else:
            remaining_unparsed = text_to_convert[current_pos:].strip()
            if remaining_unparsed:
                nfo(f"[make_paired_str_dict] Could not parse remaining part: '{remaining_unparsed[:100]}...'")
            break
            
    # nfo(f"[make_paired_str_dict] Output: {converted_text}")
    return converted_text


def process_pyexiv2_data(pyexiv2_header_data: dict) -> dict:
    """
    Formats standard photographic EXIF/XMP/IPTC data (from pyexiv2)
    into the UI's expected dictionary structure.
    """
    # nfo(f"[process_pyexiv2_data] Input keys: {list(pyexiv2_header_data.keys()) if pyexiv2_header_data else 'None'}")
    final_ui_meta = {}
    if not pyexiv2_header_data:
        return final_ui_meta

    exif_data = pyexiv2_header_data.get("EXIF", {})
    if exif_data:
        displayable_exif = {}
        if 'Exif.Image.Make' in exif_data: displayable_exif['Camera Make'] = str(exif_data['Exif.Image.Make'])
        if 'Exif.Image.Model' in exif_data: displayable_exif['Camera Model'] = str(exif_data['Exif.Image.Model'])
        if 'Exif.Photo.DateTimeOriginal' in exif_data: displayable_exif['Date Taken'] = str(exif_data['Exif.Photo.DateTimeOriginal'])
        if 'Exif.Photo.FNumber' in exif_data: displayable_exif['F-Number'] = str(exif_data['Exif.Photo.FNumber'])
        if 'Exif.Photo.ExposureTime' in exif_data: displayable_exif['Exposure Time'] = str(exif_data['Exif.Photo.ExposureTime'])
        if 'Exif.Photo.ISOSpeedRatings' in exif_data: displayable_exif['ISO'] = str(exif_data['Exif.Photo.ISOSpeedRatings'])
        if 'Exif.Photo.UserComment' in exif_data:
            uc = exif_data['Exif.Photo.UserComment']
            if isinstance(uc, bytes):
                try: uc = uc.decode('utf-8', errors='replace')
                except: uc = str(uc)
            displayable_exif['User Comment'] = uc
        if displayable_exif: final_ui_meta[DownField.EXIF] = displayable_exif
    
    xmp_data = pyexiv2_header_data.get("XMP", {})
    if xmp_data:
        displayable_xmp = {}
        if xmp_data.get('Xmp.dc.creator'):
            creator = xmp_data['Xmp.dc.creator']
            displayable_xmp['Artist'] = ", ".join(creator) if isinstance(creator, list) else str(creator)
        if xmp_data.get('Xmp.dc.description'):
            desc = xmp_data['Xmp.dc.description']
            displayable_xmp['Description'] = desc.get('x-default') if isinstance(desc, dict) else str(desc)
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
            
    # nfo(f"[process_pyexiv2_data] Output: {final_ui_meta}")
    return final_ui_meta


# --- Main Parsing Function ---
def parse_metadata(file_path_named: str) -> dict:
    final_ui_dict = {}
    is_txt_file = file_path_named.lower().endswith(".txt")

    print(f"\nDEBUG: >>> ENTERING parse_metadata for: {file_path_named}")

    data_reader = None 
    pyexiv2_raw_data = None # Initialize here for broader scope in logging

    if SDPR_AVAILABLE:
        try:
            print(f"DEBUG: Attempting to init ImageDataReader (is_txt: {is_txt_file})")
            if is_txt_file:
                with open(file_path_named, "r", encoding="utf-8") as f_obj:
                    data_reader = ImageDataReader(f_obj, is_txt=True)
            else:
                data_reader = ImageDataReader(file_path_named)
            
            print(f"DEBUG: ImageDataReader initialized.")
            if data_reader:
                print(f"    Status: {data_reader.status.name if data_reader.status else 'N/A'}") # Use .name for enum
                print(f"    Tool: {data_reader.tool}")
                print(f"    Format: {data_reader.format}")
                if not is_txt_file and hasattr(data_reader, '_info') and data_reader._info: # Check _info exists
                     print(f"    ImageDataReader internal _info keys: {list(data_reader._info.keys())}")
                     if "parameters" in data_reader._info:
                         print(f"    _info['parameters'] (first 100 chars): {str(data_reader._info['parameters'])[:100]}...")
                     elif "prompt" in data_reader._info:
                         print(f"    _info['prompt'] (first 100 chars): {str(data_reader._info['prompt'])[:100]}...")
                     else:
                         print(f"    _info does NOT contain typical AI 'parameters' or 'prompt' key.")
                elif is_txt_file and data_reader.raw:
                    print(f"    Raw from TXT (first 100 chars): {data_reader.raw[:100]}...")

        except FileNotFoundError:
            nfo(f"File not found: {file_path_named}")
            print("DEBUG: FileNotFoundError caught by parse_metadata for ImageDataReader")
            return {EmptyField.PLACEHOLDER: {"Error": "File not found."}}
        except Exception as e:
            nfo(f"Error with ImageDataReader for {file_path_named}: {e.__class__.__name__} - {e}")
            print(f"DEBUG: Exception during ImageDataReader processing: {e.__class__.__name__} - {e}")
            import traceback
            traceback.print_exc()
    else:
        print("DEBUG: sd-prompt-reader not available. Skipping AI metadata parsing with it.")

    if data_reader and data_reader.status == BaseFormat.Status.READ_SUCCESS and data_reader.tool:
        nfo(f"SDPR parsed successfully. Tool: {data_reader.tool}")
        print(f"DEBUG: SDPR READ_SUCCESS. Tool: {data_reader.tool}")

        temp_prompt_data = {}
        if data_reader.positive: temp_prompt_data["Positive"] = str(data_reader.positive)
        if data_reader.negative: temp_prompt_data["Negative"] = str(data_reader.negative)
        if data_reader.is_sdxl:
            if data_reader.positive_sdxl: temp_prompt_data["Positive SDXL"] = data_reader.positive_sdxl
            if data_reader.negative_sdxl: temp_prompt_data["Negative SDXL"] = data_reader.negative_sdxl
        if temp_prompt_data: final_ui_dict[UpField.PROMPT] = temp_prompt_data

        temp_gen_data = {}
        for key, value in data_reader.parameter.items():
            if value and value != SDPR_PARAMETER_PLACEHOLDER:
                display_key = key.replace("_", " ").capitalize()
                temp_gen_data[display_key] = str(value)
        
        if data_reader.width and str(data_reader.width) != "0": temp_gen_data["Width"] = str(data_reader.width)
        if data_reader.height and str(data_reader.height) != "0": temp_gen_data["Height"] = str(data_reader.height)

        if data_reader.setting:
            if data_reader.tool and any(t in str(data_reader.tool) for t in ["A1111", "Forge", "SD.Next"]): # Ensure data_reader.tool is string
                additional_settings = make_paired_str_dict(str(data_reader.setting))
                for key, value_add in additional_settings.items():
                    display_key_add = key.replace("_", " ").capitalize()
                    if display_key_add not in temp_gen_data or \
                       temp_gen_data.get(display_key_add) in [None, "None", SDPR_PARAMETER_PLACEHOLDER, ""]:
                        temp_gen_data[display_key_add] = str(value_add)
            else:
                temp_gen_data["Tool Settings String"] = str(data_reader.setting)
        if temp_gen_data: final_ui_dict[DownField.GENERATION_DATA] = temp_gen_data
        
        if data_reader.raw: final_ui_dict[DownField.RAW_DATA] = str(data_reader.raw)
        if data_reader.tool:
            if UpField.METADATA not in final_ui_dict: final_ui_dict[UpField.METADATA] = {}
            final_ui_dict[UpField.METADATA]["Detected Tool"] = str(data_reader.tool)
    
    elif not is_txt_file and (not SDPR_AVAILABLE or not data_reader or not data_reader.tool or (data_reader and data_reader.status != BaseFormat.Status.READ_SUCCESS)): # Added check for data_reader existence before accessing status
        status_name = data_reader.status.name if data_reader and data_reader.status else 'N/A'
        tool_name = data_reader.tool if data_reader and data_reader.tool else 'N/A'
        nfo(f"SDPR did not fully parse AI data (Tool: {tool_name}, Status: {status_name}). Trying standard EXIF/XMP.")
        print(f"DEBUG: SDPR did not fully parse (Tool: {tool_name}, Status: {status_name}). Attempting pyexiv2 fallback.")
        
        from .access_disk import MetadataFileReader
        std_reader = MetadataFileReader()
        
        file_ext_lower = file_path_named.lower()
        if file_ext_lower.endswith((".jpg", ".jpeg", ".webp")):
            pyexiv2_raw_data = std_reader.read_jpg_header_pyexiv2(file_path_named)
        elif file_ext_lower.endswith(".png"):
            pyexiv2_raw_data = std_reader.read_png_header_pyexiv2(file_path_named)

        if pyexiv2_raw_data:
            print(f"DEBUG: pyexiv2 fallback got data with keys: {list(pyexiv2_raw_data.keys())}")
            standard_photo_meta = process_pyexiv2_data(pyexiv2_raw_data)
            if standard_photo_meta:
                final_ui_dict.update(standard_photo_meta)
                nfo("Displayed standard EXIF/XMP data.")
                print("DEBUG: Populated final_ui_dict with standard EXIF/XMP.")
            elif not final_ui_dict.get(EmptyField.PLACEHOLDER):
                final_ui_dict[EmptyField.PLACEHOLDER] = {"Info": "Standard image, but no processable EXIF/XMP fields found by custom parser."}
        else:
            print("DEBUG: pyexiv2 fallback got NO data (returned None).")
            if not final_ui_dict.get(EmptyField.PLACEHOLDER):
                final_ui_dict[EmptyField.PLACEHOLDER] = {"Info": "Standard image, no EXIF/XMP found via pyexiv2."}
    
    elif data_reader and data_reader.status != BaseFormat.Status.READ_SUCCESS : 
        status_name = data_reader.status.name if data_reader.status else 'N/A'
        tool_name = data_reader.tool if data_reader.tool else 'N/A'
        error_message = f"Could not read AI metadata ({status_name})."
        if data_reader.tool: error_message += f" Detected tool: {tool_name}."
        final_ui_dict[EmptyField.PLACEHOLDER] = {"Error": error_message}
        if data_reader.raw: final_ui_dict[DownField.RAW_DATA] = str(data_reader.raw)
        print(f"DEBUG: SDPR parsing failed or incomplete. Status: {status_name}, Tool: {tool_name}")

    is_effectively_empty = not final_ui_dict or \
                           (len(final_ui_dict) == 1 and EmptyField.PLACEHOLDER in final_ui_dict)

    if is_effectively_empty:
        loggable_header_info = "Unknown header data"
        if data_reader and data_reader.raw:
            loggable_header_info = str(data_reader.raw)[:200]
        elif pyexiv2_raw_data: # Check if pyexiv2_raw_data was defined and has content
            loggable_header_info = str(list(pyexiv2_raw_data.keys()) if isinstance(pyexiv2_raw_data, dict) else pyexiv2_raw_data)[:200]
        
        nfo("Failed to find/load metadata : %s", loggable_header_info)
        if EmptyField.PLACEHOLDER not in final_ui_dict :
            final_ui_dict[EmptyField.PLACEHOLDER] = {"Error": "No processable metadata found."}
        print("DEBUG: final_ui_dict is effectively empty after all checks.")
         
    print(f"DEBUG: <<< EXITING parse_metadata. Returning keys: {list(final_ui_dict.keys())}")
    return final_ui_dict