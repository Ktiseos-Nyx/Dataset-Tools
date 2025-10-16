"""Civitai API Interaction Module

This module provides functions to interact with the Civitai API to fetch
metadata for models, LORAs, and other resources.
"""

import json
from typing import Any

import requests

from dataset_tools.logger import error_message, info_monitor, warning_message


def get_model_info_by_hash(model_hash: str) -> dict[str, Any] | None:
    """Fetches model version information from Civitai using a model hash.

    Args:
        model_hash: The SHA256 hash (can be full or short AutoV2 version).

    Returns:
        A dictionary containing the model information, or None if not found or an error occurs.

    """
    if not model_hash or not isinstance(model_hash, str):
        return None

    api_url = f"https://civitai.com/api/v1/model-versions/by-hash/{model_hash}"
    info_monitor("[Civitai API] Fetching model info from: %s", api_url)

    try:
        response = requests.get(api_url, timeout=10)  # Add a timeout

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
