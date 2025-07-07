#!/usr/bin/env python3

"""
Debug which parsers are being tried for JPEG files.
"""

import json
import os
from pathlib import Path

def debug_parser_matching():
    """Debug which parsers target JPEG files."""
    
    print("🔍 PARSER MATCHING DIAGNOSTIC")
    print("=" * 29)
    
    parser_dir = Path(__file__).parent / "parser_definitions"
    
    jpeg_parsers = []
    
    # Check all parser definitions
    for parser_file in parser_dir.glob("*.json"):
        try:
            with open(parser_file, 'r') as f:
                parser_def = json.load(f)
            
            target_types = parser_def.get("target_file_types", [])
            if any(t.upper() in ["JPEG", "JPG"] for t in target_types):
                jpeg_parsers.append({
                    "name": parser_def.get("parser_name", parser_file.name),
                    "priority": parser_def.get("priority", 0),
                    "file_types": target_types,
                    "file": parser_file.name
                })
                
        except Exception as e:
            print(f"❌ Error reading {parser_file}: {e}")
    
    # Sort by priority
    jpeg_parsers.sort(key=lambda x: x["priority"], reverse=True)
    
    print(f"\\n📋 PARSERS TARGETING JPEG FILES ({len(jpeg_parsers)} found):")
    print("   (Ordered by priority - highest first)")
    
    for i, parser in enumerate(jpeg_parsers, 1):
        print(f"\\n   {i}. {parser['name']}")
        print(f"      Priority: {parser['priority']}")
        print(f"      File types: {parser['file_types']}")
        print(f"      Definition: {parser['file']}")
    
    print("\\n🎯 DEBUGGING STEPS:")
    print("   1. Check if ComfyUI_01803_.jpeg has any EXIF UserComment data")
    print("   2. Verify each parser's detection rules in order of priority")
    print("   3. Most likely: File has no AI metadata (which is normal)")
    
    print("\\n📝 COMMON JPEG METADATA LOCATIONS:")
    print("   • EXIF UserComment (A1111, ComfyUI JPEG)")
    print("   • EXIF ImageDescription (some tools)")
    print("   • EXIF Software tag (tool identification)")
    print("   • XMP data (Adobe tools)")
    print("   • APP segments (custom metadata)")

if __name__ == "__main__":
    debug_parser_matching()