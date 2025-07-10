#!/usr/bin/env python3
# ruff: noqa: T201

"""Test Easy Diffusion detection fix - ensure it doesn't match non-Easy Diffusion files"""

import sys

sys.path.append(
    "/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/dataset_tools"
)

import logging

from vendored_sdpr.format.easydiffusion import EasyDiffusion

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_easydiffusion_detection():
    """Test that Easy Diffusion parser correctly rejects non-Easy Diffusion files."""
    print(  # noqa: T201"🔧 TESTING EASY DIFFUSION DETECTION FIX")
    print(  # noqa: T201"=" * 43)

    # Test Case 1: Celsys Studio Tool file (should be rejected)
    print(  # noqa: T201"1. Testing Celsys Studio Tool file rejection:")
    celsys_info = {"software_tag": "Celsys Studio Tool"}
    celsys_raw = '{"width": 1224, "height": 2048, "some_data": "value"}'

    ed_parser = EasyDiffusion(info=celsys_info, raw=celsys_raw)
    ed_parser.parse()

    print(  # noqa: T201f"   Status: {ed_parser.status}")
    print(  # noqa: T201f"   Error: {ed_parser.error}")

    if ed_parser.status == ed_parser.Status.FORMAT_DETECTION_ERROR:
        print(  # noqa: T201"   ✅ CORRECTLY REJECTED Celsys Studio Tool file!")
    else:
        print(  # noqa: T201"   ❌ FAILED to reject Celsys Studio Tool file")

    # Test Case 2: Adobe Photoshop file (should be rejected)
    print(  # noqa: T201"\n2. Testing Adobe Photoshop file rejection:")
    adobe_info = {"software_tag": "Adobe Photoshop 26.5"}
    adobe_raw = '{"width": 1024, "height": 1024, "format": "PNG"}'

    ed_parser2 = EasyDiffusion(info=adobe_info, raw=adobe_raw)
    ed_parser2.parse()

    print(  # noqa: T201f"   Status: {ed_parser2.status}")
    print(  # noqa: T201f"   Error: {ed_parser2.error}")

    if ed_parser2.status == ed_parser2.Status.FORMAT_DETECTION_ERROR:
        print(  # noqa: T201"   ✅ CORRECTLY REJECTED Adobe Photoshop file!")
    else:
        print(  # noqa: T201"   ❌ FAILED to reject Adobe Photoshop file")

    # Test Case 3: File without Easy Diffusion fields (should be rejected)
    print(  # noqa: T201"\n3. Testing file without Easy Diffusion fields:")
    generic_info = {}
    generic_raw = '{"prompt": "test", "seed": 123, "steps": 20, "cfg_scale": 7.0}'  # No ED-specific fields

    ed_parser3 = EasyDiffusion(info=generic_info, raw=generic_raw)
    ed_parser3.parse()

    print(  # noqa: T201f"   Status: {ed_parser3.status}")
    print(  # noqa: T201f"   Error: {ed_parser3.error}")

    if ed_parser3.status == ed_parser3.Status.FORMAT_DETECTION_ERROR:
        print(  # noqa: T201"   ✅ CORRECTLY REJECTED file without Easy Diffusion fields!")
    else:
        print(  # noqa: T201"   ❌ FAILED to reject file without Easy Diffusion fields")

    # Test Case 4: Legitimate Easy Diffusion file (should be accepted)
    print(  # noqa: T201"\n4. Testing legitimate Easy Diffusion file:")
    ed_info = {"software_tag": "Easy Diffusion"}
    ed_raw = '{"prompt": "beautiful landscape", "negative_prompt": "low quality", "num_inference_steps": 25, "guidance_scale": 7.5, "use_stable_diffusion_model": "model.safetensors", "seed": 12345, "width": 512, "height": 512}'

    ed_parser4 = EasyDiffusion(info=ed_info, raw=ed_raw)
    ed_parser4.parse()

    print(  # noqa: T201f"   Status: {ed_parser4.status}")
    print(  # noqa: T201f"   Prompt: {ed_parser4.positive}")

    if ed_parser4.status == ed_parser4.Status.READ_SUCCESS:
        print(  # noqa: T201"   ✅ CORRECTLY ACCEPTED Easy Diffusion file!")
    else:
        print(  # noqa: T201"   ❌ FAILED to accept legitimate Easy Diffusion file")

    # Test Case 5: File with Easy Diffusion fields but no software tag (should be accepted)
    print(  # noqa: T201"\n5. Testing Easy Diffusion file without software tag:")
    no_tag_info = {}
    no_tag_raw = '{"prompt": "artwork", "num_inference_steps": 30, "guidance_scale": 8.0, "seed": 98765}'

    ed_parser5 = EasyDiffusion(info=no_tag_info, raw=no_tag_raw)
    ed_parser5.parse()

    print(  # noqa: T201f"   Status: {ed_parser5.status}")
    print(  # noqa: T201f"   Prompt: {ed_parser5.positive}")

    if ed_parser5.status == ed_parser5.Status.READ_SUCCESS:
        print(  # noqa: T201"   ✅ CORRECTLY ACCEPTED file with Easy Diffusion fields!")
    else:
        print(  # noqa: T201"   ❌ FAILED to accept file with Easy Diffusion fields")

    # Test Case 6: ComfyUI file (should be rejected)
    print(  # noqa: T201"\n6. Testing ComfyUI file rejection:")
    comfy_info = {"software_tag": "ComfyUI"}
    comfy_raw = '{"workflow": {"nodes": []}, "prompt": "test"}'

    ed_parser6 = EasyDiffusion(info=comfy_info, raw=comfy_raw)
    ed_parser6.parse()

    print(  # noqa: T201f"   Status: {ed_parser6.status}")

    if ed_parser6.status == ed_parser6.Status.FORMAT_DETECTION_ERROR:
        print(  # noqa: T201"   ✅ CORRECTLY REJECTED ComfyUI file!")
    else:
        print(  # noqa: T201"   ❌ FAILED to reject ComfyUI file")

    print(  # noqa: T201"\n🎯 SUMMARY:")
    print(  # noqa: T201"-" * 12)

    test_results = [
        (
            "Celsys Studio Tool",
            ed_parser.status == ed_parser.Status.FORMAT_DETECTION_ERROR,
        ),
        (
            "Adobe Photoshop",
            ed_parser2.status == ed_parser2.Status.FORMAT_DETECTION_ERROR,
        ),
        ("No ED fields", ed_parser3.status == ed_parser3.Status.FORMAT_DETECTION_ERROR),
        ("Legitimate ED", ed_parser4.status == ed_parser4.Status.READ_SUCCESS),
        ("ED fields no tag", ed_parser5.status == ed_parser5.Status.READ_SUCCESS),
        ("ComfyUI", ed_parser6.status == ed_parser6.Status.FORMAT_DETECTION_ERROR),
    ]

    passed_tests = sum(1 for _, passed in test_results if passed)
    total_tests = len(test_results)

    print(  # noqa: T201f"✅ Passed: {passed_tests}/{total_tests} tests")

    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(  # noqa: T201f"   {test_name}: {status}")

    if passed_tests == total_tests:
        print(  # noqa: T201"\n🎉 All tests passed! Easy Diffusion detection is now more accurate!")
        print(  # noqa: T201"✅ Celsys Studio Tool files won't be misidentified as Easy Diffusion")
        print(  # noqa: T201"✅ Other non-ED software correctly rejected")
        print(  # noqa: T201"✅ Real Easy Diffusion files still work correctly")
    else:
        print(  # noqa: T201
            f"\n❌ {total_tests - passed_tests} test(s) failed - detection rules need refinement"
        )


if __name__ == "__main__":
    test_easydiffusion_detection()
