#!/usr/bin/env python3
"""Dockable UI Demo - Floating/draggable panel demonstration!

This shows QDockWidget in action - panels that can be:
- Floated as separate windows
- Docked to any edge
- Dragged and rearranged
- Stacked as tabs
- Hidden/shown from menu

Usage:
    python dockable_demo.py
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

from dataset_tools.ui.refactored_ui_poc.dockable_main_window import DockableMainWindow


def main():
    """Launch the dockable UI demo."""
    app = Qw.QApplication(sys.argv)

    app.setApplicationName("Dataset Tools - Dockable UI POC")
    app.setOrganizationName("EarthAndDuskMedia")

    # Create window
    window = DockableMainWindow()

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
        QComboBox {
            background-color: #2A2A2A;
            border: 1px solid #4A4A4A;
            border-radius: 4px;
            padding: 5px;
            color: #E0E0E0;
        }
        QDockWidget {
            color: #E0E0E0;
            titlebar-close-icon: url(none);
            titlebar-normal-icon: url(none);
        }
        QDockWidget::title {
            background-color: #2A2A2A;
            border: 1px solid #4A4A4A;
            padding: 6px;
            text-align: left;
        }
        QDockWidget::close-button, QDockWidget::float-button {
            background-color: #3A3A3A;
            border: 1px solid #4A4A4A;
            border-radius: 2px;
        }
        QDockWidget::close-button:hover, QDockWidget::float-button:hover {
            background-color: #4A4A4A;
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
        QToolBar {
            background-color: #2A2A2A;
            border: 1px solid #4A4A4A;
            spacing: 5px;
            padding: 3px;
        }
    """)

    window.show()

    # Load demo files if available
    test_dir = Path(__file__).parent.parent.parent.parent.parent / "Metadata Samples" / "sample_workflows" / "image_test_cases"
    if test_dir.exists():
        image_files = list(test_dir.glob("*.png"))[:20]
        if image_files:
            window.file_panel.set_files([str(f) for f in image_files], str(test_dir))
            window.statusBar().showMessage(f"Loaded {len(image_files)} demo files", 3000)

    # Print helpful info
    print("\n" + "="*70)
    print("DOCKABLE UI PROOF-OF-CONCEPT DEMO")
    print("="*70)
    print("\n✨ Try these awesome features:")
    print("  1. Drag panel titles to move them around")
    print("  2. Double-click titles to float panels as separate windows")
    print("  3. Drag panels to window edges to dock them")
    print("  4. Drag panels onto other docks to create TABS!")
    print("  5. Close panels and reopen from View menu")
    print("  6. Lock panels with View → Lock Panels")
    print("  7. Reset layout with View → Reset Layout")
    print("  8. Your layout is SAVED automatically when you close!")
    print("\n🎨 This is how professional apps like Photoshop work!")
    print("="*70 + "\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
