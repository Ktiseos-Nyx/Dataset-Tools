#!/usr/bin/env python3
"""Demo launcher for the refactored UI proof-of-concept.

This is a standalone launcher that demonstrates the cleaner UI architecture.
You can run it directly to see the refactored UI in action!

Usage:
    python demo.py
"""

import sys
from pathlib import Path

# Fix Python import path hell - add project root to sys.path
current_file = Path(__file__).resolve()
poc_dir = current_file.parent
ui_dir = poc_dir.parent
dataset_tools_dir = ui_dir.parent
project_root = dataset_tools_dir.parent

# Add to path if not already there
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt6 import QtWidgets as Qw

# Now import our modules
from dataset_tools.ui.refactored_ui_poc.main_window import MainWindow


def main():
    """Launch the refactored UI demo."""
    # Create Qt application
    app = Qw.QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Dataset Tools - Refactored UI POC")
    app.setOrganizationName("EarthAndDuskMedia")

    # Create and show main window
    window = MainWindow()

    # Optional: Apply a basic stylesheet for better appearance
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
        QPushButton:pressed {
            background-color: #1A1A1A;
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
        QSplitter::handle {
            background-color: #4A4A4A;
        }
        QSplitter::handle:hover {
            background-color: #6A6A6A;
        }
    """)

    window.show()

    # Load some demo files if test files directory exists
    test_dir = Path(__file__).parent.parent.parent.parent.parent / "Metadata Samples" / "sample_workflows" / "image_test_cases"
    if test_dir.exists():
        # Get first few image files
        image_files = list(test_dir.glob("*.png"))[:20]
        if image_files:
            window.file_panel.set_files([str(f) for f in image_files], str(test_dir))
            window.statusBar().showMessage(f"Loaded {len(image_files)} demo files", 3000)

    # Print helpful info
    print("\n" + "="*60)
    print("REFACTORED UI PROOF-OF-CONCEPT DEMO")
    print("="*60)
    print("\nKey Architecture Improvements:")
    print("  ✓ Proper OOP encapsulation (panels are classes)")
    print("  ✓ Type-safe composition (no dynamic attributes)")
    print("  ✓ Better separation of concerns")
    print("  ✓ Self-contained, testable components")
    print("  ✓ Uses QMainWindow features (menu bar, status bar)")
    print("\nCompare to current implementation:")
    print("  OLD: main_window.positive_prompt_box = QTextEdit()")
    print("  NEW: self.metadata_panel.positive_box")
    print("\nThe visual appearance is the same,")
    print("but the code structure is much cleaner!")
    print("="*60 + "\n")

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
