# Dataset-Tools/dataset_tools/logger.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Create console log for Dataset-Tools and provide utilities for configuring other loggers."""

import sys
import logging as pylog # Alias to distinguish from this module's 'logger' instance
from logging import StreamHandler, Formatter # Standard library components

# Rich library components
from rich.theme import Theme
from rich.console import Console
from rich.logging import RichHandler
from rich.style import Style

# Import LOG_LEVEL from the package's __init__.py and other project types
from dataset_tools import LOG_LEVEL as INITIAL_LOG_LEVEL_FROM_INIT
# from .correct_types import EXC_INFO  # Assuming this is for exc_info parameter

# --- Global variable for initial message (if any, though not currently used by this setup) ---
# msg_init = None 

# --- Rich Theme and Console Setup for Dataset-Tools' Own Logger ---
# This theme will be used by Dataset-Tools' primary logger
# and can also be used by the helper function for external loggers.
DATASET_TOOLS_RICH_THEME = Theme(
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
        "log.message": Style(color="steel_blue1"), # Default message color
        "repr.tag_start": Style(color="white"),
        "repr.tag_end": Style(color="white"),
        "repr.tag_contents": Style(color="deep_sky_blue4"),
        "repr.ellipsis": Style(color="purple4"),
        "log.level": Style(color="gray37"),
    }
)

# This is the main Rich Console instance for Dataset-Tools.
# It can be imported by metadata_parser.py to configure vendored loggers.
# The underscore indicates it's primarily for use within this package.
_dataset_tools_main_rich_console = Console(stderr=True, theme=DATASET_TOOLS_RICH_THEME)

# --- Dataset-Tools Application Specific Logger Setup ---
APP_LOGGER_NAME = "dataset_tools_app" # Main logger name for your application
logger = pylog.getLogger(APP_LOGGER_NAME) # Get the instance

# Set initial level based on what dataset_tools/__init__.py determined
_current_log_level_str_for_dt = INITIAL_LOG_LEVEL_FROM_INIT.strip().upper() # Store current level string
_initial_log_level_enum_for_dt = getattr(pylog, _current_log_level_str_for_dt, pylog.INFO)
logger.setLevel(_initial_log_level_enum_for_dt)

# Add RichHandler to Dataset-Tools' own logger instance if it doesn't have handlers
if not logger.handlers:
    _dt_rich_handler = RichHandler(
        console=_dataset_tools_main_rich_console,
        rich_tracebacks=True,
        show_path=False, # As per your original setup
        markup=True,
        level=_initial_log_level_enum_for_dt # Set level on the handler as well
    )
    logger.addHandler(_dt_rich_handler)
    logger.propagate = False # Prevent messages from this logger going to Python's root

# --- Reconfiguration Function for Dataset-Tools Logger AND Vendored Loggers ---
def reconfigure_all_loggers(new_log_level_name_str: str):
    """
    Updates the logging level of Dataset-Tools' main logger AND
    attempts to reconfigure known vendored/external loggers.
    """
    global logger, _current_log_level_str_for_dt # Allow modification of global _current_log_level_str_for_dt
    
    _current_log_level_str_for_dt = new_log_level_name_str.strip().upper()
    actual_level_enum = getattr(pylog, _current_log_level_str_for_dt, pylog.INFO)
    
    # Reconfigure Dataset-Tools main logger
    if logger:
        logger.setLevel(actual_level_enum)
        for handler in logger.handlers:
            if isinstance(handler, RichHandler): # Or other specific handlers you use
                 handler.setLevel(actual_level_enum) 
        logger.info(f"Dataset-Tools Logger level reconfigured to: {_current_log_level_str_for_dt}")
    
    # Reconfigure known vendored/external logger prefixes
    # These are the prefixes their Logger class might use when creating named loggers
    # (e.g., Logger("SD_Prompt_Reader.ImageDataReader"), Logger("SDPR.CivitaiComfyUIFormat"))
    vendored_logger_prefixes_to_reconfigure = ["SD_Prompt_Reader", "SDPR", "DSVendored_SDPR"]
    
    for prefix in vendored_logger_prefixes_to_reconfigure:
        external_parent_logger = pylog.getLogger(prefix)
        # Check if this logger was previously configured with our RichHandler
        was_configured_by_us = False
        for handler in external_parent_logger.handlers:
            if isinstance(handler, RichHandler) and handler.console == _dataset_tools_main_rich_console:
                was_configured_by_us = True
                handler.setLevel(actual_level_enum)
                break 
        
        if was_configured_by_us: # Only set level on logger if we added our handler
            external_parent_logger.setLevel(actual_level_enum)
            logger.info(f"Reconfigured vendored logger tree '{prefix}' to level {_current_log_level_str_for_dt}")
        # else:
            # logger.debug(f"Vendored logger prefix '{prefix}' not previously configured with DT RichHandler or no handlers found.")


# --- Helper Function to Configure an External Logger with Rich ---
def setup_rich_handler_for_external_logger(
    logger_to_configure: pylog.Logger, # Pass the actual logger instance
    rich_console_to_use: Console,    # Pass _dataset_tools_main_rich_console
    log_level_to_set_str: str        # Pass the desired log level string (e.g., "INFO", "DEBUG")
):
    """
    Configures the passed Python logger instance to use a RichHandler
    with the provided Rich Console and log level.
    Removes existing handlers from it and sets propagation to False.
    """
    target_log_level_enum = getattr(pylog, log_level_to_set_str.upper(), pylog.INFO)

    # Remove any pre-existing handlers from this specific logger to avoid duplicates
    # and ensure our RichHandler is the one controlling its output to console.
    for handler in logger_to_configure.handlers[:]:
        logger_to_configure.removeHandler(handler)
        # nfo(f"[DT Logger Setup] Removed existing handler {handler} from logger '{logger_to_configure.name}'")

    new_rich_handler = RichHandler(
        console=rich_console_to_use,
        rich_tracebacks=True, 
        show_path=False, 
        markup=True,
        level=target_log_level_enum # Set the level on the handler
    )
    logger_to_configure.addHandler(new_rich_handler)
    logger_to_configure.setLevel(target_log_level_enum) # Set level on the logger itself
    logger_to_configure.propagate = False # Crucial: Prevents messages handled here from also going to Python's root logger
    
    # Use the main app logger to announce this configuration
    logger.info(f"Configured external logger '{logger_to_configure.name}' with RichHandler at level {log_level_to_set_str.upper()}.")


# --- Dataset-Tools Logging Helper Functions (using the 'logger' instance) ---
def debug_monitor(func):
    """Debug output decorator function for method/function calls and returns."""
    def wrapper(*args, **kwargs):
        # Log entry before calling the function
        arg_str_list = [repr(a) for a in args]
        kwarg_str_list = [f"{k}={v!r}" for k, v in kwargs.items()]
        all_args_str = ", ".join(arg_str_list + kwarg_str_list)
        # Truncate long arg strings
        if len(all_args_str) > 150: all_args_str = all_args_str[:150] + "..."
        logger.debug(f"Call: {func.__name__}({all_args_str})")
        
        try:
            return_data = func(*args, **kwargs)
            # Truncate long return_data for cleaner logs
            return_data_str = repr(return_data) # Use repr for better type info
            if len(return_data_str) > 150:
                return_data_str = return_data_str[:150] + "..."
            logger.debug(f"Return: {func.__name__} -> {return_data_str}")
            return return_data
        except Exception as e_dec:
            # Decide on exc_info based on the logger's own INITIAL_LOG_LEVEL_FROM_INIT
            show_exc_info = INITIAL_LOG_LEVEL_FROM_INIT.strip().upper() in ["DEBUG", "TRACE", "NOTSET", "ALL"]
            logger.error(f"Exception in {func.__name__}: {e_dec}", exc_info=show_exc_info)
            raise
    return wrapper

def debug_message(*args):
    """Logs a debug message, joining all arguments into a single string."""
    message = " ".join(map(str, args))
    logger.debug(message)

def info_monitor(*args):
    """Logs an info message, joining all arguments into a single string."""
    message = " ".join(map(str, args))
    # Set exc_info based on whether an exception is being handled AND log level
    should_show_exc_info_for_info = INITIAL_LOG_LEVEL_FROM_INIT.strip().upper() in ["DEBUG", "TRACE", "NOTSET", "ALL"]
    # Only show exc_info for info messages if an exception is active AND level is verbose
    exc_info_val = sys.exc_info()[0] is not None and should_show_exc_info_for_info
    logger.info(message, exc_info=exc_info_val)