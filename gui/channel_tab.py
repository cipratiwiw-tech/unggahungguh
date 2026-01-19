import os
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QDateTimeEdit, 
    QProgressBar, QTextEdit, QFileDialog, QFrame, QAbstractItemView, 
    QLineEdit, QMessageBox, QCalendarWidget, QListWidget, QListWidgetItem,
    QStyledItemDelegate, QStyle
)
from PySide6.QtCore import Qt, QDateTime, Signal, QTime, QDate, QPoint, QEvent, QLocale
from PySide6.QtGui import (
    QDragEnterEvent, QDropEvent, QCursor, QTextOption, 
    QFontMetrics, QTextCursor, QTextCharFormat, QColor, QFont
)
from core.workers import UploadWorker
from core.auth_manager import AuthManager, OAuthWorker

# =========================================================================
# 1. EXCEL-LIKE DELEGATE (TITLE, DESC, TAGS - AUTO EXPAND)
# =========================================================================

class MultiLineDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QTextEdit(parent)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        editor.setFrameShape(QFrame.NoFrame)
        editor.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        
        # --- FIX ERROR FONT POINT SIZE (-1) ---
        font = editor.font()
        if font.pointSize() <= 0:
            font.setPointSize(10) # Set safe default
        editor.setFont(font)
        # --------------------------------------

        # Highlight Editing Focus
        editor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QTextEdit:focus {
                background-color: #1c3a5e; 
                border: 2px solid #00bcd4;
                selection-background-color: #00bcd4;
                selection-color: #1e1e2e;
            }
        """)
        return editor

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.EditRole)
        editor.setText(text if text else "")
        editor.moveCursor(QTextCursor.End)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.toPlainText(), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

# =========================================================================
# 2. CUSTOM SCHEDULE WIDGETS (POPUP & CELL)
# =========================================================================

class DatePopup(QWidget):
    dateSelected = Signal(QDate)
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setMinimumDate(QDate.currentDate())
        
        self.calendar.setStyleSheet("""
            QCalendarWidget QWidget { background-color: #1e1e2e; color: #cdd6f4; }
            QCalendarWidget QToolButton { color: white; background: #313244; }
            QCalendarWidget QSpinBox { background: #313244; color: white; }
            QCalendarWidget QAbstractItemView:disabled { color: #45475a; }
        """)
        
        # Highlight Hari Ini
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#00ffff"))
        fmt.setForeground(QColor("black"))
        self.calendar.setDateTextFormat(QDate.currentDate(), fmt)

        self.calendar.clicked.connect(self.on_date_clicked)
        layout.addWidget(self.calendar)
        
    def on_date_clicked(self, date):
        self.dateSelected.emit(date)
        self.close()

class TimePopup(QWidget):
    timeSelected = Signal(QTime)
    def __init__(self, parent=None, selected_date=None):
        super().__init__(parent, Qt.Popup)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.list_widget = QListWidget()
        self.list_widget.setFixedWidth(80)  
        self.list_widget.setFixedHeight(200)
        self.list_widget.setStyleSheet("""
            QListWidget { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #45475a; }
            QListWidget::item { padding: 5px; }
            QListWidget::item:hover { background-color: #313244; }
            QListWidget::item:selected { background-color: #89b4fa; color: #1e1e2e; }
        """)

        current_date = QDate.currentDate()
        current_time = QTime.currentTime()
        if not selected_date: selected_date = current_date

        for h in range(24):
            for m in [0, 15, 30, 45]:
                time_val = QTime(h, m)
                if selected_date == current_date and time_val < current_time:
                    continue
                item = QListWidgetItem(time_val.toString("HH:mm"))
                item.setData(Qt.UserRole, time_val)
                self.list_widget.addItem(item)

        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)

    def on_item_clicked(self, item):
        self.timeSelected.emit(item.data(Qt.UserRole))
        self.close()
        
    def scroll_to_time(self, time_val):
        items = self.list_widget.findItems(time_val.toString("HH:mm"), Qt.MatchStartsWith)
        if items: self.list_widget.scrollToItem(items[0], QAbstractItemView.PositionAtCenter)

class ScheduleCellWidget(QWidget):
    scheduleChanged = Signal(QDateTime)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.internal_dt = QDateTime.currentDateTime().addSecs(600)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)
        
        # --- FIX ERROR FONT POINT SIZE ---
        font = self.font()
        if font.pointSize() <= 0:
            font.setPointSize(10)
        self.setFont(font)
        # ---------------------------------

        self.btn_date = QPushButton()
        self.btn_date.setCursor(Qt.PointingHandCursor)
        self.btn_date.setFlat(True)
        self.btn_date.setMinimumHeight(38)
        self.btn_date.clicked.connect(self.show_date_popup)
        
        self.btn_time = QPushButton()
        self.btn_time.setCursor(Qt.PointingHandCursor)
        self.btn_time.setFlat(True)
        self.btn_time.setMinimumHeight(38)
        self.btn_time.clicked.connect(self.show_time_popup)

        layout.addWidget(self.btn_date)
        layout.addWidget(self.btn_time)
        
        self.update_display()

    def update_display(self):
        english_locale = QLocale(QLocale.English)
        date_str = english_locale.toString(self.internal_dt.date(), "dd MMM yyyy")
        time_str = self.internal_dt.toString("HH:mm")

        self.btn_date.setText(date_str)
        self.btn_time.setText(time_str)
        self.apply_styles()

    def apply_styles(self):
        base_style = """
            QPushButton { 
                text-align: center;
                font-family: 'Segoe UI', sans-serif;
                font-weight: bold; 
                border: none; 
                border-radius: 6px;
                padding: 0px 8px;
                background-color: transparent;
            } 
            QPushButton:hover { 
                background-color: rgba(0, 255, 255, 0.08);
            }
        """
        
        if self.internal_dt < QDateTime.currentDateTime():
            color_style = "color: #f38ba8;" 
        else:
            color_style = "color: #f9e2af;"

        final_style = base_style + f"QPushButton {{ {color_style} }}"
        self.btn_date.setStyleSheet(final_style)
        self.btn_time.setStyleSheet(final_style)

    def set_datetime(self, dt):
        self.internal_dt = dt
        self.update_display()

    def show_date_popup(self):
        self.date_popup = DatePopup(self)
        self.date_popup.calendar.setSelectedDate(self.internal_dt.date())
        self.date_popup.dateSelected.connect(self.set_new_date)
        pos = self.btn_date.mapToGlobal(QPoint(0, self.btn_date.height()))
        self.date_popup.move(pos)
        self.date_popup.show()

    def set_new_date(self, new_date):
        self.internal_dt = QDateTime(new_date, self.internal_dt.time())
        self.update_display()
        self.scheduleChanged.emit(self.internal_dt)

    def show_time_popup(self):
        self.time_popup = TimePopup(self, self.internal_dt.date())
        self.time_popup.scroll_to_time(self.internal_dt.time())
        self.time_popup.timeSelected.connect(self.set_new_time)
        pos = self.btn_time.mapToGlobal(QPoint(0, self.btn_time.height()))
        self.time_popup.move(pos)
        self.time_popup.show()

    def set_new_time(self, new_time):
        self.internal_dt = QDateTime(self.internal_dt.date(), new_time)
        self.update_display()
        self.scheduleChanged.emit(self.internal_dt)

    def get_iso_datetime(self):
        return self.internal_dt.toUTC().toString(Qt.ISODate)

# =========================================================================
# 3. OTHER CUSTOM WIDGETS
# =========================================================================

class ThumbnailWidget(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("📷 Drop / Click")
        self.setAcceptDrops(True)
        self.image_path = None
        self.setStyleSheet("""
            QPushButton { background-color: #313244; color: #a6adc8; border: 2px dashed #45475a; border-radius: 6px; text-align: center; font-size: 10px; }
            QPushButton:hover { border-color: #89b4fa; color: #89b4fa; }
        """)
        self.clicked.connect(self.select_image)

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Thumbnail", "", "Images (*.jpg *.png)")
        if path: self.set_image(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            ext = os.path.splitext(event.mimeData().urls()[0].toLocalFile())[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.webp']: event.accept()
            else: event.ignore()
        else: event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                self.set_image(f)
                break

    def set_image(self, path):
        self.image_path = path
        self.setText(f"🖼️ {os.path.basename(path)}")
        self.setStyleSheet("background: #313244; color: #a6e3a1; border: 2px solid #a6e3a1;")

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

class VideoDropTable(QTableWidget):
    videos_dropped = Signal(list) 
    def __init__(self, rows, cols):
        super().__init__(rows, cols)
        
        # --- FIX ERROR FONT POINT SIZE (-1) ---
        # Ini WAJIB dilakukan sebelum fontMetrics() dipanggil
        font = self.font()
        if font.pointSize() <= 0:
            font.setPointSize(10) # Safe default
        self.setFont(font)
        # --------------------------------------

        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        
        # Hitung Tinggi Baris (Aman karena font sudah divalidasi)
        fm = self.fontMetrics()
        line_height = fm.lineSpacing()
        if line_height <= 0: line_height = 15
        min_height = max(50, (line_height * 5) + 20)
        
        self.verticalHeader().setMinimumSectionSize(min_height)
        self.verticalHeader().setDefaultSectionSize(min_height)
        
        self.setStyleSheet("""
            QTableWidget { background-color: #11111b; border: none; gridline-color: #313244; }
            QHeaderView::section { background-color: #181825; color: #bac2de; padding: 8px; border: none; font-weight: bold; text-transform: uppercase; }
        """)
        
        self.setWordWrap(True)
        self.setTextElideMode(Qt.ElideNone)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed | QAbstractItemView.AnyKeyPressed)
        
        self.setItemDelegateForColumn(1, MultiLineDelegate(self))
        self.setItemDelegateForColumn(2, MultiLineDelegate(self))
        self.setItemDelegateForColumn(3, MultiLineDelegate(self))
        
        self.itemChanged.connect(self.resizeRowsToContents)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()
    def dropEvent(self, event):
        video_files = []
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.lower().endswith(('.mp4', '.mov', '.mkv', '.avi', '.flv')):
                video_files.append(f)
        if video_files: self.videos_dropped.emit(video_files)

# =========================================================================
# 4. MAIN CHANNEL TAB CLASS
# =========================================================================

class ChannelTab(QWidget):
    def __init__(self, channel_name):
        super().__init__()
        self.channel_name = channel_name
        self.worker = None
        self.auth_worker = None
        self.upload_queue = []
        self.is_processing = False

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setup_header(layout)
        self.setup_table(layout)
        self.setup_footer(layout)

        self.refresh_auth_status()

    def update_channel_identity(self, new_name):
        self.channel_name = new_name
        if hasattr(self, 'lbl_name'):
            self.lbl_name.setText(f"CHANNEL: {new_name}")
        self.refresh_auth_status()

    def setup_header(self, parent_layout):
        header = QFrame()
        header.setFixedHeight(80) 
        header.setStyleSheet("background-color: #1e1e2e; border-bottom: 1px solid #313244;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(15, 10, 15, 10)
        h_layout.setSpacing(15)

        self.box_oauth = QFrame()
        self.box_oauth.setStyleSheet("background: #181825; border-radius: 6px;")
        l_oauth = QVBoxLayout(self.box_oauth)
        l_oauth.setContentsMargins(10, 5, 10, 5)
        l_oauth.addWidget(QLabel("OAuth Status"))
        self.lbl_auth_status = QLabel("Checking...")
        self.lbl_auth_status.setStyleSheet("font-weight: bold; color: #6c7086;")
        l_oauth.addWidget(self.lbl_auth_status)
        h_layout.addWidget(self.box_oauth)

        self.box_quota = QFrame()
        self.box_quota.setStyleSheet("background: #181825; border-radius: 6px;")
        l_quota = QVBoxLayout(self.box_quota)
        l_quota.setContentsMargins(10, 5, 10, 5)
        l_quota.addWidget(QLabel("Daily Quota"))
        self.lbl_quota = QLabel("3 / 5 Left") 
        self.lbl_quota.setStyleSheet("font-weight: bold; color: #f9e2af;")
        l_quota.addWidget(self.lbl_quota)
        h_layout.addWidget(self.box_quota)

        h_layout.addStretch()

        self.lbl_name = QLabel(f"CHANNEL: {self.channel_name}")
        self.lbl_name.setStyleSheet("color: #6c7086; font-size: 10px; font-weight: bold;")
        h_layout.addWidget(self.lbl_name)

        self.btn_secret = QPushButton("Client Secret: OK")
        self.btn_secret.setEnabled(False) 
        self.btn_secret.setStyleSheet("QPushButton { background: #313244; color: #a6adc8; border: none; padding: 5px; }")
        
        self.btn_secret.clicked.connect(self.select_client_secret)
        
        h_layout.addWidget(self.btn_secret)

        self.btn_auth = QPushButton("Authorize Channel")
        self.btn_auth.setCursor(Qt.PointingHandCursor)
        self.btn_auth.setFixedSize(140, 40)
        self.btn_auth.setStyleSheet("""
            QPushButton { background: #89b4fa; color: #1e1e2e; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background: #b4befe; }
        """)
        self.btn_auth.clicked.connect(self.start_oauth_flow)
        h_layout.addWidget(self.btn_auth)
        
        parent_layout.addWidget(header)

    def setup_table(self, parent_layout):
        self.table = VideoDropTable(0, 7)
        self.table.setHorizontalHeaderLabels([
            "THUMBNAIL", "TITLE (EDIT)", "DESCRIPTION (EDIT)", 
            "TAGS (EDIT)", "SCHEDULE", "STATUS", ""
        ])
        
        self.table.videos_dropped.connect(self.handle_videos_dropped)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Title Stretch
        header.setSectionResizeMode(2, QHeaderView.Stretch) # Desc Stretch
        
        self.table.setColumnWidth(0, 110) # Thumb
        self.table.setColumnWidth(3, 140) # Tags
        self.table.setColumnWidth(4, 200) # Schedule
        self.table.setColumnWidth(5, 110) # Status
        self.table.setColumnHidden(6, True) # Path Video Hidden

        parent_layout.addWidget(self.table)

    def setup_footer(self, parent_layout):
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet("background-color: #181825; border-top: 1px solid #313244;")
        f_layout = QHBoxLayout(footer)
        
        self.btn_start = QPushButton("START UPLOAD")
        self.btn_start.setFixedSize(160, 40)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setStyleSheet("""
            QPushButton { background-color: #a6e3a1; color: #1e1e2e; font-weight: bold; border-radius: 4px; font-size: 13px; }
            QPushButton:hover { background-color: #94e2d5; }
            QPushButton:disabled { background-color: #45475a; color: #6c7086; }
        """)
        self.btn_start.clicked.connect(self.start_upload_sequence)

        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setFixedSize(100, 40)
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setStyleSheet("""
            QPushButton { background-color: #f38ba8; color: #1e1e2e; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #eba0ac; }
        """)
        self.btn_stop.clicked.connect(self.stop_upload)
        
        f_layout.addStretch()
        f_layout.addWidget(self.btn_start)
        f_layout.addWidget(self.btn_stop)
        
        parent_layout.addWidget(footer)

    def handle_videos_dropped(self, file_paths):
        for f in file_paths:
            self.add_video_row(f)

    def add_video_row(self, filepath):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        filename = os.path.basename(filepath)
        clean_name = os.path.splitext(filename)[0]

        # 0. Thumbnail
        thumb_widget = ThumbnailWidget()
        possible_thumb = filepath.replace(os.path.splitext(filepath)[1], ".jpg")
        if os.path.exists(possible_thumb):
            thumb_widget.set_image(possible_thumb)
        self.table.setCellWidget(row, 0, thumb_widget)

        # 1. Title (Align Top-Left)
        title_item = QTableWidgetItem(clean_name)
        title_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.table.setItem(row, 1, title_item)

        # 2. Description (Align Top-Left)
        desc_item = QTableWidgetItem("")
        desc_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.table.setItem(row, 2, desc_item)

        # 3. Tags (Align Top-Left)
        tags_item = QTableWidgetItem("")
        tags_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.table.setItem(row, 3, tags_item)

        # 4. Schedule (Auto Chain)
        schedule_widget = ScheduleCellWidget()
        schedule_widget.scheduleChanged.connect(
            lambda dt, w=schedule_widget: self.propagate_schedule(w, dt)
        )
        
        if row > 0:
            prev_widget = self.table.cellWidget(row - 1, 4)
            if prev_widget:
                new_dt = prev_widget.internal_dt.addSecs(15 * 60) # 15 min interval
                schedule_widget.set_datetime(new_dt)
                
        self.table.setCellWidget(row, 4, schedule_widget)

        # 5. Status
        status_widget = StatusWidget()
        self.table.setCellWidget(row, 5, status_widget)

        # 6. Hidden Path
        self.table.setItem(row, 6, QTableWidgetItem(filepath))
        
        self.table.resizeRowsToContents()

    def propagate_schedule(self, trigger_widget, new_dt):
        trigger_row = -1
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r, 4) == trigger_widget:
                trigger_row = r
                break
        
        if trigger_row == -1: return

        current_dt = new_dt
        for r in range(trigger_row + 1, self.table.rowCount()):
            next_widget = self.table.cellWidget(r, 4)
            if next_widget:
                current_dt = current_dt.addSecs(15 * 60)
                next_widget.set_datetime(current_dt)

    def refresh_auth_status(self):
        status_text, color = AuthManager.check_status(self.channel_name)
        self.lbl_auth_status.setText(status_text)
        self.lbl_auth_status.setStyleSheet(f"font-weight: bold; color: {color};")
        
        if "Missing Secret" in status_text:
            self.btn_secret.setText("Missing Secret!")
            self.btn_secret.setStyleSheet("QPushButton { background: #f38ba8; color: #1e1e2e; padding: 5px; }")
            self.btn_secret.setEnabled(True)
            self.btn_auth.setEnabled(False)
            self.btn_auth.setStyleSheet("QPushButton { background: #45475a; color: #6c7086; padding: 5px; }")
        elif "Connected" in status_text:
            self.btn_secret.setText("Secret: Configured")
            self.btn_secret.setStyleSheet("QPushButton { background: #313244; color: #a6e3a1; padding: 5px; }")
            self.btn_secret.setEnabled(False)
            self.btn_auth.setText("Re-Authorize")
            self.btn_auth.setEnabled(True)
            self.btn_auth.setStyleSheet("QPushButton { background: #313244; color: #a6e3a1; border: 1px solid #a6e3a1; }")
        else: 
            self.btn_secret.setText("Secret: Configured")
            self.btn_secret.setEnabled(False)
            self.btn_auth.setText("Authorize Channel")
            self.btn_auth.setEnabled(True)
            self.btn_auth.setStyleSheet("QPushButton { background: #fab387; color: #1e1e2e; font-weight: bold; }")

    def select_client_secret(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select client_secret.json", "", "JSON (*.json)")
        if not path:
            return 
            
        dest = AuthManager.get_paths(self.channel_name)["secret"]
        try:
            shutil.copy(path, dest)
            QMessageBox.information(self, "Success", "Client Secret updated!")
            self.refresh_auth_status()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def start_oauth_flow(self):
        self.btn_auth.setEnabled(False)
        self.btn_auth.setText("Browser Opened...")
        self.auth_worker = OAuthWorker(self.channel_name)
        self.auth_worker.finished.connect(self.on_oauth_finished)
        self.auth_worker.start()

    def on_oauth_finished(self, success, msg):
        self.btn_auth.setEnabled(True)
        if success:
            QMessageBox.information(self, "Success", "Channel Authorized!")
            self.refresh_auth_status()
        else:
            QMessageBox.critical(self, "OAuth Failed", f"Error: {msg}")
            self.refresh_auth_status()

    def start_upload_sequence(self):
        if self.is_processing: return
        self.upload_queue = []
        for r in range(self.table.rowCount()):
            stat_widget = self.table.cellWidget(r, 5)
            if stat_widget.lbl_status.text() == "READY":
                self.upload_queue.append(r)
        if not self.upload_queue: return
        self.is_processing = True
        self.btn_start.setEnabled(False)
        self.process_next()

    def stop_upload(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
        self.is_processing = False
        self.btn_start.setEnabled(True)
        self.btn_start.setText("START UPLOAD")

    def process_next(self):
        if not self.upload_queue or not self.is_processing:
            self.is_processing = False
            self.btn_start.setEnabled(True)
            return

        row = self.upload_queue.pop(0)
        self.current_processing_row = row
        
        video_path = self.table.item(row, 6).text()
        title = self.table.item(row, 1).text()
        desc = self.table.item(row, 2).text()
        tags_raw = self.table.item(row, 3).text()
        tags = tags_raw.split(",") if tags_raw else []

        thumb_path = self.table.cellWidget(row, 0).image_path
        schedule_widget = self.table.cellWidget(row, 4)
        publish_at = schedule_widget.get_iso_datetime()
        
        data = {
            "video_path": video_path,
            "title": title,
            "description": desc,
            "tags": [t.strip() for t in tags if t.strip()],
            "privacyStatus": "unlisted",
            "publishAt": publish_at,
            "thumbnail": thumb_path
        }

        stat_widget = self.table.cellWidget(row, 5)
        stat_widget.set_status("UPLOADING", "#f9e2af")
        
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
            print(msg)
        self.process_next()