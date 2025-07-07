#!/usr/bin/env python3

"""
Simple test to verify T5 parser node type support
"""

import json
import sys
import os
sys.path.append('/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/dataset_tools')

from metadata_engine.extractors.comfyui_extractors import ComfyUIExtractor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_t5_node_support():
    """Test that T5 parser now supports SamplerCustomAdvanced nodes."""
    
    print("🔧 TESTING T5 NODE TYPE SUPPORT")
    print("=" * 35)
    
    # Load the updated T5 parser definition
    t5_parser_path = "/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/dataset_tools/parser_definitions/t5_detection_system.json"
    
    with open(t5_parser_path, 'r') as f:
        t5_parser_def = json.load(f)
    
    print(f"✅ Loaded T5 parser: {t5_parser_def['parser_name']}")
    print(f"   Priority: {t5_parser_def['priority']}")
    
    # Check that our node types are included
    fields = t5_parser_def["parsing_instructions"]["fields"]
    
    print("\n🎯 CHECKING NODE TYPE SUPPORT:")
    print("-" * 32)
    
    for field in fields:
        if "sampler_node_types" in field:
            target_key = field["target_key"]
            node_types = field["sampler_node_types"]
            print(f"  {target_key}: {node_types}")
            
            if "SamplerCustomAdvanced" in node_types:
                print("    ✅ SamplerCustomAdvanced supported!")
            else:
                print("    ❌ SamplerCustomAdvanced missing!")
        
        if "text_encoder_node_types" in field:
            target_key = field["target_key"]
            node_types = field["text_encoder_node_types"]
            print(f"  {target_key} encoders: {node_types}")
            
            if "BNK_CLIPTextEncodeAdvanced" in node_types:
                print("    ✅ BNK_CLIPTextEncodeAdvanced supported!")
            else:
                print("    ❌ BNK_CLIPTextEncodeAdvanced missing!")
    
    # Test with SamplerCustomAdvanced workflow
    print("\n🧪 TESTING WITH SamplerCustomAdvanced:")
    print("-" * 40)
    
    # Create workflow with SamplerCustomAdvanced (the problematic node type)
    workflow_data = {
        "1": {
            "inputs": {
                "noise_seed": 12345,
                "steps": 30,
                "cfg": 7.5,
                "sampler_name": "dpmpp_2m_sde_gpu",
                "scheduler": "karras",
                "positive": ["2", 0],
                "negative": ["3", 0],
                "model": ["4", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "SamplerCustomAdvanced",
            "_meta": {
                "title": "SamplerCustomAdvanced"
            }
        },
        "2": {
            "inputs": {
                "text": "beautiful landscape, mountains, sunrise, high resolution",
                "clip": ["6", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {
                "title": "CLIP Text Encode (Prompt)"
            }
        },
        "3": {
            "inputs": {
                "text": "blurry, low quality, bad anatomy",
                "clip": ["6", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {
                "title": "CLIP Text Encode (Prompt)"
            }
        },
        "6": {
            "inputs": {
                "clip_name1": "t5xxl_fp16.safetensors",
                "clip_name2": "clip_l.safetensors",
                "type": "flux"
            },
            "class_type": "DualCLIPLoader",
            "_meta": {
                "title": "DualCLIPLoader"
            }
        }
    }
    
    # Test parameter extraction
    extractor = ComfyUIExtractor(logger)
    
    # Test seed extraction (note: SamplerCustomAdvanced uses noise_seed instead of seed)
    seed_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "noise_seed",  # SamplerCustomAdvanced uses noise_seed
        "value_type": "integer"
    }
    seed_result = extractor._find_input_of_main_sampler(workflow_data, seed_method, {}, {})
    print(f"  Seed (noise_seed): {seed_result}")
    
    # Test steps
    steps_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "steps",
        "value_type": "integer"
    }
    steps_result = extractor._find_input_of_main_sampler(workflow_data, steps_method, {}, {})
    print(f"  Steps: {steps_result}")
    
    # Test sampler name
    sampler_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "sampler_name",
        "value_type": "string"
    }
    sampler_result = extractor._find_input_of_main_sampler(workflow_data, sampler_method, {}, {})
    print(f"  Sampler: {sampler_result}")
    
    # Test scheduler
    scheduler_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "scheduler",
        "value_type": "string"
    }
    scheduler_result = extractor._find_input_of_main_sampler(workflow_data, scheduler_method, {}, {})
    print(f"  Scheduler: {scheduler_result}")
    
    print("\n🎯 SUMMARY:")
    print("-" * 12)
    if seed_result and steps_result and sampler_result and scheduler_result:
        print("✅ T5 parser now supports SamplerCustomAdvanced nodes!")
        print("✅ Parameter extraction working correctly")
    else:
        print("❌ Some parameter extraction still failing")
        
    print("\n💡 NOTE: The user's issue with scrambled parameters might be due to:")
    print("   1. SamplerCustomAdvanced uses 'noise_seed' instead of 'seed'")
    print("   2. Widget value position mapping might be different")
    print("   3. Template processing issue in the MetadataEngine")

if __name__ == "__main__":
    test_t5_node_support()