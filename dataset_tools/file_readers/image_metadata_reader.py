# dataset_tools/file_readers/image_metadata_reader.py

"""Image metadata reader for PNG, JPG, and other image formats.

This module specializes in reading metadata from image files using pyexiv2
with Pillow fallback. Think of it as your image specialist job class that
knows all the tricks for getting data from photos! 📸✨
"""

from pathlib import Path
from typing import Any

import pyexiv2

# Pillow import with fallback
try:
    from PIL import Image
    from PIL.ExifTags import TAGS

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# pypng import with fallback
try:
    import png

    PYPNG_AVAILABLE = True
except ImportError:
    PYPNG_AVAILABLE = False

from ..logger import debug_monitor, get_logger
from ..logger import info_monitor as nfo


class ImageMetadataReader:
    """Specialized reader for image file metadata.

    This class handles reading EXIF, IPTC, and XMP metadata from image files
    using pyexiv2 as the primary method with Pillow as a fallback.
    """

    def __init__(self) -> None:
        """Initialize the image metadata reader."""
        self.logger = get_logger(f"{__name__}.ImageMetadataReader")

        # Supported image formats
        self.supported_formats = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp"}

    def can_read_file(self, file_path: str) -> bool:
        """Check if this reader can handle the given file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if this reader supports the file format

        """
        suffix = Path(file_path).suffix.lower()
        return suffix in self.supported_formats

    @debug_monitor
    def read_metadata(self, file_path: str) -> dict[str, Any] | None:
        """Read metadata from an image file.

        Args:
            file_path: Path to the image file

        Returns:
            Dictionary containing metadata or None if reading failed

        """
        if not self.can_read_file(file_path):
            self.logger.warning("Unsupported image format: %s", file_path)
            return None

        file_suffix = Path(file_path).suffix.lower()

        if file_suffix in {".jpg", ".jpeg"}:
            return self._read_jpg_metadata(file_path)
        if file_suffix == ".png":
            return self._read_png_metadata(file_path)
        if file_suffix in {".tiff", ".tif"}:
            return self._read_tiff_metadata(file_path)
        if file_suffix == ".webp":
            return self._read_webp_metadata(file_path)
        # Generic image reading
        return self._read_generic_image_metadata(file_path)

    @debug_monitor
    def _read_jpg_metadata(self, file_path: str) -> dict[str, Any] | None:
        """Read metadata from a JPG/JPEG file."""
        nfo("[ImageReader] Reading JPG metadata: %s", Path(file_path).name)

        try:
            # Try pyexiv2 first
            result = self._read_with_pyexiv2(file_path)
            if result:
                self._log_user_comment_info(result, file_path)
                return result

            # Fallback to Pillow
            return self._fallback_to_pillow(file_path, "JPG")

        except Exception as e:
            self.logger.error("Error reading JPG metadata from %s: %s", file_path, e)
            return self._fallback_to_pillow(file_path, "JPG (after error)")

    @debug_monitor
    def _read_png_metadata(self, file_path: str) -> dict[str, Any] | None:
        """Read metadata from a PNG file.

        pyexiv2 is now smart enough to automatically use pypng for PNG text chunks!
        """
        nfo("[ImageReader] Reading PNG metadata: %s", Path(file_path).name)

        try:
            # Try pyexiv2 (now enhanced with automatic pypng fallback for PNGs)
            result = self._read_with_pyexiv2(file_path)
            if result:
                return result

            # Final fallback to Pillow
            return self._fallback_to_pillow(file_path, "PNG")

        except Exception as e:
            self.logger.error("Error reading PNG metadata from %s: %s", file_path, e)
            return self._fallback_to_pillow(file_path, "PNG (after error)")

    @debug_monitor
    def _read_tiff_metadata(self, file_path: str) -> dict[str, Any] | None:
        """Read metadata from a TIFF file."""
        nfo("[ImageReader] Reading TIFF metadata: %s", Path(file_path).name)

        try:
            result = self._read_with_pyexiv2(file_path)
            if result:
                return result

            return self._fallback_to_pillow(file_path, "TIFF")

        except Exception as e:
            self.logger.error("Error reading TIFF metadata from %s: %s", file_path, e)
            return self._fallback_to_pillow(file_path, "TIFF (after error)")

    @debug_monitor
    def _read_webp_metadata(self, file_path: str) -> dict[str, Any] | None:
        """Read metadata from a WebP file."""
        nfo("[ImageReader] Reading WebP metadata: %s", Path(file_path).name)

        try:
            result = self._read_with_pyexiv2(file_path)
            if result:
                return result

            return self._fallback_to_pillow(file_path, "WebP")

        except Exception as e:
            self.logger.error("Error reading WebP metadata from %s: %s", file_path, e)
            return self._fallback_to_pillow(file_path, "WebP (after error)")

    @debug_monitor
    def _read_generic_image_metadata(self, file_path: str) -> dict[str, Any] | None:
        """Read metadata from any supported image format."""
        nfo("[ImageReader] Reading generic image metadata: %s", Path(file_path).name)

        try:
            result = self._read_with_pyexiv2(file_path)
            if result:
                return result

            return self._fallback_to_pillow(file_path, "Generic")

        except Exception as e:
            self.logger.error("Error reading generic image metadata from %s: %s", file_path, e)
            return self._fallback_to_pillow(file_path, "Generic (after error)")

    def _read_with_pyexiv2(self, file_path: str) -> dict[str, Any] | None:
        """Read metadata using pyexiv2, enhanced with pypng for PNG files.

        For PNG files, if pyexiv2 finds no standard metadata (EXIF/IPTC/XMP),
        this automatically tries pypng to read PNG text chunks (ComfyUI workflows, etc.)

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

            # Attempt to correct UserComment decoding if pyexiv2 returned a mojibaked string
            if "Exif.Photo.UserComment" in exif_tags:
                uc_value = exif_tags["Exif.Photo.UserComment"]
                corrected_uc = uc_value  # Default to original

                if isinstance(uc_value, bytes):
                    # If pyexiv2 returns bytes, use the robust byte decoder
                    corrected_uc = self._decode_usercomment_bytes(uc_value)
                elif isinstance(uc_value, str):
                    # If pyexiv2 returns a string, try to correct it if it looks like mojibake
                    corrected_uc = self._decode_pyexiv2_usercomment_string(uc_value)
                else:
                    # Fallback for other types
                    corrected_uc = str(uc_value)

                if corrected_uc != uc_value:
                    metadata["EXIF"]["Exif.Photo.UserComment"] = corrected_uc
                    self.logger.debug("Corrected UserComment for %s", Path(file_path).name)

            # Check if we actually found any standard metadata
            has_standard_metadata = any(metadata.values())

            # ENHANCEMENT: For PNG files with no standard metadata, try pypng for text chunks
            if not has_standard_metadata and Path(file_path).suffix.lower() == ".png":
                if PYPNG_AVAILABLE:
                    self.logger.debug("[ImageReader] pyexiv2 found no standard metadata, trying pypng for PNG chunks")
                    pypng_result = self._read_png_chunks_with_pypng(file_path)
                    if pypng_result:
                        # Merge pypng results into metadata dict
                        metadata.update(pypng_result)
                        nfo("[ImageReader] pyexiv2 (enhanced with pypng) successfully read PNG chunks from: %s", Path(file_path).name)
                        return metadata
                    else:
                        nfo("[ImageReader] pyexiv2 + pypng found no metadata in: %s", Path(file_path).name)
                        return None
                else:
                    nfo("[ImageReader] pyexiv2 found no metadata in PNG (pypng not available): %s", Path(file_path).name)
                    return None

            # Standard metadata found
            if has_standard_metadata:
                nfo("[ImageReader] pyexiv2 successfully read metadata from: %s", Path(file_path).name)
                return metadata

            nfo("[ImageReader] pyexiv2 found no metadata in: %s", Path(file_path).name)
            return None

        except Exception:
            self.logger.exception("pyexiv2 error for %s", file_path)
            return None

    def _decode_pyexiv2_usercomment_string(self, data_str: str) -> str:
        """Attempts to decode a pyexiv2-returned UserComment string if it appears mojibaked.
        Specifically targets strings starting with 'charset=Unicode'.
        """
        if data_str.startswith("charset=Unicode"):
            try:
                # Extract the part after 'charset=Unicode '
                prefix_len = len("charset=Unicode ")
                if len(data_str) > prefix_len:
                    unicode_part_str = data_str[prefix_len:]

                    # Convert the string back to bytes using 'latin-1'.
                    # This assumes pyexiv2 has treated each byte of the original
                    # UTF-16LE data as a separate Latin-1 character when forming the string.
                    # Then, decode these bytes as UTF-16LE.
                    return unicode_part_str.encode("latin-1").decode("utf-16le", errors="ignore")
            except Exception as e:
                self.logger.debug("Failed to re-decode UserComment string with charset prefix: %s", e)
        # If it doesn't have the charset prefix or the above failed, return the original string
        return data_str

    def _fallback_to_pillow(self, file_path: str, context: str) -> dict[str, Any] | None:
        """Fallback to Pillow for EXIF reading.

        Args:
            file_path: Path to the image file
            context: Context string for logging

        Returns:
            Metadata dictionary or None if reading failed

        """
        if not PILLOW_AVAILABLE:
            self.logger.warning("Pillow not available for fallback EXIF reading")
            return None

        nfo("[ImageReader] Attempting Pillow fallback for %s: %s", context, Path(file_path).name)

        pillow_exif = self._read_exif_with_pillow(file_path)
        if pillow_exif:
            nfo("[ImageReader] Pillow successfully read EXIF data")
            return {"PILLOW_EXIF": pillow_exif}
        nfo("[ImageReader] Pillow found no EXIF data")
        return None

    @debug_monitor
    def _read_exif_with_pillow(self, file_path: str) -> dict[str, Any] | None:
        """Read EXIF data using Pillow.

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
                    tag_name = TAGS.get(tag_id, "Tag_%s" % tag_id)

                    # Specifically handle UserComment decoding for Pillow fallback
                    if tag_name == "UserComment" and isinstance(value, bytes):
                        value = self._decode_usercomment_bytes(value)
                    elif isinstance(value, bytes):
                        try:
                            value = value.decode("utf-8", errors="replace")
                        except UnicodeDecodeError:
                            value = str(value)

                    exif_data[tag_name] = value

                return exif_data

        except FileNotFoundError:
            self.logger.error("Image file not found: %s", file_path)
            return None
        except OSError as e:
            self.logger.error("OS error reading image %s: %s", file_path, e)
            return None
        except Exception as e:
            self.logger.error("Unexpected error reading image %s: %s", file_path, e, exc_info=True)
            return None

    def _decode_usercomment_bytes(self, data: bytes) -> str:
        """Try various decoding strategies for UserComment bytes."""
        # NEW STRATEGY: Handle the SwarmUI-style UNICODE header
        # This checks for the UTF-16LE encoding of "UNICODE { "
        swarmui_prefix = b"U\x00N\x00I\x00C\x00O\x00D\x00E\x00 \x00{\x00"

        if data.startswith(swarmui_prefix):
            try:
                # Decode the rest of the data, starting after the prefix
                json_part_bytes = data[len(swarmui_prefix):]
                # The rest of the string is separated by null bytes, so treat as utf-16le
                return json_part_bytes.decode("utf-16le").strip()
            except Exception as e:
                self.logger.debug("Failed to decode UserComment bytes with SwarmUI prefix: %s", e)

        # Strategy 1: Standard Unicode prefix with UTF-16 (for other generators)
        if data.startswith(b"UNICODE\x00\x00"):
            try:
                utf16_data = data[9:]  # Skip "UNICODE\0\0"
                return utf16_data.decode("utf-16le")
            except Exception as e:
                self.logger.debug("Failed to decode UserComment bytes as UTF-16: %s", e)

        # Strategy 2: charset=Unicode prefix (mojibake format)
        if data.startswith(b"charset=Unicode"):
            try:
                unicode_part = data[len(b"charset=Unicode ") :]
                return unicode_part.decode("utf-16le", errors="ignore")
            except Exception as e:
                self.logger.debug("Failed to decode UserComment bytes as UTF-16: %s", e)

        # Strategy 3: Direct UTF-8
        try:
            return data.decode("utf-8")
        except Exception as e:
            self.logger.debug("Failed to decode UserComment bytes as UTF-8: %s", e)

        # Strategy 4: Latin-1 (preserves all bytes)
        try:
            return data.decode("latin-1")
        except Exception as e:
            self.logger.debug("Failed to decode UserComment bytes as Latin-1: %s", e)

        # Strategy 5: Ignore errors
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            self.logger.exception("Failed to decode UserComment bytes with errors ignored")
            return ""

    def _log_user_comment_info(self, metadata: dict[str, Any], file_path: str) -> None:
        """Log information about UserComment field for debugging."""
        exif_data = metadata.get("EXIF", {})
        if "Exif.Photo.UserComment" in exif_data:
            uc_value = exif_data["Exif.Photo.UserComment"]
            self.logger.debug("UserComment type for %s: %s", Path(file_path).name, type(uc_value))

        if isinstance(uc_value, str) and uc_value.startswith("charset="):
            self.logger.debug("UserComment appears to be pre-decoded with charset prefix: %s", Path(file_path).name)

    def _read_png_chunks_with_pypng(self, file_path: str) -> dict[str, Any] | None:
        """Read PNG text chunks using pypng library.

        pypng is better at reading large PNG chunks (>50KB) and can handle
        binary chunks that Pillow might struggle with.

        Args:
            file_path: Path to PNG file

        Returns:
            Dictionary with PNG_CHUNKS key containing chunk data, or None
        """
        try:
            with open(file_path, "rb") as f:
                reader = png.Reader(f)

                # Read chunks without decoding image data
                chunks = []
                for chunk_type, chunk_data in reader.chunks():
                    # Decode chunk type from bytes to string
                    chunk_type_str = chunk_type.decode("ascii", errors="ignore") if isinstance(chunk_type, bytes) else chunk_type

                    # Only process text chunks (tEXt, iTXt, zTXt)
                    if chunk_type_str in ("tEXt", "iTXt", "zTXt"):
                        chunks.append({
                            "type": chunk_type_str,
                            "data": chunk_data,
                            "size": len(chunk_data)
                        })

                if chunks:
                    self.logger.debug("[ImageReader] pypng found %d text chunks in: %s", len(chunks), Path(file_path).name)

                    # Parse the chunks into readable format
                    parsed_chunks = {}
                    for chunk in chunks:
                        chunk_type = chunk["type"]
                        chunk_data = chunk["data"]

                        try:
                            # tEXt chunks: keyword\0text
                            if chunk_type == "tEXt":
                                null_idx = chunk_data.find(b"\x00")
                                if null_idx > 0:
                                    keyword = chunk_data[:null_idx].decode("latin-1")
                                    text = chunk_data[null_idx + 1:].decode("latin-1", errors="replace")
                                    parsed_chunks[keyword] = text

                            # iTXt chunks: keyword\0compression_flag\0compression_method\0language\0translated_keyword\0text
                            elif chunk_type == "iTXt":
                                null_idx = chunk_data.find(b"\x00")
                                if null_idx > 0:
                                    keyword = chunk_data[:null_idx].decode("utf-8")
                                    # Skip compression flag and method, just get the text
                                    # Simplified parsing - just decode as UTF-8
                                    text_start = chunk_data.find(b"\x00", null_idx + 3)
                                    if text_start > 0:
                                        text = chunk_data[text_start + 1:].decode("utf-8", errors="replace")
                                        parsed_chunks[keyword] = text

                            # zTXt chunks: keyword\0compression_method\0compressed_text
                            elif chunk_type == "zTXt":
                                import zlib
                                null_idx = chunk_data.find(b"\x00")
                                if null_idx > 0:
                                    keyword = chunk_data[:null_idx].decode("latin-1")
                                    # Skip compression method byte, decompress rest
                                    compressed_text = chunk_data[null_idx + 2:]
                                    text = zlib.decompress(compressed_text).decode("utf-8", errors="replace")
                                    parsed_chunks[keyword] = text

                        except Exception as e:
                            self.logger.debug("[ImageReader] Failed to parse %s chunk: %s", chunk_type, e)
                            continue

                    if parsed_chunks:
                        nfo("[ImageReader] pypng successfully extracted %d text chunks", len(parsed_chunks))
                        return {"PNG_CHUNKS": parsed_chunks}

                self.logger.debug("[ImageReader] pypng found no text chunks in: %s", Path(file_path).name)
                return None

        except Exception as e:
            self.logger.debug("[ImageReader] pypng extraction failed for %s: %s", Path(file_path).name, e)
            return None

    def get_supported_formats(self) -> set[str]:
        """Get the set of supported image formats."""
        return self.supported_formats.copy()


class ImageMetadataExtractor:
    """High-level interface for extracting specific metadata from images.

    This class provides convenient methods for getting common metadata
    without needing to know the internal structure. Like having preset
    actions on your hotbar! 🎮
    """

    def __init__(self, reader: ImageMetadataReader | None = None):
        """Initialize the extractor.

        Args:
            reader: ImageMetadataReader instance to use

        """
        self.reader = reader or ImageMetadataReader()
        self.logger = get_logger(f"{__name__}.ImageMetadataExtractor")

    def extract_ai_generation_data(self, file_path: str) -> str | None:
        """Extract AI generation parameters from image metadata.

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

    def extract_basic_info(self, file_path: str) -> dict[str, Any]:
        """Extract basic image information.

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
                except Exception as e:
                    self.logger.debug("Error getting image size for %s: %s", file_path, e)

            # Check for metadata presence
            metadata = self.reader.read_metadata(file_path)
            if metadata:
                info["has_exif"] = bool(metadata.get("EXIF") or metadata.get("PILLOW_EXIF"))
                info["has_xmp"] = bool(metadata.get("XMP"))
                info["has_iptc"] = bool(metadata.get("IPTC"))

        except Exception as e:
            self.logger.debug("Error extracting basic info from %s: %s", file_path, e)

        return info


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def read_image_metadata(file_path: str) -> dict[str, Any] | None:
    """Convenience function to read image metadata.

    Args:
        file_path: Path to the image file

    Returns:
        Metadata dictionary or None

    """
    reader = ImageMetadataReader()
    return reader.read_metadata(file_path)


def extract_ai_parameters(file_path: str) -> str | None:
    """Convenience function to extract AI generation parameters.

    Args:
        file_path: Path to the image file

    Returns:
        AI parameters string or None

    """
    extractor = ImageMetadataExtractor()
    return extractor.extract_ai_generation_data(file_path)


def get_image_info(file_path: str) -> dict[str, Any]:
    """Convenience function to get basic image information.

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


def test_image_metadata_reader() -> None:
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
