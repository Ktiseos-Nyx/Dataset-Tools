#!/usr/bin/env python3
# ruff: noqa: T201

"""Test script to verify Forge WebUI detection is working with our enhanced MetadataEngine."""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_tools.metadata_engine import get_metadata_engine


def test_forge_detection():
    """Test that our Forge parser correctly identifies Forge WebUI images."""
    print(  # noqa: T201"🔧 TESTING FORGE WEBUI DETECTION")
    print(  # noqa: T201"=" * 50)

    # Sample Forge metadata (like the one you showed)
    forge_metadata = """score_9, score_8_up,score_7_up, source_anime, rating_safe, 1girl, solo, <lora:EPhsrKafka:1> ,EPhsrKafka, purple hair, long hair, low ponytail, pink eyes, hair between eyes, eyewear on head, sunglasses, 

 hoop earrings, pink lips, oversized t-shirt, baggy pants, outstretched arms, blush smiling, sitting on couch, in living room, looking at viewer, pov, incoming hug,
Negative prompt: 3d, monochrome, simple background,
Steps: 24, Sampler: Euler a, CFG scale: 7, Seed: 2340366286, Size: 832x1216, Model hash: 529c72f6c3, Model: mfcgPDXL_v10, VAE hash: 735e4c3a44, VAE: sdxl_vae.safetensors, Denoising strength: 0.33, Clip skip: 2, ADetailer model: Anzhc Face seg 640 v2 y8n.pt, ADetailer confidence: 0.7, ADetailer dilate erode: 4, ADetailer mask blur: 4, ADetailer denoising strength: 0.4, ADetailer inpaint only masked: True, ADetailer inpaint padding: 32, ADetailer version: 24.5.1, Hires upscale: 1.5, Hires steps: 12, Hires upscaler: 4x_fatal_Anime_500000_G, Lora hashes: "EPhsrKafka: dba941975e80", Version: f0.0.17v1.8.0rc-latest-277-g0af28699, Hashes: {"vae": "63aeecb90f", "lora:EPhsrKafka": "5a3385485b", "model": "529c72f6c3"}"""

    # Check what parsers we have available
    parser_definitions_path = Path(__file__).parent / "parser_definitions"
    print(  # noqa: T201f"📂 Parser definitions path: {parser_definitions_path}")

    if not parser_definitions_path.exists():
        print(  # noqa: T201"❌ Parser definitions folder not found!")
        return False

    # List available parsers
    forge_parsers = list(parser_definitions_path.glob("*[Ff]orge*.json"))
    a1111_parsers = list(parser_definitions_path.glob("*a1111*.json"))

    print(  # noqa: T201f"🔧 Found {len(forge_parsers)} Forge parsers:")
    for p in forge_parsers:
        print(  # noqa: T201f"   - {p.name}")

    print(  # noqa: T201f"🤖 Found {len(a1111_parsers)} A1111 parsers:")
    for p in a1111_parsers[:3]:  # Show first 3
        print(  # noqa: T201f"   - {p.name}")
    if len(a1111_parsers) > 3:
        print(  # noqa: T201f"   ... and {len(a1111_parsers) - 3} more")

    try:
        engine = get_metadata_engine(str(parser_definitions_path))
        print(  # noqa: T201"✅ MetadataEngine initialized successfully")

        # Create a fake image with Forge metadata for testing
        from io import BytesIO

        from PIL import Image

        # Create a simple test image
        img = Image.new("RGB", (832, 1216), color=(255, 0, 0))

        # Add the Forge metadata to PIL info
        img.info["parameters"] = forge_metadata

        # Save to BytesIO to test parsing
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        img_bytes.name = "test_forge_image.jpg"

        print(  # noqa: T201"\n🧪 TESTING PARSER DETECTION:")
        print(  # noqa: T201"-" * 30)

        result = engine.get_parser_for_file(img_bytes)

        if result and isinstance(result, dict):
            tool = result.get("tool", "Unknown")
            print(  # noqa: T201"✅ Detection successful!")
            print(  # noqa: T201f"🔧 Detected tool: {tool}")

            # Check if it correctly identifies as Forge
            if "forge" in tool.lower():
                print(  # noqa: T201"🎉 CORRECT! Identified as Forge WebUI")

                # Show some parsed details
                prompt = (
                    result.get("prompt", "")[:100] + "..."
                    if len(result.get("prompt", "")) > 100
                    else result.get("prompt", "")
                )
                print(  # noqa: T201f"📝 Prompt preview: {prompt}")

                params = result.get("parameters", {})
                if params:
                    print(  # noqa: T201"⚙️  Parsed parameters:")
                    for key in ["steps", "sampler", "seed", "model", "forge_version"]:
                        if key in params:
                            print(  # noqa: T201f"   - {key}: {params[key]}")

                return True
            print(  # noqa: T201f"❌ INCORRECT! Should be Forge but detected as: {tool}")
            print(  # noqa: T201"💡 This means A1111 parser caught it before Forge parser")

            # Show what was detected
            if "parameters" in result:
                print(  # noqa: T201
                    f"📊 Still parsed some data: {list(result.get('parameters', {}).keys())}"
                )

            return False
        print(  # noqa: T201"❌ No parser matched the test data")
        print(  # noqa: T201"💡 This suggests the parsers couldn't detect the format")
        return False

    except Exception as e:
        print(  # noqa: T201f"💥 ERROR during test: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_forge_detection()
    print(  # noqa: T201f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)
