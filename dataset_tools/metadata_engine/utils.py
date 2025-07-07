# dataset_tools/metadata_engine/utils.py
import re


def get_a1111_kv_block_utility(data: str) -> str:
    """Extract the key-value parameter block from A1111 format string.

    A1111 format typically has:
    - Positive prompt (first part)
    - Negative prompt: <negative text>
    - Parameters: Steps: X, Sampler: Y, CFG scale: Z, etc.

    Returns the parameter block portion.
    """
    if not isinstance(data, str):
        return ""

    # Look for patterns that indicate start of parameter block
    # Common A1111 parameters: Steps, Sampler, CFG scale, Seed, Size, etc.
    param_patterns = [
        r"\bSteps:\s*\d+",
        r"\bSampler:\s*\w+",
        r"\bCFG scale:\s*[\d.]+",
        r"\bSeed:\s*-?\d+",
        r"\bSize:\s*\d+x\d+",
    ]

    # Find the first occurrence of any parameter pattern
    earliest_match = None
    earliest_pos = len(data)

    for pattern in param_patterns:
        match = re.search(pattern, data, re.IGNORECASE)
        if match and match.start() < earliest_pos:
            earliest_pos = match.start()
            earliest_match = match

    if earliest_match:
        # Return everything from the first parameter to the end
        return data[earliest_pos:].strip()

    return ""


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
