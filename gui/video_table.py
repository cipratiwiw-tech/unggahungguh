from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton
)

class VideoTable(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Video", "Title", "Privacy", "Status", "Progress"
        ])

        layout.addWidget(self.table)

        upload_btn = QPushButton("Upload Selected")
        layout.addWidget(upload_btn)
