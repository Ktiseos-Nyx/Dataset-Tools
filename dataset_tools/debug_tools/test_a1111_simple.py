#!/usr/bin/env python3

"""
Simple A1111 JPEG test.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_a1111_simple():
    """Simple A1111 JPEG test."""
    
    print("🔧 SIMPLE A1111 JPEG TEST")
    print("=" * 26)
    
    test_file = "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_01803_.jpeg"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {Path(test_file).name}")
        return
    
    print(f"📁 Testing: {Path(test_file).name}")
    
    try:
        from dataset_tools.metadata_engine import MetadataEngine
        import logging
        
        # Enable debug logging
        logging.basicConfig(level=logging.DEBUG)
        
        parser_definitions_path = os.path.join(os.path.dirname(__file__), "parser_definitions")
        engine = MetadataEngine(parser_definitions_path)
        
        print("\n🔍 Running MetadataEngine...")
        result = engine.get_parser_for_file(test_file)
        
        if result:
            print(f"✅ SUCCESS: {type(result)}")
            if isinstance(result, dict):
                tool = result.get("tool", "Unknown")
                print(f"   Tool: {tool}")
                
                if "prompt" in result:
                    prompt = result.get("prompt", "")
                    print(f"   Prompt: {prompt[:50]}..." if prompt else "   No prompt")
                
                if "parameters" in result:
                    params = result.get("parameters", {})
                    print(f"   Parameters: {list(params.keys())}")
                    if "steps" in params:
                        print(f"   Steps: {params['steps']}")
                    if "seed" in params:
                        print(f"   Seed: {params['seed']}")
            else:
                print(f"   Parser instance: {result}")
        else:
            print("❌ FAILED: MetadataEngine returned None")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_a1111_simple()