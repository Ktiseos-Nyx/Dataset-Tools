#!/usr/bin/env python3
"""Debug the specific workflow that has identical prompts."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging to see our debug messages
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')

from dataset_tools.metadata_parser import parse_metadata

def debug_workflow():
    """Debug the workflow with identical prompts."""
    # Look for a file that has the identical prompt issue
    test_files = list(Path("/Users/duskfall/Desktop/Comfy_UI_DATA").glob("*.png"))
    
    for test_file in test_files:
        print(f"\n🔍 Checking: {test_file.name}")
        
        result = parse_metadata(str(test_file))
        
        prompts_section = result.get('prompt_data_section', {})
        positive = prompts_section.get('Positive', 'NOT_FOUND')
        negative = prompts_section.get('Negative', 'NOT_FOUND')
        
        # Check if they're identical (the bug)
        if positive == negative and positive != 'NOT_FOUND' and len(positive) > 50:
            print(f"\n🎯 FOUND DUPLICATE PROMPTS FILE: {test_file.name}")
            print(f"Both prompts are: {positive[:100]}...")
            
            # Get the raw workflow to analyze
            raw_data = result.get('raw_tool_specific_data_section', {})
            if isinstance(raw_data, dict) and 'nodes' in raw_data:
                analyze_workflow_structure(raw_data)
            
            return True
            
        print(f"   Positive preview: {positive[:50]}...")
        print(f"   Negative preview: {negative[:50]}...")
    
    print("❌ No files with identical prompts found")
    return False

def analyze_workflow_structure(workflow_data):
    """Analyze the workflow structure to understand the issue."""
    nodes = workflow_data.get('nodes', [])
    links = workflow_data.get('links', [])
    
    print("\n=== WORKFLOW STRUCTURE ANALYSIS ===")
    
    # Find text input nodes
    text_nodes = []
    for node in nodes:
        if node.get('type') in ['String Literal', 'CLIPTextEncode']:
            widgets = node.get('widgets_values', [])
            if widgets and isinstance(widgets[0], str):
                text_preview = widgets[0][:60].replace('\n', ' ')
                text_nodes.append({
                    'id': node.get('id'),
                    'type': node.get('type'), 
                    'text': text_preview,
                    'title': node.get('title', 'No title')
                })
    
    print("\n📝 TEXT INPUT NODES:")
    for node in text_nodes:
        print(f"   Node {node['id']} ({node['type']}): {node['title']}")
        print(f"      Text: {node['text']}...")
    
    # Find sampler nodes
    sampler_nodes = []
    for node in nodes:
        node_type = node.get('type', '')
        if 'Sampler' in node_type or 'KSampler' in node_type:
            sampler_nodes.append({
                'id': node.get('id'),
                'type': node_type,
                'inputs': node.get('inputs', [])
            })
    
    print("\n🎛️ SAMPLER NODES:")
    for node in sampler_nodes:
        print(f"   Node {node['id']} ({node['type']})")
        for inp in node['inputs']:
            print(f"      Input '{inp.get('name')}' from link {inp.get('link')}")
    
    # Trace the links
    print("\n🔗 LINK ANALYSIS:")
    for link in links:
        if len(link) >= 6:
            link_id, source_id, source_out, target_id, target_in, link_type = link[:6]
            print(f"   Link {link_id}: Node {source_id}[{source_out}] → Node {target_id}[{target_in}] ({link_type})")

if __name__ == "__main__":
    debug_workflow()