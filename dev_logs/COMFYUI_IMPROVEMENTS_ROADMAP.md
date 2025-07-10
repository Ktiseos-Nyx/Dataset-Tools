# ComfyUI Extraction Improvements Roadmap

## 🎯 Current Status
- **Wildcard Workflows**: 100% success (6/6)
- **Modern Architectures**: 100% success (PixArt, FLUX tested)
- **Overall ComfyUI**: 58.3% success (improved from 41.7%)
- **KSamplerSelect Support**: ✅ Implemented workflow-only extraction

## 🚀 Next Phase Improvements (41.7% remaining failures)

### 1. **Enhanced Sampler Detection** 
```python
# Add to comfyui_extractors.py _find_legacy_text_from_main_sampler_input()
additional_sampler_types = [
    "SamplerCustom", "SamplerDPMPP_2M", "SamplerEuler", 
    "SamplerDPMPP_SDE", "SamplerLMS", "SamplerDDIM",
    "KSamplerX", "KSamplerLegacy", "AdvancedSampler"
]
```

### 2. **Complex Text Flow Patterns**
```python
# Enhance comfyui_traversal.py trace_text_flow()
additional_intermediate_nodes = [
    "TextConcat", "StringFormatter", "MultilineStringNode",
    "PromptScheduler", "DynamicPrompt", "ConditioningScheduler",
    "TextProcessorPlus", "SmartPrompt", "PromptMixer"
]
```

### 3. **Custom Node Ecosystem Support**
```python
# Add to workflow-only extraction method
custom_text_encoders = [
    "InspirePack.*TextEncode", "WAS.*TextEncode", 
    "Efficiency.*TextEncode", "SDXL.*TextEncode",
    "ComfyUI-Manager.*Text", "rgthree.*Text"
]
```

### 4. **Fallback Extraction Strategies**
```python
def _extract_with_multiple_strategies(self, data, target_input_name):
    strategies = [
        self._strategy_link_traversal,      # Current working method
        self._strategy_workflow_search,     # New KSamplerSelect method  
        self._strategy_text_node_scan,      # Brute force all text nodes
        self._strategy_widget_search,       # Search all widget_values
        self._strategy_primitive_search     # Find primitive string nodes
    ]
    
    for strategy in strategies:
        result = strategy(data, target_input_name)
        if result and result.strip():
            return result
    return ""
```

### 5. **API Format vs Workflow Format**
```python
# Handle both ComfyUI API format and workflow format better
def _normalize_workflow_format(self, data):
    if "prompt" in data and isinstance(data["prompt"], dict):
        # API format: {"prompt": {"1": {...}, "2": {...}}}
        return self._convert_api_to_workflow_format(data)
    elif "nodes" in data:
        # Workflow format: {"nodes": [...], "links": [...]}
        return data
    else:
        # Unknown format - try to auto-detect
        return self._auto_detect_format(data)
```

### 6. **Missing Link Recovery**
```python
# When links are missing/broken, reconstruct from node IDs
def _reconstruct_missing_links(self, data):
    nodes = data.get("nodes", [])
    reconstructed_links = []
    
    for node in nodes:
        inputs = node.get("inputs", [])
        for input_item in inputs:
            if "link" not in input_item and "node" in input_item:
                # Reconstruct link from node reference
                link_id = self._generate_synthetic_link_id()
                reconstructed_links.append([
                    link_id, input_item["node"], 0, 
                    node["id"], input_item.get("slot", 0), "CONDITIONING"
                ])
    
    if not data.get("links"):
        data["links"] = reconstructed_links
    return data
```

### 7. **Text Content Validation**
```python
def _validate_extracted_text(self, text, target_type):
    if not text or not text.strip():
        return False
    
    # Remove obvious non-prompts
    invalid_patterns = [
        r"^[\d\.,]+$",           # Just numbers
        r"^[TF](rue|alse)$",     # Boolean values
        r"^(enable|disable)$",   # Settings
        r"^[\w\-\.]+\.(safetensors|ckpt|pt)$"  # File names
    ]
    
    for pattern in invalid_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return False
    
    # Positive prompts should be descriptive
    if target_type == "positive" and len(text) < 10:
        return False
        
    return True
```

### 8. **Debug and Analysis Tools**
```python
# Add comprehensive workflow analysis
def analyze_failed_workflow(self, data, filepath):
    analysis = {
        "file": filepath,
        "format": self._detect_workflow_format(data),
        "node_count": len(data.get("nodes", [])),
        "link_count": len(data.get("links", [])),
        "sampler_nodes": self._find_all_samplers(data),
        "text_nodes": self._find_all_text_nodes(data),
        "custom_nodes": self._find_custom_nodes(data),
        "missing_links": self._detect_missing_links(data),
        "extraction_points": self._find_potential_extraction_points(data)
    }
    
    # Save analysis for debugging
    debug_file = f"debug_analysis_{Path(filepath).stem}.json"
    with open(debug_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    return analysis
```

### 9. **Multi-Model Architecture Detection**
```python
def _detect_model_architecture(self, data):
    nodes = self._get_all_nodes(data)
    
    # Architecture indicators
    if any("FLUX" in str(node) for node in nodes):
        return "flux"
    elif any("PixArt" in str(node) for node in nodes):
        return "pixart"  
    elif any("SD3" in str(node) for node in nodes):
        return "sd3"
    elif any("Auraflow" in str(node) for node in nodes):
        return "auraflow"
    elif any("HiDream" in str(node) for node in nodes):
        return "hidream"
    elif any("SDXL" in str(node) for node in nodes):
        return "sdxl"
    else:
        return "unknown"
```

### 10. **Performance Optimization**
```python
# Cache workflow analysis results
@lru_cache(maxsize=100)
def _analyze_workflow_structure(self, workflow_hash):
    # Expensive analysis cached by workflow content hash
    pass

# Parallel text extraction for multiple nodes
def _extract_text_parallel(self, text_nodes):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(self._extract_from_node, node) 
                  for node in text_nodes]
        results = [f.result() for f in futures if f.result()]
    return results
```

## 🎯 Implementation Priority

1. **HIGH**: Enhanced sampler detection (#1) - Should catch most remaining failures
2. **HIGH**: Fallback extraction strategies (#4) - Safety net for edge cases  
3. **MEDIUM**: Complex text flow patterns (#2) - Handle advanced workflows
4. **MEDIUM**: API/Workflow format handling (#5) - Format compatibility
5. **LOW**: Performance optimization (#10) - Speed improvements

## 📊 Expected Results
- **Target**: 85-90% success rate on all ComfyUI files
- **Modern Architectures**: Maintain 100% success  
- **Legacy Workflows**: Improve from 58% to 80%+
- **Custom Nodes**: Add support for popular ecosystems

## 🔧 Quick Wins (30 min implementation)
1. Add the additional sampler types to the detection list
2. Implement the text validation function  
3. Add the brute-force text node scanning fallback
4. Enable debug analysis for the 5 remaining failed files

This roadmap should get you to 85%+ success rate! 🚀