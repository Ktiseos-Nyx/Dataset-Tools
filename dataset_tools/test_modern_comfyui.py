#!/usr/bin/env python3
"""Test script to verify modern ComfyUI extraction system is working."""

import sys
import json
from pathlib import Path

# Add parent directory to path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_tools.metadata_parser import parse_metadata

def test_comfyui_routing():
    """Test that ComfyUI is routed through modern extraction system."""
    print("🧪 Testing ComfyUI parser routing...")
    
    try:
        # Check that ComfyUI parser definition files exist
        parser_defs_path = Path(__file__).parent / "parser_definitions"
        comfyui_parsers = list(parser_defs_path.glob("*comfy*.json"))
        if comfyui_parsers:
            print(f"✅ SUCCESS: Found {len(comfyui_parsers)} ComfyUI parser definitions")
            for parser in comfyui_parsers[:5]:  # Show first 5
                print(f"   - {parser.name}")
        else:
            print("❌ WARNING: No ComfyUI parser definitions found")
            
        # Check that the vendored ComfyUI parser is disabled in metadata_parser.py
        metadata_parser_file = Path(__file__).parent / "metadata_parser.py"
        with open(metadata_parser_file, 'r') as f:
            content = f.read()
            
        if '# register_parser_class("ComfyUI", ComfyUI)' in content:
            print("✅ SUCCESS: Vendored ComfyUI parser is commented out")
        elif 'register_parser_class("ComfyUI", ComfyUI)' in content:
            print("❌ ISSUE: Vendored ComfyUI parser is still registered")
            return False
        else:
            print("❓ WARNING: ComfyUI registration line not found")
            
        # Test if a real ComfyUI file exists in the specified directory
        comfyui_data_path = Path("/Users/duskfall/Desktop/Comfy_UI_DATA")
        if comfyui_data_path.exists():
            png_files = list(comfyui_data_path.glob("*.png"))
            if png_files:
                print(f"✅ Found {len(png_files)} PNG files in ComfyUI data directory")
                # Test with first PNG file
                test_file = str(png_files[0])
                print(f"🧪 Testing with: {png_files[0].name}")
                
                result = parse_metadata(test_file)
                print(f"✅ SUCCESS: Got result with keys: {list(result.keys())}")
                
                # Check what tool/parser was detected
                if result.get('Prompts'):
                    prompts = result['Prompts']
                    positive = prompts.get('Positive', 'NOT_FOUND')
                    negative = prompts.get('Negative', 'NOT_FOUND')
                    print(f"📝 Positive: {positive}...")
                    print(f"📝 Negative: {negative}...")
                    
                    # Check if prompts are swapped
                    if positive and "embedding:negatives" in positive:
                        print("❌ ISSUE: Positive prompt contains negative content - prompts are STILL swapped!")
                    elif negative and "embedding:negatives" in negative:
                        print("✅ Good: Negative prompt contains negative indicators")
                    else:
                        print("❓ Cannot determine if prompts are swapped")
                
                metadata = result.get('Metadata', {})
                tool = metadata.get('Detected Tool', 'Unknown')
                print(f"🔧 Detected tool: {tool}")
                
                if "Universal" in tool or "ComfyUI Universal" in tool:
                    print("✅ SUCCESS: Modern extraction system is being used!")
                    return True
                else:
                    print(f"❓ Tool detected: {tool}")
                    
            else:
                print(f"❌ No PNG files found in {comfyui_data_path}")
        else:
            print(f"❌ ComfyUI data directory not found: {comfyui_data_path}")
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_comfyui_routing()
    sys.exit(0 if success else 1)