#!/usr/bin/env python3

"""
Test ComfyUI detection rules for the CivitAI file.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_comfyui_detection():
    """Test ComfyUI detection rules."""
    
    print("🔍 COMFYUI DETECTION TEST")
    print("=" * 25)
    
    test_file = "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_08965_.jpeg"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found")
        return
    
    print(f"📁 Testing: {Path(test_file).name}")
    
    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer
        from dataset_tools.rule_evaluator import RuleEvaluator
        from dataset_tools.logger import get_logger
        
        # Get context
        preparer = ContextDataPreparer()
        context = preparer.prepare_context(test_file)
        
        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            print(f"✅ UserComment: {len(user_comment)} chars")
            
            # Check specific content
            has_ksampler = "KSampler" in user_comment
            has_extrametadata = "extraMetadata" in user_comment
            has_class_type = "class_type" in user_comment
            is_valid_json = user_comment.startswith('{"') and user_comment.endswith('}')
            
            print(f"   Contains KSampler: {has_ksampler}")
            print(f"   Contains extraMetadata: {has_extrametadata}")
            print(f"   Contains class_type: {has_class_type}")
            print(f"   Looks like JSON: {is_valid_json}")
            
            # Test JSON parsing
            if is_valid_json:
                try:
                    import json
                    workflow_data = json.loads(user_comment)
                    print(f"   ✅ Valid JSON: {len(workflow_data)} keys")
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON parse failed: {e}")
                    
            print("\n🔧 Testing ComfyUI JPEG EXIF detection rules...")
            
            # Test the detection rules manually
            logger = get_logger("ComfyUI_Test")
            evaluator = RuleEvaluator(logger)
            
            # Load ComfyUI JPEG EXIF parser definition
            import json
            parser_path = os.path.join(os.path.dirname(__file__), "parser_definitions", "ComfyUI_JPEG_EXIF.json")
            with open(parser_path, 'r') as f:
                parser_def = json.load(f)
            
            print(f"Parser: {parser_def['parser_name']} (priority {parser_def['priority']})")
            
            for i, rule in enumerate(parser_def.get('detection_rules', [])):
                print(f"\n   Rule {i+1}: {rule.get('comment', 'No comment')}")
                try:
                    result = evaluator.evaluate_rule(rule, context)
                    print(f"   Result: {'✅ PASS' if result else '❌ FAIL'}")
                    
                    if not result:
                        # Debug why it failed
                        source_data, source_found = evaluator._get_source_data_and_status(rule, context)
                        print(f"   Source found: {source_found}")
                        if source_data:
                            print(f"   Source type: {type(source_data)}")
                            if isinstance(source_data, str):
                                print(f"   Source length: {len(source_data)}")
                                operator = rule.get('operator')
                                value = rule.get('value')
                                if operator == 'contains':
                                    contains_result = value in source_data
                                    print(f"   Contains '{value}': {contains_result}")
                                elif operator == 'does_not_contain':
                                    not_contains_result = value not in source_data
                                    print(f"   Does not contain '{value}': {not_contains_result}")
                                elif operator == 'is_valid_json':
                                    try:
                                        json.loads(source_data)
                                        print(f"   Is valid JSON: True")
                                    except:
                                        print(f"   Is valid JSON: False")
                                        
                except Exception as e:
                    print(f"   Error: {e}")
        else:
            print("❌ No UserComment found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comfyui_detection()