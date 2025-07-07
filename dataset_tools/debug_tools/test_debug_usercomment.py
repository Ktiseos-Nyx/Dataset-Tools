#!/usr/bin/env python3

"""Debug UserComment extraction to see what's happening."""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def debug_usercomment():
    """Debug UserComment extraction step by step."""
    print("🔍 DEBUG USERCOMMENT EXTRACTION")
    print("=" * 35)

    test_file = "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_08965_.jpeg"

    if not Path(test_file).exists():
        print("❌ Test file not found")
        return

    print(f"📁 Testing: {Path(test_file).name}")

    try:
        import piexif
        import piexif.helper
        from PIL import Image

        print("\n🔧 STEP 1: Basic PIL EXIF")
        print("-" * 25)

        with Image.open(test_file) as img:
            print(f"Format: {img.format}")
            print(f"Size: {img.size}")
            print(f"Info keys: {list(img.info.keys())}")

            # Check for basic UserComment in info
            if "UserComment" in img.info:
                uc = img.info["UserComment"]
                print(
                    f"PIL info UserComment: {type(uc)} - {len(uc) if isinstance(uc, (str, bytes)) else 'N/A'} chars/bytes"
                )
                if isinstance(uc, str):
                    print(f"Preview: {uc[:100]}...")
                elif isinstance(uc, bytes):
                    print(f"Raw bytes: {uc[:50]}...")

            # Check PIL EXIF
            exif_dict = img.getexif()
            if exif_dict:
                print(f"PIL EXIF tags: {len(exif_dict)} tags found")
                user_comment_raw = exif_dict.get(37510)  # UserComment tag
                if user_comment_raw:
                    print(f"PIL EXIF UserComment (tag 37510): {type(user_comment_raw)} - {len(user_comment_raw)} bytes")
                    print(f"Raw bytes preview: {user_comment_raw[:100]}...")

                    # Try to decode with our robust method
                    print("\n🔧 Trying robust decoding...")
                    from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

                    preparer = ContextDataPreparer()
                    decoded = preparer._decode_usercomment_bytes_robust(user_comment_raw)
                    if decoded:
                        print(f"✅ Robust decoding SUCCESS: {len(decoded)} chars")
                        print(f"Preview: {decoded[:100]}...")

                        # Check if it's JSON
                        if decoded.startswith('{"') and decoded.endswith("}"):
                            print("   Looks like JSON data")
                        else:
                            print("   Not JSON format")
                    else:
                        print("❌ Robust decoding FAILED")
                else:
                    print("No UserComment in PIL EXIF tag 37510")
            else:
                print("No PIL EXIF data found")

        print("\n🔧 STEP 2: piexif Library")
        print("-" * 25)

        with Image.open(test_file) as img:
            exif_bytes = img.info.get("exif")
            if exif_bytes:
                print(f"Raw EXIF bytes: {len(exif_bytes)} bytes")

                try:
                    loaded_exif = piexif.load(exif_bytes)
                    print("✅ piexif.load() successful")

                    # Check for UserComment
                    uc_bytes = loaded_exif.get("Exif", {}).get(piexif.ExifIFD.UserComment)
                    if uc_bytes:
                        print(f"piexif UserComment: {len(uc_bytes)} bytes")
                        print(f"Raw bytes: {uc_bytes[:100]}...")

                        # Try piexif helper
                        try:
                            decoded_piexif = piexif.helper.UserComment.load(uc_bytes)
                            print(f"✅ piexif helper: {len(decoded_piexif)} chars")
                            print(f"Preview: {decoded_piexif[:100]}...")
                        except Exception as e:
                            print(f"❌ piexif helper failed: {e}")

                            # Try our robust decoder
                            from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

                            preparer = ContextDataPreparer()
                            decoded_robust = preparer._decode_usercomment_bytes_robust(uc_bytes)
                            if decoded_robust:
                                print(f"✅ Our robust decoder: {len(decoded_robust)} chars")
                                print(f"Preview: {decoded_robust[:100]}...")
                            else:
                                print("❌ Our robust decoder failed too")
                    else:
                        print("No UserComment in piexif Exif section")

                except Exception as e:
                    print(f"❌ piexif.load() failed: {e}")
            else:
                print("No raw EXIF bytes in PIL info")

        print("\n🔧 STEP 3: Context Preparation")
        print("-" * 30)

        # Test our actual context preparation
        import logging

        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

        # Enable debug logging
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

        preparer = ContextDataPreparer()
        context = preparer.prepare_context(test_file)

        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            print(f"✅ Context preparation SUCCESS: {len(user_comment)} chars")
            print(f"Preview: {user_comment[:100]}...")
        else:
            print("❌ Context preparation FAILED - no UserComment")

    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_usercomment()
