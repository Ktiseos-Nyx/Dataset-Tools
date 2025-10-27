"""Metadata Panel - Encapsulated metadata display component."""

from PyQt6 import QtWidgets as Qw
from PyQt6 import QtGui
from PyQt6.QtCore import pyqtSignal


class MetadataPanel(Qw.QWidget):
    """Panel for displaying image generation metadata.

    This is a self-contained widget that manages its own UI and logic.
    No more scattered attributes on the main window!

    Signals:
        metadata_copied: Emitted when user copies metadata to clipboard
    """

    metadata_copied = pyqtSignal(str)  # Signal when metadata is copied

    def __init__(self, parent=None):
        """Initialize the metadata panel.

        Args:
            parent: Parent widget (usually MainWindow)
        """
        super().__init__(parent)
        self._init_ui()
        self._current_metadata = {}

    def _init_ui(self):
        """Initialize UI components."""
        layout = Qw.QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(15)

        # Add some stretch at top for better spacing
        layout.addStretch(1)

        # Positive Prompt Section
        self.positive_label = Qw.QLabel("Positive Prompt")
        layout.addWidget(self.positive_label)

        self.positive_box = Qw.QTextEdit()
        self.positive_box.setReadOnly(True)
        self.positive_box.setSizePolicy(
            Qw.QSizePolicy.Policy.Expanding,
            Qw.QSizePolicy.Policy.Preferred
        )
        self.positive_box.setWordWrapMode(QtGui.QTextOption.WrapMode.WordWrap)
        self.positive_box.setLineWrapMode(Qw.QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self.positive_box)

        # Negative Prompt Section
        self.negative_label = Qw.QLabel("Negative Prompt")
        layout.addWidget(self.negative_label)

        self.negative_box = Qw.QTextEdit()
        self.negative_box.setReadOnly(True)
        self.negative_box.setSizePolicy(
            Qw.QSizePolicy.Policy.Expanding,
            Qw.QSizePolicy.Policy.Preferred
        )
        self.negative_box.setWordWrapMode(QtGui.QTextOption.WrapMode.WordWrap)
        self.negative_box.setLineWrapMode(Qw.QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self.negative_box)

        # Generation Details Section
        self.details_label = Qw.QLabel("Generation Details & Metadata")
        layout.addWidget(self.details_label)

        self.details_box = Qw.QTextEdit()
        self.details_box.setReadOnly(True)
        self.details_box.setSizePolicy(
            Qw.QSizePolicy.Policy.Expanding,
            Qw.QSizePolicy.Policy.Preferred
        )
        self.details_box.setWordWrapMode(QtGui.QTextOption.WrapMode.WordWrap)
        self.details_box.setLineWrapMode(Qw.QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self.details_box)

        # Bottom stretch for balanced spacing
        layout.addStretch(1)

    def update_metadata(self, metadata_dict: dict):
        """Update all metadata fields from a dictionary.

        Args:
            metadata_dict: Dict with keys 'positive', 'negative', 'details'
        """
        self._current_metadata = metadata_dict

        self.positive_box.setPlainText(metadata_dict.get('positive', ''))
        self.negative_box.setPlainText(metadata_dict.get('negative', ''))
        self.details_box.setPlainText(metadata_dict.get('details', ''))

    def clear_metadata(self):
        """Clear all metadata fields."""
        self.positive_box.clear()
        self.negative_box.clear()
        self.details_box.clear()
        self._current_metadata = {}

    def get_all_metadata_text(self) -> str:
        """Get all metadata as formatted text for copying.

        Returns:
            Formatted string with all metadata
        """
        sections = []

        if self._current_metadata.get('positive'):
            sections.append(f"Positive Prompt:\n{self._current_metadata['positive']}")

        if self._current_metadata.get('negative'):
            sections.append(f"Negative Prompt:\n{self._current_metadata['negative']}")

        if self._current_metadata.get('details'):
            sections.append(f"Generation Details:\n{self._current_metadata['details']}")

        return "\n\n".join(sections)
