# Dataset-Tools/dataset_tools/logger.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Create console log for Dataset-Tools and provide utilities for configuring other loggers."""

import logging as pylog
import sys

from rich.console import Console
from rich.logging import RichHandler
from rich.style import Style
from rich.theme import Theme

from dataset_tools import LOG_LEVEL as INITIAL_LOG_LEVEL_FROM_INIT

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
        "log.message": Style(color="steel_blue1"),
        "repr.tag_start": Style(color="white"),
        "repr.tag_end": Style(color="white"),
        "repr.tag_contents": Style(color="deep_sky_blue4"),
        "repr.ellipsis": Style(color="purple4"),
        "log.level": Style(color="gray37"),
    },
)

_dataset_tools_main_rich_console = Console(stderr=True, theme=DATASET_TOOLS_RICH_THEME)

APP_LOGGER_NAME = "dataset_tools_app"
logger = pylog.getLogger(APP_LOGGER_NAME)

_current_log_level_str_for_dt = INITIAL_LOG_LEVEL_FROM_INIT.strip().upper()
_initial_log_level_enum_for_dt = getattr(
    pylog, _current_log_level_str_for_dt, pylog.INFO
)
logger.setLevel(_initial_log_level_enum_for_dt)

if not logger.handlers:
    _dt_rich_handler = RichHandler(
        console=_dataset_tools_main_rich_console,
        rich_tracebacks=True,
        show_path=False,
        markup=True,
        level=_initial_log_level_enum_for_dt,
    )
    logger.addHandler(_dt_rich_handler)
    logger.propagate = False


def reconfigure_all_loggers(new_log_level_name_str: str):
    global _current_log_level_str_for_dt

    _current_log_level_str_for_dt = new_log_level_name_str.strip().upper()
    actual_level_enum = getattr(pylog, _current_log_level_str_for_dt, pylog.INFO)

    if logger:
        logger.setLevel(actual_level_enum)
        for handler in logger.handlers:
            if isinstance(handler, RichHandler):
                handler.setLevel(actual_level_enum)
        # Also set the root logger's level to ensure all child loggers inherit it
        pylog.root.setLevel(actual_level_enum)
        # Use the logger's own method for consistency after reconfiguration
        debug_message(
            "Dataset-Tools Logger internal level object set to: %s", actual_level_enum
        )
        info_monitor(  # Use info_monitor which is now fixed
            "Dataset-Tools Logger level reconfigured to: %s",
            _current_log_level_str_for_dt,
        )

    vendored_logger_prefixes_to_reconfigure = [
        "SD_Prompt_Reader",
        "SDPR",
        "DSVendored_SDPR",
    ]
    for prefix in vendored_logger_prefixes_to_reconfigure:
        external_parent_logger = pylog.getLogger(prefix)
        was_configured_by_us = False
        for handler in external_parent_logger.handlers:
            if (
                isinstance(handler, RichHandler)
                and handler.console == _dataset_tools_main_rich_console
            ):
                was_configured_by_us = True
                handler.setLevel(actual_level_enum)
                break
        if was_configured_by_us:
            external_parent_logger.setLevel(actual_level_enum)
            info_monitor(  # Use info_monitor
                "Reconfigured vendored logger tree '%s' to level %s",
                prefix,
                _current_log_level_str_for_dt,
            )


def setup_rich_handler_for_external_logger(
    logger_to_configure: pylog.Logger,
    rich_console_to_use: Console,
    log_level_to_set_str: str,
):
    target_log_level_enum = getattr(pylog, log_level_to_set_str.upper(), pylog.INFO)
    # Remove existing handlers to avoid duplication if called multiple times
    for handler in logger_to_configure.handlers[:]:
        logger_to_configure.removeHandler(handler)

    new_rich_handler = RichHandler(
        console=rich_console_to_use,
        rich_tracebacks=True,
        show_path=False,
        markup=True,
        level=target_log_level_enum,
    )
    logger_to_configure.addHandler(new_rich_handler)
    logger_to_configure.setLevel(target_log_level_enum)
    logger_to_configure.propagate = False
    # Use info_monitor (app's logger) to announce this configuration
    info_monitor(
        "Configured external logger '%s' with RichHandler at level %s.",
        logger_to_configure.name,
        log_level_to_set_str.upper(),
    )


def debug_monitor(func):
    """Decorator to log function calls and their returns/exceptions at DEBUG level."""

    # Uses f-strings for its own message construction, but calls logger.debug/logger.error
    def wrapper(*args, **kwargs):
        # Construct argument string representation
        arg_str_list = [repr(a) for a in args]
        kwarg_str_list = [f"{k}={v!r}" for k, v in kwargs.items()]
        all_args_str = ", ".join(arg_str_list + kwarg_str_list)

        log_msg_part1 = f"Call: {func.__name__}("
        log_msg_part2 = ")"
        # Max length for the arguments part of the log message
        max_arg_len_for_display = (
            200 - len(log_msg_part1) - len(log_msg_part2) - 3
        )  # 3 for "..."

        if len(all_args_str) > max_arg_len_for_display:
            all_args_str_display = all_args_str[:max_arg_len_for_display] + "..."
        else:
            all_args_str_display = all_args_str

        # Log the call using f-string for this specific decorator message
        logger.debug(f"{log_msg_part1}{all_args_str_display}{log_msg_part2}")

        try:
            return_data = func(*args, **kwargs)
            return_data_str = repr(return_data)

            log_ret_msg_part1 = f"Return: {func.__name__} -> "
            # Max length for the return value part of the log message
            max_ret_len_for_display = 200 - len(log_ret_msg_part1) - 3  # 3 for "..."

            if len(return_data_str) > max_ret_len_for_display:
                return_data_str_display = (
                    return_data_str[:max_ret_len_for_display] + "..."
                )
            else:
                return_data_str_display = return_data_str

            logger.debug(f"{log_ret_msg_part1}{return_data_str_display}")
            return return_data
        except Exception as e_dec:
            # Determine if full traceback should be shown based on initial log level
            show_exc_info = INITIAL_LOG_LEVEL_FROM_INIT.strip().upper() in [
                "DEBUG",
                "TRACE",
                "NOTSET",
                "ALL",
            ]
            # Use %-formatting for the error log as it's a direct call to logger.error
            logger.error(
                "Exception in %s: %s", func.__name__, e_dec, exc_info=show_exc_info
            )
            raise  # Re-raise the exception

    return wrapper


# --- CORRECTED WRAPPER FUNCTIONS ---
def debug_message(msg: str, *args, **kwargs):
    """Logs a message with DEBUG level using the main app logger.
    'msg' is the primary message string, potentially with format specifiers.
    '*args' are the arguments for the format specifiers in 'msg'.
    '**kwargs' can include 'exc_info', 'stack_info', etc., for the underlying logger.
    """
    logger.debug(msg, *args, **kwargs)


def info_monitor(msg: str, *args, **kwargs):  # Renamed from nfo for clarity
    """Logs a message with INFO level using the main app logger.
    'msg' is the primary message string, potentially with format specifiers.
    '*args' are the arguments for the format specifiers in 'msg'.
    '**kwargs' can include 'exc_info', 'stack_info', etc.

    If 'exc_info' is not explicitly passed in kwargs, it will be automatically
    set to True if an exception is active AND the initial log level was DEBUG/TRACE.
    """
    # Check if exc_info is explicitly passed by the caller
    if "exc_info" not in kwargs:
        # Default exc_info behavior: add it if an exception is active and log level is permissive
        should_add_exc_info_automatically = (
            INITIAL_LOG_LEVEL_FROM_INIT.strip().upper()
            in [
                "DEBUG",
                "TRACE",
                "NOTSET",  # Usually means log everything
                "ALL",  # Custom "ALL" level if you define it
            ]
        )
        # Check if there's an active exception
        current_exception = sys.exc_info()[0]
        if should_add_exc_info_automatically and current_exception is not None:
            kwargs["exc_info"] = True

    logger.info(msg, *args, **kwargs)


# --- END OF CORRECTED WRAPPER FUNCTIONS ---


def get_logger(name: str = None):
    """Get a logger instance for the given name, using Dataset Tools configuration."""
    if name is None:
        return logger
    return pylog.getLogger(name)
