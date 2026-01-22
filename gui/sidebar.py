# gui/sidebar.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, 
    QPushButton, QFrame, QMenu, QMessageBox, QInputDialog, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont, QColor, QBrush, QAction, QCursor
from utils import rename_channel_folder, delete_channel_folder

class Sidebar(QWidget):
    # Signals
    selection_changed = Signal(str, str) 
    add_channel_clicked = Signal()
    channel_renamed = Signal(str, str) # old_name, new_name
    channel_deleted = Signal(str)      # channel_name

    def __init__(self):
        super().__init__()
        self.setFixedWidth(280)
        
        # Style Sidebar
        self.setStyleSheet("""
            QWidget { 
                background-color: #181818; 
                border-right: 1px solid #3f3f3f; 
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Header Logo
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("border-bottom: 1px solid #3f3f3f; border-right: none;") 
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignCenter | Qt.AlignLeft)
        
        lbl_logo = QLabel("▶ Studio Manager")
        lbl_logo.setStyleSheet("font-size: 18px; font-weight: bold; color: white; padding-left: 10px; border: none;")
        h_layout.addWidget(lbl_logo)
        layout.addWidget(header)

        # 2. Navigasi Global
        self.btn_dashboard = QPushButton("  Dashboard Portofolio")
        self.btn_dashboard.setFixedHeight(50)
        self.btn_dashboard.setCursor(Qt.PointingHandCursor)
        self.btn_dashboard.setStyleSheet("""
            QPushButton { 
                text-align: left; 
                background: transparent; 
                border: none;
                border-bottom: 1px solid #3f3f3f;
                font-size: 14px; 
                padding-left: 20px; 
                border-radius: 0;
            }
            QPushButton:hover { background: #2f2f2f; }
            QPushButton:checked { color: #cc0000; font-weight: bold; }
        """)
        self.btn_dashboard.clicked.connect(lambda: self.on_item_click("global"))
        layout.addWidget(self.btn_dashboard)

        # 3. Label Kategori
        lbl_cat = QLabel("CHANNEL LIST")
        lbl_cat.setStyleSheet("""
            color: #aaaaaa; font-size: 11px; font-weight: bold; 
            padding: 15px 0 5px 20px; border: none;
        """)
        layout.addWidget(lbl_cat)

        # 4. Tree Widget (Modified for Context Menu)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setFocusPolicy(Qt.NoFocus)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu) # Enable Klik Kanan
        
        self.tree.setStyleSheet("""
            QTreeWidget { background: transparent; border: none; font-size: 14px; }
            QTreeWidget::item { padding: 8px; border-bottom: 1px solid transparent; }
            QTreeWidget::item:hover { background: #2f2f2f; }
            QTreeWidget::item:selected { 
                background: rgba(204, 0, 0, 0.1); 
                color: #cc0000; 
                border-left: 3px solid #cc0000; 
            }
        """)
        
        self.tree.itemClicked.connect(self.on_tree_click)
        self.tree.customContextMenuRequested.connect(self.open_context_menu) # Connect Handler
        
        layout.addWidget(self.tree)

        # Footer
        footer = QFrame()
        footer.setStyleSheet("border-top: 1px solid #3f3f3f; border-right: none;")
        f_layout = QVBoxLayout(footer)
        btn_add = QPushButton("+ Tambah Channel")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton { background: #2f2f2f; border: 1px dashed #aaaaaa; color: #aaaaaa; }
            QPushButton:hover { border-color: white; color: white; }
        """)
        btn_add.clicked.connect(self.add_channel_clicked.emit)
        f_layout.addWidget(btn_add)
        layout.addWidget(footer)

    # --- LOGIKA DATA & INTERAKSI ---

    def load_channels(self, channels_list):
        self.tree.clear()
        
        # Buat Kategori Dummy (Hanya Visual)
        tech_cat = QTreeWidgetItem(self.tree)
        tech_cat.setText(0, "Gaming & Tech")
        tech_cat.setExpanded(True)
        tech_cat.setForeground(0, QBrush(QColor("#aaaaaa")))
        font = QFont(); font.setBold(True)
        tech_cat.setFont(0, font)

        # Masukkan Channel
        for channel in channels_list:
            item = QTreeWidgetItem()
            item.setText(0, f"  {channel}") # Ada padding spasi di teks
            item.setIcon(0, QIcon()) 
            # Simpan nama asli di UserRole agar tidak bingung dengan spasi visual
            item.setData(0, Qt.UserRole, channel)
            tech_cat.addChild(item)

    def on_item_click(self, mode):
        if mode == "global":
            self.tree.clearSelection()
            self.selection_changed.emit("global", "Dashboard Portofolio")
            
    def on_tree_click(self, item, col):
        if item.childCount() > 0:
            item.setExpanded(not item.isExpanded())
            return
        
        # Ambil nama bersih dari UserRole jika ada, atau strip teks
        channel_name = item.data(0, Qt.UserRole)
        if not channel_name:
            channel_name = item.text(0).strip()
            
        self.selection_changed.emit("channel", channel_name)

    # --- LOGIKA KLIK KANAN (CONTEXT MENU) ---

    def open_context_menu(self, position):
        item = self.tree.itemAt(position)
        
        # Validasi: Jangan muncul menu di area kosong atau di Kategori (Top Level)
        if not item or item.parent() is None:
            return

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background-color: #2f2f2f; color: white; border: 1px solid #3f3f3f; padding: 5px; }
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background-color: #cc0000; color: white; border-radius: 4px; }
            QMenu::separator { height: 1px; background: #3f3f3f; margin: 5px 0px; }
        """)

        # Action Rename
        action_rename = QAction("✎ Ganti Nama Channel", self)
        action_rename.triggered.connect(lambda: self.handle_rename(item))
        
        # Action Delete
        action_delete = QAction("🗑 Hapus Channel", self)
        action_delete.triggered.connect(lambda: self.handle_delete(item))
        
        menu.addAction(action_rename)
        menu.addSeparator()
        menu.addAction(action_delete)
        
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def handle_rename(self, item):
        old_name = item.data(0, Qt.UserRole) or item.text(0).strip()
        
        new_name, ok = QInputDialog.getText(
            self, "Ganti Nama Channel", 
            "Masukkan nama baru:", 
            text=old_name
        )
        
        if ok and new_name.strip():
            clean_new_name = new_name.strip()
            try:
                # Panggil Utils
                rename_channel_folder(old_name, clean_new_name)
                
                # Update UI Tree
                item.setText(0, f"  {clean_new_name}")
                item.setData(0, Qt.UserRole, clean_new_name)
                
                # Emit Signal
                self.channel_renamed.emit(old_name, clean_new_name)
                QMessageBox.information(self, "Sukses", f"Channel diubah menjadi '{clean_new_name}'")
                
            except Exception as e:
                QMessageBox.critical(self, "Gagal Rename", f"Error: {str(e)}")

    def handle_delete(self, item):
        channel_name = item.data(0, Qt.UserRole) or item.text(0).strip()
        
        # POPUP WARNING (SAFETY)
        confirm = QMessageBox.warning(
            self, 
            "Konfirmasi Hapus", 
            f"⚠️ PERINGATAN KERAS ⚠️\n\n"
            f"Apakah Anda yakin ingin menghapus channel '{channel_name}' beserta SELURUH isinya?\n"
            f"Data yang dihapus (Video, Config, Secret) TIDAK BISA DIKEMBALIKAN.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                # Panggil Utils
                delete_channel_folder(channel_name)
                
                # Hapus dari UI Tree
                item.parent().removeChild(item)
                
                # Emit Signal
                self.channel_deleted.emit(channel_name)
                QMessageBox.information(self, "Terhapus", f"Channel '{channel_name}' telah dihapus.")
                
            except Exception as e:
                QMessageBox.critical(self, "Gagal Hapus", f"Error: {str(e)}")