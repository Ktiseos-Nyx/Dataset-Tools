import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable, List, Dict, Any, Optional, Union, Tuple
import os


class BaseWidget:
    """Base class for all custom widgets"""
    def __init__(self, parent):
        self.parent = parent
        self.widget = None

    def get_widget(self):
        return self.widget

    def pack(self, **kwargs):
        if self.widget:
            self.widget.pack(**kwargs)
        return self

    def grid(self, **kwargs):
        if self.widget:
            self.widget.grid(**kwargs)
        return self

    def place(self, **kwargs):
        if self.widget:
            self.widget.place(**kwargs)
        return self


class LabeledEntry(BaseWidget):
    """A labeled text entry field"""
    def __init__(self, parent, label_text: str, default_value: str = "", width: int = 20):
        super().__init__(parent)
        self.frame = ttk.Frame(parent)
        self.label = ttk.Label(self.frame, text=label_text)
        self.label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.var = tk.StringVar(value=default_value)
        self.entry = ttk.Entry(self.frame, textvariable=self.var, width=width)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.widget = self.frame
    
    def get_value(self) -> str:
        return self.var.get()
    
    def set_value(self, value: str):
        self.var.set(value)
        return self


class LabeledCombobox(BaseWidget):
    """A labeled dropdown/combobox"""
    def __init__(self, parent, label_text: str, values: List[str] = None, default_value: str = "", width: int = 20):
        super().__init__(parent)
        self.frame = ttk.Frame(parent)
        self.label = ttk.Label(self.frame, text=label_text)
        self.label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.var = tk.StringVar(value=default_value)
        self.combobox = ttk.Combobox(self.frame, textvariable=self.var, width=width)
        if values:
            self.combobox['values'] = values
        self.combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.widget = self.frame
    
    def get_value(self) -> str:
        return self.var.get()

    def get_index(self) -> int:
        return self.combobox.current()
    
    def set_value(self, value: str):
        self.var.set(value)
        return self
    
    def set_values(self, values: List[str]):
        self.combobox['values'] = values
        return self


class LabeledCheckbutton(BaseWidget):
    """A labeled checkbox"""
    def __init__(self, parent, label_text: str, default_value: bool = False):
        super().__init__(parent)
        self.frame = ttk.Frame(parent)
        
        self.var = tk.BooleanVar(value=default_value)
        self.checkbutton = ttk.Checkbutton(self.frame, text=label_text, variable=self.var)
        self.checkbutton.pack(side=tk.LEFT)
        
        self.widget = self.frame
    
    def get_value(self) -> bool:
        return self.var.get()
    
    def set_value(self, value: bool):
        self.var.set(value)
        return self


class ButtonGroup(BaseWidget):
    """A group of buttons with consistent styling"""
    def __init__(self, parent, buttons: List[Dict[str, Any]] = None):
        """
        Create a group of buttons
        
        Args:
            parent: Parent widget
            buttons: List of button configs with keys:
                - text: Button text
                - command: Button callback function
                - style: (optional) ttk style
        """
        super().__init__(parent)
        self.frame = ttk.Frame(parent)
        self.buttons = []
        
        if buttons:
            for btn_config in buttons:
                self.add_button(**btn_config)
        
        self.widget = self.frame
    
    def add_button(self, text: str, command: Callable, style: str = None, **kwargs):
        btn = ttk.Button(self.frame, text=text, command=command, style=style, **kwargs)
        btn.pack(side=tk.LEFT, padx=5)
        self.buttons.append(btn)
        return self


class ScrollableFrame(BaseWidget):
    """A frame with scrollbars"""
    def __init__(self, parent, width: int = 300, height: int = 200):
        super().__init__(parent)
        self.canvas = tk.Canvas(parent, width=width, height=height)
        self.scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.widget = self.canvas
        self.frame = self.scrollable_frame


class FileSelector(BaseWidget):
    """A widget for selecting files or directories"""
    def __init__(self, parent, label_text: str, file_type: str = "file", 
                 filetypes: List[Tuple[str, str]] = None, default_path: str = ""):
        """
        Create a file/directory selector widget
        
        Args:
            parent: Parent widget
            label_text: Label text
            file_type: 'file' or 'directory'
            filetypes: List of file type tuples for file dialog
            default_path: Default path
        """
        super().__init__(parent)
        self.file_type = file_type
        self.filetypes = filetypes or [("All files", "*.*")]
        
        self.frame = ttk.Frame(parent)
        self.label = ttk.Label(self.frame, text=label_text)
        self.label.pack(side=tk.TOP, anchor="w", pady=(0, 5))
        
        self.path_frame = ttk.Frame(self.frame)
        self.path_frame.pack(fill=tk.X, expand=True)
        
        self.var = tk.StringVar(value=default_path)
        self.entry = ttk.Entry(self.path_frame, textvariable=self.var)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.button = ttk.Button(self.path_frame, text="Browse...", command=self._browse)
        self.button.pack(side=tk.RIGHT)
        
        self.widget = self.frame
    
    def _browse(self):
        if self.file_type == "file":
            path = filedialog.askopenfilename(filetypes=self.filetypes)
        else:  # directory
            path = filedialog.askdirectory()
        
        if path:  # User didn't cancel
            self.var.set(path)
    
    def get_value(self) -> str:
        return self.var.get()
    
    def set_value(self, value: str):
        self.var.set(value)
        return self


class StatusBar(BaseWidget):
    """A status bar for displaying messages"""
    def __init__(self, parent):
        super().__init__(parent)
        self.frame = ttk.Frame(parent, relief=tk.SUNKEN)
        
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self.frame, textvariable=self.status_var, anchor=tk.W)
        self.status_label.pack(fill=tk.X)
        
        self.widget = self.frame
    
    def set_status(self, message: str):
        self.status_var.set(message)
        self.parent.update_idletasks()
        return self


class ProgressBar(BaseWidget):
    """A progress bar with optional status text"""
    def __init__(self, parent, mode: str = "determinate"):
        super().__init__(parent)
        self.frame = ttk.Frame(parent)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.frame, variable=self.progress_var, mode=mode)
        self.progress.pack(fill=tk.X, expand=True, side=tk.TOP)
        
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self.frame, textvariable=self.status_var, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.widget = self.frame
    
    def set_progress(self, value: float, message: str = None):
        self.progress_var.set(value)
        if message is not None:
            self.status_var.set(message)
        self.parent.update_idletasks()
        return self


class TabView(BaseWidget):
    """A tabbed view container"""
    def __init__(self, parent):
        super().__init__(parent)
        self.notebook = ttk.Notebook(parent)
        self.tabs = {}
        self.widget = self.notebook
    
    def add_tab(self, name: str, title: str) -> ttk.Frame:
        """Add a new tab and return its frame"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=title)
        self.tabs[name] = {'frame': frame, 'title': title}
        return frame
    
    def get_tab(self, name: str) -> ttk.Frame:
        """Get a tab frame by name"""
        if name in self.tabs:
            return self.tabs[name]['frame']
        return None


class MessageDialog:
    """Helper class for showing message dialogs"""
    @staticmethod
    def info(title: str, message: str):
        return messagebox.showinfo(title, message)
    
    @staticmethod
    def warning(title: str, message: str):
        return messagebox.showwarning(title, message)
    
    @staticmethod
    def error(title: str, message: str):
        return messagebox.showerror(title, message)
    
    @staticmethod
    def question(title: str, message: str):
        return messagebox.askquestion(title, message)
    
    @staticmethod
    def yes_no(title: str, message: str):
        return messagebox.askyesno(title, message)


class FormBuilder(BaseWidget):
    """Helper for building forms with consistent layout"""
    def __init__(self, parent, title: str = None, padding: int = 10):
        super().__init__(parent)
        self.frame = ttk.Frame(parent, padding=padding)
        self.fields = {}
        self.row = 0
        
        if title:
            self.title_label = ttk.Label(self.frame, text=title, font=("TkDefaultFont", 12, "bold"))
            self.title_label.grid(row=self.row, column=0, columnspan=2, sticky="w", pady=(0, 10))
            self.row += 1
        
        self.widget = self.frame
    
    def add_field(self, field_type: str, name: str, label: str, **kwargs) -> BaseWidget:
        """Add a field to the form"""
        field = None
        
        if field_type == "entry":
            field = LabeledEntry(self.frame, label, **kwargs)
        elif field_type == "combobox":
            field = LabeledCombobox(self.frame, label, **kwargs)
        elif field_type == "checkbox":
            field = LabeledCheckbutton(self.frame, label, **kwargs)
        elif field_type == "file":
            field = FileSelector(self.frame, label, **kwargs)
        
        if field:
            field.grid(row=self.row, column=0, sticky="ew", pady=5)
            self.fields[name] = field
            self.row += 1
        
        return field
    
    def add_separator(self):
        """Add a horizontal separator"""
        sep = ttk.Separator(self.frame, orient="horizontal")
        sep.grid(row=self.row, column=0, sticky="ew", pady=10)
        self.row += 1
    
    def add_button_group(self, buttons: List[Dict[str, Any]]):
        """Add a group of buttons at the bottom of the form"""
        btn_group = ButtonGroup(self.frame, buttons)
        btn_group.grid(row=self.row, column=0, sticky="e", pady=10)
        self.row += 1
        return btn_group
    
    def get_values(self) -> Dict[str, Any]:
        """Get all form values as a dictionary"""
        values = {}
        for name, field in self.fields.items():
            if hasattr(field, 'get_value'):
                values[name] = field.get_value()
        return values