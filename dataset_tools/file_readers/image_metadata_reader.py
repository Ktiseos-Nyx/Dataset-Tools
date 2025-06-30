# dataset_tools/file_readers/image_metadata_reader.py

"""
Image metadata reader for PNG, JPG, and other image formats.

This module specializes in reading metadata from image files using pyexiv2
with Pillow fallback. Think of it as your image specialist job class that
knows all the tricks for getting data from photos! 📸✨
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pyexiv2

# Pillow import with fallback
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from ..logger import get_logger, debug_monitor, info_monitor as nfo


class ImageMetadataReader:
    """
    Specialized reader for image file metadata.
    
    This class handles reading EXIF, IPTC, and XMP metadata from image files
    using pyexiv2 as the primary method with Pillow as a fallback.
    """
    
    def __init__(self):
        """Initialize the image metadata reader."""
        self.logger = get_logger(f"{__name__}.ImageMetadataReader")
        
        # Supported image formats
        self.supported_formats = {
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp'
        }
    
    def can_read_file(self, file_path: str) -> bool:
        """
        Check if this reader can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this reader supports the file format
        """
        suffix = Path(file_path).suffix.lower()
        return suffix in self.supported_formats
    
    @debug_monitor
    def read_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Read metadata from an image file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary containing metadata or None if reading failed
        """
        if not self.can_read_file(file_path):
            self.logger.warning(f"Unsupported image format: {file_path}")
            return None
        
        file_suffix = Path(file_path).suffix.lower()
        
        if file_suffix in {'.jpg', '.jpeg'}:
            return self._read_jpg_metadata(file_path)
        elif file_suffix == '.png':
            return self._read_png_metadata(file_path)
        elif file_suffix in {'.tiff', '.tif'}:
            return self._read_tiff_metadata(file_path)
        elif file_suffix == '.webp':
            return self._read_webp_metadata(file_path)
        else:
            # Generic image reading
            return self._read_generic_image_metadata(file_path)
    
    @debug_monitor
    def _read_jpg_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read metadata from a JPG/JPEG file."""
        nfo(f"[ImageReader] Reading JPG metadata: {Path(file_path).name}")
        
        try:
            # Try pyexiv2 first
            result = self._read_with_pyexiv2(file_path)
            if result:
                self._log_user_comment_info(result, file_path)
                return result
            
            # Fallback to Pillow
            return self._fallback_to_pillow(file_path, "JPG")
            
        except Exception as e:
            self.logger.error(f"Error reading JPG metadata from {file_path}: {e}")
            return self._fallback_to_pillow(file_path, "JPG (after error)")
    
    @debug_monitor
    def _read_png_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read metadata from a PNG file."""
        nfo(f"[ImageReader] Reading PNG metadata: {Path(file_path).name}")
        
        try:
            # Try pyexiv2 first
            result = self._read_with_pyexiv2(file_path)
            if result:
                return result
            
            # Fallback to Pillow
            return self._fallback_to_pillow(file_path, "PNG")
            
        except Exception as e:
            self.logger.error(f"Error reading PNG metadata from {file_path}: {e}")
            return self._fallback_to_pillow(file_path, "PNG (after error)")
    
    @debug_monitor
    def _read_tiff_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read metadata from a TIFF file."""
        nfo(f"[ImageReader] Reading TIFF metadata: {Path(file_path).name}")
        
        try:
            result = self._read_with_pyexiv2(file_path)
            if result:
                return result
            
            return self._fallback_to_pillow(file_path, "TIFF")
            
        except Exception as e:
            self.logger.error(f"Error reading TIFF metadata from {file_path}: {e}")
            return self._fallback_to_pillow(file_path, "TIFF (after error)")
    
    @debug_monitor
    def _read_webp_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read metadata from a WebP file."""
        nfo(f"[ImageReader] Reading WebP metadata: {Path(file_path).name}")
        
        try:
            result = self._read_with_pyexiv2(file_path)
            if result:
                return result
            
            return self._fallback_to_pillow(file_path, "WebP")
            
        except Exception as e:
            self.logger.error(f"Error reading WebP metadata from {file_path}: {e}")
            return self._fallback_to_pillow(file_path, "WebP (after error)")
    
    @debug_monitor
    def _read_generic_image_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read metadata from any supported image format."""
        nfo(f"[ImageReader] Reading generic image metadata: {Path(file_path).name}")
        
        try:
            result = self._read_with_pyexiv2(file_path)
            if result:
                return result
            
            return self._fallback_to_pillow(file_path, "Generic")
            
        except Exception as e:
            self.logger.error(f"Error reading generic image metadata from {file_path}: {e}")
            return self._fallback_to_pillow(file_path, "Generic (after error)")
    
    def _read_with_pyexiv2(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Read metadata using pyexiv2.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Metadata dictionary or None if no metadata found
        """
        try:
            img = pyexiv2.Image(file_path)
            
            exif_tags = img.read_exif() or {}
            iptc_tags = img.read_iptc() or {}
            xmp_tags = img.read_xmp() or {}
            
            img.close()
            
            metadata = {
                "EXIF": exif_tags,
                "IPTC": iptc_tags,
                "XMP": xmp_tags,
            }
            
            # Check if we actually found any metadata
            if not any(metadata.values()):
                nfo(f"[ImageReader] pyexiv2 found no metadata in: {Path(file_path).name}")
                return None
            
            nfo(f"[ImageReader] pyexiv2 successfully read metadata from: {Path(file_path).name}")
            return metadata
            
        except Exception as e:
            self.logger.debug(f"pyexiv2 error for {file_path}: {e}")
            return None
    
    def _fallback_to_pillow(self, file_path: str, context: str) -> Optional[Dict[str, Any]]:
        """
        Fallback to Pillow for EXIF reading.
        
        Args:
            file_path: Path to the image file
            context: Context string for logging
            
        Returns:
            Metadata dictionary or None if reading failed
        """
        if not PILLOW_AVAILABLE:
            self.logger.warning("Pillow not available for fallback EXIF reading")
            return None
        
        nfo(f"[ImageReader] Attempting Pillow fallback for {context}: {Path(file_path).name}")
        
        pillow_exif = self._read_exif_with_pillow(file_path)
        if pillow_exif:
            nfo(f"[ImageReader] Pillow successfully read EXIF data")
            return {"PILLOW_EXIF": pillow_exif}
        else:
            nfo(f"[ImageReader] Pillow found no EXIF data")
            return None
    
    @debug_monitor
    def _read_exif_with_pillow(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Read EXIF data using Pillow.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            EXIF data dictionary or None if reading failed
        """
        if not PILLOW_AVAILABLE:
            return None
        
        try:
            with Image.open(file_path) as img:
                exif_info = img.getexif()
                
                if not exif_info:
                    return None
                
                exif_data = {}
                for tag_id, value in exif_info.items():
                    tag_name = TAGS.get(tag_id, f"Tag_{tag_id}")
                    
                    # Handle bytes values
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8', errors='replace')
                        except UnicodeDecodeError:
                            value = str(value)
                    
                    exif_data[tag_name] = value
                
                return exif_data
                
        except FileNotFoundError:
            self.logger.error(f"Image file not found: {file_path}")
            return None
        except OSError as e:
            self.logger.error(f"OS error reading image {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error reading image {file_path}: {e}", exc_info=True)
            return None
    
    def _log_user_comment_info(self, metadata: Dict[str, Any], file_path: str) -> None:
        """Log information about UserComment field for debugging."""
        exif_data = metadata.get("EXIF", {})
        if "Exif.Photo.UserComment" in exif_data:
            uc_value = exif_data["Exif.Photo.UserComment"]
            self.logger.debug(
                f"UserComment type for {Path(file_path).name}: {type(uc_value)}"
            )
            
            if isinstance(uc_value, str) and uc_value.startswith("charset="):
                self.logger.debug(
                    f"UserComment appears to be pre-decoded with charset prefix: {Path(file_path).name}"
                )
    
    def get_supported_formats(self) -> set[str]:
        """Get the set of supported image formats."""
        return self.supported_formats.copy()


class ImageMetadataExtractor:
    """
    High-level interface for extracting specific metadata from images.
    
    This class provides convenient methods for getting common metadata
    without needing to know the internal structure. Like having preset
    actions on your hotbar! 🎮
    """
    
    def __init__(self, reader: Optional[ImageMetadataReader] = None):
        """
        Initialize the extractor.
        
        Args:
            reader: ImageMetadataReader instance to use
        """
        self.reader = reader or ImageMetadataReader()
        self.logger = get_logger(f"{__name__}.ImageMetadataExtractor")
    
    def extract_ai_generation_data(self, file_path: str) -> Optional[str]:
        """
        Extract AI generation parameters from image metadata.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            AI generation parameters string or None
        """
        metadata = self.reader.read_metadata(file_path)
        if not metadata:
            return None
        
        # Check various locations where AI data might be stored
        sources_to_check = [
            # EXIF UserComment
            ("EXIF", "Exif.Photo.UserComment"),
            # Pillow EXIF UserComment  
            ("PILLOW_EXIF", "UserComment"),
            # XMP description
            ("XMP", "Xmp.dc.description"),
            # PNG text chunks (if available)
            ("PNG_TEXT", "parameters"),
            ("PNG_TEXT", "Comment"),
        ]
        
        for source_type, key in sources_to_check:
            if source_type in metadata and key in metadata[source_type]:
                value = metadata[source_type][key]
                if value and isinstance(value, str) and len(value.strip()) > 0:
                    return value.strip()
        
        return None
    
    def extract_basic_info(self, file_path: str) -> Dict[str, Any]:
        """
        Extract basic image information.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with basic image info
        """
        info = {
            "file_name": Path(file_path).name,
            "file_size": None,
            "image_size": None,
            "format": Path(file_path).suffix.lower(),
            "has_exif": False,
            "has_xmp": False,
            "has_iptc": False,
        }
        
        try:
            # Get file size
            info["file_size"] = Path(file_path).stat().st_size
            
            # Get image dimensions with Pillow
            if PILLOW_AVAILABLE:
                try:
                    with Image.open(file_path) as img:
                        info["image_size"] = (img.width, img.height)
                except Exception:
                    pass
            
            # Check for metadata presence
            metadata = self.reader.read_metadata(file_path)
            if metadata:
                info["has_exif"] = bool(metadata.get("EXIF") or metadata.get("PILLOW_EXIF"))
                info["has_xmp"] = bool(metadata.get("XMP"))
                info["has_iptc"] = bool(metadata.get("IPTC"))
            
        except Exception as e:
            self.logger.debug(f"Error extracting basic info from {file_path}: {e}")
        
        return info


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def read_image_metadata(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to read image metadata.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Metadata dictionary or None
    """
    reader = ImageMetadataReader()
    return reader.read_metadata(file_path)


def extract_ai_parameters(file_path: str) -> Optional[str]:
    """
    Convenience function to extract AI generation parameters.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        AI parameters string or None
    """
    extractor = ImageMetadataExtractor()
    return extractor.extract_ai_generation_data(file_path)


def get_image_info(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to get basic image information.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Dictionary with image information
    """
    extractor = ImageMetadataExtractor()
    return extractor.extract_basic_info(file_path)


# ============================================================================
# TESTING UTILITIES
# ============================================================================

def test_image_metadata_reader():
    """Test the image metadata reader with sample files."""
    logger = get_logger("ImageMetadataReaderTest")
    
    reader = ImageMetadataReader()
    extractor = ImageMetadataExtractor(reader)
    
    logger.info("Testing ImageMetadataReader...")
    logger.info(f"Supported formats: {reader.get_supported_formats()}")
    
    # Test with a sample image file (if it exists)
    test_files = [
        "test_image.jpg",
        "sample.png",
        "photo.jpeg",
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            logger.info(f"\nTesting with: {test_file}")
            
            # Test basic info
            info = extractor.extract_basic_info(test_file)
            logger.info(f"Basic info: {info}")
            
            # Test metadata reading
            metadata = reader.read_metadata(test_file)
            if metadata:
                logger.info(f"Metadata keys: {list(metadata.keys())}")
                for key, value in metadata.items():
                    if isinstance(value, dict):
                        logger.info(f"  {key}: {len(value)} entries")
                    else:
                        logger.info(f"  {key}: {type(value)}")
            else:
                logger.info("No metadata found")
            
            # Test AI parameter extraction
            ai_params = extractor.extract_ai_generation_data(test_file)
            if ai_params:
                logger.info(f"AI parameters found (length: {len(ai_params)})")
            else:
                logger.info("No AI parameters found")
        else:
            logger.info(f"Test file not found: {test_file}")
    
    logger.info("ImageMetadataReader test completed!")


if __name__ == "__main__":
    # Run tests if module is executed directly
    test_image_metadata_reader()
