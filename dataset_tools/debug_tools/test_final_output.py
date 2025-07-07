#!/usr/bin/env python3

"""Test the final MetadataEngine output to see what prompts are extracted."""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_final_output():
    """Test the final MetadataEngine output."""
    print("🔍 TESTING FINAL METADATA OUTPUT")
    print("=" * 32)

    test_file = "/Users/duskfall/Downloads/Metadata Samples/B4V0V3FKDVZHZZRERKQ31YFR10.jpeg"

    if not Path(test_file).exists():
        print(f"❌ Test file not found: {Path(test_file).name}")
        return

    print(f"📁 Testing: {Path(test_file).name}")

    try:
        from dataset_tools.metadata_engine import MetadataEngine

        parser_definitions_path = os.path.join(os.path.dirname(__file__), "parser_definitions")
        engine = MetadataEngine(parser_definitions_path)

        print("🔍 Running MetadataEngine...")
        result = engine.get_parser_for_file(test_file)

        if result and isinstance(result, dict):
            print("✅ SUCCESS!")
            print(f"   Tool: {result.get('tool', 'Unknown')}")
            print(f"   Format: {result.get('format', 'Unknown')}")

            # Check for prompts
            prompt = result.get("prompt", "")
            negative_prompt = result.get("negative_prompt", "")

            print("\n📝 EXTRACTED CONTENT:")
            print(f"   Prompt ({len(prompt)} chars): {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(
                f"   Negative ({len(negative_prompt)} chars): {negative_prompt[:100]}{'...' if len(negative_prompt) > 100 else ''}"
            )

            # Check parameters
            params = result.get("parameters", {})
            if params:
                print("\n⚙️ PARAMETERS:")
                for key, value in params.items():
                    if value:  # Only show non-empty values
                        print(f"   {key}: {value}")

            # Show full result structure
            print("\n🏗️ FULL STRUCTURE:")
            print(f"   Keys: {list(result.keys())}")

        else:
            print("❌ FAILED: MetadataEngine returned None")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_final_output()
