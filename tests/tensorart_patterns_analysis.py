#!/usr/bin/env python3
"""Advanced TensorArt pattern analysis script for extracting unique signatures."""

import json
import re
from collections import defaultdict


def analyze_tensorart_patterns():
    """Analyze the extracted TensorArt metadata for unique signatures."""
    # Load the analysis results
    with open("/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/tensorart_analysis.json") as f:
        data = json.load(f)

    patterns = {
        "ems_models": set(),
        "ems_loras": set(),
        "node_types": set(),
        "job_id_patterns": [],
        "filename_prefixes": [],
        "unique_node_signatures": set(),
        "workflow_patterns": defaultdict(int),
        "tensorart_specific_nodes": set()
    }

    print("=== TENSORART METADATA PATTERN ANALYSIS ===\n")

    for extraction in data["metadata_extractions"]:
        filename = extraction["filename"]
        raw_content = extraction["parsed_metadata"].get("raw_tool_specific_data_section", {}).get("raw_content", "")

        if not raw_content:
            continue

        print(f"--- Analyzing {filename} ---")

        try:
            # Parse the workflow data
            # The raw_content is a string representation of a dict, so we need to evaluate it safely
            workflow_data = eval(raw_content)  # Note: In production, use ast.literal_eval

            analyze_workflow_for_patterns(workflow_data, patterns, filename)

        except Exception as e:
            print(f"Error parsing workflow for {filename}: {e}")

    # Print comprehensive analysis
    print_pattern_analysis(patterns)

    return patterns

def analyze_workflow_for_patterns(workflow_data: dict, patterns: dict, filename: str):
    """Analyze individual workflow for TensorArt patterns."""
    found_patterns = []

    for node_id, node_data in workflow_data.items():
        if not isinstance(node_data, dict):
            continue

        class_type = node_data.get("class_type", "")
        inputs = node_data.get("inputs", {})

        patterns["node_types"].add(class_type)

        # Check for EMS model patterns in CheckpointLoader nodes
        if "CheckpointLoader" in class_type:
            ckpt_name = inputs.get("ckpt_name", "")
            if "EMS-" in ckpt_name and "-EMS" in ckpt_name:
                patterns["ems_models"].add(ckpt_name)
                found_patterns.append(f"EMS Model: {ckpt_name}")

        # Check for EMS LoRA patterns in LoraLoader/LoraTagLoader nodes
        if "Lora" in class_type:
            lora_name = inputs.get("lora_name", "")
            text = inputs.get("text", "")

            if "EMS-" in lora_name and "-EMS" in lora_name:
                patterns["ems_loras"].add(lora_name)
                found_patterns.append(f"EMS LoRA: {lora_name}")

            # Check for LoRA references in text
            if "<lora:" in text and "EMS-" in text:
                lora_matches = re.findall(r"<lora:(EMS-[^:>]+)", text)
                for match in lora_matches:
                    patterns["ems_loras"].add(match)
                    found_patterns.append(f"EMS LoRA in text: {match}")

        # Check for TensorArt job ID patterns in SaveImage nodes
        if class_type == "SaveImage":
            filename_prefix = str(inputs.get("filename_prefix", ""))
            patterns["filename_prefixes"].append(filename_prefix)

            # Check if it's a long numeric string (likely TensorArt job ID)
            if filename_prefix.isdigit() and len(filename_prefix) >= 15:
                patterns["job_id_patterns"].append({
                    "file": filename,
                    "job_id": filename_prefix,
                    "length": len(filename_prefix)
                })
                found_patterns.append(f"TensorArt Job ID: {filename_prefix}")

        # Identify TensorArt-specific node types
        tensorart_specific_nodes = [
            "ECHOCheckpointLoaderSimple",
            "BNK_CLIPTextEncodeAdvanced",
            "LoraTagLoader",
            "SetSubseeds",
            "SetSubseeds_Image",
            "KSampler_A1111",
            "NunchakuFluxDiTLoader",
            "NunchakuFluxLoraLoader"
        ]

        if class_type in tensorart_specific_nodes:
            patterns["tensorart_specific_nodes"].add(class_type)
            patterns["unique_node_signatures"].add(f"{class_type}_{node_id}")
            found_patterns.append(f"TensorArt Node: {class_type}")

    # Pattern combinations
    workflow_signature = "_".join(sorted(patterns["node_types"]))
    patterns["workflow_patterns"][workflow_signature] += 1

    print(f"  Found {len(found_patterns)} TensorArt patterns:")
    for pattern in found_patterns:
        print(f"    - {pattern}")

def print_pattern_analysis(patterns: dict):
    """Print comprehensive pattern analysis."""
    print("\n" + "="*60)
    print("TENSORART SIGNATURE ANALYSIS RESULTS")
    print("="*60)

    # EMS Models
    print(f"\n1. EMS MODELS FOUND ({len(patterns['ems_models'])}):")
    for model in sorted(patterns["ems_models"]):
        print(f"   - {model}")

    # EMS LoRAs
    print(f"\n2. EMS LORAS FOUND ({len(patterns['ems_loras'])}):")
    for lora in sorted(patterns["ems_loras"]):
        print(f"   - {lora}")

    # Job ID Patterns
    print(f"\n3. TENSORART JOB IDS ({len(patterns['job_id_patterns'])}):")
    for job in patterns["job_id_patterns"]:
        print(f"   - {job['job_id']} (length: {job['length']}) in {job['file']}")

    # TensorArt-specific nodes
    print(f"\n4. TENSORART-SPECIFIC NODES ({len(patterns['tensorart_specific_nodes'])}):")
    for node in sorted(patterns["tensorart_specific_nodes"]):
        print(f"   - {node}")

    # All unique node types
    print(f"\n5. ALL COMFYUI NODE TYPES FOUND ({len(patterns['node_types'])}):")
    for node_type in sorted(patterns["node_types"]):
        indicator = "★" if node_type in patterns["tensorart_specific_nodes"] else " "
        print(f"   {indicator} {node_type}")

    # Filename prefixes analysis
    print("\n6. FILENAME PREFIX PATTERNS:")
    numeric_prefixes = [p for p in patterns["filename_prefixes"] if p.isdigit()]
    non_numeric_prefixes = [p for p in patterns["filename_prefixes"] if not p.isdigit()]

    print(f"   Numeric IDs: {len(numeric_prefixes)}")
    for prefix in numeric_prefixes:
        print(f"     - {prefix} (length: {len(prefix)})")

    if non_numeric_prefixes:
        print(f"   Non-numeric prefixes: {len(non_numeric_prefixes)}")
        for prefix in non_numeric_prefixes:
            print(f"     - {prefix}")

    # Detection Summary
    print("\n7. DETECTION SUMMARY:")
    total_files = len([e for e in patterns["filename_prefixes"] if e])
    ems_files = len(patterns["ems_models"]) + len(patterns["ems_loras"])
    job_id_files = len(patterns["job_id_patterns"])

    print(f"   Total files analyzed: {total_files}")
    print(f"   Files with EMS signatures: {ems_files}")
    print(f"   Files with TensorArt job IDs: {job_id_files}")
    print(f"   TensorArt-specific node types: {len(patterns['tensorart_specific_nodes'])}")

    # Pattern-based detection rules
    print("\n8. PROPOSED DETECTION RULES:")
    print("   Rule 1: EMS model pattern - 'EMS-[digits]-EMS.safetensors'")
    print("   Rule 2: EMS LoRA pattern - 'EMS-[digits]-FP8-EMS.safetensors' or '<lora:EMS-[digits]-EMS'")
    print("   Rule 3: Job ID pattern - Numeric filename_prefix with 15+ digits")
    print("   Rule 4: TensorArt node types:")
    for node in sorted(patterns["tensorart_specific_nodes"]):
        print(f"          - {node}")

def extract_ems_patterns():
    """Extract and analyze EMS numbering patterns."""
    with open("/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/tensorart_analysis.json") as f:
        data = json.load(f)

    ems_numbers = []

    for extraction in data["metadata_extractions"]:
        raw_content = extraction["parsed_metadata"].get("raw_tool_specific_data_section", {}).get("raw_content", "")

        if raw_content:
            # Find all EMS patterns
            ems_matches = re.findall(r"EMS-(\d+)-(?:FP8-)?EMS", raw_content)
            ems_numbers.extend([int(num) for num in ems_matches])

    if ems_numbers:
        print("\n9. EMS NUMBER ANALYSIS:")
        print(f"   EMS numbers found: {sorted(ems_numbers)}")
        print(f"   Range: {min(ems_numbers)} to {max(ems_numbers)}")
        print(f"   Count: {len(ems_numbers)}")

        # Check for patterns in the numbers
        differences = [ems_numbers[i+1] - ems_numbers[i] for i in range(len(ems_numbers)-1)]
        if differences:
            print(f"   Number gaps: {differences}")

if __name__ == "__main__":
    patterns = analyze_tensorart_patterns()
    extract_ems_patterns()

    # Save patterns for reference
    output_file = "/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/tensorart_patterns.json"

    # Convert sets to lists for JSON serialization
    serializable_patterns = {}
    for key, value in patterns.items():
        if isinstance(value, set):
            serializable_patterns[key] = sorted(list(value))
        else:
            serializable_patterns[key] = value

    with open(output_file, "w") as f:
        json.dump(serializable_patterns, f, indent=2)

    print(f"\nDetailed patterns saved to: {output_file}")
