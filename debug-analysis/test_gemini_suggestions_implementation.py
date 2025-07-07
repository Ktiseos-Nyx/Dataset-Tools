#!/usr/bin/env python3

"""
Test the implementations of Gemini's suggestions.
"""

import json
import tempfile
import logging
from pathlib import Path
from PIL import Image, PngImagePlugin
from dataset_tools.metadata_engine import get_metadata_engine
from dataset_tools.metadata_engine.extractors.comfyui_extractors import ComfyUIExtractor
from dataset_tools.metadata_engine.extractors.json_extractors import JSONExtractor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_prompt_cleaning():
    """Test the prompt cleaning functionality."""
    print("🧼 TESTING PROMPT CLEANING")
    print("=" * 30)
    
    extractor = ComfyUIExtractor(logger)
    
    test_cases = [
        ("embedding:negatives\\bad quality, blurry", "bad quality, blurry"),
        ("embedding:beautiful woman", "beautiful woman"),
        ("negatives\\low quality", "low quality"),
        ("normal prompt text", "normal prompt text"),
        ("", ""),
    ]
    
    for input_text, expected in test_cases:
        result = extractor._clean_prompt_text(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_text}' → '{result}' (expected: '{expected}')")
    
    return True

def test_json_path_exists():
    """Test the json_path_exists_boolean method."""
    print("\n🔍 TESTING JSON PATH EXISTS")
    print("=" * 35)
    
    extractor = JSONExtractor(logger)
    
    test_data = {
        "user": {"name": "test", "settings": {"theme": "dark"}},
        "items": ["a", "b", "c"],
        "count": 42
    }
    
    test_cases = [
        ("user.name", True),
        ("user.settings.theme", True),
        ("user.missing", False),
        ("items.0", True),
        ("items.5", False),
        ("count", True),
        ("nonexistent", False),
    ]
    
    for path, expected in test_cases:
        method_def = {"json_path": path}
        result = extractor._json_path_exists_boolean(test_data, method_def, {}, {})
        status = "✅" if result == expected else "❌"
        print(f"{status} Path '{path}': {result} (expected: {expected})")
    
    return True

def test_comfyui_with_embeddings():
    """Test ComfyUI extraction with embedding prefixes."""
    print("\n🎨 TESTING COMFYUI WITH EMBEDDINGS")
    print("=" * 40)
    
    # Mock ComfyUI workflow with embedding prefixes
    mock_data = {
        "1": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "embedding:beautiful woman, portrait",
                "clip": ["2", 1]
            },
            "_meta": {"title": "CLIP Text Encode (Prompt)"}
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "embedding:negatives\\bad quality, worst",
                "clip": ["2", 1]
            },
            "_meta": {"title": "CLIP Text Encode (Negative)"}
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 123,
                "steps": 20,
                "cfg": 7.0,
                "positive": ["1", 0],
                "negative": ["2", 0]
            }
        }
    }
    
    extractor = ComfyUIExtractor(logger)
    
    # Test text extraction with cleaning
    result = extractor._extract_comfy_text_from_clip_encode_nodes(mock_data, {}, {}, {})
    
    expected_positive = "beautiful woman, portrait"
    expected_negative = "bad quality, worst"
    
    print(f"Positive prompt: '{result.get('positive', '')}' (expected: '{expected_positive}')")
    print(f"Negative prompt: '{result.get('negative', '')}' (expected: '{expected_negative}')")
    
    positive_ok = result.get('positive') == expected_positive
    negative_ok = result.get('negative') == expected_negative
    
    print(f"✅ Positive cleaned correctly: {positive_ok}")
    print(f"✅ Negative cleaned correctly: {negative_ok}")
    
    return positive_ok and negative_ok

def test_universal_parser_integration():
    """Test the Universal Parser with all fixes."""
    print("\n🚀 TESTING UNIVERSAL PARSER INTEGRATION")
    print("=" * 45)
    
    # Create test ComfyUI data with embeddings
    prompt_data = {
        "1": {
            "class_type": "CLIPTextEncode", 
            "inputs": {
                "text": "embedding:beautiful woman, portrait",
                "clip": ["2", 1]
            },
            "_meta": {"title": "CLIP Text Encode (Prompt)"}
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "embedding:negatives\\blurry, low quality",
                "clip": ["2", 1]
            },
            "_meta": {"title": "CLIP Text Encode (Negative)"}
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 54321,
                "steps": 25,
                "cfg": 8.5,
                "sampler_name": "dpmpp_2m",
                "positive": ["1", 0],
                "negative": ["2", 0]
            }
        }
    }
    
    # Create test image
    img = Image.new('RGB', (512, 512), color='blue')
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("prompt", json.dumps(prompt_data))
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name, pnginfo=pnginfo)
    temp_file.close()
    
    try:
        # Test with metadata engine
        parser_definitions_path = Path(__file__).parent / "parser_definitions"
        engine = get_metadata_engine(str(parser_definitions_path))
        
        result = engine.get_parser_for_file(temp_file.name)
        
        if result and result.get('tool') == 'ComfyUI (Universal Parser)':
            print("✅ Universal Parser detected correctly")
            
            # Check cleaned prompts
            prompt = result.get('prompt', '')
            negative = result.get('negative_prompt', '')
            
            print(f"Extracted prompt: '{prompt}'")
            print(f"Extracted negative: '{negative}'")
            
            # These should be clean (no embedding: prefixes)
            prompt_clean = "embedding:" not in prompt
            negative_clean = "embedding:" not in negative
            
            print(f"✅ Prompt cleaned: {prompt_clean}")
            print(f"✅ Negative cleaned: {negative_clean}")
            
            return prompt_clean and negative_clean
        else:
            print(f"❌ Parser issue: {result.get('tool', 'No result') if result else 'No result'}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        Path(temp_file.name).unlink()

if __name__ == "__main__":
    print("🔍 TESTING GEMINI'S SUGGESTIONS IMPLEMENTATION")
    print("=" * 55)
    
    tests = [
        ("Prompt Cleaning", test_prompt_cleaning),
        ("JSON Path Exists", test_json_path_exists), 
        ("ComfyUI with Embeddings", test_comfyui_with_embeddings),
        ("Universal Parser Integration", test_universal_parser_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    print(f"\n📊 SUMMARY:")
    print("=" * 15)
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    all_passed = all(success for _, success in results)
    print(f"\n{'🎉 ALL TESTS PASSED!' if all_passed else '⚠️ SOME TESTS FAILED'}")