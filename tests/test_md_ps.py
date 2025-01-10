# pylint: disable=line-too-long, missing-class-docstring

import os
import unittest
from unittest.mock import Mock, patch

from dataset_tools import logger
from dataset_tools.access_disk import FileReader
from dataset_tools.metadata_parser import (
    arrange_webui_metadata,
    delineate_escape_codes,
    make_paired_str_dict,
    extract_partial_mappings,
    extract_prompts,
    arrange_nodeui_metadata,
    rename_next_keys_of
)
from typing import TypedDict

class TestParseMetadata(unittest.TestCase):
    def setUp(self):
        self.reader = FileReader()
        self.prompt = {
            "Positive prompt": "Hell4ineXLPOS  solo, long hair, looking at viewer, 1boy, jewelry, closed mouth, upper body, white hair, male focus, wings, necklace, border, cross, black wings,",
            "Negative prompt": "Negative prompt: XL_Neg",
        }
        self.deprompted = 'Steps: 30, Sampler: Euler a, Schedule type: Automatic, CFG scale: 7, Seed: 970527942, Size: 832x1216, Model hash: 238ffac319, Model: HellaineMixXL-FIX.fp16, VAE hash: 63aeecb90f, VAE: sdxl_vae.safetensors, Denoising strength: 0.35, Clip skip: 2, Hashes: {"model": "238ffac319", "embed:Hell4ineXLPOS": "23f5e3fc03", "vae": "63aeecb90f"}, Hires upscale: 1.5, Hires steps: 30, Hires upscaler: 4x_foolhardy_Remacri, TI hashes: "Hell4ineXLPOS: 23f5e3fc030a, Hell4ineXLPOS: 23f5e3fc030a", Hardware Info: "RTX 4090 24GB, Threadripper PRO 5975WX 32-s, 252GB RAM", Time taken: 18.0 sec., Version: v1.10.0'
        self.enclosed_value_return = (
            "Hell4ineXLPOS  solo, long hair, looking at viewer, 1boy, jewelry, closed mouth, upper body, white hair, male focus, wings, necklace, border, cross, black wings,Negative prompt: XL_NegSteps: 30, Sampler: Euler a, Schedule type: Automatic, CFG scale: 7, Seed: 970527942, Size: 832x1216, Model hash: 238ffac319, Model: HellaineMixXL-FIX.fp16, VAE hash: 63aeecb90f, VAE: sdxl_vae.safetensors, Denoising strength: 0.35, Clip skip: 2, , Hires upscale: 1.5, Hires steps: 30, Hires upscaler: 4x_foolhardy_Remacri, , , Time taken: 18.0 sec., Version: v1.10.0",
            {
                "Hashes": '{"model": "238ffac319", "embed:Hell4ineXLPOS": "23f5e3fc03", "vae": "63aeecb90f"}',
                'TI hashes: "Hell4ineXLPOS: 23f5e3fc030a, Hell4ineXLPOS: 23f5e3fc030a"': "Hell4ineXLPOS: 23f5e3fc030a, Hell4ineXLPOS: 23f5e3fc030a",
                'Hardware Info: "RTX 4090 24GB, Threadripper PRO 5975WX 32-s, 252GB RAM"': "RTX 4090 24GB, Threadripper PRO 5975WX 32-s, 252GB RAM",
            },
        )
        self.correct_hash = {
            "Hashes": '{"model": "238ffac319", "embed:Hell4ineXLPOS": "23f5e3fc03", "vae": "63aeecb90f"}',
            "TI hashes": '"Hell4ineXLPOS: 23f5e3fc030a, Hell4ineXLPOS: 23f5e3fc030a", Hardware Info: "RTX 4090 24GB, Threadripper PRO 5975WX 32-s, 252GB RAM"',
        }
        self.correct_dehashed = "Steps: 30, Sampler: Euler a, Schedule type: Automatic, CFG scale: 7, Seed: 970527942, Size: 832x1216, Model hash: 238ffac319, Model: HellaineMixXL-FIX.fp16, VAE hash: 63aeecb90f, VAE: sdxl_vae.safetensors, Denoising strength: 0.35, Clip skip: 2, Hires upscale: 1.5, Hires steps: 30, Hires upscaler: 4x_foolhardy_Remacri, Time taken: 18.0 sec., Version: v1.10.0"

    def test_delineate_escape_codes(self):
        mock_header_data = {"parameters": '1 2 3 4\u200b\u200b\u200b5\n6\n7\n8\xe2\x80\x8b\xe2\x80\x8b\xe2\x80\x8b9\n10\n11\n12\x00\x00\u200bbingpot\x00\n'}
        formatted_chunk = delineate_escape_codes(mock_header_data)
        logger.debug("%s", f"{list(x for x in formatted_chunk)}")
        assert formatted_chunk == ['1 2 3 4', '5', '6', '7', '8', '9', '10', '11', '12', 'bingpot']

    def test_extract_prompts(self):
        mock_extract_data = ["Lookie Lookie, all, the, terms,in, the prompt, wao","Negative prompt: no bad, only 5 fingers", "theres some other data here whatever"]
        prompt, deprompted_segments = extract_prompts(mock_extract_data)
        assert deprompted_segments == 'theres some other data here whatever'
        assert prompt == {'Negative prompt': 'no bad, only 5 fingers', 'Positive prompt': 'Lookie Lookie, all, the, terms,in, the prompt, wao'}

    def test_extract_partial_mappings(self):
        mock_partial_map = 'A: long, test: string, With: {"Some": "useful", "although": "also"}, Some: useless, data: thrown, in: as, well: !!, Only: "The": "best", "Algorithm": "Will", "Successfully": "Match", All, Correctly! !'
        hashes, dehashed_text = extract_partial_mappings(mock_partial_map)
        logger.debug(hashes)
        # logger.debug(dehashed_text)
        assert hashes ==  {'With': '{"Some": "useful", "although": "also"}', 'Only': '{"The": "best", "Algorithm": "Will", "Successfully": "Match"}'}
        assert dehashed_text == "A: long, test: string, Some: useless, data: thrown, in: as, well: !!, All, Correctly! !"

    def test_make_paired_str_dict(self):
        mock_string_data = "Who: the, Hell: makes, Production: code, Work: like, This: tho, i: say, as: i, make: the, same: mistakes"
        final_text = make_paired_str_dict(mock_string_data)
        logger.debug("%s", f"{final_text}")
        assert final_text == {"Who": "the", "Hell": "makes", "Production": "code", "Work": "like", "This": "tho", "i": "say", "as": "i", "make": "the", "same": "mistakes"}

    def test_arrange_webui_metadata(self):
        mock_delineate_escape_codes = Mock(return_value=["a", "b","1","2","y","z"])
        mock_extract_prompts = Mock(return_value={"Positive": "yay", "Negative": "boo"})
        mock_extract_partial_mappings = Mock(return_value=({"key": "value"}, "almost: right, but: not"))
        mock_make_paired_str_dict = Mock(return_value=({"Okay": "Right"}, {"This": "Time"}))

        with (
            patch("dataset_tools.metadata_parser.delineate_escape_codes", mock_delineate_escape_codes),
            patch("dataset_tools.metadata_parser.extract_prompts", mock_extract_prompts),
            patch("dataset_tools.metadata_parser.extract_partial_mappings", mock_extract_partial_mappings),
            patch("dataset_tools.metadata_parser.make_paired_str_dict", mock_make_paired_str_dict),
        ):
            result = arrange_webui_metadata("header header_data")

            assert mock_delineate_escape_codes.call_count == 1
            assert "Prompts" in result and "Generation_Data" in result and "System" in result

    # def test_arrange_nodeui_metadata():
    #     mock_prompt_map = ""
    #     mock_gen_data = ""
    #     # Mock data and calls
    #     mock_clean = {"CLIPTextEncode": {"inputs": {"text": "prompt, more prompt, extra prompt"}}}
    #     with patch('dataset_tools.metadata_parser.clean_with_json', return_value=mock_clean), \
    #         patch('dataset_tools.metadata_parser.dig_nested_values', return_value=(mock_prompt_map, mock_gen_data)):
    #         result = arrange_nodeui_metadata(mock_clean)
    #         expected_prompts = ""
    #         assert result["Prompts"] == expected_prompts
    #         expected_gen_data = ""
    #         assert result["Generation_Data"] == expected_gen_data

    def test_rename_next_keys_of_not_prompt(self):
        mock_dict = {"3" : {'inputs': {'seed': 948476150837611, 'steps': 60, 'cfg': 12.0, 'sampler_name': 'dpmpp_2m', 'scheduler': 'karras', 'denoise': 1.0, 'model': ['14', 0], 'positive': ['6', 0], 'negative': ['7', 0], 'latent_image': ['5', 0]}, 'class_type': 'KSampler'}}
        extracted = rename_next_keys_of(mock_dict, "CLIPTextEncode", ["Positive prompt", "Negative prompt", "Prompt"])
        expected_extracted = { 'KSampler': {'seed': 948476150837611, 'steps': 60, 'cfg': 12.0, 'sampler_name': 'dpmpp_2m', 'scheduler': 'karras', 'denoise': 1.0, 'model': ['14', 0], 'positive': ['6', 0], 'negative': ['7', 0], 'latent_image': ['5', 0]}}
        assert extracted == expected_extracted

    def test_rename_next_keys_of_prompt(self):
        mock_dict = {"3" : {'inputs': {"text": "a long and thought out text prompt"}, 'class_type': 'CLIPTextEncode'}}
        extracted = rename_next_keys_of(mock_dict, "CLIPTextEncode", ["Positive prompt", "Negative prompt", "Prompt"])
        expected_extracted = {"Positive prompt": "a long and thought out text prompt"}
        assert extracted == expected_extracted

if __name__ == "__main__":
    unittest.main()
