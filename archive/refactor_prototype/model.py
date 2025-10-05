# refactor_prototype/model.py

import os
import json
from collections import OrderedDict
from qtpy import QtCore, QtGui
from PIL import Image, ImageOps, PngImagePlugin
from image_utils import pil_to_qpixmap

class WorkerSignals(QtCore.QObject):
    """
    Defines the signals available from a running worker thread.
    """
    finished = QtCore.Signal()
    error = QtCore.Signal(tuple)
    result = QtCore.Signal(object)
    progress = QtCore.Signal(str)  # NEW: For status updates

class ScanDirectoryWorker(QtCore.QRunnable):
    """
    Worker thread for scanning a directory.
    NOW WITH: macOS hidden file filtering and image-only detection!
    """
    def __init__(self, path):
        super(ScanDirectoryWorker, self).__init__()
        self.path = path
        self.signals = WorkerSignals()
        
        # Supported image formats
        self.valid_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')

    @QtCore.Slot()
    def run(self):
        try:
            self.signals.progress.emit(f"Scanning folder: {self.path}")
            
            # Filter out hidden files (starts with .) and non-images
            files = []
            for entry in os.scandir(self.path):
                if not entry.is_file():
                    continue
                    
                # Skip macOS hidden files and system files
                if entry.name.startswith('.') or entry.name.startswith('_'):
                    continue
                
                # Only include valid image files
                if entry.name.lower().endswith(self.valid_extensions):
                    files.append(entry.path)
            
            # Sort alphabetically for consistent display
            files.sort()
            
            self.signals.progress.emit(f"Found {len(files)} images")
            
        except Exception as e:
            self.signals.error.emit((type(e), e, e.__traceback__))
        else:
            self.signals.result.emit(files)
        finally:
            self.signals.finished.emit()

class FileItemModel(QtCore.QAbstractListModel):
    """
    A model to hold the list of file paths for a virtualized view.
    NOW WITH: Better file path to index mapping for performance!
    """
    def __init__(self, files=None, parent=None):
        super(FileItemModel, self).__init__(parent)
        self.files = files or []
        
        # NEW: Create a reverse lookup dict for O(1) path->index access
        self.path_to_index = {path: idx for idx, path in enumerate(self.files)}

    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.files[index.row()]
        return None

    def rowCount(self, index):
        return len(self.files)
    
    def get_index_for_path(self, file_path):
        """
        NEW: Fast lookup to get a QModelIndex from a file path.
        Returns None if not found.
        """
        row = self.path_to_index.get(file_path)
        if row is not None:
            return self.index(row, 0)
        return None

class ThumbnailCache:
    """
    NEW: A smart cache manager that keeps thumbnails in memory
    but doesn't let them eat all your RAM like a hungry carbuncle.
    
    Uses LRU (Least Recently Used) eviction - keeps the stuff you're
    looking at, dumps the old stuff when we hit the limit.
    """
    def __init__(self, max_size=200):
        """
        max_size: Maximum number of thumbnails to keep in memory
        (200 thumbnails ~= 50-100MB depending on size)
        """
        self.max_size = max_size
        self.cache = OrderedDict()  # Maintains insertion order
    
    def get(self, key):
        """Get a thumbnail and mark it as recently used."""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def put(self, key, value):
        """Add a thumbnail to the cache."""
        if key in self.cache:
            # Update existing entry and move to end
            self.cache.move_to_end(key)
            self.cache[key] = value
        else:
            # Add new entry
            self.cache[key] = value
            
            # Evict oldest if we're over capacity
            if len(self.cache) > self.max_size:
                # Remove the first (oldest) item
                self.cache.popitem(last=False)
    
    def clear(self):
        """Clear the entire cache."""
        self.cache.clear()
    
    def size(self):
        """Get current cache size."""
        return len(self.cache)

class ThumbnailWorker(QtCore.QRunnable):
    """Worker thread for generating a thumbnail."""
    def __init__(self, file_path, size=140):
        super(ThumbnailWorker, self).__init__()
        self.file_path = file_path
        self.size = size
        self.signals = WorkerSignals()

    @QtCore.Slot()
    def run(self):
        try:
            self.signals.progress.emit(f"Generating thumbnail: {os.path.basename(self.file_path)}")
            with Image.open(self.file_path) as img:
                img = ImageOps.exif_transpose(img)
                
                # Create thumbnail (maintains aspect ratio)
                img.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)
                
                pixmap = pil_to_qpixmap(img)

        except Exception as e:
            self.signals.error.emit((type(e), e, e.__traceback__))
            print(f"[ThumbWorker] Error for {self.file_path}: {e}")
        else:
            self.signals.result.emit(pixmap)
        finally:
            self.signals.finished.emit()

class FullImageWorker(QtCore.QRunnable):
    """Worker thread for loading a full-resolution image."""
    def __init__(self, file_path, size=1024):
        super(FullImageWorker, self).__init__()
        self.file_path = file_path
        self.size = size
        self.signals = WorkerSignals()

    @QtCore.Slot()
    def run(self):
        try:
            self.signals.progress.emit(f"Loading image: {os.path.basename(self.file_path)}")
            
            with Image.open(self.file_path) as img:
                img = ImageOps.exif_transpose(img)
                
                # Resize if it's larger than our max preview size
                if img.width > self.size or img.height > self.size:
                    img.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)
                
                pixmap = pil_to_qpixmap(img)

        except Exception as e:
            self.signals.error.emit((type(e), e, e.__traceback__))
            print(f"[FullImageWorker] Error for {self.file_path}: {e}")
        else:
            self.signals.result.emit(pixmap)
        finally:
            self.signals.finished.emit()

class MetadataWorker(QtCore.QRunnable):
    """
    Worker thread for parsing image metadata.
    """
    def __init__(self, file_path):
        super(MetadataWorker, self).__init__()
        self.file_path = file_path
        self.signals = WorkerSignals()

    @QtCore.Slot()
    def run(self):
        metadata = {}
        try:
            self.signals.progress.emit(f"Reading metadata: {os.path.basename(self.file_path)}")
            
            with Image.open(self.file_path) as img:
                # Extract all available metadata
                for key, value in img.info.items():
                    if isinstance(value, bytes):
                        try:
                            metadata[key] = value.decode('utf-8', errors='ignore')
                        except Exception:
                            metadata[key] = str(value)
                    else:
                        metadata[key] = value
                
                # ComfyUI often stores workflow as JSON string in 'prompt' or 'workflow'
                # Ensure it's parsed if it's a string that looks like JSON
                if 'prompt' in metadata and isinstance(metadata['prompt'], str):
                    try:
                        metadata['prompt'] = json.loads(metadata['prompt'])
                    except json.JSONDecodeError:
                        pass # Keep as string if not valid JSON
                if 'workflow' in metadata and isinstance(metadata['workflow'], str):
                    try:
                        metadata['workflow'] = json.loads(metadata['workflow'])
                    except json.JSONDecodeError:
                        pass # Keep as string if not valid JSON

        except Exception as e:
            self.signals.error.emit((type(e), e, e.__traceback__))
            print(f"[MetadataWorker] General error in run for {self.file_path}: {e}")
        else:
            self.signals.result.emit(metadata)
        finally:
            self.signals.finished.emit()

class MetadataSaveWorker(QtCore.QRunnable):
    """
    Worker thread for saving image metadata.
    """
    def __init__(self, file_path, new_metadata_str):
        super(MetadataSaveWorker, self).__init__()
        self.file_path = file_path
        self.new_metadata_str = new_metadata_str
        self.signals = WorkerSignals()

    @QtCore.Slot()
    def run(self):
        try:
            self.signals.progress.emit(f"Saving metadata: {os.path.basename(self.file_path)}")
            
            # Currently only supports PNG files
            if not self.file_path.lower().endswith('.png'):
                raise NotImplementedError("Metadata saving is currently only supported for PNG files.")

            with Image.open(self.file_path) as img:
                png_info = PngImagePlugin.PngInfo()
                png_info.add_text("parameters", self.new_metadata_str)
                img.save(self.file_path, pnginfo=png_info)

        except Exception as e:
            self.signals.error.emit((type(e), e, e.__traceback__))
        else:
            self.signals.result.emit(self.file_path)
        finally:
            self.signals.finished.emit()


class DataManager(QtCore.QObject):
    """
    The brain of the operation! Manages all data operations in background threads.
    Now with better progress reporting and error handling.
    """
    model_ready = QtCore.Signal(object)
    thumbnail_ready = QtCore.Signal(str, QtGui.QPixmap)
    metadata_ready = QtCore.Signal(str, dict)
    full_image_ready = QtCore.Signal(QtGui.QPixmap)
    metadata_saved = QtCore.Signal(str)
    progress_update = QtCore.Signal(str)  # NEW: For status bar updates
    error_occurred = QtCore.Signal(str)    # NEW: User-friendly error messages

    def __init__(self):
        super().__init__()
        self.thread_pool = QtCore.QThreadPool()
        print(f"[Model] DataManager initialized with {self.thread_pool.maxThreadCount()} threads")

    def scan_directory(self, path):
        print(f"[Model] Queuing directory scan for: {path}")
        worker = ScanDirectoryWorker(path)
        worker.signals.result.connect(self.on_scan_result)
        worker.signals.progress.connect(self.progress_update.emit)
        worker.signals.error.connect(self._handle_scan_error)
        self.thread_pool.start(worker)

    def on_scan_result(self, files):
        print(f"[Model] Scan complete. Found {len(files)} files. Creating model.")
        model = FileItemModel(files)
        self.model_ready.emit(model)

    def _handle_scan_error(self, error_tuple):
        exc_type, exc_value, exc_tb = error_tuple
        error_msg = f"Failed to scan directory: {str(exc_value)}"
        print(f"[Model] {error_msg}")
        self.error_occurred.emit(error_msg)

    def request_thumbnail(self, file_path):
        worker = ThumbnailWorker(file_path)
        worker.signals.result.connect(lambda pixmap, p=file_path: self.on_thumbnail_result(p, pixmap))
        worker.signals.error.connect(lambda err, p=file_path: self._handle_thumbnail_error(p, err))
        self.thread_pool.start(worker)

    def on_thumbnail_result(self, file_path, pixmap):
        self.thumbnail_ready.emit(file_path, pixmap)

    def _handle_thumbnail_error(self, file_path, error_tuple):
        exc_type, exc_value, exc_tb = error_tuple
        print(f"[Model] Error creating thumbnail for {file_path}: {exc_value}")
        # Don't spam the user with thumbnail errors, just log them

    def request_full_image(self, file_path):
        print(f"[Model] Queuing full image load for: {file_path}")
        worker = FullImageWorker(file_path)
        worker.signals.result.connect(self.full_image_ready.emit)
        worker.signals.progress.connect(self.progress_update.emit)
        worker.signals.error.connect(self._handle_image_error)
        self.thread_pool.start(worker)

    def _handle_image_error(self, error_tuple):
        exc_type, exc_value, exc_tb = error_tuple
        error_msg = f"Failed to load image: {str(exc_value)}"
        print(f"[Model] {error_msg}")
        self.error_occurred.emit(error_msg)

    def request_metadata(self, file_path):
        print(f"[Model] Metadata requested for: {file_path}")
        worker = MetadataWorker(file_path)
        worker.signals.result.connect(lambda metadata, p=file_path: self.on_metadata_result(p, metadata))
        worker.signals.progress.connect(self.progress_update.emit)
        worker.signals.error.connect(self._handle_metadata_error)
        self.thread_pool.start(worker)

    def on_metadata_result(self, file_path, metadata):
        self.metadata_ready.emit(file_path, metadata)

    def _handle_metadata_error(self, error_tuple):
        exc_type, exc_value, exc_tb = error_tuple
        error_msg = f"Failed to read metadata: {str(exc_value)}"
        print(f"[Model] {error_msg}")
        self.error_occurred.emit(error_msg)

    def save_metadata(self, file_path, new_metadata_str):
        print(f"[Model] Queuing metadata save for: {file_path}")
        worker = MetadataSaveWorker(file_path, new_metadata_str)
        worker.signals.result.connect(self.on_metadata_saved)
        worker.signals.progress.connect(self.progress_update.emit)
        worker.signals.error.connect(self._handle_save_error)
        self.thread_pool.start(worker)

    def on_metadata_saved(self, file_path):
        print(f"[Model] Metadata saved for {file_path}. Emitting signal.")
        self.metadata_saved.emit(file_path)
        self.progress_update.emit(f"Saved: {os.path.basename(file_path)}")

    def _handle_save_error(self, error_tuple):
        exc_type, exc_value, exc_tb = error_tuple
        error_msg = f"Failed to save metadata: {str(exc_value)}"
        print(f"[Model] {error_msg}")
        self.error_occurred.emit(error_msg)
