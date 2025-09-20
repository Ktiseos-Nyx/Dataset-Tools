# dataset_tools/widgets.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Widgets for Dataset-Tools UI."""

import os
from pathlib import Path
from typing import NamedTuple  # Removed List as TypingList, Optional if progress bar gone

from PyQt6 import QtCore, QtGui
from PyQt6 import QtWidgets as Qw

from dataset_tools.correct_types import ExtensionType as Ext
from dataset_tools.logger import (
    debug_message,  # Import debug_message
    debug_monitor,
)
from dataset_tools.logger import info_monitor as nfo


class FileLoadResult(NamedTuple):
    images: list[str]
    texts: list[str]
    models: list[str]
    folder_path: str
    file_to_select: str | None


class FileLoader(QtCore.QThread):
    """Opens files in a separate thread to keep the UI responsive.
    Emits a signal when finished.
    """

    finished = QtCore.pyqtSignal(FileLoadResult)
    # progress = QtCore.pyqtSignal(int) # REMOVED if progress bar is gone

    def __init__(self, folder_path: str, file_to_select_on_finish: str | None = None):
        super().__init__()
        self.folder_path = folder_path
        self.file_to_select_on_finish = file_to_select_on_finish

    def run(self):
        nfo("[FileLoader] Starting to scan directory: %s", self.folder_path)
        folder_contents_paths = self.scan_directory(self.folder_path)
        images_list, text_files_list, model_files_list = self.populate_index_from_list(
            folder_contents_paths,
        )
        result = FileLoadResult(
            images=images_list,
            texts=text_files_list,
            models=model_files_list,
            folder_path=self.folder_path,
            file_to_select=self.file_to_select_on_finish,
        )
        nfo(
            (
                "[FileLoader] Scan finished. Emitting result for folder: %s. "
                "File to select: %s. Counts: Img=%s, Txt=%s, Mdl=%s"
            ),
            result.folder_path,
            result.file_to_select,
            len(result.images),
            len(result.texts),
            len(result.models),
        )
        self.finished.emit(result)

    @debug_monitor
    def scan_directory(self, folder_path: str) -> list[str] | None:
        try:
            # Consider replacing with pathlib for consistency if desired
            items_in_folder = os.listdir(folder_path)
            full_paths = [os.path.join(folder_path, item) for item in items_in_folder]
            nfo(
                "[FileLoader] Scanned %s items (files/dirs) in directory: %s",
                len(full_paths),
                folder_path,
            )
            return full_paths
        except FileNotFoundError:
            nfo(
                "FileNotFoundError: Error loading folder '%s'. Folder not found.",
                folder_path,
            )
        except PermissionError:
            nfo(
                "PermissionError: Error loading folder '%s'. Insufficient permissions.",
                folder_path,
            )
        except OSError as e_os:
            nfo(
                "OSError: General error loading folder '%s'. OS related issue: %s",
                folder_path,
                e_os,
            )
        return None

    @debug_monitor
    def populate_index_from_list(
        self,
        folder_item_paths: list[str] | None,
    ) -> tuple[list[str], list[str], list[str]]:
        if folder_item_paths is None:
            nfo("[FileLoader] populate_index_from_list received None. Returning empty lists.")
            return [], [], []

        local_images: list[str] = []
        local_text_files: list[str] = []
        local_model_files: list[str] = []

        if os.getenv("DEBUG_WIDGETS_EXT"):
            debug_message("--- DEBUG WIDGETS: Inspecting Ext (ExtensionType) ---")  # CHANGED
            debug_message("DEBUG WIDGETS: Type of Ext: %s", type(Ext))  # CHANGED
            expected_attrs = [
                "IMAGE",
                "SCHEMA_FILES",
                "MODEL_FILES",
                "PLAIN_TEXT_LIKE",
                "IGNORE",
            ]
            for attr_name in expected_attrs:
                has_attr = hasattr(Ext, attr_name)
                val_str = str(getattr(Ext, attr_name, "N/A"))
                val_display = val_str[:70] + "..." if len(val_str) > 70 else val_str
                # Break long log message
                debug_message(
                    "DEBUG WIDGETS: Ext.%s? %s. Value (first 70 chars): %s",  # CHANGED
                    attr_name,
                    has_attr,
                    val_display,
                )
            debug_message("--- END DEBUG WIDGETS ---")  # CHANGED

        all_image_exts = {ext for ext_set in getattr(Ext, "IMAGE", []) for ext in ext_set}
        all_plain_exts_final = set()
        if hasattr(Ext, "PLAIN_TEXT_LIKE"):
            for ext_set in Ext.PLAIN_TEXT_LIKE:
                all_plain_exts_final.update(ext_set)
        else:
            nfo("[FileLoader] WARNING: Ext.PLAIN_TEXT_LIKE attribute not found.")
        all_schema_exts = set()
        if hasattr(Ext, "SCHEMA_FILES"):
            all_schema_exts = {ext for ext_set in Ext.SCHEMA_FILES for ext in ext_set}
        else:
            nfo("[FileLoader] WARNING: Ext.SCHEMA_FILES attribute not found.")
        all_model_exts = set()
        if hasattr(Ext, "MODEL_FILES"):
            all_model_exts = {ext for ext_set in Ext.MODEL_FILES for ext in ext_set}
        else:
            nfo("[FileLoader] WARNING: Ext.MODEL_FILES attribute not found.")
        all_text_like_exts = all_plain_exts_final.union(all_schema_exts)
        ignore_list = getattr(Ext, "IGNORE", [])
        if not isinstance(ignore_list, list):
            nfo("[FileLoader] WARNING: Ext.IGNORE is not a list. Using empty ignore list.")
            ignore_list = []

        # Progress calculation and emission REMOVED
        # total_items = len(folder_item_paths)
        # processed_count = 0
        # current_progress_percent = 0

        for f_path_str in folder_item_paths:
            try:
                path = Path(str(f_path_str))
                if path.is_file() and path.name not in ignore_list:
                    suffix = path.suffix.lower()
                    file_name_only = path.name
                    if suffix in all_image_exts:
                        local_images.append(file_name_only)
                    elif suffix in all_text_like_exts:
                        local_text_files.append(file_name_only)
                    elif suffix in all_model_exts:
                        local_model_files.append(file_name_only)
            except (OSError, ValueError, TypeError, AttributeError) as e_path_specific:
                nfo(
                    "[FileLoader] Specific error processing path '%s': %s",
                    f_path_str,
                    e_path_specific,
                )
            except Exception as e_path_general:
                nfo(
                    "[FileLoader] General error processing path '%s': %s",
                    f_path_str,
                    e_path_general,
                    exc_info=True,  # This call should now be fine
                )
            # Progress emission REMOVED
            # processed_count += 1
            # ... (rest of progress logic removed) ...

        # Final progress emit REMOVED
        # ...

        local_images.sort()
        local_text_files.sort()
        local_model_files.sort()
        nfo(
            "[FileLoader] Categorized files: %s images, %s text/schema, %s models.",
            len(local_images),
            len(local_text_files),
            len(local_model_files),
        )
        return local_images, local_text_files, local_model_files


# --- ADD THE MISSING WIDGET DEFINITIONS ---


class LeftPanelWidget(Qw.QWidget):
    """Custom widget for the left panel, containing folder controls and file list."""

    # Define signals that this widget can emit
    open_folder_requested = QtCore.pyqtSignal()
    sort_files_requested = QtCore.pyqtSignal(str)  # Emits sort order string
    list_item_selected = QtCore.pyqtSignal(str)  # Emits selected file name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = Qw.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # No external margins, handled by splitter
        self.layout.setSpacing(5)

        # 1. Folder Path Display and Open Button
        folder_controls_layout = Qw.QHBoxLayout()
        self.folder_path_display = Qw.QLineEdit()
        self.folder_path_display.setPlaceholderText("Current Folder Path...")
        self.folder_path_display.setReadOnly(True)
        folder_controls_layout.addWidget(self.folder_path_display, 1)

        self.open_folder_button = Qw.QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_folder_requested.emit)  # Emit signal
        folder_controls_layout.addWidget(self.open_folder_button)
        self.layout.addLayout(folder_controls_layout)

        # 2. File List (QListWidget)
        self.file_list_widget = Qw.QListWidget()
        self.file_list_widget.currentItemChanged.connect(self._on_list_item_changed)
        self.layout.addWidget(self.file_list_widget, 1)  # Give it stretch factor

        # 3. Sort Controls (Example)
        sort_controls_layout = Qw.QHBoxLayout()
        sort_controls_layout.addWidget(Qw.QLabel("Sort by:"))
        self.sort_combo = Qw.QComboBox()
        self.sort_combo.addItems(["Name (Asc)", "Name (Desc)", "Type", "Date Modified"])  # Example sort options
        self.sort_combo.currentTextChanged.connect(self.sort_files_requested.emit)  # Emit signal
        sort_controls_layout.addWidget(self.sort_combo)
        sort_controls_layout.addStretch()
        self.layout.addLayout(sort_controls_layout)

        # Placeholder method for updating folder path display

    def set_folder_path_display(self, path_str: str):
        self.folder_path_display.setText(path_str)

    def _on_list_item_changed(self, current_item: Qw.QListWidgetItem, previous_item: Qw.QListWidgetItem):
        # Ensure current_item is not None before accessing its text
        if current_item:
            self.list_item_selected.emit(current_item.text())
        # else:
        # Optionally emit None or an empty string if selection is cleared
        # self.list_item_selected.emit("")


class ImageLabel(Qw.QLabel):
    """Custom QLabel for displaying images, potentially with scaling and aspect ratio handling."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(Qw.QFrame.Shape.StyledPanel)  # Example: give it a border
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setText("Image Preview Area")  # Placeholder text
        self.setMinimumSize(200, 200)  # Ensure it has some size

    def set_pixmap(self, pixmap: QtGui.QPixmap | None):
        if pixmap and not pixmap.isNull():
            # Scale pixmap to fit the label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            super().setPixmap(scaled_pixmap)
        else:
            self.setText("No Image / Error Loading")  # Or clear it

    # Override resizeEvent to rescale the pixmap when the label is resized
    def resizeEvent(self, event: QtGui.QResizeEvent):
        if self.pixmap() and not self.pixmap().isNull():  # type: ignore
            # Create a QPixmap from the current pixmap to avoid issues if it's None
            current_pixmap = QtGui.QPixmap(self.pixmap())  # type: ignore
            if not current_pixmap.isNull():
                self.set_pixmap(current_pixmap)
        super().resizeEvent(event)
