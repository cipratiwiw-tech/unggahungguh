# gui/sidebar.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, 
    QPushButton, QFrame, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont, QColor, QBrush

class Sidebar(QWidget):
    # Signal mengirim (tipe, data). Tipe: "global" atau "channel"
    selection_changed = Signal(str, str) 
    add_channel_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(280)
        self.setStyleSheet("background-color: #181818; border-right: 1px solid #3f3f3f;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Header Logo
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("border-bottom: 1px solid #3f3f3f;")
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignCenter | Qt.AlignLeft)
        
        lbl_logo = QLabel("▶ Studio Manager")
        lbl_logo.setStyleSheet("font-size: 18px; font-weight: bold; color: white; padding-left: 10px;")
        h_layout.addWidget(lbl_logo)
        layout.addWidget(header)

        # 2. Navigasi Global (Dashboard)
        self.btn_dashboard = QPushButton("  Dashboard Portofolio")
        self.btn_dashboard.setFixedHeight(45)
        self.btn_dashboard.setCursor(Qt.PointingHandCursor)
        self.btn_dashboard.setStyleSheet("""
            QPushButton { text-align: left; background: transparent; border: none; font-size: 14px; padding-left: 20px; }
            QPushButton:hover { background: #2f2f2f; }
            QPushButton:checked { color: #cc0000; font-weight: bold; }
        """)
        self.btn_dashboard.clicked.connect(lambda: self.on_item_click("global"))
        layout.addWidget(self.btn_dashboard)

        # 3. Tree Widget (Categories & Channels)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setFocusPolicy(Qt.NoFocus)
        self.tree.setStyleSheet("""
            QTreeWidget { background: transparent; border: none; font-size: 14px; }
            QTreeWidget::item { padding: 8px; }
            QTreeWidget::item:hover { background: #2f2f2f; }
            QTreeWidget::item:selected { background: rgba(204, 0, 0, 0.1); color: #cc0000; border-left: 3px solid #cc0000; }
        """)
        self.tree.itemClicked.connect(self.on_tree_click)
        layout.addWidget(self.tree)

        # 4. Footer
        footer = QFrame()
        f_layout = QVBoxLayout(footer)
        btn_add = QPushButton("+ Tambah Channel")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            background: #2f2f2f; border: 1px dashed #aaaaaa; color: #aaaaaa;
        """)
        btn_add.clicked.connect(self.add_channel_clicked.emit)
        f_layout.addWidget(btn_add)
        layout.addWidget(footer)

    def load_channels(self, channels_list):
        self.tree.clear()
        
        # Simulasi Kategori (Karena struktur folder flat, kita buat kategori dummy)
        tech_cat = QTreeWidgetItem(self.tree)
        tech_cat.setText(0, "Gaming & Tech")
        tech_cat.setExpanded(True)
        tech_cat.setForeground(0, QBrush(QColor("#aaaaaa")))
        font = QFont(); font.setBold(True)
        tech_cat.setFont(0, font)

        vlog_cat = QTreeWidgetItem(self.tree)
        vlog_cat.setText(0, "Lifestyle & Vlog")
        vlog_cat.setExpanded(True)
        vlog_cat.setForeground(0, QBrush(QColor("#aaaaaa")))
        vlog_cat.setFont(0, font)

        # Masukkan channel secara bergantian (hanya contoh visual)
        for i, channel in enumerate(channels_list):
            item = QTreeWidgetItem()
            item.setText(0, channel)
            # Set Avatar placeholder icon (🔴)
            item.setIcon(0, QIcon()) 
            item.setText(0, f"  {channel}")
            
            if i % 2 == 0:
                tech_cat.addChild(item)
            else:
                vlog_cat.addChild(item)

    def on_item_click(self, mode):
        if mode == "global":
            self.tree.clearSelection()
            self.selection_changed.emit("global", "Dashboard Portofolio")
            
    def on_tree_click(self, item, col):
        if item.childCount() > 0: # Klik kategori
            item.setExpanded(not item.isExpanded())
            return
            
        channel_name = item.text(0).strip()
        self.selection_changed.emit("channel", channel_name)