# views/news_result_dialog.py
import csv
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QListWidget, 
    QListWidgetItem, QPushButton, QLabel, QSplitter, QProgressBar,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont

class NewsResultDialog(QDialog):
    """뉴스 검색 결과 표시 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.news_list = []
        self.current_news = None
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        self.setWindowTitle('네이버 뉴스 검색 결과')
        self.resize(1200, 800)
        
        layout = QVBoxLayout()
        
        # 상태 표시
        self.status_label = QLabel("검색 준비 중...")
        layout.addWidget(self.status_label)
        
        # 진행률 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 메인 컨텐츠 (스플리터)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 뉴스 리스트
        self.news_list_widget = QListWidget()
        self.news_list_widget.currentItemChanged.connect(self.on_news_selected)
        splitter.addWidget(self.news_list_widget)
        
        # 뉴스 세부 내용
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        splitter.addWidget(self.detail_text)
        
        # 스플리터 비율 설정 (리스트:세부내용 = 1:2)
        splitter.setSizes([400, 800])
        layout.addWidget(splitter)
        
        # 하단 버튼들
        button_layout = QHBoxLayout()
        
        self.open_original_button = QPushButton("원문 링크 열기")
        self.open_original_button.clicked.connect(self.open_original_link)
        self.open_original_button.setEnabled(False)
        
        self.open_naver_button = QPushButton("네이버 뉴스 열기")
        self.open_naver_button.clicked.connect(self.open_naver_link)
        self.open_naver_button.setEnabled(False)
        
        self.export_button = QPushButton("CSV 내보내기")
        self.export_button.clicked.connect(self.export_to_csv)
        self.export_button.setEnabled(False)
        
        self.close_button = QPushButton("닫기")
        self.close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.open_original_button)
        button_layout.addWidget(self.open_naver_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def show_progress(self, visible=True):
        """진행률 표시/숨김"""
        self.progress_bar.setVisible(visible)
        
    def update_progress(self, current, total):
        """진행률 업데이트"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.status_label.setText(f"처리 중... ({current}/{total})")
    
    def update_status(self, message):
        """상태 메시지 업데이트"""
        self.status_label.setText(message)
    
    def show_error(self, error_message):
        """에러 메시지 표시"""
        self.status_label.setText(f"오류: {error_message}")
        QMessageBox.critical(self, "검색 오류", error_message)
        
    def display_news_results(self, news_list):
        """뉴스 검색 결과 표시"""
        self.news_list = news_list
        self.news_list_widget.clear()
        
        if not news_list:
            self.status_label.setText("검색 결과가 없습니다.")
            return
        
        # 뉴스 목록에 추가
        for news in news_list:
            item = QListWidgetItem()
            item_text = f"[{news['index']:2d}] {news['title']}"
            if len(item_text) > 80:
                item_text = item_text[:77] + "..."
            item.setText(item_text)
            item.setData(Qt.ItemDataRole.UserRole, news)
            self.news_list_widget.addItem(item)
        
        # 첫 번째 아이템 선택
        if news_list:
            self.news_list_widget.setCurrentRow(0)
            self.export_button.setEnabled(True)
        
        self.status_label.setText(f"총 {len(news_list)}개의 뉴스를 찾았습니다.")
        
    def on_news_selected(self, current_item, previous_item):
        """뉴스 선택 시 세부 정보 표시"""
        if not current_item:
            return
        
        news = current_item.data(Qt.ItemDataRole.UserRole)
        if not news:
            return
            
        self.current_news = news
        
        # 세부 정보 HTML 구성
        detail_html = f"""
        <h2 style="color: #2c5aa0; margin-bottom: 10px;">{news['title']}</h2>
        
        <div style="background-color: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px;">
            <strong>카테고리:</strong> {news['category']}<br>
            <strong>검색 키워드:</strong> {news['keyword']}<br>
            <strong>발행일:</strong> {news['pubDate']}<br>
            <strong>순서:</strong> {news['index']}번째 뉴스
        </div>
        
        <h3 style="color: #333; margin-top: 20px;">뉴스 요약</h3>
        <p style="line-height: 1.6; font-size: 14px; margin: 10px 0;">
            {news['description']}
        </p>
        
        <h3 style="color: #333; margin-top: 20px;">링크 정보</h3>
        <p style="font-size: 12px; color: #666;">
            <strong>원문 링크:</strong> <br>
            <a href="{news['originallink']}" style="word-break: break-all;">
                {news['originallink']}
            </a>
        </p>
        <p style="font-size: 12px; color: #666;">
            <strong>네이버 뉴스:</strong> <br>
            <a href="{news['link']}" style="word-break: break-all;">
                {news['link']}
            </a>
        </p>
        """
        
        self.detail_text.setHtml(detail_html)
        
        # 버튼 활성화
        self.open_original_button.setEnabled(bool(news.get('originallink')))
        self.open_naver_button.setEnabled(bool(news.get('link')))
    
    def open_original_link(self):
        """원문 링크 열기"""
        if self.current_news and self.current_news.get('originallink'):
            QDesktopServices.openUrl(QUrl(self.current_news['originallink']))
        
    def open_naver_link(self):
        """네이버 뉴스 링크 열기"""
        if self.current_news and self.current_news.get('link'):
            QDesktopServices.openUrl(QUrl(self.current_news['link']))
    
    def export_to_csv(self):
        """검색 결과를 CSV 파일로 내보내기"""
        if not self.news_list:
            QMessageBox.warning(self, "내보내기 실패", "내보낼 뉴스 데이터가 없습니다.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "뉴스 검색 결과 저장",
            "naver_news_results.csv",
            "CSV 파일 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['순번', '제목', '요약', '카테고리', '키워드', '발행일', '원문링크', '네이버링크']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # 헤더 작성
                writer.writeheader()
                
                # 뉴스 데이터 작성
                for news in self.news_list:
                    writer.writerow({
                        '순번': news['index'],
                        '제목': news['title'],
                        '요약': news['description'],
                        '카테고리': news['category'],
                        '키워드': news['keyword'],
                        '발행일': news['pubDate'],
                        '원문링크': news['originallink'],
                        '네이버링크': news['link']
                    })
            
            QMessageBox.information(
                self,
                "내보내기 완료",
                f"뉴스 검색 결과가 저장되었습니다.\n\n파일: {file_path}\n개수: {len(self.news_list)}개"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "내보내기 실패",
                f"CSV 파일 저장 중 오류가 발생했습니다.\n\n오류: {str(e)}"
            )
