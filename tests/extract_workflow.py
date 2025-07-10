import json
import argparse
import os

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
    # 1. Check for direct prompt keys
    for key, value in node_dict.items():
        if key in PROMPT_KEYS and isinstance(value, str):
            prompts[key] = value

    # 2. Check inside 'inputs' dictionary
    if 'inputs' in node_dict and isinstance(node_dict['inputs'], dict):
        for key, value in node_dict['inputs'].items():
            if key in PROMPT_KEYS and isinstance(value, str):
                prompts[key] = value

    # 3. Check inside 'widgets_values'
    if 'widgets_values' in node_dict and isinstance(node_dict['widgets_values'], list):
        for item in node_dict['widgets_values']:
            # Handle both plain strings and lists containing one string (like in ShowText)
            text_to_check = ""
            if isinstance(item, str):
                text_to_check = item
            elif isinstance(item, list) and item and isinstance(item[0], str):
                text_to_check = item[0]

            if text_to_check and len(text_to_check) > 10:
                if 'text' not in prompts:
                    prompts['text'] = text_to_check
                elif 'text_2' not in prompts: # For nodes with multiple text boxes
                    prompts['text_2'] = text_to_check

    if prompts:
        info['prompts'] = prompts

    return info

def find_nodes_recursively(data, found_nodes: list, found_hashes: set):
    """
    Traverses a Python object (from JSON) and extracts things that look like nodes.
    Now handles nested JSON within strings.
    """
    # If it's a dictionary, check if it's a node, then search its values.
    if isinstance(data, dict):
        has_id = any(key in data for key in ID_KEYS)
        has_name = any(key in data for key in NAME_KEYS)

        if has_id and has_name:
            node_hash = json.dumps(data, sort_keys=True)
            if node_hash not in found_hashes:
                node_info = extract_info_from_node(data)
                # Only add if we successfully found an ID and a name
                if 'id' in node_info and 'name' in node_info:
                    found_nodes.append(node_info)
                    found_hashes.add(node_hash)

        # Always continue searching inside the dictionary's values
        for value in data.values():
            find_nodes_recursively(value, found_nodes, found_hashes)

    # If it's a list, search each item in the list.
    elif isinstance(data, list):
        for item in data:
            find_nodes_recursively(item, found_nodes, found_hashes)

    # --- NEW: THE CRITICAL FIX ---
    # If it's a string, check if it's a JSON string and parse it.
    elif isinstance(data, str):
        stripped_data = data.strip()
        if (stripped_data.startswith('{') and stripped_data.endswith('}')) or \
           (stripped_data.startswith('[') and stripped_data.endswith(']')):
            try:
                # It looks like JSON, let's try to parse it
                nested_data = json.loads(data)
                # If successful, recurse into the newly parsed data
                find_nodes_recursively(nested_data, found_nodes, found_hashes)
            except json.JSONDecodeError:
                # It wasn't valid JSON after all, so we just ignore it.
                pass

def process_json_file(input_path: str, output_path: str):
    """
    Loads a JSON, performs a deep search for nodes, and saves the results.
    """
    print(f"[*] Processing file: {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Input file not found at: {input_path}")
        return
    except json.JSONDecodeError:
        print(f"[ERROR] Invalid JSON format in file: {input_path}")
        return

    print("[*] Starting deep search for node-like objects (including within JSON strings)...")
    all_nodes = []
    found_node_hashes = set()

    find_nodes_recursively(data, all_nodes, found_node_hashes)

    if not all_nodes:
        print("[*] Search complete. No node-like objects were found.")
        return

    def sort_key(node):
        node_id = node.get('id', 0)
        return int(node_id) if isinstance(node_id, (int, str)) and str(node_id).isdigit() else 0
    all_nodes.sort(key=sort_key)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_nodes, f, indent=4)
        print(f"\n[SUCCESS] Found and extracted data for {len(all_nodes)} nodes.")
        print(f"[*] Output saved to: {output_path}")
    except IOError as e:
        print(f"[ERROR] Could not write to output file: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Recursively search ANY JSON file for 'nodes' and extract their ID, name, and prompt data. Handles JSON embedded within strings.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_file", type=str, help="Path to the input JSON file (can be any structure).")
    parser.add_argument("-o", "--output", type=str, help="Path for the output JSON file.\nIf not provided, it will be saved next to the input file with an '_extracted' suffix.")
    args = parser.parse_args()
    output_file = args.output or f"{os.path.splitext(args.input_file)[0]}_extracted.json"
    process_json_file(args.input_file, output_file)
