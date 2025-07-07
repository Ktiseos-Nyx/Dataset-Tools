#!/usr/bin/env python3

"""
Test ComfyUI extraction methods directly.
"""

import sys
import os
from pathlib import Path
import json

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_comfyui_extraction():
    """Test ComfyUI extraction methods directly."""
    
    print("🔍 TESTING COMFYUI EXTRACTION")
    print("=" * 30)
    
    test_file = "/Users/duskfall/Downloads/Metadata Samples/B4V0V3FKDVZHZZRERKQ31YFR10.jpeg"
    
    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer
        from dataset_tools.metadata_engine.extractors.comfyui_extractors import ComfyUIExtractor
        
        # Prepare context
        preparer = ContextDataPreparer()
        context = preparer.prepare_context(test_file)
        
        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            workflow_data = json.loads(user_comment)
            print(f"✅ Workflow loaded: {len(workflow_data)} nodes")
            
            # Initialize the extractor
            import logging
            logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
            logger = logging.getLogger("test")
            extractor = ComfyUIExtractor(logger)
            
            # Test the sampler finding method
            print(f"\n🔍 TESTING SAMPLER DETECTION:")
            
            sampler_node_types = [
                "KSampler",
                "KSamplerAdvanced", 
                "KSampler_A1111",
                "SamplerCustom",
                "SamplerCustomAdvanced"
            ]
            
            # Look for sampler nodes manually
            found_samplers = []
            for node_id, node_data in workflow_data.items():
                if isinstance(node_data, dict) and "class_type" in node_data:
                    class_type = node_data["class_type"]
                    if class_type in sampler_node_types:
                        found_samplers.append((node_id, class_type))
                        print(f"   ✅ Found sampler: {node_id} ({class_type})")
            
            if not found_samplers:
                print(f"   ❌ No samplers found in workflow")
                return
            
            # Test the text extraction
            print(f"\n🔍 TESTING TEXT EXTRACTION:")
            
            for node_id, class_type in found_samplers:
                print(f"\n   Testing sampler: {node_id} ({class_type})")
                node_data = workflow_data[node_id]
                inputs = node_data.get("inputs", {})
                
                # Check positive and negative inputs
                for input_type in ["positive", "negative"]:
                    if input_type in inputs:
                        connection = inputs[input_type]
                        print(f"      {input_type}: {connection}")
                        
                        if isinstance(connection, list) and len(connection) == 2:
                            connected_node_id, output_slot = connection
                            
                            # Get the connected node
                            if connected_node_id in workflow_data:
                                connected_node = workflow_data[connected_node_id]
                                connected_class_type = connected_node.get("class_type", "Unknown")
                                print(f"         → Connected to: {connected_node_id} ({connected_class_type})")
                                
                                # Check if it's a text encoder
                                text_encoder_types = [
                                    "CLIPTextEncode",
                                    "CLIPTextEncodeSDXL", 
                                    "smZ CLIPTextEncode"
                                ]
                                
                                if connected_class_type in text_encoder_types:
                                    connected_inputs = connected_node.get("inputs", {})
                                    text_input = connected_inputs.get("text", "Not found")
                                    print(f"         ✅ Text encoder found!")
                                    print(f"         Text ({len(str(text_input))} chars): {str(text_input)[:100]}...")
                                else:
                                    print(f"         ❌ Not a recognized text encoder")
                            else:
                                print(f"         ❌ Connected node {connected_node_id} not found")
                        else:
                            print(f"         ❌ Invalid connection format: {connection}")
                    else:
                        print(f"      {input_type}: Not found")
            
            # Test the actual extraction method
            print(f"\n🔍 TESTING ACTUAL EXTRACTION METHOD:")
            
            try:
                # Get available methods
                methods = extractor.get_methods()
                print(f"   Available methods: {list(methods.keys())[:5]}...")
                
                # Test the main extraction method
                method = methods.get("comfy_find_text_from_main_sampler_input")
                if method:
                    print(f"   ✅ Method found: {method}")
                    
                    # Create a method definition like the parser would
                    method_def = {
                        "sampler_node_types": sampler_node_types,
                        "positive_input_name": "positive",
                        "text_input_name_in_encoder": "text",
                        "text_encoder_node_types": [
                            "CLIPTextEncode",
                            "CLIPTextEncodeSDXL",
                            "BNK_CLIPTextEncodeAdvanced",
                            "PixArtT5TextEncode",
                            "T5TextEncode",
                            "CLIPTextEncodeSDXLRefiner",
                            "smZ CLIPTextEncode"
                        ],
                        "fallback": "Could not extract prompt"
                    }
                    
                    print(f"   Testing with method_def: {list(method_def.keys())}")
                    
                    # Debug the data structure
                    print(f"   Data structure check:")
                    print(f"     - isinstance(workflow_data, dict): {isinstance(workflow_data, dict)}")
                    print(f"     - 'nodes' in workflow_data: {'nodes' in workflow_data}")
                    print(f"     - all values are dict: {all(isinstance(v, dict) for v in workflow_data.values())}")
                    print(f"     - sample keys: {list(workflow_data.keys())[:5]}")
                    
                    # Find non-dict values
                    non_dict_values = {k: type(v).__name__ for k, v in workflow_data.items() if not isinstance(v, dict)}
                    print(f"     - non-dict values: {non_dict_values}")
                    
                    # Filter to only dict values (node data)
                    filtered_data = {k: v for k, v in workflow_data.items() if isinstance(v, dict)}
                    print(f"     - filtered data has {len(filtered_data)} nodes")
                    
                    # Call the method (it expects data, method_def, context, fields)
                    result = method(filtered_data, method_def, {}, {})
                    print(f"   ✅ Extraction result: '{result}'")
                else:
                    print(f"   ❌ Method not found")
                
            except Exception as e:
                print(f"   ❌ Extraction failed: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comfyui_extraction()