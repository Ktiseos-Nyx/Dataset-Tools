#!/usr/bin/env python3
"""Script to analyze TensorArt images and extract metadata patterns."""

import os
import json
import sys
from pathlib import Path
import traceback

# Add the dataset tools to the path
sys.path.insert(0, str(Path(__file__).parent))

from dataset_tools.metadata_parser import parse_metadata
from dataset_tools.file_readers.image_metadata_reader import read_image_metadata

def analyze_tensorart_images(directory_path: str, max_images: int = 5):
    """Analyze TensorArt images to find metadata patterns."""
    
    results = {
        "processed_files": [],
        "metadata_extractions": [],
        "unique_patterns": {
            "node_types": set(),
            "job_id_patterns": [],
            "ems_patterns": [],
            "workflow_signatures": []
        },
        "errors": []
    }
    
    # Get PNG files from the directory
    png_files = [f for f in os.listdir(directory_path) 
                 if f.lower().endswith('.png') and not f.startswith('.')][:max_images]
    
    print(f"Found {len(png_files)} PNG files, processing first {max_images}...")
    
    for filename in png_files:
        file_path = os.path.join(directory_path, filename)
        print(f"\n=== Processing: {filename} ===")
        
        try:
            # First, let's try to read raw PNG metadata
            print("Reading raw PNG metadata...")
            raw_metadata = read_image_metadata(file_path)
            
            # Parse with the dataset tools metadata parser
            print("Parsing with dataset tools...")
            parsed_metadata = parse_metadata(file_path)
            
            # Store results
            file_result = {
                "filename": filename,
                "raw_metadata": raw_metadata,
                "parsed_metadata": parsed_metadata,
                "analysis": analyze_file_metadata(raw_metadata, parsed_metadata)
            }
            
            results["metadata_extractions"].append(file_result)
            results["processed_files"].append(filename)
            
            # Extract patterns
            extract_patterns(file_result, results["unique_patterns"])
            
            print(f"✓ Successfully processed {filename}")
            
        except Exception as e:
            error_info = {
                "filename": filename,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            results["errors"].append(error_info)
            print(f"✗ Error processing {filename}: {e}")
    
    return results

def analyze_file_metadata(raw_metadata, parsed_metadata):
    """Analyze metadata for TensorArt-specific patterns."""
    analysis = {
        "has_comfyui_workflow": False,
        "has_ems_patterns": False,
        "has_job_id": False,
        "node_types_found": [],
        "detection_confidence": "unknown"
    }
    
    # Check for ComfyUI workflow in raw metadata
    if isinstance(raw_metadata, dict):
        workflow_data = raw_metadata.get("workflow") or raw_metadata.get("prompt")
        if workflow_data:
            analysis["has_comfyui_workflow"] = True
            
            # Try to parse JSON if it's a string
            if isinstance(workflow_data, str):
                try:
                    workflow_json = json.loads(workflow_data)
                    analysis["node_types_found"] = extract_node_types(workflow_json)
                    analysis["has_ems_patterns"] = check_ems_patterns(workflow_json)
                    analysis["has_job_id"] = check_job_id_patterns(workflow_json)
                except json.JSONDecodeError:
                    pass
            elif isinstance(workflow_data, dict):
                analysis["node_types_found"] = extract_node_types(workflow_data)
                analysis["has_ems_patterns"] = check_ems_patterns(workflow_data)
                analysis["has_job_id"] = check_job_id_patterns(workflow_data)
    
    # Check parsed metadata for detection results
    if isinstance(parsed_metadata, dict):
        if "Detected Tool" in str(parsed_metadata):
            analysis["detection_confidence"] = "detected"
        
        # Look for TensorArt-specific fields
        raw_data = parsed_metadata.get("Raw Data", {})
        if raw_data and "tensorart" in str(raw_data).lower():
            analysis["detection_confidence"] = "high"
    
    return analysis

def extract_node_types(workflow_data):
    """Extract ComfyUI node types from workflow."""
    node_types = set()
    
    if isinstance(workflow_data, dict):
        for node_id, node_data in workflow_data.items():
            if isinstance(node_data, dict) and "class_type" in node_data:
                node_types.add(node_data["class_type"])
    
    return sorted(list(node_types))

def check_ems_patterns(workflow_data):
    """Check for EMS model/LoRA patterns."""
    ems_found = False
    
    if isinstance(workflow_data, dict):
        workflow_str = json.dumps(workflow_data).lower()
        ems_found = "ems-" in workflow_str and "-ems" in workflow_str
    
    return ems_found

def check_job_id_patterns(workflow_data):
    """Check for TensorArt job ID patterns in SaveImage nodes."""
    job_id_found = False
    
    if isinstance(workflow_data, dict):
        for node_id, node_data in workflow_data.items():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "")
                if "SaveImage" in class_type:
                    inputs = node_data.get("inputs", {})
                    filename_prefix = str(inputs.get("filename_prefix", ""))
                    # Check for long numeric strings (10+ digits)
                    if filename_prefix.isdigit() and len(filename_prefix) >= 10:
                        job_id_found = True
                        break
    
    return job_id_found

def extract_patterns(file_result, patterns):
    """Extract unique patterns from the file analysis."""
    analysis = file_result.get("analysis", {})
    
    # Add node types
    node_types = analysis.get("node_types_found", [])
    patterns["node_types"].update(node_types)
    
    # Look for workflow signatures in raw metadata
    raw_metadata = file_result.get("raw_metadata", {})
    if isinstance(raw_metadata, dict):
        for key in raw_metadata.keys():
            if key.lower() in ["workflow", "prompt"]:
                patterns["workflow_signatures"].append(f"PNG chunk: {key}")

def save_results(results, output_file):
    """Save results to JSON file."""
    # Convert sets to lists for JSON serialization
    if "unique_patterns" in results:
        results["unique_patterns"]["node_types"] = sorted(list(results["unique_patterns"]["node_types"]))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def main():
    tensorart_dir = "/Users/duskfall/Downloads/TensorArt"
    output_file = "/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/tensorart_analysis.json"
    
    if not os.path.exists(tensorart_dir):
        print(f"Error: Directory not found: {tensorart_dir}")
        return
    
    print("Starting TensorArt metadata analysis...")
    results = analyze_tensorart_images(tensorart_dir, max_images=8)
    
    print(f"\n=== ANALYSIS SUMMARY ===")
    print(f"Files processed: {len(results['processed_files'])}")
    print(f"Errors: {len(results['errors'])}")
    print(f"Unique node types found: {len(results['unique_patterns']['node_types'])}")
    
    if results['unique_patterns']['node_types']:
        print("\nNode types discovered:")
        for node_type in sorted(results['unique_patterns']['node_types']):
            print(f"  - {node_type}")
    
    # Save results
    save_results(results, output_file)
    print(f"\nDetailed results saved to: {output_file}")
    
    # Print summary of each file
    print(f"\n=== FILE ANALYSIS SUMMARY ===")
    for extraction in results["metadata_extractions"]:
        filename = extraction["filename"]
        analysis = extraction["analysis"]
        print(f"\n{filename}:")
        print(f"  - ComfyUI workflow: {analysis['has_comfyui_workflow']}")
        print(f"  - EMS patterns: {analysis['has_ems_patterns']}")
        print(f"  - Job ID patterns: {analysis['has_job_id']}")
        print(f"  - Detection confidence: {analysis['detection_confidence']}")
        print(f"  - Node types: {len(analysis['node_types_found'])}")

if __name__ == "__main__":
    main()