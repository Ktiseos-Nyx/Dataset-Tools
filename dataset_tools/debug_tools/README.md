# Debug Tools & Test Scripts

This directory contains debugging and testing utilities for the Dataset Tools metadata engine.

## 🔧 Debug Scripts

### Core Engine Testing
- `debug_extraction_methods.py` - Test ComfyUI extraction methods
- `debug_parser_matching.py` - Debug parser detection and matching
- `debug_jpeg_metadata.py` - Debug JPEG EXIF metadata extraction

### Format-Specific Testing
- `test_a1111_*.py` - A1111 format testing and validation
- `test_civitai_*.py` - CivitAI format testing and mojibake debugging
- `test_comfyui_*.py` - ComfyUI workflow extraction testing
- `test_t5_*.py` - T5 detection and parsing validation

### Unicode & Encoding
- `test_unicode_usercomment.py` - Unicode handling validation
- `test_mojibake_debug.py` - Mojibake detection and fixing
- `enhanced_exif_reader.py` - Enhanced EXIF reading utilities
- `extract_full_usercomment.py` - UserComment extraction debugging

### Integration Testing
- `test_enhanced_integration.py` - Full pipeline integration tests
- `test_final_output.py` - End-to-end output validation
- `test_ui_file.py` - UI integration testing

### Analysis Tools
- `test_workflow_analysis.py` - ComfyUI workflow analysis
- `test_airs.py` - CivitAI airs array analysis
- `test_extrametadata.py` - CivitAI extraMetadata parsing

## 🚀 Usage

Most scripts can be run directly:
```bash
cd debug_tools
python test_final_output.py
python debug_extraction_methods.py
```

Some scripts may require sample files in specific locations. Check individual script headers for requirements.

## 📝 Contributing

When adding new debug scripts:
1. Use descriptive names starting with `test_` or `debug_`
2. Include docstrings explaining the script's purpose
3. Add error handling and clear output messages
4. Document any required sample files or setup

## ⚠️ Note

These are development/debugging tools and not part of the main application. They're kept for troubleshooting, validation, and future development work.