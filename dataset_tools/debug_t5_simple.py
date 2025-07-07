#!/usr/bin/env python3

"""
Simple debug test for T5 traversal methods.
"""

import json
import logging

# Configure logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_simple_traversal():
    """Simple test to understand the T5 traversal issue."""
    
    print("🔧 SIMPLE T5 TRAVERSAL DEBUG")
    print("=" * 30)
    
    # Sample T5 workflow data (minimal example)
    sample_t5_data = {
        "1": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "t5xxl_fp16.safetensors",
                "clip_name2": "clip_l.safetensors"
            }
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "beautiful landscape with mountains and trees",
                "clip": [1, 0]
            }
        },
        "3": {
            "class_type": "CLIPTextEncode", 
            "inputs": {
                "text": "low quality, blurry",
                "clip": [1, 0]
            }
        },
        "4": {
            "class_type": "KSampler",
            "inputs": {
                "model": [5, 0],
                "positive": [2, 0],
                "negative": [3, 0],
                "latent_image": [6, 0],
                "seed": 123456,
                "steps": 20,
                "cfg": 7.5,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0
            }
        },
        "5": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "sd3_medium_incl_clips_t5xxlfp16.safetensors"
            }
        },
        "6": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 1024,
                "height": 1024,
                "batch_size": 1
            }
        }
    }
    
    print("1. Manual traversal test:")
    print(f"   Sample data has {len(sample_t5_data)} nodes")
    
    # Find the sampler node
    sampler_node = None
    for node_id, node_data in sample_t5_data.items():
        print(f"   Node {node_id}: {node_data.get('class_type')}")
        if node_data.get('class_type') == 'KSampler':
            sampler_node = node_data
            sampler_id = node_id
            print(f"   ✅ Found sampler node: {node_id}")
    
    if sampler_node:
        print(f"   Sampler inputs: {sampler_node.get('inputs', {})}")
        
        # Get positive connection
        positive_connection = sampler_node.get('inputs', {}).get('positive')
        print(f"   Positive connection: {positive_connection}")
        
        if positive_connection and isinstance(positive_connection, list):
            positive_node_id = str(positive_connection[0])
            print(f"   Looking for node {positive_node_id}")
            
            positive_node = sample_t5_data.get(positive_node_id)
            if positive_node:
                print(f"   ✅ Found positive node: {positive_node.get('class_type')}")
                print(f"   Positive node inputs: {positive_node.get('inputs', {})}")
                
                # Extract text
                text = positive_node.get('inputs', {}).get('text')
                print(f"   ✅ Extracted text: '{text}'")
            else:
                print(f"   ❌ Node {positive_node_id} not found")
        else:
            print("   ❌ No positive connection found")
    else:
        print("   ❌ No sampler node found")
    
    print("\n2. Connection format analysis:")
    print("   The issue might be in the connection format or traversal logic")
    
    # Test the connection format
    for node_id, node_data in sample_t5_data.items():
        inputs = node_data.get('inputs', {})
        if inputs and any(isinstance(v, list) for v in inputs.values()):
            print(f"   Node {node_id} has connections:")
            for key, value in inputs.items():
                if isinstance(value, list):
                    print(f"     {key}: {value} (connection)")
                else:
                    print(f"     {key}: {value} (direct value)")

if __name__ == "__main__":
    test_simple_traversal()