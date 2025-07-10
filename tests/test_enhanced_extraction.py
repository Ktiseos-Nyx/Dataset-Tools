#!/usr/bin/env python3
# ruff: noqa: T201

"""Test enhanced parameter extraction for SamplerCustomAdvanced nodes"""

import sys

sys.path.append(
    "/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/dataset_tools"
)

import logging

from metadata_engine.extractors.comfyui_extractors import ComfyUIExtractor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_enhanced_parameter_extraction():
    """Test the enhanced parameter extraction for different node types."""
    print(  # noqa: T201"🔧 TESTING ENHANCED PARAMETER EXTRACTION")
    print(  # noqa: T201"=" * 44)

    # Create test data with SamplerCustomAdvanced (problematic node)
    workflow_data = {
        "1": {
            "inputs": {
                "noise_seed": 999888777,  # SamplerCustomAdvanced uses noise_seed
                "steps": 25,
                "cfg": 8.0,
                "sampler_name": "dpmpp_2m_sde_gpu",
                "scheduler": "karras",
                "positive": ["2", 0],
                "negative": ["3", 0],
                "model": ["4", 0],
                "latent_image": ["5", 0],
            },
            "class_type": "SamplerCustomAdvanced",
            "_meta": {"title": "SamplerCustomAdvanced"},
        },
        "2": {
            "inputs": {
                "text": "beautiful landscape, mountains, sunrise, high resolution, masterpiece",
                "clip": ["6", 0],
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Prompt)"},
        },
        "3": {
            "inputs": {
                "text": "blurry, low quality, worst quality, bad anatomy, extra limbs",
                "clip": ["6", 0],
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Negative)"},
        },
        "6": {
            "inputs": {
                "clip_name1": "t5xxl_fp16.safetensors",
                "clip_name2": "clip_l.safetensors",
                "type": "flux",
            },
            "class_type": "DualCLIPLoader",
            "_meta": {"title": "DualCLIPLoader"},
        },
    }

    print(  # noqa: T201f"Test workflow has {len(workflow_data)} nodes")
    print(  # noqa: T201f"Main sampler: {workflow_data['1']['class_type']}")

    # Initialize extractor
    extractor = ComfyUIExtractor(logger)

    # Test parameter extraction with enhanced logic
    print(  # noqa: T201"\n🧪 TESTING PARAMETER EXTRACTION:")
    print(  # noqa: T201"-" * 37)

    # Test 1: Seed extraction (should map seed -> noise_seed for SamplerCustomAdvanced)
    print(  # noqa: T201"1. Testing seed extraction (seed -> noise_seed mapping):")
    seed_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "seed",  # Request seed, should map to noise_seed
        "value_type": "integer",
    }
    seed_result = extractor._find_input_of_main_sampler(
        workflow_data, seed_method, {}, {}
    )
    print(  # noqa: T201f"   Result: {seed_result} (expected: 999888777)")

    # Test 2: Steps extraction
    print(  # noqa: T201"2. Testing steps extraction:")
    steps_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "steps",
        "value_type": "integer",
    }
    steps_result = extractor._find_input_of_main_sampler(
        workflow_data, steps_method, {}, {}
    )
    print(  # noqa: T201f"   Result: {steps_result} (expected: 25)")

    # Test 3: CFG extraction
    print(  # noqa: T201"3. Testing CFG extraction:")
    cfg_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "cfg",
        "value_type": "float",
    }
    cfg_result = extractor._find_input_of_main_sampler(
        workflow_data, cfg_method, {}, {}
    )
    print(  # noqa: T201f"   Result: {cfg_result} (expected: 8.0)")

    # Test 4: Sampler name extraction
    print(  # noqa: T201"4. Testing sampler name extraction:")
    sampler_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "sampler_name",
        "value_type": "string",
    }
    sampler_result = extractor._find_input_of_main_sampler(
        workflow_data, sampler_method, {}, {}
    )
    print(  # noqa: T201f"   Result: '{sampler_result}' (expected: 'dpmpp_2m_sde_gpu')")

    # Test 5: Scheduler extraction
    print(  # noqa: T201"5. Testing scheduler extraction:")
    scheduler_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "scheduler",
        "value_type": "string",
    }
    scheduler_result = extractor._find_input_of_main_sampler(
        workflow_data, scheduler_method, {}, {}
    )
    print(  # noqa: T201f"   Result: '{scheduler_result}' (expected: 'karras')")

    # Test prompt extraction
    print(  # noqa: T201"\n📝 TESTING PROMPT EXTRACTION:")
    print(  # noqa: T201"-" * 32)

    prompt_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "positive_input_name": "positive",
        "text_input_name_in_encoder": "text",
        "text_encoder_node_types": [
            "CLIPTextEncode",
            "CLIPTextEncodeSD3",
            "T5TextEncode",
        ],
        "target_key": "prompt",
    }
    prompt_result = extractor._find_text_from_main_sampler_input(
        workflow_data, prompt_method, {}, {}
    )
    print(  # noqa: T201f"Positive prompt: '{prompt_result}'")

    negative_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "negative_input_name": "negative",
        "text_input_name_in_encoder": "text",
        "text_encoder_node_types": [
            "CLIPTextEncode",
            "CLIPTextEncodeSD3",
            "T5TextEncode",
        ],
        "target_key": "negative_prompt",
    }
    negative_result = extractor._find_text_from_main_sampler_input(
        workflow_data, negative_method, {}, {}
    )
    print(  # noqa: T201f"Negative prompt: '{negative_result}'")

    # Summary
    print(  # noqa: T201"\n🎯 SUMMARY:")
    print(  # noqa: T201"-" * 12)

    all_results = [
        seed_result,
        steps_result,
        cfg_result,
        sampler_result,
        scheduler_result,
        prompt_result,
        negative_result,
    ]
    successful = [r for r in all_results if r is not None]

    print(  # noqa: T201f"✅ Successfully extracted {len(successful)}/{len(all_results)} parameters")

    if len(successful) == len(all_results):
        print(  # noqa: T201"🎉 All parameter extraction working correctly!")
        print(  # noqa: T201"🔥 T5 parser should now handle SamplerCustomAdvanced nodes!")
    else:
        print(  # noqa: T201"❌ Some parameter extraction still failing")
        print(  # noqa: T201"   Check the debug output above for details")


if __name__ == "__main__":
    test_enhanced_parameter_extraction()
