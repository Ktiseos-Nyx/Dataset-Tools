# dataset_tools/vendored_sdpr/image_data_reader.py
# This is YOUR VENDORED and MODIFIED copy - FUSED VERSION
# (Corrected _try_parser, status logic, defusedxml, logger, and Pylint suggestions)

__author__ = "receyuki"
__filename__ = "image_data_reader.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
import logging  # Standard library
from pathlib import Path  # Standard library
from typing import Any, BinaryIO, TextIO  # Standard library

import piexif  # Third-party
import piexif.helper  # Third-party
from defusedxml import minidom  # Third-party
from PIL import (
    Image,  # Third-party
    UnidentifiedImageError,  # Third-party
)
from PIL.PngImagePlugin import PngInfo  # Third-party

# Local application/library specific
from .constants import PARAMETER_PLACEHOLDER
from .format import (  # Local application/library specific
    A1111,
    BaseFormat,
    CivitaiComfyUIFormat,
    ComfyUI,
    DrawThings,
    EasyDiffusion,
    Fooocus,
    InvokeAI,
    NovelAI,
    RuinedFooocusFormat,
    SwarmUI,
)
from .logger import get_logger  # Local application/library specific


# Pylint disables for class complexity - refactoring these would be major architectural changes
# pylint: disable=too-many-instance-attributes,too-many-public-methods
class ImageDataReader:
    NOVELAI_MAGIC = "stealth_pngcomp"

    def __init__(
        self,
        file_path_or_obj: str | Path | TextIO | BinaryIO,
        is_txt: bool = False,
    ):
        self._height: int = 0
        self._width: int = 0
        self._info: dict[str, Any] = {}
        self._positive: str = ""
        self._negative: str = ""
        self._positive_sdxl: dict[str, Any] = {}
        self._negative_sdxl: dict[str, Any] = {}
        self._setting: str = ""
        self._raw: str = ""
        self._tool: str = ""
        # Ensure BaseFormat.PARAMETER_KEY is accessible and a list
        base_param_key_attr = getattr(BaseFormat, "PARAMETER_KEY", None)
        if isinstance(base_param_key_attr, list):
            self._parameter_key: list[str] = base_param_key_attr
        else:
            self._parameter_key = [
                "model",
                "sampler",
                "seed",
                "cfg",
                "steps",
                "size",
            ]  # Fallback

        self._parameter: dict[str, Any] = dict.fromkeys(
            self._parameter_key,
            PARAMETER_PLACEHOLDER,
        )
        self._is_txt: bool = is_txt
        self._is_sdxl: bool = False
        self._format_str: str = ""
        self._props: str = ""
        self._parser: BaseFormat | None = None
        self._status: BaseFormat.Status = BaseFormat.Status.UNREAD
        self._error: str = ""
        # Corrected logger initialization
        self._logger: logging.Logger = get_logger("DSVendored_SDPR.ImageDataReader")
        self.read_data(file_path_or_obj)

    def _try_parser(self, parser_class: type[BaseFormat], **kwargs: Any) -> bool:
        self._logger.debug(
            f"Attempting parser: {parser_class.__name__} with kwargs: {list(kwargs.keys())}",
        )
        try:
            # Ensure width and height are integers if passed
            if "width" in kwargs and self._width > 0:  # Check if width is valid
                kwargs["width"] = int(self._width)
            if "height" in kwargs and self._height > 0:  # Check if height is valid
                kwargs["height"] = int(self._height)

            temp_parser = parser_class(**kwargs)
            parser_own_status = temp_parser.parse()

            if parser_own_status == BaseFormat.Status.READ_SUCCESS:
                self._parser = temp_parser
                self._tool = getattr(self._parser, "tool", parser_class.__name__)
                self._status = BaseFormat.Status.READ_SUCCESS
                self._error = ""
                self._logger.info(f"Successfully parsed as {self._tool}.")
                return True

            parser_error_msg = getattr(temp_parser, "error", "N/A")
            status_name = (
                parser_own_status.name
                if hasattr(parser_own_status, "name")
                else str(parser_own_status)
            )
            self._logger.debug(
                f"{parser_class.__name__} parsing attempt resulted in status: {status_name}. Error: {parser_error_msg}",
            )
            if parser_error_msg and (
                self._status == BaseFormat.Status.UNREAD or not self._error
            ):
                self._error = parser_error_msg
            return False
        except TypeError as type_err:
            self._logger.error(
                f"TypeError instantiating or calling {parser_class.__name__}: {type_err}. Check __init__/parse signature.",
                exc_info=True,
            )
            if self._status == BaseFormat.Status.UNREAD:
                self._error = f"Init/call error for {parser_class.__name__}: {type_err}"
            return False
        except Exception as general_exception:  # pylint: disable=broad-except
            self._logger.error(
                f"Unexpected exception during {parser_class.__name__} attempt: {general_exception}",
                exc_info=True,  # Log full traceback for unexpected errors
            )
            if self._status == BaseFormat.Status.UNREAD:
                self._error = (
                    f"Runtime error in {parser_class.__name__}: {general_exception}"
                )
            return False

    def _handle_text_file(self, file_obj: TextIO):
        """Process a text file object."""
        self._raw = file_obj.read()
        if self._try_parser(A1111, raw=self._raw):
            # Successfully parsed as A1111
            pass
        else:
            if (
                self._status == BaseFormat.Status.UNREAD
            ):  # If no parser claimed success yet
                self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error:  # If parser didn't set a specific error
                self._error = "Failed to parse text file as A1111 format."
        log_status_name = (
            self._status.name if hasattr(self._status, "name") else str(self._status)
        )
        self._logger.info(
            f"Text file processed. Final Status: {log_status_name}, Tool: {self._tool or 'None'}",
        )

    def _attempt_legacy_swarm_exif(self, image_obj: Image.Image):
        """Attempts to parse SwarmUI legacy EXIF."""
        if self._parser:
            return  # Already parsed
        try:
            exif_pil = image_obj.getexif()
            if exif_pil:
                # DeviceSetting (0x0110) for EXIF_TAGS.MODEL by some old SwarmUI, might be non-standard.
                # Standard UserComment is 0x9286 (ExifIFD.UserComment)
                # Standard ImageDescription is 0x010e (ImageIFD.ImageDescription)
                # Check if this key is correct for Swarm
                exif_json_str = exif_pil.get(0x0110)
                if exif_json_str:
                    exif_dict = json.loads(exif_json_str)
                    if "sui_image_params" in exif_dict:
                        self._try_parser(SwarmUI, info=exif_dict)
        except json.JSONDecodeError as json_err:
            self._logger.debug(f"SwarmUI legacy EXIF: Invalid JSON: {json_err}")
        except Exception as general_exception:  # pylint: disable=broad-except
            self._logger.debug(
                f"SwarmUI legacy EXIF check failed: {general_exception}",
                exc_info=True,
            )

    def _process_png_chunks(self, image_obj: Image.Image):
        """Processes various PNG chunks to find metadata."""
        if self._parser:
            return  # Already parsed

        # Extract relevant PNG chunks
        png_params = self._info.get("parameters")
        png_prompt = self._info.get("prompt")
        # png_workflow = self._info.get("workflow") # Not directly used by _try_parser calls here
        png_postproc = self._info.get("postprocessing")
        png_neg_prompt_ed = self._info.get("negative_prompt") or self._info.get(
            "Negative Prompt",
        )
        png_invoke_meta_keys = ["invokeai_metadata", "sd-metadata", "Dream"]
        png_invoke_meta = next(
            (
                self._info.get(key)
                for key in png_invoke_meta_keys
                if self._info.get(key)
            ),
            None,
        )
        png_software_tag = self._info.get("Software")
        png_comment_chunk = self._info.get("Comment")
        png_xmp_chunk = self._info.get("XML:com.adobe.xmp")

        # Order of attempts matters
        if png_params and not self._parser:
            if "sui_image_params" in png_params:
                self._try_parser(SwarmUI, raw=png_params)
            elif self._try_parser(A1111, info=self._info):
                if (
                    png_prompt and self._tool == "A1111 webUI"
                ):  # Check if it might be ComfyUI emulating A1111
                    self._logger.debug(
                        "PNG 'parameters' parsed by A1111, also has 'prompt', could be ComfyUI.",
                    )
                    # ComfyUI might also be tried later if this isn't definitive enough

        if png_postproc and not self._parser:  # A1111 postprocessing info
            self._try_parser(A1111, info=self._info)

        if png_neg_prompt_ed and not self._parser:  # EasyDiffusion specific field
            self._try_parser(EasyDiffusion, info=self._info)

        if png_invoke_meta and not self._parser:  # InvokeAI
            self._try_parser(InvokeAI, info=self._info)

        if png_software_tag == "NovelAI" and not self._parser:
            self._try_parser(
                NovelAI,
                info=self._info,
                width=self._width,
                height=self._height,
            )

        if png_prompt and not self._parser:  # ComfyUI often uses 'prompt' for workflow
            self._try_parser(
                ComfyUI,
                info=self._info,
                width=self._width,
                height=self._height,
            )

        if png_comment_chunk and not self._parser:  # Fooocus stores JSON in Comment
            try:
                comment_data = json.loads(png_comment_chunk)
                self._try_parser(Fooocus, info=comment_data)
            except json.JSONDecodeError:
                self._logger.warn("Fooocus PNG Comment: Not valid JSON.")

        if png_xmp_chunk and not self._parser:  # DrawThings
            self._parse_drawthings_xmp(png_xmp_chunk)

        # NovelAI LSB in PNG (alpha channel)
        if image_obj.mode == "RGBA" and not self._parser:
            self._parse_novelai_lsb(image_obj)

    def _parse_drawthings_xmp(self, xmp_chunk: str):
        """Helper to parse DrawThings XMP data."""
        if self._parser:
            return
        try:
            xmp_dom = minidom.parseString(xmp_chunk)
            uc_nodes = xmp_dom.getElementsByTagName("exif:UserComment")
            if not uc_nodes:
                return

            # Try to find the correct node structure for DrawThings
            # This can be complex due to nested rdf:Alt/rdf:li or similar structures
            # The original deep access was: uc_node[0].childNodes[1].childNodes[1].childNodes[0].data
            # This needs to be made more robust, e.g., by iterating or searching for specific tags.
            # For now, implementing a safer, if less deep, access pattern.
            # This part is a simplification and might need adjustment for actual DrawThings XMP.
            # pylint: disable=too-many-boolean-expressions
            node_l0 = uc_nodes[0]
            if (
                node_l0
                and node_l0.childNodes
                and len(node_l0.childNodes) > 1
                and node_l0.childNodes[1]  # Check level 1
                and node_l0.childNodes[1].childNodes
                and len(node_l0.childNodes[1].childNodes) > 1
                and node_l0.childNodes[1].childNodes[1]  # Check level 2
                and node_l0.childNodes[1].childNodes[1].childNodes
                # Check level 3 (data node)
                and len(node_l0.childNodes[1].childNodes[1].childNodes) > 0
                and hasattr(node_l0.childNodes[1].childNodes[1].childNodes[0], "data")
            ):
                json_str = node_l0.childNodes[1].childNodes[1].childNodes[0].data
                self._try_parser(DrawThings, info=json.loads(json_str))
            else:
                self._logger.warn(
                    "DrawThings PNG XMP: UserComment structure not as expected or data missing.",
                )
        except minidom.ExpatError as xml_err:
            self._logger.warn(f"DrawThings PNG XMP: XML parsing error: {xml_err}")
        except json.JSONDecodeError:
            self._logger.warn("DrawThings PNG XMP: UserComment content not valid JSON.")
        except Exception as general_exception:  # pylint: disable=broad-except
            self._logger.warn(
                f"DrawThings PNG XMP: Error processing XMP: {general_exception}",
                exc_info=True,
            )

    def _parse_novelai_lsb(self, image_obj: Image.Image):
        """Helper to parse NovelAI LSB data from an image object."""
        if self._parser:
            return
        try:
            reader = NovelAI.LSBExtractor(image_obj)
            magic_bytes = reader.get_next_n_bytes(len(self.NOVELAI_MAGIC))
            if (
                magic_bytes
                and magic_bytes.decode("utf-8", errors="ignore") == self.NOVELAI_MAGIC
            ):
                self._try_parser(NovelAI, extractor=reader)
        except Exception as lsb_err:  # pylint: disable=broad-except
            self._logger.warn(f"NovelAI LSB check error: {lsb_err}", exc_info=True)

    def _process_jpeg_webp_exif(self, image_obj: Image.Image):
        """Processes EXIF data for JPEG/WEBP formats."""
        if self._parser:
            return  # Already parsed

        raw_user_comment: str | None = None
        software_tag: str = ""
        jfif_comment: str = self._info.get("comment", b"").decode("utf-8", "ignore")

        if self._info.get("exif"):
            try:
                exif_data = piexif.load(self._info["exif"])
                user_comment_bytes = exif_data.get("Exif", {}).get(
                    piexif.ExifIFD.UserComment,
                )
                if user_comment_bytes:
                    raw_user_comment = piexif.helper.UserComment.load(
                        user_comment_bytes,
                    )

                software_bytes = exif_data.get("0th", {}).get(piexif.ImageIFD.Software)
                if software_bytes:
                    software_tag = software_bytes.decode("ascii", "ignore").strip()
            except piexif.InvalidImageDataError as exif_load_err:  # More specific error
                self._logger.warn(
                    f"piexif load error (InvalidImageDataError) for EXIF: {exif_load_err}",
                )
            except Exception as exif_err:  # pylint: disable=broad-except
                self._logger.warn(
                    f"piexif load error for EXIF: {exif_err}",
                    exc_info=True,
                )

        # 1. RuinedFooocus / Civitai (UserComment)
        if raw_user_comment and not self._parser:
            if raw_user_comment.strip().startswith("{"):  # Potential JSON
                try:
                    uc_json = json.loads(raw_user_comment)
                    if (
                        isinstance(uc_json, dict)
                        and uc_json.get("software") == "RuinedFooocus"
                    ):
                        self._try_parser(
                            RuinedFooocusFormat,
                            raw=raw_user_comment,
                            width=self._width,
                            height=self._height,
                        )
                except json.JSONDecodeError:
                    self._logger.debug(
                        "UserComment starts with '{' but is not valid RuinedFooocus JSON.",
                    )

            if not self._parser:  # Check for Civitai if not RuinedFooocus
                is_civitai_uc = False
                if (
                    software_tag == "4c6047c3-8b1c-4058-8888-fd48353bf47d"
                ):  # Known Civitai software tag
                    is_civitai_uc = True
                else:
                    # Civitai often has "charset=Unicode" then JSON, or just JSON.
                    # The "笀∀爀攀猀漀甀爀挀攀" part is mangled Unicode for "{"resource".
                    text_segment = raw_user_comment  # Default to full comment
                    if (
                        "charset=Unicode" in raw_user_comment
                    ):  # More specific check for Civitai
                        text_segment = raw_user_comment.split("charset=Unicode", 1)[
                            -1
                        ].strip()

                    if (
                        # Corrected hanging indent
                        text_segment.startswith("笀∀爀攀猀漀甀爀挀攀")
                        or text_segment.startswith('{"resource-stack":}')
                    ) and '"extraMetadata":' in text_segment:
                        is_civitai_uc = True
                    elif (
                        text_segment.startswith('{"resource-stack":}')
                        and '"extraMetadata":' in text_segment
                    ):  # Simpler check if no mangled Unicode
                        is_civitai_uc = True

                if is_civitai_uc:
                    self._try_parser(
                        CivitaiComfyUIFormat,
                        raw=raw_user_comment,
                        width=self._width,
                        height=self._height,
                    )

        # 2. Fooocus (JFIF Comment)
        if not self._parser and jfif_comment:
            try:
                jfif_json = json.loads(jfif_comment)
                # Fooocus JFIF comments are typically a flat JSON with "prompt", "negative_prompt" etc.
                if isinstance(jfif_json, dict) and "prompt" in jfif_json:
                    self._try_parser(Fooocus, info=jfif_json)
            except json.JSONDecodeError:
                self._logger.debug("JFIF Comment not valid Fooocus JSON.")

        # 3. Standard UserComment Fallbacks (A1111, EasyDiffusion, SwarmUI)
        if not self._parser and raw_user_comment:
            self._raw = raw_user_comment  # Set self._raw for these parsers
            if "sui_image_params" in raw_user_comment:
                self._try_parser(SwarmUI, raw=self._raw)
            # EasyDiffusion often JSON in UserComment
            elif raw_user_comment.strip().startswith("{"):
                self._try_parser(EasyDiffusion, raw=self._raw)
            else:  # A1111 often plain text in UserComment
                self._try_parser(A1111, raw=self._raw)

        # 4. NovelAI LSB (RGBA JPEG/WEBP)
        if not self._parser and image_obj.mode == "RGBA":
            self._parse_novelai_lsb(image_obj)

    # pylint: disable=too-many-branches,too-many-statements
    def read_data(self, file_path_or_obj: str | Path | TextIO | BinaryIO):
        # Reset state for fresh read
        self._status = BaseFormat.Status.UNREAD
        self._error = ""
        self._parser = None
        self._tool = ""
        self._raw = ""  # Clear raw from previous reads
        self._info = {}  # Clear info
        self._width = 0
        self._height = 0

        file_display_name = str(file_path_or_obj)
        if hasattr(file_path_or_obj, "name"):  # For file objects
            file_display_name = Path(file_path_or_obj.name).name
        elif isinstance(file_path_or_obj, (str, Path)):
            file_display_name = Path(file_path_or_obj).name

        if self._is_txt:
            if hasattr(file_path_or_obj, "read") and callable(file_path_or_obj.read):
                # Assuming file_path_or_obj is an opened text file object
                self._handle_text_file(file_path_or_obj)  # type: ignore
            else:
                self._logger.error(
                    "Text file processing expected a readable file object.",
                )
                self._status = BaseFormat.Status.FORMAT_ERROR
                self._error = "Invalid file object for text file."
            # Final logging for text files is inside _handle_text_file
            return

        try:
            with Image.open(file_path_or_obj) as img:  # Renamed f_img to img
                self._width = img.width
                self._height = img.height
                self._info = (
                    img.info.copy() if img.info else {}
                )  # Ensure it's a mutable copy
                self._format_str = img.format or ""

                # TODO: Refactor parser attempts into a strategy list or chained calls
                # Example: parser_strategies = [self._attempt_legacy_swarm_exif, self._process_png_chunks, ...]
                # for strategy_fn in parser_strategies:
                #     if self._parser: break
                #     strategy_fn(img)

                self._attempt_legacy_swarm_exif(img)

                if not self._parser and self._format_str == "PNG":
                    self._process_png_chunks(img)
                elif not self._parser and self._format_str in ["JPEG", "WEBP"]:
                    self._process_jpeg_webp_exif(img)

        except FileNotFoundError:
            self._logger.error(f"Image file not found: {file_display_name}")
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = "Image file not found."
        except UnidentifiedImageError as unident_err:  # Specific PIL error
            self._logger.error(
                f"Cannot identify image file '{file_display_name}': {unident_err}",
            )
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"Cannot identify image file: {unident_err}"
        except Exception as outer_open_err:  # pylint: disable=broad-except
            self._logger.error(
                f"Error opening or processing image '{file_display_name}': {outer_open_err}",
                exc_info=True,
            )
            self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error:  # Only set if not already set by a more specific error
                self._error = f"Pillow/general error: {outer_open_err}"

        # Final Status Check
        if self._status == BaseFormat.Status.UNREAD:
            self._logger.warn(
                f"No suitable parser found or no parser claimed success for '{file_display_name}'.",
            )
            self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error:
                self._error = "No suitable parser found or parsing failed."

        log_tool_name = self._tool if self._tool else "None"
        log_status_name = (
            self._status.name if hasattr(self._status, "name") else str(self._status)
        )
        self._logger.info(
            f"Final Reading Status for '{file_display_name}': {log_status_name}, Tool: {log_tool_name}",
        )

        # Consolidate error message logging
        final_error_to_log = self._error  # Start with ImageDataReader's own error
        if self._parser and getattr(self._parser, "error", None):
            # If parser has an error and either we didn't succeed or IDR has no error, prefer parser's.
            if self._status != BaseFormat.Status.READ_SUCCESS or not final_error_to_log:
                final_error_to_log = self._parser.error

        if self._status != BaseFormat.Status.READ_SUCCESS and final_error_to_log:
            self._logger.warn(f"Error details: {final_error_to_log}")
        elif (
            self._status != BaseFormat.Status.READ_SUCCESS
        ):  # Fallback if no error string captured
            self._logger.warn(
                f"Parsing failed with status {log_status_name} (no specific error message captured).",
            )

    @staticmethod
    def remove_data(image_file_path: Union[str, Path]) -> Optional[Image.Image]:
        try:
            with Image.open(image_file_path) as img_file:
                image_data = list(img_file.getdata())
                image_without_exif = Image.new(img_file.mode, img_file.size)
                image_without_exif.putdata(image_data)
                return image_without_exif
        except FileNotFoundError:
            get_logger("DSVendored_SDPR.ImageDataReader").error(
                f"remove_data: File not found - {image_file_path}",
            )
        except Exception as general_err:  # pylint: disable=broad-except
            get_logger("DSVendored_SDPR.ImageDataReader").error(
                f"remove_data: Error processing {image_file_path} - {general_err}",
                exc_info=True,
            )
        return None

    @staticmethod
    def save_image(
        image_path: str | Path,
        new_path: str | Path,
        image_format: str,
        data: str | None = None,
    ):
        # Specific logger for this static method
        logger_instance = get_logger("DSVendored_SDPR.ImageDataReader.Save")
        metadata_to_embed: Any = None  # Can be PngInfo or bytes for EXIF
        if data:
            image_format_upper = image_format.strip().upper()
            if image_format_upper == "PNG":
                metadata_to_embed = PngInfo()
                metadata_to_embed.add_text("parameters", data)
            elif image_format_upper in ["JPEG", "JPG", "WEBP"]:
                try:
                    # Ensure data is string for UserComment
                    user_comment_bytes = piexif.helper.UserComment.dump(
                        str(data),
                        encoding="unicode",
                    )
                    metadata_to_embed = piexif.dump(
                        {"Exif": {piexif.ExifIFD.UserComment: user_comment_bytes}},
                    )
                except Exception as dump_err:  # pylint: disable=broad-except
                    logger_instance.error(
                        f"piexif dump error: {dump_err}",
                        exc_info=True,
                    )
                    metadata_to_embed = None  # Ensure it's None if dump fails
        try:
            with Image.open(image_path) as img_to_save:
                image_format_upper = (
                    image_format.strip().upper()
                )  # Ensure it's stripped and upper
                save_kwargs: dict[str, Any] = {}

                if image_format_upper == "PNG":
                    if metadata_to_embed:
                        save_kwargs["pnginfo"] = metadata_to_embed
                elif image_format_upper in ["JPEG", "JPG"]:
                    save_kwargs["quality"] = 95
                    # Preserve existing EXIF if not embedding new metadata, or merge if piexif handles it.
                    # For simplicity, if we have new EXIF (metadata_to_embed), we use that.
                    # Otherwise, try to preserve existing.
                    if metadata_to_embed:
                        # piexif.dump produces bytes suitable for exif kwarg
                        save_kwargs["exif"] = metadata_to_embed
                        metadata_to_embed = None  # Clear it so piexif.insert is not called later for JPEG
                    elif img_to_save.info.get("exif"):
                        save_kwargs["exif"] = img_to_save.info["exif"]

                elif image_format_upper == "WEBP":
                    # For lossless, though Pillow's default might be good
                    save_kwargs["quality"] = 100
                    save_kwargs["lossless"] = True
                    if metadata_to_embed:
                        # piexif.dump produces bytes
                        save_kwargs["exif"] = metadata_to_embed
                        metadata_to_embed = None  # Clear it for WEBP too

                img_to_save.save(new_path, **save_kwargs)

                # For JPEG/WEBP, piexif.insert is sometimes used if Pillow doesn't handle EXIF well for a format
                # However, Pillow's `save` with `exif=` argument should be preferred.
                # The original code had piexif.insert calls after save for JPEG/WEBP.
                # If Pillow's `exif=` kwarg is sufficient, these are not needed.
                # Keeping the logic structure but it might be redundant if `exif=` works.
                if metadata_to_embed and image_format_upper in ["JPEG", "JPG", "WEBP"]:
                    logger_instance.debug(
                        f"Attempting piexif.insert for {new_path} (should be redundant if exif= kwarg worked)",
                    )
                    try:
                        piexif.insert(metadata_to_embed, str(new_path))
                    except Exception as insert_err:  # pylint: disable=broad-except
                        logger_instance.error(
                            f"piexif.insert ({image_format_upper}) error: {insert_err}",
                            exc_info=True,
                        )

        except FileNotFoundError:
            logger_instance.error(
                f"Image save error: Source file not found - {image_path}",
            )
        except UnidentifiedImageError:
            logger_instance.error(
                f"Image save error: Cannot identify source image - {image_path}",
            )
        except Exception as save_err:  # pylint: disable=broad-except
            logger_instance.error(
                f"Image save error for {new_path}: {save_err}",
                exc_info=True,
            )

    @staticmethod
    def construct_data(positive: str, negative: str, setting: str) -> str:
        parts = []
        if positive:
            parts.append(positive)
        if negative:
            parts.append(f"Negative prompt: {negative}")
        if setting:
            parts.append(setting)
        return "\n".join(parts)

    def prompt_to_line(self) -> str:
        if self._parser and hasattr(self._parser, "prompt_to_line"):
            return self._parser.prompt_to_line()
        # Fallback if no parser or parser has no such method
        return self.construct_data(self.positive, self.negative, self.setting)

    # Properties to access data, preferring parsed data if available
    @property
    def height(self) -> str:
        parser_h = getattr(self._parser, "height", None)
        # Ensure valid integer string before comparing to "0"
        if parser_h is not None:
            try:
                if int(str(parser_h)) > 0:
                    return str(parser_h)
            except ValueError:
                pass  # Not a valid int string
        return str(self._height) if self._height > 0 else "0"

    @property
    def width(self) -> str:
        parser_w = getattr(self._parser, "width", None)
        if parser_w is not None:
            try:
                if int(str(parser_w)) > 0:
                    return str(parser_w)
            except ValueError:
                pass
        return str(self._width) if self._width > 0 else "0"

    @property
    def info(self) -> dict[str, Any]:
        return self._info

    @property
    def positive(self) -> str:
        # getattr will return self._positive if self._parser is None or has no 'positive'
        return str(getattr(self._parser, "positive", self._positive))

    @property
    def negative(self) -> str:
        return str(getattr(self._parser, "negative", self._negative))

    @property
    def positive_sdxl(self) -> dict[str, Any]:
        return getattr(self._parser, "positive_sdxl", self._positive_sdxl or {})

    @property
    def negative_sdxl(self) -> dict[str, Any]:
        return getattr(self._parser, "negative_sdxl", self._negative_sdxl or {})

    @property
    def setting(self) -> str:
        return str(getattr(self._parser, "setting", self._setting))

    @property
    def raw(self) -> str:
        parser_raw = getattr(self._parser, "raw", None)
        # Return parser's raw if it exists and is not None, otherwise fallback to self._raw
        return str(parser_raw if parser_raw is not None else self._raw)

    @property
    def tool(self) -> str:
        parser_tool = getattr(self._parser, "tool", None)
        # Prefer parser's tool if it's valid and not "Unknown"
        return (
            str(parser_tool)
            if parser_tool and parser_tool != "Unknown"
            else str(self._tool)
        )

    @property
    def parameter(self) -> dict[str, Any]:
        # Ensure a dictionary is returned, even if the parser's parameter is None
        parser_param = getattr(self._parser, "parameter", None)
        return parser_param if parser_param is not None else (self._parameter or {})

    @property
    def format(self) -> str:
        return self._format_str

    @property
    def is_sdxl(self) -> bool:
        return getattr(self._parser, "is_sdxl", self._is_sdxl)

    @property
    def props(self) -> str:  # This typically calls the parser's props method
        if self._parser and hasattr(self._parser, "props"):
            return self._parser.props
        # Fallback to a basic representation if no parser or parser has no props
        fallback_props = {
            "positive": self.positive,
            "negative": self.negative,
            "width": self.width,
            "height": self.height,
            "tool": self.tool,
            "setting": self.setting,
            **self.parameter,
        }
        return json.dumps(fallback_props, indent=2)

    @property
    def status(self) -> BaseFormat.Status:
        return self._status

    @property
    def error(self) -> str:
        parser_err = getattr(self._parser, "error", None)
        # Prefer parser's error if it exists, otherwise ImageDataReader's own error
        return str(parser_err if parser_err else self._error)
