from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSpinBox

class Settings(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("⚙ Settings"))

        limit = QSpinBox()
        limit.setRange(1, 10)
        limit.setValue(3)

        layout.addWidget(QLabel("Daily Upload Limit"))
        layout.addWidget(limit)
