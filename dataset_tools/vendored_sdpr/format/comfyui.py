# dataset_tools/vendored_sdpr/format/comfyui.py

__author__ = "receyuki"
__filename__ = "comfyui.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
from typing import Any

from .base_format import BaseFormat
from .utility import merge_dict

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
        self._workflow_json: dict[str, Any] | None = None

    def _process(self) -> None:
        self._logger.debug("Attempting to parse using %s logic.", self.tool)
        prompt_str = self._info.get("prompt")
        workflow_str = self._info.get("workflow")

        if not prompt_str:
            self._logger.warning("%s: 'prompt' field (workflow JSON) not found.", self.tool)
            self.status = self.Status.FORMAT_ERROR
            self._error = "ComfyUI 'prompt' (workflow JSON) field missing."
            return

        try:
            loaded_prompt_json = json.loads(str(prompt_str))
            if not isinstance(loaded_prompt_json, dict):
                self._logger.error("%s: 'prompt' field not a valid JSON dict.", self.tool)
                self.status = self.Status.FORMAT_ERROR
                self._error = "ComfyUI 'prompt' (workflow JSON) not a dict."
                return
            self._prompt_json = loaded_prompt_json

            if workflow_str:
                try:
                    loaded_workflow_json = json.loads(str(workflow_str))
                    if isinstance(loaded_workflow_json, dict):
                        self._workflow_json = loaded_workflow_json
                    else:
                        self._logger.warning("%s: 'workflow' field not JSON dict. Ignoring.", self.tool)
                except json.JSONDecodeError as wf_err:
                    self._logger.warning(
                        "%s: Fail decode 'workflow' JSON: %s. Ignoring.",
                        self.tool,
                        wf_err,
                    )
            self._logger.info("%s: Loaded prompt/workflow JSON.", self.tool)
        except json.JSONDecodeError as json_err:
            self._logger.error("%s: Fail decode prompt JSON: %s", self.tool, json_err, exc_info=True)
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Invalid JSON in ComfyUI prompt: {json_err}"
            return

        self._comfy_png_traverse_and_extract()

        if self.status != self.Status.FORMAT_ERROR:
            if (
                self._positive
                or self._negative
                or self._positive_sdxl
                or self._negative_sdxl
                or self._parameter_has_data()
                or self._width != "0"
                or self._height != "0"
            ):
                self._logger.info("%s: Data parsed from workflow.", self.tool)
            else:
                self._logger.warning("%s: Traversal done but no key data.", self.tool)
                self.status = self.Status.FORMAT_ERROR
                if not self._error:
                    self._error = f"{self.tool}: Failed to extract from workflow."

    def _find_end_node_candidates(self, prompt_json_data: dict[str, Any]) -> dict[str, str]:
        candidates: dict[str, str] = {}
        is_save_image_present = any(
            node_data.get("class_type") in self.SAVE_IMAGE_TYPE for node_data in prompt_json_data.values()
        )
        for node_id, node_data in prompt_json_data.items():
            class_type = node_data.get("class_type")
            if is_save_image_present:
                if class_type in self.SAVE_IMAGE_TYPE:
                    candidates[node_id] = class_type
            elif class_type in self.KSAMPLER_TYPES:
                candidates[node_id] = class_type
        return candidates

    def _count_meaningful_params(self, flow_details: dict[str, Any]) -> int:
        count = 0
        if flow_details.get("positive_prompt") or flow_details.get("positive_sdxl_prompts"):
            count += 1
        if flow_details.get("negative_prompt") or flow_details.get("negative_sdxl_prompts"):
            count += 1
        flow_params = flow_details.get("parameters", {})
        for key in BaseFormat.PARAMETER_KEY:
            if flow_params.get(key) and flow_params[key] != self.DEFAULT_PARAMETER_PLACEHOLDER:
                count += 1
        if flow_details.get("width", "0") != "0":
            count += 1
        if flow_details.get("height", "0") != "0":
            count += 1
        return count

    def _get_best_flow_data(
        self, prompt_json_data: dict[str, Any], end_node_candidates: dict[str, str]
    ) -> dict[str, Any]:
        best_flow_data: dict[str, Any] = {}
        max_extracted_params = -1
        self._logger.debug("Candidate end nodes for traversal: %s", end_node_candidates)
        for end_node_id, class_type in end_node_candidates.items():
            self._logger.debug("Traversing from end node: %s (Type: %s)", end_node_id, class_type)
            temp_flow_details = self._run_traversal_for_node(prompt_json_data, end_node_id)
            num_params_in_flow = self._count_meaningful_params(temp_flow_details)
            self._logger.debug("Flow from node %s yielded %s params.", end_node_id, num_params_in_flow)
            if num_params_in_flow > max_extracted_params:
                max_extracted_params = num_params_in_flow
                best_flow_data = temp_flow_details
        if best_flow_data:
            self._logger.info("Best flow selected with %s params.", max_extracted_params)
        else:
            self._logger.warning("No data extracted from any traversal path.")
        return best_flow_data

    def _apply_flow_data_to_self(self, flow_data: dict[str, Any]) -> None:
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
        flow_params = flow_data.get("parameters", {})
        for key, value in flow_params.items():
            if key in self._parameter and value is not None:
                self._parameter[key] = str(value)
        fw_str = str(flow_data.get("width", "0"))
        fh_str = str(flow_data.get("height", "0"))
        if fw_str != "0":
            self._width = fw_str
        if fh_str != "0":
            self._height = fh_str
        if self._width != "0":
            self._parameter["width"] = self._width
        if self._height != "0":
            self._parameter["height"] = self._height
        if self._width != "0" and self._height != "0":
            self._parameter["size"] = f"{self._width}x{self._height}"
        custom_settings = flow_data.get("custom_settings", {})
        self._setting = self._build_settings_string(
            custom_settings_dict=custom_settings,
            include_standard_params=True,
            sort_parts=True,
        )

    def _comfy_png_traverse_and_extract(self) -> None:
        if not self._prompt_json:
            self._logger.error("%s: _prompt_json empty before traversal.", self.tool)
            self.status = self.Status.FORMAT_ERROR
            self._error = "ComfyUI prompt JSON missing."
            return
        end_nodes = self._find_end_node_candidates(self._prompt_json)
        if not end_nodes:
            self._logger.warning("%s: No SaveImage/KSampler end nodes.", self.tool)
        if not self._error:
            self._error = "No typical end nodes found, metadata may be limited."

        best_flow = self._get_best_flow_data(self._prompt_json, end_nodes)
        if not best_flow:
            self._logger.warning("%s: Graph traversal yielded no data.", self.tool)
            if self.status != self.Status.FORMAT_ERROR:
                self.status = self.Status.COMFYUI_ERROR
            if not self._error:
                self._error = "Workflow graph failed to extract data."
                return
        else:
            self._apply_flow_data_to_self(best_flow)
        if not self._raw and self._prompt_json:
            try:
                self._raw = json.dumps(self._prompt_json)
            except TypeError:
                self._logger.warning(
                    "%s: Could not serialize _prompt_json to raw.",
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
        return f"Clip G: {clip_g}, Clip L: {clip_l}"

    def _run_traversal_for_node(
        self, prompt_json_data: dict[str, Any], start_node_id: str
    ) -> dict[str, Any]:
        original_positive = self._positive
        original_negative = self._negative
        original_pos_sdxl = self._positive_sdxl.copy()
        original_neg_sdxl = self._negative_sdxl.copy()
        original_is_sdxl = self._is_sdxl
        self._positive = ""
        self._negative = ""
        self._positive_sdxl.clear()
        self._negative_sdxl.clear()
        self._is_sdxl = False

        raw_flow_values, _ = self._original_comfy_traverse_logic(prompt_json_data, start_node_id)

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
        for comfy_key, target_keys in COMFY_FLOW_TO_PARAM_MAP.items():
            if comfy_key in raw_flow_values and raw_flow_values[comfy_key] is not None:
                value = self._remove_quotes_from_string_utility(str(raw_flow_values[comfy_key]))
                tgt_list = [target_keys] if isinstance(target_keys, str) else target_keys
                for tk_item in tgt_list:
                    if tk_item in BaseFormat.PARAMETER_KEY:
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
        for key, value in raw_flow_values.items():
            if key not in handled_in_params_or_dims and value is not None:
                disp_key = self._format_key_for_display(key)
                current_path_data["custom_settings"][disp_key] = self._remove_quotes_from_string_utility(str(value))
        self._positive = original_positive
        self._negative = original_negative
        self._positive_sdxl = original_pos_sdxl
        self._negative_sdxl = original_neg_sdxl
        self._is_sdxl = original_is_sdxl
        return current_path_data

    @staticmethod
    def _remove_quotes_from_string_utility(text: str) -> str:
        if not isinstance(text, str):
            text = str(text)
        if len(text) >= 2:
            if text.startswith('"') and text.endswith('"'):
                return text[1:-1]
            if text.startswith("'") and text.endswith("'"):
                return text[1:-1]
        return text

    def _original_comfy_traverse_logic(
        self,
        prompt: dict[str, Any],
        node_id: str,
    ) -> tuple[dict[str, Any], list[str]]:
        flow: dict[str, Any] = {}
        node_path_history: list[str] = [node_id]
        try:
            current_node_details = prompt[node_id]
            current_node_inputs = current_node_details.get("inputs", {})
            class_type = current_node_details.get("class_type", "UnknownType")
        except KeyError:
            self._logger.warning("Node ID %s not in prompt.", node_id)
            return {}, node_path_history
        except Exception as e:
            self._logger.error("Error accessing node %s: %s", node_id, e, exc_info=True)
            return {}, node_path_history

        if class_type in self.SAVE_IMAGE_TYPE:
            images_input = current_node_inputs.get("images")
            if isinstance(images_input, list) and images_input and len(images_input) == 2:
                prev_node_id = str(images_input[0])
                if prev_node_id in prompt:
                    sub_flow, sub_nodes = self._original_comfy_traverse_logic(prompt, prev_node_id)
                    flow = merge_dict(flow, sub_flow)
                    node_path_history.extend(sub_nodes)
        elif class_type in self.KSAMPLER_TYPES:
            direct_keys = [
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
            for k_key in direct_keys:
                if (val := current_node_inputs.get(k_key)) is not None:
                    flow[k_key] = val
            if (
                (lat_in := current_node_inputs.get("latent_image"))
                and isinstance(lat_in, list)
                and lat_in
                and len(lat_in) == 2
            ):
                p_nid_lat = str(lat_in[0])
                if p_nid_lat in prompt and prompt[p_nid_lat].get("class_type") == "EmptyLatentImage":
                    lat_inputs = prompt[p_nid_lat].get("inputs", {})
                    if (w_val := lat_inputs.get("width")) is not None:
                        flow["k_width"] = w_val
                    if (h_val := lat_inputs.get("height")) is not None:
                        flow["k_height"] = h_val
            for input_name in ["model", "positive", "negative", "vae"]:
                input_value = current_node_inputs.get(input_name)
                if isinstance(input_value, list) and input_value and len(input_value) == 2:
                    prev_node_id = str(input_value[0])
                    if prev_node_id in prompt:
                        trav_data, p_nodes = self._original_comfy_traverse_logic(prompt, prev_node_id)
                        node_path_history.extend(p_nodes)
                        if input_name == "positive":
                            (isinstance(trav_data, str) and setattr(self, "_positive", trav_data)) or (
                                isinstance(trav_data, dict) and self._positive_sdxl.update(trav_data)
                            )
                        elif input_name == "negative":
                            (isinstance(trav_data, str) and setattr(self, "_negative", trav_data)) or (
                                isinstance(trav_data, dict) and self._negative_sdxl.update(trav_data)
                            )
                        elif isinstance(trav_data, dict):
                            flow = merge_dict(flow, trav_data)
        elif class_type in self.CLIP_TEXT_ENCODE_TYPE:
            txt_in = current_node_inputs.get("text")
            if class_type == "CLIPTextEncode":
                return (
                    (self._original_comfy_traverse_logic(prompt, str(txt_in[0])))
                    if isinstance(txt_in, list) and txt_in and len(txt_in) == 2
                    else ((txt_in, []) if isinstance(txt_in, str) else ({}, []))
                )
            if class_type == "CLIPTextEncodeSDXL":
                self._is_sdxl = True
                sdxl_p: dict[str, str] = {}
                for ck_sfx, ci_key in [("G", "text_g"), ("L", "text_l")]:
                    in_v = current_node_inputs.get(ci_key)
                    ptxt = ""
                    if isinstance(in_v, list) and in_v and len(in_v) == 2:
                        s_data, _ = self._original_comfy_traverse_logic(prompt, str(in_v[0]))
                        ptxt = s_data.get("text_output", str(s_data)) if isinstance(s_data, dict) else str(s_data)
                    elif isinstance(in_v, str):
                        ptxt = in_v
                    sdxl_p[f"Clip {ck_sfx}"] = ptxt
                return sdxl_p, []
            if class_type == "CLIPTextEncodeSDXLRefiner":
                self._is_sdxl = True
                ref_p: dict[str, str] = {}
                ptxt = ""
                if isinstance(txt_in, list) and txt_in and len(txt_in) == 2:
                    s_data, _ = self._original_comfy_traverse_logic(prompt, str(txt_in[0]))
                    ptxt = s_data.get("text_output", str(s_data)) if isinstance(s_data, dict) else str(s_data)
                elif isinstance(txt_in, str):
                    ptxt = txt_in
                ref_p["Refiner"] = ptxt
                return ref_p, []
        elif class_type == "LoraLoader":
            if "lora_name" in current_node_inputs:
                flow["lora_name"] = current_node_inputs["lora_name"]
            for input_name in ["model", "clip"]:
                if (
                    (in_val := current_node_inputs.get(input_name))
                    and isinstance(in_val, list)
                    and in_val
                    and len(in_val) == 2
                ):
                    prev_node_id = str(in_val[0])
                    if prev_node_id in prompt:
                        sub_flow, sub_nodes = self._original_comfy_traverse_logic(prompt, prev_node_id)
                        flow = merge_dict(flow, sub_flow)
                        node_path_history.extend(sub_nodes)
        elif class_type in self.CHECKPOINT_LOADER_TYPE:
            if "ckpt_name" in current_node_inputs:
                return {"ckpt_name": current_node_inputs.get("ckpt_name")}, []
        elif class_type in self.VAE_ENCODE_TYPE:
            if (
                (pix_in := current_node_inputs.get("pixels"))
                and isinstance(pix_in, list)
                and pix_in
                and len(pix_in) == 2
            ):
                prev_node_id = str(pix_in[0])
                if prev_node_id in prompt:
                    sub_flow, sub_nodes = self._original_comfy_traverse_logic(prompt, prev_node_id)
                    flow = merge_dict(flow, sub_flow)
                    node_path_history.extend(sub_nodes)
        elif class_type == "SDXLPromptStyler":
            self._positive = str(current_node_inputs.get("text_positive", ""))
            self._negative = str(current_node_inputs.get("text_negative", ""))
            return {}, []
        elif class_type in ["CR Seed", "Seed (Inspire)"]:
            return {"seed": current_node_inputs.get("seed")}, []
        elif class_type == "PrimitiveNode" or class_type.endswith("Primitive"):
            if "value" in current_node_inputs:
                return {"text_output": str(current_node_inputs["value"])}, []
        else:
            follow_order = [
                "model",
                "clip",
                "samples",
                "image",
                "conditioning",
                "latent",
                "VAE",
            ]
            for input_name in follow_order:
                if (
                    (input_val := current_node_inputs.get(input_name))
                    and isinstance(input_val, list)
                    and input_val
                    and len(input_val) == 2
                ):
                    prev_node_id = str(input_val[0])
                    if prev_node_id in prompt:
                        sub_flow, sub_nodes = self._original_comfy_traverse_logic(prompt, prev_node_id)
                        flow = merge_dict(flow, sub_flow)
                        node_path_history.extend(sub_nodes)
                        is_sig_sub_flow = isinstance(sub_flow, str) or (
                            isinstance(sub_flow, dict) and (sub_flow.get("ckpt_name") or sub_flow.get("text_output"))
                        )
                        if is_sig_sub_flow:
                            break
        return flow, node_path_history
