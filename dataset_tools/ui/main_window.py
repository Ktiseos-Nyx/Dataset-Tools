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

from PyQt6 import QtCore, QtGui
from PyQt6 import QtWidgets as Qw
from PyQt6.QtCore import QSettings, QTimer

# from PyQt6.QtWidgets import QApplication
from ..correct_types import EmptyField  # pylint: disable=relative-beyond-top-level
from ..correct_types import (
    ExtensionType as Ext,
)  # pylint: disable=relative-beyond-top-level
from ..logger import debug_monitor  # pylint: disable=relative-beyond-top-level
from ..logger import info_monitor as nfo  # pylint: disable=relative-beyond-top-level
from ..metadata_parser import (
    parse_metadata,
)  # pylint: disable=relative-beyond-top-level
from ..widgets import (
    FileLoader,  # pylint: disable=relative-beyond-top-level
    FileLoadResult,
)
from .dialogs import (
    AboutDialog,  # pylint: disable=relative-beyond-top-level
    SettingsDialog,
)
from .managers import (
    LayoutManager,  # pylint: disable=relative-beyond-top-level
    MenuManager,  # pylint: disable=relative-beyond-top-level
    MetadataDisplayManager,  # pylint: disable=relative-beyond-top-level
    ThemeManager,  # pylint: disable=relative-beyond-top-level
)

# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_WINDOW_SIZE = (1024, 768)
STATUS_MESSAGE_TIMEOUT = 3000
DATETIME_UPDATE_INTERVAL = 1000

ORGANIZATION_NAME = "EarthAndDuskMedia"
APPLICATION_NAME = "DatasetViewer"


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

    def _initialize_managers(self) -> None:
        """Initialize UI and functionality managers."""
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

        # Apply saved theme
        self.theme_manager.apply_saved_theme()

        # Setup layout
        self.layout_manager.setup_layout()

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
        return self.settings.value("lastFolderPath", os.path.expanduser("~"))

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
        # Combine and sort all files
        all_files = result.images + result.texts + result.models
        self.current_files_in_list = sorted(list(set(all_files)))

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

        # Sort and repopulate
        self.current_files_in_list.sort()
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
            folder_name = (
                Path(self.current_folder).name if self.current_folder else "Unknown Folder"
            )
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
            return {
                EmptyField.PLACEHOLDER.value: {
                    "Error": "Cannot load metadata, folder/file name missing."
                }
            }

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
        """Display an image in the preview panel.

        Args:
            image_file_path: Path to the image file

        """
        nfo("[UI] Loading image for preview: '%s'", image_file_path)

        try:
            # Clear previous pixmap to free memory
            if hasattr(self, "image_preview"):
                self.image_preview.setPixmap(None)
            pixmap = QtGui.QPixmap(image_file_path)

            if pixmap.isNull():
                nfo("[UI] Failed to load image: '%s'", image_file_path)
            else:
                # Scale down large images to save memory
                max_preview_size = 1024
                if pixmap.width() > max_preview_size or pixmap.height() > max_preview_size:
                    pixmap = pixmap.scaled(
                        max_preview_size, max_preview_size,
                        QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                        QtCore.Qt.TransformationMode.SmoothTransformation
                    )
                nfo(
                    "[UI] Image loaded successfully: %dx%d",
                    pixmap.width(),
                    pixmap.height(),
                )
                if hasattr(self, "image_preview"):
                    self.image_preview.setPixmap(pixmap)

        except Exception as e:
            nfo(
                "[UI] Exception loading image '%s': %s",
                image_file_path,
                e,
                exc_info=True,
            )
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
        current_theme = self.settings.value("theme", "dark_teal.xml")
        dialog = SettingsDialog(self, current_theme_xml=current_theme)
        dialog.exec()

    def show_about_dialog(self) -> None:
        """Show the about dialog."""
        dialog = AboutDialog(self)
        dialog.exec()

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

        super().closeEvent(event)

    def resize_window(self, width: int, height: int) -> None:
        """Resize the window to specified dimensions.

        Args:
            width: New window width
            height: New window height

        """
        self.resize(width, height)
        nfo("[UI] Window resized to: %dx%d", width, height)
