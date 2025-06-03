# tests/test_md_ps.py
import unittest
from unittest.mock import mock_open, patch  # Added mock_open

from dataset_tools.correct_types import DownField, EmptyField, UpField
from dataset_tools.metadata_parser import (
    make_paired_str_dict,
    parse_metadata,
    process_pyexiv2_data,
)

# Import from your vendored package
from dataset_tools.vendored_sdpr.format import BaseFormat  # CORRECTED IMPORT


class TestParseMetadataIntegration(unittest.TestCase):
    def setUp(self):
        # Example A1111 raw parameters string
        self.a1111_example_raw_params = (
            "positive prompt test from a1111\n"
            "Negative prompt: negative prompt test from a1111\n"
            "Steps: 30, Sampler: DPM++ 2M Karras, CFG scale: 7.5, Seed: 1234567890, "
            "Size: 512x768, Model hash: abcdef1234, Model: test_model_a1111.safetensors, "
            "Clip skip: 2, ENSD: 31337"
        )
        # Example ComfyUI prompt and workflow JSON strings
        self.comfy_example_prompt_str = json.dumps(
            {  # Use json.dumps for valid JSON string
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "seed": 987654321,
                        "steps": 25,
                        "cfg": 8.0,
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "denoise": 1.0,
                        "model": ["4", 0],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "latent_image": ["5", 0],
                    },
                },
                "4": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {"ckpt_name": "comfy_sdxl_model.safetensors"},
                },
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {"width": 768, "height": 1024, "batch_size": 1},
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "text": "positive prompt for ComfyUI test",
                        "clip": ["4", 1],
                    },
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "text": "negative prompt for ComfyUI test",
                        "clip": ["4", 1],
                    },
                },
            }
        )
        self.comfy_example_workflow_str = json.dumps(
            {"nodes": [], "links": []}
        )  # Keep it simple or make more complex if needed

    @patch("dataset_tools.metadata_parser.ImageDataReader")
    def test_parse_metadata_a1111_success(self, MockImageDataReader):
        mock_reader_instance = MockImageDataReader.return_value
        mock_reader_instance.status = BaseFormat.Status.READ_SUCCESS
        mock_reader_instance.tool = "A1111 webUI"
        mock_reader_instance.positive = "positive prompt test from a1111"
        mock_reader_instance.negative = "negative prompt test from a1111"
        mock_reader_instance.is_sdxl = False
        mock_reader_instance.positive_sdxl = {}
        mock_reader_instance.negative_sdxl = {}
        mock_reader_instance.parameter = {
            "model": "test_model_a1111.safetensors",
            "model_hash": "abcdef1234",
            "sampler_name": "DPM++ 2M Karras",
            "seed": "1234567890",
            "cfg_scale": "7.5",
            "steps": "30",
            "size": "512x768",
            "clip_skip": "2",  # Added from raw params
            # PARAMETER_PLACEHOLDER for any unparsed but defined keys in BaseFormat
        }
        mock_reader_instance.width = "512"
        mock_reader_instance.height = "768"
        mock_reader_instance.setting = "Steps: 30, Sampler: DPM++ 2M Karras, CFG scale: 7.5, Seed: 1234567890, Size: 512x768, Model hash: abcdef1234, Model: test_model_a1111.safetensors, Clip skip: 2, ENSD: 31337"
        mock_reader_instance.raw = self.a1111_example_raw_params

        result = parse_metadata("fake_a1111_image.png")

        MockImageDataReader.assert_called_once_with("fake_a1111_image.png")
        self.assertIn(UpField.PROMPT.value, result)
        self.assertEqual(
            result[UpField.PROMPT.value].get("Positive"),
            "positive prompt test from a1111",
        )
        self.assertEqual(
            result[UpField.PROMPT.value].get("Negative"),
            "negative prompt test from a1111",
        )
        self.assertIn(DownField.GENERATION_DATA.value, result)
        gen_data = result[DownField.GENERATION_DATA.value]
        self.assertEqual(gen_data.get("Steps"), "30")
        self.assertEqual(
            gen_data.get("Sampler"), "DPM++ 2M Karras"
        )  # Check display key if different
        self.assertEqual(gen_data.get("Model"), "test_model_a1111.safetensors")
        self.assertIn(UpField.METADATA.value, result)
        self.assertEqual(
            result[UpField.METADATA.value].get("Detected Tool"), "A1111 webUI"
        )

    @patch("dataset_tools.metadata_parser.ImageDataReader")
    def test_parse_metadata_comfyui_success(self, MockImageDataReader):
        mock_reader_instance = MockImageDataReader.return_value
        mock_reader_instance.status = BaseFormat.Status.READ_SUCCESS
        mock_reader_instance.tool = "ComfyUI"
        mock_reader_instance.positive = "positive prompt for ComfyUI test"
        mock_reader_instance.negative = "negative prompt for ComfyUI test"
        mock_reader_instance.is_sdxl = False  # Based on example workflow
        mock_reader_instance.positive_sdxl = {}
        mock_reader_instance.negative_sdxl = {}
        mock_reader_instance.parameter = {
            "model": "comfy_sdxl_model.safetensors",
            "sampler_name": "euler",
            "seed": "987654321",
            "cfg_scale": "8.0",
            "steps": "25",
            "size": "768x1024",  # From EmptyLatentImage
            "scheduler": "normal",
        }
        mock_reader_instance.setting = (
            "Steps: 25, Sampler: euler, CFG scale: 8.0, Seed: 987654321, "
            "Size: 768x1024, Model: comfy_sdxl_model.safetensors, "
            "Scheduler: normal, Denoise: 1.0"  # Example
        )
        mock_reader_instance.raw = (
            self.comfy_example_prompt_str
        )  # ComfyUI parser stores prompt JSON as raw

        # Simulate ImageDataReader providing the info dict
        # In metadata_parser, ImageDataReader is called with file_path_named
        # For this test, we assume ImageDataReader correctly populates its attributes
        # based on the .png file containing the comfy_example_prompt_str

        result = parse_metadata("fake_comfy_image.png")

        MockImageDataReader.assert_called_once_with("fake_comfy_image.png")
        self.assertIn(UpField.PROMPT.value, result)
        self.assertEqual(
            result[UpField.PROMPT.value].get("Positive"),
            "positive prompt for ComfyUI test",
        )
        self.assertIn(DownField.GENERATION_DATA.value, result)
        gen_data = result[DownField.GENERATION_DATA.value]
        self.assertEqual(gen_data.get("Seed"), "987654321")
        self.assertEqual(gen_data.get("Model"), "comfy_sdxl_model.safetensors")
        self.assertEqual(gen_data.get("Size"), "768x1024")
        self.assertIn(UpField.METADATA.value, result)
        self.assertEqual(result[UpField.METADATA.value].get("Detected Tool"), "ComfyUI")
        self.assertIn(
            DownField.RAW_DATA.value, result
        )  # Raw data should be the prompt JSON
        self.assertEqual(
            result[DownField.RAW_DATA.value], self.comfy_example_prompt_str
        )

    @patch("dataset_tools.metadata_parser.ImageDataReader")
    @patch("dataset_tools.metadata_parser.MetadataFileReader")
    def test_parse_metadata_standard_exif_fallback(
        self, MockMetadataFileReader, MockImageDataReader
    ):
        mock_sdpr_instance = MockImageDataReader.return_value
        mock_sdpr_instance.status = (
            BaseFormat.Status.FORMAT_ERROR
        )  # Simulate AI parsing failure
        mock_sdpr_instance.tool = "Unknown"  # Or None
        mock_sdpr_instance.raw = "Some unparseable AI data"
        mock_sdpr_instance.error = "AI Parser failed"

        mock_mfr_instance = MockMetadataFileReader.return_value
        mock_mfr_instance.read_jpg_header_pyexiv2.return_value = {
            "EXIF": {"Exif.Image.Make": "Canon", "Exif.Image.Model": "EOS R5"},
            "XMP": {
                "Xmp.dc.creator": ["Test Author"],
                "Xmp.dc.description": {"x-default": "A test image"},
            },
            "IPTC": {},  # Empty IPTC
        }
        mock_mfr_instance.read_png_header_pyexiv2.return_value = None

        result_jpg = parse_metadata("standard_photo.jpg")
        MockImageDataReader.assert_called_with("standard_photo.jpg")
        MockMetadataFileReader.assert_called_once()
        mock_mfr_instance.read_jpg_header_pyexiv2.assert_called_once_with(
            "standard_photo.jpg"
        )

        self.assertNotIn(UpField.PROMPT.value, result_jpg)  # No AI prompts
        self.assertIn(DownField.EXIF.value, result_jpg)
        self.assertEqual(result_jpg[DownField.EXIF.value]["Camera Make"], "Canon")
        self.assertIn(UpField.TAGS.value, result_jpg)
        self.assertEqual(result_jpg[UpField.TAGS.value]["Artist"], "Test Author")
        # Raw data from failed AI parse should still be present
        self.assertIn(DownField.RAW_DATA.value, result_jpg)
        self.assertEqual(
            result_jpg[DownField.RAW_DATA.value], "Some unparseable AI data"
        )

        MockImageDataReader.reset_mock()
        MockMetadataFileReader.reset_mock()
        mock_mfr_instance.reset_mock()

        mock_sdpr_instance_png = MockImageDataReader.return_value
        mock_sdpr_instance_png.status = BaseFormat.Status.FORMAT_ERROR
        mock_sdpr_instance_png.tool = "Unknown"
        mock_sdpr_instance_png.raw = None  # No AI raw data this time

        mock_mfr_instance_png = MockMetadataFileReader.return_value
        mock_mfr_instance_png.read_png_header_pyexiv2.return_value = {
            "XMP": {"Xmp.dc.title": ["PNG Title"]},
            "EXIF": {},
            "IPTC": {},
        }
        mock_mfr_instance_png.read_jpg_header_pyexiv2.return_value = None

        result_png = parse_metadata("standard_photo.png")
        MockImageDataReader.assert_called_with("standard_photo.png")
        mock_mfr_instance_png.read_png_header_pyexiv2.assert_called_once_with(
            "standard_photo.png"
        )
        self.assertIn(UpField.TAGS.value, result_png)
        self.assertEqual(result_png[UpField.TAGS.value]["Title"], "PNG Title")
        self.assertNotIn(
            DownField.RAW_DATA.value, result_png
        )  # Since mock_sdpr_instance_png.raw was None

    @patch("dataset_tools.metadata_parser.ImageDataReader")
    def test_parse_metadata_txt_file(self, MockImageDataReader):
        # This test now assumes ImageDataReader handles .txt files internally
        # and parse_metadata calls ImageDataReader for .txt files.
        # The `with open(...)` part happens inside parse_metadata before calling ImageDataReader.

        mock_reader_instance = MockImageDataReader.return_value
        mock_reader_instance.status = BaseFormat.Status.READ_SUCCESS
        mock_reader_instance.tool = "TXT File"  # Example tool name for text files
        mock_reader_instance.raw = "This is test text content."
        # How ImageDataReader populates these for a .txt file:
        mock_reader_instance.positive = "This is test text content."
        mock_reader_instance.negative = ""
        mock_reader_instance.parameter = {}  # No specific parameters for plain text
        mock_reader_instance.setting = ""
        mock_reader_instance.width = "0"
        mock_reader_instance.height = "0"
        mock_reader_instance.is_sdxl = False
        mock_reader_instance.positive_sdxl = {}
        mock_reader_instance.negative_sdxl = {}

        file_path = "test.txt"
        # We need to mock `open` if we are testing the part of parse_metadata
        # that opens the file BEFORE passing to ImageDataReader.
        with patch(
            "builtins.open",
            new_callable=mock_open,
            read_data="This is test text content.",
        ) as mock_file:
            result = parse_metadata(file_path)
            mock_file.assert_called_once_with(
                file_path, "r", encoding="utf-8", errors="replace"
            )

        # Check that ImageDataReader was called with the file object and is_txt=True
        MockImageDataReader.assert_called_once()
        call_args = MockImageDataReader.call_args
        self.assertTrue(
            hasattr(call_args[0][0], "read"),
            "ImageDataReader should be called with a file object",
        )
        self.assertEqual(call_args[1], {"is_txt": True})  # Check kwargs

        self.assertIn(UpField.PROMPT.value, result)
        self.assertEqual(
            result[UpField.PROMPT.value].get("Positive"), "This is test text content."
        )
        self.assertIn(DownField.RAW_DATA.value, result)
        self.assertEqual(result[DownField.RAW_DATA.value], "This is test text content.")
        self.assertIn(UpField.METADATA.value, result)
        self.assertEqual(
            result[UpField.METADATA.value].get("Detected Tool"), "TXT File"
        )

    @patch("dataset_tools.metadata_parser.ImageDataReader")
    def test_parse_metadata_imagedatareader_general_failure(self, MockImageDataReader):
        mock_reader_instance = MockImageDataReader.return_value
        mock_reader_instance.status = BaseFormat.Status.FORMAT_ERROR
        mock_reader_instance.tool = "SomeTool"
        mock_reader_instance.raw = "corrupted data string"
        mock_reader_instance.error = (
            "Specific parser error from SomeTool"  # Crucial for new error message
        )

        result = parse_metadata("corrupted_image.png")

        MockImageDataReader.assert_called_once_with("corrupted_image.png")
        self.assertIn(EmptyField.PLACEHOLDER.value, result)
        error_dict = result[EmptyField.PLACEHOLDER.value]
        self.assertIn("Error", error_dict)

        # Updated assertion based on new error message format in parse_metadata
        expected_error_msg = "Vendored parser (SomeTool, status FORMAT_ERROR) failed. Detail: Specific parser error from SomeTool"
        self.assertEqual(error_dict["Error"], expected_error_msg)

        self.assertIn(
            DownField.RAW_DATA.value, result
        )  # Raw data should still be populated
        self.assertEqual(result[DownField.RAW_DATA.value], "corrupted data string")

    @patch(
        "dataset_tools.metadata_parser.ImageDataReader",
        side_effect=FileNotFoundError("Mocked File Not Found by IDR"),
    )
    def test_parse_metadata_file_not_found_by_imagedatareader(
        self, MockImageDataReader
    ):
        # This tests when ImageDataReader itself (e.g., Image.open inside it) raises FileNotFoundError
        result = parse_metadata("non_existent_image.png")

        MockImageDataReader.assert_called_once_with("non_existent_image.png")
        self.assertIn(EmptyField.PLACEHOLDER.value, result)
        error_dict = result[EmptyField.PLACEHOLDER.value]
        self.assertIn("Error", error_dict)
        # Error comes from the general `except Exception as e_vsdpr:` in parse_metadata
        self.assertEqual(
            error_dict["Error"], "AI Parser Error: Mocked File Not Found by IDR"
        )

    # --- Tests for Helper Functions ---
    def test_make_paired_str_dict_various_inputs(self):
        self.assertEqual(
            make_paired_str_dict("Steps: 20, Sampler: Euler"),
            {"Steps": "20", "Sampler": "Euler"},
        )
        # Corrected expected output: outer quotes on values should be stripped by make_paired_str_dict
        self.assertEqual(
            make_paired_str_dict(
                'Lora hashes: "lora1:hashA, lora2:hashB", TI hashes: "ti1:hashC"'
            ),
            {"Lora hashes": "lora1:hashA, lora2:hashB", "TI hashes": "ti1:hashC"},
        )
        # Test with the complex string and the improved regex (this will depend on the final regex)
        # This test will likely FAIL until make_paired_str_dict's regex is perfected.
        a1111_settings = 'Steps: 30, Sampler: Euler a, Schedule type: Automatic, CFG scale: 7, Seed: 539894433, Size: 832x1216, Model hash: 137ebf59ea, Model: KN-VanguardMix.fp16, Denoising strength: 0.3, Clip skip: 2, Hashes: {"model": "137ebf59ea"}, Hires Module 1: Built-in, Hires CFG Scale: 1, Hires upscale: 2, Hires steps: 15, Hires upscaler: 4x_Fatality_Comix_260000_G, Version: f2.0.1v1.10.1-previous-659-gc055f2d4, Module 1: sdxl_vae'
        parsed_a1111 = make_paired_str_dict(a1111_settings)
        self.assertEqual(parsed_a1111.get("Steps"), "30")
        self.assertEqual(parsed_a1111.get("Sampler"), "Euler a")
        self.assertEqual(
            parsed_a1111.get("Hashes"), '{"model": "137ebf59ea"}'
        )  # Value is JSON string
        self.assertEqual(parsed_a1111.get("Module 1"), "sdxl_vae")
        # Add more assertions for other keys from a1111_settings if make_paired_str_dict is expected to parse them all

        self.assertEqual(make_paired_str_dict(""), {})
        self.assertEqual(make_paired_str_dict(None), {})  # type: ignore # Test None explicitly

    @patch("dataset_tools.metadata_parser.nfo")
    def test_process_pyexiv2_data_full(
        self, mock_nfo_logger_ignored
    ):  # Renamed mock_nfo_logger
        pyexiv2_input = {
            "EXIF": {
                "Exif.Image.Make": "Canon",
                "Exif.Image.Model": "EOS R5",
                "Exif.Photo.DateTimeOriginal": "2023:01:01 10:00:00",
                "Exif.Photo.UserComment": "Standard User Comment test",  # Test simple string UserComment
                "Exif.Photo.FNumber": 2.8,
                "Exif.Photo.ISOSpeedRatings": 100,
            },
            "XMP": {
                "Xmp.dc.creator": ["Photographer A", "Photographer B"],
                "Xmp.dc.description": {"x-default": "A test image with XMP"},
                "Xmp.photoshop.DateCreated": "2023-01-01T10:00:00",
            },
            "IPTC": {
                "Iptc.Application2.Keywords": ["test", "photo", "IPTC tag"],
                "Iptc.Application2.Caption": "IPTC Caption for image",
            },
        }
        # This expected output should match EXACTLY what your process_pyexiv2_data produces,
        # including key names and value formatting.
        expected_output = {
            DownField.EXIF.value: {  # Assuming DownField.EXIF.value resolves to "standard_exif_data_section"
                "Camera Make": "Canon",
                "Camera Model": "EOS R5",
                "Date Taken": "2023:01:01 10:00:00",
                "Usercomment (std.)": "Standard User Comment test",  # Check your func's exact key name
                # "Fnumber": "2.8", # Add if your function extracts these
                # "Iso": "100",
            },
            UpField.TAGS.value: {  # Assuming UpField.TAGS.value resolves to "tags_and_keywords_section"
                "Artist": "Photographer A, Photographer B",
                "Description": "A test image with XMP",
                "Date created (xmp)": "2023-01-01T10:00:00",  # Check your func's exact key name
                "Keywords (iptc)": "test, photo, IPTC tag",  # Check your func's exact key name
                "Caption (iptc)": "IPTC Caption for image",  # Check your func's exact key name
            },
        }

        actual_output = process_pyexiv2_data(
            pyexiv2_input, ai_tool_parsed=False
        )  # Test with ai_tool_parsed=False

        # Compare section by section
        if DownField.EXIF.value in expected_output:
            self.assertIn(DownField.EXIF.value, actual_output, "EXIF section missing")
            self.assertDictEqual(
                actual_output[DownField.EXIF.value],
                expected_output[DownField.EXIF.value],
                "EXIF data mismatch",
            )
        else:
            self.assertNotIn(
                DownField.EXIF.value, actual_output, "EXIF section unexpectedly present"
            )

        if UpField.TAGS.value in expected_output:
            self.assertIn(UpField.TAGS.value, actual_output, "TAGS section missing")
            self.assertDictEqual(
                actual_output[UpField.TAGS.value],
                expected_output[UpField.TAGS.value],
                "TAGS data mismatch",
            )
        else:
            self.assertNotIn(
                UpField.TAGS.value, actual_output, "TAGS section unexpectedly present"
            )

        # Test with ai_tool_parsed=True to see if UserComment is skipped
        actual_output_ai_parsed = process_pyexiv2_data(
            pyexiv2_input, ai_tool_parsed=True
        )
        if (
            DownField.EXIF.value in actual_output_ai_parsed
        ):  # Check if EXIF section still exists
            self.assertNotIn(
                "Usercomment (std.)",
                actual_output_ai_parsed[DownField.EXIF.value],
                "UserComment should be skipped when ai_tool_parsed is True and it's not AI data",
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
