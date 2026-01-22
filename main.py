# main.py
import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set style global ke app instance juga untuk memastikan dialog dsb kena style
    from gui.styles import GLOBAL_STYLESHEET
    app.setStyleSheet(GLOBAL_STYLESHEET)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())