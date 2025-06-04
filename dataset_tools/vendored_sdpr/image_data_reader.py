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
from typing import Any, BinaryIO, TextIO

import piexif
import piexif.helper
from defusedxml import minidom  # Used in _parse_drawthings_xmp
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


# pylint: disable=too-many-instance-attributes # Class-level Pylint disable
# Ruff might need specific rule codes if it has its own for this, e.g.
class ImageDataReader:
    """Reads and parses metadata from image files or text files.
    Attempts to identify the AI tool used and extracts prompts, settings, etc.
    """

    NOVELAI_MAGIC = "stealth_pngcomp"

    def __init__(
        self,
        file_path_or_obj: str | Path | TextIO | BinaryIO,
        is_txt: bool = False,
    ):  # ANN204: Missing type hint for self in method __init__ (if strict) -> typically not needed for __init__
        # pylint: disable=too-many-statements (If __init__ itself is too long)
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

        base_param_key_attr = getattr(BaseFormat, "PARAMETER_KEY", [])
        self._parameter_key: list[str] = (
            base_param_key_attr
            if isinstance(base_param_key_attr, list)
            else ["model", "sampler", "seed", "cfg", "steps", "size"]
        )

        self._parameter: dict[str, Any] = dict.fromkeys(self._parameter_key, PARAMETER_PLACEHOLDER)
        self._is_txt: bool = is_txt
        self._is_sdxl: bool = False
        self._format_str: str = ""
        self._parser: BaseFormat | None = None
        self._status: BaseFormat.Status = BaseFormat.Status.UNREAD
        self._error: str = ""
        self._logger: logging.Logger = get_logger("DSVendored_SDPR.ImageDataReader")

        self.read_data(file_path_or_obj)

    def _initialize_state(self) -> None:
        """Resets internal state variables before a new read operation."""
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
        self._format_str = ""

    def _get_display_name(self, file_path_or_obj: str | Path | TextIO | BinaryIO) -> str:
        """Gets a displayable name for the file or file-like object being processed."""
        if hasattr(file_path_or_obj, "name") and file_path_or_obj.name:
            try:
                return Path(file_path_or_obj.name).name
            except TypeError:
                return str(file_path_or_obj.name)
        if isinstance(file_path_or_obj, (str, Path)):
            return Path(file_path_or_obj).name
        return "UnnamedFileObject"

    def _try_parser(self, parser_class: type[BaseFormat], **kwargs: Any) -> bool:
        """Attempts to parse data using the given parser class."""
        kwarg_keys_for_log = list(kwargs.keys())
        self._logger.debug(
            "Attempting parser: %s with kwargs: %s",
            parser_class.__name__,
            kwarg_keys_for_log,
        )
        try:
            if "width" not in kwargs and self._width > 0:
                kwargs["width"] = self._width
            if "height" not in kwargs and self._height > 0:
                kwargs["height"] = self._height

            temp_parser = parser_class(**kwargs)
            parser_own_status = temp_parser.parse()

            if parser_own_status == BaseFormat.Status.READ_SUCCESS:
                self._parser = temp_parser
                self._tool = getattr(self._parser, "tool", parser_class.__name__)
                self._status = BaseFormat.Status.READ_SUCCESS
                self._error = ""
                self._logger.info("Successfully parsed as %s.", self._tool)
                return True

            parser_error_msg = getattr(temp_parser, "error", "Unknown parser error")
            status_name = parser_own_status.name if hasattr(parser_own_status, "name") else str(parser_own_status)
            self._logger.debug(
                "%s parsing attempt: Status %s. Error: %s",
                parser_class.__name__,
                status_name,
                parser_error_msg,
            )
            if parser_error_msg and (self._status == BaseFormat.Status.UNREAD or not self._error):
                self._error = parser_error_msg
            return False
        except TypeError as type_err:
            self._logger.error(
                "TypeError with %s: %s. Check __init__/parse.",
                parser_class.__name__,
                type_err,
                exc_info=True,
            )
            if self._status == BaseFormat.Status.UNREAD:
                self._error = f"Init/call error for {parser_class.__name__}: {type_err}"
            return False
        except Exception as general_exception:
            self._logger.error(
                "Unexpected exception during %s attempt: %s",
                parser_class.__name__,
                general_exception,
                exc_info=True,
            )
            if self._status == BaseFormat.Status.UNREAD:
                self._error = f"Runtime error in {parser_class.__name__}: {general_exception}"
            return False

    def _handle_text_file(self, file_obj: TextIO) -> None:
        """Processes a file object assumed to be a text file."""
        try:
            self._raw = file_obj.read()
        except Exception as e_read:
            self._logger.error("Error reading text file object: %s", e_read, exc_info=True)
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"Could not read text file content: {e_read!s}"
            return

        if not self._try_parser(A1111, raw=self._raw):  # Try A1111, if fails, set error
            if self._status == BaseFormat.Status.UNREAD:
                self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error:
                self._error = "Failed to parse text file as A1111 format."

        log_status_name = self._status.name if hasattr(self._status, "name") else str(self._status)
        self._logger.info(
            "Text file processed. Final Status: %s, Tool: %s",
            log_status_name,
            self._tool or "None",
        )

    def _attempt_legacy_swarm_exif(self, image_obj: Image.Image) -> None:
        """Attempts to parse legacy SwarmUI data from EXIF tag 0x0110."""
        if self._parser:
            return
        try:
            exif_pil = image_obj.getexif()
            if (
                exif_pil and (exif_json_str := exif_pil.get(0x0110)) and isinstance(exif_json_str, (str, bytes))
            ):  # Walrus
                if isinstance(exif_json_str, bytes):
                    exif_json_str = exif_json_str.decode("utf-8", errors="ignore")
                if "sui_image_params" in exif_json_str:
                    try:
                        exif_dict = json.loads(exif_json_str)
                        if isinstance(exif_dict, dict) and "sui_image_params" in exif_dict:
                            self._try_parser(SwarmUI, info=exif_dict)
                    except json.JSONDecodeError as json_err:
                        self._logger.debug("SwarmUI legacy EXIF (0x0110): Invalid JSON: %s", json_err)
        except Exception as e:
            self._logger.debug("SwarmUI legacy EXIF (0x0110) check failed: %s", e, exc_info=False)

    def _process_png_chunks(self, image_obj: Image.Image) -> None:
        """Processes PNG tEXt/iTXt/zTXt chunks for metadata."""
        if self._parser:
            return

        png_params = self._info.get("parameters")
        png_prompt = self._info.get("prompt")
        png_workflow = self._info.get("workflow")
        png_postproc = self._info.get("postprocessing")
        png_neg_prompt_ed = self._info.get("negative_prompt") or self._info.get("Negative Prompt")
        png_invoke_meta_keys = ["invokeai_metadata", "sd-metadata", "Dream"]
        png_invoke_meta_content = {k: self._info[k] for k in png_invoke_meta_keys if k in self._info}
        png_software = self._info.get("Software")
        png_comment = self._info.get("Comment")
        png_xmp = self._info.get("XML:com.adobe.xmp")

        parsers_to_try = [
            (A1111, {"info": self._info}, lambda: bool(png_params or png_postproc)),
            (EasyDiffusion, {"info": self._info}, lambda: bool(png_neg_prompt_ed)),
            (InvokeAI, {"info": self._info}, lambda: bool(png_invoke_meta_content)),
            (
                NovelAI,
                {"info": self._info},
                lambda: png_software == "NovelAI",
            ),  # width/height passed by _try_parser
            (ComfyUI, {"info": self._info}, lambda: bool(png_prompt or png_workflow)),
        ]  # width/height by _try_parser
        for parser_class, kwargs, condition_fn in parsers_to_try:
            if self._parser:
                break
            if condition_fn():
                self._try_parser(parser_class, **kwargs)

        if not self._parser and png_comment:
            try:
                comment_data = json.loads(png_comment)
                if isinstance(comment_data, dict) and "prompt" in comment_data:
                    self._try_parser(Fooocus, info=comment_data)
            except json.JSONDecodeError:
                self._logger.debug("PNG Comment not valid JSON or not Fooocus.")
        if not self._parser and png_params and "sui_image_params" in png_params:
            self._try_parser(SwarmUI, raw=png_params)
        if not self._parser and png_xmp:
            self._parse_drawthings_xmp(png_xmp)
        if not self._parser and image_obj.mode == "RGBA":
            self._parse_novelai_lsb(image_obj)

    def _parse_drawthings_xmp(self, xmp_chunk: str) -> None:
        """Parses DrawThings metadata from XMP chunk."""
        if self._parser:
            return
        try:
            xmp_dom = minidom.parseString(xmp_chunk)
            description_nodes = xmp_dom.getElementsByTagName("rdf:Description")
            for desc_node in description_nodes:
                uc_nodes = desc_node.getElementsByTagName("exif:UserComment")
                data_str = None
                if not uc_nodes or not uc_nodes[0].childNodes:
                    continue
                first_child = uc_nodes[0].childNodes[0]
                if first_child.nodeType == first_child.TEXT_NODE:
                    data_str = first_child.data
                elif first_child.nodeName == "rdf:Alt":
                    alt_node = first_child
                    li_nodes = alt_node.getElementsByTagName("rdf:li")
                    if (
                        li_nodes
                        and li_nodes[0].childNodes
                        and li_nodes[0].childNodes[0].nodeType == li_nodes[0].TEXT_NODE
                    ):
                        data_str = li_nodes[0].childNodes[0].data
                if data_str:
                    self._try_parser(DrawThings, info=json.loads(data_str.strip()))
                if self._parser:
                    return
        except (minidom.ExpatError, json.JSONDecodeError) as e:
            self._logger.warning("DrawThings PNG XMP: Parse error: %s", e)
        except Exception as e:
            self._logger.warning("DrawThings PNG XMP: Error: %s", e, exc_info=True)

    def _parse_novelai_lsb(self, image_obj: Image.Image) -> None:
        """Parses NovelAI metadata from LSB steganography."""
        if self._parser:
            return
        try:
            extractor = NovelAI.LSBExtractor(image_obj)
            if not extractor.lsb_bytes_list:
                self._logger.debug("NovelAI LSB: Extractor no data.")
                return
            magic_bytes = extractor.get_next_n_bytes(len(self.NOVELAI_MAGIC))
            if magic_bytes and magic_bytes.decode("utf-8", "ignore") == self.NOVELAI_MAGIC:
                self._try_parser(NovelAI, extractor=extractor)
        except Exception as e:
            self._logger.warning("NovelAI LSB check error: %s", e, exc_info=True)

    def _process_jpeg_webp_exif(self, image_obj: Image.Image) -> None:
        """Processes EXIF data from JPEG/WEBP images."""
        if self._parser:
            return
        raw_uc: str | None = None
        sw_tag: str = ""
        jfif_c_bytes = self._info.get("comment", b"")
        jfif_c = jfif_c_bytes.decode("utf-8", "ignore") if isinstance(jfif_c_bytes, bytes) else ""
        if exif_b := self._info.get("exif"):  # Walrus for exif_bytes
            try:
                exif_d = piexif.load(exif_b)
                uc_b = exif_d.get("Exif", {}).get(piexif.ExifIFD.UserComment)
                raw_uc = piexif.helper.UserComment.load(uc_b) if uc_b else None
                sw_b = exif_d.get("0th", {}).get(piexif.ImageIFD.Software)
                sw_tag = sw_b.decode("ascii", "ignore").strip() if sw_b and isinstance(sw_b, bytes) else ""
            except piexif.InvalidImageDataError as e:
                self._logger.warning("piexif EXIF load error: %s", e)
            except Exception as e:
                self._logger.warning("piexif EXIF general error: %s", e, exc_info=True)
        if raw_uc and not self._parser:
            if raw_uc.strip().startswith("{"):
                try:
                    uc_j = json.loads(raw_uc)
                    isinstance(uc_j, dict) and uc_j.get("software") == "RuinedFooocus" and self._try_parser(
                        RuinedFooocusFormat, raw=raw_uc
                    )
                except json.JSONDecodeError:
                    pass
            if not self._parser:
                is_cv = (
                    sw_tag == "4c6047c3-8b1c-4058-8888-fd48353bf47d"
                    or ("charset=Unicode" in raw_uc and '"extraMetadata":' in raw_uc)
                    or (raw_uc.startswith('{"resource-stack":') and '"extraMetadata":' in raw_uc)
                )
                if is_cv:
                    self._try_parser(CivitaiComfyUIFormat, raw=raw_uc)
        if not self._parser and jfif_c:
            try:
                jfif_j = json.loads(jfif_c)
                isinstance(jfif_j, dict) and "prompt" in jfif_j and self._try_parser(Fooocus, info=jfif_j)
            except json.JSONDecodeError:
                self._logger.debug("JFIF Comment not Fooocus JSON.")
        if not self._parser and raw_uc:
            self._raw = raw_uc
            if "sui_image_params" in raw_uc:
                self._try_parser(SwarmUI, raw=self._raw)
            elif raw_uc.strip().startswith("{"):
                self._try_parser(EasyDiffusion, raw=self._raw)
            else:
                self._try_parser(A1111, raw=self._raw)
        if not self._parser and image_obj.mode == "RGBA":
            self._parse_novelai_lsb(image_obj)

    def _process_image_file(self, file_path_or_obj: str | Path | BinaryIO, file_display_name: str) -> None:
        """Handles opening and processing image files (non-text)."""
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
                self._attempt_legacy_swarm_exif(img)
                if not self._parser:
                    if self._format_str == "PNG":
                        self._process_png_chunks(img)
                    elif self._format_str in ["JPEG", "WEBP"]:
                        self._process_jpeg_webp_exif(img)
                    else:
                        self._logger.info(  # Line 502 area - FIXED
                            "Image format '%s' not specifically handled for detailed metadata"
                            " beyond basic Pillow info.",
                            self._format_str,
                        )
                        if not self._parser and (exif_b := self._info.get("exif")):
                            try:
                                exif_d = piexif.load(exif_b)
                                uc_b = exif_d.get("Exif", {}).get(piexif.ExifIFD.UserComment)
                                if uc_b:
                                    uc_s = piexif.helper.UserComment.load(uc_b)
                                    uc_s and not uc_s.strip().startswith("{") and self._try_parser(A1111, raw=uc_s)
                            except Exception:
                                self._logger.debug("Generic A1111 UserComment fallback failed.")
        except FileNotFoundError:
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = "Image file not found."
            self._logger.error("Image file not found: %s", file_display_name)
        except UnidentifiedImageError as e:
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"Cannot identify image: {e!s}"
            self._logger.error("Cannot identify image file '%s': %s", file_display_name, e)
        except OSError as e:
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"File system error: {e!s}"
            self._logger.error(
                "OS/IO error opening image '%s': %s",
                file_display_name,
                e,
                exc_info=True,
            )
        except Exception as e:
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"Pillow/general error: {e!s}"
            self._logger.error(
                "Error opening/processing image '%s': %s",
                file_display_name,
                e,
                exc_info=True,
            )

    def read_data(self, file_path_or_obj: str | Path | TextIO | BinaryIO) -> None:
        """Main method to read and parse data from the provided file or object."""
        self._initialize_state()
        file_display_name = self._get_display_name(file_path_or_obj)
        self._logger.debug("Reading data for: %s (is_txt: %s)", file_display_name, self._is_txt)

        if self._is_txt:
            if hasattr(file_path_or_obj, "read") and callable(file_path_or_obj.read):
                self._handle_text_file(file_path_or_obj)  # type: ignore[arg-type]
            else:
                self._logger.error("Text file input expected readable file object.")
                self._status = BaseFormat.Status.FORMAT_ERROR
                self._error = "Invalid file object for text."
        else:
            self._process_image_file(file_path_or_obj, file_display_name)  # type: ignore[arg-type]

        if self._status == BaseFormat.Status.UNREAD:
            self._logger.warning("No suitable parser for '%s' or parser failed.", file_display_name)
            self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error:
                self._error = "No suitable metadata parser or file unreadable/corrupted."

        log_tool = self._tool or "None"
        log_status_name = self._status.name if hasattr(self._status, "name") else str(self._status)
        self._logger.info(
            "Final Reading Status for '%s': %s, Tool: %s",
            file_display_name,
            log_status_name,
            log_tool,
        )
        final_error_to_log = self._error
        if self._parser and hasattr(self._parser, "error") and self._parser.error:
            if self._status != BaseFormat.Status.READ_SUCCESS or not final_error_to_log:
                final_error_to_log = self._parser.error
        if self._status != BaseFormat.Status.READ_SUCCESS and final_error_to_log:
            self._logger.warning("Error details: %s", final_error_to_log)

    @staticmethod  # ANN205: Missing type hint for self in staticmethod (not applicable as no self)
    def remove_data(image_file_path: str | Path) -> Image.Image | None:
        """Removes all metadata from an image, returning a new PIL Image object without it."""
        logger_instance = get_logger("DSVendored_SDPR.ImageDataReader.RemoveData")
        try:
            with Image.open(image_file_path) as img_file:
                img_file.load()
                image_data = list(img_file.getdata())
                image_without_exif = Image.new(img_file.mode, img_file.size)
                image_without_exif.putdata(image_data)
                return image_without_exif
        except FileNotFoundError:
            logger_instance.error("remove_data: File not found - %s", image_file_path)
        except UnidentifiedImageError:
            logger_instance.error("remove_data: Cannot identify image - %s", image_file_path)
        except Exception as general_err:
            logger_instance.error(
                "remove_data: Error processing %s - %s",
                image_file_path,
                general_err,
                exc_info=True,
            )
        return None

    @staticmethod  # ANN205
    def save_image(
        image_path: str | Path,
        new_path: str | Path,
        image_format: str,
        data: str | None = None,
        quality: int = 95,
        lossless_webp: bool = True,
    ) -> None:
        """Saves an image, optionally embedding metadata."""
        logger_instance = get_logger("DSVendored_SDPR.ImageDataReader.Save")
        metadata_to_embed: Any = None
        image_format_upper = image_format.strip().upper()

        if data:
            if image_format_upper == "PNG":
                metadata_to_embed = PngInfo()
                metadata_to_embed.add_text("parameters", data)
            elif image_format_upper in ["JPEG", "JPG", "WEBP"]:
                try:
                    user_comment_bytes = piexif.helper.UserComment.dump(str(data), encoding="unicode")
                    exif_dict = {"Exif": {piexif.ExifIFD.UserComment: user_comment_bytes}}
                    metadata_to_embed = piexif.dump(exif_dict)
                except Exception as dump_err:
                    logger_instance.error(
                        "piexif dump error for %s: %s",
                        image_format_upper,
                        dump_err,
                        exc_info=True,
                    )
        try:
            with Image.open(image_path) as img_to_save:
                save_kwargs: dict[str, Any] = {}
                if image_format_upper == "PNG":
                    if metadata_to_embed:
                        save_kwargs["pnginfo"] = metadata_to_embed
                elif image_format_upper in ["JPEG", "JPG"]:
                    save_kwargs["quality"] = quality
                    if metadata_to_embed:
                        save_kwargs["exif"] = metadata_to_embed
                    elif img_to_save.info.get("exif"):
                        save_kwargs["exif"] = img_to_save.info["exif"]
                elif image_format_upper == "WEBP":
                    save_kwargs["quality"] = quality
                    save_kwargs["lossless"] = lossless_webp
                    if metadata_to_embed:
                        save_kwargs["exif"] = metadata_to_embed
                    elif img_to_save.info.get("exif"):
                        save_kwargs["exif"] = img_to_save.info["exif"]
                img_to_save.save(new_path, **save_kwargs)
                logger_instance.info("Image saved to %s with format %s", new_path, image_format_upper)
        except FileNotFoundError:
            logger_instance.error("Image save error: Source file not found - %s", image_path)
        except UnidentifiedImageError:
            logger_instance.error("Image save error: Cannot identify source image - %s", image_path)
        except Exception as save_err:
            logger_instance.error("Image save error for %s: %s", new_path, save_err, exc_info=True)

    @staticmethod  # ANN205
    def construct_data(positive: str, negative: str, setting: str) -> str:
        """Constructs a standard metadata string from positive, negative, and setting parts."""
        parts = []
        if positive:
            parts.append(positive)
        if negative:
            parts.append(f"Negative prompt: {negative}")
        if setting:
            parts.append(setting)
        return "\n".join(parts)

    def prompt_to_line(self) -> str:
        """Generates a CLI-like representation of the parsed prompt and key parameters."""
        if self._parser and hasattr(self._parser, "prompt_to_line"):
            return self._parser.prompt_to_line()
        return self.construct_data(self.positive, self.negative, self.setting)

    # --- Properties ---
    # Properties are condensed for brevity as their logic is straightforward.
    # Add type hints if Ruff requires for properties.
    @property
    def height(self) -> str:
        ph = str(getattr(self._parser, "height", "0"))
        return ph if ph.isdigit() and int(ph) > 0 else (str(self._height) if self._height > 0 else "0")

    @property
    def width(self) -> str:
        pw = str(getattr(self._parser, "width", "0"))
        return pw if pw.isdigit() and int(pw) > 0 else (str(self._width) if self._width > 0 else "0")

    @property
    def info(self) -> dict[str, Any]:
        return self._info.copy()

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
        pr = getattr(self._parser, "raw", None)
        return str(pr if pr is not None else self._raw)

    @property
    def tool(self) -> str:
        pt = getattr(self._parser, "tool", None)
        return str(pt) if pt and pt != "Unknown" else str(self._tool)

    @property
    def parameter(self) -> dict[str, Any]:
        pp = getattr(self._parser, "parameter", None)
        return pp.copy() if pp is not None else (self._parameter.copy() if self._parameter else {})  # Ensure copy

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
        fb_p = {
            "positive": self.positive,
            "negative": self.negative,
            "width": self.width,
            "height": self.height,
            "tool": self.tool,
            "setting": self.setting,
        }
        fb_p.update(self.parameter)
        return json.dumps(fb_p, indent=2)

    @property
    def status(self) -> BaseFormat.Status:
        return self._status

    @property
    def error(self) -> str:
        pe = getattr(self._parser, "error", None)
        return str(pe if pe and self._status != BaseFormat.Status.READ_SUCCESS else self._error)
