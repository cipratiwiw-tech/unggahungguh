# gui/sidebar.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, 
    QPushButton, QFrame, QMenu, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont, QColor, QBrush, QAction
from utils import rename_channel_folder, delete_channel_folder, delete_category_folder

class Sidebar(QWidget):
    # Signals
    selection_changed = Signal(str, str) # mode, value
    add_channel_clicked = Signal()
    add_category_clicked = Signal() 
    channel_renamed = Signal(str, str, str) # category, old, new
    channel_deleted = Signal(str)      
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(280)
        self.setStyleSheet("""
            QWidget { background-color: #181818; border-right: 1px solid #3f3f3f; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("border-bottom: 1px solid #3f3f3f; border-right: none;") 
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignCenter | Qt.AlignLeft)
        lbl_logo = QLabel("▶ Studio Manager")
        lbl_logo.setStyleSheet("font-size: 18px; font-weight: bold; color: white; padding-left: 10px; border: none;")
        h_layout.addWidget(lbl_logo)
        layout.addWidget(header)

        # 2. Global Nav
        self.btn_dashboard = QPushButton("  Dashboard Portofolio")
        self.btn_dashboard.setFixedHeight(50)
        self.btn_dashboard.setCursor(Qt.PointingHandCursor)
        self.btn_dashboard.setStyleSheet("""
            QPushButton { 
                text-align: left; background: transparent; border: none;
                border-bottom: 1px solid #3f3f3f; font-size: 14px; padding-left: 20px; 
            }
            QPushButton:hover { background: #2f2f2f; }
        """)
        self.btn_dashboard.clicked.connect(lambda: self.on_item_click("global"))
        layout.addWidget(self.btn_dashboard)

        # 3. Tree Widget (Accordion)
        lbl_cat = QLabel("CHANNELS BY CATEGORY")
        lbl_cat.setStyleSheet("color: #aaaaaa; font-size: 11px; font-weight: bold; padding: 15px 0 5px 20px; border: none;")
        layout.addWidget(lbl_cat)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setFocusPolicy(Qt.NoFocus)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        
        self.tree.setStyleSheet("""
            QTreeWidget { background: transparent; border: none; font-size: 14px; }
            QTreeWidget::item { padding: 8px; border-bottom: 1px solid transparent; }
            QTreeWidget::item:hover { background: #2f2f2f; }
            QTreeWidget::item:selected { background: rgba(204, 0, 0, 0.1); color: #cc0000; border-left: 3px solid #cc0000; }
        """)
        
        self.tree.itemClicked.connect(self.on_tree_click)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        layout.addWidget(self.tree)

        # 4. Footer Buttons
        footer = QFrame()
        footer.setStyleSheet("border-top: 1px solid #3f3f3f; border-right: none;")
        f_layout = QVBoxLayout(footer)
        f_layout.setSpacing(5)
        
        btn_add_chan = QPushButton("+ Add Channel")
        btn_add_chan.setCursor(Qt.PointingHandCursor)
        btn_add_chan.setStyleSheet("""
            QPushButton { background: #2f2f2f; border: 1px solid #3f3f3f; color: white; font-weight: bold;}
            QPushButton:hover { background: #cc0000; border-color: #cc0000; }
        """)
        btn_add_chan.clicked.connect(self.add_channel_clicked.emit)
        
        btn_add_cat = QPushButton("+ Add Category")
        btn_add_cat.setCursor(Qt.PointingHandCursor)
        btn_add_cat.setStyleSheet("""
            QPushButton { background: transparent; border: 1px dashed #555; color: #777; font-size: 12px;}
            QPushButton:hover { border-color: #aaa; color: #aaa; }
        """)
        btn_add_cat.clicked.connect(self.add_category_clicked.emit)

        f_layout.addWidget(btn_add_chan)
        f_layout.addWidget(btn_add_cat)
        layout.addWidget(footer)

    def load_channels(self, structure):
        self.tree.clear()
        font_cat = QFont(); font_cat.setBold(True)

        for category, channels in structure.items():
            cat_item = QTreeWidgetItem(self.tree)
            cat_item.setText(0, f" {category}")
            cat_item.setFont(0, font_cat)
            cat_item.setForeground(0, QBrush(QColor("#bac2de")))
            cat_item.setData(0, Qt.UserRole, "CATEGORY")
            cat_item.setData(0, Qt.UserRole + 1, category)
            cat_item.setExpanded(False)

            for channel in channels:
                chan_item = QTreeWidgetItem(cat_item)
                chan_item.setText(0, channel)
                chan_item.setData(0, Qt.UserRole, "CHANNEL")
                chan_item.setData(0, Qt.UserRole + 1, channel)
                chan_item.setData(0, Qt.UserRole + 2, category)

    def on_item_click(self, mode):
        if mode == "global":
            self.tree.clearSelection()
            self.selection_changed.emit("global", "Dashboard Portofolio")

    def on_tree_click(self, item, col):
        item_type = item.data(0, Qt.UserRole)
        
        if item_type == "CATEGORY":
            item.setExpanded(not item.isExpanded())
            
        elif item_type == "CHANNEL":
            channel_name = item.data(0, Qt.UserRole + 1)
            category_name = item.data(0, Qt.UserRole + 2)
            full_id = f"{category_name}/{channel_name}"
            self.selection_changed.emit("channel", full_id)

    # --- NEW: Programmatic Selection ---
    def select_channel(self, category_name, channel_name):
        """Finds the tree item for the given channel, expands the category, and selects it."""
        root = self.tree.invisibleRootItem()
        cat_item = None
        
        # 1. Find Category
        for i in range(root.childCount()):
            item = root.child(i)
            if item.data(0, Qt.UserRole + 1) == category_name:
                cat_item = item
                break
        
        if not cat_item: return

        # 2. Expand Category
        cat_item.setExpanded(True)

        # 3. Find and Select Channel
        for i in range(cat_item.childCount()):
            item = cat_item.child(i)
            if item.data(0, Qt.UserRole + 1) == channel_name:
                self.tree.setCurrentItem(item)
                # Manually emit signal because setting CurrentItem via code doesn't always trigger click
                full_id = f"{category_name}/{channel_name}"
                self.selection_changed.emit("channel", full_id)
                break

    # --- Context Menu (Unchanged) ---
    def open_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item: return

        item_type = item.data(0, Qt.UserRole)
        menu = QMenu()
        menu.setStyleSheet("QMenu { background: #2f2f2f; color: white; border: 1px solid #555; } QMenu::item:selected { background: #cc0000; }")

        if item_type == "CHANNEL":
            action_rename = QAction("✎ Rename Channel", self)
            action_rename.triggered.connect(lambda: self.handle_rename_channel(item))
            menu.addAction(action_rename)
            
            action_delete = QAction("🗑 Delete Channel", self)
            action_delete.triggered.connect(lambda: self.handle_delete_channel(item))
            menu.addAction(action_delete)
        
        elif item_type == "CATEGORY":
            action_delete = QAction("🗑 Delete Category (Recursive)", self)
            action_delete.triggered.connect(lambda: self.handle_delete_category(item))
            menu.addAction(action_delete)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def handle_rename_channel(self, item):
        old_name = item.data(0, Qt.UserRole + 1)
        category = item.data(0, Qt.UserRole + 2)
        new_name, ok = QInputDialog.getText(self, "Rename", "New Channel Name:", text=old_name)
        if ok and new_name.strip():
            try:
                rename_channel_folder(category, old_name, new_name.strip())
                item.setText(0, new_name.strip())
                item.setData(0, Qt.UserRole + 1, new_name.strip())
                self.channel_renamed.emit(category, old_name, new_name.strip())
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def handle_delete_channel(self, item):
        name = item.data(0, Qt.UserRole + 1)
        category = item.data(0, Qt.UserRole + 2)
        res = QMessageBox.warning(self, "Confirm", f"Delete channel '{name}'?", QMessageBox.Yes|QMessageBox.No)
        if res == QMessageBox.Yes:
            try:
                delete_channel_folder(category, name)
                item.parent().removeChild(item)
                self.channel_deleted.emit(name)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def handle_delete_category(self, item):
        cat_name = item.data(0, Qt.UserRole + 1)
        res = QMessageBox.warning(self, "Confirm", f"Delete Category '{cat_name}' AND ALL CHANNELS inside?", QMessageBox.Yes|QMessageBox.No)
        if res == QMessageBox.Yes:
            try:
                delete_category_folder(cat_name)
                index = self.tree.indexOfTopLevelItem(item)
                self.tree.takeTopLevelItem(index)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))