"""File Panel - Encapsulated file browser component."""

from PyQt6 import QtWidgets as Qw
from PyQt6.QtCore import pyqtSignal, Qt


class FilePanel(Qw.QWidget):
    """Panel for browsing and selecting image files.

    This is a self-contained widget that manages file list display and selection.

    Signals:
        file_selected: Emitted when user selects a file (str: filepath)
        folder_open_requested: Emitted when user clicks open folder button
        sort_requested: Emitted when user clicks sort button (str: sort_type)
    """

    file_selected = pyqtSignal(str)  # filepath
    folder_open_requested = pyqtSignal()
    sort_requested = pyqtSignal(str)  # sort type

    def __init__(self, parent=None):
        """Initialize the file panel.

        Args:
            parent: Parent widget (usually MainWindow)
        """
        super().__init__(parent)
        self._current_folder = None
        self._file_list = []
        self._init_ui()

    def _init_ui(self):
        """Initialize UI components."""
        layout = Qw.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Top controls
        controls_layout = Qw.QHBoxLayout()

        self.open_folder_btn = Qw.QPushButton("Open Folder")
        self.open_folder_btn.clicked.connect(self.folder_open_requested.emit)
        controls_layout.addWidget(self.open_folder_btn)

        self.sort_combo = Qw.QComboBox()
        self.sort_combo.addItems([
            "Name (A-Z)",
            "Name (Z-A)",
            "Date Modified (Newest)",
            "Date Modified (Oldest)",
            "Size (Largest)",
            "Size (Smallest)"
        ])
        self.sort_combo.currentTextChanged.connect(self._on_sort_changed)
        controls_layout.addWidget(self.sort_combo)

        layout.addLayout(controls_layout)

        # File counter label
        self.file_count_label = Qw.QLabel("No files loaded")
        self.file_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.file_count_label)

        # File list
        self.file_list_widget = Qw.QListWidget()
        self.file_list_widget.itemClicked.connect(self._on_file_clicked)
        layout.addWidget(self.file_list_widget)

    def _on_sort_changed(self, sort_type: str):
        """Handle sort type change."""
        self.sort_requested.emit(sort_type)

    def _on_file_clicked(self, item):
        """Handle file selection."""
        filepath = item.data(Qt.ItemDataRole.UserRole)
        if filepath:
            self.file_selected.emit(filepath)

    def set_files(self, file_paths: list[str], folder_path: str = None):
        """Update the file list.

        Args:
            file_paths: List of file paths to display
            folder_path: Optional folder path for display
        """
        self._file_list = file_paths
        self._current_folder = folder_path

        self.file_list_widget.clear()

        for filepath in file_paths:
            # Extract just the filename for display
            import os
            filename = os.path.basename(filepath)

            item = Qw.QListWidgetItem(filename)
            item.setData(Qt.ItemDataRole.UserRole, filepath)  # Store full path
            self.file_list_widget.addItem(item)

        # Update counter
        count = len(file_paths)
        self.file_count_label.setText(f"{count} file{'s' if count != 1 else ''} loaded")

    def clear_files(self):
        """Clear the file list."""
        self.file_list_widget.clear()
        self._file_list = []
        self.file_count_label.setText("No files loaded")

    def get_selected_file(self) -> str | None:
        """Get the currently selected file path.

        Returns:
            Selected filepath or None if nothing selected
        """
        current_item = self.file_list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def select_file_by_path(self, filepath: str):
        """Programmatically select a file by its path.

        Args:
            filepath: Full path to the file to select
        """
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == filepath:
                self.file_list_widget.setCurrentItem(item)
                break
