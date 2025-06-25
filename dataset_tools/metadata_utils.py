# dataset_tools/metadata_utils.py
import re


def json_path_get_utility(data_container: any, path_str: str | None) -> any:
    if not path_str:
        return data_container
    keys = path_str.split(".")
    current = data_container
    for key_part in keys:
        if current is None:
            return None
        match = re.fullmatch(r"(\w+)\[(\d+)\]", key_part)  # e.g. Options[0]
        if match:
            array_key, index_str = match.groups()
            index = int(index_str)
            if (
                not isinstance(current, dict)
                or array_key not in current
                or not isinstance(current[array_key], list)
                or index >= len(current[array_key])
            ):
                return None
            current = current[array_key][index]
        elif key_part.startswith("[") and key_part.endswith("]"):  # e.g. [0]
            if not isinstance(current, list):
                return None
            try:
                index = int(key_part[1:-1])
                if index >= len(current):
                    return None
                current = current[index]
            except ValueError:
                return None
        elif isinstance(current, dict) and key_part in current:
            current = current[key_part]
        else:
            return None
    return current

def get_a1111_kv_block_utility(a1111_string: str) -> str:
    if not isinstance(a1111_string, str):
        return ""
    neg_prompt_match = re.search(r"\nNegative prompt:", a1111_string, re.IGNORECASE)
    param_start_keywords = [
        "Steps:", "Sampler:", "CFG scale:", "Seed:", "Size:",
        "Model hash:", "Model:", "Version:",
        # Add any other keywords that reliably precede the K/V block
    ]


    # Find the earliest occurrence of any parameter keyword after the prompt
    # This logic assumes parameters are introduced by these keywords on new lines.
    # A more robust parser might handle inline parameters differently if that's a common case.

    # Determine the starting point of the parameter block more carefully.
    # The block often starts AFTER "Negative prompt:" and its content,
    # OR it starts directly with "Steps:", "Sampler:", etc. if no negative prompt.

    block_start_index = 0
    if neg_prompt_match:
        # If negative prompt exists, parameters start after it.
        # We need to find where the negative prompt *text* ends and the KV pairs begin.
        # Search for the KV keywords *after* the "Negative prompt:" line.
        search_after_neg_prompt_text_index = neg_prompt_match.end()

        # Find the first KV keyword after the negative prompt text
        first_kv_after_neg = len(a1111_string)
        substring_after_neg = a1111_string[search_after_neg_prompt_text_index:]

        for keyword in param_start_keywords:
            match = re.search(rf"^\s*{re.escape(keyword)}", substring_after_neg, re.MULTILINE) # Check start of lines
            if match:
                first_kv_after_neg = min(first_kv_after_neg, match.start())

        if first_kv_after_neg < len(substring_after_neg):
            block_start_index = search_after_neg_prompt_text_index + first_kv_after_neg
        else: # No KV keywords found after negative prompt text, maybe no params or malformed.
            return ""
    else:
        # No negative prompt, parameters start with the first KV keyword found anywhere.
        first_kv_overall = len(a1111_string)
        for keyword in param_start_keywords:
            match = re.search(rf"\n{re.escape(keyword)}", a1111_string) # Look for keyword on a new line
            if match:
                first_kv_overall = min(first_kv_overall, match.start())

        if first_kv_overall < len(a1111_string):
            block_start_index = first_kv_overall
        else: # No KV keywords found at all
            return ""

    return a1111_string[block_start_index:].strip()
