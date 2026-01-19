from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
from PySide6.QtCore import Signal, Qt

class Sidebar(QWidget):
    menu_clicked = Signal(int)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(240)
        self.setObjectName("SidebarContainer") # Untuk ID CSS

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Header Logo / Judul
        title = QLabel("UNGGAH\nUNGGUH")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white; padding: 30px 0;")
        layout.addWidget(title)

        self.buttons = []
        menus = [
            ("📊  Dashboard", 0),
            ("🎬  Video Queue", 1),
            ("⚙  Settings", 2),
        ]

        for text, index in menus:
            btn = QPushButton(text)
            btn.setCheckable(True) # Agar bisa stay 'pressed'
            btn.setObjectName("SidebarButton") # Style ID
            btn.setCursor(Qt.PointingHandCursor)
            
            # Logic agar tombol aktif menyala, yang lain mati
            btn.clicked.connect(lambda _, i=index, b=btn: self.handle_click(i, b))
            
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addStretch()
        
        # Set default active
        self.buttons[0].setChecked(True)

    def handle_click(self, index, active_btn):
        for btn in self.buttons:
            btn.setChecked(False)
        active_btn.setChecked(True)
        self.menu_clicked.emit(index)