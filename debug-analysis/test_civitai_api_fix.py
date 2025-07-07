#!/usr/bin/env python3
# ruff: noqa: T201

"""Test CivitAI API detection fix - ensure it doesn't over-match regular A1111 files"""

import re


def test_civitai_api_detection():
    """Test the updated CivitAI API detection rules."""
    print(  # noqa: T201"🔧 TESTING CIVITAI API DETECTION FIX")
    print(  # noqa: T201"=" * 40)

    # Test Case 1: User's problematic file (should NOT match CivitAI API)
    print(  # noqa: T201"1. Testing user's file (should NOT be CivitAI API):")
    user_content = """xtrvgnc, hrtdrp, SteepSlopeTiddies, highres, vibrant, pastel_colours
Negative prompt: ((painting, drawing, sketch, ai-generated, cartoon, anime, render, cgi, cg, manga, 3d, pencil))
Steps: 30, Sampler: dpmpp_2m_sde_gpu, CFG scale: 4.0, Seed: 1423235703, Size: 768x1216, Model: SDXL_Pony\\Myrij_-_α.safetensors, Model hash: 174381e92161"""

    # Test Rule 1 (A1111 parameters)
    rule1_patterns = ["Steps:", "Sampler:", "CFG scale:", "Seed:", "Model:"]
    rule1_matches = all(pattern in user_content for pattern in rule1_patterns)
    print(  # noqa: T201f"   Rule 1 (A1111 parameters): {'✅ PASS' if rule1_matches else '❌ FAIL'}")

    # Test Rule 2 (CivitAI API indicators) - OLD patterns
    old_patterns = ["illustrious", "pony", "ponydiffusion", "autismmix"]
    old_rule2_matches = any(
        pattern.lower() in user_content.lower() for pattern in old_patterns
    )
    print(  # noqa: T201
        f"   Rule 2 OLD (broad patterns): {'❌ WOULD MATCH' if old_rule2_matches else '✅ WOULD NOT MATCH'}"
    )

    # Test Rule 2 (CivitAI API indicators) - NEW patterns
    new_patterns = [
        r"Model: \d{5,7}\.safetensors",
        r"Model: \d{5,7}\.ckpt",
        r"civitai\.com",
        r"api\.civitai",
        "CivitAI API",
        r"inference\.civitai",
        r"training\.civitai",
        r"Version: \d+\.\d+\.\d+",
        "API Key:",
        "Request ID:",
        "Job ID:",
    ]
    new_rule2_matches = any(
        re.search(pattern, user_content, re.IGNORECASE) for pattern in new_patterns
    )
    print(  # noqa: T201
        f"   Rule 2 NEW (specific API indicators): {'❌ MATCH' if new_rule2_matches else '✅ NO MATCH'}"
    )

    overall_match = rule1_matches and new_rule2_matches
    print(  # noqa: T201
        f"   Overall CivitAI API detection: {'❌ WOULD MATCH' if overall_match else '✅ WOULD NOT MATCH'}"
    )

    if not overall_match:
        print(  # noqa: T201"   ✅ SUCCESS: User's file will NOT be detected as CivitAI API!")
    else:
        print(  # noqa: T201"   ❌ FAIL: User's file would still be detected as CivitAI API")

    # Test Case 2: Actual CivitAI API file (should match)
    print(  # noqa: T201"\n2. Testing actual CivitAI API file (should match):")
    api_content = """beautiful landscape, detailed, masterpiece
Negative prompt: low quality, blurry
Steps: 25, Sampler: euler, CFG scale: 7.0, Seed: 123456, Size: 512x512, Model: 287520.safetensors, Model hash: abc123def456, Version: 1.2.3, API Key: sk_1234567890abcdef, Request ID: req_abc123"""

    rule1_api = all(pattern in api_content for pattern in rule1_patterns)
    rule2_api = any(
        re.search(pattern, api_content, re.IGNORECASE) for pattern in new_patterns
    )
    api_match = rule1_api and rule2_api

    print(  # noqa: T201f"   Rule 1 (A1111 parameters): {'✅ PASS' if rule1_api else '❌ FAIL'}")
    print(  # noqa: T201f"   Rule 2 (API indicators): {'✅ PASS' if rule2_api else '❌ FAIL'}")
    print(  # noqa: T201
        f"   Overall CivitAI API detection: {'✅ MATCH' if api_match else '❌ NO MATCH'}"
    )

    if api_match:
        print(  # noqa: T201"   ✅ SUCCESS: Real API file correctly detected!")
    else:
        print(  # noqa: T201"   ❌ FAIL: Real API file not detected")

    # Test Case 3: Numbered model file (should match)
    print(  # noqa: T201"\n3. Testing numbered model file (should match):")
    numbered_content = """amazing artwork, high quality
Negative prompt: bad quality
Steps: 20, Sampler: dpm_2, CFG scale: 6.5, Seed: 987654, Size: 1024x1024, Model: 445566.safetensors, Model hash: xyz789"""

    rule1_num = all(pattern in numbered_content for pattern in rule1_patterns)
    rule2_num = any(
        re.search(pattern, numbered_content, re.IGNORECASE) for pattern in new_patterns
    )
    num_match = rule1_num and rule2_num

    print(  # noqa: T201f"   Rule 1 (A1111 parameters): {'✅ PASS' if rule1_num else '❌ FAIL'}")
    print(  # noqa: T201f"   Rule 2 (numbered model): {'✅ PASS' if rule2_num else '❌ FAIL'}")
    print(  # noqa: T201
        f"   Overall CivitAI API detection: {'✅ MATCH' if num_match else '❌ NO MATCH'}"
    )

    # Test Case 4: Regular A1111 with popular model name (should NOT match)
    print(  # noqa: T201"\n4. Testing regular A1111 with popular model (should NOT match):")
    regular_content = """cute anime girl, detailed
Negative prompt: ugly, bad anatomy
Steps: 28, Sampler: euler_a, CFG scale: 7.5, Seed: 555666, Size: 768x768, Model: anythingv5.safetensors, Model hash: def456ghi"""

    rule1_reg = all(pattern in regular_content for pattern in rule1_patterns)
    rule2_reg = any(
        re.search(pattern, regular_content, re.IGNORECASE) for pattern in new_patterns
    )
    reg_match = rule1_reg and rule2_reg

    print(  # noqa: T201f"   Rule 1 (A1111 parameters): {'✅ PASS' if rule1_reg else '❌ FAIL'}")
    print(  # noqa: T201
        f"   Rule 2 (API indicators): {'✅ NO MATCH' if not rule2_reg else '❌ MATCH'}"
    )
    print(  # noqa: T201
        f"   Overall CivitAI API detection: {'✅ NO MATCH' if not reg_match else '❌ MATCH'}"
    )

    print(  # noqa: T201"\n🎯 SUMMARY:")
    print(  # noqa: T201"-" * 12)

    test_results = [
        ("User's problematic file", not overall_match),
        ("Real API file", api_match),
        ("Numbered model file", num_match),
        ("Regular A1111 file", not reg_match),
    ]

    passed_tests = sum(1 for _, passed in test_results if passed)
    total_tests = len(test_results)

    print(  # noqa: T201f"✅ Passed: {passed_tests}/{total_tests} tests")

    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(  # noqa: T201f"   {test_name}: {status}")

    if passed_tests == total_tests:
        print(  # noqa: T201"\n🎉 All tests passed! CivitAI API detection is now more accurate!")
        print(  # noqa: T201"✅ Regular A1111 files won't be misidentified as CivitAI API")
        print(  # noqa: T201"✅ Real API files will still be correctly detected")
    else:
        print(  # noqa: T201
            f"\n❌ {total_tests - passed_tests} test(s) failed - detection rules need refinement"
        )


if __name__ == "__main__":
    test_civitai_api_detection()
