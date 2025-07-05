#!/usr/bin/env python3

"""
Debug script to see what context data the MetadataEngine is actually getting.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_tools.metadata_engine import get_metadata_engine

def debug_engine_context():
    """Debug what context data the MetadataEngine is actually receiving."""
    
    print("🔍 DEBUGGING METADATA ENGINE CONTEXT")
    print("="*50)
    
    # The test metadata (same as in user's report)
    forge_metadata = """score_9, score_8_up,score_7_up, source_anime, rating_safe, 1girl, solo, <lora:EPhsrKafka:1> ,EPhsrKafka, purple hair, long hair, low ponytail, pink eyes, hair between eyes, eyewear on head, sunglasses, 

 hoop earrings, pink lips, oversized t-shirt, baggy pants, outstretched arms, blush smiling, sitting on couch, in living room, looking at viewer, pov, incoming hug,
Negative prompt: 3d, monochrome, simple background,
Steps: 24, Sampler: Euler a, CFG scale: 7, Seed: 2340366286, Size: 832x1216, Model hash: 529c72f6c3, Model: mfcgPDXL_v10, VAE hash: 735e4c3a44, VAE: sdxl_vae.safetensors, Denoising strength: 0.33, Clip skip: 2, ADetailer model: Anzhc Face seg 640 v2 y8n.pt, ADetailer confidence: 0.7, ADetailer dilate erode: 4, ADetailer mask blur: 4, ADetailer denoising strength: 0.4, ADetailer inpaint only masked: True, ADetailer inpaint padding: 32, ADetailer version: 24.5.1, Hires upscale: 1.5, Hires steps: 12, Hires upscaler: 4x_fatal_Anime_500000_G, Lora hashes: "EPhsrKafka: dba941975e80", Version: f0.0.17v1.8.0rc-latest-277-g0af28699, Hashes: {"vae": "63aeecb90f", "lora:EPhsrKafka": "5a3385485b", "model": "529c72f6c3"}"""
    
    try:
        parser_definitions_path = Path(__file__).parent / "parser_definitions"
        engine = get_metadata_engine(str(parser_definitions_path))
        
        # Create test image with metadata
        from PIL import Image
        from io import BytesIO
        
        img = Image.new("RGB", (832, 1216), color=(255, 0, 0))
        img.info["parameters"] = forge_metadata
        
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        img_bytes.name = "test_forge_image.jpg"
        
        # Let's peek into the context preparation by accessing the engine's internal method
        print("📝 PREPARING CONTEXT DATA:")
        print("-" * 30)
        
        # Access the engine's context preparation method
        context_data = engine._prepare_context_data(img_bytes)
        
        if context_data:
            print("✅ Context data prepared successfully")
            print(f"📊 Context keys: {list(context_data.keys())}")
            print()
            
            # Check the key areas that Forge detection relies on
            print("🔍 CHECKING KEY CONTEXT VALUES:")
            print("-" * 30)
            
            # Check pil_info
            pil_info = context_data.get("pil_info", {})
            print(f"📷 pil_info keys: {list(pil_info.keys())}")
            
            if "parameters" in pil_info:
                params = pil_info["parameters"]
                print(f"⚙️  parameters type: {type(params)}")
                print(f"⚙️  parameters length: {len(params) if isinstance(params, str) else 'N/A'}")
                print(f"⚙️  parameters preview: {params[:100] if isinstance(params, str) else params}...")
            else:
                print("❌ No 'parameters' key in pil_info")
            
            # Check raw_user_comment_str
            user_comment = context_data.get("raw_user_comment_str")
            print(f"📄 raw_user_comment_str: {user_comment}")
            
            # Check what the rule evaluator would get
            print()
            print("🧪 TESTING RULE EVALUATOR ACCESS:")
            print("-" * 30)
            
            # Simulate what _get_a1111_param_string would return
            param_str = context_data.get("pil_info", {}).get("parameters")
            if isinstance(param_str, str):
                print(f"✅ Rule evaluator would get A1111 string from pil_info['parameters']")
                print(f"📏 Length: {len(param_str)}")
                
                # Test the actual Forge version pattern
                import re
                forge_pattern = r"Version: f\d+\.\d+\.\d+.*"
                forge_match = re.search(forge_pattern, param_str)
                if forge_match:
                    print(f"✅ Forge pattern FOUND: '{forge_match.group()}'")
                else:
                    print(f"❌ Forge pattern NOT FOUND")
            else:
                fallback = context_data.get("raw_user_comment_str")
                print(f"⚠️  Rule evaluator would fall back to raw_user_comment_str: {fallback}")
            
        else:
            print("❌ Failed to prepare context data")
            return False
            
    except Exception as e:
        print(f"💥 ERROR during debug: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = debug_engine_context()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)