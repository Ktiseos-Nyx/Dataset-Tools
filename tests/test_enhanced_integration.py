#!/usr/bin/env python3
# ruff: noqa: T201

"""Test the enhanced EXIF integration with the metadata engine."""

import os
import sys
from pathlib import Path

# Add the current directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_enhanced_integration():
    """Test that enhanced EXIF extraction works with the metadata engine."""
    print(  # noqa: T201"🧪 ENHANCED EXIF INTEGRATION TEST")
    print(  # noqa: T201"=" * 33)

    # Test files
    test_files = [
        "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_01803_.jpeg",  # Unicode A1111 FLUX
        "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_08965_.jpeg",  # ComfyUI JSON workflow
    ]

    # Test the context preparation directly
    try:
        from metadata_engine.context_preparation import ContextDataPreparer

        preparer = ContextDataPreparer()

        for test_file in test_files:
            if not os.path.exists(test_file):
                print(  # noqa: T201f"❌ File not found: {Path(test_file).name}")
                continue

            print(  # noqa: T201f"\\n📁 Testing: {Path(test_file).name}")

            try:
                context = preparer.prepare_context(test_file)

                if not context:
                    print(  # noqa: T201"❌ No context data prepared")
                    continue

                print(  # noqa: T201f"✅ Context prepared with {len(context)} keys")

                # Check for UserComment extraction
                user_comment = context.get("raw_user_comment_str")
                if user_comment:
                    print(  # noqa: T201f"✅ UserComment extracted: {len(user_comment)} characters")

                    # Analyze the content
                    if "Steps:" in user_comment and "Sampler:" in user_comment:
                        print(  # noqa: T201"   Type: A1111-style parameters")
                        if "flux" in user_comment.lower():
                            print(  # noqa: T201"   Model type: FLUX detected")
                    elif user_comment.startswith('{"') and '"prompt":' in user_comment:
                        print(  # noqa: T201"   Type: ComfyUI JSON workflow")
                        if "comfyui_workflow_json" in context:
                            print(  # noqa: T201"   ✅ Parsed as structured JSON")
                        else:
                            print(  # noqa: T201"   ⚠️ Not parsed as structured JSON")

                    # Show preview
                    preview = user_comment[:100].replace("\\n", " ")
                    print(  # noqa: T201f"   Preview: {preview}...")

                else:
                    print(  # noqa: T201"❌ No UserComment extracted")

                # Check other important context keys
                important_keys = [
                    "file_format",
                    "file_extension",
                    "pil_info",
                    "exif_dict",
                ]
                for key in important_keys:
                    if key in context:
                        print(  # noqa: T201f"   ✅ {key}: present")
                    else:
                        print(  # noqa: T201f"   ❌ {key}: missing")

            except Exception as e:
                print(  # noqa: T201f"❌ Error processing {Path(test_file).name}: {e}")

    except ImportError as e:
        print(  # noqa: T201f"❌ Import error: {e}")
        print(  # noqa: T201"   Make sure you're running from the correct directory")

    print(  # noqa: T201"\\n🎯 EXPECTED RESULTS:")
    print(  # noqa: T201"   • ComfyUI_01803_.jpeg: Should extract A1111-style FLUX parameters")
    print(  # noqa: T201"   • ComfyUI_08965_.jpeg: Should extract large ComfyUI JSON workflow")
    print(  # noqa: T201"   • Both should now be detectable by appropriate parsers")

    print(  # noqa: T201"\\n📝 NEXT STEPS:")
    print(  # noqa: T201"   1. If UserComment extraction works → Test with full metadata engine")
    print(  # noqa: T201"   2. If parsers still don't match → Debug detection rules")
    print(  # noqa: T201"   3. Monitor logs for 'Enhanced EXIF UserComment extracted' messages")


if __name__ == "__main__":
    test_enhanced_integration()
