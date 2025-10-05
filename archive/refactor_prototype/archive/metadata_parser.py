# refactor_prototype/metadata_parser.py

import json
import re

class MetadataParser:
    """
    Parses raw metadata from image files into a structured format.
    This is a simplified, direct implementation inspired by the logic in the user's original parser definitions.
    """
    def __init__(self, raw_metadata):
        self.raw_metadata = raw_metadata
        self.parsed_data = {
            "positive_prompt": "",
            "negative_prompt": "",
            "generation_details": {},
            "parameters": "", # Raw parameters string
            "tool": "Unknown"
        }

    def parse(self):
        """
        Applies a series of rules to extract meaningful data.
        """
        # Prefer the 'parameters' key first, as it's common in A1111 PNGs
        if 'parameters' in self.raw_metadata and isinstance(self.raw_metadata['parameters'], str):
            param_string = self.raw_metadata['parameters']
            # Check for A1111 signature
            if "Steps:" in param_string and "Sampler:" in param_string:
                self.parsed_data["tool"] = "A1111 WebUI"
                self.parsed_data["parameters"] = param_string
                self._parse_a1111_text(param_string)
                return self.parsed_data

        # Fallback for ComfyUI-style metadata (often in 'prompt' and 'workflow' keys)
        if 'prompt' in self.raw_metadata and 'workflow' in self.raw_metadata:
            self.parsed_data["tool"] = "ComfyUI"
            self._parse_comfyui_json()
            return self.parsed_data

        # Generic fallback if no specific format is detected
        self._create_fallback_details()
        return self.parsed_data

    def _parse_a1111_text(self, text):
        """Parses the classic A1111 metadata block."""
        text = text.strip()
        positive_prompt = ""
        neg_prompt_text = ""
        details_text = ""

        # Check for the presence of a negative prompt
        if "\nNegative prompt:" in text:
            # Split by negative prompt first
            main_parts = text.split("\nNegative prompt:", 1)
            positive_prompt = main_parts[0].strip()
            
            # The second part contains the negative prompt and details
            neg_and_details = main_parts[1]
            # The negative prompt is the first line of this part
            neg_lines = neg_and_details.split('\n', 1)
            neg_prompt_text = neg_lines[0].strip()
            if len(neg_lines) > 1:
                details_text = neg_lines[1].strip()
        else:
            # No negative prompt found, assume first line is prompt and the rest is details
            lines = text.split('\n', 1)
            positive_prompt = lines[0].strip()
            if len(lines) > 1:
                details_text = lines[1].strip()

        self.parsed_data['positive_prompt'] = positive_prompt
        self.parsed_data['negative_prompt'] = neg_prompt_text

        # Parse the key-value pairs from the details block
        gen_details = {}
        if details_text:
            # Use regex to find key: value pairs, allowing for values with commas
            kv_pattern = re.compile(r'([\w\s]+):\s*([^,]+(?:,[^,]+)*),?')
            matches = kv_pattern.findall(details_text)
            for key, value in matches:
                key = key.strip()
                value = value.strip()
                # Handle special cases
                if key == 'Size':
                    size_parts = value.split('x')
                    if len(size_parts) == 2:
                        gen_details['width'] = size_parts[0]
                        gen_details['height'] = size_parts[1]
                else:
                    gen_details[key] = value
        
        self.parsed_data['generation_details'] = gen_details

    def _parse_comfyui_json(self):
        """Handles ComfyUI's JSON-based metadata."""
        try:
            # In ComfyUI, the 'prompt' key contains the workflow API dump
            prompt_json = self.raw_metadata.get('prompt', '{}')
            if isinstance(prompt_json, str):
                prompt_data = json.loads(prompt_json)
            else:
                prompt_data = prompt_json
            
            # For now, we can't easily extract a single "positive" and "negative" prompt
            # So we will pretty-print the whole workflow.
            self.parsed_data['positive_prompt'] = "(See Generation Details for ComfyUI Workflow)"
            self.parsed_data['generation_details'] = prompt_data

        except json.JSONDecodeError:
            self.parsed_data['generation_details'] = {"error": "Could not parse ComfyUI JSON data."}

    def _create_fallback_details(self):
        """
        If no other parsing rules worked, create a simple key-value dump.
        """
        self.parsed_data['generation_details'] = self.raw_metadata