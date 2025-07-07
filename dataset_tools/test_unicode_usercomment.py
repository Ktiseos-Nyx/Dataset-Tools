#!/usr/bin/env python3

"""
Test Unicode UserComment decoding for A1111-style FLUX metadata.
"""

def decode_unicode_usercomment():
    """Test decoding the Unicode UserComment from the JPEG."""
    
    print("🔧 UNICODE USERCOMMENT DECODING TEST")
    print("=" * 35)
    
    # Sample bytes from the exiftool output
    # 55 4e 49 43 4f 44 45 00 00 41 00 20 00 63 00 6c 00 6f 00 73 00 65 00 2d 00 75 00 70
    # U  N  I  C  O  D  E  \0 \0 A  \0    \0 c  \0 l  \0 o  \0 s  \0 e  \0 -  \0 u  \0 p
    
    sample_bytes = bytes([
        0x55, 0x4e, 0x49, 0x43, 0x4f, 0x44, 0x45, 0x00, 0x00,  # "UNICODE\0\0"
        0x41, 0x00, 0x20, 0x00, 0x63, 0x00, 0x6c, 0x00, 0x6f, 0x00, 0x73, 0x00, 0x65, 0x00, 0x2d, 0x00,
        0x75, 0x00, 0x70, 0x00, 0x20, 0x00, 0x70, 0x00, 0x6f, 0x00, 0x72, 0x00, 0x74, 0x00, 0x72, 0x00,
        0x61, 0x00, 0x69, 0x00, 0x74, 0x00, 0x20, 0x00, 0x6f, 0x00, 0x66, 0x00, 0x20, 0x00, 0x61, 0x00
    ])
    
    print(f"Sample bytes length: {len(sample_bytes)}")
    print(f"Raw bytes: {sample_bytes[:20].hex()}")
    
    # Check for UNICODE prefix
    if sample_bytes.startswith(b'UNICODE\x00\x00'):
        print("✅ Found UNICODE prefix")
        
        # Extract the UTF-16 data (skip "UNICODE\0\0")
        utf16_data = sample_bytes[9:]  # Skip 9 bytes: "UNICODE\0\0"
        print(f"UTF-16 data length: {len(utf16_data)}")
        print(f"UTF-16 hex: {utf16_data[:20].hex()}")
        
        try:
            # Decode as UTF-16LE (little endian)
            decoded_text = utf16_data.decode('utf-16le')
            print(f"✅ UTF-16LE decoded: {decoded_text}")
            
            # Check if this looks like A1111 parameters
            if any(keyword in decoded_text for keyword in ['Steps:', 'CFG scale:', 'Seed:', 'Sampler:']):
                print("✅ Contains A1111 parameter keywords!")
            else:
                print("❌ No A1111 parameter keywords found")
                
        except Exception as e:
            print(f"❌ UTF-16LE decode failed: {e}")
            
        try:
            # Try UTF-16BE (big endian) as fallback
            decoded_text = utf16_data.decode('utf-16be')
            print(f"✅ UTF-16BE decoded: {decoded_text}")
        except Exception as e:
            print(f"❌ UTF-16BE decode failed: {e}")
    else:
        print("❌ No UNICODE prefix found")
    
    print("\\n🎯 SOLUTION:")
    print("   The A1111 parser needs to handle UNICODE-prefixed UTF-16 UserComment data")
    print("   Current flow: UserComment bytes → UTF-8 decode (fails) → empty string")
    print("   Fixed flow: UserComment bytes → detect UNICODE prefix → UTF-16 decode → A1111 parsing")
    
    print("\\n📝 IMPLEMENTATION:")
    print("   1. Check if UserComment starts with 'UNICODE\\0\\0'")
    print("   2. If yes, skip 9 bytes and decode remainder as UTF-16LE")
    print("   3. Process the decoded text through normal A1111 parsing")
    print("   4. This should catch FLUX/T5 workflows saved in A1111 format")

if __name__ == "__main__":
    decode_unicode_usercomment()