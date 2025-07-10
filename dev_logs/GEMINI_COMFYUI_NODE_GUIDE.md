# ComfyUI Node Dictionary Expansion Guide for Gemini

## 🎯 MISSION OBJECTIVE
Expand the ComfyUI Node Dictionary (`dataset_tools/comfyui_node_dictionary.json`) to handle more complex metadata parsing, particularly for images with 9000+ lines of ComfyUI workflow data.

## 🚨 CRITICAL RULES - DO NOT BREAK THESE

### ❌ ABSOLUTELY DO NOT MODIFY:
1. **File structure** - Keep the JSON format exactly as is
2. **Metadata section** (lines 1-7) - Only update `last_updated` date
3. **Category structure** - Don't rename existing categories 
4. **Existing node definitions** - Don't modify any existing entries unless adding missing parameters
5. **Parameter extraction patterns** - Don't change the syntax (e.g., `widgets_values[0]`, `inputs.text`)

### ✅ SAFE TO MODIFY/EXPAND:
1. **Add new node types** within existing categories
2. **Add new categories** if needed (follow existing structure)
3. **Expand parameter_extraction** for existing nodes (add missing parameters only)
4. **Add descriptions** and improve documentation
5. **Update version number** and last_updated date when making changes

## 📋 CURRENT STRUCTURE ANALYSIS

### File Format:
```json
{
  "metadata": { ... },           // DON'T TOUCH (except last_updated)
  "node_types": {
    "category_name": {           // Add new categories here
      "NodeTypeName": { ... }    // Add new nodes here
    }
  }
}
```

### Existing Categories:
- `text_encoding` - Text/prompt processing nodes
- `model_loading` - Model, LoRA, checkpoint loaders  
- `vae` - VAE encode/decode operations
- `sampling` - Sampling and generation control

### Current Stats:
- **414 lines total**
- **~330 node definitions** 
- **Coverage**: Basic ComfyUI nodes + some custom nodes (TensorArt, rgthree)

## 🎯 EXPANSION PRIORITIES

### 1. HIGH PRIORITY MISSING NODES
Look for these patterns in 9000+ line metadata and add definitions:

**Image Processing:**
- `ImageScale`, `ImageCrop`, `ImageResize`
- `ImageBatch`, `ImageFromBatch` 
- `ImageBlend`, `ImageComposite`

**Advanced Sampling:**
- `SamplerEulerAncestral`, `SamplerDPMPP_2M`
- `DDIMSampler`, `PLMSSampler`
- `UniPCMultistepSampler`

**ControlNet/IPAdapter:**
- `ControlNetLoader`, `ControlNetApply`
- `IPAdapterModelLoader`, `IPAdapterApply`

**Custom Nodes (Common Extensions):**
- ComfyUI-Manager nodes
- WAS Node Suite
- Impact Pack nodes
- Efficiency Nodes

### 2. NODE DEFINITION TEMPLATE
```json
"NodeTypeName": {
  "description": "Clear description of what this node does",
  "category": "appropriate_category",
  "inputs": ["input1", "input2"],        // List all inputs
  "outputs": ["OUTPUT_TYPE"],            // List all outputs  
  "parameter_extraction": {
    "param_name": "widgets_values[0]",   // For widget values
    "input_param": "inputs.param_name",  // For connected inputs
    "nested_param": "inputs.nested.value" // For nested structures
  }
}
```

### 3. PARAMETER EXTRACTION PATTERNS

**Widget Values (most common):**
- `widgets_values[0]` - First widget value
- `widgets_values[1:]` - All values from index 1 onwards
- `widgets_values` - All widget values as array

**Input Connections:**
- `inputs.parameter_name` - Direct input parameter
- `inputs.parameter_name.link_source` - Source of connected input
- `inputs.nested.parameter` - Nested input structures

**Complex Structures:**
- For arrays: `widgets_values[2:]` 
- For objects: `inputs.settings.value`
- For conditional: Use the most common pattern

## 🔍 HOW TO IDENTIFY MISSING NODES

### Step 1: Analyze Failing Metadata
Look for JSON structures like:
```json
{
  "id": 123,
  "type": "UnknownNodeType",
  "pos": [x, y],
  "inputs": [...],
  "outputs": [...],
  "widgets_values": [...]
}
```

### Step 2: Research the Node
- Check ComfyUI documentation
- Look at similar existing nodes in the dictionary
- Identify the node's purpose and category

### Step 3: Add Definition
Follow the template above, placing it in the appropriate category.

## 📝 EXAMPLE ADDITIONS

### Adding a New Image Processing Node:
```json
"ImageScale": {
  "description": "Scales image by specified factor or dimensions", 
  "category": "image_processing",
  "inputs": ["image"],
  "outputs": ["IMAGE"],
  "parameter_extraction": {
    "upscale_method": "widgets_values[0]",
    "width": "widgets_values[1]", 
    "height": "widgets_values[2]",
    "crop": "widgets_values[3]"
  }
}
```

### Adding a New Category:
```json
"image_processing": {
  "ImageScale": { ... },
  "ImageCrop": { ... },
  "ImageResize": { ... }
}
```

## 🎛️ TESTING YOUR ADDITIONS

After adding new nodes:
1. **Validate JSON** - Ensure no syntax errors
2. **Test parsing** - Use sample metadata containing the new nodes
3. **Check extraction** - Verify parameters are extracted correctly
4. **Document changes** - Update version and last_updated

## 📊 CURRENT COVERAGE GAPS

Based on common ComfyUI usage, we're missing:
- **60%** of image processing nodes
- **40%** of custom extension nodes  
- **30%** of advanced sampling nodes
- **70%** of ControlNet/IPAdapter nodes

## 🚀 GETTING STARTED

1. **First**, identify the specific node types causing parsing failures
2. **Then**, research those nodes to understand their structure
3. **Next**, add them following the template above
4. **Finally**, test with actual metadata to confirm they work

## 🎯 SUCCESS METRICS

Your additions are successful when:
- ✅ Previously unparsable images now show metadata
- ✅ Parameter extraction works correctly
- ✅ No JSON syntax errors
- ✅ Follows existing patterns consistently

---

**Remember**: Start small, test often, and follow the existing patterns exactly. The goal is to handle those massive 9000+ line metadata files that are currently failing to parse!