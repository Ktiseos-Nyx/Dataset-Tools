# This file is just a simple, central place to store things.
# It doesn't import from any other part of our project.

from ..logger import debug_message

_PARSER_CLASS_REGISTRY = {}


def register_parser_class(name: str, cls) -> None:  # noqa: ANN001
    """Adds a Python-based parser class to the central registry."""  # noqa: D401
    debug_message("REGISTRY: Registering class '%s'", name)
    _PARSER_CLASS_REGISTRY[name] = cls


def get_parser_class_by_name(name: str):  # noqa: ANN201
    """Gets a Python-based parser class from the central registry."""  # noqa: D401
    debug_message("REGISTRY: Looking up class '%s'", name)
    return _PARSER_CLASS_REGISTRY.get(name)
