# gui/custom_widgets.py
from PySide6.QtWidgets import QTextEdit, QFrame, QVBoxLayout, QDateEdit, QComboBox, QSizePolicy
from PySide6.QtCore import Qt, QDate, Signal

class AutoResizingTextEdit(QTextEdit):
    """
    Text area yang otomatis membesar tingginya mengikuti konten (Auto-Expand).
    """
    heightChanged = Signal() # Signal agar parent layout bisa update

    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        self.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                border-bottom: 2px solid transparent; 
                padding: 6px;
                color: white;
                font-family: 'Segoe UI', sans-serif;
            }
            QTextEdit:focus {
                border-bottom: 2px solid #cc0000;
                background-color: #262626;
            }
        """)
        
        self.min_height = 45
        self.setFixedHeight(self.min_height)
        
        # Hubungkan perubahan isi dokumen ke fungsi resize
        self.document().contentsChanged.connect(self.adjust_height)

    def adjust_height(self):
        doc_height = self.document().size().height()
        new_height = int(doc_height + 15) # Padding extra agar nyaman
        
        if new_height < self.min_height:
            new_height = self.min_height
            
        if new_height != self.height():
            self.setFixedHeight(new_height)
            self.heightChanged.emit() # Beritahu parent
            self.updateGeometry()

class ScheduleWidget(QFrame):
    """
    Widget gabungan Date + Time Dropdown (15 min interval).
    """
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignTop) # Penting agar menempel ke atas saat row membesar

        input_style = """
            background: #181818; 
            border: 1px solid #3f3f3f; 
            border-radius: 4px;
            padding: 4px;
            color: white;
        """

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setStyleSheet(f"QDateEdit {{ {input_style} }}")

        self.time_combo = QComboBox()
        self.time_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        self.populate_times()

        layout.addWidget(self.date_edit)
        layout.addWidget(self.time_combo)

    def populate_times(self):
        self.time_combo.clear()
        for h in range(24):
            for m in [0, 15, 30, 45]:
                self.time_combo.addItem(f"{h:02d}:{m:02d}")