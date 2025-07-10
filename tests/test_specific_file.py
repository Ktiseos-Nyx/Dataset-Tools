#!/usr/bin/env python3
"""Test the specific file that might have the prompt issue."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging to see our debug messages  
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')

from dataset_tools.metadata_parser import parse_metadata

def test_specific_file():
    """Test the ComfyUI_00017_.png file specifically."""
    test_file = "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_00017_.png"
    
    if not Path(test_file).exists():
        print(f"❌ File not found: {test_file}")
        return False
    
    print(f"🧪 Testing: {Path(test_file).name}")
    
    result = parse_metadata(test_file)
    
    prompts_section = result.get('prompt_data_section', {})
    positive = prompts_section.get('Positive', 'NOT_FOUND')
    negative = prompts_section.get('Negative', 'NOT_FOUND')
    
    print("\n" + "="*80)
    print("DETAILED EXTRACTION RESULTS:")
    print("="*80)
    print(f"Positive Prompt:\n{positive}")
    print("\n" + "-"*40 + "\n")
    print(f"Negative Prompt:\n{negative}")
    print("="*80)
    
    # Check if they're identical
    if positive == negative:
        print("\n❌ BUG CONFIRMED: Prompts are identical!")
        return False
    
    # Check if negative content is in positive
    negative_indicators = ["worst quality", "bad quality", "lowres", "bad anatomy"]
    positive_has_negative = any(indicator in positive.lower() for indicator in negative_indicators)
    negative_has_negative = any(indicator in negative.lower() for indicator in negative_indicators)
    
    if positive_has_negative and not negative_has_negative:
        print("\n❌ BUG CONFIRMED: Positive prompt contains negative quality terms!")
        return False
    elif negative_has_negative and not positive_has_negative:
        print("\n✅ CORRECT: Negative prompt contains negative quality terms!")
        return True
    else:
        print("\n❓ Unclear: Cannot determine if prompts are swapped")
        return True

if __name__ == "__main__":
    success = test_specific_file()
    sys.exit(0 if success else 1)