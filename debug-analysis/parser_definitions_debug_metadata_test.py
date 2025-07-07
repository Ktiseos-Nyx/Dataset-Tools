# debug_metadata_test.py
# ruff: noqa: T201
# Quick script to debug what the MetadataEngine is seeing

import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def debug_context_data(image_path):
    """Debug what context data is being prepared."""
    try:
        from dataset_tools.metadata_engine.context_preparation import ContextDataPreparer

        preparer = ContextDataPreparer()
        context = preparer.prepare_context(image_path)

        if not context:
            return None

        # Check specific A1111 data sources

        pil_params = context.get("pil_info", {}).get("parameters")
        if pil_params:
            pass
        else:
            pass

        user_comment = context.get("raw_user_comment_str")
        if user_comment:
            pass
        else:
            pass

        # Check image dimensions

        return context

    except Exception:
        return None


def debug_rule_matching(context, rules_path):
    """Debug rule matching."""
    try:
        from dataset_tools.rule_evaluator import RuleEvaluator

        evaluator = RuleEvaluator(logging.getLogger("RuleDebug"))

        # Check if a1111_webui specifically matches by testing rules manually
        matching_parsers = []
        for rule in evaluator.rules:
            parser_name = rule.get("parser_name")
            if parser_name == "a1111_webui":
                try:
                    matches = evaluator.evaluate_rule(rule, context)
                    if matches and parser_name not in matching_parsers:
                        matching_parsers.append(parser_name)
                except Exception:
                    pass

        # Check if a1111_webui specifically matches
        if "a1111_webui" in matching_parsers:
            pass
        else:
            pass

        return matching_parsers

    except Exception:
        return []


def debug_field_extraction(input_data) -> None:
    """Debug field extraction."""
    if not isinstance(input_data, str):
        return

    try:
        from dataset_tools.metadata_engine.field_extraction import FieldExtractor

        extractor = FieldExtractor()

        # Test individual field extraction methods

        # Test prompt extraction
        method_def = {"method": "a1111_extract_prompt_positive"}
        extractor.extract_field(method_def, input_data, {}, {})

        # Test negative prompt
        method_def = {"method": "a1111_extract_prompt_negative"}
        extractor.extract_field(method_def, input_data, {}, {})

        # Test steps extraction
        method_def = {
            "method": "key_value_extract_from_a1111_block",
            "key_name": "Steps",
        }
        extractor.extract_field(method_def, input_data, {}, {})

        # Test seed extraction
        method_def = {
            "method": "key_value_extract_from_a1111_block",
            "key_name": "Seed",
        }
        extractor.extract_field(method_def, input_data, {}, {})

    except Exception:
        pass


def debug_full_engine(image_path, parser_defs_path):
    """Debug the full MetadataEngine."""
    try:
        # Create a proper logger and pass it to the engine
        engine_logger = logging.getLogger("MetadataEngine")
        engine_logger.setLevel(logging.DEBUG)

        from dataset_tools.metadata_engine import MetadataEngine

        # Pass the logger explicitly to avoid None logger issues
        engine = MetadataEngine(parser_defs_path, engine_logger)

        result = engine.get_parser_for_file(image_path)

        if result:
            if isinstance(result, dict):
                # Print key values safely
                for key in ["tool", "prompt", "negative_prompt", "parameters"]:
                    if key in result:
                        val = result[key]
                        if isinstance(val, str) and len(val) > 100:
                            pass
                        else:
                            pass
            elif hasattr(result, "tool"):
                pass
        else:
            pass

        return result

    except Exception:
        import traceback

        traceback.print_exc()
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
