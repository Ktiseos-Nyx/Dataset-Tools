# V2 Development Plan

This document outlines the features, architectural improvements, and quality-of-life changes for the next version of the application.

## 1. Core Features

Based on user feedback, the following features are prioritized for the 1.0 release.

-   **P0: Metadata Editing:** Implement functionality to edit image metadata fields and save the changes back to the file.
-   **P0: Civitai API Integration:** Implement the "Civitai Lookup" feature to fetch and display model information from the Civitai API.
-   **P1: Search and Filter:** Add a search bar to filter the gallery by filename and eventually by metadata content.

## 2. Code Structure & Refactoring

This section outlines long-term architectural goals to ensure the application remains maintainable and extensible.

-   **Pluggable Theme System:** Design a system that allows users to easily install and apply their own custom themes (e.g., by dropping .qss or .xml files into a specific folder).
-   **Pluggable Metadata Rules:** Create a plugin system for metadata parsing. This would allow the community to contribute parsers for different image generation tools and formats, making the application far more versatile.

## 3. Quality of Life (QoL) Improvements

-   **Status Bar:** Re-implement the status bar from the old version to provide users with feedback on background processes and UI states.
-   **Layout Sizing/High-DPI:** Add settings to control layout sizing to ensure the application is usable on a wide range of display resolutions (e.g., from standard monitors to 5k Retina screens).
-   **Remember Last Folder:** The application should remember and optionally re-open the last used folder on startup.
-   **Keyboard Shortcuts:** Implement keyboard shortcuts for common actions to improve workflow efficiency.
-   **Garbage Collection:** Implement an explicit garbage collection or memory management strategy to release memory used by thumbnails and other resources, preventing high memory usage over long sessions.

## 4. UI/UX Improvements

-   **Custom Menu Bar:** Implement a custom, in-app menu bar instead of relying on the native OS menu bar for a consistent cross-platform look and feel.
-   **Advanced Layout Switching:** In addition to grid/list views, add the ability to swap the main panels between a horizontal and vertical orientation.

## 5. Architectural Goals (Re-prioritized)

-   **Advanced Metadata Parsing:** This is a high-priority task. Re-implement the rule-based metadata parsing system from the old version. The goal is to move beyond the current JSON dump and intelligently extract and display specific, relevant data in the correct UI fields.

## 6. Performance: Implement Virtualized Gallery

To solve the slow performance on large folders, we will replace the current gallery implementation (which creates a widget for every file) with a true virtualized view using Qt's Model/View architecture. This is the standard approach for high-performance lists.

-   **1. Create `FileItemModel`:**
    -   Create a new class in `model.py` that inherits from `QAbstractListModel`.
    -   This model will manage the list of file paths as pure data, without creating any widgets.

-   **2. Create `ThumbnailDelegate`:**
    -   Create a new class in `views.py` that inherits from `QStyledItemDelegate`.
    -   This delegate will be responsible for *painting* each item in the list (the thumbnail and filename) on demand.
    -   It will not create individual `ThumbnailWidget` instances, which is the key to performance.

-   **3. Replace Gallery with `QListView`:**
    -   In `MainWindow` (`views.py`), remove the current `QScrollArea` and `FlowLayout`.
    -   Replace them with a `QListView`.
    -   Set the `FileItemModel` as the view's model.
    -   Set the `ThumbnailDelegate` as the view's item delegate.
