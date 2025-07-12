# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""Metadata parser tests"""

import json
from pathlib import Path

import pytest

from dataset_tools.metadata_parser import parse_metadata

# Get the directory of the current test file
TEST_DIR = Path(__file__).parent
# Construct the path to the data directory
DATA_DIR = TEST_DIR / "data"

# Get a list of all files in the data directory
all_files = [f for f in DATA_DIR.iterdir() if f.is_file()]


@pytest.mark.parametrize("file_path", all_files)
def test_metadata_parser(file_path):
    """Test that the metadata parser can handle various file types."""
    metadata = parse_metadata(str(file_path))
    assert metadata


def test_for_secrets_in_workflow():
    """Test that the workflow file does not contain any secrets."""
    file_path = DATA_DIR / "Workflow_Animeflux.json"
    with open(file_path) as f:
        workflow = json.load(f)

    # Check for common secret keys
    assert "api_key" not in workflow
    assert "hf_token" not in workflow
    assert "secret" not in workflow


def test_generic_json_parser():
    """Test that a simple JSON file is parsed by the generic JSON parser."""
    file_path = DATA_DIR / "simple_test.json"
    metadata = parse_metadata(str(file_path))
    assert metadata
    assert metadata.get("metadata_info_section", {}).get("Detected Tool") == "JSON Parser"
    assert metadata.get("metadata_info_section", {}).get("format") == "Generic JSON"
    assert metadata.get("raw_tool_specific_data_section", {}).get("raw_json_content") is not None


def test_comfyui_animeflux_workflow_parsing():
    """Test that Workflow_Animeflux.json is correctly parsed as a ComfyUI workflow."""
    file_path = DATA_DIR / "Workflow_Animeflux.json"
    metadata = parse_metadata(str(file_path))
    assert metadata
    assert metadata.get("metadata_info_section", {}).get("Detected Tool") == "ComfyUI"
    assert (
        metadata.get("metadata_info_section", {}).get("format") == "ComfyUI Workflow (Generic Workflow Traversal)"
        or metadata.get("metadata_info_section", {}).get("format") == "ComfyUI Workflow (Civitai extraMetadata)"
    )
    assert metadata.get("raw_tool_specific_data_section", {}).get("workflow") is not None
