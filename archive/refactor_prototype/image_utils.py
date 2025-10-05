# refactor_prototype/image_utils.py

from qtpy import QtGui
from PIL import Image

def pil_to_qpixmap(pil_image):
    """Convert a PIL Image to a QPixmap."""
    if pil_image.mode == "RGBA":
        qimage = QtGui.QImage(pil_image.tobytes("raw", "RGBA"), pil_image.width, pil_image.height, QtGui.QImage.Format.Format_RGBA8888)
    else:
        pil_image = pil_image.convert("RGB")
        qimage = QtGui.QImage(pil_image.tobytes("raw", "RGBX"), pil_image.width, pil_image.height, QtGui.QImage.Format.Format_RGBX8888)
    return QtGui.QPixmap.fromImage(qimage)
