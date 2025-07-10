# Classic Firefox Theme Guide: Bringing Back the 2004 Vibes

## 🦊 Classic Firefox Color Palette

### **Original Firefox Colors (2004-2010 era)**
```python
# The EXACT classic Firefox colors
FIREFOX_COLORS = {
    # Main UI Colors
    'window_background': '#ECE7D4',      # That warm beige background
    'toolbar_background': '#DFDBD2',     # Slightly darker toolbar
    'toolbar_border': '#919B9C',        # Gray border around toolbars
    
    # Button Colors  
    'button_normal': '#F0F0F0',          # Default button face
    'button_hover': '#E0E8F8',           # Light blue hover
    'button_pressed': '#C7D2EA',         # Pressed button blue
    'button_border': '#8595A6',          # Button border gray
    
    # Active/Selected Colors
    'selected_blue': '#3875D7',          # Classic Firefox blue
    'selected_light': '#E0E8F8',         # Light selection blue  
    'active_orange': '#FF6600',          # Firefox orange accent
    
    # Text Colors
    'text_primary': '#000000',           # Main text
    'text_secondary': '#333333',         # Secondary text
    'text_disabled': '#808080',          # Disabled text
    'text_link': '#0000EE',              # Classic blue links
    
    # Status Colors
    'status_bar': '#F7F7F7',             # Status bar background
    'border_dark': '#8595A6',            # Dark borders
    'border_light': '#FFFFFF',           # Light borders (highlights)
    
    # Menu Colors
    'menu_background': '#F7F7F7',        # Menu background
    'menu_hover': '#E0E8F8',             # Menu item hover
    'menu_separator': '#D7D7D7',         # Menu separators
}
```

### **Firefox Theme Gradients**
```python
# Classic Firefox used subtle gradients everywhere
FIREFOX_GRADIENTS = {
    'toolbar_gradient': ['#DFDBD2', '#ECE7D4'],        # Top to bottom
    'button_gradient': ['#F8F8F8', '#E8E8E8'],         # Button face
    'button_hover_gradient': ['#F0F6FF', '#D0E0F8'],   # Hover state
    'selected_gradient': ['#4A8BEA', '#2E6BC7'],       # Selected items
    'status_gradient': ['#F7F7F7', '#ECECEC'],         # Status bar
}
```

## 🎨 Complete Firefox Theme Implementation

### **Qt Stylesheet Version**
```css
/* Classic Firefox Theme for Qt */

/* Main window */
QMainWindow {
    background-color: #ECE7D4;
    color: #000000;
}

/* Toolbar styling */
QToolBar {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #DFDBD2, stop: 1 #ECE7D4);
    border: 1px solid #919B9C;
    border-radius: 0px;
    spacing: 3px;
    padding: 2px;
}

/* Classic Firefox buttons */
QPushButton {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #F8F8F8, stop: 1 #E8E8E8);
    border: 1px solid #8595A6;
    border-radius: 3px;
    padding: 4px 12px;
    color: #000000;
    font-size: 11pt;
}

QPushButton:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #F0F6FF, stop: 1 #D0E0F8);
    border: 1px solid #3875D7;
}

QPushButton:pressed {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #C7D2EA, stop: 1 #B5C7E3);
    border: 1px solid #2E6BC7;
}

/* Menu bar */
QMenuBar {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #DFDBD2, stop: 1 #ECE7D4);
    border-bottom: 1px solid #919B9C;
    color: #000000;
}

QMenuBar::item {
    background: transparent;
    padding: 4px 8px;
}

QMenuBar::item:selected {
    background: #E0E8F8;
    border: 1px solid #8595A6;
    border-radius: 2px;
}

/* Menus */
QMenu {
    background-color: #F7F7F7;
    border: 1px solid #8595A6;
    padding: 2px;
}

QMenu::item {
    padding: 4px 20px;
    color: #000000;
}

QMenu::item:selected {
    background-color: #E0E8F8;
    color: #000000;
}

/* Status bar */
QStatusBar {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #F7F7F7, stop: 1 #ECECEC);
    border-top: 1px solid #D7D7D7;
    color: #333333;
}

/* Text areas */
QTextEdit, QPlainTextEdit {
    background-color: #FFFFFF;
    border: 2px inset #8595A6;
    color: #000000;
    font-family: "Segoe UI", Arial, sans-serif;
}

/* List widgets */
QListWidget {
    background-color: #FFFFFF;
    border: 2px inset #8595A6;
    color: #000000;
    alternate-background-color: #F7F7F7;
}

QListWidget::item:selected {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #4A8BEA, stop: 1 #2E6BC7);
    color: #FFFFFF;
}
```

### **Tkinter Version**
```python
def apply_firefox_classic_theme(self):
    """Apply classic Firefox theme to Tkinter."""
    
    # Firefox color palette
    bg_main = '#ECE7D4'
    bg_toolbar = '#DFDBD2' 
    button_normal = '#F0F0F0'
    button_hover = '#E0E8F8'
    selected_blue = '#3875D7'
    border_color = '#8595A6'
    text_color = '#000000'
    
    self.root.configure(bg=bg_main)
    
    # Configure ttk styles
    self.style.theme_use('clam')
    
    # Firefox-style buttons
    self.style.configure('Firefox.TButton',
                        background=button_normal,
                        foreground=text_color,
                        borderwidth=1,
                        relief='raised',
                        padding=(12, 4),
                        font=('Segoe UI', 9))
    
    self.style.map('Firefox.TButton',
                  background=[('active', button_hover),
                            ('pressed', '#C7D2EA')],
                  bordercolor=[('active', selected_blue)])
    
    # Firefox-style labels
    self.style.configure('Firefox.TLabel',
                        background=bg_main,
                        foreground=text_color,
                        font=('Segoe UI', 9))
    
    # Firefox-style frames
    self.style.configure('Firefox.TFrame',
                        background=bg_main,
                        borderwidth=1,
                        relief='solid')
    
    # Configure tk widgets
    self.root.option_add('*Button.Background', button_normal)
    self.root.option_add('*Button.Foreground', text_color)
    self.root.option_add('*Button.ActiveBackground', button_hover)
    self.root.option_add('*Button.Relief', 'raised')
    self.root.option_add('*Button.BorderWidth', '1')
    
    self.root.option_add('*Text.Background', '#FFFFFF')
    self.root.option_add('*Text.Foreground', text_color)
    self.root.option_add('*Text.Relief', 'sunken')
    self.root.option_add('*Text.BorderWidth', '2')
    
    self.root.option_add('*Listbox.Background', '#FFFFFF')
    self.root.option_add('*Listbox.SelectBackground', selected_blue)
    self.root.option_add('*Listbox.SelectForeground', '#FFFFFF')
```

## 🖼️ Image-Based Borders & Grooves

### **Creating Border Images**
```python
# Method 1: Using PIL to create border patterns
from PIL import Image, ImageDraw, ImageTk

class BorderImageCreator:
    @staticmethod
    def create_inset_border(width, height, border_width=2):
        """Create an inset/groove border image."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Outer dark border (shadow)
        draw.rectangle([0, 0, width-1, height-1], 
                      outline='#808080', width=border_width)
        
        # Inner light border (highlight)
        draw.rectangle([border_width, border_width, 
                       width-1-border_width, height-1-border_width], 
                      outline='#FFFFFF', width=1)
        
        return ImageTk.PhotoImage(img)
    
    @staticmethod
    def create_raised_border(width, height, border_width=2):
        """Create a raised/button-like border."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Top/left highlight
        draw.line([0, 0, width-1, 0], fill='#FFFFFF', width=border_width)  # Top
        draw.line([0, 0, 0, height-1], fill='#FFFFFF', width=border_width)  # Left
        
        # Bottom/right shadow  
        draw.line([0, height-1, width-1, height-1], fill='#808080', width=border_width)  # Bottom
        draw.line([width-1, 0, width-1, height-1], fill='#808080', width=border_width)  # Right
        
        return ImageTk.PhotoImage(img)
    
    @staticmethod
    def create_firefox_border(width, height):
        """Create Firefox-style border with gradients."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Firefox border colors
        border_dark = '#8595A6'
        border_light = '#FFFFFF'
        
        # Outer border
        draw.rectangle([0, 0, width-1, height-1], outline=border_dark, width=1)
        
        # Inner highlight (top/left)
        draw.line([1, 1, width-2, 1], fill=border_light, width=1)  # Top
        draw.line([1, 1, 1, height-2], fill=border_light, width=1)  # Left
        
        return ImageTk.PhotoImage(img)
```

### **Using Border Images in Tkinter**
```python
class BorderedFrame(tk.Frame):
    """Frame with custom image-based borders."""
    
    def __init__(self, parent, border_style="inset", **kwargs):
        super().__init__(parent, **kwargs)
        self.border_style = border_style
        self.border_images = {}
        
        # Create canvas for border drawing
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Content frame inside canvas
        self.content_frame = tk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(0, 0, 
                                                      anchor='nw', 
                                                      window=self.content_frame)
        
        self.bind('<Configure>', self.on_resize)
        self.content_frame.bind('<Configure>', self.on_content_resize)
    
    def on_resize(self, event):
        """Handle frame resize and redraw borders."""
        width = event.width
        height = event.height
        
        # Clear previous border
        self.canvas.delete('border')
        
        # Create new border image
        if self.border_style == "inset":
            border_img = BorderImageCreator.create_inset_border(width, height)
        elif self.border_style == "raised":
            border_img = BorderImageCreator.create_raised_border(width, height)
        elif self.border_style == "firefox":
            border_img = BorderImageCreator.create_firefox_border(width, height)
        
        # Draw border
        self.canvas.create_image(0, 0, anchor='nw', image=border_img, tags='border')
        self.border_images[id(self)] = border_img  # Keep reference
        
        # Update content frame size
        padding = 4
        self.canvas.coords(self.canvas_window, padding, padding)
        self.content_frame.configure(width=width-2*padding, 
                                   height=height-2*padding)
    
    def on_content_resize(self, event):
        """Update scroll region when content changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

# Usage example:
class FirefoxStyledApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Firefox Classic Theme")
        self.root.configure(bg='#ECE7D4')
        
        # Main content with Firefox-style border
        main_frame = BorderedFrame(self.root, border_style="firefox", 
                                 bg='#ECE7D4', width=600, height=400)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add content to the bordered frame
        title = tk.Label(main_frame.content_frame, 
                        text="Classic Firefox Style", 
                        bg='#ECE7D4', fg='#000000',
                        font=('Segoe UI', 14, 'bold'))
        title.pack(pady=10)
        
        # Toolbar-style frame
        toolbar = BorderedFrame(main_frame.content_frame, 
                               border_style="raised", 
                               bg='#DFDBD2', height=40)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        # Add toolbar buttons
        btn1 = tk.Button(toolbar.content_frame, text="File", 
                        bg='#F0F0F0', relief='raised', bd=1)
        btn1.pack(side='left', padx=2, pady=2)
        
        btn2 = tk.Button(toolbar.content_frame, text="Edit", 
                        bg='#F0F0F0', relief='raised', bd=1)
        btn2.pack(side='left', padx=2, pady=2)
        
        # Content area with inset border
        content_area = BorderedFrame(main_frame.content_frame, 
                                   border_style="inset", 
                                   bg='#FFFFFF', height=200)
        content_area.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Add some content
        text_widget = tk.Text(content_area.content_frame, 
                             bg='#FFFFFF', relief='flat', bd=0)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', "This is a Firefox-styled text area with custom borders!")
```

### **Advanced Border Techniques**
```python
class GradientBorder:
    """Create borders with gradient effects."""
    
    @staticmethod
    def create_gradient_border(width, height, colors=['#8595A6', '#FFFFFF']):
        """Create a gradient border."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # Create gradient effect
        for i in range(min(width, height) // 2):
            # Calculate color interpolation
            ratio = i / (min(width, height) // 2)
            
            # Interpolate between colors
            r1, g1, b1 = [int(colors[0][j:j+2], 16) for j in [1, 3, 5]]
            r2, g2, b2 = [int(colors[1][j:j+2], 16) for j in [1, 3, 5]]
            
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)  
            b = int(b1 + (b2 - b1) * ratio)
            
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            # Draw border ring
            draw = ImageDraw.Draw(img)
            draw.rectangle([i, i, width-1-i, height-1-i], 
                          outline=color, width=1)
        
        return ImageTk.PhotoImage(img)

class TexturedBorder:
    """Create textured/patterned borders."""
    
    @staticmethod
    def create_dotted_border(width, height, dot_size=2, spacing=4):
        """Create a dotted border pattern."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Top border dots
        for x in range(0, width, spacing):
            draw.ellipse([x, 0, x+dot_size, dot_size], fill='#8595A6')
        
        # Bottom border dots  
        for x in range(0, width, spacing):
            draw.ellipse([x, height-dot_size, x+dot_size, height], fill='#8595A6')
        
        # Left border dots
        for y in range(0, height, spacing):
            draw.ellipse([0, y, dot_size, y+dot_size], fill='#8595A6')
        
        # Right border dots
        for y in range(0, height, spacing):
            draw.ellipse([width-dot_size, y, width, y+dot_size], fill='#8595A6')
        
        return ImageTk.PhotoImage(img)
```

## 🎯 Complete Firefox Theme Example

```python
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk

class ClassicFirefoxApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dataset Tools - Firefox Classic Edition")
        self.root.configure(bg='#ECE7D4')
        self.root.geometry("800x600")
        
        self.setup_firefox_theme()
        self.create_interface()
    
    def setup_firefox_theme(self):
        """Apply complete Firefox classic theme."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure all the Firefox styles...
        # (Use the code from above)
    
    def create_interface(self):
        """Create Firefox-styled interface."""
        
        # Menu bar
        menubar = tk.Menu(self.root, bg='#DFDBD2', relief='raised', bd=1)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0, bg='#F7F7F7')
        file_menu.add_command(label="Open Folder")
        file_menu.add_command(label="Settings")
        file_menu.add_separator()
        file_menu.add_command(label="Exit")
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Main container with Firefox border
        main_frame = BorderedFrame(self.root, border_style="firefox", 
                                 bg='#ECE7D4')
        main_frame.pack(fill='both', expand=True, padx=8, pady=8)
        
        # Toolbar
        toolbar = BorderedFrame(main_frame.content_frame, 
                               border_style="raised", 
                               bg='#DFDBD2', height=35)
        toolbar.pack(fill='x', padx=4, pady=4)
        
        # Add Firefox-style toolbar buttons
        firefox_buttons = ["Open", "Process", "Export", "Help"]
        for btn_text in firefox_buttons:
            btn = tk.Button(toolbar.content_frame, text=btn_text,
                           bg='#F0F0F0', relief='raised', bd=1,
                           font=('Segoe UI', 8))
            btn.pack(side='left', padx=2, pady=2)
        
        # Content area split
        content_frame = tk.Frame(main_frame.content_frame, bg='#ECE7D4')
        content_frame.pack(fill='both', expand=True, padx=4, pady=4)
        
        # Left panel (file list)
        left_panel = BorderedFrame(content_frame, border_style="inset", 
                                 bg='#FFFFFF', width=250)
        left_panel.pack(side='left', fill='y', padx=(0, 4))
        
        list_label = tk.Label(left_panel.content_frame, text="Files:",
                             bg='#FFFFFF', font=('Segoe UI', 9, 'bold'))
        list_label.pack(anchor='w', padx=2, pady=2)
        
        file_listbox = tk.Listbox(left_panel.content_frame, 
                                 bg='#FFFFFF', relief='flat', bd=0,
                                 selectbackground='#3875D7',
                                 selectforeground='#FFFFFF')
        file_listbox.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Add sample files
        sample_files = [
            "image001.jpg", "image002.png", "image003.gif",
            "metadata.txt", "config.json"
        ]
        for file in sample_files:
            file_listbox.insert('end', file)
        
        # Right panel (preview/metadata)
        right_panel = BorderedFrame(content_frame, border_style="inset", 
                                  bg='#FFFFFF')
        right_panel.pack(side='right', fill='both', expand=True)
        
        preview_label = tk.Label(right_panel.content_frame, 
                                text="Image Preview & Metadata",
                                bg='#FFFFFF', font=('Segoe UI', 9, 'bold'))
        preview_label.pack(anchor='w', padx=2, pady=2)
        
        # Status bar
        status_frame = BorderedFrame(self.root, border_style="raised", 
                                   bg='#F7F7F7', height=25)
        status_frame.pack(fill='x', side='bottom')
        
        status_label = tk.Label(status_frame.content_frame, 
                               text="Ready - Firefox Classic Theme Active",
                               bg='#F7F7F7', font=('Segoe UI', 8))
        status_label.pack(side='left', padx=4, pady=2)
    
    def run(self):
        self.root.mainloop()

# Run the Firefox-themed app
if __name__ == "__main__":
    app = ClassicFirefoxApp()
    app.run()
```

There you go! 🦊 Complete Firefox classic theme with:
- **Exact color palette** from 2004-era Firefox
- **Image-based borders** with inset/raised/gradient effects  
- **Custom border classes** for maximum nostalgia
- **Complete implementation** ready to use

Your dataset tool will look like it belongs in the golden age of Firefox! 🔥✨