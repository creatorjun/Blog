import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox
)
from PyQt6.QtGui import QIcon
from .generate_tab import GenerateTab
from .settings_tab import SettingsTab
from utils import SettingsManager
from workers import Worker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.worker = None
        self.setup_ui()
        self.set_app_icon()
        self.load_previous_settings()
        self.connect_signals()
        self.check_api_keys_on_startup()

    def setup_ui(self):
        self.setWindowTitle('Blog Generator')
        geometry = self.settings_manager.get_window_geometry()
        self.setGeometry(geometry['x'], geometry['y'], geometry['width'], geometry['height'])
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.tabs = QTabWidget()
        self.generate_tab = GenerateTab()
        self.settings_tab = SettingsTab()
        self.tabs.addTab(self.generate_tab, "생성")
        self.tabs.addTab(self.settings_tab, "설정")
        layout.addWidget(self.tabs)

    def set_app_icon(self):
        icon_path = 'icon/app_icon.svg'
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def load_previous_settings(self):
        try:
            api_settings = self.settings_manager.get_api_settings()
            self.settings_tab.set_form_data(api_settings)
            
            search_settings = self.settings_manager.get_last_search_settings()
            self.generate_tab.category_dropdown.setCurrentIndex(search_settings.get('category_index', 0))
            self.generate_tab.topic_edit.setText(search_settings.get('keyword', ''))
        except Exception as e:
            print(f"이전 설정 로드 실패: {e}")

    def connect_signals(self):
        self.generate_tab.generation_requested.connect(self.handle_generation_request)
        self.generate_tab.search_settings_changed.connect(self.save_search_settings)
        self.settings_tab.settings_saved.connect(self.handle_settings_save)
        self.settings_tab.settings_cancelled.connect(self.handle_settings_cancel)

    def check_api_keys_on_startup(self):
        api_settings = self.settings_manager.get_api_settings()
        required_keys = ['naver_client_id', 'naver_client_secret', 'google_api_key']
        
        missing_keys = [key for key in required_keys if not api_settings.get(key)]
        
        if missing_keys:
            self.tabs.setCurrentIndex(1)
            QMessageBox.warning(
                self,
                "API 키 필요",
                "블로그 생성을 위해 필수 API 키를 먼저 설정해야 합니다.\n\n" +
                "설정 탭에서 모든 필수 API 키를 입력하고 저장해주세요."
            )

    def handle_generation_request(self, category_name, topic, category_id):
        api_settings = self.settings_manager.get_api_settings()
        missing_keys = [key for key in ['naver_client_id', 'naver_client_secret', 'google_api_key'] if not api_settings.get(key)]
        
        if missing_keys:
            QMessageBox.warning(self, "API 키 필요", f"다음 API 키를 설정해주세요: {', '.join(missing_keys)}")
            self.tabs.setCurrentIndex(1)
            self.generate_tab.on_generation_error("API 키가 설정되지 않았습니다.")
            return

        self.worker = Worker(
            api_settings['naver_client_id'], api_settings['naver_client_secret'], api_settings['google_api_key'],
            topic, category_id, category_name
        )
        self.worker.finished.connect(self.generate_tab.on_generation_finished)
        self.worker.error.connect(self.generate_tab.on_generation_error)
        self.worker.start()

    def handle_settings_save(self, settings_data):
        self.settings_manager.set_api_settings(settings_data)
        QMessageBox.information(self, "저장 완료", "API 키 설정이 저장되었습니다.")

    def handle_settings_cancel(self):
        api_settings = self.settings_manager.get_api_settings()
        self.settings_tab.set_form_data(api_settings)

    def save_search_settings(self, category_index, keyword):
        self.settings_manager.set_last_search_settings(category_index, keyword)

    def closeEvent(self, event):
        geometry = self.geometry()
        window_settings = {'x': geometry.x(), 'y': geometry.y(), 'width': geometry.width(), 'height': geometry.height()}
        self.settings_manager.set_window_geometry(window_settings)
        
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(1000)
            
        event.accept()