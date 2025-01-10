# pylint: disable=line-too-long, missing-class-docstring

import unittest
from unittest.mock import Mock, patch

from dataset_tools import logger
from dataset_tools.access_disk import MetadataFileReader
from dataset_tools.metadata_parser import (
    arrange_webui_metadata,
    delineate_by_esc_codes,
    make_paired_str_dict,
    extract_dict_by_delineation,
    extract_prompts,
    # arrange_nodeui_metadata,
    validate_dictionary_structure,
    rename_next_keys_of,
    # clean_with_json
)


class TestParseMetadata(unittest.TestCase):
    def setUp(self):
        self.reader = MetadataFileReader()
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

        self.actual_a1111_metadata = [
            "PonyXLV6_Scores GrungeOutfiPDXL_ GlamorShots_PDXL PDXL_FLWRBOY",
            'Steps: 30, Sampler: Euler a, Schedule type: Automatic, CFG scale:  7, Hires upscaler: 4x_foolhardy_Remacri, TI hashes: "PonyXLV6_Scores: 4b8555f2fb80, GrungeOutfiPDXL_: b6af61969ec4, GlamorShots_PDXL: 4b8ee3d1bd12, PDXL_FLWRBOY:  af38cbdc40f6", Version: v1.10.0',
        ]
        self.actual_metadata_str = (
            '{"PonyXLV6_Scores: 4b8555f2fb80, GrungeOutfiPDXL_: b6af61969ec4, GlamorShots_PDXL: 4b8ee3d1bd12, PDXL_FLWRBOY:  af38cbdc40f6}',
        )
        self.actual_metadata_sub_map = [
            "TI hashes",
            "PonyXLV6_Scores: 4b8555f2fb80, GrungeOutfiPDXL_: b6af61969ec4, GlamorShots_PDXL: 4b8ee3d1bd12, PDXL_FLWRBOY:  af38cbdc40f6, PonyXLV6_Scores: 4b8555f2fb80, GrungeOutfiPDXL_: b6af61969ec4, GlamorShots_PDXL: 4b8ee3d1bd12, PDXL_FLWRBOY:  af38cbdc40f6",
        ]
        self.possibly_valid = "{PonyXLV6_Scores: 4b8555f2fb80, GrungeOutfiPDXL_: b6af61969ec4, GlamorShots_PDXL: 4b8ee3d1bd12, PDXL_FLWRBOY:  af38cbdc40f6, PonyXLV6_Scores: 4b8555f2fb80, GrungeOutfiPDXL_: b6af61969ec4, GlamorShots_PDXL: 4b8ee3d1bd12, PDXL_FLWRBOY:  af38cbdc40f6}"

    def test_delineate_by_esc_codes(self):
        mock_header_data = {
            "parameters": "1 2 3 4\u200b\u200b\u200b5\n6\n7\n8\xe2\x80\x8b\xe2\x80\x8b\xe2\x80\x8b9\n10\n11\n12\x00\x00\u200bbingpot\x00\n"
        }
        formatted_chunk = delineate_by_esc_codes(mock_header_data)
        logger.debug("%s", f"{list(x for x in formatted_chunk)}")
        assert formatted_chunk == [
            "1 2 3 4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "12",
            "bingpot",
        ]

    def test_extract_prompts(self):
        mock_extract_data = [
            "Lookie Lookie, all, the, terms,in, the prompt, wao",
            "Negative prompt: no bad, only 5 fingers",
            "theres some other data here whatever",
        ]
        prompt, deprompted_segments = extract_prompts(mock_extract_data)
        assert deprompted_segments == "theres some other data here whatever"
        assert prompt == {
            "Negative prompt": "no bad, only 5 fingers",
            "Positive prompt": "Lookie Lookie, all, the, terms,in, the prompt, wao",
        }

    def test_extract_dict_by_delineation(self):
        mock_partial_map = 'A: long, test: string, With: {"Some": "useful", "although": "also"}, Some: useless, data: thrown, in: as, well: !!, Only: "The": "best", "Algorithm": "Will", "Successfully": "Match", All, Correctly! !'
        hashes, dehashed_text = extract_dict_by_delineation(mock_partial_map)
        logger.debug(hashes)
        # logger.debug(dehashed_text)
        assert hashes == {
            # "A": "{long}",
            "With": '{"Some": "useful", "although": "also"}',
            "Only": '{"The": "best", "Algorithm": "Will", "Successfully": "Match"}',
        }
        assert (
            dehashed_text
            == "A: long, test: string, Some: useless, data: thrown, in: as, well: !!, All, Correctly! !"
        )

    def test_make_paired_str_dict(self):
        mock_string_data = "Who: the, Hell: makes, Production: code, Work: like, This: tho, i: say, as: i, make: the, same: mistakes"
        final_text = make_paired_str_dict(mock_string_data)
        logger.debug("%s", f"{final_text}")
        assert final_text == {
            "Who": "the",
            "Hell": "makes",
            "Production": "code",
            "Work": "like",
            "This": "tho",
            "i": "say",
            "as": "i",
            "make": "the",
            "same": "mistakes",
        }

    def test_arrange_webui_metadata(self):
        mock_delineate_by_esc_codes = Mock(return_value=["a", "b", "1", "2", "y", "z"])
        mock_extract_prompts = Mock(return_value={"Positive": "yay", "Negative": "boo"})
        mock_extract_dict_by_delineation = Mock(
            return_value=({"key": "value"}, "almost: right, but: not")
        )
        mock_make_paired_str_dict = Mock(
            return_value=({"Okay": "Right"}, {"This": "Time"})
        )

        with (
            patch(
                "dataset_tools.metadata_parser.delineate_by_esc_codes",
                mock_delineate_by_esc_codes,
            ),
            patch(
                "dataset_tools.metadata_parser.extract_prompts", mock_extract_prompts
            ),
            patch(
                "dataset_tools.metadata_parser.extract_dict_by_delineation",
                mock_extract_dict_by_delineation,
            ),
            patch(
                "dataset_tools.metadata_parser.make_paired_str_dict",
                mock_make_paired_str_dict,
            ),
        ):
            result = arrange_webui_metadata("header header_data")

            assert mock_delineate_by_esc_codes.call_count == 1
            assert (
                "Prompts" in result
                and "Generation_Data" in result
                and "System" in result
            )

    def test_rename_next_keys_of_not_prompt(self):
        mock_dict = {
            "3": {
                "inputs": {
                    "seed": 948476150837611,
                    "steps": 60,
                    "cfg": 12.0,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": 1.0,
                    "model": ["14", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
                "class_type": "KSampler",
            }
        }
        extracted = rename_next_keys_of(
            mock_dict,
            "CLIPTextEncode",
            ["Positive prompt", "Negative prompt", "Prompt"],
        )
        expected_extracted = {
            "KSampler": {
                "seed": 948476150837611,
                "steps": 60,
                "cfg": 12.0,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 1.0,
                "model": ["14", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            }
        }
        assert extracted == expected_extracted

    def test_rename_next_keys_of_prompt(self):
        mock_dict = {
            "3": {
                "inputs": {"text": "a long and thought out text prompt"},
                "class_type": "CLIPTextEncode",
            }
        }
        extracted = rename_next_keys_of(
            mock_dict,
            "CLIPTextEncode",
            ["Positive prompt", "Negative prompt", "Prompt"],
        )
        expected_extracted = {"Positive prompt": "a long and thought out text prompt"}
        assert extracted == expected_extracted

    def test_validate_dictionary_structure(self):
        # BracketedDict = type(
        #     "BracketedDict",
        #     (object,),
        #     {"model_validate": lambda x: {"brackets": "annotated_value"}},
        # )
        possibly_valid = validate_dictionary_structure(self.actual_metadata_sub_map)
        assert isinstance(possibly_valid, str)
        assert possibly_valid == self.valid_metadata_sub_map

    # def test_arrange_nodeui_metadata(self):
    #     # Mock data and calls
    #     mock_clean = {
    #         "prompt": {
    #             "3": {
    #                 "CLIPTextEncode": {
    #                     "inputs": {"text": "prompt, more prompt, extra prompt"}
    #                 }
    #             }
    #         }
    #     }

    #     result = arrange_nodeui_metadata(str(mock_clean))
    #     expected_prompts = ""
    #     assert result["Prompts"] == expected_prompts
    #     expected_gen_data = ""
    #     assert result["Generation_Data"] == expected_gen_data


if __name__ == "__main__":
    unittest.main()

# ['PonyXLV6_Scoresmetadata_parser.py:34 GrungeOutfiPDXL_ GlamorShots_PDXL PDXL_FLWRBOY', 'Steps: 30, Sampler: Euler a, Schedule type: Automatic, CFG scale:  7, Seed: 444906227, Size: 832x1216, Model hash:  5a7e5d791e, Model: PoltergeistCOMIX-PDXL.fp16,  Denoising strength: 0.2, Clip  skip: 2, ADetailer model: face_yolov8n.pt, ADetailer confidence: 0.3, ADetailer dilate erode: 4, ADetailer mask blur: 4, ADetailer denoising strength: 0.4, ADetailer inpaint only masked: True, ADetailer inpaint padding: 32, ADetailer model 2nd: Anzhc Head+Hair seg medium no dill.pt, ADetailer confidence  2nd: 0.3, ADetailer dilate erode 2nd: 4, ADetailer mask blur 2nd: 4, ADetailer denoising strength 2nd: 0.4, ADetailer inpaint only masked  2nd: True, ADetailer inpaint padding 2nd: 32, ADetailer version: 24.11.1, Hires upscale: 2, Hires steps: 30, Hires upscaler: 4x_foolhardy_Remacri, TI hashes: "PonyXLV6_Scores: 4b8555f2fb80, GrungeOutfiPDXL_: b6af61969ec4, GlamorShots_PDXL: 4b8ee3d1bd12, PDXL_FLWRBOY:  af38cbdc40f6, PonyXLV6_Scores: 4b8555f2fb80, GrungeOutfiPDXL_: b6af61969ec4, GlamorShots_PDXL: 4b8ee3d1bd12, PDXL_FLWRBOY:  af38cbdc40f6", Version: v1.10.0']
