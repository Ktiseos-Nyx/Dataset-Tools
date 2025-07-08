# dataset_tools/vendored_sdpr/format/tensorart.py

import json
import logging
import re
from dataclasses import dataclass, field
from re import Pattern
from typing import Any

from .base_format import BaseFormat


@dataclass
class TensorArtConfig:
    """Configuration for TensorArt format parsing - systematically organized"""

    # TensorArt-specific identification patterns
    IDENTIFICATION_PATTERNS: dict[str, Pattern[str]] = field(
        default_factory=lambda: {
            "ems_model": re.compile(r"EMS-\d+-EMS\.safetensors", re.IGNORECASE),
            "ems_lora": re.compile(r"<lora:(EMS-\d+-EMS(?:\.safetensors)?)", re.IGNORECASE),
            "tensorart_job_id": re.compile(r"^\d{10,}$"),  # Long numeric strings typical of TensorArt
            "tensorart_prefix": re.compile(r"tensorart|tensor[_-]?art", re.IGNORECASE),
        }
    )

    # ComfyUI node types for parameter extraction
    COMFYUI_NODE_TYPES: dict[str, set[str]] = field(
        default_factory=lambda: {
            "ksampler": {
                "KSampler",
                "KSamplerAdvanced",
                "KSampler (Efficient)",
                "KSamplerSelect",
                "KSampler_A1111",
                "KSamplerCustom",
            },
            "checkpoint_loader": {
                "CheckpointLoader",
                "CheckpointLoaderSimple",
                "ECHOCheckpointLoaderSimple",
                "unCLIPCheckpointLoader",
                "CheckpointLoaderNF4",
            },
            "clip_text_encode": {
                "CLIPTextEncode",
                "BNK_CLIPTextEncodeAdvanced",
                "CLIPTextEncodeSDXL",
                "smZ CLIPTextEncode",
                "CLIPTextEncodeFlux",
            },
            "lora_loader": {
                "LoraLoader",
                "LoraTagLoader",
                "LoraLoaderModelOnly",
                "LoRA_Loader",
            },
            "save_image": {
                "SaveImage",
                "Image Save",
                "SaveImageWebsocket",
                "JWImageSave",
            },
            "empty_latent": {"EmptyLatentImage", "LatentFromBatch"},
        }
    )

    # Parameter mapping for ComfyUI node inputs to standard names
    PARAMETER_MAPPINGS: dict[str, str] = field(
        default_factory=lambda: {
            "seed": "seed",
            "steps": "steps",
            "cfg": "cfg_scale",
            "sampler_name": "sampler_name",
            "scheduler": "scheduler",
            "denoise": "denoising_strength",
            "width": "width",
            "height": "height",
            "batch_size": "batch_size",
            "ckpt_name": "model",
        }
    )

    # TensorArt-specific features to detect
    TENSORART_FEATURES: set[str] = field(
        default_factory=lambda: {
            "EMS",
            "tensorart_workflow",
            "community_model",
            "shared_workflow",
        }
    )


class TensorArtSignatureDetector:
    """Advanced signature detection for TensorArt identification"""

    def __init__(self, config: TensorArtConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def detect_tensorart_signatures(self, workflow_data: dict[str, Any]) -> dict[str, Any]:
        """Comprehensive TensorArt signature detection.
        Returns detailed analysis of found signatures.
        """
        detection_result = {
            "is_tensorart": False,
            "confidence_score": 0.0,
            "signatures_found": [],
            "ems_models_found": [],
            "ems_loras_found": [],
            "job_id_candidates": [],
            "node_analysis": {},
        }

        if not isinstance(workflow_data, dict):
            return detection_result

        # Analyze nodes for TensorArt signatures
        self._analyze_checkpoint_signatures(workflow_data, detection_result)
        self._analyze_lora_signatures(workflow_data, detection_result)
        self._analyze_save_image_signatures(workflow_data, detection_result)
        self._analyze_metadata_signatures(workflow_data, detection_result)

        # Calculate overall confidence
        detection_result["confidence_score"] = self._calculate_confidence_score(detection_result)

        # Determine if this is definitively TensorArt
        detection_result["is_tensorart"] = self._is_definitive_tensorart(detection_result)

        self.logger.debug(
            f"TensorArt detection: confidence={detection_result['confidence_score']:.2f}, "
            f"signatures={len(detection_result['signatures_found'])}"
        )

        return detection_result

    def _analyze_checkpoint_signatures(self, workflow_data: dict[str, Any], result: dict[str, Any]) -> None:
        """Analyze checkpoint loader nodes for EMS patterns"""
        for node_id, node_data in workflow_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if not any(
                class_type in node_types for node_types in [self.config.COMFYUI_NODE_TYPES["checkpoint_loader"]]
            ):
                continue

            inputs = node_data.get("inputs", {})
            ckpt_name = inputs.get("ckpt_name", "")

            if isinstance(ckpt_name, str) and self.config.IDENTIFICATION_PATTERNS["ems_model"].search(ckpt_name):
                result["ems_models_found"].append(
                    {
                        "node_id": node_id,
                        "model_name": ckpt_name,
                        "node_type": class_type,
                    }
                )
                result["signatures_found"].append("ems_checkpoint")
                self.logger.debug(f"TensorArt: Found EMS model in {node_id}: {ckpt_name}")

    def _analyze_lora_signatures(self, workflow_data: dict[str, Any], result: dict[str, Any]) -> None:
        """Analyze LoRA loader nodes for EMS patterns"""
        for node_id, node_data in workflow_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            inputs = node_data.get("inputs", {})

            # Check LoraLoader nodes
            if class_type in self.config.COMFYUI_NODE_TYPES["lora_loader"]:
                lora_name = inputs.get("lora_name", "")
                if isinstance(lora_name, str) and self.config.IDENTIFICATION_PATTERNS["ems_model"].search(lora_name):
                    result["ems_loras_found"].append(
                        {
                            "node_id": node_id,
                            "lora_name": lora_name,
                            "strength": inputs.get("strength_model", inputs.get("strength", 1.0)),
                            "node_type": class_type,
                        }
                    )
                    result["signatures_found"].append("ems_lora")

            # Check text inputs for embedded LoRA tags
            text_input = inputs.get("text", "")
            if isinstance(text_input, str) and "<lora:" in text_input:
                lora_matches = self.config.IDENTIFICATION_PATTERNS["ems_lora"].findall(text_input)
                for lora_match in lora_matches:
                    result["ems_loras_found"].append(
                        {
                            "node_id": node_id,
                            "lora_name": lora_match,
                            "source": "text_embedding",
                            "node_type": class_type,
                        }
                    )
                    result["signatures_found"].append("ems_lora_embedded")

    def _analyze_save_image_signatures(self, workflow_data: dict[str, Any], result: dict[str, Any]) -> None:
        """Analyze SaveImage nodes for TensorArt job ID patterns"""
        for node_id, node_data in workflow_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            if class_type not in self.config.COMFYUI_NODE_TYPES["save_image"]:
                continue

            inputs = node_data.get("inputs", {})
            filename_prefix = str(inputs.get("filename_prefix", ""))

            if self.config.IDENTIFICATION_PATTERNS["tensorart_job_id"].match(filename_prefix):
                result["job_id_candidates"].append(
                    {
                        "node_id": node_id,
                        "job_id": filename_prefix,
                        "node_type": class_type,
                    }
                )
                result["signatures_found"].append("job_id_pattern")
                self.logger.debug(f"TensorArt: Found potential job ID in {node_id}: {filename_prefix}")

    def _analyze_metadata_signatures(self, workflow_data: dict[str, Any], result: dict[str, Any]) -> None:
        """Analyze workflow metadata for TensorArt indicators"""
        # Check extraMetadata field
        extra_metadata = workflow_data.get("extraMetadata")
        if extra_metadata and isinstance(extra_metadata, str):
            try:
                metadata = json.loads(extra_metadata)
                if isinstance(metadata, dict):
                    # Look for TensorArt-specific metadata keys
                    tensorart_keys = []
                    for key in metadata.keys():
                        if self.config.IDENTIFICATION_PATTERNS["tensorart_prefix"].search(str(key)):
                            tensorart_keys.append(key)

                    if tensorart_keys:
                        result["signatures_found"].append("metadata_tensorart")
                        result["node_analysis"]["tensorart_metadata_keys"] = tensorart_keys

            except json.JSONDecodeError:
                pass

        # Check workflow-level fields for TensorArt indicators
        for key, value in workflow_data.items():
            if isinstance(key, str) and self.config.IDENTIFICATION_PATTERNS["tensorart_prefix"].search(key):
                result["signatures_found"].append("workflow_field")
                result["node_analysis"].setdefault("tensorart_workflow_keys", []).append(key)

    def _calculate_confidence_score(self, result: dict[str, Any]) -> float:
        """Calculate confidence score based on found signatures"""
        score = 0.0

        # EMS models are strong indicators
        score += len(result["ems_models_found"]) * 0.4

        # EMS LoRAs are strong indicators
        score += len(result["ems_loras_found"]) * 0.3

        # Job ID patterns are moderate indicators
        score += len(result["job_id_candidates"]) * 0.2

        # Metadata indicators are weak but supportive
        metadata_signatures = sum(
            1 for sig in result["signatures_found"] if sig in ["metadata_tensorart", "workflow_field"]
        )
        score += metadata_signatures * 0.1

        return min(score, 1.0)  # Cap at 1.0

    def _is_definitive_tensorart(self, result: dict[str, Any]) -> bool:
        """Determine if we have definitive proof this is TensorArt"""
        # Any EMS model or LoRA is definitive
        if result["ems_models_found"] or result["ems_loras_found"]:
            return True

        # High confidence with multiple signature types
        if result["confidence_score"] >= 0.8 and len(set(result["signatures_found"])) >= 2:
            return True

        return False


class TensorArtWorkflowParser:
    """Handles parsing of TensorArt ComfyUI workflows"""

    def __init__(self, config: TensorArtConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def parse_comfyui_workflow(self, workflow_data: dict[str, Any]) -> dict[str, Any]:
        """Parse TensorArt ComfyUI workflow for generation parameters.
        Returns structured extraction results.
        """
        result = {
            "positive": "",
            "negative": "",
            "parameters": {},
            "loras": [],
            "workflow_info": {},
            "parse_errors": [],
        }

        try:
            # Analyze workflow structure
            node_analysis = self._analyze_workflow_structure(workflow_data)
            result["workflow_info"] = node_analysis

            # Extract prompts
            prompts = self._extract_prompts(workflow_data, node_analysis)
            result.update(prompts)

            # Extract generation parameters
            parameters = self._extract_generation_parameters(workflow_data, node_analysis)
            result["parameters"] = parameters

            # Extract LoRA information
            loras = self._extract_lora_information(workflow_data, node_analysis)
            result["loras"] = loras

            self.logger.debug(f"TensorArt: Parsed workflow with {len(result['parameters'])} parameters")

        except Exception as e:
            self.logger.error(f"TensorArt: Workflow parsing error: {e}")
            result["parse_errors"].append(f"Workflow parsing failed: {e}")

        return result

    def _analyze_workflow_structure(self, workflow_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze the overall structure of the workflow"""
        analysis = {
            "total_nodes": len(workflow_data),
            "node_types": {},
            "ksampler_nodes": [],
            "text_encode_nodes": [],
            "checkpoint_nodes": [],
            "lora_nodes": [],
            "save_nodes": [],
            "latent_nodes": [],
        }

        for node_id, node_data in workflow_data.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "unknown")
            analysis["node_types"][class_type] = analysis["node_types"].get(class_type, 0) + 1

            # Categorize nodes
            if class_type in self.config.COMFYUI_NODE_TYPES["ksampler"]:
                analysis["ksampler_nodes"].append(node_id)
            elif class_type in self.config.COMFYUI_NODE_TYPES["clip_text_encode"]:
                analysis["text_encode_nodes"].append(node_id)
            elif class_type in self.config.COMFYUI_NODE_TYPES["checkpoint_loader"]:
                analysis["checkpoint_nodes"].append(node_id)
            elif class_type in self.config.COMFYUI_NODE_TYPES["lora_loader"]:
                analysis["lora_nodes"].append(node_id)
            elif class_type in self.config.COMFYUI_NODE_TYPES["save_image"]:
                analysis["save_nodes"].append(node_id)
            elif class_type in self.config.COMFYUI_NODE_TYPES["empty_latent"]:
                analysis["latent_nodes"].append(node_id)

        return analysis

    def _extract_prompts(self, workflow_data: dict[str, Any], analysis: dict[str, Any]) -> dict[str, str]:
        """Extract positive and negative prompts from text encode nodes"""
        prompts = {"positive": "", "negative": ""}

        # Get text from all CLIPTextEncode nodes
        text_nodes = {}
        for node_id in analysis["text_encode_nodes"]:
            node_data = workflow_data.get(node_id, {})
            inputs = node_data.get("inputs", {})
            text = inputs.get("text", "")
            if text:
                text_nodes[node_id] = text

        # Try to determine which is positive vs negative
        # This is complex in ComfyUI - for now, use heuristics
        if len(text_nodes) >= 2:
            # Heuristic: longer text is usually positive
            sorted_texts = sorted(text_nodes.items(), key=lambda x: len(x[1]), reverse=True)
            prompts["positive"] = sorted_texts[0][1]
            prompts["negative"] = sorted_texts[1][1]
        elif len(text_nodes) == 1:
            # Only one text node - assume positive
            prompts["positive"] = list(text_nodes.values())[0]

        return prompts

    def _extract_generation_parameters(self, workflow_data: dict[str, Any], analysis: dict[str, Any]) -> dict[str, str]:
        """Extract generation parameters from KSampler and other nodes"""
        parameters = {}

        # Extract from primary KSampler
        if analysis["ksampler_nodes"]:
            primary_ksampler_id = analysis["ksampler_nodes"][0]  # Simplified selection
            ksampler_data = workflow_data.get(primary_ksampler_id, {})
            ksampler_inputs = ksampler_data.get("inputs", {})

            for input_key, param_key in self.config.PARAMETER_MAPPINGS.items():
                if input_key in ksampler_inputs:
                    value = ksampler_inputs[input_key]
                    if value is not None:
                        parameters[param_key] = str(value)

        # Extract model from checkpoint loader
        if analysis["checkpoint_nodes"]:
            checkpoint_id = analysis["checkpoint_nodes"][0]
            checkpoint_data = workflow_data.get(checkpoint_id, {})
            checkpoint_inputs = checkpoint_data.get("inputs", {})
            ckpt_name = checkpoint_inputs.get("ckpt_name")
            if ckpt_name:
                parameters["model"] = self._process_model_name(ckpt_name)

        # Extract dimensions from EmptyLatentImage
        if analysis["latent_nodes"]:
            latent_id = analysis["latent_nodes"][0]
            latent_data = workflow_data.get(latent_id, {})
            latent_inputs = latent_data.get("inputs", {})

            width = latent_inputs.get("width")
            height = latent_inputs.get("height")
            if width and height:
                parameters["width"] = str(width)
                parameters["height"] = str(height)
                parameters["size"] = f"{width}x{height}"

        return parameters

    def _extract_lora_information(
        self, workflow_data: dict[str, Any], analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract LoRA information from LoRA loader nodes"""
        loras = []

        for node_id in analysis["lora_nodes"]:
            node_data = workflow_data.get(node_id, {})
            class_type = node_data.get("class_type", "")
            inputs = node_data.get("inputs", {})

            lora_info = {"node_id": node_id, "node_type": class_type}

            if "LoraLoader" in class_type:
                lora_info["name"] = inputs.get("lora_name", "unknown")
                lora_info["model_strength"] = inputs.get("strength_model", 1.0)
                lora_info["clip_strength"] = inputs.get("strength_clip", 1.0)
            elif "LoraTagLoader" in class_type:
                text = inputs.get("text", "")
                lora_match = re.search(r"<lora:([^:]+):([0-9\.]+)>", text)
                if lora_match:
                    lora_info["name"] = lora_match.group(1)
                    lora_info["strength"] = float(lora_match.group(2))

            if "name" in lora_info:
                loras.append(lora_info)

        return loras

    def _process_model_name(self, model_name: str) -> str:
        """Process model name to extract clean identifier"""
        if not model_name:
            return ""

        # Remove path and extension
        name = model_name.split("/")[-1]  # Get filename
        name = name.replace(".safetensors", "").replace(".ckpt", "")

        return name


class TensorArtFormat(BaseFormat):
    """Enhanced TensorArt format parser with ComfyUI workflow intelligence.

    TensorArt uses ComfyUI workflows with specific identifiers:
    - EMS-numbered model files (EMS-####-EMS.safetensors)
    - Long numeric job IDs in SaveImage filename_prefix
    - Community-shared workflows and models
    """

    tool = "TensorArt"

    def __init__(
        self,
        info: dict[str, Any] | None = None,
        raw: str = "",
        width: Any = 0,
        height: Any = 0,
        logger_obj: logging.Logger | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            info=info,
            raw=raw,
            width=width,
            height=height,
            logger_obj=logger_obj,
            **kwargs,
        )

        # Initialize components
        self.config = TensorArtConfig()
        self.signature_detector = TensorArtSignatureDetector(self.config, self._logger)
        self.workflow_parser = TensorArtWorkflowParser(self.config, self._logger)

        # Store processing results
        self.workflow_data: dict[str, Any] | None = None
        self._detection_result: dict[str, Any] | None = None
        self._parse_result: dict[str, Any] | None = None

    def _process(self) -> None:
        """Main processing pipeline for TensorArt format"""
        self._logger.debug(f"{self.tool}: Starting TensorArt format processing")

        # Validate input data
        if not self._raw:
            self._logger.warning(f"{self.tool}: No raw data provided")
            self.status = self.Status.MISSING_INFO
            self._error = "No raw data provided for TensorArt parsing"
            return

        # Parse ComfyUI workflow JSON
        try:
            self.workflow_data = json.loads(self._raw)
            if not isinstance(self.workflow_data, dict):
                self.status = self.Status.FORMAT_DETECTION_ERROR
                self._error = "Raw data is not a ComfyUI JSON dictionary"
                return

        except json.JSONDecodeError as e:
            self.status = self.Status.FORMAT_DETECTION_ERROR
            self._error = f"Invalid ComfyUI JSON: {e}"
            return

        # Detect TensorArt signatures
        self._detection_result = self.signature_detector.detect_tensorart_signatures(self.workflow_data)

        if not self._detection_result["is_tensorart"]:
            confidence = self._detection_result["confidence_score"]
            signatures = len(self._detection_result["signatures_found"])
            self._logger.debug(
                f"{self.tool}: Not identified as TensorArt (confidence: {confidence:.2f}, signatures: {signatures})"
            )
            self.status = self.Status.FORMAT_DETECTION_ERROR
            self._error = "ComfyUI JSON does not have TensorArt-specific markers"
            return

        # Parse workflow for parameters
        self._parse_result = self.workflow_parser.parse_comfyui_workflow(self.workflow_data)

        if self._parse_result["parse_errors"]:
            errors = self._parse_result["parse_errors"]
            self._logger.warning(f"{self.tool}: Parse errors: {errors}")
            if not self._parse_result["parameters"] and not self._parse_result["positive"]:
                self.status = self.Status.FORMAT_ERROR
                self._error = f"TensorArt workflow parsing failed: {'; '.join(errors)}"
                return

        # Apply parsing results
        self._apply_parse_results()

        # Validate extraction success
        if not self._has_meaningful_extraction():
            self._logger.warning(f"{self.tool}: No meaningful data extracted")
            self.status = self.Status.FORMAT_ERROR
            self._error = "TensorArt parsing yielded no meaningful data"
            return

        self._logger.info(
            f"{self.tool}: Successfully parsed with {self._detection_result['confidence_score']:.2f} confidence"
        )

    def _apply_parse_results(self) -> None:
        """Apply parsing results to instance variables"""
        if not self._parse_result:
            return

        # Apply prompts
        self._positive = self._parse_result["positive"]
        self._negative = self._parse_result["negative"]

        # Apply parameters
        parameters = self._parse_result["parameters"]
        self._parameter.update(parameters)

        # Apply dimensions
        if "width" in parameters:
            self._width = parameters["width"]
        if "height" in parameters:
            self._height = parameters["height"]

        # Add LoRA information to parameters
        loras = self._parse_result["loras"]
        if loras:
            self._parameter["loras"] = self._format_loras_for_display(loras)

        # Add TensorArt-specific metadata
        if self._detection_result:
            ems_models = self._detection_result["ems_models_found"]
            if ems_models:
                self._parameter["tensorart_ems_models"] = str(len(ems_models))

            job_ids = self._detection_result["job_id_candidates"]
            if job_ids:
                self._parameter["tensorart_job_id"] = job_ids[0]["job_id"]

        # Build settings string
        self._build_tensorart_settings()

    def _format_loras_for_display(self, loras: list[dict[str, Any]]) -> str:
        """Format LoRA information for display"""
        if not loras:
            return ""

        formatted_loras = []
        for lora in loras:
            name = lora.get("name", "unknown")
            if "strength" in lora:
                formatted_loras.append(f"{name}:{lora['strength']}")
            elif "model_strength" in lora:
                formatted_loras.append(f"{name}:{lora['model_strength']}")
            else:
                formatted_loras.append(name)

        return ", ".join(formatted_loras)

    def _build_tensorart_settings(self) -> None:
        """Build settings string from workflow analysis"""
        if not self._parse_result:
            return

        workflow_info = self._parse_result["workflow_info"]
        settings_parts = []

        # Add workflow structure info
        if workflow_info.get("total_nodes"):
            settings_parts.append(f"Nodes: {workflow_info['total_nodes']}")

        # Add node type summary
        node_types = workflow_info.get("node_types", {})
        if node_types:
            type_summary = ", ".join(f"{k}: {v}" for k, v in sorted(node_types.items()) if v > 0)
            if type_summary:
                settings_parts.append(f"Node types: {type_summary}")

        self._setting = "; ".join(settings_parts)

    def _has_meaningful_extraction(self) -> bool:
        """Check if extraction yielded meaningful data"""
        has_prompts = bool(self._positive.strip())
        has_parameters = self._parameter_has_data()
        has_dimensions = self._width != "0" or self._height != "0"

        return has_prompts or has_parameters or has_dimensions

    def get_format_info(self) -> dict[str, Any]:
        """Get detailed information about the parsed TensorArt data"""
        return {
            "format_name": self.tool,
            "detection_result": self._detection_result,
            "has_positive_prompt": bool(self._positive),
            "has_negative_prompt": bool(self._negative),
            "parameter_count": len(
                [v for v in self._parameter.values() if v and v != self.DEFAULT_PARAMETER_PLACEHOLDER]
            ),
            "has_dimensions": self._width != "0" or self._height != "0",
            "dimensions": (f"{self._width}x{self._height}" if self._width != "0" and self._height != "0" else None),
            "tensorart_features": self._analyze_tensorart_features(),
        }

    def _analyze_tensorart_features(self) -> dict[str, Any]:
        """Analyze TensorArt-specific features detected"""
        features = {
            "has_ems_models": False,
            "has_ems_loras": False,
            "has_job_id": False,
            "has_community_features": False,
            "ems_model_count": 0,
            "ems_lora_count": 0,
            "feature_summary": [],
        }

        if not self._detection_result:
            return features

        # EMS model detection
        ems_models = self._detection_result["ems_models_found"]
        features["has_ems_models"] = bool(ems_models)
        features["ems_model_count"] = len(ems_models)
        if ems_models:
            features["feature_summary"].append(f"EMS models: {len(ems_models)}")

        # EMS LoRA detection
        ems_loras = self._detection_result["ems_loras_found"]
        features["has_ems_loras"] = bool(ems_loras)
        features["ems_lora_count"] = len(ems_loras)
        if ems_loras:
            features["feature_summary"].append(f"EMS LoRAs: {len(ems_loras)}")

        # Job ID detection
        job_ids = self._detection_result["job_id_candidates"]
        features["has_job_id"] = bool(job_ids)
        if job_ids:
            features["feature_summary"].append("Job ID present")

        # Community features
        signatures = self._detection_result["signatures_found"]
        community_sigs = [sig for sig in signatures if "metadata" in sig or "workflow" in sig]
        features["has_community_features"] = bool(community_sigs)
        if community_sigs:
            features["feature_summary"].append("Community features")

        return features

    def debug_tensorart_detection(self) -> dict[str, Any]:
        """Get comprehensive debugging information about TensorArt detection"""
        return {
            "input_data": {
                "has_raw": bool(self._raw),
                "raw_length": len(self._raw) if self._raw else 0,
                "raw_preview": self._raw[:200] if self._raw else None,
                "workflow_parsed": bool(self.workflow_data),
                "workflow_node_count": (len(self.workflow_data) if self.workflow_data else 0),
            },
            "detection_details": self._detection_result,
            "parsing_details": self._parse_result,
            "workflow_analysis": {
                "workflow_structure": (self._parse_result.get("workflow_info", {}) if self._parse_result else {}),
                "extracted_features": self._analyze_tensorart_features(),
            },
            "config_info": {
                "identification_patterns": list(self.config.IDENTIFICATION_PATTERNS.keys()),
                "supported_node_types": {k: len(v) for k, v in self.config.COMFYUI_NODE_TYPES.items()},
                "parameter_mappings": len(self.config.PARAMETER_MAPPINGS),
                "tensorart_features": len(self.config.TENSORART_FEATURES),
            },
        }
