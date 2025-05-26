# dataset_tools/logger.py

# Copyright (c) 2025 Ktiseos Nyx/ Dataset-Tools (*EARTH & DUSK MEDIA / 0FTH3N1GHT*)
# SPDX-License-Identifier: MIT

"""Create console log"""

import sys
import logging as pylog
from logging import StreamHandler, Formatter

from rich.theme import Theme
from rich.console import Console
from rich.logging import RichHandler
from rich.style import Style

# Import LOG_LEVEL from the package's __init__.py
from dataset_tools import LOG_LEVEL as INITIAL_LOG_LEVEL_FROM_INIT
from dataset_tools.correct_types import EXC_INFO

# --- Global variable for initial message (if any) ---
msg_init = None  # pylint: disable=invalid-name # <<< THIS LINE IS NOW CORRECTLY PLACED/UNCOMMENTED

# --- Rich Theme and Console Setup ---
NOUVEAU = Theme(
    {
        "logging.level.notset": Style(dim=True),
        "logging.level.debug": Style(color="magenta3"),
        "logging.level.info": Style(color="blue_violet"),
        "logging.level.warning": Style(color="gold3"),
        "logging.level.error": Style(color="dark_orange3", bold=True),
        "logging.level.critical": Style(color="deep_pink4", bold=True, reverse=True),
        "logging.keyword": Style(bold=True, color="cyan", dim=True),
        "log.path": Style(dim=True, color="royal_blue1"),
        "repr.str": Style(color="sky_blue3", dim=True),
        "json.str": Style(color="gray53", italic=False, bold=False),
        "log.message": Style(color="steel_blue1"),
        "repr.tag_start": Style(color="white"),
        "repr.tag_end": Style(color="white"),
        "repr.tag_contents": Style(color="deep_sky_blue4"),
        "repr.ellipsis": Style(color="purple4"),
        "log.level": Style(color="gray37"),
    }
)
_console_out = Console(stderr=True, theme=NOUVEAU)

# --- Application Specific Logger Setup ---
APP_LOGGER_NAME = "dataset_tools_app"
logger = pylog.getLogger(APP_LOGGER_NAME)

_initial_log_level_enum = getattr(pylog, INITIAL_LOG_LEVEL_FROM_INIT.upper(), pylog.INFO)
logger.setLevel(_initial_log_level_enum)

if not logger.handlers: # Add handler only if it doesn't have one
    _rich_handler = RichHandler(
        console=_console_out,
        rich_tracebacks=True,
        show_path=False,
        markup=True
    )
    # Optional: Formatter if RichHandler's default isn't desired for all messages
    # _formatter = Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    # _rich_handler.setFormatter(_formatter)
    logger.addHandler(_rich_handler)
    logger.propagate = False


# --- Process Initial Message (if any) ---
if msg_init is not None: # Now msg_init is defined
    logger.info(str(msg_init))


# --- Reconfiguration Function ---
def reconfigure_logger(new_log_level_name: str):
    """Updates the logging level of the application's configured logger."""
    global logger 
    
    actual_level_enum = getattr(pylog, new_log_level_name.strip().upper(), pylog.INFO)
    
    if logger:
        logger.setLevel(actual_level_enum)
        # Update level on handlers too, especially RichHandler if it has its own level set
        for handler in logger.handlers:
            if isinstance(handler, RichHandler): # Or any handler type you use
                 handler.setLevel(actual_level_enum) # RichHandler level can be set
        logger.info(f"Logger level reconfigured to: {new_log_level_name.upper()}")
    else:
        # This case should ideally not be reached if logger is initialized at module level
        # However, adding a print for robustness during development.
        current_level_for_print = getattr(pylog, INITIAL_LOG_LEVEL_FROM_INIT.upper(), "UNKNOWN")
        print(f"ERROR (logger.py): Application logger instance was not found during reconfiguration attempt. Current initial level was {current_level_for_print}. New level {new_log_level_name} not applied to instance.")


# --- Logging Helper Functions (using the configured 'logger') ---
def debug_monitor(func):
    """Debug output decorator function for method/function calls and returns."""
    def wrapper(*args, **kwargs):
        return_data = func(*args, **kwargs)
        arg_str = f"args={args}" if args else ""
        kwarg_str = f"kwargs={kwargs}" if kwargs else ""
        parts = [f"Func {func.__name__}"]
        if arg_str: parts.append(arg_str)
        if kwarg_str: parts.append(kwarg_str)
        # Truncate long return_data for cleaner logs
        return_data_str = str(return_data)
        if len(return_data_str) > 200:
            return_data_str = return_data_str[:200] + "..."
        parts.append(f"Return: {return_data_str}")
        logger.debug(" : ".join(parts))
        return return_data
    return wrapper

def debug_message(*args):
    """Logs a debug message, joining all arguments into a single string."""
    message = " ".join(map(str, args))
    logger.debug(message)

def info_monitor(*args):
    """Logs an info message, joining all arguments into a single string."""
    message = " ".join(map(str, args))
    logger.info(message, exc_info=EXC_INFO)