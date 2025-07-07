#!/usr/bin/env python3

"""
Debug script for T5 outlier cases.
"""

import json

def test_t5_detection_rules():
    """Test T5 detection rules against outlier cases."""
    
    print("🔧 T5 OUTLIER DETECTION TEST")
    print("=" * 28)
    
    # Case 1: PixArt with T5TextEncode (not PixArtT5TextEncode)
    case1_workflow = {
        "nodes": [
            {"type": "PixArtCheckpointLoader", "inputs": {"ckpt_name": "pixart-PromptEcho-v1.safetensors"}},
            {"type": "T5v11Loader", "inputs": {"pytorch_model": "pytorch_model-00001-of-00002.bin"}},
            {"type": "T5TextEncode", "inputs": {"T5": [144, 0], "text": "Man in a suit"}},
            {"type": "KSampler", "inputs": {"seed": 70782476289330, "steps": 50, "cfg": 6.3}}
        ]
    }
    
    # Convert to JSON string for testing
    case1_json = json.dumps(case1_workflow)
    
    print("\\n1. Case 1: PixArt + T5TextEncode")
    print(f"   Contains PixArtCheckpointLoader: {'PixArtCheckpointLoader' in case1_json}")
    print(f"   Contains T5v11Loader: {'T5v11Loader' in case1_json}")
    print(f"   Contains T5TextEncode: {'T5TextEncode' in case1_json}")
    print(f"   Contains PixArtT5TextEncode: {'PixArtT5TextEncode' in case1_json}")
    
    # This should match T5 detection rules
    should_match_t5 = (
        'PixArtCheckpointLoader' in case1_json or 
        'T5v11Loader' in case1_json or 
        'T5TextEncode' in case1_json
    )
    print(f"   Should match T5 parser: {should_match_t5}")
    
    # Case 2: Test Unicode decoding for mojibake
    mojibake_text = "charset=Unicode 䄀 挀氀漀猀攀ⴀ甀瀀 瀀漀爀琀爀愀椀琀 漀昀 愀 眀漀洀愀渀"
    
    print("\\n2. Case 2: Mojibake Unicode")
    print(f"   Raw text preview: {mojibake_text[:50]}...")
    
    # Try to decode the mojibake
    try:
        # Remove charset prefix
        if mojibake_text.startswith("charset=Unicode "):
            unicode_part = mojibake_text[len("charset=Unicode "):]
            print(f"   Unicode part: {unicode_part[:50]}...")
            
            # This looks like UTF-16 encoded as UTF-8, try different approaches
            # Method 1: Try encoding back to bytes and decoding as UTF-16
            try:
                # Encode as latin-1 to get raw bytes, then decode as UTF-16
                raw_bytes = unicode_part.encode('latin-1')
                decoded = raw_bytes.decode('utf-16le', errors='ignore')
                print(f"   UTF-16LE decode: {decoded[:100]}...")
            except Exception as e:
                print(f"   UTF-16LE decode failed: {e}")
            
            # Method 2: Try UTF-16BE
            try:
                raw_bytes = unicode_part.encode('latin-1')
                decoded = raw_bytes.decode('utf-16be', errors='ignore')
                print(f"   UTF-16BE decode: {decoded[:100]}...")
            except Exception as e:
                print(f"   UTF-16BE decode failed: {e}")
                
    except Exception as e:
        print(f"   Unicode processing failed: {e}")
    
    print("\\n3. Detection Rule Analysis:")
    print("   T5 Detection Rules (should match either):")
    print("   ✓ DualCLIPLoader (FLUX/SD3)")
    print("   ✓ PixArtT5TextEncode (PixArt)")  
    print("   ✓ T5v11Loader (General T5)")
    print("   ✓ T5TextEncode (Direct T5)")
    print("   ✓ PixArtCheckpointLoader (PixArt)")
    
    print("\\n   Case 1 should match: T5v11Loader + T5TextEncode + PixArtCheckpointLoader")
    print("   Case 2 needs: Unicode decoding + A1111 FLUX parsing")

if __name__ == "__main__":
    test_t5_detection_rules()