# dataset_tools/file_operations.py

"""File operations and scanning utilities.

This module handles all file system operations, directory scanning,
and file categorization. Think of it as your inventory management
system in FFXIV - it knows where everything is and what type it is! 📦✨
"""

import os
from pathlib import Path
from typing import NamedTuple

from .correct_types import ExtensionType as Ext
from .logger import debug_monitor, get_logger

log = get_logger(__name__)


class FileScanResult(NamedTuple):
    """Result of scanning a directory for files.

    This is like your loot summary after a dungeon run! 🎁
    """

    images: list[str]
    texts: list[str]
    models: list[str]
    folder_path: str
    total_files: int
    scan_duration: float = 0.0
    scan_success: bool
    error_message: str | None = None


class FileExtensionCategories:
    """Manages file extension categorization.

    This class knows which file extensions belong to which categories,
    making it easy to classify files. Like having a well-organized
    retainer with everything in the right section! 🗃️
    """

    def __init__(self):
        """Initialize the categorizer with extension data."""
        self.logger = get_logger(f"{__name__}.FileExtensionCategories")
        self._image_extensions: set[str] | None = None
        self._text_extensions: set[str] | None = None
        self._model_extensions: set[str] | None = None
        self._ignore_list: list[str] | None = None

        # Debug extension loading if requested
        if os.getenv("DEBUG_WIDGETS_EXT"):
            self._debug_extension_types()

    @property
    def image_extensions(self) -> set[str]:
        """Get all image file extensions (cached)."""
        if self._image_extensions is None:
            self._image_extensions = self._load_image_extensions()
        return self._image_extensions

    @property
    def text_extensions(self) -> set[str]:
        """Get all text-like file extensions (cached)."""
        if self._text_extensions is None:
            self._text_extensions = self._load_text_extensions()
        return self._text_extensions

    @property
    def model_extensions(self) -> set[str]:
        """Get all model file extensions (cached)."""
        if self._model_extensions is None:
            self._model_extensions = self._load_model_extensions()
        return self._model_extensions

    @property
    def ignore_list(self) -> list[str]:
        """Get list of files to ignore (cached)."""
        if self._ignore_list is None:
            self._ignore_list = self._load_ignore_list()
        return self._ignore_list

    def _load_image_extensions(self) -> set[str]:
        """Load image extensions from the extension type configuration."""
        try:
            return {ext for ext_set in getattr(Ext, "IMAGE", []) for ext in ext_set}
        except Exception as e:
            self.logger.warning("Error loading image extensions: %s", e)
            return {
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".webp",
                ".tiff",
                ".tif",
            }  # Fallback

    def _load_text_extensions(self) -> set[str]:
        """Load text and schema file extensions."""
        text_exts = set()

        # Load plain text extensions
        if hasattr(Ext, "PLAIN_TEXT_LIKE"):
            try:
                for ext_set in Ext.PLAIN_TEXT_LIKE:
                    text_exts.update(ext_set)
            except Exception as e:
                self.logger.warning("Error loading PLAIN_TEXT_LIKE extensions: %s", e)

        # Load schema file extensions
        if hasattr(Ext, "SCHEMA_FILES"):
            try:
                schema_exts = {ext for ext_set in Ext.SCHEMA_FILES for ext in ext_set}
                text_exts.update(schema_exts)
            except Exception as e:
                self.logger.warning("Error loading SCHEMA_FILES extensions: %s", e)

        # Fallback if nothing loaded
        if not text_exts:
            text_exts = {".txt", ".json", ".yaml", ".yml", ".xml", ".csv"}

        return text_exts

    def _load_model_extensions(self) -> set[str]:
        """Load model file extensions."""
        try:
            if hasattr(Ext, "MODEL_FILES"):
                return {ext for ext_set in Ext.MODEL_FILES for ext in ext_set}
            self.logger.warning("MODEL_FILES attribute not found")
            return {
                ".ckpt",
                ".safetensors",
                ".pt",
                ".pth",
                ".gguf",
                ".bin",
            }  # Fallback
        except Exception as e:
            self.logger.warning("Error loading model extensions: %s", e)
            return {".ckpt", ".safetensors", ".pt", ".pth", ".gguf", ".bin"}  # Fallback

    def _load_ignore_list(self) -> list[str]:
        """Load list of files to ignore."""
        try:
            ignore_list = getattr(Ext, "IGNORE", [])
            if not isinstance(ignore_list, list):
                self.logger.warning("IGNORE attribute is not a list, using empty list")
                return []
            return ignore_list
        except Exception as e:
            self.logger.warning("Error loading ignore list: %s", e)
            return []

    def categorize_file(self, file_path: str) -> str | None:
        """Categorize a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            Category name ('image', 'text', 'model') or None if not categorized

        """
        try:
            path = Path(file_path)

            # Check if file should be ignored
            if path.name in self.ignore_list:
                return None

            suffix = path.suffix.lower()

            if suffix in self.image_extensions:
                return "image"
            if suffix in self.text_extensions:
                return "text"
            if suffix in self.model_extensions:
                return "model"
            return None

        except Exception as e:
            self.logger.debug("Error categorizing file '%s': %s", file_path, e)
            return None

    def _debug_extension_types(self) -> None:
        """Debug output for extension type inspection."""
        self.logger.debug("--- DEBUG WIDGETS: Inspecting Ext (ExtensionType) ---")
        self.logger.debug("Type of Ext: %s", type(Ext))

        expected_attrs = [
            "IMAGE",
            "SCHEMA_FILES",
            "MODEL_FILES",
            "PLAIN_TEXT_LIKE",
            "IGNORE",
        ]

        for attr_name in expected_attrs:
            has_attr = hasattr(Ext, attr_name)
            val_str = str(getattr(Ext, attr_name, "N/A"))
            val_display = val_str[:70] + "..." if len(val_str) > 70 else val_str

            self.logger.debug("Ext.%s? %s. Value (first 70 chars): %s", attr_name, has_attr, val_display,)

        self.logger.debug("--- END DEBUG WIDGETS ---")


class DirectoryScanner:
    """Scans directories and categorizes files.

    This is your exploration class - it goes into new areas and
    maps out what's available! 🗺️⚔️
    """

    def __init__(self, categorizer: FileExtensionCategories | None = None):
        """Initialize the directory scanner.

        Args:
            categorizer: File extension categorizer to use

        """
        self.logger = get_logger(f"{__name__}.DirectoryScanner")
        self.categorizer = categorizer or FileExtensionCategories()

    @debug_monitor
    def scan_directory(self, folder_path: str) -> FileScanResult:
        """Scan a directory and categorize all files.

        Args:
            folder_path: Path to the directory to scan

        Returns:
            FileScanResult with categorized files

        """
        self.logger.info("Starting directory scan: %s", folder_path)

        try:
            # Get all items in the directory
            items = self._get_directory_items(folder_path)
            if items is None:
                return FileScanResult(
                    images=[],
                    texts=[],
                    models=[],
                    folder_path=folder_path,
                    total_files=0,
                    scan_success=False,
                    error_message="Could not read directory",
                )

            # Categorize the files
            images, texts, models, total_files = self._categorize_files(items, folder_path)

            self.logger.info(
                "Scan completed for %s: %d images, %d texts, %d models", folder_path, len(images), len(texts), len(models)
            )

            return FileScanResult(
                images=sorted(images),
                texts=sorted(texts),
                models=sorted(models),
                folder_path=folder_path,
                total_files=total_files,
                scan_success=True,
            )

        except Exception as e:
            self.logger.error(
                "Unexpected error scanning directory '%s': %s", folder_path, e, exc_info=True
            )
            return FileScanResult(
                images=[],
                texts=[],
                models=[],
                folder_path=folder_path,
                total_files=0,
                scan_success=False,
                error_message=f"Scan error: {e!s}",
            )

    def _get_directory_items(self, folder_path: str) -> list[str] | None:
        """Get all items in a directory.

        Args:
            folder_path: Path to the directory

        Returns:
            List of full paths to items, or None if error

        """
        try:
            items_in_folder = os.listdir(folder_path)
            full_paths = [os.path.join(folder_path, item) for item in items_in_folder]
            self.logger.debug("Found %d items in directory", len(full_paths))
            return full_paths

        except FileNotFoundError:
            self.logger.warning("Directory not found: %s", folder_path)
            return None
        except PermissionError:
            self.logger.warning("Permission denied accessing directory: %s", folder_path)
            return None
        except OSError as e:
            self.logger.warning("OS error accessing directory '%s': %s", folder_path, e)
            return None

    def _categorize_files(self, item_paths: list[str], folder_path: str) -> tuple[list[str], list[str], list[str], int]:
        """Categorize a list of file paths.

        Args:
            item_paths: List of full paths to categorize
            folder_path: Base folder path for logging

        Returns:
            Tuple of (images, texts, models, total_files)

        """
        images = []
        texts = []
        models = []
        total_files = 0

        for item_path in item_paths:
            try:
                path = Path(item_path)

                # Only process actual files
                if not path.is_file():
                    continue

                total_files += 1
                file_name = path.name

                # Categorize the file
                category = self.categorizer.categorize_file(item_path)

                if category == "image":
                    images.append(file_name)
                elif category == "text":
                    texts.append(file_name)
                elif category == "model":
                    models.append(file_name)
                # Files that don't match any category are ignored

            except (OSError, ValueError, TypeError, AttributeError) as e:
                self.logger.debug("Error processing item '%s': %s", item_path, e)
            except Exception as e:
                self.logger.warning("Unexpected error processing item '%s': %s", item_path, e)

        return images, texts, models, total_files


class FileOperations:
    """High-level file operations interface.

    This is your main class that combines scanning and categorization
    into a simple, easy-to-use interface. Like your main job that
    uses abilities from different skill trees! ⚔️✨
    """

    def __init__(self):
        """Initialize file operations."""
        self.logger = get_logger(f"{__name__}.FileOperations")
        self.categorizer = FileExtensionCategories()
        self.scanner = DirectoryScanner(self.categorizer)

    def scan_folder(self, folder_path: str) -> FileScanResult:
        """Scan a folder and return categorized file lists.

        Args:
            folder_path: Path to the folder to scan

        Returns:
            FileScanResult with categorized files

        """
        return self.scanner.scan_directory(folder_path)

    def is_image_file(self, file_path: str) -> bool:
        """Check if a file is an image.

        Args:
            file_path: Path to the file

        Returns:
            True if the file is an image

        """
        return self.categorizer.categorize_file(file_path) == "image"

    def is_text_file(self, file_path: str) -> bool:
        """Check if a file is a text file.

        Args:
            file_path: Path to the file

        Returns:
            True if the file is a text file

        """
        return self.categorizer.categorize_file(file_path) == "text"

    def is_model_file(self, file_path: str) -> bool:
        """Check if a file is a model file.

        Args:
            file_path: Path to the file

        Returns:
            True if the file is a model file

        """
        return self.categorizer.categorize_file(file_path) == "model"

    def get_supported_extensions(self) -> dict[str, set[str]]:
        """Get all supported file extensions by category.

        Returns:
            Dictionary mapping category names to extension sets

        """
        return {
            "image": self.categorizer.image_extensions,
            "text": self.categorizer.text_extensions,
            "model": self.categorizer.model_extensions,
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def scan_folder_for_files(folder_path: str) -> FileScanResult:
    """Convenience function to scan a folder.

    Args:
        folder_path: Path to folder to scan

    Returns:
        FileScanResult with categorized files

    """
    operations = FileOperations()
    return operations.scan_folder(folder_path)


def categorize_file_by_extension(file_path: str) -> str | None:
    """Convenience function to categorize a single file.

    Args:
        file_path: Path to the file

    Returns:
        Category name or None

    """
    categorizer = FileExtensionCategories()
    return categorizer.categorize_file(file_path)


# ============================================================================
# TESTING UTILITIES
# ============================================================================


def test_file_operations():
    """Test the file operations system."""
    logger = get_logger("FileOperationsTest")

    # Test categorizer
    logger.info("Testing FileExtensionCategories...")
    categorizer = FileExtensionCategories()

    test_files = [
        "image.jpg",
        "photo.PNG",
        "document.txt",
        "data.json",
        "model.safetensors",
        "checkpoint.ckpt",
        "unknown.xyz",
    ]

    for test_file in test_files:
        category = categorizer.categorize_file(test_file)
        logger.info("%s: %s", test_file, category or "UNCATEGORIZED")

    # Test supported extensions
    logger.info("Supported extensions:")
    operations = FileOperations()
    extensions = operations.get_supported_extensions()

    for category, exts in extensions.items():
        logger.info("%s: %s", category.upper(), sorted(list(exts)))

    logger.info("File operations test completed!")


if __name__ == "__main__":
    # Run tests if module is executed directly
    test_file_operations()
