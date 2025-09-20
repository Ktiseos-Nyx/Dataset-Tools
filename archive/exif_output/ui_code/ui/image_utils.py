# dataset_tools/ui/image_utils.py

"""Utility functions for image processing in the UI."""

import logging

from PIL import Image, ImageOps
from PyQt6 import QtGui

logger = logging.getLogger(__name__)


def _pil_to_qpixmap(pil_image: Image.Image) -> QtGui.QPixmap:
    """Converts a PIL Image to a QPixmap."""
    # Ensure image is in a format Qt can handle
    if pil_image.mode == "RGBA":
        qimage = QtGui.QImage(
            pil_image.tobytes("raw", "RGBA"),
            pil_image.width,
            pil_image.height,
            QtGui.QImage.Format.Format_RGBA8888,
        )
    else:
        # Convert to RGB for consistency if not RGBA
        pil_image = pil_image.convert("RGB")
        qimage = QtGui.QImage(
            pil_image.tobytes("raw", "RGBX"),
            pil_image.width,
            pil_image.height,
            QtGui.QImage.Format.Format_RGBX8888,
        )
    return QtGui.QPixmap.fromImage(qimage)


def create_safe_thumbnail(image_path: str, max_size: int) -> QtGui.QPixmap:
    """Create a memory-efficient thumbnail avoiding Lanczos artifacts.

    Args:
        image_path: Path to the source image
        max_size: Maximum dimension for the thumbnail

    Returns:
        QPixmap containing the thumbnail, or null pixmap on error

    """
    try:
        # Use 'with' to ensure immediate cleanup of full-resolution image
        with Image.open(image_path) as img:
            # Fix rotation issues BEFORE doing anything else
            img = ImageOps.exif_transpose(img)

            # Use thumbnail() instead of resize() - it's memory efficient and safer
            # thumbnail() modifies in-place and uses a good resampling filter
            img.thumbnail((max_size, max_size), Image.Resampling.BILINEAR)  # Safer than LANCZOS

            # Convert to Qt format with proper color channel handling
            return _pil_to_qpixmap(img)

    except Exception as e:
        logger.error("Error creating thumbnail for '%s': %s", image_path, e)
        # Return empty pixmap on error
        return QtGui.QPixmap()
