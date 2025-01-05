
import re
import json
from collections import defaultdict
from dataset_tools import logger
from PIL import Image



def open_jpg_header(file_path_named: str) -> dict:
    """
    Open jpg format files\n
    :param file_path_named: `str` The path and file name of the jpg file
    :return: `Generator[bytes]` Generator element containing header tags
    """
    from PIL.ExifTags import TAGS
    pil_img = Image.open(file_path_named)
    exif_info = pil_img._getexif()
    exif = {TAGS.get(k, k): v for k, v in exif_info.items()}
    return exif


def open_png_header(file_path_named: str) -> dict:
    """
    Open png format files\n
    :param file_path_named: `str` The path and file name of the png file
    :return: `Generator[bytes]` Generator element containing header bytes
    """
    pil_img = Image.open(file_path_named)
    if pil_img == None:
        pil_img.load()
    text_chunks = pil_img.info
    logger.debug(text_chunks)
    return text_chunks


def format_chunk(text_chunks: dict) -> dict:
    """
    Turn raw bytes into utf8 formatted text\n
    :param text_chunk: `bytes` Data from a file header
    :return: `dict` text data in a dict structure
    """
    replace_strings = ['\xe2\x80\x8b','\x00', '\x00', '\u200b',]
    dirty_string = text_chunks.get('parameters')
    for buffer in replace_strings:
        segmented_string = dirty_string.split(buffer)
        clean_segments = [seg.replace(buffer, '') for seg in segmented_string]
        cleaned_text = ' '.join(map(str,clean_segments)).replace('\n',',')

    logger.debug(f"{cleaned_text}")
    return cleaned_text


def extract_enclosed_values(cleaned_text: str) -> tuple[str, list]:
    """
    Split string by pre-delineated tag information\n
    :param cleaned_text: `str` Text without escape codes
    :return: `tuple[str, list]` A freeform string and a partially-organized list of metadata
    """
    pattern = r'(TI hashes:\s*"([^"]*)")|(Hardware Info:\s*"([^"]*)")|Hashes: (\{.*?\})'
    prestructured_data = [x for x in re.findall(pattern, cleaned_text) if any(y for y in x)]

    structured_dict = {}
    for item in prestructured_data:
        # Only keep non-empty groups
        if item[1]:   structured_dict[item[0]] = item[1]
        elif item[3]: structured_dict[item[2]] = item[3]
        else:         structured_dict['Hashes'] = item[4]

    dehashed_text = re.sub(pattern, ',', cleaned_text).strip()
    logger.debug(f"{dehashed_text}")
    logger.debug(f"{structured_dict}")
    return dehashed_text, structured_dict

def structured_metadata_list_to_dict(prestructured_data: list) -> dict:
    """
    Convert delineated metadata into a dictionary\n
    :param prestructured_data: `list` Metadata tags pre-separated into an approximate list format
    :return: `dict` A valid dictionary structure with identical information
    """
    system_metadata = {}
    for key in prestructured_data:
        if key == 'Hashes':
            system_metadata[key] = json.loads(prestructured_data[key])
        elif ': "' in key and ':' in key:  # Handle TI hashes, split by colon and quote
            ti_hash_key = re.sub(r': .*$', '', key).strip()
            system_metadata[ti_hash_key] = prestructured_data[key]
        else: # Hardware Info, strip quotes"""
            system_metadata[key.split(' ', 1)[0]] = prestructured_data[key].strip('"')
    logger.debug(f"{system_metadata}")
    return system_metadata


def dehashed_metadata_str_to_dict(dehashed_text: str) -> dict:
    """
    Convert an unstructured metadata string into a dictionary\n
    :param dehashed_data: `str` Metadata tags with quote and bracket delineated features removed
    :return: `dict` A valid dictionary structure with identical information
    """

    #pairs = [pair.strip() for pair in dehashed_text.split(',')]
    pos_match = re.match(r'(.*?POS \s*)', dehashed_text)
    pos_key_val = {pos_match.group(1): dehashed_text[:dehashed_text.find(',Negative')].strip()} if pos_match else {}

    # Rest of dehashed as a dict:
    dehashed_pairs = [p for p in dehashed_text.split(',') if ': ' in p and p.strip()]
    neg_side = dehashed_pairs[0].split('Steps:')
    match = re.search(r'Negative prompt:\s*(.*?)Steps', dehashed_pairs[0])
    negative = match.group(1) if match else None
    logger.debug(negative)
    logger.debug(neg_side)

    logger.debug(negative)
    logger.debug(f"{dehashed_pairs}")

    generation_metadata = {k: v for k, v in (pair.split(': ', 1) for pair in dehashed_pairs)}
    logger.debug(generation_metadata)

    positive = next(iter(pos_key_val)) # Sample positive prompt
    positive_prompt = pos_key_val[positive] # Separate prompts

    prompt_metadata = {"Positive prompt" : positive_prompt } | generation_metadata
    logger.debug(f"{prompt_metadata}")
    return prompt_metadata, generation_metadata

def parse_metadata(file_path_named: str) -> dict:
    """
    Extract the metadata from the header of an image file\n
    :param file_path_named: `str` The file to open
    :return: `dict` The metadata from the header of the file
    """
    header_chunks = open_png_header(file_path_named)
    if next(iter(header_chunks)) == 'parameters':
        logger.debug(next(iter(header_chunks)))
        cleaned_text = format_chunk(header_chunks)
        dehashed_text, structured_dict = extract_enclosed_values(cleaned_text)
        system_metadata = structured_metadata_list_to_dict(structured_dict)
        prompt_metadata, generation_metadata = dehashed_metadata_str_to_dict(dehashed_text)
        logger.debug(f"{prompt_metadata | generation_metadata | system_metadata}")
    elif next(iter(header_chunks)) == 'prompt':
        """Placeholder"""
    metadata = {"Prompts": prompt_metadata, "Settings": generation_metadata, "System": system_metadata}
    return metadata


    # hash_sample = re.search(r', cleaned_text)
    # hash_sample_structure = eval(hash_sample.group(1)) # Return result 1 if found else 0
    #dehashed_text = re.sub(r'Hashes: \{.*?\}', '', cleaned_text).strip()