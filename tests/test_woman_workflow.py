#!/usr/bin/env python3
"""Test the specific 'woman' workflow you provided."""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')

from dataset_tools.metadata_engine.extractors.comfyui_extractors import ComfyUIExtractor
from dataset_tools.metadata_engine.extractors.comfyui_extractor_manager import ComfyUIExtractorManager

def test_woman_workflow():
    """Test the 'woman' workflow directly."""
    
    # The workflow data you provided
    workflow_data = {
        'id': 'd088798f-091d-4d42-9551-88a1dd59994d',
        'nodes': [
            # ... other nodes ...
            {
                'id': 41, 
                'type': 'CLIPTextEncode', 
                'widgets_values': ['woman'],
                'inputs': [
                    {'name': 'clip', 'type': 'CLIP', 'link': 145}, 
                    {'name': 'text', 'type': 'STRING', 'link': None}
                ], 
                'outputs': [
                    {'name': 'CONDITIONING', 'type': 'CONDITIONING', 'slot_index': 0, 'links': [120]}
                ]
            },
            {
                'id': 55, 
                'type': 'BasicGuider',
                'inputs': [
                    {'name': 'model', 'type': 'MODEL', 'link': 144}, 
                    {'name': 'conditioning', 'type': 'CONDITIONING', 'link': 121}
                ], 
                'outputs': [
                    {'name': 'GUIDER', 'type': 'GUIDER', 'slot_index': 0, 'links': [139]}
                ]
            },
            {
                'id': 60, 
                'type': 'FluxGuidance',
                'inputs': [
                    {'name': 'conditioning', 'type': 'CONDITIONING', 'link': 120}, 
                    {'name': 'guidance', 'type': 'FLOAT', 'link': None}
                ], 
                'outputs': [
                    {'name': 'CONDITIONING', 'type': 'CONDITIONING', 'slot_index': 0, 'links': [121]}
                ]
            }
        ],
        'links': [
            [120, 41, 0, 60, 0, 'CONDITIONING'],  # CLIPTextEncode -> FluxGuidance
            [121, 60, 0, 55, 1, 'CONDITIONING'],  # FluxGuidance -> BasicGuider
            [139, 55, 0, 56, 1, 'GUIDER'],        # BasicGuider -> SamplerCustomAdvanced
            # ... other links ...
        ]
    }
    
    print("🧪 Testing 'woman' workflow extraction...")
    
    # Initialize extractor
    logger = logging.getLogger("test")
    extractor = ComfyUIExtractor(logger)
    
    # Test positive prompt extraction
    fake_method_def = {
        "sampler_node_types": ["BasicGuider", "SamplerCustomAdvanced"],
        "positive_input_name": "positive",
        "text_encoder_node_types": ["CLIPTextEncode"]
    }
    
    result = extractor._find_legacy_text_from_main_sampler_input(
        workflow_data, fake_method_def, {}, {}
    )
    
    print(f"\n📝 Extraction Result: '{result}'")
    
    if result.strip().lower() == "woman":
        print("✅ SUCCESS: Correctly extracted 'woman' prompt!")
        return True
    elif result == "":
        print("❌ FAIL: No text extracted")
        return False
    else:
        print(f"❓ UNEXPECTED: Got '{result}' instead of 'woman'")
        return False

if __name__ == "__main__":
    success = test_woman_workflow()
    sys.exit(0 if success else 1)