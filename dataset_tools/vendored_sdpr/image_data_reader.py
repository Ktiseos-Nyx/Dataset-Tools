# dataset_tools/vendored_sdpr/image_data_reader.py
# This is YOUR VENDORED and MODIFIED copy - FUSED VERSION (Corrected _try_parser and status logic)

__author__ = "receyuki"
__filename__ = "image_data_reader.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
from xml.dom import minidom # For DrawThings
from pathlib import Path    # For getting filename in logs

import piexif               # For JPEG/WEBP EXIF
import piexif.helper
from PIL import Image       # For image opening and manipulation
from PIL.PngImagePlugin import PngInfo # For writing PNG metadata

from .logger import Logger # Your vendored logger
from .constants import PARAMETER_PLACEHOLDER # Your vendored constants
from .format import ( # Your vendored format parsers
    BaseFormat, A1111, EasyDiffusion, InvokeAI, NovelAI, ComfyUI,
    DrawThings, SwarmUI, Fooocus,
    CivitaiComfyUIFormat, # Your custom parser
    RuinedFooocusFormat,  # Your custom parser
)

class ImageDataReader:
    NOVELAI_MAGIC = "stealth_pngcomp" # Used for NovelAI LSB PNGs

    def __init__(self, file, is_txt: bool = False):
        self._height: int = 0 # Initialize (will be updated by PIL or parser)
        self._width: int = 0  # Initialize
        self._info: dict = {}  # PIL Image.info dictionary
        self._positive: str = ""
        self._negative: str = ""
        self._positive_sdxl: dict = {} # For SDXL specific positive prompts
        self._negative_sdxl: dict = {} # For SDXL specific negative prompts
        self._setting: str = ""       # Raw settings string (e.g., "Steps: 20, Sampler: Euler a, ...")
        self._raw: str = ""           # Full raw metadata string if applicable
        self._tool: str = ""          # Detected AI tool/software name
        
        # Use BaseFormat's PARAMETER_KEY if accessible, otherwise define a default
        self._parameter_key: list[str] = getattr(BaseFormat, 'PARAMETER_KEY', 
                                      ["model", "sampler", "seed", "cfg", "steps", "size"]) # Default fallback
        self._parameter: dict = dict.fromkeys(self._parameter_key, PARAMETER_PLACEHOLDER)
        
        self._is_txt: bool = is_txt    # Flag if the input 'file' is a text file
        self._is_sdxl: bool = False    # Flag if SDXL specific parameters are detected
        self._format_str: str = ""    # Image format from PIL (e.g., "PNG", "JPEG")
        self._props: str = ""         # Potentially for other properties if parsers populate it
        self._parser: BaseFormat | None = None # Holds the instantiated format parser object (type hinted)
        self._status: BaseFormat.Status = BaseFormat.Status.UNREAD # Initial status
        self._error: str = ""         # To store specific error messages during parsing
        self._logger = Logger("DSVendored_SDPR.ImageDataReader") # Use your distinct logger name
        
        self.read_data(file) # Process the file upon instantiation

    def _try_parser(self, parser_class, **kwargs) -> bool:
        """
        Helper to instantiate a given parser_class, call its parse() method,
        and if successful, update ImageDataReader's _parser, _tool, and _status.
        Returns True if the parser reported READ_SUCCESS, False otherwise.
        """
        self._logger.debug(f"Attempting parser: {parser_class.__name__} with kwargs: {list(kwargs.keys())}")
        try:
            # Ensure width and height are passed as integers if the parser expects them
            # (though BaseFormat converts them to strings internally on init)
            if 'width' in kwargs: kwargs['width'] = int(self._width) # Use current IDR width
            if 'height' in kwargs: kwargs['height'] = int(self._height) # Use current IDR height

            temp_parser = parser_class(**kwargs)
            parser_own_status = temp_parser.parse() # This should set temp_parser.status

            if parser_own_status == BaseFormat.Status.READ_SUCCESS:
                self._parser = temp_parser
                self._tool = getattr(self._parser, 'tool', parser_class.__name__) # Prefer parser's specific tool name
                
                # --- CRITICAL UPDATE: Set ImageDataReader's status upon parser success ---
                self._status = BaseFormat.Status.READ_SUCCESS
                self._error = "" # Clear any previous general error in ImageDataReader
                # --- END CRITICAL UPDATE ---

                self._logger.info(f"Successfully parsed as {self._tool}.")
                return True
            else:
                # Parser ran but did not return READ_SUCCESS
                parser_error_msg = getattr(temp_parser, 'error', 'N/A')
                self._logger.debug(f"{parser_class.__name__} parsing attempt resulted in status: {parser_own_status.name if hasattr(parser_own_status, 'name') else parser_own_status}. Error: {parser_error_msg}")
                # If this specific parser failed and set an error message,
                # and ImageDataReader doesn't have a more general error (like PIL error) yet,
                # or if its status is still UNREAD, we can tentatively store this parser's error.
                # This helps if NO parser succeeds, we might have a more specific error than "no suitable parser".
                if parser_error_msg and (self._status == BaseFormat.Status.UNREAD or not self._error):
                    self._error = parser_error_msg 
                return False
        except TypeError as te: # For errors like passing unexpected kwargs to parser's __init__
            self._logger.error(f"TypeError instantiating or calling {parser_class.__name__}: {te}. Check its __init__/parse signature and arguments passed.")
            if self._status == BaseFormat.Status.UNREAD: self._error = f"Initialization/call error for {parser_class.__name__}: {te}"
            return False
        except Exception as e: # Catch other unexpected errors during this parser's attempt
            self._logger.error(f"Unexpected exception during {parser_class.__name__} attempt: {e}", exc_info=False) # exc_info=True for deep debug
            if self._status == BaseFormat.Status.UNREAD: self._error = f"Runtime error in {parser_class.__name__}: {e}"
            return False

    def read_data(self, file_path_or_obj):
        # Reset main status and error for each new file processing at the start of this method
        self._status = BaseFormat.Status.UNREAD
        self._error = ""
        self._parser = None # Ensure parser is reset
        self._tool = ""     # Ensure tool is reset

        if self._is_txt:
            if hasattr(file_path_or_obj, 'read'):
                self._raw = file_path_or_obj.read()
            else:
                self._logger.error("Text file processing expected a file object.")
                self._status = BaseFormat.Status.FORMAT_ERROR
                self._error = "Invalid file object for text file."
                # Log final status for text file here as we return early
                self._logger.info(f"Text file processed. Final Status: {self._status.name}, Tool: {self._tool or 'None'}")
                return
            
            # For .txt, assume A1111 format. A1111.__init__(raw) doesn't take width/height.
            if self._try_parser(A1111, raw=self._raw):
                pass # _try_parser has set self._status, self._parser, self._tool
            else: # _try_parser returned False (A1111 parsing failed or didn't apply)
                if self._status == BaseFormat.Status.UNREAD: # If _try_parser didn't set a specific error status
                    self._status = BaseFormat.Status.FORMAT_ERROR
                if not self._error: # If _try_parser didn't set a specific error message
                    self._error = "Failed to parse text file as A1111 format."
            # Log final status for text file
            self._logger.info(f"Text file processed. Final Status: {self._status.name if hasattr(self._status, 'name') else self._status}, Tool: {self._tool or 'None'}")
            return

        # --- Image file processing ---
        try:
            with Image.open(file_path_or_obj) as f_img: # Renamed 'f' to 'f_img' for clarity
                self._width = f_img.width
                self._height = f_img.height
                self._info = f_img.info
                self._format_str = f_img.format
                # self._parser, self._tool, self._status, self._error are already reset above

                # --- Try Parsers in Order of Precedence ---

                # 1. SwarmUI Legacy EXIF (ModelID 0x0110)
                if not self._parser: # Only try if no parser has succeeded yet
                    try:
                        exif_pil = f_img.getexif()
                        if exif_pil:
                            exif_json_str = exif_pil.get(0x0110)
                            if exif_json_str:
                                exif_dict = json.loads(exif_json_str)
                                if "sui_image_params" in exif_dict:
                                    # VERIFY: SwarmUI.__init__(info) - Does it take width/height? Original SDPR does not pass.
                                    self._try_parser(SwarmUI, info=exif_dict)
                    except Exception as e_swarm_exif:
                        self._logger.debug(f"SwarmUI legacy EXIF check failed or data not present: {e_swarm_exif}")

                # 2. PNG Processing Logic
                if not self._parser and self._format_str == "PNG":
                    # Extract all relevant PNG info chunks once
                    png_params = self._info.get("parameters")
                    png_prompt = self._info.get("prompt")
                    png_workflow = self._info.get("workflow") # ComfyUI might use this with prompt
                    png_postproc = self._info.get("postprocessing")
                    png_neg_prompt_ed = self._info.get("negative_prompt") or self._info.get("Negative Prompt") # EasyDiffusion
                    png_invoke_meta = self._info.get("invokeai_metadata") or self._info.get("sd-metadata") or self._info.get("Dream")
                    png_software_tag = self._info.get("Software")
                    png_comment_chunk = self._info.get("Comment") # Fooocus uses this
                    png_xmp_chunk = self._info.get("XML:com.adobe.xmp") # DrawThings

                    if png_params and not self._parser:
                        if "sui_image_params" in png_params:
                            self._try_parser(SwarmUI, raw=png_params) # VERIFY: SwarmUI.__init__(raw)
                        elif not self._parser: # A1111 or compatible (e.g., Comfy using A1111 text)
                            if self._try_parser(A1111, info=self._info): # A1111.__init__(info)
                                if png_prompt and self._tool == "A1111 webUI": # Heuristic for Comfy using A1111 format
                                    self._tool = "ComfyUI (A1111 compatible)"
                    
                    if png_postproc and not self._parser: # A1111 postprocessing
                        self._try_parser(A1111, info=self._info) # A1111.__init__(info)

                    if png_neg_prompt_ed and not self._parser: # EasyDiffusion
                        self._try_parser(EasyDiffusion, info=self._info) # VERIFY: ED.__init__(info)

                    if png_invoke_meta and not self._parser: # InvokeAI
                        self._try_parser(InvokeAI, info=self._info) # VERIFY: InvokeAI.__init__(info)
                    
                    if png_software_tag == "NovelAI" and not self._parser: # NovelAI (legacy)
                        # VERIFY: NovelAI.__init__(info, width, height) - Original SDPR *DOES* pass w/h
                        self._try_parser(NovelAI, info=self._info, width=self._width, height=self._height)
                    
                    # Standard ComfyUI uses "prompt" (workflow) and "workflow" (optional extra workflow)
                    if png_prompt and not self._parser: 
                        # This might also catch A1111-compatible Comfy if the above A1111 check failed for some reason
                        # but "prompt" key exists. Ensure distinct conditions if needed.
                        # VERIFY: ComfyUI.__init__(info, width, height) - Original SDPR *DOES* pass w/h
                        self._try_parser(ComfyUI, info=self._info, width=self._width, height=self._height)

                    if png_comment_chunk and not self._parser: # Fooocus
                        try:
                            self._try_parser(Fooocus, info=json.loads(png_comment_chunk)) # VERIFY: Fooocus.__init__(info)
                        except json.JSONDecodeError: self._logger.warn("Fooocus PNG Comment: Not valid JSON.")
                    
                    if png_xmp_chunk and not self._parser: # DrawThings
                        try:
                            xmp_dom = minidom.parseString(png_xmp_chunk)
                            uc_node = xmp_dom.getElementsByTagName("exif:UserComment")
                            if uc_node and uc_node[0].childNodes and len(uc_node[0].childNodes) > 1 and \
                               uc_node[0].childNodes[1].childNodes and len(uc_node[0].childNodes[1].childNodes) > 1 and \
                               uc_node[0].childNodes[1].childNodes[1].childNodes:
                                json_str = uc_node[0].childNodes[1].childNodes[1].childNodes[0].data
                                self._try_parser(DrawThings, info=json.loads(json_str)) # VERIFY: DrawThings.__init__(info)
                        except Exception: self._logger.warn("DrawThings PNG XMP: Error parsing structure.")

                    if f_img.mode == "RGBA" and not self._parser: # NovelAI LSB
                        try:
                            # Create LSBExtractor with the PIL Image object f_img
                            reader = NovelAI.LSBExtractor(f_img) 
                            magic = reader.get_next_n_bytes(len(self.NOVELAI_MAGIC))
                            if magic and magic.decode("utf-8", errors="ignore") == self.NOVELAI_MAGIC:
                                # VERIFY: NovelAI.__init__(extractor) - no width/height here
                                self._try_parser(NovelAI, extractor=reader)
                        except Exception as e_lsb: self._logger.warn(f"NovelAI LSB (PNG) check error: {e_lsb}")

                # 3. JPEG/WEBP Processing Logic
                elif not self._parser and self._format_str in ["JPEG", "WEBP"]:
                    raw_uc = None; sw_tag = ""
                    jfif_comment = self._info.get("comment", b'').decode('utf-8', 'ignore')
                    if self._info.get("exif"):
                        try:
                            exif_d = piexif.load(self._info["exif"])
                            uc_b = exif_d.get("Exif", {}).get(piexif.ExifIFD.UserComment)
                            if uc_b: raw_uc = piexif.helper.UserComment.load(uc_b)
                            sw_b = exif_d.get("0th", {}).get(piexif.ImageIFD.Software)
                            if sw_b: sw_tag = sw_b.decode('ascii', 'ignore').strip()
                        except Exception as e_exif: self._logger.warn(f"piexif load error for EXIF: {e_exif}")

                    # 3.1. YOUR CUSTOM PARSERS (UserComment)
                    if raw_uc and not self._parser:
                        # Try RuinedFooocus
                        if raw_uc.strip().startswith("{"):
                            try:
                                uc_j = json.loads(raw_uc)
                                if isinstance(uc_j, dict) and uc_j.get("software") == "RuinedFooocus":
                                    # VERIFY: RuinedFooocusFormat.__init__(raw, width, height)
                                    self._try_parser(RuinedFooocusFormat, raw=raw_uc, width=self._width, height=self._height)
                            except json.JSONDecodeError: pass # Not JSON or not RF
                        
                        # Try Civitai if not RuinedFooocus and not already parsed
                        if not self._parser:
                            is_civ = False # Placeholder for your Civitai detection logic
                            if sw_tag == "4c6047c3-8b1c-4058-8888-fd48353bf47d": is_civ = True
                            elif raw_uc and "charset=Unicode" in raw_uc:
                                td = raw_uc.split("charset=Unicode", 1)[-1].strip()
                                if (td.startswith('笀∀爀攀猀漀甀爀挀攀') or td.startswith('{"resource-stack":')) and '"extraMetadata":' in td: is_civ = True
                            elif raw_uc and raw_uc.startswith('{"resource-stack":') and '"extraMetadata":' in raw_uc: is_civ = True
                            if is_civ:
                                # VERIFY: CivitaiComfyUIFormat.__init__(raw, width, height)
                                self._try_parser(CivitaiComfyUIFormat, raw=raw_uc, width=self._width, height=self._height)
                    
                    # 3.2. Fooocus (JFIF Comment)
                    if not self._parser and jfif_comment:
                        try:
                            jfif_j = json.loads(jfif_comment)
                            if isinstance(jfif_j, dict) and "prompt" in jfif_j:
                                self._try_parser(Fooocus, info=jfif_j) # VERIFY: Fooocus.__init__(info)
                        except json.JSONDecodeError: pass

                    # 3.3. Standard UserComment Fallbacks
                    if not self._parser and raw_uc:
                        self._raw = raw_uc # Set self._raw for these generalist parsers
                        if "sui_image_params" in raw_uc: self._try_parser(SwarmUI, raw=self._raw) # VERIFY: SwarmUI.__init__(raw)
                        elif raw_uc.strip().startswith("{") and not self._parser: self._try_parser(EasyDiffusion, raw=self._raw) # VERIFY: ED.__init__(raw)
                        elif not self._parser: self._try_parser(A1111, raw=self._raw) # A1111.__init__(raw)
                    
                    # 3.4. NovelAI LSB (RGBA JPEG/WEBP)
                    if not self._parser and f_img.mode == "RGBA":
                        try:
                            reader = NovelAI.LSBExtractor(f_img)
                            magic = reader.get_next_n_bytes(len(self.NOVELAI_MAGIC))
                            if magic and magic.decode("utf-8", errors="ignore") == self.NOVELAI_MAGIC:
                                self._try_parser(NovelAI, extractor=reader) # VERIFY: NovelAI.__init__(extractor=)
                        except Exception as e_lsb_j: self._logger.warn(f"NovelAI LSB (JPEG/WEBP) check error: {e_lsb_j}")
        
        except FileNotFoundError:
            self._logger.error(f"Image file not found: {file_path_or_obj}")
            self._status = BaseFormat.Status.FORMAT_ERROR
            self._error = "Image file not found."
        except Exception as e_outer_open: # General error opening image or during the try-cascade
            self._logger.error(f"Error opening or processing image '{Path(str(file_path_or_obj)).name}': {e_outer_open}", exc_info=False) # exc_info=True for deep debug
            self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error: self._error = f"Pillow/general error: {e_outer_open}"

        # --- Final Status Check ---
        # If _status is still UNREAD after all attempts, it means no parser was even applicable or all failed very early.
        if self._status == BaseFormat.Status.UNREAD:
            self._logger.warn(f"No suitable parser found or no parser claimed success for '{Path(str(file_path_or_obj)).name}'.")
            self._status = BaseFormat.Status.FORMAT_ERROR
            if not self._error: # If no specific error was set by _try_parser or PIL
                self._error = "No suitable parser found or parsing failed."
        
        # Log final outcome
        log_tool_name = self._tool if self._tool else "None"
        log_status_name = self._status.name if hasattr(self._status, 'name') else str(self._status)
        self._logger.info(f"Final Reading Status for '{Path(str(file_path_or_obj)).name}': {log_status_name}, Tool: {log_tool_name}")
        
        # Get the most relevant error message to log
        final_error_to_log = self._error # Start with ImageDataReader's own error
        if self._parser and getattr(self._parser, 'error', None): # If a parser was assigned and has an error
            if self._status != BaseFormat.Status.READ_SUCCESS or not final_error_to_log : # Prefer parser's error if IDR status isn't success or IDR has no error
                 final_error_to_log = self._parser.error

        if self._status != BaseFormat.Status.READ_SUCCESS and final_error_to_log:
            self._logger.warn(f"Error details: {final_error_to_log}")
        elif self._status != BaseFormat.Status.READ_SUCCESS: # Fallback if no specific error message
            self._logger.warn(f"Parsing failed with status {log_status_name} (no specific error message captured).")


    # --- Static Methods ---
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
                    if metadata_to_embed: img_to_save.save(new_path, pnginfo=metadata_to_embed)
                    else: img_to_save.save(new_path)
                elif image_format_upper in ["JPEG", "JPG"]:
                    img_to_save.save(new_path, quality=95, exif=img_to_save.info.get("exif")) # Try to preserve existing exif
                    if metadata_to_embed: # piexif.insert will overwrite existing UserComment
                        try: piexif.insert(metadata_to_embed, str(new_path))
                        except Exception as e_ins_jpg: Logger("DSVendored_SDPR.ImageDataReader").error(f"piexif insert (JPG) error: {e_ins_jpg}")
                elif image_format_upper == "WEBP":
                    # Pillow's WEBP save might not preserve all EXIF, piexif.insert is main method
                    img_to_save.save(new_path, quality=100, lossless=True) 
                    if metadata_to_embed:
                        try: piexif.insert(metadata_to_embed, str(new_path))
                        except Exception as e_ins_webp: Logger("DSVendored_SDPR.ImageDataReader").error(f"piexif insert (WEBP) error: {e_ins_webp}")
            except Exception as e_save:
                Logger("DSVendored_SDPR.ImageDataReader").error(f"Image save error for {new_path}: {e_save}")

    @staticmethod
    def construct_data(positive, negative, setting):
        return "\n".join(filter(None, [
            f"{positive}" if positive else "",
            f"Negative prompt: {negative}" if negative else "",
            f"{setting}" if setting else ""
        ]))

    def prompt_to_line(self):
        if self._parser and hasattr(self._parser, 'prompt_to_line'):
            return self._parser.prompt_to_line()
        return ""

    # --- Properties ---
    @property
    def height(self) -> str:
        parser_h = getattr(self._parser, 'height', None)
        # Use parser's height if it's valid and different from PIL's initial, else PIL's
        return str(parser_h) if parser_h is not None and str(parser_h) != "0" else str(self._height)

    @property
    def width(self) -> str:
        parser_w = getattr(self._parser, 'width', None)
        return str(parser_w) if parser_w is not None and str(parser_w) != "0" else str(self._width)

    @property
    def info(self) -> dict: return self._info
    @property
    def positive(self) -> str: return str(getattr(self._parser, 'positive', self._positive))
    @property
    def negative(self) -> str: return str(getattr(self._parser, 'negative', self._negative))
    @property
    def positive_sdxl(self) -> dict: return getattr(self._parser, 'positive_sdxl', self._positive_sdxl or {})
    @property
    def negative_sdxl(self) -> dict: return getattr(self._parser, 'negative_sdxl', self._negative_sdxl or {})
    @property
    def setting(self) -> str: return str(getattr(self._parser, 'setting', self._setting))
    @property
    def raw(self) -> str:
        parser_raw = getattr(self._parser, 'raw', None)
        return str(parser_raw if parser_raw is not None else self._raw) # Prefer parser's raw if it set one
    @property
    def tool(self) -> str:
        parser_tool = getattr(self._parser, 'tool', None)
        return str(parser_tool) if parser_tool and parser_tool != "Unknown" else str(self._tool)
    @property
    def parameter(self) -> dict: return getattr(self._parser, 'parameter', self._parameter or {})
    @property
    def format(self) -> str: return self._format_str # Image format from PIL
    @property
    def is_sdxl(self) -> bool: return getattr(self._parser, 'is_sdxl', self._is_sdxl)
    @property
    def props(self) -> str: # If parser has a props method/property
        return getattr(self._parser, 'props', self._props) 
    @property
    def status(self) -> BaseFormat.Status: return self._status
    @property
    def error(self) -> str: # Expose the error message
        parser_err = getattr(self._parser, 'error', None)
        return str(parser_err if parser_err else self._error)