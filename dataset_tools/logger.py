# Dataset-Tools/dataset_tools/logger.py

import logging as pylog
import sys
from pathlib import Path  # For creating logs directory

from rich.console import Console
from rich.logging import RichHandler
from rich.style import Style
from rich.theme import Theme

try:
    from dataset_tools import LOG_LEVEL as INITIAL_PACKAGE_LOG_LEVEL
except ImportError:
    INITIAL_PACKAGE_LOG_LEVEL = "INFO"
    print("WARNING (logger.py): Could not import LOG_LEVEL from dataset_tools, defaulting to INFO.")

# --- Configuration for File Logging ---
LOGS_DIRECTORY = Path("./logs")  # Or choose a more absolute/configurable path
LOG_FILE_NAME = "dataset_tools_app.log"
LOG_FILE_PATH = LOGS_DIRECTORY / LOG_FILE_NAME
# --- End File Logging Configuration ---

DATASET_TOOLS_RICH_THEME = Theme(
    {  # ... your existing theme ...
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

_dataset_tools_main_rich_console = Console(stderr=True, theme=DATASET_TOOLS_RICH_THEME)

_configured_loggers_cache: dict[str, pylog.Logger] = {}
_current_effective_log_level_str: str = INITIAL_PACKAGE_LOG_LEVEL.strip().upper()
_main_rich_handler_instance: RichHandler | None = None
_main_file_handler_instance: pylog.FileHandler | None = None  # NEW: For file handler


def _ensure_logs_directory_exists():
    """Creates the logs directory if it doesn't exist."""
    try:
        LOGS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        # Use a basic print here as logger might not be fully up
        print(
            f"ERROR (logger.py): Could not create logs directory {LOGS_DIRECTORY}: {e}",
            file=sys.stderr,
        )


def _create_rich_handler(level_str: str, console_obj: Console) -> RichHandler:
    level_enum = getattr(pylog, level_str.upper(), pylog.INFO)
    return RichHandler(
        console=console_obj,
        rich_tracebacks=True,
        show_path=False,
        markup=True,
        level=level_enum,
    )


# NEW: Helper to create a FileHandler
def _create_file_handler(level_str: str, file_path: Path) -> pylog.FileHandler | None:
    """Helper to create a FileHandler instance with a specific level."""
    _ensure_logs_directory_exists()  # Make sure directory exists
    level_enum = getattr(pylog, level_str.upper(), pylog.INFO)
    try:
        file_handler = pylog.FileHandler(file_path, mode="a", encoding="utf-8")  # Append mode
        formatter = pylog.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level_enum)
        return file_handler
    except (OSError, Exception) as e:
        print(
            f"ERROR (logger.py): Could not create file handler for {file_path}: {e}",
            file=sys.stderr,
        )
        return None


def get_logger(name: str) -> pylog.Logger:
    global _main_rich_handler_instance, _main_file_handler_instance

    if name in _configured_loggers_cache:
        # ... (existing logic to update cached logger level) ...
        current_level_enum = getattr(pylog, _current_effective_log_level_str.upper(), pylog.INFO)
        cached_logger = _configured_loggers_cache[name]
        if cached_logger.level != current_level_enum:
            cached_logger.setLevel(current_level_enum)
            for handler in cached_logger.handlers:
                if isinstance(handler, (RichHandler, pylog.FileHandler)):  # Update both types
                    handler.setLevel(current_level_enum)
        return cached_logger

    logger_instance = pylog.getLogger(name)
    level_enum = getattr(pylog, _current_effective_log_level_str.upper(), pylog.INFO)
    logger_instance.setLevel(level_enum)

    # Add RichHandler
    has_our_rich_handler = any(
        isinstance(h, RichHandler) and h.console == _dataset_tools_main_rich_console for h in logger_instance.handlers
    )
    if not has_our_rich_handler:
        if _main_rich_handler_instance is None:
            _main_rich_handler_instance = _create_rich_handler(
                _current_effective_log_level_str, _dataset_tools_main_rich_console
            )
        if _main_rich_handler_instance:  # Check if creation was successful
            logger_instance.addHandler(_main_rich_handler_instance)

    # NEW: Add FileHandler
    has_our_file_handler = any(
        isinstance(h, pylog.FileHandler) and getattr(h, "baseFilename", "") == str(LOG_FILE_PATH)
        for h in logger_instance.handlers
    )
    if not has_our_file_handler:
        if _main_file_handler_instance is None:  # Create it if it doesn't exist globally
            _main_file_handler_instance = _create_file_handler(_current_effective_log_level_str, LOG_FILE_PATH)
        if _main_file_handler_instance:  # Check if creation was successful
            logger_instance.addHandler(_main_file_handler_instance)

    # If adding handlers to all loggers, propagate should usually be False.
    # If you want a single root handler, then specific loggers shouldn't add handlers
    # and propagate should be True.
    # For this setup where get_logger configures EACH logger it creates with both handlers:
    logger_instance.propagate = False

    _configured_loggers_cache[name] = logger_instance
    return logger_instance


APP_LOGGER_NAME = "dataset_tools_app"
logger = get_logger(APP_LOGGER_NAME)


def reconfigure_all_loggers(new_log_level_name_str: str):
    global _current_effective_log_level_str, _main_rich_handler_instance, _main_file_handler_instance

    new_level_normalized = new_log_level_name_str.strip().upper()
    actual_level_enum = getattr(pylog, new_level_normalized, pylog.INFO)
    _current_effective_log_level_str = new_level_normalized

    # Reconfigure shared handler instances
    if _main_rich_handler_instance:
        _main_rich_handler_instance.setLevel(actual_level_enum)
    if _main_file_handler_instance:
        _main_file_handler_instance.setLevel(actual_level_enum)

    # Reconfigure all cached loggers (their own level and any non-shared handlers)
    for logger_instance in _configured_loggers_cache.values():
        logger_instance.setLevel(actual_level_enum)
        # If handlers were not shared, they'd need individual updates too.
        # The current get_logger shares _main_rich_handler and _main_file_handler.
        # If get_logger created new handler instances each time, you'd iterate handlers here:
        # for handler in logger_instance.handlers:
        #     if isinstance(handler, (RichHandler, pylog.FileHandler)):
        #        handler.setLevel(actual_level_enum)

    logger.debug(
        "Dataset-Tools loggers reconfigured to level: %s (%s)",
        _current_effective_log_level_str,
        actual_level_enum,
    )
    # ... (your existing vendored logger reconfig logic, ensure it uses `logger.info` or `info_monitor`) ...
    vendored_logger_prefixes_to_reconfigure = [
        "SD_Prompt_Reader",
        "SDPR",
        "DSVendored_SDPR",
    ]
    for prefix in vendored_logger_prefixes_to_reconfigure:
        external_parent_logger = pylog.getLogger(prefix)
        was_configured_by_us = False
        for handler in external_parent_logger.handlers:
            if isinstance(handler, RichHandler) and handler.console == _dataset_tools_main_rich_console:
                handler.setLevel(actual_level_enum)
                was_configured_by_us = True
                break
        if was_configured_by_us:
            external_parent_logger.setLevel(actual_level_enum)
            logger.info(  # Announce using main app logger
                "Reconfigured vendored logger tree '%s' to level %s",
                prefix,
                _current_effective_log_level_str,
            )


def setup_rich_handler_for_external_logger(
    logger_to_configure: pylog.Logger,
    rich_console_to_use: Console,
    log_level_to_set_str: str,
):
    # ... (existing logic, but uses _create_rich_handler)
    for handler in logger_to_configure.handlers[:]:
        logger_to_configure.removeHandler(handler)
    new_rich_handler = _create_rich_handler(log_level_to_set_str, rich_console_to_use)
    logger_to_configure.addHandler(new_rich_handler)
    logger_to_configure.setLevel(getattr(pylog, log_level_to_set_str.strip().upper(), pylog.INFO))
    logger_to_configure.propagate = False
    logger.info(
        "Configured external logger '%s' with RichHandler at level %s.",
        logger_to_configure.name,
        log_level_to_set_str.upper(),
    )


# --- Decorator and Wrapper Functions ---
def debug_monitor(func):
    # ... (your existing debug_monitor, ensure it uses the global 'logger') ...
    def wrapper(*args, **kwargs):
        # ...
        logger.debug(f"Call: {func.__name__}(...)")  # Simplified for example
        try:
            return_data = func(*args, **kwargs)
            logger.debug(f"Return: {func.__name__} -> {str(return_data)[:100]}")  # Simplified
            return return_data
        except Exception as e_dec:
            show_exc_info = _current_effective_log_level_str in [
                "DEBUG",
                "TRACE",
                "NOTSET",
                "ALL",
            ]
            logger.error("Exception in %s: %s", func.__name__, e_dec, exc_info=show_exc_info)
            raise

    return wrapper


def debug_message(msg: str, *args, **kwargs):
    logger.debug(msg, *args, **kwargs)


def info_monitor(msg: str, *args, **kwargs):
    if "exc_info" not in kwargs:
        should_add_exc_info = _current_effective_log_level_str in [
            "DEBUG",
            "TRACE",
            "NOTSET",
            "ALL",
        ]
        current_exception = sys.exc_info()[0]
        if should_add_exc_info and current_exception is not None:
            kwargs["exc_info"] = True
    logger.info(msg, *args, **kwargs)


nfo = info_monitor

# --- Initial File Handler Setup (optional, if you want the main logger to always log to file) ---
# This ensures the main "dataset_tools_app" logger also gets the file handler
# if it was the first one created by get_logger.
# Alternatively, you could add the file handler to the root logger,
# but then you'd need to manage propagation carefully.
# _ensure_logs_directory_exists() # Call it once at module load
# if _main_file_handler_instance is None: # If get_logger hasn't created it yet
#     _main_file_handler_instance = _create_file_handler(_current_effective_log_level_str, LOG_FILE_PATH)
# if _main_file_handler_instance and _main_file_handler_instance not in logger.handlers:
#      logger.addHandler(_main_file_handler_instance)

# Simpler: get_logger will add it when 'logger' is first retrieved.
