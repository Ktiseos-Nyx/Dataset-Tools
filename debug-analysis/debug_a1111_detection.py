#!/usr/bin/env python3
# ruff: noqa: T201

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

    print(  # noqa: T201"🔍 DEBUGGING A1111 DETECTION")
    print(  # noqa: T201"=" * 50)
    print(  # noqa: T201f"Test file: {test_file}")
    print(  # noqa: T201f"Parser definitions path: {parser_definitions_path}")
    print(  # noqa: T201)

    # Create engine
    engine = get_metadata_engine(str(parser_definitions_path))

    # Test direct parser lookup
    print(  # noqa: T201"📋 AVAILABLE PARSERS:")
    print(  # noqa: T201"-" * 20)
    for parser_data in engine.sorted_definitions:
        parser_name = parser_data.get("parser_name", "Unknown")
        priority = parser_data.get("priority", 0)
        print(  # noqa: T201f"  {parser_name}: priority {priority}")
    print(  # noqa: T201)

    # Test context preparation
    print(  # noqa: T201"🔧 PREPARING CONTEXT:")
    print(  # noqa: T201"-" * 20)
    context = engine.context_preparer.prepare_context(test_file)
    print(  # noqa: T201f"Context keys: {list(context.keys())}")

    # Show PIL info if available
    if "pil_info" in context:
        pil_info = context["pil_info"]
        print(  # noqa: T201f"PIL info keys: {list(pil_info.keys())}")
        if "parameters" in pil_info:
            param_str = pil_info["parameters"]
            print(  # noqa: T201f"Parameters string (first 200 chars): {param_str[:200]}...")

    if "raw_user_comment_str" in context:
        uc_str = context["raw_user_comment_str"]
        print(  # noqa: T201f"User comment string (first 200 chars): {uc_str[:200]}...")
    print(  # noqa: T201)

    # Test rule evaluation for a1111_webui parser
    print(  # noqa: T201"🧪 TESTING A1111 WEBUI PARSER:")
    print(  # noqa: T201"-" * 30)

    a1111_parser = None
    for parser_data in engine.sorted_definitions:
        if parser_data.get("parser_name") == "a1111_webui":
            a1111_parser = parser_data
            break

    if a1111_parser:
        print(  # noqa: T201
            f"Found a1111_webui parser with priority {a1111_parser.get('priority', 0)}"
        )

        detection_rules = a1111_parser.get("detection_rules", [])
        print(  # noqa: T201f"Detection rules: {len(detection_rules)}")

        for i, rule in enumerate(detection_rules):
            print(  # noqa: T201f"  Rule {i + 1}: {rule.get('comment', 'No comment')}")
            print(  # noqa: T201f"    Rule structure: {rule}")
            try:
                result = engine.rule_evaluator.evaluate_rule(rule, context)
                print(  # noqa: T201f"    Result: {result}")
            except Exception as e:
                print(  # noqa: T201f"    Error: {e}")
                import traceback

                traceback.print_exc()
    else:
        print(  # noqa: T201"❌ a1111_webui parser not found!")

    print(  # noqa: T201)

    # Test overall detection
    print(  # noqa: T201"🎯 OVERALL DETECTION:")
    print(  # noqa: T201"-" * 20)
    result = engine.get_parser_for_file(test_file)
    print(  # noqa: T201f"Final result: {result}")

    return result is not None


if __name__ == "__main__":
    success = debug_a1111_detection()
    print(  # noqa: T201f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)
