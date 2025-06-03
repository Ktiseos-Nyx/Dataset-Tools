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
    global _current_log_level_str_for_dt  # No logger variable modification needed here

    _current_log_level_str_for_dt = new_log_level_name_str.strip().upper()
    actual_level_enum = getattr(pylog, _current_log_level_str_for_dt, pylog.INFO)

    if logger:
        logger.setLevel(actual_level_enum)
        for handler in logger.handlers:
            if isinstance(handler, RichHandler):
                handler.setLevel(actual_level_enum)
        logger.info(
            "Dataset-Tools Logger level reconfigured to: %s",
            _current_log_level_str_for_dt,
        )  # % logging

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
            logger.info(
                "Reconfigured vendored logger tree '%s' to level %s",
                prefix,
                _current_log_level_str_for_dt,
            )  # % logging


def setup_rich_handler_for_external_logger(
    logger_to_configure: pylog.Logger,
    rich_console_to_use: Console,
    log_level_to_set_str: str,
):
    target_log_level_enum = getattr(pylog, log_level_to_set_str.upper(), pylog.INFO)
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
    logger.info(  # Using app's logger to announce
        "Configured external logger '%s' with RichHandler at level %s.",
        logger_to_configure.name,
        log_level_to_set_str.upper(),
    )


def debug_monitor(func):
    def wrapper(*args, **kwargs):
        arg_str_list = [repr(a) for a in args]
        kwarg_str_list = [f"{k}={v!r}" for k, v in kwargs.items()]
        all_args_str = ", ".join(arg_str_list + kwarg_str_list)

        # Split log message if all_args_str is very long
        log_msg_part1 = f"Call: {func.__name__}("
        log_msg_part2 = ")"
        max_arg_len = 150 - len(log_msg_part1) - len(log_msg_part2) - 3  # -3 for "..."

        if len(all_args_str) > max_arg_len:
            all_args_str_display = all_args_str[:max_arg_len] + "..."
        else:
            all_args_str_display = all_args_str
        # This still uses f-string for constructing the message string, then logs it.
        # For pure %-style, it'd be: logger.debug("Call: %s(%s)", func.__name__, all_args_str_display)
        # Let's keep it as is for now, as the main cost is all_args_str construction.
        logger.debug(f"{log_msg_part1}{all_args_str_display}{log_msg_part2}")

        try:
            return_data = func(*args, **kwargs)
            return_data_str = repr(return_data)
            # Similar truncation for return data
            log_ret_msg_part1 = f"Return: {func.__name__} -> "
            max_ret_len = 150 - len(log_ret_msg_part1) - 3
            if len(return_data_str) > max_ret_len:
                return_data_str_display = return_data_str[:max_ret_len] + "..."
            else:
                return_data_str_display = return_data_str
            logger.debug(f"{log_ret_msg_part1}{return_data_str_display}")
            return return_data
        except Exception as e_dec:
            show_exc_info = INITIAL_LOG_LEVEL_FROM_INIT.strip().upper() in [
                "DEBUG",
                "TRACE",
                "NOTSET",
                "ALL",
            ]
            # Using % formatting for the error log
            logger.error(
                "Exception in %s: %s", func.__name__, e_dec, exc_info=show_exc_info
            )
            raise

    return wrapper


def debug_message(*args):
    # Construct message then log; %-style would be logger.debug("%s", message_content)
    message = " ".join(map(str, args))
    logger.debug(message)


def info_monitor(*args):
    message = " ".join(map(str, args))
    should_show_exc_info_for_info = INITIAL_LOG_LEVEL_FROM_INIT.strip().upper() in [
        "DEBUG",
        "TRACE",
        "NOTSET",
        "ALL",
    ]
    exc_info_val = sys.exc_info()[0] is not None and should_show_exc_info_for_info
    logger.info(
        message, exc_info=exc_info_val
    )  # Already good if message is just the string
    # If message were a format string, it would need args
