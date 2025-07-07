#!/usr/bin/env python3
# ruff: noqa: T201

"""Debug the exact mojibake issue we're seeing."""

import os
import sys

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_mojibake_debug():
    """Debug the specific mojibake we're seeing."""
    print(  # noqa: T201"🔍 MOJIBAKE DEBUG TEST")
    print(  # noqa: T201"=" * 22)

    # The mojibake string from the user's output
    mojibake = "charset=Unicode 笀∀爀攀猀漀甀爀挀攀ⴀ猀琀愀挀欀∀㨀笀∀挀氀愀猀猀开琀礀瀀攀∀㨀∀䌀栀攀挀欀瀀漀椀渀琀䰀漀愀搀攀爀匀椀洀瀀氀攀∀Ⰰ∀椀渀瀀甀琀猀∀㨀笀∀挀欀瀀琀开渀愀洀攀∀㨀∀甀爀渀㨀愀椀爀㨀猀搀砀氀㨀挀栀攀挀欀瀀漀椀渀琀㨀挀椀瘀椀琀愀椀㨀㈀㠀㠀㔀㠀㐀䀀㌀㈀㐀㘀㄀㤀∀"

    print(  # noqa: T201f"Input string: {mojibake[:100]}...")
    print(  # noqa: T201f"Length: {len(mojibake)}")

    # This looks like UTF-16 encoded as UTF-8, let's try to decode it
    print(  # noqa: T201"\n🔧 DECODING ATTEMPTS")
    print(  # noqa: T201"-" * 20)

    # Try to encode back to bytes and decode as UTF-16
    try:
        # The part after "charset=Unicode "
        unicode_part = mojibake[len("charset=Unicode ") :]
        print(  # noqa: T201f"Unicode part: {unicode_part[:50]}...")

        # Encode to UTF-8 bytes then decode as UTF-16
        utf8_bytes = unicode_part.encode("utf-8")
        print(  # noqa: T201f"UTF-8 bytes: {utf8_bytes[:50]}...")

        # Try UTF-16 decoding
        utf16_decoded = utf8_bytes.decode("utf-16le", errors="ignore")
        print(  # noqa: T201f"UTF-16 decoded: {utf16_decoded[:100]}...")

        # Check if it looks like JSON
        if utf16_decoded.startswith('{"') or '"class_type"' in utf16_decoded:
            print(  # noqa: T201"✅ Looks like valid JSON after decoding!")
        else:
            print(  # noqa: T201"❌ Still doesn't look like JSON")

    except Exception as e:
        print(  # noqa: T201f"❌ UTF-16 decoding failed: {e}")

    # Try our robust decoder
    print(  # noqa: T201"\n🔧 TESTING OUR ROBUST DECODER")
    print(  # noqa: T201"-" * 33)

    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

        preparer = ContextDataPreparer()

        # Simulate the charset=Unicode prefix format
        fake_bytes = f"charset=Unicode {mojibake[len('charset=Unicode ') :]}".encode()
        print(  # noqa: T201f"Fake bytes: {fake_bytes[:50]}...")

        decoded = preparer._decode_usercomment_bytes_robust(fake_bytes)
        if decoded:
            print(  # noqa: T201f"✅ Robust decoder SUCCESS: {len(decoded)} chars")
            print(  # noqa: T201f"Preview: {decoded[:100]}...")

            if decoded.startswith('{"') or '"class_type"' in decoded:
                print(  # noqa: T201"✅ Looks like valid JSON!")
            else:
                print(  # noqa: T201"❌ Still doesn't look like JSON")
        else:
            print(  # noqa: T201"❌ Robust decoder returned empty")

    except Exception as e:
        print(  # noqa: T201f"❌ Robust decoder error: {e}")
        import traceback

        traceback.print_exc()

    print(  # noqa: T201"\n🎯 ANALYSIS:")
    print(  # noqa: T201"This appears to be UTF-16 data that was incorrectly decoded as UTF-8")
    print(  # noqa: T201"The 'charset=Unicode' prefix indicates it should be UTF-16LE encoded")
    print(  # noqa: T201"Our robust decoder should handle this pattern")


if __name__ == "__main__":
    test_mojibake_debug()
