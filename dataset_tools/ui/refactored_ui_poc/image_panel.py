"""Image Panel - Encapsulated image preview component."""

from PyQt6 import QtWidgets as Qw
from PyQt6 import QtGui, QtCore
from PyQt6.QtCore import Qt


class ImagePanel(Qw.QWidget):
    """Panel for displaying image previews.

    This is a self-contained widget for showing scaled image previews.

    Signals:
        image_clicked: Emitted when user clicks on the image
    """

    image_clicked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the image panel.

        Args:
            parent: Parent widget (usually MainWindow)
        """
        super().__init__(parent)
        self._current_pixmap = None
        self._current_filepath = None
        self._init_ui()

    def _init_ui(self):
        """Initialize UI components."""
        layout = Qw.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Image label with scaled contents
        self.image_label = Qw.QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(200, 200)
        self.image_label.setStyleSheet("QLabel { border: 1px solid #444; }")
        self.image_label.setText("No image loaded")
        self.image_label.setScaledContents(False)  # We'll scale manually for aspect ratio

        # Enable click detection
        self.image_label.mousePressEvent = self._on_image_clicked

        layout.addWidget(self.image_label)

        # Optional: Add image info label
        self.info_label = Qw.QLabel("")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("QLabel { color: #888; font-size: 10pt; }")
        layout.addWidget(self.info_label)

    def _on_image_clicked(self, event):
        """Handle image click."""
        if self._current_pixmap:
            self.image_clicked.emit()

    def set_image(self, filepath: str):
        """Load and display an image from file.

        Args:
            filepath: Path to the image file
        """
        self._current_filepath = filepath

        try:
            pixmap = QtGui.QPixmap(filepath)
            if pixmap.isNull():
                self._show_error("Failed to load image")
                return

            self._current_pixmap = pixmap
            self._update_display()

            # Update info label with image dimensions
            import os
            filename = os.path.basename(filepath)
            dimensions = f"{pixmap.width()} × {pixmap.height()}"
            self.info_label.setText(f"{filename}\n{dimensions}")

        except Exception as e:
            self._show_error(f"Error loading image: {e}")

    def set_pixmap(self, pixmap: QtGui.QPixmap):
        """Directly set a QPixmap to display.

        Args:
            pixmap: QPixmap to display
        """
        self._current_pixmap = pixmap
        self._current_filepath = None
        self._update_display()

        if pixmap and not pixmap.isNull():
            dimensions = f"{pixmap.width()} × {pixmap.height()}"
            self.info_label.setText(dimensions)
        else:
            self.info_label.setText("")

    def _update_display(self):
        """Update the image display with proper scaling."""
        if not self._current_pixmap or self._current_pixmap.isNull():
            self._show_error("No image")
            return

        # Scale pixmap to fit label while maintaining aspect ratio
        scaled_pixmap = self._current_pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.image_label.setPixmap(scaled_pixmap)

    def _show_error(self, message: str):
        """Show error message instead of image."""
        self.image_label.clear()
        self.image_label.setText(message)
        self.info_label.setText("")
        self._current_pixmap = None

    def clear_image(self):
        """Clear the displayed image."""
        self.image_label.clear()
        self.image_label.setText("No image loaded")
        self.info_label.setText("")
        self._current_pixmap = None
        self._current_filepath = None

    def resizeEvent(self, event):
        """Handle resize events to rescale image."""
        super().resizeEvent(event)
        if self._current_pixmap:
            self._update_display()
