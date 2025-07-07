#!/usr/bin/env python3

"""Debug which parser is matched for a given file using the new MetadataEngine."""

import argparse
import sys
from pathlib import Path

# Add the project root to the Python path to allow importing dataset_tools
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dataset_tools.metadata_engine.engine import create_metadata_engine


def debug_parser_matching(file_path: str):
    """Debug which parser is matched for a given file."""
    print(f"🔍 PARSER MATCHING DIAGNOSTIC FOR: {file_path}")
    print("=" * (33 + len(file_path)))

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

            if isinstance(result, dict):
                print("\n📋 Extracted Data:")
                import json

                print(json.dumps(result, indent=2))
            else:
                print("\n📋 Reader Instance Attributes:")
                for attr in dir(result):
                    if not attr.startswith("_") and not callable(getattr(result, attr)):
                        print(f"  - {attr}: {getattr(result, attr)}")
        else:
            print("❌ No parser matched for this file.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Debug which parser from the new MetadataEngine matches a given file.")
    parser.add_argument("file_path", type=str, help="The absolute path to the file to test.")
    args = parser.parse_args()

    debug_parser_matching(args.file_path)
