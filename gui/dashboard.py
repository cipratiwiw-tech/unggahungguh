import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from utils import get_channel_structure

class StatCard(QFrame):
    def __init__(self, title, value, color_hex):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{ background-color: #2f2f2f; border-radius: 8px; border-left: 5px solid {color_hex}; }}
        """)
        l = QVBoxLayout(self)
        t = QLabel(title)
        t.setStyleSheet("color: #aaaaaa; font-size: 12px; font-weight: bold;")
        v = QLabel(value)
        v.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        l.addWidget(t)
        l.addWidget(v)
    
    def update_value(self, new_value):
        labels = self.findChildren(QLabel)
        if len(labels) >= 2:
            labels[1].setText(new_value)

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # 1. Stats Row
        stats_layout = QHBoxLayout()
        self.card_subs = StatCard("TOTAL SUBSCRIBER", "0", "#cc0000")
        self.card_revenue = StatCard("ESTIMASI PENDAPATAN", "-", "#2ba640")
        self.card_channels = StatCard("TOTAL CHANNEL", "0 Channel", "#ffaa00")

        stats_layout.addWidget(self.card_subs)
        stats_layout.addWidget(self.card_revenue)
        stats_layout.addWidget(self.card_channels)
        layout.addLayout(stats_layout)

        # 2. Table Label
        lbl_table = QLabel("Ringkasan Channel")
        lbl_table.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px; color: #ffffff;")
        layout.addWidget(lbl_table)

        # 3. Channel Table (Updated)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["NAMA CHANNEL", "SUBSCRIBERS", "TOTAL VIEWS", "JUMLAH VIDEO"])
        
        # Konfigurasi Header & Ukuran
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch) # Nama channel ambil sisa ruang
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Styling Table agar lebih "Clean" dan Tinggi
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(60) # [UPDATE] Tinggi baris diperbesar
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Tidak bisa diedit
        self.table.setShowGrid(False) # Hilangkan garis grid kasar
        self.table.setAlternatingRowColors(True) # Warna selang-seling
        
        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: #212121; 
                border: none; 
                border-radius: 8px;
                alternate-background-color: #2a2a2a; 
            }
            QHeaderView::section { 
                background-color: #1e1e1e; 
                color: #888888; 
                padding: 15px 10px; 
                border: none; 
                font-weight: bold; 
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            QTableWidget::item { 
                padding-left: 15px; 
                padding-right: 15px;
                border: none; 
                color: #e0e0e0; 
            }
        """)
        layout.addWidget(self.table)
        
        self.refresh_data()

    def showEvent(self, event):
        self.refresh_data()
        super().showEvent(event)

    def refresh_data(self):
        self.table.setRowCount(0)
        structure = get_channel_structure()
        
        total_subs_count = 0
        total_channels_count = 0
        
        font_bold = QFont()
        font_bold.setBold(True)
        font_bold.setPointSize(11)

        font_normal = QFont()
        font_normal.setPointSize(10)

        for category, channels in structure.items():
            for channel_name in channels:
                total_channels_count += 1
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Default Data
                subs_text = "-"
                views_text = "-"
                videos_text = "-"
                raw_subs = 0
                
                # Baca Cache JSON
                try:
                    cache_path = os.path.join("channels", category, channel_name, "stats.json")
                    if os.path.exists(cache_path):
                        with open(cache_path, "r") as f:
                            data = json.load(f)
                            
                            # 1. Subs
                            raw_subs = int(data.get("subscriberCount", 0))
                            total_subs_count += raw_subs
                            subs_text = self.format_number(raw_subs)
                            
                            # 2. Views
                            raw_views = int(data.get("viewCount", 0))
                            views_text = self.format_number(raw_views)

                            # 3. Video Count
                            raw_vids = int(data.get("videoCount", 0))
                            videos_text = f"{raw_vids} Video"

                except Exception as e:
                    print(f"Error reading stats for {channel_name}: {e}")

                # --- POPULATE COLUMNS ---
                
                # Col 0: Nama Channel (Bold)
                item_name = QTableWidgetItem(channel_name)
                item_name.setFont(font_bold)
                item_name.setToolTip(f"Kategori: {category}")
                self.table.setItem(row, 0, item_name)
                
                # Col 1: Subs
                item_subs = QTableWidgetItem(subs_text)
                item_subs.setFont(font_normal)
                item_subs.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                item_subs.setForeground(QColor("#4caf50")) # Aksen Hijau
                self.table.setItem(row, 1, item_subs)
                
                # Col 2: Total Views
                item_views = QTableWidgetItem(views_text)
                item_views.setFont(font_normal)
                item_views.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table.setItem(row, 2, item_views)

                # Col 3: Video Count
                item_vids = QTableWidgetItem(videos_text)
                item_vids.setFont(font_normal)
                item_vids.setForeground(QColor("#888888")) # Warna agak redup
                item_vids.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table.setItem(row, 3, item_vids)
        
        # Update Kartu Atas
        self.card_subs.update_value(self.format_number(total_subs_count))
        self.card_channels.update_value(f"{total_channels_count} Channel")
        self.card_revenue.update_value("-")

    def format_number(self, num):
        if num >= 1000000000: return f"{num/1000000000:.1f}B"
        if num >= 1000000: return f"{num/1000000:.1f}M"
        if num >= 1000: return f"{num/1000:.1f}K"
        return str(num)