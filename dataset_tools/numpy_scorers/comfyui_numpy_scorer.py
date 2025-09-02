"""ComfyUI-Specific Numpy Scorer
=============================

Specialized numpy scoring for ComfyUI workflows.
Handles workflow graph traversal, node analysis, and ComfyUI-specific scoring.
"""

import time
from typing import Any

from ..logger import get_logger
from .base_numpy_scorer import RUNTIME_ANALYTICS, WORKFLOW_CACHE, BaseNumpyScorer
from .negative_indicators_loader import negative_indicators

logger = get_logger(__name__)

# ComfyUI Node type scoring with domain knowledge
NODE_TYPE_SCORES = {
    # Dynamic content generators (highest priority)
    "DPRandomGenerator": 3.0,  # Dynamic Prompts Random Generator - highest priority
    "ImpactWildcardEncode": 2.9,  # Impact wildcard encode - very high priority
    "ImpactWildcardProcessor": 2.5,
    "WildcardProcessor": 2.5,
    "RandomPrompt": 2.5,
    "Wildcard": 2.5,
    "WildCardProcessor": 2.5,
    "Power Prompt (rgthree)": 2.8,  # rgthree power prompt with wildcards - very high priority
    "MZ_ChatGLM3_V2": 3.0,  # ChatGLM3 LLM integration - highest priority

    # Standard prompt nodes (medium priority)
    "ChatGptPrompt": 2.0,  # ChatGPT prompt integration - high priority
    "Text Multiline": 2.2,  # Griptape Text Multiline - high priority for clean content
    "easy positive": 2.1,  # Easy positive nodes - high priority for clean content
    "Florence2Run": 2.8,  # AI vision model generated captions - very high priority
    "ShowText|pysssss": 2.9,  # Display node often shows AI-generated content - highest priority
    "OllamaVision": 2.8,  # Ollama vision model generated prompts - high priority
    "Text to Conditioning": 2.3,  # Text to conditioning converter - high priority
    "Text Find and Replace": 1.8,  # Text processing node - medium-high priority
    "Text Concatenate": 2.0,  # Text concatenation - high priority for combined prompts
    "CLIPTextEncode": 1.0,
    "CLIPTextEncodeSDXL": 1.0,  # SDXL CLIP text encoding - same priority as standard
    "CLIPTextEncodeSDXLRefiner": 1.0,  # SDXL Refiner CLIP text encoding - same priority
    "T5TextEncode": 1.5,  # T5 text encoding for PixArt workflows - higher priority
    "PixArtT5TextEncode": 1.5,  # PixArt T5 text encoding - higher priority
    "ConditioningCombine": 1.0,
    "ConditioningConcat": 1.0,
    "ConditioningSetArea": 1.0,

    # Lower priority or technical nodes
    "ConditioningSetTimesteps": 0.5,
    "ConditioningSetMask": 0.5,
    "LoadImage": 0.3,
    "SaveImage": 0.3,
    "PreviewImage": 0.3,

    # Very low priority (usually technical)
    "ModelLoader": 0.1,
    "VAELoader": 0.1,
    "SchedulerLoader": 0.1,
}

# Workflow classification system
WORKFLOW_TYPES = {
    "standard": "Basic CLIP → sampling chain",
    "randomizer": "Contains wildcard/random nodes",
    "complex": "Multiple conditioning paths",
    "experimental": "Unknown/new node types",
    "upscaling": "Contains upscaling workflows",
    "controlnet": "Uses ControlNet conditioning"
}


class ComfyUINumpyScorer(BaseNumpyScorer):
    """Numpy-based analyzer specifically for ComfyUI workflows."""

    def __init__(self):
        """Initialize the ComfyUI numpy analyzer."""
        super().__init__()
        self.logger = get_logger(f"{__name__}.ComfyUINumpyScorer")

        # Performance optimization limits
        self.MAX_DEPTH = 5  # Maximum connection tracing depth
        self.MAX_CANDIDATES = 15  # Maximum candidates to process
        self.EARLY_EXIT_SCORE = 8.0  # Stop processing when we find candidates with this score
        self.IRRELEVANT_NODE_TYPES = {
            "Note", "Reroute", "ImageSave", "LoadImage", "PreviewImage",
            "SaveImage", "ModelLoader", "VAELoader", "CheckpointLoaderSimple",
            "LoraLoader", "SchedulerLoader", "EmptyLatentImage"
        }

        # ComfyUI-specific template indicators
        self.comfyui_template_indicators = [
            "beautiful scenery nature glass bottle landscape",
            "purple galaxy bottle",
            "full body shot of a sexy goth girl with bombshell hair chained to a dungeon wall, facing the camera",
            "beautiful scenery nature glass bottle landscape",
            "chibi anime style",
        ]

        # Template pattern indicators for ComfyUI workflows
        self.template_patterns = [
            # Generic quality combinations that are often templates
            ["woman", "portrait", "detailed"],
            ["beautiful", "detailed", "high quality"],
            ["girl", "portrait", "masterpiece"],
            ["anime", "girl", "detailed"],
            # Common ComfyUI default patterns
            ["beautiful", "scenery", "landscape"],
            ["nature", "glass", "bottle"],
            ["purple", "galaxy", "bottle"],
        ]

    def _classify_workflow_type(self, workflow_data: dict[str, Any]) -> str:
        """Classify the type of ComfyUI workflow."""
        nodes = workflow_data.get("nodes", workflow_data)  # TensorArt stores nodes at root level

        # Handle both list of nodes and TensorArt-style dict of nodes
        if isinstance(nodes, dict):
            # TensorArt format: {"10035": {"class_type": "CLIPTextEncode", ...}}
            node_items = list(nodes.values())
        elif isinstance(nodes, list):
            # Standard ComfyUI format: [{"class_type": "CLIPTextEncode", ...}]
            node_items = nodes
        else:
            return "standard"

        # Look for specific node types to classify workflow
        node_classes = [node.get("class_type", "") for node in node_items if isinstance(node, dict)]

        # Check for randomizer workflows
        randomizer_nodes = {"DPRandomGenerator", "WildcardProcessor", "RandomPrompt", "Wildcard"}
        if any(node_class in randomizer_nodes for node_class in node_classes):
            return "randomizer"

        # Check for ControlNet
        if any("controlnet" in node_class.lower() for node_class in node_classes):
            return "controlnet"

        # Check for upscaling
        upscaling_indicators = ["upscale", "resize", "scale", "ESRGAN", "RealESRGAN"]
        if any(any(indicator.lower() in node_class.lower() for indicator in upscaling_indicators) for node_class in node_classes):
            return "upscaling"

        # Check for complex conditioning
        conditioning_nodes = [nc for nc in node_classes if "conditioning" in nc.lower()]
        if len(conditioning_nodes) > 3:
            return "complex"

        # Check for experimental (unknown node types)
        known_prefixes = ["CLIP", "VAE", "Model", "Load", "Save", "Preview", "Conditioning", "KSampler"]
        unknown_nodes = [nc for nc in node_classes if not any(nc.startswith(prefix) for prefix in known_prefixes)]
        if len(unknown_nodes) > len(node_classes) * 0.3:  # More than 30% unknown
            return "experimental"

        return "standard"

    def _is_comfyui_template_text(self, text: str) -> bool:
        """Check if text appears to be ComfyUI template content."""
        if self._is_template_text(text):  # Use base template detection
            return True

        text_lower = text.lower().strip()

        # Check ComfyUI-specific template indicators
        for indicator in self.comfyui_template_indicators:
            if indicator.lower() in text_lower:
                return True

        # Check template patterns
        for pattern in self.template_patterns:
            if all(word.lower() in text_lower for word in pattern):
                return True

        return False

    def _build_link_map(self, workflow_data: dict[str, Any]) -> dict[int, dict[str, Any]]:
        """Build a mapping of node connections from workflow data."""
        link_map = {}
        links = workflow_data.get("links", [])

        # Handle both list and dict formats for links
        if isinstance(links, dict):
            # TensorArt format: {link_id: [link_id, output_node, output_slot, input_node, input_slot, ...]}
            link_items = links.values()
        elif isinstance(links, list):
            # Standard ComfyUI format: [[link_id, output_node, output_slot, input_node, input_slot, ...], ...]
            link_items = links
        else:
            link_items = []

        for link in link_items:
            # Each link should be a list with at least 5 elements
            if isinstance(link, list) and len(link) >= 5:
                link_id, output_node, output_slot, input_node, input_slot = link[:5]
                link_map[link_id] = {
                    "output_node": output_node,
                    "output_slot": output_slot,
                    "input_node": input_node,
                    "input_slot": input_slot
                }
            # If dict (rare), try to extract values
            elif isinstance(link, dict):
                # Try to extract using keys if present
                link_id = link.get("id")
                output_node = link.get("output_node")
                output_slot = link.get("output_slot")
                input_node = link.get("input_node")
                input_slot = link.get("input_slot")
                if None not in (link_id, output_node, output_slot, input_node, input_slot):
                    link_map[link_id] = {
                        "output_node": output_node,
                        "output_slot": output_slot,
                        "input_node": input_node,
                        "input_slot": input_slot
                    }

        return link_map

    def _find_conditioning_nodes(self, nodes) -> list[dict[str, Any]]:
        """Find nodes that likely contain conditioning/prompts."""
        conditioning_nodes = []

        high_priority_types = [
            "DPRandomGenerator", "WildcardProcessor", "ImpactWildcardProcessor",
            "RandomPrompt", "Wildcard", "WildCardProcessor", "ImpactWildcardEncode"
        ]

        medium_priority_types = [
            "CLIPTextEncode", "CLIPTextEncodeSDXL", "CLIPTextEncodeSDXLRefiner",
            "ConditioningCombine", "ConditioningConcat", "ConditioningSetArea",
            "BNK_CLIPTextEncodeAdvanced", "String Literal", "Text Multiline",
            "easy positive", "T5TextEncode", "Florence2Run", "Text to Conditioning",
            "Text Find and Replace", "OllamaVision", "Text Concatenate",
            "CLIPTextEncodeFlux", "PixArtT5TextEncode", "ChatGptPrompt", "ShowText|pysssss"
        ]

        # Handle both list of nodes and TensorArt-style dict of nodes
        print(f"[DEBUG] _find_conditioning_nodes called with nodes type: {type(nodes)}")
        if isinstance(nodes, dict):
            # TensorArt format: {"10035": {"class_type": "CLIPTextEncode", ...}}
            node_items = list(nodes.values())
            print(f"[DEBUG] Using dict format - extracted {len(node_items)} node items")
        elif isinstance(nodes, list):
            # Standard ComfyUI format: [{"class_type": "CLIPTextEncode", ...}]
            node_items = nodes
            print(f"[DEBUG] Using list format - {len(node_items)} node items")
        else:
            print(f"[DEBUG] Nodes is neither dict nor list: {type(nodes)}")
            return conditioning_nodes

        node_types_found = []
        for node in node_items:
            if not isinstance(node, dict):
                continue

            # Handle both 'type' (standard ComfyUI) and 'class_type' (TensorArt/other formats)
            class_type = node.get("class_type") or node.get("type", "")
            node_types_found.append(class_type)

            # High priority nodes first
            if class_type in high_priority_types:
                print(f"[DEBUG] Found high priority node: {class_type}")
                conditioning_nodes.append(node)
                continue

            # Medium priority nodes
            if class_type in medium_priority_types:
                print(f"[DEBUG] Found medium priority node: {class_type}")
                conditioning_nodes.append(node)
                continue

            # Any node with 'text' in inputs
            inputs = node.get("inputs", {})
            if isinstance(inputs, dict) and "text" in inputs:
                print(f"[DEBUG] Found text input node: {class_type}")
                conditioning_nodes.append(node)

        print(f"[DEBUG] All node types found: {set(node_types_found)}")
        print(f"[DEBUG] Total conditioning nodes found: {len(conditioning_nodes)}")

        return conditioning_nodes

    def _extract_text_from_node(self, node: dict[str, Any], source_info: dict[str, Any]) -> str:
        """Extract text content from a ComfyUI node."""
        class_type = node.get("class_type") or node.get("type", "")
        inputs = node.get("inputs", {})

        print(f"[DEBUG] _extract_text_from_node: class_type={class_type}, inputs type={type(inputs)}")

        text = ""

        # 1. Prioritize widgets_values for standard ComfyUI nodes.
        # This is the most common format, where values are stored directly in the node.
        if "widgets_values" in node and isinstance(node["widgets_values"], list):
            widgets_values = node["widgets_values"]
            print(f"[DEBUG] Found widgets_values: {widgets_values}")

            if class_type in ["ImpactWildcardProcessor", "ImpactWildcardEncode"]:
                if len(widgets_values) >= 2 and isinstance(widgets_values[1], str):
                    text = widgets_values[1]
                elif len(widgets_values) >= 1 and isinstance(widgets_values[0], str):
                    text = widgets_values[0]

                # Check for template/placeholder text in wildcard processors
                template_indicators = [
                    "populate", "select the wildcard", "wildcard to add",
                    "choose wildcard", "add to the text", "select wildcard"
                ]
                # Also check for common wildcard processor mode settings that aren't real prompts
                wildcard_mode_settings = [
                    "fixed", "randomize", "increment", "decrement",
                    "random", "sequential", "shuffle"
                ]

                is_template = False
                if text:
                    # Check template indicators
                    if any(indicator.lower() in text.lower() for indicator in template_indicators) or text.strip().lower() in [mode.lower() for mode in wildcard_mode_settings]:
                        is_template = True

                if is_template:
                    print(f"[DEBUG] Detected template/mode text in {class_type}: '{text[:60]}...' - reducing priority")
                    # Don't completely exclude, but mark as low priority template
                    text = f"[TEMPLATE]{text}"
            elif class_type in ["CLIPTextEncode", "CLIPTextEncodeSDXL", "CLIPTextEncodeSDXLRefiner", "BNK_CLIPTextEncodeAdvanced", "String Literal", "Text Multiline", "easy positive", "T5TextEncode", "PixArtT5TextEncode"]:
                if len(widgets_values) >= 1 and isinstance(widgets_values[0], str):
                    text = widgets_values[0]
            elif class_type == "Florence2Run":
                # Florence2 generates captions - check for caption output first, fallback to widgets
                # Note: Florence2 caption output flows to other nodes, we need to trace connections
                # For now, check if there's caption-like content in widgets_values
                if len(widgets_values) >= 1 and isinstance(widgets_values[0], str):
                    # First widget is usually task type like 'more_detailed_caption'
                    pass  # We'll need to trace outputs to get actual caption content
            elif class_type == "Text Find and Replace":
                # Text Find and Replace processes text, first widget might be input text
                if len(widgets_values) >= 2 and isinstance(widgets_values[1], str):
                    text = widgets_values[1]  # Second widget might be replacement text
                elif len(widgets_values) >= 1 and isinstance(widgets_values[0], str):
                    text = widgets_values[0]  # First widget might be find text
            elif class_type == "Text to Conditioning":
                # Text to Conditioning usually gets text via input connections, not widgets
                # We'll need to trace input connections to get the actual text
                pass
            elif class_type == "OllamaVision":
                # OllamaVision generates text descriptions from images
                # Text might be in later widgets or we need to trace outputs
                for i, widget in enumerate(widgets_values):
                    if isinstance(widget, str) and len(widget.strip()) > 20:
                        text = widget
                        break
            elif class_type == "Text Concatenate":
                # Text Concatenate combines multiple text inputs
                # Look for concatenated result in widgets
                for i, widget in enumerate(widgets_values):
                    if isinstance(widget, str) and len(widget.strip()) > 10:
                        text = widget
                        break
            elif class_type == "CLIPTextEncodeFlux":
                # FLUX-style CLIP text encoding
                if len(widgets_values) >= 1 and isinstance(widgets_values[0], str):
                    text = widgets_values[0]
            elif class_type == "ShowText|pysssss":
                # ShowText display node - often shows AI-generated content
                # widgets_values is usually a nested array like [["generated text here"]]
                if len(widgets_values) >= 1:
                    if isinstance(widgets_values[0], list) and len(widgets_values[0]) >= 1:
                        text = str(widgets_values[0][0])
                    elif isinstance(widgets_values[0], str):
                        text = widgets_values[0]
            elif class_type == "DPRandomGenerator":
                # DPRandomGenerator's first widget is the actual prompt text
                if len(widgets_values) >= 1 and isinstance(widgets_values[0], str):
                    text = widgets_values[0]
            elif len(widgets_values) >= 1 and isinstance(widgets_values[0], str):
                 text = widgets_values[0]

        # 2. If no text from widgets, check `inputs` dict.
        # This handles "flat" formats (like TensorArt) where input values are stored in the inputs dict.
        if not text and isinstance(inputs, dict):
            print(f"[DEBUG] Checking inputs dict for text (flat/TensorArt format): {list(inputs.keys())}")
            if class_type in ["CLIPTextEncode", "CLIPTextEncodeSDXL", "CLIPTextEncodeSDXLRefiner", "BNK_CLIPTextEncodeAdvanced", "String Literal", "Text Multiline", "easy positive"]:
                text = inputs.get("text", "")
                # For "easy positive" nodes, also check for "positive" field
                if not text and class_type == "easy positive":
                    text = inputs.get("positive", "")
            elif class_type in ["DPRandomGenerator", "WildcardProcessor", "ImpactWildcardProcessor", "ImpactWildcardEncode"]:
                text = inputs.get("text", inputs.get("prompt", inputs.get("input_text", inputs.get("wildcard_text", ""))))
            elif class_type == "Florence2Run":
                # Florence2 might have processed caption in inputs (for flat formats)
                text = inputs.get("caption", inputs.get("text", ""))
            elif class_type == "Text Find and Replace":
                # Text Find and Replace might have result_text in inputs (for flat formats)
                text = inputs.get("result_text", inputs.get("text", ""))
            elif class_type == "Text to Conditioning":
                # Text to Conditioning takes text input
                text = inputs.get("text", inputs.get("string", ""))
            elif class_type == "OllamaVision":
                # OllamaVision might have generated text in inputs
                text = inputs.get("response", inputs.get("text", inputs.get("output", "")))
            elif class_type == "Text Concatenate":
                # Text Concatenate might have result in inputs
                text = inputs.get("result", inputs.get("output", inputs.get("text", "")))
            elif class_type == "CLIPTextEncodeFlux":
                # FLUX CLIP encoding
                text = inputs.get("text", "")
            else:
                text = inputs.get("text", inputs.get("prompt", inputs.get("input_text", "")))

        # Check for universal empty/placeholder text patterns
        if text:
            text_str = str(text)
            empty_patterns = [
                "echo_empty", "empty", "null", "none", "placeholder",
                "select the wildcard", "populate", "add text here", "enter text"
            ]

            if any(pattern.lower() in text_str.lower() for pattern in empty_patterns) and len(text_str.strip()) < 50:
                print(f"[DEBUG] Detected empty/placeholder text in {class_type}: '{text_str[:60]}...' - marking as template")
                text_str = f"[TEMPLATE]{text_str}"

            print(f"[DEBUG] Extracted text from {class_type}: '{text_str[:60] if text_str else 'EMPTY'}...'")
            return text_str

        print(f"[DEBUG] Extracted text from {class_type}: 'EMPTY...'")
        return ""

    def extract_text_candidates_from_workflow(self, workflow_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract text candidates from ComfyUI workflow with numpy-enhanced scoring."""
        start_time = time.time()
        candidates = []

        try:
            # Get workflow hash for caching
            workflow_hash = self._get_workflow_hash(workflow_data)
            if workflow_hash in WORKFLOW_CACHE:
                RUNTIME_ANALYTICS["cache_hits"] += 1
                return WORKFLOW_CACHE[workflow_hash]

            RUNTIME_ANALYTICS["cache_misses"] += 1

            # Classify workflow type
            workflow_type = self._classify_workflow_type(workflow_data)

            # Build connection map
            link_map = self._build_link_map(workflow_data)

            # Find conditioning nodes
            nodes = workflow_data.get("nodes", workflow_data)  # TensorArt stores nodes at root level
            conditioning_nodes = self._find_conditioning_nodes(nodes)

            # Identify sampler nodes (for connectivity check)
            sampler_types = {"KSampler", "SamplerCustomAdvanced", "KSampler_A1111", "KSampler (Efficient)"}
            sampler_node_ids = set()
            if isinstance(nodes, dict):
                for nid, n in nodes.items():
                    if n.get("class_type") in sampler_types:
                        sampler_node_ids.add(str(nid))
            elif isinstance(nodes, list):
                for n in nodes:
                    if n.get("class_type") in sampler_types and "id" in n:
                        sampler_node_ids.add(str(n["id"]))

            # Helper: check if a node is connected to a sampler
            def is_connected_to_sampler(node_id: str) -> bool:
                for link in link_map.values():
                    if str(link["output_node"]) == str(node_id) and str(link["input_node"]) in sampler_node_ids:
                        return True
                return False

            # Extract candidates from conditioning nodes
            print(f"[DEBUG] Processing {len(conditioning_nodes)} conditioning nodes")
            for i, node in enumerate(conditioning_nodes):
                print(f"[DEBUG] Processing node {i}: type={type(node)}")
                if not isinstance(node, dict):
                    print(f"[DEBUG] Skipping non-dict node: {node}")
                    continue

                text = self._extract_text_from_node(node, {})
                if text and len(text.strip()) > 0:
                    node_id = node.get("id")
                    is_connected = False
                    if node_id is not None:
                        is_connected = is_connected_to_sampler(node_id)

                    candidate = {
                        "text": text.strip(),
                        "source_node_id": node_id,
                        "source_node_type": node.get("class_type") or node.get("type", ""),
                        "node_title": node.get("title", ""),  # Add node title for negative/positive detection
                        "workflow_type": workflow_type,
                        "extraction_method": "comfyui_workflow_analysis",
                        "is_connected": is_connected
                    }

                    # Score the candidate
                    scored_candidate = self.score_candidate(candidate, "comfyui")
                    print(f"[DEBUG] Found candidate from {node.get('class_type') or node.get('type', '')}: confidence={scored_candidate.get('confidence', 0):.3f}, text_preview='{text[:60]}...'")
                    candidates.append(scored_candidate)

            # Sort by confidence and limit results
            candidates.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            candidates = candidates[:self.MAX_CANDIDATES]

            # Cache results
            WORKFLOW_CACHE[workflow_hash] = candidates

            processing_time = time.time() - start_time
            self._track_analytics("extract_text_candidates_from_workflow", True, processing_time, workflow_type)

            return candidates

        except Exception as e:
            self.logger.error(f"Error extracting ComfyUI workflow candidates: {e}")
            processing_time = time.time() - start_time
            self._track_analytics("extract_text_candidates_from_workflow", False, processing_time, "error")
            return []

    def score_candidate(self, candidate: dict[str, Any], format_type: str = "comfyui") -> dict[str, Any]:
        """Score a ComfyUI text candidate with enhanced domain knowledge."""
        # Start with base scoring
        scored_candidate = super().score_candidate(candidate, format_type)

        text = candidate.get("text", "")
        node_type = candidate.get("source_node_type", "")
        confidence = scored_candidate.get("confidence", 0.5)

        # Apply ComfyUI-specific scoring adjustments

        # Check for template content and heavily penalize
        if text.startswith("[TEMPLATE]"):
            print("[DEBUG] Template content detected - applying heavy penalty")
            confidence *= 0.1  # Reduce confidence to 10% for template content
            text = text[10:]  # Remove [TEMPLATE] prefix for further processing
            candidate["text"] = text  # Update candidate text to remove prefix

        # Node type scoring
        node_score_multiplier = NODE_TYPE_SCORES.get(node_type, 1.0)
        confidence *= node_score_multiplier

        # Dynamic content bonus
        if node_type in ["DPRandomGenerator", "WildcardProcessor", "RandomPrompt"]:
            confidence *= 1.5  # Bonus for dynamic content generators

        # Content quality scoring - ONLY add bonuses, NO penalties
        text_lower = text.lower()

        # Bonus for descriptive content (person descriptions, scenes, actions)
        descriptive_indicators = ["woman", "man", "girl", "person", "portrait", "driving", "selfie", "face", "hair", "eyes", "smile"]
        descriptive_count = sum(1 for desc in descriptive_indicators if desc in text_lower)
        if descriptive_count >= 3:
            confidence *= 1.3  # Bonus for descriptive content

        # Connection-based scoring bonus (additive, not exclusive)
        connection_bonus = self._get_connection_bonus(candidate)
        confidence += connection_bonus  # Add to existing confidence rather than multiply

        # Additive bonus for explicit node titles
        node_title = candidate.get("node_title", "").lower()
        if "positive prompt" in node_title:
            confidence += 10.0  # Large additive bonus to ensure it wins

        # ComfyUI template detection penalty - APPLY THIS LAST AND STRONGLY
        if self._is_comfyui_template_text(text):
            confidence *= 0.01  # Much heavier penalty for templates

        # Update the scored candidate (allow scores > 1.0 for high priority nodes)
        scored_candidate["confidence"] = max(0.0, confidence)
        scored_candidate["scoring_method"] = "comfyui_numpy"
        scored_candidate["node_type_score"] = node_score_multiplier
        scored_candidate["connection_bonus"] = connection_bonus

        return scored_candidate

    def _get_connection_bonus(self, candidate: dict[str, Any]) -> float:
        """Calculate connection-based bonus for prompt candidates.
        
        Gives additive bonus for connections to important workflow components:
        - Main samplers (KSampler, etc.) get highest bonus
        - Upscaling samplers get medium bonus  
        - Unconnected or unclear connections get no bonus
        """
        # This is a simple version - could be enhanced with actual connection tracing
        # For now, we'll use heuristics based on the candidate's connection info

        is_connected = candidate.get("is_connected", False)

        # Base bonus for being connected to any sampler
        if is_connected:
            return 0.2  # Small additive bonus for connected nodes

        # Could add more sophisticated connection analysis here:
        # - Trace to main vs upscaling samplers
        # - Check connection depth/path
        # - Identify primary vs secondary workflows

        return 0.0  # No bonus for unconnected nodes

    def enhance_engine_result(self, engine_result: dict[str, Any], original_file_path: str | None = None) -> dict[str, Any]:
        """Enhance engine results with ComfyUI-specific numpy analysis."""
        try:
            print("[DEBUG] ComfyUI scorer enhance_engine_result called")
            raw_metadata = engine_result.get("raw_metadata", {})

            # Check if this looks like ComfyUI data
            if not isinstance(raw_metadata, dict):
                print(f"[DEBUG] raw_metadata is not a dict: {type(raw_metadata)}")
                return engine_result

            print(f"[DEBUG] raw_metadata keys: {list(raw_metadata.keys())}")

            # Handle different workflow data locations
            workflow_data = None
            if "workflow" in raw_metadata:
                workflow_data = raw_metadata.get("workflow", {})
                print("[DEBUG] Found workflow in raw_metadata['workflow']")
            elif "nodes" in raw_metadata and isinstance(raw_metadata.get("nodes"), list):
                # Standard ComfyUI case - raw_metadata contains the workflow with nodes array
                workflow_data = raw_metadata
                print("[DEBUG] Using raw_metadata as workflow (standard ComfyUI case)")
            elif "nodes" in raw_metadata or "links" in raw_metadata:
                # TensorArt case - raw_metadata is the workflow with flat nodes
                workflow_data = raw_metadata
                print("[DEBUG] Using raw_metadata as workflow (TensorArt flat case)")
            else:
                # Check for flat format - numeric node IDs as keys with class_type
                numeric_keys = []
                for key, value in raw_metadata.items():
                    if (isinstance(key, str) and key.isdigit() and
                        isinstance(value, dict) and "class_type" in value):
                        numeric_keys.append(key)

                if numeric_keys:
                    workflow_data = raw_metadata
                    print(f"[DEBUG] Using raw_metadata as flat format workflow ({len(numeric_keys)} nodes)")
                else:
                    print("[DEBUG] No workflow structure detected in raw_metadata")

            if not isinstance(workflow_data, dict):
                print(f"[DEBUG] workflow_data is not a dict: {type(workflow_data)}")
                return engine_result

            print(f"[DEBUG] workflow_data keys: {list(workflow_data.keys())}")
            print("[DEBUG] About to call extract_text_candidates_from_workflow")

            # Extract and analyze workflow candidates
            candidates = self.extract_text_candidates_from_workflow(workflow_data)
            print(f"[DEBUG] Candidates extracted: {len(candidates)}")

            if candidates:
                # Separate positive and negative candidates
                positive_candidates = []
                negative_candidates = []

                for candidate in candidates:
                    text = candidate.get("text", "").lower()
                    original_text = candidate.get("text", "")

                    # First check ComfyUI node title for explicit negative/positive markers
                    node_title = candidate.get("node_title", "").lower() if "node_title" in candidate else ""
                    is_negative_by_title = ("negative" in node_title and "prompt" in node_title) or "negative prompt" in node_title
                    is_positive_by_title = ("positive" in node_title and "prompt" in node_title) or "positive prompt" in node_title

                    # If node title explicitly indicates type, use that (high confidence)
                    if is_negative_by_title:
                        is_negative = True
                        print(f"[DEBUG] Node title indicates negative: '{node_title}'")
                    elif is_positive_by_title:
                        is_negative = False
                        print(f"[DEBUG] Node title indicates positive: '{node_title}'")
                    else:
                        # Fallback to JSON-based negative detection system
                        is_negative = negative_indicators.is_negative_text(original_text)

                    if is_negative:
                        print(f"[DEBUG] JSON-based detection classified as negative: '{original_text[:40]}...'")

                    if is_negative:
                        print(f"[DEBUG] Found negative prompt candidate: '{candidate.get('text', '')[:40]}...'")
                        negative_candidates.append(candidate)
                    else:
                        positive_candidates.append(candidate)

                enhanced_result = engine_result.copy()

                # Find best positive candidate
                if positive_candidates:
                    best_positive = max(positive_candidates, key=lambda x: x.get("confidence", 0))
                    print(f"[DEBUG] Best positive candidate: confidence={best_positive.get('confidence', 0):.3f}, text='{best_positive.get('text', '')[:60]}...'")

                    if best_positive.get("confidence", 0) > 0.5:
                        enhanced_result["prompt"] = best_positive["text"]

                # Find best negative candidate
                if negative_candidates:
                    best_negative = max(negative_candidates, key=lambda x: x.get("confidence", 0))
                    print(f"[DEBUG] Best negative candidate: confidence={best_negative.get('confidence', 0):.3f}, text='{best_negative.get('text', '')[:60]}...'")
                    enhanced_result["negative_prompt"] = best_negative["text"]
                else:
                    # Clear any existing negative_prompt if we didn't find negative candidates
                    print("[DEBUG] No negative candidates found, clearing negative_prompt")
                    enhanced_result["negative_prompt"] = ""

                # Only enhance if we found good candidates
                if positive_candidates or negative_candidates:
                    enhanced_result["numpy_analysis"] = {
                        "enhancement_applied": True,
                        "best_positive_confidence": best_positive.get("confidence") if positive_candidates else None,
                        "best_negative_confidence": best_negative.get("confidence") if negative_candidates else None,
                        "total_candidates": len(candidates),
                        "scoring_method": "comfyui_numpy",
                        "workflow_type": (best_positive if positive_candidates else best_negative).get("workflow_type"),
                        "source_node_type": (best_positive if positive_candidates else best_negative).get("source_node_type")
                    }

                    return enhanced_result

        except Exception as e:
            self.logger.error(f"Error in ComfyUI numpy enhancement: {e}")

        return engine_result


def should_use_comfyui_numpy_scoring(engine_result: dict[str, Any]) -> bool:
    """Determine if ComfyUI numpy scoring should be applied."""
    from ..logger import get_logger
    logger = get_logger(__name__)

    raw_metadata = engine_result.get("raw_metadata", {})
    tool = engine_result.get("tool", "").lower()
    format_name = engine_result.get("format", "").lower()

    print(f"[DEBUG] ComfyUI scoring check - tool: '{tool}', format: '{format_name}'")
    print(f"[DEBUG] 'comfy' in tool: {'comfy' in tool}")
    logger.info(f"ComfyUI scoring check - tool: {tool}, format: {format_name}")
    logger.info(f"raw_metadata type: {type(raw_metadata)}, keys: {list(raw_metadata.keys()) if isinstance(raw_metadata, dict) else 'not dict'}")

    # Check for ComfyUI workflow structure
    if isinstance(raw_metadata, dict) and "workflow" in raw_metadata:
        workflow = raw_metadata.get("workflow", {})
        if isinstance(workflow, dict) and ("nodes" in workflow or "links" in workflow):
            logger.info("Found ComfyUI workflow in raw_metadata['workflow']")
            return True

    # Check if raw_metadata itself is a workflow (TensorArt case)
    if isinstance(raw_metadata, dict) and ("nodes" in raw_metadata or "links" in raw_metadata):
        logger.info("Found ComfyUI workflow in raw_metadata itself")
        return True

    # Check if raw_metadata has node IDs as keys (TensorArt flat format)
    if isinstance(raw_metadata, dict):
        # Look for keys that are numeric strings (node IDs) with class_type
        node_like_keys = []
        for key, value in raw_metadata.items():
            if isinstance(value, dict) and "class_type" in value:
                node_like_keys.append(key)
        if node_like_keys:
            logger.info(f"Found TensorArt-style workflow with {len(node_like_keys)} nodes")
            return True

    # Check for ComfyUI-specific indicators in the result
    if "comfy" in tool or "comfy" in format_name or "tensorart" in tool or "tensorart" in format_name:
        logger.info(f"Found ComfyUI indicator in tool/format names - matched on tool={tool}, format={format_name}")
        return True

    # NEW CHECK: If it's a Civitai A1111, check if its raw_metadata looks like a ComfyUI workflow
    if tool == "civitai a1111" and isinstance(raw_metadata, dict):
        # Check for typical ComfyUI workflow top-level keys
        if "nodes" in raw_metadata and "links" in raw_metadata and "version" in raw_metadata:
            logger.info("Found Civitai A1111 with ComfyUI-like workflow structure in raw_metadata, applying ComfyUI scoring")
            return True

    logger.info("No ComfyUI indicators found")
    return False
