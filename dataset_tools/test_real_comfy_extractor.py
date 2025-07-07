#!/usr/bin/env python3

"""
Test the real ComfyUI extractor after the fix.
"""

import sys
import os

# Add the parent directory to the path so we can import from metadata_engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now test by importing the modules directly from the files
import importlib.util

def load_module_from_file(file_path, module_name):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Mock logger
class MockLogger:
    def debug(self, msg):
        print(f"DEBUG: {msg}")
    def warning(self, msg):
        print(f"WARNING: {msg}")
    def error(self, msg):
        print(f"ERROR: {msg}")

def test_real_extractor():
    """Test the real ComfyUI extractor."""
    
    print("🔧 TESTING REAL COMFYUI EXTRACTOR AFTER FIX")
    print("=" * 44)
    
    # Load the real ComfyUI extractor
    extractor_path = os.path.join(os.path.dirname(__file__), "metadata_engine", "extractors", "comfyui_extractors.py")
    comfyui_module = load_module_from_file(extractor_path, "comfyui_extractors")
    
    # Create the extractor
    logger = MockLogger()
    extractor = comfyui_module.ComfyUIExtractor(logger)
    
    # Sample T5 workflow data
    sample_t5_data = {
        "1": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "t5xxl_fp16.safetensors",
                "clip_name2": "clip_l.safetensors"
            }
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "beautiful landscape with mountains and trees",
                "clip": [1, 0]
            }
        },
        "3": {
            "class_type": "CLIPTextEncode", 
            "inputs": {
                "text": "low quality, blurry",
                "clip": [1, 0]
            }
        },
        "4": {
            "class_type": "KSampler",
            "inputs": {
                "model": [5, 0],
                "positive": [2, 0],
                "negative": [3, 0],
                "latent_image": [6, 0],
                "seed": 123456,
                "steps": 20,
                "cfg": 7.5,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0
            }
        },
        "5": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "sd3_medium_incl_clips_t5xxlfp16.safetensors"
            }
        },
        "6": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 1024,
                "height": 1024,
                "batch_size": 1
            }
        }
    }
    
    print("1. Testing positive prompt extraction:")
    method_def = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "positive_input_name": "positive",
        "text_input_name_in_encoder": "text",
        "text_encoder_node_types": ["CLIPTextEncode", "CLIPTextEncodeSD3", "T5TextEncode", "BNK_CLIPTextEncodeAdvanced", "CLIPTextEncodeAdvanced"]
    }
    
    result = extractor._find_text_from_main_sampler_input(sample_t5_data, method_def, {}, {})
    print(f"   Result: '{result}'")
    
    if result == "beautiful landscape with mountains and trees":
        print("   ✅ SUCCESS: Real extractor works correctly!")
    else:
        print("   ❌ FAILED: Real extractor still has issues")
    
    print("\n2. Testing negative prompt extraction:")
    method_def = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "negative_input_name": "negative",
        "text_input_name_in_encoder": "text",
        "text_encoder_node_types": ["CLIPTextEncode", "CLIPTextEncodeSD3", "T5TextEncode", "BNK_CLIPTextEncodeAdvanced", "CLIPTextEncodeAdvanced"]
    }
    
    result = extractor._find_text_from_main_sampler_input(sample_t5_data, method_def, {}, {})
    print(f"   Result: '{result}'")
    
    if result == "low quality, blurry":
        print("   ✅ SUCCESS: Real extractor negative prompt works!")
    else:
        print("   ❌ FAILED: Real extractor negative prompt failed")
    
    print("\n3. Testing parameter extraction:")
    method_def = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "seed",
        "value_type": "integer"
    }
    
    seed_result = extractor._find_input_of_main_sampler(sample_t5_data, method_def, {}, {})
    print(f"   Seed result: {seed_result}")
    
    if seed_result == 123456:
        print("   ✅ SUCCESS: Parameter extraction works!")
    else:
        print("   ❌ FAILED: Parameter extraction failed")

if __name__ == "__main__":
    test_real_extractor()