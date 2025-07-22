# dataset_tools/file_readers/__init__.py

"""File reader factory and main interface.

This module provides a unified interface for reading different types of files
by coordinating the specialized readers.
It includes:
- FileReaderFactory: Main factory class that determines which reader to use
- Specialized readers for images, text files, prompts, and schema files
- FileReaderManager: High-level manager for batch reading and caching
Public API:
- read_file_metadata(file_path) - Main function to read any supported file
- FileReaderFactory - Main factory class
- Individual reader classes for advanced usage
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from ..correct_types import EmptyField
from ..correct_types import ExtensionType as Ext
from ..logger import debug_monitor, get_logger
from ..logger import info_monitor as nfo
from .image_metadata_reader import ImageMetadataExtractor, ImageMetadataReader
from .schema_file_reader import SchemaFileReader, StructuredDataAnalyzer
from .text_file_reader import PromptFileReader, TextContentAnalyzer, TextFileReader


class FileReaderFactory:
    """Factory class that coordinates different file readers.

    This class determines which specialized reader to use for each file
    and provides a unified interface for file reading operations.
    """

    def __init__(self):
        """Initialize the file reader factory."""
        self.logger = get_logger(f"{__name__}.FileReaderFactory")

        # Initialize specialized readers
        self.image_reader = ImageMetadataReader()
        self.text_reader = TextFileReader()
        self.prompt_reader = PromptFileReader()
        self.schema_reader = SchemaFileReader()

        # Initialize analyzers
        self.image_extractor = ImageMetadataExtractor(self.image_reader)
        self.text_analyzer = TextContentAnalyzer()
        self.data_analyzer = StructuredDataAnalyzer()

        self.logger.info("FileReaderFactory initialized with all specialized readers")

    @debug_monitor
    def read_file(self, file_path: str) -> dict[str, Any] | None:
        """Read a file using the appropriate specialized reader.

        Args:
            file_path: Path to the file to read

        Returns:
            Dictionary containing file data and metadata, or None if reading failed

        """
        if not file_path:
            self.logger.warning("Empty file path provided")
            return None

        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            self.logger.warning("File does not exist: %s", file_path)
            return self._create_error_result(f"File not found: {file_path_obj.name}")

        if not file_path_obj.is_file():
            self.logger.warning("Path is not a file: %s", file_path)
            return self._create_error_result(f"Not a file: {file_path_obj.name}")

        nfo("[FileReaderFactory] Reading file: %s", file_path_obj.name)

        # Determine file type and dispatch to appropriate reader
        reader_type = self._determine_reader_type(file_path)

        try:
            if reader_type == "image":
                return self._read_image_file(file_path)
            if reader_type == "text":
                return self._read_text_file(file_path)
            if reader_type == "prompt":
                return self._read_prompt_file(file_path)
            if reader_type == "schema":
                return self._read_schema_file(file_path)
            if reader_type == "model":
                return self._read_model_file(file_path)
            return self._create_error_result(f"Unsupported file type: {file_path_obj.suffix}")

        except Exception as e:
            self.logger.error("Error reading file %s: %s", file_path, e)
            return self._create_error_result(f"Error reading file: {e!s}")

    def _determine_reader_type(self, file_path: str) -> str:
        """Determine which reader type should handle this file.

        Args:
            file_path: Path to the file

        Returns:
            Reader type string

        """
        file_path_obj = Path(file_path)
        suffix = file_path_obj.suffix.lower()

        # Check against extension configurations
        if self._is_extension_in_group(suffix, "IMAGE"):
            return "image"
        if self._is_extension_in_group(suffix, "SCHEMA_FILES"):
            return "schema"
        if self._is_extension_in_group(suffix, "MODEL_FILES"):
            return "model"
        if self._is_extension_in_group(suffix, "PLAIN_TEXT_LIKE"):
            # Check if it might be a prompt file
            if self._might_be_prompt_file(file_path):
                return "prompt"
            return "text"
        # Try to guess based on file extension
        if suffix in {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
            ".tiff",
            ".tif",
        }:
            return "image"
        if suffix in {".json", ".toml", ".yaml", ".yml", ".xml"}:
            return "schema"
        if suffix in {".txt", ".md", ".markdown", ".rst"}:
            return "text"
        if suffix in {".ckpt", ".safetensors", ".pt", ".pth", ".gguf", ".bin"}:
            return "model"
        return "unknown"

    def _is_extension_in_group(self, extension: str, group_name: str) -> bool:
        """Check if an extension is in a specific ExtensionType group."""
        try:
            group = getattr(Ext, group_name, None)
            if group is None:
                return False

            # Handle both list of sets and single set formats
            if isinstance(group, list):
                return any(extension in ext_set for ext_set in group)
            return extension in group

        except Exception as e:
            self.logger.debug("Error checking extension group %s: %s", group_name, e)
            return False

    def _might_be_prompt_file(self, file_path: str) -> bool:
        """Quick check if a text file might be an AI prompt.

        Args:
            file_path: Path to the file

        Returns:
            True if file might be a prompt

        """
        try:
            # Quick content check - read first few lines
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                first_lines = f.read(500).lower()  # First 500 characters

            prompt_indicators = [
                "masterpiece",
                "best quality",
                "negative prompt:",
                "steps:",
                "sampler:",
                "cfg scale:",
                "detailed",
            ]

            return any(indicator in first_lines for indicator in prompt_indicators)

        except Exception:
            return False

    def _read_image_file(self, file_path: str) -> dict[str, Any] | None:
        """Read an image file."""
        nfo("[FileReaderFactory] Using image reader for: %s", Path(file_path).name)

        result = self.image_reader.read_metadata(file_path)
        if result is None:
            return self._create_error_result("Could not read image metadata")

        # Add additional analysis
        basic_info = self.image_extractor.extract_basic_info(file_path)
        ai_params = self.image_extractor.extract_ai_generation_data(file_path)

        enhanced_result = {
            **result,
            "reader_type": "image",
            "basic_info": basic_info,
        }

        if ai_params:
            enhanced_result["ai_generation_parameters"] = ai_params

        return enhanced_result

    def _read_text_file(self, file_path: str) -> dict[str, Any] | None:
        """Read a text file."""
        nfo("[FileReaderFactory] Using text reader for: %s", Path(file_path).name)

        result = self.text_reader.read_file(file_path)
        if result is None:
            return self._create_error_result("Could not read text file")

        result["reader_type"] = "text"
        return result

    def _read_prompt_file(self, file_path: str) -> dict[str, Any] | None:
        """Read a prompt file."""
        nfo("[FileReaderFactory] Using prompt reader for: %s", Path(file_path).name)

        result = self.prompt_reader.read_prompt_file(file_path)
        if result is None:
            return self._create_error_result("Could not read prompt file")

        result["reader_type"] = "prompt"
        return result

    def _read_schema_file(self, file_path: str) -> dict[str, Any] | None:
        """Read a schema file."""
        nfo("[FileReaderFactory] Using schema reader for: %s", Path(file_path).name)

        result = self.schema_reader.read_file(file_path)
        if result is None:
            return self._create_error_result("Could not read schema file")

        # Add ComfyUI workflow analysis if applicable
        if result.get("appears_to_be_workflow"):
            workflow_data = None
            for key, value in result.items():
                if key.endswith("_DATA") and isinstance(value, dict):
                    workflow_data = value
                    break

            if workflow_data:
                workflow_analysis = self.data_analyzer.analyze_comfyui_workflow(workflow_data)
                result["workflow_analysis"] = workflow_analysis

        result["reader_type"] = "schema"
        return result

    def _read_model_file(self, file_path: str) -> dict[str, Any] | None:
        """Read a model file."""
        nfo(
            "[FileReaderFactory] Attempting to read model file: %s",
            Path(file_path).name,
        )

        # Try to import and use ModelTool
        try:
            from ..model_tool import ModelTool

            tool = ModelTool()
            result = tool.read_metadata_from(file_path)

            if result:
                result["reader_type"] = "model"
                return result
            return self._create_error_result("ModelTool could not read file")

        except ImportError:
            self.logger.warning("ModelTool not available for model file reading")
            return self._create_error_result("ModelTool not available")
        except Exception as e:
            self.logger.error("Error using ModelTool: %s", e)
            return self._create_error_result(f"ModelTool error: {e!s}")

    def _create_error_result(self, error_message: str) -> dict[str, Any]:
        """Create a standardized error result."""
        return {
            EmptyField.PLACEHOLDER.value: {"Error": error_message},
            "reader_type": "error",
            "reading_success": False,
        }

    def get_supported_formats(self) -> dict[str, list[str]]:
        """Get all supported file formats by reader type.

        Returns:
            Dictionary mapping reader types to supported extensions

        """
        return {
            "image": list(self.image_reader.get_supported_formats()),
            "text": list(self.text_reader.get_supported_formats()),
            "schema": list(self.schema_reader.get_supported_formats()),
        }

    def can_read_file(self, file_path: str) -> bool:
        """Check if the factory can read a given file.

        Args:
            file_path: Path to the file

        Returns:
            True if any reader can handle this file

        """
        reader_type = self._determine_reader_type(file_path)
        return reader_type != "unknown"


class FileReaderManager:
    """High-level manager for file reading operations.

    This class provides additional functionality like batch reading,
    caching, and result filtering. Like your squadron leader who
    coordinates multiple operations! 👥✨
    """

    def __init__(self, factory: FileReaderFactory | None = None):
        """Initialize the file reader manager.

        Args:
            factory: FileReaderFactory instance to use

        """
        self.factory = factory or FileReaderFactory()
        self.logger = get_logger(f"{__name__}.FileReaderManager")

        # Simple cache for recently read files
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_max_size = 50

    def read_file(self, file_path: str, use_cache: bool = True) -> dict[str, Any] | None:
        """Read a file with optional caching.

        Args:
            file_path: Path to the file
            use_cache: Whether to use cached results

        Returns:
            File data dictionary or None

        """
        # Check cache first
        if use_cache and file_path in self._cache:
            self.logger.debug("Returning cached result for: %s", Path(file_path).name)
            return self._cache[file_path]

        # Read the file
        result = self.factory.read_file(file_path)

        # Cache successful results
        if use_cache and result and result.get("reading_success", True):
            self._add_to_cache(file_path, result)

        return result

    def read_multiple_files(self, file_paths: list[str], use_cache: bool = True) -> dict[str, dict[str, Any] | None]:
        """Read multiple files.

        Args:
            file_paths: List of file paths to read
            use_cache: Whether to use cached results

        Returns:
            Dictionary mapping file paths to results

        """
        results = {}

        for file_path in file_paths:
            try:
                result = self.read_file(file_path, use_cache)
                results[file_path] = result
            except Exception as e:
                self.logger.error("Error reading %s: %s", file_path, e)
                results[file_path] = self.factory._create_error_result(str(e))

        return results

    def filter_by_reader_type(self, results: dict[str, dict[str, Any]], reader_type: str) -> dict[str, dict[str, Any]]:
        """Filter results by reader type.

        Args:
            results: Dictionary of file reading results
            reader_type: Reader type to filter by

        Returns:
            Filtered results dictionary

        """
        return {path: result for path, result in results.items() if result and result.get("reader_type") == reader_type}

    def get_reading_summary(self, results: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Get a summary of reading results.

        Args:
            results: Dictionary of file reading results

        Returns:
            Summary dictionary

        """
        summary = {
            "total_files": len(results),
            "successful_reads": 0,
            "failed_reads": 0,
            "reader_type_counts": {},
            "error_types": {},
        }

        for result in results.values():
            if not result:
                summary["failed_reads"] += 1
                continue

            if result.get("reading_success", True):
                summary["successful_reads"] += 1

                # Count by reader type
                reader_type = result.get("reader_type", "unknown")
                summary["reader_type_counts"][reader_type] = summary["reader_type_counts"].get(reader_type, 0) + 1
            else:
                summary["failed_reads"] += 1

                # Count error types
                error = result.get(EmptyField.PLACEHOLDER.value, {}).get("Error", "Unknown error")
                summary["error_types"][error] = summary["error_types"].get(error, 0) + 1

        return summary

    def _add_to_cache(self, file_path: str, result: dict[str, Any]) -> None:
        """Add result to cache with size management."""
        # Remove oldest entries if cache is full
        if len(self._cache) >= self._cache_max_size:
            # Remove first (oldest) entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[file_path] = result

    def clear_cache(self) -> None:
        """Clear the file reading cache."""
        self._cache.clear()
        self.logger.debug("File reading cache cleared")

    def get_cache_info(self) -> dict[str, Any]:
        """Get information about the current cache state."""
        return {
            "cached_files": len(self._cache),
            "max_cache_size": self._cache_max_size,
            "cached_file_names": [Path(path).name for path in self._cache.keys()],
        }


# ============================================================================
# MAIN PUBLIC API
# ============================================================================

# Global factory instance for convenience functions
_default_factory = None
_default_manager = None


def get_default_factory() -> FileReaderFactory:
    """Get the default factory instance."""
    global _default_factory
    if _default_factory is None:
        _default_factory = FileReaderFactory()
    return _default_factory


def get_default_manager() -> FileReaderManager:
    """Get the default manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = FileReaderManager(get_default_factory())
    return _default_manager


def read_file_metadata(file_path: str) -> dict[str, Any] | None:
    """Main convenience function to read any supported file.

    This is the primary public API function that most users should use.

    Args:
        file_path: Path to the file to read

    Returns:
        Dictionary containing file data and metadata, or None if reading failed

    """
    return get_default_factory().read_file(file_path)


def read_multiple_files(file_paths: list[str]) -> dict[str, dict[str, Any] | None]:
    """Convenience function to read multiple files.

    Args:
        file_paths: List of file paths to read

    Returns:
        Dictionary mapping file paths to results

    """
    return get_default_manager().read_multiple_files(file_paths)


def get_supported_formats() -> dict[str, list[str]]:
    """Get all supported file formats.

    Returns:
        Dictionary mapping reader types to supported extensions

    """
    return get_default_factory().get_supported_formats()


# ============================================================================
# TESTING UTILITIES
# ============================================================================


def test_file_reader_factory():
    """Test the file reader factory with various file types."""
    logger = get_logger("FileReaderFactoryTest")

    factory = FileReaderFactory()
    manager = FileReaderManager(factory)

    logger.info("Testing FileReaderFactory...")

    # Show supported formats
    formats = factory.get_supported_formats()
    logger.info("Supported formats:")
    for reader_type, extensions in formats.items():
        logger.info("  %s: %s", reader_type, extensions)

    # Test with sample files (if they exist)
    test_files = [
        "test_image.jpg",
        "test_image.png",
        "test_text.txt",
        "test_prompt.txt",
        "test_config.json",
        "test_workflow.json",
    ]

    existing_files = [f for f in test_files if Path(f).exists()]

    if existing_files:
        logger.info("Testing with existing files: %s", existing_files)

        # Test single file reading
        for file_path in existing_files:
            logger.info("Reading: %s", file_path)
            result = factory.read_file(file_path)

            if result:
                logger.info("  Reader type: %s", result.get("reader_type"))
                logger.info("  Success: %s", result.get("reading_success", True))

                if "basic_info" in result:
                    info = result["basic_info"]
                    logger.info("  File size: %s bytes", info.get("file_size"))
                    if "image_size" in info:
                        logger.info("  Image size: %s", info["image_size"])
            else:
                logger.info("  Reading failed")

        # Test batch reading
        logger.info("\nTesting batch reading of %d files...", len(existing_files))
        batch_results = manager.read_multiple_files(existing_files)
        summary = manager.get_reading_summary(batch_results)

        logger.info("Batch reading summary: %s", summary)

        # Test cache
        cache_info = manager.get_cache_info()
        logger.info("Cache info: %s", cache_info)

    else:
        logger.info("No test files found - skipping file reading tests")
        logger.info("Create test files to run full tests:")
        for test_file in test_files:
            logger.info("  %s", test_file)

    logger.info("FileReaderFactory test completed!")


if __name__ == "__main__":
    # Run tests if module is executed directly
    test_file_reader_factory()
