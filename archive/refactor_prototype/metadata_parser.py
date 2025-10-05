# refactor_prototype/metadata_parser.py

import json
import re
from collections import deque

class MetadataParser:
    """
    Parses raw metadata from image files into a structured format.
    NOW WITH: Targeted extraction for ComfyUI (no more getting lost in 1000-node workflows!)
    """
    def __init__(self, raw_metadata):
        self.raw_metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
        self.parsed_data = {
            "positive_prompt": "",
            "negative_prompt": "",
            "generation_details": {},
            "parameters": "",
            "tool": "Unknown"
        }

    def parse(self):
        """
        Applies a series of rules to extract meaningful data.
        This version is "source agnostic" and supports PNG, JPEG (EXIF), and more.
        """
        # --- NEW: Prioritized Search for Raw Data ---
        # This is the key to supporting multiple formats. We look for the data
        # in the most likely places, in order.
        
        a1111_string = None
        comfyui_json = None

        # 1. A1111's "parameters" key (PNGs from A1111)
        if 'parameters' in self.raw_metadata and isinstance(self.raw_metadata['parameters'], str):
            a1111_string = self.raw_metadata['parameters']
            self.parsed_data["tool"] = "A1111 WebUI" # Tentative tool name

        # 2. ComfyUI's "prompt" or "workflow" keys (PNGs from ComfyUI)
        elif 'prompt' in self.raw_metadata or 'workflow' in self.raw_metadata:
            # We prefer 'workflow' if available, as it's usually more complete
            comfyui_json_str = self.raw_metadata.get('workflow') or self.raw_metadata.get('prompt')
            if isinstance(comfyui_json_str, str):
                try:
                    comfyui_json = json.loads(comfyui_json_str)
                    self.parsed_data["tool"] = "ComfyUI"
                except json.JSONDecodeError:
                    # It might be an A1111 string hiding in the 'prompt' key
                    a1111_string = comfyui_json_str
            elif isinstance(comfyui_json_str, dict): # Already parsed
                comfyui_json = comfyui_json_str
                self.parsed_data["tool"] = "ComfyUI"

        # 3. EXIF UserComment (JPEGs from A1111)
        # Piexif often stores UserComment under the key 'UserComment' or inside an 'Exif' dict
        elif 'UserComment' in self.raw_metadata:
            a1111_string = self.raw_metadata['UserComment']
            self.parsed_data["tool"] = "A1111 WebUI (from JPEG EXIF)"
        
        # --- NOW, PROCESS THE DATA WE FOUND ---

        if a1111_string and "Steps:" in a1111_string:
            # We found what looks like an A1111 string
            self.parsed_data["parameters"] = a1111_string
            self._parse_a1111_text(a1111_string)
            return self.parsed_data

        if comfyui_json:
            # We found a ComfyUI JSON workflow
            self._parse_comfyui_targeted(comfyui_json) # Pass the parsed JSON directly
            return self.parsed_data

        # If we found an a1111_string but it didn't have "Steps:", it's probably just a prompt
        if a1111_string:
            self.parsed_data['positive_prompt'] = a1111_string
            self.parsed_data['parameters'] = a1111_string
            return self.parsed_data

        # Generic fallback if no specific format was detected
        self._create_fallback_details()
        return self.parsed_data

    def _parse_a1111_text(self, text):
        """
        Parses the classic A1111 metadata block.
        Format: "positive prompt\nNegative prompt: negative text\nSteps: X, Sampler: Y, ..."
        """
        text = text.strip()
        positive_prompt = ""
        neg_prompt_text = ""
        details_text = ""

        # Split by negative prompt marker
        if "\nNegative prompt:" in text:
            main_parts = text.split("\nNegative prompt:", 1)
            positive_prompt = main_parts[0].strip()
            
            # Extract negative prompt and details
            neg_and_details = main_parts[1]
            neg_lines = neg_and_details.split('\n', 1)
            neg_prompt_text = neg_lines[0].strip()
            if len(neg_lines) > 1:
                details_text = neg_lines[1].strip()
        else:
            # No negative prompt
            lines = text.split('\n', 1)
            positive_prompt = lines[0].strip()
            if len(lines) > 1:
                details_text = lines[1].strip()

        self.parsed_data['positive_prompt'] = positive_prompt
        self.parsed_data['negative_prompt'] = neg_prompt_text

        # Parse generation details
        gen_details = {}
        if details_text:
            # Regex to extract key-value pairs
            kv_pattern = re.compile(r'([\w\s]+):\s*([^,]+(?:,[^,]+)*?)(?=,\s*[\w\s]+:|$)')
            matches = kv_pattern.findall(details_text)
            
            for key, value in matches:
                key = key.strip()
                value = value.strip()
                
                # Handle special cases
                if key == 'Size':
                    size_parts = value.split('x')
                    if len(size_parts) == 2:
                        gen_details['width'] = size_parts[0].strip()
                        gen_details['height'] = size_parts[1].strip()
                else:
                    gen_details[key] = value
        
        self.parsed_data['generation_details'] = gen_details

    def _parse_comfyui_targeted(self, workflow_data: dict): # Changed argument name for clarity
        """
        THE NEW HOTNESS: Targeted extraction for ComfyUI workflows.
        NOW ACCEPTS a pre-parsed dictionary.
        """
        try:
            # The workflow is now passed in directly as a dictionary
            workflow = workflow_data

            # PHASE 1: CANDIDATE IDENTIFICATION
            # Find all nodes that could contain prompts
            candidates = self._find_text_candidates(workflow)
            
            if not candidates:
                # No text nodes found, fallback to raw dump
                self.parsed_data['positive_prompt'] = "(No text nodes found in workflow)"
                self.parsed_data['generation_details'] = workflow
                return

            # PHASE 2: PATH VALIDATION
            # Build connection map for fast path tracing
            connections = self._build_connection_map(workflow)
            
            # Find which candidates connect to samplers
            positive_candidate = self._find_connected_prompt(candidates, connections, workflow, 'positive')
            negative_candidate = self._find_connected_prompt(candidates, connections, workflow, 'negative')
            
            # Extract the text
            if positive_candidate:
                self.parsed_data['positive_prompt'] = positive_candidate.get('text', '')
            else:
                # Fallback: use first CLIPTextEncode we find
                for c in candidates:
                    if 'CLIP' in c.get('class_type', ''):
                        self.parsed_data['positive_prompt'] = c.get('text', '')
                        break
            
            if negative_candidate:
                self.parsed_data['negative_prompt'] = negative_candidate.get('text', '')
            
            # Store a summary of the workflow in generation details
            self.parsed_data['generation_details'] = {
                'workflow_complexity': f"{len(workflow)} nodes",
                'text_nodes_found': len(candidates),
                'positive_source': positive_candidate.get('class_type', 'Unknown') if positive_candidate else 'Not found',
                'negative_source': negative_candidate.get('class_type', 'Unknown') if negative_candidate else 'Not found',
                'raw_workflow': workflow  # Keep the full workflow for advanced users
            }

        except json.JSONDecodeError:
            self.parsed_data['generation_details'] = {"error": "Could not parse ComfyUI JSON data."}
        except Exception as e:
            self.parsed_data['generation_details'] = {"error": f"ComfyUI parsing error: {str(e)}"}

    def _find_text_candidates(self, workflow):
        """
        PHASE 1: Find all nodes that could contain prompt text.
        
        Returns a list of candidate dictionaries with:
        - node_id: The node's ID in the workflow
        - class_type: What kind of node it is
        - text: The actual text content
        """
        candidates = []
        
        # Known text-containing node types
        text_node_types = [
            'CLIPTextEncode',
            'CLIPTextEncodeSDXL',
            'Text Multiline',
            'ShowText|pysssss',
            'Text',
            'String',
            'DPRandomGenerator',
        ]
        
        for node_id, node_data in workflow.items():
            if not isinstance(node_data, dict):
                continue
            
            class_type = node_data.get('class_type', '')
            
            # Check if this node type can contain text
            if any(text_type in class_type for text_type in text_node_types):
                # Extract text from inputs
                inputs = node_data.get('inputs', {})
                text_content = inputs.get('text', '')
                
                # Some nodes store it differently
                if not text_content:
                    text_content = inputs.get('string', '')
                if not text_content:
                    text_content = inputs.get('prompt', '')
                
                if text_content:
                    candidates.append({
                        'node_id': node_id,
                        'class_type': class_type,
                        'text': text_content,
                        'inputs': inputs  # Keep full inputs for context
                    })
        
        return candidates

    def _build_connection_map(self, workflow):
        """
        Build a forward-connection map: {node_id: [nodes it outputs to]}
        
        This lets us quickly trace paths forward from text nodes to samplers.
        """
        connections = {}
        
        for node_id, node_data in workflow.items():
            if not isinstance(node_data, dict):
                continue
            
            # Look at this node's inputs to see what it connects FROM
            inputs = node_data.get('inputs', {})
            
            for input_name, input_value in inputs.items():
                # Connections are stored as [source_node_id, output_index]
                if isinstance(input_value, list) and len(input_value) >= 1:
                    source_node_id = str(input_value[0])
                    
                    # Add this node to the source node's output list
                    if source_node_id not in connections:
                        connections[source_node_id] = []
                    
                    connections[source_node_id].append({
                        'target_node': node_id,
                        'target_input': input_name
                    })
        
        return connections

    def _find_connected_prompt(self, candidates, connections, workflow, prompt_type='positive'):
        """
        PHASE 2: Find which candidate connects to a sampler's positive/negative input.
        
        Uses BFS (Breadth-First Search) to trace forward from each candidate
        until we find one that connects to a KSampler.
        
        Args:
            prompt_type: 'positive' or 'negative'
        
        Returns: The candidate dict that has a valid connection, or None
        """
        # Find all sampler nodes first
        samplers = []
        for node_id, node_data in workflow.items():
            if not isinstance(node_data, dict):
                continue
            
            class_type = node_data.get('class_type', '')
            if 'Sampler' in class_type or 'KSampler' in class_type:
                samplers.append(node_id)
        
        if not samplers:
            # No samplers found, return first candidate as fallback
            return candidates[0] if candidates else None
        
        # Score each candidate based on its path to a sampler
        best_candidate = None
        best_score = -1
        
        for candidate in candidates:
            score = self._trace_path_to_sampler(
                candidate['node_id'],
                samplers,
                connections,
                workflow,
                prompt_type
            )
            
            if score > best_score:
                best_score = score
                best_candidate = candidate
        
        return best_candidate if best_score > 0 else None

    def _trace_path_to_sampler(self, start_node, sampler_nodes, connections, workflow, prompt_type):
        """
        Trace forward from a candidate node to see if it reaches a sampler.
        Uses BFS to find the shortest path.
        
        Returns a score:
        - 100: Direct connection to correct sampler input
        - 50: Indirect connection through other nodes
        - 0: No connection found
        """
        if start_node not in connections:
            return 0  # Dead end
        
        visited = set()
        queue = deque([(start_node, 0)])  # (node_id, depth)
        
        while queue:
            current_node, depth = queue.popleft()
            
            if current_node in visited:
                continue
            visited.add(current_node)
            
            # Check connections from this node
            if current_node in connections:
                for connection in connections[current_node]:
                    target_node = connection['target_node']
                    target_input = connection['target_input']
                    
                    # Check if we reached a sampler
                    if target_node in sampler_nodes:
                        # Check if it's the correct input type
                        if prompt_type == 'positive' and 'positive' in target_input.lower():
                            return 100 - depth  # Direct connection, penalize by depth
                        elif prompt_type == 'negative' and 'negative' in target_input.lower():
                            return 100 - depth
                        else:
                            # Connected to sampler but wrong input
                            return 50 - depth
                    
                    # Continue searching if not too deep
                    if depth < 20:  # Prevent infinite loops
                        queue.append((target_node, depth + 1))
        
        return 0  # No path found

    def _create_fallback_details(self):
        """
        If no other parsing rules worked, just dump the raw metadata.
        """
        self.parsed_data['generation_details'] = self.raw_metadata
        self.parsed_data['positive_prompt'] = "(Unknown format - see Generation Details)"
