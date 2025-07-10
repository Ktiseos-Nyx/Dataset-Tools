# Qt6 Theme Creation Guide: Making Your App Look Less Like 1995

## Overview
This guide will help you create custom Qt6 themes using qt-material style definitions. Because why settle for boring default themes when you can make your app look absolutely gorgeous?

## Theme File Structure

### Basic Theme Template
Create a new `.xml` file in your themes directory. Here's the basic structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<resources>
  <color name="primaryColor">#your_primary_color</color>
  <color name="primaryLightColor">#lighter_primary</color>
  <color name="primaryDarkColor">#darker_primary</color>
  <color name="secondaryColor">#your_secondary_color</color>
  <color name="secondaryLightColor">#lighter_secondary</color>
  <color name="secondaryDarkColor">#darker_secondary</color>
  <color name="primaryTextColor">#text_on_primary</color>
  <color name="secondaryTextColor">#text_on_secondary</color>
</resources>
```

## Complete Theme Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<resources>
    <!-- Primary Colors -->
    <color name="primaryColor">#2196F3</color>
    <color name="primaryLightColor">#64B5F6</color> 
    <color name="primaryDarkColor">#1976D2</color>
    
    <!-- Secondary Colors -->
    <color name="secondaryColor">#FF9800</color>
    <color name="secondaryLightColor">#FFB74D</color>
    <color name="secondaryDarkColor">#F57C00</color>
    
    <!-- Text Colors -->
    <color name="primaryTextColor">#FFFFFF</color>
    <color name="secondaryTextColor">#000000</color>
    
    <!-- Background Colors -->
    <color name="backgroundColor">#FAFAFA</color>
    <color name="surfaceColor">#FFFFFF</color>
    <color name="errorColor">#F44336</color>
    
    <!-- Dark Theme Variants (if creating dark theme) -->
    <color name="backgroundColorDark">#121212</color>
    <color name="surfaceColorDark">#1E1E1E</color>
    <color name="primaryTextColorDark">#FFFFFF</color>
    <color name="secondaryTextColorDark">#B3B3B3</color>
</resources>
```

## Icon & Button Sizing Guidelines

### Standard Sizes (Based on Material Design)
```python
# Button Icons
SMALL_ICON = QSize(16, 16)      # Small buttons, toolbar items
MEDIUM_ICON = QSize(24, 24)     # Standard buttons
LARGE_ICON = QSize(32, 32)      # Large action buttons
XLARGE_ICON = QSize(48, 48)     # Main action buttons

# Button Heights
SMALL_BUTTON_HEIGHT = 32
MEDIUM_BUTTON_HEIGHT = 40  
LARGE_BUTTON_HEIGHT = 48

# Spacing
STANDARD_SPACING = 8
LARGE_SPACING = 16
SECTION_SPACING = 24
```

### Button Size Categories
```python
# Use these in your icon_manager.add_icon_to_button() calls
ICON_SIZES = {
    "tiny": QSize(12, 12),       # Status indicators
    "small": QSize(16, 16),      # Toolbar, compact buttons
    "medium": QSize(24, 24),     # Standard buttons
    "large": QSize(32, 32),      # Important actions
    "xlarge": QSize(48, 48),     # Primary actions
    "huge": QSize(64, 64),       # Hero buttons (rare)
}
```

## Theme Color Palettes

### Popular Color Schemes

#### Dark Theme Template
```xml
<color name="primaryColor">#BB86FC</color>
<color name="primaryLightColor">#D7B9FF</color>
<color name="primaryDarkColor">#985EFF</color>
<color name="secondaryColor">#03DAC6</color>
<color name="backgroundColor">#121212</color>
<color name="surfaceColor">#1E1E1E</color>
<color name="primaryTextColor">#FFFFFF</color>
<color name="secondaryTextColor">#B3B3B3</color>
```

#### Cyberpunk Theme
```xml
<color name="primaryColor">#FF00FF</color>
<color name="primaryLightColor">#FF44FF</color>
<color name="primaryDarkColor">#CC00CC</color>
<color name="secondaryColor">#00FFFF</color>
<color name="backgroundColor">#0D0D0D</color>
<color name="surfaceColor">#1A1A1A</color>
<color name="primaryTextColor">#00FF00</color>
<color name="secondaryTextColor">#CCCCCC</color>
```

#### Nature Theme
```xml
<color name="primaryColor">#4CAF50</color>
<color name="primaryLightColor">#81C784</color>
<color name="primaryDarkColor">#388E3C</color>
<color name="secondaryColor">#8BC34A</color>
<color name="backgroundColor">#F1F8E9</color>
<color name="surfaceColor">#FFFFFF</color>
<color name="primaryTextColor">#FFFFFF</color>
<color name="secondaryTextColor">#2E7D32</color>
```

## Creating Your Own Theme

### Step 1: Choose Your Color Palette
Use tools like:
- [Coolors.co](https://coolors.co) - Color palette generator
- [Material Design Colors](https://materialui.co/colors) - Material design color picker
- [Adobe Color](https://color.adobe.com) - Advanced color theory tools

### Step 2: Name Your Theme
Use the format: `your_theme_name.xml`
Examples:
- `midnight_purple.xml`
- `ocean_breeze.xml` 
- `neon_synthwave.xml`
- `coffee_shop.xml`

### Step 3: Test Your Theme
1. Create your `.xml` file in the themes directory
2. Add it to the theme dropdown in settings
3. Test with different UI elements
4. Check contrast ratios for accessibility

### Step 4: Fine-tune Colors
Pay attention to:
- **Contrast:** Text should be readable on backgrounds
- **Consistency:** Related elements should use related colors
- **Accessibility:** Follow WCAG guidelines for color contrast
- **Branding:** Match your personal/project aesthetic

## Advanced Theming Tips

### Color Psychology
- **Blue:** Trust, reliability, calmness
- **Green:** Nature, growth, success
- **Purple:** Creativity, luxury, mystery  
- **Orange:** Energy, enthusiasm, warmth
- **Red:** Urgency, passion, power
- **Dark themes:** Reduce eye strain, look professional

### Icon Color Matching
Your icon manager should automatically adjust icon colors based on theme:
```python
# In your icon_manager.py, these color types map to theme colors:
COLOR_MAPPINGS = {
    "primary": "primaryColor",
    "secondary": "secondaryColor", 
    "surface": "surfaceColor",
    "text": "primaryTextColor"
}
```

### Testing Checklist
- [ ] All text is readable
- [ ] Buttons look clickable
- [ ] Icons are visible and appropriately colored
- [ ] Focus states are clear
- [ ] Error states stand out
- [ ] Theme works in both light and dark environments

## Example: Creating a "Sunset" Theme

```xml
<?xml version="1.0" encoding="UTF-8"?>
<resources>
    <!-- Sunset Orange/Pink Palette -->
    <color name="primaryColor">#FF6B35</color>
    <color name="primaryLightColor">#FF8A65</color>
    <color name="primaryDarkColor">#E64A19</color>
    
    <color name="secondaryColor">#FF8A80</color>
    <color name="secondaryLightColor">#FFB2A7</color>
    <color name="secondaryDarkColor">#FF5722</color>
    
    <color name="backgroundColor">#FFF3E0</color>
    <color name="surfaceColor">#FFFFFF</color>
    <color name="primaryTextColor">#FFFFFF</color>
    <color name="secondaryTextColor">#BF360C</color>
    <color name="errorColor">#D32F2F</color>
</resources>
```

## Pro Tips

### Do:
- ✅ Start with existing themes and modify them
- ✅ Test themes with actual content loaded
- ✅ Consider different screen sizes and resolutions
- ✅ Use color theory principles
- ✅ Make multiple variants (light/dark)

### Don't:
- ❌ Use super bright colors for large areas
- ❌ Make text hard to read for style points
- ❌ Ignore accessibility guidelines
- ❌ Use too many different colors
- ❌ Forget to test with icons

## Quick Start Commands

```bash
# Copy an existing theme to start
cp themes/dark_teal.xml themes/my_awesome_theme.xml

# Edit your theme
nano themes/my_awesome_theme.xml

# Test it in the app
# 1. Open settings
# 2. Select your new theme
# 3. Click Apply
# 4. Admire your creation!
```

## Theme Integration with Your App

Your app already supports themes! Just:
1. Create your `.xml` file in the themes directory
2. The app will automatically detect it
3. It'll appear in the settings dropdown
4. Icons will automatically adjust colors based on your theme

## Final Note

Have fun with it! Themes are one of those features where you can really let your creativity shine. Don't be afraid to make something bold and unique - your app, your rules! 🎨✨

And remember: if you make something truly hideous, you can always go back to the default theme. No judgment here! 😄

---
*Happy theming! May your colors be vibrant and your contrast ratios be accessible.*