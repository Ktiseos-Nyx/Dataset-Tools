# tests/test_md_ps.py
"""Tests for metadata_parser module, focusing on integration and helper functions."""

import json
import unittest
from unittest.mock import MagicMock, patch  # Added MagicMock

from dataset_tools.correct_types import DownField, UpField
from dataset_tools.metadata_parser import (
    make_paired_str_dict,
    parse_metadata,
    process_pyexiv2_data,
)
from dataset_tools.vendored_sdpr.format import BaseFormat


class TestParseMetadataIntegration(unittest.TestCase):
    """Tests the main parse_metadata function with various mocked inputs."""

    def setUp(self) -> None:
        """Set up example raw parameter strings for tests."""
        self.a1111_example_raw_params = (
            "positive prompt test from a1111\n"
            "Negative prompt: negative prompt test from a1111\n"
            "Steps: 30, Sampler: DPM++ 2M Karras, CFG scale: 7.5, Seed: 1234567890, "
            "Size: 512x768, Model hash: abcdef1234, Model: test_model_a1111.safetensors, "
            "Clip skip: 2, ENSD: 31337"
        )
        self.comfy_example_prompt_str = json.dumps(
            {
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
        self.comfy_example_workflow_str = json.dumps({"nodes": [], "links": []})

    @patch("dataset_tools.metadata_parser.ImageDataReader")
    def test_parse_metadata_a1111_success(self, mock_image_data_reader: MagicMock) -> None:
        """Test successful parsing of A1111 metadata via parse_metadata."""
        mock_reader_instance = mock_image_data_reader.return_value
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
            "clip_skip": "2",
        }
        mock_reader_instance.width = "512"
        mock_reader_instance.height = "768"
        mock_reader_instance.setting = (  # Line break for readability
            "Steps: 30, Sampler: DPM++ 2M Karras, CFG scale: 7.5, Seed: 1234567890, "
            "Size: 512x768, Model hash: abcdef1234, Model: test_model_a1111.safetensors, "
            "Clip skip: 2, ENSD: 31337"
        )
        mock_reader_instance.raw = self.a1111_example_raw_params

        result = parse_metadata("fake_a1111_image.png")

        mock_image_data_reader.assert_called_once_with("fake_a1111_image.png")
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
        self.assertEqual(gen_data.get("Sampler"), "DPM++ 2M Karras")
        self.assertEqual(gen_data.get("Model"), "test_model_a1111.safetensors")
        self.assertIn(UpField.METADATA.value, result)
        self.assertEqual(result[UpField.METADATA.value].get("Detected Tool"), "A1111 webUI")

    # ... (other test methods with similar docstring and type hint additions) ...

    def test_make_paired_str_dict_various_inputs(self) -> None:
        """Test the make_paired_str_dict helper with various inputs."""
        self.assertEqual(
            make_paired_str_dict("Steps: 20, Sampler: Euler"),
            {"Steps": "20", "Sampler": "Euler"},
        )
        self.assertEqual(
            make_paired_str_dict('Lora hashes: "lora1:hashA, lora2:hashB", TI hashes: "ti1:hashC"'),
            {"Lora hashes": "lora1:hashA, lora2:hashB", "TI hashes": "ti1:hashC"},
        )
        a1111_settings = (
            "Steps: 30, Sampler: Euler a, Schedule type: Automatic, CFG scale: 7, Seed: 539894433, "
            "Size: 832x1216, Model hash: 137ebf59ea, Model: KN-VanguardMix.fp16, "
            'Denoising strength: 0.3, Clip skip: 2, Hashes: {"model": "137ebf59ea"}, '
            "Hires Module 1: Built-in, Hires CFG Scale: 1, Hires upscale: 2, Hires steps: 15, "
            "Hires upscaler: 4x_Fatality_Comix_260000_G, Version: f2.0.1v1.10.1-previous-659-gc055f2d4, "
            "Module 1: sdxl_vae"
        )
        parsed_a1111 = make_paired_str_dict(a1111_settings)
        self.assertEqual(parsed_a1111.get("Steps"), "30")
        self.assertEqual(parsed_a1111.get("Sampler"), "Euler a")
        self.assertEqual(parsed_a1111.get("Hashes"), '{"model": "137ebf59ea"}')
        self.assertEqual(parsed_a1111.get("Module 1"), "sdxl_vae")
        self.assertEqual(make_paired_str_dict(""), {})
        self.assertEqual(make_paired_str_dict(None), {})  # type: ignore

    @patch("dataset_tools.metadata_parser.nfo")
    def test_process_pyexiv2_data_full(self, mock_nfo_logger: MagicMock) -> None:  # Renamed and typed mock
        """Test processing of full EXIF, XMP, and IPTC data from pyexiv2 format."""
        # ... (rest of the test, ensuring long strings or dicts are formatted for readability)
        pyexiv2_input = {
            "EXIF": {
                "Exif.Image.Make": "Canon",
                "Exif.Image.Model": "EOS R5",
                "Exif.Photo.DateTimeOriginal": "2023:01:01 10:00:00",
                "Exif.Photo.UserComment": "Standard User Comment test",
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
        expected_output = {
            DownField.EXIF.value: {
                "Camera Make": "Canon",
                "Camera Model": "EOS R5",
                "Date Taken": "2023:01:01 10:00:00",
                "Usercomment (std.)": "Standard User Comment test",
            },
            UpField.TAGS.value: {
                "Artist": "Photographer A, Photographer B",
                "Description": "A test image with XMP",
                "Date created (xmp)": "2023-01-01T10:00:00",
                "Keywords (iptc)": "test, photo, IPTC tag",
                "Caption (iptc)": "IPTC Caption for image",
            },
        }
        actual_output = process_pyexiv2_data(pyexiv2_input, ai_tool_parsed=False)
        # ... (rest of assertions) ...
        if DownField.EXIF.value in expected_output:
            self.assertIn(DownField.EXIF.value, actual_output, "EXIF section missing")
            self.assertDictEqual(
                actual_output[DownField.EXIF.value],
                expected_output[DownField.EXIF.value],
                "EXIF data mismatch",
            )
        else:
            self.assertNotIn(DownField.EXIF.value, actual_output, "EXIF section unexpectedly present")
        if UpField.TAGS.value in expected_output:
            self.assertIn(UpField.TAGS.value, actual_output, "TAGS section missing")
            self.assertDictEqual(
                actual_output[UpField.TAGS.value],
                expected_output[UpField.TAGS.value],
                "TAGS data mismatch",
            )
        else:
            self.assertNotIn(UpField.TAGS.value, actual_output, "TAGS section unexpectedly present")
        actual_output_ai_parsed = process_pyexiv2_data(pyexiv2_input, ai_tool_parsed=True)
        if DownField.EXIF.value in actual_output_ai_parsed:
            self.assertNotIn(
                "Usercomment (std.)",
                actual_output_ai_parsed[DownField.EXIF.value],
                "UserComment should be skipped",
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
