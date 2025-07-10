#!/usr/bin/env python3
"""Test the new advanced ComfyUI extractors"""

import json
import sys
from pathlib import Path

# Add the project to the path
sys.path.insert(0, str(Path(__file__).parent))

from dataset_tools.metadata_engine.extractors.comfyui_extractors import ComfyUIExtractor
from dataset_tools.logger import get_logger

def test_tipo_detection():
    """Test TIPO enhancement detection"""
    
    # Sample TIPO workflow data (from your discovered nodes)
    sample_workflow = {
        "prompt": {
            "1886": {
                "class_type": "TIPO",
                "inputs": {
                    "tags": "1girl, steampunk, gears, hydrangea, scenery, outdoors, ",
                    "nl_prompt": "A detailed character and background with intricate textures",
                    "tipo_model": "KBlueLeaf/TIPO-500M | TIPO-500M_epoch5-F16.gguf",
                    "temperature": 0.75,
                    "tag_length": "long",
                    "nl_length": "very_short",
                    "seed": 24
                }
            }
        }
    }
    
    logger = get_logger("test")
    extractor = ComfyUIExtractor(logger)
    
    # Test the TIPO detection
    result = extractor._detect_tipo_enhancement(
        sample_workflow, {}, {}, {}
    )
    
    print("🎯 TIPO Detection Test:")
    print(f"Result: {json.dumps(result, indent=2)}")
    print()

def test_complexity_scoring():
    """Test workflow complexity scoring"""
    
    # Sample complex workflow with various node types
    complex_workflow = {
        "prompt": {
            "1": {"class_type": "CheckpointLoaderSimple"},  # Basic (1)
            "2": {"class_type": "CLIPTextEncode"},  # Basic (1)  
            "3": {"class_type": "TIPO"},  # Advanced (3)
            "4": {"class_type": "T5TextEncode"},  # Advanced (3)
            "5": {"class_type": "ConditioningSetTimestepRange"},  # Advanced (3)
            "6": {"class_type": "Uncond Zero"},  # Expert (4)
            "7": {"class_type": "ProPostFilmGrain"},  # Advanced (3)
            "8": {"class_type": "SamplerCustom"},  # Intermediate (2)
        }
    }
    
    logger = get_logger("test")
    extractor = ComfyUIExtractor(logger)
    
    # Test complexity scoring
    result = extractor._calculate_workflow_complexity(
        complex_workflow, {}, {}, {}
    )
    
    print("📊 Workflow Complexity Test:")
    print(f"Result: {json.dumps(result, indent=2)}")
    print()

def test_upscaling_detection():
    """Test advanced upscaling detection"""
    
    # Sample workflow with upscaling (from your discovered nodes)
    upscaling_workflow = {
        "prompt": {
            "249": {
                "class_type": "UpscaleModelLoader", 
                "inputs": {
                    "model_name": "4x-UltraSharp.pth"
                }
            },
            "250": {
                "class_type": "ImageUpscaleWithModel",
                "inputs": {
                    "upscale_model": ["249", 0],
                    "image": ["374", 0]
                }
            }
        }
    }
    
    logger = get_logger("test")
    extractor = ComfyUIExtractor(logger)
    
    # Test upscaling detection
    result = extractor._detect_advanced_upscaling(
        upscaling_workflow, {}, {}, {}
    )
    
    print("🚀 Advanced Upscaling Test:")
    print(f"Result: {json.dumps(result, indent=2)}")
    print()

def test_custom_nodes_detection():
    """Test custom node ecosystem detection"""
    
    # Sample workflow with custom nodes (from your discovered nodes) 
    custom_workflow = {
        "prompt": {
            "1": {"class_type": "ShowText|pysssss"},  # pythonsssss pack
            "2": {"class_type": "WidthHeightMittimi01"},  # mittimi pack
            "3": {"class_type": "Anything Everywhere"},  # rgthree pack
            "4": {"class_type": "SaveImagePlus"},  # was_node_suite
            "5": {"class_type": "TIPO"},  # comfyui_controlnet_aux
        }
    }
    
    logger = get_logger("test")
    extractor = ComfyUIExtractor(logger)
    
    # Test custom node detection
    result = extractor._detect_custom_node_ecosystems(
        custom_workflow, {}, {}, {}
    )
    
    print("🔌 Custom Node Ecosystems Test:")
    print(f"Result: {json.dumps(result, indent=2)}")
    print()

if __name__ == "__main__":
    print("🧪 Testing New Advanced ComfyUI Extractors")
    print("=" * 50)
    
    try:
        test_tipo_detection()
        test_complexity_scoring()
        test_upscaling_detection()
        test_custom_nodes_detection()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()