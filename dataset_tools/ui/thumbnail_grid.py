# dataset_tools/ui/thumbnail_grid.py

"""Thumbnail grid view for file browsing.

A memory-efficient, responsive thumbnail grid that lazy-loads images as you scroll.
Automatically adjusts thumbnail size and columns based on window width.
Think of it as your inventory grid in FFXIV but for images!
"""

import hashlib
import gc
import logging
import time
from pathlib import Path

import cv2
import numpy as np
from PyQt6 import QtCore, QtGui
from PyQt6 import QtWidgets as Qw

from dataset_tools.logger import get_logger

log = get_logger(__name__)


class ThumbnailCache:
    """Simple LRU cache for thumbnail pixmaps."""

    def __init__(self, max_size: int = 200):
        self.max_size = max_size
        self._cache: dict[str, QtGui.QPixmap] = {}
        self._access_order: list[str] = []

    def get(self, key: str) -> QtGui.QPixmap | None:
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


class WorkerSignals(QtCore.QObject):
    """Defines signals available from a worker thread. Supports success and error cases."""

    thumbnail_ready = QtCore.pyqtSignal(str, QtGui.QPixmap)  # file_path, pixmap
    error = QtCore.pyqtSignal(str, str)  # file_path, error_message


class ThumbnailWorker(QtCore.QRunnable):
    """Worker task for loading a single thumbnail in a thread pool."""

    def __init__(self, file_path: str, thumb_size: int):
        super().__init__()
        self.file_path = file_path
        self.thumb_size = thumb_size
        self.signals = WorkerSignals()

    def run(self):
        """Execute the worker task."""
        log.debug("[CACHE_DEBUG] Worker started for: %s", self.file_path)
        try:
            # Check disk cache first
            pixmap = self._load_cached_thumbnail(self.file_path, self.thumb_size)

            if pixmap is None:
                # Generate new thumbnail
                pixmap = self._generate_thumbnail(self.file_path, self.thumb_size)

                # Save to disk cache
                if pixmap and not pixmap.isNull():
                    self._save_thumbnail_to_cache(self.file_path, pixmap, self.thumb_size)

            if pixmap and not pixmap.isNull():
                self.signals.thumbnail_ready.emit(self.file_path, pixmap)

        except Exception as e:
            log.error("Error loading thumbnail for %s: %s", self.file_path, e, exc_info=True)
            self.signals.error.emit(self.file_path, str(e))
        finally:
            gc.collect()
            log.debug("[CACHE_DEBUG] Worker finished for: %s", self.file_path)

    def _get_cache_path(self, image_path: str, thumb_size: int) -> Path:
        """Get the path where thumbnail should be cached."""
        folder = Path(image_path).parent
        cache_dir = folder / ".thumbnails"
        cache_dir.mkdir(exist_ok=True)

        path_str = f"{image_path}_{thumb_size}"
        path_hash = hashlib.sha256(path_str.encode()).hexdigest()[:16]
        original_name = Path(image_path).stem

        return cache_dir / f"{path_hash}_{original_name}.webp"

    def _load_cached_thumbnail(self, image_path: str, thumb_size: int) -> QtGui.QPixmap | None:
        """Load thumbnail from disk cache if available and fresh."""
        try:
            cache_path = self._get_cache_path(image_path, thumb_size)
            log.debug("[CACHE_DEBUG] Checking for cache file: %s", cache_path)

            if not cache_path.exists():
                log.debug("[CACHE_DEBUG] Cache file does not exist.")
                return None

            source_mtime = Path(image_path).stat().st_mtime
            cache_mtime = cache_path.stat().st_mtime
            log.debug("[CACHE_DEBUG] Source mtime: %s, Cache mtime: %s", source_mtime, cache_mtime)

            if source_mtime > cache_mtime:
                log.debug("[CACHE_DEBUG] Cache is stale.")
                return None  # Cache is stale

            pixmap = QtGui.QPixmap(str(cache_path))
            if not pixmap.isNull():
                log.debug("[CACHE_DEBUG] Loaded pixmap from cache.")
                return pixmap
            else:
                log.debug("[CACHE_DEBUG] Failed to load pixmap from cache file.")

        except Exception as e:
            log.debug("Cache load failed for %s: %s", image_path, e, exc_info=True)

        return None

    def _generate_thumbnail(self, image_path: str, thumb_size: int) -> QtGui.QPixmap | None:
        """Generate a new thumbnail using OpenCV for better performance."""
        log.debug("[CACHE_DEBUG] Generating thumbnail for: %s", image_path)
        start_time = time.time()
        try:
            # Load image with OpenCV (handles EXIF rotation automatically)
            img = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if img is None:
                log.error("Failed to load image: %s", image_path)
                return None

            # OpenCV loads as BGR, convert to RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Get original dimensions
            height, width = img.shape[:2]

            # Calculate aspect-preserving dimensions
            if width > height:
                new_width = thumb_size
                new_height = int(height * (thumb_size / width))
            else:
                new_height = thumb_size
                new_width = int(width * (thumb_size / height))

            # Resize using INTER_AREA (best for downscaling - fast + high quality)
            resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)

            # Letterbox to square with transparent padding
            # Create RGBA image (add alpha channel)
            square_img = np.zeros((thumb_size, thumb_size, 4), dtype=np.uint8)
            # Center the thumbnail
            x_offset = (thumb_size - new_width) // 2
            y_offset = (thumb_size - new_height) // 2
            # Paste RGB data
            square_img[y_offset:y_offset+new_height, x_offset:x_offset+new_width, :3] = resized
            # Set alpha to 255 (opaque) where image exists
            square_img[y_offset:y_offset+new_height, x_offset:x_offset+new_width, 3] = 255

            pixmap = self._numpy_to_qpixmap(square_img)
            end_time = time.time()
            log.debug("[CACHE_DEBUG] Thumbnail generation took: %.4f seconds", end_time - start_time)
            return pixmap
        except Exception as e:
            log.error("Failed to generate thumbnail for %s: %s", image_path, e, exc_info=True)
            return None

    def _save_thumbnail_to_cache(self, image_path: str, pixmap: QtGui.QPixmap, thumb_size: int):
        """Save thumbnail to disk cache."""
        try:
            cache_path = self._get_cache_path(image_path, thumb_size)
            # Lower quality for faster saves (60 is plenty for thumbnails, saves 2-3x faster)
            success = pixmap.save(str(cache_path), "WEBP", quality=60)
            if success:
                log.debug("[CACHE_DEBUG] Successfully saved cache file: %s", cache_path)
            else:
                log.debug("[CACHE_DEBUG] Failed to save cache file: %s", cache_path)
        except Exception as e:
            log.debug("Failed to save thumbnail cache: %s", e, exc_info=True)
            # Exception already logged above

    def _numpy_to_qpixmap(self, numpy_image: np.ndarray) -> QtGui.QPixmap:
        """Convert NumPy array (OpenCV format) to QPixmap."""
        height, width, channels = numpy_image.shape

        if channels == 4:
            # RGBA image
            bytes_per_line = width * 4
            qimage = QtGui.QImage(
                numpy_image.data,
                width,
                height,
                bytes_per_line,
                QtGui.QImage.Format.Format_RGBA8888,
            )
        elif channels == 3:
            # RGB image
            bytes_per_line = width * 3
            qimage = QtGui.QImage(
                numpy_image.data,
                width,
                height,
                bytes_per_line,
                QtGui.QImage.Format.Format_RGB888,
            )
        else:
            raise ValueError(f"Unsupported channel count: {channels}")

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

        # Prevent infinite resize loops during thumbnail loading
        self._is_reloading = False

        # Prevent metadata spam during mouse wheel scrolling
        self._is_scrolling = False
        self._pending_selection = None  # Store selection to emit after scroll stops
        self.scroll_debounce_timer = QtCore.QTimer()
        self.scroll_debounce_timer.setSingleShot(True)
        self.scroll_debounce_timer.timeout.connect(self._on_scroll_stopped)

        # Throttle thumbnail requests during scroll (don't check visibility on EVERY pixel)
        self.scroll_thumbnail_timer = QtCore.QTimer()
        self.scroll_thumbnail_timer.setSingleShot(True)
        self.scroll_thumbnail_timer.timeout.connect(self._request_visible_thumbnails)

        # Track if user has set manual size (disables auto-sizing on resize)
        self._manual_size_mode = False

        # Use a dedicated thread pool for thumbnail loading (not global!)
        # This prevents race conditions with other background tasks like CivitAI workers
        self.thread_pool = QtCore.QThreadPool(parent=self)
        # Use many threads for faster loading (thumbnails are I/O bound, not CPU bound)
        # 16 threads = aggressive parallelism, SSDs can handle it easily
        self.thread_pool.setMaxThreadCount(16)
        log.info(f"Thumbnail pool configured with max {self.thread_pool.maxThreadCount()} threads.")

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
        self.verticalScrollBar().valueChanged.connect(self._on_scroll_value_changed)

    def resizeEvent(self, event: QtGui.QResizeEvent):  # noqa: N802
        """Handle widget resize by debouncing thumbnail size recalculation."""
        super().resizeEvent(event)

        # Don't trigger resize during thumbnail reload (prevents infinite loops!)
        if self._is_reloading:
            return

        # Don't auto-resize if user has set manual size mode
        if self._manual_size_mode:
            return

        # Debounce: only recalculate after user stops resizing for 150ms
        self.resize_timer.start(150)

    def _update_thumbnail_size(self):
        """Calculate and apply appropriate thumbnail size based on widget width."""
        # Re-enable auto-sizing mode (user may have switched from manual to auto)
        self._manual_size_mode = False

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
        # Set reload flag to prevent resize events during reload
        self._is_reloading = True

        # ALSO block selection signals to prevent metadata spam during reload!
        self._is_scrolling = True

        # Clear memory cache (disk cache handles different sizes)
        self.thumbnail_cache.clear()
        self.requested_thumbnails.clear()

        # DON'T reset icons to placeholder - keep old size visible while new size loads!
        # This makes size switching feel instant since old thumbs stay visible
        # New thumbs will replace them as they load from disk cache

        # Request visible thumbnails at new size
        # Use longer delay to let layout stabilize completely
        QtCore.QTimer.singleShot(200, self._request_visible_and_unlock)

    def _request_visible_and_unlock(self):
        """Request visible thumbnails and unlock resize events."""
        self._request_visible_thumbnails()
        # Unlock after thumbnails start loading
        QtCore.QTimer.singleShot(500, self._unlock_resize)

    def _unlock_resize(self):
        """Unlock resize events after thumbnail loading stabilizes."""
        self._is_reloading = False
        self._is_scrolling = False  # Also unlock selection signals
        log.debug("Thumbnail reload complete, resize and selection events unlocked")
        # Request visible thumbnails one more time to catch any that were
        # missed during layout shifts
        self._request_visible_thumbnails()

    def set_manual_thumbnail_size(self, size: int, skip_reload: bool = False):
        """Set thumbnail size manually (disables auto-sizing).

        Args:
            size: Thumbnail size in pixels
            skip_reload: If True, don't reload thumbnails (used on startup)
        """
        log.info(f"Setting manual thumbnail size: {size}px (manual mode enabled)")

        # Enable manual size mode (disables auto-resize on window resize)
        self._manual_size_mode = True

        # Update size
        old_size = self.current_thumb_size
        self.current_thumb_size = size

        # Update UI
        self.setIconSize(QtCore.QSize(size, size))
        self._update_grid_size()

        # Reload thumbnails at new size (unless we're initializing on startup)
        if not skip_reload:
            self._reload_thumbnails_at_new_size()

    def set_folder(self, folder_path: str, files: list[str], file_to_select: str | None = None):
        """Set the folder and file list to display."""
        log.info(f"Setting folder: {folder_path} with {len(files)} files")

        # Cancel all pending thumbnail tasks from the previous folder
        self.thread_pool.clear()

        self.clear()
        self.thumbnail_cache.clear()
        self.requested_thumbnails.clear()

        self.folder_path = folder_path
        self.file_list = files

        # Add items with placeholder icons
        placeholder = self._create_placeholder_icon()
        for file_name in files:
            item = Qw.QListWidgetItem(file_name)
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop)
            item.setIcon(QtGui.QIcon(placeholder))
            self.addItem(item)

        # Pre-load cached thumbnails from disk into memory
        self._preload_disk_cache()

        # Select the requested file if provided
        if file_to_select:
            self.select_file_by_name(file_to_select)

        # Load visible thumbnails after a short delay
        QtCore.QTimer.singleShot(100, self._request_visible_thumbnails)

    def select_file_by_name(self, file_name: str) -> bool:
        """Select and scroll to a specific file by name.

        Returns:
            True if file was found and selected, False otherwise
        """
        for i in range(self.count()):
            item = self.item(i)
            if item and item.text() == file_name:
                self.setCurrentItem(item)
                self.scrollToItem(item, Qw.QAbstractItemView.ScrollHint.PositionAtCenter)
                log.info(f"Selected and scrolled to thumbnail: {file_name}")
                return True
        return False

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

    def _preload_disk_cache(self):
        """Pre-load existing disk cache into memory for instant display."""
        if not self.folder_path:
            return

        cache_dir = Path(self.folder_path) / ".thumbnails"
        if not cache_dir.exists():
            return

        log.info("Pre-loading disk cache from: %s", cache_dir)
        loaded_count = 0

        for file_name in self.file_list:
            full_path = str(Path(self.folder_path) / file_name)

            # Generate cache path (same logic as worker)
            path_str = f"{full_path}_{self.current_thumb_size}"
            path_hash = hashlib.sha256(path_str.encode()).hexdigest()[:16]
            original_name = Path(full_path).stem
            cache_path = cache_dir / f"{path_hash}_{original_name}.webp"

            # Check if cached thumbnail exists and is fresh
            if cache_path.exists():
                try:
                    source_mtime = Path(full_path).stat().st_mtime
                    cache_mtime = cache_path.stat().st_mtime

                    # Only use cache if it's newer than source
                    if cache_mtime >= source_mtime:
                        pixmap = QtGui.QPixmap(str(cache_path))
                        if not pixmap.isNull():
                            # Add to memory cache
                            self.thumbnail_cache.put(full_path, pixmap)
                            loaded_count += 1

                            # Update the list item immediately
                            for i in range(self.count()):
                                item = self.item(i)
                                if item and item.text() == file_name:
                                    item.setIcon(QtGui.QIcon(pixmap))
                                    break

                except Exception as e:
                    log.debug("Failed to preload cache for %s: %s", file_name, e)

        if loaded_count > 0:
            log.info("Pre-loaded %s thumbnails from disk cache", loaded_count)

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
                full_path = str(Path(self.folder_path) / file_name)

                # Skip if already requested
                if full_path in self.requested_thumbnails:
                    continue

                # Check memory cache
                cached = self.thumbnail_cache.get(full_path)
                if cached:
                    item.setIcon(QtGui.QIcon(cached))
                    continue

                # Request from worker thread
                self.requested_thumbnails.add(full_path)

                # Create and run a worker task in the thread pool
                worker = ThumbnailWorker(full_path, self.current_thumb_size)
                worker.signals.thumbnail_ready.connect(self._on_thumbnail_ready)
                self.thread_pool.start(worker)

    def _on_thumbnail_ready(self, file_path: str, pixmap: QtGui.QPixmap):
        """Handle thumbnail loaded from a worker thread."""
        # Add to memory cache
        self.thumbnail_cache.put(file_path, pixmap)

        # Find the item and update its icon
        file_name = Path(file_path).name
        for i in range(self.count()):
            item = self.item(i)
            if item and item.text() == file_name:
                item.setIcon(QtGui.QIcon(pixmap))
                break

    def _on_selection_changed(self, current, _previous):
        """Handle selection change - debounce during scrolling to prevent metadata spam."""
        if not current:
            return

        # If we're actively scrolling, store the selection and don't emit yet
        if self._is_scrolling:
            self._pending_selection = current.text()
            log.debug(f"Selection queued during scroll: {current.text()}")
            return

        # Not scrolling - emit immediately
        self.file_selected.emit(current.text())
        log.debug(f"Selection emitted immediately: {current.text()}")

    def _on_scroll_value_changed(self):
        """Handle scroll bar value change - marks us as scrolling and requests thumbnails."""
        # Mark as scrolling
        self._is_scrolling = True

        # Throttle thumbnail requests (only check every 50ms, not every pixel!)
        # This prevents scroll lag from checking 1000+ items on every scroll event
        if not self.scroll_thumbnail_timer.isActive():
            self.scroll_thumbnail_timer.start(50)

        # Reset scroll debounce timer (300ms after last scroll movement)
        self.scroll_debounce_timer.start(300)

    def _on_scroll_stopped(self):
        """Called when scrolling has stopped - emit pending selection if any."""
        self._is_scrolling = False
        log.debug("Scrolling stopped")

        # If there's a pending selection, emit it now
        if self._pending_selection:
            log.info(f"Emitting selection after scroll stopped: {self._pending_selection}")
            self.file_selected.emit(self._pending_selection)
            self._pending_selection = None

    def cleanup(self):
        """Cleanup resources on shutdown."""
        log.info("Clearing thumbnail thread pool.")
        self.thread_pool.clear()
