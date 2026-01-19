import os
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QDateTimeEdit, 
    QProgressBar, QTextEdit, QFileDialog, QFrame, QAbstractItemView, 
    QLineEdit
)
from PySide6.QtCore import Qt, QDateTime, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from core.workers import UploadWorker

# --- Custom Widget untuk Thumbnail (Click & Drop) ---
class ThumbnailWidget(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("📷 Drop / Click")
        self.setAcceptDrops(True)
        self.image_path = None
        self.setStyleSheet("""
            QPushButton {
                background-color: #313244; color: #a6adc8; 
                border: 2px dashed #45475a; border-radius: 6px;
                text-align: center; font-size: 10px;
            }
            QPushButton:hover { border-color: #89b4fa; color: #89b4fa; }
        """)
        self.clicked.connect(self.select_image)

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Thumbnail", "", "Images (*.jpg *.png)")
        if path:
            self.set_image(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.lower().endswith(('.jpg', '.png', '.jpeg')):
                self.set_image(f)
                break

    def set_image(self, path):
        self.image_path = path
        filename = os.path.basename(path)
        self.setText(f"🖼️ {filename}")
        self.setStyleSheet("background: #313244; color: #a6e3a1; border: 2px solid #a6e3a1;")

# --- Custom Widget untuk Status & Progress ---
class StatusWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        self.lbl_status = QLabel("READY")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("font-weight: bold; color: #bac2de; font-size: 11px;")
        
        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(6)
        self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet("background: #45475a; border-radius: 3px;")
        
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.pbar)

    def set_status(self, text, color="#bac2de"):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 11px;")

    def set_progress(self, val):
        self.pbar.setValue(val)


class ChannelTab(QWidget):
    def __init__(self, channel_name):
        super().__init__()
        self.channel_name = channel_name
        self.worker = None
        self.upload_queue = []
        self.is_processing = False

        # === LAYOUT UTAMA ===
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. HEADER (Fixed)
        self.setup_header(layout)

        # 2. TABLE (Video Input)
        self.setup_table(layout)

        # 3. FOOTER (Control)
        self.setup_footer(layout)

    def setup_header(self, parent_layout):
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: #1e1e2e; border-bottom: 1px solid #313244;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(15, 10, 15, 10)

        # Info
        info_layout = QVBoxLayout()
        lbl_name = QLabel(f"CHANNEL: {self.channel_name}")
        lbl_name.setStyleSheet("font-weight: bold; font-size: 16px; color: #89b4fa;")
        lbl_quota = QLabel("Daily Limit: 3 / 5 | Sisa: 2")
        lbl_quota.setStyleSheet("color: #a6adc8; font-size: 11px;")
        info_layout.addWidget(lbl_name)
        info_layout.addWidget(lbl_quota)

        # Auth Button
        btn_auth = QPushButton("🔑 Connected (Re-Auth)")
        btn_auth.setCursor(Qt.PointingHandCursor)
        btn_auth.setStyleSheet("""
            background: #313244; color: #a6e3a1; border: 1px solid #45475a; 
            padding: 5px 10px; border-radius: 4px; font-weight: bold;
        """)
        
        h_layout.addLayout(info_layout)
        h_layout.addStretch()
        h_layout.addWidget(btn_auth)
        
        parent_layout.addWidget(header)

    def setup_table(self, parent_layout):
        # 7 Kolom Total: 0=Thumb, 1=Title, 2=Desc, 3=Tags, 4=Schedule, 5=Status, 6=HiddenPath
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "THUMBNAIL", "TITLE (EDIT)", "DESCRIPTION (EDIT)", 
            "TAGS (EDIT)", "SCHEDULE (REQUIRED)", "STATUS", ""
        ])
        
        # Konfigurasi Drag & Drop Table (Untuk file video)
        self.table.setAcceptDrops(True)
        self.table.dragEnterEvent = self.dragEnterEvent
        self.table.dropEvent = self.dropEvent
        self.table.setSelectionMode(QAbstractItemView.NoSelection) # Fokus ke widget
        
        # Ukuran Kolom
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Title stretch
        header.setSectionResizeMode(2, QHeaderView.Stretch) # Desc stretch
        
        self.table.setColumnWidth(0, 110) # Thumb
        self.table.setColumnWidth(3, 150) # Tags
        self.table.setColumnWidth(4, 150) # Schedule
        self.table.setColumnWidth(5, 120) # Status
        self.table.setColumnHidden(6, True) # Path Video Hidden

        # Baris agak tinggi untuk Desc & Thumb
        self.table.verticalHeader().setDefaultSectionSize(90)
        
        # Style
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #11111b; border: none; gridline-color: #313244;
            }
            QHeaderView::section {
                background-color: #181825; color: #bac2de; padding: 8px; 
                border: none; font-weight: bold; text-transform: uppercase;
            }
        """)
        
        parent_layout.addWidget(self.table)

    def setup_footer(self, parent_layout):
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet("background-color: #181825; border-top: 1px solid #313244;")
        f_layout = QHBoxLayout(footer)
        
        btn_upload = QPushButton("🚀 START UPLOAD")
        btn_upload.setFixedSize(180, 40)
        btn_upload.setCursor(Qt.PointingHandCursor)
        btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; color: #1e1e2e; 
                font-weight: bold; border-radius: 4px; font-size: 13px;
            }
            QPushButton:hover { background-color: #b4befe; }
            QPushButton:disabled { background-color: #45475a; color: #6c7086; }
        """)
        btn_upload.clicked.connect(self.start_upload_sequence)
        
        f_layout.addStretch()
        f_layout.addWidget(btn_upload)
        
        parent_layout.addWidget(footer)

    # === DRAG & DROP LOGIC (VIDEO FILES) ===

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ['.mp4', '.mov', '.mkv', '.avi']:
                self.add_video_row(f)

    def add_video_row(self, filepath):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        filename = os.path.basename(filepath)
        clean_name = os.path.splitext(filename)[0]

        # 0. Thumbnail (Custom Widget)
        thumb_widget = ThumbnailWidget()
        # Auto-detect logic placeholder (jika ada file jpg bernama sama)
        possible_thumb = filepath.replace(os.path.splitext(filepath)[1], ".jpg")
        if os.path.exists(possible_thumb):
            thumb_widget.set_image(possible_thumb)
        self.table.setCellWidget(row, 0, thumb_widget)

        # 1. Title (LineEdit)
        inp_title = QLineEdit(clean_name)
        inp_title.setPlaceholderText("Judul Video")
        inp_title.setStyleSheet("background: transparent; border: none; color: white; font-weight: bold; font-size: 13px;")
        self.table.setCellWidget(row, 1, inp_title)

        # 2. Description (TextEdit)
        inp_desc = QTextEdit()
        inp_desc.setPlaceholderText("Tulis deskripsi...")
        inp_desc.setStyleSheet("background: transparent; border: 1px solid #313244; color: #a6adc8; font-size: 12px;")
        self.table.setCellWidget(row, 2, inp_desc)

        # 3. Tags (LineEdit)
        inp_tags = QLineEdit()
        inp_tags.setPlaceholderText("tag1, tag2")
        inp_tags.setStyleSheet("background: #1e1e2e; border: 1px solid #313244; color: #bac2de; border-radius: 4px;")
        self.table.setCellWidget(row, 3, inp_tags)

        # 4. Schedule (DateTimeEdit) - WAJIB
        # Default: Sekarang + 10 menit
        default_time = QDateTime.currentDateTime().addSecs(600)
        inp_sched = QDateTimeEdit(default_time)
        inp_sched.setDisplayFormat("dd/MM/yyyy HH:mm")
        inp_sched.setCalendarPopup(True)
        inp_sched.setStyleSheet("""
            QDateTimeEdit { background: #313244; color: #f9e2af; border: none; padding: 4px; border-radius: 4px; }
            QCalendarWidget QWidget { background-color: #1e1e2e; color: white; }
        """)
        self.table.setCellWidget(row, 4, inp_sched)

        # 5. Status (Custom Label + Progress)
        status_widget = StatusWidget()
        self.table.setCellWidget(row, 5, status_widget)

        # 6. Hidden Path
        self.table.setItem(row, 6, QTableWidgetItem(filepath))

    # === UPLOAD PROCESS ===

    def start_upload_sequence(self):
        if self.is_processing: return
        
        # Scan baris yang READY
        self.upload_queue = []
        for r in range(self.table.rowCount()):
            stat_widget = self.table.cellWidget(r, 5)
            # Cek text pada label dalam status widget
            if stat_widget.lbl_status.text() == "READY":
                self.upload_queue.append(r)
        
        if not self.upload_queue:
            return

        self.is_processing = True
        self.process_next()

    def process_next(self):
        if not self.upload_queue:
            self.is_processing = False
            return

        row = self.upload_queue.pop(0)
        self.current_processing_row = row
        
        # === AMBIL DATA (Sesuai Spec) ===
        # 1. Video Path
        video_path = self.table.item(row, 6).text()
        
        # 2. Metadata (Direct from widgets)
        title = self.table.cellWidget(row, 1).text()
        desc = self.table.cellWidget(row, 2).toPlainText()
        tags = self.table.cellWidget(row, 3).text().split(",")
        
        # 3. Schedule (ISO 8601 UTC)
        qdt = self.table.cellWidget(row, 4).dateTime()
        publish_at = qdt.toUTC().toString(Qt.ISODate) # YYYY-MM-DDTHH:MM:SSZ
        
        # 4. Thumbnail
        thumb_widget = self.table.cellWidget(row, 0)
        thumb_path = thumb_widget.image_path

        # Construct Data Packet
        data = {
            "video_path": video_path,
            "title": title,
            "description": desc,
            "tags": [t.strip() for t in tags if t.strip()],
            "privacyStatus": "unlisted", # HARDCODED WAJIB
            "publishAt": publish_at,     # HARDCODED WAJIB
            "thumbnail": thumb_path
        }

        # Update Visual
        stat_widget = self.table.cellWidget(row, 5)
        stat_widget.set_status("UPLOADING", "#f9e2af")
        
        # Start Worker
        self.worker = UploadWorker(data)
        self.worker.progress_signal.connect(stat_widget.set_progress)
        self.worker.finished_signal.connect(self.on_upload_finished)
        self.worker.start()

    def on_upload_finished(self, success, msg):
        row = self.current_processing_row
        stat_widget = self.table.cellWidget(row, 5)
        
        if success:
            stat_widget.set_status("DONE", "#a6e3a1")
            stat_widget.set_progress(100)
        else:
            stat_widget.set_status("ERROR", "#f38ba8")
            print(f"Upload Error: {msg}") # Debug log

        # Lanjut queue
        self.process_next()