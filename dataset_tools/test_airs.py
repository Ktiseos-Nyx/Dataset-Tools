#!/usr/bin/env python3

"""
Check the CivitAI airs field content.
"""

import sys
import os
from pathlib import Path
import json

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_airs():
    """Check the airs field content."""
    
    test_file = "/Users/duskfall/Downloads/Metadata Samples/B4V0V3FKDVZHZZRERKQ31YFR10.jpeg"
    
    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer
        
        preparer = ContextDataPreparer()
        context = preparer.prepare_context(test_file)
        
        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            data = json.loads(user_comment)
            
            if "extra" in data and "airs" in data["extra"]:
                airs_data = data["extra"]["airs"]
                print(f"📊 AIRS DATA ANALYSIS:")
                print(f"   Type: {type(airs_data).__name__}")
                print(f"   Content: {airs_data}")
                
                if isinstance(airs_data, str):
                    try:
                        parsed = json.loads(airs_data)
                        print(f"   ✅ AIRS is JSON with keys: {list(parsed.keys())}")
                        for key, value in parsed.items():
                            print(f"      {key}: {str(value)[:100]}...")
                    except:
                        print(f"   ❌ AIRS is not JSON")
            
            # Also check for URN patterns in the workflow
            workflow_str = json.dumps(data)
            urn_count = workflow_str.count("urn:air:")
            civitai_count = workflow_str.count("civitai:")
            
            print(f"\n🔍 URN ANALYSIS:")
            print(f"   URN patterns found: {urn_count}")
            print(f"   CivitAI patterns found: {civitai_count}")
            
            if urn_count > 0:
                print(f"   ✅ This is DEFINITELY a CivitAI file!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_airs()