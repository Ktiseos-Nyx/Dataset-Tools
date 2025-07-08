# dataset_tools/metadata_engine/context_preparation.py

"""Context data preparation module for metadata extraction.

This module handles the preparation of context data from various file types,
including images, JSON files, model files, and text files. It's like the
pre-processing stage that gathers all the raw materials before parsing.

Think of this as your crafting material preparation in FFXIV - gathering
all the components before you start the actual synthesis! 🔨✨
"""

import contextlib
import gc
import json
import logging
from pathlib import Path
from typing import Any, BinaryIO, Union

import piexif  # type: ignore
import piexif.helper  # type: ignore
from PIL import Image, UnidentifiedImageError  # type: ignore

from ..logger import get_logger

# Type aliases for better readability
ContextData = dict[str, Any]
FileInput = Union[str, Path, BinaryIO]


class ContextDataPreparer:
    """Prepares context data from various file types for metadata parsing.

    This class extracts all available metadata and file information into
    a standardized context dictionary that can be used by parsers.
    """

    def __init__(self, log: logging.Logger | None = None):
        """Initialize the context data preparer."""
        self.logger = log or get_logger("ContextDataPreparer")

    def prepare_context(self, file_input: FileInput) -> ContextData | None:
        """Prepare context data from a file input.

        Args:
            file_input: File path string, Path object, or BinaryIO object

        Returns:
            Context data dictionary or None if preparation failed

        """
        context = self._initialize_context(file_input)

        try:
            # Try to process as image first
            return self._process_as_image(file_input, context)
        except (FileNotFoundError, UnidentifiedImageError):
            # Not an image or file not found, try other formats
            return self._process_as_non_image(file_input, context)
        except Exception as e:
            self.logger.error(
                f"Error preparing context for {context['file_path_original']}: {e}",
                exc_info=True,
            )
            return None

    def _initialize_context(self, file_input: FileInput) -> ContextData:
        """Initialize the base context structure."""
        return {
            "pil_info": {},
            "exif_dict": {},
            "xmp_string": None,
            "parsed_xmp_dict": None,
            "png_chunks": {},
            "file_format": "",
            "width": 0,
            "height": 0,
            "raw_user_comment_str": None,
            "software_tag": None,
            "file_extension": "",
            "raw_file_content_text": None,
            "raw_file_content_bytes": None,
            "parsed_root_json_object": None,
            "safetensors_metadata": None,
            "safetensors_main_header": None,
            "gguf_metadata": None,
            "gguf_main_header": None,
            "file_path_original": self._get_file_path_string(file_input),
        }

    def _get_file_path_string(self, file_input: FileInput) -> str:
        """Extract a string representation of the file path."""
        if hasattr(file_input, "name") and file_input.name:
            return str(file_input.name)
        return str(file_input)

    def _process_as_image(self, file_input: FileInput, context: ContextData) -> ContextData:
        """Process the input as an image file with memory optimization."""
        self.logger.debug(f"Processing as image: {context['file_path_original']}")

        # Memory-optimized image processing
        try:
            # First pass: get basic info without loading pixels
            with Image.open(file_input) as img:
                # Check image size before full processing
                if img.width * img.height > 50_000_000:  # ~50MP limit (catches rare phone cameras)
                    self.logger.warning(
                        f"Large image detected ({img.width}x{img.height}), using minimal processing. For full metadata extraction on very large images, consider using exiftool or similar specialized tools."
                    )
                    return self._process_large_image_minimal(img, context)

                # Verify image is valid without loading pixel data
                try:
                    img.verify()
                except Exception as e:
                    self.logger.error(f"Image verification failed: {e}")
                    raise

            # Second pass: full processing for reasonable-sized images
            with Image.open(file_input) as img:
                # Basic image info
                context["pil_info"] = img.info.copy() if img.info else {}
                context["width"] = img.width
                context["height"] = img.height
                context["file_format"] = img.format.upper() if img.format else ""

            # File extension
            image_filename = getattr(img, "filename", None)
            if image_filename:
                context["file_extension"] = Path(image_filename).suffix.lstrip(".").lower()
            elif isinstance(file_input, (str, Path)):
                context["file_extension"] = Path(str(file_input)).suffix.lstrip(".").lower()

            # EXIF data processing
            self._extract_exif_data(context)

            # XMP data processing
            self._extract_xmp_data(context)

            # PNG chunks processing
            self._extract_png_chunks(context)

        except MemoryError as e:
            self.logger.error(
                f"Memory error processing image: {e}. Image too large for our processing capabilities - try using exiftool for metadata extraction on very large files."
            )
            # Try minimal processing as fallback
            return self._process_large_image_minimal_fallback(file_input, context)
        finally:
            # Force garbage collection after processing large images
            gc.collect()

        return context

    def _process_large_image_minimal(self, img: Image.Image, context: ContextData) -> ContextData:
        """Process large images with minimal memory usage."""
        # Only extract essential metadata without loading pixel data
        context["pil_info"] = img.info.copy() if img.info else {}
        context["width"] = img.width
        context["height"] = img.height
        context["file_format"] = img.format.upper() if img.format else ""

        # File extension handling
        image_filename = getattr(img, "filename", None)
        if image_filename:
            context["file_extension"] = Path(image_filename).suffix.lstrip(".").lower()

        # Extract only critical metadata (EXIF, PNG chunks) without deep processing
        self._extract_minimal_metadata(context)

        self.logger.info(f"Completed minimal processing for large image: {context['width']}x{context['height']}")
        return context

    def _process_large_image_minimal_fallback(self, file_input: FileInput, context: ContextData) -> ContextData:
        """Fallback minimal processing when memory errors occur."""
        try:
            # Try to get just basic info using PIL's lazy loading
            with Image.open(file_input) as img:
                context["width"] = img.width
                context["height"] = img.height
                context["file_format"] = img.format.upper() if img.format else ""
                # Don't copy img.info to avoid memory issues
                context["pil_info"] = {}

            self.logger.info("Fallback minimal processing completed")
        except Exception as e:
            self.logger.error(f"Even minimal processing failed: {e}")
            # Set defaults
            context.update({"width": 0, "height": 0, "file_format": "", "pil_info": {}})

        return context

    def _extract_minimal_metadata(self, context: ContextData) -> None:
        """Extract only essential metadata for large images."""
        # Only extract EXIF if present, skip deep UserComment processing
        exif_bytes = context["pil_info"].get("exif")
        if exif_bytes:
            try:
                loaded_exif = piexif.load(exif_bytes)
                # Only extract software tag, skip UserComment for large images
                sw_bytes = loaded_exif.get("0th", {}).get(piexif.ImageIFD.Software)
                if sw_bytes and isinstance(sw_bytes, bytes):
                    context["software_tag"] = sw_bytes.decode("ascii", "ignore").strip("\x00").strip()
            except Exception as e:
                self.logger.debug(f"Minimal EXIF extraction failed: {e}")

        # Extract PNG chunks if they exist (these are usually small)
        for key, val in context["pil_info"].items():
            if isinstance(val, str) and len(val) < 100000:  # Only small chunks
                if "png_chunks" not in context:
                    context["png_chunks"] = {}
                context["png_chunks"][key] = val

    def _extract_exif_data(self, context: ContextData) -> None:
        """Extract EXIF data from PIL info with enhanced UserComment handling."""
        exif_bytes = context["pil_info"].get("exif")
        if not exif_bytes:
            return

        try:
            loaded_exif = piexif.load(exif_bytes)
            context["exif_dict"] = loaded_exif

            # User comment extraction with enhanced handling
            uc_bytes = loaded_exif.get("Exif", {}).get(piexif.ExifIFD.UserComment)
            self.logger.debug(f"EXIF UserComment raw bytes (uc_bytes): {uc_bytes[:50] if uc_bytes else 'None'}...")
            if uc_bytes:
                # Try standard piexif extraction first
                try:
                    user_comment = piexif.helper.UserComment.load(uc_bytes)
                    self.logger.debug(
                        f"piexif.helper.UserComment.load result: {user_comment[:50] if user_comment else 'None'}..."
                    )
                    if user_comment and len(user_comment.strip()) > 0:
                        context["raw_user_comment_str"] = user_comment
                        self.logger.debug(f"Standard EXIF UserComment extracted: {len(user_comment)} chars")
                    else:
                        # Empty or whitespace-only result, try robust decoding
                        self.logger.debug(
                            "Standard piexif UserComment empty or whitespace-only, trying robust decoding."
                        )
                        decoded_uc = self._decode_usercomment_bytes_robust(uc_bytes)
                        self.logger.debug(
                            f"Robust decoder input (uc_bytes): {uc_bytes[:50] if uc_bytes else 'None'}..."
                        )
                        self.logger.debug(f"Robust decoder output: {decoded_uc[:50] if decoded_uc else 'None'}...")
                        if decoded_uc:
                            context["raw_user_comment_str"] = decoded_uc
                            self.logger.debug(f"Robust UserComment extracted: {len(decoded_uc)} chars")
                except Exception as e:
                    self.logger.debug(f"Standard UserComment extraction failed: {e}, trying robust method")
                    decoded_uc = self._decode_usercomment_bytes_robust(uc_bytes)
                    self.logger.debug(f"Robust decoder input (uc_bytes): {uc_bytes[:50] if uc_bytes else 'None'}...")
                    self.logger.debug(f"Robust decoder output: {decoded_uc[:50] if decoded_uc else 'None'}...")
                    if decoded_uc:
                        context["raw_user_comment_str"] = decoded_uc
                        self.logger.debug(f"Robust UserComment extracted: {len(decoded_uc)} chars")
            else:
                self.logger.debug("No uc_bytes found from piexif. Trying PIL getexif() as fallback.")
                # No UserComment in piexif, try PIL's getexif() which might have already decoded it
                self._extract_usercomment_from_pil_getexif(context)

            # Software tag extraction
            sw_bytes = loaded_exif.get("0th", {}).get(piexif.ImageIFD.Software)
            if sw_bytes and isinstance(sw_bytes, bytes):
                context["software_tag"] = sw_bytes.decode("ascii", "ignore").strip("\x00").strip()

        except Exception as e:
            self.logger.debug(f"Failed to extract EXIF data: {e}")
            # Try PIL getexif as complete fallback
            self._extract_usercomment_from_pil_getexif(context)

        self.logger.debug(
            f"Final raw_user_comment_str in context: {context['raw_user_comment_str'][:50] if context['raw_user_comment_str'] else 'None'}..."
        )

    def _extract_usercomment_from_pil_getexif(self, context: ContextData) -> None:
        """Extract UserComment using PIL's getexif() method which can handle some Unicode cases directly."""
        file_path = context.get("file_path_original")
        if not file_path:
            return

        try:
            with Image.open(file_path) as img:
                exif_data = img.getexif()
                if exif_data:
                    user_comment = exif_data.get(37510)  # UserComment tag
                    if user_comment:
                        if isinstance(user_comment, str):
                            # PIL already decoded it successfully
                            context["raw_user_comment_str"] = user_comment
                            self.logger.debug(f"PIL getexif UserComment extracted: {len(user_comment)} chars")

                            # If this is a large ComfyUI JSON, also try to parse it
                            if user_comment.startswith('{"') and '"prompt":' in user_comment:
                                try:
                                    import json

                                    workflow_data = json.loads(user_comment)
                                    context["comfyui_workflow_json"] = workflow_data
                                    self.logger.debug("Parsed ComfyUI workflow JSON from PIL getexif")
                                except json.JSONDecodeError:
                                    self.logger.debug(
                                        "PIL getexif UserComment contains JSON-like data but failed to parse"
                                    )

                        elif isinstance(user_comment, bytes):
                            # PIL returned raw bytes, try robust decoding
                            decoded = self._decode_usercomment_bytes_robust(user_comment)
                            if decoded:
                                context["raw_user_comment_str"] = decoded
                                self.logger.debug(f"PIL getexif robust UserComment extracted: {len(decoded)} chars")

                                # Check for ComfyUI JSON
                                if decoded.startswith('{"') and '"prompt":' in decoded:
                                    try:
                                        import json

                                        workflow_data = json.loads(decoded)
                                        context["comfyui_workflow_json"] = workflow_data
                                        self.logger.debug("Parsed ComfyUI workflow JSON from PIL getexif robust")
                                    except json.JSONDecodeError:
                                        self.logger.debug(
                                            "PIL getexif robust UserComment contains JSON-like data but failed to parse"
                                        )
                        else:
                            self.logger.debug(f"PIL getexif UserComment unexpected type: {type(user_comment)}")
                else:
                    self.logger.debug("No EXIF data found in PIL getexif")
                    # Final fallback to manual extraction
                    self._extract_usercomment_enhanced(context)

        except Exception as e:
            self.logger.debug(f"PIL getexif extraction failed: {e}")
            # Final fallback to manual extraction
            self._extract_usercomment_enhanced(context)

    def _extract_usercomment_enhanced(self, context: ContextData) -> None:
        """Enhanced UserComment extraction using robust PIL-based decoding for problematic cases."""
        file_path = context.get("file_path_original")
        if not file_path:
            return

        # Use robust PIL-based extraction (no external dependencies)
        self._extract_usercomment_manual_unicode(context)

    def _extract_usercomment_manual_unicode(self, context: ContextData) -> None:
        """Manual Unicode UserComment extraction using robust decoding strategies."""
        try:
            file_path = context.get("file_path_original")
            if not file_path:
                return

            # Try to get raw UserComment bytes directly from PIL
            with Image.open(file_path) as img:
                exif_data = img.getexif()
                if exif_data:
                    user_comment_raw = exif_data.get(37510)  # UserComment tag
                    if user_comment_raw and isinstance(user_comment_raw, bytes):
                        # Use the same robust decoding as the main path
                        decoded = self._decode_usercomment_bytes_robust(user_comment_raw)
                        if decoded:
                            context["raw_user_comment_str"] = decoded
                            self.logger.debug(f"Manual robust UserComment extracted: {len(decoded)} chars")

                            # If this is a large ComfyUI JSON, also try to parse it
                            if decoded.startswith('{"') and '"prompt":' in decoded:
                                try:
                                    import json

                                    workflow_data = json.loads(decoded)
                                    context["comfyui_workflow_json"] = workflow_data
                                    self.logger.debug("Parsed ComfyUI workflow JSON from manual extraction")
                                except json.JSONDecodeError:
                                    self.logger.debug("UserComment contains JSON-like data but failed to parse")

        except Exception as e:
            self.logger.debug(f"Manual Unicode extraction failed: {e}")

    def _decode_usercomment_bytes_robust(self, data: bytes) -> str:
        """Try various decoding strategies for UserComment bytes."""
        # Strategy 1: Unicode prefix with UTF-16
        if data.startswith(b"UNICODE\x00\x00"):
            try:
                utf16_data = data[9:]  # Skip "UNICODE\0\0"
                return utf16_data.decode("utf-16le")
            except Exception as e:
                self.logger.debug(f"Failed to decode UserComment bytes as UTF-16: {e}")

        # Strategy 2: charset=Unicode prefix (mojibake format)
        if data.startswith(b"charset=Unicode"):
            try:
                unicode_part = data[len(b"charset=Unicode ") :]
                return unicode_part.decode("utf-16le", errors="ignore")
            except Exception as e:
                self.logger.debug(f"Failed to decode UserComment bytes as UTF-16 (charset): {e}")

        # Strategy 3: Direct UTF-8
        try:
            return data.decode("utf-8")
        except Exception as e:
            self.logger.debug(f"Failed to decode UserComment bytes as UTF-8: {e}")

        # Strategy 4: Latin-1 (preserves all bytes)
        try:
            return data.decode("latin-1")
        except Exception as e:
            self.logger.debug(f"Failed to decode UserComment bytes as Latin-1: {e}")

        # Strategy 5: Ignore errors
        try:
            return data.decode("utf-8", errors="ignore")
        except:
            return ""

    def _extract_xmp_data(self, context: ContextData) -> None:
        """Extract XMP data from PIL info."""
        xmp_str = context["pil_info"].get("XML:com.adobe.xmp")
        if xmp_str:
            context["xmp_string"] = xmp_str
            # TODO: Parse XMP into structured format if needed

    def _extract_png_chunks(self, context: ContextData) -> None:
        """Extract PNG text chunks from PIL info."""
        for key, val in context["pil_info"].items():
            if isinstance(val, str):
                context["png_chunks"][key] = val

        # Ensure UserComment is in png_chunks if it exists
        if "UserComment" in context["pil_info"] and "UserComment" not in context["png_chunks"]:
            context["png_chunks"]["UserComment"] = context["pil_info"]["UserComment"]

    def _process_as_non_image(self, file_input: FileInput, context: ContextData) -> ContextData | None:
        """Process the input as a non-image file."""
        self.logger.info(f"Processing as non-image: {context['file_path_original']}")

        # Determine file extension and format
        file_path = Path(context["file_path_original"])
        context["file_extension"] = file_path.suffix.lstrip(".").lower()
        context["file_format"] = context["file_extension"].upper()

        # Process based on file type
        if context["file_extension"] == "json":
            return self._process_json_file(file_input, context)
        if context["file_extension"] == "txt":
            return self._process_text_file(file_input, context)
        if context["file_extension"] == "safetensors":
            return self._process_safetensors_file(file_input, context)
        if context["file_extension"] == "gguf":
            return self._process_gguf_file(file_input, context)
        self.logger.info(f"File extension '{context['file_extension']}' not specifically handled")
        # Try to read as binary for generic processing
        self._read_as_binary(file_input, context)
        return context

    def _process_json_file(self, file_input: FileInput, context: ContextData) -> ContextData:
        """Process a JSON file with memory limits."""
        try:
            # Limit JSON files to 50MB to prevent memory issues
            content_str = self._read_file_content(file_input, mode="r", encoding="utf-8", max_size=50_000_000)
            context["raw_file_content_text"] = content_str

            # Parse JSON with memory error handling
            try:
                context["parsed_root_json_object"] = json.loads(content_str)
                self.logger.debug("Successfully parsed JSON file")
            except MemoryError as e:
                self.logger.error(f"JSON file too large to parse: {e}")
                # Keep the raw text but skip parsing
                context["parsed_root_json_object"] = None

        except (json.JSONDecodeError, OSError, UnicodeDecodeError, TypeError) as e:
            self.logger.error(f"Failed to process JSON file: {e}")
            # Try to read as text anyway with size limit
            with contextlib.suppress(Exception):
                context["raw_file_content_text"] = self._read_file_content(
                    file_input,
                    mode="r",
                    encoding="utf-8",
                    errors="replace",
                    max_size=10_000_000,
                )

        return context

    def _process_text_file(self, file_input: FileInput, context: ContextData) -> ContextData | None:
        """Process a text file with memory limits."""
        try:
            # Limit text files to 10MB to prevent memory issues
            context["raw_file_content_text"] = self._read_file_content(
                file_input,
                mode="r",
                encoding="utf-8",
                errors="replace",
                max_size=10_000_000,
            )
            self.logger.debug("Successfully read text file")
        except (OSError, UnicodeDecodeError, TypeError) as e:
            self.logger.error(f"Failed to read text file: {e}")
            return None

        return context

    def _process_safetensors_file(self, file_input: FileInput, context: ContextData) -> ContextData:
        """Process a SafeTensors model file."""
        try:
            # Import here to avoid dependency issues if not available
            from ..model_parsers.safetensors_parser import (
                ModelParserStatus,
                SafetensorsParser,
            )

            file_path = context["file_path_original"]
            parser = SafetensorsParser(file_path)
            status = parser.parse()

            if status == ModelParserStatus.SUCCESS:
                context["safetensors_metadata"] = parser.metadata_header
                context["safetensors_main_header"] = parser.main_header
                self.logger.debug("Successfully parsed SafeTensors file")
            else:
                self.logger.warning(f"SafeTensors parser failed: {parser._error_message}")

        except ImportError:
            self.logger.error("SafetensorsParser not available")
        except Exception as e:
            self.logger.error(f"Error processing SafeTensors file: {e}")

        return context

    def _process_gguf_file(self, file_input: FileInput, context: ContextData) -> ContextData:
        """Process a GGUF model file."""
        try:
            # Import here to avoid dependency issues if not available
            try:
                from ..model_parsers.gguf_parser import GGUFParser, ModelParserStatus
            except ImportError:
                self.logger.error("GGUFParser module not found. Skipping GGUF parsing.")
                return context

            file_path = context["file_path_original"]
            parser = GGUFParser(file_path)
            status = parser.parse()

            if status == ModelParserStatus.SUCCESS:
                context["gguf_metadata"] = parser.metadata_header
                context["gguf_main_header"] = parser.main_header
                self.logger.debug("Successfully parsed GGUF file")
            else:
                error_msg = getattr(parser, "error_message", None)
                if error_msg is None:
                    error_msg = getattr(parser, "_error_message", "Unknown error")
                self.logger.warning(f"GGUF parser failed: {error_msg}")
        except Exception as e:
            self.logger.error(f"Error processing GGUF file: {e}")

        return context

    def _read_as_binary(self, file_input: FileInput, context: ContextData) -> None:
        """Read file as binary data with memory limits."""
        with contextlib.suppress(Exception):
            # Limit binary files to 20MB to prevent memory issues
            context["raw_file_content_bytes"] = self._read_file_content(file_input, mode="rb", max_size=20_000_000)

    def _read_file_content(
        self,
        file_input: FileInput,
        mode: str = "r",
        encoding: str | None = "utf-8",
        errors: str | None = "strict",
        max_size: int | None = None,
    ) -> str | bytes:
        """Read file content with proper handling of different input types and memory limits.

        Args:
            file_input: File to read from
            mode: File open mode
            encoding: Text encoding (for text modes)
            errors: Error handling strategy
            max_size: Maximum bytes to read (None for no limit)

        Returns:
            File content as string or bytes

        """
        # Handle BinaryIO objects
        if hasattr(file_input, "read") and hasattr(file_input, "seek"):
            file_input.seek(0)

            if max_size:
                content = file_input.read(max_size)
                if len(content) == max_size:
                    self.logger.warning(f"File truncated to {max_size} bytes due to size limit")
            else:
                content = file_input.read()

            if "b" in mode:
                return content
            # Convert bytes to string if needed
            if isinstance(content, bytes):
                return content.decode(encoding or "utf-8", errors=errors or "strict")
            return content

        # Handle file paths with size checking
        file_path = Path(file_input)

        # Check file size before reading
        try:
            file_size = file_path.stat().st_size
            if max_size and file_size > max_size:
                self.logger.warning(
                    f"File {file_path} ({file_size} bytes) exceeds max_size ({max_size}), reading truncated"
                )
        except OSError:
            pass  # Size check failed, proceed anyway

        open_kwargs = {}
        if "b" not in mode:
            open_kwargs["encoding"] = encoding
            open_kwargs["errors"] = errors

        with open(file_path, mode, **open_kwargs) as f:
            if max_size:
                content = f.read(max_size)
                if len(content) == max_size:
                    self.logger.warning(f"File {file_path} truncated to {max_size} bytes")
                return content
            return f.read()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def prepare_context_data(file_input: FileInput, logger: logging.Logger | None = None) -> ContextData | None:
    """Convenience function to prepare context data from a file.

    Args:
        file_input: File path string, Path object, or BinaryIO object
        logger: Optional logger instance

    Returns:
        Context data dictionary or None if preparation failed

    """
    preparer = ContextDataPreparer(log=logger)
    return preparer.prepare_context(file_input)


def create_test_context() -> ContextData:
    """Create a test context for development and testing."""
    return {
        "pil_info": {
            "parameters": "test prompt\nNegative prompt: test negative\nSteps: 20",
            "Comment": '{"workflow": {"nodes": {}}}',
        },
        "exif_dict": {},
        "xmp_string": None,
        "png_chunks": {"parameters": "test prompt\nSteps: 20"},
        "file_format": "PNG",
        "width": 512,
        "height": 768,
        "raw_user_comment_str": "Steps: 20, Sampler: Euler a",
        "software_tag": "AUTOMATIC1111",
        "file_extension": "png",
        "raw_file_content_text": None,
        "parsed_root_json_object": None,
        "file_path_original": "test_image.png",
    }


if __name__ == "__main__":
    # Basic testing
    logging.basicConfig(level=logging.DEBUG)
    logger = get_logger("ContextPrepTest")

    # Test with a simple context
    test_ctx = create_test_context()
    logger.info(f"Test context created with keys: {list(test_ctx.keys())}")

    preparer = ContextDataPreparer(logger)
    logger.info("Context data preparer ready for testing!")
