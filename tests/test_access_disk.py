# tests/test_access_disk.py
"""Tests for the MetadataFileReader class."""  # D100: Module docstring

import json
import unittest
from pathlib import Path  # Import Path
from unittest.mock import patch

import toml

from dataset_tools.access_disk import MetadataFileReader
from dataset_tools.correct_types import DownField, EmptyField, UpField


class TestDiskInterface(unittest.TestCase):  # D203/D211 handled by formatter
    """Tests for the disk interface and metadata file reading capabilities."""  # D101: Class docstring

    def setUp(self):  # D102: Method docstring (or ANN201 if no return hint)
        """Set up test fixtures, including creating temporary test files."""
        self.reader = MetadataFileReader()
        # Use pathlib for path manipulations
        base_dir = Path(__file__).resolve().parent
        self.test_data_folder = base_dir / "test_data_access_disk"
        self.test_data_folder.mkdir(parents=True, exist_ok=True)

        # Define file paths using pathlib
        self.png_file_no_meta = self.test_data_folder / "test_img_no_meta.png"
        self.jpg_file_with_exif = self.test_data_folder / "test_img_with_exif.jpg"
        self.jpg_file_no_exif = self.test_data_folder / "test_img_no_exif.jpg"
        self.text_file_utf8 = self.test_data_folder / "test_text_utf8.txt"
        self.text_file_utf16be = self.test_data_folder / "test_text_utf16be.txt"
        self.text_file_complex_utf8 = self.test_data_folder / "test_text_complex_utf8.txt"
        self.binary_content_in_txt_file = self.test_data_folder / "binary_content.txt"
        self.json_file = self.test_data_folder / "test_schema.json"
        self.invalid_json_file = self.test_data_folder / "invalid_schema.json"
        self.toml_file = self.test_data_folder / "test_schema.toml"
        self.invalid_toml_file = self.test_data_folder / "invalid_schema.toml"
        self.fake_model_file_path = self.test_data_folder / "test_model.safetensors"
        self.unhandled_ext_file_path = self.test_data_folder / "test.unknownext"

        # Create minimal test files using pathlib
        with self.png_file_no_meta.open("wb") as f_obj:
            f_obj.write(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDAT\x08\xd7c`"
                b"\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82"
            )
        if not self.jpg_file_with_exif.exists():  # Example for one file, apply to others if needed
            with self.jpg_file_with_exif.open("wb") as f_obj:  # Requires actual EXIF for a meaningful test
                f_obj.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9")
        with self.jpg_file_no_exif.open("wb") as f_obj:
            f_obj.write(
                b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
                b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n"
                b"\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x11\x11\x18!\x1e"
                b"\x18\x1a\x1d(%\x1e!%*( DAF4F5\x0c\r\x1a%*( DAF4F5\xff\xc9\x00\x0b"
                b"\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9"
            )
        with self.text_file_utf8.open("w", encoding="utf-8") as f_obj:
            f_obj.write("UTF-8 test content")
        with self.text_file_utf16be.open("w", encoding="utf-16-be") as f_obj:
            f_obj.write("UTF-16-BE test content")
        with self.text_file_complex_utf8.open("w", encoding="utf-8") as f_obj:
            f_obj.write("Voilà un résumé with çedillas, ñ, and ©opyright ± symbols.")
        with self.binary_content_in_txt_file.open("wb") as f_obj:
            f_obj.write(b"\xc0\x80\xf5\x80\x80\x80\xff\xfe\xa0\xa1")
        with self.json_file.open("w", encoding="utf-8") as f_obj:
            json.dump({"name": "Test JSON Schema", "version": 1}, f_obj)
        with self.invalid_json_file.open("w", encoding="utf-8") as f_obj:
            f_obj.write('{"invalid": json, "key": "value"}')  # Intentional invalid JSON
        with self.toml_file.open("w", encoding="utf-8") as f_obj:
            toml.dump({"title": "Test TOML Schema", "owner": {"name": "Test"}}, f_obj)
        with self.invalid_toml_file.open("w", encoding="utf-8") as f_obj:
            f_obj.write('invalid toml syntax = "oops" =')  # Intentional invalid TOML
        with self.fake_model_file_path.open("wb") as f_obj:
            f_obj.write(b"dummy model data")
        with self.unhandled_ext_file_path.open("w", encoding="utf-8") as f_obj:
            f_obj.write("data for unhandled extension")

    def tearDown(self):  # D102
        """Clean up temporary test files and folder."""
        file_list = [
            self.png_file_no_meta,
            self.jpg_file_with_exif,
            self.jpg_file_no_exif,
            self.text_file_utf8,
            self.text_file_utf16be,
            self.text_file_complex_utf8,
            self.binary_content_in_txt_file,
            self.json_file,
            self.invalid_json_file,
            self.toml_file,
            self.invalid_toml_file,
            self.fake_model_file_path,
            self.unhandled_ext_file_path,
        ]
        for f_path in file_list:
            if f_path.exists():  # Use pathlib
                try:
                    f_path.unlink()  # Use pathlib
                except OSError as os_err:  # Keep OSError for broad catch here
                    # Replace print with logging if desired, or keep for test output
                    print(f"Warning: Could not remove test file {f_path}: {os_err}")  # T201

        if self.test_data_folder.exists():  # Use pathlib
            try:
                # Check if directory is empty before trying to remove
                if not any(self.test_data_folder.iterdir()):  # Check if dir is empty
                    self.test_data_folder.rmdir()  # Use pathlib
                else:
                    print(f"Warning: Test data folder {self.test_data_folder} not empty, not removing.")  # T201
            except OSError as os_err_dir:  # pragma: no cover
                print(f"Warning: Could not remove test data folder {self.test_data_folder}: {os_err_dir}")  # T201

    # --- Tests for pyexiv2 based image readers (called directly) ---
    def test_read_jpg_header_pyexiv2_no_exif(self):  # D102
        """Test reading JPG with no EXIF data returns None or empty dicts."""
        result = self.reader.read_jpg_header_pyexiv2(str(self.jpg_file_no_exif))  # Pass str path
        if result is not None:
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("EXIF"), {})
            self.assertEqual(result.get("XMP"), {})
            self.assertEqual(result.get("IPTC"), {})
        else:
            self.assertIsNone(result)

    def test_read_png_header_pyexiv2_no_standard_meta(self):  # D102
        """Test reading PNG with no standard EXIF/XMP/IPTC returns None or empty dicts."""
        result = self.reader.read_png_header_pyexiv2(str(self.png_file_no_meta))  # Pass str path
        if result is not None:
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("EXIF"), {})
            self.assertEqual(result.get("XMP"), {})
            self.assertEqual(result.get("IPTC"), {})
        else:
            self.assertIsNone(result)

    def test_read_image_header_pyexiv2_file_not_found(self):  # D102
        """Test pyexiv2 readers return None for nonexistent files."""
        non_existent_jpg = self.test_data_folder / "nonexistent.jpg"
        result_jpg = self.reader.read_jpg_header_pyexiv2(str(non_existent_jpg))
        self.assertIsNone(result_jpg, "read_jpg_header_pyexiv2 should return None")

        non_existent_png = self.test_data_folder / "nonexistent.png"
        result_png = self.reader.read_png_header_pyexiv2(str(non_existent_png))
        self.assertIsNone(result_png, "read_png_header_pyexiv2 should return None")

    # --- Tests for file readers via the main dispatcher read_file_data_by_type ---
    def test_read_txt_utf8_via_dispatcher(self):  # D102
        """Test reading UTF-8 text file via dispatcher."""
        metadata = self.reader.read_file_data_by_type(str(self.text_file_utf8))
        self.assertIsNotNone(metadata, "Should not be None for valid UTF-8 text")
        self.assertIsInstance(metadata, dict)
        self.assertIn(UpField.TEXT_DATA.value, metadata)
        self.assertEqual(metadata[UpField.TEXT_DATA.value], "UTF-8 test content")

    def test_read_txt_utf16be_via_dispatcher(self):  # D102
        """Test reading UTF-16BE text file via dispatcher."""
        metadata = self.reader.read_file_data_by_type(str(self.text_file_utf16be))
        self.assertIsNotNone(metadata)
        self.assertIsInstance(metadata, dict)
        self.assertIn(UpField.TEXT_DATA.value, metadata)
        self.assertEqual(metadata[UpField.TEXT_DATA.value], "UTF-16-BE test content")

    def test_read_complex_utf8_txt_via_dispatcher(self):  # D102
        """Test reading complex UTF-8 text file via dispatcher."""
        metadata = self.reader.read_file_data_by_type(str(self.text_file_complex_utf8))
        self.assertIsNotNone(metadata, "Should read complex UTF-8 text")
        self.assertIn(UpField.TEXT_DATA.value, metadata)
        expected_text = "Voilà un résumé with çedillas, ñ, and ©opyright ± symbols."
        self.assertEqual(metadata[UpField.TEXT_DATA.value], expected_text)

    def test_read_txt_fail_encoding_via_dispatcher(self):  # D102
        """Test reading text file with undecodable binary content."""
        metadata = self.reader.read_file_data_by_type(str(self.binary_content_in_txt_file))
        self.assertIsNone(metadata, "Should be None for undecodable binary .txt")

    def test_read_json_succeed_via_dispatcher(self):  # D102
        """Test successful JSON file reading via dispatcher."""
        metadata = self.reader.read_file_data_by_type(str(self.json_file))
        self.assertIsNotNone(metadata)
        self.assertIsInstance(metadata, dict)
        self.assertIn(DownField.JSON_DATA.value, metadata)
        self.assertEqual(metadata[DownField.JSON_DATA.value]["name"], "Test JSON Schema")

    def test_read_json_fail_syntax_via_dispatcher(self):  # D102
        """Test JSON file with syntax error via dispatcher."""
        result = self.reader.read_file_data_by_type(str(self.invalid_json_file))
        self.assertIsNotNone(result)
        self.assertIn(EmptyField.PLACEHOLDER.value, result)
        self.assertIn("Error", result[EmptyField.PLACEHOLDER.value])
        self.assertIn("Invalid .json format", result[EmptyField.PLACEHOLDER.value]["Error"])

    def test_read_toml_succeed_via_dispatcher(self):  # D102
        """Test successful TOML file reading via dispatcher."""
        metadata = self.reader.read_file_data_by_type(str(self.toml_file))
        self.assertIsNotNone(metadata)
        self.assertIsInstance(metadata, dict)
        self.assertIn(DownField.TOML_DATA.value, metadata)
        self.assertEqual(metadata[DownField.TOML_DATA.value]["title"], "Test TOML Schema")

    def test_read_toml_fail_syntax_via_dispatcher(self):  # D102
        """Test TOML file with syntax error via dispatcher."""
        result = self.reader.read_file_data_by_type(str(self.invalid_toml_file))
        self.assertIsNotNone(result)
        self.assertIn(EmptyField.PLACEHOLDER.value, result)
        self.assertIn("Error", result[EmptyField.PLACEHOLDER.value])
        self.assertIn("Invalid .toml format", result[EmptyField.PLACEHOLDER.value]["Error"])

    @patch("dataset_tools.access_disk.ModelTool")
    def test_read_model_file_via_dispatcher(self, MockModelTool: unittest.mock.Mock):  # Added type hint for mock
        """Test model file reading via dispatcher (mocked ModelTool)."""
        mock_model_tool_instance = MockModelTool.return_value
        mock_model_tool_instance.read_metadata_from.return_value = {"model_metadata": "mock data"}

        metadata = self.reader.read_file_data_by_type(str(self.fake_model_file_path))

        MockModelTool.assert_called_once()
        mock_model_tool_instance.read_metadata_from.assert_called_once_with(str(self.fake_model_file_path))
        self.assertEqual(metadata, {"model_metadata": "mock data"})

    def test_read_unhandled_extension_via_dispatcher(self):  # D102
        """Test dispatcher returns None for unhandled file extensions."""
        result = self.reader.read_file_data_by_type(str(self.unhandled_ext_file_path))
        self.assertIsNone(result, "Should be None for unhandled extensions")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
