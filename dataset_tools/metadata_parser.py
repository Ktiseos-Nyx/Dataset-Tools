"""為使用者介面清理和安排元資料"""
 # pylint: disable=line-too-long

import re
import json
from json import JSONDecodeError

from PIL import Image
from PIL.ExifTags import TAGS
from dataset_tools import logger, EXC_INFO

def open_jpg_header(file_path_named: str) -> dict:
    """
    Open jpg format files\n
    :param file_path_named: The path and file name of the jpg file
    :return: Generator element containing header tags
    """
    pil_image = Image.open(file_path_named)
    info  = pil_image.info
    if info is None:
        return None
    exif = {TAGS.get(k, k): v for k, v in info.items()}
    return exif

def open_png_header(file_path_named: str) -> dict:
    """
    Open png format files\n
    :param file_path_named: The path and file name of the png file
    :return: Generator element containing header bytes
    """
    pil_img = Image.open(file_path_named)
    if pil_img is None: # We dont need to load completely unless totally necessary
        pil_img.load() # This is the case when we have no choice but to load (slower)
    text_chunks = pil_img.info
    return text_chunks


def format_chunk(text_chunks: str) -> list:
    """
    Format text from header file by escape-code delineations\n
    :param text_chunk: Data from a file header
    :return: text data in a dict structure
    """
    replace_strings = ['\xe2\x80\x8b', '\x00', '\u200b','\n',"\'Negative Prompt\'"]
    dirty_string = text_chunks.get('parameters')
    segments = [dirty_string]

    for buffer in replace_strings:
        new_segments = []
        for delination in segments: # Split segments and all sub-segments of this string
            split_segs = delination.split(buffer)
            new_segments.extend(s for s in split_segs if s)  # Skip empty strings
        segments = new_segments

    clean_segments = segments

    logger.debug("%s",f"{clean_segments}")
    return clean_segments

def extract_prompts(clean_segments: list) -> tuple[dict, str]:
    """
    Split string by pre-delineated tag information\n
    :param cleaned_text: Text without escape codes
    :return: A dictionary of prompts and a str of metadata
    """
    deprompted_segments = []
    prompt_metadata = { 'Positive prompt':clean_segments[0], 'Negative prompt': clean_segments[1] }
    for i in range(len(clean_segments)-2):
        deprompted_segments.append(clean_segments[i+2])
    deprompted_text = ''.join(deprompted_segments)
    return prompt_metadata, deprompted_text

def extract_partial_mappings(deprompted_text: str) -> tuple[str, list]:
    """
    Split string by pre-delineated tag information\n
    :param cleaned_text: Text without escape codes
    :return: A freeform string and a partially-organized list of metadata
    """
   # Regex for capturing dictionary or quoted strings

    pattern_types = [r' (\w*): ([{].*[}]),', r' (\w*\s*\w+): (["].*["]),']
    valid_mapping = {}
    remaining_text = deprompted_text
    for pattern in pattern_types:
        data = re.findall(pattern, deprompted_text)
        logger.debug(data)
        valid_mapping.setdefault(data[0][0], data[0][1])
        remaining_text = re.sub(pattern, '', remaining_text).strip()
    return valid_mapping, remaining_text

    #subtract_pattern = r'(\w*\s*?:\s*?[{].*[}])|(,\s*?\w*\s*\w+:\s*?["].*["]),'

def convert_str_to_dict(text_to_convert: str) -> tuple[dict]:
    """
    Convert an unstructured metadata string into a dictionary\n
    :param dehashed_data: Metadata tags with quote and bracket delineated features removed
    :return: A valid dictionary structure with identical information
    """
    segmented = text_to_convert.split(", ")
    delineated = [item.split(": ") for item in segmented if isinstance(item, str)]
    converted_text = {element[0]: element[1] for element in delineated}
    return converted_text

def clean_with_json(prestructured_data:dict, key_name: str) -> dict:
    """
    Use json loads to arrange half-formatted dict into valid dict\n
    :param prestructured_data: A dict with a single working key
    :param key_name: The single working key name
    :return: A formatted dictionary object
    """
    try:
        cleaned_data = json.loads(prestructured_data[key_name])
    except JSONDecodeError as error_log:
        logger.info("Attempted to parse invalid formatting on %s", f"{prestructured_data} at {key_name}, {error_log}", exc_info=EXC_INFO)
    return cleaned_data


def dig_nested_values(initial_depth:dict, search_term:str, retrieval_keyword:str, key_labels: list,) ->dict:
    """
    Trigger recursive dive into nested ditionary\n
    :param initial_depth: Where to start in the nested dictionary
    :param search_term: The value to search for
    :param keyword: Key to retrieve the data beneath
    :param key_labels: A list of labels to apply to the new dictionary
    :return: The new dictionary and the original dictionary
    """
    nested_value = {}

    def _check_depth_values(depth, k,v):
        """Find matching key, fetch values and add them to a new dictionary"""
        if isinstance(k, str) and isinstance(v, str) and (search_term in k or search_term in v):
            key_name = next(iter(key_labels))
            nested_value.setdefault(key_name,depth[retrieval_keyword].get(next(iter(depth[retrieval_keyword]))).strip('\n') )
            logger.debug(depth)
            if len(key_labels) > 1:
                key_labels.pop(0)

    def _cycle_depth(depth):
        """Recurse through the dictionary completely"""
        for k, v in depth.items():
            _check_depth_values(depth,k,v)
            if isinstance(v, dict):
                _cycle_depth(v)


    _cycle_depth(initial_depth)
    logger.debug(nested_value)
    return nested_value, initial_depth # to do : make sure  initial depth doesnt store negative prompt

def arrange_nodeui_metadata(header_chunks:str) ->dict:
    """
    Using the header from a file, run formatting and parsing processes \n
    Return format : {"Prompts": , "Settings": , "System": } \n
    :param header_chunks: Header data from a file
    :return: Metadata in a standardized format
    """
    clean_metadata = clean_with_json(header_chunks, 'prompt')
    prompt_map, mixed_map = dig_nested_values(clean_metadata, 'CLIPTextEncode', 'inputs',["Positive prompt", "Negative prompt", "Prompt"])
    logger.debug(mixed_map)
    generation_map = {}
    for node in mixed_map:
        generation_map.update(mixed_map[node]["inputs"])
    return {"Prompts": prompt_map, "Generation_Data": generation_map}


def arrange_webui_metadata(header_chunks:str) -> dict:
    """
    Using the header from a file, send to multiple formatting, cleaning, and parsing, processes \n
    Return format : {"Prompts": , "Settings": , "System": } \n
    :param header_chunks: Header data from a file
    :return: Metadata in a standardized format
    """
    cleaned_text = format_chunk(header_chunks)
    logger.debug("%s",f"{type(cleaned_text)} : {cleaned_text} )")
    prompt_map, deprompted_text = extract_prompts(cleaned_text)
    logger.debug("%s",f"{type(prompt_map)} : {prompt_map}, {type(deprompted_text)} {deprompted_text} )")
    system_map, generation_text = extract_partial_mappings(deprompted_text)
    logger.debug("%s",f"{type(system_map)} : {system_map}, {type(generation_text)} {generation_text} )")
    generation_map = convert_str_to_dict(generation_text)
    logger.debug("%s",f"{type(generation_map)} : {generation_map} )")
    return {"Prompts": prompt_map, "Generation_Data": generation_map, "System": system_map}

def parse_metadata(file_path_named: str) -> dict:
    """
    Extract the metadata from the header of an image file\n
    :param file_path_named: The file to open
    :return: The metadata from the header of the file
    """
    header_chunks = open_png_header(file_path_named)
    if header_chunks is not None and not isinstance(header_chunks, dict):
        logger.debug("%s",f"{next(iter(header_chunks))}")
    metadata = None

    if next(iter(header_chunks)) == 'parameters': # A1111 format
        metadata = arrange_webui_metadata(header_chunks)
    elif next(iter(header_chunks)) == 'prompt': # ComfyUI format
        metadata = arrange_nodeui_metadata(header_chunks)

    return metadata
