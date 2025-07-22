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
from defusedxml import minidom
from PIL import Image, UnidentifiedImageError

from .constants import PARAMETER_PLACEHOLDER
from .format import (
    A1111,
    BaseFormat,
    CivitaiFormat,  # YodayoFormat,
    ComfyUI,
    DrawThings,
    EasyDiffusion,
    Fooocus,
    InvokeAI,
    MochiDiffusionFormat,  # Now expects IPTC data
    NovelAI,
    RuinedFooocusFormat,
    SwarmUI,
)
from .logger import get_logger

# IPTC tag constants from piexif for clarity
IPTC_CAPTION_ABSTRACT = (2, 120)  # piexif.IPTCApplicationRecord.Caption
IPTC_ORIGINATING_PROGRAM = (
    2,
    65,
)  # piexif.IPTCApplicationRecord.OriginatingProgram - check if this is the right tag for Mochi's intent
IPTC_PROGRAM_VERSION = (2, 70)  # piexif.IPTCApplicationRecord.ProgramVersion

# Alternative: Pillow's getiptcinfo() uses string keys if IPTCIM is available
# For Mochi: 'caption/abstract', 'originating program', 'program version'
# These are more user-friendly if available.


class ImageDataReader:
    NOVELAI_MAGIC = "stealth_pngcomp"

    PARSER_CLASSES_PNG = [
        ComfyUI,
        CivitaiFormat,
        # YodayoFormat,
        A1111,
        EasyDiffusion,
        InvokeAI,
        NovelAI,
        SwarmUI,
        MochiDiffusionFormat,  # Mochi might save IPTC to PNGs via some mechanism, try last for PNGs
    ]

    PARSER_CLASSES_JPEG_WEBP = [
        # RuinedFooocus is handled specially before this loop
        DrawThings,
        MochiDiffusionFormat,  # <<< MOCHI FIRST FOR JPEG/WEBP due to specific IPTC usage
        CivitaiFormat,
        EasyDiffusion,
        # YodayoFormat,
        A1111,
        SwarmUI,
    ]

    def __init__(
        self,
        file_path_or_obj: str | Path | TextIO | BinaryIO,
        is_txt: bool = False,
    ):
        self._height: int = 0
        self._width: int = 0
        self._info: dict[str, Any] = {}  # Raw PIL info
        self._parsed_iptc_info: dict[str, str] = {}  # Store extracted IPTC fields
        self._positive: str = ""
        self._negative: str = ""
        # ... (other attributes as before) ...
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
        self._exif_software_tag: str | None = None
        self.read_data(file_path_or_obj)

    def _initialize_state(self) -> None:
        # ... (as before) ...
        self._status = BaseFormat.Status.UNREAD
        self._error = ""
        self._parser = None
        self._tool = ""
        self._raw = ""
        self._info = {}
        self._parsed_iptc_info = {}  # <<< ADDED: Reset parsed IPTC
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
        self._exif_software_tag = None

    def _get_display_name(self, file_path_or_obj: str | Path | TextIO | BinaryIO) -> str:
        # ... (as before) ...
        if hasattr(file_path_or_obj, "name") and file_path_or_obj.name:
            try:
                return Path(file_path_or_obj.name).name
            except TypeError:
                return str(file_path_or_obj.name)
        if isinstance(file_path_or_obj, (str, Path)):
            return Path(file_path_or_obj).name
        return "UnnamedFileObject"

    def _try_parser(self, parser_class: type[BaseFormat], **kwargs: Any) -> bool:
        # ... (logging for kwargs as before, ensuring raw is truncated) ...
        kwarg_keys_for_log = []
        temp_kwargs_for_log = kwargs.copy()
        if (
            "raw" in temp_kwargs_for_log
            and isinstance(temp_kwargs_for_log["raw"], str)
            and len(temp_kwargs_for_log["raw"]) > 70
        ):
            temp_kwargs_for_log["raw"] = temp_kwargs_for_log["raw"][:67] + "..."

        for k, v_val in temp_kwargs_for_log.items():
            if k == "logger_obj":
                continue
            if k == "info" and isinstance(v_val, dict):
                kwarg_keys_for_log.append("info=<dict>")
            else:
                kwarg_keys_for_log.append(f"{k}='{v_val}'" if isinstance(v_val, str) else f"{k}={v_val}")

        self._logger.debug(
            "Attempting parser: %s with kwargs: [%s]",
            parser_class.__name__,
            ", ".join(kwarg_keys_for_log),
        )
        # ... (rest of _try_parser as before, ensuring 'info' passed to parser includes software_tag and potentially iptc_info) ...
        try:
            if "width" not in kwargs and self._width > 0:
                kwargs["width"] = self._width
            if "height" not in kwargs and self._height > 0:
                kwargs["height"] = self._height

            kwargs["logger_obj"] = self._logger

            # Consolidate info to pass to parser
            # Start with a copy of existing kwargs["info"] or an empty dict
            parser_info_arg = kwargs.get("info", {}).copy()
            if not isinstance(parser_info_arg, dict):
                parser_info_arg = {}

            if self._exif_software_tag:
                parser_info_arg["software_tag"] = self._exif_software_tag

            # Add parsed IPTC info if Mochi is being tried (or make it general)
            # If MochiDiffusionFormat, ensure it gets the IPTC fields
            if parser_class is MochiDiffusionFormat and self._parsed_iptc_info:
                parser_info_arg.update(self._parsed_iptc_info)  # Add all parsed IPTC fields

            if parser_info_arg:  # Only pass info if it has content
                kwargs["info"] = parser_info_arg
            elif "info" in kwargs and not parser_info_arg:  # Remove empty info from kwargs
                del kwargs["info"]

            parser_kwargs = kwargs.copy()
            if parser_class in [SwarmUI, NovelAI]:
                parser_kwargs.pop("width", None)
                parser_kwargs.pop("height", None)
                parser_kwargs.pop("logger_obj", None)

            temp_parser = parser_class(**parser_kwargs)
            parser_own_status = temp_parser.parse()

            if parser_own_status == BaseFormat.Status.READ_SUCCESS:
                self._parser = temp_parser
                self._tool = getattr(self._parser, "tool", parser_class.__name__)
                self._status = BaseFormat.Status.READ_SUCCESS
                self._error = ""
                self._logger.info("Successfully parsed as %s.", self._tool)
                return True

            if parser_own_status != BaseFormat.Status.FORMAT_DETECTION_ERROR:
                parser_error_msg = getattr(temp_parser, "error", "Unknown parser error")
                if parser_error_msg and (self._status == BaseFormat.Status.UNREAD or not self._error):
                    self._error = parser_error_msg

            status_name = parser_own_status.name if hasattr(parser_own_status, "name") else str(parser_own_status)
            self._logger.debug(
                "%s parsing attempt: Status %s. Error: %s",
                parser_class.__name__,
                status_name,
                getattr(temp_parser, "error", "N/A"),
            )
            return False
        except TypeError as type_err:  # Catch TyperError from parser_class(**kwargs)
            self._logger.error(
                "TypeError with %s init/call: %s. Check parser's __init__ signature and kwargs. Passed: %s",
                parser_class.__name__,
                type_err,
                kwargs.keys(),  # Log keys that were passed
                exc_info=True,
            )
            if self._status == BaseFormat.Status.UNREAD:
                self._error = f"Init/call error for {parser_class.__name__}: {type_err}"
            return False
        except Exception as general_exception:  # Catch other exceptions during parse()
            self._logger.error(
                "Unexpected exception during %s.parse() attempt: %s",
                parser_class.__name__,
                general_exception,
                exc_info=True,
            )
            if self._status == BaseFormat.Status.UNREAD:
                self._error = f"Runtime error in {parser_class.__name__}: {general_exception}"
            return False

    def _handle_text_file(self, file_obj: TextIO) -> None:
        # ... (as before) ...
        raw_text_content = ""
        try:
            raw_text_content = file_obj.read()
        except Exception as e_read:
            self._logger.error("Error reading text file object: %s", e_read, exc_info=True)
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = f"Could not read text file content: {e_read!s}"
            return
        if not self._try_parser(A1111, raw=raw_text_content):
            if self._status == BaseFormat.Status.UNREAD:
                self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error:
                self._error = "Failed to parse text file as A1111 format."
        if not self._parser:
            self._raw = raw_text_content
        log_status_name = self._status.name if hasattr(self._status, "name") else str(self._status)
        self._logger.info(
            "Text file processed. Final Status: %s, Tool: %s",
            log_status_name,
            self._tool or "None",
        )

    def _attempt_legacy_swarm_exif(self, image_obj: Image.Image) -> None:
        # ... (as before) ...
        if self._parser:
            return
        try:
            exif_pil = image_obj.getexif()
            if exif_pil and (exif_json_str := exif_pil.get(0x0110)) and isinstance(exif_json_str, (str, bytes)):
                if isinstance(exif_json_str, bytes):
                    exif_json_str = exif_json_str.decode("utf-8", errors="ignore")
                if "sui_image_params" in exif_json_str:
                    try:
                        exif_dict = json.loads(exif_json_str)
                        if isinstance(exif_dict, dict) and "sui_image_params" in exif_dict:
                            if self._try_parser(SwarmUI, info=exif_dict):
                                return
                    except json.JSONDecodeError as json_err:
                        self._logger.debug("SwarmUI legacy EXIF (0x0110): Invalid JSON: %s", json_err)
        except Exception as e:
            self._logger.debug("SwarmUI legacy EXIF (0x0110) check failed: %s", e, exc_info=False)

    def _process_png_chunks(self, image_obj: Image.Image) -> None:
        # ... (as before, but ensure MochiDiffusionFormat is called appropriately if it might use info for PNGs) ...
        if self._parser:
            return

        png_params_chunk = self._info.get("parameters")
        png_comment_chunk = self._info.get("Comment")
        png_xmp_chunk = self._info.get("XML:com.adobe.xmp")
        png_user_comment_chunk = self._info.get("UserComment")

        for parser_class in self.PARSER_CLASSES_PNG:
            if self._parser:
                break
            kwargs_for_parser = {"info": self._info.copy()}  # Base kwargs

            # Provide 'raw' preferentially if a specific chunk is the known primary source
            if (parser_class is A1111 and png_params_chunk) or (
                parser_class is SwarmUI and png_params_chunk and "sui_image_params" in png_params_chunk
            ):
                kwargs_for_parser["raw"] = png_params_chunk
            elif parser_class is MochiDiffusionFormat:
                # Mochi uses IPTC, less likely for PNGs. If it did use a PNG chunk for its string,
                # its parser would need to look in `info`. For now, it mainly expects IPTC.
                # If Mochi wrote its string to PNG:Comment:
                if png_comment_chunk:
                    kwargs_for_parser["raw"] = png_comment_chunk

            if self._try_parser(parser_class, **kwargs_for_parser):
                continue

        if not self._parser and png_comment_chunk:
            try:
                comment_data = json.loads(png_comment_chunk)
                if isinstance(comment_data, dict) and "prompt" in comment_data:
                    if self._try_parser(Fooocus, info=comment_data):
                        return
            except json.JSONDecodeError:
                self._logger.debug("PNG Comment not valid JSON or not Fooocus.")

        if not self._parser and png_xmp_chunk:
            self._parse_drawthings_xmp(png_xmp_chunk)
            if self._parser:
                return

        if not self._parser and image_obj.mode == "RGBA":
            self._parse_novelai_lsb(image_obj)

    def _parse_drawthings_xmp(self, xmp_chunk: str) -> None:
        # ... (as before) ...
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
                    if self._try_parser(DrawThings, raw=data_str.strip()):
                        return
        except (minidom.ExpatError, json.JSONDecodeError) as e:
            self._logger.warning("DrawThings PNG XMP: Parse error: %s", e)
        except Exception as e:
            self._logger.warning("DrawThings PNG XMP: Unexpected error: %s", e, exc_info=True)

    def _parse_novelai_lsb(self, image_obj: Image.Image) -> None:
        # ... (as before) ...
        if self._parser:
            return
        try:
            extractor = NovelAI.LSBExtractor(image_obj)
            if not extractor.lsb_bytes_list:
                self._logger.debug("NovelAI LSB: Extractor found no data.")
                return
            magic_bytes = extractor.get_next_n_bytes(len(self.NOVELAI_MAGIC))
            if magic_bytes and magic_bytes.decode("utf-8", "ignore") == self.NOVELAI_MAGIC:
                if self._try_parser(NovelAI, extractor=extractor):
                    return
            else:
                self._logger.debug("NovelAI LSB: Magic bytes not found.")
        except Exception as e:
            self._logger.warning("NovelAI LSB check encountered an error: %s", e, exc_info=True)

    def _process_jpeg_webp_exif(self, image_obj: Image.Image) -> None:
        if self._parser:
            return

        raw_user_comment_str: str | None = None
        # self._exif_software_tag and self._parsed_iptc_info are populated by _process_image_file

        # Try to get UserComment from piexif if EXIF data exists
        if exif_bytes := self._info.get("exif"):  # This is raw EXIF bytes from PIL.info
            try:
                # piexif.load is done in _process_image_file to get self._parsed_iptc_info
                # and self._exif_software_tag. We need UserComment from that loaded dict.
                # For now, assume piexif.load was successful if _parsed_iptc_info has something or exif_bytes exists.
                # A better way would be to store the loaded piexif_dict itself.
                # Let's reload here for simplicity, or assume it's already available via a helper.
                temp_exif_dict = piexif.load(exif_bytes)
                user_comment_bytes = temp_exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment)
                if user_comment_bytes:
                    raw_user_comment_str = piexif.helper.UserComment.load(user_comment_bytes)
            except Exception:  # piexif.InvalidImageDataError or others
                self._logger.debug("Could not load UserComment via piexif from EXIF.")

        jfif_comment_bytes = self._info.get("comment", b"")
        jfif_comment_str = jfif_comment_bytes.decode("utf-8", "ignore") if isinstance(jfif_comment_bytes, bytes) else ""

        # --- Attempt RuinedFooocus (very specific UserComment JSON) ---
        if raw_user_comment_str and raw_user_comment_str.strip().startswith("{"):
            try:
                uc_json = json.loads(raw_user_comment_str)
                if isinstance(uc_json, dict) and uc_json.get("software") == "RuinedFooocus":
                    if self._try_parser(RuinedFooocusFormat, raw=raw_user_comment_str):
                        return
            except json.JSONDecodeError:
                pass

        # --- Iterate through ordered JPEG/WEBP parsers ---
        for parser_class in self.PARSER_CLASSES_JPEG_WEBP:
            if self._parser:
                break

            kwargs_for_parser = {}
            # MochiDiffusionFormat expects IPTC Caption-Abstract as raw, and other IPTC in info
            if parser_class is DrawThings:
                if xmp_chunk := self._info.get("XML:com.adobe.xmp"):
                    try:
                        xmp_dom = minidom.parseString(xmp_chunk)
                        description_nodes = xmp_dom.getElementsByTagName("rdf:Description")
                        for desc_node in description_nodes:
                            uc_nodes = desc_node.getElementsByTagName("exif:UserComment")
                            if uc_nodes and uc_nodes[0].childNodes:
                                data_str = uc_nodes[0].childNodes[0].data
                                if data_str:
                                    kwargs_for_parser["info"] = json.loads(data_str)
                                    break
                    except (minidom.ExpatError, json.JSONDecodeError) as e:
                        self._logger.warning("DrawThings XMP: Parse error: %s", e)
                        continue
                else:
                    continue
            elif parser_class is MochiDiffusionFormat:
                iptc_caption = self._parsed_iptc_info.get("iptc_caption_abstract", "")
                if iptc_caption:  # Only try Mochi if we actually found its main data source
                    kwargs_for_parser["raw"] = iptc_caption
                    # info kwarg with other IPTC fields is added by _try_parser if self._parsed_iptc_info is populated
                else:  # No caption, Mochi parser won't work with raw=None
                    continue  # Skip trying Mochi if no IPTC caption
            elif parser_class is EasyDiffusion:
                if raw_user_comment_str:
                    try:
                        kwargs_for_parser["info"] = json.loads(raw_user_comment_str)
                    except json.JSONDecodeError:
                        continue
                else:
                    continue

            if self._try_parser(parser_class, **kwargs_for_parser):
                return  # Successfully parsed

        # ---- Attempt parsing based on JFIF Comment if no success yet ----
        if not self._parser and jfif_comment_str:
            try:
                jfif_json_data = json.loads(jfif_comment_str)
                if isinstance(jfif_json_data, dict) and "prompt" in jfif_json_data:
                    if self._try_parser(Fooocus, info=jfif_json_data):
                        return
            except json.JSONDecodeError:
                self._logger.debug("JFIF Comment not valid JSON or not Fooocus.")

        if not self._parser and image_obj.mode == "RGBA":
            self._parse_novelai_lsb(image_obj)

    def _process_image_file(self, file_path_or_obj: str | Path | BinaryIO, file_display_name: str) -> None:
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

                # --- Extract common EXIF/IPTC fields early ---
                if exif_bytes := self._info.get("exif"):
                    try:
                        exif_data_dict = piexif.load(exif_bytes)
                        # Software Tag
                        sw_bytes = exif_data_dict.get("0th", {}).get(piexif.ImageIFD.Software)
                        if sw_bytes and isinstance(sw_bytes, bytes):
                            self._exif_software_tag = sw_bytes.decode("ascii", "ignore").strip("\x00").strip()
                            self._logger.debug("Found EXIF:Software tag: %s", self._exif_software_tag)

                        # IPTC Data for MochiDiffusion and potentially others
                        iptc_dict_from_exif = exif_data_dict.get("IPTC", {})
                        if iptc_dict_from_exif:
                            self._logger.debug("Found IPTC block in EXIF via piexif.")
                            caption_b = iptc_dict_from_exif.get(IPTC_CAPTION_ABSTRACT)
                            if caption_b:
                                try:
                                    self._parsed_iptc_info["iptc_caption_abstract"] = caption_b.decode(
                                        "utf-8", "replace"
                                    )
                                except AttributeError:
                                    self._parsed_iptc_info["iptc_caption_abstract"] = str(caption_b)

                            program_b = iptc_dict_from_exif.get(IPTC_ORIGINATING_PROGRAM)
                            if program_b:
                                try:
                                    self._parsed_iptc_info["iptc_originating_program"] = program_b.decode(
                                        "utf-8", "replace"
                                    )
                                except AttributeError:
                                    self._parsed_iptc_info["iptc_originating_program"] = str(program_b)

                            version_b = iptc_dict_from_exif.get(IPTC_PROGRAM_VERSION)
                            if version_b:
                                try:
                                    self._parsed_iptc_info["iptc_program_version"] = version_b.decode(
                                        "utf-8", "replace"
                                    )
                                except AttributeError:
                                    self._parsed_iptc_info["iptc_program_version"] = str(version_b)

                            if self._parsed_iptc_info:
                                self._logger.debug("Parsed IPTC fields: %s", self._parsed_iptc_info)

                    except Exception as e_exif_load:
                        self._logger.debug(
                            "Could not parse EXIF for Software/IPTC tags: %s",
                            e_exif_load,
                        )

                # Alternative IPTC extraction using Pillow's getiptcinfo() if IPTCIM is installed
                # This often gives more straightforward string keys.
                if not self._parsed_iptc_info and hasattr(img, "getiptcinfo"):
                    try:
                        pil_iptc_info = img.getiptcinfo()  # Needs IPTCIM package
                        if pil_iptc_info:
                            self._logger.debug("Found IPTC via Pillow getiptcinfo().")
                            # Keys in pil_iptc_info are usually like ('caption/abstract', 'originating program', etc.)
                            # We need to map these to our consistent keys
                            # (2,120) -> 'caption/abstract'
                            # (2,65)  -> 'originating program' (Mochi's definition)
                            # (2,70)  -> 'program version'
                            # The exact keys from getiptcinfo() might vary based on IPTCIM version.
                            # This part requires checking what getiptcinfo() actually returns.
                            # For example:
                            if val := pil_iptc_info.get((2, 120)):
                                self._parsed_iptc_info["iptc_caption_abstract"] = str(val)
                            if val := pil_iptc_info.get((2, 65)):
                                self._parsed_iptc_info["iptc_originating_program"] = str(val)
                            if val := pil_iptc_info.get((2, 70)):
                                self._parsed_iptc_info["iptc_program_version"] = str(val)
                            if self._parsed_iptc_info:
                                self._logger.debug(
                                    "Parsed IPTC fields from Pillow: %s",
                                    self._parsed_iptc_info,
                                )
                    except Exception as e_pil_iptc:
                        self._logger.debug(
                            "Pillow getiptcinfo() failed or IPTCIM not available: %s",
                            e_pil_iptc,
                        )

                self._attempt_legacy_swarm_exif(img)

                if not self._parser:
                    if self._format_str == "PNG":
                        self._process_png_chunks(img)
                    elif self._format_str in ["JPEG", "WEBP"]:
                        self._process_jpeg_webp_exif(img)
                    else:  # Generic fallback for other image types
                        self._logger.info(
                            "Image format '%s' not specifically handled. Checking generic EXIF UserComment.",
                            self._format_str,
                        )
                        if not self._parser and (
                            exif_b := self._info.get("exif")
                        ):  # Re-check if not parsed by IPTC path
                            try:
                                exif_d = piexif.load(exif_b)
                                uc_b = exif_d.get("Exif", {}).get(piexif.ExifIFD.UserComment)
                                if uc_b:
                                    uc_s = piexif.helper.UserComment.load(uc_b)
                                    if uc_s and not uc_s.strip().startswith("{"):  # A1111 is text
                                        if self._try_parser(A1111, raw=uc_s):
                                            pass
                            except Exception as e_gen_exif:
                                self._logger.debug(
                                    "Generic EXIF UserComment (A1111 fallback) check failed: %s",
                                    e_gen_exif,
                                )
        # ... (Exception handling as before) ...
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
        # ... (as before) ...
        self._initialize_state()
        file_display_name = self._get_display_name(file_path_or_obj)
        self._logger.debug("Reading data for: %s (is_txt: %s)", file_display_name, self._is_txt)
        if self._is_txt:
            if hasattr(file_path_or_obj, "read") and callable(file_path_or_obj.read):
                self._handle_text_file(file_path_or_obj)
            else:
                try:
                    with open(file_path_or_obj, encoding="utf-8") as f_obj:
                        self._handle_text_file(f_obj)
                except Exception as e_open:
                    self._logger.error("Error opening text file '%s': %s", file_display_name, e_open)
                    self._status = BaseFormat.Status.FORMAT_ERROR
                    self._error = f"Could not open text file: {e_open!s}"
        else:
            self._process_image_file(file_path_or_obj, file_display_name)
        if self._status == BaseFormat.Status.UNREAD:
            self._logger.warning(
                "No suitable parser for '%s' or all parsers failed/declined.",
                file_display_name,
            )
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
            self._logger.warning("Error details for '%s': %s", file_display_name, final_error_to_log)

    # ... (remove_data, save_image, construct_data, prompt_to_line, and all properties remain the same) ...
    # --- Properties ---
    @property
    def height(self) -> str:
        parser_h_str = str(getattr(self._parser, "height", "0"))
        if parser_h_str.isdigit() and int(parser_h_str) > 0:
            return parser_h_str
        return str(self._height) if self._height > 0 else "0"

    @property
    def width(self) -> str:
        parser_w_str = str(getattr(self._parser, "width", "0"))
        if parser_w_str.isdigit() and int(parser_w_str) > 0:
            return parser_w_str
        return str(self._width) if self._width > 0 else "0"

    @property
    def info(self) -> dict[str, Any]:
        return self._info.copy()

    @property
    def positive(self) -> str:
        return str(
            getattr(
                self._parser,
                "positive",
                (self._positive_sdxl.get("positive", "") if self._positive_sdxl else self._positive),
            )
        )

    @property
    def negative(self) -> str:
        return str(
            getattr(
                self._parser,
                "negative",
                (self._negative_sdxl.get("negative", "") if self._negative_sdxl else self._negative),
            )
        )

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
        return str(parser_raw if parser_raw is not None else self._raw)

    @property
    def tool(self) -> str:
        parser_tool = getattr(self._parser, "tool", None)
        return str(parser_tool if parser_tool and parser_tool != "Unknown" else self._tool)

    @property
    def parameter(self) -> dict[str, Any]:
        parser_param = getattr(self._parser, "parameter", None)
        return parser_param.copy() if parser_param is not None else (self._parameter.copy() if self._parameter else {})

    @property
    def format(self) -> str:
        return self._format_str

    @property
    def is_sdxl(self) -> bool:
        return getattr(self._parser, "is_sdxl", self._is_sdxl)

    @property
    def props(self) -> str:
        if self._parser and hasattr(self._parser, "props"):
            try:
                return self._parser.props
            except Exception as prop_err:
                self._logger.warning("Error calling parser's props: %s", prop_err)
        fb_props = {
            "positive": self.positive,
            "negative": self.negative,
            "width": self.width,
            "height": self.height,
            "tool": self.tool,
            "setting": self.setting,
            "is_sdxl": self.is_sdxl,
            "status": (self.status.name if hasattr(self.status, "name") else str(self.status)),
            "error": self.error,
            "format": self.format,
        }
        if self.positive_sdxl:
            fb_props["positive_sdxl"] = self.positive_sdxl
        if self.negative_sdxl:
            fb_props["negative_sdxl"] = self.negative_sdxl
        fb_props.update(self.parameter)
        try:
            return json.dumps(fb_props, indent=2)
        except TypeError as json_type_err:
            self._logger.error("Error serializing props to JSON: %s. Data: %s", json_type_err, fb_props)
            return f'{{"error": "Failed to serialize props to JSON: {json_type_err!s}"}}'

    @property
    def status(self) -> BaseFormat.Status:
        return self._status

    @property
    def error(self) -> str:
        parser_error = getattr(self._parser, "error", None)
        if self._status != BaseFormat.Status.READ_SUCCESS and self._error:
            return self._error
        if parser_error:
            return str(parser_error)
        return str(self._error)
