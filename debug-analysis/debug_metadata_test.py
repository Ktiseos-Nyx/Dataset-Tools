# debug_metadata_test.py
# ruff: noqa: T201
# Quick script to debug what the MetadataEngine is seeing

import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def debug_context_data(image_path):
    """Debug what context data is being prepared"""
    print(  # noqa: T201f"🔍 DEBUGGING CONTEXT DATA FOR: {image_path}")
    print(  # noqa: T201"=" * 60)

    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

        preparer = ContextDataPreparer()
        context = preparer.prepare_context(image_path)

        if not context:
            print(  # noqa: T201"❌ CONTEXT PREPARATION FAILED!")
            return None

        print(  # noqa: T201"✅ CONTEXT DATA PREPARED SUCCESSFULLY!")
        print(  # noqa: T201f"📋 Available keys: {list(context.keys())}")

        # Check specific A1111 data sources
        print(  # noqa: T201"\n🎯 A1111 DATA SOURCES:")

        pil_params = context.get("pil_info", {}).get("parameters")
        if pil_params:
            print(  # noqa: T201f"📄 PIL parameters (first 200 chars): {str(pil_params)[:200]}...")
        else:
            print(  # noqa: T201"❌ No PIL parameters found")

        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            print(  # noqa: T201
                f"💬 EXIF UserComment (first 200 chars): {str(user_comment)[:200]}..."
            )
        else:
            print(  # noqa: T201"❌ No EXIF UserComment found")

        # Check image dimensions
        print(  # noqa: T201
            f"\n📐 Image dimensions: {context.get('width', 'unknown')}x{context.get('height', 'unknown')}"
        )
        print(  # noqa: T201f"📋 File format: {context.get('file_format', 'unknown')}")

        return context

    except Exception as e:
        print(  # noqa: T201f"💥 ERROR IN CONTEXT PREPARATION: {e}")
        return None


def debug_rule_matching(context, rules_path):
    """Debug rule matching"""
    print(  # noqa: T201"\n🎯 DEBUGGING RULE MATCHING")
    print(  # noqa: T201"=" * 60)

    try:
        from dataset_tools.rule_evaluator import RuleEvaluator

        evaluator = RuleEvaluator(logging.getLogger("RuleDebug"))
        matching_parsers = evaluator.find_matching_parsers(context)

        print(  # noqa: T201f"🎮 Matching parsers: {matching_parsers}")

        # Check if a1111_webui specifically matches
        if "a1111_webui" in matching_parsers:
            print(  # noqa: T201"✅ a1111_webui rules PASSED!")
        else:
            print(  # noqa: T201"❌ a1111_webui rules FAILED!")

        return matching_parsers

    except Exception as e:
        print(  # noqa: T201f"💥 ERROR IN RULE MATCHING: {e}")
        return []


def debug_field_extraction(input_data):
    """Debug field extraction"""
    print(  # noqa: T201"\n🔧 DEBUGGING FIELD EXTRACTION")
    print(  # noqa: T201"=" * 60)

    if not isinstance(input_data, str):
        print(  # noqa: T201f"❌ Input data is not string: {type(input_data)}")
        return

    print(  # noqa: T201"📝 Input data preview (first 300 chars):")
    print(  # noqa: T201f"'{input_data[:300]}...'")

    try:
        from dataset_tools.metadata_engine.field_extraction import FieldExtractor

        extractor = FieldExtractor()

        # Test individual field extraction methods
        print(  # noqa: T201"\n🧪 TESTING FIELD EXTRACTION METHODS:")

        # Test prompt extraction
        method_def = {"method": "a1111_extract_prompt_positive"}
        prompt = extractor.extract_field(method_def, input_data, {}, {})
        print(  # noqa: T201f"✨ Prompt: '{prompt[:100] if prompt else 'None'}...'")

        # Test negative prompt
        method_def = {"method": "a1111_extract_prompt_negative"}
        neg_prompt = extractor.extract_field(method_def, input_data, {}, {})
        print(  # noqa: T201f"🚫 Negative: '{neg_prompt[:100] if neg_prompt else 'None'}...'")

        # Test steps extraction
        method_def = {
            "method": "key_value_extract_from_a1111_block",
            "key_name": "Steps",
        }
        steps = extractor.extract_field(method_def, input_data, {}, {})
        print(  # noqa: T201f"🔢 Steps: {steps}")

        # Test seed extraction
        method_def = {
            "method": "key_value_extract_from_a1111_block",
            "key_name": "Seed",
        }
        seed = extractor.extract_field(method_def, input_data, {}, {})
        print(  # noqa: T201f"🌱 Seed: {seed}")

    except Exception as e:
        print(  # noqa: T201f"💥 ERROR IN FIELD EXTRACTION: {e}")


def debug_full_engine(image_path, parser_defs_path):
    """Debug the full MetadataEngine"""
    print(  # noqa: T201"\n🚀 DEBUGGING FULL METADATA ENGINE")
    print(  # noqa: T201"=" * 60)

    try:
        from dataset_tools.metadata_engine import MetadataEngine

        engine = MetadataEngine(parser_defs_path)
        result = engine.get_parser_for_file(image_path)

        if result:
            print(  # noqa: T201"✅ ENGINE SUCCEEDED!")
            if isinstance(result, dict):
                print(  # noqa: T201f"📋 Result keys: {list(result.keys())}")
                if "tool" in result:
                    print(  # noqa: T201f"🔧 Tool: {result['tool']}")
                if "prompt" in result:
                    print(  # noqa: T201f"✨ Prompt: '{str(result['prompt'])[:100]}...'")
            else:
                print(  # noqa: T201f"📦 Result type: {type(result)}")
                if hasattr(result, "tool"):
                    print(  # noqa: T201f"🔧 Tool: {result.tool}")
        else:
            print(  # noqa: T201"❌ ENGINE RETURNED NONE!")

        return result

    except Exception as e:
        print(  # noqa: T201f"💥 ERROR IN FULL ENGINE: {e}")
        return None


if __name__ == "__main__":
    # Test with your sample image
    image_path = "/Users/duskfall/Downloads/Metadata Samples/00000-1626107238.jpeg"
    parser_defs_path = "/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/dataset_tools/parser_definitions"

    # Step by step debugging
    context = debug_context_data(image_path)

    if context:
        matching_parsers = debug_rule_matching(context, parser_defs_path)

        # Test field extraction with actual data
        pil_params = context.get("pil_info", {}).get("parameters")
        user_comment = context.get("raw_user_comment_str")

        test_data = pil_params or user_comment
        if test_data:
            debug_field_extraction(test_data)

        # Test full engine
        result = debug_full_engine(image_path, parser_defs_path)
