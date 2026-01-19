from PySide6.QtCore import QThread, Signal
import time
import json

class MockUploadWorker(QThread):
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)

    def __init__(self, data):
        super().__init__()
        self.data = data

    def run(self):
        print("\n" + "="*60)
        print("🚀 [MOCK UPLOAD] MEMULAI SIMULASI UPLOAD")
        print("="*60)
        
        # 1. VALIDASI DATA (Log Payload)
        # Ini menjawab: "gimana ngecek judul deskripsi tag schedule akurat?"
        payload_log = json.dumps(self.data, indent=4, default=str)
        print(f"📦 PAYLOAD YANG DITERIMA DARI GUI:\n{payload_log}")
        
        print("\n⏳ Simulasi progress bar berjalan...")
        
        # 2. Simulasi Proses (Cepat)
        for i in range(0, 101, 10):
            time.sleep(0.1) # Percepat waktu untuk testing (0.1s per step)
            self.progress_signal.emit(i)
            print(f"   --> Upload Progress: {i}%")

        # 3. Selesai
        print("="*60)
        print("✅ [MOCK UPLOAD] SELESAI. TIDAK ADA DATA DIKIRIM KE YOUTUBE.")
        print("="*60 + "\n")
        
        self.finished_signal.emit(True, "Simulated Success")

class MockOAuthWorker(QThread):
    finished = Signal(bool, str)
    def __init__(self, channel_name):
        super().__init__()
    def run(self):
        time.sleep(1)
        self.finished.emit(True, "Mock Authorization Successful!")