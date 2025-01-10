"""為使用者介面清理和安排元資料"""
# pylint: disable=line-too-long

from importlib.readers import FileReader
import re
import json
from json import JSONDecodeError
from typing import Tuple
from dataset_tools import logger, EXC_INFO
from dataset_tools.access_disk import FileReader
#from dataset_tools.type_checks import ValidityCheck, BracketedDict # type adapter has been removed

from pydantic import ValidationError

def delineate_escape_codes(text_chunks: dict, extra_delineation: str = "'Negative prompt'") -> list:
     """
     Format text from header file by escape-code delineations\n
     :param text_chunk: Data from a file header
     :return: text data in a dict structure
     """
     replace_strings = ["\xe2\x80\x8b", "\x00", "\u200b", "\n", extra_delineation]
     dirty_string = text_chunks.get("parameters")
     if dirty_string is None:
         dirty_string = text_chunks.get("exif") #try to get exif if present
     if dirty_string is None:
         return [] #If still None, then just return an empty list
     
     if isinstance(dirty_string, bytes): # Check if it is bytes
         try:
             dirty_string = dirty_string.decode('utf-8') # If it is, decode into utf-8 format
         except UnicodeDecodeError: # Catch exceptions if they fail to decode
             logger.info("Could not decode string") # Log it
             return [] #Return nothing if decoding fails


     segments = [dirty_string] # All string operations after this should be safe

     for buffer in replace_strings:
         new_segments = []
         for delination in segments:  # Split segments and all sub-segments of this string
             split_segs = delination.split(buffer)
             new_segments.extend(s for s in split_segs if s)  # Skip empty strings
         segments = new_segments

     clean_segments = segments

     logger.debug("%s", f"{clean_segments}")
     return clean_segments


def extract_prompts(clean_segments: list) -> Tuple[dict, str, str]:
     """
     Split string by pre-delineated tag information\n
     :param cleaned_text: Text without escape codes
     :return: A dictionary of prompts and a str of metadata
     """
     deprompted_segments = []
     prompt_metadata = {"Positive prompt": clean_segments[0], "Negative prompt": clean_segments[1].strip('Negative prompt: ')}
     #for i in range(len(clean_segments) - 2): # This line is the problem, it removes everything from the text
     #    deprompted_segments.append(clean_segments[i + 2]) # This line is the problem, it removes everything from the text
     deprompted_text = "" #"".join(deprompted_segments) # Remove this, we want the remaining text
     remaining_text = " ".join(clean_segments[2:])
     return prompt_metadata, deprompted_text, remaining_text


def extract_partial_mappings(deprompted_text: str) -> tuple[dict, str]:
         """
         Split string by pre-delineated tag information\n
         :param cleaned_text: Text without escape codes
         :return: A freeform string and a partially-organized list of metadata
         """
         logger.debug(f"deprompted_text: {deprompted_text}") # New debug line
         pattern_types = [r"\s*([^:,]+):\s*([^,]+)"]  #Match A1111 style regex
         valid_mapping = {}
         remaining_text = deprompted_text # Correct variable is now used
         logger.debug(f"remaining_text: {remaining_text}")  #Check this!
         for pattern in pattern_types:
             match = re.findall(pattern, remaining_text)
             if match:
                 for key,value in match:
                     valid_mapping[key.strip()] = value.strip()
                     remaining_text = re.sub(pattern, "", remaining_text, 1) # remove the matched text

         # Match any character after "### Generation:" until a line break or "###"
         generation_pattern = re.compile(r"### Generation:\s*(.*?)(?:###|$)", re.DOTALL)
         match = generation_pattern.findall(deprompted_text)

         generation_text = match[0] if match else "" #Handle for no match on generation as well

         return valid_mapping, generation_text

def make_paired_str_dict(text_to_convert: str) -> dict:
    """
    Convert an unstructured metadata string into a dictionary\n
    :param dehashed_data: Metadata tags with quote and bracket delineated features removed
    :return: A valid dictionary structure with identical information
    """
    segmented = text_to_convert.split(", ")
    delineated = [item.split(": ") for item in segmented if isinstance(item, str) and ": " in item]
    try:
        converted_text = {el[0]: el[1] for el in delineated if len(el) == 2}
    except IndexError as error_log:
        logger.info("Index position for prompt input out of range, %s", f"{text_to_convert} at {delineated}, {error_log}", exc_info=EXC_INFO)
        converted_text = None
    return converted_text


def clean_with_json(prestructured_data: dict, key_name: str) -> dict:
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
        return None
    return cleaned_data

#  search_pair: dict,
def rename_next_keys_of(nested_map: dict, search_key: str, new_labels: list) -> dict:
    """
    Divide the next layer of a nested ditionary by search criteria\n
    Then rename the matching values\n
    :param nested_map: Where to start in the nested dictionary
    :param search_key: Key to retrieve the data beneath
    :param new_labels: A list of labels to apply to the new dictionary
    :return: The combined dictionary with specified keys
    """
    extracted_data = {}
    for k in nested_map:
        #does_this = ValidityCheck() # TypeAdapter was removed, this class is not necessary.
        next_layer = nested_map[k]
        #does_this.node_data.validate_python(next_layer) # TypeAdapter was removed, this class is not necessary.
        if not isinstance(new_labels, list):
            raise ValidationError("Not list format in %s", new_labels)
        else:
            if search_key in next_layer.get('class_type', ""): # added a `.get` to avoid errors
                next_layer['class_type'] = next(iter(x for x in new_labels if x not in extracted_data))
                extracted_data[next_layer['class_type']] = next_layer['inputs'].get(next(iter(next_layer['inputs']))) # added a `.get` to avoid errors
            else:
                extracted_data[next_layer['class_type']] = next_layer['inputs']

    return extracted_data

def arrange_nodeui_metadata(header_data: dict) -> dict:
    """
    Using the header from a file, run formatting and parsing processes \n
    Return format : {"Prompts": , "Settings": , "System": } \n
    :param header_data: Header data from a file
    :return: Metadata in a standardized format
    """
    cleaned_metadata = clean_with_json(header_data, "prompt")
    if cleaned_metadata is None:
         return {} # Handle the case where the metadata is invalid

    prompt_map = {}
    generation_map = {}
    prompt_keys = ["Positive prompt", "Negative prompt", "Prompt"]
    node_keys = ["CLIPTextEncode","CLIPTextEncodeFlux","CLIPTextEncodeSD3", "CLIPTextEncodeSDXL","CLIPTextEncodeHunyuanDiT"]
    for encoder_type in node_keys:
        renamed_metadata = rename_next_keys_of(cleaned_metadata, encoder_type, prompt_keys)

    generation_map = renamed_metadata.copy()
    for keys in prompt_keys:
        if renamed_metadata.get(keys) is not None:
            prompt_map[keys] = renamed_metadata[keys]
            generation_map.pop(keys, None)
    return {"Prompts": prompt_map, "Generation_Data": generation_map}


def arrange_webui_metadata(header_data: str) -> dict:
    """
    Using the header from a file, send to multiple formatting, cleaning, and parsing, processes \n
    Return format : {"Prompts": , "Settings": , "System": } \n
    :param header_data: Header data from a file
    :return: Metadata in a standardized format
    """
    cleaned_text = delineate_escape_codes(header_data)
    logger.debug("%s", f"{type(cleaned_text)} : {cleaned_text} )")
    prompt_map, deprompted_text, remaining_text = extract_prompts(cleaned_text) # Updated line, variable now used in next step
    logger.debug("%s", f"{type(prompt_map)} : {prompt_map}, {type(deprompted_text)} {deprompted_text} )")
    system_map, generation_text = extract_partial_mappings(remaining_text) #Corrected this
    logger.debug("%s", f"{type(system_map)} : {system_map}, {type(generation_text)} {generation_text} )")
    generation_map = make_paired_str_dict(generation_text)
    logger.debug("%s", f"{type(generation_map)} : {generation_map} )")
    return {"Prompts": prompt_map, "Generation_Data": generation_map, "System": system_map}


def parse_metadata(file_path_named: str) -> dict:
    """
    Extract the metadata from the header of an image file\n
    :param file_path_named: The file to open
    :return: The metadata from the header of the file
    """
    reader = FileReader()
    metadata = None
    header_data = reader.read_header(file_path_named)
    if header_data is not None:
        if isinstance(header_data, dict) and header_data.get("prompt"):
            metadata = arrange_nodeui_metadata(header_data)
        elif isinstance(header_data, dict) or isinstance(header_data, str):
             metadata = arrange_webui_metadata(header_data)

        else:
            logger.error(f"Unexpected metadata type: {type(header_data)}")
            return {}
    return metadata
