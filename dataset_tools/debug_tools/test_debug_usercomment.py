#!/usr/bin/env python3
# ruff: noqa: T201

"""Debug UserComment extraction to see what's happening."""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def debug_usercomment():
    """Debug UserComment extraction step by step."""
    print(  # noqa: T201"🔍 DEBUG USERCOMMENT EXTRACTION")
    print(  # noqa: T201"=" * 35)

    test_file = "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_08965_.jpeg"

    if not Path(test_file).exists():
        print(  # noqa: T201"❌ Test file not found")
        return

    print(  # noqa: T201f"📁 Testing: {Path(test_file).name}")

    try:
        import piexif
        import piexif.helper
        from PIL import Image

        print(  # noqa: T201"\n🔧 STEP 1: Basic PIL EXIF")
        print(  # noqa: T201"-" * 25)

        with Image.open(test_file) as img:
            print(  # noqa: T201f"Format: {img.format}")
            print(  # noqa: T201f"Size: {img.size}")
            print(  # noqa: T201f"Info keys: {list(img.info.keys())}")

            # Check for basic UserComment in info
            if "UserComment" in img.info:
                uc = img.info["UserComment"]
                print(  # noqa: T201
                    f"PIL info UserComment: {type(uc)} - {len(uc) if isinstance(uc, (str, bytes)) else 'N/A'} chars/bytes"
                )
                if isinstance(uc, str):
                    print(  # noqa: T201f"Preview: {uc[:100]}...")
                elif isinstance(uc, bytes):
                    print(  # noqa: T201f"Raw bytes: {uc[:50]}...")

            # Check PIL EXIF
            exif_dict = img.getexif()
            if exif_dict:
                print(  # noqa: T201f"PIL EXIF tags: {len(exif_dict)} tags found")
                user_comment_raw = exif_dict.get(37510)  # UserComment tag
                if user_comment_raw:
                    print(  # noqa: T201
                        f"PIL EXIF UserComment (tag 37510): {type(user_comment_raw)} - {len(user_comment_raw)} bytes"
                    )
                    print(  # noqa: T201f"Raw bytes preview: {user_comment_raw[:100]}...")

                    # Try to decode with our robust method
                    print(  # noqa: T201"\n🔧 Trying robust decoding...")
                    from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

                    preparer = ContextDataPreparer()
                    decoded = preparer._decode_usercomment_bytes_robust(
                        user_comment_raw
                    )
                    if decoded:
                        print(  # noqa: T201f"✅ Robust decoding SUCCESS: {len(decoded)} chars")
                        print(  # noqa: T201f"Preview: {decoded[:100]}...")

                        # Check if it's JSON
                        if decoded.startswith('{"') and decoded.endswith("}"):
                            print(  # noqa: T201"   Looks like JSON data")
                        else:
                            print(  # noqa: T201"   Not JSON format")
                    else:
                        print(  # noqa: T201"❌ Robust decoding FAILED")
                else:
                    print(  # noqa: T201"No UserComment in PIL EXIF tag 37510")
            else:
                print(  # noqa: T201"No PIL EXIF data found")

        print(  # noqa: T201"\n🔧 STEP 2: piexif Library")
        print(  # noqa: T201"-" * 25)

        with Image.open(test_file) as img:
            exif_bytes = img.info.get("exif")
            if exif_bytes:
                print(  # noqa: T201f"Raw EXIF bytes: {len(exif_bytes)} bytes")

                try:
                    loaded_exif = piexif.load(exif_bytes)
                    print(  # noqa: T201"✅ piexif.load() successful")

                    # Check for UserComment
                    uc_bytes = loaded_exif.get("Exif", {}).get(
                        piexif.ExifIFD.UserComment
                    )
                    if uc_bytes:
                        print(  # noqa: T201f"piexif UserComment: {len(uc_bytes)} bytes")
                        print(  # noqa: T201f"Raw bytes: {uc_bytes[:100]}...")

                        # Try piexif helper
                        try:
                            decoded_piexif = piexif.helper.UserComment.load(uc_bytes)
                            print(  # noqa: T201f"✅ piexif helper: {len(decoded_piexif)} chars")
                            print(  # noqa: T201f"Preview: {decoded_piexif[:100]}...")
                        except Exception as e:
                            print(  # noqa: T201f"❌ piexif helper failed: {e}")

                            # Try our robust decoder
                            from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

                            preparer = ContextDataPreparer()
                            decoded_robust = preparer._decode_usercomment_bytes_robust(
                                uc_bytes
                            )
                            if decoded_robust:
                                print(  # noqa: T201
                                    f"✅ Our robust decoder: {len(decoded_robust)} chars"
                                )
                                print(  # noqa: T201f"Preview: {decoded_robust[:100]}...")
                            else:
                                print(  # noqa: T201"❌ Our robust decoder failed too")
                    else:
                        print(  # noqa: T201"No UserComment in piexif Exif section")

                except Exception as e:
                    print(  # noqa: T201f"❌ piexif.load() failed: {e}")
            else:
                print(  # noqa: T201"No raw EXIF bytes in PIL info")

        print(  # noqa: T201"\n🔧 STEP 3: Context Preparation")
        print(  # noqa: T201"-" * 30)

        # Test our actual context preparation
        import logging

        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

        # Enable debug logging
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

        preparer = ContextDataPreparer()
        context = preparer.prepare_context(test_file)

        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            print(  # noqa: T201f"✅ Context preparation SUCCESS: {len(user_comment)} chars")
            print(  # noqa: T201f"Preview: {user_comment[:100]}...")
        else:
            print(  # noqa: T201"❌ Context preparation FAILED - no UserComment")

    except Exception as e:
        print(  # noqa: T201f"❌ Debug error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_usercomment()
