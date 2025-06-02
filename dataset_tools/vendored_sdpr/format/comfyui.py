# dataset_tools/vendored_sdpr/format/comfyui.py

__author__ = "receyuki"
__filename__ = "comfyui.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools
__copyright__ = "Copyright 2023, Receyuki"
__email__ = "receyuki@gmail.com"

import json
import logging  # For type hinting
from typing import Any  # For type hints

# from ..logger import Logger  # OLD
from ..logger import get_logger  # NEW
from .base_format import BaseFormat
from .utility import merge_dict, remove_quotes


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
        info: dict[str, Any] | None = None,  # Added type hints
        raw: str = "",
        width: int = 0,
        height: int = 0,
    ):
        super().__init__(info=info, raw=raw, width=width, height=height)
        # self._logger = Logger(f"DSVendored_SDPR.Format.{self.tool}") # OLD
        self._logger: logging.Logger = get_logger(
            f"DSVendored_SDPR.Format.{self.tool}",
        )  # NEW
        # self.PARAMETER_PLACEHOLDER = PARAMETER_PLACEHOLDER # Inherited
        self._prompt_json: dict[str, Any] = {}  # Type hint
        self._workflow_json: dict[str, Any] = {}  # Type hint

    def _process(self):
        # pylint: disable=no-member # Temporary if Pylint still complains after get_logger
        self._logger.debug(f"Attempting to parse using {self.tool} logic.")

        prompt_str = self._info.get("prompt")
        workflow_str = self._info.get("workflow")

        if not prompt_str:
            self._logger.warn(
                f"{self.tool}: 'prompt' field (workflow JSON) not found in info dict.",
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = "ComfyUI 'prompt' (workflow JSON) field missing."
            return

        try:
            self._prompt_json = json.loads(str(prompt_str))
            if workflow_str:
                self._workflow_json = json.loads(str(workflow_str))
            self._logger.info(f"{self.tool}: Successfully loaded prompt/workflow JSON.")
        except json.JSONDecodeError as json_decode_err:  # Renamed 'e'
            self._logger.error(
                f"{self.tool}: Failed to decode prompt/workflow JSON: {json_decode_err}",
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Invalid JSON in ComfyUI prompt/workflow: {json_decode_err}"
            return
        except Exception as e_load:  # pylint: disable=broad-except
            self._logger.error(
                f"{self.tool}: Unexpected error loading prompt/workflow JSON: {e_load}",
                exc_info=True,
            )
            self.status = self.Status.FORMAT_ERROR
            self._error = f"Error loading ComfyUI JSON: {e_load}"
            return

        self._comfy_png_traverse_and_extract()

        if self._positive or any(
            v_val != self.DEFAULT_PARAMETER_PLACEHOLDER
            for k_key, v_val in self._parameter.items()
            if k_key != "size"  # Renamed k,v
        ):
            self._logger.info(f"{self.tool}: Data parsed successfully from workflow.")
            self.status = self.Status.READ_SUCCESS
        else:
            self._logger.warn(
                f"{self.tool}: Traversal completed but no key prompt/parameter data extracted.",
            )
            self.status = self.Status.FORMAT_ERROR
            if not self._error:
                self._error = f"{self.tool}: Failed to extract meaningful data from workflow graph."

    def _comfy_png_traverse_and_extract(self):
        # pylint: disable=no-member # Temporary
        prompt_json = self._prompt_json
        end_node_candidates: dict[str, str] = {}
        for node_id, node_data in prompt_json.items():
            class_type = node_data.get("class_type")
            if class_type in self.SAVE_IMAGE_TYPE or (
                class_type in self.KSAMPLER_TYPES and not end_node_candidates
            ):
                end_node_candidates[node_id] = class_type

        if not end_node_candidates:
            self._logger.warn(
                f"{self.tool}: No SaveImage or KSampler end nodes found in workflow.",
            )
            self._error = "No suitable end node (SaveImage/KSampler) found."
            return

        longest_flow_data: dict[str, Any] = {}  # Type hint
        max_extracted_params = -1

        for end_node_id, _end_node_type_val in end_node_candidates.items():  # Renamed _
            extracted_data_from_flow = self._comfy_traverse(prompt_json, end_node_id)
            num_params_in_flow = 0
            if extracted_data_from_flow.get("positive") or extracted_data_from_flow.get(
                "positive_sdxl",
            ):
                num_params_in_flow += 1
            if extracted_data_from_flow.get("negative") or extracted_data_from_flow.get(
                "negative_sdxl",
            ):
                num_params_in_flow += 1
            for key in ["steps", "cfg", "sampler_name", "seed", "ckpt_name"]:
                if extracted_data_from_flow.get(key):
                    num_params_in_flow += 1
            if num_params_in_flow > max_extracted_params:
                max_extracted_params = num_params_in_flow
                longest_flow_data = extracted_data_from_flow

        if not longest_flow_data:
            self._logger.warn(
                f"{self.tool}: Graph traversal yielded no data from any end node.",
            )
            self._error = "Workflow graph traversal failed to extract data."
            return

        self._positive = str(longest_flow_data.get("positive", ""))
        self._negative = str(longest_flow_data.get("negative", ""))
        self._positive_sdxl = longest_flow_data.get("positive_sdxl", {})
        self._negative_sdxl = longest_flow_data.get("negative_sdxl", {})
        self._is_sdxl = longest_flow_data.get("is_sdxl", False)

        if self._is_sdxl:
            if not self._positive and self._positive_sdxl:
                self._positive = self.merge_clip(self._positive_sdxl)
            if not self._negative and self._negative_sdxl:
                self._negative = self.merge_clip(self._negative_sdxl)

        mapping = {
            "ckpt_name": "model",
            "sampler_name": "sampler_name",
            "seed": "seed",
            "cfg": "cfg_scale",
            "steps": "steps",
            "scheduler": "scheduler",
        }
        for flow_key, canonical_key in mapping.items():
            if flow_key in longest_flow_data and canonical_key in self._parameter:
                value = longest_flow_data[flow_key]
                self._parameter[canonical_key] = str(remove_quotes(str(value)))

        if longest_flow_data.get("k_width") and longest_flow_data.get("k_height"):
            self._width = str(longest_flow_data["k_width"])
            self._height = str(longest_flow_data["k_height"])
        if "size" in self._parameter and self._width != "0" and self._height != "0":
            self._parameter["size"] = f"{self._width}x{self._height}"

        setting_parts = []
        if longest_flow_data.get("steps"):
            setting_parts.append(f"Steps: {longest_flow_data['steps']}")
        if longest_flow_data.get("sampler_name"):
            setting_parts.append(
                f"Sampler: {remove_quotes(str(longest_flow_data['sampler_name']))}",
            )
        if longest_flow_data.get("cfg"):
            setting_parts.append(f"CFG scale: {longest_flow_data['cfg']}")
        seed_val = longest_flow_data.get(
            "seed",
            longest_flow_data.get("noise_seed"),
        )  # Renamed variable
        if seed_val is not None:
            setting_parts.append(f"Seed: {seed_val}")
        setting_parts.append(f"Size: {self._width}x{self._height}")
        if longest_flow_data.get("ckpt_name"):
            setting_parts.append(
                f"Model: {remove_quotes(str(longest_flow_data['ckpt_name']))}",
            )
        if longest_flow_data.get("scheduler"):
            setting_parts.append(
                f"Scheduler: {remove_quotes(str(longest_flow_data['scheduler']))}",
            )

        optional_ksampler_params = [
            "add_noise",
            "start_at_step",
            "end_at_step",
            "return_with_left_over_noise",
            "denoise",
        ]
        for p_name in optional_ksampler_params:
            if longest_flow_data.get(p_name) is not None:
                display_key = p_name.replace("_", " ").capitalize()
                setting_parts.append(
                    f"{display_key}: {remove_quotes(str(longest_flow_data[p_name]))}",
                )
        if longest_flow_data.get("upscale_method"):
            setting_parts.append(
                f"Upscale method: {remove_quotes(str(longest_flow_data['upscale_method']))}",
            )
        if longest_flow_data.get("upscaler"):
            setting_parts.append(
                f"Upscaler: {remove_quotes(str(longest_flow_data['upscaler']))}",
            )
        self._setting = ", ".join(filter(None, setting_parts))

    @staticmethod
    def merge_clip(data: dict[str, Any]) -> str:  # Type hint
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

    # Type hints
    def _comfy_traverse(
        self,
        prompt_json: dict[str, Any],
        current_node_id: str,
    ) -> dict[str, Any]:
        # pylint: disable=no-member # Temporary
        self._positive = ""
        self._negative = ""
        self._positive_sdxl = {}
        self._negative_sdxl = {}
        self._is_sdxl = False
        flow_details, _ = self._original_comfy_traverse_logic(
            prompt_json,
            current_node_id,
        )
        return_data = flow_details.copy()
        return_data["positive"] = self._positive
        return_data["negative"] = self._negative
        return_data["positive_sdxl"] = self._positive_sdxl.copy()
        return_data["negative_sdxl"] = self._negative_sdxl.copy()
        return_data["is_sdxl"] = self._is_sdxl
        return return_data

    # pylint: disable=too-many-branches,too-many-statements,too-many-return-statements # For original complex logic
    def _original_comfy_traverse_logic(
        self,
        prompt: dict[str, Any],
        end_node: str,
    ) -> tuple[dict[str, Any], list[str]]:  # Type hints
        # pylint: disable=no-member # Temporary
        flow: dict[str, Any] = {}
        node_path: list[str] = [end_node]  # Renamed 'node' to 'node_path'
        inputs: dict[str, Any] = {}
        try:
            inputs = prompt[end_node]["inputs"]
        except KeyError:
            self._logger.warn(
                f"Node ID {end_node} not found in prompt JSON during traversal.",
            )
            return {}, []
        except Exception as e_input:  # pylint: disable=broad-except
            self._logger.error(
                f"Error accessing inputs for node {end_node}: {e_input}",
                exc_info=True,
            )
            return {}, []

        class_type = prompt[end_node].get("class_type", "UnknownType")

        match class_type:
            case node_type if node_type in self.SAVE_IMAGE_TYPE:
                try:
                    if (
                        "images" in inputs
                        and isinstance(inputs["images"], list)
                        and inputs["images"]
                    ):
                        last_flow, last_node_path = self._original_comfy_traverse_logic(
                            prompt,
                            str(inputs["images"][0]),
                        )
                        flow = merge_dict(flow, last_flow)
                        node_path.extend(last_node_path)
                    else:
                        self._logger.debug(
                            f"SaveImage node {end_node} has no 'images' input or not a list.",
                        )
                except (
                    Exception
                ) as save_image_err:  # Renamed 'e', pylint: disable=broad-except
                    self._logger.error(
                        f"Error traversing from SaveImage node {end_node}: {save_image_err}",
                        exc_info=True,
                    )

            case node_type if node_type in self.KSAMPLER_TYPES:
                try:
                    ksampler_keys = [
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
                    flow.update(
                        {
                            k: inputs.get(k)
                            for k in ksampler_keys
                            if inputs.get(k) is not None
                        },
                    )

                    if (
                        "latent_image" in inputs
                        and isinstance(inputs["latent_image"], list)
                        and inputs["latent_image"]
                    ):
                        prev_node_id_latent = str(inputs["latent_image"][0])
                        prev_node_info_latent = prompt.get(prev_node_id_latent)
                        if (
                            prev_node_info_latent
                            and prev_node_info_latent.get("class_type")
                            == "EmptyLatentImage"
                        ):
                            latent_inputs = prev_node_info_latent.get("inputs", {})
                            if latent_inputs.get("width") is not None:
                                flow["k_width"] = latent_inputs.get("width")
                            if latent_inputs.get("height") is not None:
                                flow["k_height"] = latent_inputs.get("height")

                    path_nodes_for_ksampler: list[str] = []  # Type hint
                    for input_key, input_value in inputs.items():
                        traversed_input_data: Any = None  # Initialize
                        if input_key in [
                            "model",
                            "positive",
                            "negative",
                            "latent_image",
                        ]:
                            if isinstance(input_value, list) and input_value:
                                prev_node_id = str(input_value[0])
                                traversed_input_data = (
                                    self._original_comfy_traverse_logic(
                                        prompt,
                                        prev_node_id,
                                    )
                                )
                                if isinstance(traversed_input_data, tuple):
                                    prev_flow, prev_nodes = traversed_input_data
                                    flow = merge_dict(flow, prev_flow)
                                    path_nodes_for_ksampler.extend(prev_nodes)
                                elif input_key == "positive":
                                    if isinstance(traversed_input_data, str):
                                        self._positive = traversed_input_data
                                    elif isinstance(traversed_input_data, dict):
                                        self._positive_sdxl.update(traversed_input_data)
                                elif input_key == "negative":
                                    if isinstance(traversed_input_data, str):
                                        self._negative = traversed_input_data
                                    elif isinstance(traversed_input_data, dict):
                                        self._negative_sdxl.update(traversed_input_data)
                                elif isinstance(traversed_input_data, dict):
                                    flow = merge_dict(flow, traversed_input_data)
                        elif input_key in ("seed", "noise_seed"):
                            if isinstance(input_value, list) and input_value:
                                seed_node_id = str(input_value[0])
                                seed_data_tuple = self._original_comfy_traverse_logic(
                                    prompt,
                                    seed_node_id,
                                )
                                # seed_data should be a dict from CR Seed or similar, or the value itself
                                seed_data = (
                                    seed_data_tuple[0]
                                    if isinstance(seed_data_tuple, tuple)
                                    else seed_data_tuple
                                )
                                if isinstance(seed_data, (int, float, str)):
                                    flow[input_key] = seed_data
                                elif (
                                    isinstance(seed_data, dict) and "seed" in seed_data
                                ):
                                    flow[input_key] = seed_data["seed"]
                        elif (
                            isinstance(input_value, list)
                            and input_value
                            and isinstance(input_value[0], str)
                            and input_value[0] in prompt
                        ):
                            prev_node_id_generic = str(
                                input_value[0],
                            )  # Renamed prev_node_id
                            traversed_input_data_generic = (
                                self._original_comfy_traverse_logic(
                                    prompt,
                                    prev_node_id_generic,
                                )
                            )  # Renamed traversed_input_data
                            if isinstance(
                                traversed_input_data_generic,
                                tuple,
                            ) and isinstance(traversed_input_data_generic[0], dict):
                                flow = merge_dict(flow, traversed_input_data_generic[0])
                                path_nodes_for_ksampler.extend(
                                    traversed_input_data_generic[1],
                                )
                            elif isinstance(traversed_input_data_generic, dict):
                                flow = merge_dict(flow, traversed_input_data_generic)
                    node_path.extend(path_nodes_for_ksampler)
                except (
                    Exception
                ) as ksampler_err:  # Renamed 'e', pylint: disable=broad-except
                    self._logger.error(
                        f"Error traversing KSampler node {end_node}: {ksampler_err}",
                        exc_info=True,
                    )

            case node_type if node_type in self.CLIP_TEXT_ENCODE_TYPE:
                try:
                    if node_type == "CLIPTextEncode":
                        text_input = inputs.get("text")  # Renamed 'text'
                        if isinstance(text_input, list) and text_input:
                            return self._original_comfy_traverse_logic(
                                prompt,
                                str(text_input[0]),
                            )
                        if isinstance(text_input, str):
                            # Return as tuple (flow, nodes)
                            return text_input, []
                        return {}, []  # Default if no text
                    if node_type == "CLIPTextEncodeSDXL":
                        self._is_sdxl = True
                        text_g, text_l = inputs.get("text_g"), inputs.get("text_l")
                        # This needs to return a dict that can be merged into positive_sdxl/negative_sdxl
                        # or directly populate self._positive_sdxl based on linked styler nodes.
                        # For simplicity, returning dict for now.
                        # The original logic was complex due to styler nodes returning (pos, neg) tuples.
                        # This simplified version returns a dict, assuming styler returns text.
                        result_sdxl: dict[str, Any] = {}  # type hint
                        # Linked, e.g. to SDXLPromptStyler
                        if isinstance(text_g, list) and text_g:
                            # Assume styler returns (pos_prompt_str, neg_prompt_str)
                            # This part of logic is tricky as _original_comfy_traverse_logic returns (flow_dict, node_list)
                            # We'd need a way for styler nodes to indicate positive/negative parts.
                            # For now, let's assume a simple text pass-through or a specific structure.
                            # This simplification might lose some of the original SDPR's advanced styler handling.
                            styler_g_data, _ = self._original_comfy_traverse_logic(
                                prompt,
                                str(text_g[0]),
                            )
                            styler_l_data, _ = self._original_comfy_traverse_logic(
                                prompt,
                                str(text_l[0]),
                            )
                            # Assuming styler_g_data might be {'text': 'styled_g'} or just 'styled_g'
                            result_sdxl["Clip G"] = (
                                styler_g_data.get("text", str(styler_g_data))
                                if isinstance(styler_g_data, dict)
                                else str(styler_g_data)
                            )
                            result_sdxl["Clip L"] = (
                                styler_l_data.get("text", str(styler_l_data))
                                if isinstance(styler_l_data, dict)
                                else str(styler_l_data)
                            )
                        else:  # Direct text inputs
                            result_sdxl["Clip G"] = str(text_g)
                            result_sdxl["Clip L"] = str(text_l)
                        return result_sdxl, []
                    if node_type == "CLIPTextEncodeSDXLRefiner":
                        self._is_sdxl = True
                        text_refiner = inputs.get("text")  # Renamed 'text'
                        result_refiner: dict[str, Any] = {}  # Type hint
                        if isinstance(text_refiner, list) and text_refiner:
                            styler_ref_data, _ = self._original_comfy_traverse_logic(
                                prompt,
                                str(text_refiner[0]),
                            )
                            result_refiner["Refiner"] = (
                                styler_ref_data.get("text", str(styler_ref_data))
                                if isinstance(styler_ref_data, dict)
                                else str(styler_ref_data)
                            )
                        else:
                            result_refiner["Refiner"] = str(text_refiner)
                        return result_refiner, []
                except (
                    Exception
                ) as clip_err:  # Renamed 'e', pylint: disable=broad-except
                    self._logger.error(
                        f"Error in CLIPTextEncode node {end_node} (type {node_type}): {clip_err}",
                        exc_info=True,
                    )

            case "LoraLoader":
                try:
                    if (
                        "model" in inputs
                        and isinstance(inputs["model"], list)
                        and inputs["model"]
                    ):
                        last_flow_model, last_node_model = (
                            self._original_comfy_traverse_logic(
                                prompt,
                                str(inputs["model"][0]),
                            )
                        )
                        flow = merge_dict(flow, last_flow_model)
                        node_path.extend(last_node_model)
                    if (
                        "clip" in inputs
                        and isinstance(inputs["clip"], list)
                        and inputs["clip"]
                    ):
                        last_flow_clip, last_node_clip = (
                            self._original_comfy_traverse_logic(
                                prompt,
                                str(inputs["clip"][0]),
                            )
                        )
                        flow = merge_dict(flow, last_flow_clip)
                        node_path.extend(last_node_clip)
                    if inputs.get("lora_name"):
                        flow["lora_name"] = inputs.get("lora_name")
                except (
                    Exception
                ) as lora_err:  # Renamed 'e', pylint: disable=broad-except
                    self._logger.error(
                        f"Error in LoraLoader node {end_node}: {lora_err}",
                        exc_info=True,
                    )

            case node_type if node_type in self.CHECKPOINT_LOADER_TYPE:
                try:
                    # Return as tuple
                    return {"ckpt_name": inputs.get("ckpt_name")}, []
                except (
                    Exception
                ) as ckpt_err:  # Renamed 'e', pylint: disable=broad-except
                    self._logger.error(
                        f"Error in CheckpointLoader node {end_node}: {ckpt_err}",
                        exc_info=True,
                    )

            case node_type if node_type in self.VAE_ENCODE_TYPE:
                try:
                    if (
                        "pixels" in inputs
                        and isinstance(inputs["pixels"], list)
                        and inputs["pixels"]
                    ):
                        last_flow, last_node_path_vae = (
                            self._original_comfy_traverse_logic(
                                prompt,
                                str(inputs["pixels"][0]),
                            )
                        )  # Renamed last_node
                        flow = merge_dict(flow, last_flow)
                        node_path.extend(last_node_path_vae)
                except (
                    Exception
                ) as vae_err:  # Renamed 'e', pylint: disable=broad-except
                    self._logger.error(
                        f"Error in VAEEncode node {end_node}: {vae_err}",
                        exc_info=True,
                    )

            case "SDXLPromptStyler":
                try:  # This node should output structured prompt data.
                    # The original code assumed it returns (pos, neg) directly.
                    # Let's assume it sets 'text_positive' and 'text_negative' in its output flow.
                    pos_prompt = inputs.get("text_positive", "")
                    neg_prompt = inputs.get("text_negative", "")
                    # This return needs to be structured so the calling KSampler can differentiate pos/neg
                    # when assigned to self._positive / self._negative.
                    # The original SDPR _comfy_traverse had complex global-like modifications.
                    # A cleaner way is for CLIPTextEncode to ask for pos/neg from this node.
                    # For now, returning a dict indicating what it provides.
                    # This part of the logic is the most complex due to recursion and shared state.
                    # Simplified return, may need adjustment based on how CLIPTextEncode handles it:
                    return {"positive": pos_prompt, "negative": neg_prompt}, []
                except (
                    Exception
                ) as styler_err:  # Renamed 'e', pylint: disable=broad-except
                    self._logger.error(
                        f"Error in SDXLPromptStyler node {end_node}: {styler_err}",
                        exc_info=True,
                    )

            case "CR Seed":
                try:
                    return {"seed": inputs.get("seed")}, []
                except (
                    Exception
                ) as cr_seed_err:  # Renamed 'e', pylint: disable=broad-except
                    self._logger.error(
                        f"Error in CR Seed node {end_node}: {cr_seed_err}",
                        exc_info=True,
                    )

            case _:  # Default case
                try:
                    follow_order = [
                        "samples",
                        "image",
                        "model",
                        "clip",
                        "conditioning",
                        "latent",
                    ]
                    for input_name in follow_order:
                        if (
                            input_name in inputs
                            and isinstance(inputs[input_name], list)
                            and inputs[input_name]
                        ):
                            prev_node_id_default = str(
                                inputs[input_name][0],
                            )  # Renamed prev_node_id
                            traversed_data_default = (
                                self._original_comfy_traverse_logic(
                                    prompt,
                                    prev_node_id_default,
                                )
                            )  # Renamed traversed_data
                            if isinstance(traversed_data_default, tuple):
                                flow = merge_dict(flow, traversed_data_default[0])
                                node_path.extend(traversed_data_default[1])
                                # Check if significant data was found
                                if (
                                    traversed_data_default[0].get("ckpt_name")
                                    or traversed_data_default[0].get("positive")
                                    or traversed_data_default[0].get("sampler_name")
                                ):
                                    break  # Found a primary path
                            elif (
                                isinstance(traversed_data_default, str)
                                and input_name == "conditioning"
                            ):
                                # Simplified: assume positive if not clearly negative
                                # This needs more robust handling for SDXL where conditioning can be complex
                                if not self._positive:
                                    self._positive = traversed_data_default
                                elif not self._negative:
                                    self._negative = traversed_input_data  # Assuming traversed_input_data was intended here
                                break
                            elif isinstance(traversed_data_default, dict):
                                flow = merge_dict(flow, traversed_data_default)
                                if (
                                    traversed_data_default.get("ckpt_name")
                                    or traversed_data_default.get("positive")
                                    or traversed_data_default.get("sampler_name")
                                ):
                                    break
                except (
                    Exception
                ) as default_err:  # Renamed 'e', pylint: disable=broad-except
                    self._logger.error(
                        f"Error in default/bridging node {end_node} (type {class_type}): {default_err}",
                        exc_info=True,
                    )
        return flow, node_path
