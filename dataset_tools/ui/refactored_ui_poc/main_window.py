"""Refactored Main Window - Clean OOP architecture demonstration.

This is a proof-of-concept showing how the UI could be structured more cleanly
using proper OOP principles instead of procedural widget creation.

Key improvements over current implementation:
- Real class composition instead of dynamic attribute assignment
- Each panel is self-contained and testable independently
- Type-safe (IDE autocomplete works!)
- Cleaner signal/slot connections
- Separation of concerns (each panel manages its own logic)
"""

from PyQt6 import QtWidgets as Qw
from PyQt6 import QtCore

from dataset_tools.ui.refactored_ui_poc.file_panel import FilePanel
from dataset_tools.ui.refactored_ui_poc.image_panel import ImagePanel
from dataset_tools.ui.refactored_ui_poc.metadata_panel import MetadataPanel


class MainWindow(Qw.QMainWindow):
    """Main application window with clean architecture.

    Instead of:
        main_window.positive_prompt_box = Qw.QTextEdit()  # Dynamic attribute!

    We have:
        self.metadata_panel = MetadataPanel()  # Real composition!
        self.metadata_panel.positive_box  # Type-safe access!
    """

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle("Dataset Tools - Refactored UI POC")
        self.setGeometry(100, 100, 1024, 768)

        # Initialize settings for persistence
        self.settings = QtCore.QSettings("EarthAndDuskMedia", "DatasetViewer_POC")

        # Create panels using proper composition
        self.file_panel = FilePanel(self)
        self.metadata_panel = MetadataPanel(self)
        self.image_panel = ImagePanel(self)

        # Setup UI layout
        self._setup_central_widget()
        self._setup_menu_bar()
        self._setup_status_bar()

        # Connect signals between panels
        self._connect_signals()

        # Restore window state
        self._restore_window_state()

    def _setup_central_widget(self):
        """Setup the central widget layout using splitters."""
        # Central widget container
        central_widget = Qw.QWidget()
        self.setCentralWidget(central_widget)

        # Main vertical layout
        main_layout = Qw.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # Horizontal splitter for main content area
        self.main_splitter = Qw.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Add file panel to left
        self.main_splitter.addWidget(self.file_panel)

        # Create right side (metadata + image)
        right_side = Qw.QWidget()
        right_layout = Qw.QHBoxLayout(right_side)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for metadata and image
        self.metadata_image_splitter = Qw.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.metadata_image_splitter.addWidget(self.metadata_panel)
        self.metadata_image_splitter.addWidget(self.image_panel)

        right_layout.addWidget(self.metadata_image_splitter)
        self.main_splitter.addWidget(right_side)

        main_layout.addWidget(self.main_splitter, stretch=1)

        # Bottom action buttons
        bottom_bar = self._create_bottom_bar()
        main_layout.addWidget(bottom_bar)

        # Set initial splitter sizes
        self.main_splitter.setSizes([256, 768])  # 1:3 ratio
        self.metadata_image_splitter.setSizes([384, 384])  # Equal split

    def _create_bottom_bar(self) -> Qw.QWidget:
        """Create the bottom action button bar.

        Returns:
            Widget containing action buttons
        """
        bottom_bar = Qw.QWidget()
        layout = Qw.QHBoxLayout(bottom_bar)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.addStretch(1)

        # Copy metadata button
        self.copy_btn = Qw.QPushButton("Copy All Metadata")
        self.copy_btn.clicked.connect(self._copy_metadata)
        layout.addWidget(self.copy_btn)

        # Settings button (placeholder)
        self.settings_btn = Qw.QPushButton("Settings")
        self.settings_btn.clicked.connect(self._show_settings)
        layout.addWidget(self.settings_btn)

        # Exit button
        self.exit_btn = Qw.QPushButton("Exit Application")
        self.exit_btn.clicked.connect(self.close)
        layout.addWidget(self.exit_btn)

        layout.addStretch(1)
        return bottom_bar

    def _setup_menu_bar(self):
        """Setup the menu bar (using QMainWindow's built-in feature!)."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = file_menu.addAction("&Open Folder...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_folder)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        copy_action = edit_menu.addAction("&Copy Metadata")
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self._copy_metadata)

        # View menu
        view_menu = menubar.addMenu("&View")

        refresh_action = view_menu.addAction("&Refresh")
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_current)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self._show_about)

    def _setup_status_bar(self):
        """Setup the status bar (using QMainWindow's built-in feature!)."""
        self.statusBar().showMessage("Ready - Refactored UI POC")

    def _connect_signals(self):
        """Connect signals between panels and main window."""
        # File panel signals
        self.file_panel.file_selected.connect(self._on_file_selected)
        self.file_panel.folder_open_requested.connect(self._on_open_folder)
        self.file_panel.sort_requested.connect(self._on_sort_requested)

        # Image panel signals
        self.image_panel.image_clicked.connect(self._on_image_clicked)

    def _on_file_selected(self, filepath: str):
        """Handle file selection from file panel.

        Args:
            filepath: Selected file path
        """
        self.statusBar().showMessage(f"Loading: {filepath}")

        # Load image
        self.image_panel.set_image(filepath)

        # Load metadata (mock for now)
        mock_metadata = self._get_mock_metadata(filepath)
        self.metadata_panel.update_metadata(mock_metadata)

        self.statusBar().showMessage(f"Loaded: {filepath}", 3000)

    def _on_open_folder(self):
        """Handle open folder request."""
        folder = Qw.QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            "",
            Qw.QFileDialog.Option.ShowDirsOnly
        )

        if folder:
            self._load_folder(folder)

    def _load_folder(self, folder_path: str):
        """Load all images from a folder.

        Args:
            folder_path: Path to folder to load
        """
        import os

        # Get all image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
        files = []

        for filename in os.listdir(folder_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in image_extensions:
                files.append(os.path.join(folder_path, filename))

        # Update file panel
        files.sort()
        self.file_panel.set_files(files, folder_path)

        self.statusBar().showMessage(f"Loaded {len(files)} files from {folder_path}", 3000)

    def _on_sort_requested(self, sort_type: str):
        """Handle sort request from file panel.

        Args:
            sort_type: Type of sort requested
        """
        self.statusBar().showMessage(f"Sorting by: {sort_type}", 2000)
        # TODO: Implement actual sorting logic

    def _on_image_clicked(self):
        """Handle image click."""
        self.statusBar().showMessage("Image clicked!", 1000)

    def _copy_metadata(self):
        """Copy all metadata to clipboard."""
        text = self.metadata_panel.get_all_metadata_text()

        if text:
            clipboard = Qw.QApplication.clipboard()
            clipboard.setText(text)
            self.statusBar().showMessage("Metadata copied to clipboard!", 2000)
        else:
            self.statusBar().showMessage("No metadata to copy", 2000)

    def _show_settings(self):
        """Show settings dialog (placeholder)."""
        Qw.QMessageBox.information(
            self,
            "Settings",
            "Settings dialog would go here!\n\nThis is just a POC demonstrating clean architecture."
        )

    def _refresh_current(self):
        """Refresh current view."""
        selected = self.file_panel.get_selected_file()
        if selected:
            self._on_file_selected(selected)
        self.statusBar().showMessage("Refreshed", 1000)

    def _show_about(self):
        """Show about dialog."""
        Qw.QMessageBox.about(
            self,
            "About Refactored UI POC",
            "Dataset Tools - Refactored UI Proof of Concept\n\n"
            "This demonstrates a cleaner, more Pythonic architecture:\n\n"
            "✓ Proper OOP encapsulation\n"
            "✓ Type-safe composition\n"
            "✓ Better separation of concerns\n"
            "✓ Self-contained, testable components\n"
            "✓ Uses QMainWindow features properly\n\n"
            "Same visual appearance, better code structure!"
        )

    def _get_mock_metadata(self, filepath: str) -> dict:
        """Get mock metadata for demonstration.

        Args:
            filepath: File path (used to generate unique mock data)

        Returns:
            Dict with metadata fields
        """
        import os
        filename = os.path.basename(filepath)

        return {
            'positive': f"1girl, portrait, detailed, masterpiece\n\n(Mock data for {filename})",
            'negative': "low quality, blurry, artifacts",
            'details': (
                f"File: {filename}\n"
                "Steps: 30\n"
                "Sampler: DPM++ 2M Karras\n"
                "CFG scale: 7\n"
                "Seed: 123456789\n"
                "Size: 512x768\n"
                "Model: sd_xl_base_1.0\n"
                "Parser: ComfyUI\n\n"
                "(This is mock data for the POC)"
            )
        }

    def _restore_window_state(self):
        """Restore window geometry and splitter sizes from settings."""
        # Restore window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Restore splitter sizes
        main_splitter_sizes = self.settings.value("mainSplitterSizes")
        if main_splitter_sizes:
            self.main_splitter.setSizes([int(s) for s in main_splitter_sizes])

        meta_img_splitter_sizes = self.settings.value("metaImageSplitterSizes")
        if meta_img_splitter_sizes:
            self.metadata_image_splitter.setSizes([int(s) for s in meta_img_splitter_sizes])

    def closeEvent(self, event):
        """Save window state before closing."""
        # Save window geometry
        self.settings.setValue("geometry", self.saveGeometry())

        # Save splitter sizes
        self.settings.setValue("mainSplitterSizes", self.main_splitter.sizes())
        self.settings.setValue("metaImageSplitterSizes", self.metadata_image_splitter.sizes())

        super().closeEvent(event)
