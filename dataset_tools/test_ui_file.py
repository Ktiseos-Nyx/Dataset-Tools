#!/usr/bin/env python3

"""
Test the specific file that's causing UI mojibake.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ui_file():
    """Test the specific file from the UI that's causing issues."""
    
    print("🔍 UI FILE MOJIBAKE TEST")
    print("=" * 25)
    
    test_file = "/Users/duskfall/Downloads/Metadata Samples/B4V0V3FKDVZHZZRERKQ31YFR10.jpeg"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {Path(test_file).name}")
        return
    
    print(f"📁 Testing: {Path(test_file).name}")
    
    # Step 1: Test context preparation
    print("\n1️⃣ CONTEXT PREPARATION")
    print("-" * 22)
    
    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer
        import logging
        
        # Enable debug logging
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
        
        preparer = ContextDataPreparer()
        context = preparer.prepare_context(test_file)
        
        if not context:
            print("❌ Context preparation failed")
            return
        
        print(f"✅ Context prepared with {len(context)} keys")
        
        # Check UserComment extraction
        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            print(f"✅ UserComment extracted: {len(user_comment)} characters")
            
            # Check for mojibake patterns
            has_chinese_chars = any('\u4e00' <= char <= '\u9fff' for char in user_comment[:100])
            starts_with_charset = user_comment.startswith("charset=Unicode")
            
            if has_chinese_chars or starts_with_charset:
                print("⚠️ MOJIBAKE DETECTED!")
                print(f"   Preview: {user_comment[:100]}...")
            else:
                print("✅ No mojibake - looks clean")
                if user_comment.startswith('{"'):
                    print("   Format: JSON")
                elif "Steps:" in user_comment:
                    print("   Format: A1111 parameters")
                else:
                    print(f"   Preview: {user_comment[:100]}...")
        else:
            print("❌ No UserComment extracted")
            
    except Exception as e:
        print(f"❌ Context preparation error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Test MetadataEngine detection
    print("\n2️⃣ METADATA ENGINE")
    print("-" * 17)
    
    try:
        from dataset_tools.metadata_engine import MetadataEngine
        
        parser_definitions_path = os.path.join(os.path.dirname(__file__), "parser_definitions")
        engine = MetadataEngine(parser_definitions_path)
        
        print("🔍 Running MetadataEngine...")
        result = engine.get_parser_for_file(test_file)
        
        if result:
            print(f"✅ SUCCESS: {type(result)}")
            if isinstance(result, dict):
                tool = result.get("tool", "Unknown")
                print(f"   Tool: {tool}")
            else:
                print(f"   Parser instance: {result}")
        else:
            print("❌ FAILED: MetadataEngine returned None")
            print("   This is why the UI falls back to vendored parser")
            
    except Exception as e:
        print(f"❌ MetadataEngine error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 3: Test raw EXIF to see what pyexiv2 would see
    print("\n3️⃣ RAW EXIF (pyexiv2 perspective)")
    print("-" * 35)
    
    try:
        from PIL import Image
        
        with Image.open(test_file) as img:
            exif_data = img.getexif()
            if exif_data:
                user_comment_raw = exif_data.get(37510)
                if user_comment_raw:
                    print(f"PIL getexif type: {type(user_comment_raw)}")
                    
                    if isinstance(user_comment_raw, str):
                        print(f"PIL decoded string: {len(user_comment_raw)} chars")
                        
                        # Check if PIL's decoding created mojibake
                        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in user_comment_raw[:100])
                        if has_chinese or "charset=Unicode" in user_comment_raw:
                            print("❌ PIL created mojibake during decoding")
                            print(f"   Preview: {user_comment_raw[:100]}...")
                            print("   This is what pyexiv2 in the UI sees!")
                        else:
                            print("✅ PIL decoded cleanly")
                            
                    elif isinstance(user_comment_raw, bytes):
                        print(f"PIL raw bytes: {len(user_comment_raw)} bytes")
                        print(f"Raw bytes: {user_comment_raw[:50]}...")
                        
                        # Try our robust decoder
                        decoded = preparer._decode_usercomment_bytes_robust(user_comment_raw)
                        if decoded:
                            print(f"✅ Our decoder: {len(decoded)} chars")
                            print(f"Preview: {decoded[:100]}...")
                else:
                    print("No UserComment in PIL EXIF")
            else:
                print("No EXIF data found")
                
    except Exception as e:
        print(f"❌ Raw EXIF error: {e}")
    
    print("\n🎯 DIAGNOSIS:")
    print("If MetadataEngine returns None, the UI falls back to pyexiv2")
    print("pyexiv2 doesn't have our Unicode handling, so it shows mojibake")
    print("We need to fix why MetadataEngine isn't detecting this file")

if __name__ == "__main__":
    test_ui_file()