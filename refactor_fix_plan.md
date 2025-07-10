# ComfyUI Extractor Refactoring - Fix Plan

## 1. Current Situation

The refactoring of `comfyui_extractors.py` into a facade/manager pattern is structurally complete, but has resulted in a **silent, critical failure**. 

**Symptom:** When loading a ComfyUI PNG, the UI displays no prompt, no generation details, and an empty workflow (`{}`).

**Root Cause:** The system is failing to correctly locate the list of `nodes` within the parsed workflow JSON. The helper function responsible for this returns an empty dictionary, which starves all subsequent extraction logic of data, causing them all to fail silently.

## 2. The Core Bug Location

The primary point of failure is the `get_nodes_from_data` method in:
`dataset_tools/metadata_engine/extractors/comfyui_traversal.py`

This function makes incorrect assumptions about the top-level structure of the JSON data and fails to find the nodes.

## 3. Action Plan: A Step-by-Step Guide to the Fix

Here is a clear plan to diagnose and resolve the issues.

### Step 1: Diagnose the JSON Structure

The first step is to see what the JSON data actually looks like.

**Action:** Add a temporary `print()` statement to the `get_nodes_from_data` function in `comfyui_traversal.py`.

```python
# In: dataset_tools/metadata_engine/extractors/comfyui_traversal.py

def get_nodes_from_data(self, data: dict) -> dict | list:
    """Helper method to extract nodes from data..."""
    # --- ADD THIS LINE --- #
    print(f"[DIAGNOSTIC] get_nodes_from_data received keys: {list(data.keys())}")
    
    if isinstance(data, dict) and "nodes" in data:
        # ... rest of the function
```

Run the application, load a ComfyUI PNG, and observe the diagnostic output in the console. This will reveal the correct path to the node list (e.g., `['workflow', 'extra_pnginfo']`, etc.).

### Step 2: Fix the `get_nodes_from_data` Method

Once the correct key/path is known from Step 1, update the function to handle it.

**Action:** Modify `get_nodes_from_data` to correctly extract the node list.

**Example:** If the diagnostic print reveals the nodes are in a top-level key called `workflow`, the fix would be:

```python
# In: dataset_tools/metadata_engine/extractors/comfyui_traversal.py

def get_nodes_from_data(self, data: dict) -> dict | list:
    """Helper method to extract nodes from data..."""
    # (You can remove the diagnostic print now)

    # Handle new case based on diagnostic output
    if isinstance(data, dict) and "workflow" in data and isinstance(data["workflow"], dict):
        return data["workflow"].get("nodes", {})

    # Existing cases
    if isinstance(data, dict) and "nodes" in data:
        return data["nodes"]
    if isinstance(data, dict) and "prompt" in data:
        return data["prompt"]
    if isinstance(data, dict) and all(isinstance(v, dict) for v in data.values()):
        return data
    
    return {} # Fallback
```

### Step 3: Re-Wire the Facade for Parameters

The current logic in the facade methods is broken. It relies on a faulty auto-detection system. The methods need to be rewritten to call the specialized modules directly.

**Action:** Replace the `_extract_legacy_workflow_parameters` method in `dataset_tools/metadata_engine/extractors/comfyui_extractors.py` with the following robust implementation.

```python
# In: dataset_tools/metadata_engine/extractors/comfyui_extractors.py

def _extract_legacy_workflow_parameters(
    self,
    data: Any,
    method_def: MethodDefinition,
    context: ContextData,
    fields: ExtractedFields,
) -> dict[str, Any]:
    """Legacy workflow parameters - NEW BRUTE-FORCE WIRING."""
    data = self._parse_json_data(data)
    if not isinstance(data, dict):
        return {}

    self.logger.debug("[FACADE] Extracting parameters using direct-call method.")
    
    all_params = {}

    # 1. Get generic sampler parameters (seed, steps, etc.)
    generic_params = self.manager._extract_generic_parameters(data)
    all_params.update(generic_params)

    # 2. Get model information (assuming sdxl extractor is generic enough)
    model_info = self.manager.sdxl._extract_model_info(data, {}, {}, {})
    all_params.update(model_info)

    # 3. Get LoRA information
    loras = self._extract_legacy_all_loras(data, {}, {}, {})
    if loras:
        all_params['loras'] = loras

    # 4. Get parameters from other specific ecosystems if needed
    efficiency_params = self.manager.efficiency._extract_sampler_params(data, {}, {}, {})
    all_params.update(efficiency_params)

    return {k: v for k, v in all_params.items() if v is not None}
```

### Step 4: Re-Wire the Facade for Prompts

Similarly, the prompt extraction methods need to be fixed to use the most reliable traversal logic directly.

**Action:** Replace the `_extract_legacy_prompts` and `_extract_legacy_negative_prompt_from_workflow` methods in `comfyui_extractors.py` with the implementations below.

**Positive Prompt:**
```python
# In: dataset_tools/metadata_engine/extractors/comfyui_extractors.py

def _extract_legacy_prompts(
    self,
    data: Any,
    method_def: MethodDefinition,
    context: ContextData,
    fields: ExtractedFields,
) -> str:
    """Legacy prompt extraction - NEW BRUTE-FORCE WIRING."""
    data = self._parse_json_data(data)
    if not isinstance(data, dict):
        return ""

    nodes = self.manager.traversal.get_nodes_from_data(data)
    if not nodes:
        return ""

    # Find the first positive text node and trace its flow
    for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
        if isinstance(node_data, dict) and self.manager.node_checker.is_text_node(node_data):
            text_value = node_data.get("widgets_values", [""])[0]
            if not self.manager.node_checker.looks_like_negative_prompt(text_value):
                traced_text = self.manager.traversal.trace_text_flow(nodes, str(node_id))
                if traced_text:
                    return traced_text
    return ""
```

**Negative Prompt:**
```python
# In: dataset_tools/metadata_engine/extractors/comfyui_extractors.py

def _extract_legacy_negative_prompt_from_workflow(
    self,
    data: Any,
    method_def: MethodDefinition,
    context: ContextData,
    fields: ExtractedFields,
) -> str:
    """Legacy negative prompt from workflow - NEW BRUTE-FORCE WIRING."""
    data = self._parse_json_data(data)
    if not isinstance(data, dict):
        return ""

    nodes = self.manager.traversal.get_nodes_from_data(data)
    if not nodes:
        return ""

    # Find the first negative text node and trace its flow
    for node_id, node_data in (nodes.items() if isinstance(nodes, dict) else enumerate(nodes)):
        if isinstance(node_data, dict) and self.manager.node_checker.is_text_node(node_data):
            text_value = node_data.get("widgets_values", [""])[0]
            if self.manager.node_checker.looks_like_negative_prompt(text_value):
                traced_text = self.manager.traversal.trace_text_flow(nodes, str(node_id))
                if traced_text:
                    return traced_text
    return ""
```

## Summary for AI

1.  **Diagnose & Fix `get_nodes_from_data`**: Add a print statement to find the correct key for the node list in the workflow JSON, then update the function to use it.
2.  **Re-wire Facade Methods**: Replace the implementations for parameter and prompt extraction in `comfyui_extractors.py` with the robust, direct-call versions provided above. This bypasses the broken auto-detection logic.
