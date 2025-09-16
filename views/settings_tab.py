# views/settings_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QLabel, QGroupBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

class SettingsTab(QWidget):
    """설정 탭 - 기본 네이티브 스타일 (CSS 미적용)"""
    
    settings_saved = pyqtSignal(dict)
    settings_cancelled = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성 (기본 스타일, CSS 미적용)"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # 제목 (기본 스타일)
        title_label = QLabel("API 키 설정")
        title_label.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 네이버 뉴스 API 설정 그룹
        news_group = QGroupBox("네이버 뉴스 API")
        news_layout = QFormLayout()
        
        self.naver_client_id_edit = QLineEdit()
        self.naver_client_id_edit.setPlaceholderText("네이버 Developer Console에서 발급받은 Client ID")
        
        self.naver_client_secret_edit = QLineEdit()
        self.naver_client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.naver_client_secret_edit.setPlaceholderText("네이버 Developer Console에서 발급받은 Client Secret")
        
        news_layout.addRow("Naver Client ID:", self.naver_client_id_edit)
        news_layout.addRow("Naver Client Secret:", self.naver_client_secret_edit)
        
        # 안내 라벨
        naver_info_label = QLabel("네이버 뉴스 검색을 위해 필요합니다\n발급: https://developers.naver.com/apps/")
        news_layout.addRow(naver_info_label)
        
        news_group.setLayout(news_layout)
        layout.addWidget(news_group)
        
        # Google Gemini API 설정 그룹
        ai_group = QGroupBox("Google Gemini API")
        ai_layout = QFormLayout()
        
        self.google_api_key_edit = QLineEdit()
        self.google_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.google_api_key_edit.setPlaceholderText("Google AI Studio에서 발급받은 API Key")
        
        ai_layout.addRow("Google API Key:", self.google_api_key_edit)
        
        # 안내 라벨
        ai_info_label = QLabel("AI 블로그 생성을 위해 필요합니다\n발급: https://aistudio.google.com/app/apikey")
        ai_layout.addRow(ai_info_label)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        # 이미지 검색 API 설정 그룹 (선택사항)
        image_group = QGroupBox("이미지 검색 API (선택사항)")
        image_layout = QFormLayout()
        
        self.unsplash_key_edit = QLineEdit()
        self.unsplash_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.unsplash_key_edit.setPlaceholderText("Unsplash Access Key (선택사항)")
        
        self.pixabay_key_edit = QLineEdit()
        self.pixabay_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pixabay_key_edit.setPlaceholderText("Pixabay API Key (선택사항)")
        
        image_layout.addRow("Unsplash Access Key:", self.unsplash_key_edit)
        image_layout.addRow("Pixabay API Key:", self.pixabay_key_edit)
        
        # 이미지 API 안내 라벨
        image_info_label = QLabel(
            "이미지 API는 선택사항입니다. 설정하지 않아도 블로그 생성 가능합니다\n"
            "Unsplash: https://unsplash.com/developers\n"
            "Pixabay: https://pixabay.com/api/docs/"
        )
        image_layout.addRow(image_info_label)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("설정 저장")
        save_button.clicked.connect(self.save_settings)
        
        cancel_button = QPushButton("취소")
        cancel_button.clicked.connect(self.cancel_settings)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def set_form_data(self, settings_data):
        """폼에 데이터 설정"""
        self.naver_client_id_edit.setText(settings_data.get('naver_client_id', ''))
        self.naver_client_secret_edit.setText(settings_data.get('naver_client_secret', ''))
        self.google_api_key_edit.setText(settings_data.get('google_api_key', ''))
        
        # 이미지 API 키 설정
        self.unsplash_key_edit.setText(settings_data.get('unsplash_access_key', ''))
        self.pixabay_key_edit.setText(settings_data.get('pixabay_api_key', ''))
        
    def get_form_data(self):
        """폼에서 데이터 수집"""
        return {
            'naver_client_id': self.naver_client_id_edit.text().strip(),
            'naver_client_secret': self.naver_client_secret_edit.text().strip(),
            'google_api_key': self.google_api_key_edit.text().strip(),
            
            # 이미지 API 키
            'unsplash_access_key': self.unsplash_key_edit.text().strip(),
            'pixabay_api_key': self.pixabay_key_edit.text().strip()
        }
        
    def save_settings(self):
        """설정 저장 (기본 메시지박스)"""
        settings_data = self.get_form_data()
        
        # 필수 API 키 검증
        required_keys = ['naver_client_id', 'naver_client_secret', 'google_api_key']
        missing_keys = [key for key in required_keys if not settings_data[key]]
        
        if missing_keys:
            missing_names = {
                'naver_client_id': 'Naver Client ID',
                'naver_client_secret': 'Naver Client Secret',
                'google_api_key': 'Google API Key'
            }
            
            missing_display = [missing_names[key] for key in missing_keys]
            
            # 기본 경고 메시지박스
            QMessageBox.warning(
                self,
                "필수 설정 누락",
                f"다음 필수 설정이 누락되었습니다:\n\n• {', '.join(missing_display)}\n\n" +
                "이미지 API 키는 선택사항이지만, 위 키들은 블로그 생성에 필수입니다."
            )
            return
            
        # 이미지 API 키 경고 (선택사항)
        if not settings_data['unsplash_access_key'] and not settings_data['pixabay_api_key']:
            reply = QMessageBox.question(
                self,
                "이미지 API 키 없음",
                "이미지 API 키가 설정되지 않았습니다.\n" +
                "블로그에 이미지가 포함되지 않을 수 있습니다.\n\n" +
                "계속 저장하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # 성공 메시지
        QMessageBox.information(
            self,
            "설정 저장 완료",
            "API 키 설정이 성공적으로 저장되었습니다."
        )
        
        self.settings_saved.emit(settings_data)
        
    def cancel_settings(self):
        """설정 취소"""
        self.settings_cancelled.emit()
