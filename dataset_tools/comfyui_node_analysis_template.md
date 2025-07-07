# ComfyUI Node Dictionary Analysis Template

## Instructions for Gemini

You are analyzing ComfyUI workflow files to build a comprehensive node dictionary. For each workflow file provided, extract ALL unique node types and their properties according to this template.

## Analysis Format

For each workflow file, provide output in this EXACT JSON structure:

```json
{
  "file_analyzed": "filename.json",
  "analysis_timestamp": "2025-01-07T20:30:00Z",
  "nodes_discovered": {
    "NodeTypeName": {
      "category": "sampling|conditioning|model_loading|image_processing|utility|custom",
      "frequency": 1,
      "inputs": {
        "input_name": {
          "type": "MODEL|CONDITIONING|LATENT|IMAGE|STRING|INT|FLOAT|COMBO|BOOLEAN",
          "required": true,
          "default_value": "value_if_found",
          "connection_source": ["node_id", "output_index"],
          "observed_values": ["list", "of", "actual", "values", "seen"]
        }
      },
      "outputs": ["OUTPUT_TYPE1", "OUTPUT_TYPE2"],
      "widget_values": {
        "widget_name": {
          "type": "STRING|INT|FLOAT|BOOLEAN|COMBO",
          "observed_values": ["value1", "value2"]
        }
      },
      "connection_patterns": {
        "typical_inputs_from": ["CheckpointLoaderSimple", "CLIPTextEncode"],
        "typical_outputs_to": ["VAEDecode", "SaveImage"]
      },
      "metadata": {
        "title": "Human readable title from _meta",
        "source": "core|custom_node|unknown",
        "aliases": ["AlternativeNodeName1", "AlternativeNodeName2"]
      }
    }
  },
  "statistics": {
    "total_nodes_in_file": 15,
    "unique_node_types": 8,
    "new_node_types_discovered": 2
  }
}
```

## Specific Analysis Instructions

### 1. Node Type Identification
- Extract the `class_type` field from each node
- Count frequency of each node type
- Identify if it's a core ComfyUI node or custom node

### 2. Input Analysis
For each node's `inputs` object:
- **Connection inputs**: `["node_id", output_index]` format
- **Direct value inputs**: Actual values (strings, numbers, booleans)
- **Widget inputs**: UI-controlled values
- Determine if input is required (present in most instances)

### 3. Output Analysis
- Infer output types from what other nodes connect to
- Count output connections to determine output count

### 4. Category Classification
Use these categories:
- **sampling**: KSampler, SamplerCustom, etc.
- **conditioning**: CLIPTextEncode, CLIPTextEncodeSDXL, etc.  
- **model_loading**: CheckpointLoaderSimple, LoraLoader, etc.
- **image_processing**: VAEDecode, VAEEncode, ImageScale, etc.
- **utility**: SaveImage, LoadImage, etc.
- **custom**: Any non-standard ComfyUI nodes

### 5. Connection Pattern Analysis
Track which node types typically connect to each other:
- What nodes usually provide inputs to this node type
- What nodes usually receive outputs from this node type

### 6. Value Pattern Recognition
For inputs that take direct values, track:
- Common values (for dropdowns/combos)
- Typical ranges (for numbers)
- String patterns (for file paths, etc.)

## Example Analysis

Here's an example of analyzing a KSampler node:

```json
{
  "KSampler": {
    "category": "sampling",
    "frequency": 3,
    "inputs": {
      "model": {
        "type": "MODEL",
        "required": true,
        "connection_source": ["resource-stack", 0],
        "observed_values": []
      },
      "positive": {
        "type": "CONDITIONING", 
        "required": true,
        "connection_source": ["6", 0],
        "observed_values": []
      },
      "seed": {
        "type": "INT",
        "required": false,
        "default_value": null,
        "observed_values": [359825400, 1531035486, -1]
      },
      "steps": {
        "type": "INT", 
        "required": false,
        "default_value": 20,
        "observed_values": [30, 25, 20]
      },
      "cfg": {
        "type": "FLOAT",
        "required": false, 
        "default_value": 7.0,
        "observed_values": [7.0, 8.0, 6.5]
      },
      "sampler_name": {
        "type": "COMBO",
        "required": false,
        "default_value": "euler",
        "observed_values": ["euler_ancestral", "euler", "dpmpp_2m"]
      }
    },
    "outputs": ["LATENT"],
    "connection_patterns": {
      "typical_inputs_from": ["CheckpointLoaderSimple", "CLIPTextEncode", "EmptyLatentImage"],
      "typical_outputs_to": ["VAEDecode", "KSampler"]
    },
    "metadata": {
      "title": "KSampler",
      "source": "core",
      "aliases": []
    }
  }
}
```

## Special Instructions

1. **Handle Custom Nodes**: Pay special attention to nodes with unusual names or prefixes (smZ, MZ_, etc.)

2. **URN Patterns**: Note when inputs contain `urn:air:` patterns - these are CivitAI resources

3. **Connection Arrays**: When you see `["node_id", index]`, that's a connection to another node's output

4. **Meta Fields**: Extract human-readable titles from `_meta.title` when available

5. **Widget vs Input**: Distinguish between node inputs (connections/values) and widget values (UI controls)

## Batch Processing Instructions

When analyzing multiple files:
1. Merge results across files
2. Aggregate frequency counts
3. Combine observed values lists
4. Identify patterns across workflows
5. Note which nodes appear together frequently

## Output Requirements

- Provide one JSON output per file analyzed
- Use consistent naming and structure
- Include statistics summary
- Flag any unusual or unrecognized patterns
- Highlight new node types not seen before

This template will help build a comprehensive ComfyUI node dictionary for improving metadata extraction!