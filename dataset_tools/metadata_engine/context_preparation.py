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
from ..model_parsers.safetensors_parser import SafetensorsParser
from ..file_readers.image_metadata_reader import ImageMetadataReader


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
        self.image_metadata_reader = ImageMetadataReader()

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
            # pyexiv2 data (raw and mapped)
            "pyexiv2_exif": {},  # Raw EXIF from pyexiv2 with prefixed keys
            "pyexiv2_xmp": {},   # Raw XMP from pyexiv2 with prefixed keys
            "pyexiv2_iptc": {},  # Raw IPTC from pyexiv2
            "exif_fields": {},   # Mapped EXIF fields (friendly names)
            "xmp_fields": {},    # Mapped XMP fields (friendly names)
        }

    def _get_file_path_string(self, file_input: FileInput) -> str:
        """Extract a string representation of the file path."""
        if hasattr(file_input, "name") and isinstance(file_input.name, str):
            return file_input.name
        return str(file_input)

# --- IN context_preparation.py, REPLACE the entire _process_as_image function with this ---

    def _process_as_image(self, file_input: FileInput, context: ContextData) -> ContextData:
        """Process the input as an image file with a clear, single-pass logic."""
        self.logger.info(f"[CONTEXT_PREP] Processing as image: {context['file_path_original']}")

        with Image.open(file_input) as img:
            context.update(
                {
                    "pil_info": img.info.copy() if img.info else {},
                    "width": img.width,
                    "height": img.height,
                    "file_format": img.format.upper() if img.format else "",
                }
            )

            # ============================================================================
            # >>> START OF NEW CODE BLOCK: WEBP EXIF BLOB NORMALIZER <<<
            # This is our surgical fix. It checks for the specific case of a WEBP file
            # storing its workflow data inside a raw 'exif' byte string.
            # ============================================================================
            if context["file_format"] == "WEBP" and "exif" in context["pil_info"] and isinstance(context["pil_info"]["exif"], bytes):
                self.logger.info("[CONTEXT_PREP] Detected WEBP with raw EXIF blob. Attempting to normalize...")
                try:
                    # Decode the entire byte string, ignoring errors from binary parts.
                    exif_data_str = context["pil_info"]["exif"].decode("utf-8", errors="ignore")

                    # Use regex to find 'workflow:' and 'prompt:' JSON objects within the string.
                    # The \x00 (null byte) is often a reliable terminator.
                    import re

                    workflow_match = re.search(r"workflow:({.*?})\x00", exif_data_str)
                    if workflow_match:
                        workflow_json_str = workflow_match.group(1)
                        # Add the extracted workflow back to pil_info as a clean, separate key.
                        context["pil_info"]["workflow"] = workflow_json_str
                        self.logger.info("Successfully extracted and normalized 'workflow' key from WEBP EXIF blob.")

                    prompt_match = re.search(r"prompt:({.*?})\x00", exif_data_str)
                    if prompt_match:
                        prompt_json_str = prompt_match.group(1)
                        # Add the extracted prompt back to pil_info as a clean, separate key.
                        context["pil_info"]["prompt"] = prompt_json_str
                        self.logger.info("Successfully extracted and normalized 'prompt' key from WEBP EXIF blob.")

                except Exception as e:
                    self.logger.warning(f"[CONTEXT_PREP] Failed to parse workflow/prompt from WEBP EXIF blob: {e}")
            # ============================================================================
            # >>> END OF NEW CODE BLOCK <<<
            # ============================================================================


            self.logger.info(f"[CONTEXT_PREP_DEBUG] PIL info keys after potential normalization: {list(context['pil_info'].keys())}")

            if img.info and "parameters" in img.info:
                param_data = img.info["parameters"]
                self.logger.info(f"[CONTEXT_PREP_DEBUG] Found 'parameters' in PIL info: {param_data[:200] if len(param_data) > 200 else param_data}")

            if img.width * img.height > MAX_IMAGE_PIXELS:
                self.logger.warning(
                    f"Large image ({img.width}x{img.height}) detected. Performing minimal metadata extraction."
                )
                self._extract_minimal_metadata(context)
                return context

            self._extract_exif_data(context)
            self._extract_xmp_data(context)
            self._extract_pyexiv2_metadata(context)

            # --- IPTC Data Extraction ---
            try:
                from PIL import IptcImagePlugin
                iptc_data = IptcImagePlugin.getiptcinfo(img)
                if iptc_data:
                    self.logger.info(f"[CONTEXT_PREP] Found {len(iptc_data)} IPTC fields.")
                    context["iptc_data"] = {}
                    for key, value in iptc_data.items():
                        if isinstance(value, bytes):
                            decoded_value = value.decode("utf-8", errors="ignore").strip()
                            context["iptc_data"][key] = decoded_value
                            # Mochi parser needs these specifically
                            if key == (2, 120): # Caption-Abstract
                                context["raw_user_comment_str"] = decoded_value
                            if key == (2, 105): # OriginatingProgram
                                context["iptc_originating_program"] = decoded_value
                        else:
                            context["iptc_data"][key] = value
            except Exception as e:
                self.logger.debug(f"Could not process IPTC data: {e}")

            self._extract_png_chunks(context)
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
                            f"[CONTEXT_PREP_DEBUG] Successfully decoded UserComment: {len(user_comment)} chars - starts with: {user_comment[:100]}"
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

            # Fallback: Check if raw EXIF bytes contain embedded JSON workflow
            # This handles cases where ComfyUI workflows are stored directly in EXIF without UserComment
            if not context.get("raw_user_comment_str") and exif_bytes:
                json_workflow = self._extract_json_from_raw_exif(exif_bytes)
                if json_workflow:
                    context["raw_user_comment_str"] = json_workflow
                    self.logger.info(f"Extracted JSON workflow from raw EXIF: {len(json_workflow)} chars")

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

    def _extract_json_from_raw_exif(self, exif_bytes: bytes) -> str:
        """Extract JSON workflow from raw EXIF bytes when not stored in UserComment.

        Some ComfyUI workflows are embedded directly in EXIF data after headers,
        as seen in certain JPEG files where the workflow appears after JFIF/MM headers.
        """
        if not exif_bytes or len(exif_bytes) < 50:
            return ""

        try:
            # Convert to string and look for JSON patterns
            exif_str = exif_bytes.decode("utf-8", errors="ignore")

            # Look for ComfyUI JSON patterns - workflows typically start with {"prompt": {
            json_patterns = [
                '{"prompt":',
                '{"workflow":',
                '{"1":',  # Node IDs often start with "1"
                '{"nodes":',
            ]

            for pattern in json_patterns:
                json_start = exif_str.find(pattern)
                if json_start >= 0:
                    # Found potential JSON, try to extract it
                    potential_json = exif_str[json_start:]

                    # Find the end of the JSON by counting braces
                    brace_count = 0
                    json_end = -1
                    in_string = False
                    escaped = False

                    for i, char in enumerate(potential_json):
                        if escaped:
                            escaped = False
                            continue
                        if char == "\\" and in_string:
                            escaped = True
                            continue
                        if char == '"' and not escaped:
                            in_string = not in_string
                            continue
                        if not in_string:
                            if char == "{":
                                brace_count += 1
                            elif char == "}":
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = i + 1
                                    break

                    if json_end > 0:
                        json_candidate = potential_json[:json_end]
                        # Validate it's actually valid JSON
                        try:
                            parsed = json.loads(json_candidate)
                            # Check if it looks like a ComfyUI workflow
                            if (isinstance(parsed, dict) and
                                (any(key in parsed for key in ["prompt", "workflow", "nodes"]) or
                                 any(isinstance(v, dict) and "class_type" in v for v in parsed.values()))):
                                self.logger.debug(f"Found valid ComfyUI JSON in raw EXIF: {len(json_candidate)} chars")
                                return json_candidate
                        except json.JSONDecodeError:
                            continue  # Try next pattern

            return ""

        except Exception as e:
            self.logger.debug(f"Failed to extract JSON from raw EXIF: {e}")
            return ""

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
                    try:
                        # Try parsing directly first
                        parsed_json = json.loads(source_str)
                    except json.JSONDecodeError:
                        # If direct parsing fails, try unescaping backslashes
                        try:
                            unescaped_str = source_str.encode("utf-8").decode("unicode_escape")
                            parsed_json = json.loads(unescaped_str)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # Still not valid JSON, or unescaping failed
                            continue  # Not a valid JSON, try the next source
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

    def _extract_pyexiv2_metadata(self, context: ContextData) -> None:
        """Extract rich EXIF/XMP metadata using pyexiv2 and map to friendly field names."""
        file_path = context.get("file_path_original")
        if not file_path:
            return

        try:
            # Use ImageMetadataReader to get pyexiv2 data
            metadata = self.image_metadata_reader.read_metadata(file_path)
            if not metadata:
                self.logger.debug(f"[PYEXIV2] No metadata extracted for: {file_path}")
                return

            # Store raw pyexiv2 data
            context["pyexiv2_exif"] = metadata.get("EXIF", {})
            context["pyexiv2_xmp"] = metadata.get("XMP", {})
            context["pyexiv2_iptc"] = metadata.get("IPTC", {})

            # Map EXIF fields to friendly names
            context["exif_fields"] = self._map_exif_fields(context["pyexiv2_exif"])

            # Map XMP fields to friendly names
            context["xmp_fields"] = self._map_xmp_fields(context["pyexiv2_xmp"])

            self.logger.info(
                f"[PYEXIV2] Extracted {len(context['exif_fields'])} EXIF fields, "
                f"{len(context['xmp_fields'])} XMP fields from: {Path(file_path).name}"
            )

        except Exception as e:
            self.logger.debug(f"[PYEXIV2] Error extracting metadata: {e}")

    def _map_exif_fields(self, exif_data: dict) -> dict:
        """Map pyexiv2 EXIF keys to friendly field names.

        Example: "Exif.Photo.UserComment" -> "UserComment"
                 "Exif.Image.Make" -> "Make"
        """
        mapped = {}
        for key, value in exif_data.items():
            # Strip the "Exif.X." prefix to get friendly name
            if key.startswith("Exif."):
                # Remove "Exif.Photo." or "Exif.Image." prefix
                friendly_name = key.split(".")[-1]  # Get last part after final dot
                mapped[friendly_name] = value
            else:
                # Keep unmapped fields as-is
                mapped[key] = value
        return mapped

    def _map_xmp_fields(self, xmp_data: dict) -> dict:
        """Map pyexiv2 XMP keys to friendly field names.

        Example: "Xmp.dc.creator" -> "creator"
                 "Xmp.xmp.CreateDate" -> "CreateDate"
        """
        mapped = {}
        for key, value in xmp_data.items():
            # Strip the "Xmp.X." prefix to get friendly name
            if key.startswith("Xmp."):
                # Remove "Xmp.namespace." prefix
                friendly_name = key.split(".")[-1]  # Get last part after final dot
                mapped[friendly_name] = value
            else:
                # Keep unmapped fields as-is
                mapped[key] = value
        return mapped

    def _extract_png_chunks(self, context: ContextData) -> None:
        """Extract PNG text chunks from PIL info."""
        self.logger.info(f"[CONTEXT_PREP_DEBUG] _extract_png_chunks called, pil_info has {len(context.get('pil_info', {}))} items")

        for key, val in context["pil_info"].items():
            if isinstance(val, str):
                context["png_chunks"][key] = val
                self.logger.info(f"[CONTEXT_PREP_DEBUG] Added PNG chunk: {key} = {val[:100] if len(val) > 100 else val}")

        # Ensure UserComment is in png_chunks if it exists
        if "UserComment" in context["pil_info"] and "UserComment" not in context["png_chunks"]:
            context["png_chunks"]["UserComment"] = context["pil_info"]["UserComment"]

        self.logger.info(f"[CONTEXT_PREP_DEBUG] Final png_chunks keys: {list(context['png_chunks'].keys())}")

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
            parser = SafetensorsParser(context["file_path_original"])
            if parser.parse():
                context["safetensors_metadata"] = parser.metadata_header
                if parser.civitai_api_info:
                    context["civitai_api_info"] = parser.civitai_api_info
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
            from ..model_parsers.gguf_parser import GGUFParser

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
