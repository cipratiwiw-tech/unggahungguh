# gui/styles.py

GLOBAL_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #212121;
    color: #ffffff;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}

/* Scrollbar Styling */
QScrollBar:vertical {
    border: none;
    background: #2f2f2f;
    width: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #3f3f3f;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Generic Buttons */
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

/* Primary Red Button */
QPushButton.primary-btn {
    background-color: #cc0000;
    border: 1px solid #cc0000;
    color: white;
    font-weight: bold;
}
QPushButton.primary-btn:hover {
    background-color: #e60000;
}

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #181818;
    border: 1px solid #3f3f3f;
    color: white;
    padding: 5px;
    border-radius: 4px;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #cc0000;
}
"""

COLORS = {
    "bg_main": "#212121",
    "bg_sidebar": "#181818",
    "bg_card": "#2f2f2f",
    "border": "#3f3f3f",
    "red_accent": "#cc0000",
    "text_main": "#ffffff",
    "text_sec": "#aaaaaa",
    "success": "#2ba640",
    "warning": "#ffaa00"
}