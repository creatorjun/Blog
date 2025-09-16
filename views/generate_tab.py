import json
import re
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QFrame, QTabWidget, QTextEdit,
    QProgressBar, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QMimeData, QUrl
from PyQt6.QtGui import QFont
from utils.image_downloader import ImageDownloader

class ImageProcessingThread(QThread):
    finished = pyqtSignal(str, str, dict)
    error = pyqtSignal(str)

    def __init__(self, blog_data, image_downloader):
        super().__init__()
        self.blog_data = blog_data
        self.image_downloader = image_downloader
        self.local_image_paths = {}

    def run(self):
        try:
            display_html = self._process_content_for_display()
            markdown_content = self._process_content_for_markdown()
            self.finished.emit(display_html, markdown_content, self.local_image_paths)
        except Exception as e:
            self.error.emit(str(e))

    def _get_content_as_string(self):
        content = self.blog_data.get('body', '') or self.blog_data.get('content', '')
        if isinstance(content, list):
            content = '\n'.join(str(item) for item in content)
        elif not isinstance(content, str):
            content = str(content)
        return content

    def _process_content_for_display(self):
        content = self._get_content_as_string()
        title = self.blog_data.get('title', '')
        conclusion = self.blog_data.get('conclusion', '')
        tags = self.blog_data.get('tags', [])
        images_data = self.blog_data.get('images', {})
        image_markers = re.findall(r'\[이미지_\d+\]', content)

        for marker in image_markers:
            marker_key = marker.strip('[]')
            if marker_key in images_data and images_data[marker_key]:
                img_data = images_data[marker_key][0]
                img_url = img_data.get('url', '')
                if img_url:
                    local_path = self.image_downloader.download_image(
                        img_url, filename_prefix=marker_key.replace('_', '')
                    )
                    if local_path and os.path.exists(local_path):
                        file_url = self.image_downloader.get_file_url(local_path)
                        self.local_image_paths[marker_key] = local_path
                        img_tag = f'<div align="center" style="margin: 1em 0;"><img src="{file_url}" style="max-width:90%; border-radius: 8px;"></div>'
                        content = content.replace(marker, img_tag)
                    else:
                        content = content.replace(marker, '<p style="color:red;">이미지를 불러올 수 없습니다</p>')
                else:
                    content = content.replace(marker, '')
            else:
                content = content.replace(marker, '')
        return self._build_display_html(title, content, conclusion, tags)

    def _process_content_for_markdown(self):
        content = self._get_content_as_string()
        title = self.blog_data.get('title', '')
        conclusion = self.blog_data.get('conclusion', '')
        tags = self.blog_data.get('tags', [])
        
        image_markers = re.findall(r'\[이미지_\d+\]', content)
        for marker in image_markers:
            content = content.replace(marker, f'\n\n{marker}\n\n')

        markdown_parts = [f'# {title}\n', content]
        if conclusion:
            markdown_parts.extend(['\n---\n## 💭 결론\n', conclusion])
        if tags:
            markdown_parts.extend(['\n---\n## 🏷️ 태그\n', ' '.join(tags)])
            
        return '\n'.join(markdown_parts)

    def _build_display_html(self, title, content, conclusion, tags):
        paragraphs = []
        for part in re.split(r'\n+', content):
            part = part.strip()
            if not part:
                continue
            if part.startswith('<div'):
                paragraphs.append(part)
            else:
                paragraphs.append(f'<p>{part}</p>')
        
        content_html = "".join(paragraphs)
        conclusion_html = f'<h2>결론</h2><p>{conclusion}</p>' if conclusion else ""
        tags_html = f"<h2>태그</h2><p>{' '.join(tags)}</p>" if tags else ""

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-size: 16px; line-height: 1.7; }}
                h1 {{ font-size: 2em; }}
                h2 {{ font-size: 1.5em; }}
                p {{ margin: 1em 0; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            {content_html}
            {conclusion_html}
            {tags_html}
        </body>
        </html>
        """
        return html

class GenerateTab(QWidget):
    generation_requested = pyqtSignal(str, str, int)
    search_settings_changed = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self.categories = {
            "정치": 100, "경제": 101, "사회": 102,
            "생활/문화": 103, "세계": 104, "IT/과학": 105
        }
        self.blog_data = None
        self.markdown_content = None
        self.local_image_paths = {}
        self.image_downloader = ImageDownloader()
        self.processing_thread = None
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        input_group = QFrame()
        input_layout = QVBoxLayout(input_group)
        
        title_label = QLabel("포스팅 생성")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_layout.addWidget(title_label)

        controls_layout = QHBoxLayout()
        category_label = QLabel("카테고리:")
        self.category_dropdown = QComboBox()
        self.category_dropdown.addItems(self.categories.keys())
        
        keyword_label = QLabel("키워드:")
        self.topic_edit = QLineEdit()
        self.topic_edit.setPlaceholderText("선택사항")

        controls_layout.addWidget(category_label)
        controls_layout.addWidget(self.category_dropdown, 1)
        controls_layout.addSpacing(15)
        controls_layout.addWidget(keyword_label)
        controls_layout.addWidget(self.topic_edit, 2)
        
        input_layout.addLayout(controls_layout)
        
        self.generate_button = QPushButton("생성 시작")
        self.generate_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.generate_button.setMinimumHeight(40)
        input_layout.addWidget(self.generate_button)
        
        main_layout.addWidget(input_group, 0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar, 0)

        self.result_widget = QWidget()
        result_layout = QVBoxLayout(self.result_widget)
        result_layout.setContentsMargins(0, 10, 0, 0)
        
        self.result_tabs = QTabWidget()
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("생성 버튼을 클릭하면 여기에 결과가 표시됩니다.")
        
        self.json_text = QTextEdit()
        self.json_text.setReadOnly(True)
        self.json_text.setFont(QFont("Courier New", 10))
        
        self.result_tabs.addTab(self.preview_text, "📖 미리보기")
        self.result_tabs.addTab(self.json_text, "📄 JSON 원본")
        result_layout.addWidget(self.result_tabs)

        button_layout = QHBoxLayout()
        self.copy_text_button = QPushButton("📝 텍스트만 복사")
        self.copy_all_button = QPushButton("📋 이미지 복사")
        self.save_button = QPushButton("💾 HTML 저장")
        button_layout.addStretch()
        button_layout.addWidget(self.copy_text_button)
        button_layout.addWidget(self.copy_all_button)
        button_layout.addWidget(self.save_button)
        result_layout.addLayout(button_layout)
        
        main_layout.addWidget(self.result_widget, 1)

    def connect_signals(self):
        self.generate_button.clicked.connect(self.start_generation)
        self.category_dropdown.currentIndexChanged.connect(self.on_search_settings_changed)
        self.topic_edit.textChanged.connect(self.on_search_settings_changed)
        self.copy_text_button.clicked.connect(self.copy_text_only)
        self.copy_all_button.clicked.connect(self.copy_with_images_to_clipboard)
        self.save_button.clicked.connect(self.save_to_html)

    def start_generation(self):
        self.generate_button.setEnabled(False)
        self.preview_text.setPlaceholderText("AI가 블로그 포스팅을 생성하고 있습니다...")
        self.preview_text.clear()
        self.json_text.clear()
        self.progress_bar.setVisible(True)
        
        category_name = self.category_dropdown.currentText()
        topic = self.topic_edit.text().strip()
        category_id = self.categories.get(category_name)
        self.generation_requested.emit(category_name, topic, category_id)

    def on_generation_finished(self, blog_data):
        self.blog_data = blog_data
        self.json_text.setPlainText(json.dumps(self.blog_data, ensure_ascii=False, indent=2))
        
        self.processing_thread = ImageProcessingThread(self.blog_data, self.image_downloader)
        self.processing_thread.finished.connect(self.on_image_processing_finished)
        self.processing_thread.error.connect(self.on_generation_error)
        self.processing_thread.start()

    def on_image_processing_finished(self, html_content, markdown_content, image_paths):
        self.markdown_content = markdown_content
        self.local_image_paths = image_paths
        self.preview_text.setHtml(html_content)
        
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)
        QMessageBox.information(self, "성공", "블로그 포스팅 생성이 완료되었습니다.")

    def on_generation_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)
        self.preview_text.setPlaceholderText("오류가 발생했습니다. 다시 시도해 주세요.")
        QMessageBox.critical(self, "오류 발생", f"블로그 생성 중 오류가 발생했습니다:\n\n{error_msg}")

    def on_search_settings_changed(self):
        self.search_settings_changed.emit(self.category_dropdown.currentIndex(), self.topic_edit.text())

    def get_form_data(self):
        return {
            'topic': self.topic_edit.text().strip(),
            'category_name': self.category_dropdown.currentText(),
            'category_id': self.categories.get(self.category_dropdown.currentText())
        }

    def set_form_data(self, data):
        category_name = data.get('category_name', 'IT/과학')
        if category_name in self.categories:
            self.category_dropdown.setCurrentText(category_name)
        self.topic_edit.setText(data.get('topic', ''))

    def copy_text_only(self):
        if not self.markdown_content:
            QMessageBox.warning(self, "복사 실패", "복사할 텍스트가 없습니다.")
            return

        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.markdown_content)
        QMessageBox.information(self, "복사 완료", "마크다운 텍스트가 클립보드에 복사되었습니다.")

    def copy_with_images_to_clipboard(self):
        if not self.markdown_content:
            QMessageBox.warning(self, "복사 실패", "복사할 콘텐츠가 없습니다.")
            return

        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        mime_data = QMimeData()
        
        mime_data.setText(self.markdown_content)
        
        html_with_local_images = self.preview_text.toHtml()
        mime_data.setHtml(html_with_local_images)
        
        if self.local_image_paths:
            urls = [QUrl.fromLocalFile(os.path.abspath(p)) for p in self.local_image_paths.values() if os.path.exists(p)]
            if urls:
                mime_data.setUrls(urls)
        
        clipboard.setMimeData(mime_data)
        QMessageBox.information(self, "전체 복사 완료", "이미지를 포함한 전체 콘텐츠가 클립보드에 복사되었습니다.")

    def save_to_html(self):
        html_content = self.preview_text.toHtml()
        if not html_content:
            QMessageBox.warning(self, "저장 실패", "저장할 콘텐츠가 없습니다.")
            return
            
        timestamp = self.blog_data.get('generated_at', '').replace(':', '').replace(' ', '_')
        default_filename = f"blog_post_{timestamp}.html"
        
        file_path, _ = QFileDialog.getSaveFileName(self, "HTML 저장", default_filename, "HTML Files (*.html)")
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                QMessageBox.information(self, "저장 완료", f"파일이 성공적으로 저장되었습니다:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "저장 실패", f"파일 저장 중 오류가 발생했습니다:\n{str(e)}")