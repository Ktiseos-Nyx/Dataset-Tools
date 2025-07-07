#!/usr/bin/env python3
# ruff: noqa: T201
"""Simple test script to verify metadata engine integration works."""

import os
import sys
from pathlib import Path

# Add the dataset_tools directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "dataset_tools"))


def test_metadata_engine():
    """Test if metadata engine can be imported and initialized."""
    print(  # noqa: T201"Testing metadata engine integration...")

    try:
        from dataset_tools.metadata_engine import get_metadata_engine

        print(  # noqa: T201"✓ Successfully imported metadata engine")

        # Test initialization
        parser_definitions_path = (
            Path(__file__).parent.parent / "dataset_tools" / "parser_definitions"
        )
        print(  # noqa: T201f"Parser definitions path: {parser_definitions_path}")
        print(  # noqa: T201f"Path exists: {parser_definitions_path.exists()}")

        if parser_definitions_path.exists():
            print(  # noqa: T201
                f"Files in parser_definitions: {len(list(parser_definitions_path.glob('*.json')))} JSON files"
            )

            # Test engine creation
            engine = get_metadata_engine(str(parser_definitions_path))
            print(  # noqa: T201"✓ Successfully created metadata engine")

            # Test with a sample file if it exists
            sample_file = (
                "/Users/duskfall/Downloads/Metadata Samples/00000-512479461968570.png"
            )
            if os.path.exists(sample_file):
                print(  # noqa: T201f"Testing with sample file: {sample_file}")
                result = engine.get_parser_for_file(sample_file)
                print(  # noqa: T201f"Result: {result}")
            else:
                print(  # noqa: T201"Sample file not found, skipping file test")

        else:
            print(  # noqa: T201"❌ Parser definitions path does not exist")

    except Exception as e:
        print(  # noqa: T201f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_metadata_engine()
