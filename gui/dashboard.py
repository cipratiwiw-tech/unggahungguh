from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("📊 Dashboard"))
        layout.addWidget(QLabel("Channel Aktif: channel_A"))
        layout.addWidget(QLabel("Status OAuth: Connected"))
        layout.addWidget(QLabel("Limit Hari Ini: 3 / 5"))
