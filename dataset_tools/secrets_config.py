"""Secure configuration management for API keys and secrets.

This module handles loading API keys from environment variables or config files
WITHOUT exposing them in the codebase or logs.

Supports:
- Environment variables (.env files)
- JSON config files (secrets.json)
- Encrypted config files (future enhancement)

SECURITY NOTES:
- NEVER commit .env or secrets.json to git!
- API keys are loaded at runtime only
- No keys are logged or printed
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SecretsManager:
    """Manages API keys and other secrets securely.

    Priority order:
    1. Environment variables (CIVITAI_API_KEY)
    2. secrets.json file
    3. QSettings (for GUI app compatibility)
    """

    def __init__(self, secrets_file: Optional[Path] = None):
        """Initialize secrets manager.

        Args:
            secrets_file: Optional path to secrets.json file
        """
        self._secrets_cache: Dict[str, str] = {}

        # Determine secrets file location
        if secrets_file:
            self.secrets_file = Path(secrets_file)
        else:
            # Default: look for secrets.json in package directory
            package_dir = Path(__file__).parent
            self.secrets_file = package_dir / "secrets.json"

        # Load secrets
        self._load_secrets()

    def _load_secrets(self) -> None:
        """Load secrets from available sources."""
        # Try loading from secrets.json
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, 'r') as f:
                    data = json.load(f)
                    self._secrets_cache.update(data)
                logger.debug("Loaded secrets from %s", self.secrets_file)
            except Exception as e:
                logger.warning("Failed to load secrets from %s: %s", self.secrets_file, e)

    def get_civitai_api_key(self) -> Optional[str]:
        """Get CivitAI API key from available sources.

        Priority:
        1. Environment variable CIVITAI_API_KEY
        2. secrets.json file
        3. QSettings (if available)

        Returns:
            API key or None if not found
        """
        # Priority 1: Environment variable
        api_key = os.environ.get('CIVITAI_API_KEY')
        if api_key:
            logger.debug("Using CivitAI API key from environment variable")
            return api_key

        # Priority 2: secrets.json
        api_key = self._secrets_cache.get('civitai_api_key')
        if api_key:
            logger.debug("Using CivitAI API key from secrets.json")
            return api_key

        # Priority 3: QSettings (for GUI compatibility)
        try:
            from PyQt6.QtCore import QSettings
            settings = QSettings("EarthAndDuskMedia", "DatasetViewer")
            api_key = settings.value("civitai_api_key", "", type=str)
            if api_key:
                logger.debug("Using CivitAI API key from QSettings")
                return api_key
        except ImportError:
            # PyQt6 not available (headless mode)
            pass

        logger.debug("No CivitAI API key found")
        return None

    def set_secret(self, key: str, value: str) -> None:
        """Set a secret value (in memory only).

        Args:
            key: Secret key name
            value: Secret value
        """
        self._secrets_cache[key] = value

    def save_to_file(self) -> None:
        """Save current secrets to secrets.json file.

        WARNING: This saves secrets in plaintext!
        Only use in secure environments.
        """
        try:
            with open(self.secrets_file, 'w') as f:
                json.dump(self._secrets_cache, f, indent=2)
            logger.info("Saved secrets to %s", self.secrets_file)

            # Set restrictive file permissions (Unix only)
            if hasattr(os, 'chmod'):
                os.chmod(self.secrets_file, 0o600)  # rw-------
        except Exception as e:
            logger.error("Failed to save secrets: %s", e)


# Global instance for easy access
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance.

    Returns:
        SecretsManager instance
    """
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_civitai_api_key() -> Optional[str]:
    """Convenience function to get CivitAI API key.

    Returns:
        API key or None if not found
    """
    return get_secrets_manager().get_civitai_api_key()
