# dataset_tools/ui/components.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Enhanced UI components for Dataset Tools.

This module extends the base widgets with additional functionality
and provides improved versions of core UI components.
"""

from PyQt6 import QtCore, QtGui
from PyQt6 import QtWidgets as Qw
from PyQt6.QtCore import QSize

from ..logger import info_monitor as nfo
from .icon_manager import get_icon_manager


class EnhancedLeftPanelWidget(Qw.QWidget):
    """Enhanced version of the left panel widget with improved functionality.

    This extends the basic LeftPanelWidget with additional features like
    better status display, improved file count management, and enhanced
    user feedback.
    """

    # Signals
    open_folder_requested = QtCore.pyqtSignal()
    sort_files_requested = QtCore.pyqtSignal()
    list_item_selected = QtCore.pyqtSignal(object, object)  # current, previous

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the UI layout and components."""
        layout = Qw.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        # Current folder display
        self.current_folder_label = Qw.QLabel("Current Folder: None")
        self.current_folder_label.setWordWrap(True)
        # self.current_folder_label.setStyleSheet("font-weight: bold; color: #666;")
        layout.addWidget(self.current_folder_label)

        # Action buttons
        self._setup_action_buttons(layout)

        # Status/message display
        self.message_label = Qw.QLabel("Select a folder to view its contents.")
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)

        # File list
        self.files_list_widget = Qw.QListWidget()
        self.files_list_widget.setSelectionMode(Qw.QAbstractItemView.SelectionMode.SingleSelection)
        self.files_list_widget.setSizePolicy(Qw.QSizePolicy.Policy.Preferred, Qw.QSizePolicy.Policy.Expanding)

        # Enable word wrap for long filenames
        self.files_list_widget.setWordWrap(True)
        self.files_list_widget.setResizeMode(Qw.QListView.ResizeMode.Adjust)
        # Force text wrapping behavior
        self.files_list_widget.setTextElideMode(QtCore.Qt.TextElideMode.ElideNone)

        # Set uniform item sizes and spacing
        self.files_list_widget.setUniformItemSizes(False)  # Allow variable heights for wrapped text
        self.files_list_widget.setSpacing(2)  # Add some space between items

        # Enhanced tooltip for file list
        self.files_list_widget.setToolTip(
            "<b>File List</b><br/>"
            "Click on any file to view its metadata and preview.<br/>"
            "Long filenames will wrap to multiple lines for better readability.<br/>"
            "<i>Use arrow keys to navigate between files</i>"
        )

        layout.addWidget(self.files_list_widget, 1)

    def _setup_action_buttons(self, layout: Qw.QVBoxLayout) -> None:
        """Setup the action button row."""
        button_layout = Qw.QHBoxLayout()
        button_layout.setSpacing(5)

        # Get icon manager for themed icons
        icon_manager = get_icon_manager()

        self.open_folder_button = Qw.QPushButton("Open Folder")
        # Add Font Awesome icon to button
        icon_manager.add_icon_to_button(self.open_folder_button, "folder-open-solid", "primary", QSize(16, 16))
        self.open_folder_button.setToolTip(
            "<b>Open Folder</b><br/>"
            "Select a folder to load image files from.<br/>"
            "Supported formats: JPG, PNG, WebP, and more.<br/>"
            "<i>Shortcut: Ctrl+O</i>"
        )
        button_layout.addWidget(self.open_folder_button)

        self.sort_button = Qw.QPushButton("Sort Files")
        # Add Font Awesome icon to button
        icon_manager.add_icon_to_button(self.sort_button, "arrow-up-a-z-solid", "primary", QSize(16, 16))
        self.sort_button.setToolTip(
            "<b>Sort Files</b><br/>"
            "Sort the current file list alphabetically.<br/>"
            "Files will be arranged in ascending order by name.<br/>"
            "<i>Useful for organizing large collections</i>"
        )
        button_layout.addWidget(self.sort_button)

        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        """Connect internal signals to handlers."""
        self.open_folder_button.clicked.connect(self.open_folder_requested.emit)
        self.sort_button.clicked.connect(self.sort_files_requested.emit)
        self.files_list_widget.currentItemChanged.connect(self.list_item_selected.emit)

    # ========================================================================
    # PUBLIC INTERFACE METHODS
    # ========================================================================

    def set_current_folder_text(self, text: str) -> None:
        """Update the current folder display text."""
        self.current_folder_label.setText(text)

    def set_message_text(self, text: str) -> None:
        """Update the status message text."""
        self.message_label.setText(text)

    def clear_file_list_display(self) -> None:
        """Clear all items from the file list."""
        self.files_list_widget.clear()

    def add_items_to_file_list(self, items: list[str]) -> None:
        """Add multiple items to the file list."""
        self.files_list_widget.addItems(items)
        nfo("[LeftPanel] Added %d items to file list", len(items))

    def set_current_file_by_name(self, file_name: str) -> bool:
        """Select a file in the list by name.

        Args:
            file_name: Name of the file to select

        Returns:
            True if file was found and selected, False otherwise

        """
        found_items = self.files_list_widget.findItems(file_name, QtCore.Qt.MatchFlag.MatchExactly)
        if found_items:
            self.files_list_widget.setCurrentItem(found_items[0])
            return True
        return False

    def set_current_file_by_row(self, row: int) -> None:
        """Select a file by row index."""
        if 0 <= row < self.files_list_widget.count():
            self.files_list_widget.setCurrentRow(row)

    def get_files_list_widget(self) -> Qw.QListWidget:
        """Get the underlying QListWidget for advanced operations."""
        return self.files_list_widget

    def set_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable the action buttons."""
        self.open_folder_button.setEnabled(enabled)
        self.sort_button.setEnabled(enabled)
        self.files_list_widget.setEnabled(enabled)

    def get_file_count(self) -> int:
        """Get the current number of files in the list."""
        return self.files_list_widget.count()

    def get_selected_file_name(self) -> str:
        """Get the currently selected file name, or empty string if none."""
        current_item = self.files_list_widget.currentItem()
        return current_item.text() if current_item else ""


class EnhancedImageLabel(Qw.QLabel):
    """Enhanced image display widget with better scaling and state management.

    This provides improved image display with automatic scaling, aspect ratio
    preservation, and better handling of loading states and errors.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_widget()
        self._original_pixmap = QtGui.QPixmap()

    def _setup_widget(self) -> None:
        """Setup the widget appearance and behavior."""
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setSizePolicy(Qw.QSizePolicy.Policy.Ignored, Qw.QSizePolicy.Policy.Ignored)
        self.setWordWrap(True)
        self.setFrameShape(Qw.QFrame.Shape.StyledPanel)
        # self.setStyleSheet(
        #     "QLabel {"
        #     "background-color: #f0f0f0;"
        #     "border: 2px dashed #ccc;"
        #     "color: #666;"
        #     "}"
        # )
        self._show_default_text()

    def _show_default_text(self) -> None:
        """Show the default placeholder text."""
        self.setText("Image Preview Area\n\n(Drag & Drop Image Here)")

    def setPixmap(self, pixmap: QtGui.QPixmap | None) -> None:
        """Set the pixmap to display, with automatic scaling.

        Args:
        pixmap: QPixmap to display, or None to clear

        """
        if pixmap is None or pixmap.isNull():
            self._original_pixmap = QtGui.QPixmap()
            super().clear()
            self._show_no_image_text()
        else:
            self._original_pixmap = pixmap
            self._update_scaled_display()

    def clear(self) -> None:
        """Clear the image and show default text."""
        super().clear()
        self._original_pixmap = QtGui.QPixmap()
        self._show_default_text()

    def _show_no_image_text(self) -> None:
        """Show text when no image can be displayed."""
        self.setText("No preview available\nor image failed to load")

    def _update_scaled_display(self) -> None:
        """Update the displayed image with proper scaling."""
        if self._original_pixmap.isNull() or self.width() <= 10 or self.height() <= 10:
            return

        # Clear text and show scaled image
        self.setText("")
        scaled_pixmap = self._original_pixmap.scaled(
            self.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        super().setPixmap(scaled_pixmap)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Handle resize events by updating the scaled image."""
        self._update_scaled_display()
        super().resizeEvent(event)

    def has_image(self) -> bool:
        """Check if an image is currently displayed."""
        return not self._original_pixmap.isNull()

    def get_original_size(self) -> tuple[int, int]:
        """Get the original image size."""
        if self.has_image():
            return self._original_pixmap.width(), self._original_pixmap.height()
        return 0, 0

    def save_image(self, file_path: str) -> bool:
        """Save the current image to a file.

        Args:
            file_path: Path where to save the image

        Returns:
            True if save was successful, False otherwise

        """
        if self.has_image():
            return self._original_pixmap.save(file_path)
        return False


# ============================================================================
# BACKWARDS COMPATIBILITY ALIASES
# ============================================================================

# For existing code that imports from widgets.py
LeftPanelWidget = EnhancedLeftPanelWidget
ImageLabel = EnhancedImageLabel
