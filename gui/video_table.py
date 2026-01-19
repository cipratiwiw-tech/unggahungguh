from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QHeaderView,
    QTableWidgetItem, QLabel, QAbstractItemView, QFrame
)
from PySide6.QtCore import Qt

class VideoTable(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label Header Tabel
        lbl = QLabel("ANTRIAN VIDEO (Drag & Drop Files)")
        lbl.setStyleSheet("color: #bac2de; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(lbl)

        # Container Tabel dengan Border
        container = QFrame()
        container.setObjectName("Panel") # Mengambil style dari MainWindow
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(1, 1, 1, 1)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "FILENAME", "TITLE", "PRIVACY", "STATUS", "SIZE"
        ])
        
        # Styling Tabel Dark Mode
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #181825;
                gridline-color: #313244;
                border: none;
                border-radius: 10px;
                color: #cdd6f4;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #bac2de;
                padding: 12px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QTableWidget::item:selected {
                background-color: #45475a;
                color: #89b4fa;
            }
        """)

        # Konfigurasi Tabel
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Drag & Drop
        self.table.setAcceptDrops(True)
        self.table.dragEnterEvent = self.dragEnterEvent
        self.table.dropEvent = self.dropEvent

        c_layout.addWidget(self.table)
        layout.addWidget(container)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            self.add_row(f)

    def add_row(self, filepath):
        row = self.table.rowCount()
        self.table.insertRow(row)
        filename = filepath.split("/")[-1]
        
        # Contoh isi data
        self.table.setItem(row, 0, QTableWidgetItem(filename))
        self.table.setItem(row, 1, QTableWidgetItem(filename))
        self.table.setItem(row, 2, QTableWidgetItem("Private"))
        
        status_item = QTableWidgetItem("Ready")
        status_item.setForeground(Qt.green) # Indikator warna teks
        self.table.setItem(row, 3, status_item)
        
        self.table.setItem(row, 4, QTableWidgetItem("15 MB"))