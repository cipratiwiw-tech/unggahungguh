import os
import random
import shutil
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, 
    QScrollArea, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QSizePolicy, QSplitter, QMessageBox, QTextEdit, QApplication, QMenu, QDialog, QComboBox, QLineEdit, QDialogButtonBox, QFormLayout,
    QApplication
)
from PySide6.QtCore import Qt, QTimer, QMimeData, Signal, QEvent
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QAction

from gui.custom_widgets import ScheduleWidget 
from core.auth_manager import AuthManager, OAuthWorker
from core.workers import UploadWorker, ChannelInfoWorker

# ... [BAGIAN STAT CARD & HELPER LAIN TETAP SAMA SEPERTI SEBELUMNYA] ...
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
        
        
    def update_value(self, new_value):
        # Kita cari label kedua (yang berisi value)
        # Ingat urutan addWidget: [0]=Title, [1]=Value
        labels = self.findChildren(QLabel)
        if len(labels) >= 2:
            labels[1].setText(new_value)
            
            
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
            QTableWidget { background-color: #2f2f2f; border: 1px solid #3f3f3f; border-radius: 6px; }
            QHeaderView::section { background-color: #181818; color: #888; padding: 4px; border: none; font-weight: bold; font-size: 10px; border-bottom: 1px solid #3f3f3f; }
            QTableWidget::item { padding: 4px; border-bottom: 1px solid #3f3f3f; color: #ddd; font-size: 11px; }
        """)

    def update_data(self, videos_data):
        self.setRowCount(0) # Reset tabel
        
        for vid in videos_data:
            row = self.rowCount()
            self.insertRow(row)
            
            # Title
            item_title = QTableWidgetItem(vid['title'])
            item_title.setToolTip(vid['title'])
            self.setItem(row, 0, item_title)
            
            # Views
            self.setItem(row, 1, QTableWidgetItem(vid['views_fmt']))
            
            # Status
            status_map = {
                "public": ("Public", "#2ba640"),   # Hijau
                "unlisted": ("Unlisted", "#ffaa00"), # Kuning
                "private": ("Private", "#cc0000")    # Merah
            }
            status_text, color_hex = status_map.get(vid['status'], (vid['status'], "#777"))
            
            item_status = QTableWidgetItem(status_text)
            item_status.setForeground(QColor(color_hex))
            item_status.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item_status)

    def add_mock_row(self, title, views, status, status_color):
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(title))
        self.setItem(row, 1, QTableWidgetItem(views))
        item_status = QTableWidgetItem(status)
        item_status.setForeground(QColor(status_color))
        self.setItem(row, 2, item_status)

class FixedHeightTextEdit(QTextEdit):
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setAcceptDrops(False)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("""
            QTextEdit { background: transparent; border: none; color: #ddd; font-family: 'Segoe UI', sans-serif; font-size: 12px; padding: 4px; }
            QTextEdit:focus { background-color: #1e1e1e; color: white; }
        """)

class UploadRow(QFrame):
    clicked = Signal(object, bool)
    deleted = Signal(object)
    def __init__(self, parent_layout):
        super().__init__()
        self.parent_layout = parent_layout 
        self.video_path = None
        self.thumb_path = None
        self.is_selected = False
        self.setFixedHeight(120)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.default_style = """
            UploadRow { background-color: #212121; border-bottom: 1px solid #2a2a2a; border-left: 3px solid transparent; }
        """
        self.selected_style = """
            UploadRow { background-color: #2a2a2a; border-bottom: 1px solid #2a2a2a; border-left: 3px solid #cc0000; }
        """
        self.setStyleSheet(self.default_style)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop) 
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

        self.btn_thumb = QPushButton("Thumb")
        self.btn_thumb.setFixedSize(60, 36)
        self.btn_thumb.setCursor(Qt.PointingHandCursor)
        self.btn_thumb.setStyleSheet("QPushButton { border: 1px dashed #444; background: #1a1a1a; color: #666; font-size: 9px; border-radius: 4px; } QPushButton:hover { border-color: #888; color: white; }")
        self.btn_thumb.clicked.connect(self.select_thumb)
        thumb_wrapper = QFrame()
        tw_layout = QVBoxLayout(thumb_wrapper)
        tw_layout.setContentsMargins(0, 10, 0, 0)
        tw_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter) 
        tw_layout.addWidget(self.btn_thumb)
        create_cell(thumb_wrapper, width=80)

        self.inp_title = FixedHeightTextEdit("Judul video...")
        self.inp_title.installEventFilter(self)
        create_cell(self.inp_title, stretch=3)
        self.inp_desc = FixedHeightTextEdit("Deskripsi...")
        self.inp_desc.installEventFilter(self) 
        create_cell(self.inp_desc, stretch=3)
        self.inp_tags = FixedHeightTextEdit("Tags...")
        self.inp_tags.installEventFilter(self) 
        create_cell(self.inp_tags, stretch=2)
        self.schedule = ScheduleWidget()
        create_cell(self.schedule, width=130)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2f2f2f; color: white; border: 1px solid #444; } QMenu::item { padding: 6px 20px; font-size: 12px; } QMenu::item:selected { background-color: #cc0000; }")
        action_del = QAction("🗑 Hapus Video", self)
        action_del.triggered.connect(self.delete_me)
        menu.addAction(action_del)
        menu.exec(self.mapToGlobal(pos))

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                modifiers = QApplication.keyboardModifiers()
                is_ctrl = modifiers == Qt.ControlModifier
                self.clicked.emit(self, is_ctrl)
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

class VideoDropArea(QScrollArea):
    def __init__(self, page_instance):
        super().__init__()
        self.page = page_instance
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)
        self.setStyleSheet("QScrollArea { background: #121212; border: none; } QWidget#DropContent { background: transparent; }")

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

class ChannelPage(QWidget):
    def __init__(self, category, channel_name, parent=None):
        # [UBAH BARIS INI] Teruskan parent ke super class
        super().__init__(parent) 
        
        self.category = category
        self.channel_name = channel_name
        self.rng = random.Random(f"{category}_{channel_name}")
        self.upload_queue = [] 
        self.selected_rows = [] 
        self.info_worker = None
        
        self.oauth_worker = None
        
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
        status_text, status_color = AuthManager.check_status(self.category, self.channel_name)
        paths = AuthManager.get_paths(self.category, self.channel_name)
        
        has_secret = os.path.exists(paths["secret"])
        is_connected = "Connected" in status_text

        # --- A. LOGIKA TOMBOL SECRET ---
        if not has_secret:
            # Belum ada file secret -> MERAH
            self.btn_secret.setText("Add Secret")
            self.btn_secret.setStyleSheet("""
                QPushButton { border: 1px solid #cc0000; color: #ffcccc; background: #330000; padding: 4px 10px; font-size: 11px; border-radius: 3px; }
                QPushButton:hover { background: #cc0000; color: white; }
            """)
        else:
            self.btn_secret.setText("Ganti Secret")
            if is_connected:
                # Sudah ada secret & Connected -> HIJAU
                self.btn_secret.setStyleSheet("""
                    QPushButton { border: 1px solid #2ba640; color: white; background: #2ba640; padding: 4px 10px; font-size: 11px; border-radius: 3px; }
                    QPushButton:hover { background: #33cc33; }
                """)
            else:
                # Sudah ada secret tapi belum Connected -> BIRU
                self.btn_secret.setStyleSheet("""
                    QPushButton { border: 1px solid #3b82f6; color: white; background: #1d4ed8; padding: 4px 10px; font-size: 11px; border-radius: 3px; }
                    QPushButton:hover { background: #3b82f6; border-color: #60a5fa; }
                """)

        # --- B. LOGIKA TOMBOL OAUTH ---
        if is_connected:
            self.btn_oauth.setText("Connected ✔")
            self.btn_oauth.setEnabled(False)
            self.btn_oauth.setStyleSheet("""
                QPushButton { border: 1px solid #2ba640; color: white; background: #2ba640; font-weight: bold; padding: 4px 10px; font-size: 11px; border-radius: 3px;}
                QPushButton:disabled { background: #2ba640; color: white; border-color: #2ba640; opacity: 1; }
            """)
            self.refresh_channel_data()
        else:
            self.btn_oauth.setText("OAuth Login")
            self.btn_oauth.setEnabled(True)
            self.btn_oauth.setStyleSheet("""
                QPushButton { border: 1px solid #cc0000; color: white; background: #cc0000; font-weight: bold; padding: 4px 10px; font-size: 11px; border-radius: 3px; }
                QPushButton:hover { background: #e60000; border-color: #ff3333; }
            """)

        # --- C. UPDATE STAT CARD ---
        if hasattr(self, 'auth_stat_card'):
            self.auth_stat_card.update_value(status_text)
            self.auth_stat_card.setStyleSheet(f"""
                QFrame {{
                    background-color: #2f2f2f;
                    border-radius: 6px;
                    border-left: 3px solid {status_color};
                    padding: 5px 8px;
                }}
            """)

    # 2. Update Method action_oauth 
    # (Menambah validasi klik jika secret belum ada)
    def action_oauth(self):
        # 1. Cek keberadaan file
        paths = AuthManager.get_paths(self.category, self.channel_name)
        if not os.path.exists(paths["secret"]):
            QMessageBox.warning(self, "Missing Secret", "File 'client_secret.json' tidak ditemukan!\nSilakan klik 'Add Secret' dulu.")
            return

        # 2. [LOGIKA BARU] Validasi Isi File Secret
        try:
            with open(paths["secret"], "r") as f:
                content = json.load(f)
                
            # Cek apakah file masih dummy (kosong)
            if not content or content == {}:
                QMessageBox.warning(self, "Invalid Secret", 
                    "File 'client_secret.json' masih kosong/dummy!\n\n"
                    "Ini adalah file otomatis saat Channel dibuat. "
                    "Anda HARUS menggantinya dengan file asli dari Google Cloud Console.\n"
                    "Klik tombol 'Ganti Secret' dan pilih file yang benar."
                )
                return
                
            # Cek apakah formatnya benar (harus ada key 'installed' atau 'web')
            if "installed" not in content and "web" not in content:
                QMessageBox.critical(self, "Format Salah", 
                    "File JSON ini sepertinya bukan Client Secret yang valid.\n"
                    "Pastikan Anda mengunduh file 'OAuth 2.0 Client ID' dari Google Cloud Console."
                )
                return

        except json.JSONDecodeError:
            QMessageBox.critical(self, "File Corrupt", "File 'client_secret.json' rusak atau bukan format JSON yang valid.")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal membaca file secret: {str(e)}")
            return

        # 3. Jalankan Worker jika validasi lolos
        self.btn_oauth.setEnabled(False)
        self.btn_oauth.setText("Waiting...")
        
        # Pastikan Worker dibuat baru setiap kali klik
        if self.oauth_worker is not None:
            if self.oauth_worker.isRunning():
                self.oauth_worker.terminate()
            self.oauth_worker = None

        self.oauth_worker = OAuthWorker(self.category, self.channel_name)
        self.oauth_worker.finished.connect(self.on_oauth_finished)
        self.oauth_worker.auth_url_signal.connect(self.on_auth_url_received)
        self.oauth_worker.start()

    def action_add_secret(self):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih client_secret.json", "", "JSON (*.json)")
        if path:
            try:
                base_dir = os.path.join("channels", self.category, self.channel_name)
                target_path = os.path.join(base_dir, "client_secret.json")
                shutil.copy(path, target_path)
                QMessageBox.information(self, "Sukses", "Client Secret berhasil disimpan.\nSilakan klik tombol 'OAuth Login'.")
                self.check_auth_status()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menyimpan secret: {str(e)}")


    def on_auth_url_received(self, url):
        # 1. Setup Dialog UI
        self.auth_dialog = QDialog(self)
        self.auth_dialog.setWindowTitle("Login YouTube")
        self.auth_dialog.setMinimumWidth(500)
        self.auth_dialog.setStyleSheet("background: #2f2f2f; color: white;")
        
        layout = QVBoxLayout(self.auth_dialog)
        
        lbl_info = QLabel("1. Salin link di bawah ini.\n2. Buka browser dan paste link.\n3. Login Google & izinkan akses.\n4. Tunggu sampai muncul halaman 'Login Berhasil'.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #ccc; margin-bottom: 10px;")
        layout.addWidget(lbl_info)
        
        txt_url = QLineEdit(url)
        txt_url.setReadOnly(True)
        txt_url.setStyleSheet("padding: 8px; border: 1px solid #555; background: #181818; color: #89b4fa; font-weight: bold;")
        layout.addWidget(txt_url)
        
        btn_box = QHBoxLayout()
        btn_copy = QPushButton("Copy Link")
        btn_copy.setCursor(Qt.PointingHandCursor)
        btn_copy.setStyleSheet("background: #2ba640; color: white; font-weight: bold; padding: 8px; border: none; border-radius: 4px;")
        btn_copy.clicked.connect(lambda: self.copy_to_clipboard(url, btn_copy))
        
        btn_close = QPushButton("Batal")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("background: transparent; border: 1px solid #555; color: #aaa; padding: 8px; border-radius: 4px;")
        # Ini akan men-trigger result() == QDialog.Rejected
        btn_close.clicked.connect(self.auth_dialog.reject)
        
        btn_box.addWidget(btn_copy)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)
        
        # 2. Tampilkan Dialog & Tunggu Hasilnya (Block sampai ditutup)
        result = self.auth_dialog.exec()

        # 3. [LOGIKA BARU] Cek Jika User Menutup/Cancel Dialog
        if result == QDialog.Rejected:
            print("Login dibatalkan oleh user.")
            
            # A. Matikan Worker Paksa (Terminate)
            # Ini penting karena worker sedang blocking menunggu koneksi socket
            if self.oauth_worker is not None:
                if self.oauth_worker.isRunning():
                    self.oauth_worker.terminate()
                    self.oauth_worker.wait() # Tunggu sampai benar-benar mati
                self.oauth_worker = None # Bersihkan referensi

            # B. Reset Tombol ke Semula
            self.btn_oauth.setText("OAuth Login")
            self.btn_oauth.setEnabled(True)
            self.btn_oauth.setStyleSheet("""
                QPushButton { border: 1px solid #cc0000; color: white; background: #cc0000; font-weight: bold; padding: 6px 12px; }
                QPushButton:hover { background: #e60000; border-color: #ff3333; }
            """)

    def on_oauth_finished(self, success, msg):
        # Tutup dialog jika masih terbuka
        if hasattr(self, 'auth_dialog') and self.auth_dialog.isVisible():
            self.auth_dialog.accept()

        self.btn_oauth.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Sukses", "Login Berhasil! Token tersimpan.")
            self.check_auth_status() # Update UI jadi hijau
        else:
            self.btn_oauth.setText("OAuth Login") # Reset teks tombol
            
            # Jika user membatalkan (menutup dialog), jangan tampilkan error critical
            if "socket" in str(msg).lower() or "closed" in str(msg).lower():
                 return # Dianggap cancel

            QMessageBox.critical(self, "Gagal", f"Login Gagal:\n{msg}")

    def copy_to_clipboard(self, text, btn_sender):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        btn_sender.setText("Copied! ✔")
        QTimer.singleShot(2000, lambda: btn_sender.setText("Copy Link"))

    # [TAMBAHKAN METHOD BARU INI]
    def refresh_channel_data(self):
        # [PENGAMAN] Cek apakah worker sudah ada dan sedang berjalan
        if self.info_worker is not None and self.info_worker.isRunning():
            print("Worker sedang berjalan, permintaan refresh diabaikan.")
            return

        # Jika aman, baru jalankan worker baru
        self.info_worker = ChannelInfoWorker(self.category, self.channel_name)
        self.info_worker.finished_signal.connect(self.on_channel_data_received)
        
        # Bersihkan referensi worker setelah selesai agar memori bersih
        self.info_worker.finished.connect(lambda: setattr(self, 'info_worker', None))
        
        self.info_worker.start()

    def on_channel_data_received(self, success, data, msg):
        # 1. JIKA GAGAL / ERROR
        if not success:
            # Set nilai default agar UI tidak kosong melompong
            self.stat_subs.update_value("-")
            self.stat_views.update_value("-")
            
            # Deteksi Error Spesifik: API Belum Enable
            if "accessNotConfigured" in msg or "API v3 has not been used" in msg:
                QMessageBox.critical(
                    self, 
                    "YouTube API Belum Aktif", 
                    "⚠️ Gagal Terhubung ke YouTube!\n\n"
                    "Penyebab: YouTube Data API v3 belum diaktifkan di Google Cloud Console.\n\n"
                    "Solusi:\n"
                    "1. Buka Google Cloud Console.\n"
                    "2. Cari 'YouTube Data API v3'.\n"
                    "3. Klik tombol 'ENABLE'.\n"
                    "4. Tunggu 1-2 menit, lalu restart aplikasi ini."
                )
            # Deteksi Error Spesifik: Token Expired/Invalid tapi lolos cek awal
            elif "invalid_grant" in msg or "Token not found" in msg:
                 QMessageBox.warning(
                    self,
                    "Sesi Berakhir",
                    "Token akses Anda kadaluarsa atau tidak valid.\n"
                    "Silakan hapus file 'token.json' manual atau login ulang."
                )
            # Error Umum Lainnya
            else:
                # Potong pesan error jika terlalu panjang agar popup muat
                short_msg = (msg[:200] + '..') if len(msg) > 200 else msg
                QMessageBox.warning(self, "Gagal Memuat Data", f"Terjadi kesalahan teknis:\n{short_msg}")
            
            return

        # 2. JIKA SUKSES (Kode Lama)
        # Format subs (contoh: 1200 -> 1.2K)
        subs = int(data.get('subscriberCount', 0))
        if subs >= 1000000: subs_str = f"{subs/1000000:.2f}M"
        elif subs >= 1000: subs_str = f"{subs/1000:.1f}K"
        else: subs_str = str(subs)
        
        views = int(data.get('viewCount', 0))
        if views >= 1000000: views_str = f"{views/1000000:.1f}M"
        elif views >= 1000: views_str = f"{views/1000:.1f}K"
        else: views_str = str(views)

        self.stat_subs.update_value(subs_str)
        self.stat_views.update_value(views_str)

        # Update Table
        self.recent_table.update_data(data.get('videos', []))

    def create_stats_widget(self):
        container = QWidget()
        l = QVBoxLayout(container)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(8) 
        
        # --- HEADER ROW (HANYA TOMBOL) ---
        header_row = QWidget()
        hl = QHBoxLayout(header_row)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(10)
        
        # [HAPUS] Label "CHANNEL OVERVIEW" dihapus agar lebih bersih
        
        hl.addStretch() # Spacer agar tombol tetap di kanan
        
        # Tombol Add Secret
        self.btn_secret = QPushButton("Add Secret")
        self.btn_secret.setCursor(Qt.PointingHandCursor)
        self.btn_secret.clicked.connect(self.action_add_secret)
        self.btn_secret.setStyleSheet("""
            QPushButton { border: 1px solid #444; color: #aaa; background: #2a2a2a; padding: 4px 10px; font-size: 11px; border-radius: 3px; }
            QPushButton:hover { background: #333; color: white; border-color: #666; }
        """)
        hl.addWidget(self.btn_secret)
        
        # Tombol OAuth Login
        self.btn_oauth = QPushButton("OAuth Login")
        self.btn_oauth.setCursor(Qt.PointingHandCursor)
        self.btn_oauth.clicked.connect(self.action_oauth)
        self.btn_oauth.setStyleSheet("""
            QPushButton { border: 1px solid #cc0000; color: white; background: #cc0000; font-weight: bold; padding: 4px 10px; font-size: 11px; border-radius: 3px; }
            QPushButton:hover { background: #e60000; border-color: #ff3333; }
        """)
        hl.addWidget(self.btn_oauth)
        
        l.addWidget(header_row)
        
        # --- CARDS ROW ---
        stats_content = QWidget()
        grid = QHBoxLayout(stats_content)
        grid.setContentsMargins(0,0,0,0)
        grid.setSpacing(5)
        
        self.stat_subs = StatCard("SUBS", "-", "#cc0000")
        self.stat_views = StatCard("TOTAL VIEWS", "-", "#2ba640")
        self.auth_stat_card = StatCard("AUTH STATUS", "Checking...", "#777")
        
        grid.addWidget(self.stat_subs)
        grid.addWidget(self.stat_views)
        grid.addWidget(self.auth_stat_card)

        l.addWidget(stats_content)
        # [HAPUS] l.addStretch() tidak diperlukan lagi karena kita ingin compact
        return container

    def create_history_widget(self):
        container = QWidget()
        l = QVBoxLayout(container)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0) # Spacing 0 agar tabel benar-benar full
        
        # [HAPUS] Bagian Header Label "RIWAYAT TERAKHIR" dihapus total
        
        self.recent_table = RecentVideosTable(self.channel_name)
        l.addWidget(self.recent_table)
        return container

    # --- [METHOD BARU] Membuat Bar Tombol Auth ---
    def create_action_bar(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 10) # Margin bawah sedikit
        layout.setAlignment(Qt.AlignRight) # Rata Kanan
        layout.setSpacing(10)

        # Tombol Add Secret
        self.btn_secret = QPushButton("Add Secret")
        self.btn_secret.setCursor(Qt.PointingHandCursor)
        self.btn_secret.clicked.connect(self.action_add_secret)
        self.btn_secret.setStyleSheet("""
            QPushButton { border: 1px solid #555; color: #ccc; background: #333; padding: 6px 12px; }
            QPushButton:hover { background: #444; border-color: #777; color: white; }
        """)
        
        # Tombol OAuth Login
        self.btn_oauth = QPushButton("OAuth Login")
        self.btn_oauth.setCursor(Qt.PointingHandCursor)
        self.btn_oauth.clicked.connect(self.action_oauth)
        # Style default (Merah / Belum Login)
        self.btn_oauth.setStyleSheet("""
            QPushButton { border: 1px solid #cc0000; color: white; background: #cc0000; font-weight: bold; padding: 6px 12px; }
            QPushButton:hover { background: #e60000; border-color: #ff3333; }
        """)

        layout.addWidget(self.btn_secret)
        layout.addWidget(self.btn_oauth)
        
        return container
    
    def create_upload_widget(self):
        container = QFrame()
        container.setStyleSheet("QFrame { background-color: #212121; border: 1px solid #333; border-radius: 6px; }")
        l = QVBoxLayout(container)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)

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

        self.scroll = VideoDropArea(self)
        content_widget = QWidget()
        content_widget.setObjectName("DropContent")
        self.rows_layout = QVBoxLayout(content_widget)
        self.rows_layout.setSpacing(0)
        self.rows_layout.setContentsMargins(0,0,0,0)
        self.rows_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(content_widget)
        l.addWidget(self.scroll)

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

        self.btn_del_selected = QPushButton("Hapus Terpilih")
        self.btn_del_selected.setFixedWidth(120)
        self.btn_del_selected.setCursor(Qt.PointingHandCursor)
        self.btn_del_selected.setStyleSheet("QPushButton { background: transparent; color: #777; border: 1px solid #444; border-radius: 4px; } QPushButton:hover { color: #ff5555; border-color: #ff5555; background: rgba(255,85,85,0.1); }")
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
        files, _ = QFileDialog.getOpenFileNames(self, "Pilih Video", "", "Video Files (*.mp4 *.mkv *.avi *.mov *.flv *.webm)")
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
        reply = QMessageBox.question(self, "Konfirmasi", f"Hapus {len(self.selected_rows)} item terpilih?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for row in self.selected_rows[:]: 
                row.delete_me()
            self.selected_rows = []
            self.update_delete_button()

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

    def update_status_ui(self, status_text): pass 

    def on_upload_finished(self, success, msg):
        # Logika "Silent Notification" untuk Multitasking
        
        if success:
            # Jika sukses, lanjut ke antrean berikutnya
            # Kita tidak perlu popup mengganggu setiap satu video selesai
            print(f"[{self.channel_name}] Sukses: {msg}")
            self.process_next_in_queue()
        else:
            # Jika Error, baru kita putuskan apakah perlu Popup
            if self.isVisible():
                # Jika user sedang melihat halaman ini, tampilkan Popup
                QMessageBox.critical(self, "Upload Gagal", f"Gagal mengupload {self.current_processing_title}:\n{msg}")
            else:
                # Jika user sedang di channel lain, jangan ganggu!
                # Cukup ubah tombol jadi merah sebagai tanda
                self.btn_action.setText(f"ERROR: {self.current_processing_title[:10]}...")
                self.btn_action.setStyleSheet("background: #cc0000; color: white;")
                
            # Lanjut (atau stop tergantung kebijakan, di sini kita coba lanjut)
            self.process_next_in_queue()

    def finish_upload_session(self):
        self.btn_action.setText("SEMUA SELESAI! ✔")
        self.btn_action.setStyleSheet("background-color: #2ba640; color: white; border: none;")
        
        # Hanya munculkan Popup "All Done" jika user sedang melihat halaman ini
        if self.isVisible():
            QMessageBox.information(self, "Selesai", "Semua video dalam antrean berhasil diupload!")
            
        QTimer.singleShot(3000, self.reset_button)

    def reset_button(self):
        self.btn_action.setText("MULAI UPLOAD ANTRIAN")
        self.btn_action.setEnabled(True)
        self.btn_action.setStyleSheet("background: #cc0000; color: white; font-weight: bold; border: none;")