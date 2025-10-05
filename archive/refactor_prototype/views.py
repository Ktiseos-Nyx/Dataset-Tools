# refactor_prototype/views.py

import os
from qtpy import QtCore, QtWidgets, QtGui
from model import DataManager, ThumbnailCache
from theme_manager import ThemeManager
from metadata_parser import MetadataParser

class ThumbnailDelegate(QtWidgets.QStyledItemDelegate):
    """
    Delegate for painting thumbnails in the list view.
    NOW WITH: Better filename display (no more jank!)
    """
    def __init__(self, parent=None):
        super(ThumbnailDelegate, self).__init__(parent)
        self.thumb_size = 140
        self.padding = 5

    def paint(self, painter, option, index):
        # Get the file path from the model
        file_path = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        file_name = os.path.basename(file_path)

        painter.save()

        # Draw background and selection state
        style = option.widget.style() if option.widget else QtWidgets.QApplication.style()
        style.drawPrimitive(QtWidgets.QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)

        # Draw thumbnail
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
            # Show a placeholder for loading thumbnails
            painter.fillRect(thumb_rect, QtGui.QColor("#2a2a2a"))
            painter.setPen(QtGui.QColor("#666"))
            painter.drawText(thumb_rect, QtCore.Qt.AlignmentFlag.AlignCenter, "Loading...")

        # Draw filename with better formatting
        text_rect = QtCore.QRect(
            option.rect.x() + self.padding,
            thumb_rect.bottom() + self.padding,
            option.rect.width() - (2 * self.padding),
            option.rect.height() - self.thumb_size - (3 * self.padding)
        )
        
        # Set text color based on selection
        text_color = option.palette.highlightedText().color() if (option.state & QtWidgets.QStyle.StateFlag.State_Selected) else option.palette.text().color()
        painter.setPen(text_color)
        
        # Use elided text (adds ... if too long) instead of word wrap
        font_metrics = painter.fontMetrics()
        elided_text = font_metrics.elidedText(
            file_name, 
            QtCore.Qt.TextElideMode.ElideMiddle,  # Keeps start and end of filename visible
            text_rect.width()
        )
        
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter, elided_text)

        painter.restore()

    def sizeHint(self, option, index):
        # Size of each item in the grid
        return QtCore.QSize(self.thumb_size + (2 * self.padding), self.thumb_size + 50)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dataset Tools - Improved Refactor")
        self.resize(1600, 900)

        self.current_folder_path = None
        self.current_file_path = None
        
        # NEW: Use the smart cache manager instead of a basic dict
        self.thumbnail_cache = ThumbnailCache(max_size=200)
        self.thumbnails_requested = set() # Keeps track of thumbnails we've asked for

        # MVC Setup
        self.model = DataManager()
        self.model.model_ready.connect(self.on_model_ready)
        self.model.thumbnail_ready.connect(self.on_thumbnail_ready)
        self.model.full_image_ready.connect(self.on_full_image_ready)
        self.model.metadata_ready.connect(self.on_metadata_ready)
        self.model.metadata_saved.connect(self.on_metadata_saved)
        
        # NEW: Connect progress and error signals
        self.model.progress_update.connect(self.on_progress_update)
        self.model.error_occurred.connect(self.on_error_occurred)
        
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

        # Gallery view with better settings
        self.gallery_view = QtWidgets.QListView()
        self.gallery_view.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self.gallery_view.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.gallery_view.setMovement(QtWidgets.QListView.Movement.Static)
        self.gallery_view.setSpacing(10)
        self.gallery_view.setUniformItemSizes(True)
        
        # NEW: Better scrolling behavior
        self.gallery_view.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.thumbnail_delegate = ThumbnailDelegate(self)
        self.gallery_view.setItemDelegate(self.thumbnail_delegate)
        left_layout.addWidget(self.gallery_view)

        # Connect scroll bar for lazy loading
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
        self.preview_label = QtWidgets.QLabel("No image selected")
        self.preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("QLabel { background-color: #1a1a1a; border-radius: 4px; }")

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
        
        # NEW: Add a status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _setup_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        view_menu = menu_bar.addMenu("&View")

        # Add the theme menu
        theme_menu = ThemeManager(self)
        view_menu.addMenu(theme_menu)

        open_action = QtGui.QAction("&Open Folder...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_action)

        refresh_action = QtGui.QAction("&Refresh Folder", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_folder)
        file_menu.addAction(refresh_action)

    def open_folder(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.current_folder_path = folder_path
            print(f"[View] Folder selected: {self.current_folder_path}")
            
            # Clear everything
            self.gallery_view.setModel(None)
            self.thumbnail_cache.clear()
            self.current_file_path = None
            
            # Clear metadata display
            self.positive_prompt_text.clear()
            self.negative_prompt_text.clear()
            self.params_text.clear()
            self.gen_details_text.clear()
            self.preview_label.setText("Loading folder...")
            
            # Start scanning
            self.model.scan_directory(self.current_folder_path)

    def refresh_folder(self):
        if self.current_folder_path:
            print(f"[View] Refreshing folder: {self.current_folder_path}")
            
            # Clear and rescan
            self.gallery_view.setModel(None) # Clear the view
            self.thumbnail_cache.clear()
            self.thumbnails_requested.clear()
            self.model.scan_directory(self.current_folder_path)
        else:
            self.status_bar.showMessage("No folder currently open", 3000)

    def on_model_ready(self, model):
        """Slot to receive the file model and set it on the view."""
        print(f"[View] Model ready with {model.rowCount(None)} items.")
        self.gallery_view.setModel(model)
        self.gallery_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        # Initial thumbnail load
        self._request_visible_thumbnails()
        
        self.status_bar.showMessage(f"Loaded {model.rowCount(None)} images")

    def _request_visible_thumbnails(self):
        """Request thumbnails for only the visible items in the view."""
        model = self.gallery_view.model()
        if not model:
            return

        viewport_rect = self.gallery_view.viewport().rect()

        for row in range(model.rowCount(None)):
            index = model.index(row, 0)
            item_rect = self.gallery_view.visualRect(index)

            # Request thumbnail only if item is visible and not already cached or requested
            if item_rect.intersects(viewport_rect):
                file_path = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
                if file_path and self.thumbnail_cache.get(file_path) is None and file_path not in self.thumbnails_requested:
                    self.thumbnails_requested.add(file_path)
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
        print(f"[View] Image selected: {os.path.basename(file_path)}")
        self.current_file_path = file_path
        
        # Show loading state
        self.preview_label.setText("Loading...")
        
        # Request full image and metadata
        self.model.request_full_image(file_path)
        self.model.request_metadata(file_path)

    def on_thumbnail_ready(self, file_path, pixmap):
        """
        NEW: Uses the smart cache and fast index lookup
        instead of searching through all items!
        """
        # Store in cache
        self.thumbnail_cache.put(file_path, pixmap)
        
        # Find and update the specific item
        model = self.gallery_view.model()
        if not model:
            return
        
        # Fast O(1) lookup instead of O(n) search!
        index = model.get_index_for_path(file_path)
        if index:
            self.gallery_view.update(index)

    def on_full_image_ready(self, pixmap):
        """Slot to receive the full image and display it."""
        self.preview_label.setPixmap(pixmap)

    def on_metadata_ready(self, file_path, metadata):
        """Slot to receive metadata and display it."""
        import json
        
        # Use the parser
        parser = MetadataParser(metadata)
        parsed_data = parser.parse()

        # Format generation details for display
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
        
        # Update status bar with tool info
        tool = parsed_data.get('tool', 'Unknown')
        self.status_bar.showMessage(f"Loaded metadata from: {tool}")

    def save_metadata(self):
        """Slot to handle the save metadata button click."""
        if not self.current_file_path:
            QtWidgets.QMessageBox.warning(
                self,
                "No File Selected",
                "Please select an image before saving metadata."
            )
            return

        print(f"[View] Save button clicked for: {self.current_file_path}")

        # Reconstruct A1111 metadata from UI fields
        new_metadata_str = self._reconstruct_a1111_metadata()

        if new_metadata_str:
            # Warn the user about overwriting
            reply = QtWidgets.QMessageBox.question(
                self,
                "Confirm Save",
                "This will overwrite the existing metadata.\nAny non-standard metadata will be lost.\n\nContinue?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No
            )
            
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
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
            if details_string:
                final_string += f"\n{details_string}"
            
            return final_string.strip()

        except Exception as e:
            print(f"[View] Error reconstructing metadata: {e}")
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to reconstruct metadata: {str(e)}"
            )
            return None

    def on_metadata_saved(self, file_path):
        """Slot to receive confirmation that metadata was saved."""
        print(f"[View] Successfully saved metadata for: {file_path}")
        QtWidgets.QMessageBox.information(
            self,
            "Success",
            f"Metadata saved successfully!\n{os.path.basename(file_path)}"
        )
    
    # NEW: Progress and error handling
    def on_progress_update(self, message):
        """Display progress updates in the status bar."""
        self.status_bar.showMessage(message, 2000)
    
    def on_error_occurred(self, error_message):
        """Show user-friendly error dialogs."""
        QtWidgets.QMessageBox.critical(
            self,
            "Error",
            error_message
        )
        self.status_bar.showMessage("Error occurred", 5000)