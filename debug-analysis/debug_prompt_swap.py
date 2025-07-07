#!/usr/bin/env python3

"""
Debug the prompt swapping issue in ComfyUI_00001_.png
"""

import json
import logging
from pathlib import Path
from PIL import Image
from dataset_tools.metadata_engine.extractors.comfyui_extractors import ComfyUIExtractor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_prompt_swap():
    """Debug why positive and negative prompts are being swapped."""
    
    print("🔍 DEBUGGING PROMPT SWAP ISSUE")
    print("=" * 40)
    
    # Load the problematic image
    image_path = "/Users/duskfall/Downloads/Metadata Samples/ComfyUI_00001_.png"
    img = Image.open(image_path)
    
    if 'prompt' not in img.info:
        print("❌ No prompt data found")
        return
    
    prompt_data = json.loads(img.info['prompt'])
    print(f"Workflow has {len(prompt_data)} nodes")
    
    # Examine the text nodes in detail
    print("\n📝 TEXT NODES ANALYSIS:")
    print("-" * 25)
    
    text_nodes = []
    for node_id, node_data in prompt_data.items():
        if isinstance(node_data, dict):
            class_type = node_data.get('class_type', '')
            if 'TextEncode' in class_type or 'CLIP' in class_type:
                inputs = node_data.get('inputs', {})
                if 'text' in inputs:
                    text = inputs['text']
                    meta = node_data.get('_meta', {})
                    title = meta.get('title', 'No title')
                    
                    print(f"Node {node_id} ({class_type}):")
                    print(f"  Title: '{title}'")
                    print(f"  Text: '{text}'")
                    
                    # Analyze text content
                    is_negative_by_content = (
                        "embedding:negatives" in text or
                        "negatives\\" in text or
                        "bad" in text.lower() or
                        "worst" in text.lower() or
                        "low quality" in text.lower()
                    )
                    is_negative_by_title = "negative" in title.lower()
                    
                    print(f"  Negative by content: {is_negative_by_content}")
                    print(f"  Negative by title: {is_negative_by_title}")
                    print()
                    
                    text_nodes.append({
                        'node_id': node_id,
                        'text': text,
                        'title': title,
                        'is_negative_by_content': is_negative_by_content,
                        'is_negative_by_title': is_negative_by_title
                    })
    
    # Test the Universal Parser methods
    print("🧪 TESTING EXTRACTION METHODS:")
    print("-" * 35)
    
    extractor = ComfyUIExtractor(logger)
    
    # Test 1: Extract positive prompt
    print("1. Testing positive prompt extraction:")
    method_def = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced", "KSampler_A1111"],
        "positive_input_name": "positive",
        "text_input_name_in_encoder": "text",
        "text_encoder_node_types": ["CLIPTextEncode", "BNK_CLIPTextEncodeAdvanced"],
        "target_key": "prompt"
    }
    positive_result = extractor._find_text_from_main_sampler_input(prompt_data, method_def, {}, {})
    print(f"   Result: '{positive_result}'")
    
    # Test 2: Extract negative prompt
    print("2. Testing negative prompt extraction:")
    method_def["target_key"] = "negative_prompt"
    negative_result = extractor._find_text_from_main_sampler_input(prompt_data, method_def, {}, {})
    print(f"   Result: '{negative_result}'")
    
    # Test 3: Check sampler connections
    print("\n3. Checking sampler connections:")
    for node_id, node_data in prompt_data.items():
        if isinstance(node_data, dict):
            class_type = node_data.get('class_type', '')
            if 'KSampler' in class_type:
                inputs = node_data.get('inputs', {})
                print(f"   Sampler {node_id} ({class_type}):")
                positive_conn = inputs.get('positive')
                negative_conn = inputs.get('negative')
                print(f"     Positive connected to: {positive_conn}")
                print(f"     Negative connected to: {negative_conn}")
                
                # Check what these connections point to
                if positive_conn and isinstance(positive_conn, list):
                    pos_node_id = str(positive_conn[0])
                    pos_node = prompt_data.get(pos_node_id, {})
                    pos_inputs = pos_node.get('inputs', {})
                    pos_text = pos_inputs.get('text', 'No text')
                    print(f"     Positive text: '{pos_text[:50]}...'")
                
                if negative_conn and isinstance(negative_conn, list):
                    neg_node_id = str(negative_conn[0])
                    neg_node = prompt_data.get(neg_node_id, {})
                    neg_inputs = neg_node.get('inputs', {})
                    neg_text = neg_inputs.get('text', 'No text')
                    print(f"     Negative text: '{neg_text[:50]}...'")

if __name__ == "__main__":
    debug_prompt_swap()