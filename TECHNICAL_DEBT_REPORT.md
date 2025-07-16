# Technical Debt & Issues Report
*Generated for Dataset Tools - Analysis Date: July 2025*

## 🚨 Critical Issues Found

### 1. Import Path Conflicts (FIXED)
- **Issue**: `FileLoadResult` class exists in two locations with different APIs
- **Location**: `dataset_tools/widgets.py` vs `dataset_tools/ui/widgets.py`
- **Impact**: ImportError for end users when installed via pip
- **Status**: ✅ **FIXED** - Updated import path in `main_window.py`
- **Applies to**: All branches (confirmed on `Themes-Lost-Dreams` branch too)

### 2. PyQt6 Theme Compatibility Issues (ACKNOWLEDGED)
- **Issue**: qt-material themes not 100% compatible with PyQt6/Qt6 elements
- **Location**: Mentioned in README.md, affects UI theming
- **Impact**: Visual inconsistencies, maintenance burden
- **Status**: 🔄 **ACTIVE ISSUE** - Considering Tkinter migration

## 📊 Code Complexity Hotspots

### Largest/Most Complex Files (Lines of Code)
1. **`comfyui_extractors.py`** - 1,325 lines 🔥
2. **`rule_engine.py`** - 1,238 lines 🔥
3. **`main_window.py`** - 1,156 lines ⚠️
4. **`metadata_engine/engine.py`** - 1,020 lines ⚠️
5. **`comfyui_extractor_manager.py`** - 958 lines ⚠️

### Ruff Configuration Complexity
- **285 per-file ignore rules** across 50+ files
- **Complexity limits increased** to silence warnings:
  - `max-branches = 30` (from default ~12)
  - `max-statements = 70` (from default ~50)
  - `max-locals = 20` (from default ~15)

## 🗑️ Legacy Code Accumulation

### Legacy/Backup Files Found
- `metadata_engine.py.legacy` - Old metadata engine
- `context_preparation_backup.legacy` - Backup context prep
- Multiple `.backup` files in extractors
- Build artifacts in `build/` directory

### Deprecated Patterns
- Files with "temp_", "tmp_", "_old" naming patterns
- Debug analysis files excluded from linting
- Emergency fixes mentioned in commit history

## 🏗️ Architecture Issues

### Threading Complexity
- PyQt6 threading model causes complexity in image loading
- Background operations require careful signal/slot management
- Thread-safety concerns with UI updates

### Module Organization
- **Monolithic files**: Several 1000+ line files
- **Circular dependencies**: Multiple try/except import blocks
- **Defensive imports**: Many optional dependency fallbacks

### Error Handling Patterns
- **192 broad exception handlers** found (`except Exception:`)
- Multiple `try/except ImportError` blocks for optional dependencies
- JSON parsing errors handled inconsistently

## 🎯 Specific Code Quality Issues

### Magic Numbers & Configuration
- Hard-coded values throughout codebase
- Complex ruff ignore configurations suggest underlying issues
- Multiple debug print statements allowed in specific files

### Unicode/Encoding Issues
- Multiple encoding fallback chains suggest historical Unicode problems
- Mojibake handling indicates past encoding challenges

### Bootstrap Debugging
- Print statements for debugging imports in `model_parsers/__init__.py`
- Suggests unstable module loading

## 🔧 Dependencies & External Issues

### Optional Dependencies
- Heavy use of try/except for imports (Pillow, qt-material, etc.)
- Model parsers may not be available
- PyExiv2 import issues on some platforms

### Vendored Code Maintenance
- Large vendored codebase from `stable-diffusion-prompt-reader`
- Adaptation layer adds complexity
- Multiple format parsers to maintain

## 📈 Recommendations

### Immediate Actions
1. **Fix Themes-Lost-Dreams branch** - Apply same FileLoadResult import fix
2. **Clean up legacy files** - Remove `.legacy` and backup files
3. **Reduce build artifacts** - Clean `build/` directory

### Medium-term Refactoring
1. **Break up monolithic files**:
   - Split `comfyui_extractors.py` (1,325 lines) into smaller modules
   - Refactor `rule_engine.py` (1,238 lines) into components
   - Modularize `main_window.py` (1,156 lines)

2. **Improve error handling**:
   - Replace broad `except Exception:` with specific exceptions
   - Standardize JSON parsing error handling
   - Create consistent error reporting patterns

3. **Simplify configuration**:
   - Reduce per-file ruff ignores by fixing underlying issues
   - Address complexity warnings instead of raising limits

### Strategic Considerations

#### Tkinter Migration Analysis
**Pros of migrating to Tkinter + ttkbootstrap**:
- ✅ Simpler threading model (you've proven this works in plural-chat)
- ✅ No qt-material compatibility issues
- ✅ Smaller dependency footprint
- ✅ Gorgeous modern themes with ttkbootstrap
- ✅ Better cross-platform consistency
- ✅ No PyQt6 licensing concerns for distribution

**Challenges**:
- ❌ Need to rebuild all UI components
- ❌ Re-implement background image loading with threading
- ❌ Lose some advanced PyQt6 widgets
- ❌ Significant development time investment

**Migration Strategy** (if pursued):
1. **Phase 1**: Create parallel Tkinter UI for basic functionality
2. **Phase 2**: Implement thread-safe image loading (using plural-chat patterns)
3. **Phase 3**: Port metadata display components
4. **Phase 4**: Add ttkbootstrap theming
5. **Phase 5**: Feature parity and testing

## 🎨 ttkbootstrap Integration Potential

Based on your enthusiasm for ttkbootstrap, a Tkinter migration could solve multiple issues:
- **Theming issues** → Modern, consistent themes
- **Threading complexity** → Simpler model you already know
- **Dependency bloat** → Lighter weight
- **Cross-platform consistency** → Better than PyQt6

The metadata viewer is a perfect candidate for ttkbootstrap - it's primarily forms, lists, and text display which ttkbootstrap handles beautifully.

## 📝 Conclusion

The codebase is **functional but carrying significant technical debt**. The PyQt6 theming issues combined with the complexity burden suggest a Tkinter migration could be a strategic win - especially given your proven threading expertise from plural-chat.

**Priority order**:
1. 🔥 Fix import issues on other branches (immediate)
2. 🧹 Clean up legacy files (quick wins)  
3. 🏗️ Consider Tkinter + ttkbootstrap migration (strategic)
4. 📊 Gradual complexity reduction (ongoing)