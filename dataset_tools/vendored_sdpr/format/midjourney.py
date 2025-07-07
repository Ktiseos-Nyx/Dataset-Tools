# dataset_tools/vendored_sdpr/format/midjourney.py

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from re import Pattern
from typing import Any

from .base_format import BaseFormat


class MidjourneySignatureType(Enum):
    """Types of Midjourney signatures for identification"""

    XMP_DIGITAL_GUID = "xmp_digital_guid"
    EXIF_MAKE = "exif_make"
    PARAMETER_PATTERNS = "parameter_patterns"
    JOB_ID_PATTERN = "job_id_pattern"


@dataclass
class MidjourneyConfig:
    """Configuration for Midjourney format parsing - systematically organized"""

    # Parameter regex patterns for Midjourney commands
    PARAMETER_PATTERNS: dict[str, Pattern[str]] = field(
        default_factory=lambda: {
            "ar": re.compile(r"--ar\s+([\d:\.]+)", re.IGNORECASE),
            "v": re.compile(r"--v(?:ersion)?\s+([\d\.]+)", re.IGNORECASE),
            "style": re.compile(r"--style\s+([a-zA-Z0-9_-]+(?:\s+raw)?)", re.IGNORECASE),
            "stylize": re.compile(r"--s(?:tylize)?\s+(\d+)", re.IGNORECASE),
            "niji": re.compile(r"--niji\s*(\d*)", re.IGNORECASE),
            "chaos": re.compile(r"--c(?:haos)?\s+(\d+)", re.IGNORECASE),
            "iw": re.compile(r"--iw\s+([\d\.]+)", re.IGNORECASE),
            "sref": re.compile(r"--sref\s+((?:https?://\S+\s*)+)", re.IGNORECASE),
            "cref": re.compile(r"--cref\s+((?:https?://\S+\s*)+)", re.IGNORECASE),
            "cw": re.compile(r"--cw\s+(\d+)", re.IGNORECASE),
            "weird": re.compile(r"--weird\s+(\d+)", re.IGNORECASE),
            "tile": re.compile(r"--tile", re.IGNORECASE),
            "quality": re.compile(r"--q(?:uality)?\s+([\d\.]+)", re.IGNORECASE),
            "seed": re.compile(r"--seed\s+(\d+)", re.IGNORECASE),
            "stop": re.compile(r"--stop\s+(\d+)", re.IGNORECASE),
            "no": re.compile(r"--no\s+([^-]+?)(?=\s*--|\s*$)", re.IGNORECASE),
            "aspect": re.compile(r"--aspect\s+([\d:\.]+)", re.IGNORECASE),  # Alternative to --ar
        }
    )

    # Flag parameters (no values)
    FLAG_PARAMETERS: set[str] = field(default_factory=lambda: {"tile", "hd", "fast", "relax", "turbo"})

    # Parameter mapping to standard names
    PARAMETER_MAPPINGS: dict[str, str] = field(
        default_factory=lambda: {
            "v": "version",
            "ar": "aspect_ratio",
            "aspect": "aspect_ratio",
            "stylize": "stylize",
            "s": "stylize",
            "chaos": "chaos",
            "c": "chaos",
            "quality": "quality",
            "q": "quality",
            "seed": "seed",
            "stop": "stop",
            "iw": "image_weight",
            "cw": "character_weight",
            "weird": "weird",
            "sref": "style_reference_urls",
            "cref": "character_reference_urls",
            "no": "negative_elements",
            "style": "style_preset",
            "niji": "niji_version",
            "tile": "tile_mode",
        }
    )

    # XMP keys for Midjourney identification
    XMP_IDENTIFICATION_KEYS: set[str] = field(
        default_factory=lambda: {
            "Xmp.iptcExt.DigImageGUID",
            "iptcExt:DigImageGUID",
            "Xmp.dc.description",
            "dc:description",
        }
    )

    # EXIF keys that might contain Midjourney signatures
    EXIF_IDENTIFICATION_KEYS: set[str] = field(
        default_factory=lambda: {
            "Exif.Image.Make",
            "Exif.Image.Software",
            "Exif.Photo.UserComment",
        }
    )

    # Job ID pattern
    JOB_ID_PATTERN: Pattern[str] = field(
        default_factory=lambda: re.compile(
            r"Job ID:\s*([0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12})",
            re.IGNORECASE,
        )
    )

    # Midjourney-specific identifiers in text
    MIDJOURNEY_IDENTIFIERS: set[str] = field(
        default_factory=lambda: {
            "midjourney",
            "discord.gg/midjourney",
            "/imagine",
            "mj_",
            "--",
        }
    )


class MidjourneySignatureDetector:
    """Advanced signature detection for Midjourney identification"""

    def __init__(self, config: MidjourneyConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def detect_midjourney_signatures(self, info_data: dict[str, Any], raw_data: str = "") -> dict[str, Any]:
        """Comprehensive Midjourney signature detection.
        Returns detailed analysis of found signatures.
        """
        detection_result = {
            "is_midjourney": False,
            "confidence_score": 0.0,
            "signatures_found": [],
            "xmp_analysis": {},
            "exif_analysis": {},
            "description_analysis": {},
            "job_id_info": {},
        }

        # Analyze XMP data
        xmp_score = self._analyze_xmp_signatures(info_data, detection_result)

        # Analyze EXIF data
        exif_score = self._analyze_exif_signatures(info_data, detection_result)

        # Analyze description/text content
        desc_score = self._analyze_description_signatures(info_data, raw_data, detection_result)

        # Calculate overall confidence
        detection_result["confidence_score"] = self._calculate_confidence(xmp_score, exif_score, desc_score)

        # Determine if this is definitively Midjourney
        detection_result["is_midjourney"] = self._is_definitive_midjourney(detection_result)

        self.logger.debug(
            f"Midjourney detection: confidence={detection_result['confidence_score']:.2f}, "
            f"signatures={len(detection_result['signatures_found'])}"
        )

        return detection_result

    def _analyze_xmp_signatures(self, info_data: dict[str, Any], result: dict[str, Any]) -> float:
        """Analyze XMP data for Midjourney signatures"""
        xmp_data = info_data.get("XMP", {})
        if not isinstance(xmp_data, dict):
            xmp_data = {}

        score = 0.0
        xmp_analysis = {
            "has_digital_guid": False,
            "digital_guid_value": None,
            "has_description": False,
            "description_source": None,
        }

        # Check for Digital Image GUID (strongest XMP indicator)
        for guid_key in ["Xmp.iptcExt.DigImageGUID", "iptcExt:DigImageGUID"]:
            if guid_key in xmp_data:
                xmp_analysis["has_digital_guid"] = True
                xmp_analysis["digital_guid_value"] = xmp_data[guid_key]
                result["signatures_found"].append(MidjourneySignatureType.XMP_DIGITAL_GUID)
                score += 0.8  # Very strong indicator
                break

        # Check for description in XMP
        for desc_key in ["Xmp.dc.description", "dc:description"]:
            if desc_key in xmp_data:
                desc_data = xmp_data[desc_key]
                if isinstance(desc_data, dict):
                    description = desc_data.get("x-default", "")
                elif isinstance(desc_data, str):
                    description = desc_data
                else:
                    continue

                if description and any(
                    identifier in description.lower() for identifier in self.config.MIDJOURNEY_IDENTIFIERS
                ):
                    xmp_analysis["has_description"] = True
                    xmp_analysis["description_source"] = desc_key
                    score += 0.3

        result["xmp_analysis"] = xmp_analysis
        return score

    def _analyze_exif_signatures(self, info_data: dict[str, Any], result: dict[str, Any]) -> float:
        """Analyze EXIF data for Midjourney signatures"""
        exif_data = info_data.get("EXIF", {})
        if not isinstance(exif_data, dict):
            exif_data = {}

        score = 0.0
        exif_analysis = {
            "make_is_midjourney": False,
            "software_is_midjourney": False,
            "has_user_comment": False,
            "make_value": None,
            "software_value": None,
        }

        # Check EXIF Make
        make_value = exif_data.get("Exif.Image.Make", info_data.get("software_tag", ""))
        if make_value and "midjourney" in str(make_value).lower():
            exif_analysis["make_is_midjourney"] = True
            exif_analysis["make_value"] = str(make_value)
            result["signatures_found"].append(MidjourneySignatureType.EXIF_MAKE)
            score += 0.6  # Strong indicator

        # Check EXIF Software
        software_value = exif_data.get("Exif.Image.Software", "")
        if software_value and "midjourney" in str(software_value).lower():
            exif_analysis["software_is_midjourney"] = True
            exif_analysis["software_value"] = str(software_value)
            score += 0.5

        # Check for UserComment
        if "Exif.Photo.UserComment" in exif_data:
            exif_analysis["has_user_comment"] = True
            score += 0.1  # Minor indicator

        result["exif_analysis"] = exif_analysis
        return score

    def _analyze_description_signatures(
        self, info_data: dict[str, Any], raw_data: str, result: dict[str, Any]
    ) -> float:
        """Analyze description/text content for Midjourney signatures"""
        description_texts = self._extract_all_description_sources(info_data, raw_data)

        score = 0.0
        desc_analysis = {
            "sources_checked": list(description_texts.keys()),
            "has_mj_parameters": False,
            "parameter_count": 0,
            "has_job_id": False,
            "job_id_value": None,
            "primary_source": None,
        }

        for source, text in description_texts.items():
            if not text:
                continue

            # Check for Midjourney parameters
            param_count = sum(1 for pattern in self.config.PARAMETER_PATTERNS.values() if pattern.search(text))
            if param_count > 0:
                desc_analysis["has_mj_parameters"] = True
                desc_analysis["parameter_count"] = max(desc_analysis["parameter_count"], param_count)
                desc_analysis["primary_source"] = source
                result["signatures_found"].append(MidjourneySignatureType.PARAMETER_PATTERNS)
                score += min(param_count * 0.1, 0.7)  # Cap at 0.7

            # Check for Job ID
            job_id_match = self.config.JOB_ID_PATTERN.search(text)
            if job_id_match:
                desc_analysis["has_job_id"] = True
                desc_analysis["job_id_value"] = job_id_match.group(1)
                result["signatures_found"].append(MidjourneySignatureType.JOB_ID_PATTERN)
                score += 0.4

        # Store job ID info in main result
        if desc_analysis["has_job_id"]:
            result["job_id_info"] = {
                "from_description": desc_analysis["job_id_value"],
                "from_xmp_guid": result["xmp_analysis"].get("digital_guid_value"),
            }

        result["description_analysis"] = desc_analysis
        return score

    def _extract_all_description_sources(self, info_data: dict[str, Any], raw_data: str) -> dict[str, str]:
        """Extract description text from all possible sources"""
        descriptions = {}

        # XMP description
        xmp_data = info_data.get("XMP", {})
        if isinstance(xmp_data, dict):
            for desc_key in ["Xmp.dc.description", "dc:description"]:
                if desc_key in xmp_data:
                    desc_data = xmp_data[desc_key]
                    if isinstance(desc_data, dict):
                        descriptions[f"XMP_{desc_key}"] = desc_data.get("x-default", "")
                    elif isinstance(desc_data, str):
                        descriptions[f"XMP_{desc_key}"] = desc_data

        # EXIF UserComment
        exif_data = info_data.get("EXIF", {})
        if isinstance(exif_data, dict):
            user_comment = exif_data.get("Exif.Photo.UserComment")
            if user_comment:
                decoded = self._decode_user_comment(user_comment)
                if decoded:
                    descriptions["EXIF_UserComment"] = decoded

        # Raw data as fallback
        if raw_data and not any(descriptions.values()):
            descriptions["raw_data"] = raw_data

        return descriptions

    def _decode_user_comment(self, user_comment: Any) -> str:
        """Decode EXIF UserComment with proper encoding handling"""
        if isinstance(user_comment, bytes):
            # Handle standard EXIF UserComment encodings
            if user_comment.startswith(b"UNICODE\x00"):
                try:
                    return user_comment[8:].decode("utf-16le", "replace")
                except UnicodeDecodeError:
                    pass
            elif user_comment.startswith(b"ASCII\x00\x00\x00"):
                try:
                    return user_comment[8:].decode("ascii", "replace")
                except UnicodeDecodeError:
                    pass
            else:
                # Try UTF-8 first, then latin-1 fallback
                try:
                    return user_comment.decode("utf-8", "replace")
                except UnicodeDecodeError:
                    return user_comment.decode("latin-1", "replace")
        elif isinstance(user_comment, str):
            return user_comment

        return ""

    def _calculate_confidence(self, xmp_score: float, exif_score: float, desc_score: float) -> float:
        """Calculate overall confidence score with weighted components"""
        # XMP has highest weight, then description analysis, then EXIF
        weighted_score = xmp_score * 3.0 + desc_score * 2.0 + exif_score * 1.5
        max_possible_score = 6.5  # Reasonable maximum for normalization
        return min(weighted_score / max_possible_score, 1.0)

    def _is_definitive_midjourney(self, result: dict[str, Any]) -> bool:
        """Determine if we have definitive proof this is Midjourney"""
        # XMP Digital GUID is definitive
        if result["xmp_analysis"].get("has_digital_guid"):
            return True

        # EXIF Make + parameters in description
        if result["exif_analysis"].get("make_is_midjourney") and result["description_analysis"].get(
            "has_mj_parameters"
        ):
            return True

        # Job ID + multiple parameters
        if (
            result["description_analysis"].get("has_job_id")
            and result["description_analysis"].get("parameter_count", 0) >= 2
        ):
            return True

        # High confidence with multiple signature types
        if result["confidence_score"] >= 0.8 and len(set(result["signatures_found"])) >= 2:
            return True

        return False


class MidjourneyParameterExtractor:
    """Extracts and processes Midjourney parameters from text"""

    def __init__(self, config: MidjourneyConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def extract_parameters_from_text(self, text: str) -> tuple[str, dict[str, str]]:
        """Extract Midjourney parameters from text and return cleaned prompt.
        Returns (cleaned_prompt, extracted_parameters)
        """
        if not text:
            return "", {}

        extracted_params = {}
        cleaned_text = text

        # Process each parameter pattern
        for param_key, pattern in self.config.PARAMETER_PATTERNS.items():
            matches = list(pattern.finditer(cleaned_text))

            for match in reversed(matches):  # Reverse to maintain indices during removal
                if param_key in self.config.FLAG_PARAMETERS:
                    # Flag parameter (no value)
                    extracted_params[param_key] = "true"
                # Parameter with value
                elif match.groups():
                    param_value = match.group(1).strip()
                    if param_value:  # Only store non-empty values
                        extracted_params[param_key] = param_value

                # Remove the matched parameter from text
                cleaned_text = cleaned_text[: match.start()] + cleaned_text[match.end() :]

        # Clean up the text after parameter removal
        cleaned_text = re.sub(r"\s{2,}", " ", cleaned_text).strip(" ,.-")

        self.logger.debug(f"Midjourney: Extracted {len(extracted_params)} parameters from text")
        return cleaned_text, extracted_params

    def standardize_parameters(self, raw_params: dict[str, str]) -> dict[str, str]:
        """Convert Midjourney parameters to standardized names"""
        standardized = {}

        for param_key, param_value in raw_params.items():
            # Map to standard name
            standard_key = self.config.PARAMETER_MAPPINGS.get(param_key, f"mj_{param_key}")

            # Process special values
            processed_value = self._process_parameter_value(param_key, param_value)
            standardized[standard_key] = processed_value

        return standardized

    def _process_parameter_value(self, param_key: str, value: str) -> str:
        """Process parameter values with key-specific logic"""
        if not value:
            return ""

        # Handle aspect ratio
        if param_key in ["ar", "aspect"]:
            return self._normalize_aspect_ratio(value)

        # Handle style references (URLs)
        if param_key in ["sref", "cref"]:
            return self._normalize_reference_urls(value)

        # Handle negative elements
        if param_key == "no":
            return self._normalize_negative_elements(value)

        # Handle boolean flags
        if param_key in self.config.FLAG_PARAMETERS:
            return "true"

        # Default: clean and return
        return value.strip()

    def _normalize_aspect_ratio(self, value: str) -> str:
        """Normalize aspect ratio to consistent format"""
        # Convert decimal to ratio if needed
        if ":" not in value and "." in value:
            try:
                decimal_value = float(value)
                # Convert common decimals to ratios
                ratio_map = {
                    1.0: "1:1",
                    1.33: "4:3",
                    1.5: "3:2",
                    1.78: "16:9",
                    2.0: "2:1",
                }
                for ratio_decimal, ratio_str in ratio_map.items():
                    if abs(decimal_value - ratio_decimal) < 0.05:
                        return ratio_str
                # If no match, convert to simple ratio
                return f"{decimal_value}:1"
            except ValueError:
                pass

        return value

    def _normalize_reference_urls(self, value: str) -> str:
        """Normalize reference URLs"""
        # Split multiple URLs and clean them
        urls = [url.strip() for url in value.split() if url.strip().startswith("http")]
        return " ".join(urls)

    def _normalize_negative_elements(self, value: str) -> str:
        """Normalize negative elements list"""
        # Clean up the negative elements list
        elements = [elem.strip() for elem in value.split(",") if elem.strip()]
        return ", ".join(elements)


class MidjourneyFormat(BaseFormat):
    """Enhanced Midjourney format parser with comprehensive signature detection.

    Handles multiple Midjourney identification methods:
    - XMP Digital Image GUID (strongest indicator)
    - EXIF Make/Software fields
    - Parameter patterns in descriptions
    - Job ID patterns
    """

    tool = "Midjourney"

    def __init__(
        self,
        info: dict[str, Any] | None = None,
        raw: str = "",
        width: Any = 0,
        height: Any = 0,
        logger_obj: logging.Logger | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            info=info,
            raw=raw,
            width=width,
            height=height,
            logger_obj=logger_obj,
            **kwargs,
        )

        # Initialize components
        self.config = MidjourneyConfig()
        self.signature_detector = MidjourneySignatureDetector(self.config, self._logger)
        self.parameter_extractor = MidjourneyParameterExtractor(self.config, self._logger)

        # Store detection results
        self._detection_result: dict[str, Any] | None = None

    def _process(self) -> None:
        """Main processing pipeline for Midjourney format"""
        self._logger.debug(f"{self.tool}: Starting Midjourney format processing")

        # Validate input data
        if not self._info:
            self._logger.debug(f"{self.tool}: No info data provided")
            self.status = self.Status.MISSING_INFO
            self._error = "No metadata provided for Midjourney analysis"
            return

        # Perform comprehensive signature detection
        self._detection_result = self.signature_detector.detect_midjourney_signatures(self._info, self._raw)

        # Check if this is definitively Midjourney
        if not self._detection_result["is_midjourney"]:
            confidence = self._detection_result["confidence_score"]
            signatures = len(self._detection_result["signatures_found"])
            self._logger.debug(
                f"{self.tool}: Not identified as Midjourney (confidence: {confidence:.2f}, signatures: {signatures})"
            )
            self.status = self.Status.FORMAT_DETECTION_ERROR
            self._error = "No definitive Midjourney signatures found"
            return

        # Extract and process data
        success = self._extract_midjourney_data()
        if not success:
            return  # Error already set

        self._logger.info(
            f"{self.tool}: Successfully parsed with {self._detection_result['confidence_score']:.2f} confidence"
        )

    def _extract_midjourney_data(self) -> bool:
        """Extract Midjourney-specific data from detected sources"""
        try:
            # Find the best description source
            desc_analysis = self._detection_result.get("description_analysis", {})
            primary_source = desc_analysis.get("primary_source")

            if not primary_source:
                # Fall back to any available source
                sources = desc_analysis.get("sources_checked", [])
                if not sources:
                    self._logger.warning(f"{self.tool}: No description sources found")
                    self.status = self.Status.FORMAT_ERROR
                    self._error = "No description text found for parameter extraction"
                    return False
                primary_source = sources[0]

            # Get the description text
            description_text = self._get_description_text_by_source(primary_source)
            if not description_text:
                self._logger.warning(f"{self.tool}: Empty description from source {primary_source}")
                self.status = self.Status.FORMAT_ERROR
                self._error = f"Empty description from {primary_source}"
                return False

            # Extract parameters and clean prompt
            prompt_text, raw_params = self.parameter_extractor.extract_parameters_from_text(description_text)

            # Set prompt
            self._positive = prompt_text.strip()

            # Process and standardize parameters
            standardized_params = self.parameter_extractor.standardize_parameters(raw_params)
            self._parameter.update(standardized_params)

            # Add Job ID if found
            job_id_info = self._detection_result.get("job_id_info", {})
            job_id = job_id_info.get("from_description") or job_id_info.get("from_xmp_guid")
            if job_id:
                self._parameter["job_id"] = job_id

            # Add detection metadata
            self._parameter["midjourney_confidence"] = f"{self._detection_result['confidence_score']:.2f}"
            self._parameter["detection_signatures"] = str(len(self._detection_result["signatures_found"]))

            # Handle dimensions
            self._apply_dimensions()

            # Set raw data and settings
            if not self._raw:
                self._raw = description_text
            self._setting = description_text  # Full original description

            return True

        except Exception as e:
            self._logger.error(f"{self.tool}: Error during data extraction: {e}")
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Midjourney data extraction failed: {e}"
            return False

    def _get_description_text_by_source(self, source: str) -> str:
        """Get description text from a specific source"""
        if source.startswith("XMP_"):
            xmp_key = source.replace("XMP_", "")
            xmp_data = self._info.get("XMP", {})
            if isinstance(xmp_data, dict) and xmp_key in xmp_data:
                desc_data = xmp_data[xmp_key]
                if isinstance(desc_data, dict):
                    return desc_data.get("x-default", "")
                if isinstance(desc_data, str):
                    return desc_data
        elif source == "EXIF_UserComment":
            exif_data = self._info.get("EXIF", {})
            if isinstance(exif_data, dict):
                user_comment = exif_data.get("Exif.Photo.UserComment")
                if user_comment:
                    return self.signature_detector._decode_user_comment(user_comment)
        elif source == "raw_data":
            return self._raw

        return ""

    def _apply_dimensions(self) -> None:
        """Apply dimensions from image or aspect ratio"""
        # Use existing dimensions if available
        if self._width != "0" and self._height != "0":
            self._parameter["width"] = self._width
            self._parameter["height"] = self._height
            self._parameter["size"] = f"{self._width}x{self._height}"
        # Could also calculate from aspect ratio if needed

    def get_midjourney_analysis(self) -> dict[str, Any]:
        """Get detailed analysis of Midjourney detection and features"""
        if not self._detection_result:
            return {"error": "No detection analysis available"}

        return {
            "detection_summary": {
                "is_midjourney": self._detection_result["is_midjourney"],
                "confidence_score": self._detection_result["confidence_score"],
                "signatures_found": [sig.value for sig in self._detection_result["signatures_found"]],
            },
            "signature_analysis": {
                "xmp_signatures": self._detection_result.get("xmp_analysis", {}),
                "exif_signatures": self._detection_result.get("exif_analysis", {}),
                "description_signatures": self._detection_result.get("description_analysis", {}),
            },
            "extracted_features": self._analyze_midjourney_features(),
        }

    def _analyze_midjourney_features(self) -> dict[str, Any]:
        """Analyze Midjourney-specific features detected"""
        features = {
            "has_version": False,
            "has_aspect_ratio": False,
            "has_style_settings": False,
            "has_reference_images": False,
            "advanced_features": [],
            "parameter_count": 0,
        }

        # Analyze parameters
        param_count = 0
        for key, value in self._parameter.items():
            if key.startswith("mj_") or key in [
                "version",
                "aspect_ratio",
                "stylize",
                "chaos",
            ]:
                param_count += 1

        features["parameter_count"] = param_count

        # Check specific features
        features["has_version"] = "version" in self._parameter
        features["has_aspect_ratio"] = "aspect_ratio" in self._parameter
        features["has_style_settings"] = any(key in self._parameter for key in ["stylize", "style_preset", "chaos"])
        features["has_reference_images"] = any(
            key in self._parameter for key in ["style_reference_urls", "character_reference_urls"]
        )

        # Advanced features
        if "niji_version" in self._parameter:
            features["advanced_features"].append("niji")
        if "weird" in self._parameter:
            features["advanced_features"].append("weird")
        if "tile_mode" in self._parameter:
            features["advanced_features"].append("tile")

        return features

    def debug_midjourney_detection(self) -> dict[str, Any]:
        """Get comprehensive debugging information"""
        if not self._detection_result:
            return {"error": "No detection data available"}

        return {
            "input_data_summary": {
                "has_info": bool(self._info),
                "info_keys": list(self._info.keys()) if self._info else [],
                "has_raw": bool(self._raw),
                "raw_length": len(self._raw) if self._raw else 0,
                "has_xmp": "XMP" in (self._info or {}),
                "has_exif": "EXIF" in (self._info or {}),
            },
            "detection_details": self._detection_result,
            "parameter_extraction": {
                "total_parameters": len(self._parameter),
                "midjourney_parameters": [
                    k
                    for k in self._parameter.keys()
                    if k.startswith("mj_") or k in self.config.PARAMETER_MAPPINGS.values()
                ],
                "prompt_length": len(self._positive) if self._positive else 0,
            },
            "config_info": {
                "total_parameter_patterns": len(self.config.PARAMETER_PATTERNS),
                "flag_parameters": list(self.config.FLAG_PARAMETERS),
                "xmp_keys_checked": list(self.config.XMP_IDENTIFICATION_KEYS),
                "exif_keys_checked": list(self.config.EXIF_IDENTIFICATION_KEYS),
            },
        }
