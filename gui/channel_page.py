# gui/channel_page.py
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, 
    QScrollArea, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from gui.custom_widgets import AutoResizingTextEdit, ScheduleWidget
from core.auth_manager import AuthManager

class UploadRow(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent; border-bottom: 1px solid #3f3f3f;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Col 1: Thumb
        self.btn_thumb = QPushButton("📷 Upload")
        self.btn_thumb.setFixedSize(80, 60)
        self.btn_thumb.setStyleSheet("""
            QPushButton { border: 1px dashed #aaaaaa; color: #aaaaaa; font-size: 10px; }
            QPushButton:hover { border-color: white; color: white; }
        """)
        self.btn_thumb.clicked.connect(self.select_thumb)
        layout.addWidget(self.btn_thumb)

        # Col 2: Title
        self.inp_title = AutoResizingTextEdit("Judul Video...")
        layout.addWidget(self.inp_title, 2)

        # Col 3: Desc
        self.inp_desc = AutoResizingTextEdit("Deskripsi...")
        layout.addWidget(self.inp_desc, 3)

        # Col 4: Tags
        self.inp_tags = AutoResizingTextEdit("Tags (koma)...")
        layout.addWidget(self.inp_tags, 2)

        # Col 5: Schedule
        self.schedule = ScheduleWidget()
        self.schedule.setFixedWidth(120)
        layout.addWidget(self.schedule)

    def select_thumb(self):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Thumbnail", "", "Images (*.jpg *.png)")
        if path:
            self.btn_thumb.setText("✔ Ready")
            self.btn_thumb.setStyleSheet("border: 1px solid #2ba640; color: #2ba640; background: rgba(43, 166, 64, 0.1);")

class ChannelPage(QWidget):
    def __init__(self, channel_name):
        super().__init__()
        self.channel_name = channel_name
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # --- 1. Top Stats (Simpel) ---
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background: #2f2f2f; border-radius: 8px; padding: 15px;")
        sf_layout = QHBoxLayout(stats_frame)
        sf_layout.addWidget(QLabel(f"CHANNEL: {channel_name}"))
        sf_layout.addWidget(QLabel(" | "))
        sf_layout.addWidget(QLabel("QUOTA HARIAN: 3/5"))
        sf_layout.addStretch()
        lbl_status = QLabel("API DISCONNECTED")
        lbl_status.setStyleSheet("color: #ffaa00; font-weight: bold;")
        self.lbl_auth_status = lbl_status
        sf_layout.addWidget(lbl_status)
        main_layout.addWidget(stats_frame)

        # --- 2. UPLOAD QUEUE CONTAINER (RED BORDER) ---
        queue_container = QFrame()
        queue_container.setObjectName("QueueBox")
        queue_container.setStyleSheet("""
            #QueueBox {
                background-color: #2f2f2f;
                border: 2px solid #cc0000;
                border-radius: 8px;
            }
        """)
        q_layout = QVBoxLayout(queue_container)
        q_layout.setContentsMargins(0, 0, 0, 0)
        q_layout.setSpacing(0)

        # Header Grid
        header = QFrame()
        header.setFixedHeight(40)
        header.setStyleSheet("background-color: #cc0000; border-top-left-radius: 6px; border-top-right-radius: 6px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(5, 0, 5, 0)
        
        labels = ["THUMB", "JUDUL", "DESKRIPSI", "TAGS", "JADWAL"]
        stretches = [0, 2, 3, 2, 0] # Proporsi lebar
        widths = [80, 0, 0, 0, 120]
        
        for i, text in enumerate(labels):
            l = QLabel(text)
            l.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")
            l.setAlignment(Qt.AlignCenter)
            if widths[i] > 0: l.setFixedWidth(widths[i])
            h_layout.addWidget(l, stretch=stretches[i])
        
        q_layout.addWidget(header)

        # Scroll Area untuk 5 baris input
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content_widget = QWidget()
        self.rows_layout = QVBoxLayout(content_widget)
        self.rows_layout.setSpacing(0)
        self.rows_layout.setContentsMargins(0,0,0,0)
        
        # Tambah 5 Baris
        self.upload_rows = []
        for _ in range(5):
            row = UploadRow()
            self.rows_layout.addWidget(row)
            self.upload_rows.append(row)
            
        self.rows_layout.addStretch() # Push ke atas
        scroll.setWidget(content_widget)
        q_layout.addWidget(scroll)

        # Footer Button
        self.btn_upload = QPushButton("UPLOAD SEMUA VIDEO (5)")
        self.btn_upload.setFixedHeight(50)
        self.btn_upload.setCursor(Qt.PointingHandCursor)
        self.btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #cc0000; color: white; font-weight: bold; font-size: 14px;
                border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #e60000; }
        """)
        self.btn_upload.clicked.connect(self.start_upload_simulation)
        q_layout.addWidget(self.btn_upload)

        main_layout.addWidget(queue_container)
        
        # Check status auth awal
        self.check_auth()

    def check_auth(self):
        status, color = AuthManager.check_status(self.channel_name)
        # Mapping warna hex dari utils ke style baru
        text_color = "#2ba640" if "Connected" in status else "#ffaa00"
        if "Missing" in status: text_color = "#cc0000"
        
        self.lbl_auth_status.setText(status.upper())
        self.lbl_auth_status.setStyleSheet(f"font-weight: bold; color: {text_color};")

    def start_upload_simulation(self):
        self.btn_upload.setText("MEMPROSES...")
        self.btn_upload.setStyleSheet("background-color: #8a0000; color: #aaaaaa; border: none;")
        self.btn_upload.setEnabled(False)
        
        # Timer simulasi 2 detik
        QTimer.singleShot(2000, self.finish_upload)

    def finish_upload(self):
        self.btn_upload.setText("SELESAI! ✔")
        self.btn_upload.setStyleSheet("background-color: #2ba640; color: white; border: none;")
        QTimer.singleShot(2000, lambda: self.reset_button())

    def reset_button(self):
        self.btn_upload.setText("UPLOAD SEMUA VIDEO (5)")
        self.btn_upload.setEnabled(True)
        self.btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #cc0000; color: white; font-weight: bold; font-size: 14px;
                border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #e60000; }
        """)