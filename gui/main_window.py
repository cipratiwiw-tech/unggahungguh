import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QStackedWidget, QPushButton, QFrame, QFileDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from gui.sidebar import Sidebar
from gui.dashboard import Dashboard
from gui.channel_page import ChannelPage
from gui.styles import GLOBAL_STYLESHEET
from utils import get_existing_channels, create_new_channel
from core.auth_manager import AuthManager, OAuthWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UnggahUngguh - Studio Manager")
        self.resize(1280, 800)
        self.setStyleSheet(GLOBAL_STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar (Kiri)
        self.sidebar = Sidebar()
        self.sidebar.selection_changed.connect(self.navigate)
        self.sidebar.add_channel_clicked.connect(self.add_new_channel_flow)
        
        # CONNECT SIGNAL RENAME & DELETE
        self.sidebar.channel_renamed.connect(self.handle_channel_renamed)
        self.sidebar.channel_deleted.connect(self.handle_channel_deleted)
        
        main_layout.addWidget(self.sidebar)

        # 2. Konten Utama (Kanan)
        content_col = QWidget()
        content_layout = QVBoxLayout(content_col)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # --- TOP BAR ---
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(60)
        self.top_bar.setStyleSheet("""
            QFrame {
                background-color: #212121; 
                border-bottom: 1px solid #3f3f3f; 
            }
        """)
        tb_layout = QHBoxLayout(self.top_bar)
        tb_layout.setContentsMargins(20, 0, 20, 0)
        tb_layout.setSpacing(10)
        
        self.lbl_page_title = QLabel("Dashboard Portofolio")
        self.lbl_page_title.setStyleSheet("font-size: 18px; font-weight: bold; border: none;")
        tb_layout.addWidget(self.lbl_page_title)
        
        tb_layout.addStretch()
        
        # Action Buttons
        self.action_container = QFrame()
        self.action_container.setStyleSheet("border-right: 1px solid #3f3f3f; border-bottom: none; border-top: none; border-left: none;")
        ac_layout = QHBoxLayout(self.action_container)
        ac_layout.setContentsMargins(0, 0, 15, 0)
        
        self.btn_secret = QPushButton("Add Secret")
        self.btn_secret.clicked.connect(self.action_add_secret)
        self.btn_secret.setVisible(False)
        self.btn_secret.setStyleSheet("border: 1px solid #3f3f3f; font-size: 11px;")
        ac_layout.addWidget(self.btn_secret)
        
        self.btn_oauth = QPushButton("OAuth Login")
        self.btn_oauth.clicked.connect(self.action_oauth)
        self.btn_oauth.setVisible(False)
        self.btn_oauth.setStyleSheet("border: 1px solid #cc0000; color: #cc0000; font-weight: bold; font-size: 11px;")
        ac_layout.addWidget(self.btn_oauth)
        
        tb_layout.addWidget(self.action_container)
        
        # Profile
        lbl_profile = QLabel("Admin User")
        lbl_profile.setStyleSheet("color: #aaaaaa; font-weight: bold; margin-left: 5px; border: none;")
        tb_layout.addWidget(lbl_profile)
        
        content_layout.addWidget(self.top_bar)

        # --- STACKED WIDGET ---
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        self.dashboard_view = Dashboard()
        self.stack.addWidget(self.dashboard_view)
        
        # Dictionary untuk menyimpan instance halaman per channel
        # Format: { "Nama Channel": WidgetPage }
        self.channel_views = {} 

        main_layout.addWidget(content_col)
        self.refresh_sidebar()

    def refresh_sidebar(self):
        channels = get_existing_channels()
        self.sidebar.load_channels(channels)

    def navigate(self, mode, title):
        self.lbl_page_title.setText(title)
        if mode == "global":
            self.stack.setCurrentWidget(self.dashboard_view)
            self.toggle_auth_buttons(False)
        else:
            channel_name = title
            
            # Logic: Jika halaman channel belum ada di memori, buat baru.
            # Karena di ChannelPage kita pakai Random Seed based on Name,
            # kontennya pasti unik per channel.
            if channel_name not in self.channel_views:
                page = ChannelPage(channel_name)
                self.channel_views[channel_name] = page
                self.stack.addWidget(page)
            
            self.stack.setCurrentWidget(self.channel_views[channel_name])
            self.toggle_auth_buttons(True)
            self.current_active_channel = channel_name

    def toggle_auth_buttons(self, visible):
        self.btn_secret.setVisible(visible)
        self.btn_oauth.setVisible(visible)
        if visible:
            self.action_container.show()
        else:
            self.action_container.hide()

    def add_new_channel_flow(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New Channel", "Nama Folder Channel:")
        if ok and name.strip():
            try:
                dummy_secret = "client_secret.json" 
                if not os.path.exists(dummy_secret):
                    with open(dummy_secret, "w") as f: f.write("{}")
                create_new_channel(name, dummy_secret)
                self.refresh_sidebar()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # --- HANDLERS UNTUK PERUBAHAN DI SIDEBAR ---

    def handle_channel_renamed(self, old_name, new_name):
        """Update dictionary views jika channel direname"""
        if old_name in self.channel_views:
            # Ambil page yang lama
            page = self.channel_views.pop(old_name)
            
            # Update properti internal page
            page.update_channel_identity(new_name)
            
            # Simpan dengan key baru
            self.channel_views[new_name] = page
            
        # Update UI jika kita sedang melihat page tersebut
        if self.lbl_page_title.text() == old_name:
            self.lbl_page_title.setText(new_name)
            self.current_active_channel = new_name

    def handle_channel_deleted(self, channel_name):
        """Hapus page dari memori dan stack jika channel dihapus"""
        if channel_name in self.channel_views:
            page = self.channel_views.pop(channel_name)
            self.stack.removeWidget(page)
            page.deleteLater() # Bersihkan memori
            
        # Jika kita sedang melihat channel yg dihapus, kembali ke dashboard
        if self.lbl_page_title.text() == channel_name:
            self.navigate("global", "Dashboard Portofolio")
            # Reset seleksi di sidebar (opsional, tapi sidebar biasanya clear sendiri itemnya)

    # --- TOP BAR ACTIONS ---

    def action_add_secret(self):
        if not hasattr(self, 'current_active_channel'): return
        path, _ = QFileDialog.getOpenFileName(self, "Pilih client_secret.json", "", "JSON (*.json)")
        if path:
            dest_dir = os.path.join("channels", self.current_active_channel)
            import shutil
            shutil.copy(path, os.path.join(dest_dir, "client_secret.json"))
            QMessageBox.information(self, "Sukses", "Client Secret berhasil diupdate.")
            self.channel_views[self.current_active_channel].check_auth_status()

    def action_oauth(self):
        if not hasattr(self, 'current_active_channel'): return
        reply = QMessageBox.question(
            self, "OAuth Authorization", 
            f"Buka browser untuk login channel '{self.current_active_channel}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.oauth_worker = OAuthWorker(self.current_active_channel)
            self.oauth_worker.finished.connect(self.on_oauth_finished)
            self.oauth_worker.start()

    def on_oauth_finished(self, success, msg):
        if success:
            QMessageBox.information(self, "Sukses", "Login Berhasil!")
        else:
            QMessageBox.critical(self, "Gagal", f"Login Gagal: {msg}")
        if self.current_active_channel in self.channel_views:
            self.channel_views[self.current_active_channel].check_auth_status()