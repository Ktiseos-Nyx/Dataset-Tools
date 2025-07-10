#!/usr/bin/env python3
"""
Test script for enhanced theme manager integration.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings

# Test basic import
try:
    from dataset_tools.ui.enhanced_theme_manager import EnhancedThemeManager
    print("✓ Enhanced theme manager imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

def test_enhanced_themes():
    """Test the enhanced theme system."""
    
    # Create minimal QApplication for testing
    app = QApplication(sys.argv)
    
    # Create a dummy main window for testing
    from PyQt6.QtWidgets import QMainWindow
    main_window = QMainWindow()
    
    # Create settings
    settings = QSettings("TestOrg", "TestApp")
    
    # Create enhanced theme manager
    print("\nCreating enhanced theme manager...")
    theme_manager = EnhancedThemeManager(main_window, settings)
    
    # Print theme report
    print("\nTheme system report:")
    theme_manager.print_theme_report()
    
    # Test theme switching
    available_themes = theme_manager.get_available_themes()
    print(f"\nTesting theme switching with {sum(len(themes) for themes in available_themes.values())} available themes...")
    
    test_themes = []
    
    # Test a few themes from each category
    for category, themes in available_themes.items():
        if themes:
            test_theme = f"{category}:{themes[0]}"
            test_themes.append(test_theme)
    
    for theme_id in test_themes[:3]:  # Test first 3 themes
        print(f"Testing theme: {theme_id}")
        success = theme_manager.apply_theme(theme_id)
        status = "✓" if success else "✗"
        print(f"  {status} Theme application {'succeeded' if success else 'failed'}")
    
    print("\nEnhanced theme integration test complete!")
    return True

if __name__ == "__main__":
    try:
        test_enhanced_themes()
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)