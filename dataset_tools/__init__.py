""" 初始化"""
 # pylint: disable=line-too-long

 # from re import I # setuptools-scm versioning
import os
import sys
from importlib.metadata import version, PackageNotFoundError
import logging
import argparse
from typing import Literal

from rich.logging import RichHandler
from rich.console import Console

if "pytest" not in sys.modules:
    parser = argparse.ArgumentParser(description="Set logging level.")
    group = parser.add_mutually_exclusive_group()


    levels = {"d": "DEBUG", "w": "WARNING", "e": "ERROR", "c": "CRITICAL", "i": "INFO"}
    choices = list(levels.keys()) + list(levels.values()) + [v.upper() for v in levels.values()]
    for short, long in levels.items():
        group.add_argument(f'-{short}', f'--{long.lower()}', f'--{long}',
                        action='store_true', help=f"Set logging level {long}")

    group.add_argument('--log-level', default='i', type=str,
                        choices=choices, help=f"Set the logging level ({choices})")

    args = parser.parse_args()

    # Resolve log_level from args dynamically
    LOG_LEVEL = levels[next(iter([k for k,v in levels.items() if getattr(args, v.lower(), False)]), args.log_level)]
else:
    LOG_LEVEL = "DEBUG"

EXC_INFO: bool = LOG_LEVEL != "i"

#begin routine
msg_init = None  # pylint: disable=invalid-name

handler = RichHandler(console=Console(stderr=True))

if handler is None:
    handler = logging.StreamHandler(sys.stdout)
    handler.propagate = False

formatter = logging.Formatter(
    fmt="%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
logging.root.setLevel(LOG_LEVEL)
logging.root.addHandler(handler)

if msg_init is not None:
    logger = logging.getLogger(__name__)
    logger.info(msg_init)

log_level = getattr(logging, LOG_LEVEL)
logger = logging.getLogger(__name__)

try:
    __version__ = version("dataset-tools")
except PackageNotFoundError:
    logger.info("dataset-tools package is not installed. Did you run `pip install .`?", exc_info=EXC_INFO)
