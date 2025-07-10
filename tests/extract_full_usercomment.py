#!/usr/bin/env python3
# ruff: noqa: T201

"""Extract the complete UserComment from the JPEG file."""

import sys

from PIL import Image


def extract_full_usercomment(filepath):
    """Extract and decode the complete UserComment from JPEG."""
    print(  # noqa: T201"🔍 FULL USERCOMMENT EXTRACTION")
    print(  # noqa: T201"=" * 31)

    try:
        with Image.open(filepath) as img:
            exif_data = img.getexif()

            if not exif_data:
                print(  # noqa: T201"❌ No EXIF data found")
                return

            # UserComment is tag 37510 (0x9286)
            user_comment = exif_data.get(37510)

            if not user_comment:
                print(  # noqa: T201"❌ No UserComment tag found")
                return

            print(  # noqa: T201f"✅ UserComment found: {len(user_comment)} bytes")

            if isinstance(user_comment, bytes):
                print(  # noqa: T201f"Raw bytes length: {len(user_comment)}")
                print(  # noqa: T201f"First 50 bytes hex: {user_comment[:50].hex()}")

                # Check for UNICODE prefix
                if user_comment.startswith(b"UNICODE\x00\x00"):
                    print(  # noqa: T201"✅ Found UNICODE prefix")

                    # Extract UTF-16 data
                    UNICODE_PREFIX = b"UNICODE\x00\x00"
                    utf16_data = user_comment[len(UNICODE_PREFIX) :]  # Skip prefix
                    print(  # noqa: T201f"UTF-16 data length: {len(utf16_data)} bytes")

                    try:
                        # Decode as UTF-16LE
                        decoded_text = utf16_data.decode("utf-16le")
                        print(  # noqa: T201f"✅ Decoded text length: {len(decoded_text)} characters")

                        print(  # noqa: T201"\\n📝 DECODED CONTENT:")
                        print(  # noqa: T201"-" * 20)
                        print(  # noqa: T201decoded_text)
                        print(  # noqa: T201"-" * 20)

                        # Check for A1111 parameters
                        a1111_keywords = [
                            "Steps:",
                            "CFG scale:",
                            "Seed:",
                            "Sampler:",
                            "Size:",
                            "Model:",
                        ]
                        found_keywords = [
                            kw for kw in a1111_keywords if kw in decoded_text
                        ]

                        if found_keywords:
                            print(  # noqa: T201f"\\n✅ Found A1111 keywords: {found_keywords}")

                            # Try to extract key parameters
                            lines = decoded_text.split("\\n")
                            print(  # noqa: T201"\\n🎯 PARAMETER ANALYSIS:")
                            for line in lines[
                                -10:
                            ]:  # Check last 10 lines for parameters
                                line = line.strip()
                                if any(kw in line for kw in a1111_keywords):
                                    print(  # noqa: T201f"   Parameter line: {line}")
                        else:
                            print(  # noqa: T201"\\n❌ No A1111 keywords found")

                            # Check for FLUX/ComfyUI signatures
                            flux_keywords = [
                                "flux",
                                "comfy",
                                "ComfyUI",
                                "DualCLIPLoader",
                                "T5",
                            ]
                            found_flux = [
                                kw
                                for kw in flux_keywords
                                if kw.lower() in decoded_text.lower()
                            ]

                            if found_flux:
                                print(  # noqa: T201f"✅ Found FLUX/ComfyUI keywords: {found_flux}")
                            else:
                                print(  # noqa: T201"❌ No FLUX/ComfyUI keywords found either")

                    except Exception as e:
                        print(  # noqa: T201f"❌ UTF-16LE decode failed: {e}")

                        # Try other encodings
                        try:
                            decoded_text = user_comment.decode("utf-8", errors="ignore")
                            print(  # noqa: T201
                                f"UTF-8 decode (with errors ignored): {decoded_text[:200]}..."
                            )
                        except:
                            print(  # noqa: T201"All decoding attempts failed")

                elif user_comment.startswith(b"charset=Unicode"):
                    print(  # noqa: T201"✅ Found charset=Unicode prefix (different format)")
                    # This is the mojibake format from earlier
                    unicode_part = user_comment[len(b"charset=Unicode ") :]
                    print(  # noqa: T201f"Unicode part: {unicode_part[:50]}")

                else:
                    print(  # noqa: T201"❌ No recognized Unicode prefix found")

                    # Try direct UTF-8 decode
                    try:
                        decoded_text = user_comment.decode("utf-8")
                        print(  # noqa: T201f"Direct UTF-8 decode: {decoded_text[:200]}...")
                    except:
                        print(  # noqa: T201"Direct UTF-8 decode failed")

            else:
                print(  # noqa: T201f"UserComment is string: {user_comment}")

    except Exception as e:
        print(  # noqa: T201f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        extract_full_usercomment(sys.argv[1])
    else:
        print(  # noqa: T201"Usage: python extract_full_usercomment.py <jpeg_file>")
