"""ComfyUI-Specific Numpy Scorer.

=============================

Specialized numpy scoring for ComfyUI workflows.
Handles workflow graph traversal, node analysis, and ComfyUI-specific scoring.
"""

import time
from typing import Any

from ..logger import get_logger  # noqa: TID252
from .base_numpy_scorer import RUNTIME_ANALYTICS, WORKFLOW_CACHE, BaseNumpyScorer
from .negative_indicators_loader import negative_indicators

logger = get_logger(__name__)

# ComfyUI Node type scoring with domain knowledge
NODE_TYPE_SCORES = {
    # Final resolved content display nodes (absolute highest priority)
    "ShowText|pysssss": 2.0,  # ShowText nodes contain final resolved content - CRITICAL
    "Show Text": 5.0,  # Alternative ShowText format
    "easy showAnything": 2.5,  # HiDream ComfyUI Easy Use display node - very high priority

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
    "TIPO": 6.0,  # TIPO AI prompt generator - prioritize base input over random ShowText output

    # Standard prompt nodes (medium priority)
    "ChatGptPrompt": 2.0,  # ChatGPT prompt integration - high priority
    "Text Multiline": 6.0,  # Griptape Text Multiline - high priority for clean content
    "easy positive": 2.1,  # Easy positive nodes - high priority for clean content
    "Florence2Run": 2.8,  # AI vision model generated captions - very high priority
    "OllamaVision": 2.8,  # Ollama vision model generated prompts - high priority
    "Text to Conditioning": 2.3,  # Text to conditioning converter - high priority
    "Text Find and Replace": 1.8,  # Text processing node - medium-high priority
    "Text Concatenate": 2.0,  # Text concatenation - high priority for combined prompts
    "TensorArt_PromptText": 2.5,  # TensorArt prompt text input - high priority
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

    # PixArt and T5 architecture loaders
    "T5v11Loader": 0.2,  # T5 v1.1 text encoder loader for PixArt workflows
    "PixArtCheckpointLoader": 0.2,  # PixArt model checkpoint loader
    "PixArtResolutionSelect": 0.1,  # PixArt resolution selector utility

    # TensorArt utility nodes (very low priority - no prompt content)
    "TensorArt_CheckpointLoader": 0.1,  # TensorArt checkpoint loader
    "TensorArt_Seed": 0.1,  # TensorArt seed selector
    "TensorArt_SelectBatchs": 0.1,  # TensorArt batch size selector
    "TensorArt_SelectResolution": 0.1,  # TensorArt resolution selector
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
        self.logger = get_logger("%s.ComfyUINumpyScorer" % __name__)

        # Performance optimization limits
        self.MAX_DEPTH = 5  # Maximum connection tracing depth
        self.MAX_CANDIDATES = 15  # Maximum candidates to process
        self.EARLY_EXIT_SCORE = 8.0  # Stop processing when we find candidates with this score
        self.IRRELEVANT_NODE_TYPES = {
            "Note", "Reroute", "ImageSave", "LoadImage", "PreviewImage",
            "SaveImage", "ModelLoader", "VAELoader", "CheckpointLoaderSimple",
            "LoraLoader", "SchedulerLoader", "EmptyLatentImage",
            "T5v11Loader", "PixArtCheckpointLoader", "PixArtResolutionSelect"
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

    def _is_comfyui_template_text(self, text: str, node_type: str = "") -> bool:
        """Check if text appears to be ComfyUI template content.

        Args:
            text: The text to check
            node_type: The source node type (e.g., 'CLIPTextEncode', 'PrimitiveNode')

        Returns:

            True if text appears to be template content
        """
        # CONTEXT-AWARE: If text is in actual text encoder nodes, it's a REAL PROMPT!
        # Don't apply template rejection to prompts in CLIPTextEncode nodes
        text_encoder_nodes = [
            "CLIPTextEncode",
            "CLIPTextEncodeSDXL",
            "CLIPTextEncodeSDXLRefiner",
            "BNK_CLIPTextEncodeAdvanced",
            "Text Multiline",
            "PCLazyTextEncode",
            "TensorArt_PromptText",
        ]

        # Dynamic content generators - their wildcard syntax is REAL USER INPUT, not templates!
        dynamic_generators = [
            "DPRandomGenerator",
            "WildcardProcessor",
            "ImpactWildcardProcessor",
            "RandomPrompt",
        ]

        if any(encoder in node_type for encoder in text_encoder_nodes):
            # This is from an actual text encoder - only reject if it's the base template check
            # (stuff like "example prompt here", "your prompt", etc.)
            return self._is_template_text(text)  # Base template check only

        if any(generator in node_type for generator in dynamic_generators):
            # Dynamic generators use wildcard syntax that LOOKS like templates but is actual user input!
            # Only reject if it's obviously a placeholder like "select wildcard" or "choose option"
            placeholder_indicators = ["select wildcard", "choose wildcard", "populate", "add to the text"]
            text_lower = text.lower()
            return any(indicator in text_lower for indicator in placeholder_indicators)

        # For other node types (PrimitiveNode, etc.), apply full template detection
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
            "RandomPrompt", "Wildcard", "WildCardProcessor", "ImpactWildcardEncode",
            "easy showAnything", "ShowText|pysssss", "Show Text"
        ]

        medium_priority_types = [
            "CLIPTextEncode", "CLIPTextEncodeSDXL", "CLIPTextEncodeSDXLRefiner",
            "ConditioningCombine", "ConditioningConcat", "ConditioningSetArea",
            "BNK_CLIPTextEncodeAdvanced", "String Literal", "Text Multiline",
            "easy positive", "T5TextEncode", "Florence2Run", "Text to Conditioning",
            "Text Find and Replace", "OllamaVision", "Text Concatenate",
            "CLIPTextEncodeFlux", "PixArtT5TextEncode", "ChatGptPrompt", "ShowText|pysssss",
            "JjkText", "CLIPTextEncodeLumina2"
        ]

        # Handle both list of nodes and TensorArt-style dict of nodes
        logger.debug("_find_conditioning_nodes called with nodes type: %s", type(nodes))
        if isinstance(nodes, dict):
            # TensorArt format: {"10035": {"class_type": "CLIPTextEncode", ...}}
            node_items = list(nodes.values())
            logger.debug("Using dict format - extracted %s node items", len(node_items))
        elif isinstance(nodes, list):
            # Standard ComfyUI format: [{"class_type": "CLIPTextEncode", ...}]
            node_items = nodes
            logger.debug("Using list format - %s node items", len(node_items))
        else:
            logger.debug("Nodes is neither dict nor list: %s", type(nodes))
            return conditioning_nodes

        node_types_found = []
        for node in node_items:
            if not isinstance(node, dict):
                continue

            # SKIP BYPASSED NODES: mode: 4 means the node is disabled/bypassed in ComfyUI
            node_mode = node.get("mode", 0)
            if node_mode == 4:
                logger.debug("Skipping bypassed node (mode: 4): %s", node.get("class_type") or node.get("type", ""))
                continue

            # Handle both 'type' (standard ComfyUI) and 'class_type' (TensorArt/other formats)
            class_type = node.get("class_type") or node.get("type", "")
            node_types_found.append(class_type)

            # High priority nodes first
            if class_type in high_priority_types:
                logger.debug("Found high priority node: %s", class_type)
                conditioning_nodes.append(node)
                continue

            # Medium priority nodes
            if class_type in medium_priority_types:
                logger.debug("Found medium priority node: %s", class_type)
                conditioning_nodes.append(node)
                continue

            # Any node with 'text' in inputs
            inputs = node.get("inputs", {})
            if isinstance(inputs, dict) and "text" in inputs:
                logger.debug("Found text input node: %s", class_type)
                conditioning_nodes.append(node)

        logger.debug("All node types found: %s", set(node_types_found))
        logger.debug("Total conditioning nodes found: %s", len(conditioning_nodes))

        return conditioning_nodes

    def _resolve_node_reference(self, source_info: dict[str, Any], node_id: str) -> str:
        """Resolve a node reference to get the actual text content.

        Args:
            source_info: The workflow source info containing all nodes
            node_id: The node ID to resolve (as string)

        Returns:
            The text content from the referenced node, or empty string if not found
        """
        workflow_data = source_info if isinstance(source_info, dict) else {}

        # Find the referenced node
        if node_id in workflow_data:
            referenced_node = workflow_data[node_id]
            # Recursively extract text from the referenced node
            return self._extract_text_from_node(referenced_node, source_info)

        logger.debug("Could not resolve node reference: %s", node_id)
        return ""

    def _extract_text_from_node(self, node: dict[str, Any], source_info: dict[str, Any]) -> str:
        """Extract text content from a ComfyUI node."""
        class_type = node.get("class_type") or node.get("type", "")
        inputs = node.get("inputs", {})

        logger.debug("_extract_text_from_node: class_type=%s, inputs type=%s", class_type, type(inputs))

        text = ""

        # 1. Prioritize widgets_values for standard ComfyUI nodes.
        # This is the most common format, where values are stored directly in the node.
        if "widgets_values" in node and isinstance(node["widgets_values"], list):
            widgets_values = node["widgets_values"]
            logger.debug("Found widgets_values: %s", widgets_values)

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
                    logger.debug("Detected template/mode text in %s: '%s...' - reducing priority", class_type, text[:60])
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
            elif class_type == "TIPO":
                # TIPO AI prompt generator - extract base input tags, not random output
                if len(widgets_values) >= 1 and isinstance(widgets_values[0], str):
                    text = widgets_values[0]  # Usually the "tags" input
            elif class_type == "CLIPTextEncodeLumina2":
                if len(widgets_values) > 1 and isinstance(widgets_values[1], str):
                    text = widgets_values[1]  # The prompt is the second element
                elif len(widgets_values) > 0 and isinstance(widgets_values[0], str):
                    text = widgets_values[0] # Fallback to the first
            elif class_type == "easy showAnything":
                # HiDream ComfyUI Easy Use display node - nested array format [[text]]
                if len(widgets_values) >= 1:
                    if isinstance(widgets_values[0], list) and len(widgets_values[0]) >= 1:
                        text = str(widgets_values[0][0])  # Unwrap nested array
                    elif isinstance(widgets_values[0], str):
                        text = widgets_values[0]  # Fallback to direct string
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
            logger.debug("Checking inputs dict for text (flat/TensorArt format): %s", list(inputs.keys()))
            if class_type in ["CLIPTextEncode", "CLIPTextEncodeSDXL", "CLIPTextEncodeSDXLRefiner", "BNK_CLIPTextEncodeAdvanced", "String Literal", "Text Multiline", "easy positive"]:
                text = inputs.get("text", "")
                # Check if text is a node reference (e.g., ['12', 0])
                if isinstance(text, list) and len(text) == 2:
                    # This is a node connection reference - need to resolve it
                    referenced_node_id = str(text[0])
                    text = self._resolve_node_reference(source_info, referenced_node_id)
                    logger.debug("Resolved node reference ['%s', %s] to text: '%s...'", referenced_node_id, text[1] if isinstance(text, list) else 0, str(text)[:60])
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
            elif class_type == "TIPO":
                # TIPO AI prompt generator - check for tags input
                text = inputs.get("tags", inputs.get("text", ""))
            elif class_type == "TensorArt_PromptText":
                # TensorArt uses capital T "Text" field
                text = inputs.get("Text", inputs.get("text", ""))
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
                logger.debug("Detected empty/placeholder text in %s: '%s...' - marking as template", class_type, text_str[:60])
                text_str = f"[TEMPLATE]{text_str}"

            logger.debug("Extracted text from %s: '%s...'", class_type, text_str[:60] if text_str else "EMPTY")
            return text_str

        logger.debug("Extracted text from %s: 'EMPTY...'", class_type)
        return ""

    def extract_text_candidates_from_workflow(self, workflow_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract text candidates from ComfyUI workflow with numpy-enhanced scoring."""
        start_time = time.time()
        candidates = []

        try:
            # Get workflow hash for caching
            from ..logger import info_monitor as nfo
            workflow_hash = self._get_workflow_hash(workflow_data)

            # TEMP DEBUG: Disable cache to test AI generator detection
            self.logger.debug("[CACHE] ⚠️ CACHE DISABLED FOR TESTING - will score fresh every time")
            RUNTIME_ANALYTICS["cache_misses"] += 1

            # if workflow_hash in WORKFLOW_CACHE:
            #     RUNTIME_ANALYTICS["cache_hits"] += 1
            #     self.logger.debug("[CACHE] ⚠️ Returning CACHED workflow results (hash: %s...)", workflow_hash[:16])
            #     self.logger.debug("[CACHE] Cached candidates will have OLD confidence scores!")
            #     return WORKFLOW_CACHE[workflow_hash]
            #
            # RUNTIME_ANALYTICS["cache_misses"] += 1
            # self.logger.debug("[CACHE] Cache miss - will score candidates fresh")

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
            logger.info("Processing %s conditioning nodes", len(conditioning_nodes))
            for i, node in enumerate(conditioning_nodes):
                logger.debug("Processing node %s: type=%s", i, type(node))
                if not isinstance(node, dict):
                    logger.debug("Skipping non-dict node: %s", node)
                    continue

                # Pass workflow_data as source_info so node references can be resolved
                text = self._extract_text_from_node(node, workflow_data)
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
                        "is_connected": is_connected,
                        # NEW: Add graph analysis data
                        "workflow_data": workflow_data,
                        "node_id": node_id
                    }

                    # Score the candidate
                    from ..logger import info_monitor as nfo
                    self.logger.debug("[EXTRACT] About to score candidate: node_type='%s'", node.get("class_type") or node.get("type", ""))
                    scored_candidate = self.score_candidate(candidate, "comfyui")
                    self.logger.debug("[EXTRACT] After scoring: confidence=%.3f", scored_candidate.get("confidence", 0))
                    logger.info("CANDIDATE: node_type='%s', confidence=%.3f, text='%s...'", node.get("class_type") or node.get("type", ""), scored_candidate.get("confidence", 0), text[:80])
                    candidates.append(scored_candidate)

            # Sort by confidence and limit results
            candidates.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            candidates = candidates[:self.MAX_CANDIDATES]

            # Cache results
            # TEMP DEBUG: Don't cache while testing
            # WORKFLOW_CACHE[workflow_hash] = candidates
            self.logger.debug("[CACHE] Skipping cache storage while testing")

            processing_time = time.time() - start_time
            self._track_analytics("extract_text_candidates_from_workflow", True, processing_time, workflow_type)

            return candidates

        except Exception as e:
            self.logger.error("Error extracting ComfyUI workflow candidates: %s", e)
            processing_time = time.time() - start_time
            self._track_analytics("extract_text_candidates_from_workflow", False, processing_time, "error")
            return []

    def score_candidate(self, candidate: dict[str, Any], format_type: str = "comfyui", prompt_type: str = "positive") -> dict[str, Any]:
        """Score a ComfyUI text candidate with enhanced domain knowledge."""
        from ..logger import info_monitor as nfo
        node_type = candidate.get("source_node_type", "")
        self.logger.debug("[SCORE_CANDIDATE] Scoring candidate: node_type='%s', text='%s...'",
            node_type, candidate.get("text", "")[:40])

        # Start with base scoring
        scored_candidate = super().score_candidate(candidate, format_type)

        text = candidate.get("text", "")
        node_type = candidate.get("source_node_type", "")
        confidence = scored_candidate.get("confidence", 0.5)
        self.logger.debug("[SCORE_CANDIDATE] After base scoring: confidence=%.3f", confidence)

        # Apply ComfyUI-specific scoring adjustments

        # Check for template content and heavily penalize
        if text.startswith("[TEMPLATE]"):
            logger.debug("Template content detected - applying heavy penalty")
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
        self.logger.debug("[SCORE_CANDIDATE] Calling _get_connection_bonus...")
        connection_bonus = self._get_connection_bonus(candidate)
        self.logger.debug("[SCORE_CANDIDATE] Connection bonus: %.3f", connection_bonus)
        confidence += connection_bonus  # Add to existing confidence rather than multiply
        self.logger.debug("[SCORE_CANDIDATE] After connection bonus: confidence=%.3f", confidence)

        # Additive bonus for explicit node titles
        node_title = candidate.get("node_title", "").lower()
        if "positive prompt" in node_title:
            confidence += 10.0  # Large additive bonus to ensure it wins

        # TensorArt LoRA/Checkpoint naming penalty - CRITICAL for flat format
        if self._is_tensorart_technical_naming(text):
            confidence *= 0.01  # Heavy penalty for LoRA technical names
            logger.debug("TensorArt technical naming penalty applied: %s...", text[:50])

        # Wildcard template pattern penalty - CRITICAL for complex workflows
        if self._is_wildcard_template_pattern(text):
            confidence *= 0.02  # Heavy penalty for unresolved wildcard templates
            logger.debug("Wildcard template pattern penalty applied: %s...", text[:50])

        # ComfyUI template detection penalty - APPLY THIS LAST AND STRONGLY
        # CONTEXT-AWARE: Pass node_type to avoid rejecting real prompts in text encoder nodes
        if self._is_comfyui_template_text(text, node_type=node_type):
            confidence *= 0.01  # Much heavier penalty for templates
            logger.debug("Template text penalty applied to %s: %s...", node_type, text[:50])

        # Update the scored candidate (allow scores > 1.0 for high priority nodes)
        scored_candidate["confidence"] = max(0.0, confidence)
        scored_candidate["scoring_method"] = "comfyui_numpy"
        scored_candidate["node_type_score"] = node_score_multiplier
        scored_candidate["connection_bonus"] = connection_bonus

        self.logger.debug("[SCORE_CANDIDATE] ✅ Final confidence: %.3f (node_type='%s')", scored_candidate["confidence"], node_type)

        return scored_candidate

    def _get_connection_bonus(self, candidate: dict[str, Any]) -> float:
        """Calculate connection-based bonus using intelligent graph traversal.

        Uses workflow graph analysis to determine actual importance:
        - Direct connections to samplers get highest bonus
        - Nodes in main execution path get high bonus
        - Utility/intermediate nodes get lower bonus
        - Disconnected nodes get no bonus
        - ShowText connected to AI generators gets large bonus
        """
        node_type = candidate.get("source_node_type", "")
        text = candidate.get("text", "")

        # Simple check: If Text Multiline has very short text, it's probably AI input
        if node_type == "Text Multiline" and len(text) < 100:
            return -5.0

        # Boost ShowText nodes with longer, more detailed content (actual prompts vs filenames)
        if node_type == "ShowText|pysssss" and len(text) > 200:
            return 3.0  # Boost for detailed ShowText content

        # Enhanced graph-aware connection scoring
        centrality_bonus = self._calculate_graph_centrality(candidate)
        return centrality_bonus

    def _calculate_graph_centrality(self, candidate: dict[str, Any]) -> float:
        """Calculate node importance using graph centrality analysis.

        This is the ADVANCED SYSTEM that does intelligent graph traversal:
        - Analyzes workflow execution paths
        - Calculates node centrality in the graph
        - Prioritizes nodes based on their role in the workflow
        """
        # Get candidate's workflow context
        workflow_data = candidate.get("workflow_data")
        node_id = candidate.get("node_id")

        if not workflow_data or node_id is None:
            return 0.1  # Small fallback bonus

        # Build execution graph
        execution_graph = self._build_execution_graph(workflow_data)

        # Calculate centrality score
        centrality_score = self._calculate_node_centrality(execution_graph, node_id)

        # Convert to bonus (0.0 to 2.0 range)
        bonus = min(centrality_score * 0.5, 2.0)

        logger.debug("Graph centrality for node %s: %.3f -> bonus %.3f", node_id, centrality_score, bonus)

        return bonus

    def _build_execution_graph(self, workflow_data: dict[str, Any]) -> dict[str, Any]:
        """Build an execution graph showing actual workflow paths.

        This creates a graph representation showing:
        - Which nodes feed into samplers (high priority paths)
        - Execution order and dependencies
        - Workflow topology for centrality analysis
        """
        nodes = workflow_data.get("nodes", [])
        links = workflow_data.get("links", [])

        # Create adjacency lists
        graph = {
            "nodes": {},
            "edges": {},  # node_id -> [connected_node_ids]
            "reverse_edges": {},  # For backward tracing
            "samplers": [],
            "prompt_nodes": []
        }

        # Index nodes by ID
        for node in nodes:
            if isinstance(node, dict):
                node_id = node.get("id")
                if node_id is not None:
                    graph["nodes"][node_id] = node
                    graph["edges"][node_id] = []
                    graph["reverse_edges"][node_id] = []

                    # Identify critical node types
                    class_type = node.get("class_type", "")
                    if "sampler" in class_type.lower() or class_type in ["KSampler", "SamplerCustomAdvanced"]:
                        graph["samplers"].append(node_id)
                    elif class_type in ["CLIPTextEncode", "Text Multiline", "DPRandomGenerator"]:
                        graph["prompt_nodes"].append(node_id)

        # Build edges from links
        for link in links:
            if isinstance(link, list) and len(link) >= 4:
                # [link_id, output_node, output_slot, input_node, input_slot, ...]
                output_node = link[1]
                input_node = link[3]

                if output_node in graph["edges"] and input_node in graph["reverse_edges"]:
                    graph["edges"][output_node].append(input_node)
                    graph["reverse_edges"][input_node].append(output_node)

        return graph

    def _calculate_node_centrality(self, execution_graph: dict[str, Any], node_id: int) -> float:
        """Calculate how central/important a node is in the workflow execution.

        Uses multiple centrality measures:
        - Distance to samplers (closer = higher score)
        - Number of paths through this node
        - Betweenness centrality (how many paths go through this node)
        """
        if node_id not in execution_graph["nodes"]:
            return 0.0

        centrality_score = 0.0

        # 1. Distance to samplers (most important factor)
        sampler_distance_score = self._calculate_sampler_distance_score(execution_graph, node_id)
        centrality_score += sampler_distance_score * 2.0  # Weight this heavily

        # 2. Betweenness centrality (how many execution paths go through this node)
        betweenness_score = self._calculate_betweenness_centrality(execution_graph, node_id)
        centrality_score += betweenness_score * 1.0

        # 3. Node type importance
        node_type_score = self._get_node_type_centrality(execution_graph, node_id)
        centrality_score += node_type_score * 1.5

        logger.debug("Node %s centrality: sampler_dist=%.2f, betweenness=%.2f, type=%.2f", node_id, sampler_distance_score, betweenness_score, node_type_score)

        return centrality_score

    def _calculate_sampler_distance_score(self, execution_graph: dict[str, Any], node_id: int) -> float:
        """Calculate score based on distance to sampler nodes (closer = better)."""
        samplers = execution_graph["samplers"]
        if not samplers:
            return 0.0

        min_distance = float("inf")

        # BFS to find shortest path to any sampler
        from collections import deque  # noqa: PLC0415
        queue = deque([(node_id, 0)])
        visited = {node_id}

        while queue:
            current_node, distance = queue.popleft()

            if current_node in samplers:
                min_distance = min(min_distance, distance)
                continue

            # Explore connected nodes
            for next_node in execution_graph["edges"].get(current_node, []):
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, distance + 1))

        # Convert distance to score (closer = higher score)
        if min_distance == float("inf"):
            return 0.0
        if min_distance == 0:
            return 1.0  # Direct sampler connection
        if min_distance == 1:
            return 0.8  # One hop from sampler
        if min_distance == 2:
            return 0.6  # Two hops
        return max(0.1, 1.0 / min_distance)

    def _calculate_betweenness_centrality(self, execution_graph: dict[str, Any], node_id: int) -> float:
        """Calculate betweenness centrality (how many paths go through this node)."""
        # Simplified betweenness: count paths from prompt nodes to samplers that go through this node
        prompt_nodes = execution_graph["prompt_nodes"]
        samplers = execution_graph["samplers"]

        if not prompt_nodes or not samplers:
            return 0.0

        paths_through_node = 0
        total_paths = 0

        # For each prompt->sampler pair, check if path goes through our node
        for prompt_node in prompt_nodes:
            for sampler_node in samplers:
                path_exists, goes_through = self._path_goes_through_node(execution_graph, prompt_node, sampler_node, node_id)
                if path_exists:
                    total_paths += 1
                    if goes_through:
                        paths_through_node += 1

        return paths_through_node / max(1, total_paths)

    def _get_node_type_centrality(self, execution_graph: dict[str, Any], node_id: int) -> float:
        """Get centrality score based on node type importance."""
        node = execution_graph["nodes"].get(node_id)
        if not node:
            return 0.0

        class_type = node.get("class_type", "")

        # High importance node types
        if class_type in ["CLIPTextEncode", "Text Multiline"]:
            return 1.0
        if class_type in ["DPRandomGenerator", "WildcardProcessor"]:
            return 1.2
        if "Sampler" in class_type:
            return 0.8  # Samplers are important but not for text content
        return 0.5

    def _path_goes_through_node(self, execution_graph: dict[str, Any], start_node: int, end_node: int, target_node: int) -> tuple[bool, bool]:
        """Check if a path from start to end exists, and if it goes through target_node."""
        if start_node == end_node:
            return True, start_node == target_node

        # BFS to find if path exists
        from collections import deque  # noqa: PLC0415
        queue = deque([(start_node, [start_node])])
        visited = {start_node}

        while queue:
            current_node, path = queue.popleft()

            if current_node == end_node:
                return True, target_node in path

            for next_node in execution_graph["edges"].get(current_node, []):
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))

        return False, False

    def _is_tensorart_technical_naming(self, text: str) -> bool:
        """Detect TensorArt LoRA/checkpoint technical naming that should be deprioritized.

        Simple, non-over-engineered detection for TA flat format issues.
        """
        text_lower = text.lower().strip()

        # LoRA patterns - the most common issue
        lora_patterns = [
            "<lora:", ".safetensors", "ems-", "-ems.safetensors",
            "lora:ems", "modelfilename", "modelhash"
        ]

        # Checkpoint/model patterns
        checkpoint_patterns = [
            ".ckpt", "checkpoint", "model.safetensors",
            "basemodel", "modelid", "vae_name"
        ]

        # Check for LoRA technical patterns
        if any(pattern in text_lower for pattern in lora_patterns):
            return True

        # Check for checkpoint technical patterns
        if any(pattern in text_lower for pattern in checkpoint_patterns):
            return True



        return False

    def _is_wildcard_template_pattern(self, text: str) -> bool:
        """Detect wildcard template patterns that haven't been resolved yet.

        Patterns like {word|}, {word1,word2|}, __wildcard__ indicate templates.
        """
        # Check for common wildcard syntax patterns
        wildcard_patterns = [
            "{", "}|",  # {vaporwave,|} style patterns
            "__", "__",  # __location__ style patterns
            "|",  # Multiple choice patterns
        ]

        # Count wildcard indicators
        wildcard_count = 0
        if "{" in text and "}" in text:
            wildcard_count += text.count("{")
        if "__" in text:
            wildcard_count += text.count("__") // 2  # Pairs
        if "|" in text and ("{" in text or "__" in text):
            wildcard_count += text.count("|")

        # If we have 3+ wildcard indicators, it's likely a template
        if wildcard_count >= 3:
            return True

        # Specific problematic patterns
        template_indicators = [
            "{vaporwave,|}", "{sharp details,|}", "{realistic,|}",
            "{muted colors|}", "__test2_location__", "__random_waifu_xl__",
            "__any_location__", "__rpg_character_m_sexy__"
        ]

        return any(indicator in text for indicator in template_indicators)

    def enhance_engine_result(self, engine_result: dict[str, Any], original_file_path: str | None = None) -> dict[str, Any]:
        """Enhance engine results with ComfyUI-specific numpy analysis."""
        try:
            from ..logger import info_monitor as nfo
            self.logger.debug("[COMFYUI_SCORER] enhance_engine_result called")
            raw_metadata = engine_result.get("raw_metadata", {})

            # Check if this looks like ComfyUI data
            if not isinstance(raw_metadata, dict):
                self.logger.debug("[COMFYUI_SCORER] raw_metadata is not a dict: %s", type(raw_metadata))
                return engine_result

            self.logger.debug("[COMFYUI_SCORER] raw_metadata is dict with keys: %s", list(raw_metadata.keys())[:10])

            # Handle different workflow data locations
            workflow_data = None
            if "workflow" in raw_metadata:
                workflow_data = raw_metadata.get("workflow", {})
                logger.debug("Found workflow in raw_metadata['workflow']")
            elif "nodes" in raw_metadata and isinstance(raw_metadata.get("nodes"), list):
                # Standard ComfyUI case - raw_metadata contains the workflow with nodes array
                workflow_data = raw_metadata
                logger.debug("Using raw_metadata as workflow (standard ComfyUI case)")
            elif "nodes" in raw_metadata or "links" in raw_metadata:
                # TensorArt case - raw_metadata is the workflow with flat nodes
                workflow_data = raw_metadata
                logger.debug("Using raw_metadata as workflow (TensorArt flat case)")
            else:
                # Check for flat format - numeric node IDs as keys with class_type
                numeric_keys = []
                for key, value in raw_metadata.items():
                    if (isinstance(key, str) and key.isdigit() and
                        isinstance(value, dict) and "class_type" in value):
                        numeric_keys.append(key)

                if numeric_keys:
                    workflow_data = raw_metadata
                    logger.debug("Using raw_metadata as flat format workflow (%s nodes)", len(numeric_keys))
                else:
                    logger.debug("No workflow structure detected in raw_metadata")

            if not isinstance(workflow_data, dict):
                self.logger.debug("[COMFYUI_SCORER] workflow_data is not a dict: %s", type(workflow_data))
                return engine_result

            self.logger.debug("[COMFYUI_SCORER] workflow_data is dict with keys: %s", list(workflow_data.keys())[:10])
            self.logger.debug("[COMFYUI_SCORER] About to call extract_text_candidates_from_workflow")

            # Extract and analyze workflow candidates
            candidates = self.extract_text_candidates_from_workflow(workflow_data)
            self.logger.debug("[COMFYUI_SCORER] Extracted %d candidates", len(candidates))

            if candidates:
                from ..logger import info_monitor as nfo
                self.logger.debug("[COMFYUI_SCORER] Analyzing %d candidates:", len(candidates))
                for idx, candidate in enumerate(candidates):
                    self.logger.debug("[COMFYUI_SCORER]   Candidate %d: node_type='%s', confidence=%.3f, text='%s...'",
                        idx + 1,
                        candidate.get("source_node_type", "UNKNOWN"),
                        candidate.get("confidence", 0),
                        candidate.get("text", "")[:60])

                # Separate positive and negative candidates
                positive_candidates = []
                negative_candidates = []

                self.logger.debug("[COMFYUI_SCORER] Classifying candidates as positive/negative:")
                for candidate in candidates:
                    text = candidate.get("text", "").lower()
                    original_text = candidate.get("text", "")
                    node_type = candidate.get("source_node_type", "UNKNOWN")

                    self.logger.debug("[COMFYUI_SCORER]   Classifying: node_type='%s', text='%s...'", node_type, original_text[:60])

                    # First check ComfyUI node title for explicit negative/positive markers
                    node_title = candidate.get("node_title", "").lower() if "node_title" in candidate else ""
                    is_negative_by_title = ("negative" in node_title and "prompt" in node_title) or "negative prompt" in node_title
                    is_positive_by_title = ("positive" in node_title and "prompt" in node_title) or "positive prompt" in node_title

                    # If node title explicitly indicates type, use that (high confidence)
                    if is_negative_by_title:
                        is_negative = True
                        logger.debug("Node title indicates negative: '%s'", node_title)
                    elif is_positive_by_title:
                        is_negative = False
                        logger.debug("Node title indicates positive: '%s'", node_title)
                    else:
                        # Fallback to JSON-based negative detection system
                        is_negative = negative_indicators.is_negative_text(original_text)

                    if is_negative:
                        logger.debug("JSON-based detection classified as negative: '%s...'", original_text[:40])

                    if is_negative:
                        self.logger.debug("[COMFYUI_SCORER]     → NEGATIVE (node_type='%s', confidence=%.3f)",
                            candidate.get("source_node_type", "UNKNOWN"),
                            candidate.get("confidence", 0))
                        negative_candidates.append(candidate)
                    else:
                        self.logger.debug("[COMFYUI_SCORER]     → POSITIVE (node_type='%s', confidence=%.3f)",
                            candidate.get("source_node_type", "UNKNOWN"),
                            candidate.get("confidence", 0))
                        positive_candidates.append(candidate)

                enhanced_result = engine_result.copy()

                # Find best positive candidate
                if positive_candidates:
                    best_positive = max(positive_candidates, key=lambda x: x.get("confidence", 0))
                    self.logger.debug("[COMFYUI_SCORER] Best positive candidate: confidence=%.3f, node_type='%s', text='%s...'",
                        best_positive.get("confidence", 0),
                        best_positive.get("source_node_type", "UNKNOWN"),
                        best_positive.get("text", "")[:80])

                    if best_positive.get("confidence", 0) > 0.5:
                        self.logger.debug("[COMFYUI_SCORER] ✅ Setting prompt to best positive candidate")
                        enhanced_result["prompt"] = best_positive["text"]
                    else:
                        self.logger.debug("[COMFYUI_SCORER] ❌ Best positive confidence too low (%.3f < 0.5), keeping parser prompt", best_positive.get("confidence", 0))
                else:
                    self.logger.debug("[COMFYUI_SCORER] No positive candidates found")

                # Find best negative candidate
                if negative_candidates:
                    best_negative = max(negative_candidates, key=lambda x: x.get("confidence", 0))
                    self.logger.debug("[COMFYUI_SCORER] Best negative candidate: confidence=%.3f, node_type='%s', text='%s...'",
                        best_negative.get("confidence", 0),
                        best_negative.get("source_node_type", "UNKNOWN"),
                        best_negative.get("text", "")[:80])

                    if best_negative.get("confidence", 0) > 0.5:
                        self.logger.debug("[COMFYUI_SCORER] ✅ Setting negative_prompt to best negative candidate")
                        enhanced_result["negative_prompt"] = best_negative["text"]
                    else:
                        self.logger.debug("[COMFYUI_SCORER] ❌ Best negative confidence too low (%.3f < 0.5), keeping parser negative", best_negative.get("confidence", 0))
                else:
                    # Keep existing negative_prompt if parser already found one
                    # Don't clear it - parser might have extracted embeddings/URNs that numpy doesn't recognize
                    self.logger.debug("[COMFYUI_SCORER] No negative candidates found, keeping existing negative_prompt from parser")
                    # No-op: keep enhanced_result["negative_prompt"] = engine_result.get("negative_prompt", "")

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
            self.logger.error("Error in ComfyUI numpy enhancement: %s", e)

        return engine_result


def should_use_comfyui_numpy_scoring(engine_result: dict[str, Any]) -> bool:
    """Determine if ComfyUI numpy scoring should be applied."""
    from ..logger import get_logger  # noqa: PLC0415, TID252
    logger = get_logger(__name__)

    raw_metadata = engine_result.get("raw_metadata", {})
    tool = engine_result.get("tool", "").lower()
    format_name = engine_result.get("format", "").lower()

    logger.debug("ComfyUI scoring check - tool: '%s', format: '%s'", tool, format_name)
    logger.debug("'comfy' in tool: %s", "comfy" in tool)
    logger.info("ComfyUI scoring check - tool: %s, format: %s", tool, format_name)
    logger.info("raw_metadata type: %s, keys: %s", type(raw_metadata), list(raw_metadata.keys()) if isinstance(raw_metadata, dict) else "not dict")

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
            logger.info("Found TensorArt-style workflow with %s nodes", len(node_like_keys))
            return True

    # Check for ComfyUI-specific indicators in the result
    if "comfy" in tool or "comfy" in format_name or "tensorart" in tool or "tensorart" in format_name:
        logger.info("Found ComfyUI indicator in tool/format names - matched on tool=%s, format=%s", tool, format_name)
        return True

    # NEW CHECK: If it's a Civitai A1111, check if its raw_metadata looks like a ComfyUI workflow
    if tool == "civitai a1111" and isinstance(raw_metadata, dict):  # noqa: SIM102
        # Check for typical ComfyUI workflow top-level keys
        if "nodes" in raw_metadata and "links" in raw_metadata and "version" in raw_metadata:
            logger.info("Found Civitai A1111 with ComfyUI-like workflow structure in raw_metadata, applying ComfyUI scoring")
            return True

    logger.info("No ComfyUI indicators found")
    return False
