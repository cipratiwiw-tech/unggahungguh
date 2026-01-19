from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
    QPushButton, QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt
from gui.channel_tab import ChannelTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UnggahUngguh – YouTube Studio Manager")
        self.resize(1366, 768) # 1366px min width for comfortable table

        # Global Dark Theme
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #11111b;
                color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QTabWidget::pane { border: 1px solid #313244; top: -1px; }
            QTabBar::tab {
                background: #181825; color: #a6adc8; padding: 10px 20px;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #1e1e2e; color: #89b4fa; border-bottom: 2px solid #89b4fa;
            }
        """)

        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App Header (Top Bar)
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #181825; border-bottom: 1px solid #313244;")
        tb_layout = QHBoxLayout(top_bar)
        
        app_title = QLabel("UNGGAH // UNGGUH")
        app_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa; letter-spacing: 1px;")
        
        btn_add_channel = QPushButton(" + Add Channel ")
        btn_add_channel.setCursor(Qt.PointingHandCursor)
        btn_add_channel.setStyleSheet("""
            background-color: #313244; color: white; border: 1px solid #45475a;
            border-radius: 4px; padding: 5px 15px;
        """)
        btn_add_channel.clicked.connect(self.add_channel_tab)

        tb_layout.addWidget(app_title)
        tb_layout.addStretch()
        tb_layout.addWidget(btn_add_channel)
        
        layout.addWidget(top_bar)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.tabs.removeTab)
        layout.addWidget(self.tabs)

        # Init Default Tab
        self.add_channel_tab()

    def add_channel_tab(self):
        count = self.tabs.count() + 1
        # Nanti di sini logic buka file dialog client_secret.json
        tab = ChannelTab(f"Channel {count}")
        self.tabs.addTab(tab, f"Channel {count}")
        self.tabs.setCurrentIndex(count - 1)