"""初始化"""
# pylint: disable=line-too-long

import sys
import argparse
from importlib.metadata import version, PackageNotFoundError
# from re import I  # setuptools-scm versioning

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
    LOG_LEVEL = levels[next(iter([k for k, v in levels.items() if getattr(args, v.lower(), False)]), args.log_level)]
else:
    LOG_LEVEL = "DEBUG"


try:
    __version__ = version("dataset-tools")
except PackageNotFoundError as error_log:
    print(f"dataset-tools package is not installed. Did you run `pip install .`? {error_log}")
