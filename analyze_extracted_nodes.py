#!/usr/bin/env python3
"""
Analyze extracted ComfyUI nodes from batch_nodes directory.
This script will help identify nodes that might be missing from our parsers.
"""

import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set


def analyze_node_files(directory: str) -> Dict[str, any]:
    """Analyze all extracted node files and return comprehensive statistics."""
    
    node_directory = Path(directory)
    if not node_directory.exists():
        print(f"Directory not found: {directory}")
        return {}
    
    all_nodes = set()
    node_counts = Counter()
    nodes_by_file = defaultdict(set)
    nodes_with_prompts = set()
    prompt_examples = defaultdict(list)
    
    json_files = list(node_directory.glob("*.json"))
    print(f"Found {len(json_files)} JSON files to analyze...")
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print(f"Skipping {file_path.name} - not a list")
                continue
            
            file_nodes = set()
            
            for item in data:
                if isinstance(item, dict) and 'name' in item:
                    node_name = item['name']
                    all_nodes.add(node_name)
                    node_counts[node_name] += 1
                    file_nodes.add(node_name)
                    
                    # Track nodes with prompts
                    if 'prompts' in item:
                        nodes_with_prompts.add(node_name)
                        if isinstance(item['prompts'], dict):
                            for key, value in item['prompts'].items():
                                if isinstance(value, str) and value.strip():
                                    prompt_examples[node_name].append({
                                        'key': key,
                                        'value': value[:100] + '...' if len(value) > 100 else value,
                                        'file': file_path.name
                                    })
            
            nodes_by_file[file_path.name] = file_nodes
            
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
    
    return {
        'total_files': len(json_files),
        'total_unique_nodes': len(all_nodes),
        'all_nodes': sorted(all_nodes),
        'node_counts': node_counts,
        'nodes_by_file': dict(nodes_by_file),
        'nodes_with_prompts': sorted(nodes_with_prompts),
        'prompt_examples': dict(prompt_examples)
    }


def generate_analysis_report(analysis_data: Dict[str, any]) -> str:
    """Generate a comprehensive analysis report."""
    
    report = []
    report.append("=" * 80)
    report.append("COMFYUI NODE ANALYSIS REPORT")
    report.append("=" * 80)
    report.append(f"Total Files Analyzed: {analysis_data['total_files']}")
    report.append(f"Total Unique Nodes: {analysis_data['total_unique_nodes']}")
    report.append("")
    
    # Most common nodes
    report.append("TOP 50 MOST COMMON NODES:")
    report.append("-" * 40)
    for node, count in analysis_data['node_counts'].most_common(50):
        report.append(f"{node:<40} {count:>5}")
    report.append("")
    
    # Nodes with prompts
    report.append("NODES THAT CONTAIN PROMPTS:")
    report.append("-" * 40)
    for node in analysis_data['nodes_with_prompts']:
        count = analysis_data['node_counts'][node]
        report.append(f"{node:<40} {count:>5}")
    report.append("")
    
    # All nodes alphabetically
    report.append("ALL UNIQUE NODES (ALPHABETICAL):")
    report.append("-" * 40)
    for i, node in enumerate(analysis_data['all_nodes'], 1):
        count = analysis_data['node_counts'][node]
        report.append(f"{i:>4}. {node:<40} {count:>5}")
    report.append("")
    
    # Sample prompt examples
    report.append("SAMPLE PROMPT EXAMPLES:")
    report.append("-" * 40)
    for node_name, examples in list(analysis_data['prompt_examples'].items())[:20]:
        report.append(f"\n{node_name}:")
        for example in examples[:3]:  # Show max 3 examples per node
            report.append(f"  {example['key']}: {example['value']}")
            report.append(f"    (from: {example['file']})")
    
    return "\n".join(report)


def save_node_categories(analysis_data: Dict[str, any], output_file: str):
    """Save categorized nodes for easier parser development."""
    
    categories = {
        'text_encoding': [],
        'image_processing': [],
        'samplers': [],
        'models': [],
        'controlnet': [],
        'lora': [],
        'conditioning': [],
        'utilities': [],
        'other': []
    }
    
    # Categorize nodes based on naming patterns
    for node in analysis_data['all_nodes']:
        node_lower = node.lower()
        
        if any(x in node_lower for x in ['clip', 'encode', 'text', 'prompt']):
            categories['text_encoding'].append(node)
        elif any(x in node_lower for x in ['image', 'preview', 'save', 'load', 'resize', 'crop']):
            categories['image_processing'].append(node)
        elif any(x in node_lower for x in ['sampler', 'ksampler', 'scheduler', 'noise']):
            categories['samplers'].append(node)
        elif any(x in node_lower for x in ['load', 'checkpoint', 'model', 'unet', 'vae']):
            categories['models'].append(node)
        elif any(x in node_lower for x in ['controlnet', 'control', 'canny', 'depth', 'pose']):
            categories['controlnet'].append(node)
        elif any(x in node_lower for x in ['lora', 'lycoris', 'locon']):
            categories['lora'].append(node)
        elif any(x in node_lower for x in ['condition', 'guidance', 'cfg']):
            categories['conditioning'].append(node)
        elif any(x in node_lower for x in ['reroute', 'primitive', 'note', 'switch']):
            categories['utilities'].append(node)
        else:
            categories['other'].append(node)
    
    # Sort each category
    for category in categories:
        categories[category].sort()
    
    # Save categorized data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)
    
    print(f"Categorized nodes saved to: {output_file}")


def main():
    """Main analysis function."""
    
    batch_nodes_dir = "/Users/duskfall/Desktop/Jsons_ForClaude/batch_nodes"
    output_dir = "/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools"
    
    print("Starting ComfyUI node analysis...")
    analysis_data = analyze_node_files(batch_nodes_dir)
    
    if not analysis_data:
        print("No analysis data generated. Check the directory path.")
        return
    
    # Generate and save report
    report = generate_analysis_report(analysis_data)
    report_file = os.path.join(output_dir, "comfyui_node_analysis_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Analysis report saved to: {report_file}")
    
    # Save categorized nodes
    categories_file = os.path.join(output_dir, "comfyui_node_categories.json")
    save_node_categories(analysis_data, categories_file)
    
    # Save raw node list
    nodes_file = os.path.join(output_dir, "all_comfyui_nodes.json")
    with open(nodes_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_nodes': len(analysis_data['all_nodes']),
            'all_nodes': analysis_data['all_nodes'],
            'node_counts': dict(analysis_data['node_counts'])
        }, f, indent=2, ensure_ascii=False)
    print(f"Raw node data saved to: {nodes_file}")
    
    print("\nAnalysis complete! Check the generated files for detailed results.")


if __name__ == "__main__":
    main()