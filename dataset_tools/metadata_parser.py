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
    NodeWorkflow,
    BracketedDict,
    ListOfDelineatedStr,
    UpField,
    DownField,
    NodeNames,
)


# /______________________________________________________________________________________________________________________ ComfyUI format


# @debug_monitor
def clean_with_json(prestructured_data: dict, first_key: str) -> dict:
    """
    Use json loads to arrange half-formatted dict into valid dict\n
    :param prestructured_data: A dict with a single working key
    :param key_name: The single working key name
    :return: A formatted dictionary object
    """
    try:
        cleaned_data = json.loads(prestructured_data[first_key])
    except JSONDecodeError as error_log:
        nfo("Attempted to parse invalid formatting on", prestructured_data, error_log)
        return None
    return cleaned_data


@debug_monitor
def validate_typical(nested_map: dict, key_name: str):
    """
    Check metadata structure and ensure it meets expectations\n
    :param nested_map: metadata structure
    :type nested_map: dict
    :return: The original node map if valid, or None
    """

    is_this_node = IsThisNode()
    if next(iter(nested_map[key_name])) in NodeWorkflow.__annotations__.keys():
        try:
            is_this_node.workflow.validate_python(nested_map)
        except ValidationError as error_log:  #
            nfo("%s", f"Node workflow not found, returning NoneType {key_name}", error_log)
        else:
            return nested_map[key_name]
    else:
        try:
            is_this_node.data.validate_python(nested_map[key_name])  # Be sure we have the right data
        except ValidationError as error_log:
            nfo("%s", "Node data not found", error_log)
        else:
            return nested_map[key_name]

    nfo("%s", f"Node workflow not found {key_name}")
    raise KeyError(f"Unknown format for dictionary {key_name} in {nested_map}")


def search_for_prompt_in(this_layer, previously_extracted_data, node_id):
    if node_id in this_layer and this_layer[node_id] in NodeNames.ENCODERS:
        for field_name, contents in this_layer[NodeNames.DATA_KEYS[node_id]].items():
            if isinstance(contents, str):
                if field_name == "text":
                    add_label = next((x for x in NodeNames.PROMPT_LABELS if x not in previously_extracted_data), "")
                    prompt_data = {add_label: contents}
                else:
                    prompt_data = {field_name: contents}
                return prompt_data

    elif "inputs" in this_layer:
        return {k: v for k, v in this_layer["inputs"].items() if v and not isinstance(v, list)}
    return {}


def rename_prompt_keys_of(normalized_clean_data):
    previously_extracted_data = {}
    for layer in normalized_clean_data:
        this_layer = validate_typical(normalized_clean_data, layer)

        if this_layer:
            search_terms = ((n, nc) for n in NodeNames.DATA_KEYS for nc in NodeNames.ENCODERS)
            for node_id, _ in search_terms:
                previously_extracted_data.update(search_for_prompt_in(this_layer, previously_extracted_data, node_id))

    return previously_extracted_data


def redivide_nodeui_data_in(header: str, first_key: str) -> Tuple[dict]:
    """
    Orchestrate tasks to recreate dictionary structure and extract relevant keys within\n
    :param header: Embedded dictionary structure
    :type variable: str
    :param section_titles: Key names for relevant data segments
    :type variable: list
    :return: Metadata dict, or empty dicts if not found
    """

    def pack_prompt(mixed_data: dict):
        """Convert dictionary to expected formatting"""
        packed_data_pass_1 = {k: mixed_data.get(k) for k in NodeNames.PROMPT_LABELS if k in mixed_data}
        packed_data_pass_2 = {k: mixed_data.get(k) for k in NodeNames.PROMPT_NODE_FIELDS if k in mixed_data}
        prompt_data = packed_data_pass_1 | packed_data_pass_2
        return prompt_data

    try:
        jsonified_header = clean_with_json(header, first_key)
        if first_key == "workflow":
            normalized_clean_data = {"1": jsonified_header}  # To match normalized_prompt_structure format
        else:
            normalized_clean_data = jsonified_header
        sorted_header_data = rename_prompt_keys_of(normalized_clean_data)
    except KeyError as error_log:
        nfo("%s", "No key found.", error_log)
        return {"": UpField.PLACEHOLDER, " ": UpField.PLACEHOLDER}
    return pack_prompt(sorted_header_data), {k: v for k, v in sorted_header_data.items() if k not in NodeNames.PROMPT_LABELS and k not in NodeNames.PROMPT_NODE_FIELDS}


def arrange_nodeui_metadata(header_data: dict) -> dict:
    """
    Using the header from a file, run formatting and parsing processes \n
    Return format : {"Prompts": , "Settings": , "System": } \n
    :param header_data: Header data from a file
    :return: Metadata in a standardized format
    """

    extracted_prompt_pairs, generation_data_pairs = redivide_nodeui_data_in(header_data, "prompt")
    if extracted_prompt_pairs == {}:
        gen_pairs_copy = generation_data_pairs.copy()
        extracted_prompt_pairs, second_gen_map = redivide_nodeui_data_in(header_data, "workflow")
        generation_data_pairs = second_gen_map | gen_pairs_copy
    return {UpField.PROMPT: extracted_prompt_pairs or {"": UpField.PLACEHOLDER}, DownField.GENERATION_DATA: generation_data_pairs}


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
def validate_mapping_bracket_pair_structure_of(possibly_invalid: str) -> str:
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
        validated_string = validate_mapping_bracket_pair_structure_of(reformed_sub_dict)
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
    Return format : {"Prompts": , "Settings": , "System": }\n
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


# /______________________________________________________________________________________________________________________ EXIF Tags


@debug_monitor
def arrange_exif_metadata(header_data: dict) -> dict:
    """Arrange EXIF data into correct format"""
    metadata = {
        UpField.TAGS: {UpField.EXIF: {key: value} for key, value in header_data.items() if (key != "icc_profile" or key != "exif")},
        DownField.ICC: {DownField.DATA: header_data.get("icc_profile")},
        DownField.EXIF: {DownField.DATA: header_data.get("exif")},
    }
    return metadata


# /______________________________________________________________________________________________________________________ Module Interface


@debug_monitor
def coordinate_metadata_ops(header_data: dict | str, metadata: dict = None) -> dict:
    """
    Process data based on identifying contents\n
    :param header_data: Metadata extracted from file
    :type header_data: dict
    :param datatype: The kind of variable storing the metadata
    :type datatype: str
    :param metadata: The filtered output extracted from header data
    :type metadata: dict
    :return: A dict of the metadata inside header data
    """

    has_prompt = isinstance(header_data, dict) and header_data.get("prompt")
    has_params = isinstance(header_data, dict) and header_data.get("parameters")
    has_tags = isinstance(header_data, dict) and ("icc_profile" in header_data or "exif" in header_data)

    if has_prompt:
        metadata = arrange_nodeui_metadata(header_data)
    elif has_params:
        metadata = arrange_webui_metadata(header_data)
    elif has_tags:
        metadata = arrange_exif_metadata(header_data)
    elif isinstance(header_data, dict):
        try:
            metadata = {UpField.JSON_DATA: json.loads(f"{header_data}")}
        except JSONDecodeError as error_log:
            nfo("JSON Decode failed %s", error_log)
    if not metadata and isinstance(header_data, str):
        metadata = {UpField.DATA: header_data}
    elif not metadata:
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
        if metadata == {UpField.PLACEHOLDER: {"": UpField.PLACEHOLDER}} or not isinstance(metadata, dict):
            nfo("Unexpected format", file_path_named)
    return metadata
