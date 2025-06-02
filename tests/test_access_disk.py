# tests/test_access_disk.py

import json
import os
import unittest
from unittest.mock import patch  # mock_open can be useful if mocking file system

import toml

# Adjust imports based on your project structure.
from dataset_tools.access_disk import MetadataFileReader
from dataset_tools.correct_types import (
    DownField,
    EmptyField,
    UpField,
)  # ExtensionType not directly used here now


class TestDiskInterface(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, including creating temporary test files."""
        self.reader = MetadataFileReader()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_data_folder = os.path.join(base_dir, "test_data_access_disk")
        os.makedirs(self.test_data_folder, exist_ok=True)

        # Define file paths
        self.png_file_no_meta = os.path.join(
            self.test_data_folder, "test_img_no_meta.png"
        )
        self.jpg_file_with_exif = os.path.join(
            self.test_data_folder, "test_img_with_exif.jpg"
        )  # Needs real EXIF
        self.jpg_file_no_exif = os.path.join(
            self.test_data_folder, "test_img_no_exif.jpg"
        )
        self.text_file_utf8 = os.path.join(self.test_data_folder, "test_text_utf8.txt")
        self.text_file_utf16be = os.path.join(
            self.test_data_folder, "test_text_utf16be.txt"
        )
        self.text_file_complex_utf8 = os.path.join(
            self.test_data_folder, "test_text_complex_utf8.txt"
        )
        self.binary_content_in_txt_file = os.path.join(
            self.test_data_folder, "binary_content.txt"
        )
        self.json_file = os.path.join(self.test_data_folder, "test_schema.json")
        self.invalid_json_file = os.path.join(
            self.test_data_folder, "invalid_schema.json"
        )
        self.toml_file = os.path.join(self.test_data_folder, "test_schema.toml")
        self.invalid_toml_file = os.path.join(
            self.test_data_folder, "invalid_schema.toml"
        )
        self.fake_model_file_path = os.path.join(
            self.test_data_folder, "test_model.safetensors"
        )
        self.unhandled_ext_file_path = os.path.join(
            self.test_data_folder, "test.unknownext"
        )

        # Create minimal test files
        with open(self.png_file_no_meta, "wb") as f_obj:
            f_obj.write(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDAT\x08\xd7c`\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82"
            )
        if not os.path.exists(self.jpg_file_with_exif):
            with open(self.jpg_file_with_exif, "wb") as f_obj:
                f_obj.write(
                    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"
                )
        with open(self.jpg_file_no_exif, "wb") as f_obj:
            f_obj.write(
                b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x11\x11\x18!\x1e\x18\x1a\x1d(%\x1e!%*( DAF4F5\x0c\r\x1a%*( DAF4F5\xff\xc9\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9"
            )
        with open(self.text_file_utf8, "w", encoding="utf-8") as f_obj:
            f_obj.write("UTF-8 test content")
        with open(self.text_file_utf16be, "w", encoding="utf-16-be") as f_obj:
            f_obj.write("UTF-16-BE test content")
        with open(self.text_file_complex_utf8, "w", encoding="utf-8") as f_obj:
            f_obj.write("Voilà un résumé with çedillas, ñ, and ©opyright ± symbols.")
        with open(self.binary_content_in_txt_file, "wb") as f_obj:
            # Problematic byte sequences
            f_obj.write(b"\xc0\x80\xf5\x80\x80\x80\xff\xfe\xa0\xa1")
        with open(self.json_file, "w", encoding="utf-8") as f_obj:
            json.dump({"name": "Test JSON Schema", "version": 1}, f_obj)
        with open(self.invalid_json_file, "w", encoding="utf-8") as f_obj:
            f_obj.write('{"invalid": json, "key": "value"}')
        with open(self.toml_file, "w", encoding="utf-8") as f_obj:
            toml.dump({"title": "Test TOML Schema", "owner": {"name": "Test"}}, f_obj)
        with open(self.invalid_toml_file, "w", encoding="utf-8") as f_obj:
            f_obj.write('invalid toml syntax = "oops" =')
        with open(self.fake_model_file_path, "wb") as f_obj:
            f_obj.write(b"dummy model data")
        with open(self.unhandled_ext_file_path, "w", encoding="utf-8") as f_obj:
            f_obj.write("data for unhandled extension")

    def tearDown(self):
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
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except OSError as os_err:
                    print(f"Warning: Could not remove test file {f_path}: {os_err}")

        if os.path.exists(self.test_data_folder):
            try:
                if not os.listdir(self.test_data_folder):
                    os.rmdir(self.test_data_folder)
            except OSError as os_err_dir:  # pragma: no cover
                print(
                    f"Warning: Could not remove test data folder {self.test_data_folder}: {os_err_dir}"
                )

    # --- Tests for pyexiv2 based image readers (called directly) ---
    def test_read_jpg_header_pyexiv2_no_exif(self):
        result = self.reader.read_jpg_header_pyexiv2(self.jpg_file_no_exif)
        if result is not None:  # pyexiv2 might return empty dicts
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("EXIF"), {})
            self.assertEqual(result.get("XMP"), {})
            self.assertEqual(result.get("IPTC"), {})
        else:  # Or None if it found absolutely nothing
            self.assertIsNone(result)

    def test_read_png_header_pyexiv2_no_standard_meta(self):
        result = self.reader.read_png_header_pyexiv2(self.png_file_no_meta)
        if result is not None:
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("EXIF"), {})
            self.assertEqual(result.get("XMP"), {})
            self.assertEqual(result.get("IPTC"), {})
        else:
            self.assertIsNone(result)

    def test_read_image_header_pyexiv2_file_not_found(self):
        """Test pyexiv2 readers return None when file is not found or unreadable."""
        non_existent_jpg = os.path.join(self.test_data_folder, "nonexistent.jpg")
        result_jpg = self.reader.read_jpg_header_pyexiv2(non_existent_jpg)
        self.assertIsNone(
            result_jpg,
            "read_jpg_header_pyexiv2 should return None for nonexistent file",
        )

        non_existent_png = os.path.join(self.test_data_folder, "nonexistent.png")
        result_png = self.reader.read_png_header_pyexiv2(non_existent_png)
        self.assertIsNone(
            result_png,
            "read_png_header_pyexiv2 should return None for nonexistent file",
        )

    # --- Tests for file readers via the main dispatcher read_file_data_by_type ---
    def test_read_txt_utf8_via_dispatcher(self):
        metadata = self.reader.read_file_data_by_type(self.text_file_utf8)
        self.assertIsNotNone(
            metadata, "Should not return None for valid UTF-8 text file"
        )
        self.assertIsInstance(metadata, dict)
        self.assertIn(UpField.TEXT_DATA.value, metadata)
        self.assertEqual(metadata[UpField.TEXT_DATA.value], "UTF-8 test content")

    def test_read_txt_utf16be_via_dispatcher(self):
        metadata = self.reader.read_file_data_by_type(self.text_file_utf16be)
        self.assertIsNotNone(metadata)
        self.assertIsInstance(metadata, dict)
        self.assertIn(UpField.TEXT_DATA.value, metadata)
        self.assertEqual(metadata[UpField.TEXT_DATA.value], "UTF-16-BE test content")

    def test_read_complex_utf8_txt_via_dispatcher(self):
        metadata = self.reader.read_file_data_by_type(self.text_file_complex_utf8)
        self.assertIsNotNone(
            metadata, "Should successfully read complex UTF-8 text file"
        )
        self.assertIn(UpField.TEXT_DATA.value, metadata)
        self.assertEqual(
            metadata[UpField.TEXT_DATA.value],
            "Voilà un résumé with çedillas, ñ, and ©opyright ± symbols.",
        )

    def test_read_txt_fail_encoding_via_dispatcher(self):
        metadata = self.reader.read_file_data_by_type(self.binary_content_in_txt_file)
        self.assertIsNone(
            metadata,
            "Should return None when all text encodings fail for a .txt file with binary content",
        )

    def test_read_json_succeed_via_dispatcher(self):
        metadata = self.reader.read_file_data_by_type(self.json_file)
        self.assertIsNotNone(metadata)
        self.assertIsInstance(metadata, dict)
        self.assertIn(DownField.JSON_DATA.value, metadata)
        self.assertEqual(
            metadata[DownField.JSON_DATA.value]["name"], "Test JSON Schema"
        )

    def test_read_json_fail_syntax_via_dispatcher(self):
        result = self.reader.read_file_data_by_type(self.invalid_json_file)
        self.assertIsNotNone(result)
        self.assertIn(EmptyField.PLACEHOLDER.value, result)
        self.assertIn("Error", result[EmptyField.PLACEHOLDER.value])
        self.assertIn(
            "Invalid .json format", result[EmptyField.PLACEHOLDER.value]["Error"]
        )

    def test_read_toml_succeed_via_dispatcher(self):
        metadata = self.reader.read_file_data_by_type(self.toml_file)
        self.assertIsNotNone(metadata)
        self.assertIsInstance(metadata, dict)
        self.assertIn(DownField.TOML_DATA.value, metadata)
        self.assertEqual(
            metadata[DownField.TOML_DATA.value]["title"], "Test TOML Schema"
        )

    def test_read_toml_fail_syntax_via_dispatcher(self):
        result = self.reader.read_file_data_by_type(self.invalid_toml_file)
        self.assertIsNotNone(result)
        self.assertIn(EmptyField.PLACEHOLDER.value, result)
        self.assertIn("Error", result[EmptyField.PLACEHOLDER.value])
        self.assertIn(
            "Invalid .toml format", result[EmptyField.PLACEHOLDER.value]["Error"]
        )

    @patch("dataset_tools.access_disk.ModelTool")
    def test_read_model_file_via_dispatcher(self, MockModelTool):
        mock_model_tool_instance = MockModelTool.return_value
        mock_model_tool_instance.read_metadata_from.return_value = {
            "model_metadata": "mock data"
        }

        metadata = self.reader.read_file_data_by_type(self.fake_model_file_path)

        MockModelTool.assert_called_once()
        mock_model_tool_instance.read_metadata_from.assert_called_once_with(
            self.fake_model_file_path
        )
        self.assertEqual(metadata, {"model_metadata": "mock data"})

    def test_read_unhandled_extension_via_dispatcher(self):
        result = self.reader.read_file_data_by_type(self.unhandled_ext_file_path)
        self.assertIsNone(result, "Should return None for unhandled file extensions")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
