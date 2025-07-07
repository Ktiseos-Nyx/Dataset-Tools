#!/usr/bin/env python3

"""Analyze the workflow to see what sampling nodes it contains using the new MetadataEngine."""

import argparse
import sys
from pathlib import Path

# Add the project root to the Python path to allow importing dataset_tools
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dataset_tools.metadata_engine.engine import create_metadata_engine


def analyze_workflow(file_path: str):
    """Analyze the ComfyUI workflow content."""
    print(f"🔍 WORKFLOW ANALYSIS FOR: {file_path}")
    print("=" * (28 + len(file_path)))

    parser_definitions_path = project_root / "dataset_tools" / "parser_definitions"

    if not parser_definitions_path.is_dir():
        print(f"❌ Error: Parser definitions directory not found at: {parser_definitions_path}")
        return

    try:
        # Create a metadata engine instance
        engine = create_metadata_engine(str(parser_definitions_path))

        # Get the parser for the file
        result = engine.get_parser_for_file(file_path)

        if result:
            tool_name = getattr(result, "tool", result.get("tool", "Unknown"))
            print(f"✅ Matched Parser: {tool_name}")

            print("\n📋 Workflow Data:")
            if isinstance(result, dict):
                workflow_data = result.get("workflow", result.get("prompt"))
                if workflow_data and isinstance(workflow_data, dict):
                    # Analyze node types
                    class_types = {}
                    nodes = workflow_data.get("nodes", workflow_data)
                    for node_id, node_data in nodes.items():
                        if isinstance(node_data, dict) and "class_type" in node_data:
                            class_type = node_data["class_type"]
                            class_types[class_type] = class_types.get(class_type, 0) + 1

                    print("\n📊 Node types:")
                    for class_type, count in sorted(class_types.items()):
                        print(f"   {class_type}: {count}")
                else:
                    print("❌ No workflow data found in the result.")
            else:
                print("❌ Result is not a dictionary.")
        else:
            print("❌ No parser matched for this file.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze the ComfyUI workflow content of a given file using the new MetadataEngine."
    )
    parser.add_argument("file_path", type=str, help="The absolute path to the file to analyze.")
    args = parser.parse_args()

    analyze_workflow(args.file_path)
