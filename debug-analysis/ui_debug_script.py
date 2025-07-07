# ui_debug_script.py
# ruff: noqa: T201
# Debug what data flows from parser to UI

import json
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def debug_json_parser_output(image_path, parser_defs_path):
    """Debug what the JSON parser actually returns"""
    print(  # noqa: T201"🔍 DEBUGGING JSON PARSER OUTPUT")
    print(  # noqa: T201"=" * 60)

    try:
        engine_logger = logging.getLogger("MetadataEngine")
        from dataset_tools.metadata_engine import MetadataEngine

        engine = MetadataEngine(parser_defs_path, engine_logger)
        result = engine.get_parser_for_file(image_path)

        if result:
            print(  # noqa: T201"✅ JSON PARSER SUCCEEDED!")
            print(  # noqa: T201f"📦 Result type: {type(result)}")

            if isinstance(result, dict):
                print(  # noqa: T201f"📋 Result keys: {list(result.keys())}")

                # Print the full structure
                print(  # noqa: T201"\n🗂️ FULL JSON PARSER OUTPUT:")
                print(  # noqa: T201json.dumps(result, indent=2, default=str))

                return result
            print(  # noqa: T201f"⚠️ Result is not a dict: {result}")
            return result
        print(  # noqa: T201"❌ JSON PARSER RETURNED NONE!")
        return None

    except Exception as e:
        print(  # noqa: T201f"💥 ERROR IN JSON PARSER: {e}")
        import traceback

        traceback.print_exc()
        return None


def debug_vendored_parser_output(image_path):
    """Debug what the vendored parser returns for comparison"""
    print(  # noqa: T201"\n🔍 DEBUGGING VENDORED PARSER OUTPUT (for comparison)")
    print(  # noqa: T201"=" * 60)

    try:
        from dataset_tools.vendored_sdpr.image_data_reader import ImageDataReader

        reader = ImageDataReader(image_path)
        status = reader.parse()

        if hasattr(reader, "status") and hasattr(reader.status, "name"):
            status_name = reader.status.name
        else:
            status_name = str(status)

        print(  # noqa: T201f"📊 Vendored status: {status_name}")
        print(  # noqa: T201f"🔧 Vendored tool: {getattr(reader, 'tool', 'Unknown')}")

        # Extract key properties that UI uses
        vendored_data = {
            "tool": getattr(reader, "tool", "Unknown"),
            "positive": getattr(reader, "positive", ""),
            "negative": getattr(reader, "negative", ""),
            "parameter": getattr(reader, "parameter", {}),
            "width": getattr(reader, "width", "0"),
            "height": getattr(reader, "height", "0"),
            "setting": getattr(reader, "setting", ""),
            "raw": getattr(reader, "raw", ""),
            "status": status_name,
        }

        print(  # noqa: T201"\n🗂️ VENDORED PARSER DATA STRUCTURE:")
        print(  # noqa: T201json.dumps(vendored_data, indent=2, default=str))

        return vendored_data

    except Exception as e:
        print(  # noqa: T201f"💥 ERROR IN VENDORED PARSER: {e}")
        import traceback

        traceback.print_exc()
        return None


def debug_ui_population_expectations():
    """Debug what the UI population code expects"""
    print(  # noqa: T201"\n🎨 DEBUGGING UI POPULATION EXPECTATIONS")
    print(  # noqa: T201"=" * 60)

    try:
        # Look at the metadata_parser.py to see what _populate_ui expects

        print(  # noqa: T201"📋 Looking at metadata_parser.py for UI population logic...")

        # Check what fields the UI population code looks for
        expected_fields = [
            "tool",
            "positive",
            "negative",
            "parameter",
            "width",
            "height",
            "setting",
            "raw",
            "status",
            "is_sdxl",
            "positive_sdxl",
            "negative_sdxl",
        ]

        print(  # noqa: T201f"🎯 UI expects these fields from parser: {expected_fields}")

        return expected_fields

    except Exception as e:
        print(  # noqa: T201f"💥 ERROR CHECKING UI EXPECTATIONS: {e}")
        return []


def debug_data_format_mismatch(json_result, vendored_result):
    """Compare JSON vs vendored data formats"""
    print(  # noqa: T201"\n🔗 DEBUGGING DATA FORMAT MISMATCH")
    print(  # noqa: T201"=" * 60)

    if not json_result:
        print(  # noqa: T201"❌ No JSON result to compare")
        return

    if not vendored_result:
        print(  # noqa: T201"❌ No vendored result to compare")
        return

    print(  # noqa: T201"🆚 COMPARING DATA FORMATS:")

    # Check if JSON result has the same structure as vendored
    vendored_keys = set(vendored_result.keys())
    json_keys = set(json_result.keys()) if isinstance(json_result, dict) else set()

    print(  # noqa: T201f"📋 Vendored keys: {sorted(vendored_keys)}")
    print(  # noqa: T201f"📋 JSON keys: {sorted(json_keys)}")

    missing_in_json = vendored_keys - json_keys
    extra_in_json = json_keys - vendored_keys

    if missing_in_json:
        print(  # noqa: T201f"❌ Missing in JSON: {sorted(missing_in_json)}")
    if extra_in_json:
        print(  # noqa: T201f"✨ Extra in JSON: {sorted(extra_in_json)}")

    # Check specific key values
    common_keys = vendored_keys & json_keys
    print(  # noqa: T201"\n🔍 COMPARING COMMON KEYS:")
    for key in sorted(common_keys):
        v_val = vendored_result[key]
        j_val = json_result[key]

        if str(v_val) != str(j_val):
            print(  # noqa: T201f"  🔧 {key}:")
            print(  # noqa: T201f"    Vendored: {v_val!r}")
            print(  # noqa: T201f"    JSON:     {j_val!r}")
        else:
            print(  # noqa: T201f"  ✅ {key}: {v_val!r}")


def suggest_ui_fix(json_result, expected_fields):
    """Suggest how to fix the UI data format"""
    print(  # noqa: T201"\n🛠️ SUGGESTED UI FIX")
    print(  # noqa: T201"=" * 60)

    if not json_result or not isinstance(json_result, dict):
        print(  # noqa: T201"❌ Can't suggest fix - JSON result invalid")
        return

    print(  # noqa: T201"💡 PROPOSED SOLUTION:")
    print(  # noqa: T201"The UI expects a BaseFormat-like object with these properties:")

    # Create a mapping from JSON to UI format
    suggested_mapping = {}

    for field in expected_fields:
        if field in json_result:
            suggested_mapping[field] = f"json_result['{field}']"
        elif field == "tool" and "tool" in json_result:
            suggested_mapping[field] = "json_result['tool']"
        elif field == "positive" and "prompt" in json_result:
            suggested_mapping[field] = "json_result['prompt']"
        elif field == "negative" and "negative_prompt" in json_result:
            suggested_mapping[field] = "json_result['negative_prompt']"
        elif field == "parameter" and "parameters" in json_result:
            suggested_mapping[field] = "json_result['parameters']"
        else:
            suggested_mapping[field] = f"json_result.get('{field}', '')"

    print(  # noqa: T201"\n📝 SUGGESTED FIELD MAPPING:")
    for ui_field, json_path in suggested_mapping.items():
        print(  # noqa: T201f"  {ui_field}: {json_path}")


if __name__ == "__main__":
    # Test with your working A1111 image
    image_path = "/Users/duskfall/Downloads/Metadata Samples/00000-1626107238.jpeg"
    parser_defs_path = "/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/dataset_tools/parser_definitions"

    # Step-by-step debugging
    json_result = debug_json_parser_output(image_path, parser_defs_path)
    vendored_result = debug_vendored_parser_output(image_path)
    expected_fields = debug_ui_population_expectations()

    if json_result and vendored_result:
        debug_data_format_mismatch(json_result, vendored_result)

    if json_result and expected_fields:
        suggest_ui_fix(json_result, expected_fields)

    print(  # noqa: T201"\n🎯 NEXT STEPS:")
    print(  # noqa: T201"1. Check if JSON result has all the fields UI expects")
    print(  # noqa: T201"2. Create a converter function to map JSON format → UI format")
    print(  # noqa: T201"3. Update metadata_parser.py to use the converter")
    print(  # noqa: T201"4. Test the UI updates!")
