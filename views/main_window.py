# views/main_window.py
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox, 
    QPushButton, QHBoxLayout, QDialog, QLabel, QProgressBar, QProgressDialog
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from .generate_tab import GenerateTab
from .settings_tab import SettingsTab
from utils import SettingsManager
from workers import NaverNewsWorker
from .news_result_dialog import NewsResultDialog
from ai_modules import BlogGenerator
from .blog_result_dialog import BlogResultDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 설정 관리자 초기화
        self.settings_manager = SettingsManager()
        
        # 워커 및 다이얼로그 초기화
        self.news_worker = None
        self.news_dialog = None
        self.blog_generator = None
        self.blog_progress_dialog = None
        self.one_click_worker = None
        self.progress_dialog = None
        
        self.setup_ui()
        self.set_app_icon()
        self.load_previous_settings()
        self.connect_signals()
        
    def setup_ui(self):
        """UI 구성"""
        self.setWindowTitle('Blog Generator')
        
        # 저장된 윈도우 크기/위치 복원
        geometry = self.settings_manager.get_window_geometry()
        self.setGeometry(
            geometry['x'], 
            geometry['y'], 
            geometry['width'], 
            geometry['height']
        )
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 탭 위젯 생성
        self.tabs = QTabWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)
        
        # 탭 생성
        self.generate_tab = GenerateTab()
        self.settings_tab = SettingsTab()
        
        self.tabs.addTab(self.generate_tab, "생성")
        self.tabs.addTab(self.settings_tab, "설정")
        
    def set_app_icon(self):
        """앱 아이콘 설정"""
        icon_path = 'icon/app_icon.svg'
        
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)
            print(f"✅ 앱 아이콘이 설정되었습니다: {icon_path}")
        else:
            print(f"⚠️ 아이콘 파일을 찾을 수 없습니다: {icon_path}")
            
    def load_previous_settings(self):
        """이전 설정 로드"""
        try:
            # API 설정 로드 (설정 탭용)
            api_settings = self.settings_manager.get_api_settings()
            self.settings_tab.set_form_data(api_settings)
            
            # 검색 설정 로드 (생성 탭용)
            search_settings = self.settings_manager.get_last_search_settings()
            category_index = search_settings.get('category_index', 0)
            keyword = search_settings.get('keyword', '')
            
            # 폼에 설정값 적용
            if hasattr(self, 'generate_tab'):
                if hasattr(self.generate_tab, 'category_dropdown'):
                    self.generate_tab.category_dropdown.setCurrentIndex(category_index)
                if hasattr(self.generate_tab, 'topic_edit'):
                    self.generate_tab.topic_edit.setText(keyword)
            
            print(f"📋 이전 설정 로드: 카테고리 {category_index}, 키워드 '{keyword}'")
            
        except Exception as e:
            print(f"⚠️ 이전 설정 로드 실패: {e}")
    
    def connect_signals(self):
        """시그널 연결"""
        try:
            # 생성 탭 시그널 연결
            if hasattr(self.generate_tab, 'generation_requested'):
                self.generate_tab.generation_requested.connect(self.handle_generation_request)
            
            if hasattr(self.generate_tab, 'search_settings_changed'):
                self.generate_tab.search_settings_changed.connect(self.save_search_settings)
            
            # 설정 탭 시그널 연결
            if hasattr(self.settings_tab, 'settings_saved'):
                self.settings_tab.settings_saved.connect(self.handle_settings_save)
            
            if hasattr(self.settings_tab, 'settings_cancelled'):
                self.settings_tab.settings_cancelled.connect(self.handle_settings_cancel)
            
            print("🔗 모든 시그널 연결 완료")
            
        except Exception as e:
            print(f"⚠️ 시그널 연결 중 오류: {e}")
    
    def handle_settings_save(self, settings_data):
        """설정 저장 처리"""
        try:
            print(f"📝 설정 저장 요청: {len(settings_data)}개 항목")
            
            # API 설정 저장
            self.settings_manager.set_api_settings(settings_data)
            
            # 설정 탭에 성공 메시지 표시
            QMessageBox.information(
                self,
                "설정 저장 완료",
                "API 키 설정이 성공적으로 저장되었습니다.\n\n" +
                "이제 블로그 생성 기능을 사용할 수 있습니다."
            )
            
            print("✅ 설정 저장 완료")
            
        except Exception as e:
            print(f"❌ 설정 저장 실패: {e}")
            
            QMessageBox.critical(
                self,
                "설정 저장 실패",
                f"설정 저장 중 오류가 발생했습니다:\n{str(e)}"
            )

    def handle_settings_cancel(self):
        """설정 취소 처리"""
        print("📋 설정 변경 취소")
        
        # 기존 설정값으로 폼 복원
        api_settings = self.settings_manager.get_api_settings()
        self.settings_tab.set_form_data(api_settings)
        
        QMessageBox.information(
            self,
            "설정 취소",
            "설정 변경이 취소되고 이전 설정으로 복원되었습니다."
        )
        
    def save_search_settings(self, category_index, keyword):
        """검색 설정 저장"""
        try:
            self.settings_manager.set_last_search_settings(category_index, keyword)
            print(f"🔍 검색 설정 저장: 카테고리 {category_index}, 키워드 '{keyword}'")
        except Exception as e:
            print(f"⚠️ 검색 설정 저장 실패: {e}")
        
    def handle_generation_request(self, category_name, topic, category_id):
        """블로그 생성 요청 처리"""
        print(f"🚀 원클릭 블로그 생성 시작: {topic}")
        
        # 현재 검색 설정 저장
        current_search = self.generate_tab.get_form_data()
        self.save_search_settings(
            self.generate_tab.category_dropdown.currentIndex(),
            current_search['topic']
        )
        
        # API 설정 확인
        api_settings = self.settings_manager.get_api_settings()
        naver_client_id = api_settings.get('naver_client_id', '').strip()
        naver_client_secret = api_settings.get('naver_client_secret', '').strip()
        gemini_api_key = api_settings.get('google_api_key', '').strip()
        
        # API 키 검증
        missing_keys = []
        if not naver_client_id:
            missing_keys.append("Naver Client ID")
        if not naver_client_secret:
            missing_keys.append("Naver Client Secret") 
        if not gemini_api_key:
            missing_keys.append("Google Gemini API Key")
        
        if missing_keys:
            QMessageBox.warning(
                self,
                "API 키 필요",
                f"다음 API 키가 필요합니다:\n• {', '.join(missing_keys)}\n\n" +
                "설정 탭에서 API 키를 입력하고 저장해주세요."
            )
            self.tabs.setCurrentIndex(1)  # 설정 탭으로 이동
            return
        
        # 전체 프로세스를 하나의 워커로 통합
        self.start_one_click_generation(category_name, topic, category_id, 
                                       naver_client_id, naver_client_secret, gemini_api_key)

    def start_one_click_generation(self, category_name, topic, category_id, 
                                  naver_id, naver_secret, gemini_key):
        """통합 생성 워커 시작"""
        try:
            from workers.one_click_blog_worker import OneClickBlogWorker
            
            self.one_click_worker = OneClickBlogWorker(
                naver_id, naver_secret, gemini_key,
                topic, category_id, category_name
            )
            
            # 시그널 연결
            self.one_click_worker.finished.connect(self.on_one_click_finished)
            self.one_click_worker.error.connect(self.on_one_click_error)
            self.one_click_worker.progress.connect(self.on_one_click_progress)
            self.one_click_worker.status_changed.connect(self.on_one_click_status)
            
            # 진행상황 표시
            self.show_simple_progress()
            
            # 워커 시작
            self.one_click_worker.start()
            
        except ImportError as e:
            QMessageBox.critical(
                self,
                "모듈 오류",
                f"원클릭 블로그 워커를 불러올 수 없습니다:\n{str(e)}\n\n" +
                "workers/one_click_blog_worker.py 파일을 확인해주세요."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "생성 시작 실패",
                f"블로그 생성을 시작할 수 없습니다:\n{str(e)}"
            )

    def show_simple_progress(self):
        """간단한 진행상황 표시"""
        self.progress_dialog = QProgressDialog("블로그 생성 중...", "취소", 0, 100, self)
        self.progress_dialog.setWindowTitle("AI 블로그 생성")
        self.progress_dialog.setModal(True)
        self.progress_dialog.canceled.connect(self.cancel_generation)
        self.progress_dialog.show()

    def cancel_generation(self):
        """블로그 생성 취소"""
        if self.one_click_worker and self.one_click_worker.isRunning():
            self.one_click_worker.terminate()
            self.one_click_worker.wait(3000)  # 3초 대기
            print("🚫 블로그 생성이 취소되었습니다.")

    def on_one_click_progress(self, value):
        """진행률 업데이트"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setValue(value)

    def on_one_click_status(self, status):
        """상태 업데이트"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setLabelText(status)

    def on_one_click_finished(self, blog_data):
        """생성 완료"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
        
        try:
            # 결과 표시
            result_dialog = BlogResultDialog(blog_data, self)
            result_dialog.exec()
            
            print("✅ 원클릭 블로그 생성 완료")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "결과 표시 오류",
                f"생성된 블로그를 표시하는 중 오류가 발생했습니다:\n{str(e)}"
            )

    def on_one_click_error(self, error_msg):
        """생성 오류"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
        
        QMessageBox.critical(
            self,
            "블로그 생성 실패",
            f"AI 블로그 생성 중 오류가 발생했습니다:\n\n{error_msg}\n\n" +
            "💡 해결 방법:\n" +
            "1. 구글 API 키가 올바른지 확인\n" +
            "2. 인터넷 연결 상태 확인\n" +
            "3. API 할당량 확인 (Google AI Studio)"
        )
        
        print(f"❌ 원클릭 블로그 생성 실패: {error_msg}")

    def closeEvent(self, event):
        """앱 종료 시 윈도우 설정 저장"""
        try:
            # 현재 윈도우 위치/크기 저장
            geometry = self.geometry()
            window_settings = {
                'x': geometry.x(),
                'y': geometry.y(),
                'width': geometry.width(),
                'height': geometry.height()
            }
            
            self.settings_manager.set_window_geometry(window_settings)
            print("💾 윈도우 설정 저장 완료")
            
            # 실행 중인 워커 정리
            if self.one_click_worker and self.one_click_worker.isRunning():
                self.one_click_worker.terminate()
                self.one_click_worker.wait(3000)
            
        except Exception as e:
            print(f"⚠️ 종료 처리 중 오류: {e}")
        
        # 앱 종료
        event.accept()
