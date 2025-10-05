# refactor_prototype/model.py

import os
import json
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

class ScanDirectoryWorker(QtCore.QRunnable):
    """
    Worker thread for scanning a directory.
    """
    def __init__(self, path):
        super(ScanDirectoryWorker, self).__init__()
        self.path = path
        self.signals = WorkerSignals()

    @QtCore.Slot()
    def run(self):
        try:
            files = [os.path.join(self.path, f) for f in os.scandir(self.path) if f.is_file()]
        except Exception as e:
            self.signals.error.emit((type(e), e, e.__traceback__))
        else:
            self.signals.result.emit(files)
        finally:
            self.signals.finished.emit()

class FileItemModel(QtCore.QAbstractListModel):
    """A model to hold the list of file paths for a virtualized view."""
    def __init__(self, files=None, parent=None):
        super(FileItemModel, self).__init__(parent)
        self.files = files or []

    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            # The data we want to display is the file path string
            return self.files[index.row()]
        # Future roles can be added here (e.g., for thumbnails)
        return None

    def rowCount(self, index):
        return len(self.files)

class ThumbnailWorker(QtCore.QRunnable):
    """
    Worker thread for generating a thumbnail.
    """
    def __init__(self, file_path, size=140):
        super(ThumbnailWorker, self).__init__()
        self.file_path = file_path
        self.size = size
        self.signals = WorkerSignals()

    @QtCore.Slot()
    def run(self):
        try:
            with Image.open(self.file_path) as img:
                img = ImageOps.exif_transpose(img)
                pixmap = pil_to_qpixmap(img)

        except Exception as e:
            self.signals.error.emit((type(e), e, e.__traceback__))
            print(f"[ThumbWorker] Error for {self.file_path}: {e}")
        else:
            self.signals.result.emit(pixmap)
        finally:
            self.signals.finished.emit()

class FullImageWorker(QtCore.QRunnable):
    """
    Worker thread for loading a full-resolution image.
    """
    def __init__(self, file_path, size=1024):
        super(FullImageWorker, self).__init__()
        self.file_path = file_path
        self.size = size # Max size for the preview
        self.signals = WorkerSignals()

    @QtCore.Slot()
    def run(self):
        try:
            with Image.open(self.file_path) as img:
                img = ImageOps.exif_transpose(img)
                # Resize if it's larger than our max preview size
                if img.width > self.size or img.height > self.size:
                    img.thumbnail((self.size, self.size), Image.Resampling.BICUBIC)
                
                pixmap = pil_to_qpixmap(img)

        except Exception as e:
            self.signals.error.emit((type(e), e, e.__traceback__))
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
            with Image.open(self.file_path) as img:
                # Most metadata is in 'info' or 'exif'
                for key, value in img.info.items():
                    if isinstance(value, bytes):
                        try:
                            # Attempt to decode bytes to a string
                            metadata[key] = value.decode('utf-8', errors='ignore')
                        except Exception:
                            # If decoding fails, represent bytes as a string
                            metadata[key] = str(value)
                    else:
                        metadata[key] = value
                
                # For formats like PNG, parameters might be in specific chunks
                if 'parameters' in metadata:
                    metadata['parameters'] = metadata['parameters']
                
                # Attempt to parse JSON data if present
                if 'a1111_json_info' in metadata:
                    try:
                        metadata['a1111_json_info'] = json.loads(metadata['a1111_json_info'])
                    except json.JSONDecodeError:
                        print(f"[MetadataWorker] Could not parse JSON from 'a1111_json_info' for {self.file_path}")


        except Exception as e:
            self.signals.error.emit((type(e), e, e.__traceback__))
            print(f"[MetadataWorker] Error for {self.file_path}: {e}")
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
            # For now, we only support PNG files
            if not self.file_path.lower().endswith('.png'):
                raise NotImplementedError("Metadata saving is currently only supported for PNG files.")

            with Image.open(self.file_path) as img:
                png_info = PngImagePlugin.PngInfo()
                # Add the new metadata. The key is arbitrary, but 'parameters' is standard.
                png_info.add_text("parameters", self.new_metadata_str)
                # Re-save the image with the new metadata
                img.save(self.file_path, pnginfo=png_info)

        except Exception as e:
            self.signals.error.emit((type(e), e, e.__traceback__))
            print(f"[MetadataSaveWorker] Error for {self.file_path}: {e}")
        else:
            self.signals.result.emit(self.file_path) # Emit the path on success
        finally:
            self.signals.finished.emit()


class DataManager(QtCore.QObject):
    """
    Manages all data operations in background threads.
    """
    model_ready = QtCore.Signal(object)
    thumbnail_ready = QtCore.Signal(str, QtGui.QPixmap)
    metadata_ready = QtCore.Signal(str, dict)
    full_image_ready = QtCore.Signal(QtGui.QPixmap)
    metadata_saved = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.thread_pool = QtCore.QThreadPool()
        print("[Model] DataManager initialized with thread pool.")

    def scan_directory(self, path):
        print(f"[Model] Queuing directory scan for: {path}")
        worker = ScanDirectoryWorker(path)
        worker.signals.result.connect(self.on_scan_result)
        worker.signals.error.connect(lambda err: print(f"[Model] Error scanning: {err}"))
        self.thread_pool.start(worker)

    def on_scan_result(self, files):
        print(f"[Model] Scan complete. Found {len(files)} files. Creating model.")
        model = FileItemModel(files)
        self.model_ready.emit(model)

    def request_thumbnail(self, file_path):
        worker = ThumbnailWorker(file_path)
        worker.signals.result.connect(lambda pixmap, p=file_path: self.on_thumbnail_result(p, pixmap))
        worker.signals.error.connect(lambda err, p=file_path: print(f"[Model] Error creating thumbnail for {p}: {err}"))
        self.thread_pool.start(worker)

    def on_thumbnail_result(self, file_path, pixmap):
        # print(f"[Model] Thumbnail generated for {file_path}. Emitting signal.")
        self.thumbnail_ready.emit(file_path, pixmap)

    def request_full_image(self, file_path):
        print(f"[Model] Queuing full image load for: {file_path}")
        worker = FullImageWorker(file_path)
        worker.signals.result.connect(self.full_image_ready.emit)
        worker.signals.error.connect(lambda err: print(f"[Model] Error loading full image: {err}") )
        self.thread_pool.start(worker)

    def request_metadata(self, file_path):
        print(f"[Model] Metadata requested for: {file_path}")
        worker = MetadataWorker(file_path)
        worker.signals.result.connect(lambda metadata, p=file_path: self.on_metadata_result(p, metadata))
        worker.signals.error.connect(lambda err, p=file_path: print(f"[Model] Error reading metadata for {p}: {err}"))
        self.thread_pool.start(worker)

    def on_metadata_result(self, file_path, metadata):
        # print(f"[Model] Metadata processed for {file_path}. Emitting signal.")
        self.metadata_ready.emit(file_path, metadata)

    def save_metadata(self, file_path, new_metadata_str):
        print(f"[Model] Queuing metadata save for: {file_path}")
        worker = MetadataSaveWorker(file_path, new_metadata_str)
        worker.signals.result.connect(self.on_metadata_saved)
        worker.signals.error.connect(lambda err: print(f"[Model] Error saving metadata: {err}"))
        self.thread_pool.start(worker)

    def on_metadata_saved(self, file_path):
        print(f"[Model] Metadata saved for {file_path}. Emitting signal.")
        self.metadata_saved.emit(file_path)