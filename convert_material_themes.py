#!/usr/bin/env python3
"""
Convert qt-material XML themes to clean QSS stylesheets.

This script extracts color palettes from Dunderlab's qt-material themes
and generates clean QSS files without the template overhead.

Credits: Color schemes from https://github.com/dunderlab/qt-material
These converted themes are for internal use only - not for redistribution.
"""

import xml.etree.ElementTree as ET
from pathlib import Path


def parse_material_xml(xml_path: Path) -> dict:
    """Extract color palette from Material XML theme."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    colors = {}
    for color in root.findall('color'):
        name = color.get('name')
        value = color.text
        colors[name] = value

    return colors


def generate_qss(theme_name: str, colors: dict, is_dark: bool) -> str:
    """Generate clean QSS stylesheet from Material color palette."""

    # Determine if this is a dark or light theme
    mode = "dark" if is_dark else "light"

    # Extract colors with fallbacks
    primary = colors.get('primaryColor', '#448aff')
    primary_light = colors.get('primaryLightColor', '#83b9ff')
    secondary = colors.get('secondaryColor', '#232629')
    secondary_light = colors.get('secondaryLightColor', '#4f5b62')
    secondary_dark = colors.get('secondaryDarkColor', '#31363b')
    primary_text = colors.get('primaryTextColor', '#ffffff')
    secondary_text = colors.get('secondaryTextColor', '#ffffff')

    # Set background/foreground based on theme type
    if is_dark:
        bg_main = secondary
        bg_alt = secondary_light
        bg_dark = secondary_dark
        text_main = primary_text
        text_secondary = secondary_text
    else:
        bg_main = '#fafafa'
        bg_alt = '#ffffff'
        bg_dark = secondary_light
        text_main = '#212121'
        text_secondary = '#757575'

    qss = f"""/* MATERIAL {theme_name.upper().replace('_', ' ')} THEME */
/*
 * This stylesheet was converted from Dunderlab's qt-material themes.
 * Original: https://github.com/dunderlab/qt-material
 *
 * This theme is for internal use within Dataset-Tools only.
 * Not for redistribution outside this application.
 *
 * Color palette credits: Dunderlab (qt-material project)
 * QSS structure: Dataset-Tools custom (thumbnail-grid optimized)
 */

QMainWindow {{
    background: {bg_main};
    color: {text_main};
    border: none;
}}

QWidget {{
    background: {bg_main};
    color: {text_main};
    font-size: 13px;
}}

QPushButton {{
    background: {primary};
    border: 1px solid {primary_light};
    border-radius: 4px;
    padding: 8px 16px;
    color: {primary_text};
    font-weight: 500;
}}

QPushButton:hover {{
    background: {primary_light};
    border: 1px solid {primary};
}}

QPushButton:pressed {{
    background: {bg_dark};
}}

QPushButton:disabled {{
    background: {bg_dark};
    color: {text_secondary};
}}

QTextEdit, QPlainTextEdit {{
    background: {bg_alt};
    border: 1px solid {bg_dark};
    border-radius: 2px;
    padding: 8px;
    color: {text_main};
    selection-background-color: {primary};
    selection-color: {primary_text};
}}

QListWidget {{
    background: {bg_alt};
    border: 1px solid {bg_dark};
    border-radius: 2px;
    color: {text_main};
    /* Minimal padding for thumbnail grid performance */
    padding: 2px;
}}

QListWidget::item {{
    /* Clean item styling without heavy padding */
    padding: 4px;
}}

QListWidget::item:selected {{
    background: {primary};
    color: {primary_text};
}}

QListWidget::item:hover {{
    background: {primary_light};
    color: {primary_text};
}}

QTreeWidget {{
    background: {bg_alt};
    border: 1px solid {bg_dark};
    border-radius: 2px;
    color: {text_main};
    alternate-background-color: {bg_main};
}}

QTreeWidget::item:selected {{
    background: {primary};
    color: {primary_text};
}}

QTreeWidget::item:hover {{
    background: {primary_light};
}}

QLineEdit {{
    background: {bg_alt};
    border: 1px solid {bg_dark};
    border-radius: 2px;
    padding: 6px;
    color: {text_main};
    selection-background-color: {primary};
    selection-color: {primary_text};
}}

QLineEdit:focus {{
    border: 2px solid {primary};
}}

QComboBox {{
    background: {bg_alt};
    border: 1px solid {bg_dark};
    border-radius: 2px;
    padding: 6px;
    color: {text_main};
}}

QComboBox:hover {{
    border: 1px solid {primary_light};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {text_main};
    margin-right: 6px;
}}

QComboBox QAbstractItemView {{
    background: {bg_alt};
    border: 1px solid {bg_dark};
    selection-background-color: {primary};
    selection-color: {primary_text};
}}

QTabWidget::pane {{
    border: 1px solid {bg_dark};
    background: {bg_main};
}}

QTabBar::tab {{
    background: {bg_dark};
    border: 1px solid {bg_dark};
    padding: 8px 16px;
    color: {text_secondary};
}}

QTabBar::tab:selected {{
    background: {primary};
    color: {primary_text};
}}

QTabBar::tab:hover {{
    background: {primary_light};
    color: {primary_text};
}}

QScrollBar:vertical {{
    background: {bg_main};
    width: 12px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: {bg_dark};
    min-height: 20px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical:hover {{
    background: {primary_light};
}}

QScrollBar:horizontal {{
    background: {bg_main};
    height: 12px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: {bg_dark};
    min-width: 20px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {primary_light};
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    border: none;
    background: none;
}}

QMenuBar {{
    background: {bg_main};
    color: {text_main};
}}

QMenuBar::item:selected {{
    background: {primary};
    color: {primary_text};
}}

QMenu {{
    background: {bg_alt};
    border: 1px solid {bg_dark};
    color: {text_main};
}}

QMenu::item:selected {{
    background: {primary};
    color: {primary_text};
}}

QStatusBar {{
    background: {bg_dark};
    color: {text_main};
}}

QToolTip {{
    background: {bg_dark};
    color: {primary_text};
    border: 1px solid {primary};
    padding: 4px;
}}

QProgressBar {{
    background: {bg_dark};
    border: 1px solid {bg_dark};
    border-radius: 2px;
    text-align: center;
    color: {text_main};
}}

QProgressBar::chunk {{
    background: {primary};
    border-radius: 2px;
}}

QCheckBox, QRadioButton {{
    color: {text_main};
    spacing: 8px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {bg_dark};
    background: {bg_alt};
}}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {primary};
    border: 2px solid {primary};
}}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border: 2px solid {primary_light};
}}

QGroupBox {{
    background: {bg_main};
    border: 1px solid {bg_dark};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 12px;
    color: {text_main};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 8px;
    color: {primary};
}}

QSlider::groove:horizontal {{
    background: {bg_dark};
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: {primary};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
    background: {primary_light};
}}
"""

    return qss


def main():
    """Convert all Material themes to QSS."""
    # Path to installed qt_material themes
    material_themes_path = Path("/Users/duskfall/.pyenv/versions/3.10.16/lib/python3.10/site-packages/qt_material/themes")

    # Output directory
    output_dir = Path("/Users/duskfall/Downloads/Dataset-Tools-Toomany_Branches_LintingFixes/Dataset-Tools/dataset_tools/themes/MATERIAL_CONVERTED")
    output_dir.mkdir(exist_ok=True)

    print("Converting Material themes to clean QSS...")
    print(f"Source: {material_themes_path}")
    print(f"Output: {output_dir}\n")

    # Convert all XML themes
    converted = 0
    for xml_file in material_themes_path.glob("*.xml"):
        theme_name = xml_file.stem
        is_dark = theme_name.startswith('dark_')

        try:
            # Parse colors
            colors = parse_material_xml(xml_file)

            # Generate QSS
            qss_content = generate_qss(theme_name, colors, is_dark)

            # Write output
            output_file = output_dir / f"material_{theme_name}.qss"
            output_file.write_text(qss_content)

            print(f"✓ Converted: {theme_name} → {output_file.name}")
            converted += 1

        except Exception as e:
            print(f"✗ Failed: {theme_name} - {e}")

    print(f"\n✅ Converted {converted} themes successfully!")
    print(f"\nThemes saved to: {output_dir}")
    print("\nRemember: These themes are for internal use only!")


if __name__ == "__main__":
    main()
