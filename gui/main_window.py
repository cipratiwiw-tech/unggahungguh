import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
    QPushButton, QHBoxLayout, QLabel, QInputDialog, 
    QFileDialog, QMessageBox, QMenu, QStackedWidget
)
from PySide6.QtCore import Qt
from gui.channel_tab import ChannelTab
from gui.sidebar import Sidebar
from gui.dashboard import Dashboard
from utils import (
    get_existing_channels, create_new_channel, 
    rename_channel_folder, delete_channel_folder
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UnggahUngguh – Persistent Channel Manager")
        self.resize(1366, 800)

        # --- GLOBAL STYLE ---
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #11111b; color: #cdd6f4; font-family: 'Segoe UI'; font-size: 13px;
            }
            /* Styling untuk QTabWidget di dalam Channel View */
            QTabWidget::pane { border: 1px solid #313244; }
            QTabBar::tab {
                background: #181825; color: #a6adc8; padding: 10px 20px;
                border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #1e1e2e; color: #89b4fa; border-bottom: 2px solid #89b4fa;
            }
            QMenu {
                background-color: #1e1e2e; border: 1px solid #45475a; color: #cdd6f4;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #313244; color: #89b4fa;
            }
        """)

        # --- MAIN CONTAINER (Horizontal: Sidebar | Content) ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. SIDEBAR (Kiri)
        self.sidebar = Sidebar()
        self.sidebar.action_triggered.connect(self.switch_view)
        main_layout.addWidget(self.sidebar)

        # 2. CONTENT AREA (Kanan)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        main_layout.addWidget(content_widget)

        # --- TOP BAR (Tetap ada di atas Content Area) ---
        top_bar = QWidget()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("background-color: #181825; border-bottom: 1px solid #313244; padding: 0 20px;")
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        
        # Judul Halaman Dinamis
        self.lbl_page_title = QLabel("DASHBOARD")
        self.lbl_page_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #cdd6f4;")
        
        # Tombol New Channel (Hanya muncul jika di view Channels)
        self.btn_add_channel = QPushButton(" + NEW CHANNEL ")
        self.btn_add_channel.setCursor(Qt.PointingHandCursor)
        self.btn_add_channel.setStyleSheet("""
            QPushButton {
                background: #313244; color: white; border: 1px solid #45475a;
                border-radius: 4px; padding: 6px 15px; font-weight: bold;
            }
            QPushButton:hover { background: #45475a; }
        """)
        self.btn_add_channel.clicked.connect(self.add_new_channel_flow)
        self.btn_add_channel.hide() # Default hide, show logic di switch_view
        
        tb_layout.addWidget(self.lbl_page_title)
        tb_layout.addStretch()
        tb_layout.addWidget(self.btn_add_channel)
        
        content_layout.addWidget(top_bar)

        # --- STACKED WIDGET (Halaman yang berubah-ubah) ---
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        # [PAGE 0] Dashboard
        self.page_dashboard = Dashboard()
        self.stack.addWidget(self.page_dashboard)

        # [PAGE 1] Channel List (QTabWidget yang lama)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self.tabs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.show_tab_context_menu)
        self.stack.addWidget(self.tabs)

        # [PAGE 2] Asset Library (Placeholder)
        self.page_assets = QLabel("📦 ASSET LIBRARY\n\n(Coming Soon: Templates, Presets, Thumbnails)")
        self.page_assets.setAlignment(Qt.AlignCenter)
        self.page_assets.setStyleSheet("font-size: 18px; color: #6c7086;")
        self.stack.addWidget(self.page_assets)

        # [PAGE 3] Global Queue (Placeholder)
        self.page_queue = QLabel("🌐 GLOBAL QUEUE\n\n(Coming Soon: Monitor all uploads here)")
        self.page_queue.setAlignment(Qt.AlignCenter)
        self.page_queue.setStyleSheet("font-size: 18px; color: #6c7086;")
        self.stack.addWidget(self.page_queue)

        # Load data awal
        self.load_persisted_channels()
        
        # Set default view
        self.switch_view("dashboard")

    # =========================================================
    # NAVIGATION LOGIC
    # =========================================================
    
    def switch_view(self, view_uid):
        """Mengganti halaman berdasarkan ID dari Sidebar"""
        title_map = {
            "dashboard": "DASHBOARD OVERVIEW",
            "channels_list": "CHANNEL WORKSPACE",
            "assets": "ASSET LIBRARY",
            "global_queue": "UPLOAD QUEUE"
        }
        
        self.lbl_page_title.setText(title_map.get(view_uid, "APP"))

        if view_uid == "dashboard":
            self.stack.setCurrentIndex(0)
            self.btn_add_channel.hide()
            
        elif view_uid == "channels_list":
            self.stack.setCurrentIndex(1)
            self.btn_add_channel.show()
            
        elif view_uid == "assets":
            self.stack.setCurrentIndex(2)
            self.btn_add_channel.hide()
            
        elif view_uid == "global_queue":
            self.stack.setCurrentIndex(3)
            self.btn_add_channel.hide()

    # =========================================================
    # CHANNEL LOGIC (WARISAN KODE LAMA)
    # =========================================================

    def load_persisted_channels(self):
        existing_channels = get_existing_channels()
        if not existing_channels:
            return
        for channel_name in existing_channels:
            self.create_tab(channel_name)

    def create_tab(self, channel_name):
        tab = ChannelTab(channel_name)
        self.tabs.addTab(tab, channel_name)

    def add_new_channel_flow(self):
        name, ok = QInputDialog.getText(self, "New Channel", "Enter Channel Name (Folder Name):")
        if not ok or not name.strip():
            return
        
        safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_', '-')]).strip()
        
        secret_path, _ = QFileDialog.getOpenFileName(
            self, "Select client_secret.json", "", "JSON Files (*.json)"
        )
        if not secret_path:
            return

        try:
            create_new_channel(safe_name, secret_path)
            self.create_tab(safe_name)
            # Pindah ke tab baru
            self.tabs.setCurrentIndex(self.tabs.count() - 1)
            QMessageBox.information(self, "Success", f"Channel '{safe_name}' created successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create channel: {str(e)}")

    def show_tab_context_menu(self, point):
        index = self.tabs.tabBar().tabAt(point)
        if index < 0:
            return 

        menu = QMenu(self)
        action_rename = menu.addAction("Rename Channel")
        action_rename.triggered.connect(lambda: self.rename_channel(index))
        
        menu.addSeparator()
        action_delete = menu.addAction("Delete Channel")
        action_delete.triggered.connect(lambda: self.delete_channel(index))
        
        menu.exec(self.tabs.mapToGlobal(point))

    def rename_channel(self, index):
        current_name = self.tabs.tabText(index)
        new_name, ok = QInputDialog.getText(self, "Rename Channel", "New Channel Name:", text=current_name)
        
        if ok and new_name.strip():
            safe_new_name = "".join([c for c in new_name if c.isalnum() or c in (' ', '_', '-')]).strip()
            if safe_new_name == current_name: return

            try:
                rename_channel_folder(current_name, safe_new_name)
                self.tabs.setTabText(index, safe_new_name)
                
                # Update Internal Tab State
                tab_widget = self.tabs.widget(index)
                if isinstance(tab_widget, ChannelTab):
                    tab_widget.update_channel_identity(safe_new_name)

            except Exception as e:
                QMessageBox.critical(self, "Rename Failed", str(e))

    def delete_channel(self, index):
        channel_name = self.tabs.tabText(index)
        msg = QMessageBox(self)
        msg.setWindowTitle("Delete Channel")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(f"Are you sure you want to delete '{channel_name}'?")
        msg.setInformativeText("This will permanently remove the channel folder and tokens.")
        
        btn_delete = msg.addButton("Delete", QMessageBox.DestructiveRole)
        msg.addButton(QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
        msg.setStyleSheet("QPushButton[text='Delete'] { color: #f38ba8; font-weight: bold; }")

        msg.exec()
        
        if msg.clickedButton() == btn_delete:
            try:
                delete_channel_folder(channel_name)
                self.tabs.removeTab(index)
            except Exception as e:
                QMessageBox.critical(self, "Delete Failed", str(e))