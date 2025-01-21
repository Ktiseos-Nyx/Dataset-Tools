# // SPDX-License-Identifier: CC0-1.0
# // --<{ Ktiseos Nyx }>--

"""建立控制檯日誌"""

import sys
import logging as pylog
from logging import StreamHandler, Formatter

from rich import theme
from rich import console
from rich import logging
from rich import style
from dataset_tools.correct_types import EXC_INFO, LOG_LEVEL


msg_init = None  # pylint: disable=invalid-name

NOUVEAU = theme.Theme(
    {
        "logging.level.notset": style.Style(dim=True),  # level ids
        "logging.level.debug": style.Style(color="magenta3"),
        "logging.level.info": style.Style(color="blue_violet"),
        "logging.level.warning": style.Style(color="gold3"),
        "logging.level.error": style.Style(color="dark_orange3", bold=True),
        "logging.level.critical": style.Style(color="deep_pink4", bold=True, reverse=True),
        "logging.keyword": style.Style(bold=True, color="cyan", dim=True),
        "log.path": style.Style(dim=True, color="royal_blue1"),  # line number
        "repr.str": style.Style(color="sky_blue3", dim=True),
        "json.str": style.Style(color="gray53", italic=False, bold=False),
        "log.message": style.Style(color="steel_blue1"),  # variable name, normal strings
        "repr.tag_start": style.Style(color="white"),  # class name tag
        "repr.tag_end": style.Style(color="white"),  # class name tag
        "repr.tag_contents": style.Style(color="deep_sky_blue4"),  # class readout
        "repr.ellipsis": style.Style(color="purple4"),
        "log.level": style.Style(color="gray37"),
    }
)
console_out = console.Console(stderr=True, theme=NOUVEAU)

log_handler = logging.RichHandler(console=console_out)

if log_handler is None:
    log_handler = StreamHandler(sys.stderr)
    log_handler.propagate = False

formatter = Formatter(
    fmt="%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log_handler.setFormatter(formatter)
pylog.root.setLevel(LOG_LEVEL)
pylog.root.addHandler(log_handler)


if msg_init is not None:
    logger = pylog.getLogger(__name__)
    logger.info(msg_init)

log_level = getattr(pylog, LOG_LEVEL)
logger = pylog.getLogger(__name__)


def debug_monitor(func):
    """Debug output decorator function
    Data returned from decorated methods/functions is automatically sent to debugger
    """

    def wrapper(*args, **kwargs) -> None:
        """Wrap log"""
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


def debug_message(*args):
    """Individual Debug messages"""
    logger.debug(args)


def info_monitor(*args):
    """Info log output"""
    logger.info(args, exc_info=EXC_INFO)
