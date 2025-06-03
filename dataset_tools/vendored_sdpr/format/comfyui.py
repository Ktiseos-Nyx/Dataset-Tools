# dataset_tools/vendored_sdpr/format/comfyui.py

__author__ = "receyuki"
__filename__ = "comfyui.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
from typing import Any

from .base_format import BaseFormat
from .utility import merge_dict  # remove_quotes is handled by _build_settings_string

COMFY_FLOW_TO_PARAM_MAP: dict[str, str | list[str]] = {
    "ckpt_name": "model",
    "sampler_name": "sampler_name",
    "seed": ["seed", "noise_seed"],
    "cfg": "cfg_scale",
    "steps": "steps",
    "scheduler": "scheduler",
}

COMFY_SPECIFIC_SETTINGS_KEYS: list[str] = [
    "add_noise",
    "start_at_step",
    "end_at_step",
    "return_with_left_over_noise",
    "denoise",
    "upscale_method",
    "upscaler",
]


class ComfyUI(BaseFormat):
    tool = "ComfyUI"

    KSAMPLER_TYPES = ["KSampler", "KSamplerAdvanced", "KSampler (Efficient)"]
    VAE_ENCODE_TYPE = ["VAEEncode", "VAEEncodeForInpaint"]
    CHECKPOINT_LOADER_TYPE = [
        "CheckpointLoader",
        "CheckpointLoaderSimple",
        "unCLIPCheckpointLoader",
        "Checkpoint Loader (Simple)",
    ]
    CLIP_TEXT_ENCODE_TYPE = [
        "CLIPTextEncode",
        "CLIPTextEncodeSDXL",
        "CLIPTextEncodeSDXLRefiner",
    ]
    SAVE_IMAGE_TYPE = ["SaveImage", "Image Save", "SDPromptSaver"]

    def __init__(
        self,
        info: dict[str, Any] | None = None,
        raw: str = "",
        width: int = 0,
        height: int = 0,
    ):
        super().__init__(info=info, raw=raw, width=width, height=height)
        self._prompt_json: dict[str, Any] = {}
        self._workflow_json: dict[str, Any] = {}

    def _process(self) -> None:
        self._logger.debug("Attempting to parse using %s logic.", self.tool)
        prompt_str = self._info.get("prompt")
        workflow_str = self._info.get("workflow")

        if not prompt_str:
            self._logger.warning(
                "%s: 'prompt' field (workflow JSON) not found in info dict.", self.tool
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "ComfyUI 'prompt' (workflow JSON) field missing."
            return

        try:
            loaded_prompt_json = json.loads(str(prompt_str))
            if not isinstance(loaded_prompt_json, dict):
                self._logger.error(
                    "%s: 'prompt' field is not a valid JSON dictionary.", self.tool
                )
                self.status = self.Status.FORMAT_ERROR
                self._error = "ComfyUI 'prompt' (workflow JSON) is not a dictionary."
                return
            self._prompt_json = loaded_prompt_json

            if workflow_str:
                loaded_workflow_json = json.loads(
                    str(workflow_str)
                )  # Corrected variable name
                if not isinstance(
                    loaded_workflow_json, dict
                ):  # Corrected variable name
                    self._logger.warning(
                        "%s: 'workflow' field provided but is not a valid JSON dictionary. Ignoring.",
                        self.tool,
                    )
                else:
                    self._workflow_json = (
                        loaded_workflow_json  # Corrected variable name
                    )
            self._logger.info(
                "%s: Successfully loaded prompt/workflow JSON.", self.tool
            )
        except json.JSONDecodeError as json_decode_err:
            self._logger.error(
                "%s: Failed to decode prompt/workflow JSON: %s",
                self.tool,
                json_decode_err,
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Invalid JSON in ComfyUI prompt/workflow: {json_decode_err}"
            return

        self._comfy_png_traverse_and_extract()

        if self.status != self.Status.FORMAT_ERROR:
            if (
                self._positive
                or self._negative
                or self._parameter_has_data()
                or self._width != "0"
            ):
                self._logger.info(
                    "%s: Data parsed successfully from workflow.", self.tool
                )
            else:
                self._logger.warning(
                    "%s: Traversal completed but no key prompt/parameter data extracted.",
                    self.tool,
                )
                self.status = self.Status.FORMAT_ERROR
                if not self._error:
                    self._error = f"{self.tool}: Failed to extract meaningful data from workflow graph."

    def _find_end_node_candidates(
        self, prompt_json_data: dict[str, Any]
    ) -> dict[str, str]:
        """Identifies potential end nodes (SaveImage or KSampler) in the workflow."""
        candidates: dict[str, str] = {}
        for node_id, node_data in prompt_json_data.items():
            class_type = node_data.get("class_type")
            if class_type in self.SAVE_IMAGE_TYPE or (class_type in self.KSAMPLER_TYPES and not any(
                typ in self.SAVE_IMAGE_TYPE for typ in candidates.values()
            )):
                candidates[node_id] = class_type
        return candidates

    def _get_best_flow_data(
        self, prompt_json_data: dict[str, Any], end_node_candidates: dict[str, str]
    ) -> dict[str, Any]:
        """Iterates through end nodes, runs traversal, and returns data from the 'best' flow."""
        best_flow_data: dict[str, Any] = {}
        max_extracted_params = -1

        for end_node_id in end_node_candidates:  # No need for _ value here
            temp_flow_details = self._run_traversal_for_node(
                prompt_json_data, end_node_id
            )

            num_params_in_flow = 0
            if temp_flow_details.get("positive_prompt") or temp_flow_details.get(
                "positive_sdxl_prompts"
            ):
                num_params_in_flow += 1
            if temp_flow_details.get("negative_prompt") or temp_flow_details.get(
                "negative_sdxl_prompts"
            ):
                num_params_in_flow += 1

            flow_params = temp_flow_details.get("parameters", {})
            for key in ["steps", "cfg_scale", "sampler_name", "seed", "model"]:
                if (
                    flow_params.get(key)
                    and flow_params[key] != self.DEFAULT_PARAMETER_PLACEHOLDER
                ):
                    num_params_in_flow += 1

            if num_params_in_flow > max_extracted_params:
                max_extracted_params = num_params_in_flow
                best_flow_data = temp_flow_details

        return best_flow_data

    def _apply_flow_data_to_self(self, flow_data: dict[str, Any]):
        """Applies the extracted data from a chosen flow to the instance attributes."""
        self._positive = str(flow_data.get("positive_prompt", ""))
        self._negative = str(flow_data.get("negative_prompt", ""))
        self._positive_sdxl = flow_data.get("positive_sdxl_prompts", {})
        self._negative_sdxl = flow_data.get("negative_sdxl_prompts", {})
        self._is_sdxl = flow_data.get("is_sdxl_workflow", False)

        if self._is_sdxl:
            if not self._positive and self._positive_sdxl:
                self._positive = self.merge_clip(self._positive_sdxl)
            if not self._negative and self._negative_sdxl:
                self._negative = self.merge_clip(self._negative_sdxl)

        flow_params_to_populate = flow_data.get("parameters", {})
        for key, value in flow_params_to_populate.items():
            if key in self._parameter and value is not None:
                self._parameter[key] = str(value)

        flow_width = flow_data.get("width")
        flow_height = flow_data.get("height")
        if flow_width is not None:
            self._width = str(flow_width)
        if flow_height is not None:
            self._height = str(flow_height)

        if "width" in self._parameter and self._width != "0":
            self._parameter["width"] = self._width
        if "height" in self._parameter and self._height != "0":
            self._parameter["height"] = self._height
        if "size" in self._parameter and self._width != "0" and self._height != "0":
            self._parameter["size"] = f"{self._width}x{self._height}"

        custom_settings_from_flow = flow_data.get("custom_settings", {})
        self._setting = self._build_settings_string(
            custom_settings_dict=custom_settings_from_flow,
            include_standard_params=True,
            sort_parts=True,
        )

    def _comfy_png_traverse_and_extract(self) -> None:
        prompt_json_data = self._prompt_json
        if not prompt_json_data:
            self._logger.error("%s: _prompt_json is empty before traversal.", self.tool)
            self.status = self.Status.FORMAT_ERROR
            self._error = "ComfyUI prompt JSON data missing for traversal."
            return

        end_node_candidates = self._find_end_node_candidates(prompt_json_data)
        if not end_node_candidates:
            self._logger.warning(
                "%s: No SaveImage or KSampler end nodes found in workflow.", self.tool
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = (
                "No suitable end node (SaveImage/KSampler) found in ComfyUI workflow."
            )
            return

        longest_flow_data = self._get_best_flow_data(
            prompt_json_data, end_node_candidates
        )
        if not longest_flow_data:
            self._logger.warning(
                "%s: Graph traversal yielded no data from any end node.", self.tool
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "Workflow graph traversal failed to extract data."
            return

        self._apply_flow_data_to_self(longest_flow_data)

        if not self._raw and self._prompt_json:  # Set self._raw if not already set
            try:
                self._raw = json.dumps(self._prompt_json)
            except TypeError:
                self._logger.warning(
                    "%s: Could not serialize _prompt_json to string for self._raw.",
                    self.tool,
                    exc_info=True,
                )
                self._raw = str(self._prompt_json)

    @staticmethod
    def merge_clip(data: dict[str, Any]) -> str:
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
        return f"Clip G: {clip_g}, Clip L: {clip_l}"  # f-string for string construction is fine

    def _run_traversal_for_node(
        self, prompt_json_data: dict[str, Any], start_node_id: str
    ) -> dict[str, Any]:
        path_positive_prompt = ""
        path_negative_prompt = ""
        path_positive_sdxl_prompts: dict[str, str] = {}
        path_negative_sdxl_prompts: dict[str, str] = {}
        path_is_sdxl_workflow = False
        path_parameters: dict[str, Any] = {}
        path_custom_settings: dict[str, str] = {}
        path_width = "0"
        path_height = "0"

        original_self_positive, original_self_negative = self._positive, self._negative
        original_self_pos_sdxl, original_self_neg_sdxl = (
            self._positive_sdxl.copy(),
            self._negative_sdxl.copy(),
        )
        original_self_is_sdxl = self._is_sdxl

        flow_node_values, _ = self._original_comfy_traverse_logic(
            prompt_json_data, start_node_id
        )

        path_positive_prompt = self._positive
        path_negative_prompt = self._negative
        path_positive_sdxl_prompts = self._positive_sdxl.copy()
        path_negative_sdxl_prompts = self._negative_sdxl.copy()
        path_is_sdxl_workflow = self._is_sdxl

        self._positive, self._negative = original_self_positive, original_self_negative
        self._positive_sdxl, self._negative_sdxl = (
            original_self_pos_sdxl,
            original_self_neg_sdxl,
        )
        self._is_sdxl = original_self_is_sdxl

        handled_flow_keys = set()
        # Use _populate_parameter concept from BaseFormat, but on path_parameters
        # This requires flow_node_values to contain keys that COMFY_FLOW_TO_PARAM_MAP understands
        for flow_key, canonical_key_target in COMFY_FLOW_TO_PARAM_MAP.items():
            if flow_key in flow_node_values:
                value_from_flow = flow_node_values[flow_key]
                target_keys_list = (
                    [canonical_key_target]
                    if isinstance(canonical_key_target, str)
                    else canonical_key_target
                )
                populated_to_standard = False
                for target_key_item in target_keys_list:
                    if target_key_item in BaseFormat.PARAMETER_KEY:
                        # Apply ComfyUI's specific remove_quotes before storing
                        path_parameters[target_key_item] = str(
                            self._remove_quotes_from_string_utility(
                                str(value_from_flow)
                            )
                        )
                        populated_to_standard = True
                        break
                if populated_to_standard:
                    handled_flow_keys.add(flow_key)
                # If not populated to standard, it might be a custom setting if the map intended that.
                # Current COMFY_FLOW_TO_PARAM_MAP only lists standard targets.

        if flow_node_values.get("k_width"):
            path_width = str(flow_node_values["k_width"])  # Corrected access
        if flow_node_values.get("k_height"):
            path_height = str(flow_node_values["k_height"])  # Corrected access
        handled_flow_keys.update(["k_width", "k_height"])

        for key in COMFY_SPECIFIC_SETTINGS_KEYS:
            if key in flow_node_values and key not in handled_flow_keys:
                display_key = self._format_key_for_display(
                    key
                )  # Inherited from BaseFormat
                path_custom_settings[display_key] = str(
                    self._remove_quotes_from_string_utility(str(flow_node_values[key]))
                )
                handled_flow_keys.add(key)

        for key, value in flow_node_values.items():
            if key not in handled_flow_keys:
                display_key = self._format_key_for_display(key)
                path_custom_settings[display_key] = str(
                    self._remove_quotes_from_string_utility(str(value))
                )

        return {
            "positive_prompt": path_positive_prompt,
            "negative_prompt": path_negative_prompt,
            "positive_sdxl_prompts": path_positive_sdxl_prompts,
            "negative_sdxl_prompts": path_negative_sdxl_prompts,
            "is_sdxl_workflow": path_is_sdxl_workflow,
            "parameters": path_parameters,
            "custom_settings": path_custom_settings,
            "width": path_width,
            "height": path_height,
        }

    @staticmethod
    def _remove_quotes_from_string_utility(text: str) -> str:
        """Static utility to remove quotes, mirroring BaseFormat._remove_quotes_from_string"""
        if len(text) >= 2:
            if text.startswith('"') and text.endswith('"'):
                return text[1:-1]
            if text.startswith("'") and text.endswith("'"):
                return text[1:-1]
        return text

    # pylint: disable=too-many-branches,too-many-statements,too-many-return-statements
    def _original_comfy_traverse_logic(
        self,
        prompt: dict[str, Any],
        end_node_id: str,
    ) -> tuple[dict[str, Any], list[str]]:
        flow: dict[str, Any] = {}
        node_path: list[str] = [end_node_id]
        current_node_inputs: dict[str, Any] = {}
        try:
            current_node_inputs = prompt[end_node_id]["inputs"]
        except KeyError:
            self._logger.warning(
                "Node ID %s not found in prompt JSON during traversal.", end_node_id
            )
            return {}, []
        except Exception as e_input:  # pylint: disable=broad-except
            self._logger.error(
                "Error accessing inputs for node %s: %s",
                end_node_id,
                e_input,
                exc_info=True,
            )
            return {}, []

        class_type = prompt[end_node_id].get("class_type", "UnknownType")

        match class_type:
            case node_type if node_type in self.SAVE_IMAGE_TYPE:
                try:
                    images_input = current_node_inputs.get("images")
                    if isinstance(images_input, list) and images_input:
                        last_flow, last_node_path = self._original_comfy_traverse_logic(
                            prompt, str(images_input[0])
                        )
                        flow = merge_dict(flow, last_flow)
                        node_path.extend(last_node_path)
                    else:
                        self._logger.debug(
                            "SaveImage node %s has no valid 'images' input.",
                            end_node_id,
                        )
                except Exception as save_image_err:  # pylint: disable=broad-except
                    self._logger.error(
                        "Error traversing from SaveImage node %s: %s",
                        end_node_id,
                        save_image_err,
                        exc_info=True,
                    )

            case node_type if node_type in self.KSAMPLER_TYPES:
                try:
                    ksampler_direct_keys = [
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
                    for k_key in ksampler_direct_keys:  # Renamed k to k_key
                        if current_node_inputs.get(k_key) is not None:
                            flow[k_key] = current_node_inputs[k_key]

                    latent_input = current_node_inputs.get("latent_image")
                    if isinstance(latent_input, list) and latent_input:
                        prev_node_id_latent = str(latent_input[0])
                        prev_node_info_latent = prompt.get(prev_node_id_latent)
                        if (
                            prev_node_info_latent
                            and prev_node_info_latent.get("class_type")
                            == "EmptyLatentImage"
                        ):
                            latent_node_inputs = prev_node_info_latent.get("inputs", {})
                            if latent_node_inputs.get("width") is not None:
                                flow["k_width"] = latent_node_inputs["width"]
                            if latent_node_inputs.get("height") is not None:
                                flow["k_height"] = latent_node_inputs["height"]

                    path_nodes_for_ksampler: list[str] = []
                    for input_key, input_value in current_node_inputs.items():
                        if not (isinstance(input_value, list) and input_value):
                            continue
                        prev_node_id = str(input_value[0])
                        if not (
                            isinstance(prev_node_id, str) and prev_node_id in prompt
                        ):
                            continue

                        traversed_data, prev_nodes = (
                            self._original_comfy_traverse_logic(prompt, prev_node_id)
                        )
                        path_nodes_for_ksampler.extend(prev_nodes)

                        if input_key == "positive":
                            if isinstance(traversed_data, str):
                                self._positive = traversed_data
                            elif isinstance(traversed_data, dict):
                                self._positive_sdxl.update(traversed_data)
                        elif input_key == "negative":
                            if isinstance(traversed_data, str):
                                self._negative = traversed_data
                            elif isinstance(traversed_data, dict):
                                self._negative_sdxl.update(traversed_data)
                        elif isinstance(traversed_data, dict):
                            flow = merge_dict(flow, traversed_data)
                        elif input_key in ("seed", "noise_seed") and isinstance(
                            traversed_data, (int, float, str)
                        ):
                            flow[input_key] = traversed_data
                        elif (
                            input_key in ("seed", "noise_seed")
                            and isinstance(traversed_data, dict)
                            and "seed" in traversed_data
                        ):
                            flow[input_key] = traversed_data["seed"]
                    node_path.extend(path_nodes_for_ksampler)
                except Exception as ksampler_err:  # pylint: disable=broad-except
                    self._logger.error(
                        "Error traversing KSampler node %s: %s",
                        end_node_id,
                        ksampler_err,
                        exc_info=True,
                    )

            case node_type if node_type in self.CLIP_TEXT_ENCODE_TYPE:
                try:
                    text_input_val = current_node_inputs.get("text")
                    if node_type == "CLIPTextEncode":
                        if isinstance(text_input_val, list) and text_input_val:
                            return self._original_comfy_traverse_logic(
                                prompt, str(text_input_val[0])
                            )
                        if isinstance(text_input_val, str):
                            return text_input_val, []
                        return {}, []

                    if node_type == "CLIPTextEncodeSDXL":
                        self._is_sdxl = True
                        text_g_val, text_l_val = current_node_inputs.get(
                            "text_g"
                        ), current_node_inputs.get("text_l")
                        sdxl_prompts: dict[str, Any] = {}

                        if isinstance(text_g_val, list) and text_g_val:
                            g_data, _ = self._original_comfy_traverse_logic(
                                prompt, str(text_g_val[0])
                            )
                            sdxl_prompts["Clip G"] = (
                                g_data.get("text", str(g_data))
                                if isinstance(g_data, dict)
                                else str(g_data)
                            )
                        else:
                            sdxl_prompts["Clip G"] = str(text_g_val)

                        if isinstance(text_l_val, list) and text_l_val:
                            l_data, _ = self._original_comfy_traverse_logic(
                                prompt, str(text_l_val[0])
                            )
                            sdxl_prompts["Clip L"] = (
                                l_data.get("text", str(l_data))
                                if isinstance(l_data, dict)
                                else str(l_data)
                            )
                        else:
                            sdxl_prompts["Clip L"] = str(text_l_val)
                        return sdxl_prompts, []

                    if node_type == "CLIPTextEncodeSDXLRefiner":
                        self._is_sdxl = True
                        refiner_prompts: dict[str, Any] = {}
                        if isinstance(text_input_val, list) and text_input_val:
                            ref_data, _ = self._original_comfy_traverse_logic(
                                prompt, str(text_input_val[0])
                            )
                            refiner_prompts["Refiner"] = (
                                ref_data.get("text", str(ref_data))
                                if isinstance(ref_data, dict)
                                else str(ref_data)
                            )
                        else:
                            refiner_prompts["Refiner"] = str(text_input_val)
                        return refiner_prompts, []
                except Exception as clip_err:  # pylint: disable=broad-except
                    self._logger.error(
                        "Error in CLIPTextEncode node %s (type %s): %s",
                        end_node_id,
                        node_type,
                        clip_err,
                        exc_info=True,
                    )

            case "LoraLoader":
                try:
                    for key_lora in ["model", "clip"]:  # Renamed key to key_lora
                        lora_input_val = current_node_inputs.get(key_lora)
                        if isinstance(lora_input_val, list) and lora_input_val:
                            sub_flow, sub_nodes = self._original_comfy_traverse_logic(
                                prompt, str(lora_input_val[0])
                            )
                            flow = merge_dict(flow, sub_flow)
                            node_path.extend(sub_nodes)
                    if current_node_inputs.get("lora_name"):
                        current_loras = flow.get("lora_name", [])
                        if not isinstance(current_loras, list):
                            current_loras = [str(current_loras)]  # Ensure list
                        current_loras.append(current_node_inputs.get("lora_name"))
                        flow["lora_name"] = current_loras

                except Exception as lora_err:  # pylint: disable=broad-except
                    self._logger.error(
                        "Error in LoraLoader node %s: %s",
                        end_node_id,
                        lora_err,
                        exc_info=True,
                    )

            case node_type if node_type in self.CHECKPOINT_LOADER_TYPE:
                return {"ckpt_name": current_node_inputs.get("ckpt_name")}, []

            case node_type if node_type in self.VAE_ENCODE_TYPE:
                try:
                    pixels_input = current_node_inputs.get("pixels")
                    if isinstance(pixels_input, list) and pixels_input:
                        last_flow, last_node_path_vae = (
                            self._original_comfy_traverse_logic(
                                prompt, str(pixels_input[0])
                            )
                        )
                        flow = merge_dict(flow, last_flow)
                        node_path.extend(last_node_path_vae)
                except Exception as vae_err:  # pylint: disable=broad-except
                    self._logger.error(
                        "Error in VAEEncode node %s: %s",
                        end_node_id,
                        vae_err,
                        exc_info=True,
                    )

            case "SDXLPromptStyler":
                try:
                    self._positive = current_node_inputs.get("text_positive", "")
                    self._negative = current_node_inputs.get("text_negative", "")
                    return {}, []
                except Exception as styler_err:  # pylint: disable=broad-except
                    self._logger.error(
                        "Error in SDXLPromptStyler node %s: %s",
                        end_node_id,
                        styler_err,
                        exc_info=True,
                    )

            case "CR Seed":
                try:
                    return {"seed": current_node_inputs.get("seed")}, []
                except Exception as cr_seed_err:  # pylint: disable=broad-except
                    self._logger.error(
                        "Error in CR Seed node %s: %s",
                        end_node_id,
                        cr_seed_err,
                        exc_info=True,
                    )

            case _:
                try:
                    follow_order = [
                        "model",
                        "clip",
                        "samples",
                        "image",
                        "conditioning",
                        "latent",
                        "VAE",
                    ]
                    found_path = False
                    for input_name in follow_order:
                        input_val = current_node_inputs.get(input_name)
                        if isinstance(input_val, list) and input_val:
                            prev_node_id_default = str(input_val[0])
                            if prev_node_id_default in prompt:
                                sub_flow, sub_nodes = (
                                    self._original_comfy_traverse_logic(
                                        prompt, prev_node_id_default
                                    )
                                )
                                flow = merge_dict(flow, sub_flow)
                                node_path.extend(sub_nodes)
                                if (
                                    sub_flow.get("ckpt_name")
                                    or sub_flow.get("sampler_name")
                                    or isinstance(sub_flow, str)
                                ):
                                    found_path = True
                                    break
                    if not found_path:
                        self._logger.debug(
                            "Default node %s (type %s) did not find a primary path in follow_order.",
                            end_node_id,
                            class_type,
                        )
                except Exception as default_err:  # pylint: disable=broad-except
                    self._logger.error(
                        "Error in default/bridging node %s (type %s): %s",
                        end_node_id,
                        class_type,
                        default_err,
                        exc_info=True,
                    )
        return flow, node_path
