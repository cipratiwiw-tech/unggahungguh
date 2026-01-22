# gui/custom_widgets.py
from PySide6.QtWidgets import QTextEdit, QFrame, QVBoxLayout, QDateEdit, QComboBox
from PySide6.QtCore import Qt, QDate

class AutoResizingTextEdit(QTextEdit):
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        
        # Style Input: Border bawah merah saat fokus
        self.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                border-bottom: 2px solid transparent; 
                padding: 4px;
                color: white;
            }
            QTextEdit:focus {
                border-bottom: 2px solid #cc0000; /* Merah Fokus */
                background-color: #262626; /* Sedikit lebih gelap saat aktif */
            }
        """)
        
        self.min_height = 40
        self.setFixedHeight(self.min_height)
        self.textChanged.connect(self.adjust_height)

    def adjust_height(self):
        doc_height = self.document().size().height()
        new_height = int(doc_height + 10)
        if new_height < self.min_height:
            new_height = self.min_height
        self.setFixedHeight(new_height)
        self.updateGeometry()

class ScheduleWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5) # Padding agar tidak menempel border kolom
        layout.setSpacing(5)

        # Style input khusus untuk schedule
        input_style = """
            background: #181818; 
            border: 1px solid #3f3f3f; 
            border-radius: 4px;
            padding: 2px;
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
        for h in range(24):
            for m in [0, 15, 30, 45]:
                self.time_combo.addItem(f"{h:02d}:{m:02d}")