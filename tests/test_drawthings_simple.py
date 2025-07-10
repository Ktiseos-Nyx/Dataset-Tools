#!/usr/bin/env python3
# ruff: noqa: T201

"""Simple test for Draw Things extraction logic"""

import json
import re


def test_drawthings_extraction():
    """Test Draw Things extraction logic without complex imports."""
    print(  # noqa: T201"🎨 TESTING DRAW THINGS EXTRACTION LOGIC")
    print(  # noqa: T201"=" * 43)

    # Mock XMP data similar to what Draw Things would produce
    xmp_data = """<?xml version='1.0' encoding='UTF-8'?>
<x:xmpmeta xmlns:x='adobe:ns:meta/'>
<rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
<rdf:Description rdf:about=''
xmlns:dc='http://purl.org/dc/elements/1.1/'
xmlns:exif='http://ns.adobe.com/exif/1.0/'
xmlns:xmp='http://ns.adobe.com/xap/1.0/'
xmp:CreatorTool='Draw Things'
dc:format='image/png'>
<exif:UserComment>{"c":"1920s, a young woman stands in a stunning country orchard, her arms wrapped around an ancient apple tree that has stood tall for over 100 years, the tree, with its gnarled branches and thick trunk, is adorned with ripe red apples that glisten in the golden afternoon sunlight, the woman wears a flowing vintage dress in soft pastels, her hair styled in loose waves that catch the light, the orchard stretches behind her with rows of fruit trees in full bloom, creating a dreamy, nostalgic atmosphere that captures the essence of rural life in the early 20th century, highly detailed, cinematic lighting, pastoral beauty","uc":"blurry, low quality, bad anatomy, extra limbs, worst quality","seed":1601874409,"steps":30,"scale":7.5,"sampler":"euler","model":"realisticVisionV60B1_v51VAE.safetensors","width":1024,"height":1536,"strength":1.0,"v2":{"aestheticScore":6.5,"negativeAestheticScore":2.0,"loras":[{"name":"detail_enhancer","strength":0.8}]}}</exif:UserComment>
</rdf:Description>
</rdf:RDF>
</x:xmpmeta>"""

    print(  # noqa: T201"🔍 STEP 1: DETECTION RULES")
    print(  # noqa: T201"-" * 28)

    # Test detection rules
    rule1_pass = "Draw Things" in xmp_data
    rule2_pass = "exif:UserComment" in xmp_data

    print(  # noqa: T201f"Rule 1 (Contains 'Draw Things'): {'✅ PASS' if rule1_pass else '❌ FAIL'}")
    print(  # noqa: T201
        f"Rule 2 (Contains 'exif:UserComment'): {'✅ PASS' if rule2_pass else '❌ FAIL'}"
    )

    if not (rule1_pass and rule2_pass):
        print(  # noqa: T201"❌ Detection rules failed - parser would not trigger")
        return

    print(  # noqa: T201"\n🔧 STEP 2: XMP TRANSFORMATION")
    print(  # noqa: T201"-" * 32)

    # Test extract_json_from_xmp_user_comment transformation
    match = re.search(r"<exif:UserComment>(.*?)</exif:UserComment>", xmp_data)
    if match:
        json_string = match.group(1)
        print(  # noqa: T201f"✅ Extracted JSON string ({len(json_string)} chars)")
        print(  # noqa: T201f"   Preview: {json_string[:100]}...")

        # Test JSON decoding
        try:
            json_data = json.loads(json_string)
            print(  # noqa: T201f"✅ JSON decoded successfully ({len(json_data)} keys)")

            print(  # noqa: T201"\n📊 STEP 3: FIELD EXTRACTION")
            print(  # noqa: T201"-" * 30)

            # Simulate the field extraction logic from the Draw Things parser
            fields_to_test = [
                ("prompt", "c", "string"),
                ("negative_prompt", "uc", "string"),
                ("parameters.seed", "seed", "integer"),
                ("parameters.steps", "steps", "integer"),
                ("parameters.cfg_scale", "scale", "float"),
                ("parameters.sampler_name", "sampler", "string"),
                ("parameters.model", "model", "string"),
                ("parameters.width", "width", "integer"),
                ("parameters.height", "height", "integer"),
                ("parameters.denoising_strength", "strength", "float"),
                ("v2_data.aesthetic_score", "v2.aestheticScore", "float"),
                (
                    "v2_data.negative_aesthetic_score",
                    "v2.negativeAestheticScore",
                    "float",
                ),
                ("v2_data.loras", "v2.loras", "array"),
            ]

            def get_json_path_value(data, path):
                """Simple JSON path getter for testing."""
                try:
                    keys = path.split(".")
                    current = data
                    for key in keys:
                        if isinstance(current, dict):
                            current = current.get(key)
                        else:
                            return None
                    return current
                except:
                    return None

            successful_extractions = 0
            total_extractions = len(fields_to_test)

            for target_key, json_path, value_type in fields_to_test:
                value = get_json_path_value(json_data, json_path)

                if value is not None:
                    # Type conversion simulation
                    try:
                        if value_type == "integer":
                            value = int(value)
                        elif value_type == "float":
                            value = float(value)
                        elif value_type == "string":
                            value = str(value)
                        elif value_type == "array":
                            # Keep as-is for arrays
                            pass

                        print(  # noqa: T201f"✅ {target_key}: {value}")
                        successful_extractions += 1
                    except (ValueError, TypeError) as e:
                        print(  # noqa: T201f"❌ {target_key}: Type conversion failed ({e})")
                else:
                    print(  # noqa: T201f"❌ {target_key}: Not found in JSON")

            print(  # noqa: T201"\n🎯 EXTRACTION SUMMARY:")
            print(  # noqa: T201"-" * 21)
            print(  # noqa: T201
                f"✅ Successfully extracted: {successful_extractions}/{total_extractions} fields"
            )

            if successful_extractions >= 10:  # Most critical fields
                print(  # noqa: T201"🎉 Draw Things parser should work correctly!")
                print(  # noqa: T201"✅ All core fields (prompt, negative, parameters) extracted")

                # Show the expected output structure
                print(  # noqa: T201"\n📋 EXPECTED OUTPUT STRUCTURE:")
                print(  # noqa: T201"-" * 33)

                expected_output = {
                    "tool": "Draw Things",
                    "format": "XMP with JSON UserComment",
                    "prompt": json_data.get("c", ""),
                    "negative_prompt": json_data.get("uc", ""),
                    "parameters": {
                        "seed": json_data.get("seed"),
                        "steps": json_data.get("steps"),
                        "cfg_scale": json_data.get("scale"),
                        "sampler_name": json_data.get("sampler"),
                        "model": json_data.get("model"),
                        "width": json_data.get("width"),
                        "height": json_data.get("height"),
                        "denoising_strength": json_data.get("strength"),
                    },
                }

                print(  # noqa: T201"✅ Prompt:", expected_output["prompt"][:60] + "...")
                print(  # noqa: T201"✅ Negative:", expected_output["negative_prompt"])
                print(  # noqa: T201"✅ Seed:", expected_output["parameters"]["seed"])
                print(  # noqa: T201"✅ Steps:", expected_output["parameters"]["steps"])
                print(  # noqa: T201"✅ Model:", expected_output["parameters"]["model"])

            else:
                print(  # noqa: T201"❌ Too many field extractions failed")
                print(  # noqa: T201"💡 Check if JSON structure matches parser expectations")

        except json.JSONDecodeError as e:
            print(  # noqa: T201f"❌ JSON decoding failed: {e}")

    else:
        print(  # noqa: T201"❌ XMP UserComment extraction failed")
        print(  # noqa: T201"💡 Check XMP structure and regex pattern")


def analyze_user_issue():
    """Analyze why the user's Draw Things image might not be extracting prompts."""
    print(  # noqa: T201"\n🔍 ANALYZING USER'S ISSUE:")
    print(  # noqa: T201"-" * 27)

    print(  # noqa: T201"User reported: 'draw things needs a prompt extraction method'")
    print(  # noqa: T201"But the parser definition shows prompt extraction IS implemented:")
    print(  # noqa: T201"  - 'prompt' field uses 'direct_json_path' with json_path: 'c'")
    print(  # noqa: T201"  - 'negative_prompt' field uses 'direct_json_path' with json_path: 'uc'")

    print(  # noqa: T201"\n💡 POSSIBLE CAUSES:")
    print(  # noqa: T201"-" * 18)
    print(  # noqa: T201"1. ❓ JSON structure in XMP doesn't match expected format")
    print(  # noqa: T201"2. ❓ XMP UserComment extraction failing")
    print(  # noqa: T201"3. ❓ Missing extraction method implementation")
    print(  # noqa: T201"4. ❓ Parser priority conflict with other parsers")
    print(  # noqa: T201"5. ❓ Detection rules not matching the actual file")

    print(  # noqa: T201"\n🔧 DEBUGGING STEPS:")
    print(  # noqa: T201"-" * 19)
    print(  # noqa: T201"1. Check actual XMP content in the problematic file")
    print(  # noqa: T201"2. Verify 'direct_json_path' method is available")
    print(  # noqa: T201"3. Test extraction with real file data")
    print(  # noqa: T201"4. Check parser execution logs")


if __name__ == "__main__":
    test_drawthings_extraction()
    analyze_user_issue()
