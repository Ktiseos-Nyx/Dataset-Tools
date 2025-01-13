# // SPDX-License-Identifier: CC0-1.0
# // --<{ Ktiseos Nyx }>--

"""建立控制檯日誌"""

import sys
import logging as pylog
from logging import StreamHandler, Formatter
from dataset_tools.correct_types import LOG_LEVEL, EXC_INFO

from rich.theme import Theme
from rich.console import Console
from rich.logging import RichHandler
from rich.style import Style


msg_init = None  # pylint: disable=invalid-name

NOUVEAU = Theme(
    {
        "logging.level.notset": Style(dim=True),  # level ids
        "logging.level.debug": Style(color="magenta3"),
        "logging.level.info": Style(color="blue_violet"),
        "logging.level.warning": Style(color="gold3"),
        "logging.level.error": Style(color="dark_orange3", bold=True),
        "logging.level.critical": Style(color="deep_pink4", bold=True, reverse=True),
        "logging.keyword": Style(bold=True, color="cyan", dim=True),
        "log.path": Style(dim=True, color="royal_blue1"),  # line number
        "repr.str": Style(color="sky_blue3", dim=True),
        "json.str": Style(color="gray53", italic=False, bold=False),
        "log.message": Style(color="steel_blue1"),  # variable name, normal strings
        "repr.tag_start": Style(color="white"),  # class name tag
        "repr.tag_end": Style(color="white"),  # class name tag
        "repr.tag_contents": Style(color="deep_sky_blue4"),  # class readout
        "repr.ellipsis": Style(color="purple4"),
        "log.level": Style(color="gray37"),
    }
)
console = Console(stderr=True, theme=NOUVEAU)

handler = RichHandler(console=console)

if handler is None:
    handler = StreamHandler(sys.stderr)
    handler.propagate = False

formatter = Formatter(
    fmt="%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
pylog.root.setLevel(LOG_LEVEL)
pylog.root.addHandler(handler)


if msg_init is not None:
    logger = pylog.getLogger(__name__)
    logger.info(msg_init)

log_level = getattr(pylog, LOG_LEVEL)
logger = pylog.getLogger(__name__)


def debug_monitor(func):
    """output debug"""

    def wrapper(*args, **kwargs) -> None:
        return_data = func(*args, **kwargs)
        if not kwargs:
            logger.debug(
                "%s",
                f"Func {func.__name__} : {type(args)} : {args} : Return : {return_data}",
            )
        else:
            logger.debug(
                "%s",
                f"Func {func.__name__}{type(args)}:{args}:{type(kwargs)}:{kwargs}:R{return_data}",
            )
        return return_data

    return wrapper


def debug_message(message, *args):
    """output debug"""
    if args:
        logger.debug("%s", f"{message} {args}", exc_info=EXC_INFO)


def info_monitor(message, *args):
    """output info"""
    if args:
        logger.info("%s", f"{message} {args}", exc_info=EXC_INFO)
