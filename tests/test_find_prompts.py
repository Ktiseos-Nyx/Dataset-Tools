#!/usr/bin/env python3
# ruff: noqa: T201

"""Find prompts in the ComfyUI workflow."""

import json
import os
import sys

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def find_prompts():
    """Find prompt-related nodes in the ComfyUI workflow."""
    print(  # noqa: T201"🔍 FINDING PROMPTS IN COMFYUI WORKFLOW")
    print(  # noqa: T201"=" * 35)

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

            print(  # noqa: T201"🔍 ANALYZING NODES FOR PROMPTS:")

            for node_id, node_data in data.items():
                if isinstance(node_data, dict) and "class_type" in node_data:
                    class_type = node_data["class_type"]
                    inputs = node_data.get("inputs", {})

                    # Look for text encoder nodes
                    if "text" in class_type.lower() or "encode" in class_type.lower():
                        print(  # noqa: T201f"\n📝 TEXT/ENCODE NODE: {node_id}")
                        print(  # noqa: T201f"   Class: {class_type}")
                        print(  # noqa: T201f"   Inputs: {list(inputs.keys())}")

                        for input_key, input_value in inputs.items():
                            if isinstance(input_value, str) and len(input_value) > 10:
                                print(  # noqa: T201f"   🎯 {input_key}: {input_value[:100]}...")

                    # Look for any node with text input
                    for input_key, input_value in inputs.items():
                        if (
                            input_key == "text"
                            and isinstance(input_value, str)
                            and len(input_value) > 10
                        ):
                            print(  # noqa: T201f"\n🎯 FOUND TEXT INPUT: {node_id} ({class_type})")
                            print(  # noqa: T201f"   text: {input_value[:100]}...")

            # Also check for any key containing "prompt" or similar
            print(  # noqa: T201"\n🔍 SEARCHING ALL KEYS FOR PROMPT-LIKE CONTENT:")
            for node_id, node_data in data.items():
                if isinstance(node_data, dict):
                    # Check all nested values for prompt-like content
                    def search_nested(obj, path=""):
                        if isinstance(obj, dict):
                            for k, v in obj.items():
                                current_path = f"{path}.{k}" if path else k
                                if isinstance(v, str) and len(v) > 20:
                                    # Check if it looks like a prompt
                                    words = v.lower().split()
                                    if any(
                                        word
                                        in [
                                            "woman",
                                            "man",
                                            "girl",
                                            "boy",
                                            "person",
                                            "beautiful",
                                            "detailed",
                                            "high",
                                            "quality",
                                        ]
                                        for word in words[:10]
                                    ):
                                        print(  # noqa: T201
                                            f"   📝 {node_id} -> {current_path}: {v[:100]}..."
                                        )
                                elif isinstance(v, (dict, list)):
                                    search_nested(v, current_path)
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                current_path = f"{path}[{i}]" if path else f"[{i}]"
                                search_nested(item, current_path)

                    search_nested(node_data)

    except Exception as e:
        print(  # noqa: T201f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    find_prompts()
