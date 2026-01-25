# gui/main_window.py
import os
import shutil
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QStackedWidget, QPushButton, QFrame, QFileDialog, QMessageBox, 
    QDialog, QComboBox, QLineEdit, QDialogButtonBox, QFormLayout,
    QSplitter, QSizePolicy, QApplication, 
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QClipboard
from gui.sidebar import Sidebar
from gui.dashboard import Dashboard
from gui.channel_page import ChannelPage
from gui.styles import GLOBAL_STYLESHEET
from utils import get_channel_structure, create_new_channel, create_category 
from core.auth_manager import AuthManager, OAuthWorker

class AddChannelDialog(QDialog):
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Channel")
        self.setModal(True)
        self.setStyleSheet("""
            QDialog { background: #2f2f2f; color: white; }
            QLabel { color: white; }
            QLineEdit, QComboBox { 
                background: #181818; border: 1px solid #555; 
                color: white; padding: 5px; 
            }
        """)
        
        layout = QFormLayout(self)
        
        self.combo_cat = QComboBox()
        self.combo_cat.addItems(categories)
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("e.g. Gameplay Highlights")
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        
        layout.addRow("Category:", self.combo_cat)
        layout.addRow("Channel Name:", self.inp_name)
        layout.addWidget(btns)

    def get_data(self):
        return self.combo_cat.currentText(), self.inp_name.text().strip()

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

        # --- SETUP SPLITTER (Agar Sidebar bisa digeser) ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(2)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #2a2a2a;
            }
            QSplitter::handle:hover {
                background-color: #cc0000; 
            }
        """)

        # 1. Sidebar (Left Pane)
        self.sidebar = Sidebar()
        self.sidebar.selection_changed.connect(self.navigate)
        self.sidebar.add_channel_clicked.connect(self.add_new_channel_flow)
        self.sidebar.add_category_clicked.connect(self.add_category_flow)
        
        self.sidebar.channel_renamed.connect(self.handle_channel_renamed)
        self.sidebar.channel_deleted.connect(self.handle_channel_deleted)
        
        self.splitter.addWidget(self.sidebar)

        # 2. Content (Right Pane)
        content_col = QWidget()
        content_layout = QVBoxLayout(content_col)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # --- TOP BAR ---
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(60)
        self.top_bar.setStyleSheet("background-color: #212121; border-bottom: 1px solid #3f3f3f;")
        tb_layout = QHBoxLayout(self.top_bar)
        tb_layout.setContentsMargins(20, 0, 20, 0)
        
        self.lbl_page_title = QLabel("Dashboard Portofolio")
        self.lbl_page_title.setStyleSheet("font-size: 18px; font-weight: bold; border: none;")
        tb_layout.addWidget(self.lbl_page_title)
        
        tb_layout.addStretch()
        
        self.action_container = QFrame()
        ac_layout = QHBoxLayout(self.action_container)
        ac_layout.setContentsMargins(0, 0, 15, 0)
        ac_layout.setSpacing(10)
        
        self.btn_secret = QPushButton("Add Secret")
        self.btn_secret.setCursor(Qt.PointingHandCursor)
        self.btn_secret.clicked.connect(self.action_add_secret)
        self.btn_secret.setVisible(False)
        self.btn_secret.setStyleSheet("""
            QPushButton { border: 1px solid #555; color: #ccc; background: #333; }
            QPushButton:hover { background: #444; border-color: #777; color: white; }
        """)
        ac_layout.addWidget(self.btn_secret)
        
        self.btn_oauth = QPushButton("OAuth Login")
        self.btn_oauth.setCursor(Qt.PointingHandCursor)
        self.btn_oauth.clicked.connect(self.action_oauth)
        self.btn_oauth.setVisible(False)
        self.btn_oauth.setStyleSheet("""
            QPushButton { border: 1px solid #cc0000; color: white; background: #cc0000; font-weight: bold; }
            QPushButton:hover { background: #e60000; border-color: #ff3333; }
        """)
        ac_layout.addWidget(self.btn_oauth)
        
        tb_layout.addWidget(self.action_container)
        
        content_layout.addWidget(self.top_bar)

        # --- STACKED WIDGET ---
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        self.dashboard_view = Dashboard()
        self.stack.addWidget(self.dashboard_view)
        
        # Cache for Channel Pages
        self.channel_views = {} 

        # Add Content to Splitter
        self.splitter.addWidget(content_col)

        # Set Initial Sizes (Sidebar 290px, Content sisa)
        self.splitter.setSizes([220, 990])
        self.splitter.setCollapsible(0, False)

        main_layout.addWidget(self.splitter)
        self.refresh_sidebar()

    def refresh_sidebar(self):
        structure = get_channel_structure()
        self.sidebar.load_channels(structure)

    def navigate(self, mode, identifier):
        self.lbl_page_title.setText(identifier)
        
        if mode == "global":
            self.stack.setCurrentWidget(self.dashboard_view)
            self.toggle_auth_buttons(False)
        else:
            if "/" in identifier:
                cat_name, chan_name = identifier.split("/", 1)
                
                if identifier not in self.channel_views:
                    page = ChannelPage(cat_name, chan_name)
                    self.channel_views[identifier] = page
                    self.stack.addWidget(page)
                
                # Update current view
                current_page = self.channel_views[identifier]
                self.stack.setCurrentWidget(current_page)
                
                # Cek ulang status auth setiap kali navigasi
                current_page.check_auth_status()
                
                self.toggle_auth_buttons(True)
                self.current_active_id = identifier 
                self.current_active_cat = cat_name
                self.current_active_chan = chan_name

    def toggle_auth_buttons(self, visible):
        self.btn_secret.setVisible(visible)
        self.btn_oauth.setVisible(visible)
        self.action_container.setVisible(visible)

    def add_category_flow(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New Category", "Category Name:")
        if ok and name.strip():
            try:
                create_category(name.strip())
                self.refresh_sidebar()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def add_new_channel_flow(self):
        structure = get_channel_structure()
        categories = list(structure.keys())
        
        if not categories:
            QMessageBox.warning(self, "No Categories", "Please create a Category first!")
            return

        dialog = AddChannelDialog(categories, self)
        if dialog.exec():
            cat, name = dialog.get_data()
            if name:
                try:
                    # Buat file dummy secret sementara agar folder structure terbentuk
                    dummy_secret = "client_secret.json" 
                    if not os.path.exists(dummy_secret):
                        with open(dummy_secret, "w") as f: f.write("{}")
                    
                    create_new_channel(cat, name, dummy_secret)
                    self.refresh_sidebar()
                    self.sidebar.select_channel(cat, name)
                    
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))

    def handle_channel_renamed(self, category, old_name, new_name):
        old_id = f"{category}/{old_name}"
        new_id = f"{category}/{new_name}"
        
        if old_id in self.channel_views:
            page = self.channel_views.pop(old_id)
            page.update_channel_identity(category, new_name)
            self.channel_views[new_id] = page
            
        if self.lbl_page_title.text() == old_id:
            self.lbl_page_title.setText(new_id)
            self.current_active_id = new_id
            self.current_active_chan = new_name

    def handle_channel_deleted(self, channel_name):
        self.refresh_sidebar()
        self.navigate("global", "Dashboard Portofolio")
        self.channel_views = {}

    def action_add_secret(self):
        """Mengambil file JSON secret dari user dan menyimpannya di folder channel"""
        if not hasattr(self, 'current_active_id'): return
        
        path, _ = QFileDialog.getOpenFileName(self, "Pilih client_secret.json", "", "JSON (*.json)")
        if path:
            try:
                base_dir = os.path.join("channels", self.current_active_cat, self.current_active_chan)
                target_path = os.path.join(base_dir, "client_secret.json")
                
                # Copy file
                shutil.copy(path, target_path)
                QMessageBox.information(self, "Sukses", "Client Secret berhasil disimpan.\nSilakan klik tombol 'OAuth Login'.")
                
                # Refresh UI Status
                if self.current_active_id in self.channel_views:
                    self.channel_views[self.current_active_id].check_auth_status()
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menyimpan secret: {str(e)}")

    def action_oauth(self):
        """Memulai proses login OAuth Google"""
        if not hasattr(self, 'current_active_id'): return
        
        self.btn_oauth.setEnabled(False)
        self.btn_oauth.setText("Waiting...")
        
        self.oauth_worker = OAuthWorker(self.current_active_cat, self.current_active_chan)
        self.oauth_worker.finished.connect(self.on_oauth_finished)
        # [NEW] Connect signal URL
        self.oauth_worker.auth_url_signal.connect(self.on_auth_url_received)
        self.oauth_worker.start()
        self.oauth_worker.start()

    def on_auth_url_received(self, url):
        # Kita buat Dialog khusus agar user bisa copy link
        dialog = QDialog(self)
        dialog.setWindowTitle("Login YouTube")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet("background: #2f2f2f; color: white;")
        
        layout = QVBoxLayout(dialog)
        
        lbl_info = QLabel("Salin link di bawah ini dan buka di <b>Profil Browser</b> yang Anda inginkan:")
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)
        
        # Text Edit untuk URL (Read Only)
        txt_url = QLineEdit(url)
        txt_url.setReadOnly(True)
        txt_url.setStyleSheet("padding: 8px; border: 1px solid #555; background: #181818; color: #aaa;")
        layout.addWidget(txt_url)
        
        # Tombol Copy & Close
        btn_box = QHBoxLayout()
        btn_copy = QPushButton("Copy Link")
        btn_copy.setStyleSheet("background: #2ba640; color: white; font-weight: bold; padding: 8px;")
        btn_copy.clicked.connect(lambda: self.copy_to_clipboard(url, btn_copy))
        
        btn_close = QPushButton("Tutup (Menunggu Login...)")
        btn_close.clicked.connect(dialog.accept) # Tutup dialog tapi worker tetap jalan background
        
        btn_box.addWidget(btn_copy)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)
        
        # Tampilkan dialog secara non-modal (show) atau modal (exec)
        # Kita pakai show() agar user masih bisa akses app jika perlu, 
        # tapi exec() lebih aman agar fokus. Kita pakai exec().
        dialog.exec()

    def copy_to_clipboard(self, text, btn_sender):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        btn_sender.setText("Copied! ✔")
        QTimer.singleShot(2000, lambda: btn_sender.setText("Copy Link"))
        
        
    def on_oauth_finished(self, success, msg):
        self.btn_oauth.setEnabled(True)
        self.btn_oauth.setText("OAuth Login")
        
        if success:
            QMessageBox.information(self, "Sukses", "Login Berhasil! Token tersimpan.")
        else:
            QMessageBox.critical(self, "Gagal", f"Login Gagal:\n{msg}")
            
        # Refresh UI di Channel Page untuk update warna status
        if self.current_active_id in self.channel_views:
            self.channel_views[self.current_active_id].check_auth_status()