# Plugin Architecture Roadmap
**"Install Only What You Need" - Modular App Suite**

**Status:** Vision / Future Planning
**Priority:** Low (Learn & Experiment Phase)
**Timeline:** Long-term (6-12+ months)
**Difficulty:** Advanced (but totally doable!)

---

## 🎯 The Dream

Transform Dataset Tools from a standalone app into a **modular suite** where users can:

1. **Install minimal core** (~50MB, basic features only)
2. **Choose which features to add** (like VS Code extensions)
3. **Install dependencies on-demand** (only download what you need)
4. **Integrate your other PyQt6 apps** as plugins
5. **Share data between plugins** (current image, theme, etc.)

### **Why This Is Awesome:**

- ✅ **Users save disk space** - Don't force everyone to install CUDA/Torch if they don't need it
- ✅ **Faster installation** - Core app installs in seconds
- ✅ **Flexible** - Power users get everything, casual users stay lightweight
- ✅ **Your apps work together** - Theme Designer + Tagger + HuggingFace tools all integrated
- ✅ **Future-proof** - Easy to add new features without bloating core

---

## 📦 Your App Ecosystem

### **Apps You Have:**

1. **Dataset Tools** (this one) - Metadata viewer/image browser
2. **Theme Designer** (QSS App) - Create and edit Qt themes
3. **HuggingFace Desktop Tool** - Upload/download datasets
4. **Image Tagger (Google Gemini)** - AI-powered tagging via API
5. **Image Tagger (ONNX)** - Local GPU-based tagging (future)

### **The Vision:**

```
┌────────────────────────────────────────────────────┐
│         Dataset Tools (Main Hub)                   │
│  ┌──────────────┐  ┌──────────────┐                │
│  │  Metadata    │  │  Image       │                │
│  │  Viewer      │  │  Preview     │                │
│  └──────────────┘  └──────────────┘                │
│                                                    │
│  Plugins (Optional - User Chooses):                │
│  ┌────────────────────────────────────────────┐   │
│  │ ☑ Theme Designer                           │   │
│  │   └─ Design themes while viewing images    │   │
│  │                                            │   │
│  │ ☑ Image Tagger (Gemini API)                │   │
│  │   └─ Tag images with AI (cloud)           │   │
│  │                                            │   │
│  │ ☐ Image Tagger (ONNX Local)                │   │
│  │   └─ Tag images with GPU (requires CUDA)  │   │
│  │                                            │   │
│  │ ☑ HuggingFace Tools                        │   │
│  │   └─ Upload/download datasets              │   │
│  └────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────┘

All plugins share:
- Current image being viewed
- Active theme
- File paths and metadata
- Configuration settings
```

---

## 🏗️ Architecture Overview

### **Three-Layer System:**

```
┌─────────────────────────────────────────┐
│  Layer 1: Core (Always Installed)      │
│  • Metadata viewer                      │
│  • Image preview                        │
│  • Plugin system                        │
│  • Event bus (plugin communication)     │
│  • Minimal dependencies (PyQt6, Pillow) │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  Layer 2: Plugin Registry               │
│  • Discovers available plugins          │
│  • Checks system requirements           │
│  • Manages installation                 │
│  • Handles enable/disable               │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  Layer 3: Plugins (Optional)            │
│  • Self-contained modules               │
│  • Own dependencies                     │
│  • Own UI (panels/windows)              │
│  • Subscribe to events                  │
└─────────────────────────────────────────┘
```

---

## 📁 File Structure

```
dataset_tools/
├── core/                          # Core functionality (always installed)
│   ├── __init__.py
│   ├── metadata_viewer/
│   │   ├── engine.py
│   │   └── parsers/
│   ├── image_preview/
│   │   └── viewer.py
│   └── plugin_system/            # Plugin infrastructure
│       ├── __init__.py
│       ├── plugin_base.py        # Base class for all plugins
│       ├── plugin_registry.py    # Discovers and tracks plugins
│       ├── plugin_installer.py   # Handles installation
│       └── event_bus.py          # Plugin communication
│
├── ui/                            # Core UI (always installed)
│   ├── main_window.py
│   ├── dialogs.py
│   └── plugin_manager_dialog.py  # UI for managing plugins
│
├── plugins/                       # Plugin definitions
│   ├── __init__.py
│   ├── plugin_base.py            # Copy of base for reference
│   │
│   ├── theme_designer/           # Theme Designer plugin
│   │   ├── __init__.py
│   │   ├── plugin.py             # Plugin class
│   │   ├── requirements.txt      # qt-material, cssutils
│   │   └── ui/                   # Theme designer UI code
│   │       └── ...
│   │
│   ├── image_tagger_gemini/      # Gemini AI tagger
│   │   ├── __init__.py
│   │   ├── plugin.py
│   │   ├── requirements.txt      # google-generativeai
│   │   └── tagger.py             # Tagging logic
│   │
│   ├── image_tagger_onnx/        # Local GPU tagger
│   │   ├── __init__.py
│   │   ├── plugin.py
│   │   ├── requirements.txt      # onnxruntime-gpu, torch
│   │   ├── tagger.py
│   │   └── models/               # Model download/cache
│   │
│   └── huggingface_tools/        # HuggingFace integration
│       ├── __init__.py
│       ├── plugin.py
│       ├── requirements.txt      # huggingface_hub
│       └── uploader.py
│
├── pyproject.toml                # Package configuration
└── README.md
```

---

## 🔌 Plugin API Design

### **Base Plugin Class:**

```python
# core/plugin_system/plugin_base.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QObject

class PluginBase(ABC):
    """Base class for all Dataset Tools plugins.

    Every plugin must inherit from this and implement required methods.
    """

    # ===== Plugin Metadata =====

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin display name (e.g., "Theme Designer")."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version (e.g., "1.0.0")."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description for plugin manager UI."""
        pass

    @property
    @abstractmethod
    def author(self) -> str:
        """Plugin author name."""
        pass

    # ===== Requirements =====

    @property
    def requirements(self) -> Dict:
        """Python package requirements and system requirements.

        Example:
            {
                'packages': ['google-generativeai>=0.3.0'],
                'system': {
                    'gpu': False,
                    'cuda_version': None,
                    'min_ram': '4GB',
                    'min_disk': '100MB'
                }
            }
        """
        return {'packages': [], 'system': {}}

    @property
    def optional_features(self) -> Dict:
        """Optional sub-features that can be enabled.

        Example:
            {
                'wd14_tagger': {
                    'description': 'WD14 tagging model',
                    'packages': ['huggingface_hub'],
                    'model_size': '1.5GB'
                }
            }
        """
        return {}

    # ===== Lifecycle Methods =====

    @abstractmethod
    def initialize(self, main_window: QObject, event_bus: QObject):
        """Initialize plugin with main window and event bus.

        Called when plugin is loaded/enabled.

        Args:
            main_window: Reference to main application window
            event_bus: Event bus for plugin communication
        """
        pass

    @abstractmethod
    def shutdown(self):
        """Clean up when plugin is disabled/unloaded.

        Close windows, disconnect signals, free resources.
        """
        pass

    # ===== UI Integration =====

    def get_menu_actions(self) -> List[Dict]:
        """Return menu actions to add to main window.

        Example:
            [
                {
                    'menu': 'Tools',
                    'text': 'Theme Designer...',
                    'callback': self.launch_theme_designer,
                    'shortcut': 'Ctrl+Shift+T'
                }
            ]
        """
        return []

    def get_dock_widget(self) -> Optional[QWidget]:
        """Return a widget to be shown as a dockable panel.

        Returns None if plugin doesn't have a dockable UI.
        """
        return None

    def get_settings_widget(self) -> Optional[QWidget]:
        """Return a widget for plugin settings.

        Shown in Settings dialog under plugin's section.
        """
        return None

    # ===== Event Handlers =====

    def on_image_changed(self, filepath: str):
        """Called when user selects a new image.

        Override this if your plugin needs to react to image changes.
        """
        pass

    def on_theme_changed(self, theme_name: str):
        """Called when theme is changed.

        Override this if your plugin needs to react to theme changes.
        """
        pass

    def on_metadata_updated(self, metadata: Dict):
        """Called when metadata is parsed/updated.

        Override this if your plugin needs metadata access.
        """
        pass
```

---

## 🎨 Example Plugin: Theme Designer

```python
# plugins/theme_designer/plugin.py
from dataset_tools.core.plugin_system import PluginBase
from PyQt6.QtWidgets import QWidget, QMainWindow
from .ui.theme_designer_window import ThemeDesignerWindow

class ThemeDesignerPlugin(PluginBase):
    """Theme Designer plugin for creating and editing QSS themes."""

    # Metadata
    name = "Theme Designer"
    version = "1.0.0"
    description = "Create and edit Qt Style Sheet (QSS) themes"
    author = "KTISEOS NYX"

    # Requirements
    requirements = {
        'packages': [
            'qt-material>=2.14',
            'cssutils>=2.6.0'
        ],
        'system': {
            'gpu': False,
            'min_ram': '512MB',
            'min_disk': '50MB'
        }
    }

    def __init__(self):
        self.main_window = None
        self.event_bus = None
        self.designer_window = None

    def initialize(self, main_window, event_bus):
        """Initialize plugin."""
        self.main_window = main_window
        self.event_bus = event_bus

        # Subscribe to theme changes
        self.event_bus.theme_changed.connect(self.on_theme_changed)

    def shutdown(self):
        """Clean up."""
        if self.designer_window:
            self.designer_window.close()
            self.designer_window = None

    def get_menu_actions(self):
        """Add menu actions."""
        return [
            {
                'menu': 'Tools',
                'text': 'Theme Designer...',
                'callback': self.launch_designer,
                'shortcut': 'Ctrl+Shift+T'
            }
        ]

    def launch_designer(self):
        """Launch theme designer window."""
        if not self.designer_window:
            self.designer_window = ThemeDesignerWindow(self.main_window)

            # When designer creates a theme, apply it
            self.designer_window.theme_applied.connect(
                self._on_theme_applied
            )

        self.designer_window.show()
        self.designer_window.raise_()

    def _on_theme_applied(self, theme_path: str):
        """When user applies a theme from designer."""
        # Tell main app to load this theme
        self.event_bus.theme_changed.emit(theme_path)

    def on_theme_changed(self, theme_name: str):
        """React to theme changes from main app."""
        if self.designer_window:
            # Update designer to show current theme
            self.designer_window.load_theme(theme_name)
```

---

## 🤖 Example Plugin: Image Tagger (Gemini)

```python
# plugins/image_tagger_gemini/plugin.py
from dataset_tools.core.plugin_system import PluginBase
from PyQt6.QtWidgets import QDockWidget
from .ui.tagger_panel import TaggerPanel

class GeminiTaggerPlugin(PluginBase):
    """AI-powered image tagging using Google Gemini API."""

    name = "Image Tagger (Gemini)"
    version = "1.0.0"
    description = "Tag images using Google's Gemini AI (cloud-based)"
    author = "KTISEOS NYX"

    requirements = {
        'packages': [
            'google-generativeai>=0.3.0',
            'pillow>=10.0.0'
        ],
        'system': {
            'gpu': False,
            'internet': True,  # Requires internet!
            'min_ram': '512MB'
        }
    }

    def __init__(self):
        self.main_window = None
        self.event_bus = None
        self.dock = None
        self.panel = None
        self.current_image = None

    def initialize(self, main_window, event_bus):
        """Initialize plugin."""
        self.main_window = main_window
        self.event_bus = event_bus

        # Subscribe to image changes
        self.event_bus.image_changed.connect(self.on_image_changed)

    def shutdown(self):
        """Clean up."""
        if self.dock:
            self.main_window.removeDockWidget(self.dock)
            self.dock = None

    def get_dock_widget(self):
        """Create dockable tagger panel."""
        if not self.panel:
            self.panel = TaggerPanel()
            self.panel.tags_generated.connect(self._on_tags_generated)

        return self.panel

    def get_menu_actions(self):
        """Add menu action to toggle panel."""
        return [
            {
                'menu': 'Tools',
                'text': 'Image Tagger',
                'callback': self.toggle_panel,
                'shortcut': 'Ctrl+T',
                'checkable': True
            }
        ]

    def toggle_panel(self):
        """Show/hide tagger panel."""
        # This is handled by the dock widget's visibility
        pass

    def on_image_changed(self, filepath: str):
        """When user selects new image, load it for tagging."""
        self.current_image = filepath
        if self.panel:
            self.panel.load_image(filepath)

    def _on_tags_generated(self, tags: list):
        """When tags are generated, emit them to other plugins."""
        # Other plugins might want to know about tags
        self.event_bus.tags_generated.emit(self.current_image, tags)
```

---

## 🎛️ Plugin Manager UI

### **Settings Dialog Integration:**

```python
# ui/dialogs.py (add to existing SettingsDialog)
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        # ... existing code ...

        # Add Plugins tab
        plugins_tab = QWidget()
        self.plugin_manager = PluginManagerWidget()
        plugins_layout = QVBoxLayout(plugins_tab)
        plugins_layout.addWidget(self.plugin_manager)

        self.tabs.addTab(plugins_tab, "Plugins")
```

### **Plugin Manager Widget:**

```python
# ui/plugin_manager_dialog.py
class PluginManagerWidget(QWidget):
    """Widget for managing plugins in Settings dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(
            "Plugins add optional features to Dataset Tools.\n"
            "Each plugin may require additional dependencies."
        )
        layout.addWidget(info)

        # Plugin list
        self.plugin_list = QListWidget()
        self.plugin_list.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self.plugin_list)

        # Plugin details panel
        self.details_panel = PluginDetailsPanel()
        layout.addWidget(self.details_panel)

        # Populate plugins
        self._populate_plugins()

    def _populate_plugins(self):
        """Load all available plugins."""
        from dataset_tools.core.plugin_system import PluginRegistry

        for plugin_info in PluginRegistry.discover_plugins():
            item = PluginListItem(plugin_info)
            self.plugin_list.addItem(item)

    def _on_selection_changed(self, current, previous):
        """Show details for selected plugin."""
        if current:
            self.details_panel.show_plugin(current.plugin_info)


class PluginDetailsPanel(QWidget):
    """Shows details and install button for a plugin."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Plugin name and version
        self.name_label = QLabel()
        self.name_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(self.name_label)

        # Description
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        # Requirements
        req_group = QGroupBox("Requirements")
        req_layout = QVBoxLayout(req_group)
        self.req_text = QTextEdit()
        self.req_text.setReadOnly(True)
        self.req_text.setMaximumHeight(100)
        req_layout.addWidget(self.req_text)
        layout.addWidget(req_group)

        # Status
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        # Install/Uninstall button
        self.action_btn = QPushButton()
        self.action_btn.clicked.connect(self._on_action_clicked)
        layout.addWidget(self.action_btn)

        layout.addStretch()

    def show_plugin(self, plugin_info):
        """Display plugin details."""
        self.current_plugin = plugin_info

        self.name_label.setText(f"{plugin_info.name} v{plugin_info.version}")
        self.desc_label.setText(plugin_info.description)

        # Show requirements
        req_text = "Python Packages:\n"
        for pkg in plugin_info.requirements.get('packages', []):
            req_text += f"  • {pkg}\n"

        system_req = plugin_info.requirements.get('system', {})
        if system_req:
            req_text += "\nSystem Requirements:\n"
            if system_req.get('gpu'):
                req_text += "  • CUDA GPU required\n"
            if system_req.get('min_ram'):
                req_text += f"  • RAM: {system_req['min_ram']}\n"

        self.req_text.setPlainText(req_text)

        # Check if installed
        if plugin_info.is_installed:
            self.status_label.setText("✓ Installed")
            self.status_label.setStyleSheet("color: green;")
            self.action_btn.setText("Uninstall")
        else:
            self.status_label.setText("✗ Not Installed")
            self.status_label.setStyleSheet("color: orange;")
            self.action_btn.setText("Install")

    def _on_action_clicked(self):
        """Install or uninstall plugin."""
        if self.current_plugin.is_installed:
            self._uninstall_plugin()
        else:
            self._install_plugin()

    def _install_plugin(self):
        """Install the plugin."""
        # Show confirmation dialog
        confirm = InstallConfirmDialog(self.current_plugin)
        if confirm.exec() != QDialog.Accepted:
            return

        # Show progress dialog
        progress = PluginInstallProgressDialog(self.current_plugin, self)
        progress.exec()

        # Refresh UI
        self.show_plugin(self.current_plugin)
```

---

## 🔧 Plugin Installation System

### **Plugin Installer:**

```python
# core/plugin_system/plugin_installer.py
import sys
import subprocess
from pathlib import Path
from typing import Tuple, Optional

class PluginInstaller:
    """Handles plugin installation and dependency management."""

    @staticmethod
    def check_requirements(plugin_info) -> Tuple[bool, str]:
        """Check if system meets plugin requirements.

        Returns:
            (success, message)
        """
        system_req = plugin_info.requirements.get('system', {})

        # Check GPU requirement
        if system_req.get('gpu', False):
            if not PluginInstaller._has_cuda_gpu():
                return False, "CUDA GPU required but not detected"

        # Check internet requirement
        if system_req.get('internet', False):
            if not PluginInstaller._has_internet():
                return False, "Internet connection required"

        # Check disk space
        min_disk = system_req.get('min_disk', '0MB')
        # TODO: Actually check disk space

        return True, "All requirements met"

    @staticmethod
    def install_plugin(plugin_info, progress_callback=None):
        """Install plugin and its dependencies.

        Args:
            plugin_info: Plugin metadata
            progress_callback: Function to call with progress updates
        """
        # Check requirements first
        ok, msg = PluginInstaller.check_requirements(plugin_info)
        if not ok:
            raise PluginInstallError(msg)

        # Get requirements file
        plugin_dir = Path(__file__).parent.parent.parent / 'plugins' / plugin_info.module_name
        requirements_file = plugin_dir / 'requirements.txt'

        if not requirements_file.exists():
            raise PluginInstallError(f"Requirements file not found: {requirements_file}")

        # Install using pip
        if progress_callback:
            progress_callback("Installing Python packages...")

        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install',
                '-r', str(requirements_file),
                '--upgrade'
            ], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise PluginInstallError(f"Failed to install packages: {e.stderr}")

        # Download models if needed
        if hasattr(plugin_info.plugin_class, 'download_models'):
            if progress_callback:
                progress_callback("Downloading models...")
            plugin_info.plugin_class.download_models(progress_callback)

        # Mark as installed
        plugin_info.mark_installed()

        if progress_callback:
            progress_callback("Installation complete!")

    @staticmethod
    def uninstall_plugin(plugin_info):
        """Uninstall a plugin (but not its dependencies)."""
        # We don't uninstall packages because other plugins might use them
        # Just mark as uninstalled
        plugin_info.mark_uninstalled()

    @staticmethod
    def _has_cuda_gpu() -> bool:
        """Check if CUDA GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            # If torch isn't installed, can't check
            # Assume no GPU
            return False

    @staticmethod
    def _has_internet() -> bool:
        """Check if internet connection is available."""
        import socket
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False


class PluginInstallError(Exception):
    """Raised when plugin installation fails."""
    pass
```

---

## 🚀 Event Bus System

### **Plugin Communication:**

```python
# core/plugin_system/event_bus.py
from PyQt6.QtCore import QObject, pyqtSignal

class EventBus(QObject):
    """Central event bus for plugin communication.

    Plugins can emit and subscribe to these signals to communicate
    with each other and the main application.
    """

    # File/Image events
    image_changed = pyqtSignal(str)           # filepath
    image_loaded = pyqtSignal(str, object)    # filepath, QPixmap
    folder_opened = pyqtSignal(str)           # folder_path

    # Metadata events
    metadata_parsed = pyqtSignal(str, dict)   # filepath, metadata_dict
    metadata_updated = pyqtSignal(dict)       # metadata_dict

    # Theme events
    theme_changed = pyqtSignal(str)           # theme_name/path

    # Tagging events (for tagger plugins)
    tags_generated = pyqtSignal(str, list)    # filepath, tags_list
    tags_applied = pyqtSignal(str, list)      # filepath, tags_list

    # Plugin lifecycle events
    plugin_loaded = pyqtSignal(str)           # plugin_name
    plugin_unloaded = pyqtSignal(str)         # plugin_name

    # Application events
    app_closing = pyqtSignal()
    settings_changed = pyqtSignal(dict)       # settings_dict


# Usage in main window:
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create event bus
        self.event_bus = EventBus()

        # Load plugins
        self.plugin_manager = PluginManager(self, self.event_bus)

        # Connect app events to event bus
        self.connect_signals()

    def connect_signals(self):
        """Connect main app signals to event bus."""
        # When user selects a file
        self.file_list.currentFileChanged.connect(
            self.event_bus.image_changed.emit
        )

        # When metadata is parsed
        self.task_manager.metadata_ready.connect(
            lambda path, data: self.event_bus.metadata_parsed.emit(path, data)
        )
```

---

## 📋 Installation Flow

### **User Journey:**

```
1. User installs Dataset Tools:
   pip install kn-dataset-tools

   ✓ Core installed (~50MB)
   ✓ Basic functionality works

2. User launches app, sees welcome:
   "Want to add more features? Check Plugins!"

3. User opens Settings → Plugins:

   Available Plugins:
   ☐ Theme Designer (qt-material, cssutils)
   ☐ Image Tagger - Gemini (google-generativeai)
   ☐ Image Tagger - ONNX (onnxruntime-gpu, torch) ⚠ GPU required
   ☐ HuggingFace Tools (huggingface_hub)

4. User clicks "Image Tagger - Gemini":

   Image Tagger (Gemini) v1.0.0
   Tag images using Google's Gemini AI

   Requirements:
   • google-generativeai>=0.3.0
   • pillow>=10.0.0

   Total download: ~10MB

   [Install]

5. User clicks Install:

   Installing Image Tagger (Gemini)...
   ▓▓▓▓▓▓▓▓░░░░░░░░ 50%
   Installing google-generativeai...

6. Installation completes:

   ✓ Image Tagger installed!

   The app will restart to load the plugin.

   [Restart Now]

7. App restarts, plugin appears:

   Tools menu now has:
   • Image Tagger

   New dockable panel: "Image Tagger"
```

---

## 🎯 Implementation Phases

### **Phase 0: Learning & Experimentation (Current)**
**Timeline:** Ongoing
**Status:** ✅ Learning PyQt6, building apps

**Focus:**
- Keep building individual apps
- Learn plugin patterns
- Understand how your apps could integrate
- No rush - this is foundation building

**Deliverables:**
- 2-3 working PyQt6 apps
- Understanding of shared functionality
- Ideas for how apps should communicate

---

### **Phase 1: Plugin System Foundation**
**Timeline:** When ready (no rush!)
**Difficulty:** Intermediate

**Tasks:**

1. **Create base plugin infrastructure:**
   ```python
   # core/plugin_system/
   ├── __init__.py
   ├── plugin_base.py       # Base class
   ├── plugin_registry.py   # Discovery
   └── event_bus.py         # Communication
   ```

2. **Design plugin API:**
   - What methods do all plugins need?
   - What events should exist?
   - How do plugins register themselves?

3. **Create simple test plugin:**
   ```python
   # plugins/hello_world/
   class HelloWorldPlugin(PluginBase):
       name = "Hello World"

       def initialize(self, main_window, event_bus):
           print("Hello from plugin!")
   ```

4. **Test plugin loading:**
   - Can main app discover plugins?
   - Can it load/unload them?
   - Do they receive events?

**Success Criteria:**
- [ ] Hello World plugin loads successfully
- [ ] Plugin can receive image_changed event
- [ ] Plugin can add menu action
- [ ] No crashes or errors

---

### **Phase 2: Convert First App to Plugin**
**Timeline:** After Phase 1 works
**Difficulty:** Intermediate

**Pick easiest app to convert** (probably Theme Designer)

**Tasks:**

1. **Wrap app as plugin:**
   ```python
   class ThemeDesignerPlugin(PluginBase):
       def initialize(self, main_window, event_bus):
           # Existing theme designer code here
           pass
   ```

2. **Test integration:**
   - Launch from Dataset Tools menu
   - Share current theme with Dataset Tools
   - Apply theme back to Dataset Tools

3. **Verify everything still works:**
   - All theme designer features functional
   - No conflicts with main app
   - Themes apply correctly

**Success Criteria:**
- [ ] Theme Designer launches from Dataset Tools
- [ ] Can design themes while viewing images
- [ ] Theme applies to main window
- [ ] Plugin can be disabled/enabled

---

### **Phase 3: Dependency Management**
**Timeline:** After Phase 2 works
**Difficulty:** Advanced

**Tasks:**

1. **Create plugin installer:**
   ```python
   class PluginInstaller:
       def install_plugin(plugin_info):
           # pip install -r requirements.txt
           pass
   ```

2. **Add requirements checking:**
   - Parse requirements.txt
   - Check system requirements
   - Warn about GPU/CUDA needs

3. **Create installation UI:**
   - Plugin manager dialog
   - Progress bar
   - Error handling

4. **Test with heavy plugin:**
   - Try ONNX tagger (big dependencies)
   - Verify graceful failure if no GPU
   - Test installation progress

**Success Criteria:**
- [ ] Can install plugins from UI
- [ ] Requirements checked before install
- [ ] Progress shown during install
- [ ] Errors handled gracefully

---

### **Phase 4: Convert Remaining Apps**
**Timeline:** After Phase 3 works
**Difficulty:** Moderate (pattern established)

**Convert each app one at a time:**

1. HuggingFace Tools → Plugin
2. Image Tagger (Gemini) → Plugin
3. Image Tagger (ONNX) → Plugin

**For each:**
- Wrap as plugin
- Add to registry
- Test integration
- Verify all features work

---

### **Phase 5: Polish & Distribution**
**Timeline:** When all plugins work
**Difficulty:** Advanced

**Tasks:**

1. **Package structure:**
   ```
   pyproject.toml with optional dependencies:
   [project.optional-dependencies]
   theme-designer = ["qt-material", "cssutils"]
   tagger-gemini = ["google-generativeai"]
   etc.
   ```

2. **Distribution:**
   - Publish to PyPI
   - Create installation docs
   - Make demo video

3. **User experience:**
   - Welcome screen for first launch
   - Plugin discovery help
   - Tutorials

---

## ⚠️ Challenges & Solutions

### **Challenge 1: Import Conflicts**

**Problem:** Plugins might use different versions of same library

**Solution:**
- Use separate virtual environments per plugin (advanced)
- OR require compatible versions (simpler)
- OR use namespace packages

**Recommendation:** Start simple - require compatible versions

---

### **Challenge 2: Plugin Crashes**

**Problem:** Bad plugin crashes entire app

**Solution:**
```python
def load_plugin(plugin_class):
    try:
        plugin = plugin_class()
        plugin.initialize(main_window, event_bus)
    except Exception as e:
        logger.error(f"Plugin {plugin_class.name} failed: {e}")
        # Disable plugin, show error to user
        # Main app continues working
```

**Recommendation:** Wrap plugin calls in try/except

---

### **Challenge 3: Circular Dependencies**

**Problem:** Plugin A needs Plugin B which needs Plugin A

**Solution:**
- Use event bus (loose coupling)
- Plugins don't directly import each other
- Communicate via signals

---

### **Challenge 4: State Management**

**Problem:** Plugins need to know current app state

**Solution:**
```python
class ApplicationState:
    """Shared state accessible to all plugins."""
    current_image: str = None
    current_theme: str = None
    current_metadata: dict = None

# Plugins can read state:
current_img = app_state.current_image
```

---

## 🔒 Security Considerations

### **Plugin Sandboxing (Future):**

For now, only load **trusted plugins you created**. In the future:

- Verify plugin signatures
- Run plugins in restricted environment
- Limit file system access
- Review plugin code before loading

**For your use case:** You're writing all the plugins, so security is lower concern.

---

## 📦 Distribution Strategy

### **Option A: All-In-One Repo (Simpler)**

```
dataset-tools/
├── core/
├── plugins/
│   ├── theme_designer/
│   ├── image_tagger_gemini/
│   └── ...
└── pyproject.toml
```

**Pros:**
- ✅ Easy to develop
- ✅ All code in one place
- ✅ Simpler to maintain

**Cons:**
- ❌ Users download everything (even if not used)
- ❌ Harder to version plugins separately

---

### **Option B: Separate Packages (Advanced)**

```
dataset-tools (core)
dataset-tools-plugin-theme-designer
dataset-tools-plugin-tagger-gemini
dataset-tools-plugin-tagger-onnx
dataset-tools-plugin-huggingface
```

**Pros:**
- ✅ Users install only what they need
- ✅ Plugins can version independently
- ✅ Professional structure

**Cons:**
- ❌ More complex to develop
- ❌ More repos to maintain

**Recommendation:** Start with Option A, migrate to B if needed

---

## 🎓 Learning Path

### **Skills You'll Need:**

1. **PyQt6 Basics** ✅ (You're learning this now!)
   - Widgets, layouts, signals/slots
   - QMainWindow, QDockWidget
   - Event handling

2. **Python Packaging** (Learn next)
   - pyproject.toml
   - Optional dependencies
   - Entry points

3. **Plugin Patterns** (Learn when ready)
   - Abstract base classes
   - Dynamic imports
   - Dependency injection

4. **Process Management** (Advanced)
   - subprocess for pip install
   - Progress tracking
   - Error handling

### **Resources:**

- **PyQt6 Docs:** Learn dockable widgets, plugin patterns
- **setuptools Docs:** Learn about optional dependencies
- **Real Examples:** Look at VS Code, Blender plugin systems

---

## 📝 Decision Points

### **When to Start:**

✅ **Good time:**
- After you have 2-3 working apps
- When you understand PyQt6 well
- When you have time to experiment
- When apps are stable

❌ **Not yet:**
- Still learning PyQt6 basics
- Apps aren't working yet
- Other priorities (themes, parsers, etc.)

### **Start Small:**

Don't build entire system at once:

1. **Week 1:** Make PluginBase class
2. **Week 2:** Make one test plugin
3. **Week 3:** Convert Theme Designer
4. **Week 4:** Test and refine

**Iterate!** Don't try to be perfect first time.

---

## 🎯 Success Metrics

### **MVP Success:**

- [ ] Core app installs without plugins
- [ ] Can discover available plugins
- [ ] Can load/enable one plugin
- [ ] Plugin can add menu action
- [ ] Plugin receives events from main app
- [ ] No crashes

### **Full Success:**

- [ ] All your apps work as plugins
- [ ] Can install dependencies from UI
- [ ] Requirements checked properly
- [ ] Plugins communicate via event bus
- [ ] Layout switcher works with plugins
- [ ] Users love the flexibility!

---

## 💭 Final Thoughts

### **This is a LONG-TERM vision**

- Don't rush it
- Learn as you go
- Build one app at a time
- Plugin system comes AFTER apps work

### **The Journey:**

```
Now:              Learning PyQt6, building individual apps
3 months:         Apps work standalone, understand plugin concept
6 months:         Experiment with plugin system
9 months:         First plugin integration working
12+ months:       Full plugin suite complete
```

### **Remember:**

- ✅ Your apps already have value standalone
- ✅ Plugin integration is a BONUS
- ✅ Take your time learning
- ✅ It's okay to change the plan
- ✅ This document is a reference, not a deadline

---

## 🚀 Next Steps (When Ready)

1. **Keep building your individual apps** - Get them working great first
2. **Read this doc occasionally** - Let ideas marinate
3. **Experiment with simple plugins** - Try Hello World plugin
4. **Ask questions** - When you're ready to start, ask for help
5. **Have fun!** - This should be exciting, not stressful

---

**You've got this!** The fact that you're thinking about architecture this early shows you're on the right path. Take your time, learn at your pace, and come back to this when you're ready. 🎉

---

**Document Version:** 1.0
**Last Updated:** 2025-10-19
**Status:** Vision / Long-term Planning
**Next Review:** When 2-3 apps are working standalone
