import os
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, 
    QScrollArea, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QSizePolicy, QSplitter, QMessageBox, QTextEdit, QApplication, QMenu
)
from PySide6.QtCore import Qt, QTimer, QMimeData, Signal, QEvent
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QAction, QCursor
from gui.custom_widgets import ScheduleWidget 
from core.auth_manager import AuthManager
from core.workers import UploadWorker

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
        super().__init__(0, 3) 
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
        
        for i in range(5): 
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

class FixedHeightTextEdit(QTextEdit):
    """TextEdit dengan tinggi fix, menolak drop file, dan tanpa menu klik kanan default"""
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setAcceptDrops(False)
        
        # [UPDATED] Matikan context menu default (Undo, Redo, Paste, dll)
        # Ini akan memaksa event klik kanan diteruskan ke parent (UploadRow)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                color: #ddd;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                padding: 4px;
            }
            QTextEdit:focus {
                background-color: #1e1e1e;
                color: white;
            }
        """)

class UploadRow(QFrame):
    # Signals
    clicked = Signal(object, bool) # self, is_ctrl_pressed
    deleted = Signal(object)       # self 

    def __init__(self, parent_layout):
        super().__init__()
        self.parent_layout = parent_layout 
        self.video_path = None
        self.thumb_path = None
        self.is_selected = False
        
        self.setFixedHeight(120)
        
        # Custom Context Menu (Klik Kanan di Row)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        self.default_style = """
            UploadRow {
                background-color: #212121;
                border-bottom: 1px solid #2a2a2a; 
                border-left: 3px solid transparent;
            }
        """
        self.selected_style = """
            UploadRow {
                background-color: #2a2a2a;
                border-bottom: 1px solid #2a2a2a; 
                border-left: 3px solid #cc0000;
            }
        """
        self.setStyleSheet(self.default_style)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop) 

        # Event Filter
        self.installEventFilter(self)

        def create_cell(widget, width=0, stretch=0, border_right=True):
            cell = QFrame()
            border = "border-right: 1px solid #2a2a2a;" if border_right else "border: none;"
            cell.setStyleSheet(f"QFrame {{ background: transparent; {border} }}")
            
            c_layout = QVBoxLayout(cell)
            c_layout.setContentsMargins(5, 5, 5, 5) 
            c_layout.addWidget(widget)
            
            if width > 0: cell.setFixedWidth(width)
            layout.addWidget(cell, stretch)
            return cell

        # 1. THUMBNAIL
        self.btn_thumb = QPushButton("Thumb")
        self.btn_thumb.setFixedSize(60, 36)
        self.btn_thumb.setCursor(Qt.PointingHandCursor)
        self.btn_thumb.setStyleSheet("""
            QPushButton { 
                border: 1px dashed #444; background: #1a1a1a; color: #666; font-size: 9px; border-radius: 4px;
            }
            QPushButton:hover { border-color: #888; color: white; }
        """)
        self.btn_thumb.clicked.connect(self.select_thumb)
        
        thumb_wrapper = QFrame()
        tw_layout = QVBoxLayout(thumb_wrapper)
        tw_layout.setContentsMargins(0, 10, 0, 0)
        tw_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter) 
        tw_layout.addWidget(self.btn_thumb)
        create_cell(thumb_wrapper, width=80)

        # 2. JUDUL
        self.inp_title = FixedHeightTextEdit("Judul video...")
        self.inp_title.installEventFilter(self)
        create_cell(self.inp_title, stretch=3)

        # 3. DESKRIPSI
        self.inp_desc = FixedHeightTextEdit("Deskripsi...")
        self.inp_desc.installEventFilter(self) 
        create_cell(self.inp_desc, stretch=3)

        # 4. TAGS
        self.inp_tags = FixedHeightTextEdit("Tags...")
        self.inp_tags.installEventFilter(self) 
        create_cell(self.inp_tags, stretch=2)

        # 5. JADWAL
        self.schedule = ScheduleWidget()
        create_cell(self.schedule, width=130)

    # --- KLIK KANAN MENU (Row Level) ---
    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2f2f2f;
                color: white;
                border: 1px solid #444;
            }
            QMenu::item {
                padding: 6px 20px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #cc0000;
            }
        """)
        
        action_del = QAction("🗑 Hapus Video", self)
        action_del.triggered.connect(self.delete_me)
        menu.addAction(action_del)
        
        menu.exec(self.mapToGlobal(pos))

    # --- EVENTS ---
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                modifiers = QApplication.keyboardModifiers()
                is_ctrl = modifiers == Qt.ControlModifier
                self.clicked.emit(self, is_ctrl)
            # Klik kanan pada text edit sekarang akan diabaikan oleh text edit 
            # (karena NoContextMenu) dan bubble up ke UploadRow -> show_context_menu
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            modifiers = QApplication.keyboardModifiers()
            is_ctrl = modifiers == Qt.ControlModifier
            self.clicked.emit(self, is_ctrl)
        super().mousePressEvent(event)

    def set_selected(self, selected):
        self.is_selected = selected
        self.setStyleSheet(self.selected_style if selected else self.default_style)

    def select_thumb(self):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Thumbnail", "", "Images (*.jpg *.png)")
        if path:
            self.thumb_path = path
            self.btn_thumb.setText("✔")
            self.btn_thumb.setStyleSheet("border: none; background: #2ba640; color: white; font-size: 14px; font-weight: bold; border-radius: 4px;")

    def set_file_data(self, file_path):
        self.video_path = file_path
        filename = os.path.basename(file_path)
        clean_title = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()
        self.inp_title.setText(clean_title)
        self.inp_title.setToolTip(f"Source: {file_path}")

    def get_data(self):
        if not self.video_path: return None
        schedule_info = self.schedule.get_scheduled_datetime()
        return {
            "video_path": self.video_path,
            "title": self.inp_title.toPlainText().strip(),
            "desc": self.inp_desc.toPlainText().strip(),
            "tags": self.inp_tags.toPlainText().strip(),
            "privacy": "private", 
            "thumb": self.thumb_path,
            "schedule_date": schedule_info["date"],
            "schedule_time": schedule_info["time"]
        }
    
    def delete_me(self):
        self.deleted.emit(self)
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
            QScrollArea { background: #121212; border: none; }
            QWidget#DropContent { background: transparent; }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
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
        if count > 0: event.acceptProposedAction()

    def mousePressEvent(self, event):
        self.page.deselect_all()
        super().mousePressEvent(event)

# =============================================================================
# HALAMAN UTAMA CHANNEL
# =============================================================================

class ChannelPage(QWidget):
    def __init__(self, category, channel_name):
        super().__init__()
        self.category = category
        self.channel_name = channel_name
        self.rng = random.Random(f"{category}_{channel_name}")
        self.upload_queue = [] 
        self.selected_rows = [] 
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        # 1. TOP PANEL
        top_panel = QWidget()
        top_panel.setFixedHeight(140) 
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(15)

        stats_widget = self.create_stats_widget()
        top_layout.addWidget(stats_widget, 4)

        history_widget = self.create_history_widget()
        top_layout.addWidget(history_widget, 6)

        self.layout.addWidget(top_panel)

        # 2. UPLOAD AREA
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
        lbl = QLabel("CHANNEL OVERVIEW")
        lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #666; letter-spacing: 1px;")
        l.addWidget(lbl)
        
        subs = f"{self.rng.randint(1, 999)}.{self.rng.randint(1,9)}K"
        views = f"{self.rng.randint(1, 50)}.{self.rng.randint(1,9)}M"
        rev = f"IDR {self.rng.randint(10, 500)}jt"

        stats_content = QWidget()
        grid = QHBoxLayout(stats_content)
        grid.setContentsMargins(0,0,0,0)
        grid.setSpacing(5)
        grid.addWidget(StatCard("SUBS", subs, "#cc0000"))
        grid.addWidget(StatCard("VIEWS", views, "#2ba640"))
        grid.addWidget(StatCard("EST. REV", rev, "#ffaa00"))
        l.addWidget(stats_content)
        l.addStretch()
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
        
        lbl_info = QLabel("Drag & Drop Video Files Here | Click to Select | Right Click to Delete")
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
        
        cols = ["THUMB", "JUDUL", "DESKRIPSI", "TAGS", "JADWAL"]
        widths = [80, 0, 0, 0, 130]
        stretches = [0, 3, 3, 2, 0]

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
            
        self.scroll.setWidget(content_widget)
        l.addWidget(self.scroll)

        # --- FOOTER ACTIONS ---
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet("background-color: #2a2a2a; border-top: 1px solid #333; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px;")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(10, 5, 10, 5)
        
        self.btn_import = QPushButton("+ Import Video")
        self.btn_import.setFixedWidth(120)
        self.btn_import.setStyleSheet("background: #333; color: #aaa; border: 1px solid #444;")
        self.btn_import.clicked.connect(self.browse_videos)
        fl.addWidget(self.btn_import)

        # Tombol Hapus Terpilih
        self.btn_del_selected = QPushButton("Hapus Terpilih")
        self.btn_del_selected.setFixedWidth(120)
        self.btn_del_selected.setCursor(Qt.PointingHandCursor)
        self.btn_del_selected.setStyleSheet("""
            QPushButton {
                background: transparent; color: #777; border: 1px solid #444; border-radius: 4px;
            }
            QPushButton:hover { color: #ff5555; border-color: #ff5555; background: rgba(255,85,85,0.1); }
        """)
        self.btn_del_selected.clicked.connect(self.delete_selected_rows)
        self.btn_del_selected.setVisible(False) 
        fl.addWidget(self.btn_del_selected)
        
        fl.addStretch()
        
        self.btn_action = QPushButton("MULAI UPLOAD ANTRIAN")
        self.btn_action.setFixedWidth(200)
        self.btn_action.setStyleSheet("background: #cc0000; color: white; font-weight: bold; border: none;")
        self.btn_action.clicked.connect(self.start_upload_queue)
        fl.addWidget(self.btn_action)

        l.addWidget(footer)

        return container

    def browse_videos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Pilih Video", "", "Video Files (*.mp4 *.mkv *.avi *.mov *.flv *.webm)"
        )
        for f in files:
            self.add_upload_row(f)

    def add_upload_row(self, file_path=None):
        row = UploadRow(self.rows_layout)
        row.clicked.connect(self.handle_row_click)
        row.deleted.connect(self.on_row_deleted) 
        self.rows_layout.addWidget(row)
        if file_path:
            row.set_file_data(file_path)

    def on_row_deleted(self, row_instance):
        if row_instance in self.selected_rows:
            self.selected_rows.remove(row_instance)
        self.update_delete_button()

    # --- SELECTION LOGIC ---
    def handle_row_click(self, row_instance, is_ctrl_pressed):
        if is_ctrl_pressed:
            if row_instance in self.selected_rows:
                row_instance.set_selected(False)
                self.selected_rows.remove(row_instance)
            else:
                row_instance.set_selected(True)
                self.selected_rows.append(row_instance)
        else:
            self.deselect_all()
            row_instance.set_selected(True)
            self.selected_rows = [row_instance]

        self.update_delete_button()

    def deselect_all(self):
        for r in self.selected_rows:
            r.set_selected(False)
        self.selected_rows = []
        self.update_delete_button()

    def update_delete_button(self):
        count = len(self.selected_rows)
        if count > 0:
            self.btn_del_selected.setText(f"Hapus ({count})")
            self.btn_del_selected.setVisible(True)
        else:
            self.btn_del_selected.setVisible(False)

    def delete_selected_rows(self):
        if not self.selected_rows: return
        
        reply = QMessageBox.question(
            self, "Konfirmasi", 
            f"Hapus {len(self.selected_rows)} item terpilih?", 
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for row in self.selected_rows[:]: 
                row.delete_me()
            self.selected_rows = []
            self.update_delete_button()

    # --- UPLOAD LOGIC ---
    def start_upload_queue(self):
        self.upload_queue = []
        cnt = self.rows_layout.count()
        for i in range(cnt):
            item = self.rows_layout.itemAt(i)
            if item:
                widget = item.widget()
                if isinstance(widget, UploadRow):
                    data = widget.get_data()
                    if data:
                        self.upload_queue.append(data)

        if not self.upload_queue:
            QMessageBox.warning(self, "Antrean Kosong", "Tidak ada video valid untuk diupload.")
            return

        self.btn_action.setEnabled(False)
        self.btn_action.setStyleSheet("background-color: #555; color: #aaa; border: none;")
        self.process_next_in_queue()

    def process_next_in_queue(self):
        if not self.upload_queue:
            self.finish_upload_session()
            return

        current_data = self.upload_queue.pop(0)
        self.current_processing_title = current_data['title']
        self.btn_action.setText(f"UPLOADING: {self.current_processing_title[:15]}...")

        self.worker = UploadWorker(self.category, self.channel_name, current_data)
        self.worker.progress_signal.connect(self.update_progress_ui)
        self.worker.status_signal.connect(self.update_status_ui)
        self.worker.finished_signal.connect(self.on_upload_finished)
        self.worker.start()

    def update_progress_ui(self, percent):
        self.btn_action.setText(f"UPLOADING {percent}% - {self.current_processing_title[:10]}...")

    def update_status_ui(self, status_text):
        pass 

    def on_upload_finished(self, success, msg):
        if success:
            self.process_next_in_queue()
        else:
            QMessageBox.critical(self, "Upload Gagal", f"Gagal mengupload {self.current_processing_title}:\n{msg}")
            self.process_next_in_queue()

    def finish_upload_session(self):
        self.btn_action.setText("SEMUA SELESAI! ✔")
        self.btn_action.setStyleSheet("background-color: #2ba640; color: white; border: none;")
        QTimer.singleShot(2000, self.reset_button)

    def reset_button(self):
        self.btn_action.setText("MULAI UPLOAD ANTRIAN")
        self.btn_action.setEnabled(True)
        self.btn_action.setStyleSheet("background: #cc0000; color: white; font-weight: bold; border: none;")