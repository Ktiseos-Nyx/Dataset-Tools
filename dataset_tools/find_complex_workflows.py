#!/usr/bin/env python3
"""Find complex workflows that might trigger the bug."""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_tools.metadata_parser import parse_metadata

def find_complex_workflows():
    """Find workflows with Efficient Loader or String Literal nodes."""
    test_files = list(Path("/Users/duskfall/Desktop/Comfy_UI_DATA").glob("*.png"))
    
    for test_file in test_files[:15]:  # Test first 15 files
        try:
            result = parse_metadata(str(test_file))
            
            # Get raw workflow data
            raw_data = result.get('raw_tool_specific_data_section', {})
            if not isinstance(raw_data, dict) or 'nodes' not in raw_data:
                continue
                
            nodes = raw_data.get('nodes', [])
            
            # Check for complex workflow patterns
            has_efficient_loader = any(node.get('type') == 'Efficient Loader' for node in nodes)
            has_string_literal = any(node.get('type') == 'String Literal' for node in nodes)
            has_ksampler_efficient = any(node.get('type') == 'KSampler (Efficient)' for node in nodes)
            
            if has_efficient_loader or has_string_literal or has_ksampler_efficient:
                print(f"\n🎯 COMPLEX WORKFLOW FOUND: {test_file.name}")
                
                # Check the prompts
                prompts_section = result.get('prompt_data_section', {})
                positive = prompts_section.get('Positive', 'NOT_FOUND')
                negative = prompts_section.get('Negative', 'NOT_FOUND')
                
                print(f"   Efficient Loader: {has_efficient_loader}")
                print(f"   String Literal: {has_string_literal}")
                print(f"   KSampler (Efficient): {has_ksampler_efficient}")
                
                print(f"   Positive: {positive[:80]}...")
                print(f"   Negative: {negative[:80]}...")
                
                # Check if identical
                if positive == negative and positive != 'NOT_FOUND':
                    print(f"   ❌ IDENTICAL PROMPTS FOUND!")
                    return test_file
                    
        except Exception as e:
            print(f"Error processing {test_file.name}: {e}")
            continue
    
    print("\n❌ No complex workflows with identical prompts found")
    return None

if __name__ == "__main__":
    result = find_complex_workflows()
    if result:
        print(f"\n🔍 Problem file found: {result}")
    else:
        print("\n✅ No immediate issues found with complex workflows")