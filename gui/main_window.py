from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget
)
from gui.sidebar import Sidebar
from gui.dashboard import Dashboard
from gui.video_table import VideoTable
from gui.settings import Settings

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UnggahUngguh – Professional YouTube Uploader")
        self.resize(1100, 650)

        root = QWidget()
        layout = QHBoxLayout(root)

        self.sidebar = Sidebar()
        self.pages = QStackedWidget()

        self.dashboard = Dashboard()
        self.video_table = VideoTable()
        self.settings = Settings()

        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.video_table)
        self.pages.addWidget(self.settings)

        self.sidebar.menu_clicked.connect(self.pages.setCurrentIndex)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.pages, 1)

        self.setCentralWidget(root)
