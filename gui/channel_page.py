import os
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, 
    QScrollArea, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QSizePolicy, QSplitter
)
from PySide6.QtCore import Qt, QTimer, QMimeData
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent
from gui.custom_widgets import AutoResizingTextEdit, ScheduleWidget
from core.auth_manager import AuthManager

# =============================================================================
# KOMPONEN KECIL (HELPER WIDGETS)
# =============================================================================

class StatCard(QFrame):
    """Kartu Statistik Compact"""
    def __init__(self, title, value, color_hex):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #2f2f2f;
                border-radius: 6px;
                border-left: 3px solid {color_hex};
                padding: 8px;
            }}
        """)
        l = QVBoxLayout(self)
        l.setContentsMargins(2,2,2,2)
        l.setSpacing(0)
        
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #888; font-size: 10px; font-weight: bold; border: none;")
        
        lbl_v = QLabel(value)
        lbl_v.setStyleSheet("color: white; font-size: 16px; font-weight: bold; border: none;")
        
        l.addWidget(lbl_t)
        l.addWidget(lbl_v)

class RecentVideosTable(QTableWidget):
    """Tabel Riwayat Video Mini"""
    def __init__(self, channel_seed):
        super().__init__(0, 3) # Kurangi kolom agar muat
        self.channel_seed = channel_seed
        
        self.setHorizontalHeaderLabels(["VIDEO TERBARU", "VIEWS", "STATUS"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        
        self.setColumnWidth(1, 60)
        self.setColumnWidth(2, 70)
        
        self.verticalHeader().setVisible(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSelectionMode(QTableWidget.NoSelection)
        
        self.setStyleSheet("""
            QTableWidget {
                background-color: #2f2f2f;
                border: 1px solid #3f3f3f;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #181818;
                color: #888;
                padding: 4px;
                border: none;
                font-weight: bold;
                font-size: 10px;
                border-bottom: 1px solid #3f3f3f;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #3f3f3f;
                color: #ddd;
                font-size: 11px;
            }
        """)
        self.generate_mock_data()

    def generate_mock_data(self):
        rng = random.Random(self.channel_seed)
        topics = ["Gameplay Part", "Review Gadget", "Tutorial", "Vlog", "News"]
        statuses = [("Aktif", "#2ba640"), ("Pending", "#ffaa00"), ("Block", "#cc0000")]
        
        for i in range(5): # Limit 5 rows
            title = f"{rng.choice(topics)} #{rng.randint(1, 99)}"
            views = f"{rng.randint(1, 999)}K"
            status, color = rng.choice(statuses)
            self.add_mock_row(title, views, status, color)

    def add_mock_row(self, title, views, status, status_color):
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(title))
        self.setItem(row, 1, QTableWidgetItem(views))
        item_status = QTableWidgetItem(status)
        item_status.setForeground(QColor(status_color))
        self.setItem(row, 2, item_status)

# =============================================================================
# ROW UPLOAD COMPLEX (Seksi Utama)
# =============================================================================

class UploadRow(QFrame):
    def __init__(self, parent_layout):
        super().__init__()
        self.parent_layout = parent_layout 
        self.video_path = None
        
        self.setStyleSheet("""
            UploadRow {
                background-color: #2f2f2f;
                border-bottom: 1px solid #3f3f3f;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop) 

        # Helper Cell Builder
        def create_cell(widget, width=0, stretch=0, border_right=True):
            cell = QFrame()
            border = "border-right: 1px solid #2a2a2a;" if border_right else "border: none;"
            cell.setStyleSheet(f"QFrame {{ background: transparent; {border} }}")
            
            c_layout = QVBoxLayout(cell)
            c_layout.setContentsMargins(0, 0, 0, 0)
            c_layout.setAlignment(Qt.AlignTop) 
            c_layout.addWidget(widget)
            
            if width > 0: cell.setFixedWidth(width)
            layout.addWidget(cell, stretch)
            return cell

        # 1. THUMBNAIL
        self.btn_thumb = QPushButton("Thumb")
        self.btn_thumb.setFixedSize(60, 40) # Lebih kecil sedikit
        self.btn_thumb.setCursor(Qt.PointingHandCursor)
        self.btn_thumb.setStyleSheet("""
            QPushButton { 
                border: 1px dashed #555; background: #222; color: #aaa; font-size: 9px; border-radius: 4px;
            }
            QPushButton:hover { border-color: #888; color: white; }
        """)
        self.btn_thumb.clicked.connect(self.select_thumb)
        
        thumb_wrapper = QFrame()
        tw_layout = QVBoxLayout(thumb_wrapper)
        tw_layout.setContentsMargins(0, 8, 0, 0)
        tw_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        tw_layout.addWidget(self.btn_thumb)
        create_cell(thumb_wrapper, width=80)

        # 2. JUDUL
        self.inp_title = AutoResizingTextEdit("Judul video...")
        self.inp_title.heightChanged.connect(self.propagate_resize)
        create_cell(self.inp_title, stretch=3) # Priority width

        # 3. DESKRIPSI
        self.inp_desc = AutoResizingTextEdit("Deskripsi...")
        self.inp_desc.heightChanged.connect(self.propagate_resize)
        create_cell(self.inp_desc, stretch=3)

        # 4. TAGS
        self.inp_tags = AutoResizingTextEdit("Tags...")
        self.inp_tags.heightChanged.connect(self.propagate_resize)
        create_cell(self.inp_tags, stretch=2)

        # 5. JADWAL
        self.schedule = ScheduleWidget()
        create_cell(self.schedule, width=130)

        # 6. DELETE
        self.btn_del = QPushButton("×")
        self.btn_del.setFixedSize(25, 25)
        self.btn_del.setCursor(Qt.PointingHandCursor)
        self.btn_del.setStyleSheet("""
            QPushButton {
                background: transparent; color: #666; font-size: 16px; font-weight: bold; border: none;
            }
            QPushButton:hover { color: #cc0000; background: rgba(204, 0, 0, 0.1); border-radius: 4px;}
        """)
        self.btn_del.clicked.connect(self.delete_me)
        
        del_wrapper = QFrame()
        dw_layout = QVBoxLayout(del_wrapper)
        dw_layout.setContentsMargins(0, 5, 0, 0)
        dw_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        dw_layout.addWidget(self.btn_del)
        create_cell(del_wrapper, width=35, border_right=False)

    def select_thumb(self):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Thumbnail", "", "Images (*.jpg *.png)")
        if path:
            self.btn_thumb.setText("✔")
            self.btn_thumb.setStyleSheet("border: none; background: #2ba640; color: white; font-size: 14px; font-weight: bold; border-radius: 4px;")

    def set_file_data(self, file_path):
        self.video_path = file_path
        filename = os.path.basename(file_path)
        clean_title = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()
        self.inp_title.setText(clean_title)
        self.inp_title.setToolTip(f"Source: {file_path}")

    def propagate_resize(self):
        self.updateGeometry()
    
    def delete_me(self):
        self.setParent(None)
        self.parent_layout.removeWidget(self)
        self.deleteLater()

# =============================================================================
# DROP AREA
# =============================================================================

class VideoDropArea(QScrollArea):
    def __init__(self, page_instance):
        super().__init__()
        self.page = page_instance
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QScrollArea { background: #1e1e1e; border: none; } /* Lebih gelap agar kontras */
            QWidget#DropContent { background: transparent; }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        video_exts = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm')
        count = 0
        for f in files:
            if f.lower().endswith(video_exts):
                self.page.add_upload_row(file_path=f)
                count += 1
        if count > 0: event.accept()

# =============================================================================
# HALAMAN UTAMA CHANNEL
# =============================================================================

class ChannelPage(QWidget):
    def __init__(self, category, channel_name):
        super().__init__()
        self.category = category
        self.channel_name = channel_name
        self.rng = random.Random(f"{category}_{channel_name}")
        
        # Main Layout Vertikal
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        # 1. TOP PANEL (Stats & History Side-by-Side)
        # Gunakan container fixed height agar tidak memakan tempat
        top_panel = QWidget()
        top_panel.setFixedHeight(140) 
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(15)

        # A. Stats Widget (Left)
        stats_widget = self.create_stats_widget()
        top_layout.addWidget(stats_widget, 4) # Ratio 40%

        # B. History Widget (Right)
        history_widget = self.create_history_widget()
        top_layout.addWidget(history_widget, 6) # Ratio 60%

        self.layout.addWidget(top_panel)

        # 2. UPLOAD AREA (Expanded)
        # Mengambil sisa semua ruang vertikal (stretch=1)
        upload_widget = self.create_upload_widget()
        self.layout.addWidget(upload_widget, 1)

        self.check_auth_status()

    def update_channel_identity(self, category, new_name):
        self.category = category
        self.channel_name = new_name
        self.check_auth_status()

    def check_auth_status(self):
        AuthManager.check_status(self.category, self.channel_name)

    def create_stats_widget(self):
        container = QWidget()
        l = QVBoxLayout(container)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(5)

        # Title Kecil
        lbl = QLabel("CHANNEL OVERVIEW")
        lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #666; letter-spacing: 1px;")
        l.addWidget(lbl)

        # 3 Kartu Vertikal tapi rapat (untuk menghemat lebar) 
        # Atau Grid 2 kolom. Mari buat Vertical Layout di dalam Left Panel.
        
        subs = f"{self.rng.randint(1, 999)}.{self.rng.randint(1,9)}K"
        views = f"{self.rng.randint(1, 50)}.{self.rng.randint(1,9)}M"
        rev = f"IDR {self.rng.randint(10, 500)}jt"

        # Pakai Grid layout untuk stats agar rapi
        stats_content = QWidget()
        grid = QHBoxLayout(stats_content) # Horizontal baris
        grid.setContentsMargins(0,0,0,0)
        grid.setSpacing(5)
        
        grid.addWidget(StatCard("SUBS", subs, "#cc0000"))
        grid.addWidget(StatCard("VIEWS", views, "#2ba640"))
        grid.addWidget(StatCard("EST. REV", rev, "#ffaa00"))

        l.addWidget(stats_content)
        l.addStretch() # Push ke atas
        return container

    def create_history_widget(self):
        container = QWidget()
        l = QVBoxLayout(container)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(5)
        
        lbl = QLabel("RIWAYAT TERAKHIR")
        lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #666; letter-spacing: 1px;")
        l.addWidget(lbl)
        
        table = RecentVideosTable(self.channel_name)
        l.addWidget(table)
        return container

    def create_upload_widget(self):
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #212121;
                border: 1px solid #333;
                border-radius: 6px;
            }
        """)
        l = QVBoxLayout(container)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)

        # --- HEADER ---
        header = QFrame()
        header.setFixedHeight(40)
        header.setStyleSheet("background-color: #2a2a2a; border-bottom: 1px solid #333; border-top-left-radius: 6px; border-top-right-radius: 6px;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(10, 0, 10, 0)
        
        lbl_title = QLabel("WORKSPACE UPLOAD")
        lbl_title.setStyleSheet("font-weight: bold; color: #ccc; font-size: 12px;")
        hl.addWidget(lbl_title)
        
        hl.addStretch()
        
        lbl_info = QLabel("Drag & Drop Video Files Here")
        lbl_info.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        hl.addWidget(lbl_info)
        
        l.addWidget(header)

        # --- COLUMN HEADERS ---
        col_header = QFrame()
        col_header.setFixedHeight(25)
        col_header.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #333;")
        chl = QHBoxLayout(col_header)
        chl.setContentsMargins(0,0,0,0)
        chl.setSpacing(0)
        
        # Kolom Header harus match dengan UploadRow
        cols = ["THUMB", "JUDUL", "DESKRIPSI", "TAGS", "JADWAL", ""]
        widths = [80, 0, 0, 0, 130, 35]
        stretches = [0, 3, 3, 2, 0, 0]

        for i, txt in enumerate(cols):
            lbl = QLabel(txt)
            lbl.setAlignment(Qt.AlignCenter)
            border = "border-right: 1px solid #333;" if i < len(cols)-1 else "border: none;"
            lbl.setStyleSheet(f"color: #666; font-weight: bold; font-size: 9px; {border}")
            if widths[i] > 0: lbl.setFixedWidth(widths[i])
            chl.addWidget(lbl, stretch=stretches[i])
            
        l.addWidget(col_header)

        # --- SCROLL AREA (DROP ZONE) ---
        self.scroll = VideoDropArea(self)
        
        content_widget = QWidget()
        content_widget.setObjectName("DropContent")
        self.rows_layout = QVBoxLayout(content_widget)
        self.rows_layout.setSpacing(0)
        self.rows_layout.setContentsMargins(0,0,0,0)
        self.rows_layout.setAlignment(Qt.AlignTop)

        # Add initial empty row
        self.add_upload_row()
            
        self.scroll.setWidget(content_widget)
        l.addWidget(self.scroll)

        # --- FOOTER ACTIONS ---
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet("background-color: #2a2a2a; border-top: 1px solid #333; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px;")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(10, 5, 10, 5)
        
        self.btn_add = QPushButton("+ Baris")
        self.btn_add.setFixedWidth(80)
        self.btn_add.setStyleSheet("background: #333; color: #aaa; border: 1px solid #444;")
        self.btn_add.clicked.connect(lambda: self.add_upload_row())
        fl.addWidget(self.btn_add)
        
        fl.addStretch()
        
        self.btn_action = QPushButton("MULAI UPLOAD ANTRIAN")
        self.btn_action.setFixedWidth(200)
        self.btn_action.setStyleSheet("background: #cc0000; color: white; font-weight: bold; border: none;")
        self.btn_action.clicked.connect(self.simulate_upload)
        fl.addWidget(self.btn_action)

        l.addWidget(footer)

        return container

    def add_upload_row(self, file_path=None):
        row = UploadRow(self.rows_layout)
        self.rows_layout.addWidget(row)
        if file_path:
            row.set_file_data(file_path)

    def simulate_upload(self):
        count = self.rows_layout.count()
        self.btn_action.setText(f"MEMPROSES {count} VIDEO...")
        self.btn_action.setEnabled(False)
        self.btn_action.setStyleSheet("background-color: #555; color: #aaa; border: none;")
        QTimer.singleShot(2000, self.finish_simulation)

    def finish_simulation(self):
        self.btn_action.setText("SELESAI! ✔")
        self.btn_action.setStyleSheet("background-color: #2ba640; color: white; border: none;")
        QTimer.singleShot(1500, self.reset_button)

    def reset_button(self):
        self.btn_action.setText("MULAI UPLOAD ANTRIAN")
        self.btn_action.setEnabled(True)
        self.btn_action.setStyleSheet("background: #cc0000; color: white; font-weight: bold; border: none;")