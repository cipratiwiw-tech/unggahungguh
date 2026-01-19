import sys
import os
from unittest.mock import patch

# Tambahkan parent directory ke path agar bisa import modul utama
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# --- 1. SETUP MOCKS ---
from tests.mock_workers import MockUploadWorker, MockOAuthWorker

def mock_check_status(channel_name):
    """
    Memalsukan status auth agar selalu hijau (Connected),
    jadi kamu bisa langsung tes tombol Upload tanpa login beneran.
    """
    return "TEST MODE (SAFE)", "#a6e3a1" # Hijau

# --- 2. JALANKAN APLIKASI DENGAN PATCH ---
def run_safe_app():
    print("🛡️  STARTING APPLICATION IN SAFE MODE (DRY RUN) 🛡️")
    print("-----------------------------------------------------")
    print("• Upload Youtube  : DISABLED (Diganti Mock Logger)")
    print("• OAuth Login     : BYPASSED (Status selalu Connected)")
    print("• Files           : Aman (Tidak ada yang terupload)")
    print("-----------------------------------------------------")

    # PATCHING: Mengganti class asli dengan class palsu secara global
    # Target: 'core.workers.UploadWorker' diganti MockUploadWorker
    # Target: 'core.auth_manager.AuthManager.check_status' diganti mock_check_status
    
    with patch('core.workers.UploadWorker', side_effect=MockUploadWorker) as MockUpload, \
         patch('core.auth_manager.OAuthWorker', side_effect=MockOAuthWorker) as MockOAuth, \
         patch('core.auth_manager.AuthManager.check_status', side_effect=mock_check_status):
        
        # Import main window SETELAH patch dipasang
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow

        app = QApplication(sys.argv)
        
        # Opsional: Beri tanda visual di window title
        window = MainWindow()
        window.setWindowTitle(window.windowTitle() + " [SAFE MODE / DRY RUN]")
        window.setStyleSheet(window.styleSheet() + """
            QMainWindow { border: 2px solid #a6e3a1; }
        """)
        
        window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    run_safe_app()