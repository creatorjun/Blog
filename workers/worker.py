import json
import requests
import xml.etree.ElementTree as ET
import re
from PyQt6.QtCore import QThread, pyqtSignal
from ai_modules import BlogGenerator
from ai_modules.image_searcher import ImageSearcher

class Worker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

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
            news_list = self._search_naver_news()
            if not news_list:
                self.error.emit("검색된 뉴스가 없습니다.")
                return

            blog_data = self._generate_blog(news_list)
            if not blog_data:
                self.error.emit("블로그 생성에 실패했습니다.")
                return

            final_blog = self._add_images(blog_data)
            self.finished.emit(final_blog)
        except Exception as e:
            self.error.emit(str(e))

    def _search_naver_news(self):
        try:
            search_query = None
            if hasattr(self, 'topic') and self.topic and self.topic.strip():
                search_query = self.topic.strip()
            elif hasattr(self, 'category_name') and self.category_name and self.category_name.strip():
                search_query = self.category_name.strip()
            elif hasattr(self, 'category_id') and self.category_id:
                category_mapping = {
                    '100': '정치', '101': '경제', '102': '사회',
                    '103': '생활문화', '104': '세계', '105': 'IT과학'
                }
                search_query = category_mapping.get(str(self.category_id), '최신뉴스')
            else:
                search_query = '최신뉴스'

            if not self.naver_id or not self.naver_secret:
                raise Exception("네이버 API 키가 설정되지 않았습니다. 설정 탭에서 API 키를 입력해주세요.")

            if len(search_query.encode('utf-8')) > 100:
                search_query = search_query[:30]

            url = "https://openapi.naver.com/v1/search/news.xml"
            params = {'query': search_query, 'display': 50, 'start': 1, 'sort': 'date'}
            headers = {
                'X-Naver-Client-Id': self.naver_id.strip(),
                'X-Naver-Client-Secret': self.naver_secret.strip(),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, params=params, headers=headers, timeout=15)

            if response.status_code != 200:
                error_messages = {
                    400: "잘못된 파라미터", 401: "Client ID/Secret이 올바르지 않음",
                    403: "API 사용량 초과 또는 서비스 제한", 429: "너무 많은 요청"
                }
                error_cause = error_messages.get(response.status_code, f"HTTP {response.status_code}")
                raise Exception(f"네이버 뉴스 API 오류: {error_cause}\n응답 내용: {response.text[:200]}...")

            root = ET.fromstring(response.content)
            news_list = []
            items = root.findall('.//item')
            if not items:
                if search_query != '최신뉴스':
                    return self._fallback_search('최신뉴스')
                else:
                    raise Exception(f"'{search_query}' 검색 결과가 없습니다.")

            for item in items:
                news_item = {
                    'title': self._clean_html(item.find('title').text if item.find('title') is not None else ''),
                    'originallink': item.find('originallink').text if item.find('originallink') is not None else '',
                    'link': item.find('link').text if item.find('link') is not None else '',
                    'description': self._clean_html(item.find('description').text if item.find('description') is not None else ''),
                    'pubDate': item.find('pubDate').text if item.find('pubDate') is not None else '',
                    'category': getattr(self, 'category_name', '전체')
                }
                if news_item['title'].strip():
                    news_list.append(news_item)

            if not news_list:
                raise Exception(f"'{search_query}' 검색 결과를 처리할 수 없습니다.")
            return news_list
        except Exception as e:
            raise Exception(f"뉴스 검색 중 오류: {str(e)}")

    def _fallback_search(self, fallback_query):
        url = "https://openapi.naver.com/v1/search/news.xml"
        params = {'query': fallback_query, 'display': 30, 'start': 1, 'sort': 'date'}
        headers = {
            'X-Naver-Client-Id': self.naver_id.strip(),
            'X-Naver-Client-Secret': self.naver_secret.strip(),
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        root = ET.fromstring(response.content)
        news_list = []
        for item in root.findall('.//item'):
            news_item = {
                'title': self._clean_html(item.find('title').text if item.find('title') is not None else ''),
                'originallink': item.find('originallink').text if item.find('originallink') is not None else '',
                'link': item.find('link').text if item.find('link') is not None else '',
                'description': self._clean_html(item.find('description').text if item.find('description') is not None else ''),
                'pubDate': item.find('pubDate').text if item.find('pubDate') is not None else '',
                'category': '전체'
            }
            if news_item['title'].strip():
                news_list.append(news_item)
        return news_list

    def _generate_blog(self, news_list):
        blog_generator = BlogGenerator(self.gemini_key)
        blog_generator.set_news_data(news_list)
        top_news = blog_generator._select_top_news()
        if not top_news:
            raise Exception("분석할 뉴스가 없습니다")
        additional_info = blog_generator._get_additional_context(top_news)
        from ai_modules.blog_prompts import BlogPrompts
        prompt = BlogPrompts.get_blog_prompt(top_news, additional_info)
        blog_data = blog_generator._generate_with_sdk(prompt)
        final_blog = blog_generator._post_process(blog_data, top_news)
        return final_blog

    def _add_images(self, blog_data):
        try:
            image_keywords = blog_data.get('image_keywords', [])
            if image_keywords:
                from utils import SettingsManager
                settings_manager = SettingsManager()
                image_searcher = ImageSearcher(settings_manager)
                images = image_searcher.search_images(image_keywords)
                blog_data['images'] = images
            else:
                blog_data['images'] = {}
            return blog_data
        except Exception as e:
            print(f"이미지 검색 오류 (계속 진행): {e}")
            blog_data['images'] = {}
            return blog_data

    def _clean_html(self, text):
        if not text:
            return ''
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&amp;', '&').replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        return text.strip()