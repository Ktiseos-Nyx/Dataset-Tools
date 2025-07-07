#!/usr/bin/env python3

"""Simple A1111 JPEG test using the new MetadataEngine."""

import argparse
import json
import sys
from pathlib import Path

# Add the project root to the Python path to allow importing dataset_tools
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dataset_tools.metadata_engine.engine import create_metadata_engine


def test_a1111_simple(file_path: str):
    """Simple A1111 JPEG test."""
    print(f"🔧 SIMPLE A1111 JPEG TEST FOR: {file_path}")
    print("=" * (30 + len(file_path)))

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
            print("✅ Metadata extracted successfully!")
            print("\n📋 Extracted Data:")
            if isinstance(result, dict):
                print(json.dumps(result, indent=2))
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
                print(json.dumps(data, indent=2))
        else:
            print("❌ No metadata could be extracted from this file.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test A1111 JPEG metadata extraction using the new MetadataEngine.")
    parser.add_argument("file_path", type=str, help="The absolute path to the A1111 JPEG file to test.")
    args = parser.parse_args()

    test_a1111_simple(args.file_path)
