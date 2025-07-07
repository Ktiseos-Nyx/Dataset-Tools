#!/usr/bin/env python3
# ruff: noqa: T201

"""Test the fixed Universal Parser on the advanced ComfyUI image."""

from pathlib import Path

from dataset_tools.metadata_engine import get_metadata_engine


def test_fixed_universal_parser():
    """Test the Universal Parser with the advanced ComfyUI image."""
    print(  # noqa: T201"🧪 TESTING FIXED UNIVERSAL PARSER")
    print(  # noqa: T201"=" * 40)

    # Test with the advanced ComfyUI image
    test_file = "/Users/duskfall/Downloads/Metadata Samples/872676588544625334.png"
    parser_definitions_path = Path(__file__).parent / "parser_definitions"

    try:
        # Create metadata engine
        engine = get_metadata_engine(str(parser_definitions_path))

        # Test parsing
        result = engine.get_parser_for_file(test_file)

        if result and result.get("tool") == "ComfyUI (Universal Parser)":
            print(  # noqa: T201"✅ Universal Parser detected correctly")

            # Check extracted data
            prompt = result.get("prompt", "")
            negative = result.get("negative_prompt", "")
            parameters = result.get("parameters", {})

            print(  # noqa: T201"\n📝 EXTRACTED DATA:")
            print(  # noqa: T201f"Prompt: {prompt[:100]}...")
            print(  # noqa: T201f"Negative: {negative}")

            print(  # noqa: T201"\n🔧 PARAMETERS:")
            for key, value in parameters.items():
                print(  # noqa: T201f"  {key}: {value} ({type(value).__name__})")

            # Validate the critical fixes
            print(  # noqa: T201"\n✅ VALIDATION:")

            # Check sampler name
            sampler = parameters.get("sampler_name")
            if sampler == "euler":
                print(  # noqa: T201"✅ Sampler name correctly extracted")
            else:
                print(  # noqa: T201f"❌ Sampler name wrong: expected 'euler', got '{sampler}'")

            # Check seed
            seed = parameters.get("seed")
            if seed == 2543922272:
                print(  # noqa: T201"✅ Seed correctly extracted")
            else:
                print(  # noqa: T201f"❌ Seed wrong: expected 2543922272, got {seed}")

            # Check cfg scale
            cfg = parameters.get("cfg_scale")
            if cfg == 5.0:
                print(  # noqa: T201"✅ CFG scale correctly extracted")
            else:
                print(  # noqa: T201f"❌ CFG scale wrong: expected 5.0, got {cfg}")

            # Check steps
            steps = parameters.get("steps")
            if steps == 25:
                print(  # noqa: T201"✅ Steps correctly extracted")
            else:
                print(  # noqa: T201f"❌ Steps wrong: expected 25, got {steps}")

            # Check for reasonable width/height
            width = parameters.get("width")
            height = parameters.get("height")
            if width and height and width > 100 and height > 100:
                print(  # noqa: T201f"✅ Dimensions look reasonable: {width}x{height}")
            else:
                print(  # noqa: T201f"❌ Dimensions look wrong: {width}x{height}")

        else:
            print(  # noqa: T201
                f"❌ Parser issue: {result.get('tool', 'No result') if result else 'No result'}"
            )

    except Exception as e:
        print(  # noqa: T201f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_fixed_universal_parser()
