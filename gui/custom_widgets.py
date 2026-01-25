from PySide6.QtWidgets import (
    QTextEdit, QFrame, QVBoxLayout, QComboBox, QSizePolicy, 
    QPushButton, QWidgetAction, QCalendarWidget, QMenu, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate, Signal, QRect
from PySide6.QtGui import QTextCharFormat, QColor, QFont

class AutoResizingTextEdit(QTextEdit):
    """
    Text area yang otomatis membesar, TAPI menolak drop file 
    agar file yang di-drag tidak masuk sebagai teks aneh.
    """
    heightChanged = Signal() 

    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        # [PENTING] Matikan fitur drop bawaan agar tidak 'memakan' file path
        self.setAcceptDrops(False) 
        
        self.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                border-bottom: 2px solid transparent; 
                padding: 6px;
                color: white;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
            QTextEdit:focus {
                border-bottom: 2px solid #cc0000;
                background-color: #262626;
            }
        """)
        
        self.min_height = 50 
        self.setMinimumHeight(self.min_height)
        self.document().contentsChanged.connect(self.adjust_height)

    def adjust_height(self):
        doc_height = self.document().size().height()
        new_height = int(doc_height + 15) 
        if new_height < self.min_height: new_height = self.min_height
            
        if new_height != self.minimumHeight():
            self.setMinimumHeight(new_height)
            self.heightChanged.emit() 
            self.updateGeometry()

class DateSelectorButton(QPushButton):
    """ Tombol Tanggal Custom dengan Popup Kalender """
    def __init__(self):
        super().__init__()
        self.current_date = QDate.currentDate()
        self.setText(self.current_date.toString("yyyy-MM-dd"))
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(30)
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                color: #ddd;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                padding-left: 10px;
                text-align: left;
                font-size: 11px;
            }
            QPushButton:hover {
                border-color: #cc0000;
                background-color: #252525;
                color: white;
            }
        """)

        # Setup Menu & Kalender
        self.menu = QMenu(self)
        self.menu.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.menu.setAttribute(Qt.WA_TranslucentBackground)
        self.menu.setStyleSheet("QMenu { background: transparent; border: none; }")
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setNavigationBarVisible(True)
        
        # 1. Disable tanggal sebelum hari ini
        self.calendar.setMinimumDate(QDate.currentDate())
        
        # 2. Highlight Current Date
        self.highlight_today()

        # Style Kalender
        self.calendar.setStyleSheet("""
            QCalendarWidget QWidget { 
                background-color: #2f2f2f; 
                color: white; 
                border-radius: 6px;
            }
            QCalendarWidget QToolButton {
                color: white;
                background-color: transparent;
                icon-size: 16px;
                font-weight: bold;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #444;
                border-radius: 4px;
            }
            QCalendarWidget QSpinBox {
                background-color: #222;
                color: white;
                selection-background-color: #cc0000;
            }
            QCalendarWidget QTableView {
                background-color: #2f2f2f;
                selection-background-color: #cc0000;
                selection-color: white;
                outline: none;
            }
            QCalendarWidget QTableView::item:hover {
                background-color: #444;
            }
            QCalendarWidget QTableView::item:disabled {
                color: #555555;
                background-color: #252525;
            }
        """)
        
        self.calendar.clicked.connect(self.on_date_selected)
        
        cal_action = QWidgetAction(self.menu)
        cal_action.setDefaultWidget(self.calendar)
        self.menu.addAction(cal_action)
        
        self.clicked.connect(self.show_calendar)

    def highlight_today(self):
        """Memberi highlight warna Cyan khusus untuk hari ini"""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("black"))
        fmt.setBackground(QColor("#06b6d4"))
        
        # [FIX] Ambil font objek dari kalender dan set ke format
        # Ini mencegah error "Point size <= 0" karena format baru tidak punya size.
        font = self.calendar.font()
        font.setBold(True)
        fmt.setFont(font)
        
        self.calendar.setDateTextFormat(QDate.currentDate(), fmt)

    def show_calendar(self):
        self.calendar.setSelectedDate(self.current_date)
        self.menu.exec(self.mapToGlobal(self.rect().bottomLeft()))

    def on_date_selected(self, date):
        self.current_date = date
        self.setText(date.toString("yyyy-MM-dd"))
        self.menu.close()
        
    def get_date_str(self):
        return self.current_date.toString("yyyy-MM-dd")

class ScheduleWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent; border: none;")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        self.setFixedWidth(130) 
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignTop)

        # 1. Date
        self.date_btn = DateSelectorButton()
        
        # 2. Time
        self.time_combo = QComboBox()
        self.time_combo.setCursor(Qt.PointingHandCursor)
        self.time_combo.setFixedHeight(30)
        self.time_combo.setMaxVisibleItems(10)
        
        self.time_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e1e1e;
                color: #ddd;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                padding-left: 10px;
                font-size: 11px;
            }
            QComboBox:hover {
                border-color: #cc0000;
                color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #2f2f2f;
                color: white;
                selection-background-color: #cc0000;
                border: 1px solid #333;
                outline: none;
            }
        """)
        self.populate_times()

        layout.addWidget(self.date_btn)
        layout.addWidget(self.time_combo)

    def populate_times(self):
        self.time_combo.clear()
        for h in range(24):
            for m in [0, 15, 30, 45]:
                self.time_combo.addItem(f"{h:02d}:{m:02d}")

    def get_scheduled_datetime(self):
        return {
            "date": self.date_btn.get_date_str(),
            "time": self.time_combo.currentText()
        }