#!/usr/bin/env python3
# ruff: noqa: T201

"""Analyze the Civitai ComfyUI data structure to understand field extraction issues."""

import json
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def analyze_civitai_structure():
    """Analyze the data structure of the Civitai ComfyUI file."""
    print(  # noqa: T201"🔍 CIVITAI COMFYUI STRUCTURE ANALYSIS")
    print(  # noqa: T201"=" * 35)

    test_file = (
        "/Users/duskfall/Downloads/Metadata Samples/B4V0V3FKDVZHZZRERKQ31YFR10.jpeg"
    )

    if not Path(test_file).exists():
        print(  # noqa: T201f"❌ Test file not found: {Path(test_file).name}")
        return

    print(  # noqa: T201f"📁 Analyzing: {Path(test_file).name}")

    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

        preparer = ContextDataPreparer()
        context = preparer.prepare_context(test_file)

        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            print(  # noqa: T201f"✅ UserComment extracted: {len(user_comment)} characters")

            # Parse as JSON
            try:
                data = json.loads(user_comment)
                print(  # noqa: T201f"✅ Valid JSON with {len(data)} top-level keys")

                print(  # noqa: T201"\n📊 TOP-LEVEL STRUCTURE:")
                for key in list(data.keys())[:10]:
                    value = data[key]
                    print(  # noqa: T201f"   {key}: {type(value).__name__}")
                    if isinstance(value, str) and len(value) < 100:
                        print(  # noqa: T201f"      = {value}")
                    elif isinstance(value, dict):
                        print(  # noqa: T201
                            f"      = dict with {len(value)} keys: {list(value.keys())[:5]}"
                        )
                    elif isinstance(value, list):
                        print(  # noqa: T201f"      = list with {len(value)} items")

                # Check for extra.extraMetadata
                if "extra" in data and isinstance(data["extra"], dict):
                    extra = data["extra"]
                    print(  # noqa: T201"\n📊 EXTRA SECTION:")
                    print(  # noqa: T201f"   extra has {len(extra)} keys: {list(extra.keys())}")

                    if "extraMetadata" in extra:
                        extra_metadata = extra["extraMetadata"]
                        print(  # noqa: T201"\n📊 EXTRA METADATA:")
                        print(  # noqa: T201f"   Type: {type(extra_metadata).__name__}")

                        if isinstance(extra_metadata, str):
                            print(  # noqa: T201f"   Length: {len(extra_metadata)} characters")
                            print(  # noqa: T201f"   Preview: {extra_metadata[:200]}...")

                            # Try to parse as JSON
                            try:
                                nested_data = json.loads(extra_metadata)
                                print(  # noqa: T201
                                    f"   ✅ extraMetadata is valid JSON with {len(nested_data)} keys"
                                )
                                print(  # noqa: T201f"   Keys: {list(nested_data.keys())}")

                                # Look for prompt-related fields
                                for key in nested_data.keys():
                                    if "prompt" in key.lower():
                                        print(  # noqa: T201
                                            f"   🎯 FOUND PROMPT FIELD: {key} = {str(nested_data[key])[:100]}..."
                                        )

                            except json.JSONDecodeError as e:
                                print(  # noqa: T201f"   ❌ extraMetadata is not valid JSON: {e}")

                        elif isinstance(extra_metadata, dict):
                            print(  # noqa: T201
                                f"   Already parsed dict with {len(extra_metadata)} keys: {list(extra_metadata.keys())}"
                            )

                # Look for direct prompt fields in root
                print(  # noqa: T201"\n🔍 SEARCHING FOR PROMPT FIELDS:")
                for key in data.keys():
                    if "prompt" in key.lower():
                        print(  # noqa: T201f"   🎯 ROOT LEVEL: {key} = {str(data[key])[:100]}...")

            except json.JSONDecodeError as e:
                print(  # noqa: T201f"❌ Failed to parse JSON: {e}")
                print(  # noqa: T201f"Raw content preview: {user_comment[:200]}...")
        else:
            print(  # noqa: T201"❌ No UserComment extracted")

    except Exception as e:
        print(  # noqa: T201f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    analyze_civitai_structure()
