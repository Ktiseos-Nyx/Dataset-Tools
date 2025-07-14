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

import piexif
import piexif.helper
from PIL import Image, UnidentifiedImageError

from ..logger import get_logger

# Type aliases
ContextData = dict[str, Any]
FileInput = Union[str, Path, BinaryIO]

# --- SUGGESTION: Define constants for limits ---
MAX_IMAGE_PIXELS = 64_000_000  # 64MP limit
MAX_JSON_SIZE = 50 * 1024 * 1024  # 50MB
MAX_TEXT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_BINARY_SIZE = 20 * 1024 * 1024  # 20MB


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
        self.logger.info(f"[CONTEXT_PREP] Starting context preparation for: {context.get('file_path_original')}")
        try:
            # First, attempt to process as an image, as they contain the most diverse metadata
            result = self._process_as_image(file_input, context)
            self.logger.info(f"[CONTEXT_PREP] Successfully processed as image: {context.get('file_path_original')}")
            return result
        except (FileNotFoundError, UnidentifiedImageError, OSError) as e:
            # If it fails, it's either not an image or the file is inaccessible
            # Proceed to process as a non-image file type (JSON, TXT, etc.)
            self.logger.info(
                f"[CONTEXT_PREP] Failed as image ({e}), trying as non-image: {context.get('file_path_original')}"
            )
            result = self._process_as_non_image(file_input, context)
            self.logger.info(f"[CONTEXT_PREP] Successfully processed as non-image: {context.get('file_path_original')}")
            return result
        except Exception as e:
            self.logger.error(
                f"[CONTEXT_PREP] Unhandled error preparing context for {context.get('file_path_original')}: {e}",
                exc_info=True,
            )
            return None
        finally:
            gc.collect()  # Good practice to force GC after any file processing

    def _initialize_context(self, file_input: FileInput) -> ContextData:
        """Initialize the base context structure."""
        path_str = self._get_file_path_string(file_input)
        return {
            "file_path_original": path_str,
            "file_extension": Path(path_str).suffix.lstrip(".").lower(),
            "file_format": "",
            "width": 0,
            "height": 0,
            "pil_info": {},
            "exif_dict": {},
            "png_chunks": {},
            "xmp_string": None,
            "software_tag": None,
            "raw_user_comment_str": None,
            "comfyui_workflow_json": None,  # Add a dedicated key for the parsed workflow
            "raw_file_content_text": None,
            "raw_file_content_bytes": None,
            "safetensors_metadata": None,
            "gguf_metadata": None,
        }

    def _get_file_path_string(self, file_input: FileInput) -> str:
        """Extract a string representation of the file path."""
        if hasattr(file_input, "name") and isinstance(file_input.name, str):
            return file_input.name
        return str(file_input)

    def _process_as_image(self, file_input: FileInput, context: ContextData) -> ContextData:
        """Process the input as an image file with a clear, single-pass logic."""
        self.logger.info(f"[CONTEXT_PREP] Processing as image: {context['file_path_original']}")

        with Image.open(file_input) as img:
            # --- STRENGTHENING: Centralize basic info extraction ---
            context.update(
                {
                    "pil_info": img.info.copy() if img.info else {},
                    "width": img.width,
                    "height": img.height,
                    "file_format": img.format.upper() if img.format else "",
                }
            )

            # Handle extremely large images by stopping early
            if img.width * img.height > MAX_IMAGE_PIXELS:
                self.logger.warning(
                    f"Large image ({img.width}x{img.height}) detected. Performing minimal metadata extraction."
                )
                self._extract_minimal_metadata(context)
                return context

            # --- STRENGTHENING: Structured metadata extraction flow ---
            # For normal-sized images, extract everything possible.
            self._extract_exif_data(context)
            self._extract_xmp_data(context)
            self._extract_png_chunks(context)

            # --- STRENGTHENING: Centralized JSON parsing logic ---
            # After all text fields are populated, try to parse the most likely one.
            self._find_and_parse_comfyui_json(context)

        return context

    def _extract_minimal_metadata(self, context: ContextData) -> None:
        """Extract minimal metadata for large images."""
        # For large images, only extract basic info to avoid memory issues
        self.logger.debug("Extracting minimal metadata for large image")
        # Basic PNG chunks that don't require heavy processing
        self._extract_png_chunks(context)

    def _extract_exif_data(self, context: ContextData) -> None:
        """Extract EXIF data, prioritizing the problematic UserComment field."""
        exif_bytes = context["pil_info"].get("exif")
        if not exif_bytes:
            self.logger.info(f"[CONTEXT_PREP] No EXIF data found in PIL info for: {context.get('file_path_original')}")
            return

        self.logger.info(f"[CONTEXT_PREP] Found EXIF data, processing: {context.get('file_path_original')}")

        try:
            loaded_exif = piexif.load(exif_bytes)
            context["exif_dict"] = loaded_exif

            # Software Tag
            sw_bytes = loaded_exif.get("0th", {}).get(piexif.ImageIFD.Software)
            if sw_bytes and isinstance(sw_bytes, bytes):
                context["software_tag"] = sw_bytes.decode("ascii", "ignore").strip("\x00").strip()

            # UserComment Extraction - Use piexif.helper.UserComment.load like SDPR does
            uc_bytes = loaded_exif.get("Exif", {}).get(piexif.ExifIFD.UserComment)
            if uc_bytes:
                self.logger.debug(f"Found UserComment bytes: {len(uc_bytes)} bytes")
                try:
                    # Use piexif's proper UserComment decoder
                    user_comment = piexif.helper.UserComment.load(uc_bytes)
                    if user_comment and user_comment.strip():
                        context["raw_user_comment_str"] = user_comment.strip()
                        self.logger.info(
                            f"Successfully decoded UserComment: {len(user_comment)} chars - starts with: {user_comment[:100]}"
                        )
                    else:
                        self.logger.debug("UserComment decoded but empty")
                except Exception as e:
                    self.logger.debug(f"piexif UserComment.load failed: {e}, trying fallback")
                    # Fallback to custom decoding
                    user_comment = self._decode_usercomment_bytes_robust(uc_bytes)
                    if user_comment:
                        context["raw_user_comment_str"] = user_comment
                        self.logger.info(f"Fallback decoded UserComment: {len(user_comment)} chars")
            else:
                self.logger.debug("No UserComment found in EXIF data")

        except Exception as e:
            self.logger.debug(f"Could not load EXIF data with piexif: {e}. Some metadata might be missing.")

    def _decode_usercomment_bytes_robust(self, data: bytes) -> str:
        """Try various decoding strategies for UserComment bytes. This is the secret sauce."""
        if not isinstance(data, bytes) or len(data) == 0:
            return ""

        # Strategy 1: Standard encoding prefix (e.g., ASCII, UTF-8, UNICODE)
        # The first 8 bytes often define the encoding, but handle shorter data too
        if len(data) >= 8:
            codec_header = data[:8]
            comment_bytes = data[8:]

            try:
                if codec_header.startswith(b"ASCII\x00"):
                    return comment_bytes.decode("ascii").strip("\x00")
                if codec_header.startswith(b"UNICODE\x00"):  # A common variation for UTF-16
                    return comment_bytes.decode("utf-16le").strip("\x00")
                if codec_header.startswith(b"UTF-8\x00"):
                    return comment_bytes.decode("utf-8").strip("\x00")
                if codec_header.startswith(b"JIS\x00"):  # Support for Japanese encoding
                    return comment_bytes.decode("shift_jis").strip("\x00")
            except UnicodeDecodeError:
                pass  # Fall through to other strategies

        # Strategy 2: Try different encodings to decode properly
        for encoding in ["utf-8", "utf-16le", "utf-16be", "shift_jis", "latin-1"]:
            try:
                # Try with header skipped first (EXIF UserComment often has 8-byte header)
                if len(data) > 8:
                    decoded = data[8:].decode(encoding).strip("\x00").strip()
                    if decoded and len(decoded) > 10:  # Reasonable length
                        return decoded

                # Try full data
                decoded = data.decode(encoding).strip("\x00").strip()
                if decoded and len(decoded) > 10:  # Reasonable length
                    return decoded

            except UnicodeDecodeError:
                continue

        # Final Fallback: Decode with replacement characters to salvage what we can
        return data.decode("utf-8", errors="replace").strip().strip("\x00")

    def _find_and_parse_comfyui_json(self, context: ContextData) -> None:
        """After all metadata is extracted, find the most likely source of ComfyUI
        workflow JSON and parse it.
        """
        # --- STRENGTHENING: Prioritized search for the workflow string ---
        png_chunks = context.get("png_chunks", {})
        potential_sources = [
            context.get("raw_user_comment_str"),  # Highest priority
            png_chunks.get("workflow"),  # ComfyUI's native PNG chunk
            png_chunks.get("prompt"),  # Also used by ComfyUI
            png_chunks.get("parameters"),  # A1111 format, sometimes adopted
        ]

        for source_str in potential_sources:
            if isinstance(source_str, str) and source_str.strip().startswith("{"):
                try:
                    # Found a potential JSON, try to parse it
                    parsed_json = json.loads(source_str)
                    # Check for a key indicator of a ComfyUI workflow
                    if isinstance(parsed_json, dict) and ("nodes" in parsed_json or "prompt" in parsed_json):
                        context["comfyui_workflow_json"] = parsed_json
                        self.logger.debug("Successfully found and parsed ComfyUI workflow JSON.")
                        return  # Stop after finding the first valid workflow
                except (json.JSONDecodeError, TypeError):
                    continue  # Not a valid JSON, try the next source

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
            content_str = self._read_file_content(file_input, mode="r", encoding="utf-8", max_size=MAX_JSON_SIZE)
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
                    max_size=MAX_TEXT_SIZE,
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
                max_size=MAX_TEXT_SIZE,
            )
            self.logger.debug("Successfully read text file")
        except (OSError, UnicodeDecodeError, TypeError) as e:
            self.logger.error(f"Failed to read text file: {e}")
            return None

        return context

    def _process_safetensors_file(self, file_input: FileInput, context: ContextData) -> ContextData:
        """Process a SafeTensors model file."""
        try:
            from ..model_parsers.safetensors_parser import SafetensorsParser

            parser = SafetensorsParser(context["file_path_original"])
            if parser.parse():
                context["safetensors_metadata"] = parser.metadata_header
            else:
                self.logger.warning(f"SafeTensors parser failed: {getattr(parser, 'error_message', 'Unknown error')}")
        except ImportError:
            self.logger.error("SafetensorsParser or its dependencies not available.")
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
            context["raw_file_content_bytes"] = self._read_file_content(file_input, mode="rb", max_size=MAX_BINARY_SIZE)

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
        "comfyui_workflow_json": None,
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
