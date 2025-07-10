#!/usr/bin/env python3
"""Debug why specific ComfyUI files are failing extraction."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')

from dataset_tools.metadata_parser import parse_metadata

def debug_failed_file():
    """Debug a file that's failing extraction."""
    
    # Test a file we know is failing
    test_file = "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_00180_.png"
    
    if not Path(test_file).exists():
        print(f"❌ File not found: {test_file}")
        return False
    
    print(f"🔍 Debugging failed extraction: {Path(test_file).name}")
    print("="*80)
    
    result = parse_metadata(test_file)
    
    # Check what we got
    prompts = result.get('prompt_data_section', {})
    positive = prompts.get('Positive', '').strip()
    negative = prompts.get('Negative', '').strip()
    
    print(f"Positive extracted: '{positive}'")
    print(f"Negative extracted: '{negative}'")
    
    # Check raw workflow
    raw_data = result.get('raw_tool_specific_data_section', {})
    if raw_data and isinstance(raw_data, str):
        import json
        try:
            raw_data = json.loads(raw_data)
        except:
            pass
    
    if isinstance(raw_data, dict) and 'nodes' in raw_data:
        nodes = raw_data['nodes']
        
        print(f"\n📝 WORKFLOW ANALYSIS:")
        print("="*80)
        
        # Find all text nodes
        text_nodes = []
        sampler_nodes = []
        
        for node in nodes:
            if isinstance(node, dict):
                node_id = node.get('id')
                node_type = node.get('class_type', node.get('type', ''))
                
                # Check for text nodes
                if any(encoder in node_type for encoder in [
                    'CLIPTextEncode', 'T5TextEncode', 'ImpactWildcardEncode', 
                    'PixArtT5TextEncode', 'String Literal'
                ]):
                    widgets = node.get('widgets_values', [])
                    if widgets and isinstance(widgets[0], str):
                        text_nodes.append({
                            'id': node_id,
                            'type': node_type,
                            'text': widgets[0]
                        })
                
                # Check for sampler nodes
                if any(sampler in node_type for sampler in [
                    'KSampler', 'BasicGuider', 'SamplerCustomAdvanced', 
                    'KSamplerSelect', 'SamplerCustom'
                ]):
                    inputs = node.get('inputs', [])
                    sampler_nodes.append({
                        'id': node_id,
                        'type': node_type,
                        'inputs': inputs
                    })
        
        print(f"📝 Text nodes found: {len(text_nodes)}")
        for node in text_nodes:
            print(f"   Node {node['id']} ({node['type']}): '{node['text']}'")
        
        print(f"\n🎛️ Sampler nodes found: {len(sampler_nodes)}")
        for node in sampler_nodes:
            print(f"   Node {node['id']} ({node['type']})")
            for inp in node['inputs']:
                if isinstance(inp, dict):
                    print(f"      Input '{inp.get('name')}' link: {inp.get('link')}")
        
        if text_nodes and not positive:
            print(f"\n🚨 PROBLEM: Found {len(text_nodes)} text nodes but extraction failed!")
            print("   This suggests the traversal logic can't connect samplers to text nodes.")
        
    return True

if __name__ == "__main__":
    debug_failed_file()