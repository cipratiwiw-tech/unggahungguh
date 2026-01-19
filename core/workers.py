from PySide6.QtCore import QThread, Signal
import time

class UploadWorker(QThread):
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)

    def __init__(self, data):
        super().__init__()
        self.data = data # Berisi video_path, title, privacyStatus, publishAt, dll

    def run(self):
        try:
            # 1. Simulasi Upload Video (Resumable)
            # Nanti gunakan: uploader.upload_video(...) dengan parameter self.data['privacyStatus']
            for i in range(1, 101, 2):
                time.sleep(0.05)
                self.progress_signal.emit(i)
            
            # 2. Simulasi Upload Thumbnail
            if self.data.get('thumbnail'):
                # Upload thumb logic here
                time.sleep(0.5)

            # 3. Log Data yang dikirim (Untuk verifikasi)
            print(f"UPLOAD SUCCESS: {self.data['title']}")
            print(f"--> Privacy: {self.data['privacyStatus']}")
            print(f"--> PublishAt: {self.data['publishAt']}")

            self.finished_signal.emit(True, "Success")

        except Exception as e:
            self.finished_signal.emit(False, str(e))