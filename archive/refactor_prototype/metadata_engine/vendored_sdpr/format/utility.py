# dataset_tools/vendored_sdpr/format/utility.py (Cleaned, Pruned, and No Unnecessary Constants Import)

__author__ = "receyuki"  # Original author
__filename__ = "utility.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools: Pruned for core parsing utilities.
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

# No external imports are needed for these specific utility functions.
# from ..constants import * # Not needed for the functions below

# --- Core String and Data Manipulation Utilities ---


def remove_quotes(string: str) -> str:
    """Removes single and double quotes from the beginning and end of a string."""
    s = str(string)  # Ensure input is a string
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def add_quotes(string: str) -> str:
    """Adds double quotes around a string."""
    return f'"{string!s}"'  # Ensure input is string


def concat_strings(base: str, addition: str, separator: str = ", ") -> str:
    """Concatenates two strings with a separator, handling cases where `base` might be empty."""
    base_str = str(base)  # Ensure base is a string
    addition_str = str(addition)  # Ensure addition is a string
    if base_str:  # If base has content
        return f"{base_str}{separator}{addition_str}"
    return addition_str  # Otherwise, just return the addition


# --- Generic Data Structure Utilities (if used by any vendored format parsers) ---


def merge_str_to_tuple(item1, item2) -> tuple:
    """Ensures both items are treated as tuples and concatenates them.
    If an item is not a tuple, it's wrapped in a single-element tuple.
    """
    t1 = item1 if isinstance(item1, tuple) else (item1,)
    t2 = item2 if isinstance(item2, tuple) else (item2,)
    return t1 + t2


def merge_dict(dict1: dict, dict2: dict) -> dict:
    """Merges dict2 into a copy of dict1.
    If a key exists in both dictionaries, their values are merged into a tuple
    using merge_str_to_tuple.
    """
    dict3 = dict1.copy()
    for k, v_from_dict2 in dict2.items():
        if k in dict3:
            dict3[k] = merge_str_to_tuple(dict3[k], v_from_dict2)
        else:
            dict3[k] = v_from_dict2
    return dict3


__all__ = [
    "add_quotes",
    "concat_strings",
    "merge_dict",
    "merge_str_to_tuple",
    "remove_quotes",
]
