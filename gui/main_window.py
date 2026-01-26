import os
import shutil
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QStackedWidget, QPushButton, QFrame, QFileDialog, QMessageBox, 
    QDialog, QComboBox, QLineEdit, QDialogButtonBox, QFormLayout,
    QSplitter, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QTimer, QRect
from gui.sidebar import Sidebar
from gui.dashboard import Dashboard
from gui.channel_page import ChannelPage
from gui.styles import GLOBAL_STYLESHEET
from utils import get_channel_structure, create_new_channel, create_category 
from gui.animations import PageAnimator

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

        # --- SETUP SPLITTER ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(2)
        self.splitter.setStyleSheet("""
            QSplitter::handle { background-color: #2a2a2a; }
            QSplitter::handle:hover { background-color: #cc0000; }
        """)

        # 1. Sidebar
        self.sidebar = Sidebar()
        self.sidebar.selection_changed.connect(self.navigate)
        self.sidebar.add_channel_clicked.connect(self.add_new_channel_flow)
        self.sidebar.add_category_clicked.connect(self.add_category_flow)
        
        self.sidebar.channel_renamed.connect(self.handle_channel_renamed)
        self.sidebar.channel_deleted.connect(self.handle_channel_deleted)
        self.sidebar.category_renamed.connect(self.handle_category_renamed)
        
        self.splitter.addWidget(self.sidebar)

        # 2. Content
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
        
        # [DIHAPUS] Bagian tombol action (Secret/OAuth) karena sudah pindah ke ChannelPage
        tb_layout.addStretch()
        
        content_layout.addWidget(self.top_bar)
        
        # [TAMBAHAN PENTING] Inisialisasi variabel state
        self.current_active_id = None 
        
        # --- STACKED WIDGET ---
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        self.dashboard_view = Dashboard()
        self.stack.addWidget(self.dashboard_view)
        
        self.channel_views = {} 

        self.splitter.addWidget(content_col)
        self.splitter.setSizes([220, 990])
        self.splitter.setCollapsible(0, False)

        main_layout.addWidget(self.splitter)
        
        self.refresh_sidebar()

    # [DIHAPUS] def update_top_bar_auth_status() -> Sudah pindah logic-nya ke ChannelPage

    def refresh_sidebar(self):
        structure = get_channel_structure()
        self.sidebar.load_channels(structure)

    def navigate(self, mode, identifier, widget_sender=None):
        """
        Menangani perpindahan halaman.
        Sekarang dilengkapi logika anti-redundansi:
        Jika klik halaman yang sama, animasi tidak akan jalan.
        """
        
        # [LOGIKA BARU] Cek apakah user mengklik halaman yang sedang aktif
        if self.current_active_id == identifier:
            return # Hentikan proses, jangan lakukan apa-apa.
        
        # Update ID halaman aktif sekarang
        self.current_active_id = identifier
        
        target_widget = None
        
        if mode == "global":
            # --- Navigasi Dashboard (Tanpa Animasi) ---
            if self.dashboard_view not in self.stack.children():
                self.stack.addWidget(self.dashboard_view)
            target_widget = self.dashboard_view
            
            self.lbl_page_title.setText(identifier)
            
            # Dashboard tidak perlu animasi slide, cukup tampil instan
            self.stack.setCurrentWidget(target_widget)
            
        else:
            # --- Navigasi Channel Page (DENGAN ANIMASI SLIDE) ---
            
            # 1. Siapkan/Buat Halaman Target
            if identifier not in self.channel_views:
                cat_name, chan_name = identifier.split("/", 1)
                # Berikan parent self.stack agar lifetime ter-manage
                page = ChannelPage(cat_name, chan_name, parent=self.stack) 
                self.channel_views[identifier] = page
            
            target_widget = self.channel_views[identifier]
            
            # 2. Update Judul
            cat_name, chan_name = identifier.split("/", 1)
            self.lbl_page_title.setText(f"{cat_name} > {chan_name}")
            
            # Update variable pelengkap (untuk keperluan rename/auth)
            self.current_active_cat = cat_name
            self.current_active_chan = chan_name
            
            # 3. JALANKAN ANIMASI SLIDE-IN
            # Hanya berjalan karena ID baru != ID lama (sudah dicek di atas)
            PageAnimator.slide_in_from_left(target_widget, self.stack)
            
            # 4. Pastikan ditampilkan (fallback jika animasi gagal)
            target_widget.show()

    # [DIHAPUS] def toggle_auth_buttons(self, visible)

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

    def handle_category_renamed(self, old_name, new_name):
        self.refresh_sidebar()
        self.navigate("global", "Dashboard Portofolio")
        self.channel_views = {}
        QMessageBox.information(self, "Sukses", f"Kategori berhasil diubah: {new_name}")

    def handle_channel_deleted(self, channel_name):
        self.refresh_sidebar()
        self.navigate("global", "Dashboard Portofolio")
        self.channel_views = {}

    # [DIHAPUS] Semua method auth (action_add_secret, action_oauth, on_auth_url_received, dll)
    # karena sudah pindah ke ChannelPage.py