"""Dockable Main Window - Floating/dockable panel architecture!

This demonstrates QDockWidget - panels that can:
- Float as separate windows
- Dock to any edge (left, right, top, bottom)
- Be dragged and rearranged by the user
- Stack as tabs when docked together
- Be shown/hidden via View menu
- Save/restore their positions

This is how professional apps like Photoshop, Blender, and VS Code work!
"""

from PyQt6 import QtWidgets as Qw
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt

from dataset_tools.ui.refactored_ui_poc.file_panel import FilePanel
from dataset_tools.ui.refactored_ui_poc.image_panel import ImagePanel
from dataset_tools.ui.refactored_ui_poc.metadata_panel import MetadataPanel


class DockableMainWindow(Qw.QMainWindow):
    """Main window with dockable/floatable panels.

    This is the ULTIMATE flexible UI - users can arrange panels however they want!
    """

    def __init__(self):
        """Initialize the dockable main window."""
        super().__init__()
        self.setWindowTitle("Dataset Tools - Dockable UI POC")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize settings for persistence
        self.settings = QtCore.QSettings("EarthAndDuskMedia", "DatasetViewer_Dockable")

        # Create panels (same as before)
        self.file_panel = FilePanel(self)
        self.metadata_panel = MetadataPanel(self)
        self.image_panel = ImagePanel(self)

        # Setup UI with dockable widgets
        self._setup_dockable_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_bottom_toolbar()

        # Connect signals
        self._connect_signals()

        # Restore window state (including dock positions!)
        self._restore_window_state()

    def _setup_dockable_ui(self):
        """Setup the UI using QDockWidget for floatable panels.

        NO CENTRAL WIDGET - Pure dockable chaos! Everything can go anywhere!
        """

        # IMPORTANT: Set NO central widget - this allows docks to use the entire window!
        # QMainWindow will automatically fill the center with docks
        self.setDockNestingEnabled(True)  # Allow docks to be nested/split

        # Create DOCKABLE FILE PANEL (left side by default)
        self.file_dock = Qw.QDockWidget("File Browser", self)
        self.file_dock.setWidget(self.file_panel)
        self.file_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.file_dock)

        # Create DOCKABLE IMAGE PANEL (right/center by default - this will fill the middle!)
        self.image_dock = Qw.QDockWidget("Image Preview", self)
        self.image_dock.setWidget(self.image_panel)
        self.image_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.image_dock)

        # Create DOCKABLE METADATA PANEL (bottom by default, or tab with image)
        self.metadata_dock = Qw.QDockWidget("Metadata", self)
        self.metadata_dock.setWidget(self.metadata_panel)
        self.metadata_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.metadata_dock)

        # Set initial sizes to make image panel take most space
        self.resizeDocks([self.file_dock], [250], Qt.Orientation.Horizontal)
        self.resizeDocks([self.metadata_dock], [200], Qt.Orientation.Vertical)

        # BONUS: You can create dock widgets for settings, tools, etc!
        # Uncomment to see an example info panel:
        # self._create_info_dock()

    def _create_info_dock(self):
        """Optional: Create an info/help dock to show off tabbed docking."""
        info_widget = Qw.QTextEdit()
        info_widget.setReadOnly(True)
        info_widget.setMarkdown("""
# Dockable UI Demo

## Try these features:

1. **Drag panel titles** to move them
2. **Double-click titles** to float panels
3. **Drag to edges** to dock them
4. **Drag onto other docks** to create tabs!
5. **Close panels** and reopen from View menu
6. **Resize panels** by dragging borders

This is how professional apps work!
        """)

        self.info_dock = Qw.QDockWidget("Info & Tips", self)
        self.info_dock.setWidget(info_widget)
        self.info_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

        # Dock it to the right, then tabify it with metadata!
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.info_dock)
        self.tabifyDockWidget(self.metadata_dock, self.info_dock)

        # Make metadata the active tab by default
        self.metadata_dock.raise_()

    def _setup_menu_bar(self):
        """Setup menu bar with View menu for dock visibility."""
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

        # VIEW MENU - This is the magic for docks!
        view_menu = menubar.addMenu("&View")

        # Add toggle actions for each dock
        view_menu.addAction(self.file_dock.toggleViewAction())
        view_menu.addAction(self.image_dock.toggleViewAction())
        view_menu.addAction(self.metadata_dock.toggleViewAction())
        # Uncomment if you enabled info dock:
        # view_menu.addAction(self.info_dock.toggleViewAction())

        view_menu.addSeparator()

        # Reset layout action
        reset_action = view_menu.addAction("Reset Layout")
        reset_action.triggered.connect(self._reset_layout)

        view_menu.addSeparator()

        # Lock/unlock docks
        self.lock_action = view_menu.addAction("Lock Panels")
        self.lock_action.setCheckable(True)
        self.lock_action.triggered.connect(self._toggle_lock_docks)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = help_menu.addAction("&About Dockable UI")
        about_action.triggered.connect(self._show_about)

    def _setup_status_bar(self):
        """Setup status bar."""
        self.statusBar().showMessage("Ready - Dockable UI POC (drag panels to rearrange!)")

    def _setup_bottom_toolbar(self):
        """Add a toolbar with action buttons."""
        toolbar = self.addToolBar("Actions")
        toolbar.setMovable(True)  # Users can move the toolbar too!

        # Copy metadata action
        copy_btn = QtGui.QAction("Copy Metadata", self)
        copy_btn.setShortcut("Ctrl+Shift+C")
        copy_btn.triggered.connect(self._copy_metadata)
        toolbar.addAction(copy_btn)

        toolbar.addSeparator()

        # Settings action
        settings_btn = QtGui.QAction("Settings", self)
        settings_btn.triggered.connect(self._show_settings)
        toolbar.addAction(settings_btn)

    def _connect_signals(self):
        """Connect signals between panels."""
        self.file_panel.file_selected.connect(self._on_file_selected)
        self.file_panel.folder_open_requested.connect(self._on_open_folder)
        self.file_panel.sort_requested.connect(self._on_sort_requested)
        self.image_panel.image_clicked.connect(self._on_image_clicked)

    def _on_file_selected(self, filepath: str):
        """Handle file selection."""
        self.statusBar().showMessage(f"Loading: {filepath}")

        self.image_panel.set_image(filepath)
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
        """Load images from folder."""
        import os

        image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
        files = []

        for filename in os.listdir(folder_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in image_extensions:
                files.append(os.path.join(folder_path, filename))

        files.sort()
        self.file_panel.set_files(files, folder_path)
        self.statusBar().showMessage(f"Loaded {len(files)} files from {folder_path}", 3000)

    def _on_sort_requested(self, sort_type: str):
        """Handle sort request."""
        self.statusBar().showMessage(f"Sorting by: {sort_type}", 2000)

    def _on_image_clicked(self):
        """Handle image click."""
        self.statusBar().showMessage("Image clicked!", 1000)

    def _copy_metadata(self):
        """Copy metadata to clipboard."""
        text = self.metadata_panel.get_all_metadata_text()

        if text:
            clipboard = Qw.QApplication.clipboard()
            clipboard.setText(text)
            self.statusBar().showMessage("Metadata copied to clipboard!", 2000)
        else:
            self.statusBar().showMessage("No metadata to copy", 2000)

    def _show_settings(self):
        """Show settings dialog."""
        Qw.QMessageBox.information(
            self,
            "Settings",
            "Settings dialog would go here!\n\n"
            "Try dragging the panels around instead! 😄"
        )

    def _toggle_lock_docks(self, locked: bool):
        """Lock or unlock dock panels."""
        features = Qw.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures if locked else (
            Qw.QDockWidget.DockWidgetFeature.DockWidgetClosable |
            Qw.QDockWidget.DockWidgetFeature.DockWidgetMovable |
            Qw.QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        self.file_dock.setFeatures(features)
        self.image_dock.setFeatures(features)
        self.metadata_dock.setFeatures(features)
        # Uncomment if info dock enabled:
        # self.info_dock.setFeatures(features)

        status = "locked" if locked else "unlocked"
        self.statusBar().showMessage(f"Panels {status}", 2000)

    def _reset_layout(self):
        """Reset dock layout to defaults."""
        # Remove all docks
        self.removeDockWidget(self.file_dock)
        self.removeDockWidget(self.image_dock)
        self.removeDockWidget(self.metadata_dock)

        # Re-add in default positions
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.file_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.image_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.metadata_dock)

        # Show all docks
        self.file_dock.show()
        self.image_dock.show()
        self.metadata_dock.show()

        self.statusBar().showMessage("Layout reset to defaults", 2000)

    def _show_about(self):
        """Show about dialog."""
        Qw.QMessageBox.about(
            self,
            "About Dockable UI POC",
            "Dataset Tools - Dockable UI Proof of Concept\n\n"
            "This demonstrates QDockWidget features:\n\n"
            "✓ Drag panel titles to move them\n"
            "✓ Double-click titles to float panels\n"
            "✓ Drag to window edges to dock\n"
            "✓ Drag onto other docks to create tabs\n"
            "✓ Close/reopen panels from View menu\n"
            "✓ Resize panels by dragging borders\n"
            "✓ Layout is saved automatically!\n\n"
            "This is how professional apps work! 🚀"
        )

    def _get_mock_metadata(self, filepath: str) -> dict:
        """Get mock metadata for demo."""
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
        """Restore window geometry and dock layout."""
        # Restore window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Restore dock state (positions, sizes, floating, etc.)
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        """Save window state before closing."""
        # Save window geometry
        self.settings.setValue("geometry", self.saveGeometry())

        # Save complete dock state (THIS IS THE MAGIC!)
        self.settings.setValue("windowState", self.saveState())

        super().closeEvent(event)
