#!/usr/bin/env python3
"""Test FLUX traversal specifically."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging to see our debug messages
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')

from dataset_tools.metadata_parser import parse_metadata

def test_flux_traversal():
    """Test the specific FLUX file that's not extracting text."""
    test_file = "/Users/duskfall/Desktop/Comfy_UI_DATA/flux_00939_.png"
    
    if not Path(test_file).exists():
        print(f"❌ File not found: {test_file}")
        return False
    
    print(f"🧪 Testing FLUX traversal: {Path(test_file).name}")
    
    result = parse_metadata(test_file)
    
    prompts_section = result.get('prompt_data_section', {})
    positive = prompts_section.get('Positive', 'NOT_FOUND')
    negative = prompts_section.get('Negative', 'NOT_FOUND')
    
    print("\n" + "="*80)
    print("FLUX WORKFLOW RESULTS:")
    print("="*80)
    print(f"Positive Prompt: {positive}")
    print(f"Negative Prompt: {negative}")
    print("="*80)
    
    # Check raw workflow for the expected text
    raw_data = result.get('raw_tool_specific_data_section', {})
    if isinstance(raw_data, dict) and 'nodes' in raw_data:
        nodes = raw_data['nodes']
        print("\n📝 TEXT NODES FOUND IN WORKFLOW:")
        for node in nodes:
            if isinstance(node, dict):
                node_id = node.get('id')
                node_type = node.get('class_type', node.get('type', ''))
                widgets = node.get('widgets_values', [])
                
                if any(encoder_type in node_type for encoder_type in [
                    "CLIPTextEncode", "T5TextEncode", "ImpactWildcardEncode", 
                    "BNK_CLIPTextEncodeAdvanced", "CLIPTextEncodeAdvanced",
                    "PixArtT5TextEncode"
                ]):
                    if widgets and isinstance(widgets[0], str):
                        text_preview = widgets[0][:100]
                        print(f"   Node {node_id} ({node_type}): {text_preview}...")
                        
                        # Check if this contains "woman"
                        if "woman" in text_preview.lower():
                            print(f"   🎯 FOUND 'WOMAN' TEXT HERE! ^^^")
    
    # Success if we extracted the expected text
    if positive != 'NOT_FOUND' and positive != '' and 'woman' in positive.lower():
        print("\n✅ SUCCESS: Found 'woman' in positive prompt!")
        return True
    elif positive == 'NOT_FOUND' or positive == '':
        print("\n❌ FAIL: No positive prompt extracted")
        return False
    else:
        print(f"\n❓ UNEXPECTED: Positive prompt doesn't contain 'woman': {positive}")
        return False

if __name__ == "__main__":
    success = test_flux_traversal()
    sys.exit(0 if success else 1)