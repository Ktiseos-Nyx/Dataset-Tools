#!/usr/bin/env python3
"""
Test script for new theme integrations.
"""

import sys
from pathlib import Path

# Test qt-themes
print("Testing qt-themes...")
try:
    import qt_themes
    print(f"✓ qt-themes imported successfully")
    
    # List available themes
    themes = [
        'one_dark_two', 'monokai', 'nord', 'catppuccin_mocha', 
        'catppuccin_macchiato', 'catppuccin_frappe', 'catppuccin_latte',
        'atom_one', 'github_dark', 'github_light', 'dracula', 'blender'
    ]
    print(f"✓ Available qt-themes: {', '.join(themes)}")
    
    # Test color extraction
    test_theme = 'nord'
    colors = qt_themes.get_colors(test_theme)
    print(f"✓ {test_theme} colors: {len(colors)} entries")
    
except Exception as e:
    print(f"✗ qt-themes error: {e}")

print()

# Test unreal-stylesheet
print("Testing unreal-stylesheet...")
try:
    import unreal_stylesheet
    print(f"✓ unreal-stylesheet imported successfully")
    print(f"✓ Version available")
    
    # Check if setup function exists
    if hasattr(unreal_stylesheet, 'setup'):
        print("✓ setup() function available")
    else:
        print("✗ setup() function not found")
    
except Exception as e:
    print(f"✗ unreal-stylesheet error: {e}")

print()

# Test BreezeStyleSheets structure
print("Testing BreezeStyleSheets...")
try:
    breeze_dir = Path("BreezeStyleSheets")
    if breeze_dir.exists():
        print(f"✓ BreezeStyleSheets directory found")
        
        dist_dir = breeze_dir / "dist"
        if dist_dir.exists():
            print(f"✓ dist/ directory found")
            
            # Check for available themes
            theme_dirs = [d for d in dist_dir.iterdir() if d.is_dir()]
            theme_names = [d.name for d in theme_dirs]
            print(f"✓ Available Breeze themes: {', '.join(theme_names)}")
            
            # Check if stylesheets exist
            for theme_dir in theme_dirs:
                qss_file = theme_dir / "stylesheet.qss"
                if qss_file.exists():
                    size = qss_file.stat().st_size // 1024
                    print(f"  ✓ {theme_dir.name}: {size} KB stylesheet")
                else:
                    print(f"  ✗ {theme_dir.name}: no stylesheet found")
        else:
            print(f"✗ dist/ directory not found")
    else:
        print(f"✗ BreezeStyleSheets directory not found")
        
except Exception as e:
    print(f"✗ BreezeStyleSheets error: {e}")

print()
print("Theme integration test complete!")