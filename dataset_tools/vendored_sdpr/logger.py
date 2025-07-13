# dataset_tools/vendored_sdpr/logger.py

__author__ = "receyuki"
__filename__ = "logger.py"
# MODIFIED by Ktiseos Nyx for Dataset-Tools and clarity
__copyright__ = "Copyright 2024, Receyuki & Ktiseos Nyx"
__email__ = "receyuki@gmail.com"

import logging

_loggers_cache: dict[str, logging.Logger] = {}


def _get_log_level_value(level_name: str | None) -> int:
    if not level_name:
        return logging.INFO
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARN": logging.WARNING,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_name.strip().upper(), logging.INFO)


def _configure_logger_instance(logger: logging.Logger, add_basic_handler: bool = False):
    if add_basic_handler and not logger.handlers:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        logger.propagate = False


def get_logger(
    name: str,
    level: str | None = None,
    force_basic_handler: bool = False,
) -> logging.Logger:
    """Retrieves a cached logger instance by name, or creates a new one."""
    # global _loggers_cache # Not needed as _loggers_cache is module-level
    if name in _loggers_cache:
        cached_logger = _loggers_cache[name]
        if level:
            log_level_value = _get_log_level_value(level)
            if cached_logger.level == 0 or cached_logger.level != log_level_value:  # Check if not set (0) or different
                cached_logger.setLevel(log_level_value)
        if force_basic_handler and not cached_logger.handlers:  # Only configure if no handlers
            _configure_logger_instance(cached_logger, add_basic_handler=True)
        return cached_logger

    logger_instance = logging.getLogger(name)
    log_level_value_to_set = _get_log_level_value(level) if level else None

    if log_level_value_to_set is not None:
        logger_instance.setLevel(log_level_value_to_set)
    # If level is None, logger inherits from parent or root, which is fine.

    if force_basic_handler:  # This will also set propagate=False if handler is added
        _configure_logger_instance(logger_instance, add_basic_handler=True)
    # If not forcing basic handler, it's assumed the main application
    # (e.g., dataset_tools.logger using setup_rich_handler_for_external_logger)
    # will configure the handlers and propagation for loggers under "DSVendored_SDPR.*"

    _loggers_cache[name] = logger_instance
    return logger_instance


def configure_global_sdpr_root_logger(level: str = "INFO"):
    """Configures the root logger. Use with caution in larger applications."""
    # This function is generally for standalone testing of this package.
    # The main application should handle overall logging configuration.
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    level_value = _get_log_level_value(level)
    root_logger = logging.getLogger()  # Get the root logger

    # Check if a similar handler already exists to avoid duplicates if called multiple times
    # This is a simple check; more robust checks might compare formatter or stream.
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)

    # Set level on root logger. Be careful, this affects all unconfigured loggers.
    root_logger.setLevel(level_value)


if __name__ == "__main__":
    # Example: Forcing basic handlers for standalone testing of this module
    # This allows seeing output without the main app's Rich setup.
    # configure_global_sdpr_root_logger("DEBUG") # Optionally configure root for all other loggers

    logger1 = get_logger("DSVendored_SDPR.Module1", level="DEBUG", force_basic_handler=True)
    logger2 = get_logger("DSVendored_SDPR.Module2", level="INFO", force_basic_handler=True)
    logger1_cached = get_logger("DSVendored_SDPR.Module1")  # Should get cached, level already set

    logger1.debug("Debug message from Module1")
    logger2.info("Info message from Module2")
    logger1_cached.info("Info message from Module1 (via cached instance)")

    # Example of a submodule logger; it will propagate to DSVendored_SDPR if not configured itself
    # and if DSVendored_SDPR has a handler and its propagate is True.
    # Or, if force_basic_handler was used on DSVendored_SDPR, it would handle it.
    # If DSVendored_SDPR.Module1 had propagate=False (due to its own basic handler),
    # this submodule's message would only be seen if it also had a handler.
    sub_logger = get_logger("DSVendored_SDPR.Module1.Submodule", force_basic_handler=True)
    sub_logger.error(
        "Error from submodule, should be handled by its own basic handler now."  # Corrected long line
    )

    # Test logger without forcing handler, assuming main app (or configure_global_sdpr_root_logger) handles it
    logger_no_force = get_logger("DSVendored_SDPR.NoForce", level="DEBUG")
    logger_no_force.debug("This message relies on external or root logger configuration for DSVendored_SDPR tree.")
