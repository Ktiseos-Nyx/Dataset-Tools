import json
import argparse
import os
import sys

# --- Heuristics: What makes a dictionary a "node"? ---
ID_KEYS = {"id", "_id", "uuid", "node_id"}
NAME_KEYS = {"type", "name", "class_type", "title", "node_type"}
PROMPT_KEYS = {"text", "prompt", "positive", "negative"}

def extract_info_from_node(node_dict: dict) -> dict:
    """
    Given a dictionary that is likely a node, extract the standardized info.
    """
    info = {}
    for key in ID_KEYS:
        if key in node_dict:
            info['id'] = node_dict[key]
            break
    for key in NAME_KEYS:
        if key in node_dict:
            info['name'] = node_dict[key]
            break

    prompts = {}
    if 'inputs' in node_dict and isinstance(node_dict['inputs'], dict):
        for key, value in node_dict['inputs'].items():
            if key in PROMPT_KEYS and isinstance(value, str):
                prompts[key] = value

    if 'widgets_values' in node_dict and isinstance(node_dict['widgets_values'], list):
        for item in node_dict['widgets_values']:
            text_to_check = ""
            if isinstance(item, str):
                text_to_check = item
            elif isinstance(item, list) and item and isinstance(item[0], str):
                text_to_check = item[0]

            if text_to_check and len(text_to_check) > 10:
                if 'text' not in prompts:
                    prompts['text'] = text_to_check
                elif 'text_2' not in prompts:
                    prompts['text_2'] = text_to_check

    if prompts:
        info['prompts'] = prompts

    return info

def find_nodes_recursively(data, found_nodes: list, found_hashes: set):
    """
    Traverses a Python object (from JSON) and extracts things that look like nodes.
    Now handles nested JSON within strings.
    """
    if isinstance(data, dict):
        has_id = any(key in data for key in ID_KEYS)
        has_name = any(key in data for key in NAME_KEYS)

        if has_id and has_name:
            node_hash = json.dumps(data, sort_keys=True)
            if node_hash not in found_hashes:
                node_info = extract_info_from_node(data)
                if 'id' in node_info and 'name' in node_info:
                    found_nodes.append(node_info)
                    found_hashes.add(node_hash)

        for value in data.values():
            find_nodes_recursively(value, found_nodes, found_hashes)
    elif isinstance(data, list):
        for item in data:
            find_nodes_recursively(item, found_nodes, found_hashes)
    elif isinstance(data, str):
        stripped_data = data.strip()
        if (stripped_data.startswith('{') and stripped_data.endswith('}')) or \
           (stripped_data.startswith('[') and stripped_data.endswith(']')):
            try:
                nested_data = json.loads(data)
                find_nodes_recursively(nested_data, found_nodes, found_hashes)
            except json.JSONDecodeError:
                pass

def process_json_file(input_path: str, output_path: str):
    """
    Worker function: Loads a single JSON, performs a deep search, and saves the results.
    """
    print(f"[*] Reading: {os.path.basename(input_path)}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"    [ERROR] Could not read or parse file: {e}")
        return False

    all_nodes = []
    found_node_hashes = set()
    find_nodes_recursively(data, all_nodes, found_node_hashes)

    if not all_nodes:
        print("    [INFO] No node-like objects were found in this file.")
        return False

    def sort_key(node):
        node_id = node.get('id', 0)
        return int(node_id) if isinstance(node_id, (int, str)) and str(node_id).isdigit() else 0
    all_nodes.sort(key=sort_key)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_nodes, f, indent=4)
        print(f"    [SUCCESS] Extracted {len(all_nodes)} nodes -> {os.path.basename(output_path)}")
        return True
    except IOError as e:
        print(f"    [ERROR] Could not write to output file: {e}")
        return False

# --- New Main "Manager" Block ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Batch process a folder of JSON files to extract node data.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_folder",
        type=str,
        help="Path to the folder containing your JSON files."
    )
    parser.add_argument(
        "-o", "--output_folder",
        type=str,
        help=(
            "Path for the output folder.\n"
            "If not provided, a subfolder named 'extracted_output' will be created\n"
            "inside the input folder."
        )
    )
    args = parser.parse_args()

    # --- 1. Validate paths and create output directory ---
    if not os.path.isdir(args.input_folder):
        print(f"[ERROR] Input folder not found: {args.input_folder}")
        sys.exit(1)

    output_dir = args.output_folder
    if not output_dir:
        output_dir = os.path.join(args.input_folder, "extracted_output")

    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Output will be saved in: {os.path.abspath(output_dir)}")
    print("-" * 40)

    # --- 2. Loop through the input folder ---
    json_files = [f for f in os.listdir(args.input_folder) if f.lower().endswith('.json')]

    if not json_files:
        print("[INFO] No .json files found in the input folder.")
        sys.exit(0)

    success_count = 0
    fail_count = 0
    for filename in json_files:
        input_path = os.path.join(args.input_folder, filename)

        # Construct a clean output filename
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}_extracted.json"
        output_path = os.path.join(output_dir, output_filename)

        if process_json_file(input_path, output_path):
            success_count += 1
        else:
            fail_count += 1

    # --- 3. Final Summary ---
    print("-" * 40)
    print("Batch processing complete.")
    print(f"    Total files processed: {len(json_files)}")
    print(f"    Successful: {success_count}")
    print(f"    Failed or empty: {fail_count}")
    print(f"[*] Check the '{os.path.abspath(output_dir)}' folder for your results.")
