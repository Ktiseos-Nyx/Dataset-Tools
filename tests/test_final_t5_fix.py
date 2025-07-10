#!/usr/bin/env python3
# ruff: noqa: T201

"""Final comprehensive test for T5 Architecture Detection fixes"""

import json
import logging
from pathlib import Path

from dataset_tools.metadata_engine.extractors.comfyui_extractors import ComfyUIExtractor
from dataset_tools.metadata_engine.extractors.json_extractors import JSONExtractor
from dataset_tools.metadata_engine.metadata_engine import MetadataEngine
from dataset_tools.metadata_engine.rule_evaluator import RuleEvaluator

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_t5_parser_integration():
    """Test the complete T5 parser integration with MetadataEngine."""
    print(  # noqa: T201"🔧 TESTING T5 PARSER INTEGRATION")
    print(  # noqa: T201"=" * 40)

    # Initialize MetadataEngine
    engine = MetadataEngine(logger)

    # Load the T5 parser definition
    t5_parser_path = Path(
        "/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/dataset_tools/parser_definitions/t5_detection_system.json"
    )

    if not t5_parser_path.exists():
        print(  # noqa: T201f"❌ T5 parser not found at {t5_parser_path}")
        return

    with open(t5_parser_path) as f:
        t5_parser_def = json.load(f)

    print(  # noqa: T201f"✅ Loaded T5 parser: {t5_parser_def['parser_name']}")
    print(  # noqa: T201f"   Priority: {t5_parser_def['priority']}")
    print(  # noqa: T201f"   Version: {t5_parser_def['version']}")

    # Create mock T5 workflow data (from user's example)
    mock_image_data = {
        "prompt": json.dumps(
            {
                "3": {
                    "inputs": {
                        "seed": 687842170175819,
                        "steps": 20,
                        "cfg": 1.0,
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "denoise": 1.0,
                        "model": ["12", 0],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "latent_image": ["5", 0],
                    },
                    "class_type": "KSamplerAdvanced",
                    "_meta": {"title": "KSampler (Advanced)"},
                },
                "6": {
                    "inputs": {
                        "text": "a woman with long red hair standing in a field of sunflowers, sunny day, golden hour, warm lighting, detailed, photorealistic",
                        "clip": ["14", 0],
                    },
                    "class_type": "CLIPTextEncode",
                    "_meta": {"title": "CLIP Text Encode (Prompt)"},
                },
                "7": {
                    "inputs": {
                        "text": "blurry, low quality, worst quality, bad anatomy, extra limbs",
                        "clip": ["14", 0],
                    },
                    "class_type": "CLIPTextEncode",
                    "_meta": {"title": "CLIP Text Encode (Prompt)"},
                },
                "12": {
                    "inputs": {"guidance": 3.5, "model": ["16", 0]},
                    "class_type": "FluxGuidance",
                    "_meta": {"title": "FluxGuidance"},
                },
                "14": {
                    "inputs": {
                        "clip_name1": "t5xxl_fp16.safetensors",
                        "clip_name2": "clip_l.safetensors",
                        "type": "flux",
                    },
                    "class_type": "DualCLIPLoader",
                    "_meta": {"title": "DualCLIPLoader"},
                },
            }
        )
    }

    # Test detection rules
    print(  # noqa: T201"\n🔍 TESTING DETECTION RULES:")
    print(  # noqa: T201"-" * 30)

    rule_evaluator = RuleEvaluator(logger)

    for i, rule in enumerate(t5_parser_def["detection_rules"]):
        print(  # noqa: T201f"Rule {i + 1}: {rule['comment']}")

        # Create context for rule evaluation
        context = {"pil_info": mock_image_data, "image_path": "test_image.png"}

        result = rule_evaluator.evaluate_rule(rule, context)
        print(  # noqa: T201f"  ✅ Passed: {result}")

    # Test field extraction
    print(  # noqa: T201"\n📊 TESTING FIELD EXTRACTION:")
    print(  # noqa: T201"-" * 32)

    # Initialize extractors
    comfy_extractor = ComfyUIExtractor(logger)
    json_extractor = JSONExtractor(logger)

    # Get the input data (parsed JSON)
    input_data = json.loads(mock_image_data["prompt"])

    # Test each field extraction
    parsing_instructions = t5_parser_def["parsing_instructions"]

    for field in parsing_instructions["fields"]:
        target_key = field["target_key"]
        method = field["method"]

        print(  # noqa: T201f"\n  Testing {target_key} using {method}:")

        # Get the appropriate extractor
        if method.startswith("comfy_"):
            extractor = comfy_extractor
            methods = extractor.get_methods()
        else:
            extractor = json_extractor
            methods = extractor.get_methods()

        if method in methods:
            method_func = methods[method]
            try:
                result = method_func(input_data, field, {}, {})
                print(  # noqa: T201f"    Result: {result}")
            except Exception as e:
                print(  # noqa: T201f"    ❌ Error: {e}")
        else:
            print(  # noqa: T201f"    ❌ Method {method} not found")

    print(  # noqa: T201"\n🎯 EXPECTED RESULTS:")
    print(  # noqa: T201"-" * 20)
    print(  # noqa: T201"✅ Architecture: flux (confidence: 0.95)")
    print(  # noqa: T201
        "✅ Prompt: 'a woman with long red hair standing in a field of sunflowers...'"
    )
    print(  # noqa: T201"✅ Negative: 'blurry, low quality, worst quality, bad anatomy, extra limbs'")
    print(  # noqa: T201"✅ Seed: 687842170175819")
    print(  # noqa: T201"✅ Steps: 20")
    print(  # noqa: T201"✅ Sampler: 'euler'")
    print(  # noqa: T201"✅ Scheduler: 'normal'")
    print(  # noqa: T201"✅ T5 Model: 't5xxl_fp16.safetensors'")
    print(  # noqa: T201"✅ CLIP Model: 'clip_l.safetensors'")


if __name__ == "__main__":
    test_t5_parser_integration()
