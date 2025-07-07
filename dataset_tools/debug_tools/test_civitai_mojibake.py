#!/usr/bin/env python3
# ruff: noqa: T201

"""Test CivitAI ComfyUI mojibake handling without external dependencies."""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_civitai_mojibake():
    """Test CivitAI ComfyUI files that have Unicode mojibake in EXIF UserComment."""
    print(  # noqa: T201"🧪 CIVITAI COMFYUI MOJIBAKE TEST")
    print(  # noqa: T201"=" * 32)

    # Test with the ComfyUI JSON workflow file that should have mojibake
    test_file = "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_08965_.jpeg"

    if not Path(test_file).exists():
        print(  # noqa: T201f"❌ Test file not found: {Path(test_file).name}")
        return

    print(  # noqa: T201f"📁 Testing: {Path(test_file).name}")

    # Test context preparation first
    print(  # noqa: T201"\n1️⃣ CONTEXT PREPARATION")
    print(  # noqa: T201"-" * 22)

    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

        preparer = ContextDataPreparer()
        context = preparer.prepare_context(test_file)

        if not context:
            print(  # noqa: T201"❌ Context preparation failed")
            return

        print(  # noqa: T201f"✅ Context prepared with {len(context)} keys")

        # Check UserComment extraction
        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            print(  # noqa: T201f"✅ UserComment extracted: {len(user_comment)} characters")

            # Check if it looks like ComfyUI JSON
            if user_comment.startswith('{"') and '"prompt":' in user_comment:
                print(  # noqa: T201"   Format: ComfyUI JSON workflow")
                try:
                    import json

                    workflow_data = json.loads(user_comment)
                    node_count = len(workflow_data.get("prompt", {}))
                    print(  # noqa: T201f"   Nodes: {node_count}")

                    # Check for ComfyUI indicators
                    workflow_str = json.dumps(workflow_data)
                    indicators = []
                    if "KSampler" in workflow_str:
                        indicators.append("KSampler")
                    if "CLIPTextEncode" in workflow_str:
                        indicators.append("CLIPTextEncode")
                    if "class_type" in workflow_str:
                        indicators.append("class_type")

                    if indicators:
                        print(  # noqa: T201f"   ComfyUI indicators: {indicators}")
                    else:
                        print(  # noqa: T201"   ⚠️ No ComfyUI indicators found")

                except json.JSONDecodeError as e:
                    print(  # noqa: T201f"   ❌ JSON parse failed: {e}")
                    print(  # noqa: T201f"   Raw preview: {user_comment[:100]}...")
            else:
                print(  # noqa: T201"   Format: Non-ComfyUI data")
                print(  # noqa: T201f"   Preview: {user_comment[:100]}...")
        else:
            print(  # noqa: T201"❌ No UserComment extracted")

        # Check for structured ComfyUI workflow JSON
        comfyui_workflow = context.get("comfyui_workflow_json")
        if comfyui_workflow:
            print(  # noqa: T201
                f"✅ Structured ComfyUI workflow parsed: {len(comfyui_workflow)} keys"
            )
        else:
            print(  # noqa: T201"❌ No structured ComfyUI workflow found")

    except Exception as e:
        print(  # noqa: T201f"❌ Context preparation error: {e}")
        import traceback

        traceback.print_exc()
        return

    # Test MetadataEngine detection
    print(  # noqa: T201"\n2️⃣ METADATA ENGINE")
    print(  # noqa: T201"-" * 17)

    try:
        from dataset_tools.metadata_engine import MetadataEngine

        parser_definitions_path = os.path.join(
            os.path.dirname(__file__), "parser_definitions"
        )
        engine = MetadataEngine(parser_definitions_path)

        print(  # noqa: T201"🔍 Running MetadataEngine...")
        result = engine.get_parser_for_file(test_file)

        if result:
            print(  # noqa: T201f"✅ SUCCESS: {type(result)}")
            if isinstance(result, dict):
                tool = result.get("tool", "Unknown")
                print(  # noqa: T201f"   Tool: {tool}")

                # Check if it's correctly identified as ComfyUI-related
                if "comfyui" in tool.lower() or "comfy" in tool.lower():
                    print(  # noqa: T201"   ✅ Correctly identified as ComfyUI")
                else:
                    print(  # noqa: T201f"   ⚠️ Unexpected tool identification: {tool}")

                # Check for workflow extraction
                if "workflow" in result or "prompt" in result:
                    print(  # noqa: T201"   ✅ Workflow/prompt data extracted")
                else:
                    print(  # noqa: T201"   ⚠️ No workflow/prompt data found")

            else:
                print(  # noqa: T201f"   Parser instance: {result}")
        else:
            print(  # noqa: T201"❌ FAILED: MetadataEngine returned None")
            print(  # noqa: T201"   This suggests detection rules failed")

    except Exception as e:
        print(  # noqa: T201f"❌ MetadataEngine error: {e}")
        import traceback

        traceback.print_exc()

    print(  # noqa: T201"\n🎯 EXPECTED BEHAVIOR:")
    print(  # noqa: T201"   • Should extract large ComfyUI JSON from EXIF UserComment")
    print(  # noqa: T201"   • Should parse JSON without mojibake corruption")
    print(  # noqa: T201"   • Should detect as ComfyUI-related tool")
    print(  # noqa: T201"   • Should work without requiring exiftool")

    print(  # noqa: T201"\n🔧 DEPENDENCY CHECK:")
    print(  # noqa: T201"   • No exiftool calls should appear in logs")
    print(  # noqa: T201"   • All extraction should use PIL + robust Unicode decoding")


if __name__ == "__main__":
    test_civitai_mojibake()
