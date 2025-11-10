# dataset_tools/ui/file_tree_panel.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""File Tree Panel - Hierarchical folder/file browser for Dataset Tools.

This module provides a tree-based file browser that shows folders and files
in a hierarchical structure, with lazy loading for performance.
"""

from pathlib import Path

from PyQt6 import QtCore, QtWidgets as Qw
from PyQt6.QtCore import Qt, pyqtSignal

from ..logger import info_monitor as nfo


class FileTreePanel(Qw.QWidget):
    """Tree view panel for hierarchical file browsing.

    Shows expandable folder tree with image files, supporting lazy loading
    for large directory structures.

    Signals:
        file_selected: Emitted when user clicks a file (str: filepath)
        folder_changed: Emitted when user expands a folder (str: folder_path)
    """

    file_selected = pyqtSignal(str)  # filepath
    folder_changed = pyqtSignal(str)  # folder path

    def __init__(self, parent=None):
        """Initialize file tree panel."""
        super().__init__(parent)
        self._root_path = None
        self._supported_extensions = None
        self._init_ui()

    def _init_ui(self):
        """Initialize UI components."""
        layout = Qw.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        # Current path label
        self.path_label = Qw.QLabel("No folder loaded")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("QLabel { color: #888; font-size: 9pt; padding: 5px; }")
        layout.addWidget(self.path_label)

        # Tree view
        self.tree = Qw.QTreeWidget()
        self.tree.setHeaderLabel("Files and Folders")
        self.tree.setColumnCount(1)

        # Enable keyboard search (type letters to jump to files)
        self.tree.setEditTriggers(Qw.QAbstractItemView.EditTrigger.NoEditTriggers)

        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.currentItemChanged.connect(self._on_item_selected)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        layout.addWidget(self.tree)

        # File counter
        self.counter_label = Qw.QLabel("0 files")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.counter_label.setStyleSheet("QLabel { padding: 5px; font-weight: bold; }")
        layout.addWidget(self.counter_label)

    def set_supported_extensions(self, extensions: set[str]):
        """Set which file extensions to display.

        Args:
            extensions: Set of file extensions (e.g., {'.png', '.jpg'})
        """
        self._supported_extensions = extensions

    def set_root_path(self, path: str):
        """Set the root folder and populate tree.

        Args:
            path: Root folder path
        """
        self._root_path = path
        root_folder = Path(path)

        if not root_folder.exists():
            nfo("[FileTreePanel] Root path does not exist: %s", path)
            return

        self.path_label.setText(f"📁 {path}")
        self.tree.clear()

        nfo("[FileTreePanel] Building tree for: %s", path)

        # Build tree
        self._populate_tree(root_folder, self.tree.invisibleRootItem())

        # Count total files
        file_count = self._count_files(root_folder)
        self.counter_label.setText(f"{file_count} file{'s' if file_count != 1 else ''}")

    def _populate_tree(self, folder: Path, parent_item: Qw.QTreeWidgetItem):
        """Recursively populate tree with folders and files.

        Args:
            folder: Folder to scan
            parent_item: Parent tree item
        """
        try:
            items = sorted(folder.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            nfo("[FileTreePanel] Permission denied: %s", folder)
            return

        for item in items:
            if item.is_dir():
                # Add folder
                folder_item = Qw.QTreeWidgetItem(parent_item)
                folder_item.setText(0, f"📁 {item.name}")
                folder_item.setData(0, Qt.ItemDataRole.UserRole, str(item))
                folder_item.setData(0, Qt.ItemDataRole.UserRole + 1, "folder")

                # Add placeholder for lazy loading
                placeholder = Qw.QTreeWidgetItem(folder_item)
                placeholder.setText(0, "...")

            elif self._is_supported_file(item):
                # Add file
                file_item = Qw.QTreeWidgetItem(parent_item)
                file_item.setText(0, f"🖼️ {item.name}")
                file_item.setData(0, Qt.ItemDataRole.UserRole, str(item))
                file_item.setData(0, Qt.ItemDataRole.UserRole + 1, "file")

    def _is_supported_file(self, path: Path) -> bool:
        """Check if file is supported.

        Args:
            path: File path to check

        Returns:
            True if file extension is supported
        """
        if not self._supported_extensions:
            return False
        return path.suffix.lower() in self._supported_extensions

    def _on_item_expanded(self, item: Qw.QTreeWidgetItem):
        """Handle folder expansion - lazy load children.

        Args:
            item: Expanded tree item
        """
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if item_type != "folder":
            return

        # Check if already loaded (no placeholder)
        if item.childCount() == 1 and item.child(0).text(0) == "...":
            # Remove placeholder
            item.removeChild(item.child(0))

            # Load children
            folder_path = Path(item.data(0, Qt.ItemDataRole.UserRole))
            self._populate_tree(folder_path, item)

            self.folder_changed.emit(str(folder_path))
            nfo("[FileTreePanel] Expanded folder: %s", folder_path)

    def _on_item_clicked(self, item: Qw.QTreeWidgetItem, column: int):
        """Handle item click.

        Args:
            item: Clicked item
            column: Column index (unused)
        """
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if item_type == "file":
            filepath = item.data(0, Qt.ItemDataRole.UserRole)
            self.file_selected.emit(filepath)
            nfo("[FileTreePanel] File selected: %s", filepath)

    def _on_item_selected(self, current: Qw.QTreeWidgetItem, previous: Qw.QTreeWidgetItem):
        """Handle item selection change (keyboard navigation).

        Args:
            current: Currently selected item
            previous: Previously selected item (unused)
        """
        if current is None:
            return

        item_type = current.data(0, Qt.ItemDataRole.UserRole + 1)
        if item_type == "file":
            filepath = current.data(0, Qt.ItemDataRole.UserRole)
            self.file_selected.emit(filepath)
            nfo("[FileTreePanel] File selected (keyboard): %s", filepath)

    def _count_files(self, folder: Path) -> int:
        """Count all supported files in folder and subfolders.

        Args:
            folder: Folder to scan

        Returns:
            Number of supported files
        """
        count = 0
        try:
            for item in folder.rglob("*"):
                if item.is_file() and self._is_supported_file(item):
                    count += 1
        except PermissionError:
            pass
        return count

    def get_all_files(self) -> list[str]:
        """Get all supported files from current root path.

        Returns:
            List of file paths
        """
        if not self._root_path:
            return []

        root = Path(self._root_path)
        files = []

        try:
            for item in root.rglob("*"):
                if item.is_file() and self._is_supported_file(item):
                    files.append(str(item))
        except PermissionError:
            pass

        return sorted(files)

    def clear_tree(self):
        """Clear the tree view."""
        self.tree.clear()
        self.path_label.setText("No folder loaded")
        self.counter_label.setText("0 files")
        self._root_path = None
        nfo("[FileTreePanel] Tree cleared")
