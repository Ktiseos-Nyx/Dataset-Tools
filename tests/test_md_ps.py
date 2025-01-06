import os
import unittest

from dataset_tools import logger
from dataset_tools.metadata_parser import (
        format_chunk,
        open_png_header,
        structured_metadata_list_to_dict,
        dehashed_metadata_str_to_dict,
        extract_enclosed_values
        )

class TestParseMetadata(unittest.TestCase):

    def setUp(self):
        self.test_folder = os.path.dirname(os.path.abspath(__file__))
        self.real_file = os.path.join(self.test_folder,'test_img.png')
        self.enclosed_value_return = ('Hell4ineXLPOS  solo, long hair, looking at viewer, 1boy, jewelry, closed mouth, upper body, white hair, male focus, wings, necklace, border, cross, black wings,Negative prompt: XL_NegSteps: 30, Sampler: Euler a, Schedule type: Automatic, CFG scale: 7, Seed: 970527942, Size: 832x1216, Model hash: 238ffac319, Model: HellaineMixXL-FIX.fp16, VAE hash: 63aeecb90f, VAE: sdxl_vae.safetensors, Denoising strength: 0.35, Clip skip: 2, , Hires upscale: 1.5, Hires steps: 30, Hires upscaler: 4x_foolhardy_Remacri, , , Time taken: 18.0 sec., Version: v1.10.0', {'Hashes': '{"model": "238ffac319", "embed:Hell4ineXLPOS": "23f5e3fc03", "vae": "63aeecb90f"}', 'TI hashes: "Hell4ineXLPOS: 23f5e3fc030a, Hell4ineXLPOS: 23f5e3fc030a"': 'Hell4ineXLPOS: 23f5e3fc030a, Hell4ineXLPOS: 23f5e3fc030a', 'Hardware Info: "RTX 4090 24GB, Threadripper PRO 5975WX 32-s, 252GB RAM"': 'RTX 4090 24GB, Threadripper PRO 5975WX 32-s, 252GB RAM'})
        self.dehashed_text = {'Positive prompt': 'Hell4ineXLPOS  solo, long hair, looking at viewer, 1boy, jewelry, closed mouth, upper body, white hair, male focus, wings, necklace, border, cross, black wings,', 'Negative prompt': 'XL_Neg   ', 'Steps': '30', ' Sampler': 'Euler a', ' Schedule type': 'Automatic', ' CFG scale': '7', ' Seed': '970527942', ' Size': '832x1216', ' Model hash': '238ffac319', ' Model': 'HellaineMixXL-FIX.fp16', ' VAE hash': '63aeecb90f', ' VAE': 'sdxl_vae.safetensors', ' Denoising strength': '0.35', ' Clip skip': '2', ' Hires upscale': '1.5', ' Hires steps': '30', ' Hires upscaler': '4x_foolhardy_Remacri', ' Time taken': '18.0 sec.', ' Version': 'v1.10.0'}, {'Negative prompt': 'XL_Neg   ', 'Steps': '30', ' Sampler': 'Euler a', ' Schedule type': 'Automatic', ' CFG scale': '7', ' Seed': '970527942', ' Size': '832x1216', ' Model hash': '238ffac319', ' Model': 'HellaineMixXL-FIX.fp16', ' VAE hash': '63aeecb90f', ' VAE': 'sdxl_vae.safetensors', ' Denoising strength': '0.35', ' Clip skip': '2', ' Hires upscale': '1.5', ' Hires steps': '30', ' Hires upscaler': '4x_foolhardy_Remacri', ' Time taken': '18.0 sec.', ' Version': 'v1.10.0'}
        self.cleaned_text = 'Hell4ineXLPOS  solo, long hair, looking at viewer, 1boy, jewelry, closed mouth, upper body, white hair, male focus, wings, necklace, border, cross, black wings,   ,Negative prompt: XL_Neg   ,Steps: 30, Sampler: Euler a, Schedule type: Automatic, CFG scale: 7, Seed: 970527942, Size: 832x1216, Model hash: 238ffac319, Model: HellaineMixXL-FIX.fp16, VAE hash: 63aeecb90f, VAE: sdxl_vae.safetensors, Denoising strength: 0.35, Clip skip: 2, Hashes: {"model": "238ffac319", "embed:Hell4ineXLPOS": "23f5e3fc03", "vae": "63aeecb90f"}, Hires upscale: 1.5, Hires steps: 30, Hires upscaler: 4x_foolhardy_Remacri, TI hashes: "Hell4ineXLPOS: 23f5e3fc030a, Hell4ineXLPOS: 23f5e3fc030a", Hardware Info: "RTX 4090 24GB, Threadripper PRO 5975WX 32-s, 252GB RAM", Time taken: 18.0 sec., Version: v1.10.0'
        self.structured_text = {'Hashes': {'model': '238ffac319', 'embed:Hell4ineXLPOS': '23f5e3fc03', 'vae': '63aeecb90f'}, 'TI hashes': 'Hell4ineXLPOS: 23f5e3fc030a, Hell4ineXLPOS: 23f5e3fc030a', 'Hardware Info': 'RTX 4090 24GB, Threadripper PRO 5975WX 32-s, 252GB RAM'}

    def test_parse_metadata_failure(self):
         with self.assertRaises(FileNotFoundError):
            open_png_header(os.path.join(self.test_folder, "nonexistent.png"))

    def test_parse_metadata_success(self):
        chunks = open_png_header(self.real_file)
        self.assertIsNotNone(chunks)
        self.assertTrue(list(chunks))  # Confirm it's not empty

    def test_format_chunk(self):
        chunks = open_png_header(self.real_file)
        formatted_chunk = format_chunk(chunks)
        assert formatted_chunk == self.cleaned_text

    def test_extract_enclosed_values(self):
        dehashed_text, structured_dict = extract_enclosed_values(self.cleaned_text)
        assert dehashed_text, structured_dict == self.enclosed_value_return

    def test_structured_metadata_list_to_dict(self):
        _, structured_dict = extract_enclosed_values(self.cleaned_text)
        final_text = structured_metadata_list_to_dict(structured_dict)
        expected_output = self.structured_text
        logger.debug("%s",f"{final_text}")
        assert final_text == expected_output

    def test_dehashed_metadata_str_to_dict(self):
        prompt_metadata, _ = extract_enclosed_values(self.cleaned_text)
        final_text = dehashed_metadata_str_to_dict(prompt_metadata)
        expected_output = self.dehashed_text
        logger.debug("%s",f"{final_text}")
        assert final_text == expected_output

if __name__ == '__main__':
    unittest.main()