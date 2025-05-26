# tests/test_md_ps.py
import unittest
from unittest.mock import patch, MagicMock # Mock is an alias for MagicMock in modern unittest

# Import ONLY what's TRULY EXPORTED by your NEW metadata_parser.py
from dataset_tools.metadata_parser import (
    parse_metadata,
    make_paired_str_dict,
    process_pyexiv2_data
)
from dataset_tools.correct_types import UpField, DownField, EmptyField
from sd_prompt_reader.format import BaseFormat # For mocking status
from sd_prompt_reader.constants import PARAMETER_PLACEHOLDER as SDPR_PARAMETER_PLACEHOLDER

class TestParseMetadataIntegration(unittest.TestCase):

    def setUp(self):
        self.a1111_example_raw_params = "positive prompt\nNegative prompt: negative prompt\nSteps: 20, Sampler: Euler, Seed: 123, Size: 512x512, Model: test_model"
        # ComfyUI prompt and workflow are typically JSON strings
        self.comfy_example_prompt_str = '{"3": {"class_type": "KSampler", "inputs": {"seed": 456, "model": ["4",0], "positive": ["6",0], "negative": ["7",0] }}, "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "comfy positive", "clip": ["4",1]}}, "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "comfy negative", "clip": ["4",1]}}, "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "comfy_model.safetensors"}}}'
        self.comfy_example_workflow_str = '{"nodes": [{"id":3,...}], "links":[]}' # Simplified

    @patch('dataset_tools.metadata_parser.ImageDataReader')
    def test_parse_metadata_a1111_success(self, MockImageDataReader):
        mock_reader_instance = MockImageDataReader.return_value
        mock_reader_instance.status = BaseFormat.Status.READ_SUCCESS
        mock_reader_instance.tool = "A1111 webUI" # Or "Forge" etc.
        mock_reader_instance.positive = "positive prompt"
        mock_reader_instance.negative = "negative prompt"
        mock_reader_instance.is_sdxl = False
        mock_reader_instance.parameter = {
            'model': 'test_model', 'sampler': 'Euler', 'seed': '123',
            'cfg': '7.0', 'steps': '20', 'size': '512x512'
        }
        mock_reader_instance.width = "512"
        mock_reader_instance.height = "512"
        mock_reader_instance.setting = "Steps: 20, Sampler: Euler, Seed: 123, Size: 512x512, Model: test_model"
        mock_reader_instance.raw = self.a1111_example_raw_params

        result = parse_metadata("fake_a1111_image.png")

        MockImageDataReader.assert_called_once_with("fake_a1111_image.png")
        self.assertIn(UpField.PROMPT, result)
        self.assertEqual(result[UpField.PROMPT]['Positive'], "positive prompt")
        self.assertIn(DownField.GENERATION_DATA, result)
        self.assertEqual(result[DownField.GENERATION_DATA].get('Steps'), '20')
        self.assertIn(UpField.METADATA, result)
        self.assertEqual(result[UpField.METADATA]['Detected Tool'], "A1111 webUI")

    @patch('dataset_tools.metadata_parser.ImageDataReader')
    def test_parse_metadata_comfyui_success(self, MockImageDataReader):
        mock_reader_instance = MockImageDataReader.return_value
        mock_reader_instance.status = BaseFormat.Status.READ_SUCCESS
        mock_reader_instance.tool = "ComfyUI"
        # ComfyUI parser in sd-prompt-reader might populate these differently.
        # Often, positive/negative are extracted from the traversed workflow.
        # Setting string might be a summary. Raw will contain the JSONs.
        mock_reader_instance.positive = "comfy positive" # Simplified for this test
        mock_reader_instance.negative = "comfy negative" # Simplified
        mock_reader_instance.is_sdxl = False
        mock_reader_instance.parameter = { # Populated by ComfyUI parser traversing nodes
            'model': 'comfy_model.safetensors', 'sampler': 'euler', 'seed': '456',
            'cfg': '8.0', 'steps': '25', 'size': '512x768'
        }
        mock_reader_instance.width = "512" # ComfyUI parser in sd-prompt-reader gets this
        mock_reader_instance.height = "768"
        mock_reader_instance.setting = "Steps: 25, Sampler: euler, CFG scale: 8.0, Seed: 456, Size: 512x768, Model: comfy_model.safetensors" # Example
        mock_reader_instance.raw = f"Prompt: {self.comfy_example_prompt_str}\nWorkflow: {self.comfy_example_workflow_str}"

        result = parse_metadata("fake_comfy_image.png")

        MockImageDataReader.assert_called_once_with("fake_comfy_image.png")
        self.assertIn(UpField.PROMPT, result)
        self.assertEqual(result[UpField.PROMPT]['Positive'], "comfy positive")
        self.assertIn(DownField.GENERATION_DATA, result)
        self.assertEqual(result[DownField.GENERATION_DATA].get('Seed'), '456')
        self.assertEqual(result[DownField.GENERATION_DATA].get('Model'), 'comfy_model.safetensors')
        self.assertIn(UpField.METADATA, result)
        self.assertEqual(result[UpField.METADATA]['Detected Tool'], "ComfyUI")

    @patch('dataset_tools.metadata_parser.ImageDataReader')
    @patch('dataset_tools.metadata_parser.MetadataFileReader')
    def test_parse_metadata_standard_exif_fallback(self, MockMetadataFileReader, MockImageDataReader):
        mock_sdpr_instance = MockImageDataReader.return_value
        mock_sdpr_instance.status = BaseFormat.Status.FORMAT_ERROR
        mock_sdpr_instance.tool = None
        mock_sdpr_instance.raw = None # Or some unidentifiable raw string

        mock_mfr_instance = MockMetadataFileReader.return_value
        mock_mfr_instance.read_jpg_header_pyexiv2.return_value = {
            "EXIF": {"Exif.Image.Make": "Canon", "Exif.Image.Model": "EOS R5"},
            "XMP": {"Xmp.dc.creator": ["Test Author"], "Xmp.dc.description": {"x-default": "A test image"}}
        }
        mock_mfr_instance.read_png_header_pyexiv2.return_value = None # Simulate no std exif in png

        result_jpg = parse_metadata("standard_photo.jpg")
        MockImageDataReader.assert_called_with("standard_photo.jpg")
        MockMetadataFileReader.assert_called_once()
        mock_mfr_instance.read_jpg_header_pyexiv2.assert_called_once_with("standard_photo.jpg")

        self.assertNotIn(UpField.PROMPT, result_jpg)
        self.assertIn(DownField.EXIF, result_jpg)
        self.assertEqual(result_jpg[DownField.EXIF]['Camera Make'], "Canon")
        self.assertIn(UpField.TAGS, result_jpg)
        self.assertEqual(result_jpg[UpField.TAGS]['Artist'], "Test Author")

        # Reset mocks for next call if they are instance-scoped in test class
        MockImageDataReader.reset_mock()
        MockMetadataFileReader.reset_mock() # If you need to re-instantiate or check calls per test
        mock_mfr_instance.reset_mock()


        mock_sdpr_instance_png = MockImageDataReader.return_value # Re-assign for clarity if needed
        mock_sdpr_instance_png.status = BaseFormat.Status.FORMAT_ERROR
        mock_sdpr_instance_png.tool = None
        mock_sdpr_instance_png.raw = None

        mock_mfr_instance_png = MockMetadataFileReader.return_value
        mock_mfr_instance_png.read_png_header_pyexiv2.return_value = { # Simulate PNG with some XMP
             "XMP": {"Xmp.dc.title": ["PNG Title"]}
        }
        mock_mfr_instance_png.read_jpg_header_pyexiv2.return_value = None


        result_png = parse_metadata("standard_photo.png")
        MockImageDataReader.assert_called_with("standard_photo.png")
        mock_mfr_instance_png.read_png_header_pyexiv2.assert_called_once_with("standard_photo.png")
        self.assertIn(UpField.TAGS, result_png)
        self.assertEqual(result_png[UpField.TAGS]['Title'], "PNG Title")


    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="This is test text content.")
    @patch('dataset_tools.metadata_parser.ImageDataReader') # Still need to mock this
    def test_parse_metadata_txt_file(self, MockImageDataReader, mock_open_file):
        # Configure ImageDataReader to simulate it handling .txt file
        mock_reader_instance = MockImageDataReader.return_value
        mock_reader_instance.status = BaseFormat.Status.READ_SUCCESS # Assume sd-prompt-reader's txt path works
        mock_reader_instance.tool = "TXT File" # Or whatever it reports
        mock_reader_instance.raw = "This is test text content."
        mock_reader_instance.positive = "This is test text content." # if it puts all text in positive for .txt
        mock_reader_instance.negative = ""
        mock_reader_instance.parameter = {}
        mock_reader_instance.setting = ""
        mock_reader_instance.width = "0"
        mock_reader_instance.height = "0"


        file_path = "test.txt"
        result = parse_metadata(file_path)

        # Check that ImageDataReader was called appropriately for a .txt file
        MockImageDataReader.assert_called_once()
        # The first argument to ImageDataReader would be a file object due to `with open(...)`
        # self.assertEqual(MockImageDataReader.call_args[0][1], {'is_txt': True}) # Check kwargs

        self.assertIn(UpField.PROMPT, result) # Assuming it puts text into positive prompt
        self.assertEqual(result[UpField.PROMPT]['Positive'], "This is test text content.")
        self.assertIn(DownField.RAW_DATA, result)
        self.assertEqual(result[DownField.RAW_DATA], "This is test text content.")
        self.assertIn(UpField.METADATA, result)
        self.assertEqual(result[UpField.METADATA]['Detected Tool'], "TXT File")

    @patch('dataset_tools.metadata_parser.ImageDataReader')
    def test_parse_metadata_imagedatareader_general_failure(self, MockImageDataReader):
        mock_reader_instance = MockImageDataReader.return_value
        mock_reader_instance.status = BaseFormat.Status.FORMAT_ERROR # General format error
        mock_reader_instance.tool = "SomeTool" # It might detect a tool but fail to parse
        mock_reader_instance.raw = "corrupted data string"

        result = parse_metadata("corrupted_image.png")

        MockImageDataReader.assert_called_once_with("corrupted_image.png")
        self.assertIn(EmptyField.PLACEHOLDER, result)
        self.assertIn("Error", result[EmptyField.PLACEHOLDER])
        self.assertTrue("FORMAT_ERROR" in result[EmptyField.PLACEHOLDER]["Error"])
        self.assertTrue("SomeTool" in result[EmptyField.PLACEHOLDER]["Error"])
        self.assertIn(DownField.RAW_DATA, result)
        self.assertEqual(result[DownField.RAW_DATA], "corrupted data string")

    @patch('dataset_tools.metadata_parser.ImageDataReader', side_effect=FileNotFoundError("Mocked File Not Found"))
    def test_parse_metadata_file_not_found_by_imagedatareader(self, MockImageDataReader):
        result = parse_metadata("non_existent_image.png")
        
        MockImageDataReader.assert_called_once_with("non_existent_image.png")
        self.assertIn(EmptyField.PLACEHOLDER, result)
        self.assertEqual(result[EmptyField.PLACEHOLDER]["Error"], "File not found.")

    # --- Tests for Helper Functions (if still public in metadata_parser.py) ---
    def test_make_paired_str_dict_various_inputs(self):
        self.assertEqual(make_paired_str_dict("Steps: 20, Sampler: Euler"), {"Steps": "20", "Sampler": "Euler"})
        self.assertEqual(make_paired_str_dict("Lora hashes: \"lora1:hashA, lora2:hashB\", TI hashes: \"ti1:hashC\""), 
                         {"Lora hashes": "\"lora1:hashA, lora2:hashB\"", "TI hashes": "\"ti1:hashC\""})
        self.assertEqual(make_paired_str_dict("Key: Value with, comma, CFG scale: 7"), {"Key": "Value with, comma", "CFG scale": "7"})
        self.assertEqual(make_paired_str_dict(""), {})
        self.assertEqual(make_paired_str_dict(None), {})

    @patch('dataset_tools.metadata_parser.nfo') # Mock logger if it's noisy or for verification
    def test_process_pyexiv2_data_full(self, mock_nfo_logger):
        pyexiv2_input = {
            "EXIF": {
                "Exif.Image.Make": "Canon", 
                "Exif.Image.Model": "EOS R5",
                "Exif.Photo.DateTimeOriginal": "2023:01:01 10:00:00",
                "Exif.Photo.FNumber": 2.8, # Example with float
                "Exif.Photo.ISOSpeedRatings": 100 # Example with int
            },
            "XMP": {
                "Xmp.dc.creator": ["Photographer A", "Photographer B"], 
                "Xmp.dc.description": {"x-default": "A test image with XMP"},
                "Xmp.photoshop.DateCreated": "2023-01-01T10:00:00"
            },
            "IPTC": { # Example, add if your process_pyexiv2_data handles IPTC
                "Iptc.Application2.Keywords": ["test", "photo"]
            }
        }
        expected_output = {
            DownField.EXIF: {
                "Camera Make": "Canon", 
                "Camera Model": "EOS R5",
                "Date Taken": "2023:01:01 10:00:00",
                # Add FNumber and ISOSpeedRatings to your process_pyexiv2_data if you want them
                # "Fnumber": "2.8",
                # "Iso": "100",
            },
            UpField.TAGS: {
                "Artist": "Photographer A, Photographer B", 
                "Description": "A test image with XMP",
                # Add DateCreated and Keywords to your process_pyexiv2_data if you want them
                # "Date Created (XMP)": "2023-01-01T10:00:00",
                # "Keywords (IPTC)": "test, photo"
            }
        }
        # Refine process_pyexiv2_data to produce exactly this, then test
        actual_output = process_pyexiv2_data(pyexiv2_input)
        
        # Check EXIF part
        if DownField.EXIF in expected_output:
            self.assertIn(DownField.EXIF, actual_output)
            self.assertEqual(actual_output[DownField.EXIF], expected_output[DownField.EXIF])
        else:
            self.assertNotIn(DownField.EXIF, actual_output)

        # Check TAGS part (XMP, IPTC)
        if UpField.TAGS in expected_output:
            self.assertIn(UpField.TAGS, actual_output)
            self.assertEqual(actual_output[UpField.TAGS], expected_output[UpField.TAGS])
        else:
            self.assertNotIn(UpField.TAGS, actual_output)


if __name__ == "__main__":
    unittest.main()