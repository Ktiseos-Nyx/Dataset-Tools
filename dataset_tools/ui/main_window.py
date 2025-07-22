# dataset_tools/ui/main_window.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Main application window for Dataset Tools.

This module contains the core MainWindow class that orchestrates the entire
application interface, handling file management, metadata display, and user interactions.
"""

import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps
from PyQt6 import QtCore, QtGui
from PyQt6 import QtWidgets as Qw
from PyQt6.QtCore import QObject, QSettings, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

# from PyQt6.QtWidgets import QApplication
from ..correct_types import EmptyField  # pylint: disable=relative-beyond-top-level
from ..correct_types import ExtensionType as Ext  # pylint: disable=relative-beyond-top-level
from ..logger import debug_monitor  # pylint: disable=relative-beyond-top-level
from ..logger import info_monitor as nfo  # pylint: disable=relative-beyond-top-level
from ..metadata_parser import (
    parse_metadata,
)  # pylint: disable=relative-beyond-top-level
from ..widgets import (
    FileLoader,  # pylint: disable=relative-beyond-top-level
)
from .dialogs import SettingsDialog
from .enhanced_theme_manager import get_enhanced_theme_manager  # pylint: disable=relative-beyond-top-level
from .font_manager import (
    apply_fonts_to_app,  # pylint: disable=relative-beyond-top-level
    get_font_manager,  # pylint: disable=relative-beyond-top-level
)
from .managers import (
    LayoutManager,  # pylint: disable=relative-beyond-top-level
    MenuManager,  # pylint: disable=relative-beyond-top-level
    MetadataDisplayManager,  # pylint: disable=relative-beyond-top-level
    ThemeManager,  # pylint: disable=relative-beyond-top-level
)
from .widgets import FileLoadResult

# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_WINDOW_SIZE = (1024, 768)
STATUS_MESSAGE_TIMEOUT = 3000
DATETIME_UPDATE_INTERVAL = 1000

ORGANIZATION_NAME = "EarthAndDuskMedia"
APPLICATION_NAME = "DatasetViewer"


# ============================================================================
# THREADED IMAGE LOADER
# ============================================================================


class ImageLoaderWorker(QObject):
    """Worker class for loading images in background thread."""

    # Signals for communication with main thread
    image_loaded = pyqtSignal(str, QtGui.QPixmap)  # file_path, pixmap
    loading_failed = pyqtSignal(str, str)  # file_path, error_message
    loading_started = pyqtSignal(str)  # file_path
    load_requested = pyqtSignal(str, int)  # file_path, max_size - for triggering work

    def __init__(self):
        super().__init__()
        self._current_task = None
        # Connect the signal to the slot
        self.load_requested.connect(self.load_image_thumbnail)

    def load_image_thumbnail(self, image_path: str, max_size: int = 1024):
        """Load and process image thumbnail in background thread.

        Args:
            image_path: Path to the image file
            max_size: Maximum dimension for the thumbnail

        """
        self._current_task = image_path
        self.loading_started.emit(image_path)

        try:
            # Create memory-efficient thumbnail using our safe method
            pixmap = self._create_safe_thumbnail(image_path, max_size)

            # Check if task was cancelled (new file selected)
            if self._current_task != image_path:
                return

            if pixmap.isNull():
                self.loading_failed.emit(image_path, "Failed to create thumbnail")
            else:
                self.image_loaded.emit(image_path, pixmap)

        except Exception as e:
            if self._current_task == image_path:  # Only emit if not cancelled
                self.loading_failed.emit(image_path, str(e))

    def cancel_current_task(self):
        """Cancel the current loading task."""
        self._current_task = None

    def _create_safe_thumbnail(self, image_path: str, max_size: int) -> QtGui.QPixmap:
        """Create a memory-efficient thumbnail avoiding Lanczos artifacts."""
        try:
            with Image.open(image_path) as img:
                img = ImageOps.exif_transpose(img)
                img.thumbnail((max_size, max_size), Image.Resampling.BILINEAR)
                return self._pil_to_qpixmap(img)
        except Exception:
            return QtGui.QPixmap()

    def _pil_to_qpixmap(self, pil_image: Image.Image) -> QtGui.QPixmap:
        """Convert PIL Image to QPixmap with proper color handling."""
        try:
            # Ensure we have RGB format for consistency
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            width, height = pil_image.size

            # Convert to bytes with proper format for Qt
            image_data = pil_image.tobytes("raw", "RGB")
            bytes_per_line = width * 3  # 3 bytes per pixel for RGB

            # Create QImage with proper byte alignment
            qimage = QtGui.QImage(
                image_data,
                width,
                height,
                bytes_per_line,
                QtGui.QImage.Format.Format_RGB888,
            )

            return QtGui.QPixmap.fromImage(qimage)

        except Exception:
            return QtGui.QPixmap()


# ============================================================================
# MAIN WINDOW CLASS
# ============================================================================


class MainWindow(Qw.QMainWindow):
    """Main application window for Dataset Tools.

    This class serves as the central coordinator for the entire application,
    managing UI components, file operations, metadata display, and user interactions.
    """

    def __init__(self):
        """Initialize the main window with all components."""
        super().__init__()

        # Initialize core attributes
        self._initialize_core_attributes()

        # Setup managers
        self._initialize_managers()

        # Setup UI components
        self._setup_window_properties()
        self._setup_status_bar()
        self._setup_datetime_timer()

        # Initialize UI
        self._initialize_ui()

        # Restore application state
        self._restore_application_state()

    def _initialize_core_attributes(self) -> None:
        """Initialize core instance attributes."""
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        self.setAcceptDrops(True)

        # File management
        self.file_loader: FileLoader | None = None  # Ensure file_loader is always defined
        self.current_files_in_list: list[str] = []
        self.current_folder: str = ""

        # UI state
        self.main_status_bar = self.statusBar()
        self.datetime_label = Qw.QLabel()
        self.status_timer: QTimer | None = None
        self.progress_bar = Qw.QProgressBar()
        self.progress_bar.setVisible(False)  # Hidden by default

        # Threaded image loading
        self.image_loader_thread: QThread | None = None
        self.image_loader_worker: ImageLoaderWorker | None = None
        self._setup_image_loading_thread()

    def _initialize_managers(self) -> None:
        """Initialize UI and functionality managers."""
        # Use enhanced theme manager for multiple theme systems
        self.enhanced_theme_manager = get_enhanced_theme_manager(self, self.settings)

        # Keep original theme manager for backward compatibility if needed
        self.theme_manager = ThemeManager(self, self.settings)

        self.menu_manager = MenuManager(self)
        self.layout_manager = LayoutManager(self, self.settings)
        self.metadata_display = MetadataDisplayManager(self)

    def _setup_window_properties(self) -> None:
        """Configure basic window properties."""
        self.setWindowTitle("Dataset Viewer")
        self.setMinimumSize(*DEFAULT_WINDOW_SIZE)

    def _setup_status_bar(self) -> None:
        """Configure the status bar."""
        self.main_status_bar.showMessage("Ready", STATUS_MESSAGE_TIMEOUT)

        # Add progress bar (initially hidden)
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setTextVisible(False)
        self.main_status_bar.addPermanentWidget(self.progress_bar)

        # Add datetime label
        self.main_status_bar.addPermanentWidget(self.datetime_label)

    def _setup_datetime_timer(self) -> None:
        """Setup timer for datetime display in status bar."""
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_datetime_status)
        self.status_timer.start(DATETIME_UPDATE_INTERVAL)
        self._update_datetime_status()

    def _initialize_ui(self) -> None:
        """Initialize the complete user interface."""
        # Setup menus first
        self.menu_manager.setup_menus()

        # Apply saved theme using enhanced theme manager
        self.enhanced_theme_manager.apply_saved_theme()

        # Setup layout (creates all widgets including text boxes)
        self.layout_manager.setup_layout()

        # Apply optimal fonts AFTER layout is created
        apply_fonts_to_app()
        nfo("Applied optimal fonts to application")

        # Connect signals
        self._connect_ui_signals()

    def _connect_ui_signals(self) -> None:
        """Connect UI component signals to handlers."""
        if hasattr(self, "left_panel"):
            self.left_panel.open_folder_requested.connect(self.open_folder)
            self.left_panel.sort_files_requested.connect(self.sort_files_list)
            self.left_panel.list_item_selected.connect(self.on_file_selected)

    def _restore_application_state(self) -> None:
        """Restore window geometry and load initial folder."""
        self.theme_manager.restore_window_geometry()
        self._load_initial_folder()

    def _load_initial_folder(self) -> None:
        """Load the last used folder or show empty state."""
        initial_folder = self.settings.value("lastFolderPath", os.getcwd())
        self.clear_file_list()

        if initial_folder and Path(initial_folder).is_dir():
            self.load_files(initial_folder)
        else:
            self._show_empty_folder_state()

    def _show_empty_folder_state(self) -> None:
        """Show UI state when no folder is loaded."""
        if hasattr(self, "left_panel"):
            self.left_panel.set_current_folder_text("Current Folder: None")
            self.left_panel.set_message_text("Please select folder.")
        self.clear_selection()

    def _setup_image_loading_thread(self) -> None:
        """Initialize the background image loading thread."""
        try:
            # Create thread and worker
            self.image_loader_thread = QThread()
            self.image_loader_worker = ImageLoaderWorker()

            # Move worker to thread
            self.image_loader_worker.moveToThread(self.image_loader_thread)

            # Connect signals
            self.image_loader_worker.image_loaded.connect(self._on_image_loaded)
            self.image_loader_worker.loading_failed.connect(self._on_image_loading_failed)
            self.image_loader_worker.loading_started.connect(self._on_image_loading_started)

            # Start the thread
            self.image_loader_thread.start()

            nfo("[UI] Image loading thread initialized successfully")

        except Exception as e:
            nfo("[UI] Failed to initialize image loading thread: %s", e)
            # Fallback to synchronous loading
            self.image_loader_thread = None
            self.image_loader_worker = None

    def _on_image_loading_started(self, file_path: str) -> None:
        """Handle when image loading starts."""
        # Show loading indicator in status bar
        self.show_status_message(f"Loading image: {Path(file_path).name}...")

        # Show indeterminate progress bar
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setVisible(True)

    def _on_image_loaded(self, file_path: str, pixmap: QtGui.QPixmap) -> None:
        """Handle when image is successfully loaded in background thread."""
        try:
            # Hide progress bar
            self.progress_bar.setVisible(False)

            # Update the image preview with the loaded pixmap
            if hasattr(self, "image_preview") and self.image_preview:
                self.image_preview.setPixmap(pixmap)

            # Update status
            self.show_status_message(f"Image loaded: {pixmap.width()}x{pixmap.height()}")
            nfo("[UI] Image loaded successfully: %dx%d", pixmap.width(), pixmap.height())

        except Exception as e:
            nfo("[UI] Error setting loaded image: %s", e)
            # Hide progress bar on error too
            self.progress_bar.setVisible(False)

    def _on_image_loading_failed(self, file_path: str, error_message: str) -> None:
        """Handle when image loading fails."""
        # Hide progress bar
        self.progress_bar.setVisible(False)

        nfo("[UI] Failed to load image '%s': %s", file_path, error_message)
        self.show_status_message(f"Failed to load image: {error_message}")

    # ========================================================================
    # DATETIME AND STATUS MANAGEMENT
    # ========================================================================

    def _update_datetime_status(self) -> None:
        """Update the datetime display in the status bar."""
        current_time = QtCore.QDateTime.currentDateTime()
        time_string = current_time.toString(QtCore.Qt.DateFormat.RFC2822Date)
        self.datetime_label.setText(time_string)

    def show_status_message(self, message: str, timeout: int = STATUS_MESSAGE_TIMEOUT) -> None:
        """Show a message in the status bar."""
        self.main_status_bar.showMessage(message, timeout)
        nfo("[UI] Status: %s", message)

    # ========================================================================
    # FILE MANAGEMENT
    # ========================================================================

    @debug_monitor
    def open_folder(self) -> None:
        """Open folder selection dialog and load files."""
        nfo("[UI] 'Open Folder' action triggered.")

        start_dir = self._get_start_directory()
        folder_path = Qw.QFileDialog.getExistingDirectory(self, "Select Folder to Load", start_dir)

        if folder_path:
            nfo("[UI] Folder selected via dialog: %s", folder_path)
            self.settings.setValue("lastFolderPath", folder_path)
            self.load_files(folder_path)
        else:
            self._handle_folder_selection_cancelled()

    def _get_start_directory(self) -> str:
        """Get the starting directory for folder selection dialog."""
        if self.current_folder and Path(self.current_folder).is_dir():
            return self.current_folder
        return self.settings.value("lastFolderPath", str(Path.home()))

    def _handle_folder_selection_cancelled(self) -> None:
        """Handle when user cancels folder selection."""
        message = "Folder selection cancelled."
        nfo("[UI] %s", message)

        if hasattr(self, "left_panel"):
            self.left_panel.set_message_text(message)
        self.show_status_message(message)

    @debug_monitor
    def load_files(self, folder_path: str, file_to_select_after_load: str | None = None) -> None:
        """Load files from a folder in a background thread.

        Args:
            folder_path: Path to the folder to load
            file_to_select_after_load: Optional file to select after loading

        """
        nfo("[UI] Attempting to load files from: %s", folder_path)

        # Check if already loading
        if self.file_loader and self.file_loader.isRunning():
            self._handle_loading_in_progress()
            return

        # Setup loading state
        self._setup_loading_state(folder_path)

        # Start background loading
        self._start_file_loading(file_to_select_after_load)

    def _handle_loading_in_progress(self) -> None:
        """Handle when file loading is already in progress."""
        nfo("[UI] File loading is already in progress.")
        if hasattr(self, "left_panel"):
            self.left_panel.set_message_text("Loading in progress... Please wait.")

    def _setup_loading_state(self, folder_path: str) -> None:
        """Setup UI state for file loading."""
        self.current_folder = str(Path(folder_path).resolve())

        if hasattr(self, "left_panel"):
            folder_name = Path(self.current_folder).name
            self.left_panel.set_current_folder_text(f"Current Folder: {self.current_folder}")
            self.left_panel.set_message_text(f"Loading files from {folder_name}...")
            self.left_panel.set_buttons_enabled(False)

    def _start_file_loading(self, file_to_select: str | None) -> None:
        """Start the file loading thread."""
        self.file_loader = FileLoader(self.current_folder, file_to_select)
        self.file_loader.finished.connect(self.on_files_loaded)
        self.file_loader.start()
        nfo("[UI] FileLoader thread started for: %s", self.current_folder)

    @debug_monitor
    def on_files_loaded(self, result: FileLoadResult) -> None:
        """Handle completion of file loading.

        Args:
            result: Result from the file loading thread

        """
        nfo(
            "[UI] FileLoader finished. Received result for folder: %s",
            result.folder_path,
        )

        if not hasattr(self, "left_panel"):
            nfo("[UI] Error: Left panel not available in on_files_loaded.")
            return

        # Check if result is stale
        if result.folder_path != self.current_folder:
            self._handle_stale_result(result)
            return

        # Re-enable UI
        self.left_panel.set_buttons_enabled(True)

        # Process results
        if self._has_compatible_files(result):
            self._populate_file_list(result)
        else:
            self._handle_no_compatible_files(result)

    def _handle_stale_result(self, result: FileLoadResult) -> None:
        """Handle stale file loading results."""
        nfo(
            "[UI] Discarding stale FileLoader result for: %s (current is %s)",
            result.folder_path,
            self.current_folder,
        )
        if hasattr(self, "left_panel"):
            self.left_panel.set_buttons_enabled(True)

    def _has_compatible_files(self, result: FileLoadResult) -> bool:
        """Check if the result contains any compatible files."""
        return bool(result and (result.images or result.texts or result.models))

    def _populate_file_list(self, result: FileLoadResult) -> None:
        """Populate the file list with loaded files."""
        # Combine and sort all files case-insensitively
        all_files = result.images + result.texts + result.models
        self.current_files_in_list = sorted(list(set(all_files)), key=str.lower)

        # Update UI
        self.left_panel.clear_file_list_display()
        self.left_panel.add_items_to_file_list(self.current_files_in_list)

        # Set status message
        folder_name = Path(result.folder_path).name
        file_count = len(self.current_files_in_list)
        self.left_panel.set_message_text(f"Loaded {file_count} file(s) from {folder_name}.")

        # Auto-select file
        self._auto_select_file(result)

    def _auto_select_file(self, result: FileLoadResult) -> None:
        """Auto-select a file after loading."""
        selected = False

        # Try to select the requested file
        if result.file_to_select:
            if self.left_panel.set_current_file_by_name(result.file_to_select):
                nfo("[UI] Auto-selected file: %s", result.file_to_select)
                selected = True

        # Fall back to first file
        if not selected and self.left_panel.get_files_list_widget().count() > 0:
            self.left_panel.set_current_file_by_row(0)
            nfo("[UI] Auto-selected first file in the list.")
        elif not selected:
            self.clear_selection()

    def _handle_no_compatible_files(self, result: FileLoadResult) -> None:
        """Handle when no compatible files are found."""
        folder_name = Path(result.folder_path).name
        message = f"No compatible files found in {folder_name}."

        self.left_panel.set_message_text(message)
        self.show_status_message(message, 5000)

        nfo(
            "[UI] No compatible files found or result was empty for %s.",
            result.folder_path,
        )

        self.current_files_in_list = []
        self.left_panel.clear_file_list_display()

    # ========================================================================
    # FILE LIST MANAGEMENT
    # ========================================================================

    def sort_files_list(self) -> None:
        """Sort the current file list alphabetically."""
        nfo("[UI] 'Sort Files' button clicked (from LeftPanelWidget).")

        if not hasattr(self, "left_panel"):
            return

        if self.current_files_in_list:
            self._perform_file_sort()
        else:
            self._handle_no_files_to_sort()

    def _perform_file_sort(self) -> None:
        """Perform the actual file sorting operation."""
        list_widget = self.left_panel.get_files_list_widget()

        # Remember current selection
        current_item = list_widget.currentItem()
        current_selection = current_item.text() if current_item else None

        # Sort and repopulate case-insensitively
        self.current_files_in_list.sort(key=str.lower)
        self.left_panel.clear_file_list_display()
        self.left_panel.add_items_to_file_list(self.current_files_in_list)

        # Restore selection
        if current_selection:
            self.left_panel.set_current_file_by_name(current_selection)
        elif list_widget.count() > 0:
            self.left_panel.set_current_file_by_row(0)

        # Update status
        file_count = len(self.current_files_in_list)
        message = f"Files sorted ({file_count} items)."
        self.left_panel.set_message_text(message)
        self.show_status_message(message)

        nfo("[UI] Files list re-sorted and repopulated.")

    def _handle_no_files_to_sort(self) -> None:
        """Handle when there are no files to sort."""
        message = "No files to sort."
        self.left_panel.set_message_text(message)
        self.show_status_message(message)
        nfo("[UI] %s", message)

    def clear_file_list(self) -> None:
        """Clear the file list and reset UI state."""
        nfo("[UI] Clearing file list and selections.")

        if hasattr(self, "left_panel"):
            self.left_panel.clear_file_list_display()
            self.left_panel.set_message_text("Select a folder or drop files/folder here.")

        self.current_files_in_list = []
        self.clear_selection()

    # ========================================================================
    # SELECTION AND DISPLAY MANAGEMENT
    # ========================================================================

    def clear_selection(self) -> None:
        """Clear current file selection and reset displays."""
        if hasattr(self, "image_preview"):
            self.image_preview.clear()

        self.metadata_display.clear_all_displays()

    @debug_monitor
    def on_file_selected(
        self,
        current_item: Qw.QListWidgetItem | None,
        _previous_item: Qw.QListWidgetItem | None = None,
    ) -> None:
        """Handle file selection from the file list.

        Args:
            current_item: Currently selected list item
            _previous_item: Previously selected item (unused)

        """
        if not current_item:
            self._handle_no_file_selected()
            return

        # Clear previous displays
        self.clear_selection()

        # Get file information
        file_name = current_item.text()
        self._update_selection_status(file_name)

        # Validate context
        if not self._validate_file_context(file_name):
            return

        # Process the selected file
        self._process_selected_file(file_name)

    def _handle_no_file_selected(self) -> None:
        """Handle when no file is selected."""
        self.clear_selection()

        if hasattr(self, "left_panel"):
            self.left_panel.set_message_text("No file selected.")
        self.show_status_message("No file selected.")

    def _update_selection_status(self, file_name: str) -> None:
        """Update UI to reflect current file selection."""
        if hasattr(self, "left_panel"):
            count = len(self.current_files_in_list)
            folder_name = Path(self.current_folder).name if self.current_folder else "Unknown Folder"
            self.left_panel.set_message_text(f"{count} file(s) in {folder_name}")

        self.show_status_message(f"Selected: {file_name}", 4000)
        nfo("[UI] File selected: '%s'", file_name)

    def _validate_file_context(self, file_name: str) -> bool:
        """Validate that we have proper file context."""
        if not self.current_folder or not file_name:
            nfo("[UI] Folder/file context missing.")
            error_data = {EmptyField.PLACEHOLDER.value: {"Error": "Folder/file context missing."}}
            self.metadata_display.display_metadata(error_data)
            return False
        return True

    def _process_selected_file(self, file_name: str) -> None:
        """Process the selected file for display."""
        full_file_path = os.path.join(self.current_folder, file_name)
        nfo("[UI] Processing file: '%s'", full_file_path)

        # Check if file exists and display image if applicable
        if self._should_display_as_image(full_file_path):
            self.display_image_of(full_file_path)

        # Load and display metadata
        self._load_and_display_metadata(file_name)

    def _should_display_as_image(self, file_path: str) -> bool:
        """Check if file should be displayed as an image."""
        path_obj = Path(file_path)

        if not path_obj.is_file():
            nfo("[UI] File does not exist: '%s'", file_path)
            return False

        file_suffix = path_obj.suffix.lower()

        # Check against image format sets
        if hasattr(Ext, "IMAGE") and isinstance(Ext.IMAGE, list):
            for image_format_set in Ext.IMAGE:
                if isinstance(image_format_set, set) and file_suffix in image_format_set:
                    nfo("[UI] File matches image format: '%s'", file_suffix)
                    return True

        nfo("[UI] File is not a supported image format: '%s'", file_suffix)
        return False

    def _load_and_display_metadata(self, file_name: str) -> None:
        """Load metadata for a file and display it."""
        try:
            metadata_dict = self.load_metadata(file_name)
            self.metadata_display.display_metadata(metadata_dict)

            if metadata_dict:
                placeholder_key = EmptyField.PLACEHOLDER.value
                if len(metadata_dict) == 1 and placeholder_key in metadata_dict:
                    nfo("No meaningful metadata for %s", file_name)
            else:
                nfo("No metadata for %s (load_metadata returned None)", file_name)

        except Exception as e:
            nfo(
                "Error loading/displaying metadata for %s: %s",
                file_name,
                e,
                exc_info=True,
            )
            self.metadata_display.display_metadata(None)

    # ========================================================================
    # METADATA OPERATIONS
    # ========================================================================

    @debug_monitor
    def load_metadata(self, file_name: str) -> dict[str, Any] | None:
        """Load metadata from a file.

        Args:
            file_name: Name of the file to load metadata from

        Returns:
            Dictionary containing metadata or None if failed

        """
        if not self.current_folder or not file_name:
            nfo("[UI] Cannot load metadata: folder/file name missing.")
            return {EmptyField.PLACEHOLDER.value: {"Error": "Cannot load metadata, folder/file name missing."}}

        full_file_path = os.path.join(self.current_folder, file_name)
        nfo("[UI] Loading metadata from: %s", full_file_path)

        try:
            return parse_metadata(full_file_path)
        except OSError as e:
            nfo("Error parsing metadata for %s: %s", full_file_path, e, exc_info=True)
            return None

    # ========================================================================
    # IMAGE DISPLAY
    # ========================================================================

    def display_image_of(self, image_file_path: str) -> None:
        """Display an image in the preview panel using background thread.

        Args:
            image_file_path: Path to the image file

        """
        nfo("[UI] Requesting image load for preview: '%s'", image_file_path)

        try:
            # Clear previous pixmap immediately for responsiveness
            if hasattr(self, "image_preview"):
                self.image_preview.setPixmap(None)

            # Use threaded loading if available, otherwise fallback to sync
            if self.image_loader_worker and self.image_loader_thread:
                # Cancel any ongoing loading task
                self.image_loader_worker.cancel_current_task()

                # Start loading in background thread using signal
                self.image_loader_worker.load_requested.emit(image_file_path, 1024)
            else:
                # Fallback to synchronous loading
                nfo("[UI] Thread not available, using synchronous loading")
                self._load_image_synchronously(image_file_path)

        except Exception as e:
            nfo(
                "[UI] Exception requesting image load '%s': %s",
                image_file_path,
                e,
                exc_info=True,
            )

    def _load_image_synchronously(self, image_file_path: str) -> None:
        """Fallback synchronous image loading when threading is not available."""
        try:
            # Memory-efficient thumbnail generation using Pillow
            max_preview_size = 1024
            pixmap = create_safe_thumbnail(image_file_path, max_preview_size)

            if pixmap.isNull():
                nfo("[UI] Failed to load image: '%s'", image_file_path)
                self.show_status_message("Failed to load image")
            else:
                nfo(
                    "[UI] Image loaded successfully: %dx%d",
                    pixmap.width(),
                    pixmap.height(),
                )
                if hasattr(self, "image_preview"):
                    self.image_preview.setPixmap(pixmap)
                self.show_status_message(f"Image loaded: {pixmap.width()}x{pixmap.height()}")

        except Exception as e:
            nfo("[UI] Exception in synchronous image loading: %s", e)
            self.show_status_message("Error loading image")
        finally:
            # Force garbage collection after image operations
            import gc

            gc.collect()

    # ========================================================================
    # USER ACTIONS
    # ========================================================================

    def copy_metadata_to_clipboard(self) -> None:
        """Copy all displayed metadata to clipboard."""
        nfo("Copy All Metadata button clicked.")

        text_content = self.metadata_display.get_all_display_text()

        if text_content:
            QtGui.QGuiApplication.clipboard().setText(text_content)
            self.show_status_message("Displayed metadata copied to clipboard!")
            nfo("Displayed metadata copied to clipboard.")
        else:
            self.show_status_message("No actual metadata displayed to copy.")
            nfo("No metadata content available for copying.")

    def apply_theme(self, theme_name: str, initial_load: bool = False) -> bool:
        """Apply a theme via the theme manager."""
        if hasattr(self, "theme_manager"):
            return self.theme_manager.apply_theme(theme_name, initial_load)
        return False

    def open_settings_dialog(self) -> None:
        """Open the application settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()
        # Re-apply fonts after dialog closes to ensure they stick
        self.apply_global_font()

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
            nfo("[UI] Error creating thumbnail for '%s': %s", image_path, e)
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
            nfo("[UI] Error converting PIL to QPixmap: %s", e)
            return QtGui.QPixmap()

    def apply_global_font(self) -> None:
        """Apply the global font settings and refresh the theme."""
        app = Qw.QApplication.instance()
        if not app:
            return

        # Use Open Sans as default if no font preference is saved
        font_family = self.settings.value("fontFamily", "Open Sans", type=str)
        font_size = self.settings.value("fontSize", 10, type=int)

        # Create font with bundled Open Sans as fallback
        font = QFont(font_family, font_size)
        nfo(f"Using font: {font_family} {font_size}pt")

        # Set application-wide font
        app.setFont(font)

        # Apply font to specific text boxes to ensure they inherit user's choice
        text_boxes = [
            "positive_prompt_box",
            "negative_prompt_box",
            "generation_data_box",
        ]

        for box_name in text_boxes:
            if hasattr(self, box_name):
                text_box = getattr(self, box_name)
                text_box.setFont(font)
                # Force update the widget to ensure font change takes effect
                text_box.update()
                # Verify the font was applied
                current_font = text_box.font()
                nfo(f"[FONT] Applied to {box_name}: {current_font.family()} {current_font.pointSize()}pt")
            else:
                nfo(f"[FONT] WARNING: {box_name} not found on main window")

        # Force a repaint of the entire window to ensure all widgets get the new font
        self.update()

    def show_about_dialog(self) -> None:
        """Show the about dialog."""
        from dataset_tools import __version__

        about_text = (
            f"<b>Dataset Viewer v{__version__}</b><br><br>"
            f"An ultralight metadata viewer for AI-generated content.<br><br>"
            f"<b>Copyright © 2025 KTISEOS NYX / EARTH & DUSK MEDIA</b><br>"
            f"Licensed under GPL-3.0<br><br>"
            f"Built with PyQt6 and Pillow for robust metadata extraction."
        )

        # Use QMessageBox.about for proper theme inheritance
        Qw.QMessageBox.about(self, "About Dataset Viewer", about_text)

    def show_font_report(self) -> None:
        """Show font availability report in console."""
        font_manager = get_font_manager()
        font_manager.print_font_report()

    def show_theme_report(self) -> None:
        """Show enhanced theme system report in console."""
        self.enhanced_theme_manager.print_theme_report()

    # ========================================================================
    # DRAG & DROP SUPPORT
    # ========================================================================

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            nfo("[UI] Drag enter accepted.")
        else:
            event.ignore()
            nfo("[UI] Drag enter ignored (not URLs).")

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        """Handle drag move events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Handle drop events for files and folders."""
        mime_data = event.mimeData()

        if not mime_data.hasUrls():
            event.ignore()
            nfo("[UI] Drop ignored: no URLs.")
            return

        urls = mime_data.urls()
        if not urls:
            event.ignore()
            nfo("[UI] Drop ignored: empty URL list.")
            return

        # Process first dropped item
        first_url = urls[0]
        if not first_url.isLocalFile():
            event.ignore()
            nfo("[UI] Drop ignored: not a local file.")
            return

        dropped_path = first_url.toLocalFile()
        nfo("[UI] Item dropped: %s", dropped_path)

        # Determine what was dropped
        folder_to_load, file_to_select = self._process_dropped_path(dropped_path)

        if folder_to_load:
            self.settings.setValue("lastFolderPath", folder_to_load)
            self.load_files(folder_to_load, file_to_select_after_load=file_to_select)
            event.acceptProposedAction()
        else:
            event.ignore()
            nfo("[UI] Drop ignored: invalid file/folder.")

    def _process_dropped_path(self, dropped_path: str) -> tuple[str, str | None]:
        """Process a dropped file/folder path.

        Args:
            dropped_path: Path that was dropped

        Returns:
            Tuple of (folder_to_load, file_to_select)

        """
        path_obj = Path(dropped_path)

        if path_obj.is_file():
            folder_to_load = str(path_obj.parent)
            file_to_select = path_obj.name
            nfo(
                "[UI] Dropped file. Loading folder: '%s', selecting: '%s'",
                folder_to_load,
                file_to_select,
            )
            return folder_to_load, file_to_select

        if path_obj.is_dir():
            folder_to_load = str(path_obj)
            nfo("[UI] Dropped folder. Loading: '%s'", folder_to_load)
            return folder_to_load, None

        return "", None

    # ========================================================================
    # WINDOW LIFECYCLE
    # ========================================================================

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle window close event and save settings."""
        nfo("[UI] Close event triggered. Saving settings.")

        # Save splitter positions
        self.layout_manager.save_layout_state()

        # Save window geometry if enabled
        if self.settings.value("rememberGeometry", True, type=bool):
            self.settings.setValue("geometry", self.saveGeometry())
        else:
            self.settings.remove("geometry")

        # Clean up image loading thread
        self._cleanup_image_loading_thread()

        super().closeEvent(event)

    def _cleanup_image_loading_thread(self) -> None:
        """Clean up the image loading thread on application close."""
        try:
            if self.image_loader_worker:
                self.image_loader_worker.cancel_current_task()

            if self.image_loader_thread and self.image_loader_thread.isRunning():
                self.image_loader_thread.quit()
                if not self.image_loader_thread.wait(3000):  # Wait up to 3 seconds
                    self.image_loader_thread.terminate()
                    self.image_loader_thread.wait()  # Wait for termination

            nfo("[UI] Image loading thread cleaned up successfully")

        except Exception as e:
            nfo("[UI] Error cleaning up image loading thread: %s", e)

    def resize_window(self, width: int, height: int) -> None:
        """Resize the window to specified dimensions.

        Args:
            width: New window width
            height: New window height

        """
        self.resize(width, height)
        nfo("[UI] Window resized to: %dx%d", width, height)

    # ========================================================================
    # EASTER EGG - KONAMI CODE
    # ========================================================================

    def _initialize_konami_code(self) -> None:
        """Initialize Konami code tracking."""
        self.konami_code_sequence = [
            QtCore.Qt.Key.Key_Up,
            QtCore.Qt.Key.Key_Up,
            QtCore.Qt.Key.Key_Down,
            QtCore.Qt.Key.Key_Down,
            QtCore.Qt.Key.Key_Left,
            QtCore.Qt.Key.Key_Right,
            QtCore.Qt.Key.Key_Left,
            QtCore.Qt.Key.Key_Right,
            QtCore.Qt.Key.Key_B,
            QtCore.Qt.Key.Key_A,
        ]
        self.konami_code_progress = 0
        self.chaos_unlocked_key = "chaosCollection/unlocked"

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Override key press event to check for Konami code."""
        super().keyPressEvent(event)

    def _check_konami_code(self, key: int) -> None:
        """Check if the pressed key matches the Konami code sequence."""
        if self.settings.value(self.chaos_unlocked_key, False, type=bool):
            return  # Already unlocked

        if key == self.konami_code_sequence[self.konami_code_progress]:
            self.konami_code_progress += 1
            if self.konami_code_progress == len(self.konami_code_sequence):
                self._unlock_chaos_collection()
                self.konami_code_progress = 0  # Reset after success
        else:
            self.konami_code_progress = 0  # Reset on incorrect key

    def _unlock_chaos_collection(self) -> None:
        """Unlock the chaos theme collection and notify user."""
        self.settings.setValue(self.chaos_unlocked_key, True)
        self.show_status_message("Chaos Collection Unlocked! Prepare for madness.", 5000)
        nfo("Chaos Collection Unlocked via Konami Code!")

        # Optionally, refresh theme manager to show new category immediately
        if hasattr(self, "enhanced_theme_manager"):
            self.enhanced_theme_manager.refresh_theme_categories()
            # Re-open settings dialog if it's open to show new themes
            # This would require a signal from theme manager to settings dialog
            # For now, a simple status message is sufficient.
