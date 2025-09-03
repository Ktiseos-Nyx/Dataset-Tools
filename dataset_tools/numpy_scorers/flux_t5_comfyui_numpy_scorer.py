"""FLUX/T5 ComfyUI Numpy Scorer

Specialized scorer for FLUX workflows that use T5TextEncode, BasicGuider,
and other FLUX-specific node architectures. Handles guider chains and
T5 conditioning workflows that are different from standard ComfyUI patterns.
"""

import json
import time
from pathlib import Path
from typing import Any

from ..logger import get_logger
from .base_numpy_scorer import RUNTIME_ANALYTICS, WORKFLOW_CACHE, BaseNumpyScorer

logger = get_logger(__name__)


class FluxT5ComfyUINumpyScorer(BaseNumpyScorer):
    """Specialized numpy scorer for FLUX/T5 ComfyUI workflows."""

    def __init__(self):
        super().__init__()
        self.logger = get_logger(f"{__name__}.FluxT5ComfyUINumpyScorer")

        # FLUX-specific node types
        self.FLUX_SAMPLER_NODES = {
            "SamplerCustomAdvanced",
            "SamplerCustom",
            "FluxSampler"
        }

        self.FLUX_GUIDER_NODES = {
            "BasicGuider",
            "CFGGuider",
            "FluxGuider"
        }

        self.T5_ENCODER_NODES = {
            "T5TextEncode",
            "PixArtT5TextEncode",
            "CLIPTextEncodeFlux"
        }

        self.FLUX_CONDITIONING_NODES = {
            "FluxGuidance",
            "ConditioningSetTimestepRange"
        }

        # Performance limits
        self.MAX_DEPTH = 10
        self.MAX_CANDIDATES = 50

        # Keywords for prompt type identification
        self.positive_keywords = [
            "masterpiece", "high quality", "detailed", "beautiful", "best quality",
            "intricate", "photorealistic", "cinematic", "portrait", "landscape",
            "anime", "realistic", "stunning", "gorgeous", "amazing", "professional",
            "artstation", "8k", "4k", "ultra detailed", "sharp focus", "vivid colors"
        ]

        self.negative_keywords = [
            "worst quality", "low quality", "bad", "blurry", "ugly", "deformed",
            "nsfw", "bad anatomy", "missing", "distorted", "jpeg artifacts",
            "watermark", "signature", "logo", "cropped", "out of frame",
            "text overlay", "boring", "amateur", "pixelated", "overexposed",
            "mutation", "mutated", "extra limb", "extra hands", "poorly drawn", "lowres"
        ]

        self.technical_terms = [
            "lanczos", "bilinear", "ddim", "euler", "dpmpp", "cfg", "randomize",
            "steps", "sampler", "scheduler", "denoise", "seed", "checkpoint",
            "lora", "embedding", "hypernetwork", "vae", "controlnet"
        ]

    def extract_text_candidates_from_workflow(self, workflow_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract candidates from FLUX/T5 workflows using guider-centric tracing."""
        start_time = time.time()
        candidates = []

        try:
            self.logger.debug("Starting FLUX/T5 workflow analysis")

            nodes = workflow_data.get("nodes", [])
            links = workflow_data.get("links", [])

            if not nodes:
                self.logger.warning("No nodes found in workflow")
                return candidates

            # Build link mapping for backwards tracing
            link_map = self._build_link_map(workflow_data)
            self.logger.debug(f"Built link map with {len(link_map)} connections")

            # STEP 1: Find FLUX samplers as entry points
            flux_samplers = self._find_flux_samplers(nodes)
            self.logger.debug(f"Found {len(flux_samplers)} FLUX samplers")

            # STEP 2: Trace from samplers through guiders to conditioning
            for sampler in flux_samplers:
                sampler_candidates = self._trace_flux_sampler_conditioning(
                    sampler, link_map, nodes
                )
                candidates.extend(sampler_candidates)

            # STEP 3: Direct T5 node extraction as fallback
            direct_candidates = self._extract_direct_t5_candidates(nodes)
            candidates.extend(direct_candidates)

            # STEP 4: Score and rank candidates
            scored_candidates = []
            for candidate in candidates:
                scored = self.score_candidate(candidate, "flux_t5")
                scored_candidates.append(scored)

            # Sort by confidence
            scored_candidates.sort(key=lambda x: x.get("confidence", 0), reverse=True)

            processing_time = time.time() - start_time
            self._track_analytics("extract_flux_candidates", True, processing_time, "flux_t5")

            self.logger.debug(f"FLUX extraction completed: {len(scored_candidates)} candidates in {processing_time:.3f}s")
            return scored_candidates[:self.MAX_CANDIDATES]

        except Exception as e:
            self.logger.error(f"Error in FLUX workflow extraction: {e}")
            processing_time = time.time() - start_time
            self._track_analytics("extract_flux_candidates", False, processing_time, "flux_t5")
            return []

    def _build_link_map(self, workflow_data: dict[str, Any]) -> dict[int, dict[str, Any]]:
        """Build mapping from link IDs to source nodes for backwards tracing."""
        link_map = {}
        links = workflow_data.get("links", [])
        nodes = workflow_data.get("nodes", [])

        # Create node lookup by ID
        node_by_id = {}
        for node in nodes:
            if isinstance(node, dict):
                node_id = node.get("id")
                if node_id is not None:
                    node_by_id[node_id] = node

        # Map each link to its source node
        for link in links:
            if isinstance(link, list) and len(link) >= 5:
                link_id = link[0]
                source_node_id = link[1]
                source_slot = link[2]
                target_node_id = link[3]
                target_slot = link[4]

                if source_node_id in node_by_id:
                    source_node = node_by_id[source_node_id]
                    link_map[link_id] = {
                        "node": source_node,
                        "source_node_type": source_node.get("type") or source_node.get("class_type", ""),
                        "source_slot": source_slot,
                        "target_node_id": target_node_id,
                        "target_slot": target_slot
                    }

        return link_map

    def _find_flux_samplers(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find FLUX sampler nodes as tracing entry points."""
        samplers = []

        for node in nodes:
            if not isinstance(node, dict):
                continue

            node_type = node.get("type") or node.get("class_type", "")
            if node_type in self.FLUX_SAMPLER_NODES:
                samplers.append(node)

        return samplers

    def _trace_flux_sampler_conditioning(
        self, sampler_node: dict[str, Any], link_map: dict[int, dict[str, Any]], all_nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Trace FLUX sampler inputs to find conditioning through guider chains."""
        candidates = []
        inputs = sampler_node.get("inputs", [])
        sampler_id = sampler_node.get("id")
        sampler_type = sampler_node.get("type") or sampler_node.get("class_type", "")

        self.logger.debug(f"Tracing FLUX sampler {sampler_id} ({sampler_type})")

        for input_def in inputs:
            input_name = input_def.get("name", "")
            input_type = input_def.get("type", "")
            link_id = input_def.get("link")

            self.logger.debug(f"  Input: {input_name} ({input_type}) -> link {link_id}")

            # FLUX samplers use "guider" input instead of direct conditioning
            if input_type == "GUIDER" and input_name == "guider":
                self.logger.debug("  Found GUIDER input, tracing guider chain")
                if isinstance(link_id, int) and link_id in link_map:
                    guider_candidates = self._trace_guider_chain(link_id, link_map, all_nodes)
                    self.logger.debug(f"  Guider chain returned {len(guider_candidates)} candidates")
                    candidates.extend(guider_candidates)
                else:
                    self.logger.debug(f"  Guider link {link_id} not found in link_map")

        return candidates

    def _trace_guider_chain(self, link_id: int, link_map: dict[int, dict[str, Any]], all_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Trace through FLUX guider chain to find conditioning."""
        candidates = []

        self.logger.debug(f"Tracing guider chain from link {link_id}")

        if link_id not in link_map:
            self.logger.debug(f"Link {link_id} not found in link_map")
            return candidates

        source_info = link_map[link_id]
        source_node = source_info["node"]
        source_node_type = source_info["source_node_type"]
        source_node_id = source_node.get("id")

        self.logger.debug(f"Found source node {source_node_id} ({source_node_type})")

        # BasicGuider has conditioning input
        if source_node_type == "BasicGuider":
            source_inputs = source_node.get("inputs", [])
            self.logger.debug(f"BasicGuider has {len(source_inputs)} inputs")
            for input_def in source_inputs:
                input_name = input_def.get("name")
                input_type = input_def.get("type")
                self.logger.debug(f"  BasicGuider input: {input_name} ({input_type})")
                if input_def.get("name") == "conditioning" and input_def.get("type") == "CONDITIONING":
                    conditioning_link_id = input_def.get("link")
                    self.logger.debug(f"  Found conditioning link {conditioning_link_id}, tracing...")
                    if isinstance(conditioning_link_id, int):
                        conditioning_candidates = self._trace_conditioning_chain(conditioning_link_id, link_map, all_nodes, "positive")
                        self.logger.debug(f"  Conditioning chain returned {len(conditioning_candidates)} candidates")
                        candidates.extend(conditioning_candidates)
        else:
            self.logger.debug(f"Expected BasicGuider, got {source_node_type}")

        return candidates

    def _trace_conditioning_chain(self, link_id: int, link_map: dict[int, dict[str, Any]], all_nodes: list[dict[str, Any]], prompt_type: str, depth: int = 0) -> list[dict[str, Any]]:
        """Recursively trace through conditioning nodes to find T5 text sources."""
        candidates = []
        if depth > self.MAX_DEPTH:
            return candidates

        if link_id not in link_map:
            return candidates

        source_info = link_map[link_id]
        source_node = source_info["node"]
        source_node_type = source_info["source_node_type"]

        # If this is a T5 encoding node, extract the text
        if source_node_type in self.T5_ENCODER_NODES:
            text_content = self._extract_t5_text_from_node(source_node, source_info)
            if text_content:
                candidates.append({
                    "text": text_content,
                    "node_type": source_node_type,
                    "source": "t5_connected",
                    "prompt_type": prompt_type,
                    "is_connected": True,
                    "connection_strength": 1.0,
                    "target_node_type": source_node_type,
                    "target_node_id": source_node.get("id"),
                    "node_title": source_node.get("title", "")
                })
        else:
            # Continue tracing through intermediate nodes (FluxGuidance, etc.)
            source_inputs = source_node.get("inputs", [])
            for input_def in source_inputs:
                if input_def.get("type") == "CONDITIONING":
                    next_link_id = input_def.get("link")
                    if isinstance(next_link_id, int):
                        candidates.extend(self._trace_conditioning_chain(next_link_id, link_map, all_nodes, prompt_type, depth + 1))

        return candidates

    def _extract_t5_text_from_node(self, node: dict[str, Any], source_info: dict[str, Any]) -> str:
        """Extract text content from T5 encoder nodes."""
        inputs = node.get("inputs", {})
        class_type = node.get("class_type") or node.get("type", "")
        widgets_values = node.get("widgets_values", [])

        self.logger.debug(f"Extracting T5 text from {class_type}")

        # T5 nodes typically use "text" input
        if isinstance(inputs, dict) and "text" in inputs:
            return str(inputs.get("text", ""))
        if len(widgets_values) >= 1:
            return str(widgets_values[0])

        return ""

    def _extract_direct_t5_candidates(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Direct extraction from T5 nodes as fallback when tracing fails."""
        candidates = []

        for node in nodes:
            if not isinstance(node, dict):
                continue

            node_type = node.get("type") or node.get("class_type", "")
            if node_type in self.T5_ENCODER_NODES:
                text = self._extract_t5_text_from_node(node, {})
                if text and len(text.strip()) > 0:
                    candidates.append({
                        "text": text.strip(),
                        "node_type": node_type,
                        "source": "t5_direct",
                        "prompt_type": "positive",  # Default assumption
                        "is_connected": False,
                        "connection_strength": 0.5,  # Lower confidence for direct extraction
                        "target_node_type": node_type,
                        "target_node_id": node.get("id"),
                        "node_title": node.get("title", "")
                    })

        return candidates

    def _trace_dynamic_prompt_outputs(self, dp_node: dict[str, Any], link_map: dict[int, dict[str, Any]], all_nodes: list[dict[str, Any]], depth: int = 0) -> list[dict[str, Any]]:
        """Trace the outputs of a DPRandomGenerator to find where the generated content goes.
        
        The typical chain is: DPRandomGenerator → ConcatStringSingle → T5TextEncode/CLIPTextEncodeFlux
        We need to follow STRING connections to find the final generated text.
        """
        candidates = []

        if depth > self.MAX_DEPTH:
            return candidates

        dp_node_id = dp_node.get("id")
        dp_node_type = dp_node.get("type", "")

        self.logger.debug(f"Tracing dynamic prompt outputs from {dp_node_type} node {dp_node_id} (depth: {depth})")

        # Find all links where this node is the source
        dp_output_links = []
        for link_id, link_info in link_map.items():
            source_node = link_info.get("node", {})
            if source_node.get("id") == dp_node_id:
                dp_output_links.append((link_id, link_info))
                target_node_type = link_info.get("source_node_type", "unknown")
                self.logger.debug(f"Found output link {link_id} from DPRandomGenerator → {target_node_type}")

        # Follow each output
        for link_id, link_info in dp_output_links:
            target_node_id = link_info.get("target_node_id")
            if not target_node_id:
                continue

            # Find the target node
            target_node = None
            for node in all_nodes:
                if node.get("id") == target_node_id:
                    target_node = node
                    break

            if not target_node:
                self.logger.debug(f"Could not find target node {target_node_id}")
                continue

            target_node_type = target_node.get("type", "")
            self.logger.debug(f"Following DPRandomGenerator output to {target_node_type} node {target_node_id}")

            # Handle different target node types in the dynamic prompt chain
            if target_node_type == "ConcatStringSingle":
                # This is a concatenation node - trace its outputs to find the final result
                self.logger.debug("Found ConcatStringSingle, tracing its outputs")
                concat_candidates = self._trace_dynamic_prompt_outputs(target_node, link_map, all_nodes, depth + 1)
                candidates.extend(concat_candidates)

            elif target_node_type == "ShowText|pysssss":
                # This might be a display node showing the generated result
                self.logger.debug("Found ShowText|pysssss display node, extracting content")
                display_content = self._extract_t5_text_from_node(target_node, link_info)
                if display_content and len(display_content) > 20:  # Substantial content
                    candidates.append({
                        "text": display_content,
                        "node_type": target_node_type,
                        "source": "dp_generated_display",
                        "prompt_type": "positive",  # Assume positive for generated content
                        "is_connected": True,
                        "connection_strength": 0.8,  # Lower than final generation (1.2)
                        "target_node_type": target_node_type,
                        "target_node_id": target_node_id
                    })
                    self.logger.debug(f"Extracted dynamic prompt result: '{display_content[:60]}...'")

            elif target_node_type in self.T5_ENCODER_NODES:
                # This is the final destination - the T5 text encoder
                self.logger.debug(f"Found final T5 encoder {target_node_type}, checking for generated content")

                # FIRST: Try to get content from the target encoder node (if it has widgets)
                encoder_content = self._extract_t5_text_from_node(target_node, link_info)

                # SECOND: If encoder is empty, extract from the source DPRandomGenerator instead
                if not encoder_content or len(encoder_content.strip()) < 10:
                    self.logger.debug("Target encoder is empty, extracting from DPRandomGenerator source")
                    # Use generic text extraction for DP node
                    inputs = dp_node.get("inputs", {})
                    widgets_values = dp_node.get("widgets_values", [])
                    if isinstance(inputs, dict) and "text" in inputs:
                        dp_content = str(inputs.get("text", ""))
                    elif len(widgets_values) >= 1:
                        dp_content = str(widgets_values[0])
                    else:
                        dp_content = ""

                    if dp_content and len(dp_content.strip()) > 20:
                        encoder_content = dp_content
                        self.logger.debug(f"Using DPRandomGenerator content: '{encoder_content[:60]}...'")

                if encoder_content and len(encoder_content.strip()) > 20:  # Substantial content, likely generated
                    candidates.append({
                        "text": encoder_content.strip(),
                        "node_type": "DPRandomGenerator",  # Mark as DP-generated
                        "source": "dp_generated_final",
                        "prompt_type": "positive",  # Assume positive for generated content
                        "is_connected": True,
                        "connection_strength": 1.2,  # High strength for final generated content
                        "target_node_type": target_node_type,
                        "target_node_id": target_node_id
                    })
                    self.logger.debug(f"Found final generated content: '{encoder_content[:60]}...'")

            else:
                # Unknown node type in the chain - continue tracing
                self.logger.debug(f"Unknown node type {target_node_type} in dynamic prompt chain, continuing trace")
                unknown_candidates = self._trace_dynamic_prompt_outputs(target_node, link_map, all_nodes, depth + 1)
                candidates.extend(unknown_candidates)

        self.logger.debug(f"Dynamic prompt tracing from node {dp_node_id} found {len(candidates)} candidates")
        return candidates

    def _extract_all_concatenation_inputs(self, concat_node: dict[str, Any], link_map: dict[int, dict[str, Any]], depth: int = 0) -> list[str]:
        """Extract all STRING inputs from a concatenation node and return their combined text."""
        texts = []
        inputs = concat_node.get("inputs", [])
        concat_id = concat_node.get("id")

        # Performance optimization: limit recursion depth for concatenation tracing
        if depth > self.MAX_DEPTH:
            self.logger.debug(f"Concatenation tracing depth limit reached at node {concat_id}")
            return texts

        self.logger.debug(f"Extracting concatenation inputs from node {concat_id} with {len(inputs)} inputs (depth: {depth})")

        # Performance optimization: limit number of inputs processed
        max_inputs = min(len(inputs), 10)  # Process at most 10 inputs

        for i, input_def in enumerate(inputs[:max_inputs]):
            input_name = input_def.get("name", "")
            input_type = input_def.get("type", "")
            link_id = input_def.get("link")

            self.logger.debug(f"Checking input {i+1}/{max_inputs} '{input_name}' (type: {input_type}, link: {link_id})")

            # Only process STRING inputs (text content)
            if input_type == "STRING" and isinstance(link_id, int) and link_id in link_map:
                source_info = link_map[link_id]
                source_node = source_info["node"]
                source_node_type = source_info.get("source_node_type", "")

                # Extract text from this input source (use T5 extraction method)
                text_content = self._extract_t5_text_from_node(source_node, source_info)
                if text_content:
                    self.logger.debug(f"Found input text from node {source_node.get('id')} ({source_node_type}): '{text_content[:60]}...'")
                    texts.append(text_content)

                    # Performance optimization: early exit if we have enough good content
                    if len(texts) >= 5 and len(text_content) > 50:  # 5 substantial inputs is plenty
                        self.logger.debug(f"Early exit from concatenation - have {len(texts)} substantial inputs")
                        break
                else:
                    self.logger.debug(f"No text content from node {source_node.get('id')} ({source_node_type})")
            else:
                self.logger.debug(f"Skipping non-STRING input '{input_name}' or no link")

        if len(inputs) > max_inputs:
            self.logger.debug(f"Concatenation node {concat_id} had {len(inputs)} inputs but only processed {max_inputs} for performance")

        self.logger.debug(f"Concatenation node {concat_id} collected {len(texts)} text inputs")
        return texts

    def score_text_candidate(self, candidate: dict[str, Any], workflow_type: str = "flux_t5") -> dict[str, Any]:
        """Enhanced FLUX/T5 scoring with comprehensive text analysis."""
        # Use the same comprehensive scoring as Advanced but with T5-specific adjustments
        text = candidate["text"]
        score = 0
        reasons = []
        prompt_type = candidate.get("prompt_type", "unknown")
        confidence_modifier = 0

        # Template detection (heavy penalty)
        is_template = self._is_template_text(text)
        if is_template:
            score -= 10
            reasons.append("TEMPLATE/DEFAULT DETECTED")
            confidence_modifier = -3
            self.logger.info(f"TEMPLATE DETECTED in FLUX candidate: '{text[:50]}...' - applying -10 penalty")

        # Length heuristics
        text_len = len(text)
        if text_len > 200:
            score += 4
            reasons.append("very long")
        elif text_len > 100:
            score += 3
            reasons.append("substantial length")
        elif text_len > 50:
            score += 2
            reasons.append("moderate length")
        elif text_len > 15:
            score += 1
            reasons.append("short but viable")

        # Quality indicators for FLUX/T5
        quality_indicators = ["masterpiece", "best quality", "absurdres", "depth of field", "dynamic angle", "photorealistic"]
        quality_count = sum(1 for indicator in quality_indicators if indicator in text.lower())
        if quality_count >= 2:
            score += quality_count * 5
            reasons.append(f"QUALITY_INDICATORS({quality_count})")

        # Multi-language support (especially important for T5)
        non_latin_chars = sum(1 for c in text if ord(c) > 127)
        if non_latin_chars > 0:
            has_cjk = any(0x4e00 <= ord(c) <= 0x9fff or 0x3400 <= ord(c) <= 0x4dbf or
                         0x3040 <= ord(c) <= 0x309f or 0x30a0 <= ord(c) <= 0x30ff for c in text)
            has_cyrillic = any(0x0400 <= ord(c) <= 0x04ff for c in text)
            has_arabic = any(0x0600 <= ord(c) <= 0x06ff for c in text)

            if has_cjk:
                score += 4  # Extra boost for T5 CJK handling
                reasons.append("CJK_CONTENT_T5_OPTIMIZED")
                if len(text) > 50:
                    score += 3
                    reasons.append("SUBSTANTIAL_CJK_T5")
            elif has_cyrillic:
                score += 3  # Good boost for T5 Cyrillic
                reasons.append("CYRILLIC_CONTENT_T5")
            elif has_arabic:
                score += 3
                reasons.append("ARABIC_CONTENT_T5")

        # FLUX/T5 specific node type bonuses
        node_type = candidate.get("node_type", "")
        if node_type in self.T5_ENCODER_NODES:
            score += 3  # T5 encoders are preferred in FLUX workflows
            reasons.append("T5_ENCODER_NODE")

        elif node_type in ["DPRandomGenerator", "ImpactWildcardProcessor"]:
            score += 4  # Dynamic content in FLUX workflows
            reasons.append("DYNAMIC_CONTENT_FLUX")

        # Connection scoring for FLUX
        source_type = candidate.get("source", "unknown")
        if source_type == "t5_connected":
            score += 6  # High boost for proper T5 connections
            reasons.append("T5_CONNECTED_SOURCE")
            confidence_modifier += 2

        elif source_type == "t5_direct":
            score += 3  # Direct T5 extraction
            reasons.append("T5_DIRECT_EXTRACTION")

        elif source_type in ["dp_generated_final", "dp_generated_display"]:
            score += 8  # Dynamic prompts in FLUX
            reasons.append("FLUX_DYNAMIC_GENERATED")
            confidence_modifier += 2

        # Structural complexity
        comma_count = text.count(",")
        if comma_count > 10:
            score += 3
            reasons.append("highly complex structure")
        elif comma_count > 5:
            score += 2
            reasons.append("complex structure")

        # Technical penalty
        tech_matches = sum(1 for term in self.technical_terms if term in text.lower())
        if tech_matches >= 2:
            score -= 2
            reasons.append("heavy technical terms")
        elif tech_matches >= 1:
            score -= 1
            reasons.append("technical terms")

        # Calculate final confidence
        final_score = max(0, score + confidence_modifier)
        if final_score >= 4:
            confidence = "HIGH"
        elif final_score >= 2:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        # Enhanced candidate
        enhanced_candidate = candidate.copy()
        enhanced_candidate.update({
            "raw_score": score,
            "final_score": final_score,
            "confidence": confidence,
            "prompt_type": prompt_type,
            "reasons": reasons,
            "is_template": is_template
        })

        return enhanced_candidate

    def score_candidate(self, candidate: dict[str, Any], format_type: str = "flux_t5") -> dict[str, Any]:
        """Score FLUX/T5 candidates with specialized logic."""
        # Start with base confidence from parent class
        scored_candidate = super().score_candidate(candidate, format_type)

        # FLUX-specific confidence adjustments
        confidence = scored_candidate.get("confidence", 0.5)

        # Boost confidence for proper T5 connections
        if candidate.get("source") == "t5_connected":
            confidence += 0.2

        # Boost for recognized T5 node types
        node_type = candidate.get("node_type", "")
        if node_type in self.T5_ENCODER_NODES:
            confidence += 0.15

        # Connection strength matters more in FLUX workflows
        connection_strength = candidate.get("connection_strength", 0)
        confidence += connection_strength * 0.1

        scored_candidate["confidence"] = min(1.0, confidence)
        scored_candidate["scoring_method"] = "flux_t5_numpy"

        return scored_candidate

    def enhance_engine_result(self, engine_result: dict[str, Any], original_file_path: str | None = None) -> dict[str, Any]:
        """Enhanced engine result processing for FLUX/T5 workflows with caching, analytics, and fallback chains."""
        self.start_time = time.time()
        self.logger.info("Starting enhanced FLUX/T5 numpy analysis of engine result")
        global WORKFLOW_CACHE, RUNTIME_ANALYTICS

        # Debug the engine_result structure
        self.logger.debug(f"engine_result keys: {list(engine_result.keys())}")
        for key, value in engine_result.items():
            if isinstance(value, dict):
                self.logger.debug(f"engine_result[{key}] is dict with keys: {list(value.keys())}")
            else:
                self.logger.debug(f"engine_result[{key}] type: {type(value)}")

        # Extract raw workflow data
        raw_metadata = engine_result.get("raw_metadata")
        workflow_data = None
        self.logger.debug(f"raw_metadata type: {type(raw_metadata)}")

        if raw_metadata:
            if isinstance(raw_metadata, dict):
                workflow_data = raw_metadata
                self.logger.debug("Using raw_metadata as dict directly")
        else:
            self.logger.debug("No raw_metadata found in engine_result")

        # If no workflow data from raw_metadata, try to read from original file (only if it's a JSON file)
        if not workflow_data and original_file_path:
            # Only try to read as text if it's likely a JSON file (not PNG/image files)
            file_ext = Path(original_file_path).suffix.lower() if original_file_path else ""
            if file_ext in [".json", ".txt"] or not file_ext:
                try:
                    self.logger.debug(f"Reading workflow data directly from JSON file: {original_file_path}")
                    with open(original_file_path, encoding="utf-8") as f:
                        workflow_data = json.load(f)
                    self.logger.debug("Successfully loaded workflow data from JSON file")
                except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
                    self.logger.debug(f"Could not read workflow from {original_file_path}: {e}")
            else:
                self.logger.debug(f"Skipping direct file read for non-JSON file: {file_ext}")

        # Try alternative metadata sources if still no workflow data
        if not workflow_data:
            # Check for workflow data in other engine_result fields
            for field in ["workflow", "raw_workflow", "comfyui_workflow", "_raw_data"]:
                if engine_result.get(field):
                    workflow_data = engine_result[field]
                    self.logger.debug(f"Found workflow data in engine_result.{field}")
                    break

        # Handle nested workflow structure (common in ComfyUI JSON files)
        if workflow_data and "workflow" in workflow_data and not workflow_data.get("nodes"):
            self.logger.debug("Detected nested workflow structure, extracting nodes")
            workflow_data = workflow_data["workflow"]

        # Debug output for workflow structure
        if workflow_data:
            self.logger.debug(f"Workflow data keys: {list(workflow_data.keys())}")
            self.logger.debug(f"Workflow data type: {type(workflow_data)}")
            nodes = workflow_data.get("nodes")
            if nodes is not None:
                self.logger.debug(f"Nodes found: {len(nodes) if isinstance(nodes, list) else 'not a list'}")
            else:
                self.logger.debug("No 'nodes' key in workflow_data")

        if not workflow_data:
            self.logger.warning("No valid workflow data found for analysis")
            processing_time = time.time() - self.start_time
            self._track_analytics("flux_t5_enhance", False, processing_time, "no_workflow")
            return engine_result

        # Classify workflow type and check cache - focus on FLUX/T5 detection
        workflow_type = self._classify_workflow_type(workflow_data)
        workflow_hash = self._get_workflow_hash(workflow_data)

        # Check cache first
        cache_key = f"{workflow_hash}:flux_t5:{workflow_type}"
        if cache_key in WORKFLOW_CACHE:
            RUNTIME_ANALYTICS["cache_hits"] += 1
            self.logger.debug(f"Cache hit for FLUX/T5 workflow {workflow_hash}")
            cached_result = WORKFLOW_CACHE[cache_key].copy()
            # Apply cached enhancements to current result
            enhanced_result = engine_result.copy()
            if cached_result.get("enhanced_prompt"):
                enhanced_result["prompt"] = cached_result["enhanced_prompt"]
            if cached_result.get("enhanced_negative"):
                enhanced_result["negative_prompt"] = cached_result["enhanced_negative"]
            processing_time = time.time() - self.start_time
            self._track_analytics("flux_t5_enhance_cached", True, processing_time, workflow_type)
            return enhanced_result

        RUNTIME_ANALYTICS["cache_misses"] += 1

        # Extract all text candidates from workflow with FLUX/T5 specialization
        candidates = self.extract_text_candidates_from_workflow(workflow_data)
        print(f"[DEBUG] Found {len(candidates)} text candidates in FLUX/T5 {workflow_type} workflow")

        if not candidates:
            print("[DEBUG] No text candidates found in FLUX/T5 workflow, enhancement failed")
            self.logger.info(f"No text candidates found in FLUX/T5 {workflow_type} workflow")
            processing_time = time.time() - self.start_time
            self._track_analytics("flux_t5_enhance", False, processing_time, workflow_type)
            return engine_result

        # Score all candidates with FLUX/T5 workflow type context
        scored_candidates = []
        high_quality_found = False

        for candidate in candidates:
            # Performance optimization: limit total candidates processed
            if len(scored_candidates) >= self.MAX_CANDIDATES:
                print(f"[DEBUG] Reached maximum candidates limit ({self.MAX_CANDIDATES}), stopping processing")
                break

            scored = self.score_text_candidate(candidate, "flux_t5")  # Use FLUX/T5 scoring
            if scored["final_score"] > 0:  # Only keep viable candidates
                scored_candidates.append(scored)
                # Performance optimization: early exit if we find high-quality candidates
                if scored["final_score"] >= self.EARLY_EXIT_SCORE:
                    high_quality_found = True
                    print(f"[DEBUG] Found high-quality FLUX/T5 candidate (score: {scored['final_score']:.1f})")

            # Performance optimization: if we found high-quality candidates, limit further processing
            if high_quality_found and len(scored_candidates) >= self.MAX_CANDIDATES:
                print(f"[DEBUG] Reached maximum candidates ({self.MAX_CANDIDATES}), stopping processing")
                break

        print(f"[DEBUG] {len(scored_candidates)} viable FLUX/T5 candidates after scoring")

        if not scored_candidates:
            print("[DEBUG] No viable FLUX/T5 candidates after scoring, enhancement failed")
            self.logger.info(f"No viable candidates after scoring in FLUX/T5 {workflow_type} workflow")
            processing_time = time.time() - self.start_time
            self._track_analytics("flux_t5_enhance", False, processing_time, workflow_type)
            return engine_result

        # Sort by final score
        scored_candidates.sort(key=lambda x: x["final_score"], reverse=True)

        # Log all candidates for debugging
        self.logger.info(f"FLUX/T5 candidate scoring results (workflow: {workflow_type}):")
        for i, candidate in enumerate(scored_candidates[:5]):  # Show top 5
            text_preview = candidate["text"][:40].replace("\n", " ") + "..." if len(candidate["text"]) > 40 else candidate["text"]
            self.logger.info(f"  {i+1}. Score: {candidate['final_score']:.1f} | Type: {candidate['prompt_type']} | Source: {candidate.get('source', 'unknown')} | Text: '{text_preview}'")
            self.logger.info(f"     Reasons: {', '.join(candidate.get('reasons', []))}")

        # Enhanced candidate selection with fallback chain
        best_positive = None
        best_negative = None
        best_content = None  # Fallback for unknown types

        print(f"[DEBUG] Selecting FLUX/T5 candidates from {len(scored_candidates)} viable options:")
        for i, candidate in enumerate(scored_candidates):
            prompt_type = candidate["prompt_type"]
            text_preview = candidate["text"][:40] + "..." if len(candidate["text"]) > 40 else candidate["text"]
            print(f"[DEBUG] Candidate {i+1}: type='{prompt_type}', score={candidate['final_score']:.1f}, text='{text_preview}'")

            # Select the HIGHEST scoring candidate for each type
            if prompt_type == "positive":
                if not best_positive or candidate["final_score"] > best_positive["final_score"]:
                    best_positive = candidate
                    print(f"[DEBUG] Selected as best_positive (score: {candidate['final_score']:.1f})")
            elif prompt_type == "negative":
                if not best_negative or candidate["final_score"] > best_negative["final_score"]:
                    best_negative = candidate
                    print(f"[DEBUG] Selected as best_negative (score: {candidate['final_score']:.1f})")
            elif prompt_type == "content":
                if not best_content or candidate["final_score"] > best_content["final_score"]:
                    best_content = candidate
                    print(f"[DEBUG] Selected as best_content (score: {candidate['final_score']:.1f})")

        # Enhanced result with comprehensive metadata
        enhanced_result = engine_result.copy()
        enhancement_applied = False

        # Update prompts if we found better ones
        original_prompt = engine_result.get("prompt", "").strip()
        original_prompt_empty = (not original_prompt or original_prompt in ["", "{}"] or
                                any(template in original_prompt.lower() for template in ["positive", "negative", "text", "clip"]))

        # Smart replacement logic for positive prompts in FLUX/T5 context
        should_replace_positive = original_prompt_empty
        if best_positive and not original_prompt_empty:
            # Check if we have significantly better T5/guider content
            is_t5_generated = best_positive.get("source", "") in ["t5_connected", "guider_traced"]
            best_score = best_positive["final_score"]
            is_complex_vs_simple = self._is_complex_scene_vs_simple_style(best_positive["text"], original_prompt)

            if is_t5_generated and best_score >= 10.0 and (len(best_positive["text"]) > len(original_prompt) * 1.2 or is_complex_vs_simple):
                should_replace_positive = True
                print(f"[DEBUG] Will replace with superior T5/guider content (score: {best_score:.1f})")

        if best_positive and should_replace_positive:
            enhanced_result["prompt"] = best_positive["text"]
            enhancement_applied = True
            print("[DEBUG] REPLACED original positive prompt with FLUX/T5 numpy enhancement")

        # Similar logic for negative prompts
        original_negative_empty = (not engine_result.get("negative_prompt") or
                                  engine_result.get("negative_prompt", "").strip() in ["", "{}"])

        if best_negative and original_negative_empty:
            enhanced_result["negative_prompt"] = best_negative["text"]
            enhancement_applied = True
            print("[DEBUG] REPLACED original negative prompt with FLUX/T5 numpy enhancement")

        # Add comprehensive numpy analysis metadata
        processing_time = time.time() - self.start_time
        enhanced_result["numpy_analysis"] = {
            "candidates_found": len(candidates),
            "viable_candidates": len(scored_candidates),
            "workflow_type": f"flux_t5_{workflow_type}",
            "workflow_hash": workflow_hash,
            "processing_time_ms": round(processing_time * 1000, 2),
            "enhancement_applied": enhancement_applied,
            "scoring_method": "flux_t5_numpy",
            "best_positive": {
                "text": best_positive["text"][:100] + "..." if best_positive and len(best_positive["text"]) > 100 else best_positive["text"] if best_positive else None,
                "score": best_positive["final_score"] if best_positive else None,
                "node_type": best_positive.get("node_type") if best_positive else None,
                "confidence": best_positive.get("confidence") if best_positive else None
            } if best_positive else None,
            "top_candidates": [
                {
                    "text": c["text"][:50] + "..." if len(c["text"]) > 50 else c["text"],
                    "score": c["final_score"],
                    "type": c["prompt_type"],
                    "node_type": c.get("node_type")
                } for c in scored_candidates[:3]  # Top 3 for debugging
            ]
        }

        # Cache results for future use
        cache_data = {
            "enhanced_prompt": enhanced_result.get("prompt") if enhancement_applied else None,
            "enhanced_negative": enhanced_result.get("negative_prompt") if enhancement_applied else None,
            "workflow_type": f"flux_t5_{workflow_type}",
            "candidates_found": len(candidates),
            "processing_time": processing_time
        }
        WORKFLOW_CACHE[cache_key] = cache_data

        # Track analytics
        self._track_analytics("flux_t5_enhance", enhancement_applied, processing_time, workflow_type)

        self.logger.info(f"FLUX/T5 numpy enhancement completed for {workflow_type} workflow in {processing_time:.3f}s (enhancement: {enhancement_applied})")
        return enhanced_result
