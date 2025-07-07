#!/usr/bin/env python3

"""Test the ComfyUI extraction methods directly using the new FieldExtractor."""

import argparse
import json
import sys
from pathlib import Path

# Add the project root to the Python path to allow importing dataset_tools
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dataset_tools.logger import get_logger
from dataset_tools.metadata_engine.field_extraction import FieldExtractor


def test_extraction(file_path: str):
    """Test the extraction methods using a real workflow file."""
    print(f"🔧 TESTING COMFYUI EXTRACTION FOR: {file_path}")
    print("=" * (38 + len(file_path)))

    logger = get_logger("TestExtraction")
    extractor = FieldExtractor(logger)

    try:
        with open(file_path) as f:
            workflow_data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"❌ Error reading or parsing workflow file: {e}")
        return

    # The context data would normally be prepared by the ContextDataPreparer
    context_data = {"parsed_root_json_object": workflow_data}

    print("1. Testing positive prompt extraction:")
    positive_field_def = {
        "target_key": "prompt",
        "method": "find_text_from_main_sampler_input",
        "method_params": {
            "positive_input_name": "positive",
            "sampler_node_types": [
                "KSampler",
                "KSamplerAdvanced",
                "SamplerCustomAdvanced",
            ],
            "text_encoder_node_types": [
                "CLIPTextEncode",
                "CLIPTextEncodeSD3",
                "T5TextEncode",
                "BNK_CLIPTextEncodeAdvanced",
                "CLIPTextEncodeAdvanced",
            ],
        },
    }

    positive_result = extractor.extract_field(positive_field_def, workflow_data, context_data, {})
    print(f"   Result: '{positive_result}'")

    if positive_result:
        print("   ✅ SUCCESS: Positive prompt extracted.")
    else:
        print("   ❌ FAILED: Positive prompt extraction failed.")

    print("\n2. Testing negative prompt extraction:")
    negative_field_def = {
        "target_key": "negative_prompt",
        "method": "find_text_from_main_sampler_input",
        "method_params": {
            "negative_input_name": "negative",
            "sampler_node_types": [
                "KSampler",
                "KSamplerAdvanced",
                "SamplerCustomAdvanced",
            ],
            "text_encoder_node_types": [
                "CLIPTextEncode",
                "CLIPTextEncodeSD3",
                "T5TextEncode",
                "BNK_CLIPTextEncodeAdvanced",
                "CLIPTextEncodeAdvanced",
            ],
        },
    }

    negative_result = extractor.extract_field(negative_field_def, workflow_data, context_data, {})
    print(f"   Result: '{negative_result}'")

    if negative_result:
        print("   ✅ SUCCESS: Negative prompt extracted.")
    else:
        print("   ❌ FAILED: Negative prompt extraction failed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test ComfyUI prompt extraction from a workflow JSON file using the new FieldExtractor."
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="The absolute path to the ComfyUI workflow JSON file.",
    )
    args = parser.parse_args()

    test_extraction(args.file_path)
