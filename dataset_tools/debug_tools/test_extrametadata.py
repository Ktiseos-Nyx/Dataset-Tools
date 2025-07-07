#!/usr/bin/env python3
# ruff: noqa: T201

"""Parse the extraMetadata to see if it contains resource descriptions."""

import json
import os
import sys

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_extrametadata():
    """Parse the extraMetadata to see what resource info it contains."""
    test_file = (
        "/Users/duskfall/Downloads/Metadata Samples/B4V0V3FKDVZHZZRERKQ31YFR10.jpeg"
    )

    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

        preparer = ContextDataPreparer()
        context = preparer.prepare_context(test_file)

        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            data = json.loads(user_comment)

            print(  # noqa: T201"🔍 CHECKING EXTRAMETADATA CONTENT:")
            print(  # noqa: T201"=" * 40)

            if "extraMetadata" in data:
                extra_meta_str = data["extraMetadata"]
                print(  # noqa: T201"📄 Raw extraMetadata string:")
                print(  # noqa: T201f"   {extra_meta_str[:200]}...")

                # Try to parse the escaped JSON
                try:
                    # First decode the Unicode escapes
                    import codecs

                    decoded = codecs.decode(extra_meta_str, "unicode_escape")
                    print(  # noqa: T201"\n📋 Decoded extraMetadata string:")
                    print(  # noqa: T201f"   {decoded[:200]}...")

                    # Then parse as JSON
                    extra_meta = json.loads(decoded)
                    print(  # noqa: T201"\n✅ PARSED EXTRAMETADATA:")
                    for key, value in extra_meta.items():
                        if key == "resources" and isinstance(value, list):
                            print(  # noqa: T201f"   📦 {key}: [")
                            for i, resource in enumerate(value):
                                print(  # noqa: T201f"      Resource {i + 1}: {resource}")
                            print(  # noqa: T201"   ]")
                        else:
                            print(  # noqa: T201f"   {key}: {value}")

                except Exception as e:
                    print(  # noqa: T201f"   ❌ Failed to parse extraMetadata: {e}")

            print(  # noqa: T201"\n🏷️ COMPARING WITH AIRS ARRAY:")
            if "extra" in data and "airs" in data["extra"]:
                airs = data["extra"]["airs"]
                print(  # noqa: T201f"   AIRS count: {len(airs)}")
                for i, urn in enumerate(airs):
                    print(  # noqa: T201f"   URN {i + 1}: {urn}")

                    # Extract the model version ID from URN
                    if "@" in urn:
                        version_id = urn.split("@")[-1]
                        print(  # noqa: T201f"           Version ID: {version_id}")

    except Exception as e:
        print(  # noqa: T201f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_extrametadata()
