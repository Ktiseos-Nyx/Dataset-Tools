# hide (Hideto Matsumoto) Pink Spider Theme Guide: Visual Kei Aesthetic Perfection

## 🕷️ The Pink Spider's Color Palette

### **hide's Signature Colors**
```python
HIDE_COLORS = {
    # Primary Pink Spider Colors
    'hot_pink': '#FF1493',           # hide's signature hot pink
    'electric_pink': '#FF69B4',      # Bright electric pink
    'neon_pink': '#FF00FF',          # Neon magenta
    'soft_pink': '#FFB6C1',          # Light pink accents
    'deep_pink': '#C71585',          # Deep pink shadows
    
    # Visual Kei Blacks & Grays
    'void_black': '#000000',         # Pure black
    'charcoal': '#1C1C1C',           # Dark charcoal
    'steel_gray': '#2F2F2F',         # Steel gray
    'silver': '#C0C0C0',             # Silver accents
    
    # X JAPAN Colors
    'blood_red': '#8B0000',          # Dark red
    'royal_purple': '#4B0082',       # Deep purple
    'electric_blue': '#0080FF',      # Electric blue
    
    # Text Colors
    'white_light': '#FFFFFF',        # Pure white
    'pink_glow': '#FFDDEE',          # Pink-tinted white
    'gray_text': '#CCCCCC',          # Light gray text
    'disabled_gray': '#666666',      # Disabled text
    
    # Special Effects
    'neon_glow': '#FF44AA',          # Neon glow effect
    'spider_web': '#444444',         # Web pattern color
    'stage_light': '#FFAADD',        # Stage lighting effect
    'amplifier_green': '#00FF00',    # Amp indicator green
}
```

### **Visual Kei Gradients**
```python
HIDE_GRADIENTS = {
    'pink_spider_main': ['#FF1493', '#8B0000'],      # Pink to dark red
    'electric_fade': ['#FF00FF', '#4B0082'],         # Magenta to purple
    'stage_lights': ['#FFAADD', '#FF1493'],          # Light pink to hot pink
    'amp_glow': ['#FF1493', '#000000'],              # Pink fading to black
    'web_pattern': ['#2F2F2F', '#000000'],           # Gray to black
    'neon_burst': ['#FF00FF', '#FF1493', '#8B0000'], # Triple gradient
}
```

## 🎸 Complete hide Theme Implementation

### **Qt Stylesheet Version**
```css
/* hide (Pink Spider) Visual Kei Theme */

/* Main window - Dark with pink accents */
QMainWindow {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #1C1C1C, stop: 1 #000000);
    color: #FFFFFF;
}

/* Pink Spider Buttons */
QPushButton {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #FF1493, stop: 1 #C71585);
    border: 2px solid #FF69B4;
    border-radius: 8px;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 11pt;
    padding: 8px 16px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

QPushButton:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #FF69B4, stop: 1 #FF1493);
    border: 2px solid #FF00FF;
    color: #000000;
    text-shadow: 0 0 5px #FF1493;
}

QPushButton:pressed {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #8B0000, stop: 1 #FF1493);
    border: 2px solid #FFFFFF;
}

/* Visual Kei Frames */
QFrame {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #2F2F2F, stop: 1 #000000);
    border: 2px solid #FF1493;
    border-radius: 10px;
}

/* Text areas with neon glow effect */
QTextEdit, QPlainTextEdit {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #000000, stop: 1 #1C1C1C);
    border: 2px solid #FF1493;
    border-radius: 8px;
    color: #FFDDEE;
    font-family: "Consolas", monospace;
    font-size: 10pt;
    selection-background-color: #FF69B4;
    selection-color: #000000;
}

/* List widgets - Visual Kei style */
QListWidget {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #1C1C1C, stop: 1 #000000);
    border: 2px solid #FF1493;
    border-radius: 8px;
    color: #FFFFFF;
    font-family: "Arial", sans-serif;
    font-weight: bold;
    alternate-background-color: #2F2F2F;
}

QListWidget::item {
    padding: 6px;
    border-bottom: 1px solid #444444;
}

QListWidget::item:selected {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #FF1493, stop: 1 #8B0000);
    color: #FFFFFF;
    border: 1px solid #FF69B4;
    border-radius: 4px;
}

QListWidget::item:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #4B0082, stop: 1 #FF1493);
    color: #FFDDEE;
}

/* Menu bar - Rock star style */
QMenuBar {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #2F2F2F, stop: 1 #1C1C1C);
    border-bottom: 3px solid #FF1493;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 11pt;
}

QMenuBar::item {
    background: transparent;
    padding: 8px 16px;
    text-transform: uppercase;
}

QMenuBar::item:selected {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #FF1493, stop: 1 #C71585);
    color: #FFFFFF;
    border-radius: 4px;
}

/* Menus */
QMenu {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #1C1C1C, stop: 1 #000000);
    border: 2px solid #FF1493;
    border-radius: 8px;
    color: #FFFFFF;
    font-weight: bold;
}

QMenu::item {
    padding: 6px 20px;
}

QMenu::item:selected {
    background: #FF1493;
    color: #FFFFFF;
    border-radius: 4px;
}

/* Status bar - Stage lighting effect */
QStatusBar {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #FF1493, stop: 0.5 #1C1C1C, stop: 1 #FF1493);
    border-top: 2px solid #FF69B4;
    color: #FFFFFF;
    font-weight: bold;
}

/* Scrollbars - Pink spider web style */
QScrollBar:vertical {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #1C1C1C, stop: 1 #000000);
    width: 18px;
    border: 1px solid #FF1493;
    border-radius: 9px;
}

QScrollBar::handle:vertical {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #FF1493, stop: 1 #C71585);
    border: 1px solid #FF69B4;
    border-radius: 8px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #FF69B4, stop: 1 #FF1493);
    border: 1px solid #FF00FF;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: #1C1C1C;
    border: 1px solid #FF1493;
    height: 18px;
    border-radius: 9px;
}

/* Labels with neon glow effect */
QLabel {
    color: #FFFFFF;
    font-weight: bold;
}

QLabel[accessibleName="title"] {
    color: #FF1493;
    font-size: 18pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 2px;
}

QLabel[accessibleName="subtitle"] {
    color: #FFDDEE;
    font-size: 12pt;
    font-style: italic;
}
```

### **Tkinter Version**
```python
class HideThemeManager:
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style()
        
    def apply_hide_theme(self):
        """Apply hide (Pink Spider) visual kei theme."""
        
        # hide color palette
        bg_black = '#000000'
        bg_charcoal = '#1C1C1C'
        bg_steel = '#2F2F2F'
        pink_hot = '#FF1493'
        pink_electric = '#FF69B4'
        pink_neon = '#FF00FF'
        white_light = '#FFFFFF'
        pink_glow = '#FFDDEE'
        blood_red = '#8B0000'
        
        self.root.configure(bg=bg_black)
        
        # Configure ttk styles
        self.style.theme_use('clam')
        
        # Pink Spider Buttons
        self.style.configure('Hide.TButton',
                            background=pink_hot,
                            foreground=white_light,
                            borderwidth=2,
                            relief='raised',
                            padding=(16, 8),
                            font=('Arial', 10, 'bold'))
        
        self.style.map('Hide.TButton',
                      background=[('active', pink_electric),
                                ('pressed', blood_red)],
                      foreground=[('active', bg_black),
                                ('pressed', white_light)],
                      bordercolor=[('active', pink_neon)])
        
        # Visual Kei Labels
        self.style.configure('Hide.TLabel',
                            background=bg_black,
                            foreground=white_light,
                            font=('Arial', 10, 'bold'))
        
        self.style.configure('HideTitle.TLabel',
                            background=bg_black,
                            foreground=pink_hot,
                            font=('Arial', 16, 'bold'))
        
        # Dark Frames
        self.style.configure('Hide.TFrame',
                            background=bg_black,
                            borderwidth=2,
                            relief='solid')
        
        # Configure tk widgets
        self.configure_hide_widgets(bg_black, bg_charcoal, pink_hot, 
                                   pink_electric, white_light, pink_glow)
    
    def configure_hide_widgets(self, bg_black, bg_charcoal, pink_hot, 
                              pink_electric, white_light, pink_glow):
        """Configure regular tk widgets for hide theme."""
        
        self.root.option_add('*Button.Background', pink_hot)
        self.root.option_add('*Button.Foreground', white_light)
        self.root.option_add('*Button.ActiveBackground', pink_electric)
        self.root.option_add('*Button.ActiveForeground', bg_black)
        self.root.option_add('*Button.Font', 'Arial 10 bold')
        self.root.option_add('*Button.Relief', 'raised')
        self.root.option_add('*Button.BorderWidth', '2')
        
        self.root.option_add('*Label.Background', bg_black)
        self.root.option_add('*Label.Foreground', white_light)
        self.root.option_add('*Label.Font', 'Arial 10 bold')
        
        self.root.option_add('*Text.Background', bg_charcoal)
        self.root.option_add('*Text.Foreground', pink_glow)
        self.root.option_add('*Text.Font', 'Consolas 10')
        self.root.option_add('*Text.Relief', 'solid')
        self.root.option_add('*Text.BorderWidth', '2')
        self.root.option_add('*Text.SelectBackground', pink_electric)
        self.root.option_add('*Text.SelectForeground', bg_black)
        
        self.root.option_add('*Listbox.Background', bg_charcoal)
        self.root.option_add('*Listbox.Foreground', white_light)
        self.root.option_add('*Listbox.SelectBackground', pink_hot)
        self.root.option_add('*Listbox.SelectForeground', white_light)
        self.root.option_add('*Listbox.Font', 'Arial 9 bold')
```

## 🕸️ Visual Kei Border Effects & Spider Web Patterns

### **Spider Web Border Creator**
```python
from PIL import Image, ImageDraw, ImageTk
import math

class SpiderWebBorderCreator:
    @staticmethod
    def create_spider_web_border(width, height, web_color='#444444', 
                                spider_color='#FF1493'):
        """Create hide's signature spider web border pattern."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw web pattern
        center_x, center_y = width // 2, height // 2
        max_radius = min(width, height) // 2
        
        # Radial web lines
        for angle in range(0, 360, 45):  # 8 main web lines
            end_x = center_x + max_radius * math.cos(math.radians(angle))
            end_y = center_y + max_radius * math.sin(math.radians(angle))
            draw.line([center_x, center_y, end_x, end_y], 
                     fill=web_color, width=1)
        
        # Concentric web circles
        for radius in range(20, max_radius, 30):
            draw.ellipse([center_x - radius, center_y - radius,
                         center_x + radius, center_y + radius],
                        outline=web_color, width=1)
        
        # Add pink spider in corner
        spider_size = 8
        spider_x, spider_y = width - 20, 20
        draw.ellipse([spider_x - spider_size, spider_y - spider_size,
                     spider_x + spider_size, spider_y + spider_size],
                    fill=spider_color, outline='#FFFFFF', width=1)
        
        # Spider legs
        leg_length = spider_size + 4
        for angle in range(0, 360, 45):
            leg_end_x = spider_x + leg_length * math.cos(math.radians(angle))
            leg_end_y = spider_y + leg_length * math.sin(math.radians(angle))
            draw.line([spider_x, spider_y, leg_end_x, leg_end_y],
                     fill=spider_color, width=2)
        
        return ImageTk.PhotoImage(img)
    
    @staticmethod
    def create_neon_glow_border(width, height, glow_color='#FF1493'):
        """Create neon glow effect like stage lighting."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Create multiple glow layers
        for i in range(10):
            alpha = int(255 * (1 - i/10))  # Fade out
            glow_width = i * 2
            
            # Convert hex to RGB
            r = int(glow_color[1:3], 16)
            g = int(glow_color[3:5], 16)
            b = int(glow_color[5:7], 16)
            
            glow_rgba = (r, g, b, alpha)
            
            # Draw glow rectangle
            draw.rectangle([i, i, width-1-i, height-1-i],
                          outline=glow_rgba, width=1)
        
        return ImageTk.PhotoImage(img)
    
    @staticmethod
    def create_amp_border(width, height):
        """Create guitar amplifier-style border."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Main border (amp case)
        border_color = '#2F2F2F'
        highlight_color = '#C0C0C0'
        shadow_color = '#000000'
        
        # Outer border
        draw.rectangle([0, 0, width-1, height-1], 
                      outline=border_color, width=3)
        
        # Highlight (top/left)
        draw.line([0, 0, width-1, 0], fill=highlight_color, width=2)  # Top
        draw.line([0, 0, 0, height-1], fill=highlight_color, width=2)  # Left
        
        # Shadow (bottom/right)
        draw.line([0, height-1, width-1, height-1], fill=shadow_color, width=2)  # Bottom
        draw.line([width-1, 0, width-1, height-1], fill=shadow_color, width=2)  # Right
        
        # Add amp "screws" in corners
        screw_color = '#808080'
        screw_size = 4
        positions = [(8, 8), (width-16, 8), (8, height-16), (width-16, height-16)]
        
        for x, y in positions:
            draw.ellipse([x, y, x+screw_size, y+screw_size], 
                        fill=screw_color, outline='#FFFFFF', width=1)
        
        # Add pink "power" LED
        led_x, led_y = width - 30, height - 30
        draw.ellipse([led_x, led_y, led_x+6, led_y+6], 
                    fill='#FF1493', outline='#FFFFFF', width=1)
        
        return ImageTk.PhotoImage(img)

class VisualKeiFrame(tk.Frame):
    """Frame with Visual Kei styling and effects."""
    
    def __init__(self, parent, border_style="spider_web", **kwargs):
        super().__init__(parent, **kwargs)
        self.border_style = border_style
        self.border_images = {}
        
        # Canvas for effects
        self.canvas = tk.Canvas(self, highlightthickness=0, bg='#000000')
        self.canvas.pack(fill='both', expand=True)
        
        # Content frame
        self.content_frame = tk.Frame(self.canvas, bg='#000000')
        self.canvas_window = self.canvas.create_window(0, 0, 
                                                      anchor='nw',
                                                      window=self.content_frame)
        
        self.bind('<Configure>', self.on_resize)
        self.content_frame.bind('<Configure>', self.on_content_resize)
    
    def on_resize(self, event):
        """Handle resize and redraw effects."""
        width = event.width
        height = event.height
        
        self.canvas.delete('border')
        
        # Create appropriate border effect
        if self.border_style == "spider_web":
            border_img = SpiderWebBorderCreator.create_spider_web_border(width, height)
        elif self.border_style == "neon_glow":
            border_img = SpiderWebBorderCreator.create_neon_glow_border(width, height)
        elif self.border_style == "amp":
            border_img = SpiderWebBorderCreator.create_amp_border(width, height)
        
        # Draw border
        self.canvas.create_image(0, 0, anchor='nw', image=border_img, tags='border')
        self.border_images[id(self)] = border_img
        
        # Update content frame
        padding = 12
        self.canvas.coords(self.canvas_window, padding, padding)
        self.content_frame.configure(width=width-2*padding, 
                                   height=height-2*padding)
    
    def on_content_resize(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
```

## 🎤 Complete hide-Themed Dataset Tools

```python
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk

class HideDatasetTools:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dataset Tools - hide (Pink Spider) Edition")
        self.root.configure(bg='#000000')
        self.root.geometry("1000x750")
        
        # Apply hide theme
        self.theme_manager = HideThemeManager(self.root)
        self.theme_manager.apply_hide_theme()
        
        self.create_visual_kei_interface()
    
    def create_visual_kei_interface(self):
        """Create hide-inspired Visual Kei interface."""
        
        # Title section - Rock star style
        title_frame = VisualKeiFrame(self.root, border_style="neon_glow", 
                                   bg='#000000', height=100)
        title_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        # Main title
        title_label = tk.Label(title_frame.content_frame,
                              text="🕷️ DATASET TOOLS 🕷️",
                              bg='#000000', fg='#FF1493',
                              font=('Arial', 20, 'bold'))
        title_label.pack(pady=5)
        
        # Subtitle with Visual Kei flair
        subtitle_label = tk.Label(title_frame.content_frame,
                                 text="~ Pink Spider Edition ~",
                                 bg='#000000', fg='#FFDDEE',
                                 font=('Arial', 12, 'italic'))
        subtitle_label.pack()
        
        # Quote from hide
        quote_label = tk.Label(title_frame.content_frame,
                              text='"Tell me what you think about me..."',
                              bg='#000000', fg='#FF69B4',
                              font=('Arial', 10))
        quote_label.pack()
        
        # Control panel - Like a guitar effects rack
        control_frame = VisualKeiFrame(self.root, border_style="amp", 
                                     bg='#000000', height=100)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Control buttons styled like amp controls
        button_frame = tk.Frame(control_frame.content_frame, bg='#000000')
        button_frame.pack(expand=True)
        
        hide_controls = [
            ("🎸 LOAD", "Load files (Rocket Dive!)"),
            ("🔊 PROCESS", "Process metadata (Pink Spider!)"),
            ("💿 EXPORT", "Export results (Lemoned I Scream!)"),
            ("⚙️ SETTINGS", "Configure (Pose Dead!)"),
            ("🎭 THEME", "Change theme (Visual Shock!)")
        ]
        
        for i, (text, tooltip) in enumerate(hide_controls):
            btn = tk.Button(button_frame, text=text,
                           bg='#FF1493', fg='#FFFFFF',
                           activebackground='#FF69B4', 
                           activeforeground='#000000',
                           font=('Arial', 10, 'bold'),
                           relief='raised', bd=3,
                           width=14, height=2)
            btn.grid(row=0, column=i, padx=4, pady=4)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg='#000000')
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left panel - File list (like a setlist)
        left_panel = VisualKeiFrame(content_frame, border_style="spider_web", 
                                  bg='#000000', width=350)
        left_panel.pack(side='left', fill='y', padx=(0, 5))
        
        list_title = tk.Label(left_panel.content_frame,
                             text="🎵 SETLIST (Files)",
                             bg='#000000', fg='#FF1493',
                             font=('Arial', 14, 'bold'))
        list_title.pack(pady=(8, 12))
        
        # File listbox with Visual Kei styling
        list_frame = tk.Frame(left_panel.content_frame, bg='#000000')
        list_frame.pack(fill='both', expand=True, padx=8, pady=8)
        
        file_listbox = tk.Listbox(list_frame,
                                 bg='#1C1C1C', fg='#FFFFFF',
                                 selectbackground='#FF1493',
                                 selectforeground='#FFFFFF',
                                 font=('Arial', 9, 'bold'),
                                 relief='solid', bd=2)
        file_listbox.pack(side='left', fill='both', expand=True)
        
        # Add sample files with hide song references
        sample_files = [
            "🎸 rocket_dive.jpg",
            "🕷️ pink_spider.png",
            "💀 pose_dead.gif", 
            "🍋 lemoned_i_scream.jpg",
            "✨ ever_free.png",
            "🎭 visual_shock.jpg",
            "🌸 beauty_and_stupid.png",
            "📜 metadata.txt",
            "⚙️ config.json"
        ]
        for file in sample_files:
            file_listbox.insert('end', file)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame, orient='vertical',
                                command=file_listbox.yview,
                                bg='#FF1493', activebackground='#FF69B4')
        scrollbar.pack(side='right', fill='y')
        file_listbox.config(yscrollcommand=scrollbar.set)
        
        # Right panel - Metadata display (like lyrics sheet)
        right_panel = VisualKeiFrame(content_frame, border_style="neon_glow", 
                                   bg='#000000')
        right_panel.pack(side='right', fill='both', expand=True)
        
        preview_title = tk.Label(right_panel.content_frame,
                                text="📝 METADATA & PREVIEW",
                                bg='#000000', fg='#FF1493',
                                font=('Arial', 14, 'bold'))
        preview_title.pack(pady=(8, 12))
        
        # Text area for metadata
        text_frame = tk.Frame(right_panel.content_frame, bg='#000000')
        text_frame.pack(fill='both', expand=True, padx=8, pady=8)
        
        metadata_text = tk.Text(text_frame,
                               bg='#1C1C1C', fg='#FFDDEE',
                               font=('Consolas', 10),
                               relief='solid', bd=2,
                               selectbackground='#FF69B4',
                               selectforeground='#000000')
        metadata_text.pack(side='left', fill='both', expand=True)
        
        # Sample metadata with hide references
        sample_metadata = """🕷️ PINK SPIDER METADATA ANALYSIS 🕷️

📝 File: rocket_dive.jpg
📏 Resolution: 1024x768 (Visual Kei Standard)
🎨 Format: JPEG
📅 Created: 1998-05-02 (hide's Birthday!)
🎸 Quality: Legendary (hide-level)

🔮 Generation Parameters:
  Prompt: "hide playing guitar, pink hair, stage lights"
  Model: "VisualKei_v2.0"
  Steps: 20 (like Rocket Dive tempo)
  CFG: 7.5
  Seed: 19641213 (hide's birthday)
  Style: "Visual Shock, Pink Spider aesthetic"

🎭 Visual Kei Tags:
  - Pink hair ✨
  - Guitar solo pose 🎸
  - Stage makeup 💄
  - Leather outfit 🖤
  - Neon lighting 💖

🎵 Song Reference: "Rocket Dive"
🕷️ Spider Level: Maximum Pink
⚡ Visual Impact: Legendary

"Tell me what you think about me
I can be anything you want me to be..."

💀 Status: Forever in our hearts (1964-1998)"""
        
        metadata_text.insert('1.0', sample_metadata)
        
        # Status bar - Like amp display
        status_frame = VisualKeiFrame(self.root, border_style="amp", 
                                    bg='#000000', height=50)
        status_frame.pack(fill='x', padx=10, pady=(5, 10))
        
        status_left = tk.Label(status_frame.content_frame,
                              text="🎸 Files: 1998  🕷️ Processed: 666",
                              bg='#000000', fg='#FFFFFF',
                              font=('Arial', 10, 'bold'))
        status_left.pack(side='left', padx=8, pady=8)
        
        # Power indicator (like amp power LED)
        power_frame = tk.Frame(status_frame.content_frame, bg='#000000')
        power_frame.pack(side='right', padx=8, pady=8)
        
        power_label = tk.Label(power_frame, text="POWER:", 
                              bg='#000000', fg='#FFFFFF',
                              font=('Arial', 9, 'bold'))
        power_label.pack(side='left')
        
        power_led = tk.Label(power_frame, text="●", 
                            bg='#000000', fg='#FF1493',
                            font=('Arial', 16))
        power_led.pack(side='left', padx=4)
        
        status_right = tk.Label(status_frame.content_frame,
                               text="🎭 Mode: Visual Shock",
                               bg='#000000', fg='#FF69B4',
                               font=('Arial', 10, 'bold'))
        status_right.pack(side='right', padx=8, pady=8)
    
    def run(self):
        self.root.mainloop()

# Run the hide-themed app
if __name__ == "__main__":
    app = HideDatasetTools()
    app.run()
```

## 🎸 Additional Visual Kei Features

### **Animated Effects**
```python
class PinkSpiderAnimation:
    """Add animated effects worthy of hide."""
    
    def __init__(self, widget):
        self.widget = widget
        self.colors = ['#FF1493', '#FF69B4', '#FF00FF', '#C71585']
        self.current_color = 0
        
    def start_neon_pulse(self):
        """Create pulsing neon effect."""
        self.widget.configure(fg=self.colors[self.current_color])
        self.current_color = (self.current_color + 1) % len(self.colors)
        self.widget.after(500, self.start_neon_pulse)
```

There you go! 🕷️💖 A complete theme worthy of the Pink Spider himself!

**Features:**
- **Signature pink/black color scheme** from hide's iconic look
- **Spider web border patterns** (Pink Spider reference!)
- **Guitar amp-styled controls** and borders
- **Neon glow effects** like stage lighting
- **Sample content** with hide song references
- **Visual Kei aesthetic** throughout

Your dataset tool will look like it belongs backstage at an X JAPAN concert! RIP hide, forever the Pink Spider! 🎸✨