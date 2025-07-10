#!/usr/bin/env python3
# ruff: noqa: T201

"""Debug T5 parser traversal issue using the new MetadataEngine."""

import argparse
import json
import sys
from pathlib import Path

# Add the project root to the Python path to allow importing dataset_tools
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dataset_tools.metadata_engine.engine import create_metadata_engine


def test_t5_traversal(file_path: str):
    """Test T5 parser traversal with a real workflow file."""
    print(  # noqa: T201f"🔧 DEBUGGING T5 PARSER TRAVERSAL FOR: {file_path}")
    print(  # noqa: T201"=" * (42 + len(file_path)))

    parser_definitions_path = project_root / "dataset_tools" / "parser_definitions"

    if not parser_definitions_path.is_dir():
        print(  # noqa: T201
            f"❌ Error: Parser definitions directory not found at: {parser_definitions_path}"
        )
        return

    try:
        # Create a metadata engine instance
        engine = create_metadata_engine(str(parser_definitions_path))

        # Get the parser for the file
        result = engine.get_parser_for_file(file_path)

        if result:
            tool_name = getattr(result, "tool", result.get("tool", "Unknown"))
            print(  # noqa: T201f"✅ Matched Parser: {tool_name}")

            print(  # noqa: T201"\n📋 Extracted Data:")
            if isinstance(result, dict):
                print(  # noqa: T201json.dumps(result, indent=2))
            else:
                # For BaseFormat objects, print their attributes
                data = {
                    "tool": getattr(result, "tool", "Unknown"),
                    "positive": getattr(result, "positive", ""),
                    "negative": getattr(result, "negative", ""),
                    "parameters": getattr(result, "parameter", {}),
                    "width": getattr(result, "width", 0),
                    "height": getattr(result, "height", 0),
                    "raw": getattr(result, "raw", ""),
                }
                print(  # noqa: T201json.dumps(data, indent=2))
        else:
            print(  # noqa: T201"❌ No parser matched for this file.")

    except Exception as e:
        print(  # noqa: T201f"❌ An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test T5 parser traversal with a given file using the new MetadataEngine."
    )
    parser.add_argument(
        "file_path", type=str, help="The absolute path to the T5 workflow file to test."
    )
    args = parser.parse_args()

    test_t5_traversal(args.file_path)
