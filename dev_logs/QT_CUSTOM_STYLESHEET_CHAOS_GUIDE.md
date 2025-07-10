# Qt Custom Stylesheet Guide: Making Aesthetic Crimes Against Good Taste

## Overview
Forget qt-material! We're going FULL CUSTOM with Qt stylesheets to create the most beautiful, terrible, amazing themes known to humanity. Geocities nostalgia and vaporwave aesthetics await!

## Basic Qt Stylesheet Structure

### How Qt Stylesheets Work
Qt stylesheets use CSS-like syntax but with Qt-specific selectors:

```css
QWidget {
    background-color: #FF00FF;
    color: #00FFFF;
    font-family: "Comic Sans MS";
}

QPushButton {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #FF00FF, stop: 1 #8B00FF);
    border: 2px solid #00FFFF;
    border-radius: 15px;
    padding: 8px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #00FFFF;
    color: #FF00FF;
}
```

## Theme Templates

### 🌈 GEOCITIES NIGHTMARE THEME
*"It's 1997 and we have NO CHILL"*

```css
/* Main window background */
QMainWindow {
    background-image: url("themes/assets/starfield.gif");
    background-repeat: repeat;
}

/* General widget styling */
QWidget {
    font-family: "Times New Roman", serif;
    font-size: 12pt;
    color: #FFFF00;
    background-color: #000080;
}

/* Buttons with maximum 90s energy */
QPushButton {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                stop: 0 #FF0000, stop: 0.5 #FFFF00, stop: 1 #00FF00);
    border: 3px outset #C0C0C0;
    border-radius: 0px;
    padding: 5px 15px;
    font-weight: bold;
    font-size: 14pt;
    color: #000000;
    text-transform: uppercase;
}

QPushButton:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                stop: 0 #00FF00, stop: 0.5 #FFFF00, stop: 1 #FF0000);
    border: 3px inset #C0C0C0;
}

QPushButton:pressed {
    background-color: #FF00FF;
    border: 3px inset #808080;
}

/* Text areas with that classic Geocities feel */
QTextEdit, QPlainTextEdit {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px inset #C0C0C0;
    font-family: "Courier New", monospace;
    font-size: 10pt;
}

/* List widgets */
QListWidget {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px inset #C0C0C0;
    alternate-background-color: #E0E0E0;
}

QListWidget::item:selected {
    background-color: #0000FF;
    color: #FFFFFF;
}

/* Menu bar */
QMenuBar {
    background-color: #C0C0C0;
    color: #000000;
    border-bottom: 2px outset #C0C0C0;
}

QMenuBar::item:selected {
    background-color: #0000FF;
    color: #FFFFFF;
}

/* Status bar */
QStatusBar {
    background-color: #C0C0C0;
    color: #000000;
    border-top: 2px outset #C0C0C0;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #C0C0C0;
    width: 20px;
    border: 2px outset #C0C0C0;
}

QScrollBar::handle:vertical {
    background-color: #808080;
    border: 2px outset #C0C0C0;
    min-height: 20px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background-color: #C0C0C0;
    border: 2px outset #C0C0C0;
    height: 20px;
}
```

### 🌸 VAPORWAVE AESTHETIC THEME
*"A E S T H E T I C   V I B E S"*

```css
/* Main window with gradient magic */
QMainWindow {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #FF006E, stop: 0.3 #8338EC, 
                                stop: 0.7 #3A86FF, stop: 1 #06FFA5);
}

/* Widget base styling */
QWidget {
    font-family: "Arial", sans-serif;
    color: #FFFFFF;
    background-color: rgba(0, 0, 0, 0.3);
}

/* Vaporwave buttons */
QPushButton {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #FF006E, stop: 1 #8338EC);
    border: 2px solid #00FFFF;
    border-radius: 20px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 11pt;
    color: #FFFFFF;
    text-transform: uppercase;
    letter-spacing: 2px;
}

QPushButton:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #00FFFF, stop: 1 #FF006E);
    border: 2px solid #FFFF00;
    box-shadow: 0 0 20px #00FFFF;
}

QPushButton:pressed {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #8338EC, stop: 1 #3A86FF);
}

/* Text areas with neon glow effect */
QTextEdit, QPlainTextEdit {
    background-color: rgba(0, 0, 0, 0.8);
    color: #00FFFF;
    border: 2px solid #FF006E;
    border-radius: 10px;
    padding: 10px;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 10pt;
}

/* List widget with neon styling */
QListWidget {
    background-color: rgba(0, 0, 0, 0.7);
    color: #FFFFFF;
    border: 2px solid #00FFFF;
    border-radius: 10px;
    padding: 5px;
}

QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid rgba(255, 0, 110, 0.3);
}

QListWidget::item:selected {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #FF006E, stop: 1 #8338EC);
    border-radius: 5px;
}

QListWidget::item:hover {
    background-color: rgba(0, 255, 255, 0.2);
    border-radius: 5px;
}

/* Menu bar with retro vibes */
QMenuBar {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #8338EC, stop: 1 #3A86FF);
    color: #FFFFFF;
    padding: 5px;
    font-weight: bold;
}

QMenuBar::item {
    padding: 8px 15px;
    border-radius: 5px;
}

QMenuBar::item:selected {
    background-color: #FF006E;
}

/* Scrollbars with neon treatment */
QScrollBar:vertical {
    background-color: rgba(0, 0, 0, 0.5);
    width: 15px;
    border-radius: 7px;
}

QScrollBar::handle:vertical {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #FF006E, stop: 1 #00FFFF);
    border-radius: 7px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #00FFFF, stop: 1 #FFFF00);
}
```

### 🎮 CYBERPUNK 2077 THEME
*"Wake the f*ck up, samurai"*

```css
QMainWindow {
    background-color: #0a0a0a;
    color: #00ff41;
}

QWidget {
    background-color: #0a0a0a;
    color: #00ff41;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 10pt;
}

QPushButton {
    background-color: #1a1a1a;
    border: 2px solid #00ff41;
    color: #00ff41;
    padding: 8px 16px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
}

QPushButton:hover {
    background-color: #00ff41;
    color: #000000;
    border: 2px solid #ffff00;
}

QPushButton:pressed {
    background-color: #ff0066;
    border: 2px solid #ff0066;
    color: #ffffff;
}

QTextEdit, QPlainTextEdit {
    background-color: #000000;
    color: #00ff41;
    border: 1px solid #00ff41;
    font-family: "Consolas", "Monaco", monospace;
}

QListWidget {
    background-color: #111111;
    color: #00ff41;
    border: 1px solid #00ff41;
}

QListWidget::item:selected {
    background-color: #00ff41;
    color: #000000;
}
```

### 🦄 KAWAII PASTEL OVERLOAD
*"UwU what's this? A theme!"*

```css
QMainWindow {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                stop: 0 #FFB3BA, stop: 0.25 #FFDFBA,
                                stop: 0.5 #FFFFBA, stop: 0.75 #BAFFC9,
                                stop: 1 #BAE1FF);
}

QWidget {
    color: #8B4B8B;
    font-family: "Comic Sans MS", cursive;
    font-size: 11pt;
}

QPushButton {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #FFB3E6, stop: 1 #E6B3FF);
    border: 3px solid #FF99CC;
    border-radius: 25px;
    padding: 12px 20px;
    font-weight: bold;
    color: #8B008B;
    font-size: 12pt;
}

QPushButton:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #FFCCF9, stop: 1 #F9CCFF);
    border: 3px solid #FF66B2;
}

QTextEdit, QPlainTextEdit {
    background-color: #FFFFFF;
    color: #8B4B8B;
    border: 2px solid #FFB3E6;
    border-radius: 15px;
    padding: 10px;
}

QListWidget {
    background-color: #FFF0F5;
    color: #8B4B8B;
    border: 2px solid #FFB3E6;
    border-radius: 10px;
}

QListWidget::item:selected {
    background-color: #FFB3E6;
    color: #8B008B;
    border-radius: 5px;
}
```

## Custom Assets & Effects

### Adding Background Images
```css
/* Tiled background */
QMainWindow {
    background-image: url("themes/assets/your_image.png");
    background-repeat: repeat;
}

/* Stretched background */
QMainWindow {
    background-image: url("themes/assets/your_image.png");
    background-repeat: no-repeat;
    background-position: center;
}
```

### Gradient Masterclass
```css
/* Linear gradients */
background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                            stop: 0 #color1, stop: 1 #color2);

/* Radial gradients */
background: qradialgradient(cx: 0.5, cy: 0.5, radius: 1,
                            stop: 0 #color1, stop: 1 #color2);

/* Multi-stop gradients */
background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                            stop: 0 #FF0000, stop: 0.3 #FFFF00,
                            stop: 0.7 #00FF00, stop: 1 #0000FF);
```

### Animation Effects (Qt 5.15+)
```css
QPushButton {
    transition: all 0.3s ease;
}

QPushButton:hover {
    transform: scale(1.05);
}
```

## Advanced Selectors

### Widget-Specific Styling
```css
/* Style specific widgets by object name */
QPushButton#copyButton {
    background-color: #FF6B35;
}

/* Style by property */
QPushButton[flat="true"] {
    border: none;
}

/* Style child widgets */
QMainWindow > QWidget {
    background-color: transparent;
}
```

### State-Based Styling
```css
QPushButton:disabled {
    background-color: #808080;
    color: #A0A0A0;
}

QPushButton:checked {
    background-color: #4CAF50;
}

QListWidget::item:alternate {
    background-color: #F5F5F5;
}
```

## Theme Integration

### File Structure
```
themes/
├── geocities_nightmare.qss
├── vaporwave_aesthetic.qss
├── cyberpunk_2077.qss
├── kawaii_overload.qss
└── assets/
    ├── starfield.gif
    ├── grid_pattern.png
    └── neon_border.png
```

### Loading Custom Stylesheets
```python
def apply_custom_theme(self, theme_file):
    """Apply a custom Qt stylesheet theme."""
    try:
        with open(f"themes/{theme_file}", 'r') as f:
            stylesheet = f.read()
        self.setStyleSheet(stylesheet)
        nfo(f"Applied custom theme: {theme_file}")
    except Exception as e:
        nfo(f"Failed to apply theme {theme_file}: {e}")
```

## Pro Tips for Maximum Aesthetic Chaos

### Color Combinations That Hurt Good
- **Geocities Special:** `#FF00FF` + `#00FFFF` + `#FFFF00`
- **Eye Searing:** `#FF0000` + `#00FF00` + `#0000FF`
- **Pastel Overdose:** `#FFB3BA` + `#FFDFBA` + `#FFFFBA` + `#BAFFC9`
- **Neon Nightmare:** `#FF1493` + `#00FF7F` + `#1E90FF`

### Fonts That Scream 90s
```css
font-family: "Comic Sans MS", cursive;
font-family: "Papyrus", fantasy;
font-family: "Brush Script MT", cursive;
font-family: "Impact", sans-serif;
```

### Border Crimes
```css
/* The classic 90s inset/outset */
border: 3px outset #C0C0C0;
border: 3px inset #C0C0C0;

/* Ridiculous border radius */
border-radius: 50px;

/* Multiple borders (use box-shadow) */
border: 2px solid #FF00FF;
box-shadow: 0 0 0 4px #00FFFF, 0 0 0 8px #FFFF00;
```

### Text Effects
```css
/* CAPS LOCK IS CRUISE CONTROL FOR COOL */
text-transform: uppercase;

/* S P A C E D   O U T */
letter-spacing: 3px;

/* Shadow effects */
text-shadow: 2px 2px 4px #000000;

/* Outline text */
color: transparent;
text-stroke: 2px #FF00FF;
```

## Testing Your Aesthetic Crimes

### Quick Test Script
```python
def test_theme(theme_file):
    """Quick theme tester."""
    app = QApplication(sys.argv)
    
    # Load your custom stylesheet
    with open(f"themes/{theme_file}", 'r') as f:
        app.setStyleSheet(f.read())
    
    # Create test window
    window = QMainWindow()
    window.setWindowTitle(f"Testing: {theme_file}")
    
    # Add some test widgets
    central = QWidget()
    layout = QVBoxLayout(central)
    
    layout.addWidget(QLabel("Test Label"))
    layout.addWidget(QPushButton("Test Button"))
    layout.addWidget(QTextEdit("Test text area"))
    
    window.setCentralWidget(central)
    window.show()
    
    app.exec()
```

### Things to Test
- [ ] Button hover/press states
- [ ] Text readability 
- [ ] Scrollbar functionality
- [ ] Menu interactions
- [ ] Focus indicators
- [ ] Different widget types
- [ ] Window resizing
- [ ] Your retinas (may cause permanent damage)

## Final Words of Chaos

Go forth and create the most beautiful, terrible themes the world has ever seen! Make users question their life choices! Make designers weep! Make the 90s proud!

Remember: There is no such thing as "too much gradient" or "too many colors." If it doesn't make people's eyes hurt a little bit, you're not trying hard enough! 🌈✨

---
*"It's not a bug, it's an aesthetic choice!"* - Every theme creator ever