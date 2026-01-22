import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, 
    QScrollArea, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor  # <--- WAJIB DI-IMPORT
from gui.custom_widgets import AutoResizingTextEdit, ScheduleWidget
from core.auth_manager import AuthManager

# =============================================================================
# KOMPONEN KECIL (HELPER WIDGETS)
# =============================================================================

class StatCard(QFrame):
    """Kartu Statistik untuk Seksi 1"""
    def __init__(self, title, value, color_hex):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #2f2f2f;
                border-radius: 6px;
                border-left: 4px solid {color_hex};
                padding: 10px;
            }}
        """)
        l = QVBoxLayout(self)
        l.setContentsMargins(5,5,5,5)
        l.setSpacing(2)
        
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #aaaaaa; font-size: 11px; font-weight: bold; border: none;")
        
        lbl_v = QLabel(value)
        lbl_v.setStyleSheet("color: white; font-size: 22px; font-weight: bold; border: none;")
        
        l.addWidget(lbl_t)
        l.addWidget(lbl_v)

class RecentVideosTable(QTableWidget):
    """Tabel Riwayat Video untuk Seksi 2"""
    def __init__(self):
        super().__init__(0, 4)
        self.setHorizontalHeaderLabels(["JUDUL VIDEO", "TANGGAL", "VIEWS", "STATUS"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # Judul Stretch
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        
        self.setColumnWidth(1, 120)
        self.setColumnWidth(2, 100)
        self.setColumnWidth(3, 100)
        
        self.verticalHeader().setVisible(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSelectionMode(QTableWidget.NoSelection)
        
        self.setStyleSheet("""
            QTableWidget {
                background-color: #2f2f2f;
                border: 1px solid #3f3f3f;
                border-radius: 6px;
                gridline-color: #3f3f3f;
            }
            QHeaderView::section {
                background-color: #181818;
                color: #aaaaaa;
                padding: 8px;
                border: none;
                font-weight: bold;
                border-bottom: 1px solid #3f3f3f;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3f3f3f;
                color: white;
            }
        """)
        
        # Mock Data
        self.add_mock_row("Review GTA 6 Leaks - Benarkah Rilis 2026?", "2 Hari lalu", "12.5K", "Aktif", "#2ba640")
        self.add_mock_row("Rakit PC 5 Jutaan Lancar Valorant", "5 Hari lalu", "8.2K", "Aktif", "#2ba640")
        self.add_mock_row("Vlog: Setup Studio Baru!", "1 Minggu lalu", "3.1K", "Review", "#ffaa00")

    def add_mock_row(self, title, date, views, status, status_color):
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(title))
        self.setItem(row, 1, QTableWidgetItem(date))
        self.setItem(row, 2, QTableWidgetItem(views))
        
        item_status = QTableWidgetItem(status)
        
        # --- PERBAIKAN DI SINI ---
        # 1. Gunakan QColor yang sudah di-import
        # 2. Set warna langsung ke object item sebelum dimasukkan ke table
        item_status.setForeground(QColor(status_color))
        
        self.setItem(row, 3, item_status)

# =============================================================================
# ROW UPLOAD COMPLEX (Seksi 3)
# =============================================================================

class UploadRow(QFrame):
    """
    Baris grid upload yang bisa membesar otomatis.
    """
    def __init__(self):
        super().__init__()
        # Style Baris
        self.setStyleSheet("""
            UploadRow {
                background-color: #2f2f2f;
                border-bottom: 1px solid #3f3f3f;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Penting: Alignment Top agar jika satu cell membesar, cell lain tetap mulai dari atas
        layout.setAlignment(Qt.AlignTop) 

        # --- Helper Cell Builder ---
        def create_cell(widget, width=0, stretch=0, last=False):
            cell = QFrame()
            # Style Cell: Border Kanan
            border = "border-right: 1px solid #2a2a2a;" if not last else "border: none;"
            cell.setStyleSheet(f"QFrame {{ background: transparent; {border} }}")
            
            c_layout = QVBoxLayout(cell)
            c_layout.setContentsMargins(0, 0, 0, 0)
            c_layout.setAlignment(Qt.AlignTop) # Widget menempel di atas cell
            c_layout.addWidget(widget)
            
            if width > 0: cell.setFixedWidth(width)
            layout.addWidget(cell, stretch)
            return cell

        # 1. THUMBNAIL (Kolom 1)
        self.btn_thumb = QPushButton("Upload\nImage")
        self.btn_thumb.setFixedSize(70, 50)
        self.btn_thumb.setCursor(Qt.PointingHandCursor)
        self.btn_thumb.setStyleSheet("""
            QPushButton { 
                border: 1px dashed #555; background: #222; color: #aaa; font-size: 10px; border-radius: 4px;
            }
            QPushButton:hover { border-color: #888; color: white; }
        """)
        self.btn_thumb.clicked.connect(self.select_thumb)
        
        # Container thumb agar center secara horizontal tapi top secara vertikal
        thumb_wrapper = QFrame()
        tw_layout = QVBoxLayout(thumb_wrapper)
        tw_layout.setContentsMargins(0, 10, 0, 0) # Padding top dikit
        tw_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        tw_layout.addWidget(self.btn_thumb)
        
        create_cell(thumb_wrapper, width=90)

        # 2. JUDUL (Kolom 2)
        self.inp_title = AutoResizingTextEdit("Judul video...")
        self.inp_title.heightChanged.connect(self.propagate_resize)
        create_cell(self.inp_title, stretch=2)

        # 3. DESKRIPSI (Kolom 3)
        self.inp_desc = AutoResizingTextEdit("Deskripsi lengkap...")
        self.inp_desc.heightChanged.connect(self.propagate_resize)
        create_cell(self.inp_desc, stretch=3)

        # 4. TAGS (Kolom 4)
        self.inp_tags = AutoResizingTextEdit("tag1, tag2, tag3...")
        self.inp_tags.heightChanged.connect(self.propagate_resize)
        create_cell(self.inp_tags, stretch=2)

        # 5. JADWAL (Kolom 5)
        self.schedule = ScheduleWidget()
        create_cell(self.schedule, width=140, last=True)

    def select_thumb(self):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Thumbnail", "", "Images (*.jpg *.png)")
        if path:
            self.btn_thumb.setText("✔")
            self.btn_thumb.setStyleSheet("""
                QPushButton { 
                    border: none; background: #2ba640; color: white; 
                    font-size: 18px; font-weight: bold; border-radius: 4px;
                }
            """)

    def propagate_resize(self):
        # Memaksa layout menghitung ulang ukuran saat text edit membesar
        self.updateGeometry()
        if self.parent():
            pass

# =============================================================================
# HALAMAN UTAMA CHANNEL
# =============================================================================

class ChannelPage(QWidget):
    def __init__(self, channel_name):
        super().__init__()
        self.channel_name = channel_name
        
        # Main Layout (Scrollable Page jika konten sangat panjang)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(25)

        # --- SEKSI 1: STATISTIK ---
        self.create_stats_section()

        # --- SEKSI 2: RIWAYAT VIDEO ---
        self.create_history_section()

        # --- SEKSI 3: UPLOAD QUEUE ---
        self.create_upload_section()

        # Check Auth di awal
        self.check_auth_status()

    def create_stats_section(self):
        # Container Stats
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        # Mock Data Stats
        stats_layout.addWidget(StatCard("TOTAL SUBSCRIBER", "1.25M", "#cc0000"))
        stats_layout.addWidget(StatCard("TOTAL VIEWS (28 Hari)", "4.8M", "#2ba640"))
        stats_layout.addWidget(StatCard("ESTIMASI PENDAPATAN", "IDR 125jt", "#ffaa00"))
        
        self.layout.addLayout(stats_layout)

    def create_history_section(self):
        container = QWidget()
        l = QVBoxLayout(container)
        l.setContentsMargins(0,0,0,0)
        l.setSpacing(10)
        
        lbl = QLabel("Riwayat Video Terbaru")
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        l.addWidget(lbl)
        
        self.history_table = RecentVideosTable()
        self.history_table.setFixedHeight(180) # Fixed height agar tidak memakan tempat
        l.addWidget(self.history_table)
        
        self.layout.addWidget(container)

    def create_upload_section(self):
        container = QWidget()
        l = QVBoxLayout(container)
        l.setContentsMargins(0,0,0,0)
        l.setSpacing(5)

        # Header Title
        title_box = QWidget()
        tb_l = QVBoxLayout(title_box)
        tb_l.setContentsMargins(0,0,0,0)
        tb_l.setSpacing(0)
        
        lbl_title = QLabel("Upload Antrian (Batch)")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #cc0000;")
        lbl_desc = QLabel("Tulisan panjang akan otomatis turun ke bawah (Auto-wrap).")
        lbl_desc.setStyleSheet("font-size: 12px; color: #aaaaaa;")
        
        tb_l.addWidget(lbl_title)
        tb_l.addWidget(lbl_desc)
        l.addWidget(title_box)

        # --- GRID CONTAINER (BORDER MERAH) ---
        grid_frame = QFrame()
        grid_frame.setObjectName("GridFrame")
        grid_frame.setStyleSheet("""
            #GridFrame {
                background-color: #2f2f2f;
                border: 2px solid #cc0000;
                border-radius: 6px;
            }
        """)
        gf_layout = QVBoxLayout(grid_frame)
        gf_layout.setContentsMargins(0, 0, 0, 0)
        gf_layout.setSpacing(0)

        # A. HEADER GRID (Merah)
        header_row = QFrame()
        header_row.setFixedHeight(35)
        header_row.setStyleSheet("background-color: #cc0000; border-top-left-radius: 4px; border-top-right-radius: 4px;")
        hr_layout = QHBoxLayout(header_row)
        hr_layout.setContentsMargins(0, 0, 0, 0)
        hr_layout.setSpacing(0)

        cols = ["THUMB", "JUDUL", "DESKRIPSI", "TAGS", "JADWAL"]
        widths = [90, 0, 0, 0, 140]
        stretches = [0, 2, 3, 2, 0]

        for i, txt in enumerate(cols):
            lbl = QLabel(txt)
            lbl.setAlignment(Qt.AlignCenter)
            # Border putih transparan antar header
            border = "border-right: 1px solid rgba(255,255,255,0.3);" if i < len(cols)-1 else "border: none;"
            lbl.setStyleSheet(f"color: white; font-weight: bold; font-size: 11px; {border}")
            
            if widths[i] > 0: lbl.setFixedWidth(widths[i])
            hr_layout.addWidget(lbl, stretch=stretches[i])

        gf_layout.addWidget(header_row)

        # B. ISI GRID (SCROLL AREA)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: #2f2f2f; border: none;")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        self.rows_layout = QVBoxLayout(content_widget)
        self.rows_layout.setSpacing(0)
        self.rows_layout.setContentsMargins(0,0,0,0)
        self.rows_layout.setAlignment(Qt.AlignTop)

        # Generate 5 Baris
        self.upload_rows = []
        for _ in range(5):
            row = UploadRow()
            self.rows_layout.addWidget(row)
            self.upload_rows.append(row)
            
        scroll.setWidget(content_widget)
        gf_layout.addWidget(scroll)

        # C. FOOTER ACTION
        self.btn_action = QPushButton("UPLOAD SEMUA VIDEO (5)")
        self.btn_action.setFixedHeight(45)
        self.btn_action.setCursor(Qt.PointingHandCursor)
        self.btn_action.setStyleSheet("""
            QPushButton {
                background-color: #cc0000; color: white; font-weight: bold; font-size: 14px;
                border: none; border-bottom-left-radius: 4px; border-bottom-right-radius: 4px;
            }
            QPushButton:hover { background-color: #aa0000; }
        """)
        self.btn_action.clicked.connect(self.simulate_upload)
        gf_layout.addWidget(self.btn_action)

        l.addWidget(grid_frame)
        self.layout.addWidget(container)

    def check_auth_status(self):
        # Placeholder untuk logika auth jika diperlukan refresh UI
        pass

    def simulate_upload(self):
        self.btn_action.setText("MEMPROSES...")
        self.btn_action.setEnabled(False)
        self.btn_action.setStyleSheet("background-color: #555; color: #aaa; border: none;")
        
        QTimer.singleShot(2000, self.finish_simulation)

    def finish_simulation(self):
        self.btn_action.setText("SELESAI! ✔")
        self.btn_action.setStyleSheet("background-color: #2ba640; color: white; border: none;")
        QTimer.singleShot(1500, self.reset_button)

    def reset_button(self):
        self.btn_action.setText("UPLOAD SEMUA VIDEO (5)")
        self.btn_action.setEnabled(True)
        self.btn_action.setStyleSheet("""
            QPushButton {
                background-color: #cc0000; color: white; font-weight: bold; font-size: 14px;
                border: none; border-bottom-left-radius: 4px; border-bottom-right-radius: 4px;
            }
            QPushButton:hover { background-color: #aa0000; }
        """)