# dataset_tools/metadata_parser.py
from .correct_types import UpField, DownField, EmptyField
from .logger import info_monitor as nfo
from sd_prompt_reader import ImageDataReader # From the installed library
from sd_prompt_reader.format import BaseFormat # For status checking
import re # For make_paired_str_dict
# import json # If needed for any direct JSON handling

# --- Helper Functions (Keep these from your code or my previous suggestions) ---
def make_paired_str_dict(text_to_convert: str) -> dict:
    if not text_to_convert or not isinstance(text_to_convert, str): return {}
    converted_text = {}
    try:
        segments = re.split(r',\s*(?![^()]*\))(?![^\[\]]*\])(?![^{}]*\})', text_to_convert)
        for item in segments:
            if isinstance(item, str) and ": " in item:
                parts = item.split(": ", 1)
                if len(parts) == 2:
                    converted_text[parts[0].strip()] = parts[1].strip()
    except Exception as e:
        nfo(f"Error in make_paired_str_dict: {e} on string {text_to_convert}")
    return converted_text

def process_pyexiv2_data(pyexiv2_header_data: dict) -> dict: # For non-AI images
    processed_dict = {}
    exif_data = pyexiv2_header_data.get("EXIF", {})
    if exif_data:
        displayable_exif = {}
        # Add your specific EXIF mappings here, e.g.:
        if 'Exif.Image.Make' in exif_data: displayable_exif['Camera Make'] = exif_data['Exif.Image.Make']
        if 'Exif.Image.Model' in exif_data: displayable_exif['Camera Model'] = exif_data['Exif.Image.Model']
        if 'Exif.Photo.DateTimeOriginal' in exif_data: displayable_exif['Date Taken'] = exif_data['Exif.Photo.DateTimeOriginal']
        # ... more standard EXIF fields
        if displayable_exif: processed_dict[DownField.EXIF] = displayable_exif
    
    xmp_data = pyexiv2_header_data.get("XMP", {})
    if xmp_data:
        displayable_xmp = {}
        # Add your specific XMP mappings here, e.g.:
        if xmp_data.get('Xmp.dc.creator'): displayable_xmp['Artist'] = str(xmp_data['Xmp.dc.creator'])
        if xmp_data.get('Xmp.dc.description'):
            desc = xmp_data['Xmp.dc.description']
            displayable_xmp['Description'] = desc.get('x-default') if isinstance(desc, dict) else str(desc)
        # ... more standard XMP fields
        if displayable_xmp: processed_dict[UpField.TAGS] = displayable_xmp
    
    # You might also want to include IPTC processing here if needed
    # iptc_data = pyexiv2_header_data.get("IPTC", {}) ...
            
    return processed_dict

# --- Main Parsing Function ---
def parse_metadata(file_path_named: str) -> dict:
    final_ui_dict = {}
    is_txt_file = file_path_named.lower().endswith(".txt")

    try:
        if is_txt_file:
            with open(file_path_named, "r", encoding="utf-8") as f_obj:
                data_reader = ImageDataReader(f_obj, is_txt=True)
        else:
            data_reader = ImageDataReader(file_path_named)
    except FileNotFoundError:
        nfo(f"File not found: {file_path_named}")
        return {EmptyField.PLACEHOLDER: {"Error": "File not found."}}
    except Exception as e:
        nfo(f"Error initializing ImageDataReader for {file_path_named}: {e}")
        return {EmptyField.PLACEHOLDER: {"Error": f"Cannot open or read image: {e}"}}

    if data_reader.status == BaseFormat.Status.READ_SUCCESS:
        nfo(f"SDPR parsed: {data_reader.tool or 'Unknown AI Tool'}")
        
        temp_prompt_data = {}
        if data_reader.positive: temp_prompt_data["Positive"] = data_reader.positive
        if data_reader.negative: temp_prompt_data["Negative"] = data_reader.negative
        if data_reader.is_sdxl:
            if data_reader.positive_sdxl: temp_prompt_data["Positive SDXL"] = data_reader.positive_sdxl
            if data_reader.negative_sdxl: temp_prompt_data["Negative SDXL"] = data_reader.negative_sdxl
        if temp_prompt_data: final_ui_dict[UpField.PROMPT] = temp_prompt_data

        temp_gen_data = {}
        for key, value in data_reader.parameter.items():
            if value and value != data_reader.PARAMETER_PLACEHOLDER: # Use placeholder from sd-prompt-reader
                display_key = key.replace("_", " ").capitalize()
                temp_gen_data[display_key] = str(value)
        
        if data_reader.width and data_reader.width != "0": temp_gen_data["Width"] = str(data_reader.width)
        if data_reader.height and data_reader.height != "0": temp_gen_data["Height"] = str(data_reader.height)

        if data_reader.setting:
            additional_settings = make_paired_str_dict(data_reader.setting)
            for key, value in additional_settings.items():
                display_key = key.replace("_", " ").capitalize()
                if display_key not in temp_gen_data or temp_gen_data[display_key] in [None, "None", data_reader.PARAMETER_PLACEHOLDER, ""]:
                    temp_gen_data[display_key] = str(value)
        if temp_gen_data: final_ui_dict[DownField.GENERATION_DATA] = temp_gen_data
        
        if data_reader.raw: final_ui_dict[DownField.RAW_DATA] = data_reader.raw
        if data_reader.tool:
            if UpField.METADATA not in final_ui_dict: final_ui_dict[UpField.METADATA] = {}
            final_ui_dict[UpField.METADATA]["Detected Tool"] = data_reader.tool

    elif not is_txt_file and not data_reader.tool: # Not AI, try standard EXIF/XMP
        nfo(f"SDPR found no AI tool for {file_path_named}. Trying standard EXIF/XMP.")
        from .access_disk import MetadataFileReader # Your original reader for pyexiv2
        std_reader = MetadataFileReader()
        pyexiv2_raw_data = None
        if file_path_named.lower().endswith((".jpg", ".jpeg")):
            pyexiv2_raw_data = std_reader.read_jpg_header_pyexiv2(file_path_named)
        elif file_path_named.lower().endswith(".png"):
             pyexiv2_raw_data = std_reader.read_png_header_pyexiv2(file_path_named)
        # Add other formats if your pyexiv2 reader supports them

        if pyexiv2_raw_data:
            standard_photo_meta = process_pyexiv2_data(pyexiv2_raw_data)
            if standard_photo_meta:
                final_ui_dict.update(standard_photo_meta)
                nfo("Displayed standard EXIF/XMP data.")
            else:
                final_ui_dict[EmptyField.PLACEHOLDER] = {"Info": "Standard image with no processable EXIF/XMP."}
        else:
            final_ui_dict[EmptyField.PLACEHOLDER] = {"Info": "Standard image, no EXIF/XMP found via pyexiv2."}
    else: # SDPR failed for some other reason
        error_message = f"Could not read AI metadata ({data_reader.status.name})."
        if data_reader.tool: error_message += f" Detected tool: {data_reader.tool}."
        final_ui_dict[EmptyField.PLACEHOLDER] = {"Error": error_message}
        if data_reader.raw: final_ui_dict[DownField.RAW_DATA] = data_reader.raw

    if not final_ui_dict:
         final_ui_dict[EmptyField.PLACEHOLDER] = {"Error": "No processable metadata found."}
         
    return final_ui_dict