# gui/dashboard.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView

class StatCard(QFrame):
    def __init__(self, title, value, color_hex):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{ background-color: #2f2f2f; border-radius: 8px; border-left: 5px solid {color_hex}; }}
        """)
        l = QVBoxLayout(self)
        t = QLabel(title)
        t.setStyleSheet("color: #aaaaaa; font-size: 12px; font-weight: bold;")
        v = QLabel(value)
        v.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        l.addWidget(t)
        l.addWidget(v)

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 1. Stats Row
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(StatCard("TOTAL SUBSCRIBER", "1.2M", "#cc0000"))
        stats_layout.addWidget(StatCard("ESTIMASI PENDAPATAN", "IDR 45.2M", "#2ba640"))
        stats_layout.addWidget(StatCard("TOTAL CHANNEL", "8 Channel", "#ffaa00"))
        layout.addLayout(stats_layout)

        # 2. Table Label
        lbl_table = QLabel("Ringkasan Channel")
        lbl_table.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_table)

        # 3. Simple Channel Table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["NAMA CHANNEL", "STATUS UPLOAD", "PERFORMA"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #2f2f2f; border: none; border-radius: 8px; }
            QHeaderView::section { background-color: #181818; color: #aaaaaa; padding: 10px; border: none; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #3f3f3f; }
        """)
        layout.addWidget(self.table)