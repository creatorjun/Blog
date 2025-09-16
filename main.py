import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QFont
from views import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont("Segoe UI", 9))
    icon_path = 'icon/app_icon.svg'
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()