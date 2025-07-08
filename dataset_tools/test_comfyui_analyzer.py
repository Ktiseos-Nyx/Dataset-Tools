#!/usr/bin/env python3

"""Test script for ComfyUI workflow analyzer."""

import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("ComfyUITest")

# Import the analyzer
from metadata_engine.extractors.comfyui_workflow_analyzer import (
    analyze_comfyui_workflow,
)

# Your workflow data
workflow_data = {
    "last_node_id": 72,
    "last_link_id": 108,
    "nodes": [
        {
            "id": 10,
            "type": "VAELoader",
            "pos": {"0": 26, "1": 379},
            "size": {"0": 315, "1": 58},
            "flags": {},
            "order": 0,
            "mode": 0,
            "inputs": [],
            "outputs": [
                {
                    "name": "VAE",
                    "type": "VAE",
                    "links": [12],
                    "slot_index": 0,
                    "shape": 3,
                }
            ],
            "properties": {"Node name for S&R": "VAELoader"},
            "widgets_values": ["ae.sft"],
        },
        {
            "id": 6,
            "type": "CLIPTextEncode",
            "pos": {"0": 424.71875, "1": 618.052001953125},
            "size": {"0": 210, "1": 54},
            "flags": {"collapsed": False},
            "order": 12,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 108},
                {
                    "name": "text",
                    "type": "STRING",
                    "link": 47,
                    "slot_index": 1,
                    "widget": {"name": "text"},
                },
            ],
            "outputs": [
                {
                    "name": "CONDITIONING",
                    "type": "CONDITIONING",
                    "links": [86],
                    "slot_index": 0,
                }
            ],
            "properties": {"Node name for S&R": "CLIPTextEncode"},
            "widgets_values": [""],
        },
        {
            "id": 22,
            "type": "BasicGuider",
            "pos": {"0": 893.71875, "1": 612.052001953125},
            "size": {"0": 196.9998779296875, "1": 62.66668701171875},
            "flags": {"collapsed": False},
            "order": 16,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 94, "slot_index": 0},
                {
                    "name": "conditioning",
                    "type": "CONDITIONING",
                    "link": 87,
                    "slot_index": 1,
                },
            ],
            "outputs": [
                {
                    "name": "GUIDER",
                    "type": "GUIDER",
                    "links": [30],
                    "slot_index": 0,
                    "shape": 3,
                }
            ],
            "properties": {"Node name for S&R": "BasicGuider"},
        },
        {
            "id": 13,
            "type": "SamplerCustomAdvanced",
            "pos": {"0": 1143.252685546875, "1": 89.17115783691406},
            "size": {"0": 352.4039611816406, "1": 463.3393859863281},
            "flags": {},
            "order": 17,
            "mode": 0,
            "inputs": [
                {"name": "noise", "type": "NOISE", "link": 37, "slot_index": 0},
                {"name": "guider", "type": "GUIDER", "link": 30, "slot_index": 1},
                {"name": "sampler", "type": "SAMPLER", "link": 19, "slot_index": 2},
                {"name": "sigmas", "type": "SIGMAS", "link": 20, "slot_index": 3},
                {"name": "latent_image", "type": "LATENT", "link": 23, "slot_index": 4},
            ],
            "outputs": [
                {
                    "name": "output",
                    "type": "LATENT",
                    "links": [24],
                    "slot_index": 0,
                    "shape": 3,
                },
                {
                    "name": "denoised_output",
                    "type": "LATENT",
                    "links": None,
                    "shape": 3,
                },
            ],
            "properties": {"Node name for S&R": "SamplerCustomAdvanced"},
        },
        {
            "id": 61,
            "type": "ModelSamplingFlux",
            "pos": {"0": 754, "1": 383},
            "size": {"0": 321.8402404785156, "1": 122},
            "flags": {},
            "order": 13,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 106},
                {
                    "name": "width",
                    "type": "INT",
                    "link": 102,
                    "widget": {"name": "width"},
                },
                {
                    "name": "height",
                    "type": "INT",
                    "link": 104,
                    "widget": {"name": "height"},
                },
            ],
            "outputs": [
                {
                    "name": "MODEL",
                    "type": "MODEL",
                    "links": [93, 94],
                    "slot_index": 0,
                    "shape": 3,
                }
            ],
            "properties": {"Node name for S&R": "ModelSamplingFlux"},
            "widgets_values": [1.15, 0.5, 1024, 1024],
        },
        {
            "id": 8,
            "type": "VAEDecode",
            "pos": {"0": 1613, "1": 62},
            "size": {"0": 210, "1": 46},
            "flags": {},
            "order": 18,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 24},
                {"name": "vae", "type": "VAE", "link": 12},
            ],
            "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [9], "slot_index": 0}],
            "properties": {"Node name for S&R": "VAEDecode"},
        },
        {
            "id": 60,
            "type": "FluxGuidance",
            "pos": {"0": 659, "1": 614},
            "size": {"0": 211.60000610351562, "1": 58},
            "flags": {},
            "order": 14,
            "mode": 0,
            "inputs": [{"name": "conditioning", "type": "CONDITIONING", "link": 86}],
            "outputs": [
                {
                    "name": "CONDITIONING",
                    "type": "CONDITIONING",
                    "links": [87],
                    "slot_index": 0,
                    "shape": 3,
                }
            ],
            "properties": {"Node name for S&R": "FluxGuidance"},
            "widgets_values": [3.5],
            "color": "#323",
            "bgcolor": "#535",
        },
        {
            "id": 16,
            "type": "KSamplerSelect",
            "pos": {"0": 809, "1": 261},
            "size": {"0": 268.2277526855469, "1": 58},
            "flags": {},
            "order": 2,
            "mode": 0,
            "inputs": [],
            "outputs": [{"name": "SAMPLER", "type": "SAMPLER", "links": [19], "shape": 3}],
            "properties": {"Node name for S&R": "KSamplerSelect"},
            "widgets_values": ["euler"],
        },
        {
            "id": 9,
            "type": "SaveImage",
            "pos": {"0": 1585, "1": 245},
            "size": {"0": 399.1837463378906, "1": 508.5245666503906},
            "flags": {},
            "order": 19,
            "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 9}],
            "outputs": [],
            "properties": {"Node name for S&R": "SaveImage"},
            "widgets_values": ["MarkuryFLUX"],
        },
        {
            "id": 5,
            "type": "EmptyLatentImage",
            "pos": {"0": 422, "1": 101},
            "size": {"0": 330.5548400878906, "1": 78},
            "flags": {},
            "order": 10,
            "mode": 0,
            "inputs": [
                {
                    "name": "width",
                    "type": "INT",
                    "link": 101,
                    "widget": {"name": "width"},
                },
                {
                    "name": "height",
                    "type": "INT",
                    "link": 103,
                    "widget": {"name": "height"},
                },
            ],
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [23], "slot_index": 0}],
            "properties": {"Node name for S&R": "EmptyLatentImage"},
            "widgets_values": [832, 1216, 1],
        },
        {
            "id": 17,
            "type": "BasicScheduler",
            "pos": {"0": 797, "1": 94},
            "size": {"0": 281.2428283691406, "1": 106},
            "flags": {},
            "order": 15,
            "mode": 0,
            "inputs": [{"name": "model", "type": "MODEL", "link": 93, "slot_index": 0}],
            "outputs": [{"name": "SIGMAS", "type": "SIGMAS", "links": [20], "shape": 3}],
            "properties": {"Node name for S&R": "BasicScheduler"},
            "widgets_values": ["beta", 25, 1],
        },
        {
            "id": 11,
            "type": "DualCLIPLoader",
            "pos": {"0": 22, "1": 214},
            "size": {"0": 315, "1": 106},
            "flags": {},
            "order": 4,
            "mode": 0,
            "inputs": [],
            "outputs": [
                {
                    "name": "CLIP",
                    "type": "CLIP",
                    "links": [108],
                    "slot_index": 0,
                    "shape": 3,
                }
            ],
            "properties": {"Node name for S&R": "DualCLIPLoader"},
            "widgets_values": [
                "t5xxl_fp8_e4m3fn.safetensors",
                "clip_l.safetensors",
                "flux",
            ],
        },
        {
            "id": 70,
            "type": "Int Literal",
            "pos": {"0": 31, "1": 484},
            "size": {"0": 315, "1": 58},
            "flags": {},
            "order": 5,
            "mode": 0,
            "inputs": [],
            "outputs": [
                {
                    "name": "INT",
                    "type": "INT",
                    "links": [101, 102],
                    "slot_index": 0,
                    "shape": 3,
                }
            ],
            "title": "Width",
            "properties": {"Node name for S&R": "Int Literal"},
            "widgets_values": [832],
        },
        {
            "id": 71,
            "type": "Int Literal",
            "pos": {"0": 28, "1": 610},
            "size": {"0": 315, "1": 58},
            "flags": {},
            "order": 6,
            "mode": 0,
            "inputs": [],
            "outputs": [
                {
                    "name": "INT",
                    "type": "INT",
                    "links": [103, 104],
                    "slot_index": 0,
                    "shape": 3,
                }
            ],
            "title": "Height",
            "properties": {"Node name for S&R": "Int Literal"},
            "widgets_values": [1216],
        },
        {
            "id": 72,
            "type": "LoraLoaderModelOnly",
            "pos": {"0": 419, "1": 403},
            "size": {"0": 315, "1": 82},
            "flags": {},
            "order": 11,
            "mode": 0,
            "inputs": [{"name": "model", "type": "MODEL", "link": 107}],
            "outputs": [
                {
                    "name": "MODEL",
                    "type": "MODEL",
                    "links": [106],
                    "slot_index": 0,
                    "shape": 3,
                }
            ],
            "properties": {"Node name for S&R": "LoraLoaderModelOnly"},
            "widgets_values": ["ArcaneFGTNR.safetensors", 1],
        },
        {
            "id": 25,
            "type": "RandomNoise",
            "pos": {"0": 424, "1": 236},
            "size": {"0": 327.1990661621094, "1": 94.58134460449219},
            "flags": {},
            "order": 7,
            "mode": 0,
            "inputs": [],
            "outputs": [{"name": "NOISE", "type": "NOISE", "links": [37], "shape": 3}],
            "properties": {"Node name for S&R": "RandomNoise"},
            "widgets_values": [837190584809552, "randomize"],
        },
        {
            "id": 12,
            "type": "UNETLoader",
            "pos": {"0": 18, "1": 84},
            "size": {"0": 315, "1": 82},
            "flags": {},
            "order": 8,
            "mode": 0,
            "inputs": [],
            "outputs": [
                {
                    "name": "MODEL",
                    "type": "MODEL",
                    "links": [107],
                    "slot_index": 0,
                    "shape": 3,
                }
            ],
            "properties": {"Node name for S&R": "UNETLoader"},
            "widgets_values": ["artsyDream_v4FP8.safetensors", "fp8_e4m3fn"],
        },
        {
            "id": 28,
            "type": "String Literal",
            "pos": {"0": 29, "1": 779},
            "size": {"0": 317.8795471191406, "1": 202.01535034179688},
            "flags": {},
            "order": 9,
            "mode": 0,
            "inputs": [],
            "outputs": [
                {
                    "name": "STRING",
                    "type": "STRING",
                    "links": [47],
                    "slot_index": 0,
                    "shape": 3,
                }
            ],
            "properties": {"Node name for S&R": "String Literal"},
            "widgets_values": [
                "ArcaneFGTNRhigh A surreal and captivating artwork of Futuristic humanoid robot with a sleek pink and white design, wearing black goggles with glowing pink heart showing up on the visor screen, short pink hair, dark illustration comic book style, dynamic action pose"
            ],
        },
    ],
    "links": [
        [9, 8, 0, 9, 0, "IMAGE"],
        [12, 10, 0, 8, 1, "VAE"],
        [19, 16, 0, 13, 2, "SAMPLER"],
        [20, 17, 0, 13, 3, "SIGMAS"],
        [23, 5, 0, 13, 4, "LATENT"],
        [24, 13, 0, 8, 0, "LATENT"],
        [30, 22, 0, 13, 1, "GUIDER"],
        [37, 25, 0, 13, 0, "NOISE"],
        [47, 28, 0, 6, 1, "STRING"],
        [86, 6, 0, 60, 0, "CONDITIONING"],
        [87, 60, 0, 22, 1, "CONDITIONING"],
        [93, 61, 0, 17, 0, "MODEL"],
        [94, 61, 0, 22, 0, "MODEL"],
        [101, 70, 0, 5, 0, "INT"],
        [102, 70, 0, 61, 1, "INT"],
        [103, 71, 0, 5, 1, "INT"],
        [104, 71, 0, 61, 2, "INT"],
        [106, 72, 0, 61, 0, "MODEL"],
        [107, 12, 0, 72, 0, "MODEL"],
        [108, 11, 0, 6, 0, "CLIP"],
    ],
    "groups": [
        {
            "title": "Load FLUX.1",
            "bounding": [1, 2, 369, 693],
            "color": "#3f789e",
            "font_size": 24,
            "flags": {},
        },
        {
            "title": "Set Parameters",
            "bounding": [379, 0, 733, 526],
            "color": "#3f789e",
            "font_size": 24,
            "flags": {},
        },
        {
            "title": "FLUX Prompt",
            "bounding": [1, 704, 368, 318],
            "color": "#3f789e",
            "font_size": 24,
            "flags": {},
        },
        {
            "title": "Conditioning",
            "bounding": [379, 535, 732, 159],
            "color": "#3f789e",
            "font_size": 24,
            "flags": {},
        },
        {
            "title": "1st Pass",
            "bounding": [1119, 0, 402, 693],
            "color": "#3f789e",
            "font_size": 24,
            "flags": {},
        },
    ],
    "config": {},
    "extra": {
        "ds": {
            "scale": 1.1000000000000005,
            "offset": [-81.86623651795526, 25.786956051986607],
        }
    },
    "version": 0.4,
}


def main():
    """Test the ComfyUI workflow analyzer."""
    logger.info("Testing ComfyUI Workflow Analyzer...")

    # Analyze the workflow
    analysis = analyze_comfyui_workflow(workflow_data, logger)

    # Print results
    print("\n" + "=" * 60)
    print("COMFYUI WORKFLOW ANALYSIS RESULTS")
    print("=" * 60)

    print(f"Is ComfyUI Workflow: {analysis['is_comfyui_workflow']}")
    print(f"Node Count: {analysis['node_count']}")
    print(f"Node Types Found: {', '.join(analysis['node_types_found'])}")

    print("\n--- EXTRACTED PARAMETERS ---")
    for param, value in analysis["extracted_parameters"].items():
        print(f"{param}: {value}")

    print("\n--- MODEL INFO ---")
    model_info = analysis["model_info"]
    print(f"Main Model: {model_info.get('main_model')}")
    print(f"VAE: {model_info.get('vae')}")
    print(f"Text Encoders: {model_info.get('text_encoders')}")
    print(f"LoRAs: {model_info.get('loras')}")

    print("\n--- PROMPT INFO ---")
    prompt_info = analysis["prompt_info"]
    print(f"Positive Prompt: {prompt_info.get('positive_prompt')}")
    print(f"Guidance Scale: {prompt_info.get('guidance_scale')}")

    print("\n--- SAMPLING INFO ---")
    sampling_info = analysis["sampling_info"]
    for key, value in sampling_info.items():
        if value is not None:
            print(f"{key}: {value}")

    print("\n--- WORKFLOW CHAINS ---")
    for chain, types in analysis["workflow_chains"].items():
        if types:
            print(f"{chain}: {' -> '.join(types)}")

    if analysis["errors"]:
        print("\n--- ERRORS ---")
        for error in analysis["errors"]:
            print(f"ERROR: {error}")


if __name__ == "__main__":
    main()
