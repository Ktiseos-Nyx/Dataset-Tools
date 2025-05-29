# dataset_tools/vendored_sdpr/image_data_reader.py
# This is YOUR VENDORED and MODIFIED copy - FUSED VERSION (Corrected _try_parser, status logic, AND defusedxml)

__author__ = "receyuki"
__filename__ = "image_data_reader.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json

# from xml.dom import minidom # Standard library, replaced by defusedxml
import defusedxml.minidom as minidom  # <<< --- USE DEFUSEDXML for safer XML parsing ---
from pathlib import Path  # For getting filename in logs

import piexif  # For JPEG/WEBP EXIF
import piexif.helper
from PIL import Image  # For image opening and manipulation
from PIL.PngImagePlugin import PngInfo  # For writing PNG metadata

from .logger import Logger  # Your vendored logger
from .constants import PARAMETER_PLACEHOLDER  # Your vendored constants
from .format import (  # Your vendored format parsers
    BaseFormat,
    A1111,
    EasyDiffusion,
    InvokeAI,
    NovelAI,
    ComfyUI,
    DrawThings,
    SwarmUI,
    Fooocus,
    CivitaiComfyUIFormat,  # Your custom parser
    RuinedFooocusFormat,  # Your custom parser
)


class ImageDataReader:
    NOVELAI_MAGIC = "stealth_pngcomp"  # Used for NovelAI LSB PNGs

    def __init__(self, file, is_txt: bool = False):
        self._height: int = 0
        self._width: int = 0
        self._info: dict = {}
        self._positive: str = ""
        self._negative: str = ""
        self._positive_sdxl: dict = {}
        self._negative_sdxl: dict = {}
        self._setting: str = ""
        self._raw: str = ""
        self._tool: str = ""
        self._parameter_key: list[str] = getattr(
            BaseFormat, "PARAMETER_KEY", ["model", "sampler", "seed", "cfg", "steps", "size"]
        )
        self._parameter: dict = dict.fromkeys(self._parameter_key, PARAMETER_PLACEHOLDER)
        self._is_txt: bool = is_txt
        self._is_sdxl: bool = False
        self._format_str: str = ""
        self._props: str = ""
        self._parser: BaseFormat | None = None
        self._status: BaseFormat.Status = BaseFormat.Status.UNREAD
        self._error: str = ""
        self._logger = Logger("DSVendored_SDPR.ImageDataReader")
        self.read_data(file)

    def _try_parser(self, parser_class, **kwargs) -> bool:
        """
        Helper to instantiate a given parser_class, call its parse() method,
        and if successful, update ImageDataReader's _parser, _tool, and _status.
        Returns True if the parser reported READ_SUCCESS, False otherwise.
        """
        self._logger.debug(f"Attempting parser: {parser_class.__name__} with kwargs: {list(kwargs.keys())}")
        try:
            if "width" in kwargs:
                kwargs["width"] = int(self._width)
            if "height" in kwargs:
                kwargs["height"] = int(self._height)

            temp_parser = parser_class(**kwargs)
            parser_own_status = temp_parser.parse()

            if parser_own_status == BaseFormat.Status.READ_SUCCESS:
                self._parser = temp_parser
                self._tool = getattr(self._parser, "tool", parser_class.__name__)
                self._status = BaseFormat.Status.READ_SUCCESS  # CRITICAL UPDATE
                self._error = ""  # CRITICAL UPDATE
                self._logger.info(f"Successfully parsed as {self._tool}.")
                return True
            else:
                parser_error_msg = getattr(temp_parser, "error", "N/A")
                self._logger.debug(
                    f"{parser_class.__name__} parsing attempt resulted in status: {parser_own_status.name if hasattr(parser_own_status, 'name') else parser_own_status}. Error: {parser_error_msg}"
                )
                if parser_error_msg and (self._status == BaseFormat.Status.UNREAD or not self._error):
                    self._error = parser_error_msg
                return False
        except TypeError as te:
            self._logger.error(
                f"TypeError instantiating or calling {parser_class.__name__}: {te}. Check __init__/parse signature."
            )
            if self._status == BaseFormat.Status.UNREAD:
                self._error = f"Init/call error for {parser_class.__name__}: {te}"
            return False
        except Exception as e:
            self._logger.error(f"Unexpected exception during {parser_class.__name__} attempt: {e}", exc_info=False)
            if self._status == BaseFormat.Status.UNREAD:
                self._error = f"Runtime error in {parser_class.__name__}: {e}"
            return False

    def read_data(self, file_path_or_obj):
        self._status = BaseFormat.Status.UNREAD
        self._error = ""
        self._parser = None
        self._tool = ""

        if self._is_txt:
            if hasattr(file_path_or_obj, "read"):
                self._raw = file_path_or_obj.read()
            else:
                self._logger.error("Text file processing expected a file object.")
                self._status = BaseFormat.Status.FORMAT_ERROR
                self._error = "Invalid file object for text file."
                self._logger.info(
                    f"Text file processed. Final Status: {self._status.name}, Tool: {self._tool or 'None'}"
                )
                return  # Added log and return

            if self._try_parser(A1111, raw=self._raw):
                pass
            else:
                if self._status == BaseFormat.Status.UNREAD:
                    self._status = BaseFormat.Status.FORMAT_ERROR
                if not self._error:
                    self._error = "Failed to parse text file as A1111 format."
            self._logger.info(
                f"Text file processed. Final Status: {self._status.name if hasattr(self._status, 'name') else self._status}, Tool: {self._tool or 'None'}"
            )
            return

        try:
            with Image.open(file_path_or_obj) as f_img:
                self._width = f_img.width
                self._height = f_img.height
                self._info = f_img.info
                self._format_str = f_img.format

                # --- Try Parsers in Order of Precedence ---
                # 1. SwarmUI Legacy EXIF
                if not self._parser:
                    try:
                        exif_pil = f_img.getexif()
                        if exif_pil:
                            exif_json_str = exif_pil.get(0x0110)
                            if exif_json_str:
                                exif_dict = json.loads(exif_json_str)
                                if "sui_image_params" in exif_dict:
                                    self._try_parser(SwarmUI, info=exif_dict)  # VERIFY SwarmUI.__init__(info) args
                    except Exception as e_swarm_exif:
                        self._logger.debug(f"SwarmUI legacy EXIF check failed: {e_swarm_exif}")

                # 2. PNG Processing Logic
                if not self._parser and self._format_str == "PNG":
                    png_params = self._info.get("parameters")
                    png_prompt = self._info.get("prompt")
                    # png_workflow = self._info.get("workflow") # F841: Not directly used here, ComfyUI parser gets full info
                    png_postproc = self._info.get("postprocessing")
                    png_neg_prompt_ed = self._info.get("negative_prompt") or self._info.get("Negative Prompt")
                    png_invoke_meta = (
                        self._info.get("invokeai_metadata") or self._info.get("sd-metadata") or self._info.get("Dream")
                    )
                    png_software_tag = self._info.get("Software")
                    png_comment_chunk = self._info.get("Comment")
                    png_xmp_chunk = self._info.get("XML:com.adobe.xmp")

                    if png_params and not self._parser:
                        if "sui_image_params" in png_params:
                            self._try_parser(SwarmUI, raw=png_params)  # VERIFY SwarmUI.__init__(raw)
                        elif not self._parser:
                            if self._try_parser(A1111, info=self._info):  # A1111.__init__(info)
                                if png_prompt and self._tool == "A1111 webUI":
                                    self._tool = "ComfyUI (A1111 compatible)"

                    if png_postproc and not self._parser:
                        self._try_parser(A1111, info=self._info)

                    if png_neg_prompt_ed and not self._parser:
                        self._try_parser(EasyDiffusion, info=self._info)  # VERIFY ED.__init__

                    if png_invoke_meta and not self._parser:
                        self._try_parser(InvokeAI, info=self._info)  # VERIFY InvokeAI.__init__

                    if png_software_tag == "NovelAI" and not self._parser:
                        self._try_parser(
                            NovelAI, info=self._info, width=self._width, height=self._height
                        )  # VERIFY NovelAI.__init__

                    if png_prompt and not self._parser:
                        self._try_parser(
                            ComfyUI, info=self._info, width=self._width, height=self._height
                        )  # VERIFY ComfyUI.__init__

                    if png_comment_chunk and not self._parser:
                        try:
                            self._try_parser(Fooocus, info=json.loads(png_comment_chunk))  # VERIFY Fooocus.__init__
                        except json.JSONDecodeError:
                            self._logger.warn("Fooocus PNG Comment: Not valid JSON.")

                    if png_xmp_chunk and not self._parser:  # DrawThings
                        try:
                            # Using defusedxml's minidom for safer XML parsing
                            xmp_dom = minidom.parseString(png_xmp_chunk)
                            uc_node = xmp_dom.getElementsByTagName("exif:UserComment")
                            if (
                                uc_node
                                and uc_node[0].childNodes
                                and len(uc_node[0].childNodes) > 1
                                and uc_node[0].childNodes[1].childNodes
                                and len(uc_node[0].childNodes[1].childNodes) > 1
                                and uc_node[0].childNodes[1].childNodes[1].childNodes
                            ):
                                json_str = uc_node[0].childNodes[1].childNodes[1].childNodes[0].data
                                self._try_parser(DrawThings, info=json.loads(json_str))  # VERIFY DrawThings.__init__
                        except minidom.ExpatError as e_xml:  # Catch specific XML parsing errors
                            self._logger.warn(f"DrawThings PNG XMP: XML parsing error: {e_xml}")
                        except json.JSONDecodeError:  # If content of UserComment isn't JSON
                            self._logger.warn("DrawThings PNG XMP: UserComment content not valid JSON.")
                        except Exception as e_dt_xmp:  # Broader catch for other issues
                            self._logger.warn(f"DrawThings PNG XMP: Error processing XMP: {e_dt_xmp}")

                    if f_img.mode == "RGBA" and not self._parser:  # NovelAI LSB
                        try:
                            reader = NovelAI.LSBExtractor(f_img)
                            magic = reader.get_next_n_bytes(len(self.NOVELAI_MAGIC))
                            if magic and magic.decode("utf-8", errors="ignore") == self.NOVELAI_MAGIC:
                                self._try_parser(NovelAI, extractor=reader)  # VERIFY NovelAI.__init__(extractor=)
                        except Exception as e_lsb:
                            self._logger.warn(f"NovelAI LSB (PNG) check error: {e_lsb}")

                # 3. JPEG/WEBP Processing Logic
                elif not self._parser and self._format_str in ["JPEG", "WEBP"]:
                    raw_uc = None
                    sw_tag = ""
                    jfif_comment = self._info.get("comment", b"").decode("utf-8", "ignore")
                    if self._info.get("exif"):
                        try:
                            exif_d = piexif.load(self._info["exif"])
                            uc_b = exif_d.get("Exif", {}).get(piexif.ExifIFD.UserComment)
                            if uc_b:
                                raw_uc = piexif.helper.UserComment.load(uc_b)
                            sw_b = exif_d.get("0th", {}).get(piexif.ImageIFD.Software)
                            if sw_b:
                                sw_tag = sw_b.decode("ascii", "ignore").strip()
                        except Exception as e_exif:
                            self._logger.warn(f"piexif load error for EXIF: {e_exif}")

                    # 3.1. YOUR CUSTOM PARSERS (UserComment)
                    if raw_uc and not self._parser:
                        if raw_uc.strip().startswith("{"):
                            try:
                                uc_j = json.loads(raw_uc)
                                if isinstance(uc_j, dict) and uc_j.get("software") == "RuinedFooocus":
                                    self._try_parser(
                                        RuinedFooocusFormat, raw=raw_uc, width=self._width, height=self._height
                                    )  # VERIFY RF.__init__
                            except json.JSONDecodeError:
                                pass

                        if not self._parser:
                            is_civ = False
                            if sw_tag == "4c6047c3-8b1c-4058-8888-fd48353bf47d":
                                is_civ = True
                            elif raw_uc and "charset=Unicode" in raw_uc:
                                td = raw_uc.split("charset=Unicode", 1)[-1].strip()
                                if (
                                    td.startswith("笀∀爀攀猀漀甀爀挀攀") or td.startswith('{"resource-stack":')
                                ) and '"extraMetadata":' in td:
                                    is_civ = True
                            elif raw_uc and raw_uc.startswith('{"resource-stack":') and '"extraMetadata":' in raw_uc:
                                is_civ = True
                            if is_civ:
                                self._try_parser(
                                    CivitaiComfyUIFormat, raw=raw_uc, width=self._width, height=self._height
                                )  # VERIFY CCF.__init__

                    # 3.2. Fooocus (JFIF Comment)
                    if not self._parser and jfif_comment:
                        try:
                            jfif_j = json.loads(jfif_comment)
                            if isinstance(jfif_j, dict) and "prompt" in jfif_j:
                                self._try_parser(Fooocus, info=jfif_j)  # VERIFY Fooocus.__init__(info)
                        except json.JSONDecodeError:
                            pass

                    # 3.3. Standard UserComment Fallbacks
                    if not self._parser and raw_uc:
                        self._raw = raw_uc
                        if "sui_image_params" in raw_uc:
                            self._try_parser(SwarmUI, raw=self._raw)  # VERIFY SwarmUI.__init__(raw)
                        elif raw_uc.strip().startswith("{") and not self._parser:
                            self._try_parser(EasyDiffusion, raw=self._raw)  # VERIFY ED.__init__(raw)
                        elif not self._parser:
                            self._try_parser(A1111, raw=self._raw)  # A1111.__init__(raw)

                    # 3.4. NovelAI LSB (RGBA JPEG/WEBP)
                    if not self._parser and f_img.mode == "RGBA":
                        try:
                            reader = NovelAI.LSBExtractor(f_img)
                            magic = reader.get_next_n_bytes(len(self.NOVELAI_MAGIC))
                            if magic and magic.decode("utf-8", errors="ignore") == self.NOVELAI_MAGIC:
                                self._try_parser(NovelAI, extractor=reader)  # VERIFY NovelAI.__init__(extractor=)
                        except Exception as e_lsb_j:
                            self._logger.warn(f"NovelAI LSB (JPEG/WEBP) check error: {e_lsb_j}")

        except FileNotFoundError:
            self._logger.error(f"Image file not found: {file_path_or_obj}")
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = "Image file not found."
        except Exception as e_outer_open:
            self._logger.error(
                f"Error opening or processing image '{Path(str(file_path_or_obj)).name}': {e_outer_open}",
                exc_info=False,
            )
            self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error:
                self._error = f"Pillow/general error: {e_outer_open}"

        # --- Final Status Check ---
        if self._status == BaseFormat.Status.UNREAD:
            self._logger.warn(
                f"No suitable parser found or no parser claimed success for '{Path(str(file_path_or_obj)).name}'."
            )
            self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error:
                self._error = "No suitable parser found or parsing failed."

        log_tool_name = self._tool if self._tool else "None"
        log_status_name = self._status.name if hasattr(self._status, "name") else str(self._status)
        self._logger.info(
            f"Final Reading Status for '{Path(str(file_path_or_obj)).name}': {log_status_name}, Tool: {log_tool_name}"
        )

        final_error_to_log = self._error
        if self._parser and getattr(self._parser, "error", None):
            if self._status != BaseFormat.Status.READ_SUCCESS or not final_error_to_log:
                final_error_to_log = self._parser.error

        if self._status != BaseFormat.Status.READ_SUCCESS and final_error_to_log:
            self._logger.warn(f"Error details: {final_error_to_log}")
        elif self._status != BaseFormat.Status.READ_SUCCESS:
            self._logger.warn(f"Parsing failed with status {log_status_name} (no specific error message captured).")

    @staticmethod
    def remove_data(image_file):
        with Image.open(image_file) as f:
            image_data = list(f.getdata())
            image_without_exif = Image.new(f.mode, f.size)
            image_without_exif.putdata(image_data)
            return image_without_exif

    @staticmethod
    def save_image(image_path, new_path, image_format, data=None):
        metadata_to_embed = None
        if data:
            image_format_upper = image_format.upper()
            if image_format_upper == "PNG":
                metadata_to_embed = PngInfo()
                metadata_to_embed.add_text("parameters", data)
            elif image_format_upper in ["JPEG", "JPG", "WEBP"]:
                try:
                    user_comment_bytes = piexif.helper.UserComment.dump(data, encoding="unicode")
                    metadata_to_embed = piexif.dump({"Exif": {piexif.ExifIFD.UserComment: user_comment_bytes}})
                except Exception as e_dump:
                    Logger("DSVendored_SDPR.ImageDataReader").error(f"piexif dump error: {e_dump}")
                    metadata_to_embed = None
        with Image.open(image_path) as img_to_save:
            try:
                image_format_upper = image_format.upper()
                if image_format_upper == "PNG":
                    if metadata_to_embed:
                        img_to_save.save(new_path, pnginfo=metadata_to_embed)
                    else:
                        img_to_save.save(new_path)
                elif image_format_upper in ["JPEG", "JPG"]:
                    img_to_save.save(new_path, quality=95, exif=img_to_save.info.get("exif"))
                    if metadata_to_embed:
                        try:
                            piexif.insert(metadata_to_embed, str(new_path))
                        except Exception as e_ins_jpg:
                            Logger("DSVendored_SDPR.ImageDataReader").error(f"piexif insert (JPG) error: {e_ins_jpg}")
                elif image_format_upper == "WEBP":
                    img_to_save.save(new_path, quality=100, lossless=True)
                    if metadata_to_embed:
                        try:
                            piexif.insert(metadata_to_embed, str(new_path))
                        except Exception as e_ins_webp:
                            Logger("DSVendored_SDPR.ImageDataReader").error(f"piexif insert (WEBP) error: {e_ins_webp}")
            except Exception as e_save:
                Logger("DSVendored_SDPR.ImageDataReader").error(f"Image save error for {new_path}: {e_save}")

    @staticmethod
    def construct_data(positive, negative, setting):
        return "\n".join(
            filter(
                None,
                [
                    f"{positive}" if positive else "",
                    f"Negative prompt: {negative}" if negative else "",
                    f"{setting}" if setting else "",
                ],
            )
        )

    def prompt_to_line(self):
        if self._parser and hasattr(self._parser, "prompt_to_line"):
            return self._parser.prompt_to_line()
        return ""

    @property
    def height(self) -> str:
        parser_h = getattr(self._parser, "height", None)
        return str(parser_h) if parser_h is not None and str(parser_h) != "0" else str(self._height)

    @property
    def width(self) -> str:
        parser_w = getattr(self._parser, "width", None)
        return str(parser_w) if parser_w is not None and str(parser_w) != "0" else str(self._width)

    @property
    def info(self) -> dict:
        return self._info

    @property
    def positive(self) -> str:
        return str(getattr(self._parser, "positive", self._positive))

    @property
    def negative(self) -> str:
        return str(getattr(self._parser, "negative", self._negative))

    @property
    def positive_sdxl(self) -> dict:
        return getattr(self._parser, "positive_sdxl", self._positive_sdxl or {})

    @property
    def negative_sdxl(self) -> dict:
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
        return str(parser_tool) if parser_tool and parser_tool != "Unknown" else str(self._tool)

    @property
    def parameter(self) -> dict:
        return getattr(self._parser, "parameter", self._parameter or {})

    @property
    def format(self) -> str:
        return self._format_str

    @property
    def is_sdxl(self) -> bool:
        return getattr(self._parser, "is_sdxl", self._is_sdxl)

    @property
    def props(self) -> str:
        return getattr(self._parser, "props", self._props)

    @property
    def status(self) -> BaseFormat.Status:
        return self._status

    @property
    def error(self) -> str:
        parser_err = getattr(self._parser, "error", None)
        return str(parser_err if parser_err else self._error)
