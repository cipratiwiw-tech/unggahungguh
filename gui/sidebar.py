from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Signal

class Sidebar(QWidget):
    menu_clicked = Signal(int)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(200)

        layout = QVBoxLayout(self)

        menus = [
            ("Dashboard", 0),
            ("Video Queue", 1),
            ("Settings", 2),
        ]

        for text, index in menus:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _, i=index: self.menu_clicked.emit(i))
            layout.addWidget(btn)

        layout.addStretch()
