import logging
import sys
from dataset_tools.correct_types import LOG_LEVEL, EXC_INFO

from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme
from rich.default_styles import Style

msg_init = None  # pylint: disable=invalid-name


NOUVEAU = Theme(
    {
        "logging.keyword": Style(bold=True, color="cyan", dim=True),
        "logging.level.notset": Style(dim=True),
        "logging.level.debug": Style(color="purple4"),
        "logging.level.info": Style(color="blue_violet"),
        "logging.level.warning": Style(color="gold3"),
        "logging.level.error": Style(color="dark_orange3", bold=True),
        "logging.level.critical": Style(color="deep_pink4", bold=True, reverse=True),
        "repr.str": Style(color="cornflower_blue", dim=True),
        "log.path": Style(dim=True, color="royal_blue1"),
        "json.str": Style(color="deep_sky_blue4", italic=False, bold=False),
        "log.message": Style(color="gray53"),
    }
)
console = Console(stderr=True, theme=NOUVEAU)

handler = RichHandler(console=console)


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


def debug_monitor(func):
    def wrapper(*args, **kwargs) -> None:
        return_data = func(*args, **kwargs)
        logger.debug("%s", f"Function {func.__name__} : {args} {kwargs} {return_data}", exc_info=True)
        return return_data

    return wrapper


def info_monitor(message, *args):
    if args:
        logger.info("%s", f"{message} {args}", exc_info=EXC_INFO)
    else:
        logger.info("%s", f"{message}", exc_info=EXC_INFO)
