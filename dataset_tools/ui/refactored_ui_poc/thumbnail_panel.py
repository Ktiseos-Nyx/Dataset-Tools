"""Thumbnail Panel - Grid view of all images."""

from PyQt6 import QtWidgets as Qw
from PyQt6 import QtGui, QtCore
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path


class ThumbnailGridWidget(Qw.QWidget):
    """Grid widget that shows image thumbnails.

    Signals:
        thumbnail_clicked: Emitted when user clicks a thumbnail (str: filepath)
    """

    thumbnail_clicked = pyqtSignal(str)  # filepath

    def __init__(self, parent=None):
        """Initialize thumbnail grid."""
        super().__init__(parent)
        self._thumbnails = []  # List of (filepath, QPixmap) tuples
        self._thumbnail_size = 150  # Thumbnail width/height
        self._spacing = 10
        self._columns = 4  # Default columns

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = Qw.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Scroll area for grid
        scroll = Qw.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Grid container
        self.grid_container = Qw.QWidget()
        self.grid_layout = Qw.QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(self._spacing)

        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll)

    def set_images(self, filepaths: list[str]):
        """Load thumbnails for given image files.

        Args:
            filepaths: List of image file paths
        """
        # Clear existing thumbnails
        self._clear_grid()
        self._thumbnails = []

        # Load thumbnails
        for filepath in filepaths:
            pixmap = QtGui.QPixmap(filepath)
            if not pixmap.isNull():
                # Scale to thumbnail size
                thumb = pixmap.scaled(
                    self._thumbnail_size,
                    self._thumbnail_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._thumbnails.append((filepath, thumb))

        # Rebuild grid
        self._rebuild_grid()

    def _clear_grid(self):
        """Clear all items from grid."""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _rebuild_grid(self):
        """Rebuild the thumbnail grid."""
        self._clear_grid()

        row = 0
        col = 0

        for filepath, pixmap in self._thumbnails:
            # Create thumbnail button
            btn = Qw.QPushButton()
            btn.setFixedSize(self._thumbnail_size, self._thumbnail_size)
            btn.setIcon(QtGui.QIcon(pixmap))
            btn.setIconSize(QtCore.QSize(self._thumbnail_size - 10, self._thumbnail_size - 10))
            btn.setToolTip(Path(filepath).name)
            btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid #444;
                    background-color: #2A2A2A;
                    padding: 2px;
                }
                QPushButton:hover {
                    border: 2px solid #6A6A6A;
                    background-color: #3A3A3A;
                }
            """)

            # Connect click to emit filepath
            btn.clicked.connect(lambda checked, fp=filepath: self.thumbnail_clicked.emit(fp))

            self.grid_layout.addWidget(btn, row, col)

            col += 1
            if col >= self._columns:
                col = 0
                row += 1

    def clear_thumbnails(self):
        """Clear all thumbnails."""
        self._clear_grid()
        # Clear pixmaps to release memory
        for filepath, pixmap in self._thumbnails:
            if pixmap:
                pixmap = None
        self._thumbnails = []

    def resizeEvent(self, event):
        """Handle resize to adjust columns."""
        super().resizeEvent(event)

        # Calculate how many columns fit
        available_width = self.width() - 40  # Account for margins/scrollbar
        new_columns = max(1, available_width // (self._thumbnail_size + self._spacing))

        if new_columns != self._columns:
            self._columns = new_columns
            self._rebuild_grid()


class ThumbnailPanel(Qw.QWidget):
    """Panel containing thumbnail grid with header.

    Signals:
        thumbnail_selected: Emitted when user clicks a thumbnail (str: filepath)
    """

    thumbnail_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        """Initialize thumbnail panel."""
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = Qw.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Header with count
        self.count_label = Qw.QLabel("No thumbnails loaded")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet("QLabel { padding: 5px; font-weight: bold; }")
        layout.addWidget(self.count_label)

        # Grid widget
        self.grid_widget = ThumbnailGridWidget(self)
        self.grid_widget.thumbnail_clicked.connect(self._on_thumbnail_clicked)
        layout.addWidget(self.grid_widget)

    def _on_thumbnail_clicked(self, filepath: str):
        """Handle thumbnail click."""
        self.thumbnail_selected.emit(filepath)

    def set_images(self, filepaths: list[str]):
        """Load images as thumbnails.

        Args:
            filepaths: List of image file paths
        """
        self.grid_widget.set_images(filepaths)
        count = len(filepaths)
        self.count_label.setText(f"{count} image{'s' if count != 1 else ''}")

    def clear_thumbnails(self):
        """Clear all thumbnails."""
        self.grid_widget.clear_thumbnails()
        self.count_label.setText("No thumbnails loaded")
