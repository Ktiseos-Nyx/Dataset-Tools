# dataset_tools/vendored_sdpr/format/comfyui.py

__author__ = "receyuki"
__filename__ = "comfyui.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki; Modified 2025, Ktiseos Nyx"
__email__ = "receyuki@gmail.com; your_email@example.com"  # Add your email if desired

import json
import logging  # For type hinting
from typing import Any  # Use Dict

from .base_format import BaseFormat  # Assuming BaseFormat is in the same package level
from .utility import merge_dict  # Assuming utility.py is in the same package level

# Mapping of common keys found in ComfyUI KSampler nodes to standard parameter names
COMFY_FLOW_TO_PARAM_MAP: dict[str, str | list[str]] = {
    "ckpt_name": "model",  # From CheckpointLoader nodes
    "sampler_name": "sampler_name",  # From KSampler nodes
    "seed": ["seed", "noise_seed"],  # KSampler "seed", KSamplerAdvanced "noise_seed"
    "cfg": "cfg_scale",  # From KSampler nodes
    "steps": "steps",  # From KSampler nodes
    "scheduler": "scheduler",  # From KSampler nodes
    # Add other mappings if there are more standard parameters extractable this way
}

# List of ComfyUI specific settings keys that might be collected for the settings string
COMFY_SPECIFIC_SETTINGS_KEYS: list[str] = [
    "add_noise",  # KSamplerAdvanced
    "start_at_step",  # KSamplerAdvanced
    "end_at_step",  # KSamplerAdvanced
    "return_with_left_over_noise",  # KSamplerAdvanced
    "denoise",  # KSampler (often for img2img or upscale)
    "upscale_method",  # E.g., from ImageScale node
    "upscaler",  # E.g., from UpscaleModelLoader node if model name is used
    "lora_name",  # From LoraLoader node
    # Add other specific settings you want to capture by key name
]


class ComfyUI(BaseFormat):
    tool = "ComfyUI"

    # Common class types for node traversal
    KSAMPLER_TYPES = [
        "KSampler",
        "KSamplerAdvanced",
        "KSampler (Efficient)",
        "Efficient KSampler",
    ]  # Added common variants
    VAE_ENCODE_TYPE = ["VAEEncode", "VAEEncodeForInpaint"]
    CHECKPOINT_LOADER_TYPE = [
        "CheckpointLoader",
        "CheckpointLoaderSimple",
        "unCLIPCheckpointLoader",
        "Checkpoint Loader (Simple)",  # Common display name
        "UltimateSDUpscaleLoader",  # If this loader provides ckpt_name
    ]
    CLIP_TEXT_ENCODE_TYPE = [
        "CLIPTextEncode",
        "CLIPTextEncodeSDXL",
        "CLIPTextEncodeSDXLRefiner",
        "smZ CLIPTextEncode",  # From an example you provided
    ]
    SAVE_IMAGE_TYPE = [
        "SaveImage",
        "Image Save",
        "SDPromptSaver",
    ]  # Add any other save nodes

    def __init__(
        self,
        info: dict[str, Any] | None = None,  # Use Dict
        raw: str = "",
        width: Any = 0,  # Use Any for flexibility from ImageDataReader
        height: Any = 0,  # Use Any for flexibility
        logger_obj: logging.Logger | None = None,  # <<< ADDED
        **kwargs: Any,  # <<< ADDED
    ):
        # Pass all relevant arguments to BaseFormat's __init__
        super().__init__(
            info=info,
            raw=raw,
            width=width,
            height=height,
            logger_obj=logger_obj,
            **kwargs,  # Pass remaining kwargs
        )
        self._prompt_json: dict[str, Any] = {}  # Parsed "prompt" chunk (workflow)
        self._workflow_json: dict[str, Any] | None = None  # Parsed "workflow" chunk (API format)

    def _process(self) -> None:
        self._logger.debug("Attempting to parse using %s logic.", self.tool)

        # ComfyUI metadata is primarily in the 'prompt' (workflow JSON)
        # or 'workflow' (API format JSON) fields of self._info.
        # ImageDataReader passes all PNG chunks in self._info.
        prompt_str = str(self._info.get("prompt", ""))  # Main source: workflow JSON
        workflow_api_str = str(self._info.get("workflow", ""))  # Secondary source: API format

        source_json_str_to_parse = None
        source_description = ""

        if prompt_str:
            source_json_str_to_parse = prompt_str
            source_description = "PNG 'prompt' chunk"
        elif workflow_api_str:  # Fallback to API 'workflow' chunk if 'prompt' is empty
            source_json_str_to_parse = workflow_api_str
            source_description = "PNG 'workflow' (API) chunk"
        else:
            self._logger.warning(
                "%s: Neither 'prompt' nor 'workflow' (API) JSON fields found in info.",
                self.tool,
            )
            self.status = self.Status.FORMAT_ERROR  # Or MISSING_INFO
            self._error = "ComfyUI metadata (prompt/workflow JSON) missing from PNG info."
            return

        try:
            loaded_json = json.loads(source_json_str_to_parse)
            if not isinstance(loaded_json, dict):
                self._logger.error(
                    "%s: Content from %s is not a valid JSON dictionary.",
                    self.tool,
                    source_description,
                )
                self.status = self.Status.FORMAT_ERROR
                self._error = f"ComfyUI metadata from {source_description} is not a dict."
                return

            # Store the parsed JSON based on its likely source type
            # If 'nodes' and 'links' are top-level, it's likely API format, store in _workflow_json
            # Otherwise, assume it's the standard workflow (node graph), store in _prompt_json
            if "nodes" in loaded_json and "links" in loaded_json:  # Heuristic for API format
                self._workflow_json = loaded_json
                self._prompt_json = loaded_json  # For traversal, treat API format like prompt if prompt chunk missing
                self._logger.info("%s: Loaded API format JSON from %s.", self.tool, source_description)
            else:  # Assume it's the standard 'prompt' chunk content (node graph)
                self._prompt_json = loaded_json
                self._logger.info("%s: Loaded workflow JSON from %s.", self.tool, source_description)

        except json.JSONDecodeError as json_err:
            self._logger.error(
                "%s: Failed to decode JSON from %s: %s",
                self.tool,
                source_description,
                json_err,
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Invalid JSON in ComfyUI {source_description}: {json_err}"
            return

        # Now that JSON is loaded (either _prompt_json or _workflow_json is populated), proceed with traversal
        self._comfy_png_traverse_and_extract()

        # Set self._raw to the JSON string that was successfully parsed, for display/consistency
        if not self._raw and source_json_str_to_parse:  # If _raw wasn't set by ImageDataReader
            self._raw = source_json_str_to_parse

        # Final status check based on extracted data
        if self.status != self.Status.FORMAT_ERROR and self.status != self.Status.COMFYUI_ERROR:
            if (
                self._positive
                or self._negative
                or self._positive_sdxl
                or self._negative_sdxl
                or self._parameter_has_data()
                or self._width != "0"
                or self._height != "0"
            ):
                self._logger.info("%s: Data successfully extracted from workflow.", self.tool)
                # BaseFormat.parse() will set READ_SUCCESS if no errors were raised by _process
            else:
                self._logger.warning(
                    "%s: Workflow traversal completed but no key data extracted.",
                    self.tool,
                )
                self.status = self.Status.COMFYUI_ERROR  # More specific than general FORMAT_ERROR
                if not self._error:  # Only set if a more specific error isn't already there
                    self._error = f"{self.tool}: Failed to extract meaningful data from workflow graph."

    def _find_end_node_candidates(self, workflow_json_data: dict[str, Any]) -> dict[str, str]:
        candidates: dict[str, str] = {}
        # Check if any SaveImage type nodes are present first
        is_save_image_present = any(
            isinstance(node_data, dict) and node_data.get("class_type") in self.SAVE_IMAGE_TYPE
            for node_data in workflow_json_data.values()
        )

        for node_id, node_data in workflow_json_data.items():
            if not isinstance(node_data, dict):  # Skip non-node entries if any
                continue
            class_type = node_data.get("class_type")
            if is_save_image_present:
                # If SaveImage nodes exist, only consider them as primary end points
                if class_type in self.SAVE_IMAGE_TYPE:
                    candidates[node_id] = class_type
            elif class_type in self.KSAMPLER_TYPES:
                # If no SaveImage nodes, KSamplers are good candidates
                candidates[node_id] = class_type

        # If still no candidates (e.g., workflow ends in VAE Decode directly to PreviewImage, and no KSampler)
        # This part is tricky. For now, we rely on SaveImage or KSampler.
        # If after all this `candidates` is empty, it means we couldn't find a typical end node.
        if not candidates:
            self._logger.debug("No SaveImage or KSampler nodes found as primary end candidates.")
            # As a last resort, consider *any* node that doesn't have outgoing links
            # to other processing nodes (harder to determine without full graph analysis here).
            # For simplicity now, we'll stick to SaveImage/KSampler.
            # If a PreviewImage is the only output, we might miss it.
            # However, most useful workflows for parameter extraction end in Save or KSampler.
            pass

        return candidates

    def _count_meaningful_params(self, flow_details: dict[str, Any]) -> int:
        count = 0
        # Check prompts
        if flow_details.get("positive_prompt") or (
            isinstance(flow_details.get("positive_sdxl_prompts"), dict) and flow_details.get("positive_sdxl_prompts")
        ):
            count += 1
        if flow_details.get("negative_prompt") or (
            isinstance(flow_details.get("negative_sdxl_prompts"), dict) and flow_details.get("negative_sdxl_prompts")
        ):
            count += 1

        # Check standard parameters
        flow_params = flow_details.get("parameters", {})
        if isinstance(flow_params, dict):  # Ensure it's a dict
            # Access PARAMETER_KEY from the class, not an instance attribute that might not be set
            for key in self.__class__.PARAMETER_KEY:
                if flow_params.get(key) and flow_params[key] != self.DEFAULT_PARAMETER_PLACEHOLDER:
                    count += 1

        # Check dimensions
        if str(flow_details.get("width", "0")).strip() not in [
            "0",
            self.DEFAULT_PARAMETER_PLACEHOLDER,
            "",
        ]:
            count += 1
        if str(flow_details.get("height", "0")).strip() not in [
            "0",
            self.DEFAULT_PARAMETER_PLACEHOLDER,
            "",
        ]:
            count += 1

        # Consider custom settings if they add to "meaningfulness"
        # For now, just prompts, standard params, and dimensions.
        # count += len(flow_details.get("custom_settings", {}))

        return count

    def _get_best_flow_data(
        self, workflow_json_data: dict[str, Any], end_node_candidates: dict[str, str]
    ) -> dict[str, Any]:
        # ... (implementation as before, ensure it uses Dict) ...
        best_flow_data: dict[str, Any] = {}
        max_extracted_params = -1
        self._logger.debug("Candidate end nodes for traversal: %s", end_node_candidates)

        if not end_node_candidates and not any(
            node_data.get("class_type") in self.KSAMPLER_TYPES
            for node_data in workflow_json_data.values()
            if isinstance(node_data, dict)
        ):
            self._logger.warning(
                "%s: No SaveImage or KSampler nodes found in the workflow. Cannot determine end points for data extraction.",
                self.tool,
            )
            self.status = self.Status.COMFYUI_ERROR
            self._error = "No SaveImage or KSampler nodes found in ComfyUI workflow."
            return {}  # Return empty if no candidates to traverse from

        for end_node_id, class_type in end_node_candidates.items():
            self._logger.debug("Traversing from end node: %s (Type: %s)", end_node_id, class_type)
            temp_flow_details = self._run_traversal_for_node(workflow_json_data, end_node_id)
            num_params_in_flow = self._count_meaningful_params(temp_flow_details)
            self._logger.debug("Flow from node %s yielded %s params.", end_node_id, num_params_in_flow)
            if num_params_in_flow > max_extracted_params:
                max_extracted_params = num_params_in_flow
                best_flow_data = temp_flow_details

        if best_flow_data:
            self._logger.info("Best flow selected with %s params.", max_extracted_params)
        elif end_node_candidates:  # Candidates existed but no data extracted
            self._logger.warning("No meaningful data extracted from any traversal path, though end nodes were found.")
            # Don't set error here if one was already set due to no candidates
            if self.status != self.Status.COMFYUI_ERROR:
                self.status = self.Status.COMFYUI_ERROR
                self._error = "Workflow traversal from candidate end nodes yielded no data."
        # If no end_node_candidates, status/error already set.
        return best_flow_data

    def _apply_flow_data_to_self(self, flow_data: dict[str, Any]) -> None:
        # ... (implementation as before, ensure types and defaults are robust) ...
        self._positive = str(flow_data.get("positive_prompt", "")).strip()
        self._negative = str(flow_data.get("negative_prompt", "")).strip()

        # Ensure SDXL prompts are dictionaries
        self._positive_sdxl = flow_data.get("positive_sdxl_prompts", {})
        if not isinstance(self._positive_sdxl, dict):
            self._positive_sdxl = {}

        self._negative_sdxl = flow_data.get("negative_sdxl_prompts", {})
        if not isinstance(self._negative_sdxl, dict):
            self._negative_sdxl = {}

        self._is_sdxl = flow_data.get("is_sdxl_workflow", False)

        if self._is_sdxl:  # If SDXL, construct main prompts from SDXL components if main ones are empty
            if not self._positive and self._positive_sdxl:
                self._positive = self.merge_clip(self._positive_sdxl)
            if not self._negative and self._negative_sdxl:
                self._negative = self.merge_clip(self._negative_sdxl)

        flow_params = flow_data.get("parameters", {})
        if isinstance(flow_params, dict):  # Ensure it's a dict
            for key, value in flow_params.items():
                if key in self._parameter and value is not None:  # Check if key is in our standard list
                    self._parameter[key] = str(value)  # Store as string

        fw_str = str(flow_data.get("width", "0")).strip()
        fh_str = str(flow_data.get("height", "0")).strip()

        if fw_str and fw_str != "0":
            self._width = fw_str
        if fh_str and fh_str != "0":
            self._height = fh_str

        # Update parameters dict with width/height/size
        if self._width != "0" and "width" in self._parameter:
            self._parameter["width"] = self._width
        if self._height != "0" and "height" in self._parameter:
            self._parameter["height"] = self._height
        if self._width != "0" and self._height != "0" and "size" in self._parameter:
            self._parameter["size"] = f"{self._width}x{self._height}"

        custom_settings = flow_data.get("custom_settings", {})
        if isinstance(custom_settings, dict):  # Ensure it's a dict
            self._setting = self._build_settings_string(
                custom_settings_dict=custom_settings,
                include_standard_params=True,  # Include standard params from self._parameter
                sort_parts=True,
            )

    def _comfy_png_traverse_and_extract(self) -> None:
        # Use self._prompt_json (filled from 'prompt' chunk) or self._workflow_json (filled from 'workflow' chunk)
        workflow_to_traverse = self._prompt_json or self._workflow_json

        if not workflow_to_traverse:
            self._logger.error("%s: No workflow JSON available for traversal.", self.tool)
            self.status = self.Status.COMFYUI_ERROR  # Or FORMAT_ERROR
            self._error = "ComfyUI workflow JSON missing for traversal."
            return

        end_nodes = self._find_end_node_candidates(workflow_to_traverse)

        # No need to set error here if end_nodes is empty, _get_best_flow_data will handle
        # if not end_nodes:
        #     self._logger.warning("%s: No SaveImage/KSampler end nodes found for traversal.", self.tool)
        # self._error could be set here, but _get_best_flow_data handles it if no data path.

        best_flow = self._get_best_flow_data(workflow_to_traverse, end_nodes)

        if not best_flow:
            # _get_best_flow_data should have set status and error if it failed to find meaningful data
            self._logger.warning("%s: Graph traversal yielded no data or failed.", self.tool)
            # Ensure error/status is set if not already
            if self.status not in [self.Status.FORMAT_ERROR, self.Status.COMFYUI_ERROR]:
                self.status = self.Status.COMFYUI_ERROR
                self._error = self._error or "Workflow graph traversal failed to extract any data."
            return  # Stop if no data could be extracted

        self._apply_flow_data_to_self(best_flow)

        # self._raw should ideally be the original JSON string.
        # It might have been set by ImageDataReader if 'raw' was passed to __init__.
        # If not, and we parsed from self._info["prompt"], set it now.
        if not self._raw:
            if self._info.get("prompt"):
                self._raw = str(self._info.get("prompt"))
            elif self._info.get("workflow"):
                self._raw = str(self._info.get("workflow"))
            elif workflow_to_traverse:  # Fallback to the parsed JSON if original string not available
                try:
                    self._raw = json.dumps(workflow_to_traverse)
                except TypeError:
                    self._raw = str(workflow_to_traverse)

    @staticmethod
    def merge_clip(data: dict[str, Any]) -> str:  # Use Dict
        # ... (implementation as before) ...
        clip_g = str(data.get("Clip G", "")).strip(" ,")
        clip_l = str(data.get("Clip L", "")).strip(" ,")
        if not clip_g and not clip_l:
            return ""
        if clip_g == clip_l:
            return clip_g
        if not clip_g:
            return clip_l
        if not clip_l:
            return clip_g
        return f"Clip G: {clip_g}, Clip L: {clip_l}"

    def _run_traversal_for_node(
        self, workflow_json_data: dict[str, Any], start_node_id: str
    ) -> dict[str, Any]:  # Use Dict
        # ... (implementation as before, ensure all dicts are Dict and use BaseFormat.PARAMETER_KEY) ...
        # Reset temporary state for this traversal path
        original_positive, self._positive = self._positive, ""
        original_negative, self._negative = self._negative, ""
        original_pos_sdxl, self._positive_sdxl = self._positive_sdxl.copy(), {}
        original_neg_sdxl, self._negative_sdxl = self._negative_sdxl.copy(), {}
        original_is_sdxl, self._is_sdxl = self._is_sdxl, False

        raw_flow_values, _ = self._original_comfy_traverse_logic(workflow_json_data, start_node_id)

        current_path_data: dict[str, Any] = {
            "positive_prompt": self._positive,
            "negative_prompt": self._negative,
            "positive_sdxl_prompts": self._positive_sdxl.copy(),
            "negative_sdxl_prompts": self._negative_sdxl.copy(),
            "is_sdxl_workflow": self._is_sdxl,
            "parameters": {},
            "custom_settings": {},
            "width": "0",
            "height": "0",
        }
        handled_in_params_or_dims = set()

        if isinstance(raw_flow_values, dict):  # Ensure raw_flow_values is a dict
            for comfy_key, target_keys_val in COMFY_FLOW_TO_PARAM_MAP.items():
                if comfy_key in raw_flow_values and raw_flow_values[comfy_key] is not None:
                    value = self._remove_quotes_from_string_utility(str(raw_flow_values[comfy_key]))
                    target_keys_list = [target_keys_val] if isinstance(target_keys_val, str) else target_keys_val
                    for tk_item in target_keys_list:
                        if tk_item in BaseFormat.PARAMETER_KEY:  # Use class variable correctly
                            current_path_data["parameters"][tk_item] = value
                            handled_in_params_or_dims.add(comfy_key)
                            break

            if raw_flow_values.get("k_width") is not None:
                current_path_data["width"] = str(raw_flow_values["k_width"])
                handled_in_params_or_dims.add("k_width")
            if raw_flow_values.get("k_height") is not None:
                current_path_data["height"] = str(raw_flow_values["k_height"])
                handled_in_params_or_dims.add("k_height")

            for setting_key in COMFY_SPECIFIC_SETTINGS_KEYS:
                if setting_key in raw_flow_values and raw_flow_values[setting_key] is not None:
                    disp_key = self._format_key_for_display(setting_key)
                    current_path_data["custom_settings"][disp_key] = self._remove_quotes_from_string_utility(
                        str(raw_flow_values[setting_key])
                    )
                    handled_in_params_or_dims.add(setting_key)

            for key, value_item in raw_flow_values.items():
                if key not in handled_in_params_or_dims and value_item is not None:
                    disp_key = self._format_key_for_display(key)
                    current_path_data["custom_settings"][disp_key] = self._remove_quotes_from_string_utility(
                        str(value_item)
                    )

        # Restore original state
        self._positive, self._negative = original_positive, original_negative
        self._positive_sdxl, self._negative_sdxl = original_pos_sdxl, original_neg_sdxl
        self._is_sdxl = original_is_sdxl
        return current_path_data

    @staticmethod
    def _remove_quotes_from_string_utility(
        text: Any,
    ) -> str:  # Accept Any, convert to str
        text_str = str(text).strip()  # Add strip here too
        if len(text_str) >= 2:
            if (text_str.startswith('"') and text_str.endswith('"')) or (
                text_str.startswith("'") and text_str.endswith("'")
            ):
                return text_str[1:-1]
        return text_str

    def _original_comfy_traverse_logic(
        self,
        prompt_data: dict[str, Any],  # Full workflow/prompt JSON
        node_id: str,  # Current node ID to process
    ) -> tuple[dict[str, Any], list[str]]:  # Returns (extracted_flow_data, node_path_list)
        flow: dict[str, Any] = {}
        node_path_history: list[str] = [node_id]  # Track nodes visited in this path

        current_node_details = prompt_data.get(node_id)
        if not isinstance(current_node_details, dict):
            self._logger.warning(
                "Node ID %s not found or not a dictionary in prompt data. Path: %s",
                node_id,
                node_path_history,
            )
            return {}, node_path_history  # Cannot proceed with this node

        current_node_inputs = current_node_details.get("inputs", {})
        if not isinstance(current_node_inputs, dict):
            current_node_inputs = {}

        class_type = str(current_node_details.get("class_type", "UnknownType"))
        self._logger.debug("Traversing node: %s (Type: %s)", node_id, class_type)

        # --- Node Type Specific Logic ---

        # 1. SaveImage (or similar output nodes)
        if class_type in self.SAVE_IMAGE_TYPE:
            images_input_link = current_node_inputs.get("images")  # Typically ["node_id_str", output_slot_int]
            if isinstance(images_input_link, list) and len(images_input_link) >= 1 and images_input_link[0] is not None:
                prev_node_id = str(images_input_link[0])
                if prev_node_id in prompt_data:
                    sub_flow, sub_nodes = self._original_comfy_traverse_logic(prompt_data, prev_node_id)
                    flow = merge_dict(flow, sub_flow)
                    node_path_history.extend(sub_nodes)

        # 2. KSampler (and variants)
        elif class_type in self.KSAMPLER_TYPES:
            # Extract direct parameters from KSampler inputs
            direct_sampler_keys = [
                "seed",
                "noise_seed",
                "steps",
                "cfg",
                "sampler_name",
                "scheduler",
                "denoise",
                "add_noise",
                "start_at_step",
                "end_at_step",
                "return_with_left_over_noise",
            ]
            for k_key in direct_sampler_keys:
                if (val := current_node_inputs.get(k_key)) is not None:  # Walrus operator
                    flow[k_key] = val

            # Try to get width/height from connected EmptyLatentImage node
            latent_input_link = current_node_inputs.get("latent_image")
            if isinstance(latent_input_link, list) and len(latent_input_link) >= 1 and latent_input_link[0] is not None:
                prev_latent_node_id = str(latent_input_link[0])
                prev_latent_node_details = prompt_data.get(prev_latent_node_id)
                if (
                    isinstance(prev_latent_node_details, dict)
                    and prev_latent_node_details.get("class_type") == "EmptyLatentImage"
                ):
                    lat_inputs = prev_latent_node_details.get("inputs", {})
                    if not isinstance(lat_inputs, dict):
                        lat_inputs = {}
                    if (w_val := lat_inputs.get("width")) is not None:
                        flow["k_width"] = w_val
                    if (h_val := lat_inputs.get("height")) is not None:
                        flow["k_height"] = h_val
                elif prev_latent_node_id in prompt_data:
                    sub_flow, sub_nodes = self._original_comfy_traverse_logic(prompt_data, prev_latent_node_id)
                    flow = merge_dict(flow, sub_flow)
                    node_path_history.extend(sub_nodes)

            # Traverse model, positive, negative inputs
            for input_name in ["model", "positive", "negative"]:
                input_link = current_node_inputs.get(input_name)
                if isinstance(input_link, list) and len(input_link) >= 1 and input_link[0] is not None:
                    prev_node_id = str(input_link[0])
                    if prev_node_id in prompt_data:
                        trav_data, p_nodes = self._original_comfy_traverse_logic(prompt_data, prev_node_id)
                        node_path_history.extend(p_nodes)
                        if input_name == "positive":
                            if isinstance(trav_data, str):
                                self._positive = trav_data
                            elif isinstance(trav_data, dict):
                                self._positive_sdxl.update(trav_data)
                        elif input_name == "negative":
                            if isinstance(trav_data, str):
                                self._negative = trav_data
                            elif isinstance(trav_data, dict):
                                self._negative_sdxl.update(trav_data)
                        elif isinstance(trav_data, dict):  # For "model" input
                            flow = merge_dict(flow, trav_data)

        # 3. CLIPTextEncode (and variants for prompts)
        elif class_type in self.CLIP_TEXT_ENCODE_TYPE:
            # Text can be a direct string input or linked from a PrimitiveNode
            text_input_val = current_node_inputs.get("text")
            actual_text_str = ""

            if isinstance(text_input_val, list) and len(text_input_val) >= 1 and text_input_val[0] is not None:
                # Text is linked from another node
                prev_text_node_id = str(text_input_val[0])
                if prev_text_node_id in prompt_data:
                    text_node_data, _ = self._original_comfy_traverse_logic(prompt_data, prev_text_node_id)
                    # PrimitiveNode returns {"text_output": "value"}
                    actual_text_str = (
                        text_node_data.get("text_output", str(text_node_data))
                        if isinstance(text_node_data, dict)
                        else str(text_node_data)
                    )
            elif isinstance(text_input_val, str):
                actual_text_str = text_input_val  # Direct string input

            if class_type == "CLIPTextEncode" or class_type == "smZ CLIPTextEncode":
                return actual_text_str.strip(), []  # Return the text string itself

            if class_type == "CLIPTextEncodeSDXL":
                self._is_sdxl = True
                sdxl_prompts: dict[str, str] = {}
                for clip_suffix, input_key in [("G", "text_g"), ("L", "text_l")]:
                    text_val_sdxl = current_node_inputs.get(input_key)
                    resolved_text_sdxl = ""
                    if isinstance(text_val_sdxl, list) and len(text_val_sdxl) >= 1 and text_val_sdxl[0] is not None:
                        prev_sdxl_text_node_id = str(text_val_sdxl[0])
                        if prev_sdxl_text_node_id in prompt_data:
                            sdxl_text_data, _ = self._original_comfy_traverse_logic(prompt_data, prev_sdxl_text_node_id)
                            resolved_text_sdxl = (
                                sdxl_text_data.get("text_output", str(sdxl_text_data))
                                if isinstance(sdxl_text_data, dict)
                                else str(sdxl_text_data)
                            )
                    elif isinstance(text_val_sdxl, str):
                        resolved_text_sdxl = text_val_sdxl
                    sdxl_prompts[f"Clip {clip_suffix}"] = resolved_text_sdxl.strip()
                return sdxl_prompts, []

            if class_type == "CLIPTextEncodeSDXLRefiner":
                self._is_sdxl = True
                refiner_prompt: dict[str, str] = {}
                # actual_text_str for refiner is resolved from "text" input above
                refiner_prompt["Refiner"] = actual_text_str.strip()
                return refiner_prompt, []

        # 4. LoraLoader
        elif class_type == "LoraLoader":
            if "lora_name" in current_node_inputs:
                flow["lora_name"] = current_node_inputs["lora_name"]
            # Also good to get strength if it's an input, but it's usually a widget.
            # The effect of LoRA is on the model, so traverse back through model/clip
            for input_name in ["model", "clip"]:
                input_link = current_node_inputs.get(input_name)
                if isinstance(input_link, list) and len(input_link) >= 1 and input_link[0] is not None:
                    prev_node_id = str(input_link[0])
                    if prev_node_id in prompt_data:
                        sub_flow, sub_nodes = self._original_comfy_traverse_logic(prompt_data, prev_node_id)
                        flow = merge_dict(flow, sub_flow)
                        node_path_history.extend(sub_nodes)

        # 5. CheckpointLoader (and variants)
        elif class_type in self.CHECKPOINT_LOADER_TYPE:
            if "ckpt_name" in current_node_inputs:
                return {"ckpt_name": current_node_inputs.get("ckpt_name")}, []

        # 6. VAEEncode (often in img2img or inpaint chains)
        elif class_type in self.VAE_ENCODE_TYPE:
            pixels_input_link = current_node_inputs.get("pixels")
            if isinstance(pixels_input_link, list) and len(pixels_input_link) >= 1 and pixels_input_link[0] is not None:
                prev_node_id = str(pixels_input_link[0])  # Could be LoadImage, etc.
                if prev_node_id in prompt_data:
                    sub_flow, sub_nodes = self._original_comfy_traverse_logic(prompt_data, prev_node_id)
                    flow = merge_dict(flow, sub_flow)
                    node_path_history.extend(sub_nodes)

        # 7. Seed Nodes (various custom seed nodes)
        elif class_type in [
            "CR Seed",
            "Seed (Inspire)",
            "Seed (integer)",
            "BNK_INT",
            "IntegerPrimitive",
        ]:  # Add other known seed nodes
            seed_val = current_node_inputs.get(
                "seed", current_node_inputs.get("int", current_node_inputs.get("Value"))
            )  # Common key names
            if seed_val is not None:
                return {"seed": seed_val}, []

        # 8. PrimitiveNode (often provides text or number to other nodes)
        elif class_type == "PrimitiveNode" or class_type.endswith("Primitive"):
            # For text, widgets_values might be more reliable if text isn't linked
            node_widgets = current_node_details.get("widgets_values")
            if isinstance(node_widgets, list) and node_widgets:
                # Assuming the first widget value is the primitive's output if it's a simple type
                return {"text_output": str(node_widgets[0])}, []
            if "value" in current_node_inputs:  # Fallback if linked
                return {"text_output": str(current_node_inputs["value"])}, []

        # 9. Specific Custom Nodes (Example: SDXLPromptStyler)
        elif class_type == "SDXLPromptStyler":  # Handles its own prompt setting
            self._positive = str(current_node_inputs.get("text_positive", "")).strip()
            self._negative = str(current_node_inputs.get("text_negative", "")).strip()
            # This node directly sets prompts on self, doesn't return flow data for merging here
            return {}, []

        # 10. Generic Fallback: Traverse common input names
        else:
            # Order of preference for traversal for unknown nodes
            preferred_input_order = [
                "model",
                "clip",
                "samples",
                "image",
                "conditioning",
                "latent",
                "VAE",
                " एनी इनपुट",
                "source_image",
            ]  # Added common custom input names
            found_traversal_path = False
            for input_name in preferred_input_order:
                input_link = current_node_inputs.get(input_name)
                if isinstance(input_link, list) and len(input_link) >= 1 and input_link[0] is not None:
                    prev_node_id = str(input_link[0])
                    if prev_node_id in prompt_data:
                        sub_flow, sub_nodes = self._original_comfy_traverse_logic(prompt_data, prev_node_id)
                        flow = merge_dict(flow, sub_flow)
                        node_path_history.extend(sub_nodes)
                        # If this path yielded significant data (model name, text output), prioritize it
                        is_significant_sub_flow = isinstance(sub_flow, str) or (
                            isinstance(sub_flow, dict) and (sub_flow.get("ckpt_name") or sub_flow.get("text_output"))
                        )
                        if is_significant_sub_flow:
                            found_traversal_path = True
                            break  # Processed the most likely important input, stop for this node
            if not found_traversal_path:
                self._logger.debug(
                    "Node %s (Type: %s): No standard inputs found to traverse.",
                    node_id,
                    class_type,
                )

        return flow, node_path_history
