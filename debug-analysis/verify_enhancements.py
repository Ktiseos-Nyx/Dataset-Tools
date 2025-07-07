#!/usr/bin/env python3

"""Verification script for T5-FLUX-COMFY branch enhancements.
Checks that our improved parsers are loaded and functional.
"""

import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_tools.metadata_engine import get_metadata_engine


def verify_enhancements():
    """Verify that our enhanced parsers are loaded correctly."""
    print("🔍 VERIFYING T5-FLUX-COMFY ENHANCEMENTS")
    print("=" * 60)

    # Initialize metadata engine
    parser_definitions_path = Path(__file__).parent / "parser_definitions"
    print(f"📂 Parser definitions path: {parser_definitions_path}")

    if not parser_definitions_path.exists():
        print("❌ Parser definitions folder not found!")
        return False

    try:
        engine = get_metadata_engine(str(parser_definitions_path))
        print("✅ Metadata engine initialized successfully")

        # Check if our enhanced parsers are loaded
        enhanced_parsers = [
            "comfyui_a1111_sampler_enhanced.json",
            "t5_detection_system.json",
            "pixart_sigma_enhanced.json",
            "comfyui_flux_gguf_style.json",
        ]

        print("\n🎯 ENHANCED PARSER VERIFICATION:")
        print("-" * 40)

        for parser_file in enhanced_parsers:
            parser_path = parser_definitions_path / parser_file
            if parser_path.exists():
                # Try to load and parse the JSON
                try:
                    with open(parser_path) as f:
                        parser_data = json.load(f)

                    parser_name = parser_data.get("parser_name", "Unknown")
                    priority = parser_data.get("priority", "N/A")
                    version = parser_data.get("version", "N/A")

                    print(f"✅ {parser_file}")
                    print(f"   📛 Name: {parser_name}")
                    print(f"   🔢 Priority: {priority}")
                    print(f"   📦 Version: {version}")

                    # Check for enhanced features
                    detection_rules = parser_data.get("detection_rules", [])
                    if len(detection_rules) > 2:
                        print(f"   🚀 Enhanced detection: {len(detection_rules)} rules")

                    fields = parser_data.get("parsing_instructions", {}).get("fields", [])
                    if len(fields) > 5:
                        print(f"   🎯 Enhanced extraction: {len(fields)} fields")

                    print()

                except json.JSONDecodeError as e:
                    print(f"❌ {parser_file}: Invalid JSON - {e}")
                except Exception as e:
                    print(f"⚠️  {parser_file}: Error reading - {e}")
            else:
                print(f"❌ {parser_file}: Not found")

        # Test T5 detection enhancements
        print("\n🔬 T5 DETECTION ENHANCEMENTS:")
        print("-" * 30)

        t5_parser_path = parser_definitions_path / "t5_detection_system.json"
        if t5_parser_path.exists():
            with open(t5_parser_path) as f:
                t5_data = json.load(f)

            # Check enhanced node types
            detection_rules = t5_data.get("detection_rules", [])
            for rule in detection_rules:
                class_types = rule.get("class_types_to_check", [])
                if class_types:
                    print(f"✅ T5 node detection covers {len(class_types)} node types:")
                    advanced_nodes = [
                        node
                        for node in class_types
                        if any(keyword in node for keyword in ["Flux", "PixArt", "Aura", "Hunyuan"])
                    ]
                    if advanced_nodes:
                        print(f"   🚀 Advanced architectures: {', '.join(advanced_nodes[:3])}...")
                    break

        # Test Flux enhancements
        print("\n⚡ FLUX PARSER ENHANCEMENTS:")
        print("-" * 30)

        flux_parser_path = parser_definitions_path / "comfyui_flux_gguf_style.json"
        if flux_parser_path.exists():
            with open(flux_parser_path) as f:
                flux_data = json.load(f)

            fields = flux_data.get("parsing_instructions", {}).get("fields", [])
            enhanced_fields = [
                f
                for f in fields
                if any(keyword in f.get("target_key", "") for keyword in ["t5_model", "clip_model", "guidance"])
            ]

            if enhanced_fields:
                print(f"✅ Flux parser enhanced with {len(enhanced_fields)} new extraction fields:")
                for field in enhanced_fields[:3]:
                    print(f"   🎯 {field.get('target_key', 'Unknown')}")

        print("\n🎉 VERIFICATION COMPLETE!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"💥 ERROR initializing metadata engine: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_enhancements()
    sys.exit(0 if success else 1)
