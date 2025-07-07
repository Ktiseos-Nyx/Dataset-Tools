#!/usr/bin/env python3

"""
Analyze the Civitai ComfyUI data structure to understand field extraction issues.
"""

import sys
import os
from pathlib import Path
import json

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_civitai_structure():
    """Analyze the data structure of the Civitai ComfyUI file."""
    
    print("🔍 CIVITAI COMFYUI STRUCTURE ANALYSIS")
    print("=" * 35)
    
    test_file = "/Users/duskfall/Downloads/Metadata Samples/B4V0V3FKDVZHZZRERKQ31YFR10.jpeg"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {Path(test_file).name}")
        return
    
    print(f"📁 Analyzing: {Path(test_file).name}")
    
    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer
        
        preparer = ContextDataPreparer()
        context = preparer.prepare_context(test_file)
        
        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            print(f"✅ UserComment extracted: {len(user_comment)} characters")
            
            # Parse as JSON
            try:
                data = json.loads(user_comment)
                print(f"✅ Valid JSON with {len(data)} top-level keys")
                
                print("\n📊 TOP-LEVEL STRUCTURE:")
                for key in list(data.keys())[:10]:
                    value = data[key]
                    print(f"   {key}: {type(value).__name__}")
                    if isinstance(value, str) and len(value) < 100:
                        print(f"      = {value}")
                    elif isinstance(value, dict):
                        print(f"      = dict with {len(value)} keys: {list(value.keys())[:5]}")
                    elif isinstance(value, list):
                        print(f"      = list with {len(value)} items")
                
                # Check for extra.extraMetadata
                if "extra" in data and isinstance(data["extra"], dict):
                    extra = data["extra"]
                    print(f"\n📊 EXTRA SECTION:")
                    print(f"   extra has {len(extra)} keys: {list(extra.keys())}")
                    
                    if "extraMetadata" in extra:
                        extra_metadata = extra["extraMetadata"]
                        print(f"\n📊 EXTRA METADATA:")
                        print(f"   Type: {type(extra_metadata).__name__}")
                        
                        if isinstance(extra_metadata, str):
                            print(f"   Length: {len(extra_metadata)} characters")
                            print(f"   Preview: {extra_metadata[:200]}...")
                            
                            # Try to parse as JSON
                            try:
                                nested_data = json.loads(extra_metadata)
                                print(f"   ✅ extraMetadata is valid JSON with {len(nested_data)} keys")
                                print(f"   Keys: {list(nested_data.keys())}")
                                
                                # Look for prompt-related fields
                                for key in nested_data.keys():
                                    if "prompt" in key.lower():
                                        print(f"   🎯 FOUND PROMPT FIELD: {key} = {str(nested_data[key])[:100]}...")
                                
                            except json.JSONDecodeError as e:
                                print(f"   ❌ extraMetadata is not valid JSON: {e}")
                        
                        elif isinstance(extra_metadata, dict):
                            print(f"   Already parsed dict with {len(extra_metadata)} keys: {list(extra_metadata.keys())}")
                
                # Look for direct prompt fields in root
                print(f"\n🔍 SEARCHING FOR PROMPT FIELDS:")
                for key in data.keys():
                    if "prompt" in key.lower():
                        print(f"   🎯 ROOT LEVEL: {key} = {str(data[key])[:100]}...")
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON: {e}")
                print(f"Raw content preview: {user_comment[:200]}...")
        else:
            print("❌ No UserComment extracted")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_civitai_structure()