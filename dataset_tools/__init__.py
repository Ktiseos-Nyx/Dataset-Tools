
 # 初始化

from importlib.metadata import version, PackageNotFoundError
from re import I # setuptools-scm versioning
try:
    __version__ = version("dataset-tools")
except PackageNotFoundError:
    # package is not installed
    pass

import sys
if "pytest" not in sys.modules:
    import argparse
    from typing import Literal

    levels = {"d": "DEBUG", "w": "WARNING", "e": "ERROR", "c": "CRITICAL", "i": "INFO"}

    parser = argparse.ArgumentParser(description="Set logging level.")
    group = parser.add_mutually_exclusive_group()

    choices = list(levels.keys()) + [v for v in levels.values()] + [v.upper() for v in levels.values()]
    for short, long in levels.items():
        group.add_argument(f'-{short}', f'--{long.lower()}', f'--{long}',
                        action='store_true', help=f"Set logging level {long}")

    group.add_argument('--log-level', default='i', type=str,
                    choices=choices, help=f"Set the logging level ({choices})")

    args = parser.parse_args()

    # Resolve log_level from args dynamically
    log_level = levels[next(iter([k for k,v in levels.items() if getattr(args, v.lower(), False)]), args.log_level)]
else:
    log_level = "DEBUG"
EXC_INFO: bool = log_level != "i"

import logging
from logging import Logger
import sys

msg_init = None
from rich.logging import RichHandler
from rich.console import Console
from rich.logging import RichHandler
handler = RichHandler(console=Console(stderr=True))

if handler is None:
    handler = logging.StreamHandler(sys.stdout)
    handler.propagate = False

formatter = logging.Formatter(
    fmt="%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
logging.root.setLevel(log_level)
logging.root.addHandler(handler)

if msg_init is not None:
    logger = logging.getLogger(__name__)
    logger.info(msg_init)

log_level = getattr(logging, log_level)
logger = logging.getLogger(__name__)
