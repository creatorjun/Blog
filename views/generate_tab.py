# views/generate_tab.py
import os
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, 
    QPushButton, QLabel, QTextEdit, QMessageBox, QFileDialog,
    QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSignal as Signal
from PyQt6.QtGui import QFont, QPixmap
from utils.image_downloader import ImageDownloader

class BlogGenerationThread(QThread):
    """블로그 생성 전용 스레드"""
    
    finished = Signal(dict, dict)  # blog_data, local_image_paths
    error = Signal(str)
    progress_update = Signal(str)
    
    def __init__(self, category, keyword, api_settings):
        super().__init__()
        self.category = category
        self.keyword = keyword
        self.api_settings = api_settings
        self.image_downloader = ImageDownloader()
        self.local_image_paths = {}
    
    def run(self):
        try:
            self.progress_update.emit("뉴스 검색 중...")
            
            # 여기서 실제 블로그 생성 로직 호출
            # (기존의 news search + AI generation + image search 로직)
            
            # 임시 데모 데이터 (실제 구현 시 대체)
            blog_data = {
                'title': f'{self.category} 관련 블로그 포스팅',
                'body': f'이것은 {self.keyword}에 대한 블로그 내용입니다.\n\n[이미지_1]\n\n더 많은 내용이 여기에 들어갑니다.\n\n[이미지_2]',
                'conclusion': '결론적으로 매우 유용한 정보였습니다.',
                'tags': ['AI', '블로그', '자동생성'],
                'images': {
                    '이미지_1': [{'url': 'https://images.unsplash.com/photo-1532679473578-37c3d5c525a7', 'description': '예시 이미지', 'photographer': 'Unknown', 'source': 'Unsplash'}],
                    '이미지_2': [{'url': 'https://images.unsplash.com/photo-1629103619880-1c0678a347b5', 'description': '예시 이미지 2', 'photographer': 'Unknown', 'source': 'Unsplash'}]
                },
                'generated_at': '2025-09-17 07:30:00',
                'generator': 'Gemini AI'
            }
            
            self.progress_update.emit("이미지 다운로드 중...")
            
            # 이미지 다운로드
            images_data = blog_data.get('images', {})
            for marker_key, image_list in images_data.items():
                if image_list:
                    img_url = image_list[0].get('url', '')
                    if img_url:
                        local_path = self.image_downloader.download_image(
                            img_url, filename_prefix=marker_key.replace('_', '')
                        )
                        if local_path:
                            self.local_image_paths[marker_key] = local_path
            
            self.progress_update.emit("생성 완료!")
            self.finished.emit(blog_data, self.local_image_paths)
            
        except Exception as e:
            self.error.emit(str(e))

class GenerateTab(QWidget):
    """생성 탭 - 통합 미리보기 포함"""
    
    # 시그널 정의
    settings_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.blog_data = None
        self.local_image_paths = {}
        self.markdown_content = ""
        self.html_content = ""
        self.generation_thread = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # 제목
        title_label = QLabel("AI 블로그 포스팅 생성")
        title_label.setFont(QFont("", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 검색 설정 그룹
        search_layout = QVBoxLayout()
        
        # 카테고리 선택
        category_layout = QHBoxLayout()
        category_label = QLabel("카테고리:")
        category_label.setFixedWidth(80)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "정치", "경제", "사회", "생활/문화", "세계", "IT/과학", "오피니언"
        ])
        self.category_combo.setCurrentIndex(5)  # IT/과학 기본 선택
        
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        category_layout.addStretch()
        
        search_layout.addLayout(category_layout)
        
        # 키워드 입력
        keyword_layout = QHBoxLayout()
        keyword_label = QLabel("키워드:")
        keyword_label.setFixedWidth(80)
        
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("추가 키워드 입력 (선택사항)")
        
        keyword_layout.addWidget(keyword_label)
        keyword_layout.addWidget(self.keyword_edit)
        
        search_layout.addLayout(keyword_layout)
        layout.addLayout(search_layout)
        
        # 생성 시작 버튼
        self.generate_button = QPushButton("🚀 생성 시작")
        self.generate_button.setFont(QFont("", 12, QFont.Weight.Bold))
        self.generate_button.clicked.connect(self.start_generation)
        layout.addWidget(self.generate_button)
        
        # 진행률 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 무한 로딩
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # 🔧 복사 & 저장 버튼들 (처음엔 비활성화)
        button_layout = QHBoxLayout()
        
        self.copy_text_button = QPushButton("📝 본문 복사")
        self.copy_text_button.setEnabled(False)
        self.copy_text_button.clicked.connect(self.copy_text_only)
        
        self.copy_image_button = QPushButton("🖼️ 이미지 복사")
        self.copy_image_button.setEnabled(False)
        self.copy_image_button.clicked.connect(self.copy_first_image)
        
        self.save_html_button = QPushButton("💾 HTML 저장")
        self.save_html_button.setEnabled(False)
        self.save_html_button.clicked.connect(self.save_to_html)
        
        button_layout.addWidget(self.copy_text_button)
        button_layout.addWidget(self.copy_image_button)
        button_layout.addWidget(self.save_html_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 🔧 미리보기 영역 (시작 버튼 아래)
        preview_label = QLabel("📖 미리보기")
        preview_label.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMinimumHeight(400)
        self.preview_text.setPlaceholderText("생성 버튼을 클릭하면 여기에 미리보기가 표시됩니다.")
        layout.addWidget(self.preview_text)
        
        self.setLayout(layout)
        
    def start_generation(self):
        """블로그 생성 시작"""
        category = self.category_combo.currentText()
        keyword = self.keyword_edit.text().strip()
        
        # API 설정 확인 (실제 구현 시)
        api_settings = {}  # 실제로는 settings_manager에서 가져와야 함
        
        # UI 상태 변경
        self.generate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_label.setText("생성 준비 중...")
        
        # 버튼들 비활성화
        self.copy_text_button.setEnabled(False)
        self.copy_image_button.setEnabled(False)
        self.save_html_button.setEnabled(False)
        
        # 미리보기 초기화
        self.preview_text.clear()
        self.preview_text.setPlaceholderText("생성 중...")
        
        # 생성 스레드 시작
        self.generation_thread = BlogGenerationThread(category, keyword, api_settings)
        self.generation_thread.finished.connect(self.on_generation_finished)
        self.generation_thread.error.connect(self.on_generation_error)
        self.generation_thread.progress_update.connect(self.on_progress_update)
        self.generation_thread.start()
        
        # 타임아웃 설정 (3분)
        QTimer.singleShot(180000, self.on_timeout)
        
    def on_progress_update(self, message):
        """진행 상황 업데이트"""
        self.progress_label.setText(message)
        
    def on_generation_finished(self, blog_data, local_image_paths):
        """생성 완료 처리"""
        self.blog_data = blog_data
        self.local_image_paths = local_image_paths
        
        # HTML 및 마크다운 생성
        self.generate_contents()
        
        # UI 상태 복원
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # 버튼들 활성화
        self.copy_text_button.setEnabled(True)
        self.copy_image_button.setEnabled(bool(self.local_image_paths))
        self.save_html_button.setEnabled(True)
        
        # 미리보기 표시
        self.preview_text.setHtml(self.html_content)
        
        # 완료 메시지
        QMessageBox.information(
            self,
            "생성 완료! 🎉",
            f"블로그 포스팅이 성공적으로 생성되었습니다!\n\n" +
            f"📝 제목: {blog_data.get('title', '')}\n" +
            f"🖼️ 이미지: {len(self.local_image_paths)}개\n" +
            f"📊 글자수: {len(self.markdown_content)}자"
        )
        
    def on_generation_error(self, error_msg):
        """생성 오류 처리"""
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        QMessageBox.critical(
            self,
            "생성 실패",
            f"블로그 생성 중 오류가 발생했습니다:\n\n{error_msg}"
        )
        
    def on_timeout(self):
        """타임아웃 처리"""
        if self.generation_thread and self.generation_thread.isRunning():
            self.generation_thread.terminate()
            
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        QMessageBox.warning(
            self,
            "시간 초과",
            "생성 시간이 3분을 초과했습니다.\n다시 시도해 주세요."
        )
        
    def generate_contents(self):
        """HTML 및 마크다운 콘텐츠 생성"""
        if not self.blog_data:
            return
            
        title = self.blog_data.get('title', '')
        body = self.blog_data.get('body', '')
        conclusion = self.blog_data.get('conclusion', '')
        tags = self.blog_data.get('tags', [])
        
        # 🔧 마크다운 생성 (이미지 URL 포함)
        markdown_parts = [f'# {title}\n']
        
        # 이미지 마커를 마크다운 링크로 교체
        markdown_body = body
        images_data = self.blog_data.get('images', {})
        for marker_key, image_list in images_data.items():
            marker = f'[{marker_key}]'
            if marker in markdown_body and image_list:
                img_url = image_list[0].get('url', '')
                if img_url:
                    markdown_body = markdown_body.replace(marker, f'![이미지]({img_url})')
                else:
                    markdown_body = markdown_body.replace(marker, '')
        
        markdown_parts.append(markdown_body)
        
        if conclusion:
            markdown_parts.append(f'\n## 💭 결론\n{conclusion}')
            
        if tags:
            markdown_parts.append(f'\n## 🏷️ 태그\n{" ".join(tags)}')
            
        markdown_parts.append(f'\n\n---\n*Generated by {self.blog_data.get("generator", "AI")} at {self.blog_data.get("generated_at", "")}*')
        
        self.markdown_content = '\n'.join(markdown_parts)
        
        # 🔧 HTML 생성 (로컬 이미지 포함)
        html_body = body
        for marker_key, local_path in self.local_image_paths.items():
            marker = f'[{marker_key}]'
            if marker in html_body:
                file_url = f'file:///{os.path.abspath(local_path).replace(os.sep, "/")}'
                img_tag = f'<div style="text-align: center; margin: 20px 0;"><img src="{file_url}" style="max-width: 100%; height: auto; border-radius: 8px;"></div>'
                html_body = html_body.replace(marker, img_tag)
        
        # 남은 마커 제거
        html_body = re.sub(r'\[이미지_\d+\]', '', html_body)
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<meta charset="utf-8">',
            '<style>',
            'body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; color: #333; }',
            'h1 { color: #0969da; border-bottom: 2px solid #0969da; padding-bottom: 10px; }',
            'h2 { color: #333; margin-top: 30px; }',
            '.conclusion { background-color: #e8f4fd; padding: 15px; border-left: 4px solid #2196f3; margin: 20px 0; }',
            '.tags { background-color: #f5f5f5; padding: 10px; border-radius: 4px; }',
            '.tag { background-color: #2196f3; color: white; padding: 4px 8px; margin: 2px; border-radius: 12px; font-size: 12px; }',
            '</style>',
            '</head>',
            '<body>',
            f'<h1>{title}</h1>',
            f'<div>{html_body.replace(chr(10), "<br>")}</div>',
        ]
        
        if conclusion:
            html_parts.append(f'<div class="conclusion"><h2>💭 결론</h2><p>{conclusion}</p></div>')
            
        if tags:
            tag_html = ''.join([f'<span class="tag">{tag}</span>' for tag in tags])
            html_parts.append(f'<div class="tags"><h2>🏷️ 태그</h2>{tag_html}</div>')
            
        html_parts.extend(['</body>', '</html>'])
        
        self.html_content = '\n'.join(html_parts)
        
    def copy_text_only(self):
        """📝 본문만 클립보드에 복사"""
        from PyQt6.QtWidgets import QApplication
        
        if not self.markdown_content:
            QMessageBox.warning(self, "복사 실패", "복사할 본문이 없습니다.")
            return
            
        clipboard = QApplication.clipboard()
        clipboard.setText(self.markdown_content)
        
        QMessageBox.information(
            self,
            "본문 복사 완료! 📝",
            "마크다운 형태의 본문이 클립보드에 복사되었습니다.\n\n" +
            "✅ 제목, 본문, 결론, 태그 포함\n" +
            "✅ 이미지는 ![이미지](URL) 링크로 포함\n" +
            "✅ 모든 블로그 플랫폼에서 붙여넣기 가능\n\n" +
            "이제 Ctrl+V로 붙여넣으세요!"
        )
        
    def copy_first_image(self):
        """🖼️ 첫 번째 이미지만 클립보드에 복사"""
        from PyQt6.QtWidgets import QApplication
        
        if not self.local_image_paths:
            QMessageBox.warning(self, "복사 실패", "복사할 이미지가 없습니다.")
            return
            
        # 첫 번째 이미지 가져오기
        first_image_path = next(iter(self.local_image_paths.values()))
        
        if not os.path.exists(first_image_path):
            QMessageBox.warning(self, "복사 실패", "이미지 파일을 찾을 수 없습니다.")
            return
            
        try:
            # 이미지를 QPixmap으로 로드하고 클립보드에 복사
            pixmap = QPixmap(first_image_path)
            if pixmap.isNull():
                QMessageBox.warning(self, "복사 실패", "이미지를 로드할 수 없습니다.")
                return
                
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(pixmap)
            
            QMessageBox.information(
                self,
                "이미지 복사 완료! 🖼️",
                f"첫 번째 이미지가 클립보드에 복사되었습니다.\n\n" +
                f"📂 경로: {os.path.basename(first_image_path)}\n\n" +
                "이제 Ctrl+V로 붙여넣으세요!"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "복사 실패", f"이미지 복사 중 오류가 발생했습니다:\n\n{str(e)}")
            
    def save_to_html(self):
        """💾 HTML 파일로 저장"""
        if not self.html_content:
            QMessageBox.warning(self, "저장 실패", "저장할 HTML 콘텐츠가 없습니다.")
            return
            
        timestamp = self.blog_data.get('generated_at', '').replace(':', '').replace(' ', '_')
        default_filename = f"blog_post_{timestamp}.html"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "블로그 포스팅 HTML 저장", 
            default_filename, 
            "HTML 파일 (*.html)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.html_content)
                    
                QMessageBox.information(
                    self,
                    "HTML 저장 완료! 💾",
                    f"HTML 파일이 성공적으로 저장되었습니다.\n\n" +
                    f"📂 경로: {file_path}\n\n" +
                    "브라우저에서 열어볼 수 있습니다!"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "저장 실패", f"파일 저장 중 오류가 발생했습니다:\n\n{str(e)}")
    
    def set_api_settings(self, settings_data):
        """API 설정 업데이트"""
        # 실제 구현 시 settings_manager와 연동
        pass
        
    def get_last_search_settings(self):
        """마지막 검색 설정 반환"""
        return {
            'category_index': self.category_combo.currentIndex(),
            'keyword': self.keyword_edit.text()
        }
        
    def set_last_search_settings(self, settings):
        """마지막 검색 설정 적용"""
        self.category_combo.setCurrentIndex(settings.get('category_index', 5))
        self.keyword_edit.setText(settings.get('keyword', ''))
