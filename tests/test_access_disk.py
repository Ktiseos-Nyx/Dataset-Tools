# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

import unittest
import os
import json
import toml

from unittest.mock import patch

from dataset_tools.access_disk import MetadataFileReader
from dataset_tools.correct_types import EmptyField

class TestDiskInterface(unittest.TestCase):
    def setUp(self):
        self.reader = MetadataFileReader()
        self.test_folder = os.path.dirname(os.path.abspath(__file__))
        self.png_file = os.path.join(self.test_folder, "test_img.png") # You'll need to create this test file
        self.jpg_file = os.path.join(self.test_folder, "test_img.jpg") # You'll need to create this test file
        self.text_file_utf8 = os.path.join(self.test_folder, "test_text_utf8.txt") # You'll need to create this test file (UTF-8 encoded)
        self.text_file_utf16be = os.path.join(self.test_folder, "test_text_utf16be.txt") # You'll need to create this test file (UTF-16-BE encoded)
        self.json_file = os.path.join(self.test_folder, "test_schema.json") # You'll need to create this test file
        self.toml_file = os.path.join(self.test_folder, "test_schema.toml") # You'll need to create this test file


    def test_read_png_header_fail_filenotfound(self):
        """Test read_header and read_png_header fail with FileNotFoundError for non-existent PNG"""
        with self.assertRaises(FileNotFoundError):
            self.reader.read_header(os.path.join(self.test_folder, "nonexistent.png"))

    def test_read_png_header_succeed(self):
        """Test successful PNG header reading and basic metadata existence"""
        chunks = self.reader.read_header(self.png_file)
        self.assertIsNotNone(chunks, "read_header should not return None for valid PNG")
        self.assertTrue(isinstance(chunks, dict), "read_header should return a dictionary for PNG")
        # Add more specific assertions to check for expected metadata content in test_img.png
        # Example (adjust based on actual metadata in your test_img.png):
        # self.assertIn("Software", chunks, "PNG metadata should contain 'Software' tag")
        # self.assertIsInstance(chunks.get("Software"), str, "'Software' tag value should be a string")

    def test_read_jpg_header_succeed(self):
        """Test successful JPG header reading and basic metadata existence"""
        chunks = self.reader.read_header(self.jpg_file)
        self.assertIsNotNone(chunks, "read_header should not return None for valid JPG")
        self.assertTrue(isinstance(chunks, dict), "read_header should return a dictionary for JPG")
         # Add more specific assertions to check for expected metadata content in test_img.jpg
        # Example (adjust based on actual metadata in your test_img.jpg EXIF):
        # self.assertIn("ExifVersion", chunks, "JPG metadata should contain 'ExifVersion' tag")
        # self.assertIsInstance(chunks.get("ExifVersion"), bytes, "'ExifVersion' tag value should be bytes")

    def test_read_txt_contents_succeed_utf8(self):
        """Test successful reading of UTF-8 encoded text file"""
        metadata = self.reader.read_header(self.text_file_utf8)
        self.assertIsNotNone(metadata, "read_header should not return None for valid UTF-8 text file")
        self.assertTrue(isinstance(metadata, dict), "read_header should return a dictionary for text file")
        self.assertIn(UpField.TEXT_DATA, metadata, "Metadata should contain TEXT_DATA key")
        # Add more specific assertions to check for expected text content in test_text_utf8.txt
        # Example (adjust based on actual text content):
        # self.assertIn("This is a test UTF-8 text file", metadata[UpField.TEXT_DATA], "Text data should contain expected content")

    def test_read_txt_contents_succeed_utf16be(self):
        """Test successful reading of UTF-16-BE encoded text file"""
        metadata = self.reader.read_header(self.text_file_utf16be)
        self.assertIsNotNone(metadata, "read_header should not return None for valid UTF-16-BE text file")
        self.assertTrue(isinstance(metadata, dict), "read_header should return a dictionary for text file")
        self.assertIn(UpField.TEXT_DATA, metadata, "Metadata should contain TEXT_DATA key")
        # Add more specific assertions to check for expected text content in test_text_utf16be.txt
        # Example (adjust based on actual text content):
        # self.assertIn("This is a test UTF-16-BE text file", metadata[UpField.TEXT_DATA], "Text data should contain expected content")

    def test_read_txt_contents_fail_encoding(self):
        """Test read_txt_contents handles UnicodeDecodeError gracefully (non-UTF8/UTF16 file)"""
        # Create a test file with an encoding that's not UTF-8 or UTF-16-BE (e.g., ISO-8859-1) - you'll need to create this
        non_unicode_text_file = os.path.join(self.test_folder, "test_text_latin1.txt")
        with open(non_unicode_text_file, "w", encoding="latin-1") as f:
            f.write("This is a test latin-1 text file")

        metadata = self.reader.read_header(non_unicode_text_file)
        self.assertIsNone(metadata, "read_header should return None when text encoding fails")


    def test_read_schema_file_json_succeed(self):
        """Test successful reading of JSON schema file"""
        metadata = self.reader.read_header(self.json_file)
        self.assertIsNotNone(metadata, "read_header should not return None for valid JSON file")
        self.assertTrue(isinstance(metadata, dict), "read_header should return a dictionary for JSON file")
        self.assertIn(DownField.JSON_DATA, metadata, "Metadata should contain JSON_DATA key")
        # Add more specific assertions to check for expected JSON content in test_schema.json
        # Example (adjust based on actual JSON content):
        # self.assertEqual(metadata[DownField.JSON_DATA].get("name"), "Test JSON Schema", "JSON data should contain expected 'name' field")

    def test_read_schema_file_json_fail_syntax(self):
        """Test read_schema_file handles JSON syntax errors by raising SyntaxError"""
        invalid_json_file = os.path.join(self.test_folder, "invalid_schema.json") # You'll need to create this invalid JSON file
        with open(invalid_json_file, "w") as f:
            f.write('{"invalid": json,}') # Intentional syntax error

        with self.assertRaises(SyntaxError): # Expecting SyntaxError to be raised
            self.reader.read_header(invalid_json_file)


    def test_read_schema_file_toml_succeed(self):
        """Test successful reading of TOML schema file"""
        metadata = self.reader.read_header(self.toml_file)
        self.assertIsNotNone(metadata, "read_header should not return None for valid TOML file")
        self.assertTrue(isinstance(metadata, dict), "read_header should return a dictionary for TOML file")
        self.assertIn(DownField.JSON_DATA, metadata, "Metadata should contain JSON_DATA key for TOML") # Note: TOML is loaded into JSON_DATA
        # Add more specific assertions to check for expected TOML content in test_schema.toml
        # Example (adjust based on actual TOML content):
        # self.assertEqual(metadata[DownField.JSON_DATA].get("title"), "Test TOML Schema", "TOML data should contain expected 'title' field")


    def test_read_schema_file_toml_fail_syntax(self):
        """Test read_schema_file handles TOML syntax errors by raising SyntaxError"""
        invalid_toml_file = os.path.join(self.test_folder, "invalid_schema.toml") # You'll need to create this invalid TOML file
        with open(invalid_toml_file, "w") as f:
            f.write('invalid toml syntax = "oops" =') # Intentional syntax error

        with self.assertRaises(SyntaxError): # Expecting SyntaxError to be raised
            self.reader.read_header(invalid_toml_file)


    @patch("dataset_tools.access_disk.ModelTool")
    def test_read_header_model_file(self, MockModelTool):
        """Test that read_header calls model_tool.read_metadata_from for model files"""
        mock_model_tool_instance = MockModelTool.return_value
        mock_model_tool_instance.read_metadata_from.return_value = {"model_metadata": "mock data"} # Mock return value

        fake_model_file_path = "test_model.safetensors" # Extension doesn't really matter for this test
        metadata = self.reader.read_header(fake_model_file_path)

        MockModelTool.assert_called_once() # Verify ModelTool class was instantiated
        mock_model_tool_instance.read_metadata_from.assert_called_once_with(fake_model_file_path) # Verify read_metadata_from was called
        self.assertEqual(metadata, {"model_metadata": "mock data"}) # Verify return value is from mock


if __name__ == "__main__":
    unittest.main()
