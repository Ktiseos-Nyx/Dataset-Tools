# dataset_tools/file_readers/text_file_reader.py

"""Text file reader for plain text files and prompts.

This module handles reading various text file formats with proper encoding
detection and error handling. Think of it as your text specialist who can
read any scroll or tome in the realm! 📜✨
"""

import re
from pathlib import Path
from typing import Any

from ..correct_types import UpField
from ..logger import debug_monitor, get_logger
from ..logger import info_monitor as nfo


class TextFileReader:
    """Specialized reader for text files.

    This class handles reading plain text files with automatic encoding
    detection and robust error handling.
    """

    def __init__(self):
        """Initialize the text file reader."""
        self.logger = get_logger(f"{__name__}.TextFileReader")

        # Supported text file extensions
        self.supported_formats = {".txt", ".text", ".md", ".markdown", ".rst", ".log"}

        # Encodings to try in order of preference
        self.encodings_to_try = [
            "utf-8",
            "utf-16",
            "utf-16-le",
            "utf-16-be",
            "utf-32",
            "latin-1",
            "cp1252",  # Windows-1252
            "iso-8859-1",
            "ascii",
        ]

    def can_read_file(self, file_path: str) -> bool:
        """Check if this reader can handle the given file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if this reader supports the file format

        """
        suffix = Path(file_path).suffix.lower()
        return suffix in self.supported_formats

    @debug_monitor
    def read_file(self, file_path: str) -> dict[str, Any] | None:
        """Read a text file with automatic encoding detection.

        Args:
            file_path: Path to the text file

        Returns:
            Dictionary containing file contents or None if reading failed

        """
        if not self.can_read_file(file_path):
            self.logger.warning(f"Unsupported text file format: {file_path}")
            return None

        nfo(f"[TextReader] Reading text file: {Path(file_path).name}")

        # Try each encoding until one works
        for encoding in self.encodings_to_try:
            try:
                content = self._read_with_encoding(file_path, encoding)
                if content is not None:
                    nfo(f"[TextReader] Successfully read with encoding: {encoding}")

                    # Analyze the content
                    analysis = self._analyze_content(content, file_path)

                    return {
                        UpField.TEXT_DATA.value: content,
                        "encoding_used": encoding,
                        "file_size": len(content),
                        "line_count": content.count("\n") + 1,
                        **analysis,
                    }

            except UnicodeDecodeError:
                self.logger.debug(f"Failed to decode {file_path} with {encoding}")
                continue
            except Exception as e:
                self.logger.warning(f"Error reading {file_path} with {encoding}: {e}")
                continue

        # If all encodings failed
        nfo(f"[TextReader] Failed to decode {Path(file_path).name} with any supported encoding")
        return None

    def _read_with_encoding(self, file_path: str, encoding: str) -> str | None:
        """Read file with a specific encoding.

        Args:
            file_path: Path to the file
            encoding: Encoding to use

        Returns:
            File content or None if reading failed

        """
        try:
            with open(file_path, encoding=encoding, errors="strict") as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            # Re-raise Unicode errors so we can try the next encoding
            raise
        except FileNotFoundError:
            self.logger.error(f"Text file not found: {file_path}")
            return None
        except PermissionError:
            self.logger.error(f"Permission denied reading text file: {file_path}")
            return None
        except OSError as e:
            self.logger.error(f"OS error reading text file {file_path}: {e}")
            return None

    def _analyze_content(self, content: str, file_path: str) -> dict[str, Any]:
        """Analyze text content for additional metadata.

        Args:
            content: Text content to analyze
            file_path: Path to the original file

        Returns:
            Dictionary with content analysis

        """
        analysis = {}

        try:
            # Basic statistics
            analysis["character_count"] = len(content)
            analysis["word_count"] = len(content.split())
            analysis["line_count"] = content.count("\n") + 1

            # Check for empty content
            analysis["is_empty"] = len(content.strip()) == 0

            # Detect likely content type
            analysis["content_type"] = self._detect_content_type(content, file_path)

            # Check for special patterns
            analysis["appears_to_be_prompt"] = self._is_likely_ai_prompt(content)
            analysis["has_metadata_markers"] = self._has_metadata_markers(content)

        except Exception as e:
            self.logger.debug(f"Error analyzing content for {file_path}: {e}")

        return analysis

    def _detect_content_type(self, content: str, file_path: str) -> str:
        """Detect the likely type of text content.

        Args:
            content: Text content
            file_path: Original file path

        Returns:
            Detected content type string

        """
        # Check file extension first
        suffix = Path(file_path).suffix.lower()

        if suffix in {".md", ".markdown"}:
            return "markdown"
        if suffix == ".rst":
            return "restructuredtext"
        if suffix == ".log":
            return "log_file"

        # Content-based detection
        content_lower = content.lower().strip()

        # Check for common prompt indicators
        prompt_indicators = [
            "masterpiece",
            "best quality",
            "highly detailed",
            "negative prompt:",
            "steps:",
            "sampler:",
            "cfg scale:",
            "seed:",
            "model:",
            "lora:",
            "embedding:",
        ]

        if any(indicator in content_lower for indicator in prompt_indicators):
            return "ai_prompt"

        # Check for markdown indicators
        markdown_indicators = ["#", "##", "###", "**", "__", "[", "]("]
        if any(indicator in content for indicator in markdown_indicators):
            return "markdown"

        # Check for code-like content
        if any(lang in content_lower for lang in ["import ", "def ", "function ", "var ", "const "]):
            return "code"

        # Check for configuration-like content
        if "=" in content and "\n" in content:
            lines = content.split("\n")
            config_lines = sum(1 for line in lines if "=" in line and not line.strip().startswith("#"))
            if config_lines > len(lines) * 0.3:  # 30% of lines look like config
                return "configuration"

        return "plain_text"

    def _is_likely_ai_prompt(self, content: str) -> bool:
        """Check if content looks like an AI prompt.

        Args:
            content: Text content to check

        Returns:
            True if content appears to be an AI prompt

        """
        content_lower = content.lower()

        # Strong AI prompt indicators
        strong_indicators = [
            "negative prompt:",
            "steps:",
            "sampler:",
            "cfg scale:",
            "model hash:",
            "masterpiece, best quality",
            "highly detailed",
        ]

        if any(indicator in content_lower for indicator in strong_indicators):
            return True

        # Weak indicators (need multiple)
        weak_indicators = [
            "masterpiece",
            "best quality",
            "detailed",
            "beautiful",
            "realistic",
            "photorealistic",
            "high resolution",
            "professional",
            "concept art",
        ]

        weak_count = sum(1 for indicator in weak_indicators if indicator in content_lower)
        return weak_count >= 3  # Need at least 3 weak indicators

    def _has_metadata_markers(self, content: str) -> bool:
        """Check if content has metadata-like markers.

        Args:
            content: Text content to check

        Returns:
            True if content has metadata patterns

        """
        # Look for key:value patterns
        lines = content.split("\n")
        metadata_patterns = 0

        for line in lines:
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                # Simple key:value pattern
                parts = line.split(":", 1)
                if len(parts) == 2 and len(parts[0].strip()) > 0:
                    metadata_patterns += 1

        # If more than 20% of lines look like metadata
        return metadata_patterns > len(lines) * 0.2

    def get_supported_formats(self) -> set[str]:
        """Get the set of supported text file formats."""
        return self.supported_formats.copy()

    def add_supported_format(self, extension: str) -> None:
        """Add a new supported file format.

        Args:
            extension: File extension to add (with or without dot)

        """
        if not extension.startswith("."):
            extension = "." + extension

        self.supported_formats.add(extension.lower())
        self.logger.debug(f"Added supported format: {extension}")


class TextContentAnalyzer:
    """Advanced analyzer for text file content.

    This class provides detailed analysis of text content beyond basic
    reading. Like having a scholar examine ancient texts! 📚✨
    """

    def __init__(self):
        """Initialize the text content analyzer."""
        self.logger = get_logger(f"{__name__}.TextContentAnalyzer")

    def analyze_ai_prompt(self, content: str) -> dict[str, Any]:
        """Analyze AI prompt content for structure and components.

        Args:
            content: AI prompt text content

        Returns:
            Dictionary with prompt analysis

        """
        analysis = {
            "has_negative_prompt": False,
            "has_parameters": False,
            "positive_prompt": "",
            "negative_prompt": "",
            "parameters": {},
            "style_tags": [],
            "quality_tags": [],
            "subject_tags": [],
        }

        try:
            # Split into sections
            sections = self._split_prompt_sections(content)
            analysis.update(sections)

            # Analyze positive prompt
            if analysis["positive_prompt"]:
                analysis["style_tags"] = self._extract_style_tags(analysis["positive_prompt"])
                analysis["quality_tags"] = self._extract_quality_tags(analysis["positive_prompt"])
                analysis["subject_tags"] = self._extract_subject_tags(analysis["positive_prompt"])

            # Count tags
            analysis["total_tags"] = len(analysis["positive_prompt"].split(","))
            analysis["tag_categories"] = {
                "style": len(analysis["style_tags"]),
                "quality": len(analysis["quality_tags"]),
                "subject": len(analysis["subject_tags"]),
            }

        except Exception as e:
            self.logger.debug(f"Error analyzing AI prompt: {e}")

        return analysis

    def _split_prompt_sections(self, content: str) -> dict[str, Any]:
        """Split prompt content into positive, negative, and parameters."""
        sections = {
            "positive_prompt": "",
            "negative_prompt": "",
            "parameters": {},
            "has_negative_prompt": False,
            "has_parameters": False,
        }

        # Look for negative prompt section
        neg_match = re.search(
            r"negative prompt:\s*(.*?)(?=\n(?:steps:|sampler:|cfg scale:|seed:|model:|$))",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if neg_match:
            sections["negative_prompt"] = neg_match.group(1).strip()
            sections["has_negative_prompt"] = True

            # Positive prompt is everything before negative prompt
            pos_end = neg_match.start()
            sections["positive_prompt"] = content[:pos_end].strip()
        else:
            # Look for parameter section to find end of positive prompt
            param_match = re.search(r"\n(?:steps:|sampler:|cfg scale:|seed:|model:)", content, re.IGNORECASE)
            if param_match:
                sections["positive_prompt"] = content[: param_match.start()].strip()
            else:
                sections["positive_prompt"] = content.strip()

        # Extract parameters
        param_patterns = [
            r"steps:\s*(\d+)",
            r"sampler:\s*([^,\n]+)",
            r"cfg scale:\s*([\d.]+)",
            r"seed:\s*(\d+)",
            r"model:\s*([^,\n]+)",
            r"model hash:\s*([^,\n]+)",
        ]

        for pattern in param_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                param_name = pattern.split(":")[0].replace(r"\s*", " ")
                sections["parameters"][param_name] = match.group(1).strip()
                sections["has_parameters"] = True

        return sections

    def _extract_style_tags(self, prompt: str) -> list[str]:
        """Extract style-related tags from prompt."""
        style_keywords = [
            "anime",
            "manga",
            "realistic",
            "photorealistic",
            "digital art",
            "oil painting",
            "watercolor",
            "sketch",
            "pencil drawing",
            "concept art",
            "illustration",
            "cartoon",
            "comic",
            "pixel art",
            "cyberpunk",
            "steampunk",
            "fantasy",
            "sci-fi",
            "medieval",
            "modern",
            "vintage",
            "retro",
            "futuristic",
            "gothic",
        ]

        found_styles = []
        prompt_lower = prompt.lower()

        for style in style_keywords:
            if style in prompt_lower:
                found_styles.append(style)

        return found_styles

    def _extract_quality_tags(self, prompt: str) -> list[str]:
        """Extract quality-related tags from prompt."""
        quality_keywords = [
            "masterpiece",
            "best quality",
            "high quality",
            "ultra quality",
            "highly detailed",
            "extremely detailed",
            "intricate details",
            "sharp focus",
            "professional",
            "award winning",
            "stunning",
            "beautiful",
            "gorgeous",
            "perfect",
            "flawless",
            "pristine",
            "high resolution",
            "4k",
            "8k",
            "ultra hd",
            "hdr",
        ]

        found_qualities = []
        prompt_lower = prompt.lower()

        for quality in quality_keywords:
            if quality in prompt_lower:
                found_qualities.append(quality)

        return found_qualities

    def _extract_subject_tags(self, prompt: str) -> list[str]:
        """Extract subject-related tags from prompt."""
        subject_keywords = [
            "person",
            "woman",
            "man",
            "girl",
            "boy",
            "child",
            "adult",
            "character",
            "portrait",
            "face",
            "eyes",
            "hair",
            "clothing",
            "landscape",
            "nature",
            "forest",
            "mountain",
            "ocean",
            "sky",
            "building",
            "architecture",
            "city",
            "street",
            "room",
            "interior",
            "animal",
            "cat",
            "dog",
            "bird",
            "horse",
            "dragon",
            "creature",
            "vehicle",
            "car",
            "ship",
            "airplane",
            "motorcycle",
            "robot",
        ]

        found_subjects = []
        prompt_lower = prompt.lower()

        for subject in subject_keywords:
            if subject in prompt_lower:
                found_subjects.append(subject)

        return found_subjects


class PromptFileReader:
    """Specialized reader for AI prompt files.

    This class combines text reading with prompt-specific analysis.
    Perfect for managing your prompt library! 📝✨
    """

    def __init__(self):
        """Initialize the prompt file reader."""
        self.text_reader = TextFileReader()
        self.analyzer = TextContentAnalyzer()
        self.logger = get_logger(f"{__name__}.PromptFileReader")

    def read_prompt_file(self, file_path: str) -> dict[str, Any] | None:
        """Read and analyze a prompt file.

        Args:
            file_path: Path to the prompt file

        Returns:
            Dictionary with prompt data and analysis

        """
        # First read the file as text
        text_data = self.text_reader.read_file(file_path)
        if not text_data:
            return None

        content = text_data[UpField.TEXT_DATA.value]

        # Check if it's likely a prompt
        if not text_data.get("appears_to_be_prompt", False):
            self.logger.debug(f"File doesn't appear to be an AI prompt: {file_path}")
            return text_data

        # Analyze as AI prompt
        prompt_analysis = self.analyzer.analyze_ai_prompt(content)

        # Combine text data with prompt analysis
        result = text_data.copy()
        result["prompt_analysis"] = prompt_analysis
        result["content_type"] = "ai_prompt"

        return result

    def extract_prompt_summary(self, file_path: str) -> dict[str, Any]:
        """Extract a summary of a prompt file.

        Args:
            file_path: Path to the prompt file

        Returns:
            Dictionary with prompt summary

        """
        data = self.read_prompt_file(file_path)
        if not data:
            return {"error": "Could not read file"}

        summary = {
            "file_name": Path(file_path).name,
            "file_size": data.get("file_size", 0),
            "is_prompt": data.get("appears_to_be_prompt", False),
            "has_negative": False,
            "has_parameters": False,
            "tag_count": 0,
            "preview": "",
        }

        # Add prompt-specific summary if available
        if "prompt_analysis" in data:
            analysis = data["prompt_analysis"]
            summary.update(
                {
                    "has_negative": analysis.get("has_negative_prompt", False),
                    "has_parameters": analysis.get("has_parameters", False),
                    "tag_count": analysis.get("total_tags", 0),
                    "style_count": len(analysis.get("style_tags", [])),
                    "quality_count": len(analysis.get("quality_tags", [])),
                }
            )

            # Create preview from positive prompt
            positive = analysis.get("positive_prompt", "")
            if positive:
                # Take first 100 characters
                summary["preview"] = positive[:100] + "..." if len(positive) > 100 else positive

        return summary


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def read_text_file(file_path: str) -> dict[str, Any] | None:
    """Convenience function to read a text file.

    Args:
        file_path: Path to the text file

    Returns:
        Dictionary with file content and analysis

    """
    reader = TextFileReader()
    return reader.read_file(file_path)


def read_prompt_file(file_path: str) -> dict[str, Any] | None:
    """Convenience function to read and analyze a prompt file.

    Args:
        file_path: Path to the prompt file

    Returns:
        Dictionary with prompt data and analysis

    """
    reader = PromptFileReader()
    return reader.read_prompt_file(file_path)


def analyze_prompt_content(content: str) -> dict[str, Any]:
    """Convenience function to analyze prompt content.

    Args:
        content: Prompt text content

    Returns:
        Dictionary with prompt analysis

    """
    analyzer = TextContentAnalyzer()
    return analyzer.analyze_ai_prompt(content)


# ============================================================================
# TESTING UTILITIES
# ============================================================================


def test_text_file_reader():
    """Test the text file reader with sample content."""
    logger = get_logger("TextFileReaderTest")

    reader = TextFileReader()
    prompt_reader = PromptFileReader()

    logger.info("Testing TextFileReader...")
    logger.info(f"Supported formats: {reader.get_supported_formats()}")

    # Test with sample content
    test_content = """masterpiece, best quality, 1girl, anime, beautiful detailed eyes, long hair, school uniform, cherry blossoms, spring, soft lighting, photorealistic
Negative prompt: ugly, blurry, bad anatomy, extra limbs, low quality, worst quality
Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 12345, Model: animefull-final-pruned"""

    # Create a temporary test file
    test_file = Path("temp_test_prompt.txt")
    try:
        test_file.write_text(test_content, encoding="utf-8")

        logger.info(f"\nTesting with temporary file: {test_file}")

        # Test basic text reading
        text_result = reader.read_file(str(test_file))
        if text_result:
            logger.info("Basic text reading successful")
            logger.info(f"Detected content type: {text_result.get('content_type')}")
            logger.info(f"Appears to be prompt: {text_result.get('appears_to_be_prompt')}")
            logger.info(f"Character count: {text_result.get('character_count')}")
            logger.info(f"Word count: {text_result.get('word_count')}")

        # Test prompt-specific reading
        prompt_result = prompt_reader.read_prompt_file(str(test_file))
        if prompt_result and "prompt_analysis" in prompt_result:
            analysis = prompt_result["prompt_analysis"]
            logger.info("\nPrompt analysis:")
            logger.info(f"Has negative prompt: {analysis.get('has_negative_prompt')}")
            logger.info(f"Has parameters: {analysis.get('has_parameters')}")
            logger.info(f"Total tags: {analysis.get('total_tags')}")
            logger.info(f"Style tags: {analysis.get('style_tags')}")
            logger.info(f"Quality tags: {analysis.get('quality_tags')}")

        # Test prompt summary
        summary = prompt_reader.extract_prompt_summary(str(test_file))
        logger.info(f"\nPrompt summary: {summary}")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()

    logger.info("TextFileReader test completed!")


if __name__ == "__main__":
    # Run tests if module is executed directly
    test_text_file_reader()
