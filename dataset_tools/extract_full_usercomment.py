#!/usr/bin/env python3

"""
Extract the complete UserComment from the JPEG file.
"""

import sys
from PIL import Image
from PIL.ExifTags import TAGS

def extract_full_usercomment(filepath):
    """Extract and decode the complete UserComment from JPEG."""
    
    print("🔍 FULL USERCOMMENT EXTRACTION")
    print("=" * 31)
    
    try:
        with Image.open(filepath) as img:
            exif_data = img.getexif()
            
            if not exif_data:
                print("❌ No EXIF data found")
                return
            
            # UserComment is tag 37510 (0x9286)
            user_comment = exif_data.get(37510)
            
            if not user_comment:
                print("❌ No UserComment tag found")
                return
            
            print(f"✅ UserComment found: {len(user_comment)} bytes")
            
            if isinstance(user_comment, bytes):
                print(f"Raw bytes length: {len(user_comment)}")
                print(f"First 50 bytes hex: {user_comment[:50].hex()}")
                
                # Check for UNICODE prefix
                if user_comment.startswith(b'UNICODE\x00\x00'):
                    print("✅ Found UNICODE prefix")
                    
                    # Extract UTF-16 data
                    utf16_data = user_comment[9:]  # Skip "UNICODE\0\0"
                    print(f"UTF-16 data length: {len(utf16_data)} bytes")
                    
                    try:
                        # Decode as UTF-16LE
                        decoded_text = utf16_data.decode('utf-16le')
                        print(f"✅ Decoded text length: {len(decoded_text)} characters")
                        
                        print("\\n📝 DECODED CONTENT:")
                        print("-" * 20)
                        print(decoded_text)
                        print("-" * 20)
                        
                        # Check for A1111 parameters
                        a1111_keywords = ['Steps:', 'CFG scale:', 'Seed:', 'Sampler:', 'Size:', 'Model:']
                        found_keywords = [kw for kw in a1111_keywords if kw in decoded_text]
                        
                        if found_keywords:
                            print(f"\\n✅ Found A1111 keywords: {found_keywords}")
                            
                            # Try to extract key parameters
                            lines = decoded_text.split('\\n')
                            print("\\n🎯 PARAMETER ANALYSIS:")
                            for line in lines[-10:]:  # Check last 10 lines for parameters
                                line = line.strip()
                                if any(kw in line for kw in a1111_keywords):
                                    print(f"   Parameter line: {line}")
                        else:
                            print("\\n❌ No A1111 keywords found")
                            
                            # Check for FLUX/ComfyUI signatures
                            flux_keywords = ['flux', 'comfy', 'ComfyUI', 'DualCLIPLoader', 'T5']
                            found_flux = [kw for kw in flux_keywords if kw.lower() in decoded_text.lower()]
                            
                            if found_flux:
                                print(f"✅ Found FLUX/ComfyUI keywords: {found_flux}")
                            else:
                                print("❌ No FLUX/ComfyUI keywords found either")
                                
                    except Exception as e:
                        print(f"❌ UTF-16LE decode failed: {e}")
                        
                        # Try other encodings
                        try:
                            decoded_text = user_comment.decode('utf-8', errors='ignore')
                            print(f"UTF-8 decode (with errors ignored): {decoded_text[:200]}...")
                        except:
                            print("All decoding attempts failed")
                            
                elif user_comment.startswith(b'charset=Unicode'):
                    print("✅ Found charset=Unicode prefix (different format)")
                    # This is the mojibake format from earlier
                    unicode_part = user_comment[len(b'charset=Unicode '):]
                    print(f"Unicode part: {unicode_part[:50]}")
                    
                else:
                    print("❌ No recognized Unicode prefix found")
                    
                    # Try direct UTF-8 decode
                    try:
                        decoded_text = user_comment.decode('utf-8')
                        print(f"Direct UTF-8 decode: {decoded_text[:200]}...")
                    except:
                        print("Direct UTF-8 decode failed")
                        
            else:
                print(f"UserComment is string: {user_comment}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        extract_full_usercomment(sys.argv[1])
    else:
        print("Usage: python extract_full_usercomment.py <jpeg_file>")