#!/usr/bin/env python3

"""Test the fixed Universal Parser on the advanced ComfyUI image."""

from pathlib import Path

from dataset_tools.metadata_engine import get_metadata_engine


def test_fixed_universal_parser():
    """Test the Universal Parser with the advanced ComfyUI image."""
    print("🧪 TESTING FIXED UNIVERSAL PARSER")
    print("=" * 40)

    # Test with the advanced ComfyUI image
    test_file = "/Users/duskfall/Downloads/Metadata Samples/872676588544625334.png"
    parser_definitions_path = Path(__file__).parent / "parser_definitions"

    try:
        # Create metadata engine
        engine = get_metadata_engine(str(parser_definitions_path))

        # Test parsing
        result = engine.get_parser_for_file(test_file)

        if result and result.get("tool") == "ComfyUI (Universal Parser)":
            print("✅ Universal Parser detected correctly")

            # Check extracted data
            prompt = result.get("prompt", "")
            negative = result.get("negative_prompt", "")
            parameters = result.get("parameters", {})

            print("\n📝 EXTRACTED DATA:")
            print(f"Prompt: {prompt[:100]}...")
            print(f"Negative: {negative}")

            print("\n🔧 PARAMETERS:")
            for key, value in parameters.items():
                print(f"  {key}: {value} ({type(value).__name__})")

            # Validate the critical fixes
            print("\n✅ VALIDATION:")

            # Check sampler name
            sampler = parameters.get("sampler_name")
            if sampler == "euler":
                print("✅ Sampler name correctly extracted")
            else:
                print(f"❌ Sampler name wrong: expected 'euler', got '{sampler}'")

            # Check seed
            seed = parameters.get("seed")
            if seed == 2543922272:
                print("✅ Seed correctly extracted")
            else:
                print(f"❌ Seed wrong: expected 2543922272, got {seed}")

            # Check cfg scale
            cfg = parameters.get("cfg_scale")
            if cfg == 5.0:
                print("✅ CFG scale correctly extracted")
            else:
                print(f"❌ CFG scale wrong: expected 5.0, got {cfg}")

            # Check steps
            steps = parameters.get("steps")
            if steps == 25:
                print("✅ Steps correctly extracted")
            else:
                print(f"❌ Steps wrong: expected 25, got {steps}")

            # Check for reasonable width/height
            width = parameters.get("width")
            height = parameters.get("height")
            if width and height and width > 100 and height > 100:
                print(f"✅ Dimensions look reasonable: {width}x{height}")
            else:
                print(f"❌ Dimensions look wrong: {width}x{height}")

        else:
            print(f"❌ Parser issue: {result.get('tool', 'No result') if result else 'No result'}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_fixed_universal_parser()
