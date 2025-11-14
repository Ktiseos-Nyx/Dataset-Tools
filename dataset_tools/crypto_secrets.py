"""Encrypted secrets management using Fernet.

Provides "good enough" encryption for API keys stored on disk.
NOT Fort Knox - just obfuscation to deter casual snoopers and automated scanners.

Security Philosophy:
- Pragmatic: 90% protection for 10% effort
- Machine-specific: Uses hardware ID as key derivation
- User-friendly: No password prompts, just works
- Transparent: Auto-migrates from plaintext secrets.json

What This Prevents:
✅ Automated scanners looking for "api_key": patterns
✅ Casual file browsing revealing keys
✅ Accidental leaks (someone sees file, can't read it)
✅ Script kiddies who move on to easier targets

What This Doesn't Prevent:
❌ Malware with system access
❌ Determined attackers with local file access
❌ Social engineering
"""

import json
import logging
import uuid
import hashlib
import base64
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)


class CryptoSecretsManager:
    """Manages encrypted API keys and secrets.

    Uses Fernet symmetric encryption with machine-specific key derivation.
    Backwards compatible with plaintext secrets.json.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize crypto secrets manager.

        Args:
            config_dir: Directory for secrets files (defaults to package dir)
        """
        self._secrets_cache: Dict[str, str] = {}

        # Determine config directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default: package directory
            self.config_dir = Path(__file__).parent

        self.plaintext_file = self.config_dir / "secrets.json"
        self.encrypted_file = self.config_dir / "secrets.enc"

        # Generate machine-specific encryption key
        if CRYPTO_AVAILABLE:
            self.cipher = self._create_cipher()
        else:
            self.cipher = None
            logger.warning("cryptography package not available - encryption disabled!")

        # Load secrets (try encrypted first, fallback to plaintext)
        self._load_secrets()

    def _create_cipher(self) -> Fernet:
        """Create Fernet cipher with machine-specific key.

        Uses MAC address as seed for key derivation.
        This means keys are machine-specific but deterministic.
        """
        # Get machine ID (MAC address as integer)
        machine_id = str(uuid.getnode())

        # Derive 32-byte key from machine ID
        key_material = hashlib.sha256(machine_id.encode()).digest()
        key = base64.urlsafe_b64encode(key_material)

        return Fernet(key)

    def _load_secrets(self) -> None:
        """Load secrets from available sources (encrypted preferred)."""
        # Priority 1: Try encrypted file
        if self.encrypted_file.exists() and CRYPTO_AVAILABLE:
            try:
                with open(self.encrypted_file, 'rb') as f:
                    encrypted_data = f.read()

                decrypted = self.cipher.decrypt(encrypted_data)
                data = json.loads(decrypted.decode('utf-8'))
                self._secrets_cache.update(data)

                logger.info("Loaded encrypted secrets from %s", self.encrypted_file.name)
                return
            except Exception as e:
                logger.error("Failed to load encrypted secrets: %s", e)
                logger.warning("Falling back to plaintext secrets...")

        # Priority 2: Try plaintext file
        if self.plaintext_file.exists():
            try:
                with open(self.plaintext_file, 'r') as f:
                    data = json.load(f)
                    self._secrets_cache.update(data)

                logger.warning("Loaded PLAINTEXT secrets from %s - consider enabling encryption!",
                             self.plaintext_file.name)

                # Auto-migrate to encrypted if possible
                if CRYPTO_AVAILABLE:
                    logger.info("Auto-migrating plaintext secrets to encrypted format...")
                    self.save_encrypted()
            except Exception as e:
                logger.error("Failed to load plaintext secrets: %s", e)

    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret value.

        Args:
            key: Secret key name

        Returns:
            Secret value or None if not found
        """
        return self._secrets_cache.get(key)

    def set_secret(self, key: str, value: str) -> None:
        """Set a secret value (in memory).

        Args:
            key: Secret key name
            value: Secret value
        """
        self._secrets_cache[key] = value

    def save_encrypted(self) -> bool:
        """Save secrets to encrypted file.

        Returns:
            True if successful, False if encryption unavailable
        """
        if not CRYPTO_AVAILABLE:
            logger.error("Cannot save encrypted - cryptography package not installed!")
            logger.info("Install with: pip install cryptography")
            return False

        try:
            # Serialize secrets to JSON
            json_data = json.dumps(self._secrets_cache, indent=2)

            # Encrypt
            encrypted = self.cipher.encrypt(json_data.encode('utf-8'))

            # Write to file
            with open(self.encrypted_file, 'wb') as f:
                f.write(encrypted)

            # Set restrictive permissions (Unix only)
            if hasattr(self.encrypted_file.chmod, '__call__'):
                self.encrypted_file.chmod(0o600)  # rw-------

            logger.info("Saved encrypted secrets to %s", self.encrypted_file.name)

            # Remove plaintext file if it exists
            if self.plaintext_file.exists():
                try:
                    self.plaintext_file.unlink()
                    logger.info("Removed plaintext secrets file (migrated to encrypted)")
                except Exception as e:
                    logger.warning("Failed to remove plaintext file: %s", e)

            return True

        except Exception as e:
            logger.error("Failed to save encrypted secrets: %s", e)
            return False

    def save_plaintext(self) -> None:
        """Save secrets to plaintext file (NOT RECOMMENDED).

        Only use for debugging or if encryption is unavailable.
        """
        try:
            with open(self.plaintext_file, 'w') as f:
                json.dump(self._secrets_cache, f, indent=2)

            # Set restrictive permissions (Unix only)
            if hasattr(self.plaintext_file.chmod, '__call__'):
                self.plaintext_file.chmod(0o600)  # rw-------

            logger.warning("Saved PLAINTEXT secrets to %s - SECURITY RISK!",
                         self.plaintext_file.name)
        except Exception as e:
            logger.error("Failed to save plaintext secrets: %s", e)

    def get_civitai_api_key(self) -> Optional[str]:
        """Get CivitAI API key with environment variable support.

        Priority:
        1. Environment variable CIVITAI_API_KEY
        2. Encrypted/plaintext secrets file
        3. QSettings (for backwards compatibility)

        Returns:
            API key or None if not found
        """
        import os

        # Priority 1: Environment variable
        api_key = os.environ.get('CIVITAI_API_KEY')
        if api_key:
            logger.debug("Using CivitAI API key from environment variable")
            return api_key

        # Priority 2: Secrets file (encrypted or plaintext)
        api_key = self.get_secret('civitai_api_key')
        if api_key:
            logger.debug("Using CivitAI API key from secrets file")
            return api_key

        # Priority 3: QSettings (backwards compatibility)
        try:
            from PyQt6.QtCore import QSettings
            settings = QSettings("EarthAndDuskMedia", "DatasetViewer")
            api_key = settings.value("civitai_api_key", "", type=str)
            if api_key:
                logger.debug("Using CivitAI API key from QSettings")
                # Migrate to encrypted storage
                self.set_secret('civitai_api_key', api_key)
                if CRYPTO_AVAILABLE:
                    self.save_encrypted()
                return api_key
        except ImportError:
            # PyQt6 not available (headless mode)
            pass

        logger.debug("No CivitAI API key found")
        return None


# Global instance
_crypto_secrets_manager: Optional[CryptoSecretsManager] = None


def get_crypto_secrets_manager() -> CryptoSecretsManager:
    """Get the global encrypted secrets manager instance.

    Returns:
        CryptoSecretsManager instance
    """
    global _crypto_secrets_manager
    if _crypto_secrets_manager is None:
        _crypto_secrets_manager = CryptoSecretsManager()
    return _crypto_secrets_manager


def get_civitai_api_key() -> Optional[str]:
    """Convenience function to get CivitAI API key.

    Returns:
        API key or None if not found
    """
    return get_crypto_secrets_manager().get_civitai_api_key()
