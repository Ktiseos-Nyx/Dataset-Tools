# /Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/exif_output/ui_code/ui_widgets_threaded.py

"""
This file contains an enhanced FileListWidget that uses background threads
to generate thumbnails without freezing the user interface.
"""

import os
import sys
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

# --- Thumbnail Generation Worker ---

class ThumbnailWorker(QtCore.QObject):
    """
    A worker object that runs on a separate thread to handle the heavy
    lifting of thumbnail creation.
    """
    # Signal: emits the file path and the generated QIcon
    thumbnail_ready = QtCore.pyqtSignal(str, QtGui.QIcon)
    finished = QtCore.pyqtSignal()

    def __init__(self, files_to_process: list[str], target_dir: str, thumb_size: QtCore.QSize):
        super().__init__()
        self.files_to_process = files_to_process
        self.target_dir = target_dir
        self.thumb_size = thumb_size
        self.is_running = True

    def run(self):
        """Processes the list of files to generate thumbnails."""
        for filename in self.files_to_process:
            if not self.is_running:
                break
            
            file_path = os.path.join(self.target_dir, filename)
            icon = self._create_thumbnail_icon(file_path)
            if icon:
                self.thumbnail_ready.emit(file_path, icon)
        
        self.finished.emit()

    def _create_thumbnail_icon(self, file_path: str) -> QtGui.QIcon | None:
        """
        Creates a QIcon with a scaled thumbnail from an image file.
        """
        try:
            pixmap = QtGui.QPixmap(file_path)
            if pixmap.isNull():
                return None
            
            scaled_pixmap = pixmap.scaled(
                self.thumb_size,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            return QtGui.QIcon(scaled_pixmap)
        except Exception:
            return None

    def stop(self):
        self.is_running = False

# --- Enhanced File List Widget ---

class ThreadedFileListWidget(QtWidgets.QWidget):
    """
    An enhanced version of the FileListWidget that loads thumbnails in the background.
    """
    file_selected = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_files: list[str] = []
        self._current_dir = ""
        self.thumbnail_size = QtCore.QSize(128, 128)
        self.icon_size = QtCore.QSize(132, 132)
        self.worker_thread = None
        self.worker = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setViewMode(QtWidgets.QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(self.icon_size)
        self.list_widget.setResizeMode(QtWidgets.QListWidget.ResizeMode.Adjust)
        self.list_widget.setWordWrap(True)
        layout.addWidget(self.list_widget)

    def _connect_signals(self):
        self.list_widget.currentItemChanged.connect(self._on_selection_changed)

    def set_files(self, directory: str, files: list[str]):
        """Populates the list with files and starts thumbnail generation."""
        self._current_dir = directory
        self._current_files = files

        # Stop any existing thumbnail generation thread
        self.stop_thumbnail_thread()

        self.list_widget.clear()

        # Initially populate with placeholder icons
        placeholder_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon)
        for filename in self._current_files:
            item = QtWidgets.QListWidgetItem(placeholder_icon, filename)
            # Store the full path in a user role for later lookup
            item.setData(QtCore.Qt.ItemDataRole.UserRole, os.path.join(self._current_dir, filename))
            self.list_widget.addItem(item)

        # Start background thread for thumbnail generation
        self.start_thumbnail_thread()

    def start_thumbnail_thread(self):
        self.worker_thread = QtCore.QThread()
        self.worker = ThumbnailWorker(self._current_files, self._current_dir, self.thumbnail_size)
        self.worker.moveToThread(self.worker_thread)

        self.worker.thumbnail_ready.connect(self.update_item_icon)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    def stop_thumbnail_thread(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker.stop()
            self.worker_thread.quit()
            self.worker_thread.wait()

    @QtCore.pyqtSlot(str, QtGui.QIcon)
    def update_item_icon(self, file_path: str, icon: QtGui.QIcon):
        """Slot to update an item's icon when a thumbnail is ready."""
        # Find the item corresponding to the file_path
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(QtCore.Qt.ItemDataRole.UserRole) == file_path:
                item.setIcon(icon)
                break

    def _on_selection_changed(self, current: QtWidgets.QListWidgetItem, previous: QtWidgets.QListWidgetItem):
        if current:
            # We stored the full path, but the main window expects just the filename
            self.file_selected.emit(Path(current.data(QtCore.Qt.ItemDataRole.UserRole)).name)

    def cleanup(self):
        self.stop_thumbnail_thread()


# --- Example Usage --- (for testing this file directly)

class TestMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Threaded Thumbnail Viewer Test")
        self.setGeometry(100, 100, 800, 600)

        # --- Main Widget and Layout ---
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)

        self.refresh_button = QtWidgets.QPushButton("Refresh File List")
        self.file_list = ThreadedFileListWidget()

        layout.addWidget(self.refresh_button)
        layout.addWidget(self.file_list)

        self.refresh_button.clicked.connect(self.do_refresh)
        self.file_list.file_selected.connect(lambda f: print(f"File selected: {f}"))

        self.do_refresh()

    def do_refresh(self):
        # In a real app, you'd get this from a dialog
        target_dir = "/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/exif_output"
        if not os.path.isdir(target_dir):
            print(f"Test directory not found: {target_dir}")
            return
        
        image_files = [f for f in os.listdir(target_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        self.file_list.set_files(target_dir, image_files)

    def closeEvent(self, event):
        self.file_list.cleanup()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())
