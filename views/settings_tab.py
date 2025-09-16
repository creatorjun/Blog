from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QGroupBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtCore import QUrl

class SettingsTab(QWidget):
    settings_saved = pyqtSignal(dict)
    settings_cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        title_label = QLabel("API 키 설정")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)

        news_group = QGroupBox("네이버 뉴스 API")
        news_layout = QFormLayout()
        self.naver_client_id_edit = QLineEdit()
        self.naver_client_id_edit.setPlaceholderText("네이버 Developer Console에서 발급받은 Client ID")
        self.naver_client_secret_edit = QLineEdit()
        self.naver_client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.naver_client_secret_edit.setPlaceholderText("네이버 Developer Console에서 발급받은 Client Secret")
        news_layout.addRow("Naver Client ID:", self.naver_client_id_edit)
        news_layout.addRow("Naver Client Secret:", self.naver_client_secret_edit)
        
        naver_url = "https://developers.naver.com/apps/"
        naver_info_label = QLabel(f'네이버 뉴스 검색을 위해 필요합니다<br>발급: <a href="{naver_url}">{naver_url}</a>')
        naver_info_label.setFont(QFont("Arial", 9))
        naver_info_label.setOpenExternalLinks(True)
        news_layout.addRow(naver_info_label)
        
        news_group.setLayout(news_layout)
        layout.addWidget(news_group)

        ai_group = QGroupBox("Google Gemini API")
        ai_layout = QFormLayout()
        self.google_api_key_edit = QLineEdit()
        self.google_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.google_api_key_edit.setPlaceholderText("Google AI Studio에서 발급받은 API Key")
        ai_layout.addRow("Google API Key:", self.google_api_key_edit)
        
        ai_url = "https://aistudio.google.com/app/apikey"
        ai_info_label = QLabel(f'AI 블로그 생성을 위해 필요합니다<br>발급: <a href="{ai_url}">{ai_url}</a>')
        ai_info_label.setFont(QFont("Arial", 9))
        ai_info_label.setOpenExternalLinks(True)
        ai_layout.addRow(ai_info_label)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

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
        
        unsplash_url = "https://unsplash.com/developers"
        pixabay_url = "https://pixabay.com/api/docs/"
        image_info_label = QLabel(
            '이미지 API는 선택사항입니다. 설정하지 않아도 블로그 생성 가능합니다<br>'
            f'Unsplash: <a href="{unsplash_url}">{unsplash_url}</a><br>'
            f'Pixabay: <a href="{pixabay_url}">{pixabay_url}</a>'
        )
        image_info_label.setFont(QFont("Arial", 9))
        image_info_label.setOpenExternalLinks(True)
        image_layout.addRow(image_info_label)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)

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
        self.naver_client_id_edit.setText(settings_data.get('naver_client_id', ''))
        self.naver_client_secret_edit.setText(settings_data.get('naver_client_secret', ''))
        self.google_api_key_edit.setText(settings_data.get('google_api_key', ''))
        self.unsplash_key_edit.setText(settings_data.get('unsplash_access_key', ''))
        self.pixabay_key_edit.setText(settings_data.get('pixabay_api_key', ''))

    def get_form_data(self):
        return {
            'naver_client_id': self.naver_client_id_edit.text().strip(),
            'naver_client_secret': self.naver_client_secret_edit.text().strip(),
            'google_api_key': self.google_api_key_edit.text().strip(),
            'unsplash_access_key': self.unsplash_key_edit.text().strip(),
            'pixabay_api_key': self.pixabay_key_edit.text().strip()
        }

    def save_settings(self):
        settings_data = self.get_form_data()
        required_keys = ['naver_client_id', 'naver_client_secret', 'google_api_key']
        missing_keys = [key for key in required_keys if not settings_data[key]]

        if missing_keys:
            missing_names = {
                'naver_client_id': 'Naver Client ID',
                'naver_client_secret': 'Naver Client Secret',
                'google_api_key': 'Google API Key'
            }
            missing_display = [missing_names[key] for key in missing_keys]
            QMessageBox.warning(
                self,
                "필수 설정 누락",
                f"다음 필수 설정이 누락되었습니다:\n\n• {', '.join(missing_display)}\n\n" +
                "이미지 API 키는 선택사항이지만, 위 키들은 블로그 생성에 필수입니다."
            )
            return

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

        QMessageBox.information(
            self,
            "설정 저장 완료",
            "API 키 설정이 성공적으로 저장되었습니다."
        )
        self.settings_saved.emit(settings_data)

    def cancel_settings(self):
        self.settings_cancelled.emit()