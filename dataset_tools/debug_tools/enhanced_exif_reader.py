#!/usr/bin/env python3

"""Enhanced EXIF reader that bypasses PIL limitations for UserComment extraction."""

import json
from pathlib import Path


class EnhancedExifReader:
    """Enhanced EXIF reader using PIL for UserComment handling."""

    def __init__(self):
        pass  # No exiftool check needed

    def extract_usercomment(self, image_path: str) -> str:
        """Extract UserComment using PIL, handling Unicode and large payloads.

        Args:
            image_path: Path to the image file

        Returns:
            Decoded UserComment text or empty string if none found

        """
        return self._extract_usercomment_pil(image_path)

    def _extract_usercomment_pil(self, image_path: str) -> str:
        """PIL-based extraction."""
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                exif_data = img.getexif()
                if exif_data:
                    user_comment = exif_data.get(37510)  # UserComment tag
                    if user_comment:
                        if isinstance(user_comment, bytes):
                            # Try different decoding strategies
                            return self._decode_usercomment_bytes(user_comment)
                        return str(user_comment)
            return ""

        except Exception as e:
            print(f"❌ PIL extraction failed: {e}")
            return ""

    def _decode_usercomment_bytes(self, data: bytes) -> str:
        """Try various decoding strategies for UserComment bytes."""
        # Strategy 1: Unicode prefix with UTF-16
        if data.startswith(b"UNICODE\x00\x00"):
            try:
                utf16_data = data[9:]  # Skip "UNICODE\0\0"
                return utf16_data.decode("utf-16le")
            except:
                pass

        # Strategy 2: charset=Unicode prefix (mojibake format)
        if data.startswith(b"charset=Unicode"):
            try:
                unicode_part = data[len(b"charset=Unicode ") :]
                return unicode_part.decode("utf-16le", errors="ignore")
            except:
                pass

        # Strategy 3: Direct UTF-8
        try:
            return data.decode("utf-8")
        except:
            pass

        # Strategy 4: Latin-1 (preserves all bytes)
        try:
            return data.decode("latin-1")
        except:
            pass

        # Strategy 5: Ignore errors
        try:
            return data.decode("utf-8", errors="ignore")
        except:
            return ""


def test_enhanced_reader():
    """Test the enhanced EXIF reader."""
    print("🔧 ENHANCED EXIF READER TEST")
    print("=" * 29)

    reader = EnhancedExifReader()

    # Test files
    test_files = [
        "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_01803_.jpeg",  # Unicode A1111
        "/Users/duskfall/Desktop/Comfy_UI_DATA/ComfyUI_08965_.jpeg",  # ComfyUI JSON
    ]

    for test_file in test_files:
        if Path(test_file).exists():  # Use Path.exists() for robustness
            print(f"\n📁 Testing: {Path(test_file).name}")

            usercomment = reader.extract_usercomment(test_file)

            if usercomment:
                print(f"✅ Extracted {len(usercomment)} characters")

                # Check what type of metadata this is
                if "Steps:" in usercomment and "Sampler:" in usercomment:
                    print("   Type: A1111-style parameters")
                    # Extract key parameters
                    if "Model:" in usercomment:
                        model_start = usercomment.find("Model:") + 6
                        model_end = usercomment.find(",", model_start)
                        if model_end == -1:
                            model_end = len(usercomment)
                        model = usercomment[model_start:model_end].strip()
                        print(f"   Model: {model}")

                elif usercomment.startswith('{"') and '"prompt":' in usercomment:
                    print("   Type: ComfyUI JSON workflow")
                    try:
                        # Try to parse as JSON
                        workflow_data = json.loads(usercomment)
                        if "prompt" in workflow_data:
                            node_count = len(workflow_data["prompt"])
                            print(f"   Nodes: {node_count}")

                        # Look for key node types
                        workflow_str = json.dumps(workflow_data)
                        if "KSampler" in workflow_str:
                            print("   Contains: KSampler nodes")
                        if "CLIPTextEncode" in workflow_str:
                            print("   Contains: Text encoding nodes")
                        if "DualCLIPLoader" in workflow_str:
                            print("   Contains: T5/FLUX components")

                    except json.JSONDecodeError:
                        print("   Warning: Invalid JSON structure")

                else:
                    print("   Type: Unknown/Other")
                    print(f"   Preview: {usercomment[:100]}...")
            else:
                print("❌ No UserComment found")
        else:
            print(f"❌ File not found: {test_file}")


if __name__ == "__main__":
    test_enhanced_reader()
