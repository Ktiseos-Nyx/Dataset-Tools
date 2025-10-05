# dataset_tools/ui/thumbnail_grid.py

"""Thumbnail grid view for file browsing.

A memory-efficient, responsive thumbnail grid that lazy-loads images as you scroll.
Automatically adjusts thumbnail size and columns based on window width.
Think of it as your inventory grid in FFXIV but for images!
"""

import hashlib
from pathlib import Path
from typing import Optional

from PIL import Image, ImageOps
from PyQt6 import QtCore, QtGui, QtWidgets as Qw

from ..logger import get_logger

log = get_logger(__name__)


class ThumbnailCache:
    """Simple LRU cache for thumbnail pixmaps."""
    
    def __init__(self, max_size: int = 200):
        self.max_size = max_size
        self._cache: dict[str, QtGui.QPixmap] = {}
        self._access_order: list[str] = []
    
    def get(self, key: str) -> Optional[QtGui.QPixmap]:
        """Get a pixmap from cache."""
        if key in self._cache:
            # Move to end (most recently used)
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None
    
    def put(self, key: str, pixmap: QtGui.QPixmap) -> None:
        """Add a pixmap to cache."""
        if key in self._cache:
            self._access_order.remove(key)
        
        self._cache[key] = pixmap
        self._access_order.append(key)
        
        # Evict oldest if over size
        while len(self._cache) > self.max_size:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]
    
    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
        self._access_order.clear()


class ThumbnailWorker(QtCore.QObject):
    """Worker for loading thumbnails in background thread."""
    
    thumbnail_ready = QtCore.pyqtSignal(str, QtGui.QPixmap)  # file_path, pixmap
    load_requested = QtCore.pyqtSignal(str, str, int)  # file_name, folder, thumb_size
    
    def __init__(self):
        super().__init__()
        self._cancelled_paths: set[str] = set()
        self.load_requested.connect(self._load_thumbnail)
    
    def _load_thumbnail(self, file_name: str, folder_path: str, thumb_size: int):
        """Load a thumbnail in the background thread."""
        full_path = str(Path(folder_path) / file_name)
        
        # Check if cancelled
        if full_path in self._cancelled_paths:
            self._cancelled_paths.discard(full_path)
            return
        
        try:
            # Check disk cache first
            pixmap = self._load_cached_thumbnail(full_path, thumb_size)
            
            if pixmap is None:
                # Generate new thumbnail
                pixmap = self._generate_thumbnail(full_path, thumb_size)
                
                # Save to disk cache
                if pixmap and not pixmap.isNull():
                    self._save_thumbnail_to_cache(full_path, pixmap, thumb_size)
            
            if pixmap and not pixmap.isNull() and full_path not in self._cancelled_paths:
                self.thumbnail_ready.emit(file_name, pixmap)
        
        except Exception as e:
            log.error(f"Error loading thumbnail for {file_name}: {e}")
    
    def cancel_path(self, file_path: str):
        """Cancel loading for a specific path."""
        self._cancelled_paths.add(file_path)
    
    def clear_cancelled(self):
        """Clear cancelled paths."""
        self._cancelled_paths.clear()
    
    def _get_cache_path(self, image_path: str, thumb_size: int) -> Path:
        """Get the path where thumbnail should be cached."""
        folder = Path(image_path).parent
        cache_dir = folder / ".thumbnails"
        cache_dir.mkdir(exist_ok=True)
        
        # Create hash of path + size to handle different thumbnail sizes
        path_str = f"{image_path}_{thumb_size}"
        path_hash = hashlib.md5(path_str.encode()).hexdigest()[:8]
        original_name = Path(image_path).stem
        
        return cache_dir / f"{path_hash}_{original_name}.jpg"
    
    def _load_cached_thumbnail(self, image_path: str, thumb_size: int) -> Optional[QtGui.QPixmap]:
        """Load thumbnail from disk cache if available and fresh."""
        try:
            cache_path = self._get_cache_path(image_path, thumb_size)
            
            if not cache_path.exists():
                return None
            
            # Check if source is newer than cache
            source_mtime = Path(image_path).stat().st_mtime
            cache_mtime = cache_path.stat().st_mtime
            
            if source_mtime > cache_mtime:
                return None  # Cache is stale
            
            # Load cached thumbnail
            pixmap = QtGui.QPixmap(str(cache_path))
            if not pixmap.isNull():
                log.debug(f"Loaded cached thumbnail for {Path(image_path).name}")
                return pixmap
            
        except Exception as e:
            log.debug(f"Cache load failed for {image_path}: {e}")
        
        return None
    
    def _generate_thumbnail(self, image_path: str, thumb_size: int) -> Optional[QtGui.QPixmap]:
        """Generate a new thumbnail."""
        try:
            with Image.open(image_path) as img:
                # Fix rotation
                img = ImageOps.exif_transpose(img)
                
                # Create thumbnail (in-place, memory efficient)
                img.thumbnail((thumb_size, thumb_size), Image.Resampling.BILINEAR)
                
                # Convert to QPixmap
                return self._pil_to_qpixmap(img)
        
        except Exception as e:
            log.error(f"Failed to generate thumbnail for {image_path}: {e}")
            return None
    
    def _save_thumbnail_to_cache(self, image_path: str, pixmap: QtGui.QPixmap, thumb_size: int):
        """Save thumbnail to disk cache."""
        try:
            cache_path = self._get_cache_path(image_path, thumb_size)
            pixmap.save(str(cache_path), "JPEG", quality=85)
            log.debug(f"Saved thumbnail to cache: {cache_path.name}")
        except Exception as e:
            log.debug(f"Failed to save thumbnail cache: {e}")
    
    def _pil_to_qpixmap(self, pil_image: Image.Image) -> QtGui.QPixmap:
        """Convert PIL Image to QPixmap."""
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        
        width, height = pil_image.size
        image_data = pil_image.tobytes("raw", "RGB")
        bytes_per_line = width * 3
        
        qimage = QtGui.QImage(
            image_data,
            width,
            height,
            bytes_per_line,
            QtGui.QImage.Format.Format_RGB888,
        )
        
        return QtGui.QPixmap.fromImage(qimage)


class ThumbnailGridWidget(Qw.QListWidget):
    """Grid view widget that displays file thumbnails with lazy loading and responsive sizing."""
    
    file_selected = QtCore.pyqtSignal(str)  # Emits filename when selected
    
    def __init__(self, parent=None, base_thumb_size: int = 128):
        super().__init__(parent)
        self.base_thumb_size = base_thumb_size  # Base size for responsive calculations
        self.current_thumb_size = base_thumb_size  # Actual current thumbnail size
        self.folder_path = ""
        self.file_list: list[str] = []
        
        # Cache
        self.thumbnail_cache = ThumbnailCache(max_size=300)
        self.requested_thumbnails: set[str] = set()
        
        # Resize debouncing
        self.resize_timer = QtCore.QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._update_thumbnail_size)
        
        # Setup worker thread
        self.worker_thread = QtCore.QThread()
        self.worker = ThumbnailWorker()
        self.worker.moveToThread(self.worker_thread)
        self.worker.thumbnail_ready.connect(self._on_thumbnail_ready)
        self.worker_thread.start()
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the grid view."""
        self.setViewMode(Qw.QListView.ViewMode.IconMode)
        self.setIconSize(QtCore.QSize(self.current_thumb_size, self.current_thumb_size))
        self.setResizeMode(Qw.QListView.ResizeMode.Adjust)
        self.setMovement(Qw.QListView.Movement.Static)
        self.setSpacing(10)
        self.setUniformItemSizes(True)
        self.setWordWrap(True)
        
        # Smooth scrolling
        self.setVerticalScrollMode(Qw.QAbstractItemView.ScrollMode.ScrollPerPixel)
        
        # Grid layout
        self._update_grid_size()
    
    def _update_grid_size(self):
        """Update the grid cell size based on current thumbnail size."""
        self.setGridSize(QtCore.QSize(
            self.current_thumb_size + 20,  # Extra space for padding
            self.current_thumb_size + 60   # Extra space for filename
        ))
    
    def _connect_signals(self):
        """Connect signals."""
        self.currentItemChanged.connect(self._on_selection_changed)
        self.verticalScrollBar().valueChanged.connect(self._request_visible_thumbnails)
    
    def resizeEvent(self, event: QtGui.QResizeEvent):
        """Handle widget resize by debouncing thumbnail size recalculation."""
        super().resizeEvent(event)
        # Debounce: only recalculate after user stops resizing for 150ms
        self.resize_timer.start(150)
    
    def _update_thumbnail_size(self):
        """Calculate and apply appropriate thumbnail size based on widget width."""
        viewport_width = self.viewport().width()
        
        if viewport_width <= 0:
            return
        
        # Calculate how many columns can fit
        spacing = 10
        min_columns = 2  # Never go below 2 columns
        max_columns = 8  # Never go above 8 columns
        
        # Try to fit as many base-size thumbnails as possible
        ideal_columns = viewport_width // (self.base_thumb_size + spacing)
        columns = max(min_columns, min(max_columns, ideal_columns))
        
        # Calculate actual thumbnail size to fill the space nicely
        available_width = viewport_width - (spacing * (columns + 1))
        new_thumb_size = max(64, min(256, available_width // columns))
        
        # Only update if size changed significantly (avoid constant resizing)
        if abs(new_thumb_size - self.current_thumb_size) > 15:
            old_size = self.current_thumb_size
            self.current_thumb_size = new_thumb_size
            
            log.info(f"Thumbnail size changed: {old_size}px → {new_thumb_size}px ({columns} columns)")
            
            # Update UI
            self.setIconSize(QtCore.QSize(new_thumb_size, new_thumb_size))
            self._update_grid_size()
            
            # Reload thumbnails at new size
            self._reload_thumbnails_at_new_size()
    
    def _reload_thumbnails_at_new_size(self):
        """Reload visible thumbnails at the new size."""
        # Clear memory cache (disk cache handles different sizes)
        self.thumbnail_cache.clear()
        self.requested_thumbnails.clear()
        
        # Reset all items to placeholder
        placeholder = self._create_placeholder_icon()
        for i in range(self.count()):
            item = self.item(i)
            if item:
                item.setIcon(QtGui.QIcon(placeholder))
        
        # Request visible thumbnails at new size
        QtCore.QTimer.singleShot(50, self._request_visible_thumbnails)
    
    def set_folder(self, folder_path: str, files: list[str]):
        """Set the folder and file list to display."""
        log.info(f"Setting folder: {folder_path} with {len(files)} files")
        
        # Clear everything
        self.clear()
        self.thumbnail_cache.clear()
        self.requested_thumbnails.clear()
        self.worker.clear_cancelled()
        
        self.folder_path = folder_path
        self.file_list = files
        
        # Add items with placeholder icons
        placeholder = self._create_placeholder_icon()
        for file_name in files:
            item = Qw.QListWidgetItem(file_name)
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop)
            item.setIcon(QtGui.QIcon(placeholder))
            self.addItem(item)
        
        # Load visible thumbnails after a short delay
        QtCore.QTimer.singleShot(100, self._request_visible_thumbnails)
    
    def _create_placeholder_icon(self) -> QtGui.QPixmap:
        """Create a placeholder icon for loading state."""
        size = self.current_thumb_size
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtGui.QColor("#2a2a2a"))
        
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QColor("#666"))
        painter.drawRect(0, 0, size - 1, size - 1)
        painter.drawText(pixmap.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "...")
        painter.end()
        
        return pixmap
    
    def _request_visible_thumbnails(self):
        """Request thumbnails for visible items only (lazy loading)."""
        if not self.folder_path:
            return
        
        viewport_rect = self.viewport().rect()
        
        for i in range(self.count()):
            item = self.item(i)
            if not item:
                continue
                
            item_rect = self.visualItemRect(item)
            
            # Only load if visible and not already requested
            if item_rect.intersects(viewport_rect):
                file_name = item.text()
                
                # Skip if already requested
                if file_name in self.requested_thumbnails:
                    continue
                
                # Check memory cache
                cached = self.thumbnail_cache.get(file_name)
                if cached:
                    item.setIcon(QtGui.QIcon(cached))
                    continue
                
                # Request from worker thread
                self.requested_thumbnails.add(file_name)
                self.worker.load_requested.emit(file_name, self.folder_path, self.current_thumb_size)
    
    def _on_thumbnail_ready(self, file_name: str, pixmap: QtGui.QPixmap):
        """Handle thumbnail loaded from worker thread."""
        # Add to memory cache
        self.thumbnail_cache.put(file_name, pixmap)
        
        # Update the item's icon
        for i in range(self.count()):
            item = self.item(i)
            if item and item.text() == file_name:
                item.setIcon(QtGui.QIcon(pixmap))
                break
    
    def _on_selection_changed(self, current, previous):
        """Handle selection change."""
        if current:
            self.file_selected.emit(current.text())
    
    def cleanup(self):
        """Cleanup resources on shutdown."""
        log.info("Cleaning up thumbnail grid worker thread")
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            if not self.worker_thread.wait(3000):
                self.worker_thread.terminate()
                self.worker_thread.wait()
