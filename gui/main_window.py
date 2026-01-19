import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
    QPushButton, QHBoxLayout, QLabel, QInputDialog, 
    QFileDialog, QMessageBox, QMenu
)
from PySide6.QtCore import Qt
from gui.channel_tab import ChannelTab
from utils import (
    get_existing_channels, create_new_channel, 
    rename_channel_folder, delete_channel_folder
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UnggahUngguh – Persistent Channel Manager")
        self.resize(1366, 800)

        # Style Global
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #11111b; color: #cdd6f4; font-family: 'Segoe UI'; font-size: 13px;
            }
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

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # --- TOP BAR ---
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #181825; border-bottom: 1px solid #313244;")
        tb_layout = QHBoxLayout(top_bar)
        
        lbl_title = QLabel("UNGGAH // UNGGUH")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 900; color: #89b4fa; letter-spacing: 2px;")
        
        btn_add = QPushButton(" + NEW CHANNEL ")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background: #313244; color: white; border: 1px solid #45475a;
                border-radius: 4px; padding: 6px 15px; font-weight: bold;
            }
            QPushButton:hover { background: #45475a; }
        """)
        btn_add.clicked.connect(self.add_new_channel_flow)
        
        tb_layout.addWidget(lbl_title)
        tb_layout.addStretch()
        tb_layout.addWidget(btn_add)
        layout.addWidget(top_bar)

        # --- TAB AREA ---
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False) 
        
        # Enable Context Menu
        self.tabs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.show_tab_context_menu)
        
        layout.addWidget(self.tabs)

        self.load_persisted_channels()

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
            self.tabs.setCurrentIndex(self.tabs.count() - 1)
            QMessageBox.information(self, "Success", f"Channel '{safe_name}' created successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create channel: {str(e)}")

    # =========================================================
    # CONTEXT MENU LOGIC (RENAME & DELETE)
    # =========================================================

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
        # 1. Ambil nama lama dari Tab Header (Sumber Kebenaran)
        current_name = self.tabs.tabText(index)
        
        # 2. Minta input nama baru
        new_name, ok = QInputDialog.getText(self, "Rename Channel", "New Channel Name:", text=current_name)
        
        if ok and new_name.strip():
            safe_new_name = "".join([c for c in new_name if c.isalnum() or c in (' ', '_', '-')]).strip()
            
            # Jangan lakukan apa-apa jika nama sama
            if safe_new_name == current_name:
                return

            try:
                # 3. Rename folder di disk (CRITICAL)
                rename_channel_folder(current_name, safe_new_name)
                
                # 4. Update UI Tab Header (CRITICAL)
                self.tabs.setTabText(index, safe_new_name)
                
                # 5. Update Internal State Widget (Agar AuthManager tahu path baru)
                tab_widget = self.tabs.widget(index)
                if isinstance(tab_widget, ChannelTab):
                    # Kita panggil method khusus untuk update identitas
                    if hasattr(tab_widget, 'update_channel_identity'):
                        tab_widget.update_channel_identity(safe_new_name)
                    else:
                        # Fallback jika method belum ada (safety)
                        tab_widget.channel_name = safe_new_name

            except Exception as e:
                QMessageBox.critical(self, "Rename Failed", str(e))

    def delete_channel(self, index):
        channel_name = self.tabs.tabText(index)
        
        # --- PERBAIKAN DI SINI (CUSTOM BUTTON) ---
        msg = QMessageBox(self)
        msg.setWindowTitle("Delete Channel")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(f"Are you sure you want to delete '{channel_name}'?")
        msg.setInformativeText(
            "This will permanently remove the channel folder, OAuth tokens, and configuration.\n\n"
            "This action cannot be undone."
        )
        
        # Tambahkan Tombol Custom "Delete" dengan Peran Destruktif
        btn_delete = msg.addButton("Delete", QMessageBox.DestructiveRole)
        btn_cancel = msg.addButton(QMessageBox.Cancel)
        
        # Set Default ke Cancel (Safety)
        msg.setDefaultButton(btn_cancel)
        
        # Styling Tombol Delete agar terlihat berbahaya (Merah)
        msg.setStyleSheet("QPushButton[text='Delete'] { color: #f38ba8; font-weight: bold; }")

        msg.exec()
        
        # Cek tombol mana yang diklik
        if msg.clickedButton() == btn_delete:
            try:
                delete_channel_folder(channel_name)
                self.tabs.removeTab(index)
            except Exception as e:
                QMessageBox.critical(self, "Delete Failed", str(e))