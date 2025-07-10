#!/usr/bin/env python3
"""Find the file with 'woman' prompt."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging to see our debug messages  
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')

from dataset_tools.metadata_parser import parse_metadata

def find_woman_prompt():
    """Find files with 'woman' in the raw workflow."""
    test_files = list(Path("/Users/duskfall/Desktop/Comfy_UI_DATA").glob("*.png"))
    
    for test_file in test_files:
        try:
            result = parse_metadata(str(test_file))
            
            # Check if raw data contains 'woman'
            raw_data = result.get('raw_tool_specific_data_section', {})
            if isinstance(raw_data, dict):
                raw_str = str(raw_data)
                if "'woman'" in raw_str or '"woman"' in raw_str:
                    print(f"\n🎯 FOUND 'WOMAN' PROMPT FILE: {test_file.name}")
                    
                    # Check the extracted prompts
                    prompts_section = result.get('prompt_data_section', {})
                    positive = prompts_section.get('Positive', 'NOT_FOUND')
                    negative = prompts_section.get('Negative', 'NOT_FOUND')
                    
                    print(f"✅ Positive: '{positive}'")
                    print(f"✅ Negative: '{negative}'")
                    
                    if positive == 'NOT_FOUND' or positive == '':
                        print("❌ BUG: Positive prompt is missing!")
                        return test_file
                    elif positive.strip().lower() == 'woman':
                        print("✅ SUCCESS: Found the 'woman' prompt correctly!")
                        return test_file
                    else:
                        print(f"❓ Unexpected positive prompt: {positive}")
                        return test_file
                        
        except Exception as e:
            continue
    
    print("❌ No 'woman' prompt file found")
    return None

if __name__ == "__main__":
    result = find_woman_prompt()
    if result:
        print(f"\n🔍 File: {result}")
    else:
        print("\n❌ File not found in test directory")