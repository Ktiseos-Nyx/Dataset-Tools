#!/usr/bin/env python3

"""
Debug A1111 JPEG support loss after Unicode handling enhancements.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_a1111_jpeg_debug():
    """Debug A1111 JPEG detection and extraction."""
    
    print("🔍 A1111 JPEG DEBUG TEST")
    print("=" * 25)
    
    # Test with the Unicode A1111 FLUX file
    test_file = "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_01803_.jpeg"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {Path(test_file).name}")
        return
    
    print(f"📁 Testing: {Path(test_file).name}")
    
    # Step 1: Test context preparation
    print("\n1️⃣ CONTEXT PREPARATION")
    print("-" * 22)
    
    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer
        
        preparer = ContextDataPreparer()
        context = preparer.prepare_context(test_file)
        
        if not context:
            print("❌ Context preparation failed")
            return
        
        print(f"✅ Context prepared with {len(context)} keys")
        
        # Check UserComment extraction
        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            print(f"✅ UserComment extracted: {len(user_comment)} characters")
            print(f"   Preview: {user_comment[:100]}...")
            
            # Check if it contains A1111 patterns
            a1111_patterns = ["Steps:", "Sampler:", "CFG scale:", "Seed:", "Size:"]
            found_patterns = [p for p in a1111_patterns if p in user_comment]
            print(f"   A1111 patterns found: {found_patterns}")
        else:
            print("❌ No UserComment extracted")
            
        # Check pil_info parameters
        pil_params = context.get("pil_info", {}).get("parameters")
        if pil_params:
            print(f"✅ PIL parameters found: {len(pil_params)} characters")
            print(f"   Preview: {pil_params[:100]}...")
        else:
            print("❌ No PIL parameters found")
            
    except Exception as e:
        print(f"❌ Context preparation error: {e}")
        return
    
    # Step 2: Test rule evaluation
    print("\n2️⃣ RULE EVALUATION")
    print("-" * 18)
    
    try:
        from dataset_tools.rule_evaluator import RuleEvaluator
        from dataset_tools.logger import get_logger
        
        logger = get_logger("A1111_Debug")
        evaluator = RuleEvaluator(logger)
        
        # Test the A1111 detection rules manually
        print("Testing A1111 detection rules...")
        
        # Load A1111 parser definition
        import json
        a1111_parser_path = os.path.join(os.path.dirname(__file__), "parser_definitions", "a1111_webui.json")
        with open(a1111_parser_path, 'r') as f:
            a1111_def = json.load(f)
        
        print(f"A1111 parser priority: {a1111_def.get('priority')}")
        print(f"Detection rules count: {len(a1111_def.get('detection_rules', []))}")
        
        # Test each detection rule
        for i, rule in enumerate(a1111_def.get('detection_rules', [])):
            print(f"\n   Rule {i+1}: {rule.get('comment', 'No comment')}")
            try:
                result = evaluator.evaluate_rule(rule, context)
                print(f"   Result: {'✅ PASS' if result else '❌ FAIL'}")
                
                if not result and rule.get('operator') in ['AND', 'OR']:
                    # Debug composite rules
                    print("   Debugging composite rule...")
                    for j, sub_rule in enumerate(rule.get('rules', [])):
                        print(f"     Sub-rule {j+1}: {sub_rule.get('comment', 'No comment')}")
                        try:
                            sub_result = evaluator.evaluate_rule(sub_rule, context)
                            print(f"     Result: {'✅ PASS' if sub_result else '❌ FAIL'}")
                        except Exception as sub_e:
                            print(f"     Error: {sub_e}")
                elif not result and rule.get('source_type') == 'a1111_parameter_string_content':
                    # Debug the a1111_parameter_string_content source
                    print("   Debugging a1111_parameter_string_content...")
                    source_data, source_found = evaluator._get_source_data_and_status(rule, context)
                    print(f"   Source found: {source_found}")
                    if source_data:
                        print(f"   Source data length: {len(source_data)}")
                        print(f"   Source preview: {source_data[:100]}...")
                        
                        # Test the regex patterns manually
                        if rule.get('operator') == 'regex_match_all':
                            patterns = rule.get('regex_patterns', [])
                            print(f"   Testing patterns: {patterns}")
                            for pattern in patterns:
                                found = pattern in source_data
                                print(f"     '{pattern}': {'✅' if found else '❌'}")
                    
            except Exception as e:
                print(f"   Error: {e}")
            
    except Exception as e:
        print(f"❌ Rule evaluation error: {e}")
    
    # Step 3: Test full metadata engine
    print("\n3️⃣ METADATA ENGINE")
    print("-" * 17)
    
    try:
        from dataset_tools.metadata_engine import MetadataEngine
        
        parser_definitions_path = os.path.join(os.path.dirname(__file__), "parser_definitions")
        engine = MetadataEngine(parser_definitions_path)
        result = engine.get_parser_for_file(test_file)
        
        if result:
            print(f"✅ MetadataEngine result: {type(result)}")
            if isinstance(result, dict):
                tool = result.get("tool", "Unknown")
                print(f"   Tool detected: {tool}")
                
                if tool == "Automatic1111 WebUI":
                    print("   ✅ Correctly identified as A1111")
                    
                    # Check key fields
                    prompt = result.get("prompt", "")
                    steps = result.get("parameters", {}).get("steps", "")
                    seed = result.get("parameters", {}).get("seed", "")
                    
                    print(f"   Prompt: {prompt[:50]}..." if prompt else "   No prompt")
                    print(f"   Steps: {steps}")
                    print(f"   Seed: {seed}")
                else:
                    print(f"   ❌ Incorrectly identified as: {tool}")
            else:
                print(f"   ❌ Unexpected result type: {type(result)}")
        else:
            print("❌ MetadataEngine returned None")
            
    except Exception as e:
        print(f"❌ MetadataEngine error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎯 EXPECTED BEHAVIOR:")
    print("   • Context should extract A1111 parameters from UserComment")
    print("   • A1111 parser should detect the parameter patterns")
    print("   • MetadataEngine should identify as 'Automatic1111 WebUI'")
    print("   • All A1111 fields should be extracted correctly")

if __name__ == "__main__":
    test_a1111_jpeg_debug()