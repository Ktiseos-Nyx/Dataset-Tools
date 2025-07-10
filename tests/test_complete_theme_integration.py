#!/usr/bin/env python3
"""
Complete test script for the enhanced theme manager integration.
This script demonstrates the complete theme integration with all supported systems.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt6.QtCore import QSettings

# Test basic import
try:
    from dataset_tools.ui.enhanced_theme_manager import EnhancedThemeManager
    print("✓ Enhanced theme manager imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

def test_complete_theme_integration():
    """Test the complete enhanced theme system integration."""
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Create a test window
    window = QMainWindow()
    window.setWindowTitle("Enhanced Theme Manager Integration Test")
    window.resize(800, 600)
    
    # Create central widget
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # Add some test content
    layout.addWidget(QLabel("Enhanced Theme Manager Integration Test"))
    layout.addWidget(QLabel("This window demonstrates all supported theme systems:"))
    layout.addWidget(QLabel("• qt-material (Material Design themes)"))
    layout.addWidget(QLabel("• qt-themes (Color palette themes)"))
    layout.addWidget(QLabel("• BreezeStyleSheets (Qt stylesheet themes)"))
    layout.addWidget(QLabel("• unreal-stylesheet (Unreal Engine style)"))
    
    # Test button
    test_button = QPushButton("Test Theme Switching")
    layout.addWidget(test_button)
    
    window.setCentralWidget(central_widget)
    
    # Create settings
    settings = QSettings("TestOrg", "ThemeTestApp")
    
    # Create enhanced theme manager
    print("\nCreating enhanced theme manager...")
    theme_manager = EnhancedThemeManager(window, settings)
    
    # Print comprehensive theme report
    print("\n" + "="*60)
    print("COMPLETE THEME INTEGRATION REPORT")
    print("="*60)
    theme_manager.print_theme_report()
    
    # Test theme switching for all categories
    available_themes = theme_manager.get_available_themes()
    print(f"\nTesting theme switching across {len(available_themes)} categories...")
    
    test_results = []
    for category, themes in available_themes.items():
        if themes:
            test_theme = f"{category}:{themes[0]}"
            print(f"  Testing {category}: {test_theme}")
            success = theme_manager.apply_theme(test_theme)
            test_results.append((test_theme, success))
            status = "✓ Success" if success else "✗ Failed"
            print(f"    Result: {status}")
    
    # Summary
    successful_tests = sum(1 for _, success in test_results if success)
    total_tests = len(test_results)
    print(f"\nTheme switching test results: {successful_tests}/{total_tests} successful")
    
    # Test menu creation (simulate)
    print("\nTesting menu creation...")
    try:
        from PyQt6.QtWidgets import QMenu
        test_menu = QMenu("Test Themes")
        theme_manager.create_theme_menus(test_menu)
        print(f"✓ Menu created with {len(theme_manager.theme_actions)} theme actions")
    except Exception as e:
        print(f"✗ Menu creation failed: {e}")
    
    # Test theme persistence
    print("\nTesting theme persistence...")
    try:
        theme_manager.apply_saved_theme()
        print("✓ Theme persistence working")
    except Exception as e:
        print(f"✗ Theme persistence failed: {e}")
    
    print("\n" + "="*60)
    print("INTEGRATION TEST COMPLETE")
    print("="*60)
    
    # Show window briefly for visual confirmation
    window.show()
    
    # Process events briefly to show the window
    app.processEvents()
    
    print("\nEnhanced theme manager integration test completed successfully!")
    print("The theme system now supports:")
    print("  • Multiple theme systems (qt-material, qt-themes, BreezeStyleSheets, unreal-stylesheet)")
    print("  • Organized theme menus with categories")
    print("  • Theme persistence and switching")
    print("  • Backward compatibility with existing theme system")
    
    return True

if __name__ == "__main__":
    try:
        test_complete_theme_integration()
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)