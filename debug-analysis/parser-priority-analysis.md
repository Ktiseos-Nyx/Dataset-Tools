# Parser Priority Analysis - 2025-07-04

## Issue
JSON parsers are being skipped in favor of vendored SDPR, contrary to intended priority order.

## Key Findings

### Current Parser Flow
The codebase runs **two separate parsing systems in parallel**:

1. **Primary**: The old `metadata_parser.py` that calls vendored SDPR directly
2. **Secondary**: The new `metadata_engine/` system that's built but not yet integrated

**The new metadata engine is not currently being used** in the main UI parsing workflow.

### Parser Order and Priority Logic

#### 1. Main Entry Point - Parser Order Decision
**File:** `dataset_tools/metadata_parser.py`
- **Lines 358-443**: Main `parse_metadata()` function
- **Line 358**: First attempts vendored SDPR parsing via `ImageDataReader`
- **Lines 444-480**: Falls back to standard pyexiv2 parsing if AI parsing fails
- **Current priority order:**
  1. **Vendored SDPR parsers** (lines 358-443)
  2. **Standard pyexiv2 metadata** (lines 444-480)

#### 2. New JSON-Based Parser Registry
**File:** `dataset_tools/metadata_engine/engine.py`
- **Lines 149-155**: `_sort_definitions_by_priority()` - Sorts JSON parser definitions by priority (highest first)
- **Lines 167-171**: `_find_matching_parser()` - Iterates through sorted definitions to find first match
- **Lines 107-115**: Decides between JSON instructions vs Python class fallback

#### 3. Parser Registry System
**File:** `dataset_tools/metadata_engine/parser_registry.py`
- **Lines 6-14**: `register_parser_class()` and `get_parser_class_by_name()` - Central registry for Python-based parsers

#### 4. Vendored SDPR Parser Order
**File:** `dataset_tools/vendored_sdpr/image_data_reader.py`
- **Lines 53-63**: `PARSER_CLASSES_PNG` - PNG parser priority order:
  1. ComfyUI
  2. CivitaiFormat  
  3. A1111
  4. EasyDiffusion
  5. InvokeAI
  6. NovelAI
  7. SwarmUI
  8. MochiDiffusionFormat

- **Lines 65-73**: `PARSER_CLASSES_JPEG_WEBP` - JPEG/WebP parser priority order:
  1. MochiDiffusionFormat
  2. CivitaiFormat
  3. EasyDiffusion
  4. A1111
  5. SwarmUI

### Integration Point
**File:** `dataset_tools/ui/main_window.py`
- **Line 551**: Calls `parse_metadata()` directly, not the new engine

## Solution Path
To implement true JSON-first with vendored fallback, the integration point needs to be modified at line 551 in `main_window.py` to use the new metadata engine instead of the old `parse_metadata()` function.

## Test Case
- **Image**: Forge version "f1.7.0-v1.10.1RC-latest-2190-g8731f1e9"
- **Current behavior**: Parsed as A1111 webUI via vendored SDPR
- **Expected behavior**: Should use JSON parsers first, then fall back to vendored if no match

## Next Steps
1. Check Forge detection rules in JSON parsers
2. Verify parser registry loading and priority ordering
3. Integrate new metadata engine into main UI workflow