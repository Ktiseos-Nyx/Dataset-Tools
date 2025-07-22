# Tkinter + ttkbootstrap Migration Plan
*Strategic migration from PyQt6 to modern Tkinter*

## 🎯 Why Migrate to Tkinter + ttkbootstrap?

### Current PyQt6 Pain Points
- ❌ qt-material theme compatibility issues
- ❌ Complex threading model with signals/slots
- ❌ Heavy dependency footprint
- ❌ PyQt6 licensing considerations for distribution
- ❌ Cross-platform styling inconsistencies

### ttkbootstrap Advantages  
- ✅ **20+ gorgeous modern themes** out of the box
- ✅ **Bootstrap-inspired design** - looks professional
- ✅ **Zero additional dependencies** (pure Python/Tkinter)
- ✅ **Lightweight & performant** (beats Qt in benchmarks)
- ✅ **Simple threading** (you've proven this works in plural-chat!)
- ✅ **Built-in theme creator** for custom themes
- ✅ **Cross-platform consistency** 

## 🏗️ Architecture Analysis

### Current PyQt6 Structure
```
MainWindow (1,156 lines)
├── MenuManager
├── LayoutManager  
├── MetadataDisplayManager
├── ThemeManager (qt-material)
├── ImageLoaderWorker (threading)
└── FileLoader (QThread)
```

### Proposed Tkinter Structure
```
MainApp (ttkbootstrap.Window)
├── MenuFrame
├── FileManagerFrame
├── MetadataDisplayFrame
├── ImagePreviewFrame
├── ThemeSelector (ttkbootstrap themes)
└── BackgroundWorker (threading.Thread + queue)
```

## 📋 Migration Phases

### Phase 1: Foundation (Week 1-2)
**Goal**: Basic UI structure with ttkbootstrap

```python
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class DatasetViewerApp:
    def __init__(self):
        self.root = ttk.Window(themename="superhero")
        self.setup_layout()
        self.setup_theme_selector()
    
    def setup_layout(self):
        # Left panel: File list
        self.file_frame = ttk.LabelFrame(self.root, text="Files")
        self.file_listbox = ttk.Treeview(self.file_frame)
        
        # Right panel: Metadata display  
        self.metadata_frame = ttk.LabelFrame(self.root, text="Metadata")
        self.metadata_text = ttk.ScrolledText(self.metadata_frame)
        
        # Bottom: Image preview
        self.image_frame = ttk.LabelFrame(self.root, text="Preview")
        self.image_label = ttk.Label(self.image_frame)
```

**Deliverables**:
- [ ] Basic window layout with ttkbootstrap
- [ ] Theme selector dropdown (20+ themes)
- [ ] File list widget (Treeview)
- [ ] Metadata display area (ScrolledText)
- [ ] Image preview area (Label)

### Phase 2: File Management (Week 3)
**Goal**: Port file loading and navigation

```python
import threading
import queue
from pathlib import Path

class FileManager:
    def __init__(self, app):
        self.app = app
        self.file_queue = queue.Queue()
        self.setup_background_worker()
    
    def setup_background_worker(self):
        # Use proven pattern from plural-chat
        self.worker_thread = threading.Thread(target=self.background_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        # Check queue periodically (thread-safe!)
        self.app.root.after(100, self.check_queue)
    
    def background_worker(self):
        # File loading happens here, safely
        pass
        
    def check_queue(self):
        # Process results on main thread
        try:
            result = self.file_queue.get_nowait()
            self.update_ui(result)
        except queue.Empty:
            pass
        self.app.root.after(100, self.check_queue)
```

**Deliverables**:
- [ ] Thread-safe file loading (using plural-chat patterns)
- [ ] Drag & drop support
- [ ] File filtering by type
- [ ] Folder navigation

### Phase 3: Metadata Engine Integration (Week 4)  
**Goal**: Connect existing metadata parsing

```python
from dataset_tools.metadata_parser import parse_metadata

class MetadataDisplay:
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="Metadata")
        
        # Create tabbed view for different metadata sections
        self.notebook = ttk.Notebook(self.frame)
        
        # Prompt tab
        self.prompt_frame = ttk.Frame(self.notebook)
        self.positive_text = ttk.ScrolledText(self.prompt_frame, height=6)
        self.negative_text = ttk.ScrolledText(self.prompt_frame, height=4)
        
        # Details tab  
        self.details_frame = ttk.Frame(self.notebook)
        self.details_text = ttk.ScrolledText(self.details_frame)
        
        self.notebook.add(self.prompt_frame, text="Prompts")
        self.notebook.add(self.details_frame, text="Details")
    
    def display_metadata(self, file_path):
        # Reuse existing metadata parsing!
        metadata = parse_metadata(file_path)
        self.update_displays(metadata)
```

**Deliverables**:
- [ ] Tabbed metadata display (Prompts, Details, Raw)
- [ ] Integration with existing metadata_parser
- [ ] Copy to clipboard functionality  
- [ ] Search/filter within metadata

### Phase 4: Image Handling (Week 5)
**Goal**: Background image loading with threading

```python
from PIL import Image, ImageTk
import threading

class ImagePreview:
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="Preview")
        self.image_label = ttk.Label(self.frame, text="No image selected")
        self.loading_label = ttk.Label(self.frame, text="Loading...", foreground="gray")
        
    def load_image_threaded(self, file_path):
        # Show loading indicator
        self.loading_label.pack()
        
        # Load in background thread (using plural-chat pattern)
        threading.Thread(
            target=self._load_image_worker,
            args=(file_path,),
            daemon=True
        ).start()
        
    def _load_image_worker(self, file_path):
        try:
            # Load and resize image
            image = Image.open(file_path)
            image.thumbnail((800, 600), Image.Resampling.LANCZOS)
            
            # Convert to Tkinter format
            photo = ImageTk.PhotoImage(image)
            
            # Queue update for main thread
            self.app.image_queue.put(('success', photo))
        except Exception as e:
            self.app.image_queue.put(('error', str(e)))
```

**Deliverables**:
- [ ] Background image loading
- [ ] Image thumbnail generation
- [ ] Loading indicators
- [ ] Error handling for corrupted images

### Phase 5: Advanced Features (Week 6)
**Goal**: Feature parity with PyQt6 version

```python
class AdvancedFeatures:
    def setup_advanced_widgets(self):
        # Settings dialog using ttkbootstrap
        self.settings_dialog = ttk.Toplevel()
        
        # Modern progress indicators
        self.progress_bar = ttk.Progressbar(
            self.root, 
            bootstyle="success-striped"
        )
        
        # Status bar with modern styling
        self.status_frame = ttk.Frame(self.root)
        self.status_label = ttk.Label(
            self.status_frame, 
            text="Ready",
            bootstyle="secondary"
        )
        
        # Theme switching with style
        self.theme_selector = ttk.Combobox(
            self.toolbar,
            values=ttk.Style().theme_names(),
            bootstyle="info"
        )
```

**Deliverables**:
- [ ] Settings dialog with theme selection
- [ ] Modern progress indicators  
- [ ] Status bar with styling
- [ ] Keyboard shortcuts
- [ ] About dialog

## 🎨 ttkbootstrap Theme Showcase

### Available Themes (20+)
- **Dark themes**: `darkly`, `superhero`, `cyborg`, `vapor`
- **Light themes**: `flatly`, `litera`, `minty`, `pulse`  
- **Colorful**: `journal`, `sandstone`, `yeti`, `united`
- **Professional**: `cosmo`, `lumen`, `simplex`

### Custom Theme Creation
```python
# Built-in theme creator
import subprocess
subprocess.run(['python', '-m', 'ttkcreator'])

# Or programmatic theme creation
from ttkbootstrap import Style
style = Style()
style.theme_create("dataset_viewer_custom", 
    parent="flatly",
    settings={
        "TLabel": {"configure": {"foreground": "#2c3e50"}},
        "TButton": {"configure": {"relief": "flat"}}
    }
)
```

## 🧵 Threading Strategy (Proven Pattern)

Based on your plural-chat success, use the queue pattern:

```python
import queue
import threading

class ThreadSafeApp:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.setup_workers()
        
    def setup_workers(self):
        # Background worker thread
        self.worker = threading.Thread(target=self.worker_loop, daemon=True)
        self.worker.start()
        
        # UI update checker (main thread)
        self.root.after(50, self.check_results)
        
    def worker_loop(self):
        while True:
            task = self.task_queue.get()
            if task is None:
                break
                
            # Do work safely in background
            result = self.process_task(task)
            self.result_queue.put(result)
            
    def check_results(self):
        try:
            while True:
                result = self.result_queue.get_nowait()
                self.update_ui_safely(result)
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self.check_results)
```

## 📦 Dependencies Comparison

### Current (PyQt6)
```toml
dependencies = [
    "PyQt6",           # ~50MB download
    "qt-material",     # Theme compatibility issues
    "pillow",
    # ... other deps
]
```

### Proposed (Tkinter + ttkbootstrap)
```toml
dependencies = [
    "ttkbootstrap",    # ~500KB, pure Python  
    "pillow",
    # ... same other deps, but no Qt!
]
```

**Bundle size reduction**: ~45-50MB smaller!

## 🚀 Migration Timeline

| Week | Phase | Focus | Deliverable |
|------|-------|-------|-------------|
| 1-2  | Foundation | Basic UI | Working ttkbootstrap app |
| 3    | File Management | Threading | File loading with themes |
| 4    | Metadata | Integration | Metadata display working |
| 5    | Images | Preview | Image loading complete |
| 6    | Polish | Features | Feature parity achieved |

## 🎯 Success Metrics

### Before (PyQt6)
- ❌ Theme compatibility issues
- ❌ 1,156-line monolithic main window
- ❌ Complex signal/slot threading
- ❌ ~50MB dependency footprint

### After (Tkinter + ttkbootstrap)  
- ✅ 20+ modern themes, zero compatibility issues
- ✅ Modular, maintainable architecture
- ✅ Simple, proven threading model
- ✅ Lightweight, fast startup

## 🛠️ Development Tools

### Theme Development
```bash
# Launch theme creator
python -m ttkcreator

# Preview all themes
python -c "
import ttkbootstrap as ttk
for theme in ttk.Style().theme_names():
    print(f'Theme: {theme}')
"
```

### Testing Strategy
1. **Parallel development**: Keep PyQt6 version working during migration
2. **Feature parity checklist**: Ensure all functionality is preserved
3. **Performance testing**: Compare startup times and memory usage
4. **Cross-platform testing**: Test themes on Windows/macOS/Linux

## 🏁 Conclusion

This migration plan leverages your proven threading expertise from plural-chat and addresses the core PyQt6 pain points. ttkbootstrap provides the *chef's kiss* modern UI you want, with the threading simplicity you've already mastered.

**Next steps**:
1. **Prototype Phase 1** (basic layout) to validate approach
2. **Document current PyQt6 functionality** to ensure nothing is missed  
3. **Set up parallel development environment**
4. **Begin migration with confidence!** 🚀

The result will be a more maintainable, better-looking, and lighter-weight Dataset Tools that users will love!