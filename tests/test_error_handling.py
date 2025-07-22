# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""Error handling and edge case tests for metadata parser"""

import os
import tempfile
from pathlib import Path

from dataset_tools.metadata_parser import parse_metadata

# Get the directory of the current test file
TEST_DIR = Path(__file__).parent
DATA_DIR = TEST_DIR / "data"


def test_corrupted_json_file():
    """Test that the parser gracefully handles corrupted JSON files."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"invalid": json content without closing brace')
        corrupted_json_path = f.name

    try:
        metadata = parse_metadata(corrupted_json_path)
        # Should not crash, should return some result (even if minimal)
        assert metadata is not None
        assert isinstance(metadata, dict)
        # Should have some basic structure even if parsing failed
        assert "metadata_info_section" in metadata or "unclassified" in metadata or "info" in metadata
    finally:
        os.unlink(corrupted_json_path)


def test_empty_file():
    """Test that the parser handles completely empty files."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".png", delete=False) as f:
        f.write("")  # Empty file
        empty_file_path = f.name

    try:
        metadata = parse_metadata(empty_file_path)
        # Should not crash
        assert metadata is not None
        assert isinstance(metadata, dict)
    finally:
        os.unlink(empty_file_path)


def test_binary_garbage_file():
    """Test that the parser handles files with random binary data."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False) as f:
        f.write(b"\x00\x01\x02\x03\xff\xfe\xfd\x12\x34\x56\x78\x9a\xbc\xde\xf0")
        garbage_file_path = f.name

    try:
        metadata = parse_metadata(garbage_file_path)
        # Should not crash
        assert metadata is not None
        assert isinstance(metadata, dict)
    finally:
        os.unlink(garbage_file_path)


def test_very_large_fake_metadata():
    """Test that the parser handles unreasonably large metadata."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        # Create a large but valid JSON with lots of nodes
        large_json = {
            "nodes": {str(i): {"class_type": f"TestNode{i}", "widgets_values": ["test"] * 100} for i in range(1000)},
            "links": [[i, i + 1, 0, i + 2, 0] for i in range(999)],
            "version": 0.4,
        }
        import json

        json.dump(large_json, f)
        large_file_path = f.name

    try:
        metadata = parse_metadata(large_file_path)
        # Should not crash even with large files
        assert metadata is not None
        assert isinstance(metadata, dict)
    finally:
        os.unlink(large_file_path)


def test_malformed_image_with_text():
    """Test parsing a file with image extension but text content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".png", delete=False) as f:
        f.write("This is not actually an image file, just text pretending to be one!")
        fake_image_path = f.name

    try:
        metadata = parse_metadata(fake_image_path)
        # Should not crash
        assert metadata is not None
        assert isinstance(metadata, dict)
    finally:
        os.unlink(fake_image_path)


def test_nonexistent_file():
    """Test that the parser handles requests for non-existent files."""
    nonexistent_path = "/this/path/definitely/does/not/exist.png"

    # Should either return None/empty dict or raise a specific exception
    try:
        metadata = parse_metadata(nonexistent_path)
        if metadata is not None:
            assert isinstance(metadata, dict)
    except (FileNotFoundError, OSError):
        # These exceptions are acceptable for non-existent files
        pass


def test_permission_denied_file():
    """Test handling of files that exist but can't be read due to permissions."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".png", delete=False) as f:
        f.write("test content")
        restricted_file_path = f.name

    try:
        # Make file unreadable
        os.chmod(restricted_file_path, 0o000)

        # Should handle permission errors gracefully
        try:
            metadata = parse_metadata(restricted_file_path)
            if metadata is not None:
                assert isinstance(metadata, dict)
        except (PermissionError, OSError):
            # These exceptions are acceptable for permission issues
            pass

    finally:
        # Restore permissions and clean up
        try:
            os.chmod(restricted_file_path, 0o644)
            os.unlink(restricted_file_path)
        except:
            pass  # File might already be cleaned up


def test_extremely_long_filename():
    """Test that extremely long filenames don't break the parser."""
    long_name = "a" * 200 + ".json"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"test": "content"}')
        temp_path = f.name

    try:
        # Try to create a file with very long name in temp directory
        long_path = os.path.join(os.path.dirname(temp_path), long_name)
        try:
            os.rename(temp_path, long_path)
            metadata = parse_metadata(long_path)
            assert metadata is not None
            assert isinstance(metadata, dict)
            os.unlink(long_path)
        except OSError:
            # If OS doesn't support long filenames, that's fine
            os.unlink(temp_path)
    except:
        # Clean up in case of any issues
        try:
            os.unlink(temp_path)
        except:
            pass


def test_unicode_filename():
    """Test that unicode characters in filenames are handled properly."""
    unicode_content = '{"test": "unicode_test", "emoji": "🎯🚀😅"}'

    with tempfile.NamedTemporaryFile(mode="w", suffix="_🎯test🚀.json", delete=False, encoding="utf-8") as f:
        f.write(unicode_content)
        unicode_file_path = f.name

    try:
        metadata = parse_metadata(unicode_file_path)
        # Should handle unicode filenames without issues
        assert metadata is not None
        assert isinstance(metadata, dict)
    finally:
        try:
            os.unlink(unicode_file_path)
        except:
            pass


def test_recursive_json_structure():
    """Test that deeply nested or circular JSON structures don't cause infinite loops."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        # Create deeply nested structure
        nested_json = {"level": 0}
        current = nested_json
        for i in range(100):  # 100 levels deep
            current["nested"] = {"level": i + 1}
            current = current["nested"]

        import json

        json.dump(nested_json, f)
        nested_file_path = f.name

    try:
        metadata = parse_metadata(nested_file_path)
        # Should not hang or crash
        assert metadata is not None
        assert isinstance(metadata, dict)
    finally:
        os.unlink(nested_file_path)
