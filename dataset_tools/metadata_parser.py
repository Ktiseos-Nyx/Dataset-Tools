# // SPDX-License-Identifier: CC0-1.0
# // --<{ Ktiseos Nyx }>--

"""為使用者介面清理和安排元資料"""

# pylint: disable=line-too-long

import re
import json
from json import JSONDecodeError
from typing import Tuple, List

from pydantic import ValidationError

from dataset_tools.logger import debug_monitor, debug_message
from dataset_tools.logger import info_monitor as nfo
from dataset_tools.access_disk import MetadataFileReader
from dataset_tools.correct_types import (
    IsThisNode,
    BracketedDict,
    ListOfDelineatedStr,
    UpField,
    DownField,
    NodeNames,
)


# /______________________________________________________________________________________________________________________ ComfyUI format


@debug_monitor
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
        nfo("Attempted to parse invalid formatting on", prestructured_data, error_log)
        return None
    return cleaned_data


@debug_monitor
def rename_next_keys_of(nested_map: dict, search_key: str, new_labels: list) -> dict:
    """
    Divide the next layer of a nested dictionary by search criteria\n
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
        is_this_node.data.validate_python(next_layer)  # be sure we have the right data
        if isinstance(new_labels, list):
            class_type = next_layer.get("class_type", False)
            if search_key in class_type:
                class_type_field = next(iter(x for x in new_labels if x not in extracted_data), "")  # Name of prompt
                inputs_field = next_layer.get("inputs", UpField.PLACEHOLDER).items()
                prompt_data = next(iter(v for k, v in inputs_field if isinstance(v, str)))
                if prompt_data:
                    extracted_data[class_type_field] = prompt_data
                    debug_message(prompt_data)

            else:
                node_inputs = next_layer.get("inputs", {"": UpField.PLACEHOLDER}).items()
                gen_data = "\n".join(f"{k}: {v}" for k, v in node_inputs if v is not None)
                if gen_data:
                    extracted_data[class_type] = gen_data

        else:
            raise ValidationError(f"Not list format in {new_labels}")

    return extracted_data


@debug_monitor
def arrange_nodeui_metadata(header_data: dict) -> dict:
    """
    Using the header from a file, run formatting and parsing processes \n
    Return format : {"Prompts": , "Settings": , "System": } \n
    :param header_data: Header data from a file
    :return: Metadata in a standardized format
    """

    if header_data:
        dirty_prompts = header_data.get("prompt")
        clean_metadata = clean_with_json(dirty_prompts)
        prompt_map = {}
        generation_map = {}
        prompt_keys = ["Positive prompt", "Negative prompt", "Prompt"]
        for encoder_type in NodeNames.ENCODERS:
            renamed_metadata = rename_next_keys_of(clean_metadata, encoder_type, prompt_keys)

        generation_map = renamed_metadata.copy()
        for keys in prompt_keys:
            if renamed_metadata.get(keys) is not None:
                prompt_map[keys] = renamed_metadata[keys]
                generation_map.pop(keys)
        if not prompt_map:
            prompt_map = {"": UpField.PLACEHOLDER}

        return {UpField.PROMPT: prompt_map, DownField.GENERATION_DATA: generation_map}
    return {"": UpField.PLACEHOLDER}


# /______________________________________________________________________________________________________________________ A4 format


@debug_monitor
def delineate_by_esc_codes(text_chunks: dict, extra_delineation: str = "'Negative prompt'") -> list:
    """
    Format text from header file by escape-code delineations\n
    :param text_chunk: Data from a file header
    :return: text data in a dict structure
    """
    segments = []
    replace_strings = ["\xe2\x80\x8b", "\x00", "\u200b", "\n", extra_delineation]
    dirty_string = text_chunks.get("parameters", text_chunks.get("exif", False))  # Try parameters, then "exif"
    if not dirty_string:
        return []  # If still None, then just return an empty list

    if isinstance(dirty_string, bytes):  # Check if it is bytes
        try:
            dirty_string = dirty_string.decode("utf-8")  # If it is, decode into utf-8 format
        except UnicodeDecodeError as error_log:  # Catch exceptions if they fail to decode
            nfo("Failed to decode", dirty_string, error_log)
            return []  # Return nothing if decoding fails

    segments = [dirty_string]  # All string operations after this should be safe

    for buffer in replace_strings:
        new_segments = []
        for delination in segments:  # Split segments and all sub-segments of this string
            split_segs = delination.split(buffer)
            new_segments.extend(s for s in split_segs if s)  # Skip empty strings
        segments = new_segments

    clean_segments = segments
    return clean_segments


@debug_monitor
def extract_prompts(clean_segments: list) -> Tuple[dict, str]:
    """
    Split string by pre-delineated tag information\n
    :param cleaned_text: Text without escape codes
    :type cleaned_text: list
    :return: A dictionary of prompts and a str of metadata
    """

    if len(clean_segments) <= 2:
        prompt_metadata = {
            "Positive prompt": clean_segments[0],
            "Negative prompt": "",
        }
        deprompted_text = " ".join(clean_segments[1:])
    elif len(clean_segments) > 2:
        prompt_metadata = {
            "Positive prompt": clean_segments[0],
            "Negative prompt": clean_segments[1].strip("Negative prompt':"),
        }
        deprompted_text = " ".join(clean_segments[2:])
    else:
        return None
    return prompt_metadata, deprompted_text


@debug_monitor
def validate_dictionary_structure(possibly_invalid: str) -> str:
    """
    Take a string and prepare it for a conversion to a dict map\n
    :param possibly_invalid: The string to prepare
    :type possibly_invalid: `str`
    :return: A correctly formatted string ready for json.loads/dict conversion operations
    """

    _, bracketed_kv_pairs = possibly_invalid
    bracketed_kv_pairs = BracketedDict(brackets=bracketed_kv_pairs)

    # There may also need to be a check for quotes here

    valid_kv_pairs = BracketedDict.model_validate(bracketed_kv_pairs)

    pair_string_checked = getattr(valid_kv_pairs, next(iter(valid_kv_pairs.model_fields)))  # Removes pydantic annotations
    pair_string = str(pair_string_checked).replace("'", '"')
    return pair_string


@debug_monitor
def extract_dict_by_delineation(deprompted_text: str) -> Tuple[dict, list]:
    """
    Split a string with partial dictionary delineations into a dict\n
    :param cleaned_text: Text without escape codes
    :return: A freeform string and a partially-organized list of metadata
    """

    def repair_flat_dict(traces_of_pairs: List[str]) -> dict:
        """
        Convert a list with the first element as a key into a string with delinations \n
        :param traces_of_kv_pairs: that has a string with dictionary delineations as its second value\n
        Examples - List[str]`['Key', '{Key, Value}'] , ['Key:', ' "Key": "Value" '] `\n
        NOT `"[Key, Key, Value]"` or other improper dicts\n
        :type traces_of_kv_pairs: `list
        :return: A corrected dictionary structure from the kv pairs
        """
        delineated_str = ListOfDelineatedStr(convert=traces_of_pairs)
        key, _ = next(iter(traces_of_pairs))
        reformed_sub_dict = getattr(delineated_str, next(iter(delineated_str.model_fields)))
        validated_string = validate_dictionary_structure(reformed_sub_dict)
        repaired_sub_dict[key] = validated_string
        return repaired_sub_dict

    key_value_trace_patterns = [
        # r"\s*([^:,]+):\s*([^,]+)",
        r" (\w*): ([{].*[}]),",
        r' (\w*\s*\w+): (["].*["]),',
    ]
    repaired_sub_dict = {}
    remaining_text = deprompted_text

    # Main loop, run through regex patterns
    for pattern in key_value_trace_patterns:  # if this is a dictionary
        traces_of_pairs = re.findall(pattern, remaining_text)  # Search matching text in the original string
        if traces_of_pairs:
            repair_flat_dict(traces_of_pairs)
            remaining_text = re.sub(pattern, "", remaining_text, 1)  # Remove matching text in the original string
        # Handle for no match on generation as well

        else:  # Safely assume this is not a dictionary
            return {}, remaining_text
    return repaired_sub_dict, remaining_text


@debug_monitor
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
        nfo("Index position for prompt input out of range", text_to_convert, "at", delineated, error_log)
        converted_text = None
    return converted_text


@debug_monitor
def arrange_webui_metadata(header_data: str) -> dict:
    """
    Using the header from a file, send to multiple formatting, cleaning, and parsing, processes \n
    Return format : {"Prompts": , "Settings": , "System": } \n
    :param header_data: Header data from a file
    :return: Metadata in a standardized format
    """
    cleaned_text = delineate_by_esc_codes(header_data)
    prompt_map, deprompted_text = extract_prompts(cleaned_text)
    system_map, generation_text = extract_dict_by_delineation(deprompted_text)
    generation_map = make_paired_str_dict(generation_text)
    return {
        UpField.PROMPT: prompt_map,
        DownField.GENERATION_DATA: generation_map,
        DownField.SYSTEM: system_map,
    }


# /______________________________________________________________________________________________________________________ Module Interface


@debug_monitor
def coordinate_metadata_ops(header_data: dict | str, metadata: dict = None) -> dict:
    """
    Process data based on identifying contents\n
    :param header_data: metadata extracted from file
    :type header_data: dict
    :param metadata: the filtered output extracted from header data
    :type metadata: dict
    :return: A dict of the metadata inside header data
    """
    is_dict = isinstance(header_data, dict)
    has_prompt = is_dict and header_data.get("prompt")
    has_params = is_dict and header_data.get("parameters")
    has_tags = is_dict and ("icc_profile" in header_data or "exif" in header_data)
    is_str = isinstance(header_data, str)

    if has_prompt:
        metadata = arrange_nodeui_metadata(header_data)
    elif has_params:
        metadata = arrange_webui_metadata(header_data)
    elif has_tags:
        metadata = {
            UpField.TAGS: {UpField.EXIF: {key: value} for key, value in header_data.items() if (key != "icc_profile" or key != "exif")},
            DownField.ICC: {DownField.DATA: header_data.get("icc_profile")},
            DownField.EXIF: {DownField.DATA: header_data.get("exif")},
        }
    elif is_dict:
        try:
            metadata = {UpField.JSON_DATA: json.loads(f"{header_data}")}
        except JSONDecodeError as error_log:
            nfo("JSON Decode failed %s", error_log)
            metadata = {UpField.DATA: header_data}
    elif is_str:
        metadata = {UpField.DATA: header_data}
    else:
        metadata = {UpField.PLACEHOLDER: {"": UpField.PLACEHOLDER}}

    return metadata


@debug_monitor
def parse_metadata(file_path_named: str) -> dict:
    """
    Extract the metadata from the header of an image file\n
    :param file_path_named: The file to open
    :return: The metadata from the header of the file
    """

    reader = MetadataFileReader()
    metadata = None
    header_data = reader.read_header(file_path_named)
    if header_data is not None:
        metadata = coordinate_metadata_ops(header_data)
        debug_message(metadata)
        if metadata == {UpField.PLACEHOLDER: {"": UpField.PLACEHOLDER}} or not isinstance(metadata, dict):
            nfo("Unexpected format", file_path_named)
    return metadata
