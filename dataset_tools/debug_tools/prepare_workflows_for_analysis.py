#!/usr/bin/env python3
# ruff: noqa: T201

"""Prepare ComfyUI workflow files for analysis with Gemini.
This script extracts workflows from image metadata and prepares them for batch analysis.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def extract_workflow_from_file(file_path: str) -> dict[str, Any]:
    """Extract ComfyUI workflow from an image file."""
    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

        preparer = ContextDataPreparer()
        context = preparer.prepare_context(file_path)

        # Try to get workflow from various sources
        workflow_data = None
        source = None

        # Check PNG chunks first
        pil_info = context.get("pil_info", {})
        if "workflow" in pil_info:
            workflow_data = pil_info["workflow"]
            source = "png_chunk"

        # Check EXIF UserComment
        if not workflow_data:
            user_comment = context.get("raw_user_comment_str")
            if user_comment:
                try:
                    parsed = json.loads(user_comment)
                    # Remove extra/extraMetadata for cleaner analysis
                    if "extra" in parsed:
                        del parsed["extra"]
                    if "extraMetadata" in parsed:
                        del parsed["extraMetadata"]
                    workflow_data = parsed
                    source = "exif_user_comment"
                except:
                    pass

        if workflow_data:
            return {
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "source": source,
                "workflow": workflow_data,
                "node_count": len(
                    [
                        k
                        for k, v in workflow_data.items()
                        if isinstance(v, dict) and "class_type" in v
                    ]
                ),
            }

    except Exception as e:
        print(  # noqa: T201f"❌ Error extracting from {Path(file_path).name}: {e}")

    return None


def prepare_workflow_batch(
    source_directory: str, output_directory: str, max_files: int = 100
):
    """Prepare a batch of workflow files for Gemini analysis."""
    source_path = Path(source_directory)
    output_path = Path(output_directory)
    output_path.mkdir(exist_ok=True)

    print(  # noqa: T201f"🔍 Scanning {source_path} for ComfyUI workflows...")

    # Find image files
    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    image_files = []

    for ext in image_extensions:
        image_files.extend(source_path.glob(f"*{ext}"))
        image_files.extend(source_path.glob(f"*{ext.upper()}"))

    print(  # noqa: T201f"📁 Found {len(image_files)} image files")

    workflows_extracted = 0
    batch_number = 1
    current_batch = []

    for image_file in image_files[:max_files]:
        print(  # noqa: T201f"📄 Processing: {image_file.name}")

        workflow_info = extract_workflow_from_file(str(image_file))
        if workflow_info:
            current_batch.append(workflow_info)
            workflows_extracted += 1

            # Save batch every 10 workflows
            if len(current_batch) >= 10:
                batch_file = output_path / f"workflow_batch_{batch_number:03d}.json"
                with open(batch_file, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "batch_number": batch_number,
                            "workflow_count": len(current_batch),
                            "workflows": current_batch,
                        },
                        f,
                        indent=2,
                    )

                print(  # noqa: T201
                    f"💾 Saved batch {batch_number} with {len(current_batch)} workflows"
                )
                current_batch = []
                batch_number += 1

    # Save final batch if any remaining
    if current_batch:
        batch_file = output_path / f"workflow_batch_{batch_number:03d}.json"
        with open(batch_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "batch_number": batch_number,
                    "workflow_count": len(current_batch),
                    "workflows": current_batch,
                },
                f,
                indent=2,
            )
        print(  # noqa: T201
            f"💾 Saved final batch {batch_number} with {len(current_batch)} workflows"
        )

    print(  # noqa: T201"\n✅ EXTRACTION COMPLETE:")
    print(  # noqa: T201f"   📊 Total workflows extracted: {workflows_extracted}")
    print(  # noqa: T201f"   📦 Batches created: {batch_number}")
    print(  # noqa: T201f"   📁 Output directory: {output_path}")

    # Create analysis instructions
    instructions_file = output_path / "analysis_instructions.md"
    with open(instructions_file, "w", encoding="utf-8") as f:
        f.write(
            f"""# ComfyUI Workflow Analysis Instructions

## Overview
This directory contains {batch_number} batch files with {workflows_extracted} ComfyUI workflows extracted from image metadata.

## Batch Files
- Format: `workflow_batch_XXX.json`
- Each batch contains up to 10 workflows
- Each workflow includes: file info, source type, and node data

## Analysis Process
1. Use the `comfyui_node_analysis_template.md` as your analysis guide
2. Process each batch file separately with Gemini
3. For each workflow in the batch, extract node information
4. Combine results into a master node dictionary

## Sample Gemini Prompt
```
Please analyze this batch of ComfyUI workflows using the provided template. 
Extract all node types, their inputs/outputs, connection patterns, and categorize them.
Focus on discovering new node types and understanding their usage patterns.

[Paste workflow batch JSON here]
```

## Expected Output
- One analysis JSON per batch following the template structure
- Merged results across all batches
- Final comprehensive node dictionary

## Key Focus Areas
- Custom nodes (smZ, MZ_, etc.)
- Connection patterns between node types  
- Input/output type mapping
- URN resource patterns
- Widget vs input distinction
"""
        )

    print(  # noqa: T201f"📋 Created analysis instructions: {instructions_file}")


def create_sample_analysis():
    """Create a sample analysis to show Gemini the expected format."""
    sample_output = output_path / "sample_analysis_output.json"

    sample = {
        "file_analyzed": "workflow_batch_001.json",
        "analysis_timestamp": "2025-01-07T20:30:00Z",
        "nodes_discovered": {
            "KSampler": {
                "category": "sampling",
                "frequency": 8,
                "inputs": {
                    "model": {
                        "type": "MODEL",
                        "required": True,
                        "connection_source": ["resource-stack", 0],
                        "observed_values": [],
                    },
                    "seed": {
                        "type": "INT",
                        "required": False,
                        "default_value": None,
                        "observed_values": [359825400, 1531035486, 654115794],
                    },
                    "steps": {
                        "type": "INT",
                        "required": False,
                        "default_value": 20,
                        "observed_values": [30, 25, 20],
                    },
                },
                "outputs": ["LATENT"],
                "connection_patterns": {
                    "typical_inputs_from": ["CheckpointLoaderSimple", "CLIPTextEncode"],
                    "typical_outputs_to": ["VAEDecode"],
                },
                "metadata": {"title": "KSampler", "source": "core", "aliases": []},
            },
            "smZ CLIPTextEncode": {
                "category": "conditioning",
                "frequency": 16,
                "inputs": {
                    "text": {
                        "type": "STRING",
                        "required": True,
                        "connection_source": None,
                        "observed_values": [
                            "masterpiece, very aesthetic...",
                            "embedding:urn:air:...",
                        ],
                    },
                    "clip": {
                        "type": "CLIP",
                        "required": True,
                        "connection_source": ["resource-stack", 1],
                        "observed_values": [],
                    },
                },
                "outputs": ["CONDITIONING"],
                "connection_patterns": {
                    "typical_inputs_from": ["CheckpointLoaderSimple", "LoraLoader"],
                    "typical_outputs_to": ["KSampler", "SamplerCustom"],
                },
                "metadata": {
                    "title": "Positive/Negative",
                    "source": "custom_node",
                    "aliases": ["CLIPTextEncode"],
                },
            },
        },
        "statistics": {
            "total_nodes_in_batch": 145,
            "unique_node_types": 12,
            "new_node_types_discovered": 3,
        },
    }

    with open(sample_output, "w", encoding="utf-8") as f:
        json.dump(sample, f, indent=2)

    print(  # noqa: T201f"📝 Created sample analysis output: {sample_output}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(  # noqa: T201
            "Usage: python prepare_workflows_for_analysis.py <source_dir> <output_dir> [max_files]"
        )
        print(  # noqa: T201
            "Example: python prepare_workflows_for_analysis.py '/Users/duskfall/Downloads/Metadata Samples' './workflow_analysis' 100"
        )
        sys.exit(1)

    source_dir = sys.argv[1]
    output_dir = sys.argv[2]
    max_files = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    prepare_workflow_batch(source_dir, output_dir, max_files)

    # Also create sample analysis
    output_path = Path(output_dir)
    create_sample_analysis()
