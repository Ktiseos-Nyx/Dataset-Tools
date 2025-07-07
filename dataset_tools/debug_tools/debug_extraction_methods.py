#!/usr/bin/env python3

"""
Test the ComfyUI extraction methods directly.
"""

class MockLogger:
    def debug(self, msg):
        print(f"DEBUG: {msg}")
    def warning(self, msg):
        print(f"WARNING: {msg}")
    def error(self, msg):
        print(f"ERROR: {msg}")

class SimpleComfyUIExtractor:
    """Simplified version of the ComfyUI extractor for testing."""
    
    def __init__(self):
        self.logger = MockLogger()
    
    def _clean_prompt_text(self, text):
        """Clean prompt text."""
        return text.strip() if text else ""
    
    def _find_node_by_id(self, nodes, node_id):
        """Find a node by its ID in either list or dict format."""
        if isinstance(nodes, dict):
            return nodes.get(str(node_id))
        elif isinstance(nodes, list):
            for node in nodes:
                if str(node.get("id", "")) == str(node_id):
                    return node
        return None
    
    def _find_text_from_main_sampler_input(self, data, method_def, context, fields):
        """Find text from main sampler input by traversing ComfyUI workflow connections."""
        self.logger.debug("[ComfyUI] Starting advanced text traversal...")
        if not isinstance(data, dict):
            return ""

        sampler_node_types = method_def.get("sampler_node_types", ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"])
        text_input_name_in_encoder = method_def.get("text_input_name_in_encoder", "text")
        text_encoder_types = method_def.get("text_encoder_node_types", ["CLIPTextEncode", "BNK_CLIPTextEncodeAdvanced"])

        # Determine which input to follow (positive or negative)
        if method_def.get("positive_input_name"):
            target_input_name = method_def.get("positive_input_name")
        elif method_def.get("negative_input_name"):
            target_input_name = method_def.get("negative_input_name")
        else:
            target_input_name = "positive"

        # Handle both prompt format (dict of nodes) and workflow format (nodes array)
        if isinstance(data, dict) and "nodes" in data:
            # Workflow format: {"nodes": [...]}
            nodes = data["nodes"]
        elif isinstance(data, dict) and all(isinstance(v, dict) for v in data.values()):
            # Prompt format: {"1": {...}, "2": {...}, ...}
            nodes = data
        else:
            return ""
        
        if not isinstance(nodes, (dict, list)):
            return ""

        # 1. Find the main sampler node
        main_sampler = None
        node_iterator = nodes.items() if isinstance(nodes, dict) else enumerate(nodes)
        for node_id, node_data in node_iterator:
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", node_data.get("type", ""))
                if any(sampler_type in class_type for sampler_type in sampler_node_types):
                    main_sampler = node_data
                    self.logger.debug(f"[ComfyUI] Found main sampler: {class_type} (ID: {node_data.get('id', node_id)})")
                    break

        if not main_sampler:
            self.logger.debug("[ComfyUI] No main sampler node found.")
            return ""

        # 2. Get the initial connection from the sampler
        inputs = main_sampler.get("inputs", {})
        target_connection = None
        if isinstance(inputs, dict):
            target_connection = inputs.get(target_input_name)
        elif isinstance(inputs, list):
            for input_item in inputs:
                if isinstance(input_item, dict) and input_item.get("name") == target_input_name:
                    link_id = input_item.get("link")
                    if link_id is not None:
                        target_connection = [link_id, 0]
                    break

        self.logger.debug(f"[ComfyUI] Target input '{target_input_name}' connection: {target_connection}")

        if not target_connection or not isinstance(target_connection, list) or len(target_connection) == 0:
            self.logger.debug(f"[ComfyUI] No initial connection found for '{target_input_name}'.")
            return ""

        # 3. Traverse backwards from the connection
        current_node_id = target_connection[0]

        MAX_TRAVERSAL_DEPTH = 20
        for i in range(MAX_TRAVERSAL_DEPTH):
            self.logger.debug(f"[ComfyUI] Traversal depth {i+1}, current node ID: {current_node_id}")

            current_node = self._find_node_by_id(nodes, current_node_id)
            if not current_node:
                self.logger.debug(f"[ComfyUI] Traversal failed: Node ID {current_node_id} not found.")
                return ""

            class_type = current_node.get("class_type", current_node.get("type", ""))
            self.logger.debug(f"[ComfyUI] Current node type: {class_type}")

            # 4a. Check if we found a text encoder
            if any(encoder_type in class_type for encoder_type in text_encoder_types):
                self.logger.debug(f"[ComfyUI] Found text encoder: {class_type}")
                encoder_inputs = current_node.get("inputs", {})
                self.logger.debug(f"[ComfyUI] Text encoder inputs: {encoder_inputs}")
                
                if text_input_name_in_encoder in encoder_inputs:
                    text = str(encoder_inputs[text_input_name_in_encoder])
                    self.logger.debug(f"[ComfyUI] Extracted text: '{text}'")
                    return self._clean_prompt_text(text)

                widgets = current_node.get("widgets_values", [])
                if widgets:
                    text = str(widgets[0])
                    self.logger.debug(f"[ComfyUI] Extracted text from widgets: '{text}'")
                    return self._clean_prompt_text(text)
                return ""

            # 4b. Check if it's a passthrough/reroute node
            node_inputs = current_node.get("inputs", {})
            if "Reroute" in class_type or len(node_inputs) == 1:
                self.logger.debug(f"[ComfyUI] Traversing through passthrough node: {class_type}.")

                next_connection = None
                if isinstance(node_inputs, dict) and node_inputs:
                    first_input_key = next(iter(node_inputs))
                    next_connection = node_inputs.get(first_input_key)
                elif isinstance(node_inputs, list) and node_inputs:
                    link_id = node_inputs[0].get("link")
                    if link_id is not None:
                        next_connection = [link_id, 0]

                if isinstance(next_connection, list) and len(next_connection) > 0:
                    current_node_id = next_connection[0]
                    continue

            self.logger.debug(f"[ComfyUI] Traversal stopped at node type: {class_type}. Not a recognized text encoder or passthrough node.")
            return ""

        self.logger.warning("[ComfyUI] Traversal depth limit reached, could not find text encoder.")
        return ""

def test_extraction():
    """Test the extraction methods."""
    
    print("🔧 TESTING COMFYUI EXTRACTION METHODS")
    print("=" * 38)
    
    # Sample T5 workflow data
    sample_t5_data = {
        "1": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "t5xxl_fp16.safetensors",
                "clip_name2": "clip_l.safetensors"
            }
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "beautiful landscape with mountains and trees",
                "clip": [1, 0]
            }
        },
        "3": {
            "class_type": "CLIPTextEncode", 
            "inputs": {
                "text": "low quality, blurry",
                "clip": [1, 0]
            }
        },
        "4": {
            "class_type": "KSampler",
            "inputs": {
                "model": [5, 0],
                "positive": [2, 0],
                "negative": [3, 0],
                "latent_image": [6, 0],
                "seed": 123456,
                "steps": 20,
                "cfg": 7.5,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0
            }
        },
        "5": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "sd3_medium_incl_clips_t5xxlfp16.safetensors"
            }
        },
        "6": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 1024,
                "height": 1024,
                "batch_size": 1
            }
        }
    }
    
    extractor = SimpleComfyUIExtractor()
    
    print("1. Testing positive prompt extraction:")
    method_def = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "positive_input_name": "positive",
        "text_input_name_in_encoder": "text",
        "text_encoder_node_types": ["CLIPTextEncode", "CLIPTextEncodeSD3", "T5TextEncode", "BNK_CLIPTextEncodeAdvanced", "CLIPTextEncodeAdvanced"]
    }
    
    result = extractor._find_text_from_main_sampler_input(sample_t5_data, method_def, {}, {})
    print(f"   Result: '{result}'")
    
    if result == "beautiful landscape with mountains and trees":
        print("   ✅ SUCCESS: Positive prompt extracted correctly!")
    else:
        print("   ❌ FAILED: Positive prompt extraction failed")
    
    print("\n2. Testing negative prompt extraction:")
    method_def = {
        "sampler_node_types": ["KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced"],
        "negative_input_name": "negative",
        "text_input_name_in_encoder": "text",
        "text_encoder_node_types": ["CLIPTextEncode", "CLIPTextEncodeSD3", "T5TextEncode", "BNK_CLIPTextEncodeAdvanced", "CLIPTextEncodeAdvanced"]
    }
    
    result = extractor._find_text_from_main_sampler_input(sample_t5_data, method_def, {}, {})
    print(f"   Result: '{result}'")
    
    if result == "low quality, blurry":
        print("   ✅ SUCCESS: Negative prompt extracted correctly!")
    else:
        print("   ❌ FAILED: Negative prompt extraction failed")

if __name__ == "__main__":
    test_extraction()