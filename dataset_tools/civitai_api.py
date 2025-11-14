"""Civitai API Interaction Module.

This module provides functions to interact with the Civitai API to fetch
metadata for models, LORAs, and other resources.
"""

import json
import time
from pathlib import Path
from typing import Any

import os
import requests

# Try to import QSettings for GUI mode, fall back to None for headless
try:
    from PyQt6.QtCore import QSettings
    HAS_QSETTINGS = True
except (ImportError, ModuleNotFoundError):
    QSettings = None
    HAS_QSETTINGS = False

from dataset_tools.logger import error_message, info_monitor, warning_message
from dataset_tools.crypto_secrets import get_civitai_api_key as get_encrypted_api_key

# Cache configuration
CACHE_DIR = Path.home() / ".cache" / "dataset-tools" / "civitai"
CACHE_EXPIRY_DAYS = 7


def _get_cache_path(cache_key: str) -> Path:
    """Get the cache file path for a given key."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{cache_key}.json"


def _load_from_cache(cache_key: str) -> dict[str, Any] | None:
    """Load cached API response if it exists and isn't expired."""
    cache_path = _get_cache_path(cache_key)

    if not cache_path.exists():
        return None

    try:
        # Check if cache is expired
        cache_age_seconds = time.time() - cache_path.stat().st_mtime
        cache_age_days = cache_age_seconds / 86400

        if cache_age_days > CACHE_EXPIRY_DAYS:
            info_monitor("[Civitai Cache] Cache expired for %s (%.1f days old)", cache_key, cache_age_days)
            return None

        # Load cached data
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            info_monitor("[Civitai Cache] Loaded from cache: %s", cache_key)
            return data

    except Exception as e:
        error_message("[Civitai Cache] Failed to load cache for %s: %s", cache_key, e)
        return None


def _save_to_cache(cache_key: str, data: dict[str, Any]) -> None:
    """Save API response to cache."""
    try:
        cache_path = _get_cache_path(cache_key)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        info_monitor("[Civitai Cache] Saved to cache: %s", cache_key)
    except Exception as e:
        error_message("[Civitai Cache] Failed to save cache for %s: %s", cache_key, e)


def clear_cache() -> tuple[int, int]:
    """Clear all cached CivitAI API responses.

    Returns:
        Tuple of (files_deleted, bytes_freed)
    """
    if not CACHE_DIR.exists():
        return (0, 0)

    files_deleted = 0
    bytes_freed = 0

    try:
        for cache_file in CACHE_DIR.glob("*.json"):
            try:
                bytes_freed += cache_file.stat().st_size
                cache_file.unlink()
                files_deleted += 1
            except Exception as e:
                error_message("[Civitai Cache] Failed to delete %s: %s", cache_file, e)

        info_monitor("[Civitai Cache] Cleared %s files (%.2f KB)", files_deleted, bytes_freed / 1024)
        return (files_deleted, bytes_freed)

    except Exception as e:
        error_message("[Civitai Cache] Error clearing cache: %s", e)
        return (0, 0)


def get_model_info_by_hash(model_hash: str) -> dict[str, Any] | None:
    """Fetches model version information from Civitai using a model hash.

    Args:
        model_hash: The SHA256 hash (can be full or short AutoV2 version).

    Returns:
        A dictionary containing the model information, or None if not found or an error occurs.

    """
    if not model_hash or not isinstance(model_hash, str):
        return None

    # Check cache first
    cache_key = f"hash_{model_hash}"
    cached_data = _load_from_cache(cache_key)
    if cached_data:
        return cached_data

    api_url = f"https://civitai.com/api/v1/model-versions/by-hash/{model_hash}"
    info_monitor("[Civitai API] Fetching model info from: %s", api_url)

    # Get API key from encrypted storage (with QSettings + env fallback)
    api_key = get_encrypted_api_key() or ""

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        info_monitor("[CIVITAI_DEBUG] Making request to: %s", api_url)
        response = requests.get(api_url, timeout=10, headers=headers)  # Add a timeout
        info_monitor("[CIVITAI_DEBUG] Response status code: %s", response.status_code)
        if response.status_code != 200:
            info_monitor("[CIVITAI_DEBUG] Response content: %s", response.text)

        if response.status_code == 200:
            data = response.json()
            # We can simplify and structure the data here to return only what we need
            model_data = data.get("model", {})
            first_image = data.get("images", [{}])[0] if data.get("images") else {}

            model_info = {
                "modelId": data.get("modelId"),
                "modelName": model_data.get("name"),
                "versionName": data.get("name"),
                "creator": model_data.get("creator", {}).get("username"),
                "type": model_data.get("type"),
                "trainedWords": data.get("trainedWords", []),
                "baseModel": data.get("baseModel"),
                "description": model_data.get("description"),
                "tags": model_data.get("tags", []),
                "downloadUrl": data.get("downloadUrl"),
                "previewImageUrl": first_image.get("url"),
            }
            # Save to cache
            _save_to_cache(cache_key, model_info)
            return model_info
        warning_message(
            "[Civitai API] Model hash not found on Civitai (Status: %s): %s",
            response.status_code,
            model_hash,
        )
        return None

    except requests.exceptions.RequestException as e:
        error_message("[Civitai API] Error fetching data: %s", e)
        return None
    except json.JSONDecodeError:
        error_message("[Civitai API] Failed to decode JSON response.")
        return None
    except Exception as e:
        error_message("[Civitai API] An unexpected error occurred: %s", e)
        return None


def get_model_info_by_id(model_id: str) -> dict[str, Any] | None:
    """Fetches model information from Civitai using a model ID.

    Args:
        model_id: The Civitai model ID.

    Returns:
        A dictionary containing the model information, or None if not found or an error occurs.

    """
    if not model_id or not isinstance(model_id, str):
        return None

    # Check cache first
    cache_key = f"model_{model_id}"
    cached_data = _load_from_cache(cache_key)
    if cached_data:
        return cached_data

    api_url = f"https://civitai.com/api/v1/models/{model_id}"
    info_monitor("[Civitai API] Fetching model info from: %s", api_url)

    # Get API key from encrypted storage (with QSettings + env fallback)
    api_key = get_encrypted_api_key() or ""

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.get(api_url, timeout=10, headers=headers)

        if response.status_code == 200:
            data = response.json()
            # Extract MINIMAL info - just resource identification
            first_version = data.get("modelVersions", [{}])[0] if data.get("modelVersions") else {}

            model_info = {
                "modelName": data.get("name"),
                "type": data.get("type"),
                "versionName": first_version.get("name"),
                "baseModel": first_version.get("baseModel"),
                "trainedWords": first_version.get("trainedWords", []),
            }
            # Save to cache
            _save_to_cache(cache_key, model_info)
            return model_info
        warning_message(
            "[Civitai API] Model ID not found on Civitai (Status: %s): %s",
            response.status_code,
            model_id,
        )
        return None

    except requests.exceptions.RequestException as e:
        error_message("[Civitai API] Error fetching data: %s", e)
        return None
    except json.JSONDecodeError:
        error_message("[Civitai API] Failed to decode JSON response.")
        return None
    except Exception as e:
        error_message("[Civitai API] An unexpected error occurred: %s", e)
        return None


def get_model_version_info_by_id(version_id: str) -> dict[str, Any] | None:
    """Fetches model version information from Civitai using a model version ID.

    Args:
        version_id: The Civitai model version ID.

    Returns:
        A dictionary containing the model version information, or None if not found or an error occurs.

    """
    if not version_id or not isinstance(version_id, str):
        return None

    # Check cache first
    cache_key = f"version_{version_id}"
    cached_data = _load_from_cache(cache_key)
    if cached_data:
        return cached_data

    api_url = f"https://civitai.com/api/v1/model-versions/{version_id}"
    info_monitor("[Civitai API] Fetching model version info from: %s", api_url)

    # Get API key from encrypted storage (with QSettings + env fallback)
    api_key = get_encrypted_api_key() or ""

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.get(api_url, timeout=10, headers=headers)

        if response.status_code == 200:
            data = response.json()
            # Extract only essential info, not the full response with all images/metadata
            model_data = data.get("model", {})

            version_info = {
                "versionId": data.get("id"),
                "versionName": data.get("name"),
                "modelId": data.get("modelId"),
                "modelName": model_data.get("name"),
                "creator": model_data.get("creator", {}).get("username"),
                "type": model_data.get("type"),
                "trainedWords": data.get("trainedWords", []),
                "baseModel": data.get("baseModel"),
                "description": model_data.get("description"),
                "downloadUrl": data.get("downloadUrl"),
            }
            # Save to cache
            _save_to_cache(cache_key, version_info)
            return version_info
        warning_message(
            "[Civitai API] Model version ID not found on Civitai (Status: %s): %s",
            response.status_code,
            version_id,
        )
        return None

    except requests.exceptions.RequestException as e:
        error_message("[Civitai API] Error fetching data: %s", e)
        return None
    except json.JSONDecodeError:
        error_message("[Civitai API] Failed to decode JSON response.")
        return None
    except Exception as e:
        error_message("[Civitai API] An unexpected error occurred: %s", e)
        return None

