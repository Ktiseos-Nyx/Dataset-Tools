# dataset_tools/model_parsers/__init__.py

print("DEBUG: model_parsers/__init__.py: TOP OF FILE")

# Initialize names to None so they exist in the module's scope,
# preventing NameError if an import fails but a later import depends on the name existing.
BaseModelParser = None
ModelParserStatus = None
SafetensorsParser = None
GGUFParser = None  # Initialize GGUFParser as None

# --- Attempt to import base classes first ---
try:
    from .base_model_parser import BaseModelParser as _BaseModelParser_temp
    from .base_model_parser import ModelParserStatus as _ModelParserStatus_temp

    BaseModelParser = _BaseModelParser_temp
    ModelParserStatus = _ModelParserStatus_temp
    print(
        f"DEBUG: model_parsers/__init__.py: Successfully imported BaseModelParser ({BaseModelParser}) and ModelParserStatus ({ModelParserStatus})",
    )
except ImportError as e_base:
    print(
        f"DEBUG: model_parsers/__init__.py: FAILED to import from .base_model_parser: {e_base}",
    )
    import traceback

    traceback.print_exc()
    # BaseModelParser and ModelParserStatus remain None
except Exception as e_base_other:
    print(
        f"DEBUG: model_parsers/__init__.py: UNEXPECTED ERROR importing from .base_model_parser: {e_base_other}",
    )
    import traceback

    traceback.print_exc()
    # BaseModelParser and ModelParserStatus remain None


# --- Attempt to import SafetensorsParser ---
# Only proceed if BaseModelParser was successfully imported (is not None)
if BaseModelParser and ModelParserStatus:  # Check if base classes are available
    try:
        from .safetensors_parser import SafetensorsParser as _SafetensorsParser_temp

        SafetensorsParser = _SafetensorsParser_temp
        print(
            f"DEBUG: model_parsers/__init__.py: Successfully imported SafetensorsParser ({SafetensorsParser})",
        )
    except ImportError as e_safe:
        print(
            f"DEBUG: model_parsers/__init__.py: FAILED to import from .safetensors_parser: {e_safe}",
        )
        import traceback

        traceback.print_exc()
        # SafetensorsParser remains None
    except Exception as e_safe_other:
        print(
            f"DEBUG: model_parsers/__init__.py: UNEXPECTED ERROR importing from .safetensors_parser: {e_safe_other}",
        )
        import traceback

        traceback.print_exc()
        # SafetensorsParser remains None
else:
        print("DEBUG: model_parsers/__init__.py: Skipping SafetensorsParser import due to base class import failure or "
                  "them being None.")
    # SafetensorsParser remains None


# --- Attempt to import GGUFParser (NOW UNCOMMENTED) ---
# Only proceed if BaseModelParser was successfully imported (is not None)
if BaseModelParser and ModelParserStatus:  # Check if base classes are available
    try:
        from .gguf_parser import (
            GGUFParser as _GGUFParser_temp,
        )  # Assuming gguf_parser.py exists and defines GGUFParser

        GGUFParser = _GGUFParser_temp
        print(
            f"DEBUG: model_parsers/__init__.py: Successfully imported GGUFParser ({GGUFParser})",
        )
    except ImportError as e_gguf:
        # This will trigger if gguf_parser.py doesn't exist, or GGUFParser isn't defined,
        # or if gguf_parser.py has its own internal import errors.
        print(
            f"DEBUG: model_parsers/__init__.py: FAILED to import from .gguf_parser: {e_gguf}",
        )
        import traceback

        traceback.print_exc()
        # GGUFParser remains None
    except Exception as e_gguf_other:
        print(
            f"DEBUG: model_parsers/__init__.py: UNEXPECTED ERROR importing from .gguf_parser: {e_gguf_other}",
        )
        import traceback

        traceback.print_exc()
        # GGUFParser remains None
else:
    print(
        "DEBUG: model_parsers/__init__.py: Skipping GGUFParser import due to base class import failure or them being None.",
    )
    # GGUFParser remains None


# --- Define __all__ based on successful imports (where the name is not None) ---
_exportable_names = []
if BaseModelParser is not None:
    _exportable_names.append("BaseModelParser")
if ModelParserStatus is not None:
    _exportable_names.append("ModelParserStatus")
if SafetensorsParser is not None:
    _exportable_names.append("SafetensorsParser")
if GGUFParser is not None:  # Add GGUFParser if it was successfully imported
    _exportable_names.append("GGUFParser")

__all__ = _exportable_names

print(f"DEBUG: model_parsers/__init__.py: FINISHED. __all__ is {__all__}.")
# To see what's actually available for import from this module:
_actually_available = [
    name for name in __all__ if name in globals() and globals()[name] is not None
]
print(
    f"DEBUG: model_parsers/__init__.py: Names actually available and not None: {_actually_available}",
)
