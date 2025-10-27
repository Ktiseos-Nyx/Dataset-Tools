"""File Tree Panel - Hierarchical folder/file browser."""

from PyQt6 import QtWidgets as Qw
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path


class FileTreePanel(Qw.QWidget):
    """Panel with tree view of folders and image files.

    Shows expandable folder tree with image files.

    Signals:
        file_selected: Emitted when user clicks an image file (str: filepath)
        folder_changed: Emitted when user expands a folder (str: folder_path)
    """

    file_selected = pyqtSignal(str)  # filepath
    folder_changed = pyqtSignal(str)  # folder path

    def __init__(self, parent=None):
        """Initialize file tree panel."""
        super().__init__(parent)
        self._root_path = None
        self._image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}
        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = Qw.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header with controls
        header_layout = Qw.QHBoxLayout()

        self.browse_btn = Qw.QPushButton("📂 Browse...")
        self.browse_btn.clicked.connect(self._browse_folder)
        header_layout.addWidget(self.browse_btn)

        self.refresh_btn = Qw.QPushButton("🔄")
        self.refresh_btn.setFixedWidth(40)
        self.refresh_btn.setToolTip("Refresh tree")
        self.refresh_btn.clicked.connect(self._refresh_tree)
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        # Current path label
        self.path_label = Qw.QLabel("No folder loaded")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("QLabel { color: #888; font-size: 9pt; padding: 3px; }")
        layout.addWidget(self.path_label)

        # Tree view
        self.tree = Qw.QTreeWidget()
        self.tree.setHeaderLabel("Files and Folders")
        self.tree.setColumnCount(1)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        layout.addWidget(self.tree)

        # File counter
        self.counter_label = Qw.QLabel("0 images")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.counter_label.setStyleSheet("QLabel { padding: 5px; font-weight: bold; }")
        layout.addWidget(self.counter_label)

    def _browse_folder(self):
        """Open folder browser."""
        folder = Qw.QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            str(Path.home()),
            Qw.QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.set_root_path(folder)

    def _refresh_tree(self):
        """Refresh the tree view."""
        if self._root_path:
            self.set_root_path(self._root_path)

    def set_root_path(self, path: str):
        """Set the root folder and populate tree.

        Args:
            path: Root folder path
        """
        self._root_path = path
        root_folder = Path(path)

        if not root_folder.exists():
            return

        self.path_label.setText(f"📁 {path}")
        self.tree.clear()

        # Build tree
        self._populate_tree(root_folder, self.tree.invisibleRootItem())

        # Count total images
        image_count = self._count_images(root_folder)
        self.counter_label.setText(f"{image_count} image{'s' if image_count != 1 else ''}")

    def _populate_tree(self, folder: Path, parent_item: Qw.QTreeWidgetItem):
        """Recursively populate tree with folders and images.

        Args:
            folder: Folder to scan
            parent_item: Parent tree item
        """
        try:
            items = sorted(folder.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
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

            elif item.suffix.lower() in self._image_extensions:
                # Add image file
                file_item = Qw.QTreeWidgetItem(parent_item)
                file_item.setText(0, f"🖼️ {item.name}")
                file_item.setData(0, Qt.ItemDataRole.UserRole, str(item))
                file_item.setData(0, Qt.ItemDataRole.UserRole + 1, "file")

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

    def _on_item_clicked(self, item: Qw.QTreeWidgetItem, column: int):
        """Handle item click.

        Args:
            item: Clicked item
            column: Column index
        """
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if item_type == "file":
            filepath = item.data(0, Qt.ItemDataRole.UserRole)
            self.file_selected.emit(filepath)

    def _count_images(self, folder: Path) -> int:
        """Count all images in folder and subfolders.

        Args:
            folder: Folder to scan

        Returns:
            Number of image files
        """
        count = 0
        try:
            for item in folder.rglob("*"):
                if item.is_file() and item.suffix.lower() in self._image_extensions:
                    count += 1
        except PermissionError:
            pass
        return count

    def get_all_image_files(self) -> list[str]:
        """Get all image files from current root path.

        Returns:
            List of image file paths
        """
        if not self._root_path:
            return []

        root = Path(self._root_path)
        files = []

        try:
            for item in root.rglob("*"):
                if item.is_file() and item.suffix.lower() in self._image_extensions:
                    files.append(str(item))
        except PermissionError:
            pass

        return sorted(files)

    def clear_tree(self):
        """Clear the tree view."""
        self.tree.clear()
        self.path_label.setText("No folder loaded")
        self.counter_label.setText("0 images")
        self._root_path = None
