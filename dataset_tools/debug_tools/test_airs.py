#!/usr/bin/env python3
# ruff: noqa: T201

"""Check the CivitAI airs field content."""

import json
import os
import sys

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_airs():
    """Check the airs field content."""
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

            if "extra" in data and "airs" in data["extra"]:
                airs_data = data["extra"]["airs"]
                print(  # noqa: T201"📊 AIRS DATA ANALYSIS:")
                print(  # noqa: T201f"   Type: {type(airs_data).__name__}")
                print(  # noqa: T201f"   Content: {airs_data}")

                if isinstance(airs_data, str):
                    try:
                        parsed = json.loads(airs_data)
                        print(  # noqa: T201f"   ✅ AIRS is JSON with keys: {list(parsed.keys())}")
                        for key, value in parsed.items():
                            print(  # noqa: T201f"      {key}: {str(value)[:100]}...")
                    except:
                        print(  # noqa: T201"   ❌ AIRS is not JSON")

            # Also check for URN patterns in the workflow
            workflow_str = json.dumps(data)
            urn_count = workflow_str.count("urn:air:")
            civitai_count = workflow_str.count("civitai:")

            print(  # noqa: T201"\n🔍 URN ANALYSIS:")
            print(  # noqa: T201f"   URN patterns found: {urn_count}")
            print(  # noqa: T201f"   CivitAI patterns found: {civitai_count}")

            if urn_count > 0:
                print(  # noqa: T201"   ✅ This is DEFINITELY a CivitAI file!")

    except Exception as e:
        print(  # noqa: T201f"❌ Error: {e}")


if __name__ == "__main__":
    test_airs()
