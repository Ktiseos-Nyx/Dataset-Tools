#!/usr/bin/env python3

"""Debug script to test individual sub-rules."""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_tools.metadata_engine import get_metadata_engine


def debug_subrules():
    """Debug individual sub-rules."""
    test_file = "/Users/duskfall/Downloads/Metadata Samples/00000-1626107238.jpeg"
    parser_definitions_path = Path(__file__).parent / "parser_definitions"

    print("🔍 DEBUGGING SUB-RULES")
    print("=" * 50)

    # Create engine
    engine = get_metadata_engine(str(parser_definitions_path))
    context = engine.context_preparer.prepare_context(test_file)

    # Test the two sub-rules individually
    subrule1 = {
        "source_type": "pil_info_key",
        "source_key": "parameters",
        "operator": "exists",
    }
    subrule2 = {"source_type": "exif_user_comment", "operator": "exists"}

    print("🧪 TESTING SUB-RULE 1:")
    print(f"Rule: {subrule1}")
    result1 = engine.rule_evaluator.evaluate_rule(subrule1, context)
    print(f"Result: {result1}")
    print()

    print("🧪 TESTING SUB-RULE 2:")
    print(f"Rule: {subrule2}")
    result2 = engine.rule_evaluator.evaluate_rule(subrule2, context)
    print(f"Result: {result2}")
    print()

    print("🧮 EXPECTED OR RESULT:")
    expected_or = result1 or result2
    print(f"({result1} OR {result2}) = {expected_or}")
    print()

    # Test the complex rule
    complex_rule = {
        "comment": "Rule 1: EITHER PNG parameters chunk OR EXIF UserComment must exist",
        "condition": "OR",
        "rules": [subrule1, subrule2],
    }

    print("🧪 TESTING COMPLEX OR RULE:")
    print(f"Rule: {complex_rule}")
    complex_result = engine.rule_evaluator.evaluate_rule(complex_rule, context)
    print(f"Result: {complex_result}")
    print()

    print("📊 SUMMARY:")
    print(f"Sub-rule 1 (pil_info_key parameters exists): {result1}")
    print(f"Sub-rule 2 (exif_user_comment exists): {result2}")
    print(f"Expected OR result: {expected_or}")
    print(f"Actual complex rule result: {complex_result}")
    print(f"Match: {expected_or == complex_result}")

    return expected_or == complex_result


if __name__ == "__main__":
    success = debug_subrules()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)
