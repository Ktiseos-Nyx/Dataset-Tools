
#pylint: disable=line-too-long, missing-class-docstring

import os
import unittest
from unittest.mock import Mock, patch
from dataset_tools import logger
from dataset_tools.metadata_parser import (
        arrange_webui_metadata,
        format_chunk,
        open_png_header,
        convert_str_to_dict,
        extract_partial_mappings,
        extract_prompts,
        #arrange_nodeui_metadata,
        )

class TestParseMetadata(unittest.TestCase):
    def setUp(self):
        self.test_folder = os.path.dirname(os.path.abspath(__file__))
        self.real_file = os.path.join(self.test_folder,'test_img.png')
        self.prompt = {'Positive prompt': 'Hell4ineXLPOS  solo, long hair, looking at viewer, 1boy, jewelry, closed mouth, upper body, white hair, male focus, wings, necklace, border, cross, black wings,', 'Negative prompt': 'Negative prompt: XL_Neg'}
        self.deprompted = 'Steps: 30, Sampler: Euler a, Schedule type: Automatic, CFG scale: 7, Seed: 970527942, Size: 832x1216, Model hash: 238ffac319, Model: HellaineMixXL-FIX.fp16, VAE hash: 63aeecb90f, VAE: sdxl_vae.safetensors, Denoising strength: 0.35, Clip skip: 2, Hashes: {"model": "238ffac319", "embed:Hell4ineXLPOS": "23f5e3fc03", "vae": "63aeecb90f"}, Hires upscale: 1.5, Hires steps: 30, Hires upscaler: 4x_foolhardy_Remacri, TI hashes: "Hell4ineXLPOS: 23f5e3fc030a, Hell4ineXLPOS: 23f5e3fc030a", Hardware Info: "RTX 4090 24GB, Threadripper PRO 5975WX 32-s, 252GB RAM", Time taken: 18.0 sec., Version: v1.10.0'
        self.enclosed_value_return = ('Hell4ineXLPOS  solo, long hair, looking at viewer, 1boy, jewelry, closed mouth, upper body, white hair, male focus, wings, necklace, border, cross, black wings,Negative prompt: XL_NegSteps: 30, Sampler: Euler a, Schedule type: Automatic, CFG scale: 7, Seed: 970527942, Size: 832x1216, Model hash: 238ffac319, Model: HellaineMixXL-FIX.fp16, VAE hash: 63aeecb90f, VAE: sdxl_vae.safetensors, Denoising strength: 0.35, Clip skip: 2, , Hires upscale: 1.5, Hires steps: 30, Hires upscaler: 4x_foolhardy_Remacri, , , Time taken: 18.0 sec., Version: v1.10.0', {'Hashes': '{"model": "238ffac319", "embed:Hell4ineXLPOS": "23f5e3fc03", "vae": "63aeecb90f"}', 'TI hashes: "Hell4ineXLPOS: 23f5e3fc030a, Hell4ineXLPOS: 23f5e3fc030a"': 'Hell4ineXLPOS: 23f5e3fc030a, Hell4ineXLPOS: 23f5e3fc030a', 'Hardware Info: "RTX 4090 24GB, Threadripper PRO 5975WX 32-s, 252GB RAM"': 'RTX 4090 24GB, Threadripper PRO 5975WX 32-s, 252GB RAM'})
        self.correct_hash = {'Hashes': '{"model": "238ffac319", "embed:Hell4ineXLPOS": "23f5e3fc03", "vae": "63aeecb90f"}', 'TI hashes': '"Hell4ineXLPOS: 23f5e3fc030a, Hell4ineXLPOS: 23f5e3fc030a", Hardware Info: "RTX 4090 24GB, Threadripper PRO 5975WX 32-s, 252GB RAM"'}
        self.correct_dehashed = 'Steps: 30, Sampler: Euler a, Schedule type: Automatic, CFG scale: 7, Seed: 970527942, Size: 832x1216, Model hash: 238ffac319, Model: HellaineMixXL-FIX.fp16, VAE hash: 63aeecb90f, VAE: sdxl_vae.safetensors, Denoising strength: 0.35, Clip skip: 2, Hires upscale: 1.5, Hires steps: 30, Hires upscaler: 4x_foolhardy_Remacri, Time taken: 18.0 sec., Version: v1.10.0'
        self.format_chunk_text = ['Hell4ineXLPOS  solo, long hair, looking at viewer, 1boy, jewelry, closed mouth, upper body, white hair, male focus, wings, necklace, border, cross, black wings,', 'Negative prompt: XL_Neg', 'Steps: 30, Sampler: Euler a, Schedule type: Automatic, CFG scale: 7, Seed: 970527942, Size: 832x1216, Model hash: 238ffac319, Model: HellaineMixXL-FIX.fp16, VAE hash: 63aeecb90f, VAE: sdxl_vae.safetensors, Denoising strength: 0.35, Clip skip: 2, Hashes: {"model": "238ffac319", "embed:Hell4ineXLPOS": "23f5e3fc03", "vae": "63aeecb90f"}, Hires upscale: 1.5, Hires steps: 30, Hires upscaler: 4x_foolhardy_Remacri, TI hashes: "Hell4ineXLPOS: 23f5e3fc030a, Hell4ineXLPOS: 23f5e3fc030a", Hardware Info: "RTX 4090 24GB, Threadripper PRO 5975WX 32-s, 252GB RAM", Time taken: 18.0 sec., Version: v1.10.0']

    def test_parse_metadata_failure(self):
        """parse"""
        with self.assertRaises(FileNotFoundError):
            open_png_header(os.path.join(self.test_folder, "nonexistent.png"))

    def test_parse_metadata_success(self):
        chunks = open_png_header(self.real_file)
        self.assertIsNotNone(chunks)
        self.assertTrue(list(chunks))  # Confirm it's not empty

    def test_format_chunk(self):
        chunks = open_png_header(self.real_file)
        formatted_chunk = format_chunk(chunks)
        logger.debug("%s",f"{list(x for x in formatted_chunk)}")
        assert formatted_chunk == self.format_chunk_text

    def test_extract_prompts(self):
        prompt, deprompted_segments  = extract_prompts(self.format_chunk_text)
        assert deprompted_segments == self.deprompted
        assert prompt == self.prompt

    def test_extract_partial_mappings(self):
        mock_partial_map = 'A: long, test: string, With: {"Some": "useful", "although": "also"}, Some: useless, data: thrown, in: as, well: !!, Only: "The": "best", "Algorithm": "Will": "Successfully": "Capture": "All", Matches, Correctly!'
        hashes, dehashed_text = extract_partial_mappings(mock_partial_map)
        logger.debug(hashes)
        logger.debug(dehashed_text)
        assert hashes == {'With': '{"Some": "useful", "although": "also"}', 'Only': '"The": "best", "Algorithm": "Will": "Successfully": "Capture": "All"'}
        assert dehashed_text == 'A: long, test: string, Some: useless, data: thrown, in: as, well: !!, Matches, Correctly!'

    def test_convert_str_to_dict(self):
        mock_string_data = "Who: the, Hell: makes, Production: code, Work: like, This: tho, i: say, as: i, make: the, same: mistakes"
        final_text = convert_str_to_dict(mock_string_data)
        logger.debug("%s",f"{final_text}")
        assert final_text == {'Who': 'the', 'Hell': 'makes', 'Production': 'code', 'Work': 'like', 'This': 'tho', 'i': 'say', 'as': 'i', 'make': 'the', 'same': 'mistakes'}

    def test_arrange_webui_metadata(self):
        mock_format_chunk = Mock(return_value='Format_chunk_return')
        mock_extract_prompts = Mock(return_value={'Positive': 'yay','Negative': 'boo'})
        mock_extract_partial_mappings = Mock(return_value=({'key': 'value'},'almost: right, but: not'))
        mock_convert_str_to_dict = Mock(return_value=({'Okay': 'Right'}, {"This": "Time"}))

        with patch('dataset_tools.metadata_parser.format_chunk', mock_format_chunk), \
            patch('dataset_tools.metadata_parser.extract_prompts',mock_extract_prompts), \
            patch('dataset_tools.metadata_parser.extract_partial_mappings', mock_extract_partial_mappings), \
            patch('dataset_tools.metadata_parser.convert_str_to_dict', mock_convert_str_to_dict):
            result = arrange_webui_metadata("header chunks")

            assert mock_format_chunk.call_count == 1
            assert 'Prompts' in result and 'Generation_Data' in result and 'System' in result

if __name__ == '__main__':
    unittest.main()
