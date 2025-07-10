#!/usr/bin/env python3
# ruff: noqa: T201

"""Test with a real file that has the mojibake issue."""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_live_mojibake():
    """Test with a real file to see the mojibake issue."""
    print(  # noqa: T201"🔍 LIVE MOJIBAKE TEST")
    print(  # noqa: T201"=" * 20)

    # We need to find a file that has this issue
    # Let's check some common CivitAI ComfyUI files
    test_files = [
        "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_08965_.jpeg",
        "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_01803_.jpeg",
    ]

    # Find files that actually exist
    existing_files = [f for f in test_files if Path(f).exists()]

    if not existing_files:
        print(  # noqa: T201"❌ No test files found")
        return

    for test_file in existing_files:
        print(  # noqa: T201f"\n📁 Testing: {Path(test_file).name}")

        try:
            import logging

            from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

            # Enable debug logging to see what's happening
            logging.basicConfig(
                level=logging.DEBUG, format="%(levelname)s: %(message)s"
            )

            preparer = ContextDataPreparer()
            context = preparer.prepare_context(test_file)

            user_comment = context.get("raw_user_comment_str")
            if user_comment:
                print(  # noqa: T201f"✅ UserComment extracted: {len(user_comment)} chars")

                # Check if it looks like mojibake
                has_chinese_chars = any(
                    "\u4e00" <= char <= "\u9fff" for char in user_comment[:100]
                )
                starts_with_charset = user_comment.startswith("charset=Unicode")

                if has_chinese_chars or starts_with_charset:
                    print(  # noqa: T201"⚠️ POTENTIAL MOJIBAKE DETECTED!")
                    print(  # noqa: T201f"   Starts with charset=Unicode: {starts_with_charset}")
                    print(  # noqa: T201f"   Contains Chinese chars: {has_chinese_chars}")
                    print(  # noqa: T201f"   Preview: {user_comment[:100]}...")

                    # This suggests our Unicode decoding isn't working
                    print(  # noqa: T201"\n🔧 RAW ANALYSIS:")

                    # Let's check the raw bytes from PIL directly
                    from PIL import Image

                    with Image.open(test_file) as img:
                        exif_data = img.getexif()
                        if exif_data:
                            raw_comment = exif_data.get(37510)
                            print(  # noqa: T201f"   PIL getexif type: {type(raw_comment)}")
                            if isinstance(raw_comment, bytes):
                                print(  # noqa: T201f"   Raw bytes: {raw_comment[:50]}...")

                                # Try our decoder on the raw bytes
                                decoded = preparer._decode_usercomment_bytes_robust(
                                    raw_comment
                                )
                                if decoded:
                                    print(  # noqa: T201f"   Manual decode: {decoded[:100]}...")
                                    if decoded != user_comment:
                                        print(  # noqa: T201
                                            "   ❌ MISMATCH! Our decoder works but context prep doesn't use it"
                                        )

                            elif isinstance(raw_comment, str):
                                print(  # noqa: T201f"   PIL already decoded: {raw_comment[:100]}...")
                                if (
                                    "charset=Unicode" in raw_comment
                                    and has_chinese_chars
                                ):
                                    print(  # noqa: T201
                                        "   ❌ PIL decoded incorrectly, creating mojibake"
                                    )
                else:
                    print(  # noqa: T201"✅ No mojibake detected - looks clean")
                    if user_comment.startswith('{"') and '"class_type"' in user_comment:
                        print(  # noqa: T201"   Looks like valid ComfyUI JSON")
            else:
                print(  # noqa: T201"❌ No UserComment extracted")

        except Exception as e:
            print(  # noqa: T201f"❌ Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    test_live_mojibake()
