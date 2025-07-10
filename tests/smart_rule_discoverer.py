# Smart Rule Discoverer - Finds new AI tools in your files automatically!

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import defaultdict, Counter
import toml

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

class ToolDiscoverer:
    """
    Automatically discovers new AI tools by analyzing metadata patterns
    in your image files and suggests rules for them!
    """
    
    def __init__(self, rules_toml_path: str = "config/rules.toml"):
        self.rules_path = Path(rules_toml_path)
        self.known_tools = self._load_known_tools()
        self.discovered_patterns = defaultdict(list)
        self.analysis_results = {}
    
    def _load_known_tools(self) -> Set[str]:
        """Load currently known tools from rules.toml"""
        known = set()
        if self.rules_path.exists():
            try:
                with open(self.rules_path, 'r', encoding='utf-8') as f:
                    config = toml.load(f)
                    if "parsers" in config:
                        known.update(config["parsers"].keys())
            except Exception as e:
                print(f"Error loading rules.toml: {e}")
        
        print(f"📋 Known tools: {sorted(known)}")
        return known
    
    def scan_folder(self, folder_path: str, max_files: int = 100) -> Dict[str, Any]:
        """
        Scan a folder for images AND JSON files to analyze metadata patterns
        """
        folder = Path(folder_path)
        if not folder.exists():
            return {"error": f"Folder not found: {folder_path}"}
        
        print(f"🔍 Scanning folder: {folder}")
        print(f"📊 Will analyze up to {max_files} files")
        
        # Find both image and JSON files
        image_files = []
        json_files = []
        
        for ext in ['.png', '.jpg', '.jpeg', '.webp']:
            image_files.extend(folder.glob(f"*{ext}"))
            image_files.extend(folder.glob(f"*{ext.upper()}"))
        
        for ext in ['.json']:
            json_files.extend(folder.glob(f"*{ext}"))
            json_files.extend(folder.glob(f"*{ext.upper()}"))
        
        all_files = image_files + json_files
        
        if not all_files:
            return {"error": "No image or JSON files found in folder"}
        
        print(f"🖼️ Found {len(image_files)} image files")
        print(f"📄 Found {len(json_files)} JSON files")
        print(f"📊 Total files to analyze: {len(all_files)}")
        
        # Analyze up to max_files
        analyzed_files = []
        unknown_patterns = []
        
        for i, file_path in enumerate(all_files[:max_files]):
            print(f"🔍 Analyzing {i+1}/{min(len(all_files), max_files)}: {file_path.name}")
            
            if file_path.suffix.lower() == '.json':
                analysis = self._analyze_json_file(file_path)
            else:
                analysis = self._analyze_image(file_path)
            
            analyzed_files.append(analysis)
            
            # Check if this looks like an unknown tool
            if analysis.get("appears_unknown"):
                unknown_patterns.append(analysis)
        
        # Group and analyze unknown patterns
        suggestions = self._analyze_unknown_patterns(unknown_patterns)
        
        results = {
            "folder_path": str(folder),
            "total_files": len(all_files),
            "image_files": len(image_files),
            "json_files": len(json_files),
            "analyzed_files": len(analyzed_files),
            "known_tools_found": self._count_known_tools(analyzed_files),
            "unknown_patterns": len(unknown_patterns),
            "suggestions": suggestions
        }
        
        self.analysis_results = results
        return results
    
    def _analyze_image(self, img_path: Path) -> Dict[str, Any]:
        """Analyze a single image for metadata patterns"""
        analysis = {
            "file_name": img_path.name,
            "file_path": str(img_path),
            "appears_unknown": False,
            "metadata_sources": [],
            "potential_tool_indicators": [],
            "patterns_found": []
        }
        
        if not PILLOW_AVAILABLE:
            analysis["error"] = "Pillow not available"
            return analysis
        
        try:
            with Image.open(img_path) as img:
                # Check PNG text chunks
                if hasattr(img, 'text') and img.text:
                    analysis["metadata_sources"].append("PNG text chunks")
                    analysis["png_chunks"] = dict(img.text)
                    
                    # Analyze PNG chunks for unknown patterns
                    for key, value in img.text.items():
                        patterns = self._analyze_metadata_content(key, value)
                        analysis["patterns_found"].extend(patterns)
                
                # Check EXIF data
                if hasattr(img, '_getexif') and img._getexif():
                    analysis["metadata_sources"].append("EXIF data")
                    # Basic EXIF analysis
                
                # Check for unknown tool indicators
                tool_indicators = self._detect_tool_indicators(analysis)
                analysis["potential_tool_indicators"] = tool_indicators
                
                # Determine if this appears to be an unknown tool
                analysis["appears_unknown"] = self._is_likely_unknown_tool(analysis)
                
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis
    
    def _analyze_json_file(self, json_path: Path) -> Dict[str, Any]:
        """Analyze a JSON file for tool patterns"""
        analysis = {
            "file_name": json_path.name,
            "file_path": str(json_path),
            "file_type": "json",
            "appears_unknown": False,
            "metadata_sources": ["JSON file"],
            "potential_tool_indicators": [],
            "patterns_found": []
        }
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            analysis["json_data"] = data
            
            # Analyze the JSON content for patterns
            patterns = self._analyze_json_content(data, "root")
            analysis["patterns_found"].extend(patterns)
            
            # Detect tool indicators from JSON content
            tool_indicators = self._detect_json_tool_indicators(data)
            analysis["potential_tool_indicators"] = tool_indicators
            
            # Determine if this appears to be an unknown tool
            analysis["appears_unknown"] = self._is_likely_unknown_json_tool(analysis)
            
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis
    
    def _analyze_json_content(self, data: Any, source_name: str) -> List[Dict[str, Any]]:
        """Analyze JSON content for tool patterns"""
        patterns = []
        
        if isinstance(data, dict):
            # Direct JSON analysis
            patterns.append({
                "type": "json_metadata",
                "source": source_name,
                "keys": list(data.keys()),
                "sample_data": self._sample_json_data(data),
                "structure_type": self._classify_json_structure(data)
            })
            
            # Check for ComfyUI workflow patterns
            if self._looks_like_comfyui(data):
                patterns.append({
                    "type": "comfyui_workflow",
                    "source": source_name,
                    "node_types": self._extract_comfyui_nodes(data),
                    "workflow_complexity": len(self._extract_comfyui_nodes(data))
                })
            
            # Check for configuration file patterns
            if self._looks_like_config(data):
                patterns.append({
                    "type": "config_file",
                    "source": source_name,
                    "config_sections": list(data.keys()),
                    "config_type": self._classify_config_type(data)
                })
            
            # Check for AI generation parameters
            if self._looks_like_ai_params(data):
                patterns.append({
                    "type": "ai_generation_params",
                    "source": source_name,
                    "param_keys": [k for k in data.keys() if self._is_ai_param_key(k)],
                    "has_prompt": any("prompt" in k.lower() for k in data.keys()),
                    "has_model": any("model" in k.lower() for k in data.keys())
                })
        
        return patterns
    
    def _classify_json_structure(self, data: Dict[str, Any]) -> str:
        """Classify the type of JSON structure"""
        keys = list(data.keys())
        
        # ComfyUI workflow detection
        if any(k.isdigit() for k in keys) or "nodes" in keys:
            return "comfyui_workflow"
        
        # Configuration file detection
        if any(k in ["settings", "config", "preferences", "options"] for k in keys):
            return "configuration"
        
        # AI parameters detection
        ai_indicators = ["prompt", "steps", "sampler", "cfg", "seed", "model", "width", "height"]
        if any(any(indicator in k.lower() for indicator in ai_indicators) for k in keys):
            return "ai_parameters"
        
        # Metadata file detection
        if any(k in ["metadata", "info", "version", "tool", "app"] for k in keys):
            return "metadata"
        
        return "unknown"
    
    def _detect_json_tool_indicators(self, data: Any) -> List[str]:
        """Detect tool indicators from JSON data"""
        indicators = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                # Look for tool/version identifiers
                if any(word in key.lower() for word in ["tool", "app", "software", "generator", "version"]):
                    if isinstance(value, str) and len(value) < 50:
                        indicators.append(f"Tool identifier: {key} = {value}")
                
                # Look for unique parameter names that might indicate specific tools
                if self._is_unique_param_name(key):
                    indicators.append(f"Unique parameter: {key}")
                
                # Look for specific model/sampler names
                if "model" in key.lower() or "sampler" in key.lower():
                    if isinstance(value, str) and self._looks_like_tool_specific_name(value):
                        indicators.append(f"Tool-specific {key}: {value}")
        
        return indicators
    
    def _is_likely_unknown_json_tool(self, analysis: Dict[str, Any]) -> bool:
        """Determine if JSON appears to be from an unknown tool"""
        # Has clear tool indicators
        has_indicators = len(analysis.get("potential_tool_indicators", [])) > 0
        
        # Has structured patterns that suggest a tool
        has_patterns = any(p["type"] in ["comfyui_workflow", "ai_generation_params", "config_file"] 
                          for p in analysis.get("patterns_found", []))
        
        # Contains AI-related terms but isn't from known tools
        contains_ai_terms = False
        for pattern in analysis.get("patterns_found", []):
            if pattern["type"] == "json_metadata":
                keys = pattern.get("keys", [])
                ai_terms = ["prompt", "steps", "sampler", "cfg", "seed", "model", "diffusion"]
                if any(any(term in k.lower() for term in ai_terms) for k in keys):
                    contains_ai_terms = True
                    break
        
        return (has_indicators or has_patterns or contains_ai_terms)
    
    def _looks_like_config(self, data: Dict[str, Any]) -> bool:
        """Check if JSON looks like a configuration file"""
        config_indicators = ["settings", "config", "preferences", "options", "params"]
        return any(indicator in data for indicator in config_indicators)
    
    def _looks_like_ai_params(self, data: Dict[str, Any]) -> bool:
        """Check if JSON looks like AI generation parameters"""
        ai_indicators = ["prompt", "steps", "sampler", "cfg", "seed", "model", "width", "height"]
        found_indicators = sum(1 for key in data.keys() 
                              if any(indicator in key.lower() for indicator in ai_indicators))
        return found_indicators >= 3  # Need at least 3 AI-related keys
    
    def _classify_config_type(self, data: Dict[str, Any]) -> str:
        """Classify the type of configuration"""
        keys = set(k.lower() for k in data.keys())
        
        if any(ui_term in keys for ui_term in ["ui", "interface", "theme", "layout"]):
            return "ui_config"
        elif any(model_term in keys for model_term in ["model", "checkpoint", "lora", "embedding"]):
            return "model_config"
        elif any(gen_term in keys for gen_term in ["generation", "sampling", "steps", "cfg"]):
            return "generation_config"
        else:
            return "general_config"
    
    def _is_ai_param_key(self, key: str) -> bool:
        """Check if a key looks like an AI parameter"""
        ai_params = [
            "prompt", "negative", "steps", "sampler", "cfg", "scale", "seed", 
            "model", "lora", "embedding", "width", "height", "batch", "denoise"
        ]
        key_lower = key.lower()
        return any(param in key_lower for param in ai_params)
    
    def _is_unique_param_name(self, key: str) -> bool:
        """Check if a parameter name looks unique/tool-specific"""
        # Skip very common keys
        common_keys = {
            "prompt", "negative_prompt", "steps", "sampler", "cfg_scale", "seed", 
            "width", "height", "model", "version", "created", "modified"
        }
        
        if key.lower() in common_keys:
            return False
        
        # Look for tool-specific patterns
        tool_patterns = [
            "_version", "_mode", "_preset", "_style", "_enhancement", 
            "_boost", "_quality", "_type", "_method", "_algorithm"
        ]
        
        return any(pattern in key.lower() for pattern in tool_patterns)
    
    def _looks_like_tool_specific_name(self, value: str) -> bool:
        """Check if a value looks like a tool-specific name"""
        if not isinstance(value, str) or len(value) > 100:
            return False
        
        # Look for version numbers, specific naming patterns
        has_version = re.search(r'v?\d+\.\d+', value.lower())
        has_special_chars = any(char in value for char in ['_', '-', '.'])
        is_descriptive = len(value) > 5 and not value.isdigit()
        
        return bool(has_version or (has_special_chars and is_descriptive))
        """Analyze metadata content for patterns"""
        patterns = []
        
        # Check if it's JSON
        if self._is_json(value):
            try:
                data = json.loads(value)
                patterns.append({
                    "type": "json_metadata",
                    "chunk": key,
                    "keys": list(data.keys()) if isinstance(data, dict) else [],
                    "sample_data": self._sample_json_data(data)
                })
            except:
                pass
        
        # Check for A1111-style text patterns
        a1111_patterns = self._detect_a1111_patterns(value)
        if a1111_patterns:
            patterns.append({
                "type": "a1111_style_text",
                "chunk": key,
                "patterns": a1111_patterns
            })
        
        # Check for ComfyUI workflow patterns
        if "workflow" in key.lower() or "prompt" in key.lower():
            if self._is_json(value):
                try:
                    data = json.loads(value)
                    if self._looks_like_comfyui(data):
                        patterns.append({
                            "type": "comfyui_workflow",
                            "chunk": key,
                            "node_types": self._extract_comfyui_nodes(data)
                        })
                except:
                    pass
        
        return patterns
    
    def _detect_tool_indicators(self, analysis: Dict[str, Any]) -> List[str]:
        """Detect potential tool name indicators"""
        indicators = []
        
        # Look for tool names in various places
        for pattern in analysis.get("patterns_found", []):
            if pattern["type"] == "json_metadata":
                # Look for version/tool keys in JSON
                keys = pattern.get("keys", [])
                for key in keys:
                    if any(word in key.lower() for word in ["version", "tool", "app", "software", "generator"]):
                        indicators.append(f"JSON key: {key}")
            
            elif pattern["type"] == "a1111_style_text":
                # Look for new patterns in A1111 style
                for p in pattern.get("patterns", []):
                    if p not in ["Steps:", "Sampler:", "CFG scale:", "Seed:", "Size:"]:
                        indicators.append(f"A1111 pattern: {p}")
            
            elif pattern["type"] == "comfyui_workflow":
                # Look for unknown node types
                nodes = pattern.get("node_types", [])
                unknown_nodes = self._filter_unknown_nodes(nodes)
                for node in unknown_nodes:
                    indicators.append(f"ComfyUI node: {node}")
        
        return indicators
    
    def _is_likely_unknown_tool(self, analysis: Dict[str, Any]) -> bool:
        """Determine if this appears to be from an unknown tool"""
        # Has metadata but no clear match to known tools
        has_metadata = len(analysis.get("metadata_sources", [])) > 0
        has_indicators = len(analysis.get("potential_tool_indicators", [])) > 0
        
        return has_metadata and has_indicators
    
    def _analyze_unknown_patterns(self, unknown_patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze unknown patterns and suggest rules"""
        if not unknown_patterns:
            return []
        
        print(f"\n🔍 Analyzing {len(unknown_patterns)} files with unknown patterns...")
        
        suggestions = []
        
        # Group by similar patterns
        grouped_patterns = self._group_similar_patterns(unknown_patterns)
        
        for group_name, group_files in grouped_patterns.items():
            suggestion = self._create_rule_suggestion(group_name, group_files)
            if suggestion:
                suggestions.append(suggestion)
        
        return suggestions
    
    def _group_similar_patterns(self, patterns: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group files with similar metadata patterns"""
        groups = defaultdict(list)
        
        for file_analysis in patterns:
            # Create a signature for this file's patterns
            signature = self._create_pattern_signature(file_analysis)
            groups[signature].append(file_analysis)
        
        # Only keep groups with multiple files (more confidence)
        filtered_groups = {k: v for k, v in groups.items() if len(v) >= 2}
        
        return filtered_groups
    
    def _create_pattern_signature(self, analysis: Dict[str, Any]) -> str:
        """Create a signature string for grouping similar patterns"""
        signatures = []
        
        for pattern in analysis.get("patterns_found", []):
            if pattern["type"] == "json_metadata":
                # Use the most distinctive keys
                keys = pattern.get("keys", [])
                distinctive_keys = [k for k in keys if any(word in k.lower() 
                                  for word in ["version", "tool", "app", "model", "sampler"])]
                if distinctive_keys:
                    signatures.append(f"json:{'-'.join(sorted(distinctive_keys[:3]))}")
            
            elif pattern["type"] == "a1111_style_text":
                # Use unique patterns
                unique_patterns = [p for p in pattern.get("patterns", []) 
                                 if p not in ["Steps:", "Sampler:", "CFG scale:", "Seed:", "Size:"]]
                if unique_patterns:
                    signatures.append(f"a1111:{'-'.join(sorted(unique_patterns[:2]))}")
            
            elif pattern["type"] == "comfyui_workflow":
                # Use distinctive node types
                nodes = pattern.get("node_types", [])
                distinctive_nodes = [n for n in nodes if not any(common in n 
                                   for common in ["KSampler", "CLIPTextEncode", "CheckpointLoader"])]
                if distinctive_nodes:
                    signatures.append(f"comfyui:{'-'.join(sorted(distinctive_nodes[:2]))}")
        
        return "|".join(signatures) or "unknown"
    
    def _create_rule_suggestion(self, group_name: str, group_files: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a rule suggestion for a group of similar files"""
        if len(group_files) < 2:
            return None
        
        # Analyze the group to suggest a tool name and rules
        suggestion = {
            "suggested_tool_name": self._suggest_tool_name(group_name, group_files),
            "confidence": len(group_files),
            "sample_files": [f["file_name"] for f in group_files[:3]],
            "pattern_analysis": self._analyze_group_patterns(group_files),
            "suggested_rules": None
        }
        
        # Generate actual TOML rules
        suggestion["suggested_rules"] = self._generate_rules_for_group(suggestion)
        
        return suggestion
    
    def _suggest_tool_name(self, signature: str, files: List[Dict[str, Any]]) -> str:
        """Suggest a tool name based on the pattern signature"""
        # Try to extract tool name from metadata
        for file_analysis in files:
            for pattern in file_analysis.get("patterns_found", []):
                if pattern["type"] == "json_metadata":
                    sample_data = pattern.get("sample_data", {})
                    # Look for tool/version indicators
                    for key, value in sample_data.items():
                        if any(word in key.lower() for word in ["tool", "app", "software", "generator"]):
                            if isinstance(value, str) and len(value) < 30:
                                return f"Unknown_{value.replace(' ', '_')}"
        
        # Fallback to signature-based name
        if "json:" in signature:
            return f"Unknown_JSON_Tool"
        elif "a1111:" in signature:
            return f"Unknown_A1111_Variant" 
        elif "comfyui:" in signature:
            return f"Unknown_ComfyUI_Variant"
        else:
            return f"Unknown_Tool_{abs(hash(signature)) % 1000}"
    
    def _analyze_group_patterns(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns across a group of files"""
        all_json_keys = []
        all_a1111_patterns = []
        all_comfyui_nodes = []
        
        for file_analysis in files:
            for pattern in file_analysis.get("patterns_found", []):
                if pattern["type"] == "json_metadata":
                    all_json_keys.extend(pattern.get("keys", []))
                elif pattern["type"] == "a1111_style_text":
                    all_a1111_patterns.extend(pattern.get("patterns", []))
                elif pattern["type"] == "comfyui_workflow":
                    all_comfyui_nodes.extend(pattern.get("node_types", []))
        
        # Find most common patterns
        return {
            "common_json_keys": [k for k, count in Counter(all_json_keys).most_common(5)],
            "common_a1111_patterns": [p for p, count in Counter(all_a1111_patterns).most_common(5)],
            "common_comfyui_nodes": [n for n, count in Counter(all_comfyui_nodes).most_common(5)]
        }
    
    def _generate_rules_for_group(self, suggestion: Dict[str, Any]) -> str:
        """Generate TOML rules for a suggested tool"""
        from toml_rule_builder import RuleBuilder, QuickTemplates
        
        tool_name = suggestion["suggested_tool_name"]
        patterns = suggestion["pattern_analysis"]
        
        # Choose the appropriate template based on patterns
        if patterns.get("common_json_keys"):
            # JSON-based tool
            distinctive_keys = [k for k in patterns["common_json_keys"] 
                              if any(word in k.lower() for word in ["version", "tool", "model", "sampler"])]
            if distinctive_keys:
                builder = QuickTemplates.json_metadata_tool(tool_name, distinctive_keys[:3])
                return builder.to_toml_section()
        
        elif patterns.get("common_a1111_patterns"):
            # A1111 variant
            standard_patterns = ["Steps:", "Sampler:", "CFG scale:", "Seed:", "Size:"]
            special_patterns = [p for p in patterns["common_a1111_patterns"] 
                              if p not in standard_patterns]
            if special_patterns:
                builder = QuickTemplates.a1111_text_variant(tool_name, standard_patterns, special_patterns[:3])
                return builder.to_toml_section()
        
        elif patterns.get("common_comfyui_nodes"):
            # ComfyUI variant
            distinctive_nodes = [n for n in patterns["common_comfyui_nodes"]
                               if not any(common in n for common in ["KSampler", "CLIPTextEncode"])]
            if distinctive_nodes:
                builder = QuickTemplates.comfyui_workflow_variant(tool_name, distinctive_nodes[:3])
                return builder.to_toml_section()
        
        return f"# Could not generate rules for {tool_name} - needs manual analysis"
    
    # Utility methods
    def _is_json(self, text: str) -> bool:
        """Check if text is valid JSON"""
        try:
            json.loads(text)
            return True
        except:
            return False
    
    def _sample_json_data(self, data: Any) -> Dict[str, Any]:
        """Get a sample of JSON data for analysis"""
        if isinstance(data, dict):
            return {k: str(v)[:50] for k, v in list(data.items())[:5]}
        return {"sample": str(data)[:100]}
    
    def _detect_a1111_patterns(self, text: str) -> List[str]:
        """Detect A1111-style patterns in text"""
        patterns = []
        # Look for "Word:" patterns
        matches = re.findall(r'\b([A-Za-z][A-Za-z0-9\s]*?):', text)
        return [f"{match.strip()}:" for match in matches if len(match.strip()) > 2]
    
    def _looks_like_comfyui(self, data: Any) -> bool:
        """Check if data looks like ComfyUI workflow"""
        if not isinstance(data, dict):
            return False
        
        # Look for ComfyUI indicators
        has_numeric_keys = any(k.isdigit() for k in data.keys())
        has_nodes = "nodes" in data
        has_workflow_structure = any(isinstance(v, dict) and "type" in v for v in data.values())
        
        return has_numeric_keys or has_nodes or has_workflow_structure
    
    def _extract_comfyui_nodes(self, data: Dict[str, Any]) -> List[str]:
        """Extract node types from ComfyUI workflow"""
        nodes = []
        
        # Check different possible structures
        if "nodes" in data and isinstance(data["nodes"], dict):
            for node_data in data["nodes"].values():
                if isinstance(node_data, dict) and "type" in node_data:
                    nodes.append(node_data["type"])
        else:
            # Check if data itself contains nodes
            for value in data.values():
                if isinstance(value, dict) and "type" in value:
                    nodes.append(value["type"])
        
        return nodes
    
    def _filter_unknown_nodes(self, nodes: List[str]) -> List[str]:
        """Filter out commonly known ComfyUI nodes"""
        common_nodes = {
            "KSampler", "KSamplerAdvanced", "CLIPTextEncode", "VAEDecode", 
            "CheckpointLoaderSimple", "LoraLoader", "EmptyLatentImage"
        }
        return [n for n in nodes if n not in common_nodes]
    
    def _count_known_tools(self, analyzed_files: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count occurrences of known tools"""
        # This would need integration with your existing detection system
        # For now, return empty dict
        return {}
    
    def print_report(self):
        """Print a nice report of the analysis"""
        if not self.analysis_results:
            print("❌ No analysis results to report. Run scan_folder() first.")
            return
        
        results = self.analysis_results
        print(f"\n📊 DISCOVERY REPORT")
        print(f"=" * 50)
        print(f"📁 Folder: {results['folder_path']}")
        print(f"🖼️ Image files: {results['image_files']}")
        print(f"📄 JSON files: {results['json_files']}")
        print(f"📊 Total files: {results['total_files']}")
        print(f"🔍 Analyzed: {results['analyzed_files']}")
        print(f"❓ Unknown patterns: {results['unknown_patterns']}")
        print(f"💡 Suggestions: {len(results['suggestions'])}")
        
        if results['suggestions']:
            print(f"\n🎯 NEW TOOL SUGGESTIONS:")
            print(f"=" * 30)
            
            for i, suggestion in enumerate(results['suggestions'], 1):
                print(f"\n{i}. {suggestion['suggested_tool_name']}")
                print(f"   Confidence: {suggestion['confidence']} files")
                print(f"   Sample files: {', '.join(suggestion['sample_files'])}")
                print(f"   \n   Suggested rules:")
                print(f"   {'-' * 20}")
                print(suggestion['suggested_rules'])


def main():
    """Main function for interactive use"""
    print("🔍 Smart Tool Discoverer")
    print("=" * 30)
    
    # Get folder from user
    folder_path = input("📁 Enter folder path to scan: ").strip()
    if not folder_path:
        folder_path = "."  # Current directory
    
    # Create discoverer and scan
    discoverer = ToolDiscoverer()
    results = discoverer.scan_folder(folder_path)
    
    # Print report
    discoverer.print_report()
    
    # Ask if user wants to save suggestions
    if results.get('suggestions'):
        save = input("\n💾 Save rule suggestions to file? (y/n): ").strip().lower()
        if save == 'y':
            output_file = "discovered_rules.toml"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Auto-discovered tool rules\n")
                f.write("# Review and add to your main rules.toml as needed\n\n")
                for suggestion in results['suggestions']:
                    f.write(suggestion['suggested_rules'])
                    f.write("\n\n")
            print(f"✅ Saved to {output_file}")


if __name__ == "__main__":
    main()
