import json
import argparse
import os

# A set of common names for prompt fields in ComfyUI nodes
PROMPT_FIELD_NAMES = {"text", "prompt", "positive", "negative"}

def find_prompts_in_inputs(inputs: dict) -> dict:
    """
    Scans the 'inputs' dictionary of a node (API format) for prompt data.
    """
    found_prompts = {}
    for key, value in inputs.items():
        if key in PROMPT_FIELD_NAMES and isinstance(value, str):
            found_prompts[key] = value
    return found_prompts

def find_prompts_in_widgets(widgets: list) -> dict:
    """
    Scans the 'widgets_values' list of a node (UI format) for prompt data.
    This is more of a heuristic, as it looks for longer strings.
    """
    found_prompts = {}
    # In UI format, prompts are often the first long string in widgets_values
    for item in widgets:
        # Check if it's a string and has a reasonable length to be a prompt
        if isinstance(item, str) and len(item) > 10:
             # We assume the first one we find is the main 'text' or 'prompt'
             if 'text' not in found_prompts:
                found_prompts['text'] = item
    return found_prompts


def extract_node_data(input_path: str, output_path: str):
    """
    Extracts node ID, name, and prompt data from a ComfyUI JSON workflow
    and saves it to a new JSON file.

    Args:
        input_path (str): The path to the input JSON file.
        output_path (str): The path where the output JSON will be saved.
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

    extracted_nodes = []

    # --- Logic to handle both UI and API formats ---

    # Case 1: UI-saved workflow format (contains a 'nodes' key with a list)
    if 'nodes' in data and isinstance(data['nodes'], list):
        print("[*] Detected UI-saved workflow format.")
        for node in data['nodes']:
            node_info = {
                'id': node.get('id'),
                'name': node.get('type')
            }
            
            # Look for prompts in widget values
            prompts = {}
            if 'widgets_values' in node:
                prompts = find_prompts_in_widgets(node['widgets_values'])
            
            # If we found any prompts, add them to our node info
            if prompts:
                node_info['prompts'] = prompts
            
            extracted_nodes.append(node_info)

    # Case 2: API prompt format (nodes are top-level keys)
    # We can identify this by checking if keys are numeric strings.
    elif all(key.isdigit() for key in data.keys()):
        print("[*] Detected API prompt format.")
        for node_id, node_details in data.items():
            node_info = {
                'id': int(node_id), # Convert string ID to number
                'name': node_details.get('class_type')
            }

            # Look for prompts in the 'inputs' dictionary
            prompts = {}
            if 'inputs' in node_details:
                prompts = find_prompts_in_inputs(node_details['inputs'])
            
            if prompts:
                node_info['prompts'] = prompts
            
            extracted_nodes.append(node_info)

    else:
        print("[ERROR] Could not determine workflow format. The JSON structure is unrecognized.")
        return

    # --- Save the extracted data to the output file ---
    
    # Sort the nodes by ID for consistency
    extracted_nodes.sort(key=lambda x: x['id'])

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_nodes, f, indent=4)
        print(f"\n[SUCCESS] Extracted data for {len(extracted_nodes)} nodes.")
        print(f"[*] Output saved to: {output_path}")
    except IOError as e:
        print(f"[ERROR] Could not write to output file: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Extract node number, name, and prompt data from ComfyUI JSON workflows.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input ComfyUI JSON file."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help=(
            "Path for the output JSON file.\n"
            "If not provided, it will be saved next to the input file\n"
            "with an '_extracted' suffix (e.g., my_workflow_extracted.json)."
        )
    )

    args = parser.parse_args()

    # Determine the output path if not provided
    output_file = args.output
    if not output_file:
        base, ext = os.path.splitext(args.input_file)
        output_file = f"{base}_extracted.json"

    extract_node_data(args.input_file, output_file)