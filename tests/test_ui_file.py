#!/usr/bin/env python3
# ruff: noqa: T201

"""Test the specific file that's causing UI mojibake using the new MetadataEngine."""

import argparse
import json
import sys
from pathlib import Path

# Add the project root to the Python path to allow importing dataset_tools
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dataset_tools.metadata_engine.engine import create_metadata_engine


def test_ui_file(file_path: str):
    """Test the specific file from the UI that's causing issues."""
    print(  # noqa: T201f"🔍 UI FILE MOJIBAKE TEST FOR: {file_path}")
    print(  # noqa: T201"=" * (30 + len(file_path)))

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
            print(  # noqa: T201"✅ Metadata extracted successfully!")
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
            print(  # noqa: T201"❌ No metadata could be extracted from this file.")

    except Exception as e:
        print(  # noqa: T201f"❌ An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test a specific file for UI mojibake issues using the new MetadataEngine."
    )
    parser.add_argument(
        "file_path", type=str, help="The absolute path to the file to test."
    )
    args = parser.parse_args()

    test_ui_file(args.file_path)
