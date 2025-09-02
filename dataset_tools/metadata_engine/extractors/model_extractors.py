# dataset_tools/metadata_engine/extractors/model_extractors.py

"""Model file extraction methods.

Handles parsing of AI model files including SafeTensors and GGUF formats.
Provides extraction methods for model metadata, architecture info, and training parameters.
"""

import logging
from typing import Any

# Type aliases
ContextData = dict[str, Any]
ExtractedFields = dict[str, Any]
MethodDefinition = dict[str, Any]


class ModelExtractor:
    """Handles AI model file extraction methods."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the model extractor."""
        self.logger = logger

    def get_methods(self) -> dict[str, callable]:
        """Return dictionary of method name -> method function."""
        return {
            "safetensors_extract_metadata": self.extract_safetensors_metadata,
            "safetensors_extract_model_info": self.extract_safetensors_model_info,
            "safetensors_extract_training_info": self.extract_safetensors_training_info,
            "gguf_extract_metadata": self.extract_gguf_metadata,
            "gguf_extract_model_info": self.extract_gguf_model_info,
            "gguf_extract_architecture_info": self.extract_gguf_architecture_info,
            "model_extract_file_info": self.extract_model_file_info,
        }

    def extract_safetensors_metadata(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract all metadata from SafeTensors model file."""
        if not isinstance(context, dict):
            return {}

        safetensors_data = context.get("safetensors_metadata")
        if not safetensors_data:
            self.logger.debug("No SafeTensors metadata found in context")
            return {}

        self.logger.debug(f"SafeTensors metadata keys: {list(safetensors_data.keys())}")
        return dict(safetensors_data)

    def extract_safetensors_model_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract model information from SafeTensors metadata."""
        safetensors_data = context.get("safetensors_metadata", {})
        if not safetensors_data:
            return {}

        model_info = {}

        # Common SafeTensors metadata fields
        if "model_name" in safetensors_data:
            model_info["name"] = safetensors_data["model_name"]
        if "base_model" in safetensors_data:
            model_info["base_model"] = safetensors_data["base_model"]
        if "model_type" in safetensors_data:
            model_info["type"] = safetensors_data["model_type"]
        if "architecture" in safetensors_data:
            model_info["architecture"] = safetensors_data["architecture"]
        if "version" in safetensors_data:
            model_info["version"] = safetensors_data["version"]
        if "description" in safetensors_data:
            model_info["description"] = safetensors_data["description"]

        return model_info

    def extract_safetensors_training_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract training information from SafeTensors metadata."""
        safetensors_data = context.get("safetensors_metadata", {})
        if not safetensors_data:
            return {}

        training_info = {}

        # Training-related fields
        training_fields = [
            "ss_learning_rate", "ss_num_train_images", "ss_num_epochs",
            "ss_batch_size_per_device", "ss_gradient_accumulation_steps",
            "ss_lr_scheduler", "ss_optimizer", "ss_mixed_precision",
            "ss_training_started_at", "ss_training_finished_at",
            "ss_epoch", "ss_max_train_steps", "ss_resolution",
            "ss_dataset_dirs", "ss_tag_frequency", "ss_dataset_size"
        ]

        for field in training_fields:
            if field in safetensors_data:
                # Clean up field name (remove ss_ prefix)
                clean_field = field.replace("ss_", "")
                training_info[clean_field] = safetensors_data[field]

        return training_info

    def extract_gguf_metadata(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract all metadata from GGUF model file."""
        if not isinstance(context, dict):
            return {}

        gguf_data = context.get("gguf_metadata")
        if not gguf_data:
            self.logger.debug("No GGUF metadata found in context")
            return {}

        self.logger.debug(f"GGUF metadata keys: {list(gguf_data.keys())}")
        return dict(gguf_data)

    def extract_gguf_model_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract model information from GGUF metadata."""
        gguf_data = context.get("gguf_metadata", {})
        if not gguf_data:
            return {}

        model_info = {}

        # Common GGUF metadata fields
        if "general.name" in gguf_data:
            model_info["name"] = gguf_data["general.name"]
        if "general.description" in gguf_data:
            model_info["description"] = gguf_data["general.description"]
        if "general.architecture" in gguf_data:
            model_info["architecture"] = gguf_data["general.architecture"]
        if "general.quantization_version" in gguf_data:
            model_info["quantization"] = gguf_data["general.quantization_version"]
        if "general.file_type" in gguf_data:
            model_info["file_type"] = gguf_data["general.file_type"]
        if "general.parameter_count" in gguf_data:
            model_info["parameter_count"] = gguf_data["general.parameter_count"]

        return model_info

    def extract_gguf_architecture_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract architecture information from GGUF metadata."""
        gguf_data = context.get("gguf_metadata", {})
        if not gguf_data:
            return {}

        arch_info = {}

        # Architecture-specific fields (examples for common architectures)
        arch_fields = [
            "llama.context_length", "llama.embedding_length", "llama.block_count",
            "llama.feed_forward_length", "llama.attention.head_count",
            "llama.attention.head_count_kv", "llama.attention.layer_norm_rms_epsilon",
            "llama.rope.dimension_count", "llama.rope.freq_base",
            "gpt2.context_length", "gpt2.embedding_length", "gpt2.block_count",
            "mistral.context_length", "mistral.embedding_length", "mistral.block_count"
        ]

        for field in arch_fields:
            if field in gguf_data:
                arch_info[field] = gguf_data[field]

        return arch_info

    def extract_model_file_info(
        self,
        data: Any,
        method_def: MethodDefinition,
        context: ContextData,
        fields: ExtractedFields,
    ) -> dict[str, Any]:
        """Extract general file information for model files."""
        if not isinstance(context, dict):
            return {}

        file_info = {}

        # Basic file information
        if "file_path_original" in context:
            file_info["file_path"] = context["file_path_original"]
        if "file_size" in context:
            file_info["file_size"] = context["file_size"]
        if "file_extension" in context:
            file_info["format"] = context["file_extension"].upper()
        if "file_modified_date" in context:
            file_info["modified_date"] = context["file_modified_date"]

        # Model type detection
        if context.get("file_extension") == "safetensors":
            file_info["model_format"] = "SafeTensors"
        elif context.get("file_extension") == "gguf":
            file_info["model_format"] = "GGUF"
        elif context.get("file_extension") in ["bin", "pt", "pth"]:
            file_info["model_format"] = "PyTorch"
        elif context.get("file_extension") == "ckpt":
            file_info["model_format"] = "Checkpoint"

        return file_info
