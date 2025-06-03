# dataset_tools/vendored_sdpr/image_data_reader.py
# This is YOUR VENDORED and MODIFIED copy - FUSED VERSION

__author__ = "receyuki"
__filename__ = "image_data_reader.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
import logging
from pathlib import Path
from typing import Any, BinaryIO, TextIO  # Added Union

import piexif
import piexif.helper
from defusedxml import minidom
from PIL import Image, UnidentifiedImageError
from PIL.PngImagePlugin import PngInfo

from .constants import PARAMETER_PLACEHOLDER
from .format import (
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
from .logger import get_logger


# pylint: disable=too-many-instance-attributes,too-many-public-methods
class ImageDataReader:
    NOVELAI_MAGIC = "stealth_pngcomp"

    def __init__(
        self,
        file_path_or_obj: str | Path | TextIO | BinaryIO,  # Used Union
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

        base_param_key_attr = getattr(BaseFormat, "PARAMETER_KEY", None)
        if isinstance(base_param_key_attr, list):
            self._parameter_key: list[str] = base_param_key_attr
        else:  # Fallback if BaseFormat.PARAMETER_KEY is not as expected
            self._parameter_key = ["model", "sampler", "seed", "cfg", "steps", "size"]

        self._parameter: dict[str, Any] = dict.fromkeys(
            self._parameter_key, PARAMETER_PLACEHOLDER
        )
        self._is_txt: bool = is_txt
        self._is_sdxl: bool = False
        self._format_str: str = ""  # To store image.format
        # self._props: str = "" # Not used as an instance var, props is a property
        self._parser: BaseFormat | None = None
        self._status: BaseFormat.Status = BaseFormat.Status.UNREAD
        self._error: str = ""
        self._logger: logging.Logger = get_logger("DSVendored_SDPR.ImageDataReader")

        self.read_data(file_path_or_obj)

    def _try_parser(self, parser_class: type[BaseFormat], **kwargs: Any) -> bool:
        # Use list(kwargs.keys()) only for logging, not for performance-critical paths
        kwarg_keys_for_log = list(kwargs.keys())
        self._logger.debug(
            "Attempting parser: %s with kwargs: %s",
            parser_class.__name__,
            kwarg_keys_for_log,
        )
        try:
            if "width" in kwargs and isinstance(self._width, int) and self._width > 0:
                kwargs["width"] = self._width  # No need for int() if already int
            if (
                "height" in kwargs
                and isinstance(self._height, int)
                and self._height > 0
            ):
                kwargs["height"] = self._height

            temp_parser = parser_class(**kwargs)
            parser_own_status = temp_parser.parse()

            if parser_own_status == BaseFormat.Status.READ_SUCCESS:
                self._parser = temp_parser
                self._tool = getattr(self._parser, "tool", parser_class.__name__)
                self._status = BaseFormat.Status.READ_SUCCESS
                self._error = ""  # Clear previous errors if successful
                self._logger.info("Successfully parsed as %s.", self._tool)
                return True

            parser_error_msg = getattr(temp_parser, "error", "Unknown parser error")
            status_name = (
                parser_own_status.name
                if hasattr(parser_own_status, "name")
                else str(parser_own_status)
            )
            self._logger.debug(
                "%s parsing attempt resulted in status: %s. Error: %s",
                parser_class.__name__,
                status_name,
                parser_error_msg,
            )
            # Only update self._error if no more specific error is already set
            # or if the current status is still UNREAD (meaning this is the first error encountered)
            if parser_error_msg and (
                self._status == BaseFormat.Status.UNREAD or not self._error
            ):
                self._error = parser_error_msg
            return False
        except TypeError as type_err:
            self._logger.error(
                "TypeError instantiating or calling %s: %s. Check __init__/parse signature.",
                parser_class.__name__,
                type_err,
                exc_info=True,
            )
            if self._status == BaseFormat.Status.UNREAD:
                self._error = f"Init/call error for {parser_class.__name__}: {type_err}"
            return False
        except (
            Exception
        ) as general_exception:  # Justified fallback for diverse parser errors
            self._logger.error(
                "Unexpected exception during %s attempt: %s",
                parser_class.__name__,
                general_exception,
                exc_info=True,
            )
            if self._status == BaseFormat.Status.UNREAD:
                self._error = (
                    f"Runtime error in {parser_class.__name__}: {general_exception}"
                )
            return False

    def _handle_text_file(self, file_obj: TextIO):
        try:
            self._raw = file_obj.read()
        except Exception as e_read:  # Catch errors during file read
            self._logger.error(
                "Error reading text file object: %s", e_read, exc_info=True
            )
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"Could not read text file content: {e_read}"
            return

        if self._try_parser(A1111, raw=self._raw):
            pass  # Successfully parsed
        else:
            if self._status == BaseFormat.Status.UNREAD:
                self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error:
                self._error = "Failed to parse text file as A1111 format."

        log_status = (
            self._status.name if hasattr(self._status, "name") else str(self._status)
        )
        self._logger.info(
            "Text file processed. Final Status: %s, Tool: %s",
            log_status,
            self._tool or "None",
        )

    def _attempt_legacy_swarm_exif(self, image_obj: Image.Image):
        if self._parser:
            return
        try:
            exif_pil = image_obj.getexif()  # This can be slow for some images
            if exif_pil:
                # SwarmUI used non-standard EXIF tag 0x0110 (Model) for its JSON in some versions
                exif_json_str = exif_pil.get(0x0110)  # ImageIFD.Model
                if exif_json_str and isinstance(exif_json_str, (str, bytes)):
                    if isinstance(exif_json_str, bytes):  # Decode if bytes
                        exif_json_str = exif_json_str.decode("utf-8", errors="ignore")

                    # Check if it looks like SwarmUI JSON
                    if "sui_image_params" in exif_json_str:
                        try:
                            exif_dict = json.loads(exif_json_str)
                            if "sui_image_params" in exif_dict:
                                self._try_parser(SwarmUI, info=exif_dict)
                        except json.JSONDecodeError as json_err:
                            self._logger.debug(
                                "SwarmUI legacy EXIF (0x0110): Invalid JSON: %s",
                                json_err,
                            )
        except Exception as general_exception:
            self._logger.debug(
                "SwarmUI legacy EXIF (0x0110) check failed: %s",
                general_exception,
                exc_info=False,
            )  # exc_info False for debug unless needed

    def _process_png_chunks(self, image_obj: Image.Image):
        if self._parser:
            return

        png_params = self._info.get("parameters")
        png_prompt = self._info.get("prompt")
        png_workflow = self._info.get("workflow")  # Used by ComfyUI _try_parser
        png_postproc = self._info.get("postprocessing")
        png_neg_prompt_ed = self._info.get("negative_prompt") or self._info.get(
            "Negative Prompt"
        )
        png_invoke_meta_keys = ["invokeai_metadata", "sd-metadata", "Dream"]
        png_invoke_meta_content = {
            k: self._info[k] for k in png_invoke_meta_keys if k in self._info
        }
        png_software = self._info.get("Software")
        png_comment = self._info.get("Comment")
        png_xmp = self._info.get("XML:com.adobe.xmp")  # Standard XMP key from Pillow

        # Ordered attempts
        parsers_to_try_with_info = [
            (
                A1111,
                {"info": self._info},
                lambda: png_params or png_postproc,
            ),  # A1111 can use parameters or postprocessing
            (EasyDiffusion, {"info": self._info}, lambda: png_neg_prompt_ed),
            (InvokeAI, {"info": self._info}, lambda: png_invoke_meta_content),
            (
                NovelAI,
                {"info": self._info, "width": self._width, "height": self._height},
                lambda: png_software == "NovelAI",
            ),
            (
                ComfyUI,
                {"info": self._info, "width": self._width, "height": self._height},
                lambda: png_prompt or png_workflow,
            ),
        ]
        for parser_class, kwargs, condition in parsers_to_try_with_info:
            if self._parser:
                break
            if condition():
                self._try_parser(parser_class, **kwargs)

        if not self._parser and png_comment:
            try:  # For Fooocus primarily
                comment_data = json.loads(png_comment)
                if isinstance(comment_data, dict):  # Ensure it's a dict for Fooocus
                    self._try_parser(Fooocus, info=comment_data)
            except json.JSONDecodeError:
                self._logger.debug("PNG Comment: Not valid JSON for Fooocus.")

        if (
            not self._parser and png_params and "sui_image_params" in png_params
        ):  # Swarm specific check on params
            self._try_parser(
                SwarmUI, raw=png_params
            )  # SwarmUI parser might expect raw string

        if not self._parser and png_xmp:
            self._parse_drawthings_xmp(png_xmp)
        if not self._parser and image_obj.mode == "RGBA":
            self._parse_novelai_lsb(image_obj)

    def _parse_drawthings_xmp(self, xmp_chunk: str):
        if self._parser:
            return
        try:
            xmp_dom = minidom.parseString(xmp_chunk)
            # DrawThings stores JSON in exif:UserComment inside XMP
            # <rdf:Description ...><exif:UserComment><rdf:Alt><rdf:li xml:lang="x-default">JSON_HERE...
            description_nodes = xmp_dom.getElementsByTagName("rdf:Description")
            for desc_node in description_nodes:
                uc_nodes = desc_node.getElementsByTagName("exif:UserComment")
                if not uc_nodes:
                    continue
                # UserComment might have rdf:Alt -> rdf:li structure
                data_str = None
                if uc_nodes[0].childNodes:
                    if (
                        uc_nodes[0].childNodes[0].nodeType == uc_nodes[0].TEXT_NODE
                    ):  # Direct text
                        data_str = uc_nodes[0].childNodes[0].data
                    elif (
                        uc_nodes[0].childNodes[0].nodeName == "rdf:Alt"
                    ):  # Nested structure
                        alt_node = uc_nodes[0].childNodes[0]
                        li_nodes = alt_node.getElementsByTagName("rdf:li")
                        if (
                            li_nodes
                            and li_nodes[0].childNodes
                            and li_nodes[0].childNodes[0].nodeType
                            == li_nodes[0].TEXT_NODE
                        ):
                            data_str = li_nodes[0].childNodes[0].data
                if data_str:
                    self._try_parser(DrawThings, info=json.loads(data_str.strip()))
                    if self._parser:
                        return  # Parsed successfully
        except (minidom.ExpatError, json.JSONDecodeError) as xml_json_err:
            self._logger.warning(
                "DrawThings PNG XMP: Parsing error (XML or JSON): %s", xml_json_err
            )
        except Exception as general_exception:
            self._logger.warning(
                "DrawThings PNG XMP: Error processing XMP: %s",
                general_exception,
                exc_info=True,
            )

    def _parse_novelai_lsb(self, image_obj: Image.Image):
        if self._parser:
            return
        try:
            reader = NovelAI.LSBExtractor(image_obj)  # LSBExtractor expects PIL.Image
            magic_val = reader.get_next_n_bytes(len(self.NOVELAI_MAGIC))
            if magic_val and magic_val.decode("utf-8", "ignore") == self.NOVELAI_MAGIC:
                self._try_parser(
                    NovelAI, extractor=reader, width=self._width, height=self._height
                )  # Pass dims
        except Exception as lsb_err:
            self._logger.warning("NovelAI LSB check error: %s", lsb_err, exc_info=True)

    def _process_jpeg_webp_exif(self, image_obj: Image.Image):
        if self._parser:
            return

        raw_user_comment: str | None = None
        software_tag: str = ""
        # JFIF comment for Fooocus (present in img.info['comment'] for JPEG)
        jfif_comment_bytes = self._info.get("comment", b"")
        jfif_comment = (
            jfif_comment_bytes.decode("utf-8", "ignore")
            if isinstance(jfif_comment_bytes, bytes)
            else ""
        )

        if self._info.get("exif"):
            try:
                exif_data = piexif.load(
                    self._info["exif"]
                )  # piexif operates on exif bytestring
                user_comment_bytes = exif_data.get("Exif", {}).get(
                    piexif.ExifIFD.UserComment
                )
                if user_comment_bytes:
                    raw_user_comment = piexif.helper.UserComment.load(
                        user_comment_bytes
                    )

                software_bytes = exif_data.get("0th", {}).get(piexif.ImageIFD.Software)
                if software_bytes and isinstance(software_bytes, bytes):
                    software_tag = software_bytes.decode("ascii", "ignore").strip()
            except piexif.InvalidImageDataError as exif_load_err:
                self._logger.warning("piexif EXIF load error: %s", exif_load_err)
            except Exception as exif_err:
                self._logger.warning(
                    "piexif EXIF general error: %s", exif_err, exc_info=True
                )

        # Order of attempts for EXIF based data
        if raw_user_comment and not self._parser:
            if raw_user_comment.strip().startswith("{"):  # RuinedFooocus candidate
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
                    pass  # Not RuinedFooocus JSON

            # Civitai UserComment check (can be complex due to encodings)
            if not self._parser:
                # Civitai often sets a specific software tag or has characteristic UserComment structures
                # This check could be more robust by inspecting software_tag and UserComment structure
                is_civitai = (
                    software_tag == "4c6047c3-8b1c-4058-8888-fd48353bf47d"
                    or (
                        "charset=Unicode" in raw_user_comment
                        and '"extraMetadata":' in raw_user_comment
                    )
                    or (
                        raw_user_comment.startswith('{"resource-stack":')
                        and '"extraMetadata":' in raw_user_comment
                    )
                )
                if is_civitai:
                    self._try_parser(
                        CivitaiComfyUIFormat,
                        raw=raw_user_comment,
                        width=self._width,
                        height=self._height,
                    )

        if not self._parser and jfif_comment:  # Fooocus (JFIF Comment)
            try:
                jfif_json = json.loads(jfif_comment)
                if (
                    isinstance(jfif_json, dict) and "prompt" in jfif_json
                ):  # Basic check for Fooocus structure
                    self._try_parser(
                        Fooocus, info=jfif_json
                    )  # Fooocus parser expects info dict
            except json.JSONDecodeError:
                self._logger.debug("JFIF Comment not Fooocus JSON.")

        # Fallbacks for UserComment (A1111, EasyDiffusion, SwarmUI)
        if not self._parser and raw_user_comment:
            self._raw = raw_user_comment  # Set self._raw for these parsers
            if "sui_image_params" in raw_user_comment:
                self._try_parser(SwarmUI, raw=self._raw)
            elif raw_user_comment.strip().startswith("{"):
                self._try_parser(EasyDiffusion, raw=self._raw)
            else:
                self._try_parser(A1111, raw=self._raw)

        if (
            not self._parser and image_obj.mode == "RGBA"
        ):  # NovelAI LSB if RGBA (uncommon for JPEG/WEBP but possible)
            self._parse_novelai_lsb(image_obj)

    # pylint: disable=too-many-branches,too-many-statements
    def read_data(self, file_path_or_obj: str | Path | TextIO | BinaryIO):
        self._status = BaseFormat.Status.UNREAD
        self._error = ""
        self._parser = None
        self._tool = ""
        self._raw = ""
        self._info = {}
        self._width = 0
        self._height = 0
        self._positive = ""
        self._negative = ""
        self._setting = ""
        self._positive_sdxl = {}
        self._negative_sdxl = {}
        self._is_sdxl = False
        self._parameter = dict.fromkeys(self._parameter_key, PARAMETER_PLACEHOLDER)

        file_display_name = str(file_path_or_obj)
        if hasattr(file_path_or_obj, "name"):
            file_display_name = Path(file_path_or_obj.name).name
        elif isinstance(file_path_or_obj, (str, Path)):
            file_display_name = Path(file_path_or_obj).name

        self._logger.debug(
            "Reading data for: %s (is_txt: %s)", file_display_name, self._is_txt
        )

        if self._is_txt:
            if hasattr(file_path_or_obj, "read") and callable(file_path_or_obj.read):
                self._handle_text_file(file_path_or_obj)  # type: ignore
            else:
                self._logger.error(
                    "Text file processing expected a readable file object."
                )
                self._status = BaseFormat.Status.FORMAT_ERROR
                self._error = "Invalid file object for text file."
            return

        try:
            with Image.open(file_path_or_obj) as img:
                self._width = img.width
                self._height = img.height
                self._info = img.info.copy() if img.info else {}
                self._format_str = img.format or ""
                self._logger.debug(
                    "Image opened: %s, Format: %s, Size: %sx%s",
                    file_display_name,
                    self._format_str,
                    self._width,
                    self._height,
                )

                # Try SwarmUI legacy EXIF first for any image type if applicable
                self._attempt_legacy_swarm_exif(img)

                if not self._parser:  # Only proceed if not already parsed
                    if self._format_str == "PNG":
                        self._process_png_chunks(img)
                    elif self._format_str in ["JPEG", "WEBP"]:
                        self._process_jpeg_webp_exif(img)
                    # Add other format handlers here if needed (e.g., TIFF)
                    else:
                        self._logger.info(
                            "Image format '%s' not specifically handled for detailed metadata beyond basic Pillow info.",
                            self._format_str,
                        )
                        # Attempt a generic A1111 parse on exif UserComment if present and nothing else worked
                        if not self._parser and self._info.get("exif"):
                            try:
                                exif_data_gen = piexif.load(self._info["exif"])
                                uc_bytes_gen = exif_data_gen.get("Exif", {}).get(
                                    piexif.ExifIFD.UserComment
                                )
                                if uc_bytes_gen:
                                    uc_str_gen = piexif.helper.UserComment.load(
                                        uc_bytes_gen
                                    )
                                    if uc_str_gen and not uc_str_gen.strip().startswith(
                                        "{"
                                    ):  # Avoid JSON parsers
                                        self._try_parser(A1111, raw=uc_str_gen)
                            except Exception:  # pylint: disable=broad-except
                                self._logger.debug(
                                    "Generic A1111 UserComment fallback attempt failed."
                                )

        except FileNotFoundError:
            self._logger.error("Image file not found: %s", file_display_name)
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = "Image file not found."
        except UnidentifiedImageError as unident_err:
            self._logger.error(
                "Cannot identify image file '%s': %s", file_display_name, unident_err
            )
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"Cannot identify image: {unident_err}"
        except OSError as e_io:  # Catch more specific IO errors
            self._logger.error(
                "OS/IO error opening image '%s': %s",
                file_display_name,
                e_io,
                exc_info=True,
            )
            self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error:
                self._error = f"File system error: {e_io}"
        except Exception as outer_open_err:  # Fallback for other Pillow errors
            self._logger.error(
                "Error opening/processing image '%s': %s",
                file_display_name,
                outer_open_err,
                exc_info=True,
            )
            self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error:
                self._error = f"Pillow/general error: {outer_open_err}"

        if (
            self._status == BaseFormat.Status.UNREAD
        ):  # If no parser succeeded and no major open error
            self._logger.warning(
                "No suitable parser found for '%s' or no parser claimed success.",
                file_display_name,
            )
            self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error:
                self._error = "No suitable metadata parser found."

        log_tool = self._tool or "None"
        log_status = (
            self._status.name if hasattr(self._status, "name") else str(self._status)
        )
        self._logger.info(
            "Final Reading Status for '%s': %s, Tool: %s",
            file_display_name,
            log_status,
            log_tool,
        )

        final_error_to_log = self._error
        if self._parser and getattr(self._parser, "error", None):
            if self._status != BaseFormat.Status.READ_SUCCESS or not final_error_to_log:
                final_error_to_log = self._parser.error
        if self._status != BaseFormat.Status.READ_SUCCESS and final_error_to_log:
            self._logger.warning("Error details: %s", final_error_to_log)

    @staticmethod
    def remove_data(
        image_file_path: str | Path,
    ) -> Image.Image | None:  # Return type PIL.Image
        logger_instance = get_logger("DSVendored_SDPR.ImageDataReader.RemoveData")
        try:
            with Image.open(image_file_path) as img_file:
                image_data = list(img_file.getdata())  # This loads all pixel data
                image_without_exif = Image.new(img_file.mode, img_file.size)
                image_without_exif.putdata(image_data)
                return image_without_exif
        except FileNotFoundError:
            logger_instance.error("remove_data: File not found - %s", image_file_path)
        except UnidentifiedImageError:
            logger_instance.error(
                "remove_data: Cannot identify image - %s", image_file_path
            )
        except Exception as general_err:
            logger_instance.error(
                "remove_data: Error processing %s - %s",
                image_file_path,
                general_err,
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
        logger_instance = get_logger("DSVendored_SDPR.ImageDataReader.Save")
        metadata_to_embed: Any = None
        image_format_upper = image_format.strip().upper()  # Standardize once

        if data:
            if image_format_upper == "PNG":
                metadata_to_embed = PngInfo()
                metadata_to_embed.add_text(
                    "parameters", data
                )  # Standard param key for A1111-like
            elif image_format_upper in ["JPEG", "JPG", "WEBP"]:
                try:
                    user_comment_bytes = piexif.helper.UserComment.dump(
                        str(data), encoding="unicode"
                    )
                    exif_dict = {
                        "Exif": {piexif.ExifIFD.UserComment: user_comment_bytes}
                    }
                    # Could add other basic EXIF like Software tag here if desired
                    # exif_dict["0th"] = {piexif.ImageIFD.Software: b"DatasetTools"}
                    metadata_to_embed = piexif.dump(exif_dict)
                except Exception as dump_err:
                    logger_instance.error(
                        "piexif dump error for %s: %s",
                        image_format_upper,
                        dump_err,
                        exc_info=True,
                    )
                    metadata_to_embed = None

        try:
            with Image.open(image_path) as img_to_save:
                save_kwargs: dict[str, Any] = {}
                if image_format_upper == "PNG" and metadata_to_embed:
                    save_kwargs["pnginfo"] = metadata_to_embed
                elif image_format_upper in ["JPEG", "JPG"]:
                    save_kwargs["quality"] = 95  # Good default
                    if metadata_to_embed:
                        save_kwargs["exif"] = metadata_to_embed
                    elif img_to_save.info.get("exif"):
                        save_kwargs["exif"] = img_to_save.info[
                            "exif"
                        ]  # Preserve existing
                elif image_format_upper == "WEBP":
                    save_kwargs["quality"] = 100
                    save_kwargs["lossless"] = True
                    if metadata_to_embed:
                        save_kwargs["exif"] = metadata_to_embed
                    elif img_to_save.info.get("exif"):
                        save_kwargs["exif"] = img_to_save.info[
                            "exif"
                        ]  # Preserve existing

                img_to_save.save(new_path, **save_kwargs)
                logger_instance.info(
                    "Image saved to %s with format %s", new_path, image_format_upper
                )

        except FileNotFoundError:
            logger_instance.error(
                "Image save error: Source file not found - %s", image_path
            )
        except UnidentifiedImageError:
            logger_instance.error(
                "Image save error: Cannot identify source image - %s", image_path
            )
        except Exception as save_err:
            logger_instance.error(
                "Image save error for %s: %s", new_path, save_err, exc_info=True
            )

    @staticmethod
    def construct_data(positive: str, negative: str, setting: str) -> str:
        parts = []
        if positive:
            parts.append(positive)
        if negative:
            parts.append(f"Negative prompt: {negative}")  # Consistent prefix
        if setting:
            parts.append(setting)
        return "\n".join(parts)

    def prompt_to_line(self) -> str:
        if self._parser and hasattr(self._parser, "prompt_to_line"):
            return self._parser.prompt_to_line()
        return self.construct_data(self.positive, self.negative, self.setting)

    @property
    def height(self) -> str:
        parser_h = str(getattr(self._parser, "height", "0"))
        try:
            return (
                parser_h
                if int(parser_h) > 0
                else (str(self._height) if self._height > 0 else "0")
            )
        except ValueError:
            return str(self._height) if self._height > 0 else "0"

    @property
    def width(self) -> str:
        parser_w = str(getattr(self._parser, "width", "0"))
        try:
            return (
                parser_w
                if int(parser_w) > 0
                else (str(self._width) if self._width > 0 else "0")
            )
        except ValueError:
            return str(self._width) if self._width > 0 else "0"

    @property
    def info(self) -> dict[str, Any]:
        return self._info.copy()  # Return a copy

    @property
    def positive(self) -> str:
        return str(getattr(self._parser, "positive", self._positive))

    @property
    def negative(self) -> str:
        return str(getattr(self._parser, "negative", self._negative))

    @property
    def positive_sdxl(self) -> dict[str, Any]:
        return getattr(self._parser, "positive_sdxl", None) or self._positive_sdxl or {}

    @property
    def negative_sdxl(self) -> dict[str, Any]:
        return getattr(self._parser, "negative_sdxl", None) or self._negative_sdxl or {}

    @property
    def setting(self) -> str:
        return str(getattr(self._parser, "setting", self._setting))

    @property
    def raw(self) -> str:
        parser_raw = getattr(self._parser, "raw", None)
        return str(parser_raw if parser_raw is not None else self._raw)

    @property
    def tool(self) -> str:
        parser_tool = getattr(self._parser, "tool", None)
        return (
            str(parser_tool)
            if parser_tool and parser_tool != "Unknown"
            else str(self._tool)
        )

    @property
    def parameter(self) -> dict[str, Any]:
        parser_param = getattr(self._parser, "parameter", None)
        return parser_param if parser_param is not None else (self._parameter or {})

    @property
    def format(self) -> str:
        return self._format_str

    @property
    def is_sdxl(self) -> bool:
        return getattr(self._parser, "is_sdxl", self._is_sdxl)

    @property
    def props(self) -> str:
        if self._parser and hasattr(self._parser, "props"):
            return self._parser.props
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
        return str(
            parser_err
            if parser_err and self._status != BaseFormat.Status.READ_SUCCESS
            else self._error
        )
