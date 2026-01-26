import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QMenu, 
    QMessageBox, QInputDialog, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont, QCursor
from PySide6.QtWidgets import QWidget
from utils import rename_channel_folder, delete_channel_folder, delete_category_folder, rename_category_folder

# =============================================================================
# COLOR PALETTE (Dark Muted Tints)
# =============================================================================
CATEGORY_COLORS = [
    "#2d1b1b", # Dark Red Tint
    "#1b242d", # Dark Blue Tint
    "#1b2d20", # Dark Green Tint
    "#2a1b2d", # Dark Purple Tint
    "#2d261b", # Dark Orange/Brown Tint
    "#1b2d2d", # Dark Teal Tint
    "#252525", # Neutral Dark
]

# =============================================================================
# CUSTOM COMPONENT: CHANNEL BUTTON
# =============================================================================
class ChannelBtn(QPushButton):
    """Custom Button representing a single Channel inside a Category."""
    def __init__(self, text, category, sidebar):
        super().__init__(text)
        self.category = category
        self.channel_name = text
        self.sidebar = sidebar
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Connect signals
        self.clicked.connect(self.on_click)
        self.customContextMenuRequested.connect(self.on_context_menu)
        
        # Initial Style
        self.update_style(False)

    def update_style(self, active):
        if active:
            self.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 10px 8px 20px;
                    background-color: rgba(204, 0, 0, 0.2); /* Red Accent Transparan */
                    color: #ff5555;
                    border: none;
                    border-left: 3px solid #cc0000;
                    font-weight: bold;
                    border-radius: 0px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 10px 8px 20px;
                    background-color: transparent;
                    color: #cccccc; /* Text agak terang */
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                    color: white;
                }
            """)

    def set_active(self, active):
        self.setChecked(active)
        self.update_style(active)

    def on_click(self):
        self.sidebar.handle_channel_click(self)

    def on_context_menu(self, pos):
        self.sidebar.open_channel_context_menu(self, pos)


# =============================================================================
# CUSTOM COMPONENT: CATEGORY GROUP CONTAINER
# =============================================================================
class CategoryGroup(QFrame):
    """
    Visual Container for a Category.
    """
    def __init__(self, category_name, channels, sidebar, bg_color="#1e1e1e"):
        super().__init__()
        self.category_name = category_name
        self.sidebar = sidebar
        self.is_expanded = True
        
        # --- CONTAINER STYLE ---
        # Background color dinamis sesuai parameter
        self.setStyleSheet(f"""
            CategoryGroup {{
                background-color: {bg_color};
                border: 1px solid #333333;
                border-radius: 8px;
            }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # 1. HEADER (Category Name)
        # Menggunakan background transparan hitam (rgba) agar warnanya 
        # otomatis menjadi versi lebih gelap dari warna kartu.
        self.header = QPushButton(f"  {category_name.upper()}")
        self.header.setCursor(Qt.PointingHandCursor)
        self.header.setStyleSheet("""
            QPushButton {
                text-align: left;
                background-color: rgba(0, 0, 0, 0.3); 
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 1px;
                padding: 12px;
                border: none;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }
            QPushButton:hover { background-color: rgba(0, 0, 0, 0.5); }
        """)
        self.header.clicked.connect(self.toggle_expand)
        self.header.setContextMenuPolicy(Qt.CustomContextMenu)
        self.header.customContextMenuRequested.connect(self.on_context_menu)
        
        self.layout.addWidget(self.header)

        # 2. CONTENT AREA (List of Channels)
        self.content_area = QWidget()
        # Background transparan agar mengikuti warna parent (CategoryGroup)
        self.content_area.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 5, 0, 5)
        self.content_layout.setSpacing(2)
        
        for chan_name in channels:
            btn = ChannelBtn(chan_name, category_name, sidebar)
            self.content_layout.addWidget(btn)
            sidebar.register_channel_btn(btn)
            
        self.layout.addWidget(self.content_area)

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_area.setVisible(self.is_expanded)

    def on_context_menu(self, pos):
        self.sidebar.open_category_context_menu(self, pos)


# =============================================================================
# MAIN SIDEBAR CLASS
# =============================================================================
class Sidebar(QWidget):
    # Signals
    selection_changed = Signal(str, str, QWidget) # mode, value
    add_channel_clicked = Signal()
    add_category_clicked = Signal() 
    channel_renamed = Signal(str, str, str) # category, old, new
    channel_deleted = Signal(str)      
    category_renamed = Signal(str, str) # old_name, new_name
    
    
    def __init__(self):
        super().__init__()
        
        self.setMinimumWidth(220) 
        self.resize(290, self.height())
        self.setStyleSheet("background-color: #121212;") 

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header (Logo)
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("border-bottom: 1px solid #2a2a2a; background: #181818;") 
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignCenter | Qt.AlignLeft)
        lbl_logo = QLabel("▶ Studio Manager")
        lbl_logo.setStyleSheet("font-size: 18px; font-weight: bold; color: white; padding-left: 15px; border: none;")
        h_layout.addWidget(lbl_logo)
        main_layout.addWidget(header)

        # 2. Global Navigation (Dashboard)
        self.btn_dashboard = QPushButton("  Dashboard Portofolio")
        self.btn_dashboard.setFixedHeight(50)
        self.btn_dashboard.setCursor(Qt.PointingHandCursor)
        self.btn_dashboard.setStyleSheet("""
            QPushButton { 
                text-align: left; background: #181818; border: none;
                border-bottom: 1px solid #2a2a2a; font-size: 14px; padding-left: 20px; color: #ddd;
            }
            QPushButton:hover { background: #2f2f2f; color: white; }
        """)
        self.btn_dashboard.clicked.connect(lambda: self.on_global_click())
        main_layout.addWidget(self.btn_dashboard)

        # 3. Scroll Area for Categories
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: #121212; }
            QScrollBar:vertical { width: 6px; background: #121212; }
            QScrollBar::handle:vertical { background: #333; border-radius: 3px; }
        """)
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        
        # Layout for the stack of cards
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(15, 20, 15, 20)
        self.container_layout.setSpacing(20) # Gap antar kategori
        self.container_layout.setAlignment(Qt.AlignTop)
        
        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)

        # 4. Footer Buttons
        footer = QFrame()
        footer.setStyleSheet("background: #181818; border-top: 1px solid #2a2a2a;")
        f_layout = QVBoxLayout(footer)
        f_layout.setContentsMargins(15, 15, 15, 15)
        f_layout.setSpacing(10)
        
        btn_add_chan = QPushButton("+ Add Channel")
        btn_add_chan.setCursor(Qt.PointingHandCursor)
        btn_add_chan.setStyleSheet("""
            QPushButton { background: #cc0000; border: none; color: white; font-weight: bold; border-radius: 4px; padding: 10px;}
            QPushButton:hover { background: #e60000; }
        """)
        btn_add_chan.clicked.connect(self.add_channel_clicked.emit)
        
        btn_add_cat = QPushButton("Create Category")
        btn_add_cat.setCursor(Qt.PointingHandCursor)
        btn_add_cat.setStyleSheet("""
            QPushButton { background: transparent; border: 1px dashed #555; color: #777; border-radius: 4px; padding: 8px;}
            QPushButton:hover { border-color: #aaa; color: #aaa; }
        """)
        btn_add_cat.clicked.connect(self.add_category_clicked.emit)

        f_layout.addWidget(btn_add_chan)
        f_layout.addWidget(btn_add_cat)
        main_layout.addWidget(footer)

        # Internal State
        self.channel_btns = []
        self.current_btn = None

    def register_channel_btn(self, btn):
        self.channel_btns.append(btn)

    def load_channels(self, structure):
        """Rebuilds the sidebar content based on directory structure"""
        # Clear existing content
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget: 
                widget.deleteLater()
        
        self.channel_btns = []
        self.current_btn = None

        # Build new cards with Cyclic Colors
        for i, (category, channels) in enumerate(structure.items()):
            # Ambil warna secara bergantian menggunakan Modulo
            bg_color = CATEGORY_COLORS[i % len(CATEGORY_COLORS)]
            
            group = CategoryGroup(category, channels, self, bg_color=bg_color)
            self.container_layout.addWidget(group)

    def on_global_click(self):
        if self.current_btn:
            self.current_btn.set_active(False)
            self.current_btn = None
        self.selection_changed.emit("global", "Dashboard Portofolio", self.btn_dashboard)

    def handle_channel_click(self, btn):
        if self.current_btn:
            self.current_btn.set_active(False)
        
        self.current_btn = btn
        self.current_btn.set_active(True)
        
        full_id = f"{btn.category}/{btn.channel_name}"
        self.selection_changed.emit("channel", full_id, btn)

    def select_channel(self, category_name, channel_name):
        for btn in self.channel_btns:
            if btn.category == category_name and btn.channel_name == channel_name:
                self.handle_channel_click(btn)
                return

    # --- Context Menus ---
    def open_channel_context_menu(self, btn, pos):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background: #2f2f2f; color: white; border: 1px solid #444; } 
            QMenu::item { padding: 6px 24px; font-size: 12px; }
            QMenu::item:selected { background-color: #cc0000; color: white; }
        """)
        
        rn = QAction("✎ Rename Channel", self)
        rn.triggered.connect(lambda: self.handle_rename(btn))
        menu.addAction(rn)
        
        dl = QAction("🗑 Delete Channel", self)
        dl.triggered.connect(lambda: self.handle_delete(btn))
        menu.addAction(dl)
        
        menu.exec(btn.mapToGlobal(pos))

    def open_category_context_menu(self, group, pos):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background: #2f2f2f; color: white; border: 1px solid #444; } 
            QMenu::item { padding: 6px 24px; font-size: 12px; }
            QMenu::item:selected { background-color: #cc0000; color: white; }
        """)
        
        rn = QAction("✎ Rename Category", self)
        rn.triggered.connect(lambda: self.handle_rename_category(group))
        menu.addAction(rn)
        
        dl = QAction("🗑 Delete Category (Recursive)", self)
        dl.triggered.connect(lambda: self.handle_delete_category(group))
        menu.addAction(dl)
        
        menu.exec(group.header.mapToGlobal(pos))
        
    # --- Action Handlers ---
    def handle_rename(self, btn):
        new_name, ok = QInputDialog.getText(self, "Rename", "New Name:", text=btn.channel_name)
        if ok and new_name.strip():
            try:
                rename_channel_folder(btn.category, btn.channel_name, new_name.strip())
                old_name = btn.channel_name
                btn.setText(new_name.strip())
                btn.channel_name = new_name.strip()
                self.channel_renamed.emit(btn.category, old_name, new_name.strip())
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def handle_rename_category(self, group):
        old_name = group.category_name
        new_name, ok = QInputDialog.getText(self, "Rename Category", "New Name:", text=old_name)
        if ok and new_name.strip():
            try:
                rename_category_folder(old_name, new_name.strip())
                self.category_renamed.emit(old_name, new_name.strip())
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                
    def handle_delete(self, btn):
        res = QMessageBox.warning(self, "Confirm", f"Delete '{btn.channel_name}'?", QMessageBox.Yes|QMessageBox.No)
        if res == QMessageBox.Yes:
            try:
                delete_channel_folder(btn.category, btn.channel_name)
                self.channel_deleted.emit(btn.channel_name)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def handle_delete_category(self, group):
        res = QMessageBox.warning(self, "Confirm", f"Delete '{group.category_name}' AND ALL CHANNELS?", QMessageBox.Yes|QMessageBox.No)
        if res == QMessageBox.Yes:
            try:
                delete_category_folder(group.category_name)
                self.channel_deleted.emit("CAT_DEL")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))