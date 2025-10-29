# dataset_tools/ui/civitai_api_worker.py

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from .. import civitai_api


class CivitaiInfoWorkerSignals(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)


class CivitaiInfoWorker(QRunnable):
    def __init__(self, ids_to_fetch):
        super().__init__()
        self.ids_to_fetch = ids_to_fetch
        self.signals = CivitaiInfoWorkerSignals()

    def run(self):
        results = {}
        try:
            for item in self.ids_to_fetch:
                if "model_id" in item:
                    model_id = item["model_id"]
                    model_info = civitai_api.get_model_info_by_id(model_id)
                    if model_info:
                        results[f"model_{model_id}"] = model_info

                if "version_id" in item:
                    version_id = item["version_id"]
                    version_info = civitai_api.get_model_version_info_by_id(version_id)
                    if version_info:
                        results[f"version_{version_id}"] = version_info

            self.signals.finished.emit(results)
        except Exception as e:
            self.signals.error.emit(str(e))
