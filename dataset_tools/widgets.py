# dataset_tools/widgets.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Widgets for Dataset-Tools UI"""

import os
from pathlib import Path
from typing import NamedTuple

from PyQt6 import QtCore

# Use absolute import from the package root for clarity and robustness
from dataset_tools.correct_types import ExtensionType as Ext
from dataset_tools.logger import debug_monitor
from dataset_tools.logger import info_monitor as nfo


# Define the data structure for FileLoader results
class FileLoadResult(NamedTuple):
    images: list[str]
    texts: list[str]
    models: list[str]
    folder_path: str
    file_to_select: str | None


class FileLoader(QtCore.QThread):
    """Opens files in a separate thread to keep the UI responsive.
    Emits signals for progress and when finished.
    """

    # Signal now emits a single FileLoadResult object
    finished = QtCore.pyqtSignal(FileLoadResult)
    progress = QtCore.pyqtSignal(int)  # For progress updates (0-100)

    def __init__(self, folder_path: str, file_to_select_on_finish: str | None = None):
        super().__init__()
        self.folder_path = folder_path
        self.file_to_select_on_finish = file_to_select_on_finish
        # Instance attributes for storing categorized files are no longer strictly needed here
        # if run() directly constructs and emits the result based on populate_index_from_list return.
        # However, keeping them can be useful if other methods in FileLoader might need them.
        # For this refactor, populate_index_from_list will return them, and run() will use those.

    def run(self):
        """Scans the directory, categorizes files, and emits the results.
        This method is executed when the thread starts (self.start()).
        """
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

        nfo(  # Corrected for line length and using result attributes
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
        """Gathers full paths to all files in the selected folder.
        :param folder_path: The directory path (string) to scan.
        :return: A list of full file paths, or None if an error occurs.
        """
        try:
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
        # Removed blind except Exception as specific errors are caught.
        # If other OS-level errors are common, they could be added to the OSError catch.
        return None

    @debug_monitor
    def populate_index_from_list(
        self,
        folder_item_paths: list[str] | None,
    ) -> tuple[list[str], list[str], list[str]]:
        """Categorizes files from a list of full paths into images, text-like, and model files.
        :param folder_item_paths: A list of full paths to items in a folder.
        :return: A tuple of three lists: (image_filenames, text_filenames, model_filenames).
        """
        if folder_item_paths is None:
            nfo(
                "[FileLoader] populate_index_from_list received None. Returning empty lists."
            )
            return [], [], []

        local_images: list[str] = []
        local_text_files: list[str] = []
        local_model_files: list[str] = []

        # Debug prints for ExtensionType attributes (shortened to avoid line length issues)
        # These are primarily for developer diagnosis, not regular operation.
        if os.getenv("DEBUG_WIDGETS_EXT"):  # Optional debug via environment variable
            print("--- DEBUG WIDGETS: Inspecting Ext (ExtensionType) ---")
            print(f"DEBUG WIDGETS: Type of Ext: {type(Ext)}")
            # Print only a few attributes, and shorten their value representation
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
                print(
                    f"DEBUG WIDGETS: Ext.{attr_name}? {has_attr}. Value: {val_display}"
                )
            print("--- END DEBUG WIDGETS ---")

        # Flatten extension lists for easier checking.
        all_image_exts = {
            ext for ext_set in getattr(Ext, "IMAGE", []) for ext in ext_set
        }

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
            nfo(
                "[FileLoader] WARNING: Ext.IGNORE is not a list. Using empty ignore list."
            )
            ignore_list = []

        total_items = len(folder_item_paths)
        processed_count = 0
        current_progress_percent = 0

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
            # Catch more specific errors for path operations
            except (OSError, ValueError, TypeError, AttributeError) as e_path_specific:
                nfo(
                    "[FileLoader] Specific error processing path '%s': %s",
                    f_path_str,
                    e_path_specific,
                )
            except (
                Exception
            ) as e_path_general:  # Fallback for truly unexpected path issues
                nfo(
                    "[FileLoader] General error processing path '%s': %s",
                    f_path_str,
                    e_path_general,
                    exc_info=True,
                )

            processed_count += 1
            if total_items > 0:
                progress_percent = int((processed_count / total_items) * 100)
                if progress_percent > current_progress_percent and (
                    progress_percent % 5 == 0 or progress_percent == 100
                ):
                    self.progress.emit(progress_percent)
                    current_progress_percent = progress_percent

        if total_items > 0 and current_progress_percent < 100:
            self.progress.emit(100)

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
