# gui/channel_page.py
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, 
    QScrollArea, QFileDialog
)
from PySide6.QtCore import Qt, QTimer
from gui.custom_widgets import AutoResizingTextEdit, ScheduleWidget
from core.auth_manager import AuthManager

class UploadRow(QFrame):
    def __init__(self):
        super().__init__()
        # Garis Pemisah Baris (Row Separator)
        self.setStyleSheet("""
            UploadRow {
                background-color: #2f2f2f;
                border-bottom: 1px solid #3f3f3f; 
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # Nol margin agar border kolom menyatu
        layout.setSpacing(0) # Nol spacing agar garis vertikal continuous

        # --- Helper untuk membuat Cell Container dengan Border Kanan ---
        def create_cell(widget, width=0, stretch=0, last=False):
            cell = QFrame()
            # Garis Pemisah Kolom (Column Separator) - Sedikit lebih gelap (#2a2a2a)
            # Kecuali kolom terakhir (last=True) tidak punya border kanan
            border_style = "border-right: 1px solid #2a2a2a;" if not last else "border: none;"
            cell.setStyleSheet(f"""
                QFrame {{ 
                    background: transparent; 
                    {border_style}
                }}
            """)
            
            c_layout = QVBoxLayout(cell)
            c_layout.setContentsMargins(0, 0, 0, 0)
            c_layout.addWidget(widget)
            
            if width > 0: cell.setFixedWidth(width)
            layout.addWidget(cell, stretch)
            return cell

        # Col 1: Thumb
        self.btn_thumb = QPushButton("📷 Drop Img")
        self.btn_thumb.setFixedSize(60, 40)
        self.btn_thumb.setStyleSheet("""
            QPushButton { border: none; background: transparent; color: #aaaaaa; font-size: 10px; }
            QPushButton:hover { color: #cc0000; }
        """)
        self.btn_thumb.clicked.connect(self.select_thumb)
        
        # Bungkus tombol thumb agar bisa di tengah cell
        thumb_container = QWidget()
        tc_layout = QVBoxLayout(thumb_container)
        tc_layout.setAlignment(Qt.AlignCenter)
        tc_layout.setContentsMargins(0,0,0,0)
        tc_layout.addWidget(self.btn_thumb)
        
        create_cell(thumb_container, width=80)

        # Col 2: Title
        self.inp_title = AutoResizingTextEdit("Judul Video...")
        create_cell(self.inp_title, stretch=2)

        # Col 3: Desc
        self.inp_desc = AutoResizingTextEdit("Deskripsi...")
        create_cell(self.inp_desc, stretch=3)

        # Col 4: Tags
        self.inp_tags = AutoResizingTextEdit("Tags...")
        create_cell(self.inp_tags, stretch=2)

        # Col 5: Schedule (Last - No Right Border)
        self.schedule = ScheduleWidget()
        create_cell(self.schedule, width=130, last=True)

    def select_thumb(self):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Thumbnail", "", "Images (*.jpg *.png)")
        if path:
            self.btn_thumb.setText("✔ OK")
            self.btn_thumb.setStyleSheet("color: #2ba640; font-weight: bold; border: none; background: transparent;")

class ChannelPage(QWidget):
    def __init__(self, channel_name):
        super().__init__()
        self.channel_name = channel_name
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # --- Top Stats & Section Divider ---
        top_container = QWidget()
        tc_layout = QVBoxLayout(top_container)
        tc_layout.setContentsMargins(0,0,0,0)
        tc_layout.setSpacing(5)
        
        # Header Text
        lbl_header = QLabel(f"Overview: {channel_name}")
        lbl_header.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        tc_layout.addWidget(lbl_header)
        
        # Garis Batas Bagian (Section Divider)
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #3f3f3f;") # Menggunakan properti color untuk HLine standard
        tc_layout.addWidget(divider)
        
        main_layout.addWidget(top_container)

        # --- UPLOAD GRID CONTAINER ---
        queue_container = QFrame()
        queue_container.setObjectName("QueueBox")
        queue_container.setStyleSheet("""
            #QueueBox {
                background-color: #2f2f2f;
                border: 2px solid #cc0000; /* Border Luar Merah */
                border-radius: 6px;
            }
        """)
        q_layout = QVBoxLayout(queue_container)
        q_layout.setContentsMargins(0, 0, 0, 0)
        q_layout.setSpacing(0)

        # HEADER KOLOM (Merah dengan separator putih transparan)
        header_frame = QFrame()
        header_frame.setFixedHeight(35)
        header_frame.setStyleSheet("""
            QFrame { 
                background-color: #cc0000; 
                border-top-left-radius: 4px; 
                border-top-right-radius: 4px; 
            }
        """)
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        
        labels = ["THUMB", "JUDUL", "DESKRIPSI", "TAGS", "JADWAL"]
        stretches = [0, 2, 3, 2, 0]
        widths = [80, 0, 0, 0, 130]
        
        for i, text in enumerate(labels):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignCenter)
            # Separator Putih Transparan antar header kolom
            border = "border-right: 1px solid rgba(255,255,255,0.2);" if i < len(labels)-1 else "border: none;"
            lbl.setStyleSheet(f"color: white; font-weight: bold; font-size: 11px; {border}")
            
            if widths[i] > 0: lbl.setFixedWidth(widths[i])
            h_layout.addWidget(lbl, stretch=stretches[i])
        
        q_layout.addWidget(header_frame)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Hilangkan border scroll area agar menyatu
        scroll.setStyleSheet("background: #2f2f2f; border: none;") 
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #2f2f2f;")
        self.rows_layout = QVBoxLayout(content_widget)
        self.rows_layout.setSpacing(0)
        self.rows_layout.setContentsMargins(0,0,0,0)
        
        # 5 Baris Antrian
        self.upload_rows = []
        for _ in range(5):
            row = UploadRow()
            self.rows_layout.addWidget(row)
            self.upload_rows.append(row)
            
        self.rows_layout.addStretch() 
        scroll.setWidget(content_widget)
        q_layout.addWidget(scroll)

        # Tombol Upload Bawah
        self.btn_upload = QPushButton("UPLOAD SEMUA VIDEO (5)")
        self.btn_upload.setFixedHeight(45)
        self.btn_upload.setCursor(Qt.PointingHandCursor)
        self.btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #cc0000; color: white; font-weight: bold;
                border-radius: 0px; 
                border-bottom-left-radius: 4px; border-bottom-right-radius: 4px; 
                border: none;
            }
            QPushButton:hover { background-color: #e60000; }
        """)
        q_layout.addWidget(self.btn_upload)

        main_layout.addWidget(queue_container)