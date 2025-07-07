#!/usr/bin/env python3
"""Font Awesome SVG to Theme-Compatible Converter

This script automatically converts Font Awesome SVG icons to work with Qt Material themes
by replacing hardcoded fills with "currentColor" so they adapt to theme colors.

Usage: python convert_icons_to_theme_compatible.py
"""

import re
from pathlib import Path


def convert_svg_to_theme_compatible(svg_content: str) -> str:
    """Convert SVG content to be theme-compatible.

    Args:
        svg_content: Original SVG content

    Returns:
        Modified SVG content with theme-compatible fills

    """
    # Make a copy to work with
    modified_content = svg_content

    # 1. Replace any explicit black fills
    modified_content = re.sub(
        r'fill="#000000?"', 'fill="currentColor"', modified_content
    )
    modified_content = re.sub(r'fill="black"', 'fill="currentColor"', modified_content)
    modified_content = re.sub(
        r'fill="rgb\(0,\s*0,\s*0\)"', 'fill="currentColor"', modified_content
    )

    # 2. For Font Awesome paths that don't have explicit fill, add currentColor
    # This regex finds <path> tags that don't already have a fill attribute
    def add_fill_to_path(match):
        path_tag = match.group(0)
        if "fill=" not in path_tag:
            # Insert fill="currentColor" after <path
            return path_tag.replace("<path", '<path fill="currentColor"')
        return path_tag

    modified_content = re.sub(r"<path[^>]*>", add_fill_to_path, modified_content)

    # 3. Handle any other shape elements that might need fills
    shape_elements = ["circle", "rect", "ellipse", "polygon", "polyline"]
    for element in shape_elements:
        pattern = f"<{element}[^>]*>"

        def add_fill_to_shape(match):
            tag = match.group(0)
            if (
                "fill=" not in tag and "stroke=" in tag
            ):  # Only if it's meant to be filled
                return tag.replace(f"<{element}", f'<{element} fill="currentColor"')
            return tag

        modified_content = re.sub(pattern, add_fill_to_shape, modified_content)

    # 4. Clean up any double fills that might have been created
    modified_content = re.sub(
        r'fill="currentColor"\s+fill="[^"]*"', 'fill="currentColor"', modified_content
    )

    return modified_content


def backup_original_file(file_path: Path) -> Path:
    """Create a backup of the original file.

    Args:
        file_path: Path to the original file

    Returns:
        Path to the backup file

    """
    backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
    backup_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def convert_icons_in_directory(icons_dir: Path, create_backups: bool = True) -> dict:
    """Convert all SVG icons in a directory to be theme-compatible.

    Args:
        icons_dir: Directory containing SVG icons
        create_backups: Whether to create backup files

    Returns:
        Dictionary with conversion results

    """
    results = {"converted": [], "skipped": [], "errors": [], "backups_created": []}

    if not icons_dir.exists():
        print(f"❌ Icons directory not found: {icons_dir}")
        return results

    print(f"🔍 Scanning for SVG files in: {icons_dir}")
    svg_files = list(icons_dir.glob("*.svg"))

    if not svg_files:
        print("❌ No SVG files found in the directory")
        return results

    print(f"📁 Found {len(svg_files)} SVG files to process")

    for svg_file in svg_files:
        try:
            print(f"\n🔧 Processing: {svg_file.name}")

            # Read the original content
            original_content = svg_file.read_text(encoding="utf-8")

            # Check if it already looks theme-compatible
            if "currentColor" in original_content:
                print(f"✅ {svg_file.name} already appears theme-compatible, skipping")
                results["skipped"].append(svg_file.name)
                continue

            # Create backup if requested
            if create_backups:
                backup_path = backup_original_file(svg_file)
                results["backups_created"].append(backup_path.name)
                print(f"💾 Backup created: {backup_path.name}")

            # Convert the content
            converted_content = convert_svg_to_theme_compatible(original_content)

            # Check if anything actually changed
            if converted_content == original_content:
                print(f"⚠️  No changes needed for {svg_file.name}")
                results["skipped"].append(svg_file.name)
                continue

            # Write the converted content
            svg_file.write_text(converted_content, encoding="utf-8")

            print(f"✅ Converted {svg_file.name} to theme-compatible format")
            results["converted"].append(svg_file.name)

        except Exception as e:
            error_msg = f"{svg_file.name}: {e!s}"
            print(f"❌ Error processing {svg_file.name}: {e}")
            results["errors"].append(error_msg)

    return results


def main():
    """Main conversion function."""
    print("🎨 Font Awesome SVG to Theme-Compatible Converter")
    print("=" * 50)

    # Find the icons directory
    icons_dir = Path(__file__).parent / "dataset_tools" / "ui" / "icons"

    if not icons_dir.exists():
        print(f"❌ Icons directory not found at: {icons_dir}")
        print("Please run this script from the project root directory.")
        return

    print(f"📂 Icons directory: {icons_dir}")
    print("🔄 Converting SVG icons to be Qt Material theme compatible...")

    # Convert the icons
    results = convert_icons_in_directory(icons_dir, create_backups=True)

    # Print results summary
    print("\n" + "=" * 50)
    print("📊 CONVERSION RESULTS:")
    print(f"✅ Successfully converted: {len(results['converted'])} files")
    print(f"⏭️  Skipped (already compatible): {len(results['skipped'])} files")
    print(f"❌ Errors: {len(results['errors'])} files")
    print(f"💾 Backups created: {len(results['backups_created'])} files")

    if results["converted"]:
        print("\n🎯 Converted files:")
        for file in results["converted"]:
            print(f"   • {file}")

    if results["errors"]:
        print("\n⚠️  Errors encountered:")
        for error in results["errors"]:
            print(f"   • {error}")

    if results["converted"]:
        print("\n🎉 SUCCESS! Your Font Awesome icons are now theme-compatible!")
        print("🔄 Restart your app to see the icons adapt to theme colors.")
        print("💾 Original files backed up with .backup extension")
    else:
        print("\n📝 No files needed conversion - you're all set!")


if __name__ == "__main__":
    main()
