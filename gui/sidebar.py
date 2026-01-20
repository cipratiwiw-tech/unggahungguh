from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtCore import Signal, Qt

class Sidebar(QWidget):
    # Mengirimkan ID menu (string) alih-alih index tab (int)
    # Contoh output: "dashboard", "channels_list", "assets", "global_queue"
    action_triggered = Signal(str)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(240)
        self.setStyleSheet("background-color: #11111b; border-right: 1px solid #313244;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 25, 10, 25)
        layout.setSpacing(8)

        # --- 1. HEADER LOGO ---
        title = QLabel("UNGGAH\nUNGGUH")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 20px; 
            font-weight: 900; 
            color: #89b4fa; 
            letter-spacing: 1px;
            margin-bottom: 20px;
        """)
        layout.addWidget(title)

        # --- 2. MENU ITEMS ---
        self.btn_group = []
        
        # Konfigurasi Menu: (Label, Icon Emoji, ID Unik)
        menus = [
            ("Dashboard", "📊", "dashboard"),
            ("Channels List", "📺", "channels_list"), 
            ("Asset Library", "📦", "assets"),       
            ("Global Queue", "🌐", "global_queue"),  
        ]

        for label, icon, uid in menus:
            btn = self.create_nav_button(f"  {icon}   {label}", uid)
            layout.addWidget(btn)
            self.btn_group.append(btn)

        # --- 3. SPACER (Agar menu naik ke atas) ---
        vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(vertical_spacer)
        
        # --- 4. FOOTER INFO ---
        lbl_ver = QLabel("v0.2.0-alpha")
        lbl_ver.setStyleSheet("color: #45475a; font-size: 10px; font-weight: bold;")
        lbl_ver.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_ver)

        # Set Default Active: Dashboard
        if self.btn_group:
            self.btn_group[0].setChecked(True)

    def create_nav_button(self, text, uid):
        """Membuat tombol navigasi standar."""
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setProperty("uid", uid) # Menyimpan ID di dalam properti widget
        
        # Styling CSS untuk tombol
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 12px 15px;
                border-radius: 8px;
                color: #a6adc8;
                font-weight: bold;
                background-color: transparent;
                border: none;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #313244;
                color: white;
            }
            QPushButton:checked {
                background-color: #313244;
                color: #89b4fa; /* Catppuccin Blue */
                border-left: 3px solid #89b4fa; /* Indikator Aktif */
            }
        """)
        
        # Hubungkan klik dengan handler
        btn.clicked.connect(lambda: self.handle_click(btn))
        return btn

    def handle_click(self, clicked_btn):
        # 1. Visual Toggle (Matikan tombol lain, nyalakan yang diklik)
        for btn in self.btn_group:
            btn.setChecked(False)
        clicked_btn.setChecked(True)
        
        # 2. Emit Signal ID (Contoh: "dashboard")
        uid = clicked_btn.property("uid")
        self.action_triggered.emit(uid)