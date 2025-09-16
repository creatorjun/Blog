# main.py
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QFont
from views import MainWindow

def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 스타일 설정
    app.setStyle('Fusion')

    # 🔧 기본 폰트를 안전한 폰트로 설정
    app.setFont(QFont("Segoe UI", 9))
    
    # 애플리케이션 전역 아이콘 설정 (태스크바용)
    icon_path = 'icon/app_icon.svg'
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    
    # 이벤트 루프 시작
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
