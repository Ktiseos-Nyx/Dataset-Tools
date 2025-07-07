#!/usr/bin/env python3

"""
Analyze the workflow to see what sampling nodes it contains.
"""

import sys
import os
from pathlib import Path
import json

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_workflow():
    """Analyze the ComfyUI workflow content."""
    
    test_file = "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_08965_.jpeg"
    
    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer
        
        preparer = ContextDataPreparer()
        context = preparer.prepare_context(test_file)
        
        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            workflow_data = json.loads(user_comment)
            
            print("🔍 WORKFLOW ANALYSIS")
            print("=" * 20)
            print(f"Workflow keys: {list(workflow_data.keys())}")
            
            if "prompt" in workflow_data:
                nodes = workflow_data["prompt"]
                print(f"Nodes count: {len(nodes)}")
                
                # Analyze node types
                class_types = {}
                for node_id, node_data in nodes.items():
                    if isinstance(node_data, dict) and "class_type" in node_data:
                        class_type = node_data["class_type"]
                        class_types[class_type] = class_types.get(class_type, 0) + 1
                
                print("\n📊 Node types:")
                for class_type, count in sorted(class_types.items()):
                    print(f"   {class_type}: {count}")
                    
                # Look for sampling-related nodes
                sampling_nodes = [ct for ct in class_types.keys() if any(keyword in ct.lower() for keyword in ["sampl", "denois", "noise", "scheduler", "sigmas"])]
                
                print(f"\n🎯 Sampling-related nodes:")
                for node in sampling_nodes:
                    print(f"   {node}: {class_types[node]}")
                    
                # Look for specific patterns
                print(f"\n🔍 Pattern analysis:")
                workflow_str = json.dumps(workflow_data)
                patterns = ["KSampler", "SamplerCustom", "RandomNoise", "BasicScheduler", "SamplerDPMPP", "SamplerEuler"]
                for pattern in patterns:
                    found = pattern in workflow_str
                    print(f"   {pattern}: {'✅' if found else '❌'}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_workflow()