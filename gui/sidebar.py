# gui/sidebar.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, 
    QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont, QColor, QBrush

class Sidebar(QWidget):
    selection_changed = Signal(str, str) 
    add_channel_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(280)
        # Pemisah Vertikal Utama (Kanan)
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
        # Garis bawah header sidebar (opsional, untuk konsistensi)
        header.setStyleSheet("border-bottom: 1px solid #3f3f3f; border-right: none;") 
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignCenter | Qt.AlignLeft)
        
        lbl_logo = QLabel("▶ Studio Manager")
        lbl_logo.setStyleSheet("font-size: 18px; font-weight: bold; color: white; padding-left: 10px; border: none;")
        h_layout.addWidget(lbl_logo)
        layout.addWidget(header)

        # 2. Navigasi Global (Dashboard) dengan Garis Bawah
        self.btn_dashboard = QPushButton("  Dashboard Portofolio")
        self.btn_dashboard.setFixedHeight(50)
        self.btn_dashboard.setCursor(Qt.PointingHandCursor)
        self.btn_dashboard.setStyleSheet("""
            QPushButton { 
                text-align: left; 
                background: transparent; 
                border: none;
                border-bottom: 1px solid #3f3f3f; /* Garis Pengelompokan */
                font-size: 14px; 
                padding-left: 20px; 
                border-radius: 0;
            }
            QPushButton:hover { background: #2f2f2f; }
            QPushButton:checked { color: #cc0000; font-weight: bold; }
        """)
        self.btn_dashboard.clicked.connect(lambda: self.on_item_click("global"))
        layout.addWidget(self.btn_dashboard)

        # 3. Label Kategori (Visual Separator)
        lbl_cat = QLabel("CHANNEL LIST")
        lbl_cat.setStyleSheet("""
            color: #aaaaaa; font-size: 11px; font-weight: bold; 
            padding: 15px 0 5px 20px; border: none;
        """)
        layout.addWidget(lbl_cat)

        # 4. Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setFocusPolicy(Qt.NoFocus)
        self.tree.setStyleSheet("""
            QTreeWidget { background: transparent; border: none; font-size: 14px; }
            QTreeWidget::item { padding: 8px; border-bottom: 1px solid transparent; } /* Item separator halus jika perlu */
            QTreeWidget::item:hover { background: #2f2f2f; }
            QTreeWidget::item:selected { 
                background: rgba(204, 0, 0, 0.1); 
                color: #cc0000; 
                border-left: 3px solid #cc0000; 
            }
        """)
        self.tree.itemClicked.connect(self.on_tree_click)
        layout.addWidget(self.tree)

        # Footer
        footer = QFrame()
        footer.setStyleSheet("border-top: 1px solid #3f3f3f; border-right: none;") # Garis pisah footer
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

    def load_channels(self, channels_list):
        self.tree.clear()
        
        tech_cat = QTreeWidgetItem(self.tree)
        tech_cat.setText(0, "Gaming & Tech")
        tech_cat.setExpanded(True)
        tech_cat.setForeground(0, QBrush(QColor("#aaaaaa")))
        font = QFont(); font.setBold(True)
        tech_cat.setFont(0, font)

        for channel in channels_list:
            item = QTreeWidgetItem()
            item.setText(0, channel)
            item.setIcon(0, QIcon()) 
            item.setText(0, f"  {channel}")
            tech_cat.addChild(item)

    def on_item_click(self, mode):
        if mode == "global":
            self.tree.clearSelection()
            self.selection_changed.emit("global", "Dashboard Portofolio")
            
    def on_tree_click(self, item, col):
        if item.childCount() > 0:
            item.setExpanded(not item.isExpanded())
            return
        channel_name = item.text(0).strip()
        self.selection_changed.emit("channel", channel_name)