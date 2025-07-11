# Bundled Fonts for Dataset Tools

This directory contains a minimal set of essential fonts bundled with Dataset Tools to ensure excellent code readability while maintaining a small distribution size.

## Font Philosophy

**Minimal Bundle Strategy:**
- Bundle only essential fonts that significantly improve user experience
- Prioritize system fonts for UI elements (respects user preferences)
- Include specialized fonts only where they provide clear value
- Keep total bundle size under 1MB

## Bundled Fonts

### JetBrains Mono (Monospace Font)
- **License**: SIL Open Font License 1.1
- **Source**: https://github.com/JetBrains/JetBrainsMono
- **Usage**: Code/technical metadata display in generation details
- **Files**: `JetBrainsMono-Regular.ttf` (263 KB), `JetBrainsMono-Bold.ttf` (267 KB)
- **Why bundled**: Excellent code readability with perfect alignment and ligatures

**Total Bundle Size: 531 KB**

## Font Loading Strategy

1. **JetBrains Mono**: Loaded from bundle for technical metadata
2. **UI Elements**: Use system-ui font (respects user's OS preferences)
3. **Text Content**: Use system fonts with graceful fallbacks
4. **Fallback Chain**: bundled → system → generic

## Font Loading

Fonts are automatically loaded at application startup via `FontManager._load_bundled_fonts()`. No user action required.

## Fallback Behavior

If bundled fonts fail to load, the application gracefully falls back to system fonts:
- **UI**: system-ui → sans-serif
- **Monospace**: JetBrains Mono → system monospace
- **Reading**: system-ui → serif

## Font Updates

To update JetBrains Mono:
1. Download latest release from https://github.com/JetBrains/JetBrainsMono/releases
2. Replace TTF files in this directory
3. Keep only Regular and Bold weights to minimize size

## Design Decisions

- **No UI font bundling**: System fonts work great for UI and respect user preferences
- **No reading font bundling**: System fonts are optimized for reading on each platform
- **JetBrains Mono only**: The one font where bundling provides clear value for code display
- **Minimal weights**: Only Regular and Bold to keep size reasonable