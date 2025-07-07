#!/usr/bin/env python3
# ruff: noqa: T201

"""Test Midjourney parser with the new regex extraction methods."""

import sys

sys.path.append(
    "/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/dataset_tools"
)

import logging

from metadata_engine.extractors.regex_extractors import RegexExtractor
from metadata_engine.field_extraction import FieldExtractor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_midjourney_extraction():
    """Test the Midjourney regex extraction methods."""
    print(  # noqa: T201"🔧 TESTING MIDJOURNEY REGEX EXTRACTION METHODS")
    print(  # noqa: T201"=" * 48)

    # Sample Midjourney metadata (typical format)
    midjourney_text = "beautiful landscape with mountains and trees --ar 16:9 --v 6 --stylize 750 --seed 123456 Job ID: abc123-def456"

    # Initialize the regex extractor
    regex_extractor = RegexExtractor(logger)

    print(  # noqa: T201"1. Testing regex_extract_before_pattern (extract prompt):")
    method_def = {"pattern": "(?:\\s--[a-zA-Z]|\\sJob ID:)", "value_type": "string"}

    prompt_result = regex_extractor._extract_before_pattern(
        midjourney_text, method_def, {}, {}
    )
    print(  # noqa: T201f"   Input: {midjourney_text}")
    print(  # noqa: T201f"   Extracted prompt: '{prompt_result}'")

    if (
        prompt_result
        and prompt_result.strip() == "beautiful landscape with mountains and trees"
    ):
        print(  # noqa: T201"   ✅ CORRECTLY extracted prompt!")
    else:
        print(  # noqa: T201"   ❌ FAILED to extract prompt correctly")

    print(  # noqa: T201"\n2. Testing regex_extract_group (extract aspect ratio):")
    method_def = {"pattern": "--ar\\s+([^\\s]+)", "group": 1, "value_type": "string"}

    ar_result = regex_extractor._extract_regex_group(
        midjourney_text, method_def, {}, {}
    )
    print(  # noqa: T201f"   Pattern: {method_def['pattern']}")
    print(  # noqa: T201f"   Extracted aspect ratio: '{ar_result}'")

    if ar_result == "16:9":
        print(  # noqa: T201"   ✅ CORRECTLY extracted aspect ratio!")
    else:
        print(  # noqa: T201"   ❌ FAILED to extract aspect ratio correctly")

    print(  # noqa: T201"\n3. Testing regex_extract_group (extract version):")
    method_def = {"pattern": "--v\\s+([^\\s]+)", "group": 1, "value_type": "string"}

    version_result = regex_extractor._extract_regex_group(
        midjourney_text, method_def, {}, {}
    )
    print(  # noqa: T201f"   Pattern: {method_def['pattern']}")
    print(  # noqa: T201f"   Extracted version: '{version_result}'")

    if version_result == "6":
        print(  # noqa: T201"   ✅ CORRECTLY extracted version!")
    else:
        print(  # noqa: T201"   ❌ FAILED to extract version correctly")

    print(  # noqa: T201"\n4. Testing regex_extract_group (extract stylize):")
    method_def = {"pattern": "--stylize\\s+(\\d+)", "group": 1, "value_type": "integer"}

    stylize_result = regex_extractor._extract_regex_group(
        midjourney_text, method_def, {}, {}
    )
    print(  # noqa: T201f"   Pattern: {method_def['pattern']}")
    print(  # noqa: T201f"   Extracted stylize: {stylize_result}")

    if stylize_result == 750:
        print(  # noqa: T201"   ✅ CORRECTLY extracted stylize value!")
    else:
        print(  # noqa: T201"   ❌ FAILED to extract stylize value correctly")

    print(  # noqa: T201"\n5. Testing regex_extract_group (extract seed):")
    method_def = {"pattern": "--seed\\s+(\\d+)", "group": 1, "value_type": "integer"}

    seed_result = regex_extractor._extract_regex_group(
        midjourney_text, method_def, {}, {}
    )
    print(  # noqa: T201f"   Pattern: {method_def['pattern']}")
    print(  # noqa: T201f"   Extracted seed: {seed_result}")

    if seed_result == 123456:
        print(  # noqa: T201"   ✅ CORRECTLY extracted seed value!")
    else:
        print(  # noqa: T201"   ❌ FAILED to extract seed value correctly")

    print(  # noqa: T201"\n6. Testing regex_extract_group (extract Job ID):")
    method_def = {"pattern": "Job ID:\\s*([\\w-]+)", "group": 1, "value_type": "string"}

    job_id_result = regex_extractor._extract_regex_group(
        midjourney_text, method_def, {}, {}
    )
    print(  # noqa: T201f"   Pattern: {method_def['pattern']}")
    print(  # noqa: T201f"   Extracted Job ID: '{job_id_result}'")

    if job_id_result == "abc123-def456":
        print(  # noqa: T201"   ✅ CORRECTLY extracted Job ID!")
    else:
        print(  # noqa: T201"   ❌ FAILED to extract Job ID correctly")

    print(  # noqa: T201"\n7. Testing FieldExtractor integration:")
    field_extractor = FieldExtractor(logger)

    # Test that the regex methods are registered
    method_def = {
        "method": "regex_extract_before_pattern",
        "pattern": "(?:\\s--[a-zA-Z]|\\sJob ID:)",
        "value_type": "string",
    }

    integrated_result = field_extractor.extract_field(
        method_def, midjourney_text, {}, {}
    )
    print(  # noqa: T201f"   FieldExtractor result: '{integrated_result}'")

    if (
        integrated_result
        and integrated_result.strip() == "beautiful landscape with mountains and trees"
    ):
        print(  # noqa: T201"   ✅ CORRECTLY integrated with FieldExtractor!")
    else:
        print(  # noqa: T201"   ❌ FAILED to integrate with FieldExtractor")

    # Test various method registrations
    print(  # noqa: T201"\n8. Testing method registry:")
    methods = field_extractor._method_registry
    regex_methods = [
        "regex_extract_group",
        "regex_extract_before_pattern",
        "regex_extract_after_pattern",
        "regex_extract_between_patterns",
        "regex_replace_pattern",
        "regex_split_on_pattern",
    ]

    for method_name in regex_methods:
        if method_name in methods:
            print(  # noqa: T201f"   ✅ {method_name} registered")
        else:
            print(  # noqa: T201f"   ❌ {method_name} NOT registered")

    # Summary
    print(  # noqa: T201"\n🎯 SUMMARY:")
    print(  # noqa: T201"-" * 12)

    test_results = [
        (
            "Extract prompt",
            prompt_result
            and prompt_result.strip() == "beautiful landscape with mountains and trees",
        ),
        ("Extract aspect ratio", ar_result == "16:9"),
        ("Extract version", version_result == "6"),
        ("Extract stylize", stylize_result == 750),
        ("Extract seed", seed_result == 123456),
        ("Extract Job ID", job_id_result == "abc123-def456"),
        (
            "FieldExtractor integration",
            integrated_result
            and integrated_result.strip()
            == "beautiful landscape with mountains and trees",
        ),
        ("Method registry", all(method in methods for method in regex_methods)),
    ]

    passed_tests = sum(1 for _, passed in test_results if passed)
    total_tests = len(test_results)

    print(  # noqa: T201f"✅ Passed: {passed_tests}/{total_tests} tests")

    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(  # noqa: T201f"   {test_name}: {status}")

    if passed_tests == total_tests:
        print(  # noqa: T201"\n🎉 All tests passed! Midjourney extraction methods are working!")
        print(  # noqa: T201"✅ RegexExtractor properly integrated")
        print(  # noqa: T201"✅ All regex methods registered in FieldExtractor")
        print(  # noqa: T201"✅ Midjourney parser can now extract prompts and parameters")
    else:
        print(  # noqa: T201
            f"\n❌ {total_tests - passed_tests} test(s) failed - extraction methods need fixes"
        )


if __name__ == "__main__":
    test_midjourney_extraction()
