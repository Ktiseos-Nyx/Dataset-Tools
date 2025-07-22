# dataset_tools/event_handlers.py
# --- FINAL POLISHED VERSION ---

"""Event handlers for the Dataset Tools application.

This module provides event handling functions for UI interactions,
including file selection, metadata display, and image preview functionality.
"""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6 import QtWidgets as Qw

from .correct_types import ExtensionType as Ext
from .display_formatter import format_metadata_for_display

# --- This is the fix for circular import type hints ---
if TYPE_CHECKING:
    from .ui import MainWindow  # This import only runs for type checkers

log = logging.getLogger(__name__)

# --- Main Handler Function (The Conductor) ---


def handle_file_selection(main_window: "MainWindow", current_item: Qw.QListWidgetItem | None):
    """Orchestrates all actions when a new file is selected."""
    if not current_item:
        _handle_no_selection(main_window)
        return

    main_window.clear_selection()
    file_name = current_item.text()
    _update_status_for_selection(main_window, file_name)

    if not main_window.current_folder or not file_name:
        log.warning("Folder/file context is missing, cannot proceed.")
        # We can now directly call the formatter, but since
        # MainWindow already does this...
        # ...it's better to just call the method on MainWindow. Your original
        # code was correct.

        formatted_data = format_metadata_for_display(
            {main_window.EmptyField.PLACEHOLDER.value: {"Error": "Folder/file context missing."}}
        )
        main_window.display_text_of(formatted_data)
        return

    full_file_path = os.path.join(main_window.current_folder, file_name)

    # Do the file check once at the beginning
    if not Path(full_file_path).is_file():
        log.warning("Path check FAILED for '%s'. It is not a file.", full_file_path)
        # Display the file name in the text panels even if it's not a valid file
        metadata_dict = main_window.load_metadata(file_name)
        main_window.display_text_of(metadata_dict)
        return

    _process_image_preview(main_window, full_file_path, file_name)

    metadata_dict = main_window.load_metadata(file_name)
    main_window.display_text_of(metadata_dict)


# --- Helper functions for this module ---


def _handle_no_selection(main_window: "MainWindow"):
    """Clears UI elements when no file is selected."""
    main_window.clear_selection()
    if hasattr(main_window, "left_panel"):
        main_window.left_panel.set_message_text("No file selected.")
    main_window.main_status_bar.showMessage("No file selected.", 3000)
    log.info("File selection cleared or current_item is None.")


def _update_status_for_selection(main_window: "MainWindow", file_name: str):
    """Updates the status bar and other UI text for a new selection."""
    if hasattr(main_window, "left_panel"):
        count = len(main_window.current_files_in_list)
        folder_name = Path(main_window.current_folder).name if main_window.current_folder else "Unknown"
        main_window.left_panel.set_message_text(f"{count} file(s) in {folder_name}")
    main_window.main_status_bar.showMessage(f"Selected: {file_name}", 4000)
    log.info("File selected: '%s' in folder '%s'", file_name, main_window.current_folder)


def _process_image_preview(main_window: "MainWindow", full_file_path: str, file_name: str):
    """Checks if a file is an image and calls the display function if it is."""
    file_suffix_lower = Path(full_file_path).suffix.lower()

    # Create a single set of all valid image extensions for a fast check
    all_image_exts = {ext for ext_set in getattr(Ext, "IMAGE", []) for ext in ext_set}

    if file_suffix_lower in all_image_exts:
        log.debug("File '%s' is a displayable image, showing preview.", file_name)
        main_window.display_image_of(full_file_path)
    else:
        log.debug("File '%s' did not match any image format set for display.", file_name)
