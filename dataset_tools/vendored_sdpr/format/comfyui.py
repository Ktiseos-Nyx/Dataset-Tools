# dataset_tools/vendored_sdpr/format/comfyui.py

__author__ = "receyuki"
__filename__ = "comfyui.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json

from .base_format import BaseFormat
from ..logger import Logger # Use your vendored logger
from ..utility import remove_quotes, merge_dict # Assuming utility.py is in the same 'format' dir
from ..constants import PARAMETER_PLACEHOLDER

class ComfyUI(BaseFormat):
    tool = "ComfyUI" # Tool name

    # comfyui node types (class attributes for easy access)
    KSAMPLER_TYPES = ["KSampler", "KSamplerAdvanced", "KSampler (Efficient)"]
    VAE_ENCODE_TYPE = ["VAEEncode", "VAEEncodeForInpaint"]
    CHECKPOINT_LOADER_TYPE = [
        "CheckpointLoader", "CheckpointLoaderSimple", "unCLIPCheckpointLoader",
        "Checkpoint Loader (Simple)", # Original name from ComfyUI
    ]
    CLIP_TEXT_ENCODE_TYPE = [
        "CLIPTextEncode", "CLIPTextEncodeSDXL", "CLIPTextEncodeSDXLRefiner",
    ]
    SAVE_IMAGE_TYPE = ["SaveImage", "Image Save", "SDPromptSaver"] # SDPromptSaver might be a custom node

    # This mapping was for a direct zip with PARAMETER_KEY.
    # It's better to map individually from `longest_flow` to `self._parameter`.
    # SETTING_KEY = ["ckpt_name", "sampler_name", "", "cfg", "steps", ""] # Old style

    def __init__(
        self, info: dict = None, raw: str = "", width: int = 0, height: int = 0 # Original SDPR passes w/h
    ):
        super().__init__(info=info, raw=raw, width=width, height=height)
        self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool}")
        self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER
        # These are specific to ComfyUI's graph parsing
        self._prompt_json = {} # Will store the parsed "prompt" JSON from info
        self._workflow_json = {} # Will store the parsed "workflow" JSON from info
        # self._positive, self._negative, etc., are initialized by BaseFormat

    # `parse()` method is inherited from BaseFormat, which calls `_process()`

    def _process(self): # Called by BaseFormat.parse()
        """
        Main parsing logic for ComfyUI PNG metadata.
        Extracts workflow and prompt, traverses the graph, and populates attributes.
        """
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")

        prompt_str = self._info.get("prompt")
        workflow_str = self._info.get("workflow")

        if not prompt_str: # "prompt" (workflow JSON) is essential for ComfyUI
            self._logger.warn(f"{self.tool}: 'prompt' field (workflow JSON) not found in info dict.")
            self.status = self.Status.FORMAT_ERROR
            self._error = "ComfyUI 'prompt' (workflow JSON) field missing."
            return

        try:
            self._prompt_json = json.loads(str(prompt_str)) # Ensure it's a string before loading
            if workflow_str: # Workflow is optional but good to have
                self._workflow_json = json.loads(str(workflow_str))
            self._logger.info(f"{self.tool}: Successfully loaded prompt/workflow JSON.")
        except json.JSONDecodeError as e:
            self._logger.error(f"{self.tool}: Failed to decode prompt/workflow JSON: {e}")
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Invalid JSON in ComfyUI prompt/workflow: {e}"
            return
        except Exception as e_load: # Catch other potential errors during load
            self._logger.error(f"{self.tool}: Unexpected error loading prompt/workflow JSON: {e_load}")
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Error loading ComfyUI JSON: {e_load}"
            return

        # Perform the graph traversal and data extraction
        self._comfy_png_traverse_and_extract()

        # After traversal, check if essential data was populated
        # Heuristic: if positive prompt or some parameters were found.
        if self._positive or any(v != self.PARAMETER_PLACEHOLDER for k, v in self._parameter.items() if k != "size"):
            self._logger.info(f"{self.tool}: Data parsed successfully from workflow.")
            self.status = self.Status.READ_SUCCESS
        else:
            self._logger.warn(f"{self.tool}: Traversal completed but no key prompt/parameter data extracted.")
            self.status = self.Status.FORMAT_ERROR
            if not self._error: # If _comfy_png_traverse_and_extract didn't set a specific error
                self._error = f"{self.tool}: Failed to extract meaningful data from workflow graph."
        
        # Consolidate raw data for display (optional, self._raw from BaseFormat might be enough if set from info)
        # self._raw = "\n".join(filter(None, [str(self._prompt_json), str(self._workflow_json)]))


    def _comfy_png_traverse_and_extract(self):
        """
        Traverses the ComfyUI node graph (from self._prompt_json) to extract metadata.
        Populates self._positive, self._negative, self._parameter, etc.
        """
        prompt_json = self._prompt_json # Use the parsed JSON

        # Find end nodes (SaveImage or KSampler as a fallback)
        end_node_candidates = {} # Store as {node_id: class_type}
        for node_id, node_data in prompt_json.items():
            class_type = node_data.get("class_type")
            if class_type in self.SAVE_IMAGE_TYPE:
                end_node_candidates[node_id] = class_type
            elif class_type in self.KSAMPLER_TYPES and not end_node_candidates: # KSampler only if no SaveImage
                end_node_candidates[node_id] = class_type
        
        if not end_node_candidates:
            self._logger.warn(f"{self.tool}: No SaveImage or KSampler end nodes found in workflow.")
            self._error = "No suitable end node (SaveImage/KSampler) found."
            # Status will be set to FORMAT_ERROR by _process if this path is taken without success
            return

        # Traverse from each end node and find the "longest" or most complete flow
        longest_flow_data = {}
        # longest_nodes_path = [] # If you need to store the path of nodes
        max_extracted_params = -1

        for end_node_id, _ in end_node_candidates.items():
            current_flow_data = {}
            # Resetting these for each traversal path attempt might be needed if not careful
            # For now, assume _comfy_traverse updates instance attributes correctly or returns all data
            temp_positive = ""
            temp_negative = ""
            temp_positive_sdxl = {}
            temp_negative_sdxl = {}
            temp_is_sdxl = False

            # The _comfy_traverse needs to be adapted to return all collected data
            # or to populate temporary variables that we then check.
            # The original _comfy_traverse directly modified self._positive, self._negative etc.
            # which is problematic if multiple end-nodes are traversed.
            
            # Let's refine _comfy_traverse to return a dictionary of found items.
            extracted_data_from_flow = self._comfy_traverse(prompt_json, end_node_id)
            
            # Check how many relevant parameters were found in this flow
            num_params_in_flow = 0
            if extracted_data_from_flow.get("positive") or extracted_data_from_flow.get("positive_sdxl"): num_params_in_flow +=1
            if extracted_data_from_flow.get("negative") or extracted_data_from_flow.get("negative_sdxl"): num_params_in_flow +=1
            for key in ["steps", "cfg", "sampler_name", "seed", "ckpt_name"]: # Key parameters
                if extracted_data_from_flow.get(key):
                    num_params_in_flow +=1
            
            if num_params_in_flow > max_extracted_params:
                max_extracted_params = num_params_in_flow
                longest_flow_data = extracted_data_from_flow

        if not longest_flow_data:
            self._logger.warn(f"{self.tool}: Graph traversal yielded no data from any end node.")
            self._error = "Workflow graph traversal failed to extract data."
            return

        # Populate attributes from the "best" flow found (longest_flow_data)
        self._positive = str(longest_flow_data.get("positive", ""))
        self._negative = str(longest_flow_data.get("negative", ""))
        self._positive_sdxl = longest_flow_data.get("positive_sdxl", {})
        self._negative_sdxl = longest_flow_data.get("negative_sdxl", {})
        self._is_sdxl = longest_flow_data.get("is_sdxl", False)

        # If SDXL and main prompts are empty, merge from SDXL clips
        if self._is_sdxl:
            if not self._positive and self._positive_sdxl: self._positive = self.merge_clip(self._positive_sdxl)
            if not self._negative and self._negative_sdxl: self._negative = self.merge_clip(self._negative_sdxl)

        # Populate self._parameter, mapping from longest_flow_data keys to canonical keys
        # BaseFormat already initialized self._parameter with placeholders.
        mapping = {
            "ckpt_name": "model",
            "sampler_name": "sampler_name", # Or "sampler" if that's your canonical
            "seed": "seed",                 # Also handles "noise_seed" in _comfy_traverse
            "cfg": "cfg_scale",             # Or "cfg"
            "steps": "steps",
            "scheduler": "scheduler",
            # width/height are handled by self._width, self._height if passed to __init__
            # or if found in KSampler node by _comfy_traverse
        }
        for flow_key, canonical_key in mapping.items():
            if flow_key in longest_flow_data and canonical_key in self._parameter:
                value = longest_flow_data[flow_key]
                self._parameter[canonical_key] = str(remove_quotes(str(value))) # remove_quotes for strings

        # Update width/height if KSampler provided them
        if longest_flow_data.get("k_width") and longest_flow_data.get("k_height"):
            self._width = str(longest_flow_data["k_width"])
            self._height = str(longest_flow_data["k_height"])
        
        if "size" in self._parameter and self._width != "0" and self._height != "0":
             self._parameter["size"] = f"{self._width}x{self._height}"


        # Reconstruct self._setting string from longest_flow_data or self._parameter
        setting_parts = []
        # Required params first
        if longest_flow_data.get("steps"): setting_parts.append(f"Steps: {longest_flow_data['steps']}")
        if longest_flow_data.get("sampler_name"): setting_parts.append(f"Sampler: {remove_quotes(str(longest_flow_data['sampler_name']))}")
        if longest_flow_data.get("cfg"): setting_parts.append(f"CFG scale: {longest_flow_data['cfg']}")
        if longest_flow_data.get("seed", longest_flow_data.get("noise_seed")):
            setting_parts.append(f"Seed: {longest_flow_data.get('seed', longest_flow_data.get('noise_seed'))}")
        
        setting_parts.append(f"Size: {self._width}x{self._height}") # Use current width/height
        if longest_flow_data.get("ckpt_name"): setting_parts.append(f"Model: {remove_quotes(str(longest_flow_data['ckpt_name']))}")
        if longest_flow_data.get("scheduler"): setting_parts.append(f"Scheduler: {remove_quotes(str(longest_flow_data['scheduler']))}")

        # Optional KSampler params (from original _comfy_png)
        optional_ksampler_params = [
            "add_noise", "start_at_step", "end_at_step", 
            "return_with_left_over_noise", "denoise"
        ]
        for p_name in optional_ksampler_params:
            if longest_flow_data.get(p_name) is not None: # Check for None explicitly for booleans
                 # Format key for display
                display_key = p_name.replace("_", " ").capitalize()
                setting_parts.append(f"{display_key}: {remove_quotes(str(longest_flow_data[p_name]))}")
        
        # Upscaling info
        if longest_flow_data.get("upscale_method"): setting_parts.append(f"Upscale method: {remove_quotes(str(longest_flow_data['upscale_method']))}")
        if longest_flow_data.get("upscaler"): setting_parts.append(f"Upscaler: {remove_quotes(str(longest_flow_data['upscaler']))}")
        
        self._setting = ", ".join(filter(None, setting_parts))


    @staticmethod
    def merge_clip(data: dict) -> str: # data is like {"Clip G": "prompt_g", "Clip L": "prompt_l"}
        clip_g = str(data.get("Clip G", "")).strip(" ,")
        clip_l = str(data.get("Clip L", "")).strip(" ,")

        if not clip_g and not clip_l: return ""
        if clip_g == clip_l: return clip_g
        if not clip_g: return clip_l
        if not clip_l: return clip_g
        # Prefer to return them distinctly if possible for UI to handle,
        # but original merged. For simplicity of a single string:
        return f"Clip G: {clip_g}, Clip L: {clip_l}" # Or use "\n"

    def _comfy_traverse(self, prompt_json: dict, current_node_id: str) -> dict:
        """
        Recursive helper to traverse the ComfyUI graph from a given node_id.
        Returns a dictionary of extracted parameters relevant to generation.
        This needs to be carefully designed to avoid infinite loops for cyclic graphs
        and to correctly aggregate data. This is a simplified conceptual rewrite.
        """
        # visited_nodes = set() # To handle cycles if not passed down

        # def traverse(node_id_str):
        #     if node_id_str in visited_nodes: return {}
        #     visited_nodes.add(node_id_str)

        #     node_info = prompt_json.get(node_id_str)
        #     if not node_info: return {}

        #     class_type = node_info.get("class_type")
        #     inputs = node_info.get("inputs", {})
        #     extracted_data = {}

        #     if class_type in self.KSAMPLER_TYPES:
        #         extracted_data.update({k: inputs.get(k) for k in ["seed", "noise_seed", "steps", "cfg", "sampler_name", "scheduler", "denoise", "add_noise", "start_at_step", "end_at_step", "return_with_left_over_noise"] if inputs.get(k) is not None})
        #         # Try to get width/height if this KSampler has latent_image from an EmptyLatentImage
        #         if "latent_image" in inputs and isinstance(inputs["latent_image"], list):
        #             prev_node_id = str(inputs["latent_image"][0])
        #             prev_node_info = prompt_json.get(prev_node_id)
        #             if prev_node_info and prev_node_info.get("class_type") == "EmptyLatentImage":
        #                 extracted_data["k_width"] = prev_node_info.get("inputs", {}).get("width")
        #                 extracted_data["k_height"] = prev_node_info.get("inputs", {}).get("height")

        #         # Recurse for model, positive, negative, latent
        #         if "model" in inputs: extracted_data = merge_dict(extracted_data, traverse(str(inputs["model"][0])))
        #         if "positive" in inputs:
        #             pos_data = traverse(str(inputs["positive"][0]))
        #             if isinstance(pos_data, str): extracted_data["positive"] = pos_data
        #             else: extracted_data["positive_sdxl"] = merge_dict(extracted_data.get("positive_sdxl",{}), pos_data)
        #         # ... similar for negative, latent_image ...

        #     elif class_type in self.CLIP_TEXT_ENCODE_TYPE:
        #         # ... logic to extract text, potentially checking for SDXL structure ...
        #         # This part of original SDPR is complex due to various custom nodes.
        #         # Simplified:
        #         if "text" in inputs: return str(inputs["text"]) # For simple CLIPTextEncode
        #         if "text_g" in inputs and "text_l" in inputs: # For SDXL
        #             extracted_data["is_sdxl"] = True
        #             return {"Clip G": str(inputs["text_g"]), "Clip L": str(inputs["text_l"])}


        #     elif class_type in self.CHECKPOINT_LOADER_TYPE:
        #         extracted_data["ckpt_name"] = inputs.get("ckpt_name")

        #     # ... handle other node types like LoraLoader, VAEEncode, ControlNet, Upscalers ...
            
        #     # Default/bridging nodes: try to follow common input names
        #     elif not extracted_data: # If this node type didn't directly yield data
        #         for common_input in ["samples", "image", "model", "clip", "conditioning"]:
        #             if common_input in inputs and isinstance(inputs[common_input], list):
        #                 # Recurse on the first linked input
        #                 extracted_data = merge_dict(extracted_data, traverse(str(inputs[common_input][0])))
        #                 if extracted_data and (extracted_data.get("positive") or extracted_data.get("ckpt_name")): # Found something meaningful
        #                     break 
        #     return extracted_data

        # return traverse(current_node_id)
        
        # --- Using the original _comfy_traverse logic directly for now ---
        # This is complex and prone to issues if not perfectly adapted.
        # The original modifies instance variables directly during recursion.
        # For a cleaner approach, _comfy_traverse should return a dict of found values.
        #
        # For this iteration, I will keep your original _comfy_traverse structure
        # and assume it populates self._positive, self._negative, self._positive_sdxl, etc.
        # The main _comfy_png_traverse_and_extract will then copy these into longest_flow_data.
        # This is NOT IDEAL but reflects your provided code.

        # Reset instance accumulators before a new traversal from an end_node
        self._positive = ""
        self._negative = ""
        self._positive_sdxl = {}
        self._negative_sdxl = {}
        self._is_sdxl = False
        # self._parameter is already reset with placeholders in BaseFormat or this class's init

        # Call the original recursive traversal. It populates instance attributes.
        flow_details, _ = self._original_comfy_traverse_logic(prompt_json, current_node_id)

        # After it runs, copy the populated instance attributes into a dictionary to return
        # This adapts the side-effect based original to a functional return.
        return_data = flow_details.copy() # flow_details should contain KSampler params etc.
        return_data["positive"] = self._positive
        return_data["negative"] = self._negative
        return_data["positive_sdxl"] = self._positive_sdxl.copy()
        return_data["negative_sdxl"] = self._negative_sdxl.copy()
        return_data["is_sdxl"] = self._is_sdxl
        # Parameters like ckpt_name, sampler_name etc. should be in flow_details from KSampler part.

        return return_data


    def _original_comfy_traverse_logic(self, prompt, end_node): # Renamed your _comfy_traverse
        # THIS IS YOUR ORIGINAL _comfy_traverse method's logic
        # It directly modifies self._positive, self._negative, etc.
        flow = {}
        node = [end_node]
        inputs = {}
        try:
            inputs = prompt[end_node]["inputs"]
        except KeyError: # Node ID might not exist if graph is malformed or ID is wrong
            self._logger.warn(f"Node ID {end_node} not found in prompt JSON during traversal.")
            return {}, [] # Return empty if node doesn't exist
        except Exception as e_input: # Other errors accessing inputs
            self._logger.error(f"Error accessing inputs for node {end_node}: {e_input}")
            return {}, []


        class_type = prompt[end_node].get("class_type", "UnknownType")
        # self._logger.debug(f"Traversing node: {end_node} (Type: {class_type})")

        match class_type:
            case node_type if node_type in self.SAVE_IMAGE_TYPE:
                try:
                    # Follow the 'images' input link
                    if "images" in inputs and isinstance(inputs["images"], list):
                        last_flow, last_node = self._original_comfy_traverse_logic(
                            prompt, str(inputs["images"][0]) # Ensure node_id is string
                        )
                        flow = merge_dict(flow, last_flow)
                        node += last_node
                    else:
                        self._logger.debug(f"SaveImage node {end_node} has no 'images' input or not a list.")
                except Exception as e: self._logger.error(f"Error traversing from SaveImage node {end_node}: {e}")
            
            case node_type if node_type in self.KSAMPLER_TYPES:
                try:
                    # Directly copy relevant KSampler inputs to flow
                    # These are parameters specific to the KSampler operation
                    flow.update({k: inputs.get(k) for k in 
                                 ["seed", "noise_seed", "steps", "cfg", "sampler_name", 
                                  "scheduler", "denoise", "add_noise", "start_at_step", 
                                  "end_at_step", "return_with_left_over_noise"] 
                                 if inputs.get(k) is not None})
                    
                    # Try to get width/height if this KSampler has latent_image from an EmptyLatentImage
                    if "latent_image" in inputs and isinstance(inputs["latent_image"], list):
                        prev_node_id_latent = str(inputs["latent_image"][0])
                        prev_node_info_latent = prompt.get(prev_node_id_latent)
                        if prev_node_info_latent and prev_node_info_latent.get("class_type") == "EmptyLatentImage":
                            latent_inputs = prev_node_info_latent.get("inputs", {})
                            if latent_inputs.get("width") is not None: flow["k_width"] = latent_inputs.get("width")
                            if latent_inputs.get("height") is not None: flow["k_height"] = latent_inputs.get("height")


                    # Recursively traverse inputs like model, positive, negative, latent_image
                    # Each recursive call returns a (flow_dict, path_list) tuple.
                    # We are primarily interested in the flow_dict for merging.
                    path_nodes_for_ksampler = []
                    for input_key, input_value in inputs.items():
                        if input_key in ["model", "positive", "negative", "latent_image"]: # Common linked inputs
                            if isinstance(input_value, list) and input_value: # Ensure it's a list with a link
                                prev_node_id = str(input_value[0])
                                traversed_input_data = self._original_comfy_traverse_logic(prompt, prev_node_id)
                                
                                # traversed_input_data is a tuple (dict_flow, list_nodes)
                                # or a string (for text from CLIPTextEncode)
                                # or a dict (for SDXL prompts or Checkpoint name)
                                
                                if isinstance(traversed_input_data, tuple): # (dict, list)
                                    prev_flow, prev_nodes = traversed_input_data
                                    flow = merge_dict(flow, prev_flow)
                                    path_nodes_for_ksampler.extend(prev_nodes)
                                elif input_key == "positive":
                                    if isinstance(traversed_input_data, str): self._positive = traversed_input_data
                                    elif isinstance(traversed_input_data, dict): self._positive_sdxl.update(traversed_input_data)
                                elif input_key == "negative":
                                    if isinstance(traversed_input_data, str): self._negative = traversed_input_data
                                    elif isinstance(traversed_input_data, dict): self._negative_sdxl.update(traversed_input_data)
                                elif isinstance(traversed_input_data, dict) : # e.g. from CheckpointLoader
                                     flow = merge_dict(flow, traversed_input_data)
                        
                        elif input_key in ("seed", "noise_seed"): # Handle "CR Seed" custom node if value is a list
                            if isinstance(input_value, list) and input_value:
                                seed_node_id = str(input_value[0])
                                seed_data = self._original_comfy_traverse_logic(prompt, seed_node_id) # Should return the seed value or a dict containing it
                                if isinstance(seed_data, (int, float, str)): flow[input_key] = seed_data
                                elif isinstance(seed_data, dict) and "seed" in seed_data: flow[input_key] = seed_data["seed"] # CR Seed returns dict
                        
                        # For other list inputs that might be links (e.g. "optional_lora_stack")
                        elif isinstance(input_value, list) and input_value and isinstance(input_value[0], str) and input_value[0] in prompt:
                            # This is a generic attempt to follow other links if they lead to data
                            # self._logger.debug(f"KSampler: Following generic link for input '{input_key}'")
                            prev_node_id = str(input_value[0])
                            traversed_input_data = self._original_comfy_traverse_logic(prompt, prev_node_id)
                            if isinstance(traversed_input_data, tuple) and isinstance(traversed_input_data[0], dict):
                                flow = merge_dict(flow, traversed_input_data[0])
                                path_nodes_for_ksampler.extend(traversed_input_data[1])
                            elif isinstance(traversed_input_data, dict):
                                flow = merge_dict(flow, traversed_input_data)


                    node.extend(path_nodes_for_ksampler)
                except Exception as e: self._logger.error(f"Error traversing KSampler node {end_node}: {e}")

            case node_type if node_type in self.CLIP_TEXT_ENCODE_TYPE:
                try:
                    if node_type == "CLIPTextEncode":
                        if isinstance(inputs.get("text"), list): # Link to another node (e.g., PromptStyler)
                            text_node_id = str(inputs["text"][0])
                            # This traverse should return (positive_str, negative_str) or a dict for SDXL
                            traversed_text = self._original_comfy_traverse_logic(prompt, text_node_id)
                            return traversed_text # Propagate up
                        elif isinstance(inputs.get("text"), str):
                            return inputs["text"] # Actual text string
                    
                    elif node_type == "CLIPTextEncodeSDXL":
                        self._is_sdxl = True
                        text_g, text_l = inputs.get("text_g"), inputs.get("text_l")
                        if isinstance(text_g, list): # Linked, e.g. to SDXLPromptStyler
                            prompt_styler_g = self._original_comfy_traverse_logic(prompt, str(text_g[0]))
                            prompt_styler_l = self._original_comfy_traverse_logic(prompt, str(text_l[0])) # Assume text_l is also linked
                            # prompt_styler should return (pos, neg) tuple
                            return {"Clip G Pos": prompt_styler_g[0], "Clip G Neg": prompt_styler_g[1],
                                    "Clip L Pos": prompt_styler_l[0], "Clip L Neg": prompt_styler_l[1]}
                        else: # Direct text inputs
                            return {"Clip G": str(text_g), "Clip L": str(text_l)}

                    elif node_type == "CLIPTextEncodeSDXLRefiner":
                        self._is_sdxl = True
                        text = inputs.get("text")
                        if isinstance(text, list): # Linked
                            prompt_styler = self._original_comfy_traverse_logic(prompt, str(text[0]))
                            return {"Refiner Pos": prompt_styler[0], "Refiner Neg": prompt_styler[1]}
                        else: # Direct text
                            return {"Refiner": str(text)}
                except Exception as e: self._logger.error(f"Error in CLIPTextEncode node {end_node} (type {node_type}): {e}")

            case "LoraLoader":
                try: # LoraLoader passes through model and clip from previous node
                    if "model" in inputs and isinstance(inputs["model"], list):
                        last_flow_model, last_node_model = self._original_comfy_traverse_logic(prompt, str(inputs["model"][0]))
                        flow = merge_dict(flow, last_flow_model)
                        node.extend(last_node_model)
                    if "clip" in inputs and isinstance(inputs["clip"], list):
                        last_flow_clip, last_node_clip = self._original_comfy_traverse_logic(prompt, str(inputs["clip"][0]))
                        flow = merge_dict(flow, last_flow_clip) # Clip data might be prompts for SDXL
                        node.extend(last_node_clip)
                    # Add LoRA name if available directly
                    if inputs.get("lora_name"): flow["lora_name"] = inputs.get("lora_name") # Or append to a list of loras
                except Exception as e: self._logger.error(f"Error in LoraLoader node {end_node}: {e}")

            case node_type if node_type in self.CHECKPOINT_LOADER_TYPE:
                try: # Returns dict with ckpt_name, potentially others
                    return {"ckpt_name": inputs.get("ckpt_name")}
                except Exception as e: self._logger.error(f"Error in CheckpointLoader node {end_node}: {e}")
            
            case node_type if node_type in self.VAE_ENCODE_TYPE:
                try: # Follow 'pixels' input (usually to a LoadImage node)
                    if "pixels" in inputs and isinstance(inputs["pixels"], list):
                        last_flow, last_node = self._original_comfy_traverse_logic(prompt, str(inputs["pixels"][0]))
                        flow = merge_dict(flow, last_flow)
                        node.extend(last_node)
                except Exception as e: self._logger.error(f"Error in VAEEncode node {end_node}: {e}")

            # Custom Node Examples (from original SDPR) - adapt as needed
            case "SDXLPromptStyler": # This node outputs (text_positive, text_negative)
                try: return inputs.get("text_positive"), inputs.get("text_negative")
                except Exception as e: self._logger.error(f"Error in SDXLPromptStyler node {end_node}: {e}")
            
            case "CR Seed": # This node outputs a seed value
                try: return {"seed": inputs.get("seed")} # Return as dict to merge
                except Exception as e: self._logger.error(f"Error in CR Seed node {end_node}: {e}")

            # Fallback for other/bridging nodes: try to follow common link names
            case _: # Default case for unknown or passthrough nodes
                try:
                    # Prioritize inputs that are likely to lead to data
                    follow_order = ["samples", "image", "model", "clip", "conditioning", "latent"]
                    followed_something = False
                    for input_name in follow_order:
                        if input_name in inputs and isinstance(inputs[input_name], list) and inputs[input_name]:
                            # self._logger.debug(f"Default traversal for node {end_node} (type {class_type}), following '{input_name}'")
                            prev_node_id = str(inputs[input_name][0])
                            traversed_data = self._original_comfy_traverse_logic(prompt, prev_node_id)
                            if isinstance(traversed_data, tuple): # (dict_flow, list_nodes)
                                flow = merge_dict(flow, traversed_data[0])
                                node.extend(traversed_data[1])
                            elif isinstance(traversed_input_data, str) and input_name == "conditioning": # Text from conditioning
                                 # This is tricky, conditioning can be positive or negative.
                                 # For simplicity, assume positive if not otherwise specified.
                                 self._positive = merge_dict(self._positive, traversed_input_data) if self._positive else traversed_input_data
                            elif isinstance(traversed_data, dict): # Merge dict results (e.g. from checkpoint)
                                flow = merge_dict(flow, traversed_data)
                            
                            # If this path yielded significant data (e.g. a model name or prompt),
                            # we might consider it the primary path and stop.
                            if flow.get("ckpt_name") or flow.get("positive") or flow.get("sampler_name"):
                                followed_something = True
                                break 
                    # if not followed_something:
                        # self._logger.debug(f"Node {end_node} (type {class_type}) is a leaf or unhandled passthrough in this traversal.")
                except Exception as e: self._logger.error(f"Error in default/bridging node {end_node} (type {class_type}): {e}")
        
        return flow, node