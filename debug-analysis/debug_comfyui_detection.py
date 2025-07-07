#!/usr/bin/env python3

"""Debug script to understand why ComfyUI files are not being detected by enhanced parsers."""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_tools.metadata_engine import get_metadata_engine


def debug_comfyui_detection():
    """Debug ComfyUI detection process."""
    test_file = "/Users/duskfall/Downloads/Metadata Samples/ComfyUI_00001_.png"
    parser_definitions_path = Path(__file__).parent / "parser_definitions"

    print("🔍 DEBUGGING COMFYUI DETECTION")
    print("=" * 50)
    print(f"Test file: {test_file}")
    print()

    # Create engine
    engine = get_metadata_engine(str(parser_definitions_path))

    # Show ComfyUI related parsers
    print("📋 COMFYUI PARSERS:")
    print("-" * 20)
    comfyui_parsers = []
    for parser_data in engine.sorted_definitions:
        parser_name = parser_data.get("parser_name", "Unknown")
        if "comfy" in parser_name.lower() or "ComfyUI" in parser_data.get("description", ""):
            priority = parser_data.get("priority", 0)
            print(f"  {parser_name}: priority {priority}")
            comfyui_parsers.append(parser_data)
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

        # Check for common ComfyUI data sources
        for key in ["prompt", "workflow", "parameters"]:
            if key in pil_info:
                value = pil_info[key]
                if isinstance(value, str):
                    print(f"{key} (first 100 chars): {value[:100]}...")
                else:
                    print(f"{key} type: {type(value)}")
    print()

    # Test the first few ComfyUI parsers
    print("🧪 TESTING COMFYUI PARSERS:")
    print("-" * 30)

    for i, parser_data in enumerate(comfyui_parsers[:3]):  # Test first 3
        parser_name = parser_data.get("parser_name", "Unknown")
        priority = parser_data.get("priority", 0)
        print(f"\n{i + 1}. {parser_name} (priority {priority}):")

        detection_rules = parser_data.get("detection_rules", [])
        print(f"   Detection rules: {len(detection_rules)}")

        all_pass = True
        for j, rule in enumerate(detection_rules):
            try:
                result = engine.rule_evaluator.evaluate_rule(rule, context)
                status = "✅" if result else "❌"
                print(f"   Rule {j + 1}: {status} {result} - {rule.get('comment', 'No comment')}")
                if not result:
                    all_pass = False
            except Exception as e:
                print(f"   Rule {j + 1}: 💥 Error: {e}")
                all_pass = False

        print(f"   Overall match: {'✅' if all_pass else '❌'} {all_pass}")

        if all_pass:
            print("   🎉 This parser should match!")
            break

    print()

    # Test overall detection
    print("🎯 OVERALL DETECTION:")
    print("-" * 20)
    result = engine.get_parser_for_file(test_file)
    if result:
        print(f"✅ Enhanced detection succeeded: {result.get('tool', 'Unknown')}")
    else:
        print("❌ Enhanced detection failed - will fall back to vendored SDPR")

    return result is not None


if __name__ == "__main__":
    success = debug_comfyui_detection()
    print(f"\n{'🎉 SUCCESS' if success else '❌ NEEDS INVESTIGATION'}")
    sys.exit(0 if success else 1)
