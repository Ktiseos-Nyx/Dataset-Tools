#!/usr/bin/env python3
"""Test the new advanced ComfyUI parser with real images"""

import json
import sys
from pathlib import Path

# Add the project to the path
sys.path.insert(0, str(Path(__file__).parent))

from dataset_tools.metadata_engine import MetadataEngine
from dataset_tools.logger import get_logger

def test_advanced_parser():
    """Test the advanced ComfyUI parser on a real image"""
    
    # Initialize the metadata engine
    parser_definitions_path = Path(__file__).parent / "dataset_tools" / "parser_definitions"
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = get_logger("test_advanced")
    
    try:
        print(f"🔍 Looking for parser definitions in: {parser_definitions_path}")
        print(f"🔍 Directory exists: {parser_definitions_path.exists()}")
        
        engine = MetadataEngine(parser_definitions_path, logger)
        print(f"✅ MetadataEngine initialized with {len(engine.parser_definitions)} parser definitions")
        
        # Check if our new parser was loaded
        advanced_parser = None
        for parser in engine.parser_definitions:
            if parser.get("parser_name") == "ComfyUI Advanced Node Discovery":
                advanced_parser = parser
                break
        
        if advanced_parser:
            logger.info("✅ Advanced Node Discovery parser found!")
            logger.info(f"   Priority: {advanced_parser.get('priority')}")
            logger.info(f"   Fields: {len(advanced_parser.get('parsing_instructions', {}).get('fields', []))}")
        else:
            logger.error("❌ Advanced Node Discovery parser not found!")
            return
        
        # Test with sample image paths (you can modify these)
        test_images = [
            # Add paths to ComfyUI images here
            "/Users/duskfall/Downloads/Metadata Samples/ComfyUI_08965_.jpeg",
            "/Users/duskfall/Downloads/Metadata Samples/Comfyui_00491_.jpg"
        ]
        
        # If no test images provided, create a mock test
        if not test_images:
            logger.info("No test images provided. Creating mock workflow test...")
            
            # Test the extractors directly with sample data
            from dataset_tools.metadata_engine.extractors.comfyui_extractors import ComfyUIExtractor
            
            extractor = ComfyUIExtractor(logger)
            
            # Sample workflow with TIPO and complexity
            sample_workflow = {
                "prompt": {
                    "1": {"class_type": "CheckpointLoaderSimple"},
                    "2": {"class_type": "TIPO", "inputs": {
                        "tipo_model": "KBlueLeaf/TIPO-500M | TIPO-500M_epoch5-F16.gguf",
                        "temperature": 0.75,
                        "tag_length": "long"
                    }},
                    "3": {"class_type": "T5TextEncode"},
                    "4": {"class_type": "ProPostFilmGrain", "inputs": {
                        "grain_type": "Fine",
                        "grain_power": 0.5
                    }},
                    "5": {"class_type": "ImageUpscaleWithModel", "inputs": {
                        "model_name": "4x-UltraSharp.pth"
                    }},
                    "6": {"class_type": "ConditioningSetTimestepRange", "inputs": {
                        "start": 0.0,
                        "end": 0.85
                    }}
                }
            }
            
            # Test each extractor
            print("\n🧪 TESTING EXTRACTORS:")
            print("=" * 50)
            
            # Test TIPO detection
            tipo_result = extractor._detect_tipo_enhancement(sample_workflow, {}, {}, {})
            print(f"🎯 TIPO Detection: {json.dumps(tipo_result, indent=2)}")
            print()
            
            # Test complexity scoring
            complexity_result = extractor._calculate_workflow_complexity(sample_workflow, {}, {}, {})
            print(f"📊 Complexity Scoring: {json.dumps(complexity_result, indent=2)}")
            print()
            
            # Test upscaling detection
            upscaling_result = extractor._detect_advanced_upscaling(sample_workflow, {}, {}, {})
            print(f"🚀 Upscaling Detection: {json.dumps(upscaling_result, indent=2)}")
            print()
            
            # Test conditioning detection
            conditioning_result = extractor._detect_multi_stage_conditioning(sample_workflow, {}, {}, {})
            print(f"🎨 Multi-Stage Conditioning: {json.dumps(conditioning_result, indent=2)}")
            print()
            
            logger.info("✅ Mock test completed successfully!")
            return
        
        # Test with real images
        for image_path in test_images:
            if not Path(image_path).exists():
                logger.warning(f"⚠️  Image not found: {image_path}")
                continue
                
            logger.info(f"\n🔍 Testing image: {Path(image_path).name}")
            
            try:
                result = engine.get_parser_for_file(image_path)
                
                if result:
                    print(f"✅ Parser found: {result.get('tool', 'Unknown')}")
                    
                    # Show advanced metadata if available
                    advanced_fields = [
                        'tipo_enhancement', 'workflow_complexity', 'advanced_upscaling',
                        'multi_stage_conditioning', 'post_processing_effects',
                        'custom_node_ecosystems', 'workflow_techniques'
                    ]
                    
                    for field in advanced_fields:
                        if field in result:
                            print(f"  📊 {field}:")
                            if isinstance(result[field], dict):
                                for k, v in result[field].items():
                                    print(f"    {k}: {v}")
                            else:
                                print(f"    {result[field]}")
                    
                    # Show simple extracted fields
                    simple_fields = [
                        'has_tipo_enhancement', 'complexity_level', 'complexity_score',
                        'total_nodes', 'detected_techniques', 'custom_node_packs'
                    ]
                    
                    print(f"  📋 Quick Summary:")
                    for field in simple_fields:
                        if field in result:
                            print(f"    {field}: {result[field]}")
                            
                else:
                    print(f"❌ No parser found for: {Path(image_path).name}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {Path(image_path).name}: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize MetadataEngine: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Testing Advanced ComfyUI Node Discovery Parser")
    print("=" * 60)
    
    test_advanced_parser()
    
    print("\n✅ Test completed!")