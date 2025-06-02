# dataset_tools/widgets.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Widgets for Dataset-Tools UI"""

import os
from pathlib import Path

from PyQt6 import QtCore

# Use absolute import from the package root for clarity and robustness
from dataset_tools.correct_types import ExtensionType as Ext
from dataset_tools.logger import debug_monitor
from dataset_tools.logger import info_monitor as nfo


class FileLoader(QtCore.QThread):
    """Opens files in a separate thread to keep the UI responsive.
    Emits signals for progress and when finished.
    """

    # Signal: finished(list_images, list_text_files, list_model_files, folder_path_str, file_to_select_str_or_None)
    finished = QtCore.pyqtSignal(list, list, list, str, object)
    progress = QtCore.pyqtSignal(int)  # For progress updates (0-100)

    def __init__(self, folder_path: str, file_to_select_on_finish: str | None = None):
        super().__init__()
        self.folder_path = folder_path
        self.file_to_select_on_finish = file_to_select_on_finish
        # These lists will be populated by populate_index_from_list
        self.images: list[str] = []
        self.text_files: list[str] = []
        self.model_files: list[str] = []

    def run(self):
        """Scans the directory, categorizes files, and emits the results.
        This method is executed when the thread starts (self.start()).
        """
        nfo(f"[FileLoader] Starting to scan directory: {self.folder_path}")
        folder_contents_paths = self.scan_directory(self.folder_path)

        # populate_index_from_list will categorize files and assign to instance attributes
        # It now returns the lists, so we assign them here.
        self.images, self.text_files, self.model_files = self.populate_index_from_list(
            folder_contents_paths,
        )

        nfo(
            f"[FileLoader] Scan finished. Emitting results for folder: {self.folder_path}. File to select: {self.file_to_select_on_finish}",
        )
        self.finished.emit(
            self.images,
            self.text_files,
            self.model_files,
            self.folder_path,
            self.file_to_select_on_finish,
        )

    @debug_monitor
    def scan_directory(self, folder_path: str) -> list[str] | None:
        """Gathers full paths to all files in the selected folder.
        :param folder_path: The directory path (string) to scan.
        :return: A list of full file paths, or None if an error occurs.
        """
        try:
            # List items in directory
            items_in_folder = os.listdir(folder_path)
            # Construct full paths for each item
            full_paths = [os.path.join(folder_path, item) for item in items_in_folder]
            nfo(
                f"[FileLoader] Scanned {len(full_paths)} items (files/dirs) in directory: {folder_path}",
            )
            return full_paths
        except FileNotFoundError:
            nfo(
                f"FileNotFoundError: Error loading folder '{folder_path}'. Folder not found.",
            )
        except PermissionError:
            nfo(
                f"PermissionError: Error loading folder '{folder_path}'. Insufficient permissions.",
            )
        except OSError as e_os:
            nfo(
                f"OSError: General error loading folder '{folder_path}'. OS related issue: {e_os}",
            )
        except Exception as e_gen:
            nfo(f"Unexpected error loading folder '{folder_path}': {e_gen}")
        return None  # Return None on any error during scanning

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
                "[FileLoader] populate_index_from_list received None for folder_item_paths. Returning empty lists.",
            )
            return [], [], []

        local_images: list[str] = []
        local_text_files: list[str] = []
        local_model_files: list[str] = []

        # --- Debug prints for ExtensionType attributes ---
        # These will help confirm that widgets.py is seeing the correct ExtensionType definition
        print(
            "--- DEBUG WIDGETS: Inspecting Ext (ExtensionType) from correct_types.py ---",
        )
        print(f"DEBUG WIDGETS: Type of Ext: {type(Ext)}")
        # Print only a few
        print(f"DEBUG WIDGETS: Attributes of Ext (first few): {dir(Ext)[:15]}...")

        # Check for specific attributes by their correct names
        expected_attrs = [
            "IMAGE",
            "SCHEMA_FILES",
            "MODEL_FILES",
            "PLAIN_TEXT_LIKE",
            "IGNORE",
        ]
        for attr_name in expected_attrs:
            has_attr = hasattr(Ext, attr_name)
            print(f"DEBUG WIDGETS: Does Ext have '{attr_name}'? {has_attr}")
            if has_attr:
                attr_value = getattr(Ext, attr_name)
                # Avoid printing huge lists if they are very long
                print_val = str(attr_value)
                if len(print_val) > 100:
                    print_val = print_val[:100] + "..."
                print(f"DEBUG WIDGETS: Value of Ext.{attr_name}: {print_val}")
        print("--- END DEBUG WIDGETS ---")
        # --- End Debug prints ---

        # Flatten extension lists for easier checking.
        # These rely on Ext having the correct attributes like IMAGE, SCHEMA_FILES, etc.
        all_image_exts = {ext for ext_set in Ext.IMAGE for ext in ext_set}

        all_plain_exts_final = set()
        # Use hasattr to safely check for PLAIN_TEXT_LIKE before iterating
        if hasattr(Ext, "PLAIN_TEXT_LIKE"):
            for ext_set in Ext.PLAIN_TEXT_LIKE:
                all_plain_exts_final.update(ext_set)
        else:
            nfo(
                "[FileLoader] WARNING: Ext.PLAIN_TEXT_LIKE attribute not found in ExtensionType.",
            )

        all_schema_exts = set()
        if hasattr(Ext, "SCHEMA_FILES"):
            all_schema_exts = {
                ext for ext_set in Ext.SCHEMA_FILES for ext in ext_set
            }  # CORRECTED
        else:
            nfo(
                "[FileLoader] WARNING: Ext.SCHEMA_FILES attribute not found in ExtensionType.",
            )

        all_model_exts = set()
        if hasattr(Ext, "MODEL_FILES"):
            all_model_exts = {
                ext for ext_set in Ext.MODEL_FILES for ext in ext_set
            }  # CORRECTED
        else:
            nfo(
                "[FileLoader] WARNING: Ext.MODEL_FILES attribute not found in ExtensionType.",
            )

        all_text_like_exts = all_plain_exts_final.union(all_schema_exts)

        # Ensure Ext.IGNORE exists and is a list/set of strings
        ignore_list = []
        if hasattr(Ext, "IGNORE") and isinstance(Ext.IGNORE, list):
            ignore_list = Ext.IGNORE
        else:
            nfo(
                "[FileLoader] WARNING: Ext.IGNORE attribute not found or not a list in ExtensionType. Using empty ignore list.",
            )

        total_items = len(folder_item_paths)
        processed_count = 0
        current_progress_percent = 0  # To avoid emitting same progress repeatedly

        for f_path_str in folder_item_paths:
            try:
                path = Path(str(f_path_str))  # Ensure f_path_str is string
                if (
                    path.is_file() and path.name not in ignore_list
                ):  # Use the verified ignore_list
                    suffix = path.suffix.lower()
                    file_name_only = (
                        path.name
                    )  # We only need the name for the QListWidget

                    if suffix in all_image_exts:
                        local_images.append(file_name_only)
                    elif suffix in all_text_like_exts:
                        local_text_files.append(file_name_only)
                    elif suffix in all_model_exts:
                        local_model_files.append(file_name_only)
                # else:
                # nfo(f"[FileLoader] Skipping non-file or ignored item: {path.name}") # Can be noisy
            except (
                Exception
            ) as e_path:  # Catch errors related to Path object or os.path operations
                nfo(f"[FileLoader] Error processing path '{f_path_str}': {e_path}")

            processed_count += 1
            if total_items > 0:
                progress_percent = int((processed_count / total_items) * 100)
                # Emit progress if it has changed significantly or for key milestones
                if progress_percent > current_progress_percent and (
                    progress_percent % 5 == 0 or progress_percent == 100
                ):
                    self.progress.emit(progress_percent)
                    current_progress_percent = progress_percent

        # Emit final 100% progress if not already done
        if total_items > 0 and current_progress_percent < 100:
            self.progress.emit(100)

        # Sort the lists of filenames
        local_images.sort()
        local_text_files.sort()
        local_model_files.sort()

        nfo(
            f"[FileLoader] Categorized files: {len(local_images)} images, {len(local_text_files)} text/schema, {len(local_model_files)} models.",
        )
        return local_images, local_text_files, local_model_files
