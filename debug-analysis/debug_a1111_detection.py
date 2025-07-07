#!/usr/bin/env python3

"""Debug script to understand why A1111 files are not being detected by the enhanced MetadataEngine."""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_tools.metadata_engine import get_metadata_engine


def debug_a1111_detection():
    """Debug A1111 detection process."""
    test_file = "/Users/duskfall/Downloads/Metadata Samples/00000-1626107238.jpeg"
    parser_definitions_path = Path(__file__).parent / "parser_definitions"

    print("🔍 DEBUGGING A1111 DETECTION")
    print("=" * 50)
    print(f"Test file: {test_file}")
    print(f"Parser definitions path: {parser_definitions_path}")
    print()

    # Create engine
    engine = get_metadata_engine(str(parser_definitions_path))

    # Test direct parser lookup
    print("📋 AVAILABLE PARSERS:")
    print("-" * 20)
    for parser_data in engine.sorted_definitions:
        parser_name = parser_data.get("parser_name", "Unknown")
        priority = parser_data.get("priority", 0)
        print(f"  {parser_name}: priority {priority}")
    print()

    # Test context preparation
    print("🔧 PREPARING CONTEXT:")
    print("-" * 20)
    context = engine.context_preparer.prepare_context(test_file)
    print(f"Context keys: {list(context.keys())}")

    # Show PIL info if available
    if "pil_info" in context:
        pil_info = context["pil_info"]
        print(f"PIL info keys: {list(pil_info.keys())}")
        if "parameters" in pil_info:
            param_str = pil_info["parameters"]
            print(f"Parameters string (first 200 chars): {param_str[:200]}...")

    if "raw_user_comment_str" in context:
        uc_str = context["raw_user_comment_str"]
        print(f"User comment string (first 200 chars): {uc_str[:200]}...")
    print()

    # Test rule evaluation for a1111_webui parser
    print("🧪 TESTING A1111 WEBUI PARSER:")
    print("-" * 30)

    a1111_parser = None
    for parser_data in engine.sorted_definitions:
        if parser_data.get("parser_name") == "a1111_webui":
            a1111_parser = parser_data
            break

    if a1111_parser:
        print(f"Found a1111_webui parser with priority {a1111_parser.get('priority', 0)}")

        detection_rules = a1111_parser.get("detection_rules", [])
        print(f"Detection rules: {len(detection_rules)}")

        for i, rule in enumerate(detection_rules):
            print(f"  Rule {i + 1}: {rule.get('comment', 'No comment')}")
            print(f"    Rule structure: {rule}")
            try:
                result = engine.rule_evaluator.evaluate_rule(rule, context)
                print(f"    Result: {result}")
            except Exception as e:
                print(f"    Error: {e}")
                import traceback

                traceback.print_exc()
    else:
        print("❌ a1111_webui parser not found!")

    print()

    # Test overall detection
    print("🎯 OVERALL DETECTION:")
    print("-" * 20)
    result = engine.get_parser_for_file(test_file)
    print(f"Final result: {result}")

    return result is not None


if __name__ == "__main__":
    success = debug_a1111_detection()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)
