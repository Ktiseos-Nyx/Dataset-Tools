#!/usr/bin/env python3
"""Add advanced node discovery to existing ComfyUI parsers"""

import json
import shutil
from pathlib import Path

def enhance_parser_definitions():
    """Add advanced extractors to existing ComfyUI parser definitions"""
    
    parser_dir = Path("dataset_tools/parser_definitions")
    backup_dir = Path("parser_backups")
    
    # Create backup directory
    backup_dir.mkdir(exist_ok=True)
    
    # Advanced extraction fields to add
    advanced_fields = [
        {
            "comment": "🎯 TIPO AI Prompt Enhancement Detection",
            "target_key": "tipo_enhancement",
            "method": "comfyui_detect_tipo_enhancement"
        },
        {
            "comment": "📊 Workflow Complexity Analysis", 
            "target_key": "workflow_complexity",
            "method": "comfyui_calculate_workflow_complexity"
        },
        {
            "comment": "🚀 Advanced Upscaling Detection",
            "target_key": "advanced_upscaling",
            "method": "comfyui_detect_advanced_upscaling"
        },
        {
            "comment": "🎨 Multi-Stage Conditioning Detection",
            "target_key": "multi_stage_conditioning", 
            "method": "comfyui_detect_multi_stage_conditioning"
        },
        {
            "comment": "✨ Post-Processing Effects Detection",
            "target_key": "post_processing_effects",
            "method": "comfyui_detect_post_processing_effects"
        },
        {
            "comment": "🔌 Custom Node Ecosystem Detection",
            "target_key": "custom_node_ecosystems",
            "method": "comfyui_detect_custom_node_ecosystems"
        },
        {
            "comment": "🎯 High-Level Workflow Techniques",
            "target_key": "workflow_techniques",
            "method": "comfyui_extract_workflow_techniques"
        }
    ]
    
    # Target ComfyUI parsers to enhance
    target_parsers = [
        "comfyui.json",
        "comfyui_generic.json", 
        "ComfyUI_JPEG_EXIF.json",
        "simple_comfyui_parser.json",
        "ComfyUI_Simple.json",
        "comfyui_flux_gguf_style.json",
        "tensorart_comfyui.json",
        "civitai_comfyui.json",
        "comfyui_custom_ecosystem.json",
        "comfyui_advanced_sampling.json",
        "t5_detection_system.json",
        "pixart_sigma_parser.json",
        "pixart_sigma_enhanced.json"
    ]
    
    enhanced_count = 0
    
    for parser_file in target_parsers:
        parser_path = parser_dir / parser_file
        
        if not parser_path.exists():
            print(f"⚠️  Parser not found: {parser_file}")
            continue
            
        print(f"🔧 Enhancing parser: {parser_file}")
        
        # Backup original
        backup_path = backup_dir / parser_file
        shutil.copy2(parser_path, backup_path)
        print(f"   💾 Backed up to: {backup_path}")
        
        try:
            # Load parser definition
            with open(parser_path, 'r', encoding='utf-8') as f:
                parser_def = json.load(f)
            
            # Check if it has fields to enhance
            if 'parsing_instructions' not in parser_def:
                print(f"   ⚠️  No parsing_instructions found, skipping")
                continue
                
            if 'fields' not in parser_def['parsing_instructions']:
                print(f"   ⚠️  No fields found, skipping")
                continue
            
            # Check if already enhanced
            existing_fields = parser_def['parsing_instructions']['fields']
            if any(field.get('target_key') == 'workflow_complexity' for field in existing_fields):
                print(f"   ✅ Already enhanced, skipping")
                continue
            
            # Add advanced fields
            original_field_count = len(existing_fields)
            parser_def['parsing_instructions']['fields'].extend(advanced_fields)
            
            # Update priority to ensure enhanced parsers are preferred
            if 'priority' in parser_def:
                parser_def['priority'] += 10
            
            # Add enhancement marker
            parser_def['enhanced_with_node_discovery'] = True
            parser_def['enhancement_date'] = "2025-07-08"
            
            # Save enhanced parser
            with open(parser_path, 'w', encoding='utf-8') as f:
                json.dump(parser_def, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ Enhanced! Added {len(advanced_fields)} advanced fields")
            print(f"      Fields: {original_field_count} → {len(parser_def['parsing_instructions']['fields'])}")
            print(f"      Priority: {parser_def.get('priority', 'N/A')}")
            enhanced_count += 1
            
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON error in {parser_file}: {e}")
        except Exception as e:
            print(f"   ❌ Error enhancing {parser_file}: {e}")
    
    print(f"\n🎉 ENHANCEMENT COMPLETE!")
    print(f"   Enhanced parsers: {enhanced_count}")
    print(f"   Backup directory: {backup_dir}")
    print(f"   Advanced fields added per parser: {len(advanced_fields)}")
    
    print(f"\n📋 Advanced capabilities now available:")
    for field in advanced_fields:
        print(f"   • {field['comment']}")

if __name__ == "__main__":
    print("🚀 Enhancing Existing ComfyUI Parsers with Advanced Node Discovery")
    print("=" * 70)
    enhance_parser_definitions()