#!/usr/bin/env python3
"""Check additional TensorArt samples for different workflow patterns."""

import os
import sys
from pathlib import Path

# Add the dataset tools to the path
sys.path.insert(0, str(Path(__file__).parent))

from dataset_tools.metadata_parser import parse_metadata

def check_additional_samples():
    """Check samples that weren't processed in the first batch."""
    
    tensorart_dir = "/Users/duskfall/Downloads/TensorArt"
    
    # Get all PNG files
    all_files = [f for f in os.listdir(tensorart_dir) 
                 if f.lower().endswith('.png') and not f.startswith('.')]
    
    # Files we haven't analyzed yet
    already_analyzed = [
        "883289781298057046.png",
        "884233797929799233.png", 
        "a738b908397b4f0f80af4c784a09407bd6e221b8c2c8a9ed93a55985c987ee33.png",
        "hC9L2mOQgeJYH5AcTiObj.png",
        "l9kz8EISxlHzDI9JR1cqM.png",
        "3MHSJskeIoKo6NY_7CmgT.png",
        "874162108210635487.png",
        "pK8PXn5K6ohMKfzZk2kpo.png"
    ]
    
    new_files = [f for f in all_files if f not in already_analyzed]
    
    print(f"Found {len(new_files)} additional files to check:")
    for f in new_files:
        print(f"  - {f}")
    
    print("\n=== CHECKING ADDITIONAL SAMPLES ===")
    
    for filename in new_files[:5]:  # Check first 5 additional files
        file_path = os.path.join(tensorart_dir, filename)
        print(f"\n--- {filename} ---")
        
        try:
            parsed_metadata = parse_metadata(file_path)
            
            # Check if it has workflow data
            raw_content = parsed_metadata.get("raw_tool_specific_data_section", {}).get("raw_content", "")
            
            if raw_content:
                print("✓ Has ComfyUI workflow metadata")
                
                # Quick check for EMS patterns
                if "EMS-" in raw_content and "-EMS" in raw_content:
                    print("✓ Contains EMS patterns")
                    
                    # Extract EMS patterns
                    import re
                    ems_models = re.findall(r'EMS-\d+-EMS\.safetensors', raw_content)
                    ems_loras = re.findall(r'EMS-\d+(?:-FP8)?-EMS\.safetensors', raw_content)
                    
                    if ems_models:
                        print(f"  EMS Models: {ems_models}")
                    if ems_loras:
                        print(f"  EMS LoRAs: {ems_loras}")
                else:
                    print("✗ No EMS patterns found")
                    
                # Check for TensorArt job IDs
                if "SaveImage" in raw_content:
                    import re
                    job_ids = re.findall(r'"filename_prefix":\s*["\'](\d{15,})', raw_content)
                    if job_ids:
                        print(f"  TensorArt Job IDs: {job_ids}")
                
                # Check for common TensorArt node types
                tensorart_nodes = [
                    "ECHOCheckpointLoaderSimple",
                    "BNK_CLIPTextEncodeAdvanced", 
                    "LoraTagLoader",
                    "SetSubseeds",
                    "KSampler_A1111"
                ]
                
                found_nodes = [node for node in tensorart_nodes if node in raw_content]
                if found_nodes:
                    print(f"  TensorArt nodes: {found_nodes}")
                else:
                    print("  Using standard ComfyUI nodes")
                    
            else:
                print("✗ No ComfyUI workflow metadata found")
                
            # Check basic metadata
            if "prompt_data_section" in parsed_metadata:
                positive = parsed_metadata["prompt_data_section"].get("Positive", "")
                if positive:
                    print(f"  Has prompt: {positive[:50]}...")
                    
        except Exception as e:
            print(f"✗ Error: {e}")

if __name__ == "__main__":
    check_additional_samples()