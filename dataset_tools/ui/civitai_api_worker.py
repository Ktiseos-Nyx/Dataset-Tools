# dataset_tools/ui/civitai_api_worker.py

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from .. import civitai_api


class CivitaiInfoWorkerSignals(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)


class CivitaiInfoWorker(QRunnable):
    def __init__(self, ids_to_fetch, file_path=None):
        super().__init__()
        self.ids_to_fetch = ids_to_fetch
        self.file_path = file_path  # Track which file this worker is for
        self.signals = CivitaiInfoWorkerSignals()

    def _fetch_with_retry(self, fetch_func, item_id, max_retries=3, timeout=30):
        """Fetch with exponential backoff retry logic for rate limits."""
        start_time = time.time()
        retry_delays = [2, 4, 8]  # Exponential backoff: 2s, 4s, 8s

        for attempt in range(max_retries):
            # Check if we've exceeded total timeout
            if time.time() - start_time > timeout:
                return None

            try:
                result = fetch_func(item_id)
                return result
            except Exception as e:
                error_str = str(e).lower()
                # Check if this is a rate limit error
                is_rate_limit = ("429" in error_str or "rate limit" in error_str or
                                 "too many requests" in error_str)

                # If rate limited and we have retries left, wait and retry
                if is_rate_limit and attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    time.sleep(delay)
                    continue

                # If not rate limited or out of retries, return None
                return None

        return None

    def _fetch_item(self, item):
        """Fetch a single item (model or version) with retry logic."""
        results = {}

        if "model_id" in item:
            model_id = item["model_id"]
            model_info = self._fetch_with_retry(civitai_api.get_model_info_by_id, model_id)
            if model_info:
                results[f"model_{model_id}"] = model_info

        if "version_id" in item:
            version_id = item["version_id"]
            version_info = self._fetch_with_retry(civitai_api.get_model_version_info_by_id, version_id)
            if version_info:
                results[f"version_{version_id}"] = version_info

        return results

    def run(self):
        results = {}
        try:
            # Use ThreadPoolExecutor for parallel fetching with 5 workers
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Submit all fetch tasks
                future_to_item = {executor.submit(self._fetch_item, item): item
                                  for item in self.ids_to_fetch}

                # Collect results as they complete
                for future in as_completed(future_to_item):
                    try:
                        item_results = future.result()
                        results.update(item_results)
                    except Exception as e:
                        # Log individual item failures but continue processing others
                        pass

            try:
                self.signals.finished.emit(results)
            except RuntimeError:
                # Signal object was deleted (window closed, etc.)
                pass
        except Exception as e:
            try:
                self.signals.error.emit(str(e))
            except RuntimeError:
                # Signal object was deleted
                pass
