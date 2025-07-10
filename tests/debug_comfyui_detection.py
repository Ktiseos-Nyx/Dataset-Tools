#!/usr/bin/env python3
# ruff: noqa: T201

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

    print(  # noqa: T201"🔍 DEBUGGING COMFYUI DETECTION")
    print(  # noqa: T201"=" * 50)
    print(  # noqa: T201f"Test file: {test_file}")
    print(  # noqa: T201)

    # Create engine
    engine = get_metadata_engine(str(parser_definitions_path))

    # Show ComfyUI related parsers
    print(  # noqa: T201"📋 COMFYUI PARSERS:")
    print(  # noqa: T201"-" * 20)
    comfyui_parsers = []
    for parser_data in engine.sorted_definitions:
        parser_name = parser_data.get("parser_name", "Unknown")
        if "comfy" in parser_name.lower() or "ComfyUI" in parser_data.get(
            "description", ""
        ):
            priority = parser_data.get("priority", 0)
            print(  # noqa: T201f"  {parser_name}: priority {priority}")
            comfyui_parsers.append(parser_data)
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

        # Check for common ComfyUI data sources
        for key in ["prompt", "workflow", "parameters"]:
            if key in pil_info:
                value = pil_info[key]
                if isinstance(value, str):
                    print(  # noqa: T201f"{key} (first 100 chars): {value[:100]}...")
                else:
                    print(  # noqa: T201f"{key} type: {type(value)}")
    print(  # noqa: T201)

    # Test the first few ComfyUI parsers
    print(  # noqa: T201"🧪 TESTING COMFYUI PARSERS:")
    print(  # noqa: T201"-" * 30)

    for i, parser_data in enumerate(comfyui_parsers[:3]):  # Test first 3
        parser_name = parser_data.get("parser_name", "Unknown")
        priority = parser_data.get("priority", 0)
        print(  # noqa: T201f"\n{i + 1}. {parser_name} (priority {priority}):")

        detection_rules = parser_data.get("detection_rules", [])
        print(  # noqa: T201f"   Detection rules: {len(detection_rules)}")

        all_pass = True
        for j, rule in enumerate(detection_rules):
            try:
                result = engine.rule_evaluator.evaluate_rule(rule, context)
                status = "✅" if result else "❌"
                print(  # noqa: T201
                    f"   Rule {j + 1}: {status} {result} - {rule.get('comment', 'No comment')}"
                )
                if not result:
                    all_pass = False
            except Exception as e:
                print(  # noqa: T201f"   Rule {j + 1}: 💥 Error: {e}")
                all_pass = False

        print(  # noqa: T201f"   Overall match: {'✅' if all_pass else '❌'} {all_pass}")

        if all_pass:
            print(  # noqa: T201"   🎉 This parser should match!")
            break

    print(  # noqa: T201)

    # Test overall detection
    print(  # noqa: T201"🎯 OVERALL DETECTION:")
    print(  # noqa: T201"-" * 20)
    result = engine.get_parser_for_file(test_file)
    if result:
        print(  # noqa: T201f"✅ Enhanced detection succeeded: {result.get('tool', 'Unknown')}")
    else:
        print(  # noqa: T201"❌ Enhanced detection failed - will fall back to vendored SDPR")

    return result is not None


if __name__ == "__main__":
    success = debug_comfyui_detection()
    print(  # noqa: T201f"\n{'🎉 SUCCESS' if success else '❌ NEEDS INVESTIGATION'}")
    sys.exit(0 if success else 1)
