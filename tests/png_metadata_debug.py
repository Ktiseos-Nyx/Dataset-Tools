# PNG Metadata Debug Script
# Let's see what's REALLY inside these PNG files!

import json
from PIL import Image
from pathlib import Path

def debug_png_metadata(image_path: str):
    """
    Deep dive into PNG metadata to see what your JSON parsers are missing!
    Like using a Garlean detection device to scan for Zodiark's influence! 🔍⚔️
    """
    print(f"🔍 DEBUGGING PNG METADATA FOR: {Path(image_path).name}")
    print("=" * 80)
    
    try:
        # Open the image and get ALL the metadata
        with Image.open(image_path) as img:
            print(f"📷 Image Info: {img.format}, {img.size[0]}x{img.size[1]}")
            print()
            
            # Check what's in the info dictionary
            print("📋 Available PNG Chunks:")
            if hasattr(img, 'info') and img.info:
                for key, value in img.info.items():
                    # Show the key and a preview of the value
                    if isinstance(value, str):
                        preview = value[:100] + "..." if len(value) > 100 else value
                        print(f"  ✅ '{key}': {type(value).__name__} (length: {len(value)})")
                        print(f"      Preview: {repr(preview)}")
                    else:
                        print(f"  ✅ '{key}': {type(value).__name__} = {value}")
                print()
            else:
                print("  ❌ No PNG chunks found in img.info")
                print()
            
            # Specifically check for ComfyUI chunks
            print("🎯 ComfyUI-Specific Chunk Analysis:")
            
            # Check 'workflow' chunk
            if 'workflow' in img.info:
                workflow_data = img.info['workflow']
                print(f"  ✅ 'workflow' chunk found: {type(workflow_data)} (length: {len(workflow_data)})")
                
                # Try to parse as JSON
                try:
                    workflow_json = json.loads(workflow_data)
                    print(f"  ✅ 'workflow' is valid JSON with {len(workflow_json)} nodes")
                    
                    # Show some sample nodes
                    sample_nodes = list(workflow_json.keys())[:3]
                    for node_id in sample_nodes:
                        node = workflow_json[node_id]
                        class_type = node.get('class_type', 'Unknown')
                        print(f"    📦 Node {node_id}: {class_type}")
                        
                except json.JSONDecodeError as e:
                    print(f"  ❌ 'workflow' chunk is not valid JSON: {e}")
                    print(f"      Raw content preview: {repr(workflow_data[:200])}")
            else:
                print("  ❌ 'workflow' chunk not found")
            
            # Check 'prompt' chunk  
            if 'prompt' in img.info:
                prompt_data = img.info['prompt']
                print(f"  ✅ 'prompt' chunk found: {type(prompt_data)} (length: {len(prompt_data)})")
                
                # Try to parse as JSON
                try:
                    prompt_json = json.loads(prompt_data)
                    print(f"  ✅ 'prompt' is valid JSON with {len(prompt_json)} nodes")
                    
                    # Show some sample nodes
                    sample_nodes = list(prompt_json.keys())[:3]
                    for node_id in sample_nodes:
                        node = prompt_json[node_id]
                        class_type = node.get('class_type', 'Unknown')
                        print(f"    📦 Node {node_id}: {class_type}")
                        
                except json.JSONDecodeError as e:
                    print(f"  ❌ 'prompt' chunk is not valid JSON: {e}")
                    print(f"      Raw content preview: {repr(prompt_data[:200])}")
            else:
                print("  ❌ 'prompt' chunk not found")
            
            print()
            
            # Check for other common chunks
            print("🔍 Other Metadata Chunks:")
            other_chunks = [key for key in img.info.keys() if key not in ['workflow', 'prompt']]
            if other_chunks:
                for key in other_chunks:
                    value = img.info[key]
                    print(f"  📝 '{key}': {type(value).__name__}")
                    if isinstance(value, str) and len(value) > 50:
                        print(f"      (length: {len(value)}, preview: {repr(value[:50])}...)")
            else:
                print("  📝 No other chunks found")
                
    except Exception as e:
        print(f"💥 ERROR reading PNG metadata: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)
    print()


def check_json_parser_detection_logic(image_path: str):
    """
    Test what your JSON parser detection rules would see.
    """
    print(f"🎯 TESTING JSON PARSER DETECTION FOR: {Path(image_path).name}")
    print("=" * 80)
    
    try:
        with Image.open(image_path) as img:
            info = img.info
            
            # Test Rule 1: Must have ComfyUI JSON structure
            print("📋 Rule 1: Has ComfyUI JSON structure")
            
            for chunk_name in ['workflow', 'prompt']:
                if chunk_name in info:
                    try:
                        json_data = json.loads(info[chunk_name])
                        print(f"  ✅ '{chunk_name}' chunk has valid JSON")
                        
                        # Test Rule 2: JSON must have numeric string keys
                        numeric_keys = [k for k in json_data.keys() if k.isdigit()]
                        if numeric_keys:
                            print(f"  ✅ '{chunk_name}' has numeric string keys: {numeric_keys[:5]}...")
                        else:
                            print(f"  ❌ '{chunk_name}' has no numeric string keys")
                        
                        # Test Rule 3: Must contain recognizable ComfyUI nodes
                        node_types = []
                        for node_id, node_data in json_data.items():
                            if isinstance(node_data, dict) and 'class_type' in node_data:
                                node_types.append(node_data['class_type'])
                        
                        print(f"  📦 Node types found: {set(node_types)}")
                        
                        # Check against your detection list
                        detection_types = [
                            "KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced",
                            "CLIPTextEncode", "CheckpointLoaderSimple", 
                            "EmptyLatentImage", "VAEDecode", "SaveImage", "PreviewImage"
                        ]
                        
                        matches = [t for t in node_types if t in detection_types]
                        if matches:
                            print(f"  ✅ Matching detection types: {matches}")
                        else:
                            print(f"  ❌ No matching detection types found!")
                            print(f"      Your detection list: {detection_types}")
                            print(f"      Actual node types: {list(set(node_types))}")
                        
                    except json.JSONDecodeError:
                        print(f"  ❌ '{chunk_name}' chunk is not valid JSON")
                else:
                    print(f"  ❌ '{chunk_name}' chunk not found")
            
            # Test Rule 4: Not a Civitai format
            has_civitai = False
            for chunk_name in ['workflow', 'prompt']:
                if chunk_name in info:
                    try:
                        json_data = json.loads(info[chunk_name])
                        if any('extra' in str(node) and 'extraMetadata' in str(node) for node in json_data.values()):
                            has_civitai = True
                            break
                    except:
                        pass
            
            print(f"📋 Rule 4: Not Civitai format")
            if has_civitai:
                print("  ❌ Appears to be Civitai format - would be excluded")
            else:
                print("  ✅ Not Civitai format - would pass")
            
    except Exception as e:
        print(f"💥 ERROR in detection logic test: {e}")
    
    print("=" * 80)
    print()


def main():
    """Scan ALL images in the metadata samples folder."""
    import os
    
    # Scan the entire folder
    folder_path = "/Users/duskfall/Downloads/Metadata Samples"
    
    if not Path(folder_path).exists():
        print(f"⚠️ Folder not found: {folder_path}")
        return
    
    # Get all image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
    image_files = []
    
    for file_path in Path(folder_path).iterdir():
        if file_path.suffix.lower() in image_extensions:
            image_files.append(file_path)
    
    print(f"🔍 SCANNING {len(image_files)} IMAGES IN: {folder_path}")
    print("=" * 100)
    print()
    
    # Statistics tracking
    stats = {
        'total_files': len(image_files),
        'png_files': 0,
        'jpeg_files': 0,
        'other_files': 0,
        'has_workflow_chunk': 0,
        'has_prompt_chunk': 0,
        'has_exif_data': 0,
        'has_comfyui_json': 0,
        'detection_failures': [],
        'file_types': {},
        'node_types_found': set()
    }
    
    # Quick scan mode - just the essentials
    for i, file_path in enumerate(image_files, 1):
        print(f"📁 {i:3d}/{len(image_files)}: {file_path.name}")
        
        try:
            with Image.open(file_path) as img:
                # Track file types
                file_ext = file_path.suffix.lower()
                stats['file_types'][file_ext] = stats['file_types'].get(file_ext, 0) + 1
                
                if file_ext == '.png':
                    stats['png_files'] += 1
                elif file_ext in ['.jpg', '.jpeg']:
                    stats['jpeg_files'] += 1
                else:
                    stats['other_files'] += 1
                
                # Check for metadata
                info = img.info if hasattr(img, 'info') else {}
                
                has_workflow = 'workflow' in info
                has_prompt = 'prompt' in info
                has_exif = 'exif' in info
                
                if has_workflow:
                    stats['has_workflow_chunk'] += 1
                if has_prompt:
                    stats['has_prompt_chunk'] += 1
                if has_exif:
                    stats['has_exif_data'] += 1
                
                # Quick ComfyUI detection
                found_comfyui = False
                comfyui_source = None
                
                # Check PNG chunks
                for chunk_name in ['workflow', 'prompt']:
                    if chunk_name in info:
                        try:
                            json_data = json.loads(info[chunk_name])
                            if isinstance(json_data, dict) and any(
                                isinstance(v, dict) and 'class_type' in v 
                                for v in json_data.values()
                            ):
                                found_comfyui = True
                                comfyui_source = f"PNG:{chunk_name}"
                                
                                # Collect node types
                                for node_data in json_data.values():
                                    if isinstance(node_data, dict) and 'class_type' in node_data:
                                        stats['node_types_found'].add(node_data['class_type'])
                                break
                        except:
                            pass
                
                # Check EXIF for JPEG files (simplified check)
                if not found_comfyui and 'exif' in info and file_ext in ['.jpg', '.jpeg']:
                    # This is a simplified check - vendored parser does more complex EXIF parsing
                    comfyui_source = "EXIF:UserComment(?)"
                
                if found_comfyui:
                    stats['has_comfyui_json'] += 1
                    print(f"    ✅ ComfyUI data found in {comfyui_source}")
                else:
                    print(f"    ❌ No ComfyUI data detected")
                    stats['detection_failures'].append(file_path.name)
        
        except Exception as e:
            print(f"    💥 ERROR: {e}")
            stats['detection_failures'].append(f"{file_path.name} (ERROR)")
    
    print()
    print("📊 ANALYSIS SUMMARY")
    print("=" * 100)
    print(f"📁 Total files scanned: {stats['total_files']}")
    print(f"🖼️  File types: {dict(stats['file_types'])}")
    print()
    print(f"📦 PNG files: {stats['png_files']}")
    print(f"   - With 'workflow' chunk: {stats['has_workflow_chunk']}")
    print(f"   - With 'prompt' chunk: {stats['has_prompt_chunk']}")
    print()
    print(f"📷 JPEG files: {stats['jpeg_files']}")
    print(f"   - With EXIF data: {stats['has_exif_data']}")
    print()
    print(f"🎯 ComfyUI detection results:")
    print(f"   - Files with ComfyUI JSON: {stats['has_comfyui_json']}")
    print(f"   - Detection failures: {len(stats['detection_failures'])}")
    print()
    
    if stats['node_types_found']:
        print(f"🔧 Node types discovered ({len(stats['node_types_found'])} unique):")
        node_list = sorted(list(stats['node_types_found']))
        for i in range(0, len(node_list), 4):  # Print 4 per line
            line_nodes = node_list[i:i+4]
            print(f"   {', '.join(line_nodes)}")
        print()
    
    if stats['detection_failures']:
        print(f"❌ Files that failed ComfyUI detection ({len(stats['detection_failures'])}):")
        for failure in stats['detection_failures'][:10]:  # Show first 10
            print(f"   - {failure}")
        if len(stats['detection_failures']) > 10:
            print(f"   ... and {len(stats['detection_failures']) - 10} more")
        print()
    
    # Analysis recommendations
    print("💡 RECOMMENDATIONS FOR JSON PARSER FIXES:")
    print("=" * 60)
    
    if stats['jpeg_files'] > 0:
        print(f"🔧 {stats['jpeg_files']} JPEG files need EXIF UserComment support in detection rules")
    
    if stats['node_types_found']:
        current_detection = {
            "KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced",
            "CLIPTextEncode", "CheckpointLoaderSimple", 
            "EmptyLatentImage", "VAEDecode", "SaveImage", "PreviewImage"
        }
        missing_types = stats['node_types_found'] - current_detection
        if missing_types:
            print(f"🔧 Add these node types to detection rules: {sorted(missing_types)}")
    
    print("\n🎉 Mass forensic analysis complete!")
    print(f"📋 Ready to overthrow Zodiark with data from {stats['total_files']} files! ⚔️")


if __name__ == "__main__":
    main()
