#!/usr/bin/env python3

"""
Debug T5 Architecture Detection parameter extraction
"""

import json
import logging
from pathlib import Path
from PIL import Image
from dataset_tools.metadata_engine.extractors.comfyui_extractors import ComfyUIExtractor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_t5_extraction():
    """Debug T5 parameter extraction with the user's problematic workflow."""
    
    print("🔍 DEBUGGING T5 PARAMETER EXTRACTION")
    print("=" * 45)
    
    # Use the T5 workflow data from the user's message
    workflow_data = {
        "3": {
            "inputs": {
                "seed": 687842170175819,
                "steps": 20,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["12", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSamplerAdvanced",
            "meta": {
                "title": "KSampler (Advanced)"
            }
        },
        "4": {
            "inputs": {
                "seed": 951413442465493,
                "steps": 5,
                "cfg": 3.5,
                "sampler_name": "dpmpp_sde_gpu",
                "scheduler": "normal",
                "denoise": 0.8,
                "model": ["13", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["3", 0]
            },
            "class_type": "KSamplerAdvanced",
            "meta": {
                "title": "KSampler (Advanced)"
            }
        },
        "6": {
            "inputs": {
                "text": "a woman with long red hair standing in a field of sunflowers, sunny day, golden hour, warm lighting, detailed, photorealistic",
                "clip": ["14", 0]
            },
            "class_type": "CLIPTextEncode",
            "meta": {
                "title": "CLIP Text Encode (Prompt)"
            }
        },
        "7": {
            "inputs": {
                "text": "blurry, low quality, worst quality, bad anatomy, extra limbs",
                "clip": ["14", 0]
            },
            "class_type": "CLIPTextEncode",
            "meta": {
                "title": "CLIP Text Encode (Prompt)"
            }
        },
        "12": {
            "inputs": {
                "guidance": 3.5,
                "model": ["16", 0]
            },
            "class_type": "FluxGuidance",
            "meta": {
                "title": "FluxGuidance"
            }
        },
        "14": {
            "inputs": {
                "clip_name1": "t5xxl_fp16.safetensors",
                "clip_name2": "clip_l.safetensors",
                "type": "flux"
            },
            "class_type": "DualCLIPLoader",
            "meta": {
                "title": "DualCLIPLoader"
            }
        }
    }
    
    print(f"Workflow has {len(workflow_data)} nodes")
    
    # Initialize extractor
    extractor = ComfyUIExtractor(logger)
    
    # Test T5 architecture detection
    print("\n🏗️ TESTING T5 ARCHITECTURE DETECTION:")
    print("-" * 42)
    
    method_def = {
        "architecture_families": {
            "flux": ["DualCLIPLoaderGGUF", "FluxGuidance", "ModelSamplingFlux"]
        }
    }
    
    t5_result = extractor._detect_t5_architecture(workflow_data, method_def, {}, {})
    print(f"T5 Detection Result: {t5_result}")
    
    # Test parameter extraction methods
    print("\n🔧 TESTING PARAMETER EXTRACTION:")
    print("-" * 37)
    
    # Test seed extraction
    seed_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "seed",
        "value_type": "integer"
    }
    seed_result = extractor._find_input_of_main_sampler(workflow_data, seed_method, {}, {})
    print(f"Seed: {seed_result}")
    
    # Test steps extraction
    steps_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "steps",
        "value_type": "integer"
    }
    steps_result = extractor._find_input_of_main_sampler(workflow_data, steps_method, {}, {})
    print(f"Steps: {steps_result}")
    
    # Test sampler name extraction
    sampler_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "sampler_name",
        "value_type": "string"
    }
    sampler_result = extractor._find_input_of_main_sampler(workflow_data, sampler_method, {}, {})
    print(f"Sampler: {sampler_result}")
    
    # Test scheduler extraction
    scheduler_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "input_key": "scheduler",
        "value_type": "string"
    }
    scheduler_result = extractor._find_input_of_main_sampler(workflow_data, scheduler_method, {}, {})
    print(f"Scheduler: {scheduler_result}")
    
    # Test prompt extraction
    print("\n📝 TESTING PROMPT EXTRACTION:")
    print("-" * 32)
    
    prompt_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "positive_input_name": "positive",
        "text_input_name_in_encoder": "text",
        "text_encoder_node_types": ["CLIPTextEncode", "CLIPTextEncodeSD3", "T5TextEncode", "BNK_CLIPTextEncodeAdvanced"],
        "target_key": "prompt"
    }
    prompt_result = extractor._find_text_from_main_sampler_input(workflow_data, prompt_method, {}, {})
    print(f"Positive prompt: {prompt_result}")
    
    negative_method = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "negative_input_name": "negative",
        "text_input_name_in_encoder": "text",
        "text_encoder_node_types": ["CLIPTextEncode", "CLIPTextEncodeSD3", "T5TextEncode", "BNK_CLIPTextEncodeAdvanced"],
        "target_key": "negative_prompt"
    }
    negative_result = extractor._find_text_from_main_sampler_input(workflow_data, negative_method, {}, {})
    print(f"Negative prompt: {negative_result}")
    
    # Test model extraction
    print("\n🤖 TESTING MODEL EXTRACTION:")
    print("-" * 30)
    
    model_method = {
        "class_type": "DualCLIPLoader",
        "field_name": "clip_name1"
    }
    model_result = extractor._extract_comfy_node_by_class(workflow_data, model_method, {}, {})
    print(f"T5 Model: {model_result}")
    
    clip_method = {
        "class_type": "DualCLIPLoader",
        "field_name": "clip_name2"
    }
    clip_result = extractor._extract_comfy_node_by_class(workflow_data, clip_method, {}, {})
    print(f"CLIP Model: {clip_result}")

if __name__ == "__main__":
    debug_t5_extraction()