# ComfyUI Extraction Fix Plan

## Problem Summary

The ComfyUI extraction system in Dataset-Tools has been experiencing critical issues with prompt extraction, specifically:

1. **Prompt Swapping**: Positive and negative prompts being extracted incorrectly, with positive prompts containing negative content like "embedding:negatives\IllusGen_Neg"
2. **Missing FLUX Prompts**: FLUX workflows missing positive prompts entirely (e.g., "woman", "cute kitty emote" examples)
3. **Architecture Confusion**: System was using vendored parsers instead of the modern extraction system

## Root Causes Identified

1. **Routing Issue**: ComfyUI files were being processed by vendored parsers (`vendored_sdpr.format.comfyui.py`) instead of the modern extraction system
2. **Content-Based Guessing**: Original negative prompt extraction used flawed content-based text detection instead of proper workflow link traversal
3. **FLUX Workflow Support**: Missing support for BasicGuider nodes and FLUX-specific workflow patterns

## Architecture Overview

```
Current System:
metadata_parser.py → ComfyUI_Simple.json → comfyui_extractors.py → ComfyUIExtractorManager

Fixed Routing:
- Disabled vendored parser: `# register_parser_class("ComfyUI", ComfyUI)` in metadata_parser.py:38
- Routes through parser definitions using modern extraction methods
```

## Key Files and Their Roles

### 1. `/metadata_parser.py` (Line 38)
- **Status**: ✅ FIXED
- **Change**: Disabled vendored ComfyUI parser registration
- **Impact**: Routes ComfyUI through modern extraction system

### 2. `/metadata_engine/extractors/comfyui_extractors.py`
- **Status**: 🔄 IN PROGRESS (Gemini working on manager system)
- **Key Methods**:
  - `_extract_legacy_prompt_from_workflow()` (Line 723-744)
  - `_extract_legacy_negative_prompt_from_workflow()` (Line 746-767)
  - `_find_legacy_text_from_main_sampler_input()` (Line 319-447)

### 3. `/parser_definitions/ComfyUI_Simple.json`
- **Status**: ✅ ACTIVE
- **Methods Used**:
  - `comfyui_extract_prompt_from_workflow`
  - `comfyui_extract_negative_prompt_from_workflow`

## Fixes Implemented

### ✅ Completed Fixes

1. **Routing Fix**: Disabled vendored parser registration
2. **Link Traversal**: Fixed prompt extraction to use proper workflow link following instead of content guessing
3. **FLUX Support**: Added BasicGuider and FluxGuidance node handling
4. **Fallback Logic**: Added "conditioning" input fallback for FLUX workflows

### 🔄 Current Work (Gemini)

Gemini is implementing a comprehensive ComfyUIExtractorManager system with:
- Specialized extractors for different node types
- Improved traversal logic using `trace_text_flow` method
- Modular architecture for easier maintenance

## Test Cases to Validate

### Priority Test Files
Based on user examples, we need to test:

1. **"woman" prompt file** - Should extract "woman" as positive prompt
2. **"cute kitty emote holding a sign that says 'Dusk Is Big Doodoo Dummy'"** - FLUX workflow test
3. **Files with "embedding:negatives" swapping** - Should have proper positive/negative separation
4. **Complex workflows** - Efficient Loader, String Literal patterns

### Test Scripts Available
- `find_woman_prompt.py` - Locates files with "woman" prompt
- `find_complex_workflows.py` - Finds Efficient Loader patterns  
- `test_specific_file.py` - Tests specific problematic files
- `debug_specific_workflow.py` - Analyzes workflow structure

## Implementation Strategy

### Phase 1: Complete Manager System (Gemini - IN PROGRESS)
- Finish ComfyUIExtractorManager implementation
- Simplify `_find_legacy_text_from_main_sampler_input` to delegate to `trace_text_flow`
- Test with existing problematic files

### Phase 2: FLUX Workflow Validation
- Test FLUX workflows with missing positive prompts
- Verify BasicGuider → T5TextEncode path works
- Ensure conditioning fallback works correctly

### Phase 3: Comprehensive Testing
- Run test scripts on full dataset
- Validate no regression in SDXL workflows
- Check complex patterns (Efficient Loader, String Literal)

## Debugging Tools

### Logging Strategy
- `[ComfyUI EXTRACTOR]` prefix for all extraction logs
- Node traversal debugging in `_find_legacy_text_from_main_sampler_input`
- Link analysis logging for workflow connections

### Key Debug Points
1. **Sampler Detection**: Log found sampler/guider nodes
2. **Link Following**: Show link traversal path
3. **Text Extraction**: Log final extracted text with preview
4. **FLUX Fallbacks**: Log when conditioning fallback triggers

## Expected Outcomes

### Success Criteria
1. ✅ Positive prompts contain actual positive content
2. ✅ Negative prompts contain negative content (or empty for FLUX)
3. ✅ No more "embedding:negatives" in positive prompts
4. ✅ FLUX workflows extract positive prompts correctly
5. ✅ Complex workflows (Efficient Loader) work properly

### Performance Targets
- Extraction success rate > 95% for standard SDXL workflows
- FLUX workflow positive prompt extraction > 90%
- No significant performance regression

## Risk Mitigation

### Potential Issues
1. **Manager System Complexity**: New system might introduce bugs
2. **Backward Compatibility**: Ensure existing workflows still work
3. **Performance**: Complex traversal might be slower

### Mitigation Strategies
1. **Gradual Rollout**: Test with subset of files first
2. **Fallback Logic**: Keep simple extraction as backup
3. **Comprehensive Testing**: Use existing test files for validation

## Next Steps

1. **Complete Manager System**: Wait for Gemini to finish implementation
2. **Integration Testing**: Test complete system with user's problem files
3. **Performance Validation**: Ensure no significant slowdown
4. **Documentation Update**: Update any user-facing documentation

## Notes

- User has been very patient and helpful with specific examples
- Gemini is taking 900+ seconds due to peak usage but making progress
- The core architecture fix (routing) is already in place
- Focus should be on completing the manager system and testing

---

*Last Updated: 2025-07-10*
*Status: Manager system in development, core routing fixed*