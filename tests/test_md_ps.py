# // SPDX-License-Identifier: CC0-1.0
# // --<{ Ktiseos Nyx }>--

"""Test Parser"""

# pylint: disable=line-too-long, missing-class-docstring

import unittest
from unittest.mock import Mock, patch

from pydantic import ValidationError

from dataset_tools.logger import logger
from dataset_tools.access_disk import MetadataFileReader
from dataset_tools.correct_types import UpField, DownField
from dataset_tools.metadata_parser import (
    arrange_webui_metadata,
    delineate_by_esc_codes,
    make_paired_str_dict,
    extract_dict_by_delineation,
    extract_prompts,
    coordinate_metadata_ops,
    arrange_nodeui_metadata,
    validate_dictionary_structure,
    rename_next_keys_of,
    parse_metadata,
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

    def test_delineate_by_esc_codes(self):
        """test"""
        mock_header_data = {"parameters": "1 2 3 4\u200b\u200b\u200b5\n6\n7\n8\xe2\x80\x8b\xe2\x80\x8b\xe2\x80\x8b9\n10\n11\n12\x00\x00\u200bbingpot\x00\n"}
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
        """test"""
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
        """test"""
        mock_partial_map = 'A: long, test: string, With: {"Some": "useful", "although": "also"}, Some: useless, data: thrown, in: as, well: !!, Only: "The": "best", "Algorithm": "Will", "Successfully": "Match", All, Correctly! !'
        hashes, dehashed_text = extract_dict_by_delineation(mock_partial_map)
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

    def test_rename_next_keys_of_not_prompt(self):
        """test"""
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
        expected_extracted = {"KSampler": "seed: 948476150837611\nsteps: 60\ncfg: 12.0\nsampler_name: dpmpp_2m\nscheduler: karras\ndenoise: 1.0"}
        assert extracted == expected_extracted

    def test_rename_next_keys_of_prompt(self):
        """test"""
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
        """test"""
        possibly_valid = validate_dictionary_structure(self.actual_metadata_sub_map)
        assert isinstance(possibly_valid, str)
        assert possibly_valid == self.valid_metadata_sub_map

    def test_arrange_nodeui_metadata(self):
        """test"""
        self.assertEqual(arrange_nodeui_metadata({}), {"": "No Data"})

    next_keys = {"Positive prompt": {"clip_l": "Red gauze tape spun around an invisible hand", "t5xxl": "Red gauze tape spun around an invisible hand"}, "Negative prompt": {" "}}

    @patch("dataset_tools.metadata_parser.clean_with_json")
    @patch("dataset_tools.metadata_parser.rename_next_keys_of")
    def test_arrange_nodeui_metadata_calls(self, mock_rename, mock_clean):
        """test"""
        test_data = {
            "2": {
                "inputs": {"seed": 1944739425534, "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0, "model": ["136", 0], "positive": ["110", 0], "negative": ["110", 1], "latent_image": ["88", 0]},
                "class_type": "KSampler",
                "_meta": {"title": "3 KSampler"},
            },
            "109": {
                "inputs": {"clip_l": "Red gauze tape spun around an invisible hand", "t5xxl": "Red gauze tape spun around an invisible hand", "guidance": 1.0, "clip": ["136", 1]},
                "class_type": "CLIPTextEncodeFlux",
                "_meta": {"title": "CLIPTextEncodeFlux"},
            },
            "113": {"inputs": {"text": "", "clip": ["136", 1]}, "class_type": "CLIPTextEncode", "_meta": {"title": "2b Negative [CLIP Text Encode (Prompt)]"}},
        }
        gen_data = {
            "inputs": {"seed": 1944739425534, "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0, "model": ["136", 0], "positive": ["110", 0], "negative": ["110", 1], "latent_image": ["88", 0]},
        }
        mock_clean.return_value = test_data
        mock_rename.return_value = {"Positive prompt": {"clip_l": "Red gauze tape spun around an invisible hand", "t5xxl": "Red gauze tape spun around an invisible hand"}, "Negative prompt": {" "}, "inputs": gen_data["inputs"]}
        result = arrange_nodeui_metadata({"prompt": f"{test_data}"})
        expected_result = {"Generation Data": gen_data, "Prompt Data": self.next_keys}
        mock_clean.assert_called_with(str(test_data))
        self.assertEqual(result, expected_result)

    @patch("dataset_tools.metadata_parser.clean_with_json")
    def test_is_dict(self, mock_clean):
        """test"""
        data = {"prompt": {"2": {"class_type": "deblah", "inputs": {"even_more_blah": "meh"}}}}
        mock_clean.return_value = {"2": {"class_type": "deblah", "inputs": {"even_more_blah": "meh"}}}
        assert arrange_nodeui_metadata(data)

    @patch("dataset_tools.metadata_parser.clean_with_json")
    def test_fail_dict(self, mock_clean):
        """test"""
        # data = {"prompt": {"2": {"class_type": "deblah", "inputs": {"even_more_blah":"meh"} } } }
        mock_clean.return_value = {"2": {"glass_type": "deblah", "inputs": {"even_more_blah": "meh"}}}
        assert ValidationError

    @patch("dataset_tools.metadata_parser.arrange_webui_metadata")
    def test_coordinate_webui(self, mock_webui):
        """test"""
        data = {"parameters": {"random": "data"}}
        mock_webui.return_value = data
        result = coordinate_metadata_ops(data)
        mock_webui.assert_called_with(data)
        assert result == data

    @patch("dataset_tools.metadata_parser.arrange_nodeui_metadata")
    def test_coordinate_nodeui(self, mock_node):
        """test"""
        data = {"prompt": {"random": "data"}}
        mock_node.return_value = data
        result = coordinate_metadata_ops(data)
        mock_node.assert_called_with(data)
        assert result == data

    @patch("dataset_tools.metadata_parser.coordinate_metadata_ops")
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
        expected_return = {UpField.PLACEHOLDER: {"": UpField.PLACEHOLDER}}
        mock_read.return_value = data
        mock_coord.return_value = {UpField.PLACEHOLDER: {"": UpField.PLACEHOLDER}}
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
        with patch("dataset_tools.metadata_parser.coordinate_metadata_ops", return_value={"key": "value"}):
            self.assertEqual(parse_metadata("path"), {"key": "value"})


if __name__ == "__main__":
    unittest.main()
