#!/usr/bin/env python3
# ruff: noqa: T201

"""Find sampling nodes in the ComfyUI workflow."""

import json
import os
import sys

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def find_sampler_nodes():
    """Find sampling-related nodes in the ComfyUI workflow."""
    print(  # noqa: T201"🔍 FINDING SAMPLING NODES")
    print(  # noqa: T201"=" * 25)

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

            print(  # noqa: T201"🔍 ALL NODES BY CLASS TYPE:")

            class_type_count = {}

            for node_id, node_data in data.items():
                if isinstance(node_data, dict) and "class_type" in node_data:
                    class_type = node_data["class_type"]
                    class_type_count[class_type] = (
                        class_type_count.get(class_type, 0) + 1
                    )

                    print(  # noqa: T201f"   {node_id}: {class_type}")

                    # Look for any node that might be doing sampling
                    if any(
                        keyword in class_type.lower()
                        for keyword in ["sampl", "denois", "noise", "sigm", "schedule"]
                    ):
                        inputs = node_data.get("inputs", {})
                        print(  # noqa: T201f"      🎯 POTENTIAL SAMPLER: {class_type}")
                        print(  # noqa: T201f"      Inputs: {list(inputs.keys())}")

                        # Check for connections to text encoders
                        for input_key, input_value in inputs.items():
                            if isinstance(input_value, list) and len(input_value) == 2:
                                connected_node, output_slot = input_value
                                print(  # noqa: T201
                                    f"         {input_key} <- Node {connected_node}[{output_slot}]"
                                )

            print(  # noqa: T201"\n📊 CLASS TYPE SUMMARY:")
            for class_type, count in sorted(class_type_count.items()):
                print(  # noqa: T201f"   {class_type}: {count}")

            # Look for nodes that connect to text encoders
            print(  # noqa: T201"\n🔍 NODES CONNECTED TO TEXT ENCODERS:")

            text_encoder_nodes = []
            for node_id, node_data in data.items():
                if isinstance(node_data, dict) and "class_type" in node_data:
                    class_type = node_data["class_type"]
                    if "text" in class_type.lower() and "encode" in class_type.lower():
                        text_encoder_nodes.append(node_id)
                        print(  # noqa: T201f"   Text Encoder: {node_id} ({class_type})")

            # Find nodes that use text encoder outputs
            for node_id, node_data in data.items():
                if isinstance(node_data, dict) and "inputs" in node_data:
                    inputs = node_data["inputs"]
                    class_type = node_data["class_type"]

                    for input_key, input_value in inputs.items():
                        if isinstance(input_value, list) and len(input_value) == 2:
                            connected_node, output_slot = input_value
                            if connected_node in text_encoder_nodes:
                                print(  # noqa: T201
                                    f"   🎯 {node_id} ({class_type}) uses text encoder {connected_node} via '{input_key}'"
                                )

    except Exception as e:
        print(  # noqa: T201f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    find_sampler_nodes()
