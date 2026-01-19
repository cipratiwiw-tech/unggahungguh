from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QSpinBox, QPushButton
)
from PySide6.QtCore import Qt

class Settings(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # -- Bagian Settings --
        lbl_limit = QLabel("Daily Upload Limit:")
        lbl_limit.setStyleSheet("color: #bac2de; font-weight: bold;")
        
        self.limit = QSpinBox()
        self.limit.setRange(1, 50)
        self.limit.setValue(5)
        self.limit.setFixedWidth(80)
        self.limit.setStyleSheet("""
            QSpinBox {
                background-color: #181825;
                color: white;
                border: 1px solid #45475a;
                padding: 5px;
                border-radius: 4px;
            }
        """)

        layout.addWidget(lbl_limit)
        layout.addWidget(self.limit)

        # Spacer agar tombol ke kanan
        layout.addStretch()

        # -- Bagian Tombol Aksi --
        self.btn_upload = QPushButton("🚀 START UPLOAD SEQUENCE")
        self.btn_upload.setCursor(Qt.PointingHandCursor)
        self.btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; /* Accent Blue */
                color: #1e1e2e;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton:pressed {
                background-color: #74c7ec;
            }
        """)
        
        layout.addWidget(self.btn_upload)