#!/usr/bin/env python3
# ruff: noqa: T201

"""Test the final MetadataEngine output to see what prompts are extracted."""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_final_output():
    """Test the final MetadataEngine output."""
    print(  # noqa: T201"🔍 TESTING FINAL METADATA OUTPUT")
    print(  # noqa: T201"=" * 32)

    test_file = (
        "/Users/duskfall/Downloads/Metadata Samples/B4V0V3FKDVZHZZRERKQ31YFR10.jpeg"
    )

    if not Path(test_file).exists():
        print(  # noqa: T201f"❌ Test file not found: {Path(test_file).name}")
        return

    print(  # noqa: T201f"📁 Testing: {Path(test_file).name}")

    try:
        from dataset_tools.metadata_engine import MetadataEngine

        parser_definitions_path = os.path.join(
            os.path.dirname(__file__), "parser_definitions"
        )
        engine = MetadataEngine(parser_definitions_path)

        print(  # noqa: T201"🔍 Running MetadataEngine...")
        result = engine.get_parser_for_file(test_file)

        if result and isinstance(result, dict):
            print(  # noqa: T201"✅ SUCCESS!")
            print(  # noqa: T201f"   Tool: {result.get('tool', 'Unknown')}")
            print(  # noqa: T201f"   Format: {result.get('format', 'Unknown')}")

            # Check for prompts
            prompt = result.get("prompt", "")
            negative_prompt = result.get("negative_prompt", "")

            print(  # noqa: T201"\n📝 EXTRACTED CONTENT:")
            print(  # noqa: T201
                f"   Prompt ({len(prompt)} chars): {prompt[:100]}{'...' if len(prompt) > 100 else ''}"
            )
            print(  # noqa: T201
                f"   Negative ({len(negative_prompt)} chars): {negative_prompt[:100]}{'...' if len(negative_prompt) > 100 else ''}"
            )

            # Check parameters
            params = result.get("parameters", {})
            if params:
                print(  # noqa: T201"\n⚙️ PARAMETERS:")
                for key, value in params.items():
                    if value:  # Only show non-empty values
                        print(  # noqa: T201f"   {key}: {value}")

            # Show full result structure
            print(  # noqa: T201"\n🏗️ FULL STRUCTURE:")
            print(  # noqa: T201f"   Keys: {list(result.keys())}")

        else:
            print(  # noqa: T201"❌ FAILED: MetadataEngine returned None")

    except Exception as e:
        print(  # noqa: T201f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_final_output()
