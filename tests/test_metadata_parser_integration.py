#!/usr/bin/env python3
# ruff: noqa: T201

"""Test script to verify our MetadataEngine integration in metadata_parser.py is working."""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_tools.metadata_parser import parse_metadata


def test_metadata_parser_integration():
    """Test that our enhanced MetadataEngine integration is being called."""
    print(  # noqa: T201"🔧 TESTING METADATA_PARSER INTEGRATION")
    print(  # noqa: T201"=" * 50)

    # Create a test image with Forge metadata
    forge_metadata = """score_9, score_8_up,score_7_up, source_anime, rating_safe, 1girl, solo, <lora:EPhsrKafka:1> ,EPhsrKafka, purple hair, long hair, low ponytail, pink eyes, hair between eyes, eyewear on head, sunglasses, 

 hoop earrings, pink lips, oversized t-shirt, baggy pants, outstretched arms, blush smiling, sitting on couch, in living room, looking at viewer, pov, incoming hug,
Negative prompt: 3d, monochrome, simple background,
Steps: 24, Sampler: Euler a, CFG scale: 7, Seed: 2340366286, Size: 832x1216, Model hash: 529c72f6c3, Model: mfcgPDXL_v10, VAE hash: 735e4c3a44, VAE: sdxl_vae.safetensors, Denoising strength: 0.33, Clip skip: 2, ADetailer model: Anzhc Face seg 640 v2 y8n.pt, ADetailer confidence: 0.7, ADetailer dilate erode: 4, ADetailer mask blur: 4, ADetailer denoising strength: 0.4, ADetailer inpaint only masked: True, ADetailer inpaint padding: 32, ADetailer version: 24.5.1, Hires upscale: 1.5, Hires steps: 12, Hires upscaler: 4x_fatal_Anime_500000_G, Lora hashes: "EPhsrKafka: dba941975e80", Version: f0.0.17v1.8.0rc-latest-277-g0af28699, Hashes: {"vae": "63aeecb90f", "lora:EPhsrKafka": "5a3385485b", "model": "529c72f6c3"}"""

    try:
        # Create test image file
        import os
        import tempfile

        from PIL import Image

        # Create a temporary image file with metadata
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        img = Image.new("RGB", (832, 1216), color=(255, 0, 0))

        # For JPEG, we need to use EXIF UserComment
        import piexif
        import piexif.helper

        # Create EXIF data with UserComment
        user_comment = piexif.helper.UserComment.dump(
            forge_metadata, encoding="unicode"
        )
        exif_data = {"Exif": {piexif.ExifIFD.UserComment: user_comment}}
        exif_bytes = piexif.dump(exif_data)

        img.save(tmp_path, format="JPEG", exif=exif_bytes)

        print(  # noqa: T201f"📷 Created test image: {tmp_path}")
        print(  # noqa: T201
            "📝 Contains Forge metadata with version: f0.0.17v1.8.0rc-latest-277-g0af28699"
        )
        print(  # noqa: T201)

        print(  # noqa: T201"🚀 CALLING parse_metadata():")
        print(  # noqa: T201"-" * 30)

        result = parse_metadata(tmp_path)

        print(  # noqa: T201"✅ parse_metadata returned successfully")
        print(  # noqa: T201f"📊 Result keys: {list(result.keys())}")
        print(  # noqa: T201)

        # Check what parser was used
        if "_dt_internal_placeholder_" in result:
            placeholder_data = result["_dt_internal_placeholder_"]
            parser_used = placeholder_data.get("Parser Used", "Unknown")
            tool_detected = placeholder_data.get("Tool", "Unknown")

            print(  # noqa: T201f"🔧 Parser Used: {parser_used}")
            print(  # noqa: T201f"🛠️  Tool Detected: {tool_detected}")

            if "Enhanced MetadataEngine" in parser_used:
                print(  # noqa: T201"🎉 SUCCESS! Enhanced MetadataEngine was used")

                if "forge" in tool_detected.lower():
                    print(  # noqa: T201"🎉 DOUBLE SUCCESS! Correctly detected as Forge")
                    return True
                print(  # noqa: T201f"⚠️  Used enhanced engine but detected as: {tool_detected}")
                print(  # noqa: T201"💡 This means our Forge parser needs more work")
                return True  # Still progress
            print(  # noqa: T201f"❌ Still using old system: {parser_used}")
            print(  # noqa: T201"💡 Our integration might not be working")
            return False
        print(  # noqa: T201"❌ No parser information found in result")
        return False

    except Exception as e:
        print(  # noqa: T201f"💥 ERROR during test: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # Clean up
        try:
            if "tmp_path" in locals():
                os.unlink(tmp_path)
        except:
            pass


if __name__ == "__main__":
    success = test_metadata_parser_integration()
    print(  # noqa: T201f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)
