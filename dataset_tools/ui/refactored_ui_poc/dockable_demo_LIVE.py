#!/usr/bin/env python3
"""LIVE Dockable UI Demo - NOW WITH REAL METADATA! 🚀

This connects the dockable POC to the ACTUAL metadata engine!
See how the refactored UI handles real ComfyUI/A1111/FLUX workflows!

Usage:
    python dockable_demo_LIVE.py
"""

import sys
from pathlib import Path

# Fix Python import path
current_file = Path(__file__).resolve()
poc_dir = current_file.parent
ui_dir = poc_dir.parent
dataset_tools_dir = ui_dir.parent
project_root = dataset_tools_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt6 import QtWidgets as Qw
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt

# Import the POC panels
from dataset_tools.ui.refactored_ui_poc.file_panel import FilePanel
from dataset_tools.ui.refactored_ui_poc.image_panel import ImagePanel
from dataset_tools.ui.refactored_ui_poc.metadata_panel import MetadataPanel
from dataset_tools.ui.refactored_ui_poc.thumbnail_panel import ThumbnailPanel
from dataset_tools.ui.refactored_ui_poc.file_tree_panel import FileTreePanel

# Import REAL metadata engine! 🔥
from dataset_tools.metadata_parser import parse_metadata
from dataset_tools.correct_types import UpField, DownField


class LiveDockableWindow(Qw.QMainWindow):
    """Dockable UI with REAL metadata integration!"""

    def __init__(self):
        """Initialize with real metadata support."""
        super().__init__()
        self.setWindowTitle("Dataset Tools - LIVE Dockable POC 🔥")
        self.setGeometry(100, 100, 1400, 900)

        # Settings
        self.settings = QtCore.QSettings("EarthAndDuskMedia", "DatasetViewer_LiveDockable")

        # Create panels
        self.file_panel = FilePanel(self)
        self.metadata_panel = MetadataPanel(self)
        self.image_panel = ImagePanel(self)
        self.thumbnail_panel = ThumbnailPanel(self)
        self.file_tree_panel = FileTreePanel(self)

        # Setup dockable UI
        self._setup_docks()
        self._setup_menu()
        self._setup_fake_menubar()  # FAKE MENUBAR FOR ANTI-MACOS FREEDOM!
        self._setup_statusbar()
        self._connect_signals()

        # Current file tracking
        self.current_file = None
        self.current_directory = None
        self.current_image_files = []  # Track loaded files for thumbnail grid

        # Optional docks (can be shown/hidden)
        self.thumbnail_dock = None
        self.file_tree_dock = None

    def closeEvent(self, event):
        """Handle window close - clean up properly."""
        try:
            # Disconnect signals to prevent issues during cleanup
            self.file_panel.file_selected.disconnect()
            self.thumbnail_panel.thumbnail_selected.disconnect()
            self.file_tree_panel.file_selected.disconnect()

            # Clear images to release pixmaps
            self.image_panel.clear_image()
            self.thumbnail_panel.clear_thumbnails()
            self.file_tree_panel.clear_tree()
        except Exception:
            pass  # Ignore cleanup errors

        # Accept the close event
        event.accept()

    def _setup_docks(self):
        """Setup dockable panels."""
        self.setDockNestingEnabled(True)

        # File browser (left)
        self.file_dock = Qw.QDockWidget("📁 File Browser", self)
        self.file_dock.setWidget(self.file_panel)
        self.file_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.file_dock)

        # Image preview (center/right)
        self.image_dock = Qw.QDockWidget("🖼️ Image Preview", self)
        self.image_dock.setWidget(self.image_panel)
        self.image_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.image_dock)

        # Metadata (bottom or tabbed)
        self.metadata_dock = Qw.QDockWidget("📋 Metadata (LIVE!)", self)
        self.metadata_dock.setWidget(self.metadata_panel)
        self.metadata_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.metadata_dock)

        # Set initial sizes
        self.resizeDocks([self.file_dock], [300], Qt.Orientation.Horizontal)
        self.resizeDocks([self.metadata_dock], [250], Qt.Orientation.Vertical)

    def _setup_menu(self):
        """Setup menu bar (real macOS menubar for the normies)."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        open_action = file_menu.addAction("📂 Open Directory...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_directory)
        file_menu.addSeparator()
        quit_action = file_menu.addAction("❌ Quit")
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.file_dock.toggleViewAction())
        view_menu.addAction(self.image_dock.toggleViewAction())
        view_menu.addAction(self.metadata_dock.toggleViewAction())
        view_menu.addSeparator()
        # Extra docks
        show_thumbnails_action = view_menu.addAction("🖼️ Show Thumbnail Grid")
        show_thumbnails_action.triggered.connect(self._show_thumbnail_dock)
        show_tree_action = view_menu.addAction("🌳 Show File Tree")
        show_tree_action.triggered.connect(self._show_file_tree_dock)

    def _setup_fake_menubar(self):
        """Setup FAKE menubar toolbar (for anti-macOS freedom fighters!)."""
        # Create toolbar
        toolbar = self.addToolBar("Fake Menubar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2A2A2A;
                border-bottom: 1px solid #4A4A4A;
                spacing: 5px;
                padding: 3px;
            }
            QToolButton {
                background-color: #2A2A2A;
                color: #E0E0E0;
                border: none;
                padding: 5px 10px;
                font-size: 10pt;
            }
            QToolButton:hover {
                background-color: #3A3A3A;
            }
            QToolButton::menu-indicator {
                image: none;
                width: 0px;
            }
        """)

        # FILE MENU BUTTON
        file_btn = Qw.QToolButton()
        file_btn.setText("📂 File")
        file_btn.setPopupMode(Qw.QToolButton.ToolButtonPopupMode.InstantPopup)

        file_menu = Qw.QMenu(file_btn)
        file_menu.addAction("📂 Open Directory...", self._open_directory)
        file_menu.addSeparator()
        file_menu.addAction("❌ Quit", self.close)
        file_btn.setMenu(file_menu)

        toolbar.addWidget(file_btn)

        # VIEW MENU BUTTON
        view_btn = Qw.QToolButton()
        view_btn.setText("👁️ View")
        view_btn.setPopupMode(Qw.QToolButton.ToolButtonPopupMode.InstantPopup)

        view_menu = Qw.QMenu(view_btn)
        view_menu.addAction(self.file_dock.toggleViewAction())
        view_menu.addAction(self.image_dock.toggleViewAction())
        view_menu.addAction(self.metadata_dock.toggleViewAction())
        view_menu.addSeparator()
        view_menu.addAction("🖼️ Show Thumbnail Grid", self._show_thumbnail_dock)
        view_menu.addAction("🌳 Show File Tree", self._show_file_tree_dock)
        view_btn.setMenu(view_menu)

        toolbar.addWidget(view_btn)

        # Spacer to push everything left
        spacer = Qw.QWidget()
        spacer.setSizePolicy(Qw.QSizePolicy.Policy.Expanding, Qw.QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)

        # ANTI-MACOS FREEDOM LABEL
        freedom_label = Qw.QLabel("💪 FAKE MENUBAR = FREEDOM")
        freedom_label.setStyleSheet("QLabel { color: #888; font-size: 9pt; padding-right: 10px; }")
        toolbar.addWidget(freedom_label)

    def _setup_statusbar(self):
        """Setup status bar."""
        self.statusBar().showMessage("Ready! Open a directory to get started...")

    def _connect_signals(self):
        """Connect panel signals."""
        self.file_panel.file_selected.connect(self._on_file_selected)
        self.file_panel.folder_open_requested.connect(self._open_directory)
        self.thumbnail_panel.thumbnail_selected.connect(self._on_file_selected)
        self.file_tree_panel.file_selected.connect(self._on_file_selected)

    def _open_directory(self):
        """Open directory dialog."""
        dir_path = Qw.QFileDialog.getExistingDirectory(
            self,
            "Select Image Directory",
            str(Path.home()),
            Qw.QFileDialog.Option.ShowDirsOnly
        )

        if dir_path:
            self._load_directory(dir_path)

    def _show_thumbnail_dock(self):
        """Show or create the thumbnail grid dock."""
        if self.thumbnail_dock is None:
            # Create the dock
            self.thumbnail_dock = Qw.QDockWidget("🖼️ Thumbnail Grid", self)
            self.thumbnail_dock.setWidget(self.thumbnail_panel)
            self.thumbnail_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

            # Add to right side initially
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.thumbnail_dock)

            # Load current images if any
            if self.current_image_files:
                self.thumbnail_panel.set_images(self.current_image_files)

            self.statusBar().showMessage("✨ Thumbnail grid opened!", 2000)
        else:
            # Just show it if it exists
            self.thumbnail_dock.show()
            self.statusBar().showMessage("✨ Thumbnail grid shown!", 2000)

    def _show_file_tree_dock(self):
        """Show or create the file tree dock."""
        if self.file_tree_dock is None:
            # Create the dock
            self.file_tree_dock = Qw.QDockWidget("🌳 File Tree", self)
            self.file_tree_dock.setWidget(self.file_tree_panel)
            self.file_tree_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

            # Add to left side initially
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.file_tree_dock)

            # Load current directory if any
            if self.current_directory:
                self.file_tree_panel.set_root_path(self.current_directory)

            self.statusBar().showMessage("✨ File tree opened!", 2000)
        else:
            # Just show it if it exists
            self.file_tree_dock.show()
            self.statusBar().showMessage("✨ File tree shown!", 2000)

    def _load_directory(self, dir_path: str):
        """Load images from directory."""
        directory = Path(dir_path)
        if not directory.exists():
            self.statusBar().showMessage(f"❌ Directory not found: {dir_path}", 5000)
            return

        # Find image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
        image_files = [
            str(f) for f in directory.iterdir()
            if f.suffix.lower() in image_extensions
        ]

        if not image_files:
            self.statusBar().showMessage(f"❌ No images found in {dir_path}", 5000)
            return

        # Load into file panel
        self.file_panel.set_files(image_files, dir_path)
        self.current_directory = dir_path
        self.current_image_files = image_files  # Store for thumbnail grid

        # Update thumbnail grid if it's open
        if self.thumbnail_dock and self.thumbnail_dock.isVisible():
            self.thumbnail_panel.set_images(image_files)

        # Update file tree if it's open
        if self.file_tree_dock and self.file_tree_dock.isVisible():
            self.file_tree_panel.set_root_path(dir_path)

        self.statusBar().showMessage(f"✅ Loaded {len(image_files)} images from {directory.name}", 3000)

    def _on_file_selected(self, filepath: str):
        """Handle file selection - LOAD REAL METADATA!"""
        print(f"\n{'='*70}")
        print(f"🔥 LOADING REAL METADATA: {Path(filepath).name}")
        print(f"{'='*70}\n")

        self.current_file = filepath
        self.statusBar().showMessage(f"Loading metadata: {Path(filepath).name}...")

        try:
            # REAL METADATA ENGINE CALL! 🚀
            metadata_dict = parse_metadata(filepath, lambda msg: self.statusBar().showMessage(msg, 1000))

            if metadata_dict:
                # Extract data for display
                display_data = self._format_metadata_for_display(metadata_dict)

                # Update panels
                self.metadata_panel.update_metadata(display_data)
                self.image_panel.set_image(filepath)

                # Show tool name in status
                tool_name = metadata_dict.get(DownField.GENERATION_DATA.value, {}).get('Tool', 'Unknown')
                self.statusBar().showMessage(f"✅ Loaded: {Path(filepath).name} | Tool: {tool_name}", 5000)

                # Print debug info
                print(f"✅ Successfully parsed metadata!")
                print(f"   Tool: {tool_name}")
                print(f"   Keys: {list(metadata_dict.keys())}")

            else:
                self.statusBar().showMessage(f"❌ No metadata found in {Path(filepath).name}", 5000)
                print(f"❌ No metadata found!")

        except Exception as e:
            error_msg = f"❌ Error parsing metadata: {e}"
            self.statusBar().showMessage(error_msg, 5000)
            print(f"\n{error_msg}\n")
            import traceback
            traceback.print_exc()

    def _format_metadata_for_display(self, metadata_dict: dict) -> dict:
        """Format real metadata for the POC panel."""
        # Get prompt data
        prompts = metadata_dict.get(UpField.PROMPT.value, {})
        positive = prompts.get('Positive', '')
        negative = prompts.get('Negative', '')

        # Get parameters (from DownField, not UpField!)
        params = metadata_dict.get(DownField.GENERATION_DATA.value, {})

        # Format parameters as readable text
        param_lines = []
        for key, value in sorted(params.items()):
            if isinstance(value, dict):
                param_lines.append(f"{key}:")
                for sub_key, sub_value in sorted(value.items()):
                    param_lines.append(f"  {sub_key}: {sub_value}")
            elif isinstance(value, list):
                param_lines.append(f"{key}: {len(value)} items")
            else:
                param_lines.append(f"{key}: {value}")

        details = "\n".join(param_lines)

        return {
            'positive': positive,
            'negative': negative,
            'details': details
        }


def main():
    """Launch the LIVE dockable UI demo!"""
    app = Qw.QApplication(sys.argv)

    app.setApplicationName("Dataset Tools - LIVE Dockable POC")
    app.setOrganizationName("EarthAndDuskMedia")

    # Create window
    window = LiveDockableWindow()

    # Apply dark theme
    window.setStyleSheet("""
        QMainWindow {
            background-color: #1A1A1A;
        }
        QWidget {
            background-color: #1A1A1A;
            color: #E0E0E0;
            font-family: 'Segoe UI', sans-serif;
            font-size: 10pt;
        }
        QPushButton {
            background-color: #2A2A2A;
            border: 1px solid #4A4A4A;
            border-radius: 4px;
            padding: 6px 12px;
            color: #E0E0E0;
        }
        QPushButton:hover {
            background-color: #3A3A3A;
            border-color: #6A6A6A;
        }
        QTextEdit, QListWidget {
            background-color: #2A2A2A;
            border: 1px solid #4A4A4A;
            border-radius: 4px;
            padding: 5px;
            color: #E0E0E0;
        }
        QLabel {
            color: #E0E0E0;
            background-color: transparent;
        }
        QDockWidget {
            color: #E0E0E0;
        }
        QDockWidget::title {
            background-color: #2A2A2A;
            border: 1px solid #4A4A4A;
            padding: 6px;
            text-align: left;
        }
        QMenuBar {
            background-color: #2A2A2A;
            color: #E0E0E0;
            border-bottom: 1px solid #4A4A4A;
        }
        QMenuBar::item:selected {
            background-color: #3A3A3A;
        }
        QMenu {
            background-color: #2A2A2A;
            border: 1px solid #4A4A4A;
            color: #E0E0E0;
        }
        QMenu::item:selected {
            background-color: #3A3A3A;
        }
        QStatusBar {
            background-color: #2A2A2A;
            color: #E0E0E0;
            border-top: 1px solid #4A4A4A;
        }
    """)

    window.show()

    # Try to load test directory automatically
    test_dir = Path.home() / "Downloads" / "Metadata Samples" / "images_1760758931015"
    if test_dir.exists():
        window._load_directory(str(test_dir))
        print(f"\n✅ Auto-loaded test directory: {test_dir}")

    # Print instructions
    print("\n" + "="*70)
    print("🔥 LIVE DOCKABLE UI - NOW WITH REAL METADATA! 🔥")
    print("="*70)
    print("\n✨ Features:")
    print("  • Real metadata parsing from ComfyUI/A1111/FLUX workflows")
    print("  • Drag panels to rearrange")
    print("  • Float panels as separate windows")
    print("  • Tab panels together")
    print("  • Full metadata engine integration!")
    print("\n📂 Use File → Open Directory to load your images")
    print("="*70 + "\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
