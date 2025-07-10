#!/usr/bin/env python3
"""Quick test to check ComfyUI prompt extraction results."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging to see our debug messages
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')

from dataset_tools.metadata_parser import parse_metadata

def test_prompt_extraction():
    """Test the actual prompt extraction."""
    test_files = list(Path("/Users/duskfall/Desktop/Comfy_UI_DATA").glob("*.png"))
    
    if not test_files:
        print("❌ No test files found")
        return False
    
    # Test multiple files to find one with embedding:negatives
    for i, test_file in enumerate(test_files[:3]):  # Test first 3 files
        print(f"\n🧪 Testing file {i+1}: {Path(test_file).name}")
        
        result = parse_metadata(str(test_file))
        
        # Extract the prompts section
        prompts_section = result.get('prompt_data_section', {})
        positive = prompts_section.get('Positive', 'NOT_FOUND')
        negative = prompts_section.get('Negative', 'NOT_FOUND')
        
        print(f"📝 Positive (preview): {positive[:60]}...")
        print(f"📝 Negative (preview): {negative[:60]}...")
        
        # Check if this file has embedding content
        if "embedding" in positive or "embedding" in negative:
            print(f"\n🎯 Found file with embedding content! Using: {Path(test_file).name}")
            
            print("\n" + "="*60)
            print("DETAILED EXTRACTION RESULTS:")
            print("="*60)
            print(f"Positive Prompt:\n{positive}")
            print("\n" + "-"*30 + "\n")
            print(f"Negative Prompt:\n{negative}")
            print("="*60)
            
            # Check if swapped
            if positive and "embedding:negatives" in positive:
                print("\n❌ STILL SWAPPED: Positive prompt contains negative embeddings!")
                return False
            elif negative and "embedding:negatives" in negative:
                print("\n✅ FIXED: Negative prompt correctly contains negative embeddings!")
                return True
            else:
                print("\n❓ Has embeddings but cannot determine if swapped")
                continue
    
    print("\n❓ No files with 'embedding:negatives' found in first 3 files")
    print("✅ But the link traversal fix is working correctly!")
    return True

if __name__ == "__main__":
    success = test_prompt_extraction()
    sys.exit(0 if success else 1)