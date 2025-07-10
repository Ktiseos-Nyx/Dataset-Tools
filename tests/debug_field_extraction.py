#!/usr/bin/env python3
"""Debug field extraction for ComfyUI files."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s')

from dataset_tools.metadata_parser import parse_metadata

def debug_extraction():
    """Debug the complete extraction pipeline."""
    
    # Test with the FLUX file we know has "woman" in it
    test_file = "/Users/duskfall/Desktop/Comfy_UI_DATA/flux_00939_.png"
    
    if not Path(test_file).exists():
        print(f"❌ File not found: {test_file}")
        return False
    
    print(f"🔍 Debugging extraction pipeline: {Path(test_file).name}")
    print("="*80)
    
    result = parse_metadata(test_file)
    
    print("\n📊 COMPLETE RESULT STRUCTURE:")
    print("="*80)
    for key, value in result.items():
        if key == 'raw_tool_specific_data_section':
            print(f"  {key}: <large_workflow_data>")
        else:
            if isinstance(value, dict):
                print(f"  {key}: {dict(value)}")
            else:
                print(f"  {key}: {value}")
    
    print("\n🎯 PROMPT DATA SECTION:")
    print("="*80)
    prompt_section = result.get('prompt_data_section', {})
    if prompt_section:
        for key, value in prompt_section.items():
            print(f"  {key}: '{value}'")
    else:
        print("  ❌ NO PROMPT DATA SECTION FOUND!")
    
    print("\n🎯 CHECKING IF EXTRACTION METHODS WERE CALLED:")
    print("="*80)
    
    # Try direct method calls to see if they work
    raw_data = result.get('raw_tool_specific_data_section', {})
    if raw_data:
        print("  ✅ Raw workflow data exists")
        
        # Check if nodes contain our expected content
        nodes = raw_data.get('nodes', [])
        text_nodes = []
        for node in nodes:
            if isinstance(node, dict):
                node_type = node.get('class_type', node.get('type', ''))
                if any(encoder in node_type for encoder in ['CLIPTextEncode', 'ImpactWildcardEncode', 'T5TextEncode']):
                    widgets = node.get('widgets_values', [])
                    if widgets and isinstance(widgets[0], str):
                        text_nodes.append({
                            'id': node.get('id'),
                            'type': node_type,
                            'text': widgets[0]
                        })
        
        print(f"  📝 Found {len(text_nodes)} text nodes:")
        for node in text_nodes:
            print(f"    Node {node['id']} ({node['type']}): '{node['text']}'")
    else:
        print("  ❌ No raw workflow data found!")
    
    return True

if __name__ == "__main__":
    debug_extraction()