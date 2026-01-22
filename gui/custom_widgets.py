# gui/custom_widgets.py
from PySide6.QtWidgets import QTextEdit, QFrame, QVBoxLayout, QLabel, QDateEdit, QComboBox
from PySide6.QtCore import Qt, QSize, QDate, Signal

class AutoResizingTextEdit(QTextEdit):
    """
    Text area yang otomatis membesar tingginya mengikuti konten (Auto-Expand).
    """
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("background: transparent; border: none; padding: 4px;")
        
        # Minimum tinggi
        self.min_height = 40
        self.setFixedHeight(self.min_height)
        
        self.textChanged.connect(self.adjust_height)

    def adjust_height(self):
        doc_height = self.document().size().height()
        # Tambahkan sedikit padding
        new_height = int(doc_height + 10) 
        if new_height < self.min_height:
            new_height = self.min_height
            
        self.setFixedHeight(new_height)
        # Emit signal agar parent layout bisa update jika perlu
        self.updateGeometry()

class ScheduleWidget(QFrame):
    """
    Widget gabungan Date + Time Dropdown (15 min interval).
    """
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Date Picker
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setStyleSheet("""
            QDateEdit { background: #181818; border: 1px solid #3f3f3f; padding: 4px; border-radius: 4px; }
            QDateEdit::drop-down { border: none; }
        """)

        # Time Dropdown
        self.time_combo = QComboBox()
        self.time_combo.setStyleSheet("""
            QComboBox { background: #181818; border: 1px solid #3f3f3f; padding: 4px; border-radius: 4px; }
            QComboBox QAbstractItemView { background: #2f2f2f; selection-background-color: #cc0000; }
        """)
        self.populate_times()

        layout.addWidget(self.date_edit)
        layout.addWidget(self.time_combo)

    def populate_times(self):
        for h in range(24):
            for m in [0, 15, 30, 45]:
                self.time_combo.addItem(f"{h:02d}:{m:02d}")