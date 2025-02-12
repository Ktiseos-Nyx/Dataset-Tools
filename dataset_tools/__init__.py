# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""Initialize"""

import sys
import argparse

from importlib import metadata

if "pytest" not in sys.modules:
    parser = argparse.ArgumentParser(description="Set logging level.")
    group = parser.add_mutually_exclusive_group()

    levels = {"d": "DEBUG", "w": "WARNING", "e": "ERROR", "c": "CRITICAL", "i": "INFO"}
    choices = list(levels.keys()) + list(levels.values()) + [value.upper() for value in levels.values()]
    for short, long in levels.items():
        group.add_argument(f"-{short}", f"--{long.lower()}", f"--{long}", action="store_true", help=f"Set logging level {long}")

    group.add_argument("--log-level", default="i", type=str, choices=choices, help=f"Set the logging level ({choices})")

    args = parser.parse_args()

    # Resolve log_level from args dynamically
    log_level_from_args = "INFO"  # Default value
    for short, long in levels.items():
        if getattr(args, long.lower(), False):
            log_level_from_args = levels[short]
            break  # Stop after finding the first match
    else: # will only enter if for loop doesn't break
        log_level_from_args = levels.get(args.log_level.lower(), "INFO") #.get incase there's a bad argument

    LOG_LEVEL = log_level_from_args

else:
    LOG_LEVEL = "DEBUG"


try:
    __version__ = metadata.version("dataset-tools")
except metadata.PackageNotFoundError as error_log:
    print(f"dataset-tools package is not installed. Did you run `pip install .`? {error_log}")
