#!/usr/bin/env python3
"""Test KSamplerSelect workflow simulation."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')

from dataset_tools.metadata_engine.extractors.comfyui_extractors import ComfyUIExtractor

def simulate_ksamplerselect_workflow():
    """Simulate a modern architecture workflow with KSamplerSelect only."""
    
    # Create a logger for testing
    logger = logging.getLogger("test")
    
    # Initialize extractor
    extractor = ComfyUIExtractor(logger)
    
    # Simulate a FLUX/modern architecture workflow with only KSamplerSelect
    # (no traditional KSampler with inputs)
    mock_workflow = {
        "nodes": {
            "1": {
                "id": 1,
                "class_type": "T5TextEncode",
                "widgets_values": ["beautiful woman portrait, detailed face, masterpiece"]
            },
            "2": {
                "id": 2,
                "class_type": "CLIPTextEncode", 
                "widgets_values": ["ugly, bad quality, blurry"]
            },
            "3": {
                "id": 3,
                "class_type": "KSamplerSelect",
                "inputs": [],  # Empty inputs - this is the key difference
                "widgets_values": ["dpmpp_2m"]
            },
            "4": {
                "id": 4,
                "class_type": "PixArtT5TextEncode",
                "widgets_values": ["amazing sci-fi landscape, cyberpunk city"]
            }
        },
        "links": []
    }
    
    print("🧪 Testing KSamplerSelect workflow simulation...")
    print("="*80)
    
    # Test positive extraction
    print("Testing positive prompt extraction:")
    positive = extractor._extract_from_workflow_text_nodes(mock_workflow, "positive")
    print(f"Positive result: '{positive}'")
    
    # Test negative extraction
    print("\\nTesting negative prompt extraction:")
    negative = extractor._extract_from_workflow_text_nodes(mock_workflow, "negative")
    print(f"Negative result: '{negative}'")
    
    # Test the full method that should call workflow-only extraction
    print("\\n" + "="*80)
    print("Testing full extraction method (should trigger workflow-only):")
    
    fake_method_def = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced", "KSampler_A1111"],
        "positive_input_name": "positive",
        "text_input_name_in_encoder": "text",
        "text_encoder_node_types": ["CLIPTextEncode", "BNK_CLIPTextEncodeAdvanced", "CLIPTextEncodeAdvanced", "PixArtT5TextEncode"]
    }
    
    full_positive = extractor._find_legacy_text_from_main_sampler_input(
        mock_workflow, fake_method_def, {}, {}
    )
    print(f"Full method positive result: '{full_positive}'")
    
    print("\\n" + "="*80)
    print("📊 SIMULATION RESULTS:")
    print("="*80)
    print(f"✅ Workflow-only positive: '{positive}'")
    print(f"✅ Workflow-only negative: '{negative}'") 
    print(f"✅ Full method result: '{full_positive}'")
    
    success = bool(positive and full_positive)
    if success:
        print("\\n🎉 SUCCESS: KSamplerSelect workflow-only extraction is working!")
    else:
        print("\\n🚨 FAILURE: KSamplerSelect workflow-only extraction needs fixes!")
    
    return success

if __name__ == "__main__":
    simulate_ksamplerselect_workflow()