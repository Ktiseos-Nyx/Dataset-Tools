#!/usr/bin/env python3
"""Test modern ComfyUI architectures (FLUX, SD3, PixArt, HiDream, Auraflow)."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')

from dataset_tools.metadata_parser import parse_metadata

def test_modern_architectures():
    """Test modern ComfyUI architectures that use KSamplerSelect."""
    
    # Test files that are known to use modern architectures
    test_files = [
        "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_00180_.png",  # PixArt workflow
        "/Users/duskfall/Downloads/image_workflows_for_Dusk/animugirl1.png",  # Wildcard workflow
        "/Users/duskfall/Downloads/image_workflows_for_Dusk/animugirl2.png",  # Another wildcard
    ]
    
    print("🔍 Testing modern ComfyUI architectures...")
    print("="*100)
    
    results = {
        'total_files': 0,
        'successful_positive': 0,
        'successful_negative': 0,
        'failed_extraction': 0,
        'modern_architecture_detected': 0
    }
    
    for i, test_file in enumerate(test_files):
        if not Path(test_file).exists():
            print(f"{i+1:2d}. {Path(test_file).name[:40]:<40} | ❌ File not found")
            continue
            
        results['total_files'] += 1
        
        try:
            result = parse_metadata(str(test_file))
            
            # Check if it's detected as ComfyUI
            tool = result.get('metadata_info_section', {}).get('Detected Tool', 'Unknown')
            
            if tool != 'ComfyUI':
                print(f"{i+1:2d}. {Path(test_file).name[:40]:<40} | ❌ Not ComfyUI ({tool})")
                continue
            
            # Check prompt extraction
            prompts = result.get('prompt_data_section', {})
            positive = prompts.get('Positive', '').strip()
            negative = prompts.get('Negative', '').strip()
            
            status_positive = "✅" if positive else "❌"
            status_negative = "✅" if negative else "⚪"  # Empty negative is OK
            
            if positive:
                results['successful_positive'] += 1
            if negative:
                results['successful_negative'] += 1
            if not positive:
                results['failed_extraction'] += 1
            
            # Check if modern architecture was detected
            raw_data = result.get('raw_tool_specific_data_section', {})
            if raw_data and isinstance(raw_data, str):
                import json
                try:
                    raw_data = json.loads(raw_data)
                except:
                    pass
            
            modern_detected = False
            if isinstance(raw_data, dict) and 'nodes' in raw_data:
                nodes = raw_data['nodes']
                if isinstance(nodes, list):
                    for node in nodes:
                        if isinstance(node, dict) and node.get('class_type') == 'KSamplerSelect':
                            modern_detected = True
                            results['modern_architecture_detected'] += 1
                            break
                elif isinstance(nodes, dict):
                    for node in nodes.values():
                        if isinstance(node, dict) and node.get('class_type') == 'KSamplerSelect':
                            modern_detected = True
                            results['modern_architecture_detected'] += 1
                            break
            
            arch_indicator = "🏗️" if modern_detected else "🏛️"
            
            # Show preview
            pos_preview = positive[:50] + "..." if len(positive) > 50 else positive
            neg_preview = negative[:30] + "..." if len(negative) > 30 else negative
            
            print(f"{i+1:2d}. {Path(test_file).name[:40]:<40} | {arch_indicator} {status_positive} Pos: {pos_preview:<55} | {status_negative} Neg: {neg_preview}")
            
        except Exception as e:
            print(f"{i+1:2d}. {Path(test_file).name[:40]:<40} | 💥 ERROR: {str(e)[:50]}")
            continue
    
    print("\\n" + "="*100)
    print("📊 MODERN ARCHITECTURE TEST SUMMARY:")
    print("="*100)
    print(f"Total files tested: {results['total_files']}")
    print(f"Modern architecture detected: {results['modern_architecture_detected']}")
    print(f"")
    print(f"✅ Successful positive extraction: {results['successful_positive']}/{results['total_files']} ({results['successful_positive']/max(results['total_files'],1)*100:.1f}%)")
    print(f"✅ Successful negative extraction: {results['successful_negative']}/{results['total_files']} ({results['successful_negative']/max(results['total_files'],1)*100:.1f}%)")
    print(f"❌ Failed extractions: {results['failed_extraction']}/{results['total_files']} ({results['failed_extraction']/max(results['total_files'],1)*100:.1f}%)")
    
    if results['failed_extraction'] == 0:
        print(f"\\n🎉 SUCCESS: All modern architecture workflows are extracting prompts correctly!")
    else:
        print(f"\\n🚨 ISSUES: {results['failed_extraction']} modern architecture files are not extracting prompts!")

if __name__ == "__main__":
    test_modern_architectures()