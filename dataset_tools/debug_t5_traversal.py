#!/usr/bin/env python3

"""
Debug T5 parser traversal issue - figure out why prompts aren't being extracted.
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from metadata_engine.extractors.comfyui_extractors import ComfyUIExtractor
from metadata_engine.field_extraction import FieldExtractor
import logging

# Configure logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_t5_traversal():
    """Test T5 parser traversal with sample data."""
    
    print("🔧 DEBUGGING T5 PARSER TRAVERSAL ISSUE")
    print("=" * 42)
    
    # Sample T5 workflow data (minimal example)
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
    
    print("1. Testing direct ComfyUI extractor:")
    comfy_extractor = ComfyUIExtractor(logger)
    
    # Test the method directly
    method_def = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "positive_input_name": "positive",
        "text_input_name_in_encoder": "text",
        "text_encoder_node_types": ["CLIPTextEncode", "CLIPTextEncodeSD3", "T5TextEncode", "BNK_CLIPTextEncodeAdvanced", "CLIPTextEncodeAdvanced"]
    }
    
    print(f"   Sample data has {len(sample_t5_data)} nodes")
    for node_id, node_data in sample_t5_data.items():
        print(f"   Node {node_id}: {node_data.get('class_type')}")
    
    positive_prompt = comfy_extractor._find_text_from_main_sampler_input(
        sample_t5_data, method_def, {}, {}
    )
    print(f"   Positive prompt result: '{positive_prompt}'")
    
    # Test negative prompt
    method_def["negative_input_name"] = "negative"
    method_def.pop("positive_input_name", None)
    
    negative_prompt = comfy_extractor._find_text_from_main_sampler_input(
        sample_t5_data, method_def, {}, {}
    )
    print(f"   Negative prompt result: '{negative_prompt}'")
    
    print("\n2. Testing with FieldExtractor integration:")
    field_extractor = FieldExtractor(logger)
    
    # Test positive prompt extraction
    positive_method_def = {
        "method": "comfy_find_text_from_main_sampler_input",
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "positive_input_name": "positive",
        "text_input_name_in_encoder": "text",
        "text_encoder_node_types": ["CLIPTextEncode", "CLIPTextEncodeSD3", "T5TextEncode", "BNK_CLIPTextEncodeAdvanced", "CLIPTextEncodeAdvanced"]
    }
    
    integrated_positive = field_extractor.extract_field(
        positive_method_def, sample_t5_data, {}, {}
    )
    print(f"   Integrated positive prompt: '{integrated_positive}'")
    
    # Test negative prompt extraction
    negative_method_def = {
        "method": "comfy_find_text_from_main_sampler_input",
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "negative_input_name": "negative",
        "text_input_name_in_encoder": "text",
        "text_encoder_node_types": ["CLIPTextEncode", "CLIPTextEncodeSD3", "T5TextEncode", "BNK_CLIPTextEncodeAdvanced", "CLIPTextEncodeAdvanced"]
    }
    
    integrated_negative = field_extractor.extract_field(
        negative_method_def, sample_t5_data, {}, {}
    )
    print(f"   Integrated negative prompt: '{integrated_negative}'")
    
    print("\n3. Testing parameter extraction:")
    seed_method_def = {
        "method": "comfy_find_input_of_main_sampler",
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "seed",
        "value_type": "integer"
    }
    
    seed_result = field_extractor.extract_field(
        seed_method_def, sample_t5_data, {}, {}
    )
    print(f"   Seed: {seed_result}")
    
    steps_method_def = {
        "method": "comfy_find_input_of_main_sampler",
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "steps",
        "value_type": "integer"
    }
    
    steps_result = field_extractor.extract_field(
        steps_method_def, sample_t5_data, {}, {}
    )
    print(f"   Steps: {steps_result}")
    
    print("\n4. Testing with workflow format (nodes array):")
    # Convert to workflow format
    workflow_data = {
        "nodes": [
            {"id": "1", "class_type": "DualCLIPLoader", "inputs": {"clip_name1": "t5xxl_fp16.safetensors", "clip_name2": "clip_l.safetensors"}},
            {"id": "2", "class_type": "CLIPTextEncode", "inputs": {"text": "beautiful landscape with mountains", "clip": [1, 0]}},
            {"id": "3", "class_type": "CLIPTextEncode", "inputs": {"text": "low quality, blurry", "clip": [1, 0]}},
            {"id": "4", "class_type": "KSampler", "inputs": [
                {"name": "model", "link": 5},
                {"name": "positive", "link": 2},
                {"name": "negative", "link": 3},
                {"name": "latent_image", "link": 6}
            ], "widgets_values": [123456, 20, 7.5, "euler", "normal", 1.0]},
            {"id": "5", "class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd3_medium.safetensors"}},
            {"id": "6", "class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}}
        ]
    }
    
    workflow_positive = field_extractor.extract_field(
        positive_method_def, workflow_data, {}, {}
    )
    print(f"   Workflow positive prompt: '{workflow_positive}'")
    
    workflow_seed = field_extractor.extract_field(
        seed_method_def, workflow_data, {}, {}
    )
    print(f"   Workflow seed: {workflow_seed}")
    
    # Summary
    print("\n🎯 SUMMARY:")
    print("-" * 12)
    
    test_results = [
        ("Direct positive prompt extraction", positive_prompt == "beautiful landscape with mountains and trees"),
        ("Direct negative prompt extraction", negative_prompt == "low quality, blurry"),
        ("Integrated positive prompt extraction", integrated_positive == "beautiful landscape with mountains and trees"),
        ("Integrated negative prompt extraction", integrated_negative == "low quality, blurry"),
        ("Parameter extraction (seed)", seed_result == 123456),
        ("Parameter extraction (steps)", steps_result == 20),
        ("Workflow format positive prompt", workflow_positive == "beautiful landscape with mountains"),
        ("Workflow format seed", workflow_seed == 123456),
    ]
    
    passed_tests = sum(1 for _, passed in test_results if passed)
    total_tests = len(test_results)
    
    print(f"✅ Passed: {passed_tests}/{total_tests} tests")
    
    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! T5 traversal is working correctly!")
        print("✅ Text extraction working for both formats")
        print("✅ Parameter extraction working")
        print("✅ The issue might be elsewhere in the pipeline")
    else:
        print(f"\n❌ {total_tests - passed_tests} test(s) failed")
        print("🔍 The traversal methods need debugging")
        
        # Additional debugging for failed tests
        print("\n🔍 DEBUGGING FAILED TESTS:")
        if not positive_prompt:
            print("   - Positive prompt extraction failed")
            print("   - Check if the traversal is finding the sampler node")
            print("   - Check if the connection format is correct")
        
        if not integrated_positive:
            print("   - Integrated positive prompt extraction failed")
            print("   - Check FieldExtractor method registration")

if __name__ == "__main__":
    test_t5_traversal()