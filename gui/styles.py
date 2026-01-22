# gui/styles.py

COLORS = {
    "bg_main": "#212121",
    "bg_sidebar": "#181818",
    "bg_card": "#2f2f2f",
    "border": "#3f3f3f",          # Abu-abu Medium (Border Utama)
    "border_dark": "#2a2a2a",     # Abu-abu Gelap (Pemisah Kolom)
    "red_accent": "#cc0000",      # Merah YouTube
    "text_main": "#ffffff",
    "text_sec": "#aaaaaa",
    "success": "#2ba640",
    "warning": "#ffaa00"
}

GLOBAL_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #212121;
    color: #ffffff;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}

/* --- SCROLLBAR --- */
QScrollBar:vertical {
    border: none;
    background: #2f2f2f;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #3f3f3f;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* --- BUTTONS --- */
QPushButton {
    border: 1px solid #3f3f3f;
    border-radius: 4px;
    padding: 6px 12px;
    background-color: #2f2f2f;
    color: #ffffff;
}
QPushButton:hover {
    background-color: #3f3f3f;
}

/* --- INPUTS (Base Style) --- */
/* Style khusus fokus ada di implementasi widget masing-masing untuk kontrol lebih presisi */
QLineEdit, QTextEdit, QPlainTextEdit, QDateEdit, QComboBox {
    background-color: transparent; /* Transparan agar menyatu dengan grid */
    border: 1px solid transparent; /* Invisible border default */
    color: white;
    padding: 4px;
    border-radius: 0px; /* Flat look */
}

/* Dropdown styling */
QComboBox QAbstractItemView {
    background-color: #2f2f2f;
    border: 1px solid #3f3f3f;
    selection-background-color: #cc0000;
}
"""