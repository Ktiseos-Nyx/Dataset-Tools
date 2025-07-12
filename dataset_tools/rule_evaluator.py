# In dataset_tools/rule_evaluator.py

import json

# import os
import re

# from pathlib import Path
import toml

# --- CORRECTED IMPORTS ---
from . import CONFIG_PATH  # Import the path from the package's __init__.py
from .metadata_engine.utils import json_path_get_utility


class RuleEvaluator:
    def __init__(self, logger) -> None:  # noqa: ANN001
        self.logger = logger
        self.rules: list[dict] = []

        rules_filepath = CONFIG_PATH / "rules.toml"
        self.logger.debug("RuleEvaluator: Checking for rules at: %s", rules_filepath)

        if rules_filepath.is_file():
            self.load_rules(str(rules_filepath))
        else:
            self.logger.warning(
                "No rules.toml file found or loaded at %s. Rule evaluation will be limited.",
                rules_filepath,
            )

    def load_rules(self, filepath: str) -> None:
        """Load and organizes detection rules from a specified TOML file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:  # noqa: PTH123, UP015
                all_config = toml.load(f)

            if "global_rules" in all_config:
                self.rules.extend(all_config["global_rules"])

            if "parsers" in all_config:
                for parser_name, parser_config in all_config["parsers"].items():
                    if "detection_rules" in parser_config:
                        for rule in parser_config["detection_rules"]:
                            rule["parser_name"] = parser_name
                        self.rules.extend(parser_config["detection_rules"])

            self.logger.info(f"Successfully loaded {len(self.rules)} rules from {filepath}.")
        except Exception as e:
            self.logger.error("Failed to load or parse rules from %s: %s", filepath, e, exc_info=True)

    def _get_a1111_param_string(self, context_data: dict) -> str | None:
        """Help to extract the A1111 parameter string from common locations with Unicode handling."""
        param_str = context_data.get("pil_info", {}).get("parameters")
        if isinstance(param_str, str):
            return param_str

        # Try enhanced UserComment extraction with Unicode decoding
        user_comment = context_data.get("raw_user_comment_str")
        if user_comment:
            # If it's already decoded, return it
            if "Steps:" in user_comment:
                return user_comment

        # If no decoded UserComment or it doesn't contain A1111 patterns, try enhanced extraction
        return self._extract_usercomment_for_detection(context_data)

    def _extract_usercomment_for_detection(self, context_data: dict) -> str | None:
        """Enhanced UserComment extraction for detection phase (Unicode handling)."""
        file_path = context_data.get("file_path_original")
        if not file_path:
            return None

        # Use PIL-based extraction only - no ExifTool dependency in production
        try:
            from PIL import Image

            with Image.open(file_path) as img:
                exif_data = img.getexif()
                if exif_data:
                    user_comment_raw = exif_data.get(37510)  # UserComment tag
                    if user_comment_raw and isinstance(user_comment_raw, bytes):
                        # Strategy 1: Unicode prefix with UTF-16
                        if user_comment_raw.startswith(b"UNICODE\x00\x00"):
                            try:
                                utf16_data = user_comment_raw[9:]
                                decoded = utf16_data.decode("utf-16le")
                                if "Steps:" in decoded:
                                    self.logger.debug(
                                        f"Detection: Manual Unicode extracted {len(decoded)} chars with A1111 patterns"
                                    )
                                    return decoded
                            except Exception as e:
                                self.logger.debug(f"Detection: Manual Unicode extraction failed as UTF-16: {e}")

                        # Strategy 2: charset=Unicode prefix
                        if user_comment_raw.startswith(b"charset=Unicode"):
                            try:
                                unicode_part = user_comment_raw[len(b"charset=Unicode ") :]
                                decoded = unicode_part.decode("utf-16le", errors="ignore")
                                if "Steps:" in decoded:
                                    self.logger.debug(
                                        f"Detection: charset=Unicode extracted {len(decoded)} chars with A1111 patterns"
                                    )
                                    return decoded
                            except Exception as e:
                                self.logger.debug(f"Detection: charset=Unicode extraction failed as UTF-16: {e}")
        except Exception as e:
            self.logger.debug(f"Detection: Manual Unicode extraction completely failed: {e}")

        self.logger.debug("Detection: No A1111 patterns found in UserComment")
        return None

    def _get_data_from_json_path(self, rule: dict, context_data: dict) -> tuple[any, bool]:
        """Handle source_types that need to query a JSON object via a path."""
        source_keys = rule.get("source_key_options") or [rule.get("source_key")]
        json_path_to_check = rule.get("json_path")

        initial_json_str = None
        for sk in source_keys:
            if sk and sk in context_data.get("pil_info", {}):
                initial_json_str = context_data["pil_info"].get(sk)
                if initial_json_str is not None:
                    break

        if not isinstance(initial_json_str, str):
            return None, False

        try:
            parsed_json = json.loads(initial_json_str)
            value_at_path = json_path_get_utility(parsed_json, json_path_to_check)
            return value_at_path, value_at_path is not None
        except json.JSONDecodeError:
            self.logger.debug("Could not parse JSON for JSON path rule.")
            return None, False

    def _get_source_data_and_status(self, rule: dict, context_data: dict) -> tuple[any, bool]:
        """Gets the source data for a rule to evaluate."""  # noqa: D401
        source_type = rule.get("source_type")
        source_key = rule.get("source_key")

        # --- Simple, direct lookups in context_data ---
        simple_source_map = {
            "pil_info_key": context_data.get("pil_info", {}).get(source_key),
            "png_chunk": context_data.get("png_chunks", {}).get(source_key),
            "software_tag": context_data.get("software_tag"),
            "exif_software_tag": context_data.get("software_tag"),
            "exif_user_comment": context_data.get("raw_user_comment_str"),
            "xmp_string_content": context_data.get("xmp_string"),
            "file_format": context_data.get("file_format"),
            "file_extension": context_data.get("file_extension"),
            "raw_file_content_text": context_data.get("raw_file_content_text"),
            "direct_context_key": context_data.get(source_key),
            "pil_info_pil_mode": context_data.get("pil_mode"),
            "pil_info_object": context_data.get("pil_info"),
            "context_iptc_field_value": context_data.get("parsed_iptc", {}).get(rule.get("iptc_field_name")),
        }
        if source_type in simple_source_map:
            data = simple_source_map[source_type]
            return data, data is not None

        # --- Chain for more complex source types ---

        if source_type == "pil_info_key_or_exif_user_comment_json_path":
            # This is one of the new, more complex handlers.
            json_path_to_check = rule.get("json_path")
            initial_json_str = None
            if source_key and source_key in context_data.get("pil_info", {}):
                initial_json_str = context_data["pil_info"].get(source_key)
            if not initial_json_str:
                initial_json_str = context_data.get("raw_user_comment_str")

            if not isinstance(initial_json_str, str):
                return None, False

            try:
                parsed_json = json.loads(initial_json_str)
                data_to_check = json_path_get_utility(parsed_json, json_path_to_check)
                return data_to_check, data_to_check is not None
            except json.JSONDecodeError:
                return None, False

        elif source_type == "direct_context_key_path_value":
            data = json_path_get_utility(context_data, source_key)
            return data, data is not None

        elif source_type == "auto_detect_parameters_or_usercomment":
            param_str = context_data.get("pil_info", {}).get("parameters")
            uc_str = context_data.get("raw_user_comment_str")
            data = param_str if param_str is not None else uc_str
            return data, data is not None

        elif source_type == "a1111_parameter_string_content":
            a1111_string = self._get_a1111_param_string(context_data)
            if a1111_string is None:
                return None, False
            try:
                wrapper = json.loads(a1111_string)
                if isinstance(wrapper, dict) and "parameters" in wrapper and isinstance(wrapper["parameters"], str):
                    return wrapper["parameters"], True
            except json.JSONDecodeError:
                pass
            return a1111_string, True

        elif source_type == "any_metadata_source":
            # Check PNG chunks first (for PNG files)
            png_chunks = context_data.get("pil_info", {})
            for chunk_key in ["prompt", "workflow", "parameters"]:
                chunk_data = png_chunks.get(chunk_key)
                if chunk_data is not None:
                    return chunk_data, True

            # Check EXIF UserComment (for JPEG files)
            user_comment = context_data.get("raw_user_comment_str")
            if user_comment is not None:
                return user_comment, True

            # Check XMP string
            xmp_string = context_data.get("xmp_string")
            if xmp_string is not None:
                return xmp_string, True

            # No metadata found
            return None, False

        elif source_type == "pil_info_key_json_path":
            return self._get_data_from_json_path(rule, context_data)

        elif source_type == "pil_info_key_json_path_string_is_json":
            value_at_path, found = self._get_data_from_json_path(rule, context_data)
            return value_at_path, found

        elif source_type == "json_from_usercomment_or_png_chunk":
            json_str = context_data.get("raw_user_comment_str")
            if not json_str:
                png_chunks = context_data.get("png_chunks", {})
                for key in rule.get("chunk_source_key_options_for_png", ["parameters", "Comment"]):
                    if key in png_chunks:
                        json_str = png_chunks[key]
                        break
            if json_str:
                try:
                    self.logger.debug(f"Attempting to load JSON from user comment/PNG chunk: {json_str[:50]}...")
                    return json.loads(json_str), True
                except json.JSONDecodeError:
                    self.logger.debug(f"Failed to decode JSON from user comment/PNG chunk: {json_str[:50]}...")
                    return None, False
            return None, False

        elif source_type == "json_from_xmp_exif_user_comment":
            json_str = context_data.get("xmp_user_comment_json_str")
            if json_str:
                self.logger.debug(f"Attempting to load JSON from extracted XMP UserComment: {json_str[:50]}...")
                try:
                    return json.loads(json_str), True
                except json.JSONDecodeError:
                    self.logger.debug(f"Failed to decode JSON from XMP UserComment: {json_str[:50]}...")
                    return None, False
            return None, False

        elif source_type == "json_from_exif_user_comment":
            json_str = context_data.get("raw_user_comment_str")
            if json_str:
                try:
                    self.logger.debug(f"Attempting to load JSON from raw_user_comment_str: {json_str[:50]}...")
                    return json.loads(json_str), True
                except json.JSONDecodeError:
                    self.logger.debug(f"Failed to decode JSON from raw_user_comment_str: {json_str[:50]}...")
                    return None, False
            return None, False

        # Handle pil_info_key_json_path_query - this IS implemented, check operator handling below
        elif source_type == "pil_info_key_json_path_query":
            value_at_path, found = self._get_data_from_json_path(rule, context_data)
            return value_at_path, found

        else:  # Final catch-all
            if source_type is not None:
                self.logger.warning(f"RuleEvaluator: Unknown source_type in detection rule: '{source_type}'")
            else:
                self.logger.debug("RuleEvaluator: Rule is missing 'source_type'.")
            return None, False

    def _apply_operator(self, operator: str, data_to_check: any, rule: dict, context_data: dict) -> bool:
        # Parameters extracted from 'rule' (as you have at the top of your _apply_operator)
        expected_value = rule.get("value")
        expected_keys = rule.get("expected_keys")
        regex_pattern = rule.get("regex_pattern")
        regex_patterns = rule.get("regex_patterns")
        json_path = rule.get("json_path")
        json_query_type = rule.get("json_query_type")
        class_types_to_check = rule.get("class_types_to_check")
        value_list = rule.get("value_list")
        source_type = rule.get("source_type")

        try:
            if operator == "exists":
                return data_to_check is not None
            elif operator in {"not_exists", "is_none"}:  # noqa: RET505
                return data_to_check is None
            elif operator == "is_not_none":
                return data_to_check is not None
            elif operator == "equals":
                if data_to_check is None and expected_value is not None:
                    return False
                if data_to_check is not None and expected_value is None:
                    return False
                if data_to_check is None and expected_value is None:
                    return True
                return str(data_to_check).strip() == str(expected_value).strip()
            elif operator == "equals_case_insensitive":
                if data_to_check is None and expected_value is not None:
                    return False
                if data_to_check is not None and expected_value is None:
                    return False
                if data_to_check is None and expected_value is None:
                    return True
                return str(data_to_check).strip().lower() == str(expected_value).strip().lower()
            elif operator == "contains":
                if not isinstance(data_to_check, str):
                    return False
                return str(expected_value) in data_to_check
            elif operator == "contains_case_insensitive":
                if not isinstance(data_to_check, str):
                    return False
                return str(expected_value).lower() in data_to_check.lower()
            elif operator == "startswith":
                if not isinstance(data_to_check, str):
                    return False
                return data_to_check.startswith(str(expected_value))
            elif operator == "endswith":
                if not isinstance(data_to_check, str):
                    return False
                return data_to_check.endswith(str(expected_value))
            elif operator == "regex_match":
                if not isinstance(data_to_check, str):
                    return False
                if not regex_pattern:
                    self.logger.warning("RuleEvaluator: Operator 'regex_match' called without 'regex_pattern'.")
                    return False
                return re.search(regex_pattern, data_to_check) is not None
            elif operator == "regex_match_all":
                if not isinstance(data_to_check, str):
                    return False
                if not regex_patterns or not isinstance(regex_patterns, list):
                    self.logger.warning("RuleEvaluator: 'regex_match_all' needs list 'regex_patterns'.")
                    return False
                return all(re.search(p, data_to_check) for p in regex_patterns)
            elif operator == "regex_match_any":
                if not isinstance(data_to_check, str):
                    return False
                if not regex_patterns or not isinstance(regex_patterns, list):
                    self.logger.warning("RuleEvaluator: 'regex_match_any' needs list 'regex_patterns'.")
                    return False
                return any(re.search(p, data_to_check) for p in regex_patterns)
            elif operator == "is_string":
                return isinstance(data_to_check, str)
            elif operator == "is_true" and source_type != "pil_info_key_json_path_query":
                return data_to_check is True
            elif operator == "is_in_list":
                if data_to_check is None:
                    return False
                if not value_list or not isinstance(value_list, list):
                    self.logger.warning("RuleEvaluator: 'is_in_list' needs list 'value_list'.")
                    return False
                return str(data_to_check) in value_list

            elif operator == "json_path_exists":  # This was one of the operators we added earlier
                if not json_path:
                    self.logger.warning("RuleEvaluator: Operator 'json_path_exists': 'json_path' not provided in rule.")
                    return False
                target_obj = None
                if isinstance(data_to_check, dict | list):
                    target_obj = data_to_check
                elif isinstance(data_to_check, str):
                    try:
                        target_obj = json.loads(data_to_check)
                    except json.JSONDecodeError:
                        self.logger.debug("RuleEvaluator: Op 'json_path_exists': data string not valid JSON.")
                        return False
                else:
                    self.logger.debug("RuleEvaluator: Op 'json_path_exists': data not suitable for JSON path.")
                    return False
                return json_path_get_utility(target_obj, json_path) is not None

            # --- THIS IS THE json_contains_any_key BLOCK ---
            elif operator == "json_contains_any_key":
                target_json_obj_for_keys = None  # Initialize

                if isinstance(data_to_check, dict):  # data_to_check might be pil_info or parsed JSON from source_type
                    target_json_obj_for_keys = data_to_check
                elif isinstance(data_to_check, str):  # If data_to_check is a string that needs parsing
                    try:
                        target_json_obj_for_keys = json.loads(data_to_check)
                    except json.JSONDecodeError:
                        self.logger.debug(f"RuleEvaluator: Op '{operator}', data_to_check string not valid JSON.")
                        return False  # Cannot proceed if string is not valid JSON
                # else: data_to_check is None or some other type, target_json_obj_for_keys remains None

                # Now check if we have a dictionary to work with
                if not isinstance(target_json_obj_for_keys, dict):
                    self.logger.debug(
                        f"RuleEvaluator: Op '{operator}', target for key check is not a dictionary (was {type(data_to_check)})."
                    )
                    return False

                # 'expected_keys' is defined at the top of _apply_operator from rule.get("expected_keys")
                if not expected_keys or not isinstance(expected_keys, list):
                    self.logger.warning(f"RuleEvaluator: Op '{operator}' needs a list for 'expected_keys' in rule.")
                    return False  # Rule is malformed if expected_keys isn't a list

                if not expected_keys:  # If the list of expected_keys is empty
                    self.logger.debug(
                        f"RuleEvaluator: Op '{operator}', 'expected_keys' list is empty. Returning False as no keys can be found."
                    )
                    return False  # Or True, depending on desired behavior for empty list (usually False)

                return any(k in target_json_obj_for_keys for k in expected_keys)
            # --- THIS IS THE exists_and_is_dictionary BLOCK ---
            elif operator == "exists_and_is_dictionary":
                # data_to_check should be the object from source_type, e.g., pil_info_object
                is_dict = isinstance(data_to_check, dict)
                # bool(data_to_check) checks if the dictionary is not empty
                is_not_empty = bool(data_to_check) if is_dict else False
                self.logger.debug(
                    f"RuleEvaluator: Op 'exists_and_is_dictionary': data type {type(data_to_check)}, is_dict={is_dict}, is_not_empty={is_not_empty}"
                )
                return is_dict and is_not_empty

            # ...
            elif operator == "json_path_value_equals":
                if not json_path:
                    self.logger.warning("RuleEvaluator: Op 'json_path_value_equals': 'json_path' not provided.")
                    return False
                target_obj = None
                if isinstance(data_to_check, dict | list):
                    target_obj = data_to_check
                elif isinstance(data_to_check, str):
                    try:
                        target_obj = json.loads(data_to_check)
                    except json.JSONDecodeError:
                        self.logger.debug("RuleEvaluator: Op 'json_path_value_equals': data string not valid JSON.")
                        return False
                else:
                    self.logger.debug("RuleEvaluator: Op 'json_path_value_equals': data not suitable for JSON path.")
                    return False
                value_at_path = json_path_get_utility(target_obj, json_path)  # USE UTILITY
                if value_at_path is None and expected_value is not None:
                    return False
                if value_at_path is not None and expected_value is None:
                    return False
                if value_at_path is None and expected_value is None:
                    return True
                return str(value_at_path).strip() == str(expected_value).strip()

            elif operator == "is_valid_json":
                if source_type == "file_content_json":
                    return isinstance(context_data.get("parsed_root_json_object"), dict | list)
                if isinstance(data_to_check, dict | list):
                    return True
                if not isinstance(data_to_check, str):
                    return False
                try:
                    json.loads(data_to_check)
                    return True
                except json.JSONDecodeError:
                    return False

            elif operator == "is_valid_json_structure":
                return isinstance(context_data.get("parsed_root_json_object"), dict | list)

            elif operator in ["json_contains_keys", "json_contains_all_keys"]:
                target_json_obj_for_keys = None
                if isinstance(data_to_check, dict):
                    target_json_obj_for_keys = data_to_check
                elif isinstance(data_to_check, str):
                    try:
                        target_json_obj_for_keys = json.loads(data_to_check)
                    except json.JSONDecodeError:
                        return False
                if not isinstance(target_json_obj_for_keys, dict):
                    return False
                if not expected_keys or not isinstance(expected_keys, list):
                    self.logger.warning("RuleEvaluator: '{operator}' needs list 'expected_keys'.")
                    return False
                return all(k in target_json_obj_for_keys for k in expected_keys)

            elif operator == "is_true" and source_type == "pil_info_key_json_path_query":
                if not isinstance(data_to_check, str):
                    self.logger.debug(
                        "RuleEvaluator: Operator 'is_true' with 'pil_info_key_json_path_query' expected string data_to_check, got {type(data_to_check)}"
                    )
                    return False
                if not json_query_type:  # json_query_type is from top of this method
                    self.logger.warning(
                        "RuleEvaluator: Operator 'is_true' with 'pil_info_key_json_path_query': 'json_query_type' not provided."
                    )
                    return False
                try:
                    json_obj_for_query = json.loads(data_to_check)
                    if json_query_type == "has_numeric_string_keys":
                        return isinstance(json_obj_for_query, dict) and any(k.isdigit() for k in json_obj_for_query)
                    if json_query_type == "has_any_node_class_type":
                        if not class_types_to_check or not isinstance(
                            class_types_to_check, list
                        ):  # class_types_to_check from top
                            self.logger.warning(
                                "RuleEvaluator: Operator 'is_true' with query 'has_any_node_class_type': 'class_types_to_check' not provided or not a list."
                            )
                            return False
                        if not isinstance(json_obj_for_query, dict):
                            return False
                        nodes_container = json_obj_for_query.get("nodes", json_obj_for_query)
                        if not isinstance(nodes_container, dict):
                            return False
                        return any(
                            isinstance(nd_val, dict) and nd_val.get("type") in class_types_to_check
                            for nd_val in nodes_container.values()
                        )
                    else:  # noqa: RET505
                        self.logger.warning(
                            "RuleEvaluator: Operator 'is_true' with 'pil_info_key_json_path_query': Unknown 'json_query_type': {json_query_type}"
                        )
                        return False
                except json.JSONDecodeError:
                    self.logger.debug(
                        "RuleEvaluator: Operator 'is_true' with 'pil_info_key_json_path_query': data_to_check string is not valid JSON."
                    )
                    return False

            elif operator == "not_strictly_simple_json_object_with_prompt_key":
                if not isinstance(data_to_check, str):
                    self.logger.debug(f"RuleEvaluator: Operator '{operator}': data_to_check is not a string, failing.")
                    return False
                is_simple_json_with_prompt = False
                try:
                    parsed_json = json.loads(data_to_check)
                    if isinstance(parsed_json, dict):
                        has_prompt_key = any(k in parsed_json for k in ["prompt", "Prompt", "positive_prompt"])
                        if has_prompt_key:
                            is_simple_json_with_prompt = True
                except json.JSONDecodeError:
                    return True
                return not is_simple_json_with_prompt

            # <<< INSERT THE NEW OPERATOR *BEFORE* THE FINAL 'else' >>>

            elif operator == "does_not_contain":
                if not isinstance(data_to_check, str):
                    return False
                return str(expected_value) not in data_to_check

            elif operator == "exists_and_is_dictionary":
                # For source_type "pil_info_object", data_to_check should be context_data.get("pil_info")
                is_dict = isinstance(data_to_check, dict)
                # bool(data_to_check) checks if the dictionary is not empty
                is_not_empty = bool(data_to_check) if is_dict else False
                self.logger.debug(
                    f"RuleEvaluator: Op 'exists_and_is_dictionary': data type {type(data_to_check)}, is_dict={is_dict}, is_not_empty={is_not_empty}"
                )
                return is_dict and is_not_empty

            # This 'else' should be the VERY LAST condition in the operator chain
            else:
                self.logger.warning(
                    f"RuleEvaluator: Operator '{operator}' is not implemented or recognized. Rule: {rule.get('comment', 'Unnamed')}"
                )
                return False

        except Exception as e_op:
            self.logger.error(
                f"RuleEvaluator: Error evaluating op '{operator}' for rule '{rule.get('comment', 'Unnamed rule')}': {e_op}",
                exc_info=True,
            )
            return False

    def evaluate_rule(self, rule: dict, context_data: dict) -> bool:
        operator_for_precheck = rule.get("operator", "exists")
        data_to_check, source_found = self._get_source_data_and_status(rule, context_data)

        if not source_found and operator_for_precheck not in ["not_exists", "is_none"]:
            rule_comment = rule.get(
                "comment",
                f"source_type: {rule.get('source_type')}, operator: {operator_for_precheck}",
            )
            self.logger.debug(f"RuleEvaluator: Source data not found for rule '{rule_comment}'.")
            return False

        return self._apply_operator(operator_for_precheck, data_to_check, rule, context_data)
