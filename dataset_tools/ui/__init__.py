# dataset_tools/ui/__init__.py

# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: GPL-3.0

"""
Modern modular UI system for Dataset Tools.

This package provides a clean, maintainable UI architecture with
separated concerns for layout, dialogs, widgets, and managers.
"""

# Import main window for easy access
from .main_window import MainWindow

# Import key components for advanced usage
from .dialogs import AboutDialog, SettingsDialog
from .managers import LayoutManager, MenuManager, MetadataDisplayManager

__all__ = [
    "MainWindow",
    "AboutDialog",
    "SettingsDialog",
    "LayoutManager",
    "MenuManager",
    "MetadataDisplayManager",
]
