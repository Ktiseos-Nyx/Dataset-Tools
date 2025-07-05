#!/usr/bin/env python3

"""Test script to understand Forge version detection logic."""

import re
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from vendored_sdpr.format.forge_format import ForgeFormat

def test_forge_version_detection():
    """Test the Forge version detection logic with various version strings."""
    
    print("=== FORGE VERSION DETECTION TEST ===\n")
    
    # Test cases with various version strings
    test_cases = [
        # The specific version string from the user's question
        {
            "name": "User's Forge version",
            "version": "f1.7.0-v1.10.1RC-latest-2190-g8731f1e9",
            "raw_text": "Steps: 20, CFG scale: 7, Seed: 123456, Size: 512x768, Version: f1.7.0-v1.10.1RC-latest-2190-g8731f1e9"
        },
        # Common A1111 versions for comparison
        {
            "name": "A1111 v1.6.0",
            "version": "v1.6.0",
            "raw_text": "Steps: 20, CFG scale: 7, Seed: 123456, Size: 512x768, Version: v1.6.0"
        },
        # More Forge-like versions
        {
            "name": "Forge with 'f' prefix",
            "version": "f1.5.0",
            "raw_text": "Steps: 20, CFG scale: 7, Seed: 123456, Size: 512x768, Version: f1.5.0"
        },
        {
            "name": "Forge with git hash",
            "version": "f1.6.0-dev-abc123",
            "raw_text": "Steps: 20, CFG scale: 7, Seed: 123456, Size: 512x768, Version: f1.6.0-dev-abc123"
        },
        # Test with Schedule type: Automatic
        {
            "name": "Forge with Schedule type: Automatic",
            "version": "v1.5.0",
            "raw_text": "Steps: 20, CFG scale: 7, Seed: 123456, Size: 512x768, Version: v1.5.0, Schedule type: Automatic"
        },
        # Test with Hires Module
        {
            "name": "Forge with Hires Module",
            "version": "v1.5.0",
            "raw_text": "Steps: 20, CFG scale: 7, Seed: 123456, Size: 512x768, Version: v1.5.0, Hires Module 1: something"
        },
        # Edge cases
        {
            "name": "Version with f in middle",
            "version": "v1.5.0-forge-abc",
            "raw_text": "Steps: 20, CFG scale: 7, Seed: 123456, Size: 512x768, Version: v1.5.0-forge-abc"
        },
        {
            "name": "Case sensitivity test",
            "version": "F1.5.0",
            "raw_text": "Steps: 20, CFG scale: 7, Seed: 123456, Size: 512x768, Version: F1.5.0"
        }
    ]
    
    print("FORGE DETECTION REGEX PATTERNS:")
    print("--------------------------------")
    print("1. Version regex: r\"Version:\\s*f\" (case insensitive)")
    print("2. Schedule type: \"Schedule type: Automatic\" (exact match)")
    print("3. Hires Module: \"Hires Module 1:\" (exact match)")
    print()
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        print(f"Version: {test_case['version']}")
        print(f"Raw text: {test_case['raw_text']}")
        
        # Test the actual regex patterns used in ForgeFormat
        raw_text = test_case["raw_text"]
        
        # Pattern 1: Version starts with 'f'
        forge_version_match = re.search(r"Version:\s*f", raw_text, re.IGNORECASE)
        has_auto_scheduler = "Schedule type: Automatic" in raw_text
        has_hires_module = "Hires Module 1:" in raw_text
        
        is_forge = forge_version_match or has_auto_scheduler or has_hires_module
        
        print(f"  → Version regex match: {bool(forge_version_match)}")
        print(f"  → Has auto scheduler: {has_auto_scheduler}")
        print(f"  → Has hires module: {has_hires_module}")
        print(f"  → Would be detected as Forge: {is_forge}")
        
        # Try to create a ForgeFormat instance to see if it works
        try:
            forge_parser = ForgeFormat(raw=raw_text)
            forge_parser.parse()
            print(f"  → Parser status: {forge_parser.status}")
            print(f"  → Parser tool: {forge_parser.tool}")
        except Exception as e:
            print(f"  → Parser error: {e}")
        
        print("-" * 60)
    
    print("\nANALYSIS:")
    print("--------")
    print("The Forge detection logic looks for:")
    print("1. Version field starting with 'f' (case insensitive)")
    print("2. 'Schedule type: Automatic' marker")
    print("3. 'Hires Module 1:' marker")
    print()
    print("Your version string 'f1.7.0-v1.10.1RC-latest-2190-g8731f1e9' SHOULD match")
    print("the first pattern since it starts with 'f'.")
    print()
    print("If it's not being detected, the issue might be:")
    print("1. ForgeFormat is not in the parser class lists in ImageDataReader")
    print("2. The raw text extraction is not working properly")
    print("3. There's an issue with the dispatcher integration")

if __name__ == "__main__":
    test_forge_version_detection()