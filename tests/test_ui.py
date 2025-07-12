# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""Initial UI tests"""

import sys

from PyQt6 import QtWidgets

from dataset_tools.ui.main_window import MainWindow


# Basic test to ensure the MainWindow can be instantiated.
def test_main_window_creation(qtbot):
    """Test if the main window can be created."""
    # Create the application instance
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    # Create the main window
    window = MainWindow()

    # Add the window to qtbot to manage it
    qtbot.addWidget(window)

    # Show the window
    window.show()

    # Assert that the window is created and visible
    assert window is not None  # noqa: S101
    assert window.isVisible()  # noqa: S101

    # Assert the window title is set correctly
    assert window.windowTitle() == "Dataset Viewer"  # noqa: S101
