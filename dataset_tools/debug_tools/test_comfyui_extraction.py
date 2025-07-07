#!/usr/bin/env python3
# ruff: noqa: T201

"""Test ComfyUI extraction methods directly using the new MetadataEngine."""

import argparse
import sys
from pathlib import Path

# Add the project root to the Python path to allow importing dataset_tools
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dataset_tools.metadata_engine.engine import create_metadata_engine


def test_comfyui_extraction(file_path: str):
    """Test ComfyUI extraction methods directly."""
    print(  # noqa: T201f"🔍 TESTING COMFYUI EXTRACTION FOR: {file_path}")
    print(  # noqa: T201"=" * (33 + len(file_path)))

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

            print(  # noqa: T201"\n📋 Extracted Prompts:")
            if isinstance(result, dict):
                positive_prompt = result.get("prompt", "Not found")
                negative_prompt = result.get("negative_prompt", "Not found")
                print(  # noqa: T201f"  - Positive: {positive_prompt}")
                print(  # noqa: T201f"  - Negative: {negative_prompt}")
            else:
                positive_prompt = getattr(result, "positive", "Not found")
                negative_prompt = getattr(result, "negative", "Not found")
                print(  # noqa: T201f"  - Positive: {positive_prompt}")
                print(  # noqa: T201f"  - Negative: {negative_prompt}")
        else:
            print(  # noqa: T201"❌ No parser matched for this file.")

    except Exception as e:
        print(  # noqa: T201f"❌ An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test ComfyUI prompt extraction from a given file using the new MetadataEngine."
    )
    parser.add_argument(
        "file_path", type=str, help="The absolute path to the ComfyUI file to test."
    )
    args = parser.parse_args()

    test_comfyui_extraction(args.file_path)
