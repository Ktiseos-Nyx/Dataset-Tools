# tests/test_access_disk.py

import unittest
import os
import json
import toml
from unittest.mock import patch, MagicMock # Added patch and MagicMock

# Adjust imports based on your project structure.
# If tests/ is a top-level directory alongside dataset_tools/:
from dataset_tools.access_disk import MetadataFileReader
from dataset_tools.correct_types import UpField, DownField, EmptyField
import pyexiv2 # Import if you're catching pyexiv2.Exiv2Error specifically or mocking its classes

class TestDiskInterface(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, including creating temporary test files."""
        self.reader = MetadataFileReader()
        
        # Create a dedicated folder for test data if it doesn't exist
        # This is better than polluting the same directory as the test script.
        # Assumes tests/test_data/ relative to where pytest is run (project root)
        # Or, more robustly, relative to this test file's location:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_data_folder = os.path.join(base_dir, "test_data_access_disk")
        os.makedirs(self.test_data_folder, exist_ok=True)

        # Define file paths
        self.png_file_no_meta = os.path.join(self.test_data_folder, "test_img_no_meta.png")
        self.jpg_file_with_exif = os.path.join(self.test_data_folder, "test_img_with_exif.jpg") # Should have actual EXIF for good tests
        self.jpg_file_no_exif = os.path.join(self.test_data_folder, "test_img_no_exif.jpg")
        self.text_file_utf8 = os.path.join(self.test_data_folder, "test_text_utf8.txt")
        self.text_file_utf16be = os.path.join(self.test_data_folder, "test_text_utf16be.txt")
        self.non_unicode_text_file = os.path.join(self.test_data_folder, "test_text_latin1.txt")
        self.json_file = os.path.join(self.test_data_folder, "test_schema.json")
        self.invalid_json_file = os.path.join(self.test_data_folder, "invalid_schema.json")
        self.toml_file = os.path.join(self.test_data_folder, "test_schema.toml")
        self.invalid_toml_file = os.path.join(self.test_data_folder, "invalid_schema.toml")
        self.fake_model_file_path = os.path.join(self.test_data_folder, "test_model.safetensors")

        # Create minimal test files
        with open(self.png_file_no_meta, "wb") as f:
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDAT\x08\xd7c`\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82')

        # For self.jpg_file_with_exif, you should ideally place a real JPG
        # with known EXIF data in the test_data_folder.
        # This minimal JPG likely has no EXIF for pyexiv2 to find.
        if not os.path.exists(self.jpg_file_with_exif):
             with open(self.jpg_file_with_exif, "wb") as f: # Example: create a placeholder if missing
                  f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9') # Minimal JPG

        with open(self.jpg_file_no_exif, "wb") as f:
            # Corrected byte string - removed extraneous backslashes before spaces
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x11\x11\x18!\x1e\x18\x1a\x1d(%\x1e!%*( DAF4F5\x0c\r\x1a%*( DAF4F5\xff\xc9\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9')

        with open(self.text_file_utf8, "w", encoding="utf-8") as f: f.write("UTF-8 test content")
        with open(self.text_file_utf16be, "w", encoding="utf-16-be") as f: f.write("UTF-16-BE test content")
        with open(self.non_unicode_text_file, "w", encoding="latin-1") as f: f.write("Latin-1 test content")
        with open(self.json_file, "w", encoding="utf-8") as f: json.dump({"name": "Test JSON Schema", "version": 1}, f)
        with open(self.invalid_json_file, "w", encoding="utf-8") as f: f.write('{"invalid": json, "key": "value"}') # Invalid JSON
        with open(self.toml_file, "w", encoding="utf-8") as f: toml.dump({"title": "Test TOML Schema", "owner": {"name": "Test"}}, f)
        with open(self.invalid_toml_file, "w", encoding="utf-8") as f: f.write('invalid toml syntax = "oops" =') # Invalid TOML
        with open(self.fake_model_file_path, "wb") as f: f.write(b"dummy model data") # For model tool test

    def tearDown(self):
        """Clean up temporary test files and folder."""
        file_list = [
            self.png_file_no_meta, self.jpg_file_with_exif, self.jpg_file_no_exif,
            self.text_file_utf8, self.text_file_utf16be, self.non_unicode_text_file,
            self.json_file, self.invalid_json_file,
            self.toml_file, self.invalid_toml_file,
            self.fake_model_file_path,
        ]
        for f_path in file_list:
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except OSError as e:
                    print(f"Warning: Could not remove test file {f_path}: {e}")
        
        if os.path.exists(self.test_data_folder):
            # Only remove the folder if it's empty, as a safety measure
            if not os.listdir(self.test_data_folder):
                os.rmdir(self.test_data_folder)
            else: # pragma: no cover (hard to test this branch reliably without complex setup)
                print(f"Warning: Test data folder {self.test_data_folder} not empty, not removing.")

    # --- Tests for pyexiv2 based image readers ---
    def test_read_jpg_header_pyexiv2_no_exif(self):
        """Test pyexiv2 JPG reader with a JPG that has no (or minimal) EXIF."""
        # The self.jpg_file_no_exif is a minimal JPG, unlikely to have EXIF.
        result = self.reader.read_jpg_header_pyexiv2(self.jpg_file_no_exif)
        # pyexiv2 might return a dict with empty EXIF/XMP/IPTC sections, or None
        if result is not None:
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("EXIF"), {})
            self.assertEqual(result.get("XMP"), {})
            self.assertEqual(result.get("IPTC"), {})
        else:
            # This case is also acceptable if pyexiv2 decides there's nothing at all
            self.assertIsNone(result)

    def test_read_png_header_pyexiv2_no_standard_meta(self):
        """Test pyexiv2 PNG reader with a PNG that has no standard EXIF/XMP."""
        result = self.reader.read_png_header_pyexiv2(self.png_file_no_meta)
        # Expect None or empty dicts if no standard metadata is found by pyexiv2 in PNG
        if result is not None:
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("EXIF"), {})
            self.assertEqual(result.get("XMP"), {})
            self.assertEqual(result.get("IPTC"), {})
        else:
            self.assertIsNone(result)

    def test_read_image_header_pyexiv2_file_not_found(self):
        """Test pyexiv2 readers handle FileNotFoundError (or internal error)."""
        # pyexiv2.Image() constructor might raise Exiv2Error, not FileNotFoundError
        # if the file doesn't exist or isn't a valid image.
        with self.assertRaises(Exception): # Catching general Exception as pyexiv2 error is specific
            # Your wrapper read_jpg_header_pyexiv2 might return None or raise it.
            # The current access_disk.py returns None on exception.
            # If it were to re-raise, this test would be different.
            result = self.reader.read_jpg_header_pyexiv2(os.path.join(self.test_data_folder, "nonexistent.jpg"))
            # If it returns None on error, then the test should be:
            # self.assertIsNone(result)
            # For now, let's assume if pyexiv2.Image() itself fails, an exception propagates
            # unless your wrapper explicitly catches and returns None.
            # Your current wrapper *does* catch Exception and returns None. So:
            self.assertIsNone(self.reader.read_jpg_header_pyexiv2(os.path.join(self.test_data_folder, "nonexistent.jpg")))
            self.assertIsNone(self.reader.read_png_header_pyexiv2(os.path.join(self.test_data_folder, "nonexistent.png")))


    # --- Tests for text and schema file readers (via read_general_file_content) ---
    def test_read_general_file_content_txt_utf8(self):
        metadata = self.reader.read_general_file_content(self.text_file_utf8)
        self.assertIsNotNone(metadata, "Should not return None for valid UTF-8 text file")
        self.assertIsInstance(metadata, dict)
        self.assertIn(UpField.TEXT_DATA, metadata)
        self.assertEqual(metadata[UpField.TEXT_DATA], "UTF-8 test content")

    def test_read_general_file_content_txt_utf16be(self):
        metadata = self.reader.read_general_file_content(self.text_file_utf16be)
        self.assertIsNotNone(metadata)
        self.assertIsInstance(metadata, dict)
        self.assertIn(UpField.TEXT_DATA, metadata)
        self.assertEqual(metadata[UpField.TEXT_DATA], "UTF-16-BE test content")

    def test_read_general_file_content_txt_fail_encoding(self):
        metadata = self.reader.read_general_file_content(self.non_unicode_text_file)
        # Your read_txt_contents tries multiple encodings. If all fail, it returns None.
        self.assertIsNone(metadata, "Should return None when all text encodings fail")

    def test_read_general_file_content_json_succeed(self):
        metadata = self.reader.read_general_file_content(self.json_file)
        self.assertIsNotNone(metadata)
        self.assertIsInstance(metadata, dict)
        self.assertIn(DownField.JSON_DATA, metadata)
        self.assertEqual(metadata[DownField.JSON_DATA]["name"], "Test JSON Schema")

    def test_read_general_file_content_json_fail_syntax(self):
        # Your read_schema_file is designed to return a dict with an error message for UI
        result = self.reader.read_general_file_content(self.invalid_json_file)
        self.assertIsNotNone(result)
        self.assertIn(EmptyField.PLACEHOLDER, result)
        self.assertIn("Error", result[EmptyField.PLACEHOLDER])
        self.assertTrue("Invalid .json format" in result[EmptyField.PLACEHOLDER]["Error"])


    def test_read_general_file_content_toml_succeed(self):
        metadata = self.reader.read_general_file_content(self.toml_file)
        self.assertIsNotNone(metadata)
        self.assertIsInstance(metadata, dict)
        # Your read_schema_file puts TOML data under DownField.TOML_DATA now
        self.assertIn(DownField.TOML_DATA, metadata)
        self.assertEqual(metadata[DownField.TOML_DATA]["title"], "Test TOML Schema")

    def test_read_general_file_content_toml_fail_syntax(self):
        result = self.reader.read_general_file_content(self.invalid_toml_file)
        self.assertIsNotNone(result)
        self.assertIn(EmptyField.PLACEHOLDER, result)
        self.assertIn("Error", result[EmptyField.PLACEHOLDER])
        self.assertTrue("Invalid .toml format" in result[EmptyField.PLACEHOLDER]["Error"])

    @patch("dataset_tools.access_disk.ModelTool")
    def test_read_general_file_content_model_file(self, MockModelTool):
        mock_model_tool_instance = MockModelTool.return_value
        mock_model_tool_instance.read_metadata_from.return_value = {"model_metadata": "mock data"}

        metadata = self.reader.read_general_file_content(self.fake_model_file_path)

        MockModelTool.assert_called_once()
        mock_model_tool_instance.read_metadata_from.assert_called_once_with(self.fake_model_file_path)
        self.assertEqual(metadata, {"model_metadata": "mock data"})

    def test_read_general_file_content_unhandled_extension(self):
        unhandled_file = os.path.join(self.test_data_folder, "test.unknownext")
        with open(unhandled_file, "w") as f: f.write("data")
        self.addCleanup(os.remove, unhandled_file) # Ensure cleanup

        result = self.reader.read_general_file_content(unhandled_file)
        self.assertIsNone(result, "Should return None for unhandled file extensions")

if __name__ == "__main__":
    unittest.main()