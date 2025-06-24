# Tkinter Widgets Manual

This manual provides documentation for the custom Tkinter widgets available in the `dataset_tools/ui/widgets.py` file. These widgets are designed to make building consistent UIs easier and more maintainable.

## Table of Contents

1. [Introduction](#introduction)
2. [Base Widget](#base-widget)
3. [Input Widgets](#input-widgets)
   - [LabeledEntry](#labeledentry)
   - [LabeledCombobox](#labeledcombobox)
   - [LabeledCheckbutton](#labeledcheckbutton)
   - [FileSelector](#fileselector)
4. [Container Widgets](#container-widgets)
   - [ScrollableFrame](#scrollableframe)
   - [TabView](#tabview)
   - [FormBuilder](#formbuilder)
5. [UI Elements](#ui-elements)
   - [ButtonGroup](#buttongroup)
   - [StatusBar](#statusbar)
   - [ProgressBar](#progressbar)
6. [Utility Classes](#utility-classes)
   - [MessageDialog](#messagedialog)
7. [Examples](#examples)

## Introduction

The widgets in this library are designed with the following principles:

- **Consistency**: All widgets follow a similar pattern and API
- **Composability**: Widgets can be combined to create complex UIs
- **Maintainability**: Changes to widgets propagate to all instances
- **Method Chaining**: Most methods return `self` to allow for method chaining

To use these widgets, import them from the `dataset_tools.ui.widgets` module:

```python
from dataset_tools.ui.widgets import LabeledEntry, ButtonGroup, FormBuilder
```

## Base Widget

All widgets inherit from the `BaseWidget` class, which provides common functionality:

```python
# Create a widget
widget = SomeWidget(parent)

# Get the underlying Tkinter widget
tk_widget = widget.get_widget()

# Use layout managers
widget.pack(side=tk.LEFT, fill=tk.X)
widget.grid(row=0, column=0)
widget.place(x=10, y=10)
```

## Input Widgets

### LabeledEntry

A text entry field with a label.

```python
# Create a labeled entry
entry = LabeledEntry(parent, "Name:", default_value="John", width=30)
entry.pack()

# Get the current value
name = entry.get_value()

# Set a new value
entry.set_value("Jane")
```

### LabeledCombobox

A dropdown/combobox with a label.

```python
# Create a labeled combobox
combo = LabeledCombobox(
    parent, 
    "Country:", 
    values=["USA", "Canada", "UK"], 
    default_value="USA"
)
combo.pack()

# Get the selected value
country = combo.get_value()

# Get the selected index
index = combo.get_index()

# Set a new value
combo.set_value("UK")

# Update the list of values
combo.set_values(["France", "Germany", "Spain"])
```

### LabeledCheckbutton

A checkbox with a label.

```python
# Create a labeled checkbox
checkbox = LabeledCheckbutton(parent, "Subscribe to newsletter", default_value=True)
checkbox.pack()

# Get the current state (True/False)
is_subscribed = checkbox.get_value()

# Set a new state
checkbox.set_value(False)
```

### FileSelector

A widget for selecting files or directories.

```python
# Create a file selector for images
file_selector = FileSelector(
    parent,
    "Select Image:",
    file_type="file",
    filetypes=[("Image files", "*.png;*.jpg"), ("All files", "*.*")]
)
file_selector.pack()

# Create a directory selector
dir_selector = FileSelector(
    parent,
    "Output Directory:",
    file_type="directory"
)
dir_selector.pack()

# Get the selected path
image_path = file_selector.get_value()
output_dir = dir_selector.get_value()

# Set a default path
file_selector.set_value("C:/Users/default/image.png")
```

## Container Widgets

### ScrollableFrame

A frame with scrollbars for content that exceeds the view.

```python
# Create a scrollable frame
scrollable = ScrollableFrame(parent, width=400, height=300)
scrollable.pack(fill=tk.BOTH, expand=True)

# Add content to the scrollable frame
for i in range(20):
    label = ttk.Label(scrollable.frame, text=f"Item {i}")
    label.pack(pady=5)
```

### TabView

A tabbed interface for organizing content.

```python
# Create a tab view
tabs = TabView(parent)
tabs.pack(fill=tk.BOTH, expand=True)

# Add tabs
general_tab = tabs.add_tab("general", "General Settings")
advanced_tab = tabs.add_tab("advanced", "Advanced Settings")

# Add content to tabs
ttk.Label(general_tab, text="General settings go here").pack(pady=10)
ttk.Label(advanced_tab, text="Advanced settings go here").pack(pady=10)

# Get a tab by name
tab = tabs.get_tab("general")
```

### FormBuilder

A helper for building forms with consistent layout.

```python
# Create a form
form = FormBuilder(parent, title="User Information", padding=15)
form.pack(fill=tk.BOTH, expand=True)

# Add fields
form.add_field("entry", "name", "Full Name:", default_value="John Doe")
form.add_field("entry", "email", "Email Address:")
form.add_field("combobox", "country", "Country:", 
               values=["USA", "Canada", "UK"])
form.add_separator()
form.add_field("checkbox", "subscribe", "Subscribe to newsletter")

# Add buttons
form.add_button_group([
    {"text": "Save", "command": save_form},
    {"text": "Cancel", "command": cancel_form}
])

# Get all form values as a dictionary
values = form.get_values()
# {'name': 'John Doe', 'email': '', 'country': 'USA', 'subscribe': False}
```

## UI Elements

### ButtonGroup

A group of buttons with consistent styling.

```python
# Create a button group
buttons = ButtonGroup(parent, buttons=[
    {"text": "Save", "command": save_function},
    {"text": "Cancel", "command": cancel_function},
    {"text": "Help", "command": help_function, "style": "Info.TButton"}
])
buttons.pack(pady=10)

# Add a button later
buttons.add_button("Export", export_function)
```

### StatusBar

A status bar for displaying messages.

```python
# Create a status bar
status = StatusBar(parent)
status.pack(side=tk.BOTTOM, fill=tk.X)

# Set status message
status.set_status("Ready")

# Update status during operations
status.set_status("Processing...")
# ... do work ...
status.set_status("Done")
```

### ProgressBar

A progress bar with optional status text.

```python
# Create a progress bar
progress = ProgressBar(parent)
progress.pack(fill=tk.X, pady=10)

# Update progress
for i in range(101):
    progress.set_progress(i, f"Processing item {i}/100")
    # ... do work ...

# Create an indeterminate progress bar
busy = ProgressBar(parent, mode="indeterminate")
busy.pack(fill=tk.X, pady=10)
busy.set_progress(0, "Please wait...")
```

## Utility Classes

### MessageDialog

Helper class for showing message dialogs.

```python
# Show an information dialog
MessageDialog.info("Success", "Operation completed successfully")

# Show a warning dialog
MessageDialog.warning("Warning", "This action cannot be undone")

# Show an error dialog
MessageDialog.error("Error", "Failed to save file")

# Ask a yes/no question
if MessageDialog.yes_no("Confirm", "Are you sure you want to delete this item?"):
    # User clicked Yes
    delete_item()
else:
    # User clicked No
    pass
```

## Examples

### Simple Form Application

```python
import tkinter as tk
from tkinter import ttk
from dataset_tools.ui.widgets import FormBuilder, StatusBar, MessageDialog

def create_ui():
    root = tk.Tk()
    root.title("Dataset Configuration")
    root.geometry("500x400")
    
    # Create main frame
    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Create form
    form = FormBuilder(main_frame, title="Dataset Settings")
    form.pack(fill=tk.BOTH, expand=True)
    
    # Add form fields
    form.add_field("entry", "name", "Dataset Name:")
    form.add_field("file", "input_dir", "Input Directory:", file_type="directory")
    form.add_field("file", "output_dir", "Output Directory:", file_type="directory")
    form.add_field("combobox", "format", "Output Format:", 
                  values=["CSV", "JSON", "XML", "Parquet"])
    form.add_separator()
    form.add_field("checkbox", "compress", "Compress Output")
    
    # Add buttons
    def save_settings():
        values = form.get_values()
        # Process values...
        status.set_status(f"Saved settings for dataset: {values['name']}")
        MessageDialog.info("Success", "Settings saved successfully")
    
    form.add_button_group([
        {"text": "Save", "command": save_settings},
        {"text": "Cancel", "command": root.destroy}
    ])
    
    # Add status bar
    status = StatusBar(root)
    status.pack(side=tk.BOTTOM, fill=tk.X)
    status.set_status("Ready")
    
    return root

if __name__ == "__main__":
    app = create_ui()
    app.mainloop()
```

### Complex Application with Tabs

```python
import tkinter as tk
from tkinter import ttk
from dataset_tools.ui.widgets import (
    TabView, FormBuilder, ButtonGroup, 
    ScrollableFrame, ProgressBar, StatusBar
)

def create_complex_ui():
    root = tk.Tk()
    root.title("Dataset Tools")
    root.geometry("800x600")
    
    # Create main frame
    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Create tabs
    tabs = TabView(main_frame)
    tabs.pack(fill=tk.BOTH, expand=True)
    
    # Create tabs
    config_tab = tabs.add_tab("config", "Configuration")
    process_tab = tabs.add_tab("process", "Processing")
    results_tab = tabs.add_tab("results", "Results")
    
    # Configuration tab content
    config_form = FormBuilder(config_tab, title="Dataset Configuration")
    config_form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    config_form.add_field("entry", "name", "Dataset Name:")
    config_form.add_field("file", "input_dir", "Input Directory:", file_type="directory")
    config_form.add_field("combobox", "type", "Dataset Type:", 
                         values=["Images", "Text", "Tabular", "Time Series"])
    
    # Processing tab content
    process_frame = ttk.Frame(process_tab, padding=10)
    process_frame.pack(fill=tk.BOTH, expand=True)
    
    progress = ProgressBar(process_frame)
    progress.pack(fill=tk.X, pady=10)
    
    log_label = ttk.Label(process_frame, text="Processing Log:")
    log_label.pack(anchor="w", pady=(10, 5))
    
    log_frame = ScrollableFrame(process_frame, height=300)
    log_frame.pack(fill=tk.BOTH, expand=True)
    
    # Results tab content
    results_frame = ttk.Frame(results_tab, padding=10)
    results_frame.pack(fill=tk.BOTH, expand=True)
    
    # Add status bar
    status = StatusBar(root)
    status.pack(side=tk.BOTTOM, fill=tk.X)
    status.set_status("Ready")
    
    return root

if __name__ == "__main__":
    app = create_complex_ui()
    app.mainloop()
```

This manual provides an overview of the available widgets and how to use them. For more detailed information, refer to the docstrings in the `widgets.py` file.
