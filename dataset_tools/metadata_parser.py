#// SPDX-License-Identifier: CC0-1.0
#// --<{ Ktiseos Nyx }>--
"""為使用者介面清理和安排元資料"""

# pylint: disable=line-too-long

from importlib.readers import FileReader
import re
import json
from json import JSONDecodeError
from typing import Tuple, List

from dataset_tools import logger, EXC_INFO
from dataset_tools.access_disk import FileReader
from dataset_tools.correct_types import IsThisNode, BracketedDict, ListOfDelineatedStr

from pydantic import ValidationError, TypeAdapter


def delineate_by_esc_codes(text_chunks: dict, extra_delineation: str = "'Negative prompt'") -> list:
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
    logger.debug('clean_segments:: %s', f'{type(clean_segments)} {clean_segments}')
    return clean_segments


def extract_prompts(clean_segments: list) -> Tuple[dict, str]:
     """
     Split string by pre-delineated tag information\n
     :param cleaned_text: Text without escape codes
     :return: A dictionary of prompts and a str of metadata
     """
     deprompted_segments = []
     prompt_metadata = {"Positive prompt": clean_segments[0], "Negative prompt": clean_segments[1].strip('Negative prompt: ')}
     deprompted_text = " ".join(clean_segments[2:])
     return prompt_metadata, deprompted_text


def validate_dictionary_structure(possibly_invalid: str) -> str:
    """
    Take a string and prepare it for a conversion to a dict map\n
    :param possibly_invalid: The string to prepare
    :tyye possibly_invalid : `str`
    :return: A correctly formatted string ready for json.loads/dict conversion operations
    """
    logger.debug('possibly_invalid:: %s', f'{type(possibly_invalid)} {possibly_invalid}')
    key, bracketed_kv_pairs = possibly_invalid
    bracketed_kv_pairs = BracketedDict(brackets=bracketed_kv_pairs)

    # There may also need to be a check for quotes here

    valid_kv_pairs = BracketedDict.model_validate(bracketed_kv_pairs)
    kv_dict_annotated = dict(valid_kv_pairs)
    logger.debug('kv_dict_annotated:: %s', f'{type(kv_dict_annotated)} {kv_dict_annotated}')
    pair_string = str(kv_dict_annotated['brackets']).replace("\'","\"") # Remove the annotations left from pydantic
    #form_dict = json.loads(str(quotes))
    return pair_string


def extract_dict_by_delineation(deprompted_text: str) -> Tuple[dict, list]:
    """
    Split a string with partial dictionary delineations into a dict\n
    :param cleaned_text: Text without escape codes
    :return: A freeform string and a partially-organized list of metadata
    """
    def repair_flat_dict(traces_of_kv_pairs: List[str]) -> dict:
        """
        Convert a list with the first element as a key into a string with delinations \n
        :param traces_of_kv_pairs: that has a string with dictionary delineations as its second value\n
        Examples - List[str]`['Key', '{Key, Value}'] , ['Key:', ' "Key": "Value" '] `\n
        NOT `"[Key, Key, Value]"` or other improper dicts\n
        :type traces_of_kv_pairs: `list
        :return: A corrected dictionary structure from the kv pairs
        """
        reformed_sub_dict = {}
        validated_string = validate_dictionary_structure(traces_of_kv_pairs)
        return validated_string

    # pattern_types = [r"\s*([^:,]+):\s*([^,]+)"]  #Match A1111 style regex
    key_value_trace_patterns = [r' (\w*): ([{].*[}]),', r' (\w*\s*\w+): (["].*["]),'] #match pattern
    repaired_sub_dict = {}
    logger.debug('deprompted_text:: %s', f'{type(deprompted_text)} {deprompted_text}')  #Check this!
    remaining_text = deprompted_text

    #Main loop, run through regex patterns
    for pattern in key_value_trace_patterns: #if this is a dictionary
        traces_of_pairs = re.findall(pattern, deprompted_text) # Search matching text in the original string
        if traces_of_pairs:
            logger.debug('traces_of_pairs:: %s', f'{type(traces_of_pairs)} {traces_of_pairs}')
            delineated_str =  ListOfDelineatedStr(convert=traces_of_pairs)
            key, _  = next(iter(traces_of_pairs))
            reformed_sub_dict = getattr(delineated_str, next(iter(delineated_str.model_fields)))
            repaired_sub_dict[key] = repair_flat_dict(reformed_sub_dict)
            remaining_text = re.sub(pattern, "", remaining_text, 1) # Remove matching text in the original string
        #Handle for no match on generation as well

        else: # Safely assume this is not a dictionary
            return {}, remaining_text
    return repaired_sub_dict, remaining_text


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


def clean_with_json(prestructured_data: dict) -> dict:
    """
    Use json loads to arrange half-formatted dict into valid dict\n
    :param prestructured_data: A dict with a single working key
    :param key_name: The single working key name
    :return: A formatted dictionary object
    """
    try:
        cleaned_data = json.loads(prestructured_data)
    except JSONDecodeError as error_log:
        logger.info("Attempted to parse invalid formatting on %s", f"{prestructured_data} {error_log}", exc_info=EXC_INFO)
        return None
    return cleaned_data

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
    for key_name in nested_map:
        is_this_node = IsThisNode()
        next_layer = nested_map[key_name]
        logger.debug('key:: %s', f'{type(key_name)} {key_name}')
        logger.debug('next_layer:: %s', f'{type(next_layer)} {next_layer}')
        is_this_node.data.validate_python(next_layer) #be sure we have the right data
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

    if header_data:
        dirty_metadata =header_data["prompt"]
        clean_metadata = clean_with_json(dirty_metadata)
        logger.debug('clean_metadata:: %s', f'{type(clean_metadata)} {clean_metadata}')
        prompt_map = {}
        generation_map = {}
        prompt_keys = ["Positive prompt", "Negative prompt", "Prompt"]
        node_keys = ["CLIPTextEncode","CLIPTextEncodeFlux","CLIPTextEncodeSD3", "CLIPTextEncodeSDXL","CLIPTextEncodeHunyuanDiT"]
        for encoder_type in node_keys:
            renamed_metadata = rename_next_keys_of(clean_metadata, encoder_type, prompt_keys)

        generation_map = renamed_metadata.copy()
        for keys in prompt_keys:
            if renamed_metadata.get(keys) is not None:
                logger.debug('renamed_metadata.get(keys):: %s', f'{type(renamed_metadata.get(keys))} {renamed_metadata.get(keys)}')
                prompt_map[keys] = renamed_metadata[keys]
                generation_map.pop(keys)
        return {"Prompts": prompt_map, "Generation_Data": generation_map}


def arrange_webui_metadata(header_data: str) -> dict:
    """
    Using the header from a file, send to multiple formatting, cleaning, and parsing, processes \n
    Return format : {"Prompts": , "Settings": , "System": } \n
    :param header_data: Header data from a file
    :return: Metadata in a standardized format
    """
    cleaned_text = delineate_by_esc_codes(header_data)
    logger.debug('cleaned_text:: %s', f'{type(cleaned_text)} {cleaned_text}')
    prompt_map, deprompted_text = extract_prompts(cleaned_text)
    logger.debug('prompt_map:: %s', f'{type(prompt_map)} {prompt_map}')
    logger.debug('deprompted_text:: %s', f'{type(deprompted_text)} {deprompted_text}')
    system_map, generation_text = extract_dict_by_delineation(deprompted_text)
    logger.debug('system_map:: %s', f'{type(system_map)} {system_map}')
    logger.debug('generation_text:: %s', f'{type(generation_text)} {generation_text}')
    generation_map = make_paired_str_dict(generation_text)
    logger.debug('generation_map:: %s', f'{type(generation_map)} {generation_map}')
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
            return {"Prompts": "No Data", "Generation_Data": "No Data", "System": "No Data"} # return placeholders
    return metadata

