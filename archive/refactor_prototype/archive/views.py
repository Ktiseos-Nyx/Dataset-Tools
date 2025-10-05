# refactor_prototype/views.py

import os
from qtpy import QtCore, QtWidgets, QtGui
from model import DataManager
from theme_manager import ThemeManager
from metadata_parser import MetadataParser

class ThumbnailDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate for painting thumbnails in the list view."""
    def __init__(self, parent=None):
        super(ThumbnailDelegate, self).__init__(parent)
        self.thumb_size = 140
        self.padding = 5

    def paint(self, painter, option, index):
        # Get the file path from the model
        file_path = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        file_name = os.path.basename(file_path)

        painter.save()

        # --- Draw Background and Selection State ---
        style = option.widget.style() if option.widget else QtWidgets.QApplication.style()
        style.drawPrimitive(QtWidgets.QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)

        # --- Draw Thumbnail ---
        thumb_rect = QtCore.QRect(
            option.rect.x() + self.padding,
            option.rect.y() + self.padding,
            self.thumb_size,
            self.thumb_size
        )

        thumbnail = self.parent().thumbnail_cache.get(file_path)
        if thumbnail:
            scaled_thumb = thumbnail.scaled(
                thumb_rect.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation
            )
            x = round(thumb_rect.x() + (thumb_rect.width() - scaled_thumb.width()) / 2)
            y = round(thumb_rect.y() + (thumb_rect.height() - scaled_thumb.height()) / 2)
            painter.drawPixmap(x, y, scaled_thumb)
        else:
            painter.fillRect(thumb_rect, QtGui.QColor("#333"))

        # --- Draw Filename ---
        text_rect = QtCore.QRect(
            option.rect.x(),
            thumb_rect.bottom() + self.padding,
            option.rect.width(),
            option.rect.height() - self.thumb_size - (2 * self.padding)
        )
        # Set text color based on selection
        text_color = option.palette.highlightedText().color() if (option.state & QtWidgets.QStyle.StateFlag.State_Selected) else option.palette.text().color()
        painter.setPen(text_color)
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.TextFlag.TextWordWrap, file_name)

        painter.restore()

    def sizeHint(self, option, index):
        # Define the size of each item in the grid
        return QtCore.QSize(self.thumb_size + 10, self.thumb_size + 40)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dataset Tools - Refactor Prototype")
        self.resize(1600, 900)

        self.current_folder_path = None
        self.current_file_path = None
        self.thumbnail_cache = {}

        # MVC Setup
        self.model = DataManager()
        self.model.model_ready.connect(self.on_model_ready)
        self.model.thumbnail_ready.connect(self.on_thumbnail_ready)
        self.model.full_image_ready.connect(self.on_full_image_ready)
        self.model.metadata_ready.connect(self.on_metadata_ready)
        self.model.metadata_saved.connect(self.on_metadata_saved)
        
        self._setup_ui()
        self._setup_menus()

    def _setup_ui(self):
        # Main container
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)

        # --- Left Panel (Buttons + Gallery) ---
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0,0,0,0)

        button_layout = QtWidgets.QHBoxLayout()
        open_button = QtWidgets.QPushButton("Open Folder")
        refresh_button = QtWidgets.QPushButton("Refresh")
        open_button.clicked.connect(self.open_folder)
        refresh_button.clicked.connect(self.refresh_folder)
        button_layout.addWidget(open_button)
        button_layout.addWidget(refresh_button)
        button_layout.addStretch()
        left_layout.addLayout(button_layout)

        # --- New Virtualized Gallery ---
        self.gallery_view = QtWidgets.QListView()
        self.gallery_view.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self.gallery_view.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.gallery_view.setMovement(QtWidgets.QListView.Movement.Static)
        self.gallery_view.setSpacing(10)
        self.gallery_view.setUniformItemSizes(True) # Performance boost

        self.thumbnail_delegate = ThumbnailDelegate(self)
        self.gallery_view.setItemDelegate(self.thumbnail_delegate)
        left_layout.addWidget(self.gallery_view)

        # Connect scroll bar signals for lazy loading
        self.gallery_view.verticalScrollBar().valueChanged.connect(self._request_visible_thumbnails)

        
        # --- Middle Panel (Metadata) ---
        metadata_container = QtWidgets.QWidget()
        metadata_layout = QtWidgets.QVBoxLayout(metadata_container)

        metadata_layout.addWidget(QtWidgets.QLabel("Positive Prompt"))
        self.positive_prompt_text = QtWidgets.QTextEdit()
        metadata_layout.addWidget(self.positive_prompt_text)

        metadata_layout.addWidget(QtWidgets.QLabel("Negative Prompt"))
        self.negative_prompt_text = QtWidgets.QTextEdit()
        metadata_layout.addWidget(self.negative_prompt_text)

        metadata_layout.addWidget(QtWidgets.QLabel("Parameters"))
        self.params_text = QtWidgets.QTextEdit()
        metadata_layout.addWidget(self.params_text)

        metadata_layout.addWidget(QtWidgets.QLabel("Generation Details"))
        self.gen_details_text = QtWidgets.QTextEdit()
        metadata_layout.addWidget(self.gen_details_text)

        save_button = QtWidgets.QPushButton("Save Metadata")
        save_button.clicked.connect(self.save_metadata)
        metadata_layout.addWidget(save_button)

        # --- Right Panel (Image Preview) ---
        self.preview_label = QtWidgets.QLabel("Image Preview")
        self.preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # --- Splitters ---
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        right_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        right_splitter.addWidget(metadata_container)
        right_splitter.addWidget(self.preview_label)
        right_splitter.setSizes([400, 500])

        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([500, 1100])

        main_layout.addWidget(main_splitter)

    def _setup_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        view_menu = menu_bar.addMenu("&View")

        # Add the theme menu
        theme_menu = ThemeManager(self)
        view_menu.addMenu(theme_menu)

        open_action = QtGui.QAction("&Open Folder...", self)
        open_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_action)

        refresh_action = QtGui.QAction("&Refresh Folder", self)
        refresh_action.triggered.connect(self.refresh_folder)
        file_menu.addAction(refresh_action)

    def open_folder(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.current_folder_path = folder_path
            print(f"[View] Folder selected: {self.current_folder_path}")
            self.gallery_view.setModel(None) # Clear the view
            self.model.scan_directory(self.current_folder_path)

    def refresh_folder(self):
        if self.current_folder_path:
            print(f"[View] Refreshing folder: {self.current_folder_path}")
            self.gallery_view.setModel(None) # Clear the view
            self.model.scan_directory(self.current_folder_path)
        else:
            print("[View] No folder currently open to refresh.")

    def on_model_ready(self, model):
        """Slot to receive the file model and set it on the view."""
        print(f"[View] Model ready with {model.rowCount(None)} items.")
        self.gallery_view.setModel(model)
        self.gallery_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        # Initial thumbnail load
        self._request_visible_thumbnails()

    def _request_visible_thumbnails(self):
        """Request thumbnails for only the visible items in the view."""
        model = self.gallery_view.model()
        if not model:
            return

        viewport_rect = self.gallery_view.viewport().rect()

        for row in range(model.rowCount(None)):
            index = model.index(row, 0)
            item_rect = self.gallery_view.visualRect(index)

            # Request thumbnail only if item is visible and not already cached
            if item_rect.intersects(viewport_rect):
                file_path = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
                if file_path not in self.thumbnail_cache:
                    self.model.request_thumbnail(file_path)


    def on_selection_changed(self, selected, deselected):
        """Handle selection changes in the QListView."""
        indexes = selected.indexes()
        if not indexes:
            return
        
        index = indexes[0]
        file_path = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        self.on_thumbnail_clicked(file_path)

    def on_thumbnail_clicked(self, file_path):
        """Slot to handle when a thumbnail is clicked."""
        print(f"[View] Thumbnail {file_path} was selected.")
        self.current_file_path = file_path
        self.model.request_full_image(file_path)
        self.model.request_metadata(file_path)

    def on_thumbnail_ready(self, file_path, pixmap):
        # This is where the magic happens for the delegate
        # We store the pixmap in a cache
        self.thumbnail_cache[file_path] = pixmap
        # Find the item in the model and tell the view to repaint it
        model = self.gallery_view.model()
        if not model:
            return
        # This is inefficient, a direct mapping would be better, but it works for now
        for row in range(model.rowCount(None)):
            index = model.index(row, 0)
            if index.data(QtCore.Qt.ItemDataRole.DisplayRole) == file_path:
                self.gallery_view.update(index)
                break

    def on_full_image_ready(self, pixmap):
        """Slot to receive the full image and display it."""
        print("[View] Full image received, updating preview.")
        self.preview_label.setPixmap(pixmap)

    def on_metadata_ready(self, file_path, metadata):
        """Slot to receive metadata and display it."""
        import json
        print(f"[View] Metadata received for {file_path}")

        # Use the new parser
        parser = MetadataParser(metadata)
        parsed_data = parser.parse()

        # The 'generation_details' can be a dict, so we format it for display
        gen_details = parsed_data.get('generation_details', '')
        if isinstance(gen_details, dict):
            gen_details_text = json.dumps(gen_details, indent=4)
        else:
            gen_details_text = str(gen_details)

        # Populate the UI fields
        self.params_text.setText(parsed_data.get('parameters', ''))
        self.gen_details_text.setText(gen_details_text)
        self.positive_prompt_text.setText(parsed_data.get('positive_prompt', ''))
        self.negative_prompt_text.setText(parsed_data.get('negative_prompt', ''))

    def save_metadata(self):
        """Slot to handle the save metadata button click."""
        if not self.current_file_path:
            print("[View] No file selected to save metadata for.")
            return

        print(f"[View] Save button clicked for: {self.current_file_path}")

        # For now, we only support reconstructing A1111 metadata
        # We can add more sophisticated reconstruction logic later.
        new_metadata_str = self._reconstruct_a1111_metadata()

        if new_metadata_str:
            print("[View] WARNING: This will overwrite the entire metadata chunk.")
            print("[View] Any non-standard or unrecognized metadata will be lost.")
            self.model.save_metadata(self.current_file_path, new_metadata_str)

    def _reconstruct_a1111_metadata(self):
        """Reconstructs the A1111 'parameters' string from the UI fields."""
        try:
            positive_prompt = self.positive_prompt_text.toPlainText().strip()
            negative_prompt = self.negative_prompt_text.toPlainText().strip()
            details_string = self.params_text.toPlainText().strip()

            # Assemble the final string
            final_string = positive_prompt
            if negative_prompt:
                final_string += f"\nNegative prompt: {negative_prompt}"
            final_string += f"\n{details_string}"
            
            return final_string.strip()

        except Exception as e:
            print(f"[View] Error reconstructing metadata: {e}")
            return None

    def on_metadata_saved(self, file_path):
        """Slot to receive confirmation that metadata was saved."""
        print(f"[View] Successfully saved metadata for: {file_path}")
        # We could show a status bar message here in the future
