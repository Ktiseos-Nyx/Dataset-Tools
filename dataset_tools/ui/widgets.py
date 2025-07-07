# dataset_tools/ui/widgets.py

from dataclasses import dataclass

from PyQt6.QtCore import QThread, pyqtSignal


@dataclass
class FileLoadResult:
    """Result from file loading operation."""

    folder_path: str
    image_files: list[str] = None
    text_files: list[str] = None
    model_files: list[str] = None
    selected_file: str | None = None


class FileLoader(QThread):
    """Simple file loader for compatibility."""

    result_ready = pyqtSignal(object)

    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        """Executes the file loading process and emits a FileLoadResult

        with empty lists for images, texts, and models.

        Emits:
            result_ready (FileLoadResult): Signal emitted with an empty

            FileLoadResult containing the current folder_path.
        """
        # Basic implementation - just emit empty result for now
        result = FileLoadResult(folder_path=self.folder_path, image_files=[], text_files=[], model_files=[])
        self.result_ready.emit(result)
