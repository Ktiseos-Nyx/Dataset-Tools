#!/usr/bin/env python3

"""
Debug script to understand why Forge rules aren't matching.
"""

import sys
import re
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_forge_rules_manually():
    """Test Forge detection rules manually to see what's happening."""
    
    print("🐛 DEBUGGING FORGE DETECTION RULES")
    print("="*50)
    
    # The test metadata (same as in user's report)
    forge_metadata = """score_9, score_8_up,score_7_up, source_anime, rating_safe, 1girl, solo, <lora:EPhsrKafka:1> ,EPhsrKafka, purple hair, long hair, low ponytail, pink eyes, hair between eyes, eyewear on head, sunglasses, 

 hoop earrings, pink lips, oversized t-shirt, baggy pants, outstretched arms, blush smiling, sitting on couch, in living room, looking at viewer, pov, incoming hug,
Negative prompt: 3d, monochrome, simple background,
Steps: 24, Sampler: Euler a, CFG scale: 7, Seed: 2340366286, Size: 832x1216, Model hash: 529c72f6c3, Model: mfcgPDXL_v10, VAE hash: 735e4c3a44, VAE: sdxl_vae.safetensors, Denoising strength: 0.33, Clip skip: 2, ADetailer model: Anzhc Face seg 640 v2 y8n.pt, ADetailer confidence: 0.7, ADetailer dilate erode: 4, ADetailer mask blur: 4, ADetailer denoising strength: 0.4, ADetailer inpaint only masked: True, ADetailer inpaint padding: 32, ADetailer version: 24.5.1, Hires upscale: 1.5, Hires steps: 12, Hires upscaler: 4x_fatal_Anime_500000_G, Lora hashes: "EPhsrKafka: dba941975e80", Version: f0.0.17v1.8.0rc-latest-277-g0af28699, Hashes: {"vae": "63aeecb90f", "lora:EPhsrKafka": "5a3385485b", "model": "529c72f6c3"}"""
    
    print("📝 Test metadata preview:")
    print(forge_metadata[:200] + "...")
    print()
    
    # Test Forge detection rules manually
    print("🔍 TESTING FORGE DETECTION RULES:")
    print("-" * 40)
    
    # Rule 1: Must first look like a standard A1111 text block
    rule1_patterns = ["Steps:", "Sampler:", "Seed:"]
    print("Rule 1: A1111 text block patterns")
    for pattern in rule1_patterns:
        found = pattern in forge_metadata
        print(f"   ✅ '{pattern}': {'FOUND' if found else 'NOT FOUND'}")
    
    rule1_pass = all(pattern in forge_metadata for pattern in rule1_patterns)
    print(f"   🏁 Rule 1 result: {'PASS' if rule1_pass else 'FAIL'}")
    print()
    
    # Rule 2: Must contain Forge-specific signature
    forge_pattern = r"Version: f\d+\.\d+\.\d+.*"
    print("Rule 2: Forge-specific version pattern")
    print(f"   🔍 Pattern: {forge_pattern}")
    
    forge_match = re.search(forge_pattern, forge_metadata)
    if forge_match:
        print(f"   ✅ FOUND: '{forge_match.group()}'")
        rule2_pass = True
    else:
        print(f"   ❌ NOT FOUND")
        rule2_pass = False
        
        # Let's see what version strings are there
        version_matches = re.findall(r"Version: [^\n,]+", forge_metadata)
        if version_matches:
            print(f"   💡 Found other version strings: {version_matches}")
        else:
            print(f"   💡 No version strings found at all")
    
    print(f"   🏁 Rule 2 result: {'PASS' if rule2_pass else 'FAIL'}")
    print()
    
    # Overall result
    overall_pass = rule1_pass and rule2_pass
    print(f"🎯 OVERALL FORGE DETECTION: {'PASS' if overall_pass else 'FAIL'}")
    print()
    
    if not overall_pass:
        print("🔧 DEBUGGING SUGGESTIONS:")
        if not rule1_pass:
            print("   - Rule 1 failed: Missing basic A1111 patterns")
        if not rule2_pass:
            print("   - Rule 2 failed: Forge version pattern not matching")
            print("   - Check if the version string format is different")
    
    return overall_pass

if __name__ == "__main__":
    success = test_forge_rules_manually()
    print(f"\n{'🎉 RULES PASS' if success else '❌ RULES FAIL'}")
    sys.exit(0 if success else 1)