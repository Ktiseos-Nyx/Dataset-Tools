# Weird ComfyUI Workflows: A Documentary of User Crimes Against Sanity

## Overview
This document catalogs the various ways ComfyUI users have decided to make their workflows as complex as humanly possible, thereby breaking our perfectly reasonable parsers.

## Current Known Crimes Against Parsing

### Crime #1: The Reroute Node Spaghetti Factory
**File:** `Comfyui_00491_.jpg`
**Crime:** Using multiple reroute nodes and dynamic input connections like `["266:1", 0]` and `["266:0", 0]`
**What They Did:** Instead of directly connecting samplers to encoders, they created a web of reroute nodes that would make a spider jealous
**Impact:** Our traversal methods can't follow the bread crumbs through this maze
**Status:** Currently only extracting `loras: []` instead of the full workflow

### Crime #2: The Grouped Workflow Node Madness
**File:** Same victim as above
**Crime:** Using grouped workflow nodes like `"workflow>STEPS / CFG"` with sub-nodes
**What They Did:** Decided that normal parameter passing wasn't fancy enough, so they created grouped parameter nodes
**Impact:** Parser doesn't understand these grouped parameter structures
**Symptoms:** Missing steps, cfg_scale, and other critical parameters

### Crime #3: The Multiple Sampler Confusion
**File:** You guessed it, same file
**Crime:** Having both `KSamplerAdvanced` (node 184) AND `KSampler` (node 300) in the same workflow
**What They Did:** Apparently one sampler wasn't enough, they needed TWO
**Impact:** Parser doesn't know which one is the "main" sampler
**Current Behavior:** Probably getting confused about which sampler to use as the primary

### Crime #4: The Custom Node Ecosystem Explosion
**File:** Multiple files in the wild
**Crime:** Using every custom node known to humanity
**Examples Found:**
- `HelperNodes_Steps`
- `Cfg Literal` 
- `GlobalSampler //Inspire`
- `WidthHeightMittimi01`
- `HFRemoteVAEDecode`
- `SaveImagePlus`
- `UltralyticsDetectorProvider`
- `FaceDetailer`
**Impact:** Our node type lists become outdated faster than iPhone models

## The Actual EXIF Data (Evidence of the Crime)
```json
{
  "prompt": {
    "160": {
      "inputs": {
        "text_g": "illustration, expressionism style, high quality, A Dog sitting underneath a lemon tree during a rainstorm, best quality, very detailed"
      },
      "class_type": "CLIPTextEncodeSDXL"
    },
    "162": {
      "inputs": {
        "text_g": "low quality, bad quality, bright light, watermark, low details, jpg artefacts, closeup, realistic, photograph"  
      },
      "class_type": "CLIPTextEncodeSDXL"
    },
    "184": {
      "inputs": {
        "steps": ["266:1", 0],
        "cfg": ["266:0", 0],
        "sampler_name": "dpmpp_3m_sde_gpu",
        "scheduler": "sgm_uniform"
      },
      "class_type": "KSamplerAdvanced"
    },
    "300": {
      "inputs": {
        "steps": ["266:1", 0], 
        "cfg": ["266:0", 0],
        "sampler_name": "dpmpp_3m_sde_gpu"
      },
      "class_type": "KSampler"
    },
    "266:0": {
      "inputs": {"float": 6.500000000000001},
      "class_type": "Cfg Literal"
    },
    "266:1": {
      "inputs": {"steps": 35},
      "class_type": "HelperNodes_Steps" 
    }
  }
}
```

## Solutions Needed (For Future Claude or Gemini)

### Priority 1: Dynamic Connection Resolver
Need to implement a connection resolver that can:
1. Follow array-style connections like `["266:1", 0]`
2. Understand that `266:1` means "node 266, output 1"
3. Recursively traverse until finding the actual value

### Priority 2: Multi-Sampler Detection Logic
Need smarter logic to:
1. Identify which sampler is the "primary" one
2. Handle workflows with multiple sampling stages
3. Maybe use the one connected to the final output?

### Priority 3: Grouped Node Understanding
Need to parse grouped workflow nodes properly:
1. Understand the `workflow>STEPS / CFG` syntax
2. Extract values from sub-nodes within groups
3. Map grouped parameters back to standard parameter names

### Priority 4: Custom Node Registry
Need a system to:
1. Automatically detect unknown custom node types
2. Update parser definitions with new node types
3. Provide fallback extraction methods for unknown nodes

## Current Parser Status
- ✅ Correctly identifies as ComfyUI JPEG 
- ✅ Extracts basic loras (empty array)
- ❌ Fails to extract prompt/negative_prompt
- ❌ Fails to extract steps, cfg_scale, seed
- ❌ Fails to extract model, dimensions
- ❌ Doesn't handle dynamic connections

## Moral of the Story
ComfyUI users: "Let's make the most complex workflow possible!"
Our Parser: "Why do you hurt me like this?"

## Note to Future Self/Gemini
When you see a ComfyUI workflow that only extracts `loras: []`, check if it has:
1. Dynamic input connections with array syntax
2. Multiple samplers
3. Grouped workflow nodes  
4. Reroute node spaghetti

If yes, you've found another creative workflow that needs the advanced connection resolver!

---
*Created in frustration after discovering that users can't just make simple, linear workflows like normal people.*