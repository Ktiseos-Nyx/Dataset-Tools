#!/usr/bin/env python3
"""Test wildcard-based ComfyUI workflows."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise

from dataset_tools.metadata_parser import parse_metadata

def test_wildcard_workflows():
    """Test wildcard-based ComfyUI workflows."""
    
    test_dir = Path("/Users/duskfall/Downloads/image_workflows_for_Dusk")
    if not test_dir.exists():
        print(f"❌ Directory not found: {test_dir}")
        return
    
    # Get all PNG files
    png_files = list(test_dir.glob("*.png"))
    print(f"🔍 Testing {len(png_files)} wildcard workflow files...")
    print("="*100)
    
    results = {
        'total_files': 0,
        'comfyui_files': 0,
        'successful_positive': 0,
        'successful_negative': 0,
        'failed_extraction': 0,
        'non_comfyui': 0
    }
    
    for i, png_file in enumerate(png_files):
        results['total_files'] += 1
        
        try:
            result = parse_metadata(str(png_file))
            
            # Check if it's detected as ComfyUI
            tool = result.get('metadata_info_section', {}).get('Detected Tool', 'Unknown')
            
            if tool != 'ComfyUI':
                results['non_comfyui'] += 1
                print(f"{i+1:2d}. {png_file.name[:30]:<30} | ❌ Not ComfyUI ({tool})")
                continue
            
            results['comfyui_files'] += 1
            
            # Check prompt extraction
            prompts = result.get('prompt_data_section', {})
            positive = prompts.get('Positive', '').strip()
            negative = prompts.get('Negative', '').strip()
            
            status_positive = "✅" if positive else "❌"
            status_negative = "✅" if negative else "⚪"  # Empty negative is OK for FLUX
            
            if positive:
                results['successful_positive'] += 1
            if negative:
                results['successful_negative'] += 1
            if not positive:
                results['failed_extraction'] += 1
                
            # Show preview
            pos_preview = positive[:40] + "..." if len(positive) > 40 else positive
            neg_preview = negative[:40] + "..." if len(negative) > 40 else negative
            
            print(f"{i+1:2d}. {png_file.name[:30]:<30} | {status_positive} Pos: {pos_preview:<45} | {status_negative} Neg: {neg_preview}")
            
        except Exception as e:
            print(f"{i+1:2d}. {png_file.name[:30]:<30} | 💥 ERROR: {str(e)[:50]}")
            continue
    
    print("\n" + "="*100)
    print("📊 WILDCARD WORKFLOW SUMMARY:")
    print("="*100)
    print(f"Total files tested: {results['total_files']}")
    print(f"ComfyUI files: {results['comfyui_files']}")
    print(f"Non-ComfyUI files: {results['non_comfyui']}")
    print(f"")
    print(f"✅ Successful positive extraction: {results['successful_positive']}/{results['comfyui_files']} ({results['successful_positive']/max(results['comfyui_files'],1)*100:.1f}%)")
    print(f"✅ Successful negative extraction: {results['successful_negative']}/{results['comfyui_files']} ({results['successful_negative']/max(results['comfyui_files'],1)*100:.1f}%)")
    print(f"❌ Failed extractions: {results['failed_extraction']}/{results['comfyui_files']} ({results['failed_extraction']/max(results['comfyui_files'],1)*100:.1f}%)")
    
    if results['failed_extraction'] > 0:
        print(f"\n🚨 WILDCARD ISSUES: {results['failed_extraction']} wildcard workflow files are not extracting prompts!")
    else:
        print(f"\n🎉 SUCCESS: All wildcard workflow files are extracting prompts correctly!")

if __name__ == "__main__":
    test_wildcard_workflows()