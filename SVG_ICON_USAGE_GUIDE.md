# SVG Icon Integration Guide

## 🎨 Overview

The Dataset Tools app now has a comprehensive SVG icon system that automatically adapts to Qt Material themes! Icons change color automatically when you switch between light and dark themes.

## 📁 Icon Directory Structure

``` bash
dataset_tools/ui/icons/
├── folder-open.svg          # Open folder button
├── sort-alphabetical.svg    # Sort files button
├── image-multiple.svg       # Image-related actions
└── [your-custom-icons].svg  # Add more here!
```

## 🎯 How to Add Your SVG Icons

### 1. **Prepare Your SVG Files**

- Name them descriptively (e.g., `settings.svg`, `refresh.svg`, `search.svg`)
- Use `fill="currentColor"` in your SVG paths (this allows theme-based coloring)
- Keep them simple and clean (24x24px viewBox works best)

### 2. **Example SVG Format**

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
  <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z" />
</svg>
```

### 3. **Add Icons to Buttons**

```python
# In your UI code:
from .icon_manager import get_icon_manager
from PyQt6.QtCore import QSize

# Get the icon manager
icon_manager = get_icon_manager()

# Add icon to a button
icon_manager.add_icon_to_button(
    button=my_button,
    icon_name="your-icon-name",  # without .svg extension
    color_type="primary",        # "primary", "secondary", "accent", "disabled"
    icon_size=QSize(16, 16)     # icon size
)
```

## 🎨 Color Types Available

- **`primary`**: Main icon color (white in dark themes, dark gray in light themes)
- **`secondary`**: Subtle icon color (light gray in dark, medium gray in light)
- **`accent`**: Highlight color (cyan in dark themes, teal in light themes)
- **`disabled`**: Muted color for disabled states

## 🔧 Current Icon Implementations

### ✅ Already Implemented

- **Open Folder button**: `folder-open.svg` with primary color
- **Sort Files button**: `sort-alphabetical.svg` with primary color

### 🎯 Great Icons to Add Next

```bash
# Place these in dataset_tools/ui/icons/
refresh.svg         # Refresh/reload button
settings.svg        # Settings/preferences
search.svg          # Search functionality
filter.svg          # Filter files
view-grid.svg       # Grid view toggle
view-list.svg       # List view toggle
info.svg            # Information/about
close.svg           # Close/cancel actions
save.svg            # Save operations
export.svg          # Export metadata
theme.svg           # Theme switcher
fullscreen.svg      # Fullscreen mode
```

## 🚀 Advanced Usage

### Get Icons Programmatically

```python
from .icon_manager import get_themed_icon
from PyQt6.QtCore import QSize

# Get a themed icon directly
icon = get_themed_icon("settings", "accent", QSize(20, 20))
my_action.setIcon(icon)
```

### Custom Color Updates

```python
# The icon manager automatically detects theme changes, but you can manually update:
icon_manager = get_icon_manager()
icon_manager.set_theme_colors(
    primary=QColor(255, 0, 0),    # Custom red
    secondary=QColor(128, 128, 128),
    accent=QColor(0, 255, 0)      # Custom green
)
```

## 🎯 Benefits of This System

1. **Automatic Theme Adaptation**: Icons change color when themes switch
2. **Performance Optimized**: Icons are cached after first load
3. **Fallback Support**: Shows simple placeholders if SVG files are missing
4. **Qt Material Compatible**: Works perfectly with all qt-material themes
5. **Easy to Extend**: Just drop SVG files in the icons folder and use them

## 📝 Icon Naming Conventions

Use descriptive, kebab-case names:

- ✅ `folder-open.svg`
- ✅ `sort-alphabetical.svg`
- ✅ `image-multiple.svg`
- ❌ `icon1.svg`
- ❌ `FolderOpen.svg`

## 🎨 Where to Find Good SVG Icons

- **Material Design Icons**: https://materialdesignicons.com/
- **Heroicons**: https://heroicons.com/
- **Lucide**: https://lucide.dev/
- **Tabler Icons**: https://tabler-icons.io/

## 🔍 Testing Your Icons

1. **Add your SVG** to `dataset_tools/ui/icons/`
2. **Update a button** to use the new icon
3. **Test with different themes** (light/dark) to ensure proper coloring
4. **Check fallback** by temporarily renaming the SVG file

## 💡 Pro Tips

- Icons automatically scale well from 12px to 32px
- Use `primary` color for most buttons
- Use `accent` color for important/active states
- Use `secondary` color for subtle/helper buttons
- Use `disabled` color for inactive states

Your icon system is now ready to make the UI much more polished and professional! 🎨✨
