# dataset_tools/main.py
# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Launch and exit the application"""

import argparse  # Import argparse for command-line argument processing
import multiprocessing
import sys
from pathlib import Path

from PyQt6 import QtWidgets
from PyQt6.QtGui import QFontDatabase

# For version display
# Import from your package's __init__.py
from dataset_tools import (
    __version__,  # type: ignore
    set_package_log_level,  # type: ignore
)
from dataset_tools import logger as app_logger  # type: ignore

# Import your logger module
# Import your UI and logger
from dataset_tools.ui import MainWindow


def main(cli_args_list=None):
    """Launch application"""
    parser = argparse.ArgumentParser(
        description=(f"Dataset Tools v{__version__} - Metadata Viewer and Editor."),
    )
    levels_map_cli = {
        "d": "DEBUG",
        "i": "INFO",
        "w": "WARNING",
        "e": "ERROR",
        "c": "CRITICAL",
    }

    # Using 'level_val' instead of 'l'
    valid_log_level_choices = (
        list(levels_map_cli.keys())
        + list(level_val.upper() for level_val in levels_map_cli.values())  # Line 30
        + list(level_val.lower() for level_val in levels_map_cli.values())  # Line 31
    )

    parser.add_argument(
        "--log-level",
        default="INFO",  # Default log level if not specified by user
        type=str,
        choices=valid_log_level_choices,
        help=(
            "Set the logging level. "
            f"Valid choices: {', '.join(levels_map_cli.values())} "
            f"or their first letters: {', '.join(levels_map_cli.keys())}. "
            "Case-insensitive."
        ),
        metavar="LEVEL",
    )
    # Add other command-line arguments for your application here if needed
    # parser.add_argument("--some-option", action="store_true",
    # help="An example option")

    # Parse arguments
    # If cli_args_list is None (normal execution), parse from sys.argv.
    # Otherwise (e.g., for testing), parse from the provided list.
    args = parser.parse_args(args=cli_args_list)

    # 2. Determine the final log level string (e.g., "DEBUG", "INFO")
    chosen_log_level_name = args.log_level.upper()
    # If user gave a short form (e.g., "d"), convert to full name ("DEBUG")
    if chosen_log_level_name.lower() in levels_map_cli:
        chosen_log_level_name = levels_map_cli[chosen_log_level_name.lower()].upper()
    # At this point, chosen_log_level_name should be one of "DEBUG",
    # "INFO", etc.

    # 3. Update the LOG_LEVEL variable in __init__.py
    # This makes it available to any modules imported *after* this point,
    # but modules already imported (like logger.py) won't see this change
    # automatically.
    set_package_log_level(chosen_log_level_name)

    # 4. Reconfigure the actual logger instance(s)
    # This is crucial because logger.py likely initialized its logger(s)
    # with the default LOG_LEVEL from __init__.py when it was first imported.
    # In main.py - CORRECTED
    if hasattr(
        app_logger,
        "reconfigure_all_loggers",
    ):  # Check for the correct function name
        app_logger.reconfigure_all_loggers(
            chosen_log_level_name,
        )  # Call the correct function

        # Configure external libraries to use our Rich console logging
        import logging as pylog

        # PyQt6 logging
        qt_logger = pylog.getLogger("PyQt6")
        if hasattr(app_logger, "setup_rich_handler_for_external_logger"):
            app_logger.setup_rich_handler_for_external_logger(
                qt_logger,
                app_logger._dataset_tools_main_rich_console,
                chosen_log_level_name,
            )

        # PIL/Pillow logging
        pil_logger = pylog.getLogger("PIL")
        if hasattr(app_logger, "setup_rich_handler_for_external_logger"):
            app_logger.setup_rich_handler_for_external_logger(
                pil_logger,
                app_logger._dataset_tools_main_rich_console,
                chosen_log_level_name,
            )
    else:
        # This else block might not even be strictly necessary if you know the
        # function exists,
        # but it's good for defensive programming if the logger module could
        # change.
        print(
            f"WARNING (main.py): Logger module does not have "
            f"'reconfigure_all_loggers'. "
            f"Log level '{chosen_log_level_name}' set via CLI may not be "
            f"effective "
            "for already initialized loggers.",
        )
        # You might need to manually set the level on the root logger or your
        # specific logger
        # if no reconfigure function exists, e.g.:
        # import logging as pylog
        # pylog.getLogger("dataset_tools").setLevel(chosen_log_level_name)
        # If you use named loggers
        # pylog.root.setLevel(chosen_log_level_name) # If you modify the root
        # logger

    # Now use your logger (it should reflect the new level if reconfigured)
    app_logger.info_monitor("Dataset Tools v%s launching...", __version__)
    app_logger.info_monitor("Application log level set to: %s", chosen_log_level_name)
    app_logger.info_monitor("Log file location: %s", app_logger.get_log_file_path())
    # Example debug message
    app_logger.debug_message("Arguments parsed: %s", args)

    # 5. Initialize and run the PyQt application
    # For QApplication, sys.argv is usually passed to allow Qt to process its
    # own CLI args
    # (like -style), but it's fine if your argparse has already consumed
    # app-specific ones.
    qt_app_args = sys.argv  # Keep original sys.argv for Qt if needed
    app = QtWidgets.QApplication(qt_app_args)

    # Load all custom fonts from the 'fonts' directory

    fonts_dir = Path(__file__).parent / "fonts"
    if fonts_dir.is_dir():
        for font_file in fonts_dir.iterdir():
            if font_file.suffix.lower() in (".ttf", ".otf"):
                font_id = QFontDatabase.addApplicationFont(str(font_file))
                if font_id != -1:
                    family = QFontDatabase.applicationFontFamilies(font_id)[0]
                    app_logger.info_monitor(f"Successfully loaded font: '{family}' from {font_file.name}")
                else:
                    app_logger.info_monitor(f"Failed to load font: {font_file.name}")

    window = MainWindow()  # Initialize our main window.
    window.show()
    window.apply_global_font()  # Apply saved font settings after UI is fully created

    try:
        exit_code = app.exec()
    finally:
        # Log session end for debugging support
        app_logger.log_session_end()

    sys.exit(exit_code)


if __name__ == "__main__":
    # This block is executed when you run `python dataset_tools/main.py`
    # or `python -m dataset_tools.main`
    # The `dataset-tools` script generated by pip also effectively calls this.
    multiprocessing.freeze_support()  # Essential for Windows compatibility
    main()
