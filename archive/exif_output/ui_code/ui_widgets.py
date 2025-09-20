# dataset_tools/ui_widgets.py

"""UI Widgets for Dataset-Tools.

This module contains all the custom UI widgets used in the application.
Each widget has a specific purpose and clean interface
"""

import sys
from pathlib import Path

from PyQt6 import QtCore, QtGui
from PyQt6 import QtWidgets as Qw
from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter

from .logger import get_logger

log = get_logger(__name__)


# ============================================================================
# FILE LIST WIDGET
# ============================================================================


class FileListWidget(Qw.QWidget):
    """Widget for displaying and managing a list of files.

    This combines a file list with controls for sorting and filtering.
    Think of it as your inventory screen with sorting options! 📦
    """

    # Signals
    file_selected = QtCore.pyqtSignal(str)  # Emits selected filename
    sort_changed = QtCore.pyqtSignal(str)  # Emits sort option

    def __init__(self, parent=None):
        """Initialize the file list widget."""
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.FileListWidget")

        self._current_files: list[str] = []
        self._filtered_files: list[str] = []

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = Qw.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # File list
        self.list_widget = Qw.QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setSelectionMode(Qw.QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.list_widget, 1)  # Give it most of the space

        # Sort controls
        sort_layout = Qw.QHBoxLayout()
        sort_layout.addWidget(Qw.QLabel("Sort:"))

        self.sort_combo = Qw.QComboBox()
        self.sort_combo.addItems(["Name (A-Z)", "Name (Z-A)", "Type", "Size", "Date Modified"])
        sort_layout.addWidget(self.sort_combo)
        sort_layout.addStretch()

        layout.addLayout(sort_layout)

        # Filter controls
        filter_layout = Qw.QHBoxLayout()
        filter_layout.addWidget(Qw.QLabel("Filter:"))

        self.filter_edit = Qw.QLineEdit()
        self.filter_edit.setPlaceholderText("Type to filter files...")
        filter_layout.addWidget(self.filter_edit)

        self.clear_filter_btn = Qw.QPushButton("Clear")
        self.clear_filter_btn.setMaximumWidth(60)
        filter_layout.addWidget(self.clear_filter_btn)

        layout.addLayout(filter_layout)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.list_widget.currentItemChanged.connect(self._on_selection_changed)
        self.sort_combo.currentTextChanged.connect(self._on_sort_changed)
        self.filter_edit.textChanged.connect(self._on_filter_changed)
        self.clear_filter_btn.clicked.connect(self._clear_filter)

    def set_files(self, files: list[str]) -> None:
        """Set the list of files to display.

        Args:
            files: List of filenames to display

        """
        self._current_files = files.copy()
        self._apply_filter_and_sort()
        self.logger.debug("Set %d files in list", len(files))

    def add_files(self, files: list[str]) -> None:
        """Add files to the current list.

        Args:
            files: List of filenames to add

        """
        self._current_files.extend(files)
        self._apply_filter_and_sort()
        self.logger.debug("Added %d files to list", len(files))

    def clear_files(self) -> None:
        """Clear all files from the list."""
        self._current_files.clear()
        self._filtered_files.clear()
        self.list_widget.clear()
        self.logger.debug("Cleared file list")

    def get_selected_file(self) -> str | None:
        """Get the currently selected filename.

        Returns:
            Selected filename or None if no selection

        """
        current_item = self.list_widget.currentItem()
        return current_item.text() if current_item else None

    def select_file(self, filename: str) -> bool:
        """Select a specific file in the list.

        Args:
            filename: Name of file to select

        Returns:
            True if file was found and selected

        """
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item and item.text() == filename:
                self.list_widget.setCurrentItem(item)
                self.logger.debug("Selected file: %s", filename)
                return True

        self.logger.debug("File not found for selection: %s", filename)
        return False

    def get_file_count(self) -> int:
        """Get the number of files currently displayed."""
        return len(self._filtered_files)

    def get_total_file_count(self) -> int:
        """Get the total number of files (before filtering)."""
        return len(self._current_files)

    def _apply_filter_and_sort(self) -> None:
        """Apply current filter and sort settings."""
        # Apply filter
        filter_text = self.filter_edit.text().lower()
        if filter_text:
            self._filtered_files = [f for f in self._current_files if filter_text in f.lower()]
        else:
            self._filtered_files = self._current_files.copy()

        # Apply sort
        sort_option = self.sort_combo.currentText()
        if sort_option == "Name (A-Z)":
            self._filtered_files.sort()
        elif sort_option == "Name (Z-A)":
            self._filtered_files.sort(reverse=True)
        elif sort_option == "Type":
            self._filtered_files.sort(key=lambda f: (Path(f).suffix, f))
        # Size and Date Modified would need additional file info

        # Update the display
        self._update_list_display()

    def _update_list_display(self) -> None:
        """Update the list widget display."""
        self.list_widget.clear()

        for filename in self._filtered_files:
            item = Qw.QListWidgetItem(filename)

            # Add icon based on file type
            icon = self._get_file_icon(filename)
            if icon:
                item.setIcon(icon)

            self.list_widget.addItem(item)

    def _get_file_icon(self, filename: str) -> QtGui.QIcon | None:
        """Get an appropriate icon for a file.

        Args:
            filename: Name of the file

        Returns:
            QIcon or None

        """
        # You could enhance this with your file categorization system
        suffix = Path(filename).suffix.lower()

        # Use standard style icons
        style = self.style()

        if suffix in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}:
            return style.standardIcon(Qw.QStyle.StandardPixmap.SP_FileIcon)
        if suffix in {".txt", ".json", ".yaml", ".xml"}:
            return style.standardIcon(Qw.QStyle.StandardPixmap.SP_FileDialogDetailedView)
        if suffix in {".ckpt", ".safetensors", ".pt", ".pth"}:
            return style.standardIcon(Qw.QStyle.StandardPixmap.SP_ComputerIcon)
        return style.standardIcon(Qw.QStyle.StandardPixmap.SP_FileIcon)

    def _on_selection_changed(
        self,
        current: Qw.QListWidgetItem,
        previous: Qw.QListWidgetItem,
    ) -> None:
        """Handle selection change.

        Args:
            current: Currently selected item
            previous: Previously selected item (required by Qt but unused)

        """
        if current:
            filename = current.text()
            self.file_selected.emit(filename)
            self.logger.debug("File selection changed to: %s", filename)

    def _on_sort_changed(self, sort_option: str) -> None:
        """Handle sort option change."""
        self._apply_filter_and_sort()
        self.sort_changed.emit(sort_option)
        self.logger.debug("Sort changed to: %s", sort_option)

    def _on_filter_changed(self, filter_text: str) -> None:
        """Handle filter text change."""
        self._apply_filter_and_sort()
        self.logger.debug("Filter changed to: '%s'", filter_text)

    def _clear_filter(self) -> None:
        """Clear the filter."""
        self.filter_edit.clear()


# ============================================================================
# FOLDER CONTROL WIDGET
# ============================================================================


class FolderControlWidget(Qw.QWidget):
    """Widget for folder path display and navigation controls.

    This shows the current folder and provides controls for changing folders.
    Like your minimap showing your current location! 🗺️
    """

    # Signals
    open_folder_requested = QtCore.pyqtSignal()
    folder_path_changed = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        """Initialize the folder control widget."""
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.FolderControlWidget")

        self._current_folder = ""

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = Qw.QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Folder path display
        self.path_display = Qw.QLineEdit()
        self.path_display.setPlaceholderText("No folder selected...")
        self.path_display.setReadOnly(True)
        layout.addWidget(self.path_display, 1)

        # Open folder button
        self.open_button = Qw.QPushButton("Open Folder")
        self.open_button.setMinimumWidth(100)
        layout.addWidget(self.open_button)

        # Up directory button
        self.up_button = Qw.QPushButton("↑")
        self.up_button.setMaximumWidth(30)
        self.up_button.setToolTip("Go to parent directory")
        self.up_button.setEnabled(False)
        layout.addWidget(self.up_button)

        # Refresh button
        self.refresh_button = Qw.QPushButton("⟳")
        self.refresh_button.setMaximumWidth(30)
        self.refresh_button.setToolTip("Refresh current folder")
        self.refresh_button.setEnabled(False)
        layout.addWidget(self.refresh_button)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.open_button.clicked.connect(self.open_folder_requested.emit)
        self.up_button.clicked.connect(self._go_up_directory)
        self.refresh_button.clicked.connect(self._refresh_folder)

    def set_folder_path(self, folder_path: str) -> None:
        """Set the current folder path.

        Args:
            folder_path: Path to the current folder

        """
        self._current_folder = folder_path
        self.path_display.setText(folder_path)

        # Enable/disable navigation buttons
        can_go_up = bool(folder_path and Path(folder_path).parent != Path(folder_path))
        self.up_button.setEnabled(can_go_up)
        self.refresh_button.setEnabled(bool(folder_path))

        self.logger.debug("Folder path set to: %s", folder_path)

    def get_folder_path(self) -> str:
        """Get the current folder path."""
        return self._current_folder

    def _go_up_directory(self) -> None:
        """Navigate to the parent directory."""
        if not self._current_folder:
            return

        parent_path = str(Path(self._current_folder).parent)
        if parent_path != self._current_folder:  # Prevent infinite loop at root
            self.folder_path_changed.emit(parent_path)
            self.logger.debug("Navigating up to: %s", parent_path)

    def _refresh_folder(self) -> None:
        """Refresh the current folder."""
        if self._current_folder:
            self.folder_path_changed.emit(self._current_folder)
            self.logger.debug("Refreshing folder: %s", self._current_folder)


# ============================================================================
# IMAGE PREVIEW WIDGET
# ============================================================================


class ImagePreviewWidget(Qw.QLabel):
    """Widget for displaying image previews with proper scaling.

    This shows images with aspect ratio preservation and smooth scaling.
    Like your glamour preview in FFXIV! ✨🖼️
    """

    def __init__(self, parent=None):
        """Initialize the image preview widget."""
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.ImagePreviewWidget")

        self._original_pixmap: QtGui.QPixmap | None = None
        self._placeholder_text = "No image selected"

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setFrameShape(Qw.QFrame.Shape.StyledPanel)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setScaledContents(False)  # We'll handle scaling manually

        # Set placeholder
        self.set_placeholder_text(self._placeholder_text)

    def set_image(self, image_path: str) -> bool:
        """Set the image to display.

        Args:
            image_path: Path to the image file

        Returns:
            True if image was loaded successfully

        """
        try:
            # Create memory-efficient thumbnail instead of loading full image
            max_size = 2048  # Reasonable max for preview widget
            pixmap = self._create_safe_thumbnail(image_path, max_size)

            if pixmap.isNull():
                self.logger.warning("Failed to load image: %s", image_path)
                self.set_error_text("Could not load image")
                return False

            # Store the already-scaled pixmap instead of full resolution
            self._original_pixmap = pixmap
            self._update_scaled_pixmap()

            self.logger.debug(
                "Loaded image: %s (%sx%s)",
                Path(image_path).name,
                pixmap.width(),
                pixmap.height(),
            )
            return True

        except Exception as e:
            self.logger.error("Error loading image '%s': %s", image_path, e)
            self.set_error_text(f"Error loading image: {e!s}")
            return False

    def _create_safe_thumbnail(self, image_path: str, max_size: int) -> QtGui.QPixmap:
        """Create a memory-efficient thumbnail avoiding Lanczos artifacts.

        Args:
            image_path: Path to the source image
            max_size: Maximum dimension for the thumbnail

        Returns:
            QPixmap containing the thumbnail, or null pixmap on error

        """
        try:
            # Use 'with' to ensure immediate cleanup of full-resolution image
            with Image.open(image_path) as img:
                # Fix rotation issues BEFORE doing anything else
                img = ImageOps.exif_transpose(img)

                # Use thumbnail() instead of resize() - it's memory efficient and safer
                # thumbnail() modifies in-place and uses a good resampling filter
                img.thumbnail((max_size, max_size), Image.Resampling.BILINEAR)  # Safer than LANCZOS

                # Convert to Qt format with proper color channel handling
                return self._pil_to_qpixmap(img)

        except Exception as e:
            self.logger.error("Error creating thumbnail for '%s': %s", image_path, e)
            # Return empty pixmap on error
            return QtGui.QPixmap()

    def _pil_to_qpixmap(self, pil_image: Image.Image) -> QtGui.QPixmap:
        """Convert PIL Image to QPixmap with proper color handling.

        Args:
            pil_image: PIL Image to convert

        Returns:
            QPixmap or null pixmap on error

        """
        try:
            # Convert to RGB if needed (handles various modes safely)
            if pil_image.mode not in ("RGB", "RGBA"):
                pil_image = pil_image.convert("RGB")

            # Get image data
            width, height = pil_image.size

            if pil_image.mode == "RGBA":
                # Handle transparency
                image_data = pil_image.tobytes("raw", "RGBA")
                qimage = QtGui.QImage(image_data, width, height, QtGui.QImage.Format.Format_RGBA8888)
            else:
                # RGB mode
                image_data = pil_image.tobytes("raw", "RGB")
                qimage = QtGui.QImage(image_data, width, height, QtGui.QImage.Format.Format_RGB888)

            return QtGui.QPixmap.fromImage(qimage)

        except Exception as e:
            self.logger.error("Error converting PIL to QPixmap: %s", e)
            return QtGui.QPixmap()

    def set_pixmap_direct(self, pixmap: QtGui.QPixmap) -> None:
        """Set a pixmap directly.

        Args:
            pixmap: QPixmap to display

        """
        if pixmap and not pixmap.isNull():
            self._original_pixmap = pixmap
            self._update_scaled_pixmap()
        else:
            self.clear_image()

    def clear_image(self) -> None:
        """Clear the current image."""
        self._original_pixmap = None
        self.clear()
        self.set_placeholder_text(self._placeholder_text)
        self.logger.debug("Image cleared")

    def set_placeholder_text(self, text: str) -> None:
        """Set placeholder text to display when no image is loaded.

        Args:
            text: Placeholder text

        """
        self._placeholder_text = text
        if not self._original_pixmap:
            self.setText(text)
            self.setStyleSheet("color: gray; font-style: italic;")

    def set_error_text(self, text: str) -> None:
        """Set error text to display when image loading fails.

        Args:
            text: Error text

        """
        self._original_pixmap = None
        self.clear()
        self.setText(text)
        self.setStyleSheet("color: red; font-style: italic;")

    def get_image_size(self) -> tuple[int, int] | None:
        """Get the original image size.

        Returns:
            Tuple of (width, height) or None if no image

        """
        if self._original_pixmap:
            return (self._original_pixmap.width(), self._original_pixmap.height())
        return None

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Handle widget resize by updating scaled pixmap."""
        super().resizeEvent(event)
        if self._original_pixmap:
            self._update_scaled_pixmap()

    def _update_scaled_pixmap(self) -> None:
        """Update the displayed pixmap with proper scaling."""
        if not self._original_pixmap:
            return

        # Scale pixmap to fit widget while maintaining aspect ratio
        scaled_pixmap = self._original_pixmap.scaled(
            self.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )

        super().setPixmap(scaled_pixmap)
        self.setStyleSheet("")  # Clear any error/placeholder styling


# ============================================================================
# STATUS INFO WIDGET
# ============================================================================


class StatusInfoWidget(Qw.QWidget):
    """Widget for displaying status information and file counts.

    This shows information about the current folder and files.
    Like your party status display! 👥📊
    """

    def __init__(self, parent=None):
        """Initialize the status info widget."""
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.StatusInfoWidget")

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = Qw.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Main status label
        self.status_label = Qw.QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)

        # File counts
        counts_layout = Qw.QGridLayout()

        # Images
        counts_layout.addWidget(Qw.QLabel("Images:"), 0, 0)
        self.images_label = Qw.QLabel("0")
        counts_layout.addWidget(self.images_label, 0, 1)

        # Texts
        counts_layout.addWidget(Qw.QLabel("Texts:"), 1, 0)
        self.texts_label = Qw.QLabel("0")
        counts_layout.addWidget(self.texts_label, 1, 1)

        # Models
        counts_layout.addWidget(Qw.QLabel("Models:"), 2, 0)
        self.models_label = Qw.QLabel("0")
        counts_layout.addWidget(self.models_label, 2, 1)

        # Total
        counts_layout.addWidget(Qw.QLabel("Total:"), 3, 0)
        self.total_label = Qw.QLabel("0")
        self.total_label.setStyleSheet("font-weight: bold;")
        counts_layout.addWidget(self.total_label, 3, 1)

        layout.addLayout(counts_layout)
        layout.addStretch()

    def set_status_text(self, text: str) -> None:
        """Set the main status text.

        Args:
            text: Status text to display

        """
        self.status_label.setText(text)
        self.logger.debug("Status text set to: %s", text)

    def set_file_counts(self, images: int = 0, texts: int = 0, models: int = 0) -> None:
        """Set the file count displays.

        Args:
            images: Number of image files
            texts: Number of text files
            models: Number of model files

        """
        total = images + texts + models

        self.images_label.setText(str(images))
        self.texts_label.setText(str(texts))
        self.models_label.setText(str(models))
        self.total_label.setText(str(total))

        self.logger.debug(
            "File counts updated: %si, %st, %sm = %s total",
            images,
            texts,
            models,
            total,
        )

    def clear_counts(self) -> None:
        """Clear all file counts."""
        self.set_file_counts(0, 0, 0)


# ============================================================================
# LEFT PANEL WIDGET (COMPOSITE)
# ============================================================================


class LeftPanelWidget(Qw.QWidget):
    """Composite widget for the left panel containing folder controls and file list.

    This combines multiple widgets into a cohesive left panel interface.
    Like your main UI panel that contains multiple components! 🎮
    """

    # Signals
    open_folder_requested = QtCore.pyqtSignal()
    folder_path_changed = QtCore.pyqtSignal(str)
    file_selected = QtCore.pyqtSignal(str)
    sort_changed = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        """Initialize the left panel widget."""
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.LeftPanelWidget")

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = Qw.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Folder controls
        self.folder_control = FolderControlWidget()
        layout.addWidget(self.folder_control)

        # File list
        self.file_list = FileListWidget()
        layout.addWidget(self.file_list, 1)  # Give it most of the space

        # Status info
        self.status_info = StatusInfoWidget()
        layout.addWidget(self.status_info)

    def _connect_signals(self) -> None:
        """Connect internal widget signals to external signals."""
        self.folder_control.open_folder_requested.connect(self.open_folder_requested.emit)
        self.folder_control.folder_path_changed.connect(self.folder_path_changed.emit)
        self.file_list.file_selected.connect(self.file_selected.emit)
        self.file_list.sort_changed.connect(self.sort_changed.emit)

    def set_folder_path(self, folder_path: str) -> None:
        """Set the current folder path."""
        self.folder_control.set_folder_path(folder_path)
        folder_name = Path(folder_path).name if folder_path else "No folder"
        self.status_info.set_status_text(f"Folder: {folder_name}")

    def set_files(self, images: list[str], texts: list[str], models: list[str]) -> None:
        """Set the files to display."""
        all_files = images + texts + models
        self.file_list.set_files(all_files)
        self.status_info.set_file_counts(len(images), len(texts), len(models))

    def select_file(self, filename: str) -> bool:
        """Select a specific file."""
        return self.file_list.select_file(filename)

    def get_selected_file(self) -> str | None:
        """Get the currently selected file."""
        return self.file_list.get_selected_file()

    def clear_files(self) -> None:
        """Clear all files."""
        self.file_list.clear_files()
        self.status_info.clear_counts()

    def set_message_text(self, text: str) -> None:
        """Set a message in the status area."""
        self.status_info.set_status_text(text)


# ============================================================================
# TESTING UTILITIES
# ============================================================================


def test_ui_widgets():
    """Test the UI widgets."""
    app = QApplication(sys.argv)

    # Create main window for testing
    window = QMainWindow()
    window.setWindowTitle("UI Widgets Test")
    window.resize(800, 600)

    # Create test layout
    splitter = QSplitter()
    window.setCentralWidget(splitter)

    # Left panel
    left_panel = LeftPanelWidget()
    splitter.addWidget(left_panel)

    # Right panel with image preview
    image_preview = ImagePreviewWidget()
    splitter.addWidget(image_preview)

    # Set up test data
    test_images = ["test1.jpg", "test2.png", "photo.gif"]
    test_texts = ["readme.txt", "config.json", "data.yaml"]
    test_models = ["model.ckpt", "checkpoint.safetensors"]

    left_panel.set_folder_path("/test/folder")
    left_panel.set_files(test_images, test_texts, test_models)

    # Connect signals for testing
    def on_file_selected(filename):
        print(f"File selected: {filename}")
        # Set a placeholder image
        image_preview.set_placeholder_text(f"Preview of {filename}")

    def on_folder_requested():
        print("Open folder requested")

    def on_sort_changed(sort_option):
        print(f"Sort changed to: {sort_option}")

    left_panel.file_selected.connect(on_file_selected)
    left_panel.open_folder_requested.connect(on_folder_requested)
    left_panel.sort_changed.connect(on_sort_changed)

    # Show the window
    window.show()

    print("UI Widgets test window created!")
    print("- Try selecting files in the list")
    print("- Try filtering with the search box")
    print("- Try changing sort options")
    print("- Try the folder navigation buttons")

    # Auto-close after 30 seconds for automated testing
    QtCore.QTimer.singleShot(30000, app.quit)

    app.exec()


if __name__ == "__main__":
    # Run tests if module is executed directly
    test_ui_widgets()
