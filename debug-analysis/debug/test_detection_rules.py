# PNG Metadata Debug Script - Modified for Dataset Tools testing
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
    print(f"🔍 DEBUGGING PNG METADATA FOR: {Path(image_path).name}")
    print("=" * 80)

    try:
        # Open the image and get ALL the metadata
        with Image.open(image_path) as img:
            print(f"📷 Image Info: {img.format}, {img.size[0]}x{img.size[1]}")
            print()

            # Check what's in the info dictionary
            print("📋 Available PNG Chunks:")
            if hasattr(img, "info") and img.info:
                for key, value in img.info.items():
                    # Show the key and a preview of the value
                    if isinstance(value, str):
                        preview = value[:100] + "..." if len(value) > 100 else value
                        print(f"  ✅ '{key}': {type(value).__name__} (length: {len(value)})")
                        print(f"      Preview: {preview!r}")
                    else:
                        print(f"  ✅ '{key}': {type(value).__name__} = {value}")
                print()
            else:
                print("  ❌ No PNG chunks found in img.info")
                print()

            # Specifically check for ComfyUI chunks
            print("🎯 ComfyUI-Specific Chunk Analysis:")

            # Check 'workflow' chunk
            if "workflow" in img.info:
                workflow_data = img.info["workflow"]
                print(f"  ✅ 'workflow' chunk found: {type(workflow_data)} (length: {len(workflow_data)})")

                # Try to parse as JSON
                try:
                    workflow_json = json.loads(workflow_data)
                    print(f"  ✅ 'workflow' is valid JSON with {len(workflow_json)} nodes")

                    # Show some sample nodes
                    sample_nodes = list(workflow_json.keys())[:3]
                    for node_id in sample_nodes:
                        node = workflow_json[node_id]
                        class_type = node.get("class_type", "Unknown")
                        print(f"    📦 Node {node_id}: {class_type}")

                except json.JSONDecodeError as e:
                    print(f"  ❌ 'workflow' chunk is not valid JSON: {e}")
                    print(f"      Raw content preview: {workflow_data[:200]!r}")
            else:
                print("  ❌ 'workflow' chunk not found")

            # Check 'prompt' chunk
            if "prompt" in img.info:
                prompt_data = img.info["prompt"]
                print(f"  ✅ 'prompt' chunk found: {type(prompt_data)} (length: {len(prompt_data)})")

                # Try to parse as JSON
                try:
                    prompt_json = json.loads(prompt_data)
                    print(f"  ✅ 'prompt' is valid JSON with {len(prompt_json)} nodes")

                    # Show some sample nodes
                    sample_nodes = list(prompt_json.keys())[:3]
                    for node_id in sample_nodes:
                        node = prompt_json[node_id]
                        class_type = node.get("class_type", "Unknown")
                        print(f"    📦 Node {node_id}: {class_type}")

                except json.JSONDecodeError as e:
                    print(f"  ❌ 'prompt' chunk is not valid JSON: {e}")
                    print(f"      Raw content preview: {prompt_data[:200]!r}")
            else:
                print("  ❌ 'prompt' chunk not found")

            print()

            # Check for other common chunks
            print("🔍 Other Metadata Chunks:")
            other_chunks = [key for key in img.info.keys() if key not in ["workflow", "prompt"]]
            if other_chunks:
                for key in other_chunks:
                    value = img.info[key]
                    print(f"  📝 '{key}': {type(value).__name__}")
                    if isinstance(value, str) and len(value) > 50:
                        print(f"      (length: {len(value)}, preview: {value[:50]!r}...)")
            else:
                print("  📝 No other chunks found")

    except Exception as e:
        print(f"💥 ERROR reading PNG metadata: {e}")
        import traceback

        traceback.print_exc()

    print("=" * 80)
    print()


def test_metadata_engine_detection(image_path: str):
    """Test what your metadata engine detects for this file."""
    print(f"🤖 TESTING METADATA ENGINE FOR: {Path(image_path).name}")
    print("=" * 80)

    try:
        # Initialize metadata engine
        parser_definitions_path = Path(__file__).parent / "parser_definitions"
        print(f"📂 Parser definitions path: {parser_definitions_path}")

        if not parser_definitions_path.exists():
            print("❌ Parser definitions folder not found!")
            return

        engine = get_metadata_engine(str(parser_definitions_path))
        print("✅ Metadata engine initialized")

        # Test detection
        result = engine.get_parser_for_file(image_path)
        print(f"🎯 Detection result: {result}")

        if result and isinstance(result, dict):
            tool = result.get("tool", "Unknown")
            print(f"🔧 Detected tool: {tool}")

            # Show basic info
            if "prompt" in result:
                prompt_preview = result["prompt"][:100] + "..." if len(result["prompt"]) > 100 else result["prompt"]
                print(f"📝 Prompt preview: {prompt_preview}")

            if "parameters" in result:
                params = result["parameters"]
                print(f"⚙️  Parameters: {list(params.keys()) if isinstance(params, dict) else 'Not a dict'}")
        else:
            print("❌ No detection result or invalid format")

    except Exception as e:
        print(f"💥 ERROR in metadata engine test: {e}")
        import traceback

        traceback.print_exc()

    print("=" * 80)
    print()


def main():
    """Test with a specific image file."""
    # Test with the images the user mentioned
    test_images = [
        "/Users/duskfall/Downloads/Metadata Samples/Image #2.png",
        "/Users/duskfall/Downloads/Metadata Samples/Image #3.png",
        "/Users/duskfall/Downloads/Metadata Samples/Image #4.png",
        "/Users/duskfall/Downloads/Metadata Samples/Image #5.png",
    ]

    print("🚀 STARTING METADATA ENGINE TEST")
    print("=" * 100)
    print()

    for image_path in test_images:
        if Path(image_path).exists():
            print(f"Testing: {image_path}")
            debug_png_metadata(image_path)
            test_metadata_engine_detection(image_path)
            print("\n" + "=" * 100 + "\n")
        else:
            print(f"❌ File not found: {image_path}")

    print("🎉 Testing complete!")


if __name__ == "__main__":
    main()
