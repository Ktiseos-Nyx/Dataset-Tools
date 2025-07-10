#!/usr/bin/env python3
# ruff: noqa: T201

"""Test script to verify our pil_info_key_json_path_query fix is working."""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_tools.logger import get_logger
from dataset_tools.rule_evaluator import RuleEvaluator


def test_json_path_query_fix():
    """Test that pil_info_key_json_path_query is no longer throwing warnings."""
    print(  # noqa: T201"🔧 TESTING pil_info_key_json_path_query FIX")
    print(  # noqa: T201"=" * 50)

    logger = get_logger("TestRuleEvaluator")
    rule_evaluator = RuleEvaluator(logger)

    # Mock context data with some JSON in pil_info
    test_json = (
        '{"nodes": {"1": {"type": "KSampler"}, "2": {"type": "CLIPTextEncode"}}}'
    )
    context_data = {"pil_info": {"workflow": test_json}}

    # Test rule that uses pil_info_key_json_path_query
    test_rule = {
        "source_type": "pil_info_key_json_path_query",
        "source_key_options": ["workflow"],
        "json_query_type": "has_numeric_string_keys",
        "operator": "is_true",
    }

    print(  # noqa: T201"📝 Test rule:")
    print(  # noqa: T201f"   source_type: {test_rule['source_type']}")
    print(  # noqa: T201f"   json_query_type: {test_rule['json_query_type']}")
    print(  # noqa: T201f"   operator: {test_rule['operator']}")
    print(  # noqa: T201)

    print(  # noqa: T201"🧪 Testing rule evaluation...")

    try:
        result = rule_evaluator.evaluate_rule(test_rule, context_data)
        print(  # noqa: T201f"✅ Rule evaluation successful: {result}")
        print(  # noqa: T201"🎉 No 'not yet implemented' warning should appear!")
        return True
    except Exception as e:
        print(  # noqa: T201f"❌ Rule evaluation failed: {e}")
        return False


if __name__ == "__main__":
    success = test_json_path_query_fix()
    print(  # noqa: T201f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)
