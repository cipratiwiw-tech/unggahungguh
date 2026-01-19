from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QFrame

class StatItem(QFrame):
    def __init__(self, label, value, accent_color):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #313244;
                border-radius: 8px;
                padding: 5px 15px;
                border-left: 4px solid {accent_color};
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        v_layout = QVBoxLayout(self)
        v_layout.setContentsMargins(5,5,5,5)
        v_layout.setSpacing(2)
        
        lbl_title = QLabel(label)
        lbl_title.setStyleSheet("font-size: 11px; color: #a6adc8; font-weight: bold;")
        
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        
        v_layout.addWidget(lbl_title)
        v_layout.addWidget(lbl_val)

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Stats Items (Warna Neon: Hijau, Kuning, Merah)
        layout.addWidget(StatItem("CHANNEL AKTIF", "Malam Minggu", "#a6e3a1"))
        layout.addWidget(StatItem("UPLOAD HARIAN", "3 / 5 Video", "#f9e2af"))
        layout.addWidget(StatItem("STATUS API", "Connected", "#89b4fa"))