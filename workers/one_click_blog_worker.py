# workers/one_click_blog_worker.py
import json
import requests
import xml.etree.ElementTree as ET
import re
from PyQt6.QtCore import QThread, pyqtSignal
from ai_modules import BlogGenerator
from ai_modules.image_searcher import ImageSearcher

class OneClickBlogWorker(QThread):
    """원클릭 블로그 생성을 위한 통합 워커 (카테고리/키워드 통합 검색 지원)"""
    
    finished = pyqtSignal(dict)       # 완성된 블로그 데이터
    error = pyqtSignal(str)           # 오류 메시지
    progress = pyqtSignal(int)        # 진행률 (0-100)
    status_changed = pyqtSignal(str)  # 상태 메시지
    
    def __init__(self, naver_id, naver_secret, gemini_key, topic, category_id, category_name):
        super().__init__()
        self.naver_id = naver_id
        self.naver_secret = naver_secret
        self.gemini_key = gemini_key
        self.topic = topic
        self.category_id = category_id  
        self.category_name = category_name
        
    def run(self):
        try:
            # 1단계: 뉴스 검색 (0-40%)
            self.status_changed.emit("네이버 뉴스 검색 중...")
            self.progress.emit(10)
            
            news_list = self._search_naver_news()
            if not news_list:
                self.error.emit("검색된 뉴스가 없습니다.")
                return
            
            self.progress.emit(40)
            
            # 2단계: 블로그 생성 (40-80%)
            self.status_changed.emit("AI 블로그 생성 중...")
            
            blog_data = self._generate_blog(news_list)
            if not blog_data:
                self.error.emit("블로그 생성에 실패했습니다.")
                return
            
            self.progress.emit(80)
            
            # 3단계: 이미지 검색 및 삽입 (80-100%)
            self.status_changed.emit("관련 이미지 검색 중...")
            
            final_blog = self._add_images(blog_data)
            
            self.progress.emit(100)
            self.status_changed.emit("완료!")
            
            # 완성된 블로그 전송
            self.finished.emit(final_blog)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def _search_naver_news(self):
        """네이버 뉴스 통합 검색 (카테고리 + 키워드 지원)"""
        try:
            # 🔧 검색어 결정 로직 개선
            search_query = None
            
            # 1순위: 키워드가 있으면 키워드 사용
            if hasattr(self, 'topic') and self.topic and self.topic.strip():
                search_query = self.topic.strip()
                search_type = "키워드"
                
            # 2순위: 카테고리명이 있으면 카테고리명 사용  
            elif hasattr(self, 'category_name') and self.category_name and self.category_name.strip():
                search_query = self.category_name.strip()
                search_type = "카테고리"
                
            # 3순위: 카테고리 ID를 기반으로 기본 검색어 생성
            elif hasattr(self, 'category_id') and self.category_id:
                category_mapping = {
                    '100': '정치',
                    '101': '경제', 
                    '102': '사회',
                    '103': '생활문화',
                    '104': '세계',
                    '105': 'IT과학'
                }
                search_query = category_mapping.get(str(self.category_id), '최신뉴스')
                search_type = "카테고리 매핑"
                
            # 최후 수단: 기본 검색어
            else:
                search_query = '최신뉴스'
                search_type = "기본"
            
            # API 키 검증
            if not self.naver_id or not self.naver_secret:
                raise Exception("네이버 API 키가 설정되지 않았습니다. 설정 탭에서 API 키를 입력해주세요.")
            
            # 검색어 길이 제한 (네이버 API 제한: 100바이트)
            if len(search_query.encode('utf-8')) > 100:
                search_query = search_query[:30]
                print(f"⚠️ 검색어가 너무 길어서 축약: '{search_query}'")
            
            url = "https://openapi.naver.com/v1/search/news.xml"
            
            params = {
                'query': search_query,
                'display': 50,
                'start': 1,
                'sort': 'date'
            }
            
            headers = {
                'X-Naver-Client-Id': self.naver_id.strip(),
                'X-Naver-Client-Secret': self.naver_secret.strip(),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # 🔧 디버깅 로그
            print(f"🔍 네이버 뉴스 검색 ({search_type}): '{search_query}'")
            print(f"📡 API 요청: {url}")
            print(f"📋 파라미터: {params}")
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            # 🔧 상세한 HTTP 오류 처리
            if response.status_code == 400:
                raise Exception(
                    f"네이버 API 요청 오류 (HTTP 400)\n"
                    f"검색어: '{search_query}' ({search_type})\n"
                    f"원인: 잘못된 파라미터\n"
                    f"해결방법: 검색어를 변경하거나 API 키를 확인해주세요."
                )
            elif response.status_code == 401:
                raise Exception(
                    f"네이버 API 인증 실패 (HTTP 401)\n"
                    f"원인: Client ID/Secret이 올바르지 않음\n"
                    f"해결방법:\n"
                    f"1. 설정 탭에서 네이버 API 키 재확인\n"
                    f"2. https://developers.naver.com 에서 키 상태 확인"
                )
            elif response.status_code == 403:
                raise Exception(
                    f"네이버 API 접근 거부 (HTTP 403)\n"
                    f"원인: API 사용량 초과 또는 서비스 제한\n"
                    f"해결방법: 잠시 후 다시 시도하거나 네이버 개발자센터 확인"
                )
            elif response.status_code == 429:
                raise Exception(
                    f"네이버 API 요청 한도 초과 (HTTP 429)\n"
                    f"원인: 너무 많은 요청\n"
                    f"해결방법: 1분 후 다시 시도해주세요"
                )
            elif response.status_code != 200:
                raise Exception(
                    f"네이버 뉴스 API 오류: HTTP {response.status_code}\n"
                    f"응답 내용: {response.text[:200]}..."
                )
            
            # XML 파싱
            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as e:
                raise Exception(f"네이버 API 응답 파싱 실패: {str(e)}")
            
            # 검색 결과 추출
            news_list = []
            items = root.findall('.//item')
            
            if not items:
                # 검색 결과가 없을 때 대안 검색
                if search_query != '최신뉴스':
                    print(f"⚠️ '{search_query}' 검색 결과 없음. '최신뉴스'로 재검색...")
                    return self._fallback_search('최신뉴스')
                else:
                    raise Exception(f"'{search_query}' 검색 결과가 없습니다.")
            
            for item in items:
                try:
                    news_item = {
                        'title': self._clean_html(item.find('title').text if item.find('title') is not None else ''),
                        'originallink': item.find('originallink').text if item.find('originallink') is not None else '',
                        'link': item.find('link').text if item.find('link') is not None else '',
                        'description': self._clean_html(item.find('description').text if item.find('description') is not None else ''),
                        'pubDate': item.find('pubDate').text if item.find('pubDate') is not None else '',
                        'category': getattr(self, 'category_name', '전체'),
                        'search_query': search_query,
                        'search_type': search_type
                    }
                    
                    # 빈 제목은 제외
                    if news_item['title'].strip():
                        news_list.append(news_item)
                        
                except Exception as e:
                    print(f"⚠️ 뉴스 아이템 파싱 오류: {e}")
                    continue
            
            if not news_list:
                raise Exception(f"'{search_query}' 검색 결과를 처리할 수 없습니다.")
            
            print(f"✅ 뉴스 검색 완료 ({search_type}): {len(news_list)}개 발견")
            return news_list
            
        except Exception as e:
            if "네이버" in str(e) or "API" in str(e):
                raise e  # 이미 처리된 API 오류
            else:
                raise Exception(f"뉴스 검색 중 예상치 못한 오류: {str(e)}")

    def _fallback_search(self, fallback_query):
        """대안 검색 (검색 결과가 없을 때)"""
        try:
            url = "https://openapi.naver.com/v1/search/news.xml"
            
            params = {
                'query': fallback_query,
                'display': 30,
                'start': 1,
                'sort': 'date'
            }
            
            headers = {
                'X-Naver-Client-Id': self.naver_id.strip(),
                'X-Naver-Client-Secret': self.naver_secret.strip(),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                raise Exception(f"대안 검색 실패: HTTP {response.status_code}")
            
            root = ET.fromstring(response.content)
            news_list = []
            
            for item in root.findall('.//item'):
                news_item = {
                    'title': self._clean_html(item.find('title').text if item.find('title') is not None else ''),
                    'originallink': item.find('originallink').text if item.find('originallink') is not None else '',
                    'link': item.find('link').text if item.find('link') is not None else '',
                    'description': self._clean_html(item.find('description').text if item.find('description') is not None else ''),
                    'pubDate': item.find('pubDate').text if item.find('pubDate') is not None else '',
                    'category': '전체',
                    'search_query': fallback_query,
                    'search_type': '대안검색'
                }
                
                if news_item['title'].strip():
                    news_list.append(news_item)
            
            print(f"🔄 대안 검색 완료: {len(news_list)}개")
            return news_list
            
        except Exception as e:
            raise Exception(f"대안 검색 실패: {str(e)}")
    
    def _generate_blog(self, news_list):
        """블로그 생성"""
        try:
            blog_generator = BlogGenerator(self.gemini_key)
            blog_generator.set_news_data(news_list)
            
            # 뉴스 선택
            top_news = blog_generator._select_top_news()
            if not top_news:
                raise Exception("분석할 뉴스가 없습니다")
            
            # 추가 컨텍스트
            additional_info = blog_generator._get_additional_context(top_news)
            
            # 프롬프트 생성
            from ai_modules.blog_prompts import BlogPrompts
            prompt = BlogPrompts.get_blog_prompt(top_news, additional_info)
            
            # 블로그 생성
            blog_data = blog_generator._generate_with_sdk(prompt)
            
            # 후처리
            final_blog = blog_generator._post_process(blog_data, top_news)
            
            return final_blog
            
        except Exception as e:
            raise Exception(f"AI 블로그 생성 실패: {str(e)}")
    
    def _add_images(self, blog_data):
        """이미지 검색 및 추가"""
        try:
            # 이미지 검색어가 있는 경우만 처리
            image_keywords = blog_data.get('image_keywords', [])
            
            if image_keywords:
                # settings_manager를 통해 이미지 검색
                from utils import SettingsManager
                settings_manager = SettingsManager()
                
                image_searcher = ImageSearcher(settings_manager)
                images = image_searcher.search_images(image_keywords)
                
                # 본문에서 [이미지_N] 마커를 실제 이미지로 교체
                content = blog_data.get('content', '')
                
                for marker, image_list in images.items():
                    if image_list:
                        img = image_list[0]
                        img_html = f'''
<div style="text-align: center; margin: 20px 0;">
    <img src="{img["url"]}" alt="{img["description"]}" style="width:100%;max-width:600px;height:auto;border-radius:8px;">
    <p style="font-size:12px;color:#666;margin-top:5px;">사진: {img["photographer"]} ({img["source"]})</p>
</div>'''
                        content = content.replace(f'[{marker}]', img_html)
                    else:
                        # 이미지 못 찾은 경우 마커 제거
                        content = content.replace(f'[{marker}]', '')
                
                blog_data['content'] = content
                blog_data['images'] = images
            else:
                # 이미지 키워드가 없으면 마커만 제거
                content = blog_data.get('content', '')
                content = re.sub(r'\[이미지_\d+\]', '', content)
                blog_data['content'] = content
                blog_data['images'] = {}
            
            return blog_data
            
        except Exception as e:
            print(f"이미지 검색 오류 (계속 진행): {e}")
            # 이미지 검색 실패해도 블로그는 완성
            content = blog_data.get('content', '')
            content = re.sub(r'\[이미지_\d+\]', '', content)
            blog_data['content'] = content
            blog_data['images'] = {}
            return blog_data
    
    def _clean_html(self, text):
        """HTML 태그 및 엔티티 제거"""
        if not text:
            return ''
        
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # HTML 엔티티 디코딩
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&amp;', '&').replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        return text.strip()
