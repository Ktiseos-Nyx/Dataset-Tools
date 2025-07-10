#!/usr/bin/env python3
"""Debug wildcard workflow extraction."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')

from dataset_tools.metadata_parser import parse_metadata

def debug_wildcard():
    """Debug wildcard workflow extraction."""
    
    # Test a wildcard file
    test_file = "/Users/duskfall/Downloads/image_workflows_for_Dusk/animugirl1.png"
    
    if not Path(test_file).exists():
        print(f"❌ File not found: {test_file}")
        return False
    
    print(f"🔍 Debugging wildcard workflow: {Path(test_file).name}")
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
        
        print(f"\n📝 WILDCARD WORKFLOW ANALYSIS:")
        print("="*80)
        
        # Find wildcard processors and samplers
        wildcard_nodes = []
        auto_negative_nodes = []
        sampler_nodes = []
        text_encoder_nodes = []
        
        # Look in nodes (dict format)
        for node_id, node in nodes.items():
            if isinstance(node, dict):
                class_type = node.get('class_type', '')
                
                if 'ImpactWildcardProcessor' in class_type:
                    wildcard_nodes.append({
                        'id': node_id,
                        'type': class_type,
                        'inputs': node.get('inputs', {})
                    })
                
                if 'AutoNegativePrompt' in class_type:
                    auto_negative_nodes.append({
                        'id': node_id,
                        'type': class_type,
                        'inputs': node.get('inputs', {})
                    })
                
                if 'Sampler' in class_type or class_type == 'KSamplerAdvanced':
                    sampler_nodes.append({
                        'id': node_id,
                        'type': class_type,
                        'inputs': node.get('inputs', {})
                    })
                
                if 'CLIPTextEncode' in class_type:
                    text_encoder_nodes.append({
                        'id': node_id,
                        'type': class_type,
                        'inputs': node.get('inputs', {})
                    })
        
        print(f"🎯 Wildcard Processors: {len(wildcard_nodes)}")
        for node in wildcard_nodes:
            print(f"   Node {node['id']}: {node['type']}")
            populated_text = node['inputs'].get('populated_text', '')
            wildcard_text = node['inputs'].get('wildcard_text', '')
            print(f"     populated_text: {populated_text[:100]}..." if len(populated_text) > 100 else f"     populated_text: {populated_text}")
            print(f"     wildcard_text: {wildcard_text[:100]}..." if len(wildcard_text) > 100 else f"     wildcard_text: {wildcard_text}")
        
        print(f"\n🎯 Auto Negative Prompts: {len(auto_negative_nodes)}")
        for node in auto_negative_nodes:
            print(f"   Node {node['id']}: {node['type']}")
            base_negative = node['inputs'].get('base_negative', '')
            print(f"     base_negative: {base_negative}")
        
        print(f"\n🎛️ Samplers: {len(sampler_nodes)}")
        for node in sampler_nodes:
            print(f"   Node {node['id']}: {node['type']}")
            for input_name, input_val in node['inputs'].items():
                print(f"     {input_name}: {input_val}")
        
        print(f"\n📝 Text Encoders: {len(text_encoder_nodes)}")
        for node in text_encoder_nodes:
            print(f"   Node {node['id']}: {node['type']}")
            for input_name, input_val in node['inputs'].items():
                print(f"     {input_name}: {input_val}")
        
        if wildcard_nodes and not positive:
            print(f"\n🚨 WILDCARD PROBLEM: Found {len(wildcard_nodes)} wildcard processors but extraction failed!")
            print("   This suggests the traversal isn't reaching these nodes from the samplers.")
    
    return True

if __name__ == "__main__":
    debug_wildcard()