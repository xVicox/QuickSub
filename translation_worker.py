from PyQt5.QtCore import QThread, pyqtSignal, QObject
from pa_translator_service import PATranslatorService

class TranslationWorker(QObject):
    finished = pyqtSignal()  # Signal to notify when done

    def __init__(self, payload):
        super().__init__()
        self._translation_payload = payload

    def run(self):
        try:
            # init translator service
            service = PATranslatorService(payload=self._translation_payload)
            service.process_translation()
            self.finished.emit()
        except Exception as e:
            print(f"Worker error: {e}")