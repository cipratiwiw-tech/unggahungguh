# gui/main_window.py
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QStackedWidget, QPushButton, QFrame, QFileDialog, QMessageBox, 
    QDialog, QComboBox, QLineEdit, QDialogButtonBox, QFormLayout,
    QSplitter, QSizePolicy # Tambahkan QSplitter
)
from PySide6.QtCore import Qt
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
        self.splitter.setHandleWidth(2) # Garis pemisah tipis
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #2a2a2a;
            }
            QSplitter::handle:hover {
                background-color: #cc0000; /* Warna merah saat di-hover */
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
        
        self.btn_secret = QPushButton("Add Secret")
        self.btn_secret.clicked.connect(self.action_add_secret)
        self.btn_secret.setVisible(False)
        self.btn_secret.setStyleSheet("border: 1px solid #555; color: #aaa;")
        ac_layout.addWidget(self.btn_secret)
        
        self.btn_oauth = QPushButton("OAuth Login")
        self.btn_oauth.clicked.connect(self.action_oauth)
        self.btn_oauth.setVisible(False)
        self.btn_oauth.setStyleSheet("border: 1px solid #cc0000; color: #cc0000; font-weight: bold;")
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
        self.splitter.setSizes([290, 990])
        self.splitter.setCollapsible(0, False) # Sidebar tidak bisa di-collapse total

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
                
                self.stack.setCurrentWidget(self.channel_views[identifier])
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
        if not hasattr(self, 'current_active_id'): return
        path, _ = QFileDialog.getOpenFileName(self, "Pilih client_secret.json", "", "JSON (*.json)")
        if path:
            base_dir = os.path.join("channels", self.current_active_cat, self.current_active_chan)
            import shutil
            shutil.copy(path, os.path.join(base_dir, "client_secret.json"))
            QMessageBox.information(self, "Sukses", "Client Secret berhasil diupdate.")
            
            if self.current_active_id in self.channel_views:
                self.channel_views[self.current_active_id].check_auth_status()

    def action_oauth(self):
        if not hasattr(self, 'current_active_id'): return
        self.oauth_worker = OAuthWorker(self.current_active_cat, self.current_active_chan)
        self.oauth_worker.finished.connect(self.on_oauth_finished)
        self.oauth_worker.start()

    def on_oauth_finished(self, success, msg):
        if success:
            QMessageBox.information(self, "Sukses", "Login Berhasil!")
        else:
            QMessageBox.critical(self, "Gagal", f"Login Gagal: {msg}")
            
        if self.current_active_id in self.channel_views:
            self.channel_views[self.current_active_id].check_auth_status()