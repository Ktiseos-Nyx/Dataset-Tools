# dataset_tools/metadata_engine/extractors/invokeai_extractors.py

"""InvokeAI extraction methods.

Handles parsing of InvokeAI metadata formats, including multiple metadata
formats (invokeai_metadata, sd-metadata, Dream format). Based on the vendored
format code but adapted for the metadata_engine system.
"""

import json
import logging
import re
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]

# Parameter mappings from vendored InvokeAI code
INVOKE_METADATA_PARAM_MAP: dict[str, str] = {
    "seed": "seed",
    "steps": "steps",
    "cfg_scale": "cfg_scale",
    "scheduler": "scheduler",
    "refiner_steps": "refiner_steps",
    "refiner_cfg_scale": "refiner_cfg_scale",
    "refiner_scheduler": "refiner_scheduler",
    "refiner_positive_aesthetic_score": "refiner_positive_aesthetic_score",
    "refiner_negative_aesthetic_score": "refiner_negative_aesthetic_score",
    "refiner_start": "refiner_start",
}

SD_METADATA_IMAGE_PARAM_MAP: dict[str, str] = {
    "sampler": "sampler_name",
    "seed": "seed",
    "cfg_scale": "cfg_scale",
    "steps": "steps",
}

DREAM_FORMAT_PARAM_MAP: dict[str, str] = {
    "s": "steps",
    "S": "seed",
    "C": "cfg_scale",
    "A": "sampler_name",
}


class InvokeAIExtractor:
    """Handles InvokeAI-specific extraction methods."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the InvokeAI extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "invokeai_extract_prompt": self.extract_invokeai_prompt,
            "invokeai_extract_negative_prompt": self.extract_invokeai_negative_prompt,
            "invokeai_extract_parameters": self.extract_invokeai_parameters,
            "invokeai_extract_model_info": self.extract_invokeai_model_info,
            "invokeai_parse_dream_format": self.parse_dream_format,
            "invokeai_split_prompt": self.split_invokeai_prompt,
        }

    def extract_invokeai_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract positive prompt from InvokeAI metadata."""
        if not isinstance(data, dict):
            return ""

        # Try different InvokeAI format variations
        prompt = ""

        # Check for invokeai_metadata format
        if "invokeai_metadata" in data:
            prompt = self._extract_from_invokeai_metadata(data["invokeai_metadata"], "positive_prompt")

        # Check for sd-metadata format
        elif "sd-metadata" in data:
            prompt = self._extract_from_sd_metadata(data["sd-metadata"], "prompt")

        # Check for Dream format
        elif "Dream" in data:
            dream_text = data.get("Dream", "")
            if isinstance(dream_text, str):
                prompt, _ = self.split_invokeai_prompt(dream_text)

        return prompt.strip() if prompt else ""

    def extract_invokeai_negative_prompt(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> str:
        """Extract negative prompt from InvokeAI metadata."""
        if not isinstance(data, dict):
            return ""

        # Try different InvokeAI format variations
        negative_prompt = ""

        # Check for invokeai_metadata format
        if "invokeai_metadata" in data:
            negative_prompt = self._extract_from_invokeai_metadata(data["invokeai_metadata"], "negative_prompt")

        # Check for sd-metadata format
        elif "sd-metadata" in data:
            prompt_text = self._extract_from_sd_metadata(data["sd-metadata"], "prompt")
            if prompt_text:
                _, negative_prompt = self.split_invokeai_prompt(prompt_text)

        # Check for Dream format
        elif "Dream" in data:
            dream_text = data.get("Dream", "")
            if isinstance(dream_text, str):
                _, negative_prompt = self.split_invokeai_prompt(dream_text)

        return negative_prompt.strip() if negative_prompt else ""

    def extract_invokeai_parameters(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract generation parameters from InvokeAI metadata."""
        if not isinstance(data, dict):
            return {}

        parameters = {}

        # Check for invokeai_metadata format
        if "invokeai_metadata" in data:
            parameters.update(self._extract_params_from_invokeai_metadata(data["invokeai_metadata"]))

        # Check for sd-metadata format
        elif "sd-metadata" in data:
            parameters.update(self._extract_params_from_sd_metadata(data["sd-metadata"]))

        # Check for Dream format
        elif "Dream" in data:
            parameters.update(self._extract_params_from_dream_format(data["Dream"]))

        self.logger.debug(f"InvokeAI parameters extracted: {list(parameters.keys())}")
        return parameters

    def extract_invokeai_model_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract model information from InvokeAI metadata."""
        if not isinstance(data, dict):
            return {}

        model_info = {}

        # Check for invokeai_metadata format
        if "invokeai_metadata" in data:
            try:
                metadata = json.loads(data["invokeai_metadata"])
                if isinstance(metadata, dict) and "model" in metadata:
                    model_data = metadata["model"]
                    if isinstance(model_data, dict):
                        if "model_name" in model_data:
                            model_info["model"] = model_data["model_name"]
                        if "hash" in model_data:
                            model_info["model_hash"] = model_data["hash"]
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.debug(f"Error extracting model info from invokeai_metadata: {e}")

        # Check for sd-metadata format
        elif "sd-metadata" in data:
            try:
                metadata = json.loads(data["sd-metadata"])
                if isinstance(metadata, dict) and "model_weights" in metadata:
                    model_info["model"] = metadata["model_weights"]
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.debug(f"Error extracting model info from sd-metadata: {e}")

        return model_info

    def parse_dream_format(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Parse Dream format string into components."""
        if not isinstance(data, str):
            return {}

        # Dream format: "prompt text -s steps -S seed -C cfg_scale -A sampler"
        result = {"prompt": "", "parameters": {}}

        # Extract parameters using regex
        param_pattern = r"-([sSCA])\s+([^\-]+?)(?=\s-[sSCA]|\s*$)"
        matches = re.findall(param_pattern, data)

        parameters = {}
        for key, value in matches:
            std_key = DREAM_FORMAT_PARAM_MAP.get(key)
            if std_key:
                value = value.strip()
                if std_key in ["seed", "steps"]:
                    try:
                        parameters[std_key] = int(value)
                    except ValueError:
                        pass
                elif std_key == "cfg_scale":
                    try:
                        parameters[std_key] = float(value)
                    except ValueError:
                        pass
                else:
                    parameters[std_key] = value

        # Extract prompt (everything before first parameter)
        prompt_match = re.match(r"^(.*?)(?:\s-[sSCA]\s|$)", data)
        if prompt_match:
            result["prompt"] = prompt_match.group(1).strip()

        result["parameters"] = parameters
        return result

    def split_invokeai_prompt(self, prompt_text: str) -> tuple[str, str]:
        """Split InvokeAI prompt text into positive and negative parts."""
        if not isinstance(prompt_text, str):
            return "", ""

        # InvokeAI format: "positive prompt [negative prompt]"
        # Look for negative prompt in square brackets
        neg_match = re.search(r"\[(.*?)\]$", prompt_text.strip())
        if neg_match:
            negative = neg_match.group(1).strip()
            positive = prompt_text[:neg_match.start()].strip()
            return positive, negative

        return prompt_text.strip(), ""

    def _extract_from_invokeai_metadata(self, metadata_str: str, field: str) -> str:
        """Extract field from invokeai_metadata JSON string."""
        try:
            metadata = json.loads(metadata_str)
            if isinstance(metadata, dict):
                return str(metadata.get(field, ""))
        except (json.JSONDecodeError, KeyError):
            pass
        return ""

    def _extract_from_sd_metadata(self, metadata_str: str, field: str) -> str:
        """Extract field from sd-metadata JSON string."""
        try:
            metadata = json.loads(metadata_str)
            if isinstance(metadata, dict) and "image" in metadata:
                image_data = metadata["image"]
                if isinstance(image_data, dict):
                    prompt_field = image_data.get("prompt")
                    if isinstance(prompt_field, list) and prompt_field:
                        prompt_entry = prompt_field[0]
                        if isinstance(prompt_entry, dict):
                            return str(prompt_entry.get("prompt", ""))
                    elif isinstance(prompt_field, str):
                        return prompt_field
        except (json.JSONDecodeError, KeyError):
            pass
        return ""

    def _extract_params_from_invokeai_metadata(self, metadata_str: str) -> dict[str, Any]:
        """Extract parameters from invokeai_metadata JSON string."""
        try:
            metadata = json.loads(metadata_str)
            if isinstance(metadata, dict):
                parameters = {}
                for invoke_key, std_key in INVOKE_METADATA_PARAM_MAP.items():
                    if invoke_key in metadata:
                        value = metadata[invoke_key]
                        if std_key in ["seed", "steps", "refiner_steps"]:
                            try:
                                parameters[std_key] = int(value)
                            except (ValueError, TypeError):
                                pass
                        elif std_key in ["cfg_scale", "refiner_cfg_scale", "refiner_positive_aesthetic_score",
                                        "refiner_negative_aesthetic_score", "refiner_start"]:
                            try:
                                parameters[std_key] = float(value)
                            except (ValueError, TypeError):
                                pass
                        else:
                            parameters[std_key] = str(value)

                # Extract dimensions
                if "width" in metadata:
                    try:
                        parameters["width"] = int(metadata["width"])
                    except (ValueError, TypeError):
                        pass
                if "height" in metadata:
                    try:
                        parameters["height"] = int(metadata["height"])
                    except (ValueError, TypeError):
                        pass

                return parameters
        except (json.JSONDecodeError, KeyError):
            pass
        return {}

    def _extract_params_from_sd_metadata(self, metadata_str: str) -> dict[str, Any]:
        """Extract parameters from sd-metadata JSON string."""
        try:
            metadata = json.loads(metadata_str)
            if isinstance(metadata, dict) and "image" in metadata:
                image_data = metadata["image"]
                if isinstance(image_data, dict):
                    parameters = {}
                    for sd_key, std_key in SD_METADATA_IMAGE_PARAM_MAP.items():
                        if sd_key in image_data:
                            value = image_data[sd_key]
                            if std_key in ["seed", "steps"]:
                                try:
                                    parameters[std_key] = int(value)
                                except (ValueError, TypeError):
                                    pass
                            elif std_key == "cfg_scale":
                                try:
                                    parameters[std_key] = float(value)
                                except (ValueError, TypeError):
                                    pass
                            else:
                                parameters[std_key] = str(value)

                    # Extract dimensions
                    if "width" in image_data:
                        try:
                            parameters["width"] = int(image_data["width"])
                        except (ValueError, TypeError):
                            pass
                    if "height" in image_data:
                        try:
                            parameters["height"] = int(image_data["height"])
                        except (ValueError, TypeError):
                            pass

                    return parameters
        except (json.JSONDecodeError, KeyError):
            pass
        return {}

    def _extract_params_from_dream_format(self, dream_str: str) -> dict[str, Any]:
        """Extract parameters from Dream format string."""
        if not isinstance(dream_str, str):
            return {}

        dream_data = self.parse_dream_format(dream_str, {}, {}, {})
        return dream_data.get("parameters", {})
