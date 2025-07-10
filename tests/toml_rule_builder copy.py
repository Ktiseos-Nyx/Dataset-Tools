# Helper to make TOML rule creation less painful!

from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class RuleBuilder:
    """Builder to create TOML rules more easily - like a quest template!"""
    
    def __init__(self, parser_name: str):
        self.parser_name = parser_name
        self.rules = []
    
    def add_chunk_exists_rule(self, chunk_name: str, comment: str = "") -> 'RuleBuilder':
        """Add a rule checking if a PNG chunk exists"""
        rule = {
            "comment": comment or f"Check if {chunk_name} chunk exists",
            "source_type": "png_chunk",
            "source_key": chunk_name,
            "operator": "exists"
        }
        self.rules.append(rule)
        return self
    
    def add_json_keys_rule(self, expected_keys: List[str], 
                          source_chunks: List[str] = None,
                          match_type: str = "any",
                          comment: str = "") -> 'RuleBuilder':
        """Add a rule checking for specific JSON keys"""
        if source_chunks is None:
            source_chunks = ["parameters", "Comment"]
            
        rule = {
            "comment": comment or f"Check for {match_type} of: {expected_keys}",
            "source_type": "json_from_usercomment_or_png_chunk",
            "chunk_source_key_options_for_png": source_chunks,
            "operator": f"json_contains_{match_type}_key",
            "expected_keys": expected_keys
        }
        self.rules.append(rule)
        return self
    
    def add_comfyui_workflow_rule(self, node_types: List[str], comment: str = "") -> 'RuleBuilder':
        """Add a rule for ComfyUI workflow detection"""
        # First rule: Check for workflow/prompt chunks
        workflow_rule = {
            "comment": "Must have ComfyUI workflow or prompt chunk",
            "condition": "OR",
            "rules": [
                {"source_type": "pil_info_key", "source_key": "workflow", "operator": "is_valid_json"},
                {"source_type": "pil_info_key", "source_key": "prompt", "operator": "is_valid_json"}
            ]
        }
        self.rules.append(workflow_rule)
        
        # Second rule: Check for specific node types
        node_rule = {
            "comment": comment or f"Must contain nodes: {node_types}",
            "source_type": "pil_info_key_json_path_query",
            "source_key_options": ["workflow", "prompt"],
            "json_query_type": "has_any_node_class_type",
            "class_types_to_check": node_types,
            "operator": "is_true"
        }
        self.rules.append(node_rule)
        return self
    
    def add_a1111_style_rule(self, required_patterns: List[str], comment: str = "") -> 'RuleBuilder':
        """Add rules for A1111-style text detection"""
        # Check for data source
        source_rule = {
            "comment": "EITHER PNG parameters OR EXIF UserComment must exist",
            "condition": "OR", 
            "rules": [
                {"source_type": "pil_info_key", "source_key": "parameters", "operator": "exists"},
                {"source_type": "exif_user_comment", "operator": "exists"}
            ]
        }
        self.rules.append(source_rule)
        
        # Check for A1111 patterns
        pattern_rule = {
            "comment": comment or f"Must contain patterns: {required_patterns}",
            "source_type": "a1111_parameter_string_content",
            "operator": "regex_match_all",
            "regex_patterns": required_patterns
        }
        self.rules.append(pattern_rule)
        return self
    
    def add_custom_rule(self, rule_dict: Dict[str, Any]) -> 'RuleBuilder':
        """Add a custom rule directly"""
        self.rules.append(rule_dict)
        return self
    
    def to_toml_section(self) -> str:
        """Generate the TOML section for these rules"""
        toml_lines = [f"# --- Rules for {self.parser_name} ---"]
        
        for i, rule in enumerate(self.rules):
            toml_lines.append(f"[[parsers.{self.parser_name}.detection_rules]]")
            toml_lines.extend(self._dict_to_toml_lines(rule, indent="  "))
            if i < len(self.rules) - 1:  # Add blank line between rules
                toml_lines.append("")
        
        return "\n".join(toml_lines)
    
    def _dict_to_toml_lines(self, d: Dict[str, Any], indent: str = "") -> List[str]:
        """Convert dict to TOML lines"""
        lines = []
        for key, value in d.items():
            if isinstance(value, str):
                lines.append(f'{indent}{key} = "{value}"')
            elif isinstance(value, list):
                if all(isinstance(x, str) for x in value):
                    # String array
                    formatted_items = [f'"{item}"' for item in value]
                    lines.append(f'{indent}{key} = [{", ".join(formatted_items)}]')
                elif all(isinstance(x, dict) for x in value):
                    # Array of objects
                    lines.append(f'{indent}{key} = [')
                    for i, item in enumerate(value):
                        lines.append(f'{indent}  {{')
                        lines.extend(self._dict_to_toml_lines(item, indent + "    "))
                        lines.append(f'{indent}  }}{"," if i < len(value) - 1 else ""}')
                    lines.append(f'{indent}]')
            elif isinstance(value, bool):
                lines.append(f'{indent}{key} = {str(value).lower()}')
            elif isinstance(value, (int, float)):
                lines.append(f'{indent}{key} = {value}')
            else:
                lines.append(f'{indent}{key} = "{str(value)}"')
        return lines

# Usage examples - much easier than writing TOML by hand!

def create_new_tool_rules():
    """Examples of how to use the rule builder"""
    
    # Example 1: Simple JSON-based tool
    simple_tool = (RuleBuilder("NewSimpleTool")
                  .add_chunk_exists_rule("metadata", "Tool stores data in metadata chunk")
                  .add_json_keys_rule(["tool_name", "version"], comment="Check for tool signature"))
    
    print("=== Simple Tool Rules ===")
    print(simple_tool.to_toml_section())
    print("\n")
    
    # Example 2: ComfyUI variant
    comfy_variant = (RuleBuilder("NewComfyUIVariant")
                    .add_comfyui_workflow_rule(["SpecialSampler", "CustomNode"], 
                                             "Must have special nodes"))
    
    print("=== ComfyUI Variant Rules ===")
    print(comfy_variant.to_toml_section())
    print("\n")
    
    # Example 3: A1111-style variant
    a1111_variant = (RuleBuilder("NewA1111Variant")
                    .add_a1111_style_rule(["Steps:", "NewSampler:", "SpecialCFG:"])
                    .add_custom_rule({
                        "comment": "Must contain tool-specific marker",
                        "source_type": "a1111_parameter_string_content", 
                        "operator": "regex_match_any",
                        "regex_patterns": ["NewTool:", "SpecialFeature:"]
                    }))
    
    print("=== A1111 Variant Rules ===")
    print(a1111_variant.to_toml_section())
    print("\n")

# Quick templates for common tool types
class QuickTemplates:
    """Pre-built templates for common AI tool types"""
    
    @staticmethod
    def json_metadata_tool(name: str, signature_keys: List[str], chunk_name: str = "parameters"):
        """Template for tools that store JSON in PNG chunks"""
        return (RuleBuilder(name)
               .add_chunk_exists_rule(chunk_name)
               .add_json_keys_rule(signature_keys, [chunk_name]))
    
    @staticmethod
    def a1111_text_variant(name: str, required_patterns: List[str], special_patterns: List[str] = None):
        """Template for A1111-style text format variants"""
        builder = RuleBuilder(name).add_a1111_style_rule(required_patterns)
        
        if special_patterns:
            builder.add_custom_rule({
                "comment": f"Must contain {name}-specific patterns",
                "source_type": "a1111_parameter_string_content",
                "operator": "regex_match_any", 
                "regex_patterns": special_patterns
            })
        
        return builder
    
    @staticmethod 
    def comfyui_workflow_variant(name: str, required_nodes: List[str]):
        """Template for ComfyUI workflow variants"""
        return RuleBuilder(name).add_comfyui_workflow_rule(required_nodes)

# Even easier usage!
def quick_add_examples():
    """Super quick ways to add new tools"""
    
    # Add a new JSON-based tool in 1 line
    foobar_tool = QuickTemplates.json_metadata_tool(
        "FoobarAI", 
        ["foobar_version", "foobar_model", "foobar_settings"]
    )
    
    # Add a new A1111 variant in 1 line  
    mega_a1111 = QuickTemplates.a1111_text_variant(
        "MegaA1111",
        ["Steps:", "Sampler:", "CFG scale:"],  # Standard A1111
        ["MegaBoost:", "UltraQuality:"]         # Tool-specific
    )
    
    # Add a ComfyUI variant in 1 line
    flux_comfy = QuickTemplates.comfyui_workflow_variant(
        "FluxComfyUI",
        ["FluxSampler", "FluxLoader", "FluxVAE"]
    )
    
    print("=== Quick Template Examples ===")
    print(foobar_tool.to_toml_section())
    print("\n" + "="*50 + "\n")
    print(mega_a1111.to_toml_section()) 
    print("\n" + "="*50 + "\n")
    print(flux_comfy.to_toml_section())

if __name__ == "__main__":
    create_new_tool_rules()
    print("="*60)
    quick_add_examples()
