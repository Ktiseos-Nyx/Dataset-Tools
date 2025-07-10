# New ComfyUI Metadata Extractors Based on Discovered Nodes

## 🎯 Advanced Model Detection

### T5/FLUX Pipeline Detection
```python
# New extractor: advanced_text_encoding
"t5_text_encoding": {
    "pattern": r'"class_type":\s*"T5TextEncode"',
    "category": "advanced_models",
    "extraction": "t5_model_version, text_encoding_method"
}

"pixart_model": {
    "pattern": r'"class_type":\s*"PixArtCheckpointLoader".*?"ckpt_name":\s*"([^"]+)"',
    "category": "advanced_models", 
    "extraction": "model_architecture=PixArt, checkpoint_name=$1"
}
```

### Advanced VAE Detection
```python
"hf_remote_vae": {
    "pattern": r'"class_type":\s*"HFRemoteVAEDecode".*?"VAE_type":\s*"([^"]+)"',
    "category": "vae_processing",
    "extraction": "vae_type=$1, vae_source=huggingface_remote"
}
```

## 🎨 Workflow Technique Detection

### Multi-Stage Conditioning
```python
"timestep_conditioning": {
    "pattern": r'"class_type":\s*"ConditioningSetTimestepRange".*?"start":\s*([0-9.]+).*?"end":\s*([0-9.]+)',
    "category": "advanced_conditioning",
    "extraction": "conditioning_start=$1, conditioning_end=$2, technique=timestep_range"
}

"conditioning_combination": {
    "pattern": r'"class_type":\s*"ConditioningConcat|ConditioningCombine"',
    "category": "advanced_conditioning",
    "extraction": "technique=multi_conditioning"
}
```

### Custom Sampling Techniques
```python
"advanced_samplers": {
    "pattern": r'"class_type":\s*"(SamplerDPMPP_SDE|GlobalSampler|GITSScheduler)"',
    "category": "advanced_sampling",
    "extraction": "sampler_type=$1, sampling_technique=advanced"
}

"custom_scheduler": {
    "pattern": r'"class_type":\s*"GITSScheduler".*?"coeff":\s*([0-9.]+)',
    "category": "advanced_sampling", 
    "extraction": "scheduler=GITS, gits_coefficient=$1"
}
```

## 🔧 Post-Processing Detection

### Professional Effects
```python
"film_grain_processing": {
    "pattern": r'"class_type":\s*"ProPostFilmGrain".*?"grain_type":\s*"([^"]+)".*?"grain_power":\s*([0-9.]+)',
    "category": "post_processing",
    "extraction": "effect=film_grain, grain_type=$1, grain_intensity=$2"
}

"image_sharpening": {
    "pattern": r'"class_type":\s*"ImageSharpen".*?"alpha":\s*([0-9.]+)',
    "category": "post_processing",
    "extraction": "effect=sharpening, sharpen_amount=$1"
}
```

### Upscaling Detection
```python
"advanced_upscaling": {
    "pattern": r'"class_type":\s*"ImageUpscaleWithModel".*?"model_name":\s*"([^"]+)"',
    "category": "upscaling",
    "extraction": "upscale_model=$1, upscale_method=model_based"
}

"upscale_models": {
    "patterns": {
        "4x-UltraSharp": "upscale_factor=4x, model_type=sharp",
        "2x-AnimeSharpV2": "upscale_factor=2x, model_type=anime_sharp"
    }
}
```

## 🤖 AI Enhancement Detection

### TIPO Prompt Enhancement
```python
"tipo_enhancement": {
    "pattern": r'"class_type":\s*"TIPO".*?"tipo_model":\s*"([^"]+)".*?"temperature":\s*([0-9.]+)',
    "category": "ai_enhancement",
    "extraction": "prompt_enhancer=TIPO, tipo_model=$1, enhancement_temperature=$2"
}

"tipo_settings": {
    "pattern": r'"tag_length":\s*"([^"]+)".*?"nl_length":\s*"([^"]+)"',
    "category": "ai_enhancement",
    "extraction": "tag_length=$1, natural_language_length=$2"
}
```

### Classifier-Free Guidance Tweaks
```python
"uncond_zero": {
    "pattern": r'"class_type":\s*"Uncond Zero".*?"scale":\s*([0-9.]+)',
    "category": "cfg_tweaks",
    "extraction": "cfg_modification=uncond_zero, uncond_scale=$1"
}
```

## 📐 Layout & Dimension Detection

### Custom Dimension Helpers
```python
"dimension_helpers": {
    "pattern": r'"class_type":\s*"WidthHeightMittimi01".*?"Width":\s*([0-9]+).*?"Height":\s*([0-9]+)',
    "category": "dimensions",
    "extraction": "custom_dimensions=true, target_width=$1, target_height=$2"
}
```

## 🔄 Workflow Complexity Indicators

### Node Complexity Scoring
```python
"workflow_complexity": {
    "indicators": {
        "basic": ["KSampler", "VAEDecode", "CheckpointLoaderSimple"],
        "intermediate": ["ConditioningConcat", "ImageUpscaleWithModel", "SamplerCustom"],
        "advanced": ["TIPO", "T5TextEncode", "ProPostFilmGrain", "GITSScheduler"],
        "expert": ["Uncond Zero", "ConditioningSetTimestepRange", "HFRemoteVAEDecode"]
    }
}

"technique_tags": {
    "multi_stage_conditioning": ["ConditioningSetTimestepRange", "ConditioningConcat"],
    "advanced_text_encoding": ["T5TextEncode", "CLIPTextEncodeSDXL"],
    "professional_post_processing": ["ProPostFilmGrain", "ImageSharpen"],
    "ai_prompt_enhancement": ["TIPO", "ShowText|pysssss"],
    "custom_sampling": ["SamplerDPMPP_SDE", "GITSScheduler"]
}
```

## 🎮 Custom Node Ecosystem Detection

### Popular Custom Node Packs
```python
"custom_node_packs": {
    "pythonsssss": ["ShowText|pysssss"],
    "inspire_pack": ["GlobalSampler //Inspire"],
    "efficiency_nodes": ["HelperNodes_Steps"],
    "was_node_suite": ["SaveImagePlus"],
    "comfyui_controlnet_aux": ["TIPO"]
}
```

## 📊 New Metadata Fields to Add

### Database Schema Extensions
```sql
-- Advanced model info
advanced_model_type TEXT,
text_encoder_type TEXT,
vae_source TEXT,

-- Workflow complexity
workflow_complexity_score INTEGER,
technique_tags TEXT, -- JSON array
custom_node_packs TEXT, -- JSON array

-- Post-processing
post_processing_effects TEXT, -- JSON array
upscale_model TEXT,
upscale_factor TEXT,

-- AI enhancements
prompt_enhancement_method TEXT,
cfg_modifications TEXT,

-- Advanced sampling
custom_scheduler TEXT,
sampling_technique_level TEXT
```

## 🚀 Implementation Priority

### High Priority (Common & Valuable)
1. TIPO prompt enhancement detection
2. Advanced upscaling model detection
3. Multi-stage conditioning detection
4. Workflow complexity scoring

### Medium Priority (Specialized)
1. Custom scheduler detection
2. Post-processing effects
3. T5/FLUX pipeline detection
4. CFG modification detection

### Low Priority (Expert Level)
1. Custom node pack identification
2. HuggingFace integration detection
3. Advanced VAE routing
4. Professional film effects