# dataset_tools/vendored_sdpr/logger.py

__author__ = "receyuki"  # Original author if applicable
__filename__ = "logger.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools and clarity
__copyright__ = "Copyright 2024, Receyuki & Ktiseos Nyx"  # Adjusted
__email__ = "receyuki@gmail.com"  # Original email

import logging

# Module-level cache for logger instances
_loggers_cache: dict[str, logging.Logger] = {}


def _get_log_level_value(level_name: str | None) -> int:
    """Converts a string log level name to its corresponding logging integer value."""
    if not level_name:
        return logging.INFO  # Default level if none provided or empty string
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARN": logging.WARNING,  # Standard Python logging level name
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_name.strip().upper(), logging.INFO)


def _configure_logger_instance(logger: logging.Logger, add_basic_handler: bool = False):
    """Basic configuration for a logger instance.
    Typically, handlers are added by the main application's logging setup.
    This function can ensure a handler exists if this module is run standalone or for testing.
    """
    if add_basic_handler and not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        # Prevent messages from propagating to the root logger if we added a specific handler,
        # allowing more fine-grained control by the main application's logger.
        logger.propagate = False


def get_logger(
    name: str,
    level: str | None = None,
    force_basic_handler: bool = False,
) -> logging.Logger:
    """Retrieves a cached logger instance by name, or creates a new one.

    Args:
        name (str): The name for the logger.
        level (Optional[str]): The desired logging level string (e.g., "INFO", "DEBUG").
                               If None, the logger's existing level or parent's level is used.
        force_basic_handler (bool): If True, ensures a basic StreamHandler is added
                                    if the logger has no handlers. Useful for standalone
                                    testing of this vendored package. Defaults to False,
                                    assuming the main application will configure handlers.

    Returns:
        logging.Logger: The configured logger instance.

    """
    global _loggers_cache
    if name in _loggers_cache:
        # If logger exists and a new level is specified, update it.
        cached_logger = _loggers_cache[name]
        if level:
            log_level_value = _get_log_level_value(level)
            # Only set if different or not set (0)
            if cached_logger.level != log_level_value:
                cached_logger.setLevel(log_level_value)
        if force_basic_handler:
            _configure_logger_instance(cached_logger, add_basic_handler=True)
        return cached_logger

    logger_instance = logging.getLogger(name)
    if level:
        log_level_value = _get_log_level_value(level)
        logger_instance.setLevel(log_level_value)

    if force_basic_handler:
        _configure_logger_instance(logger_instance, add_basic_handler=True)
    # Else, assume the main application (dataset_tools.logger) will configure
    # handlers for loggers matching "DSVendored_SDPR.*"

    _loggers_cache[name] = logger_instance
    return logger_instance


def configure_global_sdpr_root_logger(level: str = "INFO"):
    """Configures the root logger.
    NOTE: This might conflict with or be redundant if the main application
    (dataset_tools.logger) already configures the root logger or external loggers.
    Use with caution or for standalone use of this vendored package.
    """
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    level_value = _get_log_level_value(level)

    root_logger = logging.getLogger()  # Get the root logger
    root_logger.setLevel(level_value)

    # Remove existing handlers to avoid duplication if this is called multiple times
    # or if other configurations exist. Be careful with this in a larger app.
    # for handler in root_logger.handlers[:]:
    #     root_logger.removeHandler(handler)

    # Add a stream handler if one doesn't already exist or if you want a specific one
    has_stream_handler = any(
        isinstance(h, logging.StreamHandler) for h in root_logger.handlers
    )
    if not has_stream_handler:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)

    # Example: file handler (usually managed by main app's logging)
    # file_handler = logging.FileHandler(f"{root_logger.name or 'root'}.log")
    # file_handler.setFormatter(formatter)
    # root_logger.addHandler(file_handler)


# Example of how this might be used standalone (for testing this module)
if __name__ == "__main__":
    # This global configuration is generally NOT recommended if this module
    # is part of a larger application that has its own logging setup.
    # configure_global_sdpr_root_logger("DEBUG")

    # Get specific loggers using the factory
    logger1 = get_logger(
        "DSVendored_SDPR.Module1",
        level="DEBUG",
        force_basic_handler=True,
    )
    logger2 = get_logger(
        "DSVendored_SDPR.Module2",
        level="INFO",
        force_basic_handler=True,
    )
    logger1_cached = get_logger("DSVendored_SDPR.Module1")  # Should be cached

    logger1.debug("Debug message from Module1")
    logger2.info("Info message from Module2")
    logger1_cached.info("Info message from Module1 via cached instance")
    logging.getLogger("DSVendored_SDPR.Module1.Submodule").error(
        "Error from submodule, will propagate if not configured.",
    )
