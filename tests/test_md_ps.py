# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""Test Parser"""

# pylint: disable=line-too-long, missing-class-docstring

import unittest
from unittest.mock import Mock, patch, call

from pydantic import ValidationError

from dataset_tools.logger import logger
from dataset_tools.access_disk import MetadataFileReader
from dataset_tools.correct_types import UpField, DownField, EmptyField
from dataset_tools.metadata_parser import (
    arrange_webui_metadata,
    delineate_by_esc_codes,
    make_paired_str_dict,
    extract_dict_by_delineation,
    extract_prompts,
    coordinate_metadata_operations,
    arrange_nodeui_metadata,
    validate_mapping_bracket_pair_structure_of,
    filter_keys_of,
    parse_metadata,
    redivide_nodeui_data_in,
    validate_typical,
    # clean_with_json
)


class TestParseMetadata(unittest.TestCase):
    def setUp(self):
        self.reader = MetadataFileReader()
        self.actual_metadata_sub_map = [
            "TI hashes",
            "PonyXLV6_Scores: 4b8555f2fb80, GrungeOutfiPDXL_: b6af61969ec4, GlamorShots_PDXL: 4b8ee3d1bd12, PDXL_FLWRBOY:  af38cbdc40f6, PonyXLV6_Scores: 4b8555f2fb80, GrungeOutfiPDXL_: b6af61969ec4, GlamorShots_PDXL: 4b8ee3d1bd12, PDXL_FLWRBOY:  af38cbdc40f6",
        ]
        self.valid_metadata_sub_map = "{PonyXLV6_Scores: 4b8555f2fb80, GrungeOutfiPDXL_: b6af61969ec4, GlamorShots_PDXL: 4b8ee3d1bd12, PDXL_FLWRBOY:  af38cbdc40f6, PonyXLV6_Scores: 4b8555f2fb80, GrungeOutfiPDXL_: b6af61969ec4, GlamorShots_PDXL: 4b8ee3d1bd12, PDXL_FLWRBOY:  af38cbdc40f6}"
        self.test_is_dict_data = {"prompt": {"2": {"class_type": "deblah", "inputs": {"even_more_blah": "meh"}}}}
        self.test_delineate_mock_header = {"parameters": "1 2 3 4\u200b\u200b\u200b5\n6\n7\n8\xe2\x80\x8b\xe2\x80\x8b\xe2\x80\x8b9\n10\n11\n12\x00\x00\u200bbingpot\x00\n"}
        self.test_extract_prompts_mock_extract_data = [
            "Lookie Lookie, all, the, terms,in, the prompt, wao",
            "Negative prompt: no bad, only 5 fingers",
            "theres some other data here whatever",
        ]
        self.extract_dict_mock_partial_map = 'A: long, test: string, With: {"Some": "useful", "although": "also"}, Some: useless, data: thrown, in: as, well: !!, Only: "The": "best", "Algorithm": "Will", "Successfully": "Match", All, Correctly! !'
        self.mock_dict = {
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
        self.mock_bracket_dict_next_keys = {
            "Positive prompt": {"clip_l": "Red gauze tape spun around an invisible hand", "t5xxl": "Red gauze tape spun around an invisible hand"},
            "Negative prompt": {" "},
        }

        self.mock_bracket_dict_gen_data = {
            "inputs": {
                "seed": 1944739425534,
                "steps": 4,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["136", 0],
                "positive": ["110", 0],
                "negative": ["110", 1],
                "latent_image": ["88", 0],
            },
        }
        self.redivide_dict_test_data = {
            "2": {
                "inputs": {
                    "seed": 1944739425534,
                    "steps": 4,
                    "cfg": 1.0,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1.0,
                    "model": ["136", 0],
                    "positive": ["110", 0],
                    "negative": ["110", 1],
                    "latent_image": ["88", 0],
                },
                "class_type": "KSampler",
                "_meta": {"title": "3 KSampler"},
            },
            "109": {
                "inputs": {
                    "clip_l": "Red gauze tape spun around an invisible hand",
                    "t5xxl": "Red gauze tape spun around an invisible hand",
                    "guidance": 1.0,
                    "clip": ["136", 1],
                },
                "class_type": "CLIPTextEncodeFlux",
                "_meta": {"title": "CLIPTextEncodeFlux"},
            },
            "113": {
                "inputs": {"text": "", "clip": ["136", 1]},
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "2b Negative [CLIP Text Encode (Prompt)]"},
            },
        }
        self.new_prompt_dict_labels = ["Positive prompt", "Negative prompt", "Prompt"]

    def test_delineate_by_esc_codes(self):
        """test"""
        formatted_chunk = delineate_by_esc_codes(self.test_delineate_mock_header)
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
        """test"""
        prompt, deprompted_segments = extract_prompts(self.test_extract_prompts_mock_extract_data)
        assert deprompted_segments == "theres some other data here whatever"
        assert prompt == {
            "Negative prompt": "no bad, only 5 fingers",
            "Positive prompt": "Lookie Lookie, all, the, terms,in, the prompt, wao",
        }

    def test_extract_dict_by_delineation(self):
        """test"""
        hashes, dehashed_text = extract_dict_by_delineation(self.extract_dict_mock_partial_map)
        logger.debug(hashes)
        logger.debug(dehashed_text)
        assert hashes == {
            # "A": "{long}",
            "With": '{"Some": "useful", "although": "also"}',
            "Only": '{"The": "best", "Algorithm": "Will", "Successfully": "Match"}',
        }
        assert dehashed_text == "A: long, test: string, Some: useless, data: thrown, in: as, well: !!, All, Correctly! !"

    def test_make_paired_str_dict(self):
        """test"""
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
        """test"""
        mock_delineate_by_esc_codes = Mock(return_value=["a", "b", "1", "2", "y", "z"])
        mock_extract_prompts = Mock(return_value={"Positive": "yay", "Negative": "boo"})
        mock_extract_dict_by_delineation = Mock(return_value=({"key": "value"}, "almost: right, but: not"))
        mock_make_paired_str_dict = Mock(return_value=({"Okay": "Right"}, {"This": "Time"}))

        with (
            patch(
                "dataset_tools.metadata_parser.delineate_by_esc_codes",
                mock_delineate_by_esc_codes,
            ),
            patch("dataset_tools.metadata_parser.extract_prompts", mock_extract_prompts),
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
            assert UpField.PROMPT in result and DownField.GENERATION_DATA in result and DownField.SYSTEM in result

    def test_filter_keys_of_not_prompt(self):
        """test"""
        extracted = filter_keys_of(self.mock_dict)
        assert extracted == (
            {},
            {
                "seed": 948476150837611,
                "steps": 60,
                "cfg": 12.0,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 1.0,
            },
        )

    def test_filter_keys_of_prompt(self):
        """test"""
        extracted = filter_keys_of(
            self.redivide_dict_test_data,
        )
        expected_extracted = (
            {
                "clip_l": "Red gauze tape spun around an invisible hand",
                "t5xxl": "Red gauze tape spun around an invisible hand",
                # "text": "",
                "guidance": 1.0,
            },
            {
                "seed": 1944739425534,
                "steps": 4,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
            },
        )
        assert extracted == expected_extracted

    def test_validate_mapping_bracket_pair_structure_of(self):
        """test"""
        possibly_valid = validate_mapping_bracket_pair_structure_of(self.actual_metadata_sub_map)
        assert isinstance(possibly_valid, str)
        assert possibly_valid == self.valid_metadata_sub_map

    @patch("dataset_tools.metadata_parser.redivide_nodeui_data_in")
    def test_arrange_nodeui_metadata_prompt(self, mock_redivide):
        mock_input = {"prompt": "prompt"}
        mock_redivide.return_value = "prompt", "gen"
        result = arrange_nodeui_metadata(mock_input)
        mock_redivide.assert_called_with(mock_input, "prompt")
        expected_result = {"Prompt Data": "prompt", "Generation Data": "gen"}
        assert result == expected_result

    def test_validate_typical_success(self):
        result = validate_typical(self.redivide_dict_test_data, "2")
        expected_output = self.redivide_dict_test_data["2"]
        assert result == expected_output

    @patch("dataset_tools.metadata_parser.debug_message")
    def test_validate_typical_fail(self, mock_debug_msg):
        subdict = {"mock": "data"}
        mock_data = {"prompt": subdict}
        out = validate_typical(mock_data, "prompt")
        mock_debug_msg.assert_called()
        assert out is None

    @patch("dataset_tools.metadata_parser.redivide_nodeui_data_in")
    def test_arrange_nodeui_metadata_workflow(self, mock_redivide):
        full_metadata_key_test = {"prompt": "data", "workflow": "two"}
        mock_redivide.side_effect = [({}, {"data": "tokeep"}), ({"Positive": "three"}, {"gen_data": "one"})]
        result = arrange_nodeui_metadata(full_metadata_key_test)
        mock_redivide.assert_has_calls([call({"prompt": "data", "workflow": "two"}, "prompt"), call({"prompt": "data", "workflow": "two"}, "workflow")], any_order=False)
        # mock_redivide.assert_called_with({"1": "dict_data"}, self.new_prompt_dict_labels)
        assert result == {"Generation Data": {"data": "tokeep", "gen_data": "one"}, "Prompt Data": {"Positive": "three"}}

    @patch("dataset_tools.metadata_parser.clean_with_json")
    @patch("dataset_tools.metadata_parser.filter_keys_of")
    def test_redivide_nodeui_data_in(self, mock_filter, mock_clean):
        """test"""

        mock_clean.return_value = self.redivide_dict_test_data
        mock_filter.return_value = (
            {"Positive prompt": {"clip_l": "Red gauze tape spun around an invisible hand", "t5xxl": "Red gauze tape spun around an invisible hand"}, "Negative prompt": {" "}},
            {
                "inputs": self.mock_bracket_dict_gen_data["inputs"],
            },
        )
        mock_data_with_prompt = {"prompt": f"{self.redivide_dict_test_data}"}
        result = redivide_nodeui_data_in(mock_data_with_prompt, "prompt")
        mock_clean.assert_called_with(mock_data_with_prompt, "prompt")
        expected_result = (
            self.mock_bracket_dict_next_keys,
            self.mock_bracket_dict_gen_data,
        )
        self.assertEqual(result, expected_result)

    @patch("dataset_tools.metadata_parser.clean_with_json")
    @patch("dataset_tools.metadata_parser.filter_keys_of")
    def test_redivide_nodeui_data_empty_prompt(self, mock_filter, mock_clean):
        """test"""

        mock_clean.return_value = self.mock_dict
        mock_filter.return_value = ({}, self.mock_dict)
        result = redivide_nodeui_data_in(f"{self.mock_dict}", "prompt")
        mock_clean.assert_called_with(str(self.mock_dict), "prompt")
        expected_result = {}, self.mock_dict

        self.assertEqual((result), expected_result)

    @patch("dataset_tools.metadata_parser.clean_with_json")
    def test_fail_dict(self, mock_clean):
        """test"""
        mock_clean.return_value = {"2": {"glass_type": "deblah", "inputs": {"even_more_blah": "meh"}}}
        assert ValidationError

    @patch("dataset_tools.metadata_parser.arrange_webui_metadata")
    def test_coordinate_webui(self, mock_webui):
        """test"""
        data = {"parameters": {"random": "data"}}
        mock_webui.return_value = data
        result = coordinate_metadata_operations(data, dict)
        mock_webui.assert_called_with(data)
        assert result == data

    @patch("dataset_tools.metadata_parser.arrange_nodeui_metadata")
    def test_coordinate_nodeui(self, mock_node):
        """test"""
        data = {"prompt": {"random": "data"}}
        mock_node.return_value = data
        result = coordinate_metadata_operations(data, dict)
        mock_node.assert_called_with(data)
        assert result == data

    @patch("dataset_tools.metadata_parser.coordinate_metadata_operations")
    @patch("dataset_tools.access_disk.MetadataFileReader.read_header")
    @patch("dataset_tools.metadata_parser.nfo")
    def test_parse_fail(
        self,
        mock_nfo,
        mock_read,
        mock_coord,
    ):
        """test"""
        data = "No Data"
        fake_file = "fake.png"
        expected_return = {EmptyField.PLACEHOLDER: {"": EmptyField.PLACEHOLDER}}
        mock_read.return_value = data
        mock_coord.return_value = {EmptyField.PLACEHOLDER: {"": EmptyField.PLACEHOLDER}}
        result = parse_metadata(fake_file)
        mock_read.assert_called_with(fake_file)
        mock_coord.assert_called_with(data)
        mock_nfo.assert_called_with("Unexpected format", fake_file)
        assert result == expected_return

    @patch("dataset_tools.metadata_parser.MetadataFileReader")
    def test_success(self, MockReader):
        """test"""
        mock_reader = MockReader.return_value
        mock_reader.read_header.return_value = "header"
        with patch("dataset_tools.metadata_parser.coordinate_metadata_operations", return_value={"key": "value"}):
            self.assertEqual(parse_metadata("path"), {"key": "value"})


if __name__ == "__main__":
    unittest.main()
