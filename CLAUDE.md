# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Commands

### Development Tools
- **Install for development**: `pip install -e .`
- **Run application**: `dataset-tools` or `python -m dataset_tools.main`
- **Install dependencies**: `pip install .` (installs all required dependencies from pyproject.toml)

### Testing and Quality Assurance
- **Run tests**: `pytest` (uses test configuration from pyproject.toml)
- **Type checking**: `mypy .` (configuration in mypy.ini)
- **Linting**: `ruff check .` (extensive configuration in pyproject.toml)
- **Formatting**: `ruff format .`
- **Personal linting tools**: Install with `pip install -e .[kn]` for ruff and pylint

### Build and Distribution
- **Build package**: `python -m build` (uses setuptools with setuptools_scm for versioning)
- **Install from source**: `pip install .` after cloning

## Architecture Overview

### Core Structure
This is a PyQt6-based desktop application for viewing and editing AI-generated image metadata. The application follows a modular architecture:

**Main Components:**
- `dataset_tools/main.py` - Application entry point with CLI argument parsing
- `dataset_tools/ui/` - PyQt6 user interface components and theme management
- `dataset_tools/metadata_engine/` - Core metadata parsing and extraction system
- `dataset_tools/file_readers/` - File format handlers for images, text, and schemas
- `dataset_tools/model_parsers/` - Parsers for AI model files (safetensors, GGUF)

### Metadata Engine Architecture
The metadata engine is the heart of the application with priority-based detection:

**Key Components:**
- `metadata_engine/engine.py` - Main parsing orchestrator
- `metadata_engine/extractors/` - Format-specific extractors for different AI tools
- `metadata_engine/rule_engine.py` - Rule-based metadata processing
- `metadata_engine/template_system.py` - Template-based field extraction
- `parser_definitions/*.json` - Declarative parser configurations for 25+ AI formats

**Supported AI Platforms:**
- A1111/Forge WebUI, ComfyUI, NovelAI, Midjourney, InvokeAI, Fooocus, Easy Diffusion, CivitAI
- Advanced ComfyUI workflow analysis with node traversal and connection mapping
- Specialized extractors for custom nodes and complex workflows

### Vendored Code
- `dataset_tools/vendored_sdpr/` - Adapted code from stable-diffusion-prompt-reader
- Uses fallback parsing when specialized parsers fail
- Contains format-specific parsers for maximum compatibility

### Configuration and Theming
- Extensive ruff configuration in pyproject.toml with per-file ignores for complex files
- Theme system using qt-material with custom theme management
- Font management system with bundled fonts in `dataset_tools/fonts/`

### File Organization
- `tests/` - Test suite with sample data files for various AI formats
- `logs/` - Application logging output
- `config/` and `dataset_tools/config/` - Configuration files including rules.toml

## Development Notes

### Code Quality
- Uses extensive ruff configuration with 25+ rule categories enabled
- Many files have specific ignores due to complexity (see pyproject.toml per-file-ignores)
- MyPy type checking with pydantic plugin
- Comprehensive pytest configuration with deprecation warning filtering

### Dependencies
- Requires Python 3.10+
- Core deps: PyQt6, Pillow, pydantic, rich, toml, pyexiv2, piexif, qt-material
- Dev deps: pytest, mypy, types packages
- Uses setuptools_scm for automatic versioning from git tags

### Entry Points
- Console script: `dataset-tools` → `dataset_tools.main:main`
- Module execution: `python -m dataset_tools.main`
- Supports CLI arguments including `--log-level` for debugging

### Testing
- Test data in `tests/data/` includes samples from various AI platforms
- Comprehensive metadata parsing tests
- UI component testing