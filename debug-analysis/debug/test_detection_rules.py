# PNG Metadata Debug Script - Modified for Dataset Tools testing
# ruff: noqa: T201
# Let's see what's REALLY inside these PNG files!

import json
import sys
from pathlib import Path

from PIL import Image

# Add the parent directory to the path so we can import dataset_tools
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_tools.metadata_engine import get_metadata_engine


def debug_png_metadata(image_path: str):
    """Deep dive into PNG metadata to see what your JSON parsers are missing!"""
    print(  # noqa: T201f"🔍 DEBUGGING PNG METADATA FOR: {Path(image_path).name}")
    print(  # noqa: T201"=" * 80)

    try:
        # Open the image and get ALL the metadata
        with Image.open(image_path) as img:
            print(  # noqa: T201f"📷 Image Info: {img.format}, {img.size[0]}x{img.size[1]}")
            print(  # noqa: T201)

            # Check what's in the info dictionary
            print(  # noqa: T201"📋 Available PNG Chunks:")
            if hasattr(img, "info") and img.info:
                for key, value in img.info.items():
                    # Show the key and a preview of the value
                    if isinstance(value, str):
                        preview = value[:100] + "..." if len(value) > 100 else value
                        print(  # noqa: T201
                            f"  ✅ '{key}': {type(value).__name__} (length: {len(value)})"
                        )
                        print(  # noqa: T201f"      Preview: {preview!r}")
                    else:
                        print(  # noqa: T201f"  ✅ '{key}': {type(value).__name__} = {value}")
                print(  # noqa: T201)
            else:
                print(  # noqa: T201"  ❌ No PNG chunks found in img.info")
                print(  # noqa: T201)

            # Specifically check for ComfyUI chunks
            print(  # noqa: T201"🎯 ComfyUI-Specific Chunk Analysis:")

            # Check 'workflow' chunk
            if "workflow" in img.info:
                workflow_data = img.info["workflow"]
                print(  # noqa: T201
                    f"  ✅ 'workflow' chunk found: {type(workflow_data)} (length: {len(workflow_data)})"
                )

                # Try to parse as JSON
                try:
                    workflow_json = json.loads(workflow_data)
                    print(  # noqa: T201
                        f"  ✅ 'workflow' is valid JSON with {len(workflow_json)} nodes"
                    )

                    # Show some sample nodes
                    sample_nodes = list(workflow_json.keys())[:3]
                    for node_id in sample_nodes:
                        node = workflow_json[node_id]
                        class_type = node.get("class_type", "Unknown")
                        print(  # noqa: T201f"    📦 Node {node_id}: {class_type}")

                except json.JSONDecodeError as e:
                    print(  # noqa: T201f"  ❌ 'workflow' chunk is not valid JSON: {e}")
                    print(  # noqa: T201f"      Raw content preview: {workflow_data[:200]!r}")
            else:
                print(  # noqa: T201"  ❌ 'workflow' chunk not found")

            # Check 'prompt' chunk
            if "prompt" in img.info:
                prompt_data = img.info["prompt"]
                print(  # noqa: T201
                    f"  ✅ 'prompt' chunk found: {type(prompt_data)} (length: {len(prompt_data)})"
                )

                # Try to parse as JSON
                try:
                    prompt_json = json.loads(prompt_data)
                    print(  # noqa: T201f"  ✅ 'prompt' is valid JSON with {len(prompt_json)} nodes")

                    # Show some sample nodes
                    sample_nodes = list(prompt_json.keys())[:3]
                    for node_id in sample_nodes:
                        node = prompt_json[node_id]
                        class_type = node.get("class_type", "Unknown")
                        print(  # noqa: T201f"    📦 Node {node_id}: {class_type}")

                except json.JSONDecodeError as e:
                    print(  # noqa: T201f"  ❌ 'prompt' chunk is not valid JSON: {e}")
                    print(  # noqa: T201f"      Raw content preview: {prompt_data[:200]!r}")
            else:
                print(  # noqa: T201"  ❌ 'prompt' chunk not found")

            print(  # noqa: T201)

            # Check for other common chunks
            print(  # noqa: T201"🔍 Other Metadata Chunks:")
            other_chunks = [
                key for key in img.info.keys() if key not in ["workflow", "prompt"]
            ]
            if other_chunks:
                for key in other_chunks:
                    value = img.info[key]
                    print(  # noqa: T201f"  📝 '{key}': {type(value).__name__}")
                    if isinstance(value, str) and len(value) > 50:
                        print(  # noqa: T201
                            f"      (length: {len(value)}, preview: {value[:50]!r}...)"
                        )
            else:
                print(  # noqa: T201"  📝 No other chunks found")

    except Exception as e:
        print(  # noqa: T201f"💥 ERROR reading PNG metadata: {e}")
        import traceback

        traceback.print_exc()

    print(  # noqa: T201"=" * 80)
    print(  # noqa: T201)


def test_metadata_engine_detection(image_path: str):
    """Test what your metadata engine detects for this file."""
    print(  # noqa: T201f"🤖 TESTING METADATA ENGINE FOR: {Path(image_path).name}")
    print(  # noqa: T201"=" * 80)

    try:
        # Initialize metadata engine
        parser_definitions_path = Path(__file__).parent / "parser_definitions"
        print(  # noqa: T201f"📂 Parser definitions path: {parser_definitions_path}")

        if not parser_definitions_path.exists():
            print(  # noqa: T201"❌ Parser definitions folder not found!")
            return

        engine = get_metadata_engine(str(parser_definitions_path))
        print(  # noqa: T201"✅ Metadata engine initialized")

        # Test detection
        result = engine.get_parser_for_file(image_path)
        print(  # noqa: T201f"🎯 Detection result: {result}")

        if result and isinstance(result, dict):
            tool = result.get("tool", "Unknown")
            print(  # noqa: T201f"🔧 Detected tool: {tool}")

            # Show basic info
            if "prompt" in result:
                prompt_preview = (
                    result["prompt"][:100] + "..."
                    if len(result["prompt"]) > 100
                    else result["prompt"]
                )
                print(  # noqa: T201f"📝 Prompt preview: {prompt_preview}")

            if "parameters" in result:
                params = result["parameters"]
                print(  # noqa: T201
                    f"⚙️  Parameters: {list(params.keys()) if isinstance(params, dict) else 'Not a dict'}"
                )
        else:
            print(  # noqa: T201"❌ No detection result or invalid format")

    except Exception as e:
        print(  # noqa: T201f"💥 ERROR in metadata engine test: {e}")
        import traceback

        traceback.print_exc()

    print(  # noqa: T201"=" * 80)
    print(  # noqa: T201)


def main():
    """Test with a specific image file."""
    # Test with the images the user mentioned
    test_images = [
        "/Users/duskfall/Downloads/Metadata Samples/Image #2.png",
        "/Users/duskfall/Downloads/Metadata Samples/Image #3.png",
        "/Users/duskfall/Downloads/Metadata Samples/Image #4.png",
        "/Users/duskfall/Downloads/Metadata Samples/Image #5.png",
    ]

    print(  # noqa: T201"🚀 STARTING METADATA ENGINE TEST")
    print(  # noqa: T201"=" * 100)
    print(  # noqa: T201)

    for image_path in test_images:
        if Path(image_path).exists():
            print(  # noqa: T201f"Testing: {image_path}")
            debug_png_metadata(image_path)
            test_metadata_engine_detection(image_path)
            print(  # noqa: T201"\n" + "=" * 100 + "\n")
        else:
            print(  # noqa: T201f"❌ File not found: {image_path}")

    print(  # noqa: T201"🎉 Testing complete!")


if __name__ == "__main__":
    main()
