#!/usr/bin/env python3

"""
Test SD.Next detection with the updated priority.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_tools.metadata_engine import get_metadata_engine

def test_sdnext_detection():
    """Test SD.Next detection."""
    
    # Create test context with SD.Next metadata
    test_metadata = """<lora:When_Life_Gives_You_Lemons-000005:1.0>wl_lemons,an old man, wearing thick glasses with yellow lemon lenses, on a beach, portrait, head partially turned, looking away, candid,  <lora:DetailTweakerXL:1.0>
Negative prompt: 
Steps: 30, Size: 832x1216, Sampler: DPM++ 2M, Seed: 3873706916, CFG scale: 6, CFG rescale: 0.7, Model: SDXLFaetastic_v24, Model hash: 07b985d12f, App: SD.Next, Version: cb0eb55, Backend: Diffusers, Pipeline: StableDiffusionXLImg2ImgPipeline, Parser: native, Operations: upscale; img2img, Refine: True, Hires force: False, Hires steps: 20, HiRes mode: 1, Hires upscaler: ESRGAN 4x Remacri, Hires scale: 2, Hires size: 1664x2432, Hires strength: 0.3, Hires sampler: DPM2++ 3M SDE FlowMatch, Hires CFG scale: 6, Init image size: 832x1216, Init image hash: f33bac7b, Image CFG scale: 6, Resize scale: 1, Denoising strength: 0.3, Resize mode: Fixed, Sampler sigma: karras, Sampler dynamic shift: False, LoRA networks: "When_Life_Gives_You_Lemons-000005, DetailTweakerXL"""
    
    parser_definitions_path = Path(__file__).parent / "parser_definitions"
    
    print("🔍 TESTING SD.NEXT DETECTION")
    print("=" * 50)
    
    # Create engine
    engine = get_metadata_engine(str(parser_definitions_path))
    
    # Show parser priorities
    print("📋 PARSER PRIORITIES:")
    print("-" * 20)
    for parser_data in engine.sorted_definitions[:10]:  # Show top 10
        parser_name = parser_data.get('parser_name', 'Unknown')
        priority = parser_data.get('priority', 0)
        print(f"  {parser_name}: {priority}")
    print()
    
    # Create test context
    context = {
        'raw_user_comment_str': test_metadata,
        'pil_info': {},
        'file_extension': 'png'
    }
    
    # Test SD.Next parser specifically
    sdnext_parser = None
    a1111_parser = None
    
    for parser_data in engine.sorted_definitions:
        if parser_data.get('parser_name') == 'SD_Next':
            sdnext_parser = parser_data
        elif parser_data.get('parser_name') == 'a1111_webui':
            a1111_parser = parser_data
    
    if sdnext_parser:
        print("🧪 TESTING SD.NEXT PARSER:")
        print(f"Priority: {sdnext_parser.get('priority', 0)}")
        
        detection_rules = sdnext_parser.get('detection_rules', [])
        all_pass = True
        for i, rule in enumerate(detection_rules):
            result = engine.rule_evaluator.evaluate_rule(rule, context)
            print(f"  Rule {i+1}: {result} - {rule.get('comment', 'No comment')}")
            if not result:
                all_pass = False
        
        print(f"  Overall SD.Next match: {all_pass}")
        print()
    
    if a1111_parser:
        print("🧪 TESTING A1111 PARSER:")
        print(f"Priority: {a1111_parser.get('priority', 0)}")
        
        detection_rules = a1111_parser.get('detection_rules', [])
        all_pass = True
        for i, rule in enumerate(detection_rules):
            result = engine.rule_evaluator.evaluate_rule(rule, context)
            print(f"  Rule {i+1}: {result} - {rule.get('comment', 'No comment')}")
            if not result:
                all_pass = False
        
        print(f"  Overall A1111 match: {all_pass}")
        print()
    
    print("🎯 EXPECTED RESULT:")
    print("SD.Next should be detected (higher priority + more specific rules)")
    
    return True

if __name__ == "__main__":
    success = test_sdnext_detection()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)