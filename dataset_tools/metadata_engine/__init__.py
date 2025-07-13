# dataset_tools/metadata_engine/__init__.py

"""Metadata Engine - Modular metadata parsing system.

This package provides a sophisticated, modular system for parsing metadata
from various file types. Think of it as your complete crafting guild with
specialists for every type of material! ⚔️✨

Main Components:
- MetadataEngine: Main orchestrator that coordinates all parsing
- ContextDataPreparer: Extracts raw file data and context information
- FieldExtractor: Specialized methods for extracting specific data fields
- TemplateProcessor: Processes output templates with variable substitution
- RuleEngine: Evaluates rules to determine which parser to use

Quick Start:
    from dataset_tools.metadata_engine import MetadataEngine

    engine = MetadataEngine(parser_definitions_path, logger)
    result = engine.get_parser_for_file(file_path)

Advanced Usage:
    from dataset_tools.metadata_engine import (
        MetadataEngine, MetadataEngineBuilder,
        ContextDataPreparer, FieldExtractor
    )
"""

# Main engine components
# Core processing components
from .context_preparation import ContextDataPreparer, prepare_context_data
from .engine import (
    MetadataEngine,
    MetadataEngineBuilder,
    MetadataEngineManager,
    create_metadata_engine,
    parse_file_metadata,
)
from .field_extraction import A1111ParameterExtractor, ComfyUIWorkflowExtractor, FieldExtractor, create_field_extractor
from .template_system import (
    OutputFormatter,
    StandardTemplates,
    TemplateBuilder,
    TemplateProcessor,
    format_template_output,
    process_template,
)

# Rule evaluation (if you want to expose it)
try:
    from .rule_engine import RuleBuilder, RuleEngine, create_rule_engine

    RULE_ENGINE_AVAILABLE = True
except ImportError:
    RULE_ENGINE_AVAILABLE = False
    RuleEngine = None
    RuleBuilder = None
    create_rule_engine = None

# Version info
__version__ = "2.0.0"
__author__ = "KTISEOS NYX"

# Main public API - these are the most commonly used components
__all__ = [
    # Main engine interface
    "MetadataEngine",
    "MetadataEngineBuilder",
    "MetadataEngineManager",
    # Convenience functions
    "create_metadata_engine",
    "parse_file_metadata",
    "prepare_context_data",
    # Core components for advanced usage
    "ContextDataPreparer",
    "FieldExtractor",
    "TemplateProcessor",
    "OutputFormatter",
    # Specialized extractors
    "A1111ParameterExtractor",
    "ComfyUIWorkflowExtractor",
    # Template tools
    "TemplateBuilder",
    "StandardTemplates",
    # Utility functions
    "create_field_extractor",
    "process_template",
    "format_template_output",
]

# Add rule engine components if available
if RULE_ENGINE_AVAILABLE:
    __all__.extend(["RuleBuilder", "RuleEngine", "create_rule_engine"])


# Convenience imports for backward compatibility
def get_metadata_engine(parser_definitions_path, logger=None):
    """Convenience function to create a MetadataEngine instance.

    This provides backward compatibility with older code that might
    expect a simple factory function.

    Args:
        parser_definitions_path: Path to parser definition files
        logger: Optional logger instance

    Returns:
        MetadataEngine instance

    """
    return MetadataEngine(parser_definitions_path, logger)


# Add to public API
__all__.append("get_metadata_engine")

# Module-level docstring for help()
__doc__ = """
MetadataEngine - Advanced Modular Metadata Parsing System

This package provides a sophisticated system for extracting metadata from
various file types including images, text files, JSON/TOML configurations,
and AI model files.

Key Features:
- Modular architecture with specialized components
- Rule-based parser selection
- Template-driven output formatting
- Extensible field extraction methods
- Support for multiple file formats
- Robust error handling and fallback mechanisms

Basic Usage:
    >>> from dataset_tools.metadata_engine import MetadataEngine
    >>> engine = MetadataEngine("./parser_definitions")
    >>> result = engine.get_parser_for_file("image.png")
    >>> print(result["tool"])  # Shows which tool parsed the file

Advanced Usage:
    >>> from dataset_tools.metadata_engine import MetadataEngineBuilder
    >>> engine = (MetadataEngineBuilder()
    ...           .with_parser_definitions("./parsers")
    ...           .with_logger(my_logger)
    ...           .build())

For more examples and documentation, see the individual module docstrings.
"""


# Perform any necessary initialization
def _initialize_metadata_engine():
    """Initialize the metadata engine package."""
    import logging

    # Set up a default logger for the package if none exists
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        # Add a null handler to prevent logging errors
        logger.addHandler(logging.NullHandler())

    # Log successful initialization at debug level
    logger.debug("MetadataEngine package initialized successfully")


# Initialize on import
_initialize_metadata_engine()
