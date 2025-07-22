# dataset_tools/__init__.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""Initialize dataset_tools package"""

import sys
from importlib import metadata
from pathlib import Path

# Configuration path
CONFIG_PATH = Path(__file__).parent / "config"

# --- Default Log Level ---
# This will be used if the application isn't run via main.py's argument parsing,
# or before main.py has a chance to parse arguments.
LOG_LEVEL = "INFO"  # Sensible default

# If pytest is running, set LOG_LEVEL to DEBUG for more verbose test logs.
# This specific check for pytest can stay if you want this behavior.
if "pytest" in sys.modules:
    LOG_LEVEL = "DEBUG"
    # For clarity
    print("DEBUG (__init__.py): Pytest detected, setting LOG_LEVEL to DEBUG.")

# --- Version ---
try:
    __version__ = metadata.version("kn-dataset-tools")
except metadata.PackageNotFoundError:
    # Fallback version if not installed (e.g., running from source directly)
    __version__ = "0.0.0-dev"
    # Optional: print a warning, but avoid exiting or raising an error that halts tests.
    # print("Warning (__init__.py): dataset-tools package not installed. Version set to placeholder.")

# --- Function to allow main.py to update the log level ---
# This variable LOG_LEVEL will be updated by this function.
# Your logger.py will read this variable when it initializes.
# If logger.py needs to change its level *after* initialization (which it will,
# if main.py calls this function after logger.py has already been imported and configured),
# then logger.py needs a reconfigure function.

_log_level_map_internal = {
    "d": "DEBUG",
    "debug": "DEBUG",
    "i": "INFO",
    "info": "INFO",
    "w": "WARNING",
    "warning": "WARNING",
    "e": "ERROR",
    "error": "ERROR",
    "c": "CRITICAL",
    "critical": "CRITICAL",
}


def set_package_log_level(level_input: str) -> None:
    """Sets the global LOG_LEVEL for the package based on a string argument.
    Called by the main application entry point after parsing CLI args.
    The logger module should then re-read this or be explicitly reconfigured.
    """
    global LOG_LEVEL  # Declare that we are modifying the LOG_LEVEL in this module's scope

    normalized_input = str(level_input).strip().lower()

    # Check if the input is a direct key (e.g., 'd') or a value (e.g., 'debug')
    if normalized_input in _log_level_map_internal:
        LOG_LEVEL = _log_level_map_internal[normalized_input]
    else:
        # Fallback to INFO if an invalid level string is provided
        # print(f"Warning (__init__.py): Invalid log level '{level_input}' provided. Defaulting to INFO.")
        LOG_LEVEL = "INFO"

    # This print is for debugging the mechanism itself. Your actual app logs will come from logger.py
    print(f"DEBUG (__init__.py): Package LOG_LEVEL variable updated to: {LOG_LEVEL}")

    # IMPORTANT: This only sets the LOG_LEVEL *variable* in this __init__.py.
    # Your logger.py (which imports LOG_LEVEL from here) will use this value when it's
    # first imported. If main.py calls set_package_log_level *after* logger.py
    # has already been imported and configured its own logger instance, you need
    # a way to tell that logger instance to update its level.
    # This is typically done by calling a reconfigure function in logger.py, e.g.:
    # from . import logger as app_logger
    # app_logger.reconfigure_logger(LOG_LEVEL)
    # This call would happen in main.py *after* calling set_package_log_level.


# --- Optional: Make submodules easily accessible ---
# You can uncomment these if you want to be able to do, for example:
# import dataset_tools
# print(dataset_tools.ui.MainWindow)
# Or:
# from dataset_tools import ui
#
# This is a matter of API design for your package. It's not strictly necessary
# as users can always do `from dataset_tools.ui import MainWindow`.

# from . import access_disk
# from . import correct_types
# from . import logger
# from . import main as app_main # Avoid confusion with main script module
# from . import metadata_parser
# from . import model_tool
# from . import ui
# from . import widgets
