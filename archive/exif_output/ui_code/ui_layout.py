# dataset_tools/ui_layout.py
import logging

from PyQt6 import QtCore
from PyQt6 import QtWidgets as Qw

# Font functions removed - fonts now inherit from user settings
# Import your custom widgets. These must be defined in widgets.py first.
from .widgets import ImageLabel, LeftPanelWidget

log = logging.getLogger(__name__)


def setup_ui_layout(main_window: Qw.QMainWindow):
    """Creates and arranges all the visual widgets inside the MainWindow.
    This function takes the main_window object and adds attributes (like .main_splitter) to it.
    """
    log.info("Setting up main UI layout...")

    # --- Main Containers and Splitters ---
    main_widget = Qw.QWidget()
    main_window.setCentralWidget(main_widget)
    overall_layout = Qw.QVBoxLayout(main_widget)
    overall_layout.setContentsMargins(10, 10, 10, 10)
    overall_layout.setSpacing(5)

    main_window.main_splitter = Qw.QSplitter(QtCore.Qt.Orientation.Horizontal)
    overall_layout.addWidget(main_window.main_splitter, 1)

    # --- Left Panel ---
    main_window.left_panel = LeftPanelWidget()
    # Connect the signals from the widget to the methods in the main window
    main_window.left_panel.open_folder_requested.connect(main_window.open_folder)
    main_window.left_panel.sort_files_requested.connect(main_window.sort_files_list)
    main_window.left_panel.list_item_selected.connect(main_window.on_file_selected)
    main_window.main_splitter.addWidget(main_window.left_panel)

    # --- Middle and Right Area (Metadata and Image) ---
    middle_right_area_widget = Qw.QWidget()
    middle_right_layout = Qw.QHBoxLayout(middle_right_area_widget)
    middle_right_layout.setContentsMargins(0, 0, 0, 0)
    middle_right_layout.setSpacing(5)

    main_window.metadata_image_splitter = Qw.QSplitter(QtCore.Qt.Orientation.Horizontal)
    middle_right_layout.addWidget(main_window.metadata_image_splitter)

    # --- Metadata Panel (the text boxes) ---
    metadata_panel_widget = Qw.QWidget()
    metadata_layout = Qw.QVBoxLayout(metadata_panel_widget)
    metadata_layout.setContentsMargins(10, 20, 10, 20)
    metadata_layout.setSpacing(15)
    metadata_layout.addStretch(1)

    main_window.positive_prompt_label = Qw.QLabel("Positive Prompt")
    metadata_layout.addWidget(main_window.positive_prompt_label)
    main_window.positive_prompt_box = Qw.QTextEdit()
    main_window.positive_prompt_box.setReadOnly(True)
    main_window.positive_prompt_box.setSizePolicy(Qw.QSizePolicy.Policy.Expanding, Qw.QSizePolicy.Policy.Preferred)
    main_window.positive_prompt_box.setWordWrapMode(Qw.QTextOption.WrapMode.WordWrap)
    main_window.positive_prompt_box.setLineWrapMode(Qw.QTextEdit.LineWrapMode.WidgetWidth)
    # Font will be inherited from global font settings
    metadata_layout.addWidget(main_window.positive_prompt_box)

    main_window.negative_prompt_label = Qw.QLabel("Negative Prompt")
    metadata_layout.addWidget(main_window.negative_prompt_label)
    main_window.negative_prompt_box = Qw.QTextEdit()
    main_window.negative_prompt_box.setReadOnly(True)
    main_window.negative_prompt_box.setSizePolicy(Qw.QSizePolicy.Policy.Expanding, Qw.QSizePolicy.Policy.Preferred)
    main_window.negative_prompt_box.setWordWrapMode(Qw.QTextOption.WrapMode.WordWrap)
    main_window.negative_prompt_box.setLineWrapMode(Qw.QTextEdit.LineWrapMode.WidgetWidth)
    # Font will be inherited from global font settings
    metadata_layout.addWidget(main_window.negative_prompt_box)

    main_window.generation_data_label = Qw.QLabel("Generation Details & Metadata")
    metadata_layout.addWidget(main_window.generation_data_label)
    main_window.generation_data_box = Qw.QTextEdit()
    main_window.generation_data_box.setReadOnly(True)
    main_window.generation_data_box.setSizePolicy(Qw.QSizePolicy.Policy.Expanding, Qw.QSizePolicy.Policy.Preferred)
    main_window.generation_data_box.setWordWrapMode(Qw.QTextOption.WrapMode.WordWrap)
    main_window.generation_data_box.setLineWrapMode(Qw.QTextEdit.LineWrapMode.WidgetWidth)
    # Font will be inherited from global font settings
    metadata_layout.addWidget(main_window.generation_data_box)
    metadata_layout.addStretch(1)

    main_window.metadata_image_splitter.addWidget(metadata_panel_widget)

    # --- Image Preview Panel ---
    main_window.image_preview = ImageLabel()
    main_window.metadata_image_splitter.addWidget(main_window.image_preview)
    main_window.metadata_image_splitter.setContentsMargins(15, 15, 15, 15)
    # Add the whole middle/right area to the main splitter
    main_window.main_splitter.addWidget(middle_right_area_widget)

    # --- Bottom Bar (Action Buttons) ---
    bottom_bar = Qw.QWidget()
    bottom_layout = Qw.QHBoxLayout(bottom_bar)
    bottom_layout.setContentsMargins(10, 5, 10, 5)
    bottom_layout.addStretch(1)
    action_buttons_layout = Qw.QHBoxLayout()
    action_buttons_layout.setSpacing(10)

    main_window.copy_metadata_button = Qw.QPushButton("Copy All Metadata")
    main_window.copy_metadata_button.clicked.connect(main_window.copy_metadata_to_clipboard)
    action_buttons_layout.addWidget(main_window.copy_metadata_button)

    main_window.settings_button = Qw.QPushButton("Settings")
    main_window.settings_button.clicked.connect(main_window.open_settings_dialog)
    action_buttons_layout.addWidget(main_window.settings_button)

    main_window.exit_button = Qw.QPushButton("Exit Application")
    main_window.exit_button.clicked.connect(main_window.close)
    action_buttons_layout.addWidget(main_window.exit_button)

    bottom_layout.addLayout(action_buttons_layout)
    bottom_layout.addStretch(1)
    overall_layout.addWidget(bottom_bar, 0)

    # --- Restore Splitter Sizes ---
    try:
        win_width = main_window.width() if main_window.isVisible() else 1024
    except RuntimeError:
        win_width = 1024

    main_splitter_sizes = main_window.settings.value(
        "mainSplitterSizes", [win_width // 4, win_width * 3 // 4], type=list
    )
    main_window.main_splitter.setSizes([int(s) for s in main_splitter_sizes])

    meta_img_splitter_sizes = main_window.settings.value(
        "metaImageSplitterSizes", [win_width // 3, win_width * 2 // 3], type=list
    )
    main_window.metadata_image_splitter.setSizes([int(s) for s in meta_img_splitter_sizes])
