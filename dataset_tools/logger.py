import logging
import sys
from dataset_tools.correct_types import LOG_LEVEL, EXC_INFO

from rich.logging import RichHandler
from rich.console import Console

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


def debug_monitor(func):
    def wrapper(*args, **kwargs) -> None:
        return_data = func(*args, **kwargs)
        logger.debug("%s", f"Function {func.__name__} : {args} {kwargs} {return_data}", exc_info=True)
        return return_data

    return wrapper


def info_monitor(message, *args):
    logger.info("%s", f"{message} {args}", exc_info=EXC_INFO)
