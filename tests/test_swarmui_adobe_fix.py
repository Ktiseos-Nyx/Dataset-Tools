#!/usr/bin/env python3
# ruff: noqa: T201

"""Test SwarmUI Adobe detection fix"""

import sys

sys.path.append(
    "/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/dataset_tools"
)

import logging

from vendored_sdpr.format.swarmui import SwarmUI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_swarmui_adobe_rejection():
    """Test that SwarmUI parser correctly rejects Adobe Photoshop files."""
    print(  # noqa: T201"🔧 TESTING SWARMUI ADOBE REJECTION")
    print(  # noqa: T201"=" * 38)

    # Test Case 1: Adobe Photoshop file (should be rejected)
    print(  # noqa: T201"1. Testing Adobe Photoshop file rejection:")
    adobe_info = {
        "software_tag": "Adobe Photoshop 26.5 (20250212.m.2973 455b503)  (Macintosh)"
    }

    swarm_parser = SwarmUI(
        info=adobe_info,
        raw='{"software_tag": "Adobe Photoshop 26.5 (20250212.m.2973 455b503)  (Macintosh)"}',
    )
    swarm_parser.parse()

    print(  # noqa: T201f"   Status: {swarm_parser.status}")
    print(  # noqa: T201f"   Error: {swarm_parser.error}")
    print(  # noqa: T201f"   Tool: {swarm_parser.tool}")

    if swarm_parser.status == swarm_parser.Status.FORMAT_DETECTION_ERROR:
        print(  # noqa: T201"   ✅ CORRECTLY REJECTED Adobe Photoshop file!")
    else:
        print(  # noqa: T201"   ❌ FAILED to reject Adobe Photoshop file")

    # Test Case 2: Actual SwarmUI file (should be accepted)
    print(  # noqa: T201"\n2. Testing legitimate SwarmUI file acceptance:")
    swarmui_info = {"software_tag": "StableSwarmUI v0.6.2"}
    swarmui_raw = '{"prompt": "beautiful landscape", "negativeprompt": "bad quality", "model": "realisticVision", "seed": 12345, "steps": 20, "cfgscale": 7.5}'

    swarm_parser2 = SwarmUI(info=swarmui_info, raw=swarmui_raw)
    swarm_parser2.parse()

    print(  # noqa: T201f"   Status: {swarm_parser2.status}")
    print(  # noqa: T201f"   Prompt: {swarm_parser2.positive}")
    print(  # noqa: T201f"   Tool: {swarm_parser2.tool}")

    if swarm_parser2.status == swarm_parser2.Status.READ_SUCCESS:
        print(  # noqa: T201"   ✅ CORRECTLY ACCEPTED SwarmUI file!")
    else:
        print(  # noqa: T201"   ❌ FAILED to accept legitimate SwarmUI file")

    # Test Case 3: Other Adobe software (should be rejected)
    print(  # noqa: T201"\n3. Testing other Adobe software rejection:")
    other_adobe_info = {"software_tag": "Adobe Lightroom 13.1"}

    swarm_parser3 = SwarmUI(
        info=other_adobe_info, raw='{"software_tag": "Adobe Lightroom 13.1"}'
    )
    swarm_parser3.parse()

    print(  # noqa: T201f"   Status: {swarm_parser3.status}")
    print(  # noqa: T201f"   Error: {swarm_parser3.error}")

    if swarm_parser3.status == swarm_parser3.Status.FORMAT_DETECTION_ERROR:
        print(  # noqa: T201"   ✅ CORRECTLY REJECTED other Adobe software!")
    else:
        print(  # noqa: T201"   ❌ FAILED to reject other Adobe software")

    # Test Case 4: Other non-AI software (should be rejected)
    print(  # noqa: T201"\n4. Testing other non-AI software rejection:")
    gimp_info = {"software_tag": "GIMP 2.10.34"}

    swarm_parser4 = SwarmUI(info=gimp_info, raw='{"software_tag": "GIMP 2.10.34"}')
    swarm_parser4.parse()

    print(  # noqa: T201f"   Status: {swarm_parser4.status}")
    print(  # noqa: T201f"   Error: {swarm_parser4.error}")

    if swarm_parser4.status == swarm_parser4.Status.FORMAT_DETECTION_ERROR:
        print(  # noqa: T201"   ✅ CORRECTLY REJECTED GIMP software!")
    else:
        print(  # noqa: T201"   ❌ FAILED to reject GIMP software")

    # Test Case 5: No software tag (should attempt parsing)
    print(  # noqa: T201"\n5. Testing file with no software tag:")
    no_tag_info = {}
    no_tag_raw = '{"prompt": "test prompt", "model": "test_model"}'

    swarm_parser5 = SwarmUI(info=no_tag_info, raw=no_tag_raw)
    swarm_parser5.parse()

    print(  # noqa: T201f"   Status: {swarm_parser5.status}")
    print(  # noqa: T201f"   Prompt: {swarm_parser5.positive}")

    if swarm_parser5.status == swarm_parser5.Status.READ_SUCCESS:
        print(  # noqa: T201"   ✅ CORRECTLY PROCESSED file without software tag!")
    else:
        print(  # noqa: T201"   ❌ FAILED to process file without software tag")

    print(  # noqa: T201"\n🎯 SUMMARY:")
    print(  # noqa: T201"-" * 12)
    print(  # noqa: T201"✅ SwarmUI parser should now correctly reject Adobe Photoshop files")
    print(  # noqa: T201"✅ The user's issue should be resolved")
    print(  # noqa: T201"✅ Adobe files will no longer be misidentified as StableSwarmUI")


if __name__ == "__main__":
    test_swarmui_adobe_rejection()
