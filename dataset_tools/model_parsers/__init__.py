# dataset_tools/model_parsers/__init__.py
from dataset_tools.logger import debug_message

debug_message("model_parsers/__init__.py: TOP OF FILE")

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
    debug_message(
        "model_parsers/__init__.py: Successfully imported BaseModelParser (%s) and ModelParserStatus (%s)",
        BaseModelParser,
        ModelParserStatus,
    )
except ImportError as e_base:
    debug_message(
        "model_parsers/__init__.py: FAILED to import from .base_model_parser: %s",
        e_base,
        exc_info=True,
    )
except Exception as e_base_other:  # Keep broad for bootstrap phase
    debug_message(
        "model_parsers/__init__.py: UNEXPECTED ERROR importing from .base_model_parser: %s",
        e_base_other,
        exc_info=True,
    )


# --- Attempt to import SafetensorsParser ---
if BaseModelParser and ModelParserStatus:
    try:
        from .safetensors_parser import SafetensorsParser as _SafetensorsParser_temp

        SafetensorsParser = _SafetensorsParser_temp
        debug_message(
            "model_parsers/__init__.py: Successfully imported SafetensorsParser (%s)",
            SafetensorsParser,
        )
    except ImportError as e_safe:
        debug_message(
            "model_parsers/__init__.py: FAILED to import from .safetensors_parser: %s",
            e_safe,
            exc_info=True,
        )
    except Exception as e_safe_other:  # Keep broad for bootstrap phase
        debug_message(
            "model_parsers/__init__.py: UNEXPECTED ERROR importing from .safetensors_parser: %s",
            e_safe_other,
            exc_info=True,
        )
else:
    debug_message(
        "model_parsers/__init__.py: Skipping SafetensorsParser import due to base class import failure or "
        "them being None."
    )

# --- Attempt to import GGUFParser (NOW UNCOMMENTED) ---
if BaseModelParser and ModelParserStatus:
    try:
        from .gguf_parser import GGUFParser as _GGUFParser_temp

        GGUFParser = _GGUFParser_temp
        debug_message(
            "model_parsers/__init__.py: Successfully imported GGUFParser (%s)",
            GGUFParser,
        )
    except ImportError as e_gguf:
        debug_message(
            "model_parsers/__init__.py: FAILED to import from .gguf_parser: %s",
            e_gguf,
            exc_info=True,
        )
    except Exception as e_gguf_other:  # Keep broad for bootstrap phase
        debug_message(
            "model_parsers/__init__.py: UNEXPECTED ERROR importing from .gguf_parser: %s",
            e_gguf_other,
            exc_info=True,
        )
else:
    debug_message(
        (
            "model_parsers/__init__.py: Skipping GGUFParser import due to base class import failure "
            "or them being None."
        ),  # Corrected line length
    )

_exportable_names = []
if BaseModelParser is not None:
    _exportable_names.append("BaseModelParser")
if ModelParserStatus is not None:
    _exportable_names.append("ModelParserStatus")
if SafetensorsParser is not None:
    _exportable_names.append("SafetensorsParser")
if GGUFParser is not None:
    _exportable_names.append("GGUFParser")
__all__ = _exportable_names

debug_message("model_parsers/__init__.py: FINISHED. __all__ is %s.", __all__)
_actually_available = [name for name in __all__ if name in globals() and globals()[name] is not None]
debug_message(
    "model_parsers/__init__.py: Names actually available and not None: %s",
    _actually_available,
)
