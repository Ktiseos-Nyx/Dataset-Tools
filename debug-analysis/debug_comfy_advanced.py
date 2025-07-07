#!/usr/bin/env python3
# ruff: noqa: T201

"""Debug advanced ComfyUI workflow parsing to fix Universal Parser issues."""

import json
import logging
from pathlib import Path

from PIL import Image

from dataset_tools.metadata_engine.extractors.comfyui_extractors import ComfyUIExtractor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def debug_advanced_comfyui():
    """Debug the advanced ComfyUI image that's failing."""
    print(  # noqa: T201"🔍 DEBUGGING ADVANCED COMFYUI WORKFLOW")
    print(  # noqa: T201"=" * 50)

    # Load the problematic image
    image_path = "/Users/duskfall/Downloads/Metadata Samples/872676588544625334.png"
    img = Image.open(image_path)

    print(  # noqa: T201f"Image: {Path(image_path).name}")
    print(  # noqa: T201f"PIL info keys: {list(img.info.keys())}")

    if "prompt" in img.info:
        prompt_data = json.loads(img.info["prompt"])
        print(  # noqa: T201f"Prompt data: {len(prompt_data)} nodes")

        # Show node types
        node_types = {}
        for node_id, node_data in prompt_data.items():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "unknown")
                node_types[class_type] = node_types.get(class_type, 0) + 1

        print(  # noqa: T201f"Node types: {dict(sorted(node_types.items()))}")
        print(  # noqa: T201)

        # Test the Universal Parser extraction methods
        extractor = ComfyUIExtractor(logger)

        print(  # noqa: T201"🧪 TESTING UNIVERSAL PARSER METHODS:")
        print(  # noqa: T201"-" * 40)

        # Test 1: Find text from main sampler input (positive)
        print(  # noqa: T201"1. Testing positive prompt extraction:")
        method_def = {
            "sampler_node_types": [
                "KSampler",
                "KSamplerAdvanced",
                "SamplerCustomAdvanced",
            ],
            "positive_input_name": "positive",
            "text_input_name_in_encoder": "text",
            "text_encoder_node_types": ["CLIPTextEncode", "BNK_CLIPTextEncodeAdvanced"],
            "target_key": "prompt",
        }
        positive_result = extractor._find_text_from_main_sampler_input(
            prompt_data, method_def, {}, {}
        )
        print(  # noqa: T201f"   Result: '{positive_result}'")

        # Test 2: Find text from main sampler input (negative)
        print(  # noqa: T201"2. Testing negative prompt extraction:")
        method_def["target_key"] = "negative_prompt"
        negative_result = extractor._find_text_from_main_sampler_input(
            prompt_data, method_def, {}, {}
        )
        print(  # noqa: T201f"   Result: '{negative_result}'")

        # Test 3: Parameter extraction
        print(  # noqa: T201"3. Testing parameter extraction:")

        test_params = [
            ("seed", "integer"),
            ("steps", "integer"),
            ("cfg", "float"),
            ("sampler_name", "string"),
        ]

        for param_name, param_type in test_params:
            method_def = {
                "sampler_node_types": [
                    "KSampler",
                    "KSamplerAdvanced",
                    "SamplerCustomAdvanced",
                ],
                "input_key": param_name,
                "value_type": param_type,
            }
            result = extractor._find_input_of_main_sampler(
                prompt_data, method_def, {}, {}
            )
            print(  # noqa: T201f"   {param_name}: {result} ({type(result)})")

        # Test 4: Examine the actual sampler nodes
        print(  # noqa: T201"\n4. Examining sampler nodes:")
        for node_id, node_data in prompt_data.items():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "")
                if any(sampler in class_type for sampler in ["KSampler", "Sampler"]):
                    print(  # noqa: T201f"   Node {node_id} ({class_type}):")
                    inputs = node_data.get("inputs", {})
                    print(  # noqa: T201f"     Inputs: {list(inputs.keys())}")
                    for key, value in inputs.items():
                        if isinstance(value, (str, int, float)):
                            print(  # noqa: T201f"       {key}: {value}")
                        elif isinstance(value, list):
                            print(  # noqa: T201f"       {key}: connection to node {value[0]}")

        # Test 5: Examine text encoding nodes
        print(  # noqa: T201"\n5. Examining text encoding nodes:")
        for node_id, node_data in prompt_data.items():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "")
                if "TextEncode" in class_type or "CLIP" in class_type:
                    print(  # noqa: T201f"   Node {node_id} ({class_type}):")
                    inputs = node_data.get("inputs", {})
                    if "text" in inputs:
                        text = inputs["text"]
                        print(  # noqa: T201f"     Text: '{text[:100]}...' ({len(text)} chars)")
                    widgets = node_data.get("widgets_values", [])
                    if widgets:
                        print(  # noqa: T201f"     Widgets: {widgets[:2]}...")


if __name__ == "__main__":
    debug_advanced_comfyui()
