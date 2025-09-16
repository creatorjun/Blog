# views/blog_result_dialog.py
import json
import re
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
    QPushButton, QTabWidget, QWidget, QProgressBar, QMessageBox,
    QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QMimeData, QUrl
from PyQt6.QtGui import QFont, QPixmap
from utils.image_downloader import ImageDownloader

class ImageProcessingThread(QThread):
    """이미지 처리 전용 스레드"""
    
    finished = pyqtSignal(str, str, dict)  # HTML 콘텐츠, 마크다운 콘텐츠, 이미지 경로들
    error = pyqtSignal(str)                # 오류 메시지
    
    def __init__(self, blog_data, image_downloader):
        super().__init__()
        self.blog_data = blog_data
        self.image_downloader = image_downloader
        self.local_image_paths = {}  # 이미지 마커 → 로컬 경로 매핑
    
    def run(self):
        try:
            display_html = self._process_content_for_display()
            markdown_content = self._process_content_for_markdown()
            self.finished.emit(display_html, markdown_content, self.local_image_paths)
        except Exception as e:
            self.error.emit(str(e))
    
    def _get_content_as_string(self):
        """콘텐츠를 안전하게 문자열로 변환"""
        content = self.blog_data.get('body', '') or self.blog_data.get('content', '')
        
        if isinstance(content, list):
            content = '\n'.join(str(item) for item in content)
        elif not isinstance(content, str):
            content = str(content)
        
        return content
    
    def _process_content_for_display(self):
        """화면 표시용 HTML 생성 (로컬 이미지 경로 사용)"""
        try:
            content = self._get_content_as_string()
            title = self.blog_data.get('title', '')
            conclusion = self.blog_data.get('conclusion', '')
            tags = self.blog_data.get('tags', [])
            
            # 이미지 마커 처리
            images_data = self.blog_data.get('images', {})
            image_markers = re.findall(r'\[이미지_\d+\]', content)
            
            for marker in image_markers:
                marker_key = marker.strip('[]')
                
                if marker_key in images_data and images_data[marker_key]:
                    img_data = images_data[marker_key][0]
                    img_url = img_data.get('url', '')
                    
                    if img_url:
                        # 로컬에 다운로드
                        local_path = self.image_downloader.download_image(
                            img_url, filename_prefix=marker_key.replace('_', '')
                        )
                        
                        if local_path and os.path.exists(local_path):
                            file_url = self.image_downloader.get_file_url(local_path)
                            # 🔧 이미지 경로 저장 (클립보드 복사용)
                            self.local_image_paths[marker_key] = local_path
                            
                            img_tag = f'<div class="image-container"><img src="{file_url}" alt="이미지" class="blog-image"></div>'
                            content = content.replace(marker, img_tag)
                        else:
                            content = content.replace(marker, f'<p class="error-message">❌ 이미지를 불러올 수 없습니다</p>')
                    else:
                        content = content.replace(marker, '')
                else:
                    content = content.replace(marker, '')
            
            return self._build_display_html(title, content, conclusion, tags)
            
        except Exception as e:
            raise Exception(f"화면용 HTML 생성 오류: {str(e)}")
    
    def _process_content_for_markdown(self):
        """마크다운 클립보드용 콘텐츠 생성"""
        try:
            content = self._get_content_as_string()
            title = self.blog_data.get('title', '')
            conclusion = self.blog_data.get('conclusion', '')
            tags = self.blog_data.get('tags', [])
            
            # 이미지 마커를 마크다운 이미지 링크로 교체
            images_data = self.blog_data.get('images', {})
            image_markers = re.findall(r'\[이미지_\d+\]', content)
            
            for marker in image_markers:
                marker_key = marker.strip('[]')
                
                if marker_key in images_data and images_data[marker_key]:
                    img_data = images_data[marker_key][0]
                    img_url = img_data.get('url', '')
                    
                    if img_url:
                        md_img = f'![이미지]({img_url})\n'
                        content = content.replace(marker, md_img)
                    else:
                        content = content.replace(marker, '')
                else:
                    content = content.replace(marker, '')
            
            # 마크다운 형태로 전체 콘텐츠 구성
            markdown_parts = []
            markdown_parts.append(f'# {title}\n')
            markdown_parts.append(content)
            
            if conclusion:
                markdown_parts.append('\n---\n## 💭 결론\n')
                markdown_parts.append(conclusion)
            
            if tags:
                markdown_parts.append('\n---\n## 🏷️ 태그\n')
                markdown_parts.append(' '.join(tags))
            
            generator = self.blog_data.get('generator', 'AI')
            generated_at = self.blog_data.get('generated_at', '')
            markdown_parts.append(f'\n\n---\n*Generated by {generator} at {generated_at}*')
            
            return '\n'.join(markdown_parts)
            
        except Exception as e:
            raise Exception(f"마크다운 생성 오류: {str(e)}")
    
    def _build_display_html(self, title, content, conclusion, tags):
        """화면 표시용 HTML 문서 구성 (PyQt 호환 CSS)"""
        css_styles = """
        body { 
            font-family: Arial, sans-serif;
            font-size: 16px;
            line-height: 1.7; 
            max-width: 780px;
            max-height: 600px; 
            margin: 0 auto; 
            padding: 30px;
            color: #1f2328;
            background-color: #ffffff;
        }
        h1 { 
            color: #0969da; 
            font-size: 28px;
            font-weight: bold;
            border-bottom: 3px solid #0969da; 
            padding-bottom: 15px;
            margin-bottom: 35px;
        }
        h2 { 
            color: #1f2328; 
            font-size: 22px;
            font-weight: bold;
            margin-top: 40px; 
            margin-bottom: 20px;
            border-left: 5px solid #0969da;
            padding-left: 15px;
            background-color: #f6f8fa;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        h3 { 
            color: #656d76; 
            font-size: 18px;
            font-weight: bold;
            margin-top: 30px; 
            margin-bottom: 15px;
        }
        p { 
            margin-bottom: 18px; 
            text-align: justify;
            color: #24292f;
        }
        .image-container {
            text-align: center; 
            margin: 35px 0;
            padding: 20px;
            background-color: #f6f8fa;
            border-radius: 10px;
            border: 1px solid #d1d9e0;
        }
        .blog-image {
            max-width: 100%; 
            height: auto; 
            border-radius: 8px; 
            border: 1px solid #d1d9e0;
        }
        .conclusion { 
            background-color: #dbeafe;
            padding: 25px; 
            border-left: 6px solid #2563eb; 
            margin: 40px 0;
            border-radius: 8px;
        }
        .conclusion h3 {
            color: #1e40af;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 18px;
        }
        .conclusion p {
            color: #1e3a8a;
            margin-bottom: 0;
        }
        .tags { 
            background-color: #f6f8fa;
            padding: 22px; 
            border-radius: 8px; 
            margin-top: 40px;
            border: 1px solid #d1d9e0;
        }
        .tags h3 {
            color: #24292f;
            margin-top: 0;
            margin-bottom: 18px;
            font-size: 16px;
        }
        .tag { 
            display: inline-block; 
            background-color: #0969da;
            color: #ffffff; 
            padding: 8px 16px; 
            margin: 4px 8px 4px 0; 
            border-radius: 20px; 
            font-size: 13px;
            font-weight: bold;
        }
        .error-message {
            color: #d1242f;
            text-align: center;
            font-style: italic;
            background-color: #fff8f8;
            border: 2px solid #fecaca;
            padding: 20px;
            border-radius: 8px;
            margin: 25px 0;
        }
        """
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'<style>{css_styles}</style>',
            '</head>',
            '<body>',
            f'<h1>{title}</h1>',
            self._markdown_to_html(content),
            self._generate_conclusion_html(conclusion) if conclusion else '',
            self._generate_tags_html(tags) if tags else '',
            '</body>',
            '</html>'
        ]
        
        return '\n'.join(html_parts)
    
    def _markdown_to_html(self, text):
        """마크다운을 HTML로 변환"""
        if not text:
            return ""
        
        # 헤딩 변환
        text = re.sub(r'^### (.*)', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*)', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.*)', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        
        # 줄바꿈 처리
        text = text.replace('\\n\\n', '</p><p>')
        text = text.replace('\\n', '<br>')
        
        # 문단 처리
        if text and not text.startswith('<'):
            text = f'<p>{text}</p>'
        
        text = text.replace('<p></p>', '')
        return text
    
    def _generate_conclusion_html(self, conclusion):
        """결론 HTML 생성"""
        if not conclusion:
            return ""
        return f'<div class="conclusion"><h3>💭 결론</h3><p>{conclusion}</p></div>'
    
    def _generate_tags_html(self, tags):
        """태그 HTML 생성"""
        if not tags:
            return ""
        
        tag_elements = []
        for tag in tags:
            tag_elements.append(f'<span class="tag">{tag}</span>')
        
        tags_html = ''.join(tag_elements)
        return f'<div class="tags"><h3>🏷️ 태그</h3>{tags_html}</div>'

class BlogResultDialog(QDialog):
    """생성된 블로그 포스팅 결과 표시 다이얼로그 (이미지 포함 복사 + 다크 모드)"""
    
    def __init__(self, blog_data, parent=None):
        super().__init__(parent)
        self.blog_data = blog_data
        self.image_downloader = ImageDownloader()
        self.display_content = None
        self.markdown_content = None
        self.local_image_paths = {}  # 🔧 로컬 이미지 경로 저장
        self.processing_thread = None
        
        self.timeout = 3 * 60 * 1000
        
        self.setup_ui()
        self.start_processing()
    
    def _get_content_as_string(self):
        """콘텐츠를 안전하게 문자열로 변환"""
        content = self.blog_data.get('body', '') or self.blog_data.get('content', '')
        
        if isinstance(content, list):
            content = '\n'.join(str(item) for item in content)
        elif not isinstance(content, str):
            content = str(content)
        
        return content
        
    def setup_ui(self):
        """UI 구성 (다크 모드 적용)"""
        self.setWindowTitle("🤖 AI 블로그 포스팅 생성 결과")
        self.resize(1100, 850)
        
        # 🔧 다크 모드 다이얼로그 스타일
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: #e0e0e0;
                font-family: Arial, sans-serif;
            }
        """)
        
        self.layout = QVBoxLayout()
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # 제목 (다크 모드 스타일)
        title_label = QLabel(f"📝 {self.blog_data.get('title', '제목 없음')}")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #4a9eff; 
                background-color: #2a2a2a;
                padding: 20px; 
                border-radius: 8px;
                border: 2px solid #404040;
                margin-bottom: 15px;
                font-weight: bold;
            }
        """)
        title_label.setWordWrap(True)
        self.layout.addWidget(title_label)
        
        # 로딩 위젯 (다크 모드)
        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout()
        
        self.loading_label = QLabel("🔄 이미지를 다운로드하고 클립보드 복사를 준비하고 있습니다...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setFont(QFont("Arial", 13))
        self.loading_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0; 
                background-color: #2a2a2a;
                padding: 25px;
                border-radius: 8px;
                border: 1px solid #404040;
                margin: 20px 0;
            }
        """)
        loading_layout.addWidget(self.loading_label)
        
        # 무한 프로그레스바 (다크 모드)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: #404040;
                margin: 10px 20px;
            }
            QProgressBar::chunk {
                background-color: #4a9eff;
                border-radius: 6px;
            }
        """)
        loading_layout.addWidget(self.progress_bar)
        
        # 타임아웃 안내
        timeout_label = QLabel("⏱️ 최대 3분 소요될 수 있습니다. 이미지와 클립보드 데이터 준비 중...")
        timeout_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timeout_label.setStyleSheet("""
            QLabel {
                color: #999999; 
                font-size: 12px; 
                margin: 10px 0 20px 0;
                font-style: italic;
            }
        """)
        loading_layout.addWidget(timeout_label)
        
        loading_layout.addStretch()
        self.loading_widget.setLayout(loading_layout)
        self.layout.addWidget(self.loading_widget)
        
        # 실제 콘텐츠 영역 (처음에는 숨김)
        self.content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # 탭 위젯 (다크 모드)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                border-radius: 6px;
                background-color: #2a2a2a;
            }
            QTabBar::tab {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #404040;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #2a2a2a;
                color: #4a9eff;
                border-bottom-color: #2a2a2a;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #333333;
                color: #4a9eff;
            }
        """)
        
        # 미리보기 탭
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 15px;
                font-size: 14px;
            }
        """)
        self.tabs.addTab(self.preview_text, "📖 미리보기")
        
        # JSON 탭
        json_tab = self.create_json_tab()
        self.tabs.addTab(json_tab, "📄 JSON 원본")
        
        content_layout.addWidget(self.tabs)
        
        # 버튼들 (다크 모드)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        copy_button = QPushButton("📋 이미지 포함 복사")
        copy_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        copy_button.clicked.connect(self.copy_with_images_to_clipboard)
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: #ffffff;
                border: none;
                padding: 12px 20px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 160px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        
        save_html_button = QPushButton("💾 HTML 저장")
        save_html_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        save_html_button.clicked.connect(self.save_to_html)
        save_html_button.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: #ffffff;
                border: none;
                padding: 12px 20px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #3d8bdb;
            }
            QPushButton:pressed {
                background-color: #357abd;
            }
        """)
        
        close_button = QPushButton("❌ 닫기")
        close_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: #ffffff;
                border: none;
                padding: 12px 20px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        
        button_layout.addWidget(copy_button)
        button_layout.addWidget(save_html_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        content_layout.addLayout(button_layout)
        self.content_widget.setLayout(content_layout)
        self.content_widget.hide()  # 처음에는 숨김
        
        self.layout.addWidget(self.content_widget)
        self.setLayout(self.layout)
        
        # 타임아웃 타이머 설정
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.on_timeout)
    
    def start_processing(self):
        """이미지 처리 시작"""
        self.loading_widget.show()
        self.content_widget.hide()
        
        # 타임아웃 타이머 시작
        self.timeout_timer.start(self.timeout)
        
        # 이미지 처리 스레드 시작
        self.processing_thread = ImageProcessingThread(self.blog_data, self.image_downloader)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.error.connect(self.on_processing_error)
        self.processing_thread.start()
    
    def on_processing_finished(self, html_content, markdown_content, image_paths):
        """이미지 처리 완료"""
        self.timeout_timer.stop()
        
        self.display_content = html_content
        self.markdown_content = markdown_content
        self.local_image_paths = image_paths  # 🔧 이미지 경로 저장
        self.preview_text.setHtml(html_content)
        
        # UI 전환
        self.loading_widget.hide()
        self.content_widget.show()
        
        print("✅ 이미지 처리 완료 - 클립보드 복사 준비됨")
    
    def on_processing_error(self, error_msg):
        """이미지 처리 오류"""
        self.timeout_timer.stop()
        
        # 기본 마크다운 콘텐츠 생성
        self.markdown_content = self._create_basic_markdown()
        basic_html = self._create_basic_html()
        
        self.preview_text.setHtml(basic_html)
        
        self.loading_widget.hide()
        self.content_widget.show()
        
        # 🔧 다크 모드 메시지박스
        msg = QMessageBox(self)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            QMessageBox QPushButton {
                background-color: #4a9eff;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #3d8bdb;
            }
        """)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("처리 중 오류 발생")
        msg.setText(f"이미지 처리 중 오류가 발생했습니다:\n\n{error_msg}\n\n기본 콘텐츠로 표시됩니다.")
        msg.exec()
        
        print(f"❌ 이미지 처리 오류: {error_msg}")
    
    def on_timeout(self):
        """3분 타임아웃 처리"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.processing_thread.wait(1000)
        
        # 기본 콘텐츠로 처리
        self.markdown_content = self._create_basic_markdown()
        timeout_html = """
        <div style="text-align: center; padding: 50px; color: #e67e22;">
            <h2>⏰ 처리 시간 초과</h2>
            <p>이미지 처리에 3분이 초과되었습니다.</p>
            <p>기본 콘텐츠로 표시됩니다. 마크다운 복사는 정상 작동합니다.</p>
        </div>
        """
        
        self.preview_text.setHtml(timeout_html)
        
        self.loading_widget.hide()
        self.content_widget.show()
        
        print("⏰ 3분 타임아웃 - 기본 콘텐츠로 처리")
    
    def copy_with_images_to_clipboard(self):
        """🔧 이미지 포함 클립보드 복사 (HTML + 이미지 데이터)"""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QMimeData, QUrl
        from PyQt6.QtGui import QPixmap
        
        clipboard = QApplication.clipboard()
        mime_data = QMimeData()
        
        if self.markdown_content:
            # 1. 텍스트 데이터
            mime_data.setText(self.markdown_content)
            
            # 2. HTML 데이터 (로컬 이미지 경로 포함)
            html_with_local_images = self._create_clipboard_html()
            mime_data.setHtml(html_with_local_images)
            
            # 3. 이미지 파일들을 URL 리스트로 추가
            if self.local_image_paths:
                image_urls = []
                for image_path in self.local_image_paths.values():
                    if os.path.exists(image_path):
                        image_url = QUrl.fromLocalFile(os.path.abspath(image_path))
                        image_urls.append(image_url)
                
                if image_urls:
                    mime_data.setUrls(image_urls)
            
            # 클립보드에 복합 데이터 설정
            clipboard.setMimeData(mime_data)
            
            # 🔧 다크 모드 성공 메시지
            msg = QMessageBox(self)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #1a1a1a;
                    color: #e0e0e0;
                    min-width: 400px;
                }
                QMessageBox QPushButton {
                    background-color: #28a745;
                    color: #ffffff;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    min-width: 80px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #218838;
                }
            """)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("복사 완료! 📋")
            msg.setText(
                "이미지 포함 복사가 완료되었습니다! 🎉\n\n" +
                "✅ 마크다운 텍스트 포함\n" +
                "✅ HTML 형식 포함\n" +
                "✅ 로컬 이미지 파일들 포함\n\n" +
                f"📷 {len(self.local_image_paths)}개 이미지가 포함되었습니다.\n\n" +
                "이제 블로그 에디터나 워드 프로세서에\nCtrl+V로 붙여넣으세요!"
            )
            msg.exec()
        else:
            # 기본 마크다운 생성 후 복사
            self.markdown_content = self._create_basic_markdown()
            mime_data.setText(self.markdown_content)
            clipboard.setMimeData(mime_data)
            
            msg = QMessageBox(self)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #1a1a1a;
                    color: #e0e0e0;
                }
                QMessageBox QPushButton {
                    background-color: #28a745;
                    color: #ffffff;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
            """)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("복사 완료! 📋")
            msg.setText("기본 마크다운이 클립보드에 복사되었습니다.")
            msg.exec()
    
    def _create_clipboard_html(self):
        """클립보드용 HTML 생성 (로컬 이미지 경로 사용)"""
        title = self.blog_data.get('title', '')
        content = self._get_content_as_string()
        conclusion = self.blog_data.get('conclusion', '')
        tags = self.blog_data.get('tags', [])
        
        # 이미지 마커를 로컬 이미지로 교체
        for marker_key, local_path in self.local_image_paths.items():
            marker = f'[{marker_key}]'
            if marker in content:
                file_url = f'file:///{os.path.abspath(local_path).replace(os.sep, "/")}'
                img_html = f'<div style="text-align: center; margin: 20px 0;"><img src="{file_url}" alt="이미지" style="max-width: 100%; height: auto; border-radius: 8px;"></div>'
                content = content.replace(marker, img_html)
        
        # HTML 문서 생성
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 20px; }}
                h1 {{ color: #0969da; border-bottom: 2px solid #0969da; padding-bottom: 10px; }}
                h2 {{ color: #333; margin-top: 30px; }}
                img {{ display: block; margin: 20px auto; max-width: 100%; border-radius: 8px; }}
                .conclusion {{ background-color: #e8f4fd; padding: 15px; border-left: 4px solid #2196f3; margin: 20px 0; }}
                .tags {{ background-color: #f5f5f5; padding: 10px; border-radius: 4px; }}
                .tag {{ background-color: #2196f3; color: white; padding: 4px 8px; margin: 2px; border-radius: 12px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            {content.replace('\\n', '<br>')}
            {f'<div class="conclusion"><h3>💭 결론</h3><p>{conclusion}</p></div>' if conclusion else ''}
            {f'<div class="tags"><h3>🏷️ 태그</h3>{" ".join([f"<span class=\\'tag\\'>{tag}</span>" for tag in tags])}</div>' if tags else ''}
        </body>
        </html>
        '''
        
        return html
    
    def _create_basic_markdown(self):
        """기본 마크다운 콘텐츠 생성"""
        try:
            title = self.blog_data.get('title', '')
            content = self._get_content_as_string()
            conclusion = self.blog_data.get('conclusion', '')
            tags = self.blog_data.get('tags', [])
            images = self.blog_data.get('images', {})
            
            # 이미지 마커를 간단한 마크다운 이미지 링크로 교체
            image_markers = re.findall(r'\[이미지_\d+\]', content)
            for marker in image_markers:
                marker_key = marker.strip('[]')
                if marker_key in images and images[marker_key]:
                    img_data = images[marker_key][0]
                    img_url = img_data.get('url', '')
                    
                    if img_url:
                        md_img = f'![이미지]({img_url})\n'
                        content = content.replace(marker, md_img)
                    else:
                        content = content.replace(marker, '')
                else:
                    content = content.replace(marker, '')
            
            # 마크다운 조립
            markdown_parts = [f'# {title}\n']
            markdown_parts.append(content)
            
            if conclusion:
                markdown_parts.append('\n---\n## 💭 결론\n')
                markdown_parts.append(conclusion)
            
            if tags:
                markdown_parts.append('\n---\n## 🏷️ 태그\n')
                markdown_parts.append(' '.join(tags))
            
            generator = self.blog_data.get('generator', 'AI')
            generated_at = self.blog_data.get('generated_at', '')
            markdown_parts.append(f'\n\n---\n*Generated by {generator} at {generated_at}*')
            
            return '\n'.join(markdown_parts)
            
        except Exception as e:
            return f"# 오류 발생\n\n마크다운 생성 중 오류가 발생했습니다: {str(e)}"
    
    def _create_basic_html(self):
        """기본 HTML 생성 (이미지 없이)"""
        title = self.blog_data.get('title', '')
        content = self._get_content_as_string()
        
        try:
            content = re.sub(r'\[이미지_\d+\]', '', content)
        except TypeError as e:
            print(f"⚠️ re.sub 오류 방지: {e}")
            content = str(content)
            content = re.sub(r'\[이미지_\d+\]', '', content)
        
        return f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
            <h1 style="color: #0969da; border-bottom: 2px solid #0969da; padding-bottom: 10px;">{title}</h1>
            <div style="line-height: 1.6;">{content.replace('\\n', '<br>')}</div>
        </div>
        """
    
    def create_json_tab(self):
        """JSON 원본 탭 생성 (다크 모드)"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        json_text = QTextEdit()
        json_text.setPlainText(json.dumps(self.blog_data, ensure_ascii=False, indent=2))
        json_text.setReadOnly(True)
        json_text.setFont(QFont("Consolas", 11))
        json_text.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        
        layout.addWidget(json_text)
        tab.setLayout(layout)
        return tab
    
    def save_to_html(self):
        """HTML 파일로 저장"""
        content = self.display_content or self._create_basic_html()
        
        timestamp = self.blog_data.get('generated_at', '').replace(':', '').replace(' ', '_')
        default_filename = f"blog_post_{timestamp}.html"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "블로그 포스팅 HTML 저장", default_filename, "HTML 파일 (*.html)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                # 🔧 다크 모드 성공 메시지
                msg = QMessageBox(self)
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #1a1a1a;
                        color: #e0e0e0;
                    }
                    QMessageBox QPushButton {
                        background-color: #4a9eff;
                        color: #ffffff;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                    }
                """)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("저장 완료! 💾")
                msg.setText(f"HTML 파일이 저장되었습니다.\n\n{file_path}")
                msg.exec()
            except Exception as e:
                # 🔧 다크 모드 오류 메시지
                msg = QMessageBox(self)
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #1a1a1a;
                        color: #e0e0e0;
                    }
                    QMessageBox QPushButton {
                        background-color: #dc3545;
                        color: #ffffff;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                    }
                """)
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("저장 실패")
                msg.setText(f"파일 저장 중 오류가 발생했습니다:\n\n{str(e)}")
                msg.exec()
    
    def closeEvent(self, event):
        """다이얼로그 닫기 시 스레드 정리"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.processing_thread.wait(1000)
        
        if self.timeout_timer.isActive():
            self.timeout_timer.stop()
            
        event.accept()
