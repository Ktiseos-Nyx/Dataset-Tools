#!/usr/bin/env python3
"""Show the current font status for Dataset Tools."""

from pathlib import Path


def show_font_status() -> None:
    """Show current bundled font status."""
    fonts_dir = Path(__file__).parent

    print("=" * 50)
    print("DATASET TOOLS FONT STATUS")
    print("=" * 50)

    # Check bundled fonts
    bundled_fonts = ["JetBrainsMono-Regular.ttf", "JetBrainsMono-Bold.ttf"]

    print("BUNDLED FONTS:")
    for font in bundled_fonts:
        font_path = fonts_dir / font
        status = "✓" if font_path.exists() else "✗"
        size = f"({font_path.stat().st_size // 1024} KB)" if font_path.exists() else ""
        print(f"  {status} {font} {size}")

    print("\nFONT STRATEGY:")
    print("  • JetBrains Mono: For code/technical metadata (bundled)")
    print("  • System UI font: For interface elements (system)")
    print("  • System fonts: For text content (system)")
    print("  • Graceful fallbacks: monospace → sans-serif → serif")

    print("\nWHY THIS APPROACH:")
    print("  • Minimal bundle size (only essential fonts)")
    print("  • Respects user's system preferences")
    print("  • Excellent code readability with JetBrains Mono")
    print("  • No permissions required (app-level loading)")
    print("  • Works offline")

    total_size = sum((fonts_dir / font).stat().st_size for font in bundled_fonts if (fonts_dir / font).exists())
    print(f"\nTOTAL BUNDLE SIZE: {total_size // 1024} KB")


if __name__ == "__main__":
    show_font_status()
