#!/usr/bin/env python3

"""
Debug script to examine JPEG metadata structure.
"""

import os
import sys
from PIL import Image
from PIL.ExifTags import TAGS

def debug_jpeg_metadata(filepath):
    """Debug what metadata is actually in the JPEG file."""
    
    print("🔍 JPEG METADATA DIAGNOSTIC")
    print("=" * 28)
    print(f"File: {os.path.basename(filepath)}")
    
    if not os.path.exists(filepath):
        print("❌ File not found!")
        return
    
    print(f"File size: {os.path.getsize(filepath):,} bytes")
    
    try:
        # Open with PIL
        with Image.open(filepath) as img:
            print(f"Image mode: {img.mode}")
            print(f"Image size: {img.size}")
            print(f"Image format: {img.format}")
            
            # Check PIL info
            print(f"\\nPIL info keys: {list(img.info.keys())}")
            
            # Check each info key
            for key, value in img.info.items():
                if isinstance(value, bytes):
                    try:
                        value_str = value.decode('utf-8', errors='ignore')[:100]
                        print(f"  {key}: (bytes) {value_str}...")
                    except:
                        print(f"  {key}: (bytes) <{len(value)} bytes>")
                else:
                    value_str = str(value)[:100]
                    print(f"  {key}: {value_str}...")
            
            # Check EXIF data
            exif_data = img.getexif()
            if exif_data:
                print(f"\\nEXIF tags found: {len(exif_data)} entries")
                
                # Look for key EXIF tags
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, f"Tag_{tag_id}")
                    
                    if tag_name in ['UserComment', 'ImageDescription', 'Software', 'Make', 'Model', 'Artist']:
                        if isinstance(value, bytes):
                            try:
                                value_str = value.decode('utf-8', errors='ignore')[:100]
                                print(f"  {tag_name}: (bytes) {value_str}...")
                            except:
                                print(f"  {tag_name}: (bytes) <{len(value)} bytes>")
                        else:
                            value_str = str(value)[:100]
                            print(f"  {tag_name}: {value_str}...")
                
                # Check for UserComment specifically
                user_comment = exif_data.get(37510)  # UserComment tag
                if user_comment:
                    print(f"\\n🎯 UserComment found:")
                    if isinstance(user_comment, bytes):
                        print(f"   Raw bytes length: {len(user_comment)}")
                        try:
                            decoded = user_comment.decode('utf-8', errors='ignore')
                            print(f"   UTF-8 decode: {decoded[:200]}...")
                        except:
                            print("   UTF-8 decode failed")
                        
                        # Check for charset prefix
                        if user_comment.startswith(b'charset='):
                            print("   Has charset prefix")
                    else:
                        print(f"   String: {user_comment}")
                else:
                    print("\\n❌ No UserComment tag found")
            else:
                print("\\n❌ No EXIF data found")
                
    except Exception as e:
        print(f"❌ Error reading image: {e}")
    
    print("\\n📋 DIAGNOSTIC SUMMARY:")
    print("   If no UserComment: File likely has no AI metadata")
    print("   If UserComment exists but empty: Metadata stripped/corrupted")
    print("   If UserComment has data: Check encoding/format issues")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug_jpeg_metadata(sys.argv[1])
    else:
        print("Usage: python debug_jpeg_metadata.py <jpeg_file>")
        print("Example: python debug_jpeg_metadata.py '/path/to/ComfyUI_01803_.jpeg'")