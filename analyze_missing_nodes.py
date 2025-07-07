#!/usr/bin/env python3
"""ComfyUI Missing Node Analyzer

This script helps identify which ComfyUI node types are missing from our dictionary
by analyzing failed metadata parsing attempts.

Usage with Gemini:
1. Run this script on images that fail to parse
2. Share the output with Gemini along with the guide
3. Gemini can then add the missing node definitions

Example usage:
    python analyze_missing_nodes.py "/path/to/failed/image.png"
"""

import json
import sys
from pathlib import Path
from typing import Any


def load_node_dictionary() -> dict[str, Any]:
    """Load the current ComfyUI node dictionary."""
    dict_path = Path(__file__).parent / "dataset_tools" / "comfyui_node_dictionary.json"
    try:
        with open(dict_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Dictionary not found at: {dict_path}")
        return {}


def get_known_nodes(dictionary: dict[str, Any]) -> set[str]:
    """Extract all known node types from the dictionary."""
    known_nodes = set()
    node_types = dictionary.get("node_types", {})

    for category in node_types.values():
        if isinstance(category, dict):
            known_nodes.update(category.keys())

    return known_nodes


def extract_workflow_nodes(metadata_raw: str) -> set[str]:
    """Extract all node types from ComfyUI workflow JSON."""
    workflow_nodes = set()

    try:
        # Try to parse as JSON
        if metadata_raw.strip().startswith("{"):
            workflow_data = json.loads(metadata_raw)
        else:
            # Handle embedded JSON in metadata
            import re

            json_match = re.search(r"\{.*\}", metadata_raw, re.DOTALL)
            if json_match:
                workflow_data = json.loads(json_match.group())
            else:
                return workflow_nodes

        # Extract node types from workflow
        if "nodes" in workflow_data:
            for node in workflow_data["nodes"]:
                if isinstance(node, dict) and "type" in node:
                    workflow_nodes.add(node["type"])

        # Also check for direct node definitions
        for key, value in workflow_data.items():
            if isinstance(value, dict) and "class_type" in value:
                workflow_nodes.add(value["class_type"])

    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse workflow JSON: {e}")
    except Exception as e:
        print(f"⚠️  Error extracting nodes: {e}")

    return workflow_nodes


def analyze_image_metadata(image_path: str) -> dict[str, Any]:
    """Analyze an image to find missing ComfyUI nodes."""
    # Import here to avoid circular dependencies
    sys.path.insert(0, str(Path(__file__).parent))

    try:
        from dataset_tools.metadata_parser import parse_metadata
        from dataset_tools.vendored_sdpr.image_data_reader import ImageDataReader

        print(f"🔍 Analyzing: {Path(image_path).name}")

        # Try our parser first
        result = parse_metadata(image_path)

        # Also try direct SDPR reading
        try:
            reader = ImageDataReader(image_path)
            raw_metadata = getattr(reader, "raw", "")
        except:
            raw_metadata = ""

        # Get raw workflow data
        workflow_data = ""
        if "raw_tool_specific_data_section" in result:
            workflow_data = result["raw_tool_specific_data_section"]
        elif raw_metadata:
            workflow_data = raw_metadata

        return {
            "parsed_successfully": "prompt_data_section" in result,
            "has_workflow_data": bool(workflow_data),
            "workflow_data": workflow_data,
            "parse_result": result,
        }

    except Exception as e:
        print(f"❌ Error analyzing {image_path}: {e}")
        return {"error": str(e)}


def main():
    """Main analysis function."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_missing_nodes.py <image_path>")
        print("       python analyze_missing_nodes.py <path_to_workflow.json>")
        sys.exit(1)

    file_path = sys.argv[1]

    # Load dictionary
    print("📚 Loading ComfyUI node dictionary...")
    dictionary = load_node_dictionary()
    known_nodes = get_known_nodes(dictionary)
    print(f"📊 Dictionary contains {len(known_nodes)} known node types")

    # Analyze file
    if file_path.endswith(".json"):
        # Direct workflow file
        with open(file_path, encoding="utf-8") as f:
            workflow_data = f.read()
        analysis = {
            "parsed_successfully": False,
            "has_workflow_data": True,
            "workflow_data": workflow_data,
        }
    else:
        # Image file
        analysis = analyze_image_metadata(file_path)

    if "error" in analysis:
        print(f"❌ Analysis failed: {analysis['error']}")
        return

    # Extract workflow nodes
    if analysis["has_workflow_data"]:
        workflow_nodes = extract_workflow_nodes(analysis["workflow_data"])
        missing_nodes = workflow_nodes - known_nodes

        print("\n📊 ANALYSIS RESULTS:")
        print(
            f"   • Parsed successfully: {'✅' if analysis['parsed_successfully'] else '❌'}"
        )
        print(f"   • Total workflow nodes: {len(workflow_nodes)}")
        print(f"   • Known nodes: {len(workflow_nodes & known_nodes)}")
        print(f"   • Missing nodes: {len(missing_nodes)}")

        if missing_nodes:
            print("\n🚨 MISSING NODE TYPES:")
            for node in sorted(missing_nodes):
                print(f"   • {node}")

            print("\n📋 FOR GEMINI:")
            print(f"Add these {len(missing_nodes)} node types to the dictionary:")
            for node in sorted(missing_nodes):
                print(f"- {node}")

        else:
            print("\n✅ All workflow nodes are already in the dictionary!")
            if not analysis["parsed_successfully"]:
                print(
                    "❓ Parsing failed for other reasons (check parameter extraction patterns)"
                )

    else:
        print("\n❌ No ComfyUI workflow data found in this file")


if __name__ == "__main__":
    main()
