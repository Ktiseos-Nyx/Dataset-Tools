# dataset_tools/ui/main_window.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""Main application window for Dataset Tools.

This module contains the core MainWindow class that orchestrates the entire
application interface, handling file management, metadata display, and user interactions.
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, PngImagePlugin
from PyQt6 import QtCore, QtGui
from PyQt6 import QtWidgets as Qw
from PyQt6.QtCore import QObject, QSettings, QThread, QThreadPool, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog

from .civitai_api_worker import CivitaiInfoWorker

from ..background_operations import (  # pylint: disable=relative-beyond-top-level
    TaskManager,
    parse_metadata_in_background,
)

# from PyQt6.QtWidgets import QApplication
from ..correct_types import DownField, UpField, EmptyField  # pylint: disable=relative-beyond-top-level
from ..correct_types import ExtensionType as Ext  # pylint: disable=relative-beyond-top-level
from ..logger import debug_message, debug_monitor  # pylint: disable=relative-beyond-top-level
from ..logger import info_monitor as nfo  # pylint: disable=relative-beyond-top-level
from ..metadata_parser import (
    parse_metadata,
)  # pylint: disable=relative-beyond-top-level
from ..widgets import (
    FileLoader,  # pylint: disable=relative-beyond-top-level
)
from .dialogs import SettingsDialog, TextEditDialog
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
from .thumbnail_grid import ThumbnailGridWidget
from .widgets import FileLoadResult
from .file_tree_panel import FileTreePanel

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
        self.current_selected_file: str | None = None
        self.current_metadata: dict | None = None
        self.civitai_api_worker: CivitaiInfoWorker | None = None
        self.active_workers = []
        # Load saved sort mode from settings
        self.current_sort_mode: str = self.settings.value("sortMode", "Name (Natural)", type=str)

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

        self.thread_pool = QThreadPool.globalInstance()

    def _initialize_managers(self) -> None:
        """Initialize UI and functionality managers."""
        # Use enhanced theme manager for multiple theme systems
        self.enhanced_theme_manager = get_enhanced_theme_manager(self, self.settings)

        # Keep original theme manager for backward compatibility if needed
        self.theme_manager = ThemeManager(self, self.settings)

        self.menu_manager = MenuManager(self)
        self.layout_manager = LayoutManager(self, self.settings)
        self.metadata_display = MetadataDisplayManager(self)

        # Background task manager for threading operations
        self.task_manager = TaskManager(self)

    def _setup_window_properties(self) -> None:
        """Configure basic window properties."""
        self.setWindowTitle("Dataset Viewer")
        self.setMinimumSize(*DEFAULT_WINDOW_SIZE)

    def _setup_status_bar(self) -> None:
        """Configure the status bar."""
        self.main_status_bar.showMessage("Ready", STATUS_MESSAGE_TIMEOUT)

        # Add current folder label (initially empty)
        self.current_folder_status_label = Qw.QLabel("No folder selected")
        self.current_folder_status_label.setMinimumWidth(200)
        self.main_status_bar.addPermanentWidget(self.current_folder_status_label)

        # Add file count label (initially empty)
        self.file_count_label = Qw.QLabel("")
        self.file_count_label.setMinimumWidth(100)
        self.main_status_bar.addPermanentWidget(self.file_count_label)

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
            self.left_panel.refresh_folder_requested.connect(self.refresh_current_folder)
            self.left_panel.sort_files_requested.connect(self.sort_files_list)
            self.left_panel.sort_mode_changed.connect(self.on_sort_mode_changed)
            self.left_panel.list_item_selected.connect(self.on_file_selected)

    def set_file_view_mode(self, mode: str) -> None:
        """Set the file view mode (list, grid, or tree).

        Args:
            mode: Either 'list', 'grid', or 'tree'

        """
        if mode == "grid":
            if not hasattr(self, "thumbnail_grid"):
                # Lazy init - only create grid when first needed
                self._initialize_thumbnail_grid()

            # Only repopulate if switching TO grid mode, not if already in grid mode
            was_already_grid = self.left_panel.file_view_stack.currentWidget() == self.thumbnail_grid

            self.left_panel.file_view_stack.setCurrentWidget(self.thumbnail_grid)

            # Only reload folder if we're switching views (not just adjusting settings)
            if not was_already_grid and self.current_folder and self.current_files_in_list:
                image_files = [f for f in self.current_files_in_list
                               if self._should_display_as_image(os.path.join(self.current_folder, f))]
                self.thumbnail_grid.set_folder(self.current_folder, image_files)

        elif mode == "tree":
            if not hasattr(self, "file_tree"):
                # Lazy init - only create tree when first needed
                self._initialize_file_tree()

            self.left_panel.file_view_stack.setCurrentWidget(self.file_tree)

            # Populate with current folder
            if self.current_folder:
                self.file_tree.set_root_path(self.current_folder)

        else:  # list mode
            self.left_panel.file_view_stack.setCurrentWidget(self.left_panel.files_list_widget)

        # Save view mode preference
        self.settings.setValue("fileViewMode", mode)

        nfo(f"[UI] File view mode set to: {mode}")

    def _initialize_thumbnail_grid(self):
        """Lazy initialization of thumbnail grid."""
        self.thumbnail_grid = ThumbnailGridWidget(parent=self)
        self.thumbnail_grid.file_selected.connect(self.on_file_selected)
        self.left_panel.file_view_stack.addWidget(self.thumbnail_grid)

        # Load saved thumbnail size settings
        thumb_auto = self.settings.value("thumbnailSizeAuto", True, type=bool)
        thumb_size = self.settings.value("thumbnailSize", 128, type=int)

        if not thumb_auto:
            # User has manual size set - apply it (skip reload since no thumbnails loaded yet)
            self.thumbnail_grid.set_manual_thumbnail_size(thumb_size, skip_reload=True)
            nfo(f"[UI] Thumbnail grid initialized with manual size: {thumb_size}px")
        else:
            nfo("[UI] Thumbnail grid initialized with auto-sizing")

    def _initialize_file_tree(self):
        """Lazy initialization of file tree."""
        self.file_tree = FileTreePanel(parent=self)
        self.file_tree.file_selected.connect(self.on_file_selected)
        self.file_tree.folder_changed.connect(lambda path: nfo("[UI] Tree folder changed: %s", path))
        self.left_panel.file_view_stack.addWidget(self.file_tree)

        # Set supported extensions from file operations
        from ..file_operations import FileOperations
        file_ops = FileOperations()
        extensions = file_ops.get_supported_extensions()
        all_extensions = set()
        for ext_set in extensions.values():
            all_extensions.update(ext_set)
        self.file_tree.set_supported_extensions(all_extensions)

        nfo("[UI] File tree initialized")

    def _restore_application_state(self) -> None:
        """Restore window geometry and load initial folder."""
        self.theme_manager.restore_window_geometry()
        self._load_initial_folder()

        # Apply saved view mode
        view_mode = self.settings.value("fileViewMode", "list", type=str)
        if view_mode in ("grid", "tree"):
            self.set_file_view_mode(view_mode)

        # Restore sort mode combo box to match saved setting
        if hasattr(self, "left_panel") and hasattr(self.left_panel, "sort_mode_combo"):
            self.left_panel.sort_mode_combo.setCurrentText(self.current_sort_mode)
            nfo("[UI] Restored sort mode combo box to: %s", self.current_sort_mode)

    def _load_initial_folder(self) -> None:
        """Load the last used folder or show empty state."""
        initial_folder = self.settings.value("lastFolderPath", os.getcwd())
        last_selected_file = self.settings.value("lastSelectedFile", None, type=str)
        self.clear_file_list()

        if initial_folder and Path(initial_folder).is_dir():
            # Restore last selected file if available
            self.load_files(initial_folder, file_to_select_after_load=last_selected_file)
        else:
            self._show_empty_folder_state()

    def _show_empty_folder_state(self) -> None:
        """Show UI state when no folder is loaded."""
        if hasattr(self, "left_panel"):
            # Current folder info now in status bar
            self.current_folder_status_label.setText("No folder selected")
            # Left panel stays clean - status only in status bar
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

    def refresh_current_folder(self) -> None:
        """Refresh the current folder by reloading its files."""
        nfo("[UI] 'Refresh Folder' action triggered.")

        if self.current_folder and Path(self.current_folder).is_dir():
            nfo("[UI] Refreshing folder: %s", self.current_folder)
            # Preserve current selection when refreshing
            self.load_files(self.current_folder, file_to_select_after_load=self.current_selected_file)
        else:
            nfo("[UI] No current folder to refresh.")

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
            # Left panel stays clean - status only in status bar
            pass  # self.left_panel.set_message_text(message)
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
            # Left panel stays clean - status only in status bar
            pass  # self.left_panel.set_message_text("Loading in progress... Please wait.")

    def _setup_loading_state(self, folder_path: str) -> None:
        """Setup UI state for file loading."""
        self.current_folder = str(Path(folder_path).resolve())

        if hasattr(self, "left_panel"):
            # Current folder info now in status bar
            folder_name = Path(self.current_folder).name if self.current_folder else "Unknown"
            self.current_folder_status_label.setText(f"Folder: {folder_name}")
            # Status info moved to status bar - keep left panel clean
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
        import re

        # Use natural sort for initial population (instead of lexicographic)
        def natural_sort_key(text):
            return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", text)]

        all_files = sorted(list(set(result.images + result.texts + result.models)), key=natural_sort_key)
        self.current_files_in_list = all_files

        self.left_panel.clear_file_list_display()
        self.left_panel.add_items_to_file_list(self.current_files_in_list)

        folder_name = Path(result.folder_path).name
        file_count = len(all_files)
        self.file_count_label.setText(f"{file_count} files in {folder_name}")

        # Apply the saved sort mode BEFORE creating thumbnail grid to prevent race condition
        if self.current_sort_mode != "Name (Natural)":
            nfo("[UI] Re-applying saved sort mode: %s", self.current_sort_mode)
            # Don't call _perform_file_sort() yet - it would repopulate thumbnail grid twice
            # Just sort the list in place
            self._sort_file_list_only(self.current_sort_mode)

        self._auto_select_file(result)

        # Update thumbnail grid if in grid mode (after sorting!)
        if hasattr(self, "thumbnail_grid") and self.settings.value("fileViewMode", "list") == "grid":
            total_files = len(self.current_files_in_list)
            nfo("[UI] Filtering %d files for thumbnail grid...", total_files)

            image_files = []
            for file_name in self.current_files_in_list:
                if self._should_display_as_image(os.path.join(self.current_folder, file_name)):
                    image_files.append(file_name)

            nfo("[UI] Found %d images, populating grid...", len(image_files))
            # Pass the file_to_select to thumbnail grid so it can scroll to it
            file_to_select = result.file_to_select if result.file_to_select in image_files else None
            nfo("[UI] Calling thumbnail_grid.set_folder with %d images, file_to_select=%s", len(image_files), file_to_select)
            self.thumbnail_grid.set_folder(self.current_folder, image_files, file_to_select=file_to_select)
            nfo("[UI] thumbnail_grid.set_folder returned")

        # Update tree view if in tree mode
        if hasattr(self, "file_tree") and self.settings.value("fileViewMode", "list") == "tree":
            nfo("[UI] Updating tree view for new folder...")
            self.file_tree.set_root_path(self.current_folder)

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

        # Update status bar to show 0 files
        self.file_count_label.setText(f"0 files in {folder_name}")

        # Keep left panel clean - status info in status bar only
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

    def on_sort_mode_changed(self, mode: str) -> None:
        """Handle sort mode change from the combo box.

        Args:
            mode: The selected sort mode (e.g., "Name (Natural)", "Date Modified", etc.)
        """
        nfo("[UI] Sort mode changed to: %s", mode)

        # Save the current sort mode so it persists across refreshes and app restarts
        self.current_sort_mode = mode
        self.settings.setValue("sortMode", mode)

        if not hasattr(self, "left_panel"):
            return

        if self.current_files_in_list:
            self._perform_file_sort(mode)
        else:
            nfo("[UI] No files to sort.")

    def _sort_file_list_only(self, mode: str) -> None:
        """Sort the file list in place without refreshing UI.

        This is used during initial folder load to avoid double-populating the UI.
        """
        import re

        if mode == "Name (Natural)":
            # Natural sort: handles numbers properly
            def natural_sort_key(text):
                return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", text)]
            self.current_files_in_list.sort(key=natural_sort_key)

        elif mode == "Date Modified":
            # Sort by modification time (newest first)
            def get_mtime(f):
                try:
                    return -os.path.getmtime(os.path.join(self.current_folder, f))
                except OSError:
                    return 0
            self.current_files_in_list.sort(key=get_mtime)

        elif mode == "Date Created":
            # Sort by creation time (newest first)
            def get_ctime(f):
                try:
                    return -os.path.getctime(os.path.join(self.current_folder, f))
                except OSError:
                    return 0
            self.current_files_in_list.sort(key=get_ctime)

        elif mode == "File Size":
            # Sort by file size (largest first)
            def get_size(f):
                try:
                    return -os.path.getsize(os.path.join(self.current_folder, f))
                except OSError:
                    return 0
            self.current_files_in_list.sort(key=get_size)

    def _perform_file_sort(self, mode: str = "Name (Natural)") -> None:
        """Perform the actual file sorting operation.

        Args:
            mode: Sort mode - one of "Name (Natural)", "Date Modified", "Date Created", "File Size"
        """
        import re
        from pathlib import Path

        list_widget = self.left_panel.get_files_list_widget()

        # Remember current selection
        current_item = list_widget.currentItem()
        current_selection = current_item.text() if current_item else None

        # Get the sort key function based on mode
        if mode == "Name (Natural)":
            # Natural sort: handles numbers properly (IMG_2.jpg before IMG_10.jpg)
            def natural_sort_key(text):
                return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", text)]
            self.current_files_in_list.sort(key=natural_sort_key)

        elif mode == "Date Modified":
            # Sort by modification time (newest first)
            def mtime_key(filepath):
                try:
                    # Use full path for stat
                    return -Path(os.path.join(self.current_folder, filepath)).stat().st_mtime
                except (OSError, AttributeError):
                    return 0
            self.current_files_in_list.sort(key=mtime_key)

        elif mode == "Date Created":
            # Sort by creation time (newest first)
            def ctime_key(filepath):
                try:
                    # Use full path for stat
                    return -Path(os.path.join(self.current_folder, filepath)).stat().st_ctime
                except (OSError, AttributeError):
                    return 0
            self.current_files_in_list.sort(key=ctime_key)

        elif mode == "File Size":
            # Sort by file size (largest first)
            def size_key(filepath):
                try:
                    # Use full path for stat
                    return -Path(os.path.join(self.current_folder, filepath)).stat().st_size
                except (OSError, AttributeError):
                    return 0
            self.current_files_in_list.sort(key=size_key)

        # Refresh the appropriate view
        view_mode = self.settings.value("fileViewMode", "list", type=str)

        if view_mode == "grid":
            if hasattr(self, "thumbnail_grid"):
                nfo("[UI] Refreshing thumbnail grid with sorted files.")
                image_files = [f for f in self.current_files_in_list if self._should_display_as_image(os.path.join(self.current_folder, f))]
                # Pass current selection to restore it after reload
                file_to_select = current_selection if current_selection and current_selection in image_files else None
                self.thumbnail_grid.set_folder(self.current_folder, image_files, file_to_select=file_to_select)
        else:
            nfo("[UI] Refreshing file list with sorted files.")
            self.left_panel.clear_file_list_display()
            self.left_panel.add_items_to_file_list(self.current_files_in_list)
            # Restore selection
            if current_selection:
                self.left_panel.set_current_file_by_name(current_selection)
            elif list_widget.count() > 0:
                self.left_panel.set_current_file_by_row(0)

        # Update status bar
        file_count = len(self.current_files_in_list)
        message = f"Files sorted by {mode} ({file_count} items)."
        self.show_status_message(message)

        nfo("[UI] Files list re-sorted by %s and repopulated.", mode)

    def _handle_no_files_to_sort(self) -> None:
        """Handle when there are no files to sort."""
        message = "No files to sort."
        self.show_status_message(message)
        nfo("[UI] %s", message)

    def clear_file_list(self) -> None:
        """Clear the file list and reset UI state."""
        nfo("[UI] Clearing file list and selections.")

        if hasattr(self, "left_panel"):
            self.left_panel.clear_file_list_display()
            # Left panel stays clean - status only in status bar
            pass  # self.left_panel.set_message_text("Select a folder or drop files/folder here.")

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
        current_item: Qw.QListWidgetItem | str | None,
        _previous_item: Qw.QListWidgetItem | None = None,
    ) -> None:
        """Handle file selection from either the list view or the grid view."""
        file_name: str | None = None

        if isinstance(current_item, str):
            file_name = current_item
        elif hasattr(current_item, "text"):
            # It's likely a QListWidgetItem
            file_name = current_item.text()

        if not file_name:
            self._handle_no_file_selected()
            return

        self.current_selected_file = file_name

        # Save selected file for next session
        self.settings.setValue("lastSelectedFile", file_name)

        # Clear previous displays
        self.clear_selection()

        # Get file information
        self._update_selection_status(file_name)

        # Validate context
        if not self._validate_file_context(file_name):
            return

        # Process the selected file
        self._process_selected_file(file_name)

    def _handle_no_file_selected(self) -> None:
        """Handle when no file is selected."""
        self.clear_selection()
        self.current_selected_file = None

        if hasattr(self, "left_panel"):
            # Left panel stays clean - status only in status bar
            pass  # self.left_panel.set_message_text("No file selected.")
        self.show_status_message("No file selected.")

    def _update_selection_status(self, file_name: str) -> None:
        """Update UI to reflect current file selection."""
        if hasattr(self, "left_panel"):
            count = len(self.current_files_in_list)
            folder_name = Path(self.current_folder).name if self.current_folder else "Unknown Folder"
            # Left panel stays clean - status only in status bar
            pass  # self.left_panel.set_message_text(f"{count} file(s) in {folder_name}")

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
            # Load and display metadata for images
            self._load_and_display_metadata(file_name)

        elif self._should_display_as_text(full_file_path):
            # Handle text files by displaying their content
            try:
                # Check file size before loading (prevent UI freeze on huge files)
                path_obj = Path(full_file_path)
                file_size = path_obj.stat().st_size
                max_size = 10 * 1024 * 1024  # 10MB limit

                if file_size > max_size:
                    self.show_status_message(f"File too large to display ({file_size / (1024*1024):.1f}MB > 10MB limit)")
                    self.metadata_display.clear_all_displays()
                    self.generation_data_box.setText(
                        f"[File too large to display]\n\n"
                        f"File size: {file_size / (1024*1024):.1f}MB\n"
                        f"Maximum display size: 10MB\n\n"
                        f"Please open this file in a text editor."
                    )
                    return

                with open(full_file_path, encoding="utf-8") as f:
                    content = f.read()
                self.metadata_display.clear_all_displays()
                self.generation_data_box.setText(content)
                self.show_status_message(f"Displayed content of {file_name}")
            except Exception as e:
                self.show_status_message(f"Error reading text file: {e}")
                logger.error("Error reading text file: %s", e, exc_info=True)
        else:
            # For other file types like models, just load metadata
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
                    debug_message("[UI] File matches image format: '%s'", file_suffix)
                    return True

        nfo("[UI] File is not a supported image format: '%s'", file_suffix)
        return False

    def _should_display_as_text(self, file_path: str) -> bool:
        """Check if file should be treated as a displayable text file."""
        path_obj = Path(file_path)

        if not path_obj.is_file():
            return False

        file_suffix = path_obj.suffix.lower()

        # Check against plain text and schema file types
        text_exts = {ext for ext_set in getattr(Ext, "PLAIN_TEXT_LIKE", []) for ext in ext_set}
        schema_exts = {ext for ext_set in getattr(Ext, "SCHEMA_FILES", []) for ext in ext_set}
        all_text_like_exts = text_exts.union(schema_exts)

        if file_suffix in all_text_like_exts:
            nfo("[UI] File matches text format: '%s'", file_suffix)
            return True

        return False

    def _load_and_display_metadata(self, file_name: str) -> None:
        """Load metadata for a file and display it."""
        try:
            self.current_metadata = self.load_metadata(file_name)

            # If background processing is enabled, metadata_dict will be None
            # and the display will be updated asynchronously via callbacks
            if self.current_metadata is not None:
                self.metadata_display.display_metadata(self.current_metadata)
                self.fetch_civitai_info(self.current_metadata)

                placeholder_key = EmptyField.PLACEHOLDER.value
                if len(self.current_metadata) == 1 and placeholder_key in self.current_metadata:
                    nfo("No meaningful metadata for %s", file_name)
            else:
                # Check if we're using background processing
                use_background = self.settings.value("use_background_processing", False, type=bool)
                if not use_background:
                    nfo("No metadata for %s (load_metadata returned None)", file_name)
                # If background processing, don't log - it will be handled async

        except Exception as e:
            nfo(
                "Error loading/displaying metadata for %s: %s",
                file_name,
                e,
                exc_info=True,
            )
            self.metadata_display.display_metadata(None)

    def fetch_civitai_info(self, metadata_dict: dict) -> None:
        """Fetch Civitai info in a background thread using pre-extracted IDs."""
        # Check if the metadata engine already extracted CivitAI IDs for us
        civitai_api_info = metadata_dict.get(UpField.CIVITAI_INFO.value, {})

        # Debug logging removed - only log when actually fetching
        if isinstance(civitai_api_info, dict) and "ids_to_fetch" in civitai_api_info:
            # Use the IDs extracted by the metadata engine
            ids_to_fetch = civitai_api_info.get("ids_to_fetch", [])
        else:
            # Fallback: No Civitai IDs found - skip API call
            return

        if not ids_to_fetch:
            return

        nfo("[CIVITAI] Starting async fetch for %d CivitAI resources", len(ids_to_fetch))

        if ids_to_fetch:
            # Pass the current file path to the worker to prevent race conditions
            worker = CivitaiInfoWorker(ids_to_fetch, file_path=self.current_selected_file)
            worker.signals.finished.connect(self.on_civitai_info_fetched)
            worker.signals.error.connect(self.on_civitai_info_error)
            worker.signals.finished.connect(self.cleanup_worker)
            self.thread_pool.start(worker)
            self.active_workers.append(worker)

    def on_civitai_info_fetched(self, civitai_info: dict) -> None:
        """Update the UI with the fetched Civitai info."""
        # Get the worker that sent this signal
        worker = self.sender()

        # Race condition check: Only update if we're still viewing the same file
        if hasattr(worker, 'file_path') and worker.file_path != self.current_selected_file:
            nfo("[CIVITAI] Ignoring stale Civitai data for: %s (current: %s)",
                worker.file_path, self.current_selected_file)
            return

        if civitai_info and self.current_metadata:
            # Format CivitAI resources as human-readable parameter entries
            resources = []
            seen_resources = set()  # Track duplicates
            urn_to_name = {}  # Map URN → display name for prompt replacement

            for key, info in civitai_info.items():
                if isinstance(info, dict):
                    resource_type = info.get("type", "Unknown")
                    model_name = info.get("modelName", "Unknown")
                    version_name = info.get("versionName", "")
                    base_model = info.get("baseModel", "")
                    trained_words = info.get("trainedWords", [])

                    # For embeddings, use the activation tag instead of model name
                    if resource_type in ["TextualInversion", "Embedding"] and trained_words:
                        # Use first trained word as the display name
                        display_name = trained_words[0] if isinstance(trained_words, list) else str(trained_words)
                    else:
                        # Format: "ModelName v1.0 (Type - BaseModel)"
                        display_name = model_name
                        if version_name:
                            display_name += f" {version_name}"

                    if resource_type or base_model:
                        details = []
                        if resource_type:
                            details.append(resource_type)
                        if base_model:
                            details.append(base_model)
                        display_name += f" ({' - '.join(details)})"

                    # Only add if we haven't seen this exact resource
                    if display_name not in seen_resources:
                        resources.append(display_name)
                        seen_resources.add(display_name)

            # Build URN to name mapping from civitai_airs in parameters
            if DownField.GENERATION_DATA.value in self.current_metadata:
                params = self.current_metadata[DownField.GENERATION_DATA.value]
                civitai_airs = params.get("civitai_airs", [])

                # Match URNs to fetched resource info by model/version IDs
                import re
                for urn in civitai_airs:
                    if isinstance(urn, str):
                        urn_match = re.search(r'urn:air:.*?civitai:([0-9]+)@([0-9]+)', urn)
                        if urn_match:
                            model_id, version_id = urn_match.groups()
                            # Try to find matching resource info by ID
                            for key, info in civitai_info.items():
                                # Check if this info matches the URN's model_id or version_id
                                if model_id in key or version_id in key:
                                    if isinstance(info, dict):
                                        resource_type = info.get("type", "")
                                        info_model_name = info.get("modelName", "")
                                        trained_words = info.get("trainedWords", [])

                                        # For embeddings, use activation tag; otherwise use model name
                                        if resource_type in ["TextualInversion", "Embedding"] and trained_words:
                                            simple_name = trained_words[0] if isinstance(trained_words, list) else str(trained_words)
                                        else:
                                            simple_name = info_model_name

                                        if simple_name:
                                            urn_to_name[urn] = simple_name
                                            break

            # Replace URNs in prompt text with human-readable names
            if UpField.PROMPT.value in self.current_metadata and urn_to_name:
                prompt_data = self.current_metadata[UpField.PROMPT.value]
                for prompt_type in ["Positive", "Negative"]:
                    if prompt_type in prompt_data:
                        prompt_text = prompt_data[prompt_type]
                        for urn, name in urn_to_name.items():
                            # Replace "embedding:urn:air:..." with activation tag
                            prompt_text = prompt_text.replace(f"embedding:{urn}", name)
                            # Also replace bare URNs just in case
                            prompt_text = prompt_text.replace(urn, name)
                        prompt_data[prompt_type] = prompt_text

            # Add to parameters section as "CivitAI Resources" and reorder to show first
            if resources and DownField.GENERATION_DATA.value in self.current_metadata:
                params = self.current_metadata[DownField.GENERATION_DATA.value]

                # Create new ordered dict with civitai_resources first
                new_params = {"civitai_resources": resources}

                # Add all other fields after
                for key, value in params.items():
                    if key != "civitai_resources":  # Skip if it already exists
                        new_params[key] = value

                # Replace the parameters dict with the reordered one
                self.current_metadata[DownField.GENERATION_DATA.value] = new_params
                self.metadata_display.display_metadata(self.current_metadata)

    def cleanup_worker(self):
        worker = self.sender()
        if worker in self.active_workers:
            self.active_workers.remove(worker)

    def on_civitai_info_error(self, error_message: str) -> None:
        """Show an error message in the status bar when Civitai info fetching fails."""
        self.show_status_message(f"Civitai API Error: {error_message}")

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

        # Check if background processing is enabled
        use_background = self.settings.value("use_background_processing", False, type=bool)

        if use_background:
            # Use background processing for complex workflows
            self._load_metadata_in_background(full_file_path, file_name)
            return None  # Will be handled asynchronously
        # Use synchronous processing (original behavior)
        try:
            return parse_metadata(full_file_path, self.show_status_message)
        except OSError as e:
            nfo("Error parsing metadata for %s: %s", full_file_path, e, exc_info=True)
            return None

    def _load_metadata_in_background(self, full_file_path: str, file_name: str) -> None:
        """Load metadata in background thread."""
        def on_progress(percentage: int, message: str):
            if percentage >= 0:
                nfo(f"[Background] Progress: {percentage}% - {message}")
            else:
                nfo(f"[Background] Status: {message}")

            # Update status bar if we have a message
            if message:
                self.show_status_message(message)

        def on_completion(result: dict):
            nfo(f"[Background] Metadata loading completed for {file_name}")
            # Display the result
            self.metadata_display.display_metadata(result)

        def on_error(error: str):
            nfo(f"[Background] Metadata loading failed for {file_name}: {error}")
            error_dict = {EmptyField.PLACEHOLDER.value: {"Error": f"Background parsing failed: {error}"}}
            self.metadata_display.display_metadata(error_dict)

        # Start the background task
        task = parse_metadata_in_background(
            full_file_path,
            progress_callback=on_progress,
            completion_callback=on_completion,
            error_callback=on_error,
            parent=self,
        )

        # Track the task with our manager
        task_id = self.task_manager.start_task(task, f"parse_{file_name}")
        nfo(f"[Background] Started metadata parsing task: {task_id}")

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

    def open_edit_dialog(self) -> None:
        """Open the dialog to edit metadata for the selected file."""
        nfo("Edit Metadata button clicked.")

        if not self.current_folder or not self.current_selected_file:
            self.show_status_message("No file selected to edit.")
            return

        file_name = self.current_selected_file
        full_path = os.path.join(self.current_folder, file_name)

        # --- Text File Handling ---
        if file_name.lower().endswith(".txt"):
            try:
                with open(full_path, encoding="utf-8") as f:
                    initial_text = f.read()
            except Exception as e:
                self.show_status_message(f"Error reading file: {e}")
                return

            accepted, new_text = TextEditDialog.get_edited_text(self, initial_text)

            if accepted:
                try:
                    # Write to temp file first, then atomic replace
                    temp_path = full_path + ".tmp"
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write(new_text)
                    os.replace(temp_path, full_path)  # Atomic replace
                    self.show_status_message(f"Successfully saved changes to {file_name}.")
                    # Refresh the display to show new content
                    self.on_file_selected(self.current_selected_file)
                except Exception as e:
                    self.show_status_message(f"Error saving file: {e}")
                    logger.error("Error saving text file: %s", e, exc_info=True)
                    # Clean up temp file if it exists
                    temp_path = full_path + ".tmp"
                    if os.path.exists(temp_path):
                        try:
                            os.unlink(temp_path)
                        except OSError:
                            pass  # Best effort cleanup
            return  # End of text file logic

        # --- PNG File Handling ---
        if file_name.lower().endswith(".png"):
            try:
                img = Image.open(full_path)
                # Ensure it's a PNG and has metadata
                if img.format != "PNG" or not img.info:
                    self.show_status_message("Not a valid PNG file or no metadata found.")
                    return

                # Find the primary metadata key
                raw_key = None
                priority_keys = ["parameters", "prompt", "invokeai_metadata", "Dream", "sd-metadata"]
                for key in priority_keys:
                    if key in img.info:
                        raw_key = key
                        break

                if not raw_key:
                    self.show_status_message("No recognized raw metadata block found to edit.")
                    return

                initial_text = img.info[raw_key]

                # Show the dialog
                accepted, new_text = TextEditDialog.get_edited_text(self, initial_text)

                if accepted:
                    # Save the new metadata
                    new_meta = PngImagePlugin.PngInfo()
                    # Copy all other metadata first
                    for key, value in img.info.items():
                        if key != raw_key:
                            new_meta.add_text(key, value)

                    # Add the edited metadata
                    new_meta.add_text(raw_key, new_text)

                    # Save safely with proper cleanup
                    temp_path = full_path + ".tmp"
                    try:
                        img.save(temp_path, "PNG", pnginfo=new_meta)
                        os.replace(temp_path, full_path)  # Atomic on POSIX
                        self.show_status_message(f"Successfully saved metadata to {file_name}.")
                        # Refresh the view
                        self.on_file_selected(self.current_selected_file)
                    except Exception as save_error:
                        # Clean up temp file if it exists
                        if os.path.exists(temp_path):
                            try:
                                os.unlink(temp_path)
                            except OSError:
                                pass  # Best effort cleanup
                        raise save_error  # Re-raise to outer handler

            except Exception as e:
                self.show_status_message(f"Error processing PNG: {e}")
                logger.error("Error during PNG edit process: %s", e, exc_info=True)
            return  # End of PNG logic

        self.show_status_message("Editing is currently only supported for .txt and .png files.")

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
        # Each tab has its own Apply button - OK button just closes the dialog
        # No need to apply anything here

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
            nfo("[UI] Error creating thumbnail for '%s': %s", image_path, e, exc_info=True)
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
            nfo("[UI] Error converting PIL to QPixmap: %s", e, exc_info=True)
            return QtGui.QPixmap()

    def apply_global_font(self) -> None:
        """Apply the global font settings and refresh the theme."""
        app = Qw.QApplication.instance()
        if not app:
            return

        # Use JetBrains Mono as default if no font preference is saved
        font_family = self.settings.value("fontFamily", "JetBrains Mono", type=str)
        font_size = self.settings.value("fontSize", 10, type=int)

        # Create font with bundled Open Sans as fallback
        font = QFont(font_family, font_size)
        nfo(f"Using font: {font_family} {font_size}pt")

        # Set application-wide font
        app.setFont(font)

        # CRITICAL: Inject font into stylesheet to override QSS font rules
        # Get current stylesheet and append font override
        current_stylesheet = app.styleSheet()
        # Remove any previous font injection
        if "/* USER_FONT_OVERRIDE */" in current_stylesheet:
            parts = current_stylesheet.split("/* USER_FONT_OVERRIDE */")
            current_stylesheet = parts[0]

        # Inject user font choice into stylesheet with high specificity
        font_injection = f"""
/* USER_FONT_OVERRIDE */
QWidget, QTextEdit, QPlainTextEdit, QListWidget, QPushButton, QLabel, QLineEdit {{
    font-family: "{font_family}" !important;
    font-size: {font_size}pt !important;
}}
"""
        app.setStyleSheet(current_stylesheet + font_injection)

        # Apply font to specific text boxes to ensure they inherit user's choice
        text_boxes = [
            "positive_prompt_box",
            "negative_prompt_box",
            "generation_data_box",
            "parameters_box",
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

        # Apply font to file list widget (for list view)
        if hasattr(self, "left_panel"):
            try:
                files_list = self.left_panel.get_files_list_widget()
                files_list.setFont(font)
                files_list.update()
                nfo(f"[FONT] Applied to file list widget: {font.family()} {font.pointSize()}pt")
            except Exception as e:
                nfo(f"[FONT] Could not apply font to file list: {e}")

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

    def clear_thumbnail_cache(self) -> None:
        """Clear the thumbnail cache for the current folder and its subdirectories."""
        if not self.current_folder:
            self.show_status_message("No folder loaded, nothing to clear.")
            return

        nfo(f"[CACHE] Starting thumbnail cache clear for: {self.current_folder}")
        deleted_count = 0
        try:
            for root, dirs, _files in os.walk(self.current_folder):
                if ".thumbnails" in dirs:
                    cache_dir = os.path.join(root, ".thumbnails")
                    try:
                        shutil.rmtree(cache_dir)
                        nfo(f"[CACHE] Deleted thumbnail cache: {cache_dir}")
                        deleted_count += 1
                    except Exception as e:
                        nfo(f"[CACHE] Error deleting cache directory {cache_dir}: {e}")

            if deleted_count > 0:
                self.show_status_message(f"Successfully cleared {deleted_count} thumbnail cache(s).")
                # Refresh the view to show placeholders
                if hasattr(self, "thumbnail_grid"):
                    self.thumbnail_grid.set_folder(self.current_folder, self.current_files_in_list)
            else:
                self.show_status_message("No thumbnail caches found to clear.")

        except Exception as e:
            nfo(f"[CACHE] Error during cache clearing process: {e}")
            self.show_status_message("An error occurred while clearing the cache.")

    def clear_workflow_cache(self) -> None:
        """Clear the in-memory workflow analysis cache."""
        from ..numpy_scorers.base_numpy_scorer import WORKFLOW_CACHE
        cache_size = len(WORKFLOW_CACHE)
        WORKFLOW_CACHE.clear()
        nfo(f"[CACHE] Workflow cache cleared ({cache_size} entries removed).")
        self.show_status_message(f"Workflow cache cleared ({cache_size} workflows).")

    def clear_all_caches(self) -> None:
        """Clear all caches (thumbnails + workflow analysis)."""
        self.clear_thumbnail_cache()
        self.clear_workflow_cache()

    # ========================================================================
    # DRAG & DROP SUPPORT
    # ========================================================================

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:  # noqa: N802
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            nfo("[UI] Drag enter accepted.")
        else:
            event.ignore()
            nfo("[UI] Drag enter ignored (not URLs).")

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:  # noqa: N802
        """Handle drag move events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:  # noqa: N802
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

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
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

        # Clean up thumbnail worker thread
        if hasattr(self, "thumbnail_grid"):
            self.thumbnail_grid.cleanup()

        # Wait for any background workers (CivitAI, thumbnails, etc.) to finish
        from PyQt6.QtCore import QThreadPool
        thread_pool = QThreadPool.globalInstance()
        if thread_pool.activeThreadCount() > 0:
            nfo("[UI] Waiting for %d background workers to finish...", thread_pool.activeThreadCount())
            thread_pool.waitForDone(2000)  # Wait up to 2 seconds max

        super().closeEvent(event)

    def _cleanup_image_loading_thread(self) -> None:
        """Clean up the image loading thread on application close."""
        try:
            if self.image_loader_worker:
                self.image_loader_worker.cancel_current_task()

            if self.image_loader_thread and self.image_loader_thread.isRunning():
                self.image_loader_thread.quit()
                if not self.image_loader_thread.wait(3000):  # Wait up to 3 seconds
                    # Double-check thread is still running before terminate
                    if self.image_loader_thread.isRunning():
                        self.image_loader_thread.terminate()
                        self.image_loader_thread.wait()  # Wait for termination

            nfo("[UI] Image loading thread cleaned up successfully")

        except Exception as e:
            nfo("[UI] Error cleaning up image loading thread: %s", e, exc_info=True)

    def resize_window(self, width: int, height: int) -> None:
        """Resize the window to specified dimensions.

        Args:
            width: New window width
            height: New window height

        """
        self.resize(width, height)
        nfo("[UI] Window resized to: %dx%d", width, height)

